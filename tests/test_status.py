"""Readiness classification and pagination of the read-only status overview."""
import json

from status import classify, main, render, report


def blocker(number, state='CLOSED', reason='COMPLETED', merged=None):
    prs = [{'number': 100 + number, 'merged': True, 'baseRefName': merged}] if merged else []
    return {'number': number, 'title': f'Blocker {number}', 'state': state, 'stateReason': reason,
            'closedByPullRequestsReferences': {'nodes': prs}}


def issue(number, label='Epic', labels=(), blockers=(), parent=None, owners=(), children=()):
    return {'number': number, 'title': f'{label} {number}', 'url': f'https://example.invalid/{number}',
            'labels': {'nodes': [{'name': name} for name in (label, *labels)]},
            'assignees': {'nodes': [{'login': login} for login in owners]},
            'parent': {'number': parent, 'title': 'Parent'} if parent else None,
            'subIssues': {'totalCount': len(children), 'nodes': [{'state': state} for state in children]},
            'blockedBy': {'nodes': list(blockers)}}


def test_readiness_states():
    assert classify(issue(1))['status'] == 'ready'
    assert classify(issue(2, blockers=[blocker(9, merged='initiative/x')]))['status'] == 'ready'
    assert classify(issue(3, blockers=[blocker(9)]))['status'] == 'check'
    assert classify(issue(4, blockers=[blocker(9, state='OPEN', reason=None)]))['status'] == 'blocked'
    assert classify(issue(5, blockers=[blocker(9, reason='NOT_PLANNED', merged='main')]))['status'] == 'blocked'
    assert classify(issue(6, labels=['in progress'], blockers=[blocker(9, state='OPEN')]))['status'] == 'claimed'
    assert classify(issue(7, labels=['In-Progress']))['status'] == 'claimed'


def test_only_standalone_tasks_are_entry_points():
    assert classify(issue(1, label='Task', parent=5)) is None
    entry = classify(issue(2, label='Task'))
    assert entry['kind'] == 'Task' and entry['tasks'] is None
    epic = classify(issue(3, parent=8, owners=['dev'], children=['CLOSED', 'OPEN']))
    assert epic['tasks'] == {'closed': 1, 'total': 2} and epic['parent'] == 8 and epic['owners'] == ['dev']


def test_report_orders_by_readiness_and_renders_blockers():
    entries = report([issue(1, labels=['in-progress']), issue(2, blockers=[blocker(9, state='OPEN')]), issue(3)])
    assert [entry['number'] for entry in entries] == [3, 2, 1]
    text = render(entries)
    assert 'ready    Epic #3' in text and 'blocked by #9: open' in text
    assert render([]) == 'No open Epics or standalone Tasks.'


def test_cli_paginates_and_resolves_repository(capsys):
    pages = [{'hasNextPage': True, 'endCursor': 'c1', 'nodes': [issue(1)]},
             {'hasNextPage': False, 'endCursor': None, 'nodes': [issue(2, label='Task')]}]
    calls = []

    def run(args):
        calls.append(args)
        if args[:2] == ['repo', 'view']:
            return json.dumps({'nameWithOwner': 'owner/name'})
        page = pages[len(calls) - 2]
        return json.dumps({'data': {'repository': {'issues': {
            'pageInfo': {'hasNextPage': page['hasNextPage'], 'endCursor': page['endCursor']}, 'nodes': page['nodes']}}}})

    assert main(['--json'], run) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['repository'] == 'owner/name'
    assert [entry['number'] for entry in output['entries']] == [1, 2]
    assert 'cursor=c1' in calls[2]


def test_cli_reports_errors(capsys):
    assert main(['--repo', 'not-a-repo'], lambda args: '') == 2
    assert 'OWNER/NAME' in capsys.readouterr().err
