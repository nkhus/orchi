# Review and deliver the assembled result

Use once Tasks are implemented and relevant verification is available. Read the
actual diff, acceptance/design, affected documentation, and check results tied
to the candidate commit. Missing checks return to the implementer for verification;
review consumes existing evidence and does not launch another test campaign.

Perform one full Epic review, independently when a reviewer is available. Assess
correctness, requirement coverage, shared contracts, failure behavior, attributable
regressions, and agreement between code and documentation. Report actual coverage
and limitations; do not infer a clean result from an author's summary.

A blocker states the violated criterion, concrete causal path, consequence, and
evidence. Deduplicate root causes. Advisory style, speculative concerns, and
unrelated existing defects do not become required repair Tasks. Repair supported
blockers, rerun affected checks, and perform one targeted follow-up over changed
paths and unresolved findings. If blockers remain, report them and the needed
next action; never reset review rounds or declare success to exhaust a budget.

Check the PR target explicitly and serialize integration into the shared branch.
If the target changed after verification, inspect compatibility and rerun affected
checks before merging. Squash the Epic PR into its Initiative branch, or main
for a standalone Epic. Confirm the merge, close the Epic, and clear ownership.
Non-default branch merges need explicit issue bookkeeping. Do not treat a cancelled
or manually closed predecessor as satisfying a dependency.

At final Initiative integration, reconcile current main, code, Core, and agreed
requirement coverage. Run the full applicable suite on the combined candidate.
Review cross-Epic integration and final reconciliation, reusing completed Epic
reviews instead of restarting them. Any repair needs relevant revalidation.
Squash the final PR to main within the user's publication authority, confirm the
merge, then close the Initiative. A small fix uses one proportional review and
its relevant checks, with no Epic/final review ceremony.

Report the actual delivered scope, PR/merge reference, checks, and material
limitations. If publication is pending, say so; local verification is not a remote
merge, and merging is not deployment. Preserve evidence in existing PRs/history;
there is no checkpoint proposal, exported attestation, or release receipt.
