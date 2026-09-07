# Controller protocol

## CLI and state routing

Use the installed entrypoint:

```bash
uv run /path/to/skills/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" next
```

`--control` takes precedence over the `ORCHI_CONTROL` environment variable. `doctor` and `schemas --out <directory>` do not require a control store. Other commands require operator-owned state. Place global options before the command. Successful commands return a JSON envelope with `ok` and `result`; contract/input errors return `ok: false`, a code, and a message. Exit codes are 0 for normal results, 2 for input/contract errors, and 3 for a reported blocked result. Argument-parser usage errors also exit 2.

| Phase | Next responsibility |
| --- | --- |
| `EMPTY` | Define the initiative |
| `AWAITING_APPROVAL` | Present the exact request and await the human decision |
| `PLANNING` | Design the next epic against actual state |
| `EXECUTING` | Claim/run ready tasks or report wait/block conditions |
| `REVIEW` | Request or complete epic review |
| `REPAIR_REQUIRED` | Prepare bounded repair work |
| `KNOWLEDGE` | Checkpoint verified intermediate knowledge |
| `FINALIZING` | Reconcile cumulative Core |
| `FINAL_REVIEW` | Review the exact final candidate, then obtain approval |
| `READY_TO_PUBLISH` | Return operator publication instructions |
| `PUBLISHED` | Report the completed publication |
| `PAUSED` | Require explicit resolution |

`next` supplies machine-readable routing; skills do not guess the phase from chat history. Waiting does not start another paid model session. The foreground runner does not cross approval, review, or knowledge boundaries automatically.

## Approval binding

A gate request includes an identifier, kind, initiative, baseline, accepted head, policy digest, exact inputs, and expiry. The operator signs the request together with the decision and operator identifier. A changed request invalidates the prior signature. Replaying a consumed decision does not authorize another transition.

`gate` exports the pending request. `refresh-gate` creates a new request when required; the human reviews and signs that request. `apply-decision` verifies the exact binding. Rejection returns to an allowed planning boundary or pauses work; silence is never approval.

## Claims, attempts, and fencing

A transactional claim reserves a ready task, its paths, and exclusive resources. Defaults are four workers, three attempts per task, 48 attempts per epic, and 200 attempts per initiative. These are operator-adjustable operational limits, not empirically optimal settings. Default process time is 900 seconds and lease duration is 3,600 seconds; size both preparation and execution with verification/queue overhead in mind.

`activate` and `submit` validate ticket identity, epoch, plan digest, status, expiry, and context bindings. New plan revisions do not accept old tickets. New sessions and amendments do not erase attempts or review ledgers. Expiry alone does not requeue a worker.

## Verification and integration

The operator's fixed registry maps check identifiers to trusted argument arrays and timeouts. The controller executes commands without a shell in a checkout of the exact candidate, with a minimal environment, bounded output, and POSIX process-group termination. Observed records include command, return code, stop reason, output, elapsed time, commit/tree, and policy identity.

Task verification first checks the isolated candidate and then the combined tree with already accepted work. Required regression checks continue to apply. The worker's own report is not a substitute for these observations.

Use stable suite, lint, or type-check commands that exercise the current snapshot. The controller does not allow workers to add arbitrary commands to the trusted registry. Changes to tests remain reviewable code; independent acceptance tests and worktree dependency provisioning are operator responsibilities.

## Review ledger

Each epic has a review ledger; the initiative has a separate final ledger. The default budget is one full report and at most two targeted follow-ups. A clean complete review passes without manufacturing edits. Blockers must be tied to changed paths, violated criteria, causal effects, and evidence. Unrelated pre-existing findings remain advisory.

An unresolved blocker cannot disappear from subsequent reports without disposition. An incomplete report or exhausted unresolved review budget pauses work. It does not trigger an unbounded retry or automatic success.

## Recovery and change

Long operations reserve durable state before execution and accept only against the same operation and head. After a crash, stop involved processes before `recover-operation --stopped --reason ...`. Recovery clears an uncertain reservation; it does not invent successful evidence or accept code.

For an expired or failed worker, confirm termination, use `release --stopped`, then choose an explicit `retry` within the retained budget. Active design changes require an exact signed `amend`. Future scope changes use `roadmap` between epics. A final code defect requires an approved corrective epic while retaining the final review ledger.

Canonical movement blocks publication: baseline-specific proof and approval cannot silently transfer to another base. Coordinate and replan explicitly; automatic rebase or forced publication is not supported. Exported audit material is evidence, not an automatic live-state restore mechanism.
