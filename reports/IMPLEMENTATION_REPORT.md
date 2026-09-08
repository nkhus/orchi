# Orchi implementation and validation report

## Delivered contract

This pack is the complete current Orchi source tree, installed runtime and five-skill bundle. It implements the accepted development-flow direction on top of the supplied target pack. It is not a patch directory or a proposed architecture presented as working code.

**One finite request, one accepted Intent, progressively designed epics, parallel tasks, verified checkpoints and one atomic final publication remain the default and supported authority contract.** The repository does not have to stop moving while a request is in progress. The original baseline stays immutable; a reviewed, checked and signed synchronization can advance the accepted integration base and its matching Current knowledge together.

The detailed [implementation plan](IMPLEMENTATION_PLAN.md) defines seven workstreams and their acceptance boundaries. The [machine-readable validation summary](validation-summary.json) records this delivery's actual execution, including input hashes. All durable documentation and installed procedures are in English and describe current behavior rather than release history.

## Implementation by workstream

| Workstream | Shipped behavior | Main implementation and executable evidence |
| --- | --- | --- |
| Proportionate authoring | `ChangeBrief`, deterministic expansion, combined initial direction/first-plan gate, software/knowledge/investigation outcomes, atomic-only delivery | `authoring.py`, `models.py`; compact, no-fake-task and original-request tests |
| Exact context and scope | Ownership is navigation, inline/on-demand sources, fixed versus snapshot observations, bounded additional scope, known-input preflight, read-only IDE views | `context.py`, `preflight.py`, `execution.py`, `views.py`; exact read, ownership, drift, size, grant and view tests |
| Execution and transfer | Human/agent/pair contracts, bounded investigations, preserved stopped candidates, fenced handoff, exact diff import, targeted task amendment | `execution.py`, `runner.py`, `engine.py`; handoff/import, investigation and unaffected-worker amendment tests |
| Optimistic integration | Parallel isolated and combined checks, exact-head compare-and-swap, retained superseded evidence, recomposition without rerunning the worker, explicit resource exclusion | `execution.py`, `resources.py`; barrier-controlled race, stale acceptance and resource tests |
| Moving canonical | Status/draft, three-way file composition, explicit Core/Working decisions, prospective checks/lint/review/signature, atomic authority promotion | `synchronization.py`; upstream, conflict, failure, final invalidation and two-initiative tests |
| Operator and publication | Readable exact gate, direct operator signing, exact/squash/merge policy shapes, safe local publication and external Git handoff | `views.py`, `operator_cli.py`, `publication.py`; displayed-ID, expected-parent/tree and later-head tests |
| Skills and distribution | Five concise skills, thirteen generated schemas, source/operator/worker references, examples, deterministic demos, local installation smoke and expanded live cases | `skills/`, `schemas/`, `docs/`, `tests/`, `tools/`, `evals/` |

Module names in this table refer to `skills/orchi/scripts/orchi_core/`. Tests live at repository level. Existing authority, retrieval, signatures, review/checkpoint, recovery and finalization tests remain part of the full suite.

### Compact and substantial changes

`start --file brief.json` binds the exact supplied user request, requirements, architecture/no-change statement, selected design and first task DAG in a single initial approval. The controller does not invent omitted architecture or make a material product decision. `brief-expand` can write the ordinary authoring artifacts without accepting them. Larger requests continue through `begin` and one selected `plan` at a time.

A knowledge-only outcome can close an epic without manufacturing a coding task. An investigation task may produce observations and evidence but cannot submit product edits; implementation follows an accepted implementation design. Documentation proposals from workers stay evidence, not Current. Normal review, checkpoint, requirement reconciliation and final acceptance still apply to compact requests.

### Worker autonomy without authority confusion

A task's approved directory/action/local-choice envelope can authorize additional technical files. `scope-acquire` refuses protected paths, another task's declared output, active ownership conflicts and requests marked as design or Target changes. It records exact before-images and applicable instruction sources. A grant is a mechanical permission within a declared envelope, **not proof that an arbitrary diff is semantically local**; implementation review still has to enforce the accepted decisions.

`amend-tasks` preserves unchanged task contracts and shared design bytes. It invalidates the declared affected tasks and their transitive dependents, not every unrelated worker. Changed shared design, integrated affected work or an affected live ticket cannot hide in this smaller amendment path.

`handoff` requires an explicit stopped attestation, preserves candidate/notes/assumptions and fences the old ticket. The receiving attempt has a new readiness boundary and rechecks scope grants. `import-candidate` can reuse exact product changes after readiness, but rejects stale fixed assumptions, unexpected paths and mismatching before-images. Historical approval is never invented for imported work.

