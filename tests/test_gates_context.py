import copy
from pathlib import Path
import pytest
from orchi_core import context
from orchi_core.common import OrchiError
from orchi_core.signing import sign, keygen


def test_forged_approval_does_not_transition(world):
    req=world.e.begin(world.spec, world.bundle); other=world.root/'other.pem'; keygen(other)
    with pytest.raises(OrchiError, check=lambda e: e.code=='BAD_SIGNATURE'): world.e.approve(sign(req,other,'approve','outsider'))
    assert world.e.state()['phase']=='AWAITING_APPROVAL'


def test_replay_approval_rejected(world):
    req=world.e.begin(world.spec, world.bundle); decision=sign(req,world.key,'approve','operator'); world.e.approve(decision)
    with pytest.raises(OrchiError, check=lambda e: e.code=='NO_APPROVAL_PENDING'): world.e.approve(decision)


def test_refreshed_gate_invalidates_old_signature(world):
    req=world.e.begin(world.spec, world.bundle); decision=sign(req,world.key,'approve','operator'); world.e.refresh_gate()
    with pytest.raises(OrchiError, check=lambda e: e.code=='STALE_APPROVAL'): world.e.approve(decision)


def test_rejection_does_not_start_workers(world):
    req=world.e.begin(world.spec, world.bundle); world.e.approve(sign(req,world.key,'reject','operator'))
    assert world.e.next()['action']=='define_initiative'


def test_no_readiness_no_submission(world):
    world.begin(); world.approve(world.propose_plan(world.plan1())); t=world.e.claim('left')
    with pytest.raises(OrchiError): world.e.submit(t['id'],{'status':'completed','summary':'claimed done'})


def test_readiness_wrong_fingerprint(world):
    world.begin(); world.approve(world.propose_plan(world.plan1())); t=world.e.claim('left')
    with pytest.raises(OrchiError): world.e.activate(t['id'],{'packet_fingerprint':'0'*64,'understood_goal':'left','fixed_decisions':['Preserve the module interface'],'acceptance_ids':['ac-left'],'questions':[]})


def test_required_packet_not_truncated(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    with world.e.store.transaction('test.policy.limit') as s: s['policy']['max_packet_bytes']=1024
    with pytest.raises(OrchiError, check=lambda e: e.code=='CONTEXT_TOO_LARGE'): world.e.claim('left')
    assert not world.e.state()['tickets']


def test_working_replaces_core_only_in_explicit_scope(world):
    world.finish_first(); s=world.e.state()
    canonical=context.get(world.e.repo,s,'docs/architecture.md')
    working=context.get(world.e.repo,s,'docs/architecture.md','feature')
    assert 'zero' in canonical['content'] and canonical['layer']=='canonical'
    assert 'one' in working['content'] and working['layer']=='working'
    assert context.search(world.e.repo,s,'one')['results']==[]
    assert len(context.owners(world.e.repo,s,'src/left.py','feature')['owners'])==1
    with pytest.raises(OrchiError, check=lambda e: e.code=='INITIATIVE_SCOPE'): context.get(world.e.repo,s,'docs/architecture.md','other')


def test_partial_epic_does_not_relabel_working_state(world):
    world.finish_first(); s=world.e.state(); kh=s['knowledge_head']
    # An unaccepted working tree edit has no authority over the checkpoint.
    Path(world.repo/'docs/architecture.md').write_text('An unverified proposed rewrite')
    assert context.get(world.e.repo,world.e.state(),'docs/architecture.md','feature')['source_commit']==kh


def test_known_stale_overlay_never_falls_back(world):
    world.finish_first()
    with world.e.store.transaction('test.artifact.drift') as s:
        s['knowledge_head']=world.e.repo.write(s['head'],{'src/left.py':b'VALUE = 9\n'},'fixture drift')
    with pytest.raises(OrchiError, check=lambda e: e.code=='STALE_WORKING_KNOWLEDGE'): context.get(world.e.repo,world.e.state(),'docs/architecture.md','feature')
    assert context.search(world.e.repo,world.e.state(),'Architecture','feature')['diagnostics']


def test_retirement_masks_baseline(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    world.perform('left',{'src/left.py':'VALUE = 1\n'}); world.perform('right',{'src/right.py':'VALUE = 2\n'}); world.pass_review()
    cp=world.checkpoint1(); cp['entries'][0].update(action='retire',content=None); world.e.checkpoint(cp)
    with pytest.raises(OrchiError, check=lambda e: e.code=='RETIRED_KNOWLEDGE'): context.get(world.e.repo,world.e.state(),'docs/architecture.md','feature')
    assert 'zero' in context.get(world.e.repo,world.e.state(),'docs/architecture.md')['content']
