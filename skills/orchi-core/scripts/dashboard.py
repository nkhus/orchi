#!/usr/bin/env python3
"""Read-only snapshot of an Orchi pool for its dashboard: the work tree, PRs, recent merges, and the crews."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime

import status

QUERY = '''
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    initiatives: issues(first: 50, states: OPEN, labels: ["Initiative"], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title url labels(first: 20) { nodes { name } } subIssues(first: 100) { totalCount nodes { state } } }
    }
    epics: issues(first: 100, states: OPEN, labels: ["Epic"]) {
      nodes { number subIssues(first: 100) { nodes { number title url state labels(first: 20) { nodes { name } } } } }
    }
    planning: issues(first: 50, states: OPEN, labels: ["needs-planning", "Exploration"],
                     orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title url labels(first: 20) { nodes { name } } }
    }
    claimed: issues(first: 100, states: OPEN, labels: ["in-progress"]) { nodes { number body } }
    open: pullRequests(first: 50, states: OPEN, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url isDraft baseRefName reviewDecision
        closingIssuesReferences(first: 10) { nodes { number } }
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      }
    }
    merged: pullRequests(first: 5, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { number title url mergedAt baseRefName }
    }
  }
}
'''
CLAIM = re.compile(r'Assigned to (crew-\d+)')
ROLES = {'researcher': 'Researcher', 'prototyper': 'Prototyper', 'planner': 'Planner', 'designer': 'Designer',
         'dev-lead': 'Dev lead'}
TITLE = re.compile(r'\[([a-z-]+)\] ')
CHECKS = {'SUCCESS': 'passing', 'FAILURE': 'failing', 'ERROR': 'failing', 'PENDING': 'running', 'EXPECTED': 'running'}


def role(title: str) -> str | None:
    """The crew role its title names (`[dev-lead] pay`), or None for a free crew (`crew-2`)."""
    match = TITLE.match(title)
    return ROLES.get(match[1]) if match else None


def collect(repo: str, run: status.Runner = status.gh) -> dict:
    """GitHub state of the repository, shaped for the dashboard page."""
    owner, _, name = repo.partition('/')
    data = json.loads(run(['api', 'graphql', '-f', 'query=' + QUERY, '-f', 'owner=' + owner,
                           '-f', 'name=' + name]))['data']['repository']
    crews = {node['number']: match[1] for node in data['claimed']['nodes']
             if (match := CLAIM.search(node.get('body') or ''))}
    work = []
    for node in data['initiatives']['nodes']:
        children = node['subIssues']
        work.append({'number': node['number'], 'kind': 'Initiative', 'title': node['title'], 'url': node['url'],
                     'status': 'claimed' if status.claimed(status.names(node['labels'], 'name')) else 'ready',
                     'parent': None, 'crew': crews.get(node['number']),
                     'progress': {'done': sum(child['state'] == 'CLOSED' for child in children['nodes']),
                                  'total': children['totalCount']}})
    for entry in status.report(status.fetch(repo, run)):
        work.append({'number': entry['number'], 'kind': entry['kind'], 'title': entry['title'], 'url': entry['url'],
                     'status': entry['status'], 'parent': entry['parent'], 'crew': crews.get(entry['number']),
                     'progress': ({'done': entry['tasks']['closed'], 'total': entry['tasks']['total']}
                                  if entry['tasks'] else None)})
    # An Epic's open Tasks, nested under it; status.py lists only Tasks without a parent.
    shown = {item['number'] for item in work}
    for node in data['epics']['nodes']:
        if node['number'] not in shown:
            continue
        for child in node['subIssues']['nodes']:
            if child['state'] != 'OPEN' or child['number'] in shown:
                continue
            work.append({'number': child['number'], 'kind': 'Task', 'title': child['title'], 'url': child['url'],
                         'status': 'claimed' if status.claimed(status.names(child['labels'], 'name')) else 'todo',
                         'parent': node['number'], 'crew': crews.get(child['number']), 'progress': None})
    planning = [{'number': node['number'], 'title': node['title'], 'url': node['url'],
                 'kind': 'Exploration' if status.labelled(status.names(node['labels'], 'name'), 'Exploration')
                 else 'needs-planning', 'crew': crews.get(node['number'])}
                for node in data['planning']['nodes']]
    default = (data.get('defaultBranchRef') or {}).get('name')
    pulls = []
    for node in data['open']['nodes']:
        commits = node['commits']['nodes']
        rollup = ((commits[0]['commit'].get('statusCheckRollup') or {}) if commits else {}).get('state')
        pulls.append({'number': node['number'], 'title': node['title'], 'url': node['url'],
                      'draft': node['isDraft'], 'base': node['baseRefName'], 'into_default': node['baseRefName'] == default,
                      'checks': CHECKS.get(rollup, 'none'), 'review': node.get('reviewDecision'),
                      'closes': [issue['number'] for issue in node['closingIssuesReferences']['nodes']]})
    merged = [{'number': node['number'], 'title': node['title'], 'url': node['url'], 'merged_at': node['mergedAt'],
               'base': node['baseRefName']} for node in data['merged']['nodes']]
    return {'default_branch': default, 'work': work, 'planning': planning, 'pulls': pulls, 'merged': merged}


def lineage(work: list[dict], number: int | None) -> list[int]:
    """The Initiative and Epic an item sits in, outermost first: `[1, 2]` for Task 9 of Epic 2 of Initiative 1."""
    parents = {item['number']: item.get('parent') for item in work}
    chain = []
    while number in parents and parents[number] and parents[number] not in chain:
        number = parents[number]
        chain.insert(0, number)
    return chain


def snapshot(repo: str, github: dict, crews: list[dict], mode: str, now: datetime) -> dict:
    """The document the dashboard page renders: GitHub state joined with the crews the session read from the host."""
    # A crew's own claim is its outermost one: a dev lead's Epic, not the Tasks of it that also name its crew.
    claims = {}
    for item in github['work'] + github['planning']:
        if item.get('crew') and item['crew'] not in claims:
            claims[item['crew']] = item['number']
    joined = []
    for crew in crews:
        title = crew.get('title') or crew['name']
        issue = crew.get('issue') or claims.get(crew['name'])
        state = crew.get('state') or ('free' if role(title) is None else 'idle')
        joined.append({**crew, 'title': title, 'role': role(title), 'issue': issue, 'state': state,
                       'path': lineage(github['work'], issue)})
    return {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'mode': mode,
            'error': None, 'crews': joined, **github}


def waiting(document: dict) -> list[dict]:
    """What waits for the user: crews that asked them something, and PRs into the default branch ready to merge."""
    items = [{'kind': 'question', 'crew': crew['name'], 'issue': crew.get('issue'), 'text': crew.get('question') or ''}
             for crew in document['crews'] if crew['state'] == 'waiting']
    items += [{'kind': 'merge', 'pull': pull['number'], 'text': pull['title']} for pull in document['pulls']
              if pull['into_default'] and not pull['draft'] and pull['checks'] in {'passing', 'none'}]
    return items


def summary(document: dict) -> str:
    """The dashboard session's title: the time of the refresh and the counts the user scans for."""
    time = document['updated'][11:16]
    if document.get('error'):
        return f'📊 {time} · refresh failed'
    active = sum(crew['state'] in {'working', 'waiting', 'idle'} and crew['role'] is not None for crew in document['crews'])
    return f"📊 {time} · {active} active · {len(document['waiting'])} wait for you · {len(document['pulls'])} PRs"


def main(argv: list[str] | None = None, run: status.Runner = status.gh, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', help='OWNER/NAME; defaults to the current repository')
    parser.add_argument('--crews', required=True, help='JSON file with the crews read from the host')
    parser.add_argument('--mode', required=True, choices=('on', 'off'), help='Whether autonomous mode is on')
    parser.add_argument('--out', required=True, help='Where to write the snapshot JSON')
    args = parser.parse_args(argv)
    now = now or datetime.now().astimezone()
    try:
        with open(args.crews, encoding='utf-8') as handle:
            crews = json.load(handle)
        repo = args.repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        document = snapshot(repo, collect(repo, run), crews, args.mode, now)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        detail = str(getattr(error, 'stderr', '') or error).strip()
        # Only the failure and its time: merged into the stored snapshot, the page keeps the last good state.
        document = {'updated': now.isoformat(timespec='seconds'), 'error': detail}
        print(f'Orchi dashboard error: {detail}', file=sys.stderr)
    else:
        document['waiting'] = waiting(document)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(document, handle, ensure_ascii=False, indent=1)
    print(summary(document))
    return 2 if document['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
