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
SKILLS = ('orchi', 'orchi-plan', 'orchi-deliver')
ROLES = ('orchi-fixer', 'orchi-implementer', 'orchi-reviewer', 'orchi-scout')


def smoke(out: Path, installer: str, github: bool = False) -> dict:
    """Never use an existing destination."""
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    project = out / 'project'
    project.mkdir()
    env = {key: value for key, value in os.environ.items() if key not in {'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV'}}
    env.update(DISABLE_TELEMETRY='1', DO_NOT_TRACK='1')
    log = out / 'commands.log'

    def run(argv: list[str], extra: dict | None = None, expect: int = 0) -> str:
        with log.open('a', encoding='utf-8') as stream:
            stream.write('\n$ ' + repr(argv) + '\n')
            stream.flush()
            result = subprocess.run(argv, cwd=project, env={**env, **(extra or {})}, capture_output=True,
                                    text=True, timeout=300, check=False)
            stream.write(result.stdout + result.stderr)
        if result.returncode != expect:
            raise RuntimeError(f'Command failed ({result.returncode}); see {log}: {argv!r}')
        return result.stdout

    run(['git', 'init', '-b', 'main'])
    preserved = {
        'CLAUDE.md': '# Existing project instructions\nKeep these instructions.\n',
        'AGENTS.md': '# Instructions for other assistants\n',
        '.claude/skills/unrelated/SKILL.md': '---\nname: unrelated\ndescription: Existing skill\n---\n',
        'docs/guide.md': '# Guide\nSession behavior.\n',
        'pyproject.toml': '[project]\nname = "unrelated-application"\nrequires-python = ">=3.99"\n',
    }
    for relative, text in preserved.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    if installer == 'skills':
        run(['npx', '--yes', 'skills', 'add', str(ROOT), '--skill', '*', '--agent', 'claude-code', '--yes'])
    elif installer == 'npm':
        run(['node', str(ROOT / 'bin/orchi.js'), '--project', str(project), *(['--github'] if github else [])])
    else:
        run([sys.executable, str(ROOT / 'tools/install.py'), '--project', str(project), *(['--github'] if github else [])])
    for name in SKILLS:
        if not (project / '.claude/skills' / name / 'SKILL.md').is_file():
            raise RuntimeError('Missing installed skill: ' + name)
    knowledge = project / '.claude/skills/orchi/scripts/knowledge.py'
    hits = json.loads(run([sys.executable, str(knowledge), 'search', 'session']))['results']
    if [hit['path'] for hit in hits] != ['docs/guide.md']:
        raise RuntimeError('Installed knowledge search returned unexpected results')
    run([sys.executable, str(knowledge), 'lint'])
    if github and installer != 'skills':
        for relative in ('.github/workflows/orchi-docs.yml', '.github/ISSUE_TEMPLATE/orchi-epic.yml'):
            if not (project / relative).is_file():
                raise RuntimeError('Missing GitHub setup file: ' + relative)
        template = (project / '.github/pull_request_template.md').read_text(encoding='utf-8')
        run([sys.executable, str(knowledge), 'impact'], {'PR_BODY': template}, expect=1)
        run([sys.executable, str(knowledge), 'impact'], {'PR_BODY': template.replace(
            '## Documentation impact\n', '## Documentation impact\n\nUpdated docs/guide.md.\n')})
    for relative, text in preserved.items():
        installed_text = (project / relative).read_text(encoding='utf-8')
        if relative == 'CLAUDE.md' and installer != 'skills':
            if not installed_text.startswith(text) or installed_text.count('<!-- orchi:begin -->') != 1:
                raise RuntimeError('Managed Claude instructions were not installed correctly')
        elif installed_text != text:
            raise RuntimeError('Installation modified an unrelated file: ' + relative)
    if installer != 'skills':
        folder = project / '.claude/agents'
        found = sorted(path.name for path in folder.iterdir()) if folder.is_dir() else []
        if found != [name + '.md' for name in ROLES]:
            raise RuntimeError('Unexpected Orchi subagents in .claude/agents: ' + ', '.join(found))
        for path in folder.glob('*.md'):
            if '{{' in path.read_text(encoding='utf-8'):
                raise RuntimeError('Unexpanded placeholder in ' + str(path))
        for unexpected in ('.agents', '.codex'):
            if (project / unexpected).exists():
                raise RuntimeError('Installation wrote outside Claude Code locations: ' + unexpected)
    result = {'ok': True, 'installer': installer, 'github': github, 'skills': len(SKILLS),
              'subagents': 0 if installer == 'skills' else len(ROLES),
              'preserved_files': len(preserved), 'live_model': False, 'out': str(out)}
    (out / 'smoke-report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='A new disposable output directory')
    parser.add_argument('--installer', choices=('skills', 'local', 'npm'), default='npm')
    parser.add_argument('--github', action='store_true', help='Also install and check the GitHub setup files')
    args = parser.parse_args()
    try:
        result = smoke(args.out, args.installer, args.github)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
