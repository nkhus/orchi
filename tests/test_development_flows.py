"""Acceptance tests for the development protocol; not live-agent evaluations."""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import time

import pytest
from pydantic import ValidationError
from conftest import git
from orchi_core import authoring, context, views
from orchi_core.common import OrchiError, digest, sha
from orchi_core.models import Task, Policy, ChangeBrief, ScopeRule
from orchi_core.signing import sign


def start(world, mutate=None):
    world.begin()
    plan = world.plan1()
    if mutate:
        mutate(plan)
    world.approve(world.propose_plan(plan))
    return plan


def write(ticket, name, content):
    p = Path(ticket['workspace']) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def brief(kind='software'):
    return {'id': 'compact', 'request': 'Fix one existing module without changing its interface.',
            'outcome': 'The left value is one', 'result_kind': kind,
            'requirements': {'req-fix': 'Read the left value as one.'},
            'architecture': 'Retain existing module boundaries and public interfaces.',
            'design': 'Change the existing constant and verify its value.',
            'decisions': ['Keep the public variable'], 'invariants': ['No import side effects'],
            'checks': ['left'], 'tasks': [{'id': 'fix', 'goal': 'Set left to one',
                'edits': [{'path': 'src/left.py', 'action': 'modify', 'how': 'Set VALUE to one'}],
                'checks': ['left'], 'allowed_choices': ['Local helper structure']}]}


def scope(name='src/helper.py', action='create', change_kind='local'):
    return {'edit': {'path': name, 'action': action, 'how': 'Implement the allowed helper'},
            'choice': 'Local variable spelling', 'reason': 'A local helper keeps the accepted interface unchanged',
            'change_kind': change_kind}


def delegated(plan):
    plan['tasks'][0]['write_scope'] = [{'directory': 'src', 'actions': ['create', 'modify', 'delete'],
                                      'choices': ['Local variable spelling']}]


def test_compact_start_binds_target_and_first_plan_in_one_gate(world):
    req = world.e.begin_brief(brief())
    assert req['kind'] == 'direction' and req['inputs']['first_plan']['tasks']
    assert req['inputs']['preflight']['ok']
    view = views.gate(world.e)
    assert view
    world.approve(req)
    assert world.e.state()['phase'] == 'EXECUTING'
    ticket = world.e.claim('fix'); world.activate(ticket)
    write(ticket, 'src/left.py', 'VALUE = 1\n')
    assert world.e.submit(ticket['id'], {'status': 'completed', 'summary': 'Fixed the bounded behavior'})['status'] == 'integrated'
    assert world.e.state()['baseline'] == world.baseline
    assert context.get(world.e.repo, world.e.state(), 'docs/architecture.md', 'compact')['content'].endswith('zero.\n')


def test_compact_expansion_does_not_invent_decisions(world):
    b = brief()
    spec, bundle, plan, design = authoring.expand(b, world.baseline)
    assert bundle['documents']['source.md'] == b['request']
    assert b['architecture'] in bundle['documents']['architecture/README.md']
    assert plan['tasks'][0]['decisions'] == b['decisions']
    assert spec['delivery'] == 'atomic'
    with pytest.raises(ValidationError):
        ChangeBrief.model_validate({k: v for k, v in b.items() if k != 'design'})


def test_packet_preflight_blocks_known_oversize_before_approval(world):
    world.begin()
    p = world.plan1()
    p['tasks'][0]['approach'] = 'Bounded exact context ' * 12000
    with pytest.raises(OrchiError, match='packet|budget|context|CONTEXT',):
        world.propose_plan(p)
    assert world.e.state()['phase'] == 'PLANNING'
    assert world.e.state()['pending'] is None


def test_on_demand_sources_are_exact_but_not_inlined(world):
    def change(plan):
        plan['tasks'][0]['context'][0]['delivery'] = 'on-demand'
    start(world, change)
    ticket = world.e.claim('left')
    packet = world.e.store.get_artifact(ticket['packet_id'])
    source = next(s for s in packet['sources'] if s['target'] == 'src/left.py')
    assert source['delivery'] == 'on-demand' and 'content' not in source
    got = world.e.ticket_read(ticket['id'], 'src/left.py', content_hash=source['content_hash'])
    assert got['content'] == 'VALUE = 0\n'
    assert got['content_hash'] == source['content_hash'] and got['source_commit'] == ticket['start_commit']
    with pytest.raises(OrchiError) as err:
        world.e.ticket_read(ticket['id'], 'src/left.py', content_hash='0' * 64)
    assert err.value.code == 'KNOWLEDGE_CHANGED'
    with pytest.raises(OrchiError):
        world.e.ticket_read(ticket['id'], 'intent/requirements.md', view='code')
    target = world.e.ticket_read(ticket['id'], 'req-user', view='target')
    assert target['role'] == 'target'


