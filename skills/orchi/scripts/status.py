#!/usr/bin/env python3
"""Read-only overview of Orchi entry points: open Epics and standalone Tasks, their owners, and readiness."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Callable

QUERY = '''
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $cursor, states: OPEN, labels: ["Epic", "Task"],
           orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url
        labels(first: 20) { nodes { name } }
        assignees(first: 10) { nodes { login } }
        parent { number title }
        subIssues(first: 100) { totalCount nodes { number title state } }
        blockedBy(first: 50) { nodes {
          number title state stateReason
          closedByPullRequestsReferences(first: 10, includeClosedPrs: true) {
            nodes { number merged baseRefName } }
        } }
      }
    }
  }
}
'''
TAGS = re.compile(r'\[([A-Z][A-Z0-9]{1,7})\]')
ORDER = {'ready': 0, 'check': 1, 'blocked': 2, 'claimed': 3}

Runner = Callable[[list[str]], str]


def gh(args: list[str]) -> str:
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout


def names(connection: dict | None, key: str) -> list[str]:
    return [node[key] for node in (connection or {}).get('nodes', [])]


def claimed(labels: list[str]) -> bool:
    # Accept the common "in progress" spelling as well as the documented label.
    return any(label.casefold().replace(' ', '-') == 'in-progress' for label in labels)


def tags(title: str) -> list[str]:
    """Leading [TAG] groups of a title."""
    found, position = [], 0
    while match := TAGS.match(title, position):
        found.append(match[1])
        position = match.end()
    return found


def shown(path: list[str]) -> str:
    return ''.join(f'[{tag}]' for tag in path) or 'no tags'


def naming(issue: dict, kind: str) -> list[str]:
    """Titles start with the Initiative tag and the Epic tag; Tasks repeat their Epic's tags."""
    own = tags(issue['title'])
    warnings = []
    if kind == 'Epic':
        parent = tags(issue['parent']['title']) if issue.get('parent') else []
        if own[:-1] != parent or len(own) != len(parent) + 1:
            expected = ''.join(f'[{tag}]' for tag in parent) + '[<EPIC TAG>]'
            warnings.append(f'title should start with {expected}, not {shown(own)}')
        for child in (issue.get('subIssues') or {}).get('nodes', []):
            if child.get('state') == 'OPEN' and 'title' in child and tags(child['title']) != own:
                warnings.append(f"Task #{child['number']} title should start with {shown(own)}, not {shown(tags(child['title']))}")
    elif own:
        warnings.append(f'a standalone Task title has no tags, not {shown(own)}')
    return warnings


def blocker_state(node: dict) -> tuple[str, str]:
    """Classify one native blocker as satisfied, unverified, or blocking."""
    if node['state'] == 'OPEN':
        return 'blocking', 'open'
    if node.get('stateReason') != 'COMPLETED':
        return 'blocking', 'cancelled'
    merged = [pr for pr in (node.get('closedByPullRequestsReferences') or {}).get('nodes', []) if pr['merged']]
    if merged:
        return 'satisfied', 'merged into ' + ', '.join(sorted({pr['baseRefName'] for pr in merged}))
    return 'unverified', 'closed without a linked merged PR'


def classify(issue: dict) -> dict | None:
    """Return an entry-point summary, or None for Tasks that belong to a parent."""
    labels = names(issue.get('labels'), 'name')
    kind = 'Epic' if 'Epic' in labels else 'Task'
    if kind == 'Task' and issue.get('parent'):
        return None
    blockers = []
    for node in (issue.get('blockedBy') or {}).get('nodes', []):
        state, detail = blocker_state(node)
        blockers.append({'number': node['number'], 'title': node['title'], 'state': state, 'detail': detail})
    states = {blocker['state'] for blocker in blockers}
    if claimed(labels):
        status = 'claimed'
    elif 'blocking' in states:
        status = 'blocked'
    elif 'unverified' in states:
        status = 'check'
    else:
        status = 'ready'
    children = issue.get('subIssues') or {'totalCount': 0, 'nodes': []}
    done = sum(1 for node in children['nodes'] if node['state'] == 'CLOSED')
    parent = issue.get('parent')
    return {'number': issue['number'], 'kind': kind, 'title': issue['title'], 'url': issue['url'],
            'status': status, 'owners': names(issue.get('assignees'), 'login'),
            'parent': parent['number'] if parent else None,
            'tasks': {'closed': done, 'total': children['totalCount']} if kind == 'Epic' else None,
            'blockers': blockers, 'naming': naming(issue, kind)}


def fetch(repo: str, run: Runner = gh) -> list[dict]:
    owner, _, name = repo.partition('/')
    if not owner or not name:
        raise ValueError('Repository must be OWNER/NAME: ' + repo)
    issues, cursor = [], None
    while True:
        args = ['api', 'graphql', '-f', 'query=' + QUERY, '-F', 'owner=' + owner, '-F', 'name=' + name]
        if cursor:
            args += ['-F', 'cursor=' + cursor]
        page = json.loads(run(args))['data']['repository']['issues']
        issues += page['nodes']
        if not page['pageInfo']['hasNextPage']:
            return issues
        cursor = page['pageInfo']['endCursor']


def report(issues: list[dict]) -> list[dict]:
    entries = [entry for entry in map(classify, issues) if entry]
    return sorted(entries, key=lambda entry: (ORDER[entry['status']], entry['number']))


def render(entries: list[dict]) -> str:
    if not entries:
        return 'No open Epics or standalone Tasks.'
    lines = []
    for entry in entries:
        extra = []
        if entry['parent']:
            extra.append(f"in #{entry['parent']}")
        if entry['tasks'] is not None:
            extra.append(f"tasks {entry['tasks']['closed']}/{entry['tasks']['total']}")
        if entry['owners']:
            extra.append('owner ' + ', '.join(entry['owners']))
        lines.append(f"{entry['status']:<8} {entry['kind']:<4} #{entry['number']} {entry['title']}"
                     + (f"  ({'; '.join(extra)})" if extra else ''))
        for blocker in entry['blockers']:
            lines.append(f"           blocked by #{blocker['number']}: {blocker['detail']}")
        for warning in entry['naming']:
            lines.append(f'           naming: {warning}')
    lines.append('Snapshot only: confirm predecessor results are on the intended integration branch before claiming.')
    return '\n'.join(lines)


def main(argv: list[str] | None = None, run: Runner = gh) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', help='OWNER/NAME; defaults to the current repository')
    parser.add_argument('--json', action='store_true', help='Print machine-readable output')
    args = parser.parse_args(argv)
    try:
        repo = args.repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        entries = report(fetch(repo, run))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, 'stderr', '') or error
        print(f'Orchi status error: {detail}'.rstrip(), file=sys.stderr)
        return 2
    print(json.dumps({'repository': repo, 'entries': entries}, indent=2) if args.json else render(entries))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
