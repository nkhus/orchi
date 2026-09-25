---
name: orchi
description: "Research development requests, agree scope and approach with the user, then execute tasks, epics, or initiatives through Git branches and GitHub Issues. Use for implementation work, continuing Orchi work from an issue or branch, and project documentation search."
---

# Orchi

Orchi is a development convention. Git stores code and documentation; GitHub
Issues store ownership, hierarchy, dependencies, and delivery status. There is
no operator, local state database, ticket activation, approval receipt, or
mandatory command facade.

At the start, identify your role (researcher, epic owner, initiative integrator, or reader),
inspect branch/worktree changes, and read the relevant issue and PR when present.
Resume existing work rather than creating duplicates. Read repository instructions
(AGENTS.md, CLAUDE.md, `.github/copilot-instructions.md`) and scoped instructions;
they take precedence over the defaults below. Preserve the user's request, decisions, and existing
edits; resolve material ambiguity in conversation without manufacturing gates.

## Research, propose, and agree

Begin a new request with discovery before choosing its delivery scope. Read the
relevant code, documentation, and existing issues; investigate constraints,
dependencies, unknowns, and what is already implemented. Ask focused questions
when missing user context affects the result. Scale research to uncertainty: a
small fix may need only a short inspection, while a large request needs enough
investigation to identify meaningful Epic boundaries.

Present the findings, plausible approaches and tradeoffs, and a recommended
outcome and delivery scope: Task, Epic, or Initiative. Do not force three options
when only one is sensible. Explain why the scope fits the discovered work and
identify unresolved inputs that could change it.

Agree the direction with the user before creating delivery branches, Issues,
or implementation changes. Until then, keep findings and proposed decomposition
in the conversation or an explicitly requested research draft. Initial research
needs no tracking ceremony. The request to explore a problem is not agreement
to an agent-selected implementation scope; silence is not agreement.

Once the user agrees the outcome and approach, follow the selected route below.
Do not ask again for an already agreed direction when resuming or refining work
within that scope. If discovery during execution materially changes the outcome,
approach, or scale (for example, a Task becomes an Initiative), explain the new
evidence and agree the changed direction before starting the expanded work.
This is a conversation, with no controller, receipt, or approval command.

## Execute the agreed scope

| Request | Tracking | Branch and PR |
| --- | --- | --- |
| Read-only question or exploration | None | None |
| Small fix with one reviewable result | Standalone Task | Short branch from main, PR to main |
| Outcome decomposed into Tasks | Epic → Tasks | One Epic branch from main, one PR to main |
| Outcome decomposed into Epics | Initiative → Epics → Tasks | Initiative branch from main; one branch and PR per Epic targeting the Initiative; final Initiative PR to main |

Use `initiative/<slug>`, `epic/<slug>`, and `fix/<slug>` as branch conventions;
reuse an established branch recorded in the issue. The initiative branch is the
integration base for that initiative, not a change to GitHub's default branch.
Create it after direction agreement, before writing the delivery plan and
initiative documentation or implementation. Carry the initial research findings
into that documentation; research itself does not require an initiative branch.
Start from the fetched remote target after inspecting local changes and divergence; never
reset another checkout to establish a baseline.

For GitHub operations, follow the repository's issue rules when it has them;
otherwise use the [GitHub conventions](references/github.md).
Use the three type labels `Initiative`, `Epic`, and `Task`. Do not create
placeholder parents for small work. GitHub unavailability should be reported;
local drafts can proceed within authorization, but never claim tracking was
created or ownership acquired remotely when it was not.

## Stage guidance

Read only the reference needed for the current stage. References share this
workflow and do not introduce separate state or approvals.

| Stage | Reference |
| --- | --- |
| Search or read documentation; validate links | [Retrieval](references/retrieval.md) |
| Design an Initiative/Epic and derive Tasks | [Planning](references/planning.md) |
| Execute, resume, or hand off | [Execution](references/execution.md) |
| Update requirements/Core or reconcile documentation | [Knowledge](references/knowledge.md) |
| Create, relate, or close GitHub Issues and PRs | [GitHub conventions](references/github.md) |
| Review and integrate a completed result | [Review and delivery](references/review-delivery.md) |

## Plan proportionately

A fix needs an outcome and verification in its Task, not a design package.
For an Epic, record scope, approach, acceptance, and relevant documentation in
its issue or a linked document, then create its Tasks. Do not require a separate
planning task for each field.

