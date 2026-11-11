#!/usr/bin/env python3
"""Read-only snapshot of an Orchi pool for its dashboard: the work tree as a board, PRs, recent merges, the crews and
their questions, and what moved since the last refresh."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import status

QUERY = '''
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    initiatives: issues(first: 50, states: OPEN, labels: ["Initiative"], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title url labels(first: 20) { nodes { name } }
              subIssues(first: 100) { totalCount nodes { number title url state } } }
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
WAITS = re.compile(r'waits for #(\d+)')
# A crew quiet for longer than this, with nothing running and nothing to wait for, looks stalled; a background run
# this old needs a look; a crew listed this long ago with no activity since did not answer Orchi's `status?`.
STALL = timedelta(minutes=30)
LONG_RUN = timedelta(hours=3)
ANSWER = timedelta(minutes=10)
# A crew ends its `Background:` line with `(pid <n>[, <m>])` for each command it runs in the background.
PIDS = re.compile(r'\(pids? (\d+(?:, *\d+)*)\)\s*$')
ENDED = timedelta(minutes=10)
# Orchi's notes: a heading line, a numbered question for the user (not an indented sub-item), a question that asks
# the user's yes for a merge, and standing decisions that defer an Issue or hold a PR.
HEADING = re.compile(r'^\s*#{1,6}\s+(.*)$')
QUESTION = re.compile(r'^(?:[-*] )?(\d+)[.)]\s+(.+?)\s*$')
MERGE = re.compile(r'^Merge PR #(\d+)\b')
DEFERRED = re.compile(r'#(\d+)\s+deferred\b', re.IGNORECASE)
HELD = re.compile(r'#(\d+)\s+on hold\b', re.IGNORECASE)
# A question block, as a crew ends its turn with it or Orchi keeps it in its notes: `Question: <text>`, an optional
# `Context: <text>`, and its options, `1. <option>: <what it leads to> (recommended)`.
ASK = re.compile(r'^\s*Question\s*:\s*(.+?)\s*$', re.IGNORECASE)
CONTEXT = re.compile(r'^\s*Context\s*:\s*(.+?)\s*$', re.IGNORECASE)
OPTION = re.compile(r'^\s*(?:[-*]|\d+[.)])\s+(.+?)\s*$')
RECOMMENDED = re.compile(r'\s*\((?:recommended|rec\.)\)\s*', re.IGNORECASE)
REFERENCE = re.compile(r'#(\d+)\b')
# The board's columns, in the order a parent takes the first its own state or its children reach.
COLUMNS = ('questions', 'review', 'progress', 'planning', 'backlog', 'done')
HISTORY = 10


def running(pid: int) -> bool:
    """Whether a process with this id still runs on this machine (one owned by another user counts as running)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def ended(run: str | None, alive=None) -> bool:
    """Whether every command a `Background:` line names by process id has ended; False when it names none."""
    match = PIDS.search(run or '')
    alive = alive or running
    return bool(match) and not any(alive(int(pid)) for pid in re.split(r', *', match.group(1)))
ROLES = {'researcher': 'Researcher', 'prototyper': 'Prototyper', 'planner': 'Planner', 'designer': 'Designer',
         'dev-lead': 'Dev lead'}
TITLE = re.compile(r'\[([a-z-]+)\] ')
CHECKS = {'SUCCESS': 'passing', 'FAILURE': 'failing', 'ERROR': 'failing', 'PENDING': 'running', 'EXPECTED': 'running'}
# A crew's work runs while its subagents write their transcripts, or while a command it or they started runs: every
# Bash tool command runs in a shell that sources a shell snapshot, a child of the session's own `claude` process.
# `ps` and `lsof` get `PROBE` seconds; what they cannot tell in time counts as nothing.
RECENT = timedelta(minutes=10)
SHELL = '/shell-snapshots/snapshot-'
PROBE = 10


