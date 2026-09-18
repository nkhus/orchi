---
name: orchi-review
description: "Review an exact integrated Orchi epic or final initiative candidate; triage causal findings, deduplicate, and perform bounded targeted repair. Use at controller review actions only. No unlimited whole-repository review loops and no unrelated style repair."
compatibility: "Requires Git and POSIX; use uv or Python with bundled dependencies. Install all five Orchi skills together."
---

# Review the exact candidate

Use `uv run <skills>/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" …`.
Read [review](../orchi/references/review.md). Read `next` before selecting scope.
Request `review-request --scope epic|initiative --out review-request.json`.
Use a fresh read-only reviewer context: exact definition, candidate diff, required paths and test evidence.
Do not inherit the author's persuasive narrative as evidence; inspect actual paths and contracts.

## Find, then triage

Review only correctness, acceptance, security and regressions attributable to this change.
A blocker requires a concrete causal path, affected criterion, consequence and evidence.
Mark pre-existing unrelated issues advisory. Reject unsupported claims explicitly as unsubstantiated.
Deduplicate by root cause; do not invent cosmetic edits to make a review appear useful.
Preserve every prior blocker with an explicit current disposition; omission is not resolution.
When a concern cannot safely be resolved, mark the review incomplete and return to the human.
Return the structured report with request ID, reviewer, actual coverage, findings and summary.
Submit `review-record --file review.json`.

## Stop rules

Zero significant findings is a successful review; do not demand changes anyway.
One full pass is followed only by bounded targeted passes on repairs and their effects.
Use `repair` only when requested; `$orchi-work` executes the assigned repair packets.
Do not change the approved task scope during repair; use an amendment for a new decision.
Review rounds and attempts survive revisions, renames of sessions and process restarts.
At an unresolved limit, stop; neither another blind pass nor an automatic PASS is permitted.
Final cross-epic blockers require a human-approved corrective epic, not hidden edits to the candidate.
Do not sign approval, publish, modify documentation, or execute untrusted check commands.
