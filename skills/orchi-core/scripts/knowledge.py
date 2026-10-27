#!/usr/bin/env python3
"""Read-only Orchi Markdown search, exact reads, local-link validation, and documentation checks for PRs."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit


# Installed skill bundles, assistant agent definitions, and vendored trees are not project documentation.
EXCLUDED_PREFIXES = ('.agents/skills/', '.claude/skills/', '.github/skills/', '.claude/agents/')
EXCLUDED_PARTS = {'node_modules', 'vendor', '.venv', 'venv', 'site-packages'}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode('utf-8')


class Documents:
    def __init__(self, repo: Path, ref: str | None = None, prefixes: list[str] | None = None):
        self.root = Path(git(repo, 'rev-parse', '--show-toplevel').strip())
        self.revision = git(self.root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').strip() if ref else None
        if self.revision:
            self.paths = set(git(self.root, 'ls-tree', '-rz', '--name-only', self.revision).split('\0')) - {''}
        else:
            self.paths = {p for p in git(self.root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split('\0') if p and (self.root / p).is_file()}
        scope = tuple(prefix.strip('/') + '/' for prefix in prefixes or [] if prefix.strip('/'))
        self.names = sorted(p for p in self.paths if p.endswith('.md')
                            and not p.startswith(EXCLUDED_PREFIXES)
                            and not EXCLUDED_PARTS.intersection(PurePosixPath(p).parts)
                            and (not scope or p.startswith(scope)))

    def read(self, path: str) -> str:
        if path not in self.paths or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
            raise ValueError(f'Not a repository file in this snapshot: {path}')
        if self.revision:
            return git(self.root, 'show', f'{self.revision}:{path}')
        source = (self.root / path).resolve()
        if not source.is_relative_to(self.root):
            raise ValueError(f'File escapes repository: {path}')
        return source.read_bytes().decode('utf-8')

    def exists(self, path: str) -> bool:
        if path == '.':
            return True
        return path in self.paths or any(p.startswith(path.rstrip('/') + '/') for p in self.paths)


def prose(text: str, strip_code: bool = True) -> list[tuple[int, str]]:
    """Omit fenced examples and inline code from structural link checks."""
    result = []
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None:
            result.append((number, re.sub(r'(`+).*?\1', '', line) if strip_code else line))
    return result


def anchors(text: str) -> set[str]:
    found = set()
    counts: dict[str, int] = {}
    # Preserve heading code text, whose characters contribute to GitHub anchors.
    for _, line in prose(text, strip_code=False):
        heading = re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*#*$', line)
        if heading:
            slug = re.sub(r'[^\w\- ]', '', heading[1].lower()).replace(' ', '-')
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            found.add(slug + (f'-{count}' if count else ''))
        found.update(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', line))
    return found


def lint(docs: Documents) -> list[str]:
    errors = []
    for name in docs.names:
        text = docs.read(name)
        rows = prose(text)
        definitions = {}
        for _, line in rows:
            match = re.match(r'^\s{0,3}\[([^]]+)\]:\s*(<[^>]+>|\S+)', line)
            if match:
                definitions[' '.join(match[1].casefold().split())] = match[2].strip('<>')
        for number, line in rows:
            targets = re.findall(r'!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s()]*(?:\([^()]*\)[^\s()]*)*)(?:\s+["\'][^\n]*?["\'])?\s*\)', line)
            # GitHub renders an undefined reference such as [PAY][TOKEN] as literal text,
            # so only defined references are links whose targets need checking.
            for label, reference in re.findall(r'\[([^]]+)\]\[([^]]*)\]', line):
                key = ' '.join((reference or label).casefold().split())
                if key in definitions:
                    targets.append(definitions[key])
            for target in targets:
                target = target.strip('<>')
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or target.startswith('//'):
                    continue
                raw = unquote(parsed.path)
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), raw)) if raw else name
                if raw.startswith('/'):
                    resolved = posixpath.normpath(raw.lstrip('/'))
                if resolved.startswith('../') or not docs.exists(resolved):
                    errors.append(f'{name}:{number}: missing local target {target}')
                elif parsed.fragment and resolved.endswith('.md'):
                    if unquote(parsed.fragment) not in anchors(docs.read(resolved)):
                        errors.append(f'{name}:{number}: missing anchor {target}')
    return errors


def search(docs: Documents, query: str, limit: int) -> list[dict]:
    terms = list(dict.fromkeys(re.findall(r'\w+', query.casefold())))
    if not terms:
        raise ValueError('Search needs at least one word')
    hits = []
    for name in docs.names:
        content = docs.read(name)
        heading = ''
        for number, line in enumerate(content.splitlines(), 1):
            if re.match(r'^#{1,6}\s', line):
                heading = line.lstrip('# ').strip()
            context = f'{name} {heading} {line}'.casefold()
            if all(term in context for term in terms):
                hits.append({'path': name, 'line': number, 'heading': heading,
                             'snippet': line[:400], 'sha256': hashlib.sha256(content.encode()).hexdigest()})
    return hits[:limit]


def new_errors(current: list[str], baseline: list[str]) -> list[str]:
    """Errors not present in the baseline, matched by file and message because line numbers shift."""
    def key(error: str) -> str:
        name, _, rest = error.partition(':')
        return name + ':' + rest.partition(':')[2]
    remaining = Counter(map(key, baseline))
    result = []
    for error in current:
        if remaining[key(error)]:
            remaining[key(error)] -= 1
        else:
            result.append(error)
    return result


PLACEHOLDERS = {'', 'n/a', 'na', 'none', 'todo', 'tbd', '-', '...'}


def impact(body: str) -> str | None:
    """Return an error unless the PR body has a filled Documentation impact section."""
    text = re.sub(r'<!--.*?-->', '', body.replace('\r\n', '\n'), flags=re.S)
    match = re.search(r'^#{1,6}\s+Documentation impact\s*#*\s*$(.*?)(?=^#{1,6}\s|\Z)', text, re.M | re.S | re.I)
    if not match:
        return 'The PR body has no "Documentation impact" section.'
    content = ' '.join(match[1].split()).strip(' .')
    if content.casefold() in PLACEHOLDERS:
        return 'The "Documentation impact" section is empty: list the pages updated, or explain why none change.'
    return None


MAP = 'docs/README.md'
WORK = 'docs/work/'
PRODUCT = 'docs/product/'


def impact_text(body: str) -> str:
    """The Documentation impact section of a PR body, without comments; empty when missing."""
    text = re.sub(r'<!--.*?-->', '', body.replace('\r\n', '\n'), flags=re.S)
    match = re.search(r'^#{1,6}\s+Documentation impact\s*#*\s*$(.*?)(?=^#{1,6}\s|\Z)', text, re.M | re.S | re.I)
    return match[1] if match else ''


def table_rows(text: str, heading: str) -> list[dict[str, str]]:
    """The first Markdown table under `## <heading>`, as rows keyed by header."""
    section = re.search(rf'^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)', text, re.M | re.S)
    lines = [line.strip() for line in (section[1] if section else '').splitlines() if line.strip().startswith('|')]
    if len(lines) < 2:
        return []
    split = lambda line: [cell.strip().replace('`', '').strip() for cell in line.strip('|').split('|')]
    header = split(lines[0])
    return [dict(zip(header, split(line))) for line in lines[2:] if any(split(line))]


def ownership(text: str) -> list[tuple[str, list[str]]]:
    """The map's Ownership table: each code path pattern with the pages that describe it."""
    return [(row.get('Code', ''), [page.strip() for page in row.get('Pages', '').split(',') if page.strip()])
            for row in table_rows(text, 'Ownership') if row.get('Code')]


