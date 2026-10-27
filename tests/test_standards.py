"""Behavioral tests for standards.py: declared checks against CI, the gate ratchet, and the ruleset."""
import datetime
import json
from pathlib import Path
import subprocess

import pytest

import standards

ROOT = Path(__file__).resolve().parents[1]
TODAY = datetime.date(2026, 10, 27)
DOCUMENT = """# Engineering

## Checks

| Check | Tool | Command | CI job | Config | Threshold | Blocking |
| --- | --- | --- | --- | --- | --- | --- |
| Lint | ESLint | `pnpm lint` | lint | eslint.config.mjs | - | yes |
| Coverage | Vitest | `pnpm coverage:changed` | test | - | >= 90 | yes |
| File size | ESLint | `pnpm lint` | lint | eslint.config.mjs | <= 300 | yes |
| Mutation | Stryker | `pnpm mutation` | mutation | - | - | weekly |

## Exceptions

| Rule | Where | Reason | Expires |
| --- | --- | --- | --- |
{exceptions}
"""
CI = """name: CI
on:
  pull_request:
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm lint
  test:
    name: Unit tests
    runs-on: ubuntu-latest
    steps:
      - run: |
          pnpm test
          pnpm coverage:changed
"""
WEEKLY = """name: Weekly
on:
  schedule:
    - cron: "0 6 * * 1"
jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm mutation
"""


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout


def commit(root, message='change'):
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', message)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    write(tmp_path, 'ENGINEERING.md', DOCUMENT.format(exceptions=''))
    write(tmp_path, '.github/workflows/ci.yml', CI)
    write(tmp_path, '.github/workflows/weekly.yml', WEEKLY)
    write(tmp_path, 'eslint.config.mjs', 'export default [{ rules: { "no-console": "error" } }];\n')
    write(tmp_path, 'src/cart.ts', 'export const total = (a: number, b: number) => a + b;\n')
    write(tmp_path, 'src/cart.test.ts', 'test("adds", () => {\n  expect(total(1, 2)).toBe(3);\n  expect(total(0, 0)).toBe(0);\n});\n')
    commit(tmp_path, 'baseline')
    git(tmp_path, 'checkout', '-qb', 'feature')
    return tmp_path


def test_check_passes_when_every_declared_check_runs_in_ci(repo):
    assert standards.check(repo, TODAY) == {'ok': True, 'findings': []}


def test_check_reports_missing_job_command_config_and_schedule(repo):
    write(repo, '.github/workflows/ci.yml', CI.replace('pnpm lint', 'pnpm eslint .'))
    write(repo, '.github/workflows/weekly.yml', WEEKLY.replace('schedule:\n    - cron: "0 6 * * 1"', 'pull_request:'))
    (repo / 'eslint.config.mjs').unlink()
    text = (repo / 'ENGINEERING.md').read_text()
    write(repo, 'ENGINEERING.md', text.replace('| Mutation |', '| Dead code | knip | `pnpm knip` | dead-code | - | - | yes |\n| Mutation |'))
    findings = standards.check(repo, TODAY)['findings']
    assert '.github/workflows/ci.yml: checks: Lint: job `lint` does not run `pnpm lint`' in findings
    assert 'eslint.config.mjs: checks: Lint: configuration file is not committed' in findings
    assert 'ENGINEERING.md: checks: Dead code: no CI job `dead-code` in .github/workflows/' in findings
    assert '.github/workflows/weekly.yml: checks: Mutation: job `mutation` is not scheduled' in findings


def test_check_fails_on_an_expired_or_undated_exception(repo):
    rows = '| no-console | src/log.ts | CLI output | 2026-10-01 |\n| noqa | tools/*.py | generated | soon |'
    write(repo, 'ENGINEERING.md', DOCUMENT.format(exceptions=rows))
    findings = standards.check(repo, TODAY)['findings']
    assert findings == ['src/log.ts: exceptions: no-console: expired on 2026-10-01',
                        'tools/*.py: exceptions: noqa: Expires is not a date']