For an Initiative, capture the original request and agreed outcome, exclusions,
requirements, major decisions, and Epic dependency outline in
`docs/initiatives/<slug>/README.md` on its branch. Link existing requirements and
stable IDs instead of duplicating them. Keep future Epics at outcome level;
detail Tasks when an Epic is ready to start. Do not duplicate issue status or
child lists as a second checklist in the document. Existing project document
locations may be retained if they already serve this purpose.

## Claim and execute

An open issue without `in-progress` is unclaimed. An open issue with
`in-progress` is owned work. Closed issues are completed or explicitly cancelled;
use the close reason to distinguish them. Use assignees and an issue-body work
reference (assistant task/session URL or identifier, branch, and PR) for the
owner. Assistants sharing a GitHub login must use distinct work references.

Before taking an Epic, check its native blockers and current ownership. It is
ready only when unclaimed and all required predecessor results have merged into
its intended integration branch. A cancelled predecessor does not satisfy a
dependency. Claim by updating the issue, then re-read ownership before editing.
GitHub labels are not atomic locks: if claims race or another active owner is
visible, resolve ownership before either continues; do not overwrite a claim.
There is no scheduler or central unlock operation. Relinquish ownership explicitly
on handoff, leaving branch/PR and remaining work available to the next owner.

Parallel execution is across independent Epics, each with its own owner, branch,
and worktree. Do not dispatch parallel implementation Tasks within one Epic.
The owner marks the current Task `in-progress`, implements and verifies it in
the Epic branch, and records its result in the shared Epic PR. Tasks have no
separate branch or PR. Close a Task and remove `in-progress` once its result is
implemented and verified in the Epic branch, recording the branch/commit evidence.
For a standalone fix, close its Task only after its PR merges to main.
Epic Task completion is within the Epic, not integration into main. Reopen a Task if
its result is invalidated before Epic integration.

Mark an Initiative `in-progress` while its planning or Epics are active. This
aggregate marker does not prevent independent Epic claims. A Task under an Epic
is never independently claimable outside its owner; only standalone Tasks and
ready Epics are independent work entry points.

Use native Epic dependencies for real ordering constraints. If parallel Epics
share changing contracts, establish the dependency before concurrent edits.
Do not infer blocking from the parent relationship or require operator isolation
configuration. Git worktrees provide workspace separation, not security isolation.

## Verify and integrate

Run project checks appropriate to the changed surfaces, as documented by the
repository's instructions, README, or CI configuration. Record commands, outcomes, and
candidate commit in the PR. Review the assembled Epic once; use an independent
reviewer when available. If unavailable, disclose that limitation rather than
claiming independent review. Repair demonstrated blockers and recheck affected
surfaces; use a targeted follow-up instead of repeated broad review campaigns.
Do not turn advisory observations into mandatory work.

Squash each Epic PR into its recorded target branch. Check current target and
resolve conflicts before merge, then rerun checks affected by integration.
Confirm its Tasks are completed, then close the Epic only after the merge is
confirmed and remove `in-progress`. A closed issue alone is not proof of merged implementation.
For non-default targets, do not rely on closing keywords to close issues.
After a predecessor merges, branch dependent Epics from the updated integration
branch. Serialize merges into a shared target and recheck compatibility when
another Epic has landed since validation.

Before the final Initiative PR to main, reconcile with current main, including
code and Core documentation, and run the full applicable project suite on that
integrated candidate. Squash into main, confirm the merge, and close the
Initiative. A standalone Epic follows the same flow directly to main. Small
fixes use a proportional review and checks without an Initiative/Epic ceremony.
Follow the user's existing publication authority; do not infer merge or deployment
permission solely from permission to implement.

## Documentation and retrieval

Update Core files at their normal paths alongside code in the Epic branch.
When an Epic merges, those changes become the Initiative branch's working Core;
they do not become main's Core until final Initiative integration. Keep planning
and unresolved decisions in initiative documentation and label proposed behavior
clearly; never present unimplemented plans as current behavior.

Read current released/integrated facts from main, initiative working facts from
its integration branch, and an Epic candidate from its branch. State the branch
or commit when the distinction matters. Use Orchi [search and exact reads](references/retrieval.md) for documentation;
use `rg` for code discovery. No database or generated knowledge projection is
required. Reconcile overlapping edits semantically,
including main changes made during the initiative; never bulk-copy the initiative
Core over main. Git records history; documents need not mirror process states.
