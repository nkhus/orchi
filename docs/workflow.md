---
kind: reference
area: orchi
artifacts: [skills/orchi/scripts/orchi_core/engine.py]
relations:
  part_of: [docs/README.md]
  depends_on: [docs/planning.md, docs/verification-and-finalization.md]
---
# Workflow

## Author and accept

Start in an operator-provisioned `EMPTY` store. A large request uses `begin` to bind Initiative and exact Intent; accepting its direction gate enters `PLANNING`. A bounded request can use `start` with a complete ChangeBrief; its combined gate binds Intent and the selected first plan/design and enters `EXECUTING` after acceptance. It is not auto-approval.

The next epic is selected from the accepted outcome-level roadmap. Only its detailed design and task DAG are authored. Future epics do not contain file edits or executable plans. `plan-preflight` inspects known sources and packet limits; `plan` repeats validation before requesting approval. Dependency outputs and runtime services cannot be guaranteed before they exist.

## Execute and checkpoint

A task moves through `pending -> claimed -> running -> checking -> validated -> integrating -> integrated`. Checks are exact candidate operations, not assertions from the worker. A blocked/expired/released attempt is not silently retried. An integrated task does not update Current knowledge.

Readiness binds the fingerprint, fixed decisions and acceptance IDs. The actor may be an agent, person or pair. The foreground runner automatically dispatches only `agent` tasks. Ticket-only read/scope operations are available through the local relay when the sandbox permits it; manual controller relays use the same methods.

All tasks must integrate before full epic checks and review. Review uses a full pass followed by bounded targeted repair. A checkpoint then reconciles each changed product path and affected knowledge mapping. Only this verified boundary updates Working Knowledge and allows the next epic to be designed.

## Three kinds of change

A local extra file requires an accepted directory/action/choice envelope and `scope-acquire`. A shared design or acceptance change requires `amend` after stopping affected execution under its full-epic boundary. `amend-tasks` is narrower: same task set and byte-identical shared design/acceptance, only explicitly affected pending or blocked tasks and transitive dependents may change. Unaffected workers may finish isolated validation while the narrow gate is pending; acceptance into the head waits for the gate.

A material target change uses an accepted `revise-intent` between epics, preserving original source and completed history. Stop/release workers and accept `stop-epic` when an active epic must return to its original checked boundary. Its candidates remain inspectable/importable; abandoned code is not automatically reused.

## Pause, handoff and recovery

`handoff --stopped` records the old candidate, assumptions, notes and scope grants; fences its ticket; creates a new attempt/readiness boundary. Existing delegated grants are rechecked, not blindly inherited. `import-candidate` applies only approved-path diffs with matching before-images to a clean activated worktree. A preserved candidate with stale fixed assumptions must be manually reconciled, not imported unchanged.

Per-ticket check loss leaves a `checking`/`integrating` attempt and immutable candidate. Confirm process termination, `release --stopped`, then explicitly retry/handoff. Aggregate check loss uses `recover-operation --stopped`. Lease expiration alone is never proof the process stopped. Budgets survive all transitions.

## Synchronize and finish

`sync-status` does not advance state. At a closed boundary, prepare an exact sync candidate, run checks, review it in `SYNC_REVIEW`, then sign its gate. Current changes only at acceptance. A rejected/discarded candidate leaves the old authority intact. A required Target revision blocks later plans/finalization.

After all epics close: `FINALIZING -> FINAL_REVIEW -> AWAITING_APPROVAL -> READY_TO_PUBLISH -> PUBLISHED`. An upstream advance blocks finalization/publication until accepted synchronization. Synchronizing a ready final result invalidates its candidate and approval and returns to final reconciliation.

Use `next` or `overview` after transitions. A pending gate, running process, validation candidate, stale assumption or resource conflict is a distinct action condition, not a reason for an unbounded paid-agent polling loop.
