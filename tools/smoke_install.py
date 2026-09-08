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
        'docs/authentication.md': '# Identity\n\n## Callback validation\nValidate authentication callback signatures.\n',
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
    run(['git', 'add', 'docs/authentication.md'])
    run(['git', '-c', 'user.name=Orchi Test', '-c', 'user.email=test@example.invalid',
         'commit', '-m', 'Synthetic documentation fixture'])
    if installer == 'skills':
        run(['npx', '--yes', 'skills', 'add', str(ROOT), '--skill', '*', '--agent', 'codex', '--yes'])
    elif installer == 'npx':
        run(['npx', '--yes', '--package', str(ROOT), 'orchi', '--project', str(project)])
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
    search = json.loads(run([*prefix, str(scripts / 'orchi.py'), 'search', 'authentication callback', '--repo', '.']))
    hit = search['result']['results'][0]
    if hit['heading'] != 'Callback validation' or hit['target'] != 'docs/authentication.md':
        raise RuntimeError('Installed retrieval did not find the exact source section')
    exact = json.loads(run([*prefix, str(scripts / 'orchi.py'), 'get', hit['target'], '--repo', '.',
                           '--content-hash', hit['content_hash']]))
    if hit['snippet'] not in exact['result']['content']:
        raise RuntimeError('Installed retrieval readback did not match the source')
    stats = json.loads(run([*prefix, str(scripts / 'orchi.py'), 'stat', '--repo', '.']))
    if stats['result']['index']['status'] != 'reused':
        raise RuntimeError('Installed retrieval did not reuse its scoped cache')
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
    # Exercise accepted Target exclusively through copied entrypoints, not source imports.
    intent_dir = out / 'target'
    (intent_dir / 'architecture').mkdir(parents=True)
    docs = {
        'source.md': 'Synthetic request: preserve authentication callbacks.\n',
        'requirements.md': '---\nkind: requirements\nrequirements: [req-callback]\n---\n# Requirements\n<a id="req-callback"></a>\n## Callback\nRetain verifiable authentication callback signatures.\n',
        'architecture/README.md': '---\nkind: architecture\nrelations:\n  addresses: [req-callback]\n---\n# Target architecture\nKeep callback verification within the existing authentication boundary.\n',
    }
    for name, text in docs.items():
        (intent_dir / name).write_text(text)
    built = json.loads(run([*prefix, str(scripts / 'orchi.py'), 'intent-build', '--directory', str(intent_dir), '--initiative', 'smoke']))['result']
    initiative = {'id': 'smoke', 'outcome': 'Preserve callback signatures', 'intent': built['intent'],
                  'epics': [{'id': 'callback', 'title': 'Callback', 'outcome': 'Verify callback boundaries',
                             'contributes_to': ['req-callback'], 'realizes': ['intent/architecture/README.md']}]}
    spec_path = out / 'initiative.json'; spec_path.write_text(json.dumps(initiative))
    # This smoke proves installation/knowledge access, not product verification. Its no-op
    # check and automatic signing identity are deliberately confined to a disposable repo.
    policy = {'public_key': (out / 'test-only-public.pem').read_text(),
              'checks': {'fixture': {'argv': [sys.executable, '-c', 'pass']}},
              'baseline_checks': [], 'final_checks': ['fixture']}
    policy_path = out / 'policy.json'; policy_path.write_text(json.dumps(policy))
    control = out / 'control'
    command = [*prefix, str(scripts / 'orchi.py'), '--control', str(control)]
    run([*command, 'setup', '--repo', str(project), '--policy', str(policy_path)])
    run([*command, 'begin', '--file', str(spec_path), '--intent', str(intent_dir)])
    request, decision = out / 'request.json', out / 'decision.json'
    run([*command, 'gate', '--out', str(request)])
    run([*prefix, str(scripts / 'operator.py'), 'sign', '--request', str(request),
         '--private', str(out / 'test-only-private.pem'), '--decision', 'approve',
         '--operator', 'synthetic-smoke-only', '--out', str(decision)])
    run([*command, 'apply-decision', '--file', str(decision)])
    target = json.loads(run([*command, 'search', 'callback', '--initiative', 'smoke', '--view', 'target']))['result']
    if not target['primary_matches'] or any(h['role'] != 'target' for h in target['primary_matches']):
        raise RuntimeError('Installed Target search mixed authority roles')
    target_hash = next(h['content_hash'] for h in target['primary_matches'] if h['target'] == 'intent/requirements.md')
    exact_target = json.loads(run([*command, 'get', 'req-callback', '--initiative', 'smoke', '--view', 'target', '--content-hash', target_hash]))['result']
    if exact_target['content'] != docs['requirements.md']:
        raise RuntimeError('Installed Target exact read differs from accepted bytes')
    run([*command, 'related', 'req-callback', '--initiative', 'smoke', '--view', 'all', '--relation', 'addressed_by'])
    run([*command, 'lint', '--initiative', 'smoke', '--view', 'all'])
    run([*command, 'map', '--initiative', 'smoke', '--view', 'all', '--out', str(out / 'knowledge-map.html')])
    coverage = json.loads(run([*command, 'coverage', '--initiative', 'smoke']))['result']
    if coverage['requirements'][0]['state'] != 'planned':
        raise RuntimeError('An unimplemented installed fixture was reported as verified')
    for relative, text in preserved.items():
        if (project / relative).read_text(encoding='utf-8') != text:
            raise RuntimeError('Installation modified an unrelated file: ' + relative)
    for unexpected in ('.venv', 'uv.lock'):
        if (project / unexpected).exists():
            raise RuntimeError('Runtime used the consuming application environment: ' + unexpected)
    result = {'ok': True, 'installer': installer, 'runner': runner, 'skills': len(SKILLS),
              'schemas': len(actual), 'preserved_files': len(preserved), 'retrieval_readback': True,
              'retrieval_cache_reused': True, 'target_exact_readback': True,
              'graph_map_lint_coverage': True,
              'live_model': False, 'out': str(out)}
    (out / 'smoke-report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='A new disposable output directory')
    parser.add_argument('--installer', choices=('skills', 'npx', 'local'), default='skills')
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