def notes(path: str | None) -> dict:
    """Orchi's open questions for the user, the PRs they ask the user to merge, and the Issues and PRs the user deferred
    or held, read from its notes; empty without them."""
    found = {'questions': [], 'merges': [], 'deferred': [], 'held': []}
    try:
        with open(path, encoding='utf-8') as handle:
            lines = handle.read().splitlines()
    except (OSError, TypeError, ValueError):
        return found
    section, current = '', None
    for line in lines:
        heading = HEADING.match(line)
        if heading:
            section, current = heading.group(1).strip().lower(), None
        elif section == 'questions for the user' and (question := QUESTION.match(line)):
            number, text = int(question.group(1)), question.group(2)
            current = None
            if all(item['number'] != number for item in found['questions']):
                current = {'number': number, 'text': text, 'context': None, 'options': []}
                found['questions'].append(current)
                if merge := MERGE.match(text):
                    found['merges'].append(int(merge.group(1)))
        elif section == 'questions for the user' and current and line[:1].isspace():
            # An indented line under a question: its context or one of its options.
            if context := CONTEXT.match(line):
                current['context'] = context.group(1)
            elif option := OPTION.match(line):
                current['options'].append(choice(option.group(1)))
        elif section == 'standing decisions':
            for key, pattern in (('deferred', DEFERRED), ('held', HELD)):
                found[key] += [int(n) for n in pattern.findall(line) if int(n) not in found[key]]
    return found


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
    waits = {node['number']: int(match[1]) for node in data['claimed']['nodes']
             if (match := WAITS.search(node.get('body') or ''))}
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
    for item in work + planning:
        item['waits_for'] = waits.get(item['number'])
    # Closed Epics of the open Initiatives and closed Tasks of the open Epics: the board's Done column.
    closed, shown = [], {item['number'] for item in work}
    for node, kind, source in ([(node, 'Epic', node) for node in data['initiatives']['nodes']]
                               + [(node, 'Task', node) for node in data['epics']['nodes']]):
        if node['number'] not in shown:
            continue
        for child in source['subIssues']['nodes']:
            if child.get('state') == 'CLOSED' and child.get('number') and child['number'] not in shown:
                closed.append({'number': child['number'], 'kind': kind, 'title': child.get('title') or '',
                               'url': child.get('url'), 'parent': node['number']})
    return {'default_branch': default, 'work': work, 'planning': planning, 'pulls': pulls, 'merged': merged,
            'closed': closed}


def lineage(work: list[dict], number: int | None) -> list[int]:
    """The Initiative and Epic an item sits in, outermost first: `[1, 2]` for Task 9 of Epic 2 of Initiative 1."""
    parents = {item['number']: item.get('parent') for item in work}
    chain = []
    while number in parents and parents[number] and parents[number] not in chain:
        number = parents[number]
        chain.insert(0, number)
    return chain


def choice(text: str) -> dict:
    """One option of a question: `<label>: <what it leads to>`, marked recommended by `(recommended)`."""
    recommended = bool(RECOMMENDED.search(text))
    text = RECOMMENDED.sub(' ', text).strip()
    label, _, consequence = text.partition(': ')
    return {'label': label.strip(), 'consequence': consequence.strip() or None, 'recommended': recommended}


def questions(block: str | None, fallback: str | None = None) -> list[dict]:
    """The questions in a crew's question block: each `Question:` line with the `Context:` and options after it. A
    crew that asked in another form gets its one-line question, without options."""
    found, current = [], None
    for line in (block or '').splitlines():
        if ask := ASK.match(line):
            current = {'text': ask.group(1), 'context': None, 'options': []}
            found.append(current)
        elif current and (context := CONTEXT.match(line)):
            current['context'] = context.group(1)
        elif current and (option := OPTION.match(line)):
            current['options'].append(choice(option.group(1)))
    if not found and fallback:
        found = [{'text': fallback, 'context': None, 'options': []}]
    for item in found:
        item['here'] = '(user, here)' in item['text']
    return found[:6]


def directories(pids: list[str]) -> dict[str, str]:
    """The working directory of each process that still runs: `/proc` on Linux, else `lsof`."""
    if os.path.isdir('/proc/self'):
        found = {}
        for pid in pids:
            try:
                found[pid] = os.readlink(f'/proc/{pid}/cwd')
            except OSError:
                pass
        return found
    # lsof exits 1 when one of the processes has ended; the others are still listed.
    listing = subprocess.run(['lsof', '-nP', '-a', '-d', 'cwd', '-Fpn', '-p', ','.join(pids)],
                             capture_output=True, text=True, timeout=PROBE).stdout
    found, pid = {}, None
    for line in listing.splitlines():
        if line.startswith('p'):
            pid = line[1:]
        elif line.startswith('n') and pid:
            found[pid] = line[1:]
    return found


