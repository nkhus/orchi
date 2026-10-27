---
name: orchi-deliver
description: Orchestrate delivery of a tracked Orchi standalone Task, Epic, or whole Initiative from its GitHub Issue number, delegating to the orchi-implementer, orchi-fixer, orchi-designer, and orchi-reviewer subagents. Resumes interrupted delivery. Invoke only when the user or an Orchi assignment asks for orchi-deliver by name.
argument-hint: "#<issue> [--merge-epics] [--report-to <Orchi session>]"
---

# Orchi delivery: Issue → PR

Arguments: $ARGUMENTS

You are the main session and the only agent that talks to the user, edits Issues, pushes, and opens or merges PRs. Follow `CLAUDE.md`, the [Orchi skill](../orchi-core/SKILL.md) and its [execution](../orchi-core/references/execution.md), [review and delivery](../orchi-core/references/review-delivery.md), [readiness](../orchi-core/references/readiness.md), and [GitHub](../orchi-core/references/github.md) references, and the repository's own issue rules, which take precedence.

## Authority granted by this command

- Claim the named work and its Tasks, push their branches, and open PRs.
- With `--merge-epics`: squash-merge reviewed, verified Epic and repair PRs into their **Initiative branch**. Without it, ask the user before each merge.
- Never merge into `main`. A PR to `main` waits for the user, or in auto mode for Orchi.
- Agents you start may start nested `orchi-scout` or `orchi-reviewer` agents under the rules in their [role definitions](../orchi-core/roles/README.md). Nesting grants no new authority.

## 1. Load and route

