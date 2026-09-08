---
kind: guide
area: orchi
relations:
  part_of: [docs/README.md]
  depends_on: [docs/planning.md, docs/workflow.md, docs/synchronization.md]
---
# Developer formats and their boundaries

Use one finite initiative per accepted result. A continuing maintenance responsibility is a stream of initiatives, not a never-ending request that can never reconcile. Select authoring depth by uncertainty and consequences; there is no mandatory separate state machine for every ticket label.

| Situation | Supported flow |
| --- | --- |
| Understood small fix | Compact brief, combined initial gate, one task/epic, regression evidence, final approval |
| Ordinary feature | Shared contracts, one or more progressively designed epics, task DAG |
| Large brownfield change | Outcome-level roadmap, latest checked Current/Target, checkpoints and explicit upstream sync |
| Greenfield | Empty/minimal Current, accepted Target first, then verified implementation accumulated through checkpoints |
| Diagnosis/research | Investigation task with no product writes; evidence/observations first, implementation only under an accepted design |
| Documentation-only | No fake code task; knowledge-only epic and explicit verified final Core |
| Architecture proposal | A knowledge/investigation outcome; future architecture remains proposal/Intent/evidence, not implemented Core |
| Refactor/dependency upgrade | Acceptance emphasizes unchanged contracts; broad technical scope can be explicitly delegated without changing semantic invariants |
| Human, pair or agent | Same readiness/candidate/check/review protocol; runner dispatches only agent tasks |
| Existing branch/PR | Accept outcome and design, import an exact bounded diff after readiness, verify it without inventing historical approvals |
| Interrupted or transferred task | Stop attestation, preserved candidate/notes, new fenced attempt, explicit revalidation/import |
| Parallel frontend/backend | Accept common interface first; parallel DAG branches, then joint compatibility and checkpoint checks |
| Several independent initiatives | Separate controls and IDs; independent execution, exact shared-target sync/publication |
| Hotfix/release/backport | Separate bounded initiative with operator-selected target ref and explicit checks; backport is verified on its own base |
| Stacked task changes | Explicit producer dependency/contract; consumer source materializes after integration, not from hypothetical output |

## Bounded fix

Create a meaningful `ChangeBrief` using the installed [brief examples](../skills/orchi/assets/examples/brief-fix.json). The brief supplies decisions; the controller does not guess them. After operator setup:

```bash
orchi start --file /operator/drafts/brief.json
orchi inspect
# Operator decide binds the displayed exact request ID.
orchi run --adapter /operator/adapter.json
# Review/checkpoint, final reconciliation, final review and final approval still apply.
```

A software fix with unchanged architecture can use the `unchanged` final architecture disposition. It still references existing artifacts and checks. No-change is a supported architectural answer, not missing design.

## Existing work and transfer

Accept a task before importing work. `claim`, read packet, `activate`, then `import-candidate --commit ... --base ... --reason ...`. Initial/approved extra paths and before-images must match. The imported diff is unverified until submission and review.

`handoff --ticket ... --stopped --reason ... --executor human` preserves the previous attempt and creates a new readiness boundary. It rechecks allowed grants and reports blocked ones. The receiver gets old assumptions and notes, not a false claim the candidate remains compatible. Import of the preserved diff fails if its fixed assumptions are stale.

## What this pack deliberately does not claim

One initiative has only one active epic and atomic publication of its entire request. Future dependent epics are not designed speculatively. Cross-initiative stacked PR orchestration is external: use existing Git workflow and accepted sync rather than assuming Orchi schedules dependent remote PRs.

Incremental publication of portions of one request is not enabled. Multi-repository release coordination may link requirements/evidence manually, but there is no distributed atomic transaction. Production deployment, database rollout, emergency policy changes and remote job fencing require explicit external processes. Hotfix urgency is not a check/signature bypass.

The foreground command adapter and local worker relay are executable protocols. Live Codex quality, sandbox IPC permission, hosted PR creation and hosted queues require the actual environment and are not implied by deterministic local fixtures.
