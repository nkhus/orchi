# Find, claim, execute, and hand off

## Ownership

An open issue labelled `in-progress` is owned; without it, it is unclaimed.
Closed issues are completed or cancelled; the close reason distinguishes them.
Record the owner as an assignee plus a work reference in the issue body: assistant
session or identifier, branch, and PR. Assistants sharing a GitHub login need
distinct work references.

Only ready Epics and standalone Tasks are independent entry points. A Task under
an Epic belongs to the Epic owner. Mark an Initiative `in-progress` while its
planning or Epics are active; that marker does not block independent Epic claims.

## Find ready work

Run `python3 .agents/skills/orchi/scripts/status.py` for an overview. It reports
each open Epic and standalone Task as:

- `ready`: unclaimed, and every native blocker is closed as completed with a merged PR;
- `check`: unclaimed, but a blocker closed as completed without a linked merged
  PR, so confirm its result reached the integration branch before starting;
- `blocked`: a blocker is open or was cancelled (a cancelled predecessor does not
  satisfy a dependency);
- `claimed`: another owner holds it.

The report is a snapshot of GitHub, not a lock. Confirm that required predecessor
results are merged into this Epic's intended integration branch.

## Claim

Claim by adding `in-progress`, the assignee, and the work reference, then re-read
the issue before editing. Labels are not atomic locks: if claims race or another
active owner appears, resolve ownership before either continues. There is no
scheduler or central unlock. Use native Epic dependencies for real ordering
constraints; if parallel Epics share a changing contract, add the dependency
before concurrent edits. Worktrees separate workspaces; they are not a security
boundary.

## Execute

Read the Epic issue, design, Tasks in order, branch and PR, dependency results,
and scoped instructions. Check that the actual branch matches the issue.

Implement Tasks in sequence on the Epic branch; Tasks have no separate branch or
PR. Mark the current Task `in-progress`. Update code, tests, and owning
documentation together. Run the checks that establish the Task's acceptance and
record the result and commit in the shared PR. A failing check is unresolved
work; an unavailable environment is a verification limitation, not evidence of
success or of a product defect.

Close an Epic Task and remove `in-progress` once its result is implemented and
verified on the Epic branch, recording the commit. Close a standalone Task only
after its PR merges to main. Reopen a Task whose result is invalidated before
integration; keep its earlier evidence.

If new information changes shared contracts, coordinate with affected Epic owners
and update dependencies before conflicting edits. Escalate material direction
changes to the user. Keep pre-existing changes separate from this result. Keep
research prototypes labelled as prototypes until deliberately adopted and verified.

## Hand off and resume

When interrupted or handing over, update the `Handoff` section of the PR body
(create the PR as a draft if needed) with exactly these fields:

```md
## Handoff
- Branch / commit: epic/<tag>-<epic-tag>-<slug> @ <sha>
- Done: <Tasks and results completed>
- Remaining: <next Tasks or open work>
- Uncommitted or local-only changes: <none, or where they are>
- Checks: <commands run and results; known limitations>
- Next step: <one concrete action>
```

Push local-only changes before releasing ownership; a worktree path on one machine
is not available on another. Confirm the former writer has stopped, and remove
ownership only on explicit release or agreed transfer.

To resume, read the Handoff section first, then verify the current diff and target
before continuing. Do not restart planning, recreate Tasks, or discard a
candidate. If a GitHub failure left bookkeeping incomplete, report and reconcile
it. Do not take shared work whose ownership cannot be established.
