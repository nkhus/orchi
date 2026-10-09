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
SKILLS = ('orchi', 'orchi-explore', 'orchi-plan', 'orchi-deliver')
# Only the workflow skill loads implicitly; the entry skills run when the user invokes them.
IMPLICIT = {'orchi'}
IGNORED = {'__pycache__', '.pytest_cache', '.venv', '.git', 'reports', 'build', 'dist', 'node_modules'}
# The npm package publishes the installed skills plus these wrapper files, and nothing else.
WRAPPER_FILES = {'bin/orchi.js', 'tools/install.py'}
PUBLISHED_EXTRAS = {'README.md'}
SKILL_LINES = 100
sys.path.insert(0, str(ROOT / 'skills/orchi/scripts'))
import knowledge  # noqa: E402  (the installed link/anchor lint, reused rather than reimplemented)


def files(root: Path = ROOT) -> list[Path]:
    return [p for p in sorted(root.rglob('*')) if p.is_file()
            and not any(part in IGNORED or part.endswith('.egg-info') for part in p.relative_to(root).parts)
            and p.suffix not in {'.pyc', '.pyo'}]


class SourceDocuments(knowledge.Documents):
    """The validated source files as a knowledge.py document set, so links and anchors use its lint."""

    def __init__(self, root: Path, source_files: list[Path]):
        self.root, self.revision = root, None
        self.paths = {p.relative_to(root).as_posix() for p in source_files}
        self.names = sorted(p for p in self.paths if p.endswith('.md'))


def glob_pattern(pattern: str) -> re.Pattern:
    """An npm `files` entry: `**` spans directories, `*` and `?` stay within one path segment."""
    parts = re.split(r'(\*\*/|\*\*|\*|\?)', pattern.strip('/'))
    tokens = {'**/': '(?:[^/]+/)*', '**': '.*', '*': '[^/]*', '?': '[^/]'}
    return re.compile(''.join(tokens.get(part, re.escape(part)) for part in parts))


def published(patterns: list[str], path: str) -> bool:
    """Whether npm publishes a path: it matches an entry, or lies inside a directory an entry matches."""
    prefixes = [path.split('/')[:n] for n in range(1, path.count('/') + 2)]
    return any(glob_pattern(pattern).fullmatch('/'.join(prefix)) for pattern in patterns for prefix in prefixes)


def package_file_errors(root: Path, patterns: list, source_files: list[Path]) -> list[str]:
    """Every installed file is published, every entry matches something, and nothing else is published."""
    from orchi_core import installation
    if not isinstance(patterns, list) or not all(isinstance(p, str) and p for p in patterns):
        return ['package.json "files" must be a list of path patterns']
    required = set(WRAPPER_FILES)
    for name in installation.NAMES:
        required.update(f'skills/{name}/{relative}' for relative in installation.inventory(root / 'skills' / name))
    sources = [p.relative_to(root).as_posix() for p in source_files]
    errors = ['Installed file missing from the npm "files" allowlist: ' + path
              for path in sorted(required) if not published(patterns, path)]
    errors += ['npm "files" entry matches no source file: ' + pattern
               for pattern in patterns if not any(published([pattern], path) for path in sources)]
    errors += ['npm "files" publishes a file the installer does not use: ' + path for path in sources
               if published(patterns, path) and path not in required | PUBLISHED_EXTRAS]
    return errors


def third_party_imports(text: str) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            modules.add(node.module.split('.')[0])
    return modules - set(sys.stdlib_module_names) - {'orchi_core', '__future__'}


def validate_roles() -> tuple[list[str], int]:
    """Every role source renders to a Claude Code agent that carries its instructions."""
    from orchi_core import roles
    errors: list[str] = []
    try:
        loaded = roles.load_roles()
    except (OSError, ValueError) as exc:
        return ['Role sources: ' + str(exc)], 0
    skill = '/home/user/.claude/skills/orchi'
    for role in loaded:
        body = roles.instructions(role, skill)
        if roles.PLACEHOLDER in body or skill not in body:
            errors.append('Role instructions must name the Orchi skill through ' + roles.PLACEHOLDER + ': ' + role.name)
        try:
            claude = roles.render_claude(role, skill)
            meta = yaml.safe_load(claude.split('---', 2)[1])
            if meta.get('name') != role.name or meta.get('description') != role.meta['description']:
                errors.append('Claude agent front matter does not match its role: ' + role.name)
            if not claude.endswith(body):
                errors.append('Claude agent does not carry its role instructions: ' + role.name)
        except (yaml.YAMLError, IndexError, AttributeError) as exc:
            errors.append(role.name + ': ' + str(exc))
    return errors, len(loaded)


def validate(root: Path = ROOT) -> dict:
    errors: list[str] = []
    compiled = 0
    source_files = files(root)
    if sorted(p.name for p in (root / 'skills').iterdir() if p.is_dir()) != sorted(SKILLS):
        errors.append('Unexpected skill set')
    for name in SKILLS:
        try:
            folder = root / 'skills' / name
            text = (folder / 'SKILL.md').read_text()
            metadata = yaml.safe_load(text.split('---', 2)[1])
            if metadata.get('name') != name or not metadata.get('description') or len(text.splitlines()) > SKILL_LINES:
                errors.append('Invalid skill metadata or oversized instructions: ' + name)
            if len(metadata['description']) > 1024: errors.append('Skill description exceeds 1024 characters: ' + name)
            if name in IMPLICIT and metadata.get('disable-model-invocation'):
                errors.append('Entrypoint must allow implicit use: ' + name)
            if name not in IMPLICIT and metadata.get('disable-model-invocation') is not True:
                errors.append('Entry skill must be explicit-only: ' + name)
            if (folder / 'agents').exists(): errors.append('Unexpected assistant interface metadata: ' + name)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc: errors.append(name + ': ' + str(exc))
    for file in source_files:
        rel = file.relative_to(root).as_posix()
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
                if file.relative_to(root).parts[0] == 'skills' and not target.is_relative_to(root / 'skills'):
                    errors.append(rel + ': installed reference escapes the skill bundle: ' + link)
    # Skills route agents by heading anchors, so a renamed heading must fail like a missing file.
    errors.extend(knowledge.lint(SourceDocuments(root, source_files)))
    role_errors, role_count = validate_roles()
    errors.extend(role_errors)
    config = tomllib.loads((root / 'pyproject.toml').read_text())
    if 'project' in config or 'build-system' in config:
        errors.append('The installed skill must not require a Python application package')
    try:
        package = json.loads((root / 'package.json').read_text())
        if package.get('name') != '@nkhus/orchi' or package.get('bin') != {'orchi': 'bin/orchi.js'}:
            errors.append('Invalid npm installer identity or executable')
        from orchi_core.agents import VERSION
        if package.get('version') != VERSION:
            errors.append('package.json version differs from the bundled installer version')
        errors.extend(package_file_errors(root, package.get('files'), source_files))
        if package.get('dependencies') or package.get('devDependencies'):
            errors.append('The npm installer must remain dependency-free')
        if {'preinstall', 'install', 'postinstall'} & package.get('scripts', {}).keys():
            errors.append('The npm installer must not use lifecycle installation scripts')
    except (OSError, ValueError, TypeError) as exc:
        errors.append('package.json: ' + str(exc))
    for unwanted in ('CHANGELOG.md', 'CHECKSUMS.json', 'schemas'):
        if (root / unwanted).exists(): errors.append('Unexpected source artifact: ' + unwanted)
    return {'ok': not errors, 'errors': errors, 'python_files_compiled': compiled,
            'skills': len(SKILLS), 'roles': role_count, 'files': len(source_files)}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
