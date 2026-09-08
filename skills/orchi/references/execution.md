# Bounded execution

Read `next` and the exact task packet. The task may be implemented by an agent, person or pair; the foreground runner dispatches only agent tasks. A worker receives assigned worktree/inputs, not the control store or operator key.

## Prepare and read

Preparation is read-only. Inspect goal, fixed decisions, acceptance, exact before-images, sources, dependency contracts and applicable instructions. Return fingerprint, understood goal, fixed decisions, acceptance IDs and material questions. Any unresolved material question blocks activation; do not invent a solution and report empty questions.

Sources may be inline or on-demand. In the foreground runner, use the ticket-only helper:

```bash
"$ORCHI_WORKER_PYTHON" "$ORCHI_WORKER_REQUEST" read docs/component.md --view current --content-hash "$HASH"
"$ORCHI_WORKER_PYTHON" "$ORCHI_WORKER_REQUEST" read req-example --view target
"$ORCHI_WORKER_PYTHON" "$ORCHI_WORKER_REQUEST" read src/service.py --start-line 1 --end-line 80
```

The channel binds dispatch snapshots and exposes only read and bounded scope acquisition. It does not expose arbitrary CLI/approval/publish actions. The sandbox must permit the local socket; report access failure, never disable the sandbox or read a newer branch instead. In a manual workflow the coordinator relays equivalent `ticket-read` requests. Full-source and returned-slice hashes are distinct.

## Implement inside authority

After activation, implement initial edits and explicitly delegated local choices. Request an additional path only within accepted scope, using ScopeRequest and `scope-acquire` through the coordinator or helper `scope --file -` with JSON stdin. Read any newly returned instructions. A mechanical grant is not approval to change fixed decisions, public contracts or Target. Such discoveries require design/Intent escalation even inside an allowed directory.

Do not edit Core, accepted Intent, installed instructions, policy or protected paths. Write documentation proposals into WorkerResult, not `docs/`. Investigation tasks produce concrete observations and no product diff. Implementation tasks must produce a product diff; fake success is rejected.

Fixed assumptions include declared read_paths, before-images, instructions and extra_reads. Explicit snapshot observations may drift, which triggers wider combined checks and review metadata. Ownership is not a read lock. Report additional fixed code reads; use role-explicit knowledge reads for documents.

## Submit once; integrate the frozen result

Submission freezes exact candidate/evidence, then runs isolated checks without a global integration lock. Exact-head combined checks may overlap other validations. Acceptance uses a short compare-and-swap; a superseded combination is rechecked without another worker session. `validated` means candidate retained, not integrated; the coordinator can call `integrate --ticket` later. Conflicts or changed fixed assumptions block acceptance.

On process loss, inspect ticket/evidence and confirm termination before release/retry. Do not launch duplicate paid sessions because a lease expired. Handoff preserves candidate/notes and rechecks grants, creates a new readiness boundary and fences the old executor. An existing candidate can be imported only into a clean activated worktree with matching before-images and valid scope/assumptions. No imported result carries automatic approval.

Checks and review establish acceptance; a worktree is not a security sandbox. Real credentials, shared resources and controller access remain operator-controlled.
