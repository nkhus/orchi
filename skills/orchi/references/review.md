# Finite review campaign

One ledger per epic plus one final cross-epic ledger. A new conversation or amended plan does not reset it.
Default maximum three accepted reports: initial full review plus at most two targeted follow-ups.
Repeated requests for an outstanding review return the same request, not a new round.
Targeted requests include changed paths since the last review and all prior findings needing disposition.

Report only what was actually inspected. Each blocker needs a changed path, violated criterion, causal
root cause, consequence and concrete evidence. Assign repairing task IDs only when inside approved scopes.
An unrelated old problem is advisory. `unsubstantiated` means explicitly triaged as nonblocking because a
credible causal claim was not established; it is not a way to hide an unresolved material risk.
If a material concern cannot be resolved, submit complete=false and escalate once.

Duplicates collapse on normalized path + criterion + root cause. Known blockers cannot disappear from the next
report; resolve or explicitly reclassify with evidence. No significant findings is a valid successful report.
At the budget limit unresolved blockers pause, never pass. Incomplete review also pauses.
Report attribution and coverage are evidence claims; the controller cannot prove reviewer independence or
semantic quality. Human high-risk review remains important.

Targeted repair reuses original scopes and preserved attempt counters. New architectural decisions require
amendment. Final cross-epic defects use a human-approved corrective epic appended to the roadmap.
Do not request a broad new review after a clean report just because budget remains.
