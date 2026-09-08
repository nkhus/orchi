"""Operator and executor boundaries, resource exclusion and non-code delivery."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest
from conftest import git
from test_development_flows import start, delegated, scope, brief, write
from orchi_core import authoring, context, operator_cli, publication, resources
from orchi_core.common import OrchiError, digest
from orchi_core.engine import Engine
from orchi_core.models import Policy
from orchi_core.relay import WorkerRelay
from orchi_core.runner import run_ready
from orchi_core.signing import sign


def test_handoff_reacquires_only_still_delegated_scopes_and_preserves_packet(world):
    start(world, delegated)
    old = world.e.claim('left'); world.activate(old)
    world.e.acquire_scope(old['id'],scope())
    write(old,'src/left.py','VALUE = 1\n'); write(old,'src/helper.py','HELPER = True\n')
    handed = world.e.handoff(old['id'],True,'Continue stopped work with a person')
    new = handed['ticket']
    assert handed['reacquired_scope'] and not handed['blocked_scope']
    packet = world.e.store.get_artifact(new['packet_id'])
    assert packet['handoff']['candidate'] == handed['handoff']['candidate']
    assert 'src/helper.py' in new['writes']
    world.activate(new)
    world.e.import_candidate(new['id'],handed['handoff']['candidate'],handed['handoff']['base'],'Reuse reviewed local diff')
    assert world.e.submit(new['id'],{'status':'completed','summary':'Completed preserved bounded change'})['status'] == 'integrated'


def test_handoff_old_diff_cannot_hide_changed_fixed_assumptions(world):
    def changed(plan):
        plan['tasks'][0]['context'].append({'kind':'code','path':'src/right.py','reason':'A fixed dependency assumption'})
    start(world,changed)
    old = world.e.claim('left'); world.activate(old); write(old,'src/left.py','VALUE = 1\n')
    assert world.perform('right',{'src/right.py':'VALUE = 2\n'})['status'] == 'integrated'
    handed = world.e.handoff(old['id'],True,'Stopped; recipient must reassess changed assumptions')
    new = handed['ticket']; world.activate(new)
    with pytest.raises(OrchiError) as err:
        world.e.import_candidate(new['id'],handed['handoff']['candidate'],handed['handoff']['base'],'Attempt unchanged reuse')
    assert err.value.code == 'IMPORT_ASSUMPTIONS_STALE'
    assert (Path(new['workspace'])/'src/left.py').read_text() == 'VALUE = 0\n'


def test_unknown_verifier_exit_is_fenced_after_explicit_release(world, monkeypatch):
    start(world)
    ticket = world.e.claim('left'); world.activate(ticket); write(ticket,'src/left.py','VALUE = 1\n')
    original = world.e._checks
    def release_during_checks(commit, ids, kind):
        result = original(commit,ids,kind)
        world.e.release(ticket['id'],True,'Test operator observed terminated old executor')
        return result
    monkeypatch.setattr(world.e,'_checks',release_during_checks)
    head = world.e.state()['head']
    with pytest.raises(OrchiError):
        world.e.submit(ticket['id'],{'status':'completed','summary':'A result cannot survive release fencing'})
    assert world.e.state()['head'] == head
    assert world.e.state()['tickets'][ticket['id']]['status'] == 'released'


def test_resource_exclusion_and_release_on_exception(world):
    p = Policy.model_validate({**world.policy,'resource_directory':str(world.root/'check-resources'),'resource_wait_seconds':1})
    inside = threading.Event()
    def owner():
        with resources.acquire(p,['staging']):
            inside.set(); time.sleep(.15)
    start_time = time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(owner); assert inside.wait(2)
        with resources.acquire(p,['staging']):
            assert time.monotonic() - start_time >= .12
        first.result()
    with pytest.raises(RuntimeError):
        with resources.acquire(p,['a','b']):
            raise RuntimeError('Check aborted')
    with resources.acquire(p,['b','a']):
        pass


def test_resource_timeouts_fail_closed(world):
    p = Policy.model_validate({**world.policy,'resource_directory':str(world.root/'resources'),'resource_wait_seconds':1})
    with resources.acquire(p,['shared']):
        with pytest.raises(OrchiError) as err:
            with resources.acquire(p,['shared']):
                pytest.fail('Contended resource was granted')
        assert err.value.code == 'RESOURCE_BUSY'


def test_read_only_relay_is_ticket_bound_and_does_not_expose_controller(world):
    start(world,delegated)
    ticket = world.e.claim('left')
    with WorkerRelay(world.e,ticket['id'],'prepare') as channel:
        env = channel.environment()
        cmd = [sys.executable,env['ORCHI_WORKER_REQUEST'],'read','req-user','--view','target']
        output = subprocess.run(cmd,env={**os.environ,**env},capture_output=True,text=True,check=True)
        assert json.loads(output.stdout)['result']['role'] == 'target'
        request = {'id':'one','token':channel.token,'operation':'read','arguments':{'path':'src/left.py'}}
        first = channel.dispatch(request); second = channel.dispatch(request)
        assert first == second and first['ok']
        with pytest.raises(OrchiError):
            channel.dispatch({**request,'token':'forged'})
        denied = channel.dispatch({'id':'deny','token':channel.token,'operation':'approve','arguments':{}})
        assert denied['code'] == 'CHANNEL_OPERATION_DENIED'
        denied = channel.dispatch({'id':'scope','token':channel.token,'operation':'scope','arguments':scope()})
        assert denied['code'] == 'READINESS_REQUIRED'
        assert all('control' not in k.lower() for k in env)
        socket_path = channel.socket
    assert not socket_path.exists()


def test_command_adapter_can_read_and_acquire_scope_without_control_access(world, tmp_path):
    start(world,delegated)
    agent = tmp_path/'channel_agent.py'
    agent.write_text('''import json,os,pathlib,subprocess,sys
assert 'ORCHI_CONTROL' not in os.environ
p=json.loads(pathlib.Path(os.environ['ORCHI_PACKET']).read_text())
def ask(*args, payload=None):
    proc=subprocess.run([os.environ['ORCHI_WORKER_PYTHON'],os.environ['ORCHI_WORKER_REQUEST'],*args],input=payload,text=True,capture_output=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    return json.loads(proc.stdout)['result']
ask('read','req-user','--view','target')
if os.environ['ORCHI_PHASE']=='prepare':
    result={'packet_fingerprint':p['fingerprint'],'understood_goal':p['task']['goal'],'fixed_decisions':p['task']['decisions'],'acceptance_ids':list(p['task']['acceptance']),'questions':[]}
else:
    tid=p['task']['id']
    if tid=='left':
        request={'edit':{'path':'src/helper.py','action':'create','how':'Approved local helper'},'choice':'Local variable spelling','reason':'Preserve the accepted public interface'}
        ask('scope','--file','-',payload=json.dumps(request))
        pathlib.Path('src/helper.py').write_text('HELPER=True\\n')
    pathlib.Path('src/'+tid+'.py').write_text('VALUE = '+('1' if tid=='left' else '2')+'\\n')
    result={'status':'completed','summary':'Implemented through the bounded ticket channel'}
pathlib.Path(os.environ['ORCHI_OUTPUT']).write_text(json.dumps(result))
''')
    result = run_ready(world.e,{'kind':'command','argv':[sys.executable,str(agent)]})
    assert all(o['status']=='integrated' for o in result['outcomes']), result
    assert 'src/helper.py' in world.e.repo.files(world.e.state()['head'])
    assert all(t['read_events'] for t in world.e.state()['tickets'].values())


def test_operator_decide_requires_the_displayed_exact_request(world, capsys):
    gate = world.e.begin(world.spec,world.bundle)
    args=['decide','--control',str(world.e.store.root),'--private',str(world.key),'--operator','human','--decision','approve']
    assert operator_cli.main([*args,'--request-id','not-the-displayed-request']) == 2
    assert world.e.state()['phase'] == 'AWAITING_APPROVAL'
    assert operator_cli.main([*args,'--request-id',gate['id']]) == 0
    assert world.e.state()['phase'] == 'PLANNING'
    assert world.e.state()['approvals']


def test_knowledge_only_full_publication_has_no_fake_implementation_task(world):
    policy=copy.deepcopy(world.policy)
    policy['checks']['guide']={'argv':[sys.executable,'-c',"from pathlib import Path; assert 'verified module' in Path('docs/guide.md').read_text()"]}
    policy['final_checks']=['guide']
    world.e=Engine.setup(world.root/'docs-control',world.repo,policy)
    b=brief('knowledge'); b['tasks']=[]; b['checks']=['baseline']; b['outcome']='Document the verified module'
    b['requirements']={'req-guide':'A readable guide describes the verified module'}
    b['architecture']='This knowledge outcome does not add a system architecture or claim future implementation'
    world.approve(world.e.begin_brief(b))
    assert world.e.state()['active']['plan']['tasks'] == []
    world.pass_review()
    world.e.checkpoint({'epic_id':'delivery','based_on':world.e.state()['head'],'report':'Describe existing checked code',
        'entries':[{'target':'docs/guide.md','action':'replace','content':'---\nkind: guide\n---\n# Guide\nThe verified module has a plain constant.\n',
                    'artifacts':[],'checks':['baseline'],'reason':'Documentation-only result from the existing implementation'}],
        'dispositions':[]})
    p=world.e.final_draft();p['report']='Reconciled documentation without product code edits'
    p['requirements'][0].update(disposition='satisfied',reason='Final guide check establishes presence and content',checks=['guide'],core_targets=['docs/guide.md'])
    p['architecture'][0].update(disposition='not-applicable',reason='The accepted outcome is only existing-system knowledge',checks=['guide'])
    candidate=world.e.finalize(p)['candidate'];world.approve(world.pass_review('initiative'))
    assert world.e.repo.read(candidate,'src/left.py')==b'VALUE = 0\n'
    assert world.e.repo.read(candidate,'docs/guide.md').find(b'verified module')>=0
    git(world.repo,'update-ref','refs/heads/main',candidate,world.baseline)
    assert world.e.record_publication(candidate)['status']=='published'


def test_original_request_whitespace_is_preserved(world):
    b=brief();b['request']='\n  Exact original user text.\n\n'
    _,bundle,_,_=authoring.expand(b,world.baseline)
    assert bundle['documents']['source.md']==b['request']
