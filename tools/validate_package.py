#!/usr/bin/env python3
"""Offline source checks for the skill bundle, links, installer package, and English text."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('orchi',)
IGNORED = {'__pycache__', '.pytest_cache', '.venv', '.git', 'reports', 'build', 'dist', 'node_modules'}
PACKAGE_FILES = ['bin/orchi.js', 'tools/install.py', 'skills/orchi/SKILL.md', 'skills/orchi/agents/openai.yaml',
                 'skills/orchi/references', 'skills/orchi/scripts/**/*.py', 'README.md']


def files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file()
            and not any(part in IGNORED or part.endswith('.egg-info') for part in p.relative_to(ROOT).parts)
            and p.suffix not in {'.pyc', '.pyo'}]


def third_party_imports(text: str) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            modules.add(node.module.split('.')[0])
    return modules - set(sys.stdlib_module_names) - {'orchi_core', '__future__'}


def validate() -> dict:
    errors: list[str] = []
    compiled = 0
    source_files = files()
    if sorted(p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()) != sorted(SKILLS):
        errors.append('Unexpected skill set')
    for name in SKILLS:
        try:
            folder = ROOT / 'skills' / name
            text = (folder / 'SKILL.md').read_text()
            metadata = yaml.safe_load(text.split('---', 2)[1])
            ui = yaml.safe_load((folder / 'agents/openai.yaml').read_text())
            if metadata.get('name') != name or not metadata.get('description') or len(text.splitlines()) >= 250:
                errors.append('Invalid skill metadata or oversized instructions: ' + name)
            if len(metadata['description']) > 1024: errors.append('Skill description exceeds 1024 characters: ' + name)
            if not 25 <= len(ui['interface']['short_description']) <= 64: errors.append('Invalid interface description: ' + name)
            if '$' + name not in ui['interface']['default_prompt']: errors.append('Missing invocation example: ' + name)
            if ui['policy']['allow_implicit_invocation'] is not True: errors.append('Entrypoint must allow implicit use: ' + name)
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
            try:
                compile(text, str(file), 'exec'); compiled += 1
                if rel.startswith('skills/') and third_party_imports(text):
                    errors.append(rel + ': installed scripts must use only the standard library: '
                                  + ', '.join(sorted(third_party_imports(text))))
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
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    if 'project' in config or 'build-system' in config:
        errors.append('The installed skill must not require a Python application package')
    try:
        package = json.loads((ROOT / 'package.json').read_text())
        if package.get('name') != '@nkhus/orchi' or package.get('bin') != {'orchi': 'bin/orchi.js'}:
            errors.append('Invalid npm installer identity or executable')
        if package.get('files') != PACKAGE_FILES:
            errors.append('The npm publish allowlist must contain only installer resources')
        if package.get('dependencies') or package.get('devDependencies'):
            errors.append('The npm installer must remain dependency-free')
        if {'preinstall', 'install', 'postinstall'} & package.get('scripts', {}).keys():
            errors.append('The npm installer must not use lifecycle installation scripts')
    except (OSError, ValueError, TypeError) as exc:
        errors.append('package.json: ' + str(exc))
    for unwanted in ('CHANGELOG.md', 'CHECKSUMS.json', 'schemas'):
        if (ROOT / unwanted).exists(): errors.append('Unexpected source artifact: ' + unwanted)
    return {'ok': not errors, 'errors': errors, 'python_files_compiled': compiled,
            'skills': len(SKILLS), 'files': len(source_files)}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
