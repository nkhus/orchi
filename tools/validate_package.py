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
SKILLS = ('orchi', 'orchi-plan', 'orchi-deliver')
# Only the workflow skill loads implicitly; the entry skills run when the user invokes them.
IMPLICIT = {'orchi'}
IGNORED = {'__pycache__', '.pytest_cache', '.venv', '.git', 'reports', 'build', 'dist', 'node_modules'}
PACKAGE_FILES = ['bin/orchi.js', 'tools/install.py', 'skills/orchi/SKILL.md', 'skills/orchi/agents/openai.yaml',
                 'skills/orchi/assets', 'skills/orchi/references', 'skills/orchi/roles', 'skills/orchi/scripts/**/*.py',
                 'skills/orchi-plan', 'skills/orchi-deliver', 'README.md']
SKILL_LINES = 100


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


def validate_roles() -> tuple[list[str], int]:
    """Every role source renders to a Claude agent and a Codex agent that parse back to its instructions."""
    sys.path.insert(0, str(ROOT / 'skills/orchi/scripts'))
    from orchi_core import roles
    errors: list[str] = []
    try:
        loaded = roles.load_roles()
    except (OSError, ValueError) as exc:
        return ['Role sources: ' + str(exc)], 0
    skill = '/home/user/.agents/skills/orchi'
    for role in loaded:
        body = roles.instructions(role, skill)
        if roles.PLACEHOLDER in body or skill not in body:
            errors.append('Role instructions must name the Orchi skill through ' + roles.PLACEHOLDER + ': ' + role.name)
        try:
            codex = tomllib.loads(roles.render_codex(role, skill))
            if codex.get('developer_instructions') != body or codex.get('name') != role.name:
                errors.append('Codex agent does not round-trip its role: ' + role.name)
            claude = roles.render_claude(role, skill)
            meta = yaml.safe_load(claude.split('---', 2)[1])
            if meta.get('name') != role.name or meta.get('description') != role.meta['description']:
                errors.append('Claude agent front matter does not match its role: ' + role.name)
            if not claude.endswith(body):
                errors.append('Claude agent does not carry its role instructions: ' + role.name)
        except (tomllib.TOMLDecodeError, yaml.YAMLError, IndexError, AttributeError) as exc:
            errors.append(role.name + ': ' + str(exc))
    return errors, len(loaded)


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
            if metadata.get('name') != name or not metadata.get('description') or len(text.splitlines()) > SKILL_LINES:
                errors.append('Invalid skill metadata or oversized instructions: ' + name)
            if len(metadata['description']) > 1024: errors.append('Skill description exceeds 1024 characters: ' + name)
            if not 25 <= len(ui['interface']['short_description']) <= 64: errors.append('Invalid interface description: ' + name)
            if '$' + name not in ui['interface']['default_prompt']: errors.append('Missing invocation example: ' + name)
            if name in IMPLICIT and ui['policy']['allow_implicit_invocation'] is not True:
                errors.append('Entrypoint must allow implicit use: ' + name)
            if name not in IMPLICIT and ui['policy']['allow_implicit_invocation'] is not False:
                errors.append('Entry skill must be explicit-only: ' + name)
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
    role_errors, role_count = validate_roles()
    errors.extend(role_errors)
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    if 'project' in config or 'build-system' in config:
        errors.append('The installed skill must not require a Python application package')
    try:
        package = json.loads((ROOT / 'package.json').read_text())
        if package.get('name') != '@nkhus/orchi' or package.get('bin') != {'orchi': 'bin/orchi.js'}:
            errors.append('Invalid npm installer identity or executable')
        sys.path.insert(0, str(ROOT / 'skills/orchi/scripts'))
        from orchi_core.agents import VERSION
        if package.get('version') != VERSION:
            errors.append('package.json version differs from the bundled installer version')
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
            'skills': len(SKILLS), 'roles': role_count, 'files': len(source_files)}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