### Exact reads without granting control access

Task packets include a bounded required design/context plus exact source identities. On-demand sources are read from the frozen dispatch snapshot, not the latest branch. Exact line slices retain the complete-source hash and a separate slice hash. A fixed assumption rejects stale integration; an explicitly selected snapshot observation records the change and triggers broader compatibility validation.

The foreground runner starts an ephemeral ticket-bound Unix-socket channel for `read` and, after readiness, bounded `scope`. `worker_request.py` is a standard-library helper. The protocol has a capability token, strict operation/argument allowlists, bounded requests and idempotent request identities; no arbitrary controller CLI or signing operation is exposed. It closes with that foreground invocation. A real subprocess command adapter exercised both reading and scope acquisition without `ORCHI_CONTROL` in its environment.

This is **not a sandbox certification**. The outer runtime must actually isolate the controller, signing keys and canonical writes while permitting this limited channel. A shared operating-system identity, another readable environment or shared Git metadata can defeat assumptions about isolation. Live Codex sandbox access to this IPC channel was not exercised.

### Parallelism and compatibility

Tasks execute in separate snapshots. Documentation ownership no longer becomes a component-wide read reservation. Initial same-path writes and task-local exclusive resources remain conservative scheduling conflicts. Declared fixed dependencies are checked at acceptance rather than preventing every immutable read/write overlap.

Isolated checks and combined checks do not hold the global integration operation. Each combined result is bound to a specific accepted head and composition; the short acceptance transaction compares ticket/token/epoch/definition/head identities. A race loser preserves its evidence and recomposes. It does not rerun coding or isolated checks simply because another valid task integrated first. Retry exhaustion leaves a validated candidate for explicit later `integrate`.

The test suite forces isolated and combined verification overlap with barriers and verifies that both tasks eventually integrate after at least one recomposition. The two-epic demo also observed a real recomposition. These are correctness/concurrency observations, **not a throughput benchmark**.

Cumulative verification remains the default. Scoped verification must explicitly name operator-selected integration checks; ontology ownership does not infer a safe reduced suite. Full checkpoint and final checks remain mandatory. Shared check resources use explicitly configured same-host POSIX locks. Task `exclusive_resources` is controller-local; neither mechanism promises coordination across different hosts or fencing of external jobs.

### Synchronization is a new checked knowledge snapshot

At a closed boundary, `sync-status` and `sync-draft` identify the exact upstream delta, code conflicts and knowledge impact. `sync-check` constructs a prospective state, runs accumulated/policy/declared checks and lints its resolved Current. Same-path divergent code requires explicit bytes/deletion/exact-source resolution. Rewritten or unrelated upstream history fails closed.

Working records affected by upstream code or Core need explicit `update`, `revalidate`, `retire` or checked `use-upstream` decisions. Newly inherited Core that describes this initiative's changed implementation is also considered. A same-document upstream edit cannot be hidden by revalidating unchanged Working text.

The exact sync candidate requires full review and a human signature. Acceptance checks that upstream has not moved again and promotes code, integration base, knowledge head and Working revision together. Until then the previous Current remains effective. Original request/Intent and completed epic history are preserved. Old final candidates/approvals become invalidated history, not authority for the new state. An explicit required Target revision blocks subsequent planning/finalization until that revision is accepted.

The two-initiative demonstration starts both requests from the same original baseline. The first publishes. The second explicitly syncs to that publication, retains its original baseline, and then publishes its own checked atomic result. Both changes are present in the final canonical code.

### Publication shapes and limits

Policy selects `exact` by default; `squash` and `merge` are explicit alternatives for Git history shape, not incremental request delivery. All modes require the exact checked tree and approved integration base, with mode-specific parents. A correct publication can be recorded from canonical ancestry after a later unrelated commit arrives.

`publication` creates a structured Git/PR handoff, **not a remote PR**. The local operator helper uses expected-old-commit compare-and-swap and refuses a target branch checked out in any worktree. Hosted recomposition on a new base needs sync and fresh final checks/review/approval. No automatic deployment, feature-flag activation or production migration is performed.

## Executed validation

All results below were obtained from the delivered implementation, not copied from the input pack's report.

