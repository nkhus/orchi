# Execution protocol

1. `claim --task <id>` atomically reserves read/write paths and exclusive resources and issues a ticket.
2. Give the worker its assigned worktree and input directory (TASK.md, packet.json, README.txt).
3. Prepare read-only: return readiness with exact fingerprint, understood goal, fixed decisions, criterion IDs,
   and questions. Nonempty questions block writing.
4. `activate --ticket <ticket> --file readiness.json` checks bindings and current read assumptions.
5. Implement only declared edits. No git commit, plans/Core edits, merge, keys, control state or policy changes.
6. `submit --ticket <ticket> --file result.json` captures the actual tree and tests it, then tests a fresh
   combination with already accepted work. Only this advances the internal initiative head.

Use the foreground `run --adapter ...` for automatic preparation/execution process pairs and ready-task drain.
The default Codex adapter uses read-only preparation, workspace-write execution and explicit no-interaction
approval policy. It does not bypass the sandbox. Model and environment are operator choices.
Other assistants can use the same packet through a registered command adapter or a manual operator relay.

Read/write overlap is serialized; semantic conflicts not visible in declared paths still require tests/review.
New reads must be reported in result.extra_reads. Changed read assumptions reject stale results.
Task code passes do not permit Core writes. Per-task counters, epic counters, total attempt limits and leases persist.
Unknown exits require explicit process-stop attestation before release/retry. Expiration alone never requeues.
A read-only preparation that modifies the worktree is rejected by the local runner.

The controller enforces candidate acceptance, not adversarial process isolation. Use real OS/container policy
for shared Git metadata, secrets, external systems, policy and control-state separation.
