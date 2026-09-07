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
SKILLS = ('orchi', 'orchi-plan', 'orchi-work', 'orchi-review', 'orchi-deliver')


def smoke(out: Path, installer: str, runner: str) -> dict:
    """Never use an existing destination or a production control directory."""
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    project = out / 'project'
    project.mkdir()
    env = {key: value for key, value in os.environ.items()
           if key not in {'PYTHONPATH', 'PYTHONHOME', 'ORCHI_CONTROL', 'VIRTUAL_ENV'}}
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
        'pyproject.toml': (
            '[project]\nname = "unrelated-application"\nrequires-python = ">=3.99"\n'
            'dependencies = ["deliberately-unresolvable-orchi-smoke-dependency"]\n'
        ),
    }
    for relative, text in preserved.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    if installer == 'skills':
        run(['npx', '--yes', 'skills', 'add', str(ROOT), '--skill', '*', '--agent', 'codex', '--yes'])
    else:
        run([sys.executable, str(ROOT / 'tools/install.py'), '--project', str(project)])
    for name in SKILLS:
        if not (project / '.agents/skills' / name / 'SKILL.md').is_file():
            raise RuntimeError('Missing installed skill: ' + name)
    scripts = project / '.agents/skills/orchi/scripts'
    prefix = ['uv', 'run'] if runner == 'uv' else [sys.executable]
    diagnostics = json.loads(run([*prefix, str(scripts / 'orchi.py'), 'doctor', '--repo', '.']))
    if diagnostics.get('result', {}).get('status') != 'ready':
        raise RuntimeError('Installed diagnostics did not report ready')
    run([*prefix, str(scripts / 'operator.py'), '--help'])
    generated = out / 'schemas'
    run([*prefix, str(scripts / 'orchi.py'), 'schemas', '--out', str(generated)])
    expected = {p.name: json.loads(p.read_text()) for p in (ROOT / 'schemas').glob('*.json')}
    actual = {p.name: json.loads(p.read_text()) for p in generated.glob('*.json')}
    if actual != expected:
        raise RuntimeError('Installed contracts differ from the repository schemas')
    # The test-only key stays outside the consuming project.
    run([*prefix, str(scripts / 'operator.py'), 'keygen',
         '--private', str(out / 'test-only-private.pem'), '--public', str(out / 'test-only-public.pem')])
    for relative, text in preserved.items():
        if (project / relative).read_text(encoding='utf-8') != text:
            raise RuntimeError('Installation modified an unrelated file: ' + relative)
    for unexpected in ('.venv', 'uv.lock'):
        if (project / unexpected).exists():
            raise RuntimeError('Runtime used the consuming application environment: ' + unexpected)
    result = {'ok': True, 'installer': installer, 'runner': runner, 'skills': len(SKILLS),
              'schemas': len(actual), 'preserved_files': len(preserved),
              'live_model': False, 'out': str(out)}
    (out / 'smoke-report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='A new disposable output directory')
    parser.add_argument('--installer', choices=('skills', 'local'), default='skills')
    parser.add_argument('--runner', choices=('uv', 'python'), default='uv')
    args = parser.parse_args()
    try:
        result = smoke(args.out, args.installer, args.runner)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
