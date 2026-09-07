import copy
from pathlib import Path
import pytest
from orchi_core.common import OrchiError


def ready(w):
    w.begin(); w.approve(w.e.plan(w.plan1()))
    w.perform('left',{'src/left.py':'VALUE = 1\n'}); w.perform('right',{'src/right.py':'VALUE = 2\n'})


def finding():
    return {'path':'src/left.py','criterion':'ac-left','root_cause':'A concrete path is not covered','consequence':'Required behavior can fail','evidence':'Reproduction with exact inputs; synthetic fixture only','disposition':'blocker','task_ids':['left']}


def report(req,fs):
    return {'request_id':req['id'],'reviewer':'synthetic-reviewer','complete':True,'covered_paths':req['required_paths'],'findings':fs,'summary':'Exact scoped review'}


def test_no_findings_finishes_without_repairs(world):
    ready(world); req=world.e.review_request(); assert req['mode']=='full'
    r=world.e.record_review(report(req,[])); assert r['status']=='passed'; assert world.e.next()['action']=='checkpoint_epic'
    with pytest.raises(OrchiError): world.e.review_request()


def test_reviews_are_bounded_and_zero_duplicate_bug_hunt(world):
    ready(world)
    for i in range(3):
        req=world.e.review_request(); assert req['round']==i+1; assert req['mode']==('full' if i==0 else 'targeted')
        r=world.e.record_review(report(req,[finding(),finding()]))
        assert len(world.e.state()['reviews']['values']['findings'])==1
        if i<2:
            world.e.repair(); t=world.e.claim('left'); p=world.activate(t)
            assert p['repair_findings']
            # Deliberately leaves synthetic reviewer issue unresolved; tests alone don't grant PASS.
            (Path(t["workspace"])/"src/left.py").write_text("VALUE = 1\n# repair round " + str(i) + "\n")
            world.e.submit(t['id'],{'status':'completed','summary':'Candidate still returns expected value'})
        else:
            assert r['status']=='blocked'; assert world.e.state()['phase']=='PAUSED'
    assert world.e.state()['attempts']['values/left']==3


def test_old_blocker_cannot_disappear(world):
    ready(world); req=world.e.review_request(); world.e.record_review(report(req,[finding()])); world.e.repair()
    t=world.e.claim('left'); world.activate(t); (Path(t['workspace'])/'src/left.py').write_text('VALUE = 1\n# targeted repair\n'); world.e.submit(t['id'],{'status':'completed','summary':'Retested'})
    req=world.e.review_request()
    with pytest.raises(OrchiError, check=lambda e: e.code=='FINDING_DROPPED'): world.e.record_review(report(req,[]))
    resolved=finding(); resolved['disposition']='resolved'; resolved['evidence']='Exact reproduction now passes'
    assert world.e.record_review(report(req,[resolved]))['status']=='passed'


def test_unrelated_preexisting_issue_cannot_expand_scope(world):
    ready(world); req=world.e.review_request(); f=finding(); f['path']='src/unrelated.py'
    with pytest.raises(OrchiError, check=lambda e: e.code=='OUT_OF_SCOPE_BLOCKER'): world.e.record_review(report(req,[f]))
    f['disposition']='advisory'; assert world.e.record_review(report(req,[f]))['status']=='passed'


def test_incomplete_review_blocks_instead_of_retrying_forever(world):
    ready(world); req=world.e.review_request(); r=report(req,[]); r['complete']=False
    assert world.e.record_review(r)['status']=='blocked'
    assert world.e.state()['phase']=='PAUSED'
