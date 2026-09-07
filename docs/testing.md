# Testing

## Deterministic validation

Run from the Orchi repository, not from a production initiative:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
python tools/demo.py --out /tmp/orchi-demo
```

The output directory for the demo must not exist. The demo creates a disposable Git repository, synthetic process workers, and a test-only signing key. It exercises two epics, intermediate Working Knowledge, final Core reconciliation, and a single canonical publication. Its generated packet, audit export, and report are local evidence, not source files to commit.

## Coverage

Contract tests cover exact paths, protected writes, explicit task designs, future-epic boundaries, acceptance coverage, safe context parsing, and generated schemas. State-machine tests cover approvals, signature replay, readiness, knowledge scoping, mandatory checkpoints, retained budgets, finalization, and canonical drift.

Execution tests use real Git worktrees, SQLite, signatures, and subprocesses. They cover parallel claims and workers, read assumptions, resource serialization, actual combined-tree verification, process timeout/output limits, recovery, transactional rollback, and content-addressed artifacts. Review tests cover clean passes, causal scope, retained blockers, bounded repair, and incomplete reviews.

Retrieval tests cover heading and line extraction, relevance, prefix/substring/fuzzy matching, Unicode,
bounded queries and excerpts, scope masking, retirements, stale artifacts, canonical drift, checkpoint
invalidation, readback hashes, concurrent atomic cache construction, corruption recovery, capability
fallbacks, standalone CLI use, and unchanged workflow authority. Installed-skill tests execute search from
the copied bundle; accepted-checkpoint tests use real Git and controller transitions.

Packaging tests cover a fresh installation, user-file preservation, idempotency, explicit replacement backup, symlink refusal, bundled entrypoints, schema parity, and complete skill resources. Diagnostics distinguish local prerequisite checks from live authentication or model validation.

`tools/validate_package.py` checks Python syntax, metadata, local Markdown links, bundled resources, JSON, schema drift, English-only repository text, and absence of product release metadata. It is an offline source validation tool, not a model evaluation.

## Installed-skill smoke test

Validate installation into a disposable project rather than only running from this repository:

```bash
ORCHI_SOURCE="$PWD"
TARGET="$(mktemp -d)"
git -C "$TARGET" init -b main
(
  cd "$TARGET"
  npx skills add "$ORCHI_SOURCE" --skill '*' --agent codex --yes
  uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
  uv run .agents/skills/orchi/scripts/operator.py --help
  uv run .agents/skills/orchi/scripts/orchi.py schemas --out "$TARGET/generated-schemas"
)
```

The same checks, including preservation of existing user files and isolation from an incompatible application manifest, are automated by `python tools/smoke_install.py --out /tmp/orchi-installation`. Its `--installer local --runner python` mode checks a pre-provisioned offline environment. Both modes require a new output directory.

The first invocation may need network access to obtain the external CLI and Python packages. In a provisioned offline environment, use the bundled copying tool and managed Python environment instead. The installed runtime must work without importing from the source checkout or the target application's package configuration.

## Continuous integration

The included GitHub Actions workflow runs source validation and the deterministic suite. The installation job invokes the actual Skills CLI against a local checkout, then executes the bundled scripts in an isolated target project using `uv`. No production keys or live model credentials are used.

## Live model evaluation

`evals/scenarios.json` defines model-behavior scenarios separately from pytest. A scenario needs an appropriate controller state, repository, model/CLI configuration, and observed evidence; a prompt alone cannot validate state routing.

Assess correct next action, forbidden writes, unsupported approvals, source-selection mistakes, unnecessary interventions, review-loop waste, and actual root acceptance. Semantic assessment is required for task design and knowledge prose. Record traces, tool calls, final state, outcomes, cost, and intervention rate in a private report as appropriate.

Synthetic workers validate protocol execution, not coding intelligence. A green test suite does not establish correct live skill selection, design quality, sandbox isolation, authentication, or production readiness. Do not report the live scenarios as passed unless they have actually been executed and assessed.
