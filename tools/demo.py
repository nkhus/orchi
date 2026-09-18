#!/usr/bin/env python3
"""Synthetic two-epic demonstration. Never run approvals on a real repository."""
from pathlib import Path
import argparse
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'skills/orchi/scripts'),str(ROOT/'tests')]
from conftest import World, git
from orchi_core.runner import run_ready
from orchi_core import context


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    if a.out.exists(): p.error('--out must be a new directory; demo never uses an existing project')
    a.out.mkdir(parents=True);w=World(a.out)
    w.begin();w.approve(w.e.plan(w.plan1()))
    # Explicitly a fake deterministic process, not a model benchmark.
    r=run_ready(w.e,{'kind':'command','argv':[sys.executable,str(ROOT/'tests/fake_agent.py')]})
    assert all(x['status']=='integrated' for x in r['outcomes'])
    w.pass_review();w.e.checkpoint(w.checkpoint1())
    intermediate={'baseline':w.baseline,'head':w.e.state()['head'],
                  'canonical_doc':context.get(w.e.repo,w.e.state(),'docs/architecture.md')['content'],
                  'working_doc':context.get(w.e.repo,w.e.state(),'docs/architecture.md','feature')['content']}
    task=w.task('api','api.py','api',action='create',with_doc=True)
    plan={'initiative_id':'feature','epic_id':'api','based_on':w.e.state()['head'],'goal':'Expose values',
          'shared_design':'Build on the verified prior epic, not initial canonical implementation',
          'acceptance':{'ac-api':'API available'},'acceptance_checks':{'ac-api':['api']},'tasks':[task]}
    w.approve(w.e.plan(plan));ticket=w.e.claim('api')
    shutil.copytree(Path(ticket['packet']).parent,a.out/'task-packet')
    w.activate(ticket);(Path(ticket['workspace'])/'src/api.py').write_text('ANSWER = 3\n')
    w.e.submit(ticket['id'],{'status':'completed','summary':'Synthetic implementation'})
    w.pass_review();w.e.checkpoint({'epic_id':'api','based_on':w.e.state()['head'],'report':'Verified new API',
        'entries':[{'target':'docs/api.md','action':'replace','content':'# API\nThe answer is three.\n','artifacts':['src/api.py'],'checks':['api'],'reason':'Verified interface'}],
        'dispositions':[{'path':'src/api.py','targets':['docs/api.md'],'reason':'Interface changed'}]})
    draft=w.e.final_draft();draft['report']='Synthetic cumulative reconciliation: values and API tested, source docs updated only now.'
    w.e.finalize(draft);w.approve(w.pass_review('initiative'));pub=w.e.publication()
    git(w.repo,'merge','--ff-only',pub['candidate']);w.e.record_publication(pub['candidate'])
    w.e.export(a.out/'audit')
    report={'synthetic':True,'live_model':False,'stages':['direction','epic-values','epic-api','finalization','final-approval','operator-publication'],
            'parallel_outcomes':r['outcomes'],'intermediate':intermediate,'publication':pub,
            'canonical_commits':len(git(w.repo,'rev-list',w.baseline+'..main').splitlines()),'phase':w.e.state()['phase']}
    (a.out/'demo-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'out':str(a.out),'phase':report['phase'],'canonical_commits':report['canonical_commits'],'synthetic':True}))

if __name__=='__main__':main()