def commands(listing: str, cwd=directories) -> Counter:
    """Running Bash tool commands per session directory, from `ps -axo pid=,ppid=,args=`; a shell nested in another
    tool shell is part of its command."""
    shells = {}
    for line in listing.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and SHELL in parts[2]:
            shells[parts[0]] = parts[1]
    parents = [parent for parent in shells.values() if parent not in shells]
    places = {pid: os.path.realpath(path) for pid, path in cwd(sorted(set(parents))).items()} if parents else {}
    return Counter(places[parent] for parent in parents if parent in places)


def activity(crews: list[dict], now: datetime, root: Path | None = None, listing: str | None = None,
             cwd=directories) -> dict:
    """What runs for each crew with a role and a `cwd`: `{name: {"subagents", "commands"}}`, crews with nothing left
    out. Subagents count while their transcripts, under the session's folder in `~/.claude/projects`, were written in
    the last `RECENT`. What cannot be read counts as nothing."""
    places = {crew['name']: crew['cwd'] for crew in crews if crew.get('cwd') and role(crew.get('title') or crew['name'])}
    if not places:
        return {}
    root = root or Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude') / 'projects'
    try:
        if listing is None:
            listing = subprocess.run(['ps', '-axo', 'pid=,ppid=,args='], capture_output=True, text=True,
                                     check=True, timeout=PROBE).stdout
        running = commands(listing, cwd)
    except (OSError, ValueError, subprocess.SubprocessError):
        running = Counter()
    found = {}
    for name, place in places.items():
        subagents = 0
        for path in (root / re.sub(r'[^A-Za-z0-9]', '-', place)).glob('*/subagents/*.jsonl'):
            try:
                subagents += now.timestamp() - path.stat().st_mtime <= RECENT.total_seconds()
            except OSError:
                pass
        counts = {'subagents': subagents, 'commands': running[os.path.realpath(place)]}
        if any(counts.values()):
            found[name] = counts
    return found


def plural(count: int, noun: str) -> str:
    return f'{count} {noun}' + ('' if count == 1 else 's')


def snapshot(repo: str, github: dict, crews: list[dict], mode: str, now: datetime, running: dict | None = None) -> dict:
    """The document the dashboard page renders: GitHub state joined with the crews the session read from the host,
    and what runs for them (`activity`). An idle crew whose work runs is in a background run, named by the crew's own
    `Background:` line when the collector found one."""
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
        entry = {**crew, 'title': title, 'role': role(title), 'issue': issue, 'state': state,
                 'path': lineage(github['work'], issue),
                 'questions': questions(crew.get('ask'), crew.get('question')) if state == 'waiting' else []}
        entry.pop('ask', None)
        counts = (running or {}).get(crew['name'])
        if counts:
            entry['running'] = counts
            if state == 'idle' and not crew.get('background'):
                entry['background'] = (f"{plural(counts['subagents'], 'subagent')}, "
                                       f"{plural(counts['commands'], 'command')} running")
        joined.append(entry)
    return {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'mode': mode,
            'error': None, 'crews': joined, **github}


def waiting(document: dict) -> list[dict]:
    """What waits for the user: crews that asked them something, and PRs that wait for their yes to merge: those Orchi's
    notes ask about, or, without notes, with autonomous mode off, PRs into the default branch ready to merge."""
    items = [{'kind': 'question', 'crew': crew['name'], 'issue': crew.get('issue'), 'text': crew.get('question') or ''}
             for crew in document['crews'] if crew['state'] == 'waiting']
    asked = document.get('merges')
    items += [{'kind': 'merge', 'pull': pull['number'], 'text': pull['title']} for pull in document['pulls']
              if (pull['number'] in asked if asked is not None else document.get('mode') == 'off' and pull['into_default']
                  and not pull['draft'] and pull['checks'] in {'passing', 'none'})]
    return items