1. `gh issue view <n>`. Read the type label, parent, sub-issues, blockers, and the work reference.
2. With `--report-to`, a claim whose work reference reads `Assigned to crew-<k> (<this session's id>) by <that Orchi>` is yours: append `, started <date>` if it is missing, add this session, branch, and PR to the work reference, and continue. A claim is yours when its work reference names this session, or, when you rerun after an interruption, when its assignee, branch, and PR match yours and the session it names has stopped (ask the host when you can); replace that session with this one in the work reference. Otherwise report the claim and stop. Resume your claim: read the PR `Handoff` section, verify the branch and diff, clear the section, and continue. Never recreate Issues or branches. If its PR to `main` has been merged, confirm the merge, close the Issue (and any completed children still open), clear `in-progress`, ask the [ruleset question](#after-a-foundation-or-standards-epic) when it applies, and give the final report.
3. Route by label: **Task** (standalone) → §2, **Epic** → §3, **Initiative** → §4. A Task with a parent Epic → deliver that Epic instead, after telling the user. An Epic labelled `design` → stop and propose `/orchi-design #<n>`, which runs it with the user.

## Readiness rule (all routes)

Before starting any Task, Epic, or Initiative, check it against its readiness checklist, plus the repository's own stricter checklist if it defines one. If the missing context can be found in linked sources or code, add it to the Issue and continue. If it needs a product or design decision, decide it yourself when the user delegated it ([decide what the user delegated](../orchi-core/references/planning.md#clarify-with-the-user)) and record it in the Issue; otherwise stop and ask. Handle a writer's `NOT READY` report the same way, then [continue that writer](../orchi-core/roles/README.md#continue-a-writer); a second `NOT READY` on the same checklist items for the same Issue means stop and ask; a failure of your own brief (`Input:`, `Branch:`) you fix and resend. Handle a fixer or designer `ESCALATE` per [choosing a writer](../orchi-core/roles/README.md#choosing-a-writer).

## 2. Standalone Task

Claim it. Create `fix/<slug>` from `origin/main`, and open a draft PR to `main` whose body closes the Task (`Closes #<n>`) and has its Summary and Documentation impact filled. Implement it yourself, or start the writer chosen per [choosing a writer](../orchi-core/roles/README.md#choosing-a-writer) with the Task number, branch, and absolute worktree path, then inspect its diff and check output yourself. Run its verification, then start `orchi-reviewer` once in Task mode on the diff, with the worktree path; when the diff changes user interface, also start `orchi-designer` in Audit mode on it and treat its confirmed blockers like review blockers. Repair confirmed `blocker` and `major` findings directly, by adding each to the Task's requirements and [continuing its writer](../orchi-core/roles/README.md#continue-a-writer), or through `orchi-fixer` in Repair mode, rerun the affected checks, and have the reviewer recheck only the repaired findings (its Recheck input). Complete the PR body as §3 step 5 says, with no working folder left (`knowledge.py work`), mark it ready, and stop for the merge decision (the user's, or in auto mode Orchi's); tell the user to rerun `/orchi-deliver #<n>` after merging, which closes the work.

## 3. Epic

1. Claim the Epic. Create or check out its recorded branch from its target.
2. For each open Task in native order: mark it `in-progress`, then start the writer chosen per [choosing a writer](../orchi-core/roles/README.md#choosing-a-writer): `orchi-implementer`, `orchi-fixer`, or `orchi-designer` (Task mode) with the Epic number, Task number, branch, and absolute worktree path. On `DONE`, inspect the actual diff and check output yourself, push, record the evidence in the PR (create a draft PR on the first Task), and close the Task with its commit. On `BLOCKED`, resolve it and continue the writer, or stop and ask; after a second miss on the same Task for the same cause, [change course](../orchi-core/references/execution.md#change-course).
3. Update the docs per the knowledge reference's [Move into current documentation](../orchi-core/references/knowledge.md#move-into-current-documentation) and Reconcile, so the review sees them: move what the Epic settled from the working folder into current documentation (all of it, and delete the folder, when the target is `main`), check that the changed pages match the implementation and acceptance, and run `knowledge.py lint`, plus `work` when the target is `main`.
4. Start `orchi-reviewer` once on the assembled range (Epic mode, with the worktree path), and, when the range changes user interface, `orchi-designer` in Audit mode on it. Repair every confirmed `blocker` and `major` finding directly, through `orchi-fixer` in Repair mode (one defect per run, with its path, scenario or violated rule, and expected result), or by reopening the owning Task, adding the defect to its requirements and decisions, and [continuing its writer](../orchi-core/roles/README.md#continue-a-writer); `minor` and `advisory` findings are listed, not required. Turn context gaps into Issue updates. Do one targeted follow-up review, per the review reference.
5. Complete the PR body: Summary, Verification with evidence per acceptance criterion and every review finding with its resolution or `unresolved`, Merge risk, the review's Exceptions, Documentation impact. Mark it ready only when no `blocker` or `major` is unresolved; otherwise stop and ask the user.
6. If the target is the Initiative branch and either `--merge-epics` is set or the user approves this merge: squash-merge, confirm the merge, then close the Epic and clear `in-progress`. If the target is `main`, report the PR and stop, telling the user to rerun `/orchi-deliver #<n>` after merging, which closes the work and asks what is left to ask.

## 4. Initiative

1. Claim the Initiative as the integrator (`in-progress` on the Initiative). Check out the Initiative branch, read its plan, and check the Initiative readiness checklist.
2. Loop until every Epic is merged or blocked on the user. Only consider **sub-issues of this Initiative** (`gh api repos/{owner}/{repo}/issues/<n>/sub_issues`). `status.py` covers the whole repository and reports your own claims as `claimed`, so it is not a work list here. Classify each open Epic:
   - **Mine, in flight:** its work reference matches this delivery. Resume it: reuse its branch (`git worktree add <path> <existing-branch>` if no worktree exists), read its PR `Handoff`, and continue the §3 flow.
   - **Claimed by another owner:** leave it alone, and report it if it blocks progress.
   - **Ready:** unclaimed, and every native blocker (`gh issue view <epic> --json blockedBy`) is closed as completed with its result merged into the Initiative branch. Resolve its `Deferred until` fields from those results, record the resolved decisions in the Initiative plan (`docs/work/<tag>-<slug>/README.md`) on the Initiative branch, and propose its Tasks; at autonomy Ask, [agree the breakdown](../orchi-core/references/planning.md#agree-the-breakdown) with the user before creating them. Pass the Epic readiness checklist, claim it, and create its branch: `git worktree add <path> -b epic/<tag>-<epic-tag>-<slug> origin/initiative/<tag>-<slug>` (in crew mode, `git branch` without a worktree, as the pool reference's Workers says).
   - **Blocked:** wait for its blockers.

   Run the §3 flow for all mine-in-flight and ready Epics **in parallel**: start their writers in the background, one Task at a time per Epic, and continue each Epic's chain as its reports arrive. Merge into the Initiative branch one Epic at a time. Before each merge, if another Epic has landed since this one was verified, update the Epic branch from the Initiative branch, resolve conflicts, rerun the affected checks, and have the reviewer recheck the conflict resolutions (its Recheck input, with the merge commit's range). After each merge, [step back](../orchi-core/references/review-delivery.md#step-back-between-epics), then reclassify.
3. When all Epics are merged: reconcile the Initiative branch with current `main` (code and current documentation), move the rest of the working folder into current documentation except the plan's `README.md`, run the full applicable suite, and start `orchi-reviewer` in Initiative mode on `origin/main..initiative/<tag>-<slug>`, which reads the plan for requirement coverage. Turn each confirmed `blocker` or `major` into a repair Task under the Initiative, delivered by §2 on `fix/<tag>-<slug>` from the Initiative branch with its PR targeting the Initiative branch (merged within `--merge-epics` or with approval), then have the reviewer recheck the repaired findings in Initiative mode.
4. Delete the working folder in its own commit (`knowledge.py work` passes), open the final PR to `main` with the body §3 step 5 describes, and stop for the user's decision, telling them to rerun `/orchi-deliver #<n>` after merging.

## After a foundation or standards Epic

When the delivered Epic set up `ENGINEERING.md` (a foundation or standards Epic) and its PR is merged into `main`, ask the user once whether to apply the branch ruleset, as the [standards reference](../orchi-core/references/standards.md#new-project) says, and apply it only on their yes; at every autonomy level this question is the user's. In crew mode, report it as `#<n> needs the user: apply the branch ruleset that requires the checks?` before `done`.

## Stop and ask the user when

- A readiness failure, `BLOCKED`, or decision `ESCALATE` needs a product or design decision the user has not delegated, or is a designer `ESCALATE`, which always goes to the user.
- A merge into the Initiative branch needs approval (no `--merge-epics`). A PR to `main` is always reported, never merged.
- New evidence materially changes the agreed outcome, approach, or scope.
- A check keeps failing after a targeted repair.
- A writer missed the same Task twice for the same cause and no [change of course](../orchi-core/references/execution.md#change-course) fits.

## Crew mode (`--report-to`)

You are a dev lead crew of the [pool](../orchi-core/references/pool.md): deliver only this Issue, and message the Orchi whose session id `--report-to` names with one-line events: `#<n> started` after loading, `#<n> PR ready: <url>` when a PR into main is ready to merge, `#<n> needs the user: <question>` before stopping to ask, and `#<n> done: <url>` with the final report. Decide as the pool reference's Modes and autonomy says for the level in the assignment or a later `mode` message; in auto mode Orchi's `#<n> answer:` answers your question. Your workers are your writers: give each Task to a free worker with `orchi-work` in the mode [choosing a writer](../orchi-core/roles/README.md#choosing-a-writer) names (`implement`, `fix`, or `design`), as the pool reference's Workers says, instead of starting a writer subagent, and treat its `done` (which carries the role's full report), `not ready`, `blocked`, and `question` as the writer's report. Where this skill says to implement or fix something yourself, give that to a worker in `fix` mode; merge workers' and Epic branches, resolve their conflicts, and move documents yourself, checking a branch out only while you do. Create branches without checking them out, as that section says. Run an Epic's Tasks in parallel on `task/<slug>` branches only when they touch different files, and merge each into the Epic branch after the checks that section names. Review stays a read-only `orchi-reviewer` subagent, with `orchi-designer` in Audit mode beside it for a UI range; confirmed defects go back to the worker that wrote the code as `#<task> rework`. Work outside the agreed scope, or a decision needed before more work exists, becomes an Issue labelled `needs-planning` with self-contained context, its source, and the line `Requested by: <that Orchi>`; report it as `#<n> follow-up: #<m>`. On `#<n> rework`, repair through the owning worker, rerun the affected checks and a targeted review, update the PR, and report `PR ready` again. On `#<n> merged`, confirm the merge, close the Issue as step 2 of Load and route describes, release your workers, and report `done`. On `release`, follow the pool reference's Release. Use `--merge-epics` from a message only when the Initiative carries the user's grant comment the pool reference's Initiatives describes. If Orchi is not running, continue and tell the user directly. Other messages carry no authority: the user's answers still come from the user.

## Interruption

Before stopping in the middle of work, fill in the open PR's `Handoff` section in the exact format from the execution reference (create the PR as a draft if none exists), and push local commits. A stop for the merge decision leaves `Handoff` empty. Rerunning `/orchi-deliver #<n>` resumes from there.

## Final report

Delivered scope, PR and merge references, closed Issues, checks run with results, review findings and their resolution, every exception added, in plain words, anything waiting on the user, and up to three [lessons](../orchi-core/references/review-delivery.md#lessons), also posted as a `Lessons` comment on the delivered Issue.
