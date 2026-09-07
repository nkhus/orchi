---
name: orchi-deliver
description: "Reconcile verified intermediate knowledge at an epic boundary, or reconcile Core documentation and prepare final publication after the entire initiative. Use only at controller checkpoint/finalization/publication actions. Never publish an intermediate epic."
compatibility: "Requires Git and POSIX; use uv or Python with bundled dependencies. Install all five Orchi skills together."
---

# Complete the right boundary

Use `uv run <skills>/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" …`.
Read `next`, [knowledge](../orchi/references/knowledge.md) and [delivery](../orchi/references/delivery.md).
Do not confuse epic completion with publication of the user's whole request.

## Epic checkpoint

After all epic tasks, combined checks and review pass, inspect actual integrated code and impact.
Write a checkpoint proposal covering every changed executable path, including explicit no-doc-impact reasons.
Replace, retire or revalidate affected initiative knowledge with passed evidence and exact artifact references.
Store only verified intermediate semantics, never the unimplemented future design.
Use `checkpoint --file checkpoint.json`; the controller stores the scoped overlay and closes the epic.
Do not edit `docs/`, archive the initiative or merge to canonical at this stage.
Return to `$orchi-plan`: design the next epic against this actual checkpoint.

## Entire initiative

Only after all roadmap epics close, use `final-draft --out finalization.json`.
Review cumulative code, root acceptance and all working replacements; the draft itself is not reconciliation.
Produce coherent Core updates and a substantive reconciliation report; retain no future claims.
Use `finalize --file finalization.json`; the controller builds one baseline-parent code-plus-docs commit,
archives initiative material and runs all required checks on the exact final tree.
Route to `$orchi-review` for bounded cross-epic review; then present final human acceptance and stop.
After approval, `publication` returns the exact candidate and expected canonical parent.
An operator performs the normal fast-forward merge, then calls `record-publication --commit <hash>`.
Do not merge automatically. Canonical drift invalidates publication; no silent rebase or deployment.