def board(document: dict) -> dict:
    """Each item's column on the board, from the real state; `pr-<n>` for a PR that closes no Issue shown.

    A Task, or any item without children, takes the first that holds: closed (`done`); a question for the user on it,
    from its crew or Orchi's notes (`questions`); a PR that waits for the user's yes (`review`); a PR, a claim, or a
    crew on it (`progress`); deferred (`backlog`); in the planning queue (`planning`); otherwise `backlog`. An Epic or
    Initiative takes the first column in `COLUMNS` that it or its children reach; one still open whose children are all
    closed is in its final check (`progress`).
    """
    work, planning, closed = document['work'], document['planning'], document.get('closed') or []
    asked = {item['pull'] for item in document.get('waiting') or [] if item['kind'] == 'merge'}
    review, pulled = set(), set()
    for pull in document['pulls']:
        pulled.update(pull['closes'])
        if pull['number'] in asked:
            review.update(pull['closes'])
    asks = {crew['issue'] for crew in document['crews'] if crew['state'] == 'waiting' and crew.get('issue')}
    for question in document.get('questions') or []:
        merge = MERGE.match(question['text'])
        if merge:
            review.update(next((pull['closes'] for pull in document['pulls'] if pull['number'] == int(merge[1])), []))
        else:
            asks.update(int(n) for n in REFERENCE.findall(question['text']))
    deferred, queued = set(document.get('deferred') or []), {item['number'] for item in planning}

    def own(item: dict) -> str:
        number = item['number']
        if item.get('status') == 'closed':
            return 'done'
        if number in asks:
            return 'questions'
        if number in review:
            return 'review'
        if number in pulled or item.get('status') == 'claimed' or item.get('crew'):
            return 'progress'
        if number in deferred:
            return 'backlog'
        return 'planning' if number in queued else 'backlog'

    items = work + planning + [{**item, 'status': 'closed'} for item in closed]
    children = {}
    for item in items:
        children.setdefault(item.get('parent'), []).append(item)
    columns: dict[str, str] = {}

    def place(item: dict, seen: frozenset) -> str:
        key = str(item['number'])
        if key in columns:
            return columns[key]
        kids = [place(child, seen | {item['number']}) for child in children.get(item['number'], [])
                if child['number'] not in seen]
        reached = [own(item)] + kids
        if item.get('status') != 'closed':
            reached = [column for column in reached if column != 'done']
            if kids and all(column == 'done' for column in kids):
                reached.append('progress')
        columns[key] = min(reached, key=COLUMNS.index)
        return columns[key]

    for item in items:
        place(item, frozenset())
    shown = set(columns)
    for pull in document['pulls']:
        if not any(str(number) in shown for number in pull['closes']):
            columns[f"pr-{pull['number']}"] = 'review' if pull['number'] in asked else 'progress'
    return columns


def moves(document: dict, previous: dict, now: datetime) -> list[dict]:
    """Each card's history, with a move for each card that changed column since the previous run (a page refresh or a
    stall check): at most `HISTORY` moves per card shown, newest last, a move from `review` back to `progress` marked
    `back`. Returns the moves since the last summary, which the next summary tells."""
    before, after = previous.get('columns') or {}, document['columns']
    history = {key: list(value) for key, value in (previous.get('history') or {}).items() if key in after}
    for key, column in after.items():
        if key in before and before[key] != column:
            move = {'from': before[key], 'to': column, 'at': now.isoformat(timespec='seconds'),
                    'back': before[key] == 'review' and column == 'progress'}
            history[key] = (history.get(key, []) + [move])[-HISTORY:]
    document['history'] = history
    told = moment(document.get('summary_at')) or now - timedelta(days=1)
    return sorted(({'card': key, **move} for key, entries in history.items() for move in entries
                   if (moment(move['at']) or now) > told), key=lambda move: move['at'])


def digest(document: dict, moved: list[dict], now: datetime) -> dict:
    """The facts the refresh writes its summary from: moves since the last refresh, today's merges, the cards per
    column, what waits for the user, and the crews that need a look."""
    titles = {str(item['number']): item.get('title') or '' for item in document['work'] + document['planning']
              + (document.get('closed') or [])}
    titles.update({f"pr-{pull['number']}": pull['title'] for pull in document['pulls']})
    def today(pull: dict) -> bool:
        merged = moment(pull.get('merged_at'))
        return bool(merged) and merged.astimezone(now.tzinfo).date() == now.date()

    return {'moved': [{**move, 'title': titles.get(move['card'], '')} for move in moved],
            'merged_today': [pull['title'] for pull in document['merged'] if today(pull)],
            'columns': {column: sum(value == column for value in document['columns'].values()) for column in COLUMNS},
            'waiting': len(document['waiting']), 'attention': [item['crew'] for item in document['attention']]}


