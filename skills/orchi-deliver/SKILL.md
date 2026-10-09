---
name: orchi-deliver
description: Orchestrate delivery of a tracked Orchi standalone Task, Epic, or whole Initiative from its GitHub Issue number, delegating to the orchi-implementer, orchi-fixer, orchi-designer, and orchi-reviewer subagents. Resumes interrupted delivery.
argument-hint: "#<issue> [--merge-epics] [--report-to <orchestrator session>]"
disable-model-invocation: true
---

# Orchi delivery: Issue → PR

Arguments: $ARGUMENTS

You are the main session: orchestrator and the only agent that talks to the user, edits Issues, pushes, and opens or merges PRs. Follow `CLAUDE.md`, the [Orchi skill](../orchi/SKILL.md) and its [execution](../orchi/references/execution.md), [review and delivery](../orchi/references/review-delivery.md), [readiness](../orchi/references/readiness.md), and [GitHub](../orchi/references/github.md) references, and the repository's own issue rules, which take precedence.

## Authority granted by this command

- Claim the named work and its Tasks, push their branches, and open PRs.
- With `--merge-epics`: squash-merge reviewed, verified Epic and repair PRs into their **Initiative branch**. Without it, ask the user before each merge.
- Never merge into `main`. A PR to `main` always waits for the user.
- Agents you start may start nested `orchi-scout` or `orchi-reviewer` agents under the rules in their [role definitions](../orchi/roles/README.md). Nesting grants no new authority.

## 1. Load and route

1. `gh issue view <n>`. Read the type label, parent, sub-issues, blockers, and the work reference.
2. With `--report-to`, a claim whose work reference reads `Dispatched to orchi-worker #<n> … by <that orchestrator>` is yours: replace the work reference with this session, branch, and PR, and continue. If another owner has claimed it, report the claim and stop. If it is yours (same work reference), resume: read the PR `Handoff` section, then verify the branch and diff before continuing. Never recreate Issues or branches. If its PR to `main` has been merged by the user, confirm the merge, close the Issue (and any completed children still open), clear `in-progress`, and give the final report.
3. Route by label: **Task** (standalone) → §2, **Epic** → §3, **Initiative** → §4. A Task with a parent Epic → deliver that Epic instead, after telling the user.

## Readiness rule (all routes)

