#!/usr/bin/env python3
"""Offline source checks for contracts, installed resources, links, and English text."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/orchi/scripts'))
from orchi_core.models import CONTRACTS

SKILLS = ('orchi', 'orchi-plan', 'orchi-work', 'orchi-review', 'orchi-deliver')
IGNORED = {'__pycache__', '.pytest_cache', '.venv', '.git', 'reports', 'build', 'dist', 'node_modules'}


def files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file()
            and not any(part in IGNORED or part.endswith('.egg-info') for part in p.relative_to(ROOT).parts)
            and p.suffix not in {'.pyc', '.pyo'}]


def inline_metadata(path: Path) -> dict:
    match = re.search(r'^# /// script\n(.*?)^# ///$', path.read_text(), re.M | re.S)
    if not match:
        raise ValueError('Missing inline script metadata: ' + str(path))
    return tomllib.loads('\n'.join(line.removeprefix('# ').removeprefix('#') for line in match[1].splitlines()))


def validate() -> dict:
    errors: list[str] = []
    compiled = 0
    source_files = files()
    for name, model in CONTRACTS.items():
        try:
            actual = json.loads((ROOT / 'schemas' / (name + '.schema.json')).read_text())
            if actual != model.model_json_schema(): errors.append('Schema drift: ' + name)
        except (OSError, ValueError) as exc: errors.append(str(exc))
    if sorted(p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()) != sorted(SKILLS):
        errors.append('Unexpected skill set')
    for name in SKILLS:
        try:
            folder = ROOT / 'skills' / name
            text = (folder / 'SKILL.md').read_text()
            metadata = yaml.safe_load(text.split('---', 2)[1])
            ui = yaml.safe_load((folder / 'agents/openai.yaml').read_text())
            if metadata.get('name') != name or not metadata.get('description') or len(text.splitlines()) >= 60:
                errors.append('Invalid skill metadata or oversized instructions: ' + name)
            if not 25 <= len(ui['interface']['short_description']) <= 64: errors.append('Invalid interface description: ' + name)
            if '$' + name not in ui['interface']['default_prompt']: errors.append('Missing invocation example: ' + name)
            if ui['policy']['allow_implicit_invocation'] != (name == 'orchi'): errors.append('Ambiguous implicit routing: ' + name)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc: errors.append(name + ': ' + str(exc))
    for file in source_files:
        rel = file.relative_to(ROOT).as_posix()
        try: text = file.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            errors.append(rel + ': ' + str(exc)); continue
        if re.search(r'[\u0400-\u052f]', text): errors.append('Non-English repository text: ' + rel)
        if re.search(r'\borchi-[a-z-]+/\d+', text) or re.search(r'\bOrchi[^\n]{0,30}\bv?\d+\.\d+\.\d+', text):
            errors.append('Product release marker: ' + rel)
        if file.suffix == '.py':
            try: compile(text, str(file), 'exec'); compiled += 1
            except SyntaxError as exc: errors.append(str(exc))
        if file.suffix == '.json':
            try: json.loads(text)
            except ValueError as exc: errors.append(rel + ': ' + str(exc))
        if file.suffix in {'.yaml', '.yml'}:
            try: yaml.safe_load(text)
            except yaml.YAMLError as exc: errors.append(rel + ': ' + str(exc))
        if file.suffix == '.md':
            prose = re.sub(r'```.*?```', '', text, flags=re.S)
            for link in re.findall(r'\]\(([^\s)]+)\)', prose):
                if ':' in link or link.startswith('#'): continue
                target = (file.parent / link.split('#')[0]).resolve()
                if not target.exists(): errors.append(rel + ': missing ' + link)
                if file.relative_to(ROOT).parts[0] == 'skills' and not target.is_relative_to(ROOT / 'skills'):
                    errors.append(rel + ': installed reference escapes the skill bundle: ' + link)
    requirements = (ROOT / 'skills/orchi/scripts/requirements.txt').read_text().splitlines()
    for entrypoint in ('orchi.py', 'operator.py'):
        try:
            metadata = inline_metadata(ROOT / 'skills/orchi/scripts' / entrypoint)
            if metadata.get('requires-python') != '>=3.11' or metadata.get('dependencies') != requirements:
                errors.append('Dependency metadata drift: ' + entrypoint)
        except ValueError as exc: errors.append(str(exc))
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    if 'project' in config or 'build-system' in config:
        errors.append('The installed runtime must not require a Python application package')
    try:
        package = json.loads((ROOT / 'package.json').read_text())
        if package.get('name') != '@nkhus/orchi' or package.get('bin') != {'orchi': 'bin/orchi.js'}:
            errors.append('Invalid npm installer identity or executable')
        expected_files = ['bin/orchi.js', 'tools/install.py', 'skills/*/SKILL.md',
                          'skills/*/agents/openai.yaml', 'skills/orchi/assets',
                          'skills/orchi/references', 'skills/orchi/scripts/**/*.py',
                          'skills/orchi/scripts/requirements.txt', 'README.md']
        if package.get('files') != expected_files:
            errors.append('The npm publish allowlist must contain only installer resources')
        if package.get('dependencies') or package.get('devDependencies'):
            errors.append('The npm installer must remain dependency-free')
        if {'preinstall', 'install', 'postinstall'} & package.get('scripts', {}).keys():
            errors.append('The npm installer must not use lifecycle installation scripts')
    except (OSError, ValueError, TypeError) as exc:
        errors.append('package.json: ' + str(exc))
    for unwanted in ('CHANGELOG.md', 'docs/migration.md', 'docs/target-design.md', 'CHECKSUMS.json'):
        if (ROOT / unwanted).exists(): errors.append('Unexpected source artifact: ' + unwanted)
    return {'ok': not errors, 'errors': errors, 'python_files_compiled': compiled,
            'schemas': len(CONTRACTS), 'skills': len(SKILLS), 'files': len(source_files)}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