def paragraphs(path: str) -> list[dict]:
    """The summary the refresh wrote: a JSON list of `{"lead", "text"}`, at most six, each part trimmed."""
    with open(path, encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError('the summary is not a list')
    found = []
    for item in data[:6]:
        if isinstance(item, dict) and isinstance(item.get('lead'), str) and isinstance(item.get('text', ''), str):
            found.append({'lead': item['lead'].strip()[:200], 'text': str(item.get('text') or '').strip()[:700]})
    return found


def moment(value) -> datetime | None:
    """An ISO time with its offset (`Z` included), or None when it is missing, unreadable, or has no offset."""
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError, TypeError):
        return None
    return parsed if parsed.tzinfo else None


def attention(document: dict, now: datetime, previous: dict, alive=None) -> list[dict]:
    """Crews that look stuck, from this refresh and the previous snapshot. The host shows only whether a turn runs,
    so a background run (`background`) is the crew's own line or what `activity` found running, and the run's start is
    carried from refresh to refresh.

    - `stalled`: holds an Issue, runs nothing, has no background run (named or found running), waits for no other
      Issue and no merge of its PR.
    - `long run`: its background run has gone on for hours.
    - `question`: in autonomous mode, its question to Orchi has waited (a `(user)` question waits for the user).
    - `run ended`: every command its background line, or an idle worker's (`worker_runs`), names by process id has
      ended, yet nothing woke anyone (a session restarted, which ends its runs without a wake); listed after `ENDED`.
    A worker's run whose named process still runs counts as a busy worker.
    Each other kind is listed once the crew has been quiet for `STALL`; `unanswered` once it stays quiet `ANSWER` after
    that.
    """
    waits = {item['number']: item.get('waits_for') for item in document['work'] + document['planning']}
    merging = {number for pull in document['pulls'] if not pull['draft'] for number in pull['closes']}
    seen = {(item.get('crew'), item.get('quiet')): item.get('first_seen') for item in previous.get('attention') or []}
    starts, document['background_since'] = previous.get('background_since') or {}, {}
    items = []
    for crew in document['crews']:
        name, quiet, run = crew['name'], moment(crew.get('last_activity')), crew.get('background')
        if run and crew['state'] == 'idle':
            start = starts.get(name) or {}
            document['background_since'][name] = {'text': run, 'since': start.get('since') if start.get('text') == run
                                                   else crew.get('last_activity')}
        runs = crew.get('worker_runs') or []
        dead = ([run] if crew['state'] == 'idle' and run and ended(run, alive) else []) + [
            line for line in runs if ended(line, alive)]
        busy = (crew.get('workers') or {}).get('busy', 0) > 0 or any(PIDS.search(line) and not ended(line, alive) for line in runs)
        if crew['role'] is None or not quiet or busy or now - quiet <= (ENDED if dead else STALL):
            continue
        issue, since, text = crew.get('issue'), crew['last_activity'], crew.get('stage') or ''
        if dead and crew['state'] == 'idle':
            kind, text = 'run ended', dead[0]
        elif run and crew['state'] == 'idle':
            since, text = document['background_since'][name]['since'], run
            kind = 'long run' if now - (moment(since) or quiet) > LONG_RUN else None
        elif crew['state'] == 'idle':
            kind = 'stalled' if issue and not waits.get(issue) and issue not in merging else None
        elif crew['state'] == 'waiting' and document.get('mode') == 'on' and '(user)' not in (crew.get('question') or ''):
            kind, text = 'question', crew.get('question') or ''
        else:
            kind = None
        if kind:
            first = moment(seen.get((name, crew['last_activity'])))
            items.append({'kind': kind, 'crew': name, 'issue': issue, 'text': text, 'since': since,
                          'quiet': crew['last_activity'],
                          'first_seen': first.isoformat(timespec='seconds') if first else now.isoformat(timespec='seconds'),
                          'unanswered': bool(first) and now - first >= ANSWER})
    return items


