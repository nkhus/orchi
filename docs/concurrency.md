---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/execution.py
  - skills/orchi/scripts/orchi_core/resources.py
  - skills/orchi/scripts/orchi_core/runner.py
relations:
  part_of: [docs/README.md]
  depends_on: [docs/synchronization.md, docs/security.md]
---
# Concurrency and verification

## Independent snapshots

Parallel tasks receive different detached worktrees at exact accepted starts. Read/read and read/write observations do not reserve each other's immutable snapshots. Initial exact write/write overlap and declared task `exclusive_resources` serialize dispatch inside a controller. The plan must order tasks that promise the same output path.

Ontology artifacts/ownership is for navigation and impact. It neither grants edits nor locks an entire component. `read_paths`, dependency outputs, before-images and applicable instructions are fixed equality assumptions. Additional implementation sources can explicitly select `consistency: snapshot`; drift then triggers wider compatibility checks and is recorded for review. It is not silently treated as unchanged or as proof of independence.

## Optimistic exact-head integration

1. Freeze the worker result and product diff. Controller observations are Evidence, not Core.
2. Run isolated checks without holding the global integration operation.
3. Compose with the current accepted head. Written before-images must match; no silent textual/semantic merge is attempted for conflicts.
4. Run combined checks for that exact composition outside the acceptance transaction. Other candidates may do the same concurrently.
5. Compare-and-swap the head and ticket/token identities. Accept only the checked combination. If another accepted result changed the head, retain this evidence as superseded and recompose/recheck without another coding session or isolated run.

Recomposition is bounded by policy. Exhaustion preserves a validated candidate for `integrate --ticket`; it does not reset attempt budgets. Checks that fail on a superseded combination cannot block a different current combination without rechecking it. A released/expired/fenced attempt cannot accept a late result.

## Verification policy

`cumulative` is the default: accepted task/epic checks accumulate and are rerun during composition. `scoped` requires operator-selected `integration_checks`; it does not infer safe test selection from documentation ownership. Snapshot-observation drift broadens checks. Full epic acceptance and final cumulative checks remain mandatory. Do not run unfinished tasks' acceptance prematurely merely to call a test set complete.

Batching several candidates into one diagnostic unit and automatic conflict resolution are not implemented. The principal throughput gain is overlapping isolated and combined verification with short acceptance, not weakening evidence.

## Shared resources

Prefer separate databases, ports and fixtures per check. When isolation is unavailable, a check may declare named `resources`. The policy must name the same absolute operator-owned `resource_directory` across participating local controllers. POSIX kernel-held locks acquire resource names in sorted order, time out rather than run concurrently, and release when the holder exits.

Task `exclusive_resources` remain controller-local. Named check locks coordinate only processes using the same accessible directory on the same supported host. They do not automatically coordinate another laptop, remote CI runner, orphaned external job or production deployment. Local locks are not fencing tokens for external systems. The outer runtime must prevent a dead local process from leaving an active remote operation.

## Multiple initiatives

Use a separate control directory and unique initiative ID for each independent accepted outcome. Do not split one atomic feature just to obtain more workers. Controllers need not know every external developer: actual canonical history, explicit sync and exact publication checks establish the boundary. Publication is serialized by Git/hosting rules; independent design/coding can overlap.

Only one epic is active per initiative. Parallel branches of its task DAG cover a shared accepted outcome. Dependent future epic designs remain just in time. Multi-repository transactions and distributed global scheduling are separate systems, not implied by this model.
