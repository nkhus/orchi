"""Moving-canonical and publication protocols on real local Git repositories."""
from __future__ import annotations
import copy
from pathlib import Path
import pytest
from conftest import git
from orchi_core import context, intent, publication, synchronization
from orchi_core.common import OrchiError, digest
from orchi_core.engine import Engine
from orchi_core.signing import sign


def upstream(world, changes):
    old = world.e.repo.resolve(world.e.policy.canonical_ref)
    new = world.e.repo.write(old, {k: (v.encode() if isinstance(v, str) else v) for k,v in changes.items()}, 'Independent upstream delivery')
    git(world.repo, 'update-ref', world.e.policy.canonical_ref, new, old)
    return new


def proposal(world):
    p = world.e.sync_draft()
    p['reason'] = 'Integrate the latest canonical delivery without losing initiative changes'
    p['target_assessment'] = 'Accepted target interfaces remain valid; no target decision changed'
    return p


def approve_sync(world, prepared):
    req = prepared['review_request']
    gate = world.e.sync_review({'request_id': req['id'], 'reviewer':'independent-sync-reviewer',
                'complete': True, 'covered_paths': req['required_paths'], 'findings': [],
                'summary':'Compared both code and knowledge snapshots and checked the target assessment'})
    return world.approve(gate)


def test_sync_disjoint_upstream_does_not_rewrite_origin_or_completed_history(world):
    world.finish_first()
    before = copy.deepcopy(world.e.state())
    new = upstream(world, {'src/upstream.py': 'UPSTREAM = True\n'})
    assert world.e.sync_status()['moved']
    p = proposal(world)
    assert not p['resolutions'] and not p['knowledge']
    result = world.e.synchronize(p)
    assert result['status'] == 'sync_review_required'
    pending = world.e.state()
    assert pending['head'] == before['head']
    assert pending['knowledge_head'] == before['knowledge_head']
    assert pending['integration_base'] == before['integration_base']
    approve_sync(world, result)
    after = world.e.state()
    assert after['baseline'] == before['baseline'] == world.baseline
    assert after['integration_base'] == new
    assert after['completed'] == before['completed']
    assert after['intent'] == before['intent']
    assert after['knowledge_head'] == after['head']
    assert world.e.repo.read(after['head'], 'src/upstream.py') == b'UPSTREAM = True\n'
    assert world.e.repo.read(after['head'], 'src/left.py') == b'VALUE = 1\n'
    assert context.get(world.e.repo, after, 'docs/architecture.md', 'feature')['content'].endswith('one.\n')
    assert after['sync_history'][0]['before']['head'] == before['head']
    world.finish_second()
    final = world.final(); final['report'] = 'The completed outcome retains the independent upstream delivery and checked knowledge'
    candidate = world.e.finalize(final)['candidate']
    assert world.e.repo.git('rev-list', '--parents', '-n', '1', candidate).decode().split()[1:] == [new]


def test_sync_requires_explicit_upstream_core_working_reconciliation(world):
    world.finish_first()
    upstream(world, {'docs/architecture.md': '---\nkind: component\nartifacts: [src/left.py]\n---\n# Architecture\nThe left value starts at zero. New upstream compatibility constraint.\n'})
    assert world.e.sync_status()['affected_knowledge'][0]['target'] == 'docs/architecture.md'
    p = proposal(world)
    with pytest.raises(OrchiError) as err:
        world.e.synchronize({**p, 'knowledge': []})
    assert err.value.code == 'INCOMPLETE_SYNC_KNOWLEDGE'
    p['knowledge'] = [{'target':'docs/architecture.md','action':'revalidate', 'reason':'Old text still valid', 'checks':['left']}]
    with pytest.raises(OrchiError) as err:
        world.e.synchronize(p)
    assert err.value.code == 'UPSTREAM_DOC_MASK'
    p['knowledge'] = [{'target':'docs/architecture.md','action':'update',
        'reason':'Preserve the upstream compatibility constraint while documenting the verified value',
        'content':'---\nkind: component\n---\n# Architecture\nThe left value is one. New upstream compatibility constraint.\n',
        'artifacts':['src/left.py'],'checks':['left']}]
    checked = world.e.synchronize(p)
    assert 'compatibility constraint' not in context.get(world.e.repo, world.e.state(), 'docs/architecture.md','feature')['content']
    approve_sync(world, checked)
    assert 'one. New upstream compatibility constraint' in context.get(world.e.repo, world.e.state(), 'docs/architecture.md','feature')['content']


