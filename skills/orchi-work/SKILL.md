---
name: orchi-work
description: "Execute one ready Orchi task or dispatch approved independent tasks through the local runner. Use only after epic approval; consume generated task packets, prepare readiness, implement bounded changes, and submit verifiable candidates. Do not plan, review globally, or update Core."
compatibility: "Requires Git and POSIX; use uv or Python with bundled dependencies. Install all five Orchi skills together."
---

# Execute approved tasks

For a packet-only worker session, return readiness/result to the controller; do not claim tasks or access control state.
The commands below are for the coordinator or operator relay, not the sandboxed child worker.

Read `next`. Only ready, unblocked tasks may run; a worktree alone does not establish independence.
Use `uv run <skills>/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" …`.
Read [execution](../orchi/references/execution.md) for the exact claim/readiness/result protocol.

For `repair_confirmed_findings`, run `repair` once, then follow the resulting ready-task state.

## Coordinated parallel execution

Use `run --adapter /operator/config/adapter.json` with a trusted operator-provided adapter.
The foreground runner claims ready tasks, runs separate processes/worktrees and validates candidates.
It stops at epic review, a human gate, a checkpoint, or a blocker; it is not a background daemon.
Do not spawn untracked workers or bypass declared read/write/resource reservations.

## One portable packet

For a manual assistant, use `claim --task <id>` and hand off its assigned worktree plus input packet.
Read `TASK.md`, exact referenced sources and relevant repository instructions.
Return readiness with the packet fingerprint, task goal, fixed decisions and covered acceptance IDs.
Run `activate --ticket <id> --file readiness.json` before writing.
If preparation finds a missing major decision or contradiction, return blocked; do not improvise.
Implement only declared paths in the assigned checkout. Do not commit, merge or edit `docs/`, plans or policy.
Follow fixed decisions; make only delegated local choices. Record extra reads and deviations honestly.
Return `completed` or `blocked`, summary, extra reads and deviations; submit the exact ticket and result.
The controller runs actual candidate and combined-tree checks before advancing the internal head.
A reported completion is not integration. An expired lease is not permission to restart a second worker.

On failure inspect recorded evidence. Retry only explicitly and within retained attempt budgets.
Do not start another broad code review or expand scope to unrelated defects.
Read [recovery](../orchi/references/recovery.md) for uncertain process exits or integration failures.
