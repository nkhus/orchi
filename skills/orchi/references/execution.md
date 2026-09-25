# Execute and hand off an Epic

Use when taking or resuming a ready Epic. Read its issue, design, Tasks in order,
branch/PR, dependency results, and relevant scoped instructions. Check that the
actual branch matches the issue before editing. Claim ownership using the main
skill's GitHub convention; do not introduce tickets or activation commands.

Implement Tasks sequentially in that branch. Update code, relevant tests, and
owning documentation together. Run the checks that establish the Task's acceptance;
record the result and commit in the shared PR and link it from the Task. A check
failure is unresolved work; an unavailable environment is a verification limitation,
not evidence of a product defect or success.

Close an Epic Task only after its result is implemented and verified in the Epic
branch. For a standalone Task, close only after its fix PR merges to main. Keep
`in-progress` until completion or explicit handoff. Reopen completed Tasks whose
result is invalidated; do not erase their prior evidence.

If new information changes shared contracts, coordinate the affected Epic owners
before conflicting edits. Update dependencies if independence no longer holds.
Escalate material direction changes to the user; routine local choices remain
with the owner. Preserve pre-existing changes and separate them from this result.
Research prototypes stay identified as prototypes until deliberately adopted and
verified against product requirements.

For interruption or handoff, leave a short note in the existing issue/PR with:
branch and latest commit, completed and remaining work, relevant uncommitted
changes, checks run and limitations, and the next concrete step. Make local-only
changes accessible to the next owner before relinquishing them. Never assume a
worktree path on one machine is available on another. Confirm the former writer
has stopped; remove ownership only on explicit release or agreed transfer.

Resume from those artifacts and verify the current diff and target, rather than
restarting planning, recreating Tasks, or discarding a candidate. GitHub failures
can leave bookkeeping pending; report and reconcile it on recovery. Do not take
shared work whose ownership cannot be established.
