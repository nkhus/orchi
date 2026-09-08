---
name: orchi-review
description: "Independently review exact integrated epic, final or upstream-sync candidates; assess causal correctness, semantic scope and traceability with bounded repair. No unrelated style churn, self-approval or publication."
compatibility: "Requires Git and POSIX; use uv or Python with bundled dependencies. Install all five Orchi skills together."
---

# Review the exact candidate

Read next and [review](../orchi/references/review.md).
Use review-request for epic/initiative; sync-check already returns the exact sync review request.
Use a fresh read-only context with actual contracts, required paths, diff and verification evidence.
Do not inherit the author's persuasive narrative as proof.

## Findings

Review correctness, acceptance, security and attributable regressions.
A blocker needs criterion, causal path, consequence and evidence.
Mark unrelated pre-existing issues advisory; unsupported allegations unsubstantiated.
Deduplicate root causes. Preserve every old blocker with an explicit disposition.
If a concern cannot be safely resolved, mark review incomplete instead of guessing PASS.
Return request ID, reviewer, actual coverage, findings and summary.
Submit review-record for epic/final or sync-review for synchronization.

## Semantic boundaries

Check task scope grants and changed snapshot assumptions; a free path is not semantic permission.
Target is not existing implementation; observations/proposed docs are not verified Current.
Challenge requirement and architecture dispositions against actual candidate evidence.
For sync, inspect both versions of code and Core/Working, new upstream ownership and Target impact.
A reviewed sync remains prospective until human acceptance.

## Bounded repair

Zero significant findings is success. One full pass precedes bounded targeted repair passes.
Do not invent cosmetic edits, repeat whole-repository reviews or omit prior blockers.
Use repair only when requested; scope changes need design amendment.
Limits survive revisions. At exhaustion stop with evidence rather than reset or auto-pass.
Final cross-epic code defects need an accepted corrective epic, not hidden candidate edits.
Do not sign, publish, edit docs or execute unregistered check commands.
