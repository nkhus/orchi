# Review and deliver the assembled result

Use once Tasks are implemented and verification evidence exists. Read the actual
diff, acceptance and design, affected documentation, and check results tied to the
candidate commit. Missing checks go back to the implementer; review consumes
existing evidence and does not launch another test campaign.

## Documentation impact

Every PR needs a filled `Documentation impact` section in its body: either the
owning pages updated, or a short reason why no documentation changes. A missing,
empty, or placeholder section is a blocker. Check that the listed pages actually
describe the changed behavior, and that `knowledge.py lint` passes on the candidate.

## Review

Perform one full Epic review, independently when a reviewer is available; if not,
disclose that limitation rather than claiming independent review. Assess
correctness, requirement coverage, shared contracts, failure behavior, attributable
regressions, and agreement between code and documentation. Report actual coverage
and limitations; do not infer a clean result from the author's summary.

A blocker states the violated criterion, concrete causal path, consequence, and
evidence. Deduplicate root causes. Advisory style, speculative concerns, and
unrelated existing defects do not become required repair Tasks. Repair supported
blockers, rerun affected checks, and do one targeted follow-up over the changed
paths and unresolved findings. If blockers remain, report them and the next
action; never reset review rounds or declare success to exhaust a budget.

## Integrate

Check the PR target explicitly. If it moved after verification, resolve conflicts,
inspect compatibility, and rerun affected checks. Serialize merges into a shared
target, rechecking when another Epic has landed since validation. Squash the Epic
PR into its Initiative branch, or into main for a standalone Epic.

Confirm the merge, confirm its Tasks are completed, then close the Epic and clear
`in-progress`. A closed issue alone does not prove merged implementation. Closing
keywords only work for the default branch; close issues explicitly after merging
into an Initiative branch. Branch dependent Epics from the updated integration
branch.

At final Initiative integration, reconcile with current main, including code and
Core documentation, and check agreed requirement coverage. Run the full applicable
suite on the combined candidate. Review cross-Epic integration and reconciliation,
reusing completed Epic reviews instead of restarting them. Revalidate any repair.
Squash the final PR into main within the user's publication authority, confirm the
merge, then close the Initiative. A small fix uses one proportional review and its
relevant checks.

Report the delivered scope, PR and merge reference, checks, and material
limitations. If publication is pending, say so: local verification is not a
remote merge, and merging is not deployment.