def test_new_upstream_core_owning_local_changes_is_not_blindly_inherited(world):
    world.finish_first()
    upstream(world, {'docs/new.md': '---\nkind: component\nartifacts: [src/right.py]\n---\n# Right value\nThe right value is zero.\n',
                    'docs/README.md': '---\nkind: index\n---\n# Documentation\n[Architecture](architecture.md)\n[Right](new.md)\n'})
    p = proposal(world)
    assert [d['target'] for d in p['knowledge']] == ['docs/new.md']
    with pytest.raises(OrchiError) as err:
        world.e.synchronize({**p, 'knowledge': []})
    assert err.value.code == 'INCOMPLETE_SYNC_KNOWLEDGE'
    p['knowledge'] = [{'target':'docs/new.md','action':'update','content':'---\nkind: component\n---\n# Right\nThe verified right value is two.\n',
                       'artifacts':['src/right.py'],'checks':['right'],'reason':'Reconcile newly inherited Core with local accepted implementation'}]
    approve_sync(world, world.e.synchronize(p))
    current = context.get(world.e.repo, world.e.state(), 'docs/new.md','feature')
    assert 'two' in current['content'] and current['role'] == 'current'


def test_sync_textual_conflict_requires_exact_reviewed_resolution(world):
    world.finish_first()
    upstream(world, {'src/left.py':'VALUE = 4\n'})
    p = proposal(world)
    assert p['resolutions'][0]['path'] == 'src/left.py'
    with pytest.raises(OrchiError) as err:
        world.e.synchronize({**p,'resolutions':[]})
    assert err.value.code == 'INCOMPLETE_SYNC_RESOLUTION'
    p['resolutions'] = [{'path':'src/left.py','action':'replace','content':'VALUE = 1\n# Includes the acknowledged upstream compatibility review\n',
                         'reason':'Keep the accepted requirement value; reviewer explicitly assesses the upstream difference'}]
    p['knowledge'] = [{'target':'docs/architecture.md','action':'revalidate','reason':'The merged constant remains one', 'checks':['left']}]
    approve_sync(world, world.e.synchronize(p))
    assert world.e.repo.read(world.e.state()['head'],'src/left.py').startswith(b'VALUE = 1')


def test_sync_failed_checks_never_promote_code_or_knowledge(world):
    world.finish_first()
    before = copy.deepcopy(world.e.state())
    upstream(world, {'src/left.py':'VALUE = 4\n'})
    p = proposal(world)
    p['resolutions'] = [{'path':'src/left.py','action':'replace','content':'VALUE = 4\n','reason':'Candidate intentionally exercises failed validation'}]
    p['knowledge'] = [{'target':'docs/architecture.md','action':'revalidate','reason':'Requires a fresh check','checks':['left']}]
    result = world.e.synchronize(p)
    assert result['status'] == 'blocked'
    after = world.e.state()
    for key in ['head','baseline','integration_base','knowledge_head','knowledge','knowledge_revision']:
        assert after[key] == before[key]
    assert after['operation'] is None


def test_sync_gate_fails_if_upstream_moves_again(world):
    world.begin()
    upstream(world, {'src/upstream.py':'UPSTREAM = 1\n'})
    prepared = world.e.synchronize(proposal(world)); req = prepared['review_request']
    gate = world.e.sync_review({'request_id':req['id'],'reviewer':'reviewer','complete':True,'covered_paths':req['required_paths'],
                               'findings':[],'summary':'Checked exact sync candidate'})
    upstream(world, {'src/upstream.py':'UPSTREAM = 2\n'})
    with pytest.raises(OrchiError) as err:
        world.approve(gate)
    assert err.value.code == 'STALE_UPSTREAM'
    world.e.withdraw_gate('Upstream moved after review')
    result = synchronization.discard(world.e, 'Prepare a new snapshot')
    assert result['phase'] == 'PLANNING' and world.e.state()['integration_base'] == world.baseline