| Validation | Observed result | Retained evidence |
| --- | --- | --- |
| Complete deterministic suite | **276 passed, 0 failed, 0 errors, 0 skipped**; 516.352 seconds in this run | [pytest.log](pytest.log), [pytest.xml](pytest.xml) |
| Added acceptance/boundary cases | 50 parameterized cases across three new test modules | `tests/test_development_flows.py`, `tests/test_synchronization_publication.py`, `tests/test_workflow_boundaries.py` |
| Source/package validator | 132 source files; 56 Python files compiled; 13 schemas; 5 skills; no errors | [source-validation.json](source-validation.json) |
| Canonical knowledge lint | 14 committed Core documents; no diagnostics | [canonical-lint.json](canonical-lint.json) |
| Two-epic synthetic lifecycle | `PUBLISHED`; one canonical child commit; Core unchanged at intermediate checkpoint | [multi-epic-demo.json](multi-epic-demo.json) |
| Two independent initiatives | Both `PUBLISHED`; one reviewed/signed upstream sync; two final canonical commits; immutable origins retained | [two-initiative-demo.json](two-initiative-demo.json) |
| Local installed runtime | Five skills/thirteen schemas; unrelated files preserved; Current/Target exact reads, cache, graph/map/lint/coverage pass | [installed-smoke.json](installed-smoke.json) |
| Model-behavior scenarios | **54 defined, 0 executed live**; not part of the pass count | `evals/scenarios.json` |

Commands executed from the package source:

```bash
python -m pytest -q --tb=short --junitxml=/external/pytest.xml
python tools/validate_package.py
python skills/orchi/scripts/orchi.py lint --repo /absolute/path/to/orchi --ref HEAD
python tools/demo.py --out /new/disposable/multi-epic
python tools/demo_development.py --out /new/disposable/two-initiatives
python tools/smoke_install.py --installer local --runner python --out /new/disposable/installed
```

Only the absolute disposable paths have been normalized in this command listing. The committed-source lint used the actual final source/docs tree. Synthetic fixtures use test-only signatures; no private fixture key or controller directory is distributed.

### Environment

Python 3.13.5; Linux-6.18.35-x86_64-with-glibc2.41; git version 2.47.3; SQLite 3.46.1. Installed validation dependencies: Pydantic 2.13.4, cryptography 46.0.4, PyYAML 6.0.3, pytest 9.0.2.

The source declares Python 3.11+ and includes CI configuration, but **only Python 3.13.5 on this Linux host was actually executed here**. Hosted CI, optional network Skills CLI/`uv` installation, real model authentication, production workload performance, other operating systems and cross-machine resources were not validated in this run.

## Supported formats and deliberate exclusions

The same contracts cover bounded fixes, ordinary features, large brownfield work, greenfield, read-only diagnosis, knowledge-only outcomes, refactors/upgrades, human/agent transfer, bounded existing-diff import, parallel task branches, separate initiatives and explicitly selected release/backport targets. Source examples and tests show their actual boundaries; a JSON-shaped brief alone does not establish meaningful acceptance.

There is one active epic per initiative. Cross-initiative stacked PR scheduling remains an external Git/hosting responsibility; within an epic, producer outputs become exact dependency sources after integration. Incremental publication of portions of one request, speculative future detailed designs, mandatory repository-wide scheduling, distributed locks, atomic multi-repository transactions and universal deployment orchestration are not enabled.

New controls use state version 2. **Initialize a fresh external control directory; existing active stores are not automatically converted.** Do not reinterpret old signatures or mutate an active old database to fit new contracts. Keep prior stores/exports for their own provenance.

## Reading and using the pack

Start with [README](../README.md), [installation](../docs/installation.md), the [operator guide](../skills/orchi/references/operator-guide.md), [development formats](../docs/development-flows.md), [concurrency](../docs/concurrency.md) and [synchronization](../docs/synchronization.md). The compact examples live in `skills/orchi/assets/examples/`. Review the security boundary before configuring a live worker.

The archive contains source, tests, examples, skills, schemas, this plan/report and sanitized validation evidence. `source-manifest.json` and `SOURCE_SHA256SUMS.txt` bind every non-report source file. The final delivery is checked by fresh extraction, source-hash comparison, ZIP integrity and the package validator; the machine-readable packaging result records that check. Git metadata, controller databases, mutable worktrees, caches, environments, authentication material and private keys are excluded.

From an extracted archive on a system with `sha256sum`, source integrity can be checked before provisioning dependencies:

```bash
cd orchi
sha256sum --check reports/SOURCE_SHA256SUMS.txt
```

Deterministic checks substantiate the protocol and failure boundaries listed above. They do not replace live-agent behavioral evaluation, meaningful domain acceptance, independent architecture review or real production isolation testing.
