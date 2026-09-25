"""Source validation and self-contained installation of the skill bundle."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load_tool('install')


def test_source_validation():
    report = load_tool('validate_package').validate()
    assert report['ok'], report['errors']


def test_runtime_has_no_application_package_metadata():
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert 'project' not in config and 'build-system' not in config
    assert json.loads((ROOT / 'package.json').read_text())['name'] == '@nkhus/orchi'


def test_fresh_install_preserves_user_files(tmp_path):
    (tmp_path / 'AGENTS.md').write_text('User rules')
    (tmp_path / '.codex').mkdir(); (tmp_path / '.codex/config.toml').write_text('model="operator-model"')
    assert installer.install(tmp_path)['status'] == 'installed'
    assert (tmp_path / 'AGENTS.md').read_text().startswith('User rules\n\n<!-- orchi:begin -->')
    assert (tmp_path / '.codex/config.toml').read_text() == 'model="operator-model"'
    assert sorted(p.name for p in (tmp_path / '.agents/skills').iterdir()) == sorted(installer.NAMES)
    assert installer.install(tmp_path)['status'] == 'unchanged'


def test_dry_run_no_mutation(tmp_path):
    installer.install(tmp_path, dry=True)
    assert list(tmp_path.iterdir()) == []


def test_modified_skill_refuses_silent_overwrite(tmp_path):
    installer.install(tmp_path)
    skill = tmp_path / '.agents/skills/orchi/SKILL.md'; skill.write_text('User customizations')
    with pytest.raises(ValueError):
        installer.install(tmp_path)
    result = installer.install(tmp_path, replace=True)
    assert (Path(result['backup']) / '.agents/skills/orchi/SKILL.md').read_text() == 'User customizations'


def test_unrelated_skills_are_preserved(tmp_path):
    other = tmp_path / '.agents/skills/custom-skill'; other.mkdir(parents=True)
    (other / 'SKILL.md').write_text('User skill')
    installer.install(tmp_path)
    assert (other / 'SKILL.md').read_text() == 'User skill'


def test_install_symlink_rejected(tmp_path):
    outside = tmp_path / 'outside'; outside.mkdir()
    project = tmp_path / 'project'; project.mkdir()
    (project / '.agents').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        installer.install(project)
    assert list(outside.iterdir()) == []


def test_installed_knowledge_tool_runs_without_source_checkout(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'docs').mkdir(); (tmp_path / 'docs/guide.md').write_text('# Guide\nSession rules.\n')
    installer.install(tmp_path)
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="unrelated-app"\nrequires-python=">=3.99"\n')
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    script = tmp_path / '.agents/skills/orchi/scripts/knowledge.py'
    result = subprocess.run([sys.executable, str(script), 'search', 'session'], cwd=tmp_path,
                            env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert [hit['path'] for hit in json.loads(result.stdout)['results']] == ['docs/guide.md']
    lint = subprocess.run([sys.executable, str(script), 'lint'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert lint.returncode == 0, lint.stdout
    assert not list((tmp_path / '.agents').rglob('__pycache__'))


def test_copy_install_rollback_preserves_modified_skill(tmp_path, monkeypatch):
    installer.install(tmp_path)
    target = tmp_path / '.agents/skills/orchi/SKILL.md'; target.write_text('User customization')
    original_move = installer.shutil.move
    def fail_staged_move(source, destination):
        if '.orchi-stage-' in str(source): raise OSError('Injected staging failure')
        return original_move(source, destination)
    monkeypatch.setattr(installer.shutil, 'move', fail_staged_move)
    with pytest.raises(OSError):
        installer.install(tmp_path, replace=True)
    assert target.read_text() == 'User customization'
