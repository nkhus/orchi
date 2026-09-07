#!/usr/bin/env python3
"""Transactional local-skill installation. Never rewrites AGENTS.md or Codex config."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('orchi','orchi-plan','orchi-work','orchi-review','orchi-deliver')


def inventory(d: Path) -> dict[str,str]:
    result={}
    for p in sorted(d.rglob('*')):
        if p.is_symlink(): raise ValueError('Refusing symlink: '+str(p))
        if '__pycache__' in p.parts or p.suffix=='.pyc': continue
        if p.is_file(): result[p.relative_to(d).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def install(project: Path, replace=False, dry=False):
    if project.is_symlink(): raise ValueError('Project must not be a symlink')
    project=project.resolve()
    if not project.is_dir(): raise ValueError('Project must already exist')
    dest=project/'.agents/skills'
    for p in (project/'.agents',dest,project/'.agents/.orchi-install.json'):
        if p.is_symlink(): raise ValueError('Refusing symlink: '+str(p))
    desired={n:inventory(ROOT/'skills'/n) for n in NAMES}
    existing={n:dest/n for n in NAMES if (dest/n).exists() or (dest/n).is_symlink()}
    for n,d in existing.items():
        if d.is_symlink() or not d.is_dir(): raise ValueError('Refusing non-directory/symlink skill '+str(d))
        inventory(d)
    different=[n for n in NAMES if n not in existing or inventory(existing[n])!=desired[n]]
    conflicts=[n for n in different if n in existing]
    if conflicts and not replace:
        raise ValueError('Existing Orchi content differs: '+', '.join(conflicts)+'. Review and use --replace-orchi; a backup will be kept.')
    result={'project':str(project),'install':different,
            'preserved':['AGENTS.md','.codex/config.toml','non-Orchi skills']}
    if dry: return {**result,'dry_run':True}
    if not different: return {**result,'status':'unchanged'}
    backup=project.parent/(project.name+'-orchi-backup-'+uuid.uuid4().hex[:10])
    backup.mkdir(); dest.mkdir(parents=True,exist_ok=True)
    staged=Path(tempfile.mkdtemp(prefix='.orchi-stage-',dir=dest.parent))
    moved=[]; added=[]
    manifest=project/'.agents/.orchi-install.json'
    oldmanifest=manifest.read_bytes() if manifest.exists() else None
    try:
        for n in different:
            shutil.copytree(ROOT/'skills'/n,staged/n,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            if inventory(staged/n)!=desired[n]: raise ValueError('Staging integrity failed: '+n)
        for n in conflicts:
            shutil.move(str(existing[n]),str(backup/n)); moved.append(n)
        for n in different:
            shutil.move(str(staged/n),str(dest/n)); added.append(n)
        manifest.write_text(json.dumps({'skills':desired},indent=2)+'\n')
    except BaseException:
        for n in added: shutil.rmtree(dest/n)
        for n in reversed(moved): shutil.move(str(backup/n),str(dest/n))
        if oldmanifest is not None: manifest.write_bytes(oldmanifest)
        elif manifest.exists(): manifest.unlink()
        raise
    finally:
        shutil.rmtree(staged,ignore_errors=True)
    if not moved: backup.rmdir(); result['backup']=None
    else: result['backup']=str(backup)
    return {**result,'status':'installed'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True);p.add_argument('--replace-orchi',action='store_true');p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    try: print(json.dumps(install(a.project,a.replace_orchi,a.dry_run),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError) as e: print(json.dumps({'error':str(e)},ensure_ascii=False));return 2

if __name__=='__main__': raise SystemExit(main())
