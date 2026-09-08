# Recovery without losing authority

Use `overview`, `status` and `next`, not chat reconstruction. Record the actual process/ticket/operation, preserved candidate and evidence.

| Situation | Action |
| --- | --- |
| Human gate pending | Inspect exact request; human `decide` or sign/apply; never self-sign |
| Per-ticket check interrupted | Confirm verifier/worker stopped; `release --stopped`, then explicit retry or handoff |
| Aggregate checkpoint/final/sync check interrupted | Stop involved processes; `recover-operation --stopped --reason ...` |
| Lease expired, process unknown | Establish termination before reissue; expiry alone is not a stop attestation |
| Validated candidate awaiting composition | `integrate --ticket`; no new coding session or repeated isolated verification |
| Written path / fixed read stale | Preserve candidate; replan or reconcile against a fresh packet, never force-accept |
| Additional local file | Acquire only a delegated path/action/choice; shared decisions still escalate |
| Pending-task clarification | Narrow `amend-tasks` only if shared design/acceptance/unaffected contracts stay identical |
| Shared implementation design wrong | Stop/release and `amend` exact plan/design; keep attempt budgets/history |
| Material Target wrong | At a closed boundary use accepted Intent revision; stop/accept stop-epic first when active |
| Canonical moved | Explicit [synchronization](synchronization.md), including Core/Working and final reapproval |
| Ready final candidate made stale | Sync/reconcile/check/review/sign again; do not reuse its old approval |
| Person takes over | `handoff --stopped --executor human`; inspect notes and reacquired/blocked scopes |
| Limits exhausted | Stop with evidence; do not rename tasks, reset counters or make a new store to evade budgets |

Release clears ownership, not proof of success. A stopped task's frozen candidate survives; retries/handoffs get a new fenced ticket and exact context. Unknown scopes or stale fixed assumptions can prevent automatic import even when a person takes over. Manual reconciliation must follow the new accepted packet.

`withdraw-gate` records the withdrawn request and returns to the previous phase. Rejecting a narrow tasks amendment preserves the unchanged execution contracts; rejecting a sync leaves its prospective candidate available for inspection/discard. `sync-discard` never changes Current.

A paused initiative uses `resume-request` only from a safe phase, with human acceptance. Aggregate recovery and stopped-epic rollback do not automatically rebase, verify, publish or deploy. Preserve controller export and Git objects when internal candidates must remain replayable.
