from pathlib import Path
import copy
import pytest
from orchi_core.common import OrchiError
from orchi_core.runner import run_ready


def test_checks_crash_requires_explicit_recovery(world,monkeypatch):
    world.begin();world.approve(world.propose_plan(world.plan1()));t=world.e.claim('left');world.activate(t)
    (Path(t['workspace'])/'src/left.py').write_text('VALUE = 1\n');old=world.e.state()['head']
    def crash(*a,**kw):raise RuntimeError('simulated process loss')
    monkeypatch.setattr(world.e,'_checks',crash)
    with pytest.raises(RuntimeError):world.e.submit(t['id'],{'status':'completed','summary':'candidate'})
    assert world.e.state()['operation'] is None and world.e.state()['head']==old
    assert world.e.state()['tickets'][t['id']]['status']=='checking'
    assert world.e.state()['tickets'][t['id']]['candidate']
    with pytest.raises(OrchiError):world.e.release(t['id'],False,'unknown')
    world.e.release(t['id'],True,'Operator confirmed this verifier/worker stopped')
    assert world.e.state()['head']==old and world.e.state()['attempts']['values/left']==1
    world.e.retry('left','Inspect prior candidate');retry=world.e.claim('left')
    assert world.e.store.get_artifact(retry['packet_id'])['previous_candidate']


def test_amendment_retains_attempts_and_fences_old_ticket(world):
    world.begin();world.approve(world.propose_plan(world.plan1()));t=world.e.claim('left')
    world.e.release(t['id'],True,'Stopped for approved design revision')
    plan=world.plan1();plan['tasks'][0]['approach']='A revised but compatible implementation approach'
    world.approve(world.amend_plan(plan,'Human accepted revised mechanism'))
    assert world.e.state()['attempts']['values/left']==1
    with pytest.raises(OrchiError):world.activate(t)
    new=world.e.claim('left');assert new['epoch']>t['epoch']
    assert world.e.state()['attempts']['values/left']==2


def test_roadmap_can_change_future_but_not_history(world):
    world.finish_first();spec=copy.deepcopy(world.spec);spec['epics'][1]['risks']=['Discovered integration constraint']
    world.approve(world.e.propose_roadmap(spec,'Learned from actual first epic'))
    assert world.e.state()['spec_revision']==2
    spec['epics'][0]['outcome']='Retcon completed work'
    with pytest.raises(OrchiError,check=lambda e:e.code=='HISTORY_REWRITE'):
        world.e.propose_roadmap(spec,'Disallowed history change')


def test_codex_missing_is_not_a_mock_success(world,monkeypatch):
    monkeypatch.setattr('orchi_core.runner.shutil.which',lambda _:None)
    with pytest.raises(OrchiError,check=lambda e:e.code=='CODEX_NOT_INSTALLED'):
        run_ready(world.e,{'kind':'codex'})


def test_final_cannot_skip_knowledge_or_acceptance(world):
    world.finish_first();world.finish_second();draft=world.final()
    with pytest.raises(OrchiError,check=lambda e:e.code=='UNRECONCILED_DRAFT'):world.e.finalize(draft)
    draft['report']='Cumulative review complete';draft['entries']=[]
    with pytest.raises(OrchiError):world.e.finalize(draft)
    draft=world.final();draft['report']='Cumulative review complete';draft['requirements'][0]['requirement_id']='req-not-original'
    with pytest.raises(OrchiError,check=lambda e:e.code=='INCOMPLETE_ACCEPTANCE'):world.e.finalize(draft)


def test_final_cannot_publish_before_final_review_and_human(world):
    world.finish_first();world.finish_second();draft=world.final();draft['report']='Cumulative review complete'
    final=world.e.finalize(draft)
    with pytest.raises(OrchiError,check=lambda e:e.code=='APPROVAL_REQUIRED'):world.e.publication()
    gate=world.pass_review('initiative')
    with pytest.raises(OrchiError,check=lambda e:e.code=='APPROVAL_REQUIRED'):world.e.record_publication(final['candidate'])
    world.approve(gate)
    with pytest.raises(OrchiError,check=lambda e:e.code=='PUBLICATION_NOT_VISIBLE'):world.e.record_publication(final['candidate'])


def test_knowledge_only_epic_is_a_real_supported_mode(world):
    spec=copy.deepcopy(world.spec);spec['epics']=[spec['epics'][0]]
    world.approve(world.e.begin(spec, world.bundle))
    plan=world.plan1();plan.update(mode='knowledge-only',tasks=[],acceptance_checks={'ac-values':['baseline']})
    world.approve(world.propose_plan(plan));assert world.e.next()['action']=='request_epic_review'
    world.pass_review();world.e.checkpoint({'epic_id':'values','based_on':world.e.state()['head'],
        'report':'Investigation confirms existing baseline semantics',
        'entries':[{'target':'docs/architecture.md','action':'revalidate','artifacts':['src/left.py'],'checks':['baseline'],'reason':'Read-only investigation'}],
        'dispositions':[]})
    assert world.e.state()['phase']=='FINALIZING'
