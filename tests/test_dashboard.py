"""The dashboard snapshot joins GitHub state with the crews and says what waits for the user."""
import json
from datetime import datetime, timezone

import dashboard
import status

NOW = datetime(2026, 10, 27, 15, 4, tzinfo=timezone.utc)


def labels(*names):
    return {'nodes': [{'name': name} for name in names]}


def epic(number, *children, extra=(), parent=None):
    return {'number': number, 'title': f'[E{number}] Epic', 'url': f'https://example.invalid/{number}',
            'labels': labels('Epic', *extra), 'assignees': {'nodes': []},
            'parent': {'number': parent, 'title': '[INI] Payments'} if parent else None,
            'subIssues': {'totalCount': len(children), 'nodes': [{'number': 90 + i, 'title': f'[E{number}] Task',
                                                                   'state': s} for i, s in enumerate(children)]},
            'blockedBy': {'nodes': []}}


def task(number, state, *extra):
    return {'number': number, 'title': f'[E2] Task {number}', 'url': f'https://example.invalid/{number}',
            'state': state, 'labels': labels('Task', *extra)}


def pull(number, draft=False, base='main', rollup='SUCCESS'):
    return {'number': number, 'title': f'PR {number}', 'url': f'https://example.invalid/pull/{number}',
            'isDraft': draft, 'baseRefName': base, 'reviewDecision': None,
            'closingIssuesReferences': {'nodes': [{'number': 2}]},
            'commits': {'nodes': [{'commit': {'statusCheckRollup': {'state': rollup} if rollup else None}}]}}


REPOSITORY = {
    'defaultBranchRef': {'name': 'main'},
    'initiatives': {'nodes': [{'number': 1, 'title': '[INI] Payments', 'url': 'https://example.invalid/1',
                               'labels': labels('Initiative', 'in-progress'),
                               'subIssues': {'totalCount': 3, 'nodes': [{'state': 'CLOSED'}, {'state': 'OPEN'},
                                                                        {'state': 'OPEN'}]}}]},
    'epics': {'nodes': [{'number': 2, 'subIssues': {'nodes': [task(90, 'CLOSED'), task(92, 'OPEN', 'in-progress'),
                                                              task(93, 'OPEN')]}},
                        {'number': 99, 'subIssues': {'nodes': [task(98, 'OPEN')]}}]},
    'planning': {'nodes': [{'number': 5, 'title': 'Hotel control center', 'url': 'https://example.invalid/5',
                            'labels': labels('Exploration')}]},
    'claimed': {'nodes': [{'number': 2, 'body': 'Work reference: Assigned to crew-2 (local_x) by Orchi on 2026-10-27'},
                          {'number': 5, 'body': 'Assigned to crew-1 (local_y) by Orchi'},
                          {'number': 92, 'body': 'Assigned to crew-2 (local_x), worker-1, by Orchi'}]},
    'open': {'nodes': [pull(10), pull(11, draft=True), pull(12, base='epic/x'), pull(13, rollup='FAILURE')]},
    'merged': {'nodes': [{'number': 7, 'title': 'PR 7', 'url': 'u', 'mergedAt': '2026-10-27T10:00:00Z',
                          'baseRefName': 'main'}]},
}


def runner(args):
    if args[:2] == ['repo', 'view']:
        return json.dumps({'nameWithOwner': 'o/r'})
    query = next(arg for arg in args if arg.startswith('query='))
    if query == 'query=' + dashboard.QUERY:
        return json.dumps({'data': {'repository': REPOSITORY}})
    assert query == 'query=' + status.QUERY
    issues = [epic(2, 'CLOSED', 'CLOSED', 'OPEN', extra=['in-progress'], parent=1), epic(3)]
    return json.dumps({'data': {'repository': {'issues': {'pageInfo': {'hasNextPage': False}, 'nodes': issues}}}})


def run(tmp_path, crews, fail=None):
    (tmp_path / 'crews.json').write_text(json.dumps(crews))
    out = tmp_path / 'snapshot.json'

    def broken(args):
        raise OSError(fail)
    code = dashboard.main(['--crews', str(tmp_path / 'crews.json'), '--mode', 'off',
                           '--out', str(out)], run=broken if fail else runner, now=NOW)
    return code, json.loads(out.read_text())


