#!/usr/bin/env python3
"""Exercise the complete installed bundle in a new, unrelated Git project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('orchi',)


def smoke(out: Path, installer: str, agents: list[str] | None = None) -> dict:
    """Never use an existing destination."""
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    project = out / 'project'
    project.mkdir()
    agents = agents or ['codex', 'copilot', 'claude']
    env = {key: value for key, value in os.environ.items() if key not in {'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV'}}
    env.update(DISABLE_TELEMETRY='1', DO_NOT_TRACK='1')
    log = out / 'commands.log'

    def run(argv: list[str]) -> str:
        with log.open('a', encoding='utf-8') as stream:
            stream.write('\n$ ' + repr(argv) + '\n')
            stream.flush()
            result = subprocess.run(argv, cwd=project, env=env, capture_output=True,
                                    text=True, timeout=300, check=False)
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}); see {log}: {argv!r}')
        return result.stdout

    run(['git', 'init', '-b', 'main'])
    preserved = {
        'AGENTS.md': '# Existing project instructions\nKeep these instructions.\n',
        '.codex/config.toml': 'model = "operator-selected-model"\n',
        '.agents/skills/unrelated/SKILL.md': '---\nname: unrelated\ndescription: Existing skill\n---\n',
        'docs/guide.md': '# Guide\nSession behavior.\n',
        'pyproject.toml': '[project]\nname = "unrelated-application"\nrequires-python = ">=3.99"\n',
    }
    for relative, text in preserved.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    if installer == 'skills':
        names = {'codex': 'codex', 'copilot': 'github-copilot', 'claude': 'claude-code'}
        run(['npx', '--yes', 'skills', 'add', str(ROOT), '--skill', '*', '--agent', *[names[name] for name in agents], '--yes'])
    elif installer == 'npm':
        run(['node', str(ROOT / 'bin/orchi.js'), '--project', str(project), '--agents', *agents])
    else:
        run([sys.executable, str(ROOT / 'tools/install.py'), '--project', str(project), '--agents', *agents])
    for name in SKILLS:
        if not (project / '.agents/skills' / name / 'SKILL.md').is_file():
            raise RuntimeError('Missing installed skill: ' + name)
    knowledge = project / '.agents/skills/orchi/scripts/knowledge.py'
    hits = json.loads(run([sys.executable, str(knowledge), 'search', 'session']))['results']
    if [hit['path'] for hit in hits] != ['docs/guide.md']:
        raise RuntimeError('Installed knowledge search returned unexpected results')
    run([sys.executable, str(knowledge), 'lint'])
    for relative, text in preserved.items():
        installed_text = (project / relative).read_text(encoding='utf-8')
        if relative == 'AGENTS.md' and installer != 'skills':
            if not installed_text.startswith(text) or installed_text.count('<!-- orchi:begin -->') != 1:
                raise RuntimeError('Managed root instructions were not installed correctly')
        elif installed_text != text:
            raise RuntimeError('Installation modified an unrelated file: ' + relative)
    if 'claude' in agents:
        for name in SKILLS:
            if (project / '.claude/skills' / name).resolve() != project / '.agents/skills' / name:
                raise RuntimeError('Claude does not share the canonical skill bundle')
    result = {'ok': True, 'installer': installer, 'agents': agents, 'skills': len(SKILLS),
              'preserved_files': len(preserved), 'live_model': False, 'out': str(out)}
    (out / 'smoke-report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='A new disposable output directory')
    parser.add_argument('--installer', choices=('skills', 'local', 'npm'), default='npm')
    parser.add_argument('--agents', nargs='+', choices=('codex', 'copilot', 'claude'), default=['codex', 'copilot', 'claude'])
    args = parser.parse_args()
    try:
        result = smoke(args.out, args.installer, args.agents)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
