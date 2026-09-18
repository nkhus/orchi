# Recovery and material changes

Read status and next; use recorded tickets, operation IDs and evidence, not chat reconstruction.

| Situation | Action |
|---|---|
| Human gate pending | Show exact request; operator signs approve/reject; apply-decision; never self-sign |
| Worker failed, timed out or blocked | Inspect evidence; known-stopped ticket release; explicit retry if budget remains |
| Lease expired, process status unknown | Stop/confirm termination, then release --stopped; no speculative reissue |
| Controller stopped mid-check/integration | Stop involved controller/check processes; recover-operation --stopped --reason ... |
| Wrong accepted design | Stop/release workers; amend exact next plan, based_on actual head; ask human |
| Later roadmap needs change | Between epics propose roadmap with reason; completed epic contracts are immutable |
| Final review finds a code defect | Human-approved corrective epic; retain final review ledger |
| Canonical moved | Publication blocked; coordinate externally; no unsupported auto-rebase command |
| Review or attempt budget exhausted | Stop and expose evidence; do not reset database/counters or create renamed duplicate tasks |

A recovery call clears an in-flight reservation, not evidence of success. Accepted head advances only after
verified integration. Existing candidate commits are kept for inspection and a bounded repair attempt.
A paused initiative can use resume-request when the previous phase is safe; human approval is required.
There is no background retry loop or unconditional reset.