def test_work_progress_claims_and_pull_checks(tmp_path):
    code, document = run(tmp_path, [])
    assert code == 0 and document['repository'] == 'o/r' and document['mode'] == 'off'
    work = {item['number']: item for item in document['work']}
    assert work[1]['kind'] == 'Initiative' and work[1]['progress'] == {'done': 1, 'total': 3}
    assert work[1]['status'] == 'claimed'
    assert work[2]['progress'] == {'done': 2, 'total': 3} and work[2]['crew'] == 'crew-2'
    assert work[3]['status'] == 'ready' and work[3]['crew'] is None
    assert document['planning'] == [{'number': 5, 'title': 'Hotel control center', 'url': 'https://example.invalid/5',
                                     'kind': 'Exploration', 'crew': 'crew-1', 'waits_for': None}]
    checks = {item['number']: (item['checks'], item['into_default']) for item in document['pulls']}
    assert checks == {10: ('passing', True), 11: ('passing', True), 12: ('passing', False), 13: ('failing', True)}
    assert document['merged'][0]['merged_at'] == '2026-10-27T10:00:00Z'


def test_crews_get_roles_and_claims_and_waiting_lists_questions_and_merges(tmp_path, capsys):
    crews = [{'name': 'crew-1', 'title': '[researcher] hotel', 'state': 'waiting', 'question': 'Which scale?'},
             {'name': 'crew-2', 'title': '[dev-lead] pay', 'state': 'working', 'workers': {'busy': 2, 'total': 3},
              'remote': True},
             {'name': 'crew-3', 'title': 'crew-3'},
             {'name': 'crew-4', 'title': '[planner] csv', 'state': 'idle', 'workers': {'busy': 0, 'total': 3}}]
    code, document = run(tmp_path, crews)
    roles = {crew['name']: (crew['role'], crew['issue'], crew['state']) for crew in document['crews']}
    assert roles == {'crew-1': ('Researcher', 5, 'waiting'), 'crew-2': ('Dev lead', 2, 'working'),
                     'crew-3': (None, None, 'free'), 'crew-4': ('Planner', None, 'idle')}
    assert document['crews'][1]['remote'] is True
    assert document['waiting'] == [{'kind': 'question', 'crew': 'crew-1', 'issue': 5, 'text': 'Which scale?'},
                                   {'kind': 'merge', 'pull': 10, 'text': 'PR 10'}]
    assert capsys.readouterr().out.strip() == '📊 15:04 · 2 active · 2 wait for you · 4 PRs'


def test_a_failure_keeps_only_its_time_and_reason(tmp_path, capsys):
    code, document = run(tmp_path, [], fail='gh: not logged in')
    assert code == 2 and document == {'updated': '2026-10-27T15:04:00+00:00', 'error': 'gh: not logged in',
                                      'attention': [], 'background_since': {}}
    assert capsys.readouterr().out.strip() == '📊 15:04 · refresh failed'


def test_work_is_a_tree_and_a_crew_knows_its_initiative_and_epic(tmp_path):
    crews = [{'name': 'crew-2', 'title': '[dev-lead] pay', 'state': 'working'}]
    code, document = run(tmp_path, crews)
    work = {item['number']: item for item in document['work']}
    assert work[2]['parent'] == 1
    assert (work[92]['kind'], work[92]['parent'], work[92]['status'], work[92]['crew']) == ('Task', 2, 'claimed', 'crew-2')
    assert (work[93]['status'], work[93]['crew']) == ('todo', None)
    assert 90 not in work and 98 not in work
    crew = document['crews'][0]
    assert (crew['issue'], crew['path']) == (2, [1])
    assert dashboard.lineage(document['work'], 92) == [1, 2] and dashboard.lineage(document['work'], 1) == []
    assert document['crews'][0]['state'] == 'working' and code == 0