def pattern(glob: str) -> re.Pattern:
    """A path glob: `**` spans directories, `*` and `?` stay within one path segment."""
    tokens = {'**/': '(?:[^/]+/)*', '**': '.*', '*': '[^/]*', '?': '[^/]'}
    return re.compile(''.join(tokens.get(part, re.escape(part)) for part in re.split(r'(\*\*/|\*\*|\*|\?)', glob)))


def read_map(root: Path) -> str | None:
    path = root / MAP
    return path.read_text(encoding='utf-8') if path.is_file() else None


def stale_changes(root: Path, base: str, body: str) -> list[str]:
    """Owned code a change touched while its pages stayed unchanged and unexplained."""
    text = read_map(root)
    if text is None:
        return []
    changed = set(git(root, 'diff', '--name-only', f'{base}...HEAD').split())
    reason = impact_text(body)
    errors = []
    for glob, pages in ownership(text):
        code = sorted(path for path in changed if pattern(glob).fullmatch(path) and path not in pages)
        if code and not changed.intersection(pages) and not any(page in reason for page in pages):
            errors.append(f'{", ".join(pages)}: {glob} changed ({code[0]}) without this documentation; update it, '
                          'or name it in Documentation impact with the reason it still holds')
    return errors


def last_change(root: Path, *pathspec: str) -> int:
    stamp = git(root, 'log', '-1', '--format=%ct', '--', *pathspec).strip()
    return int(stamp) if stamp else 0


def stale_pages(root: Path) -> list[str]:
    """Pages whose owned code has a later commit than the page itself."""
    text = read_map(root)
    if text is None:
        return []
    errors = []
    for glob, pages in ownership(text):
        code = last_change(root, f':(glob){glob}')
        for page in pages:
            if not (root / page).is_file():
                errors.append(f'{page}: listed in {MAP} but missing')
            elif code > last_change(root, page):
                errors.append(f'{page}: {glob} changed after this page did')
    return errors


