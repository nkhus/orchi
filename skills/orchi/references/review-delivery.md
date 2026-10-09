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

Keep three axes apart, so that a pass on one cannot hide a failure on another:
**Spec** (the Issues' requirements, acceptance, and scenarios, including scope
creep: behavior no requirement asks for), **Standards** (the repository's rules
and documentation), and **Tests** (per [testing](testing.md#review-the-tests)).
A new or changed test without red evidence or a stated reason goes back to its
writer like any other missing check. Remove scope creep, or agree it with the
user and record the decision; never accept it silently.

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

## Lessons

After delivery, turn what went wrong into changes to the environment rather
than into more instructions. Collect the events this delivery produced: `NOT
READY` and `ESCALATE` reports, review blockers and context gaps, repair rounds,
checks that failed late, held messages, and corrections the user made.

For an event that could recur, propose one change on the first rung that fits:

1. A deterministic check (test, lint rule, CI job, or hook) for a mechanical
   mistake.
2. A field or item in the repository's Issue forms or stricter readiness
   checklist, for context an Issue lacked.
3. A rule in the coding standards the reviewer reads, for a judgement call.
4. A pointer in `CLAUDE.md` or `AGENTS.md`, for something an agent could not
   find.
5. An Issue in the Orchi repository, for a defect in Orchi itself.

Propose removing an instruction that changed nothing, too. Each lesson names
its event (an Issue, PR, or finding link) and its rung; without an observed
event it is not a lesson. Report at most three, most costly first, and post
them as a `Lessons` comment on the delivered Issue. Only propose: never change
instructions, checklists, or checks on your own. The session that ran the
delivery files each lesson the user accepts as an Issue labelled `retro` and
`needs-planning`, which planning takes like any request. When a failure recurs after its `retro`
Issue closed, say so: that change did not work, and the next one belongs on a
more deterministic rung.