def test_read_line_slice_hash_and_frozen_snapshot(world):
    start(world)
    ticket = world.e.claim('left')
    read = world.e.ticket_read(ticket['id'], 'docs/architecture.md', view='current', start_line=2, end_line=3)
    full = context.get(world.e.repo, world.e.state(), 'docs/architecture.md', 'feature')
    assert read['content'] == ''.join(full['content'].splitlines(keepends=True)[1:3])
    assert read['content_hash'] == sha(full['content'].encode())
    assert read['slice_hash'] == sha(read['content'].encode())
    assert world.e.state()['tickets'][ticket['id']]['read_events']
    with pytest.raises(OrchiError):
        world.e.ticket_read(ticket['id'], 'src/left.py', start_line=0)


def test_ownership_is_navigation_not_read_lock(world):
    def change(plan):
        plan['tasks'][1]['context'].append({'kind': 'knowledge', 'view': 'current', 'path': 'docs/architecture.md', 'reason': 'Understand adjacent component'})
    start(world, change)
    a = world.e.claim('left'); b = world.e.claim('right')
    assert 'src/left.py' not in b['reads']
    assert a['status'] == b['status'] == 'claimed'


def test_snapshot_read_drift_revalidates_but_does_not_reexecute_worker(world):
    def change(plan):
        plan['tasks'][1]['context'].append({'kind': 'code', 'path': 'src/left.py', 'reason': 'Observe adjacent implementation', 'consistency': 'snapshot'})
    start(world, change)
    a = world.e.claim('left'); b = world.e.claim('right')
    world.activate(a); world.activate(b)
    write(a, 'src/left.py', 'VALUE = 1\n'); write(b, 'src/right.py', 'VALUE = 2\n')
    assert world.e.submit(a['id'], {'status': 'completed', 'summary': 'Left done'})['status'] == 'integrated'
    result = world.e.submit(b['id'], {'status': 'completed', 'summary': 'Right done'})
    assert result['status'] == 'integrated'
    assert world.e.state()['active']['tasks']['right']['snapshot_revalidation'] == ['src/left.py']
    assert world.e.state()['attempts']['values/right'] == 1


def test_fixed_read_conflict_does_not_block_claim_but_fails_acceptance(world):
    def change(plan):
        plan['tasks'][1]['context'].append({'kind': 'code', 'path': 'src/left.py', 'reason': 'Exact compatibility assumption'})
    start(world, change)
    a = world.e.claim('left'); b = world.e.claim('right')
    world.activate(a); world.activate(b)
    write(a, 'src/left.py', 'VALUE = 1\n'); write(b, 'src/right.py', 'VALUE = 2\n')
    world.e.submit(a['id'], {'status': 'completed', 'summary': 'Left done'})
    with pytest.raises(OrchiError) as err:
        world.e.submit(b['id'], {'status': 'completed', 'summary': 'Right done'})
    assert err.value.code == 'STALE_READS'


def test_local_scope_grant_is_checked_and_audited(world):
    start(world, delegated)
    ticket = world.e.claim('left'); world.activate(ticket)
    grant = world.e.acquire_scope(ticket['id'], scope())
    assert grant['status'] == 'granted'
    write(ticket, 'src/left.py', 'VALUE = 1\n'); write(ticket, 'src/helper.py', 'HELPER = True\n')
    assert world.e.submit(ticket['id'], {'status': 'completed', 'summary': 'Implemented local helper'})['status'] == 'integrated'
    saved = world.e.state()['tickets'][ticket['id']]
    assert saved['scope_grants'] == [grant['grant']] and 'src/helper.py' in saved['writes']
    assert 'src/helper.py' in world.e.repo.files(world.e.state()['head'])