def test_without_engineering_document_nothing_is_checked(tmp_path):
    git(tmp_path, 'init', '-q')
    assert standards.check(tmp_path, TODAY)['ok']
    assert standards.ratchet(tmp_path, 'HEAD')['note'] == 'No ENGINEERING.md; nothing to check.'


def test_ratchet_passes_a_change_that_weakens_nothing(repo):
    write(repo, 'src/cart.ts', 'export const total = (a: number, b: number): number => a + b;\n')
    commit(repo)
    assert standards.ratchet(repo, 'main') == {'ok': True, 'findings': [], 'exceptions': []}


def test_ratchet_fails_on_suppressions_until_an_exception_names_them(repo):
    write(repo, 'src/cart.ts', '// eslint-disable-next-line no-console\nconsole.log(1);\n// @ts-ignore\nexport const x = 1;\n')
    write(repo, 'src/cart.test.ts', (repo / 'src/cart.test.ts').read_text() + 'test.skip("later", () => {\n  expect(1).toBe(1);\n});\n')
    commit(repo)
    result = standards.ratchet(repo, 'main')
    assert not result['ok']
    assert {line.split(': ')[1] for line in result['findings']} == {'eslint-disable', 'ts-ignore', 'test-skip'}
    rows = ('| no-console | src/cart.ts | CLI prints the total | 2026-12-31 |\n'
            '| ts-ignore | src/cart.ts | untyped vendor module | 2026-12-31 |\n'
            '| test-skip | src/*.test.ts | flaky upstream | 2026-11-15 |')
    write(repo, 'ENGINEERING.md', DOCUMENT.format(exceptions=rows))
    commit(repo)
    result = standards.ratchet(repo, 'main')
    assert result['ok'], result
    assert result['exceptions'][0] == 'no-console in src/cart.ts until 2026-12-31: CLI prints the total'


def test_ratchet_fails_when_engineering_document_loosens_a_check(repo):
    text = DOCUMENT.format(exceptions='')
    text = text.replace('| >= 90 | yes |', '| >= 80 | yes |').replace('| <= 300 | yes |', '| <= 400 | yes |')
    text = text.replace('| mutation | - | - | weekly |', '| mutation | - | - | no |')
    text = text.replace('| Lint | ESLint | `pnpm lint` | lint | eslint.config.mjs | - | yes |\n', '')
    write(repo, 'ENGINEERING.md', text)
    commit(repo)
    findings = standards.ratchet(repo, 'main')['findings']
    assert findings == ['ENGINEERING.md: check removed: Lint',
                        'ENGINEERING.md: threshold: Coverage: >= 90 -> >= 80',
                        'ENGINEERING.md: threshold: File size: <= 300 -> <= 400',
                        'ENGINEERING.md: non-blocking: Mutation: weekly -> no']


def test_ratchet_allows_tightening_a_threshold(repo):
    write(repo, 'ENGINEERING.md', DOCUMENT.format(exceptions='').replace('>= 90', '>= 95').replace('<= 300', '<= 250'))
    commit(repo)
    assert standards.ratchet(repo, 'main')['ok']


def test_ratchet_fails_when_a_declared_configuration_turns_a_rule_off(repo):
    write(repo, 'eslint.config.mjs', 'export default [{ rules: { "no-console": "off" } }];\n')
    commit(repo)
    assert standards.ratchet(repo, 'main')['findings'] == [
        'eslint.config.mjs: config: export default [{ rules: { "no-console": "off" } }];']