def test_a_quiet_crew_on_its_work_or_an_hours_long_background_run_needs_a_look(tmp_path, capsys):
    from datetime import timedelta
    # Claims: crew-6 holds Epic 3; crew-7 holds Exploration 5, which waits for #2. PR 10 (ready) closes Epic 2.
    REPOSITORY['claimed']['nodes'].append({'number': 3, 'body': 'Assigned to crew-6 (local_z) by Orchi'})
    REPOSITORY['claimed']['nodes'][1]['body'] = 'Assigned to crew-7 (local_y) by Orchi, waits for #2'
    try:
        crews = [
            # Holds Epic 3, quiet 40 minutes, nothing running: stalled.
            {'name': 'crew-3', 'title': '[dev-lead] audit', 'state': 'idle', 'issue': 3, 'stage': 'Suites passed',
             'last_activity': '2026-10-27T14:24:00Z', 'workers': {'busy': 0, 'total': 3}},
            # Holds Epic 2, whose PR waits to merge: not stalled.
            {'name': 'crew-2', 'title': '[dev-lead] pay', 'state': 'idle', 'last_activity': '2026-10-27T12:00:00Z'},
            # A question to Orchi in autonomous mode is listed; this one is for the user, so it is not.
            {'name': 'crew-1', 'title': '[researcher] hotel', 'state': 'waiting', 'question': 'Which scale? (user)',
             'last_activity': '2026-10-27T10:00:00Z'},
            # A named run of 20 minutes on held work, and one of 4 hours.
            {'name': 'crew-5', 'title': '[planner] csv', 'state': 'idle', 'issue': 3, 'background': 'research subagents',
             'last_activity': '2026-10-27T14:44:00Z'},
            {'name': 'crew-6', 'title': '[dev-lead] audit', 'state': 'idle', 'background': 'visual suite, slot 0',
             'last_activity': '2026-10-27T11:04:00Z'},
            # Waits for #2; quiet only 10 minutes; a busy worker; an unreadable time.
            {'name': 'crew-7', 'title': '[researcher] hotel', 'state': 'idle', 'last_activity': '2026-10-27T12:00:00Z'},
            {'name': 'crew-8', 'title': '[dev-lead] x', 'state': 'idle', 'issue': 3, 'last_activity': '2026-10-27T14:54:00Z'},
            {'name': 'crew-9', 'title': '[dev-lead] y', 'state': 'idle', 'issue': 3, 'last_activity': '2026-10-27T12:00:00Z',
             'workers': {'busy': 1, 'total': 3}},
            {'name': 'crew-10', 'title': '[dev-lead] z', 'state': 'idle', 'issue': 3, 'last_activity': 1793000000},
            {'name': 'crew-11', 'title': '[dev-lead] w', 'state': 'idle', 'issue': 3, 'last_activity': '2026-10-27T12:00:00'}]

        def check(crews, now, mode='on'):
            (tmp_path / 'crews.json').write_text(json.dumps(crews))
            dashboard.main(['--crews', str(tmp_path / 'crews.json'), '--mode', mode, '--out', str(tmp_path / 'snapshot.json')],
                           run=runner, now=now)
            capsys.readouterr()
            return json.loads((tmp_path / 'snapshot.json').read_text())

        document = check(crews, NOW)
        looks = [(item['kind'], item['crew'], item['unanswered']) for item in document['attention']]
        assert looks == [('stalled', 'crew-3', False), ('long run', 'crew-6', False)]
        assert document['attention'][1]['text'] == 'visual suite, slot 0'
        assert dashboard.summary(document) == '📊 15:04 · 4 active · 2 wait for you · 4 PRs · 2 need a look'
        crews[2]['question'] = 'Which scale?'
        assert [item['kind'] for item in check(crews, NOW)['attention']] == ['stalled', 'question', 'long run']
        assert [item['kind'] for item in check(crews, NOW, mode='off')['attention']] == ['stalled', 'long run']
        # Two refreshes close together: not yet unanswered. Ten minutes on with no activity: unanswered.
        assert not any(item['unanswered'] for item in check(crews, NOW + timedelta(minutes=2))['attention'])
        # crew-6 answered `status?` with the same run: its run's start is kept, and it is not unanswered.
        crews[4]['last_activity'] = '2026-10-27T15:10:00Z'
        later = check(crews, NOW + timedelta(minutes=12))
        assert [(item['crew'], item['unanswered']) for item in later['attention']] == [('crew-3', True), ('crew-1', True)]
        assert later['background_since']['crew-6'] == {'text': 'visual suite, slot 0', 'since': '2026-10-27T11:04:00Z'}
        # A failed refresh keeps the check's memory for the next one.
        dashboard.main(['--crews', str(tmp_path / 'crews.json'), '--mode', 'on', '--out', str(tmp_path / 'snapshot.json')],
                       run=lambda args: (_ for _ in ()).throw(OSError('offline')), now=NOW + timedelta(minutes=13))
        failed = json.loads((tmp_path / 'snapshot.json').read_text())
        assert failed['error'] == 'offline' and failed['attention'] == later['attention']
        assert check(crews, NOW + timedelta(minutes=14))['attention'][0]['unanswered'] is True
    finally:
        REPOSITORY['claimed']['nodes'].pop()
        REPOSITORY['claimed']['nodes'][1]['body'] = 'Assigned to crew-1 (local_y) by Orchi'


