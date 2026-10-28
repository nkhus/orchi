"""The dashboard snapshot joins GitHub state with the crews and says what waits for the user."""
import json
from datetime import datetime, timezone

import dashboard
import status

NOW = datetime(2026, 10, 27, 15, 4, tzinfo=timezone.utc)


def labels(*names):
    return {'nodes': [{'name': name} for name in names]}


def epic(number, *children, extra=()):
    return {'number': number, 'title': f'[E{number}] Epic', 'url': f'https://example.invalid/{number}',
            'labels': labels('Epic', *extra), 'assignees': {'nodes': []}, 'parent': None,
            'subIssues': {'totalCount': len(children), 'nodes': [{'number': 90 + i, 'title': f'[E{number}] Task',
                                                                   'state': s} for i, s in enumerate(children)]},
            'blockedBy': {'nodes': []}}


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
    'planning': {'nodes': [{'number': 5, 'title': 'Hotel control center', 'url': 'https://example.invalid/5',
                            'labels': labels('Exploration')}]},
    'claimed': {'nodes': [{'number': 2, 'body': 'Work reference: Assigned to crew-2 (local_x) by Orchi on 2026-10-27'},
                          {'number': 5, 'body': 'Assigned to crew-1 (local_y) by Orchi'}]},
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
    issues = [epic(2, 'CLOSED', 'CLOSED', 'OPEN', extra=['in-progress']), epic(3)]
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
                                     'kind': 'Exploration', 'crew': 'crew-1'}]
    checks = {item['number']: (item['checks'], item['into_default']) for item in document['pulls']}
    assert checks == {10: ('passing', True), 11: ('passing', True), 12: ('passing', False), 13: ('failing', True)}
    assert document['merged'][0]['merged_at'] == '2026-10-27T10:00:00Z'


def test_crews_get_roles_and_claims_and_waiting_lists_questions_and_merges(tmp_path, capsys):
    crews = [{'name': 'crew-1', 'title': '[researcher] hotel', 'state': 'waiting', 'question': 'Which scale?'},
             {'name': 'crew-2', 'title': '[dev-lead] pay', 'state': 'working', 'workers': {'busy': 2, 'total': 3}},
             {'name': 'crew-3', 'title': 'crew-3'}]
    code, document = run(tmp_path, crews)
    roles = {crew['name']: (crew['role'], crew['issue'], crew['state']) for crew in document['crews']}
    assert roles == {'crew-1': ('Researcher', 5, 'waiting'), 'crew-2': ('Dev lead', 2, 'working'),
                     'crew-3': (None, None, 'free')}
    assert document['waiting'] == [{'kind': 'question', 'crew': 'crew-1', 'issue': 5, 'text': 'Which scale?'},
                                   {'kind': 'merge', 'pull': 10, 'text': 'PR 10'}]
    assert capsys.readouterr().out.strip() == '📊 15:04 · 2 active · 2 wait for you · 4 PRs'


def test_a_failure_keeps_only_its_time_and_reason(tmp_path, capsys):
    code, document = run(tmp_path, [], fail='gh: not logged in')
    assert code == 2 and document == {'updated': '2026-10-27T15:04:00+00:00', 'error': 'gh: not logged in'}
    assert capsys.readouterr().out.strip() == '📊 15:04 · refresh failed'