def test_ratchet_fails_on_deleted_tests_and_lost_assertions(repo):
    write(repo, 'src/cart.test.ts', 'test("adds", () => {\n  expect(total(1, 2)).toBe(3);\n});\n')
    write(repo, 'tests/checkout.spec.ts', 'test("pays", () => {\n  expect(true).toBe(true);\n});\n')
    commit(repo)
    git(repo, 'checkout', '-q', '-b', 'later')
    (repo / 'tests/checkout.spec.ts').unlink()
    commit(repo)
    assert standards.ratchet(repo, 'feature')['findings'] == [
        'tests/checkout.spec.ts: test deleted: test file deleted without the code it covers']
    assert standards.ratchet(repo, 'main')['findings'] == ['src/cart.test.ts: assertions removed: 1 fewer assertions']


def test_ratchet_accepts_a_test_deleted_with_its_code(repo):
    (repo / 'src/cart.ts').unlink()
    (repo / 'src/cart.test.ts').unlink()
    commit(repo)
    assert standards.ratchet(repo, 'main')['ok']


def test_ruleset_requires_blocking_jobs_by_their_status_check_names(repo, capsys):
    assert standards.main(['--root', str(repo), 'ruleset']) == 0
    ruleset = json.loads(capsys.readouterr().out)
    required = next(rule for rule in ruleset['rules'] if rule['type'] == 'required_status_checks')
    assert required['parameters']['required_status_checks'] == [{'context': 'Unit tests'}, {'context': 'lint'}]
    assert {rule['type'] for rule in ruleset['rules']} >= {'deletion', 'non_fast_forward', 'required_linear_history'}


def test_main_exits_one_on_findings_and_prints_them(repo, capsys):
    (repo / 'eslint.config.mjs').unlink()
    assert standards.main(['--root', str(repo), 'check', '--today', '2026-10-27']) == 1
    assert 'configuration file is not committed' in capsys.readouterr().out


def test_template_declares_valid_checks_and_the_installed_impeccable():
    from orchi_core import installation
    text = (ROOT / 'skills/orchi-core/assets/standards/ENGINEERING.md').read_text()
    rows = standards.checks(text)
    assert rows and all(row['Blocking'] in standards.BLOCKING for row in rows)
    assert all(row['Threshold'] == '-' or standards.THRESHOLD.match(row['Threshold']) for row in rows)
    assert f"impeccable@{installation.IMPECCABLE} detect" in text
    assert standards.exceptions(text) == []


def prose(relative):
    return " ".join((ROOT / relative).read_text().split())


def test_standards_wording_agrees_across_planning_delivery_and_roles():
    """Text, not behavior: the standards track is wired into every stage that reads it."""
    from orchi_core import installation
    planning, plan = prose('skills/orchi-core/references/planning.md'), prose('skills/orchi-plan/SKILL.md')
    assert "every other Epic and Task, the design Epic included, is blocked by it" in planning
    assert "Never ask the user to choose a tool, threshold, or code layout" in planning
    assert "continue with [orchi-standards](../orchi-standards/SKILL.md) in this session" in plan
    assert "is blocked by the foundation or standards Epic" in prose('skills/orchi-core/references/readiness.md')
    review = prose('skills/orchi-core/references/review-delivery.md')
    assert "`standards.py ratchet` against the PR target must pass on the candidate" in review
    assert "in its Exceptions section in plain words" in review
    assert "## Exceptions" in installation.PR_TEMPLATE
    assert "`ENGINEERING.md`" in installation.instruction_blocks(ROOT, False)["CLAUDE.md"]
    assert "relay its Exceptions to the user in plain words" in prose('skills/orchi/SKILL.md')
    for role in ('orchi-implementer', 'orchi-fixer', 'orchi-designer'):
        assert "adding a suppression, loosening a check, or recording an exception" in prose(
            f'skills/orchi-core/roles/{role}.md')
    standards_skill = prose('skills/orchi-standards/SKILL.md')
    assert "never ask about tools, thresholds, or layout" in standards_skill
    assert "the product constraints are the user's, even in auto mode" in standards_skill
    assert "| Planner | `orchi-standards` |" in prose('skills/orchi-core/references/pool.md')