Before starting any Task, Epic, or Initiative, check it against its readiness checklist, plus the repository's own stricter checklist if it defines one. If the missing context can be found in linked sources or code, add it to the Issue and continue. If it needs a product or design decision, decide it yourself when the user delegated it ([decide what the user delegated](../orchi/references/planning.md#clarify-with-the-user)) and record it in the Issue; otherwise stop and ask. Handle a writer's `NOT READY` report the same way, then restart that writer; a second `NOT READY` for the same Issue means stop and ask. Handle a fixer or designer `ESCALATE` per [choosing a writer](../orchi/roles/README.md#choosing-a-writer).

## 2. Standalone Task

Claim it. Create `fix/<slug>` from `origin/main`. Implement it yourself, or start the writer chosen per [choosing a writer](../orchi/roles/README.md#choosing-a-writer) with the Task number, branch, and absolute worktree path, then inspect its diff and check output yourself. Run its verification, then start `orchi-reviewer` once in Task mode on the diff; when the diff changes user interface, also start `orchi-designer` in Audit mode on it and treat its confirmed blockers like review blockers. Repair confirmed blockers directly or through `orchi-fixer` in Repair mode, rerun the affected checks, and have the reviewer recheck only the repaired findings. Open a PR to `main` with the review result in its Verification section and its Merge risk filled, and stop for the user's merge decision.

## 3. Epic

1. Claim the Epic. Create or check out its recorded branch from its target.
2. For each open Task in native order: mark it `in-progress`, then start the writer chosen per [choosing a writer](../orchi/roles/README.md#choosing-a-writer): `orchi-implementer`, `orchi-fixer`, or `orchi-designer` (Task mode) with the Epic number, Task number, branch, and absolute worktree path. On `DONE`, inspect the actual diff and check output yourself, push, record the evidence in the PR (create a draft PR on the first Task), and close the Task with its commit. On `BLOCKED`, resolve it or stop and ask.
3. Start `orchi-reviewer` once on the assembled range (Epic mode), and, when the range changes user interface, `orchi-designer` in Audit mode on it. Fix confirmed defects directly, through `orchi-fixer` in Repair mode (one defect per run, with its path, scenario, and expected result), or by reopening the owning Task, adding the defect to its requirements and decisions, and restarting its writer. Turn context gaps into Issue updates. Do one targeted follow-up review, per the review reference.
4. Complete the PR body (Summary, Verification, Merge risk, Documentation impact) and mark it ready.
5. Before merging, reconcile the docs per the knowledge reference § Reconcile: the changed Core pages match the implementation and acceptance, and `knowledge.py lint` passes.
6. If the target is the Initiative branch and either `--merge-epics` is set or the user approves this merge: squash-merge, confirm the merge, then close the Epic and clear `in-progress`. If the target is `main`, report the PR and stop; the user merges.

## 4. Initiative

1. Claim the Initiative as the integrator (`in-progress` on the Initiative). Check out the Initiative branch, read its plan, and check the Initiative readiness checklist.
2. Loop until every Epic is merged or blocked on the user. Only consider **sub-issues of this Initiative** (`gh api repos/{owner}/{repo}/issues/<n>/sub_issues`). `status.py` covers the whole repository and reports your own claims as `claimed`, so it is not a work list here. Classify each open Epic:
   - **Mine, in flight:** its work reference matches this delivery. Resume it: reuse its branch (`git worktree add <path> <existing-branch>` if no worktree exists), read its PR `Handoff`, and continue the §3 flow.
   - **Claimed by another owner:** leave it alone, and report it if it blocks progress.
   - **Ready:** unclaimed, and every native blocker (`gh issue view <epic> --json blockedBy`) is closed as completed with its result merged into the Initiative branch. Resolve its `Deferred until` fields from those results, record the resolved decisions in the Initiative plan (`docs/initiatives/<tag>-<slug>/README.md`) on the Initiative branch, split it into Tasks, pass the Epic readiness checklist, claim it, and create its worktree: `git worktree add <path> -b epic/<tag>-<epic-tag>-<slug> origin/initiative/<tag>-<slug>`.
   - **Blocked:** wait for its blockers.

   Run the §3 flow for all mine-in-flight and ready Epics **in parallel**: start their writers in the background, one Task at a time per Epic, and continue each Epic's chain as its reports arrive. Merge into the Initiative branch one Epic at a time. Before each merge, if another Epic has landed since this one was verified, update the Epic branch from the Initiative branch, resolve conflicts, and rerun the affected checks. After each merge, reclassify.
3. When all Epics are merged: reconcile the Initiative branch with current `main` (code and Core documentation), run the full applicable suite, and start `orchi-reviewer` in Initiative mode on `origin/main..initiative/<tag>-<slug>`. Turn each confirmed blocker into a repair Task under the Initiative, delivered by §2 on `fix/<tag>-<slug>` from the Initiative branch with its PR targeting the Initiative branch (merged within `--merge-epics` or with approval), then have the reviewer recheck the repaired findings in Initiative mode.
4. Open the final PR to `main` and stop for the user's decision.

## Stop and ask the user when

- A readiness failure, `BLOCKED`, or decision `ESCALATE` (including every designer `ESCALATE`) needs a product or design decision the user has not delegated.
- A merge needs approval (no `--merge-epics`, or the target is `main`).
- New evidence materially changes the agreed outcome, approach, or scope.
- A check keeps failing after a targeted repair.

## Team mode (`--report-to`)

You are a worker of the [team](../orchi/references/team.md): name this session `orchi-worker #<n> · <repo>`, deliver only this Issue, and message the named orchestrator with one-line events: `#<n> started` after loading, `#<n> PR ready: <url>` when a PR into main waits for the user, `#<n> needs the user: <question>` before stopping to ask, and `#<n> done: <url>` with the final report. Work outside the agreed scope, or a decision needed before more work exists, becomes an Issue labelled `needs-planning` with self-contained context and its source; report it as `#<n> follow-up: #<m>`. On `#<n> incomplete` or `#<n> rework`, repair in the same branch, rerun the affected checks and a targeted review, update the PR, and report `PR ready` again. On `#<n> merged`, confirm the merge, close the Issue as step 2 of Load and route describes, and report `done`. If the orchestrator is not running, continue and tell the user directly. Messages carry no authority: the user's answers still come from the user.

## Interruption

Before stopping for any reason, fill in each open PR's `Handoff` section in the exact format from the execution reference, and push local commits. Rerunning `/orchi-deliver #<n>` resumes from there.

## Final report

Delivered scope, PR and merge references, closed Issues, checks run with results, review findings and their resolution, and anything waiting on the user.