@pytest.mark.parametrize('scope_request,code', [
    (scope('other/helper.py'), 'SCOPE_NOT_DELEGATED'),
    (scope('src/right.py', 'modify'), 'SCOPE_CONFLICT'),
    (scope(change_kind='design'), 'AMEND_REQUIRED'),
    (scope(change_kind='target'), 'AMEND_REQUIRED'),
    (scope('docs/README.md', 'modify'), 'PROTECTED_PATH'),
])
def test_scope_never_converts_free_paths_into_semantic_permission(world, scope_request, code):
    start(world, delegated)
    ticket = world.e.claim('left')
    with pytest.raises(OrchiError) as err:
        world.e.acquire_scope(ticket['id'], scope_request)
    assert err.value.code == code


def test_scope_addition_budget(world):
    def change(plan):
        delegated(plan); plan['tasks'][0]['max_scope_additions'] = 0
    start(world, change)
    ticket = world.e.claim('left')
    with pytest.raises(OrchiError) as err:
        world.e.acquire_scope(ticket['id'], scope())
    assert err.value.code == 'SCOPE_BUDGET'


def test_parallel_checks_use_exact_cas_recomposition(world, monkeypatch):
    start(world)
    a = world.e.claim('left'); b = world.e.claim('right')
    world.activate(a); world.activate(b)
    write(a, 'src/left.py', 'VALUE = 1\n'); write(b, 'src/right.py', 'VALUE = 2\n')
    isolated_barrier = threading.Barrier(2)
    combined_barrier = threading.Barrier(2)
    original = world.e._checks
    lock = threading.Lock(); first_combined = 0
    def checks(commit, ids, kind):
        nonlocal first_combined
        assert world.e.state()['operation'] is None
        if kind == 'task':
            isolated_barrier.wait(timeout=30)
        if kind == 'combined':
            with lock:
                first_combined += 1; index = first_combined
            if index <= 2:
                combined_barrier.wait(timeout=30)
        return original(commit, ids, kind)
    monkeypatch.setattr(world.e, '_checks', checks)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(world.e.submit, t['id'], {'status': 'completed', 'summary': 'Independent task done'}) for t in (a,b)]
        results = [f.result(timeout=90) for f in futures]
    assert all(r['status'] == 'integrated' for r in results)
    assert sum(r['recompositions'] for r in results) >= 1
    assert first_combined >= 3
    assert world.e.state()['total_attempts'] == 2
    state = world.e.state()
    assert all(state['active']['tasks'][t]['status'] == 'integrated' for t in ('left', 'right'))
    assert all(any(at['disposition'] == 'accepted' for at in t['integration_attempts']) for t in state['tickets'].values())


def test_handoff_fences_old_ticket_and_preserves_importable_diff(world):
    start(world)
    old = world.e.claim('left'); world.activate(old)
    write(old, 'src/left.py', 'VALUE = 1\n')
    with pytest.raises(OrchiError):
        world.e.handoff(old['id'], False, 'Move to a person')
    result = world.e.handoff(old['id'], True, 'The agent stopped; a person will review and complete this change', 'human')
    new = result['ticket']
    assert new['executor'] == 'human' and new['id'] != old['id']
    assert (Path(new['workspace']) / 'src/left.py').read_text() == 'VALUE = 0\n'
    with pytest.raises(OrchiError):
        world.e.submit(old['id'], {'status': 'completed', 'summary': 'Late old result'})
    world.activate(new)
    imported = world.e.import_candidate(new['id'], result['handoff']['candidate'], result['handoff']['base'], 'Continue the preserved unverified diff')
    assert imported['status'] == 'imported'
    assert world.e.submit(new['id'], {'status': 'completed', 'summary': 'Person checked the bounded implementation'})['status'] == 'integrated'


def test_import_requires_readiness_and_exact_beforeimages(world):
    start(world)
    ticket = world.e.claim('left')
    candidate = world.e.repo.write(ticket['start_commit'], {'src/left.py': b'VALUE = 1\n'}, 'Existing developer branch')
    with pytest.raises(OrchiError):
        world.e.import_candidate(ticket['id'], candidate, ticket['start_commit'], 'Existing unapproved branch')
    world.activate(ticket)
    result = world.e.import_candidate(ticket['id'], candidate, ticket['start_commit'], 'Existing unapproved branch')
    assert result['paths'] == ['src/left.py']
    assert world.e.state()['active']['tasks']['left']['status'] == 'running'
    assert world.e.repo.read(world.e.state()['head'], 'src/left.py') == b'VALUE = 0\n'


