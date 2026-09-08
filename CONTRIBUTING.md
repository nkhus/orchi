# Contributing

Use English for source documentation, instructions, examples, diagnostics, and tests. Describe the implemented system directly. Keep product release labels, changelogs, historical design comparisons, generated execution logs, and local keys out of the source package.

## Development environment

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

The repository is a skill distribution with a dependency-free npm installation wrapper, not a separately packaged runtime application. The wrapper and installed entrypoints use `uv`; `pyproject.toml` contains test configuration. Installed Orchi does not depend on Node or the consuming project's Python environment.

## Source ownership

Keep shared runtime code under `skills/orchi/scripts/orchi_core/`. Every resource needed after skill installation must be inside `skills/`. Root `docs/`, `tests/`, and `tools/` serve repository readers and contributors; installed skills must not rely on them at runtime.

Use short `SKILL.md` files for routing and procedures, focused references for detailed rules, and assets for templates. The four explicit stage skills share the `orchi` runtime and references; install them together. Avoid duplicating implementation logic or authoring generated task packets by hand.

## Contracts and dependencies

Python models are authoritative for generated JSON Schemas. After an intentional contract change:

```bash
python skills/orchi/scripts/orchi.py schemas --out schemas
python tools/validate_package.py
```

Keep inline dependency declarations in both entrypoints aligned with `skills/orchi/scripts/requirements.txt`. Third-party dependency constraints and plan revision counters are technical requirements, not Orchi release identifiers. Preserve bounded verification and fail-closed behavior when changing contracts.

## Behavioral changes

Preserve initiative-level publication, sequential epic planning, task design before execution, exact human gates, Core freeze, verified knowledge checkpoints, ticket fencing, real candidate/combined checks, bounded review, and explicit recovery. A claimed invariant needs a meaningful test. Update the corresponding reference and project document when the mechanism changes; do not rewrite unrelated documentation for a routine implementation detail.

Use disposable repositories and test-only keys. Never run synthetic automatic approvals, demo fixtures, or untrusted workers against a real project. Tests of agent intelligence belong in `evals/`; do not count an unexecuted scenario or synthetic worker as a live model result.

## Before committing

Run source validation and the full test suite, then test a fresh installation into a temporary project. Confirm that operator tooling, schema export, and diagnostics work from the installed directories without the source checkout. Keep caches, environments, generated reports, audit exports, and private state out of the commit.