# Running work, read from the host: two sessions' `claude` processes (71459 in CREW, 5654 in OTHER) and a terminal;
# crew-6's writer runs `make` from its own worktree in a tool shell (30491) that nests another (30495).
CREW, OTHER = '/work/repo/.claude/worktrees/rsh-9771c5', '/work/repo/.claude/worktrees/busy-jepsen-0f3bc8'
SNAPSHOT = '/bin/zsh -c source /home/u/.claude/shell-snapshots/snapshot-zsh-1.sh 2>/dev/null || true && eval'
LISTING = f'''\
71459     1 /Applications/Claude/claude
 5654     1 /Applications/Claude/claude
58448     1 /bin/zsh -l
30491 71459 {SNAPSHOT} 'make visual-test-linux'
30494 30491 /usr/bin/make visual-test-linux
30495 30491 {SNAPSHOT} 'tail -40'
29392  5654 {SNAPSHOT} 'sh .orchi-tmp/pw.sh'
'''
PLACES = {'71459': CREW, '5654': OTHER, '58448': CREW, '30491': CREW + '/../agent-a71ad'}


def directories(pids):
    return {pid: PLACES[pid] for pid in pids if pid in PLACES}


def transcript(root, cwd, name, minutes):
    from datetime import timedelta
    import os
    path = root / cwd.replace('/', '-').replace('.', '-') / 'f3d1-session' / 'subagents' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{}\n')
    stamp = (NOW - timedelta(minutes=minutes)).timestamp()
    os.utime(path, (stamp, stamp))


def idle(name='crew-6', cwd=CREW, **extra):
    return {'name': name, 'title': '[dev-lead] audit', 'state': 'idle', 'workers': {'busy': 0, 'total': 0},
            'last_activity': '2026-10-27T14:00:00Z', 'cwd': cwd, **extra}


def test_a_crews_running_subagents_and_commands_are_read_from_the_host(tmp_path):
    transcript(tmp_path, CREW, 'agent-a71ad.jsonl', 2)
    transcript(tmp_path, CREW, 'agent-a0994.jsonl', 9)
    transcript(tmp_path, CREW, 'agent-old.jsonl', 40)
    free = {**idle('crew-2'), 'title': 'crew-2'}
    found = dashboard.activity([idle(), idle('crew-4', OTHER), idle('crew-1', None), free], NOW, root=tmp_path,
                               listing=LISTING, cwd=directories)
    assert found == {'crew-6': {'subagents': 2, 'commands': 1}, 'crew-4': {'subagents': 0, 'commands': 1}}

    def broken(pids):
        raise OSError('lsof: not found')

    assert dashboard.activity([idle()], NOW, root=tmp_path, listing=LISTING, cwd=broken) == {
        'crew-6': {'subagents': 2, 'commands': 0}}
    assert dashboard.activity([idle()], NOW, root=tmp_path / 'missing', listing='', cwd=broken) == {}


def test_an_idle_crew_whose_work_runs_is_in_a_background_run_and_active_not_stalled():
    github = {'default_branch': 'main', 'planning': [], 'pulls': [], 'merged': [],
              'work': [{'number': 7, 'kind': 'Task', 'title': 'T', 'url': 'u', 'status': 'claimed', 'parent': None,
                        'crew': 'crew-6', 'progress': None, 'waits_for': None}]}

    def document(crews, running):
        doc = dashboard.snapshot('o/r', github, crews, 'on', NOW, running)
        doc['waiting'], doc['attention'] = dashboard.waiting(doc), dashboard.attention(doc, NOW, {})
        return doc

    doc = document([idle()], {'crew-6': {'subagents': 1, 'commands': 2}})
    assert doc['crews'][0]['background'] == '1 subagent, 2 commands running' and doc['attention'] == []
    assert dashboard.summary(doc) == '📊 15:04 · 1 active · 0 wait for you · 0 PRs'
    named = document([idle(background='the #1946 writer')], {'crew-6': {'subagents': 1, 'commands': 0}})['crews'][0]
    assert (named['background'], named['running']) == ('the #1946 writer', {'subagents': 1, 'commands': 0})
    doc = document([idle()], {})
    assert 'running' not in doc['crews'][0] and [item['kind'] for item in doc['attention']] == ['stalled']
    assert dashboard.summary(doc) == '📊 15:04 · 0 active · 0 wait for you · 0 PRs · 1 need a look'