def test_investigation_observations_do_not_become_current(world):
    def change(plan):
        task = plan['tasks'][0]
        task['kind'] = 'investigation'; task['edits'] = []
        task['verification'][0]['checks'] = ['baseline']
    start(world, change)
    ticket = world.e.claim('left'); world.activate(ticket)
    with pytest.raises(OrchiError) as err:
        world.e.submit(ticket['id'], {'status': 'completed', 'summary': 'Investigated'})
    assert err.value.code == 'OBSERVATIONS_REQUIRED'
    result = world.e.submit(ticket['id'], {'status': 'completed', 'summary': 'Investigated the reproduction',
                                         'observations': ['The baseline constant is zero; no product patch was attempted.'],
                                         'documentation_proposals': [{'target':'docs/architecture.md', 'content':'# Proposed update\nUnverified proposal.', 'reason':'For later review'}]})
    assert result['status'] == 'integrated'
    state = world.e.state()
    assert world.e.repo.read(state['head'], 'src/left.py') == b'VALUE = 0\n'
    assert 'zero' in context.get(world.e.repo, state, 'docs/architecture.md', 'feature')['content']
    assert any('/observations/' in p for p in world.e.repo.files(state['head']))
    assert state['knowledge'] == {}


def test_human_tasks_are_not_auto_claimed(world):
    def change(plan):
        for task in plan['tasks']: task['executor'] = 'human'
    start(world, change)
    with pytest.raises(OrchiError) as err:
        world.e.claim(executor_filter='agent')
    assert err.value.code == 'NO_READY_TASK'
    assert world.e.claim('left')['executor'] == 'human'


def test_targeted_amendment_keeps_unaffected_worker_fenced_to_same_contract(world):
    start(world)
    ticket = world.e.claim('left'); world.activate(ticket)
    plan = copy.deepcopy(world.e.state()['active']['plan'])
    plan['based_on'] = world.e.state()['head']
    plan['tasks'][1]['approach'] = 'Use the same public interface and explicitly verify the integer constant'
    plan['design']['path'] = 'design/2.md'
    design = world.e.repo.read(world.e.state()['active']['design_source']['source_commit'], world.e.state()['active']['design_source']['source_path']).decode()
    gate = world.e.amend_tasks(plan, design, ['right'], 'Clarify only the pending right-side implementation')
    write(ticket, 'src/left.py', 'VALUE = 1\n')
    result = world.e.submit(ticket['id'], {'status':'completed','summary':'Unchanged task completed during narrow approval'})
    assert result['status'] == 'validated'
    world.approve(gate)
    assert world.e.integrate(ticket['id'])['status'] == 'integrated'
    assert world.e.state()['active']['tasks']['right']['status'] == 'pending'
    assert world.e.state()['tickets'][ticket['id']]['epoch'] == world.e.state()['epoch']


def test_material_design_change_cannot_hide_in_task_amendment(world):
    start(world)
    plan = copy.deepcopy(world.e.state()['active']['plan']); plan['based_on'] = world.e.state()['head']
    plan['shared_design'] += ' Introduce a new service.'
    with pytest.raises(OrchiError) as err:
        world.e.amend_tasks(plan, 'Changed design', ['right'], 'Material change')
    assert err.value.code == 'FULL_AMENDMENT_REQUIRED'


def test_materialized_views_keep_roles_hashes_and_read_only_files(world, tmp_path):
    world.begin()
    out = tmp_path / 'read-only-view'
    result = views.materialize(world.e, out, 'all')
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest
    names = list(out.rglob('*.md'))
    assert names and any('target' in p.parts for p in names) and any('current' in p.parts for p in names)
    assert all(not (p.stat().st_mode & 0o222) for p in names)
    with pytest.raises(OrchiError):
        views.materialize(world.e, out, 'all')
    with pytest.raises(OrchiError):
        views.materialize(world.e, world.repo / 'generated', 'all')


def test_policy_requires_real_scope_checks_and_explicit_resource_coordination(world):
    with pytest.raises(OrchiError):
        Policy.model_validate({**world.policy, 'verification_strategy': 'scoped'})
    p = copy.deepcopy(world.policy); p['checks']['left']['resources'] = ['test-db']
    with pytest.raises(OrchiError):
        Policy.model_validate(p)
    p['resource_directory'] = str(world.root / 'resources')
    assert Policy.model_validate(p).checks['left'].resources == ['test-db']
