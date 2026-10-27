"""Behavioral tests for the documentation checks that keep project context current: stale, work, and behavior."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from knowledge import Documents, behavior, ownership, stale_changes, stale_pages, work_files

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/orchi-core/scripts/knowledge.py'
MAP = """# Documentation

## Ownership

| Code | Pages | Area |
| --- | --- | --- |
| `src/cart/**` | `docs/cart/README.md`, `docs/product/cart.md` | Cart |
| `src/auth/*.ts` | `docs/auth/README.md` | Sign-in |
"""


def git(root, *args, when=None):
    env = dict(os.environ)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True, env=env).stdout


def commit(root, when=None):
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'change', when=when)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    write(tmp_path, 'docs/README.md', MAP)
    write(tmp_path, 'docs/cart/README.md', '# Cart\n')
    write(tmp_path, 'docs/product/cart.md', '# Cart\n')
    write(tmp_path, 'docs/auth/README.md', '# Sign-in\n')
    write(tmp_path, 'src/cart/total.ts', 'export const total = 1;\n')
    write(tmp_path, 'src/auth/login.ts', 'export const login = 1;\n')
    commit(tmp_path, when='2026-10-01T10:00:00')
    git(tmp_path, 'checkout', '-qb', 'feature')
    return tmp_path


def test_ownership_reads_code_patterns_and_pages():
    assert ownership(MAP) == [('src/cart/**', ['docs/cart/README.md', 'docs/product/cart.md']),
                              ('src/auth/*.ts', ['docs/auth/README.md'])]


def test_changed_code_without_its_page_is_stale_until_named_with_a_reason(repo):
    write(repo, 'src/cart/rules/discount.ts', 'export const discount = 0;\n')
    commit(repo)
    errors = stale_changes(repo, 'main', '## Documentation impact\n\nNone.\n')
    assert errors == ['docs/cart/README.md, docs/product/cart.md: src/cart/** changed (src/cart/rules/discount.ts) '
                      'without this documentation; update it, or name it in Documentation impact with the reason '
                      'it still holds']
    reason = '## Documentation impact\n\ndocs/cart/README.md still holds: an internal constant.\n'
    assert stale_changes(repo, 'main', reason) == []


def test_changed_code_with_its_page_is_current(repo):
    write(repo, 'src/auth/login.ts', 'export const login = 2;\n')
    write(repo, 'docs/auth/README.md', '# Sign-in\n\nNew behavior.\n')
    write(repo, 'src/auth/nested/token.ts', 'export const token = 1;\n')
    commit(repo)
    assert stale_changes(repo, 'main', '') == []


def test_weekly_run_lists_pages_older_than_their_code(repo):
    write(repo, 'src/cart/total.ts', 'export const total = 2;\n')
    commit(repo, when='2026-10-20T10:00:00')
    (repo / 'docs/auth/README.md').unlink()
    commit(repo, when='2026-10-21T10:00:00')
    assert stale_pages(repo) == ['docs/cart/README.md: src/cart/** changed after this page did',
                                 'docs/product/cart.md: src/cart/** changed after this page did',
                                 'docs/auth/README.md: listed in docs/README.md but missing']


def test_working_documents_are_found_anywhere_under_docs_work(repo):
    assert work_files(Documents(repo)) == []
    write(repo, 'docs/work/pay-tokens/research/vault.md', '# Vault\n')
    write(repo, 'docs/work/pay-tokens/data.json', '{}\n')
    assert work_files(Documents(repo)) == ['docs/work/pay-tokens/data.json', 'docs/work/pay-tokens/research/vault.md']


def test_behavior_pages_name_existing_acceptance_tests(repo):
    write(repo, 'e2e/cart.spec.ts', 'test("adds an item to the cart", async () => {});\n')
    write(repo, 'docs/product/cart.md', """# Cart

## Behavior

| Criterion | Acceptance test |
| --- | --- |
| A shopper adds an item and sees it in the cart | `e2e/cart.spec.ts::adds an item to the cart` |
| A shopper removes an item | `e2e/cart.spec.ts::removes an item` |
| The cart survives a reload | `e2e/reload.spec.ts` |
| Prices show in the shopper's currency | - |
""")
    assert behavior(Documents(repo)) == ["docs/product/cart.md: e2e/cart.spec.ts has no test named 'removes an item'",
                                         'docs/product/cart.md: acceptance test file e2e/reload.spec.ts does not exist']


def run(repo, *args, body=''):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True,
                          env={**os.environ, 'PR_BODY': body})


def test_commands_exit_by_their_findings(repo):
    write(repo, 'src/cart/total.ts', 'export const total = 3;\n')
    write(repo, 'docs/work/cart/README.md', '# Plan\n')
    commit(repo)
    stale = run(repo, 'stale', '--since', 'main')
    assert stale.returncode == 1 and 'src/cart/** changed' in stale.stdout
    work = run(repo, 'work')
    assert work.returncode == 1 and 'docs/work/cart/README.md: working documents never reach this branch' in work.stdout
    assert run(repo, 'behavior').returncode == 0
    (repo / 'docs/README.md').unlink()
    assert run(repo, 'stale').stdout.strip() == 'No docs/README.md; nothing to check.'


def prose(relative):
    return " ".join((ROOT / relative).read_text().split())


def test_context_wording_agrees_across_exploration_planning_and_delivery():
    """Text, not behavior: working folders, decision fates, promotion, and the checks are wired through."""
    from orchi_core import installation
    knowledge = prose('skills/orchi-core/references/knowledge.md')
    assert "a decision that no longer holds is not kept" in knowledge
    assert "`knowledge.py work` fails while anything under `docs/work/` is present" in knowledge
    assert "never by the work that produced them" in knowledge
    exploration = prose('skills/orchi-core/references/exploration.md')
    assert "one branch, `explore/<slug>` from main, holds its working folder `docs/work/<slug>/`" in exploration
    assert "Write each verified finding to `research/<question>.md`" in exploration
    assert "creates its Initiative or Epic branch from `explore/<slug>`" in exploration
    assert "give each of its decisions (D1, D2, ...) a fate" in prose('skills/orchi-core/references/planning.md')
    plan = prose('skills/orchi-plan/SKILL.md')
    assert "`docs/work/<tag>-<slug>/README.md`" in plan and "from `explore/<slug>`" in plan
    review = prose('skills/orchi-core/references/review-delivery.md')
    assert "`knowledge.py work` must pass" in review and "move the rest of the working folder there and delete it" in review
    docs = (installation.GITHUB_ASSETS / 'workflows/orchi-docs.yml').read_text()
    assert 'knowledge.py stale --since "origin/$BASE_REF"' in docs and 'knowledge.py behavior' in docs
    assert 'if: github.base_ref == github.event.repository.default_branch' in docs
    assert 'knowledge.py stale 2>&1' in (installation.GITHUB_ASSETS / 'workflows/orchi-standards.yml').read_text()
    assert "`docs/work/`" in installation.instruction_blocks(ROOT, False)["CLAUDE.md"]
    for path in (ROOT / 'skills').rglob('*'):
        if path.is_file() and path.suffix in {'.md', '.yml', '.py'}:
            assert 'docs/initiatives/' not in path.read_text(), path