def work_files(docs: Documents) -> list[str]:
    return sorted(path for path in docs.paths if path.startswith(WORK))


def behavior(docs: Documents) -> list[str]:
    """Every acceptance test a behavior page names exists and contains its name."""
    errors = []
    for name in docs.names:
        if not name.startswith(PRODUCT):
            continue
        for heading in re.findall(r'^## (.+?)\s*$', docs.read(name), re.M):
            for row in table_rows(docs.read(name), heading):
                test = row.get('Acceptance test', '')
                if not test or test == '-':
                    continue
                path, _, title = test.partition('::')
                if path not in docs.paths:
                    errors.append(f'{name}: acceptance test file {path} does not exist')
                elif title and title not in docs.read(path):
                    errors.append(f'{name}: {path} has no test named {title!r}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--ref', help='Explicit Git revision; default is the working tree, including drafts')
    parser.add_argument('--path', action='append', default=[], help='Limit search/lint to this directory prefix (repeatable)')
    commands = parser.add_subparsers(dest='command', required=True)
    find = commands.add_parser('search')
    find.add_argument('query')
    find.add_argument('--limit', type=int, default=20)
    get = commands.add_parser('get')
    get.add_argument('path')
    get.add_argument('--sha256', help='Refuse content that changed since search')
    lint_command = commands.add_parser('lint')
    lint_command.add_argument('--since', metavar='REF', help='Fail only on errors that are not already present in REF')
    check = commands.add_parser('impact', help='Require a filled Documentation impact section in a PR body')
    check.add_argument('--body-file', help='File containing the PR body; default is the PR_BODY environment variable')
    stale = commands.add_parser('stale', help=f'Pages from the {MAP} Ownership table whose code changed without them')
    stale.add_argument('--since', metavar='REF', help='Check the changes since REF against the PR body; '
                       'without it, list pages whose code has a later commit than the page')
    stale.add_argument('--body-file', help='File containing the PR body; default is the PR_BODY environment variable')
    commands.add_parser('work', help=f'Fail when working documents ({WORK}) are present')
    commands.add_parser('behavior', help=f'Every acceptance test a page in {PRODUCT} names exists')
    args = parser.parse_args()
    body = ''
    if args.command in {'impact', 'stale'}:
        body = Path(args.body_file).read_text(encoding='utf-8') if args.body_file else os.environ.get('PR_BODY', '')
    if args.command == 'impact':
        error = impact(body)
        print(error or 'Documentation impact: recorded')
        return int(bool(error))
    try:
        if args.command == 'stale':
            root = Path(git(Path(args.repo), 'rev-parse', '--show-toplevel').strip())
            if read_map(root) is None:
                print(f'No {MAP}; nothing to check.')
                return 0
            errors = stale_changes(root, args.since, body) if args.since else stale_pages(root)
            print('\n'.join(errors) or 'Documentation is current with its code')
            return int(bool(errors))
        docs = Documents(Path(args.repo), args.ref, args.path)
        if args.command == 'get':
            content = docs.read(args.path)
            if args.sha256 and hashlib.sha256(content.encode()).hexdigest() != args.sha256:
                raise ValueError('Content hash changed; repeat search in the intended snapshot')
            print(content, end='')
        elif args.command in {'work', 'behavior'}:
            errors = work_files(docs) if args.command == 'work' else behavior(docs)
            if args.command == 'work' and errors:
                errors = [f'{path}: working documents never reach this branch; move what is settled into the '
                          'current documentation and delete the folder' for path in errors]
            print('\n'.join(errors) or ('No working documents' if args.command == 'work' else
                                         'Every named acceptance test exists'))
            return int(bool(errors))
        elif args.command == 'search':
            if not 1 <= args.limit <= 100:
                raise ValueError('limit must be between 1 and 100')
            print(json.dumps({'source': docs.revision or 'working-tree (may contain unverified drafts)',
                              'results': search(docs, args.query, args.limit)}, ensure_ascii=False, indent=2))
        else:
            errors = lint(docs)
            existing = 0
            if args.since:
                introduced = new_errors(errors, lint(Documents(Path(args.repo), args.since, args.path)))
                existing, errors = len(errors) - len(introduced), introduced
            for error in errors:
                print(error)
            summary = f'Orchi documentation lint: {len(docs.names)} files, {len(errors)} errors'
            print(summary + (f' (new since {args.since}; {existing} pre-existing ignored)' if args.since else ''))
            return int(bool(errors))
    except (ValueError, OSError, UnicodeError, subprocess.CalledProcessError) as error:
        print(f'Orchi knowledge error: {error}', file=__import__('sys').stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
