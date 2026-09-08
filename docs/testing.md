---
kind: guide
area: orchi
artifacts:
  - tests/**
  - tools/validate_package.py
  - tools/demo.py
  - tools/smoke_install.py
relations:
  part_of: [docs/README.md]
---
# Testing and validation

Run the source validator, full deterministic suite, synthetic lifecycle demo and installed-runtime smoke in an environment with `requirements-dev.txt`. Exact commands, platform, counts and limitations belong in the delivery report; do not copy pass counts from an input archive.

```bash
python tools/validate_package.py
python -m pytest -q --junitxml=/private/reports/pytest.xml
python tools/demo_development.py --out /new/disposable/moving-main-demo
python tools/demo.py --out /new/disposable/demo
python tools/smoke_install.py --installer local --runner python --out /new/disposable/install
python tools/smoke_install.py --installer npx --runner python --out /new/disposable/npm-install
```

## Deterministic coverage

The suite covers strict contracts/signatures, progressive planning, exact Current/Target snapshots, greenfield, ontology/graph/retrieval, review/repair, final traceability, scope protection, budgets, worktrees and process termination. It additionally exercises compact combined approval, on-demand reads, fixed versus snapshot assumptions, delegated additions, handoff/import, investigation evidence, knowledge-only publication, targeted amendment and read-only materialized views.

Concurrency tests force simultaneous candidates through barriers, observe actual isolated and combined verification, and require a losing combination to recompose without a new worker attempt. A command-adapter fixture exercises ticket-bound read/scope requests without a control-store environment. Resource tests cover contention, timeout and release. These establish protocol behavior, not hostile-container security.

Synchronization tests cover code conflicts, Core/Working collisions, newly inherited Core that documents local changes, unchanged authority on failure, upstream movement during approval, rewritten history, required target revisions, final invalidation and two independent initiatives publishing in sequence. Publication tests cover exact, equivalent-tree squash, two-parent merge, later canonical advances, wrong trees and checked-out branch refusal.

Existing recovery assertions use per-ticket validation state for task checks and aggregate operation state for checkpoint/final/sync checks. Both require explicit stop/recovery and preserve candidate evidence. A test must not restore a coarse global task lock just to match an obsolete implementation expectation.

## Schemas and packaging

Regenerate with `python skills/orchi/scripts/orchi.py schemas --out schemas`. Schema files must equal the Pydantic contracts. The source validator checks five installed siblings, concise skill entrypoints, English source, valid local links, syntax and dependency metadata. All installed references/tools must work without a separate source checkout. Installation into an unrelated project tests runtime independence from application package metadata.

## Live-agent boundary

`evals/scenarios.json` defines behavioral scenarios, not pytest passes. Assess routing, unnecessary intervention, semantic task design, context provenance, scopes, review quality and final accepted outcomes with actual traces. Model authentication, actual Codex IPC/sandbox permissions, hosted queues and cross-machine behavior require their real environment. Synthetic keys/review reports are strictly test fixtures.

CI configuration is not evidence every Python/platform/network combination ran locally. Record executed offline checks separately from network installs and live models. Do not count unexecuted scenarios as passed or skipped deterministic tests.
