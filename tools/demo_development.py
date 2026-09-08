#!/usr/bin/env python3
"""Two independent atomic initiatives on a moving local Git target; synthetic only."""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'skills/orchi/scripts'),str(ROOT/'tests')]
from conftest import World, git
from test_synchronization_publication import completed_compact, finalize_compact, proposal, approve_sync
from orchi_core import views


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    if a.out.exists():p.error('--out must be a new disposable directory')
    a.out.mkdir(parents=True)
    w=World(a.out)
    first=completed_compact(w,'independent-left','src/left.py','left',1,a.out/'left-control')
    second=completed_compact(w,'independent-right','src/right.py','right',2,a.out/'right-control')
    commit1=finalize_compact(first,w.key)
    git(w.repo,'update-ref','refs/heads/main',commit1,w.baseline)
    first.record_publication(commit1)
    w.e=second
    before=second.state()
    checked=second.synchronize(proposal(w));approve_sync(w,checked)
    projection=views.materialize(second,a.out/'second-current-and-target','all')
    commit2=finalize_compact(second,w.key)
    git(w.repo,'update-ref','refs/heads/main',commit2,commit1)
    second.record_publication(commit2)
    first.export(a.out/'left-audit');second.export(a.out/'right-audit')
    report={'synthetic':True,'live_model':False,'original_baseline':w.baseline,
            'first':{'phase':first.state()['phase'],'publication':commit1},
            'second':{'phase':second.state()['phase'],'publication':commit2,'old_integration_base':before['integration_base'],
                      'accepted_integration_base':second.state()['integration_base'],'origin_baseline':second.state()['baseline']},
            'synchronizations':len(second.state()['sync_history']),'derived_view':projection,
            'canonical_commits':len(git(w.repo,'rev-list',w.baseline+'..main').splitlines()),
            'left':second.repo.read(commit2,'src/left.py').decode(),'right':second.repo.read(commit2,'src/right.py').decode(),
            'external_pr':False,'deployment':False}
    (a.out/'development-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