def test_sync_not_allowed_with_active_epic(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    upstream(world, {'src/upstream.py':'UPSTREAM = 1\n'})
    with pytest.raises(OrchiError) as err:
        world.e.synchronize(proposal(world))
    assert err.value.code == 'SYNC_BOUNDARY_REQUIRED'


def test_sync_rejects_rewritten_canonical_history(world):
    world.begin()
    first = upstream(world, {'src/upstream.py':'UPSTREAM = 1\n'})
    approve_sync(world, world.e.synchronize(proposal(world)))
    git(world.repo,'update-ref','refs/heads/main',world.baseline,first)
    with pytest.raises(OrchiError) as err:
        world.e.synchronize(proposal(world))
    assert err.value.code == 'UPSTREAM_REWRITE'


def test_sync_target_impact_explicitly_blocks_future_design(world):
    world.begin()
    upstream(world, {'src/upstream.py':'UPSTREAM = 1\n'})
    p = proposal(world); p['target_revision_required'] = True
    p['target_assessment'] = 'A future interface assumption requires an explicit accepted Intent revision'
    approve_sync(world, world.e.synchronize(p))
    assert world.e.next()['action'] == 'revise_intent_after_sync'
    with pytest.raises(OrchiError) as err:
        world.propose_plan(world.plan1())
    assert err.value.code == 'INTENT_REVISION_REQUIRED'


def test_sync_invalidates_previous_final_review_and_signature(world):
    world.finish_first(); world.finish_second()
    final = world.final(); final['report'] = 'Reconciled exact completed feature'
    world.e.finalize(final)
    world.approve(world.pass_review('initiative'))
    assert world.e.state()['phase'] == 'READY_TO_PUBLISH'
    old = world.e.state()['final']
    upstream(world, {'src/upstream.py':'UPSTREAM = 1\n'})
    with pytest.raises(OrchiError) as err:
        world.e.publication()
    assert err.value.code == 'CANONICAL_MOVED'
    approve_sync(world, world.e.synchronize(proposal(world)))
    state = world.e.state()
    assert state['phase'] == 'FINALIZING' and state['final'] is None
    assert state['final_history'][0]['final'] == old
    assert '@initiative' not in state['reviews']


def completed_compact(world, name, path, check, value, control):
    """A complete atomic patch on a shared repository, no architecture redesign."""
    policy = copy.deepcopy(world.policy); policy['final_checks'] = [check]
    e = Engine.setup(control, world.repo, policy)
    from test_development_flows import brief
    b = brief(); b['id'] = name; b['checks'] = [check]
    b['outcome'] = 'Set the requested constant to ' + str(value)
    b['tasks'][0]['edits'][0]['path'] = path; b['tasks'][0]['checks'] = [check]
    b['requirements'] = {'req-fix':'The requested constant is ' + str(value)}
    e.approve(sign(e.begin_brief(b), world.key, 'approve', 'operator'))
    t = e.claim('fix'); packet = e.store.get_artifact(t['packet_id'])
    e.activate(t['id'], {'packet_fingerprint':packet['fingerprint'],'understood_goal':packet['task']['goal'],
                        'fixed_decisions':packet['task']['decisions'],'acceptance_ids':list(packet['task']['acceptance']),'questions':[]})
    (Path(t['workspace']) / path).write_text(f'VALUE = {value}\n')
    assert e.submit(t['id'],{'status':'completed','summary':'The requested constant is checked'})['status'] == 'integrated'
    request = e.review_request()
    e.record_review({'request_id':request['id'],'reviewer':'reviewer','complete':True,'covered_paths':request['required_paths'],'findings':[],'summary':'Checked the exact change'})
    target = 'docs/architecture.md' if path == 'src/left.py' else 'docs/right.md'
    e.checkpoint({'epic_id':'delivery','based_on':e.state()['head'],'report':'Verified the bounded public behavior',
        'entries':[{'target':target,'action':'replace','content':f'---\nkind: component\n---\n# Value\nThe {path} value is {value}.\n',
                    'artifacts':[path],'checks':[check],'reason':'Document actual verified value'}],
        'dispositions':[{'path':path,'targets':[target],'reason':'Document the accepted result'}]})
    return e


def finalize_compact(e, key):
    p = e.final_draft(); p['report'] = 'Checked the entire accepted atomic result and retained module boundaries'
    for r in p['requirements']:
        r.update(disposition='satisfied',reason='The exact candidate checks establish the requested constant',checks=e.policy.final_checks,core_targets=[])
    for a in p['architecture']:
        a.update(disposition='unchanged',reason='The existing plain module boundaries are unchanged',artifacts=['src/left.py','src/right.py'],checks=e.policy.final_checks)
    result = e.finalize(p); assert result['status'] == 'final_review_required'
    req = e.review_request('initiative')
    gate = e.record_review({'request_id':req['id'],'reviewer':'reviewer','complete':True,'covered_paths':req['required_paths'],'findings':[],'summary':'Verified the atomic final candidate'})
    e.approve(sign(gate,key,'approve','operator'))
    return e.state()['final']['commit']


def test_two_independent_initiatives_publish_after_explicit_upstream_sync(world):
    a = completed_compact(world, 'change-a', 'src/left.py', 'left', 1, world.root/'control-a')
    b = completed_compact(world, 'change-b', 'src/right.py', 'right', 2, world.root/'control-b')
    assert a.state()['baseline'] == b.state()['baseline']
    assert a.state()['controller_id'] != b.state()['controller_id']
    commit_a = finalize_compact(a, world.key)
    git(world.repo,'update-ref','refs/heads/main',commit_a,world.baseline)
    a.record_publication(commit_a)
    world.e = b
    checked = b.synchronize(proposal(world)); approve_sync(world,checked)
    assert b.state()['integration_base'] == commit_a
    commit_b = finalize_compact(b,world.key)
    git(world.repo,'update-ref','refs/heads/main',commit_b,commit_a)
    b.record_publication(commit_b)
    assert a.state()['phase'] == b.state()['phase'] == 'PUBLISHED'
    assert b.repo.read(commit_b,'src/left.py') == b'VALUE = 1\n'
    assert b.repo.read(commit_b,'src/right.py') == b'VALUE = 2\n'
    assert any(p.startswith('initiatives/archive/change-a/') for p in b.repo.files(commit_b))
    assert any(p.startswith('initiatives/archive/change-b/') for p in b.repo.files(commit_b))


@pytest.mark.parametrize('mode',['exact','squash','merge'])
def test_publication_policy_checks_exact_tree_and_approved_parents(world, mode):
    e = completed_compact(world, 'publish-'+mode, 'src/left.py','left',1, world.root/('control-'+mode))
    # Policy is operator-owned and immutable after setup in ordinary use. Set the mode
    # before the final approval in this fixture, exactly as a separately initialized policy.
    from orchi_core.models import Policy
    with e.store.transaction('test.operator.policy') as s:
        s['policy']['publication_mode'] = mode
    e = Engine(e.store.root)
    candidate = finalize_compact(e,world.key)
    base = e.state()['integration_base']
    if mode == 'exact':
        published = candidate
    elif mode == 'squash':
        published = e.repo.commit(e.repo.tree(candidate),base,'Operator squash message')
    else:
        published = e.repo.git('commit-tree',e.repo.tree(candidate),'-p',base,'-p',candidate,data=b'Operator merge\n').decode().strip()
    git(world.repo,'update-ref','refs/heads/main',published,base)
    later = e.repo.write(published,{'src/later.py':b'LATER = True\n'},'Later accepted change')
    git(world.repo,'update-ref','refs/heads/main',later,published)
    result = e.record_publication(published)
    assert result['status'] == 'published' and result['observed_canonical'] == later
    assert result['deployment'] == 'not-implied'


def test_local_publication_refuses_checked_out_main_and_uses_cas(world):
    e = completed_compact(world,'local-publish','src/left.py','left',1,world.root/'control-local')
    candidate = finalize_compact(e,world.key)
    with pytest.raises(OrchiError) as err:
        publication.publish_local(e)
    assert err.value.code == 'TARGET_CHECKED_OUT'
    git(world.repo,'checkout','--detach')
    result = publication.publish_local(e)
    assert result['commit'] == candidate and e.repo.resolve('refs/heads/main') == candidate


def test_wrong_tree_never_accepted_as_publication(world):
    e = completed_compact(world,'wrong-tree','src/left.py','left',1,world.root/'control-wrong')
    candidate = finalize_compact(e,world.key)
    changed = e.repo.write(candidate,{'src/surprise.py':b'SURPRISE = True\n'},'Unapproved additional code')
    forged = e.repo.commit(e.repo.tree(changed),e.state()['integration_base'],'Unapproved result')
    git(world.repo,'update-ref','refs/heads/main',forged,e.state()['integration_base'])
    with pytest.raises(OrchiError) as err:
        e.record_publication(forged)
    assert err.value.code == 'WRONG_PUBLISHED_TREE'
