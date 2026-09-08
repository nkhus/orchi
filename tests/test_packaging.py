"""Installed-runtime tests independent of the consuming project's toolchain."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tomllib
import pytest
from orchi_core import diagnostics
from orchi_core.cli import parser
from orchi_core.operator_cli import main as operator_main
from orchi_core.signing import verify

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_validation():
    report = load_tool('validate_package').validate()
    assert report['ok'], report['errors']


def test_npm_package_is_a_dependency_free_installer():
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert 'project' not in config and 'build-system' not in config
    package = json.loads((ROOT / 'package.json').read_text())
    assert package['name'] == '@nkhus/orchi'
    assert package['bin'] == {'orchi': 'bin/orchi.js'}
    assert package['files'] == [
        'bin/orchi.js', 'tools/install.py', 'skills/*/SKILL.md', 'skills/*/agents/openai.yaml',
        'skills/orchi/assets', 'skills/orchi/references', 'skills/orchi/scripts/**/*.py',
        'skills/orchi/scripts/requirements.txt', 'README.md']
    assert 'dependencies' not in package and 'devDependencies' not in package
    assert not any(name in package.get('scripts', {}) for name in ('install', 'preinstall', 'postinstall'))


def test_node_installer_uses_uv_and_current_directory(tmp_path):
    result = subprocess.run(['node', str(ROOT / 'bin/orchi.js'), '--dry-run'], cwd=tmp_path,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['project'] == str(tmp_path.resolve()) and report['dry_run'] is True
    assert list(tmp_path.iterdir()) == []


def test_node_installer_installs_complete_bundle(tmp_path):
    result = subprocess.run(['node', str(ROOT / 'bin/orchi.js')], cwd=tmp_path,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert sorted(path.name for path in (tmp_path / '.agents/skills').iterdir()) == sorted(
        ('orchi', 'orchi-plan', 'orchi-work', 'orchi-review', 'orchi-deliver'))


def test_entrypoints_declare_same_isolated_dependencies():
    validator = load_tool('validate_package')
    requirements = (ROOT / 'skills/orchi/scripts/requirements.txt').read_text().splitlines()
    for script in ('orchi.py', 'operator.py'):
        metadata = validator.inline_metadata(ROOT / 'skills/orchi/scripts' / script)
        assert metadata['dependencies'] == requirements
        assert metadata['requires-python'] == '>=3.11'


def test_doctor_does_not_create_control_state(tmp_path):
    control = tmp_path / 'nonexistent-control'
    env = {**os.environ, 'ORCHI_CONTROL': str(control)}
    result = subprocess.run([sys.executable, str(ROOT / 'skills/orchi/scripts/orchi.py'), 'doctor'],
                            env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['result']['status'] == 'ready'
    assert not control.exists()


def test_doctor_detects_partial_skill_installation(tmp_path, monkeypatch):
    bundle = tmp_path / 'skills/orchi/scripts/orchi_core/diagnostics.py'
    bundle.parent.mkdir(parents=True)
    monkeypatch.setattr(diagnostics, '__file__', str(bundle))
    report = diagnostics.doctor()
    assert report['status'] == 'blocked'
    assert any(item['name'] == 'skill:orchi-plan' and not item['passed'] for item in report['checks'])


def test_doctor_distinguishes_missing_optional_codex(monkeypatch):
    actual = diagnostics.shutil.which
    monkeypatch.setattr(diagnostics.shutil, 'which', lambda name: None if name == 'codex' else actual(name))
    assert diagnostics.doctor()['status'] == 'ready'
    assert diagnostics.doctor(require_codex=True)['status'] == 'blocked'


def test_doctor_checks_existing_git_repository(tmp_path):
    subprocess.run(['git', 'init', '-b', 'main', str(tmp_path)], check=True, capture_output=True)
    assert diagnostics.doctor(str(tmp_path))['status'] == 'ready'
    assert diagnostics.doctor(str(tmp_path / 'missing'))['status'] == 'blocked'


def test_control_environment_and_explicit_precedence(monkeypatch):
    monkeypatch.setenv('ORCHI_CONTROL', '/operator/default-control')
    assert parser().parse_args(['next']).control == '/operator/default-control'
    assert parser().parse_args(['--control', '/operator/explicit-control', 'next']).control == '/operator/explicit-control'


def test_complete_installed_bundle_does_not_need_source_checkout(tmp_path):
    load_tool('install').install(tmp_path)
    scripts = tmp_path / '.agents/skills/orchi/scripts'
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="unrelated-app"\nrequires-python=">=3.99"\n')
    env = {k: v for k, v in os.environ.items() if k not in {'PYTHONPATH', 'ORCHI_CONTROL'}}
    for script, args in [('orchi.py', ['doctor']), ('operator.py', ['--help']),
                         ('orchi.py', ['schemas', '--out', str(tmp_path / 'exported-schemas')])]:
        result = subprocess.run([sys.executable, str(scripts / script), *args], cwd=tmp_path,
                                env=env, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
    assert len(list((tmp_path / 'exported-schemas').glob('*.json'))) == len(__import__('orchi_core.models', fromlist=['CONTRACTS']).CONTRACTS)
    assert not list((tmp_path / '.agents').rglob('__pycache__'))


def test_operator_key_generation_and_overwrite_refusal(tmp_path, capsys):
    private, public = tmp_path / 'private.pem', tmp_path / 'public.pem'
    args = ['keygen', '--private', str(private), '--public', str(public)]
    assert operator_main(args) == 0
    before = private.read_bytes()
    assert private.stat().st_mode & 0o777 == 0o600
    assert operator_main(args) == 2
    assert private.read_bytes() == before


def test_operator_existing_public_key_does_not_leave_new_private_key(tmp_path, capsys):
    public = tmp_path / 'public.pem'; public.write_text('Do not replace')
    private = tmp_path / 'private.pem'
    assert operator_main(['keygen', '--private', str(private), '--public', str(public)]) == 2
    assert not private.exists() and public.read_text() == 'Do not replace'


def test_operator_signs_exact_gate_and_refuses_output_overwrite(tmp_path, capsys):
    private, public = tmp_path / 'private.pem', tmp_path / 'public.pem'
    assert operator_main(['keygen', '--private', str(private), '--public', str(public)]) == 0
    request = {'format': 'orchi-gate', 'id': 'test-request', 'inputs': {'intent': 'Test only'}}
    source = tmp_path / 'request.json'; source.write_text(json.dumps(request))
    output = tmp_path / 'decision.json'
    args = ['sign', '--request', str(source), '--private', str(private), '--decision', 'approve',
            '--operator', 'test-operator', '--out', str(output)]
    assert operator_main(args) == 0
    verify(request, json.loads(output.read_text()), public.read_text())
    assert operator_main(args) == 2


def test_operator_rejects_non_gate_input(tmp_path, capsys):
    source = tmp_path / 'request.json'; source.write_text('{"arbitrary": true}')
    assert operator_main(['sign', '--request', str(source), '--private', str(tmp_path / 'absent-key'),
                          '--decision', 'approve', '--operator', 'test', '--out', str(tmp_path / 'output')]) == 2
    assert not (tmp_path / 'output').exists()


def test_copy_install_rollback_preserves_modified_skill(tmp_path, monkeypatch):
    installer = load_tool('install')
    installer.install(tmp_path)
    target = tmp_path / '.agents/skills/orchi/SKILL.md'; target.write_text('User customization')
    original_move = installer.shutil.move
    def fail_staged_move(source, destination):
        if '.orchi-stage-' in str(source): raise OSError('Injected staging failure')
        return original_move(source, destination)
    monkeypatch.setattr(installer.shutil, 'move', fail_staged_move)
    with pytest.raises(OSError): installer.install(tmp_path, replace=True)
    assert target.read_text() == 'User customization'
