"""Source validation and self-contained installation of the skill bundle."""
from pathlib import Path
import importlib.util
import json
import os
import shutil
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
    (tmp_path / 'CLAUDE.md').write_text('User rules')
    (tmp_path / 'AGENTS.md').write_text('Other assistant rules')
    assert installer.install(tmp_path)['status'] == 'installed'
    assert (tmp_path / 'CLAUDE.md').read_text().startswith('User rules\n\n<!-- orchi:begin -->')
    assert (tmp_path / 'AGENTS.md').read_text() == 'Other assistant rules'
    assert sorted(p.name for p in (tmp_path / '.claude/skills').iterdir()) == sorted(installer.NAMES)
    assert installer.install(tmp_path)['status'] == 'unchanged'
    installer.install(tmp_path, uninstall=True)
    assert (tmp_path / 'CLAUDE.md').read_text() == 'User rules'


def test_dry_run_no_mutation(tmp_path):
    installer.install(tmp_path, dry=True)
    assert list(tmp_path.iterdir()) == []


def test_modified_skill_refuses_silent_overwrite(tmp_path):
    installer.install(tmp_path)
    skill = tmp_path / '.claude/skills/orchi/SKILL.md'; skill.write_text('User customizations')
    with pytest.raises(ValueError):
        installer.install(tmp_path)
    result = installer.install(tmp_path, replace=True)
    assert (Path(result['backup']) / '.claude/skills/orchi/SKILL.md').read_text() == 'User customizations'


def test_unrelated_skills_are_preserved(tmp_path):
    other = tmp_path / '.claude/skills/custom-skill'; other.mkdir(parents=True)
    (other / 'SKILL.md').write_text('User skill')
    installer.install(tmp_path)
    assert (other / 'SKILL.md').read_text() == 'User skill'


def test_install_symlink_rejected(tmp_path):
    outside = tmp_path / 'outside'; outside.mkdir()
    project = tmp_path / 'project'; project.mkdir()
    (project / '.claude').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        installer.install(project)
    assert list(outside.iterdir()) == []


def test_installed_knowledge_tool_runs_without_source_checkout(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'docs').mkdir(); (tmp_path / 'docs/guide.md').write_text('# Guide\nSession rules.\n')
    installer.install(tmp_path)
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="unrelated-app"\nrequires-python=">=3.99"\n')
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    script = tmp_path / '.claude/skills/orchi/scripts/knowledge.py'
    result = subprocess.run([sys.executable, str(script), 'search', 'session'], cwd=tmp_path,
                            env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert [hit['path'] for hit in json.loads(result.stdout)['results']] == ['docs/guide.md']
    lint = subprocess.run([sys.executable, str(script), 'lint'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert lint.returncode == 0, lint.stdout
    assert not list((tmp_path / '.claude').rglob('__pycache__'))


def test_copy_install_rollback_preserves_modified_skill(tmp_path, monkeypatch):
    installer.install(tmp_path)
    target = tmp_path / '.claude/skills/orchi/SKILL.md'; target.write_text('User customization')
    original_move = installer.shutil.move
    def fail_staged_move(source, destination):
        if '.orchi-stage-' in str(source): raise OSError('Injected staging failure')
        return original_move(source, destination)
    monkeypatch.setattr(installer.shutil, 'move', fail_staged_move)
    with pytest.raises(OSError):
        installer.install(tmp_path, replace=True)
    assert target.read_text() == 'User customization'


def source_copy(tmp_path):
    """A disposable copy of the source tree, so validation failures never touch the real files."""
    validator = load_tool('validate_package')
    copy = tmp_path / 'source'
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('.git', *validator.IGNORED, '*.pyc'))
    return validator, copy


@pytest.mark.parametrize('linking, target', [
    ('skills/orchi/references/execution.md', 'skills/orchi/references/planning.md'),
    ('docs/testing.md', 'docs/installation.md'),
])
def test_renamed_heading_breaks_validation(tmp_path, linking, target):
    validator, copy = source_copy(tmp_path)
    with (copy / target).open('a', encoding='utf-8') as stream:
        stream.write('\n## Probe heading\n\nText.\n')
    with (copy / linking).open('a', encoding='utf-8') as stream:
        stream.write('\nSee [the probe](' + Path(target).name + '#probe-heading).\n')
    report = validator.validate(copy)
    assert report['ok'], report['errors']
    text = (copy / target).read_text(encoding='utf-8')
    (copy / target).write_text(text.replace('## Probe heading', '## Renamed probe'), encoding='utf-8')
    report = validator.validate(copy)
    assert not report['ok']
    assert any(error.startswith(linking + ':') and 'missing anchor' in error and '#probe-heading' in error
               for error in report['errors']), report['errors']


def test_installed_file_outside_npm_files_breaks_validation(tmp_path):
    validator, copy = source_copy(tmp_path)
    new = copy / 'skills/orchi/templates/example.md'
    new.parent.mkdir()
    new.write_text('# Example\n', encoding='utf-8')
    report = validator.validate(copy)
    assert 'Installed file missing from the npm "files" allowlist: skills/orchi/templates/example.md' in report['errors']
    package = json.loads((copy / 'package.json').read_text())
    package['files'].append('skills/orchi/templates')
    (copy / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    report = validator.validate(copy)
    assert report['ok'], report['errors']


def test_npm_files_reject_stale_and_extra_entries(tmp_path):
    validator, copy = source_copy(tmp_path)
    package = json.loads((copy / 'package.json').read_text())
    package['files'] += ['skills/orchi/missing', 'tests/**/*.py']
    (copy / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    errors = validator.validate(copy)['errors']
    assert 'npm "files" entry matches no source file: skills/orchi/missing' in errors
    assert 'npm "files" publishes a file the installer does not use: tests/test_packaging.py' in errors


@pytest.mark.skipif(shutil.which('npm') is None, reason='npm is not installed')
def test_npm_pack_publishes_what_validation_expects():
    validator = load_tool('validate_package')
    result = subprocess.run(['npm', 'pack', '--dry-run', '--json', '--ignore-scripts'], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    packed = {entry['path'] for entry in json.loads(result.stdout)[0]['files']} - {'package.json'}
    patterns = json.loads((ROOT / 'package.json').read_text())['files']
    expected = {path.relative_to(ROOT).as_posix() for path in validator.files()}
    assert packed == {path for path in expected if validator.published(patterns, path)}


def test_repository_ci_is_not_an_installed_asset():
    from orchi_core import installation
    assert installation.GITHUB_ASSETS == ROOT / 'skills/orchi/assets/github'
    assert '.github/workflows/ci.yml' not in installation.github_files()