def summary(document: dict) -> str:
    """The line the refresh subagent replies with: the time of the refresh and the counts the user scans for."""
    time = document['updated'][11:16]
    if document.get('error'):
        return f'📊 {time} · refresh failed'
    # An idle crew runs nothing; it counts as active only while its workers or its background run go on.
    def counts(crew: dict) -> bool:
        if crew['role'] is None:
            return False
        if crew['state'] in {'working', 'waiting'}:
            return True
        return crew['state'] == 'idle' and ((crew.get('workers') or {}).get('busy', 0) > 0 or bool(
            crew.get('background') or crew.get('worker_runs')))
    active = sum(counts(crew) for crew in document['crews'])
    line = f"📊 {time} · {active} active · {len(document['waiting'])} wait for you · {len(document['pulls'])} PRs"
    look = len(document.get('attention') or [])
    return line + (f' · {look} need a look' if look else '')


def main(argv: list[str] | None = None, run: status.Runner = status.gh, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', help='OWNER/NAME; defaults to the current repository')
    parser.add_argument('--crews', help='JSON file with the crews read from the host')
    parser.add_argument('--mode', choices=('on', 'off'), help='Whether autonomous mode is on')
    parser.add_argument('--summary', help='Add this summary (a JSON list of {"lead", "text"}) to the snapshot in --out')
    parser.add_argument('--out', required=True, help='Where to write the snapshot JSON')
    parser.add_argument('--notes', help="Orchi's notes file, for its questions to the user and the deferred Issues")
    parser.add_argument('--limit', type=int, default=3, help='The pool size: how many crews may hold work at once')
    args = parser.parse_args(argv)
    if not args.summary and not (args.crews and args.mode):
        parser.error('--crews and --mode are required unless --summary is given')
    now = now or datetime.now().astimezone()
    try:
        with open(args.out, encoding='utf-8') as handle:
            previous = json.load(handle)
        previous = previous if isinstance(previous, dict) else {}
    except (OSError, ValueError):
        previous = {}
    if args.summary:
        try:
            previous['summary'] = paragraphs(args.summary)
        except (OSError, ValueError) as error:
            print(f'Orchi dashboard error: summary: {error}', file=sys.stderr)
            return 2
        previous['summary_at'] = now.isoformat(timespec='seconds')
        with open(args.out, 'w', encoding='utf-8') as handle:
            json.dump(previous, handle, ensure_ascii=False, indent=1)
        print(summary(previous) if previous.get('crews') is not None else 'summary added')
        return 0
    try:
        with open(args.crews, encoding='utf-8') as handle:
            crews = json.load(handle)
        repo = args.repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        document = snapshot(repo, collect(repo, run), crews, args.mode, now, activity(crews, now))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        detail = str(getattr(error, 'stderr', '') or error).strip()
        # The failure and its time, merged into the stored snapshot so the page keeps the last good state; the stall
        # check's memory is carried over for the next refresh.
        document = {'updated': now.isoformat(timespec='seconds'), 'error': detail,
                    'attention': previous.get('attention') or [], 'background_since': previous.get('background_since') or {},
                    **{key: previous[key] for key in ('summary', 'summary_at') if key in previous}}
        print(f'Orchi dashboard error: {detail}', file=sys.stderr)
    else:
        if args.notes:
            document.update(notes(args.notes))
        document['limit'] = args.limit
        document['waiting'] = waiting(document)
        document['attention'] = attention(document, now, previous)
        # The summary stays until the refresh writes the next one; it says when it was written.
        for key in ('summary', 'summary_at'):
            if key in previous:
                document[key] = previous[key]
        # The board's last columns and its history live beside the snapshot, so that a failed run, whose snapshot
        # goes onto the page's older data, never carries them, and a stall check between two refreshes loses none.
        state = os.path.join(os.path.dirname(os.path.abspath(args.out)), 'board.json')
        try:
            with open(state, encoding='utf-8') as handle:
                kept = json.load(handle)
            kept = kept if isinstance(kept, dict) else {}
        except (OSError, ValueError):
            kept = {key: previous.get(key) for key in ('columns', 'history')}
        document['columns'] = board(document)
        document['digest'] = digest(document, moves(document, kept, now), now)
        with open(state, 'w', encoding='utf-8') as handle:
            json.dump({'columns': document['columns'], 'history': document['history']}, handle, ensure_ascii=False)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(document, handle, ensure_ascii=False, indent=1)
    print(summary(document))
    return 2 if document['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
