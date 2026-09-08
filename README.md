# Orchi

A local, Git-native controller that takes an accepted development request to a checked, reviewed, atomically published result. A bounded fix and a large initiative use the same authority model; only the depth of authoring changes. Humans and agents use the same candidate-acceptance protocol.

## Install

Install all five sibling skills into the target project with `npx`:

```bash
npx --yes github:nkhus/orchi --project /absolute/path/to/project
uv run /absolute/path/to/project/.agents/skills/orchi/scripts/orchi.py doctor --repo /absolute/path/to/project
```

Run the installer without `--project` to target the current directory. The wrapper uses `uv run --no-project` so installation does not inherit the consuming project's Python package metadata. The installed entrypoints use their inline `uv` dependency metadata. Node 18+, `uv`, Python 3.11+, POSIX, Git with SHA-1 objects and SQLite FTS5 are required. Installation preserves unrelated skills and project instructions. See [installation](docs/installation.md) and the bundled [operator guide](skills/orchi/references/operator-guide.md) for keys, checks and real worker isolation. The npm package is only an installation wrapper; the installed runtime does not depend on Node or a separately published Python application.

## One development cycle

```text
Request -> accepted Intent -> design the nearest verifiable epic
        -> parallel human/agent tasks -> isolated checks
        -> exact-head composition + compatibility checks + short CAS acceptance
        -> independent review -> verified Working Knowledge checkpoint
        -> next epic, or final requirement/architecture/Core reconciliation
        -> exact final checks + review + human acceptance -> atomic publication
```

For a small understood change, `start --file brief.json` deterministically expands one compact brief into normal Intent and the first Epic Plan, with one combined initial approval. A final approval is still required. Larger requests use `begin` and progressively accepted `plan` calls. The controller does not invent missing requirements or architecture.

Investigations return observations without product writes. Knowledge-only epics need no fake implementation task. Existing diffs can be imported after readiness, and explicitly stopped work can be handed from an agent to a person without losing its candidate. Local file-scope additions are permitted only inside the accepted directory/action/choice envelope; changing a shared design or Target requires its own revision.

Only one epic is active per initiative. Independent tasks can run in parallel; multiple independent initiatives use separate control directories and a shared Git target. Reading an immutable snapshot is not a file lock. Documentation ownership remains navigation/impact metadata, not a scheduler reservation.

## A moving repository, not a frozen main

The original baseline is immutable provenance. Current uses the **accepted integration base plus verified Working Knowledge**. Other developers can publish to the canonical branch. At a closed boundary, `sync-status`, `sync-draft`, `sync-check`, exact review and signed acceptance reconcile both code and knowledge against the new upstream snapshot. Until acceptance, the old Current remains authoritative. A sync invalidates an old final candidate and approval.

An upstream edit to a document cannot be silently hidden by an old Working replacement. Same-path code conflicts and affected knowledge require explicit dispositions. Rewritten upstream history fails closed. See [synchronization](docs/synchronization.md).

## Knowledge views

| View | Meaning |
| --- | --- |
| Current | Published Core, or this initiative's accepted base plus verified sparse overlay |
| Target | Accepted requirements, architecture and target decisions |
| All | Both, with explicit role and exact Git/hash provenance |

Intent, Epic Design, Working Knowledge and Evidence are separate. Greenfield can have empty Current and a useful Target. Search resolves authority first, keeps BM25/prefix/substring/fuzzy primary hits separate from typed graph neighbors, then supports exact reads. `related`, `owners`, `lint`, `map` and `coverage` are derived navigation. No vector service, graph database or remote knowledge authority is required.

Task packets support inline and on-demand exact sources. The foreground runner provides a ticket-bound local read/scope channel; workers do not need the control database or signing key. The outer sandbox must permit that limited channel. `views --out /new/external/path --view all` creates a read-only, provenance-labelled snapshot for a human's IDE; it is not another source of truth.

## Decisions and publication

`overview` explains pending work; `inspect` shows the actual pending gate. The operator can inspect, sign and apply an exact request ID without manually transporting decision files. Cryptographic gates, fixed policy and review remain in force.

Atomic initiative is the only delivery contract: this initiative's code and Core publish after its whole request is reconciled. Exact commit is the default Git shape; policy can explicitly select squash-equivalent or a two-parent merge with the same checked tree and approved base. `publication` produces a Git/PR handoff, not a remote PR. Local operator publication uses compare-and-swap and refuses a branch checked out in any worktree. Hosted queue recomposition requires a new sync/final check/approval. Publication is not deployment.

Incremental publication of one request, parallel active epics, distributed locking, atomic multi-repository delivery and a universal deployment engine are not claimed. See the [development formats](docs/development-flows.md) for precise support boundaries.

## Skills and source layout

`orchi` routes controller state; `orchi-plan` authors accepted intent and designs; `orchi-work` executes bounded tasks; `orchi-review` reviews exact candidates; `orchi-deliver` reconciles checkpoints, synchronization and publication. All five remain siblings.

```text
skills/       Installed runtime, five skills, operator and worker tools, references, examples
schemas/      Generated strict authoring contracts
docs/         Current-state architecture and operating guides
tests/        Deterministic protocol, concurrency and installation tests
evals/        Live-agent scenarios, explicitly separate from deterministic results
reports/      Detailed implementation plan, executed validation and delivery manifest
tools/        Offline installer, validator, demonstration and installed-runtime smoke
```

## Validate

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
python tools/demo_development.py --out /new/disposable/moving-main-demo
python tools/demo.py --out /new/disposable/orchi-demo
python tools/smoke_install.py --installer local --runner python --out /new/disposable/orchi-install
```

The [implementation plan](reports/IMPLEMENTATION_PLAN.md) and [implementation report](reports/IMPLEMENTATION_REPORT.md) distinguish shipped behavior, executed evidence and untested external integrations. Synthetic workers and test-only signatures are not model evaluations or production authorization. See [security](docs/security.md) before using live agents. Initialize a fresh control directory for these contracts; existing active stores are not automatically converted.
