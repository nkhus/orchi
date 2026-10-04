---
name: orchi
description: "Research development requests, agree scope and approach with the user, then execute tasks, epics, or initiatives through Git branches and GitHub Issues. Use for implementation work, continuing Orchi work from an issue or branch, and project documentation search."
---

# Orchi

Orchi is a development convention. Git stores code and documentation; GitHub
Issues store ownership, hierarchy, dependencies, and status. There is no
controller, state database, approval receipt, or mandatory command facade.

Start by identifying your role (researcher, Epic owner, Initiative integrator, or
reader). Inspect branch and worktree changes, and read the relevant issue and PR.
Resume existing work instead of duplicating it. Read repository instructions
(CLAUDE.md, AGENTS.md, scoped files); they take
precedence over these defaults. Preserve the user's request, decisions, and edits.

## Research, propose, agree

Before choosing a delivery scope, read the relevant code, documentation, and
issues. Scale research to uncertainty and ask focused questions when missing
context would change the result ([clarify](references/planning.md#clarify-with-the-user)). Present findings, sensible approaches with
tradeoffs, and a recommended outcome and scope.

Agree the direction with the user before creating branches, Issues, or changes.
Exploring a problem is not agreement to an agent-chosen scope; silence is not
agreement. Do not re-ask for agreed direction when resuming within it. If new
evidence changes the outcome, approach, or scale, explain it and agree again.

## Scope

| Request | Tracking | Branch and PR |
| --- | --- | --- |
| Question or exploration | None | None |
| Small fix | Standalone Task | `fix/<slug>` from main, PR to main |
| Outcome decomposed into Tasks | Epic → Tasks | One `epic/<tag>-<slug>` branch and PR to main |
| Outcome decomposed into Epics | Initiative → Epics → Tasks | `initiative/<tag>-<slug>` from main; one `epic/<tag>-<epic-tag>-<slug>` PR per Epic into it; final PR to main |

Start titles with the Initiative and Epic tags they belong to, for example
`[PAY][TOKEN] Add token column`; labels carry the type. See
[titles and tags](references/github.md#titles-and-tags). Reuse a branch already recorded in the issue. Create an Initiative branch after
agreement, before its plan or code. Branch from the fetched remote target after
inspecting local changes; never reset another checkout to get a baseline. Do not
create placeholder parents for small work.

## Core rules

- Parallel work happens across independent Epics, each with its own owner, branch,
  and worktree. Tasks within an Epic run in sequence on the Epic branch and share
  its PR.
- Claim before editing and never overwrite another owner's claim. Only ready
  Epics and standalone Tasks are independent entry points.
- Update documentation with the code, in the same branch. Never present planned
  behavior as current behavior.
- Record checks, outcomes, and the candidate commit in the PR. Review each
  standalone Task and each assembled Epic once, then repair demonstrated
  blockers with a targeted follow-up.
- Squash-merge. Close Epics, Initiatives, and standalone Tasks only after
  confirming the merge; close Epic Tasks as the execution reference says. Do not infer merge
  or deployment permission from permission to implement.
- If GitHub is unavailable, say so. Local drafts may continue, but never claim
  that tracking or ownership exists remotely when it does not.

## Stage guidance

Read only the reference needed for the current stage.

| Stage | Reference |
| --- | --- |
| Clarify with the user, design, and write Issues for agents | [Planning](references/planning.md) |
| Check that a Task or Epic is ready to start or delegate | [Readiness](references/readiness.md) |
| Find ready work, claim, execute, hand off, resume | [Execution](references/execution.md) |
| Review, integrate, and close | [Review and delivery](references/review-delivery.md) |
| Update Core documentation or reconcile branches | [Knowledge](references/knowledge.md) |
| Create, relate, or close Issues; PR conventions | [GitHub conventions](references/github.md) |
| Search or read documentation; validate links | [Retrieval](references/retrieval.md) |

## Entry skills and subagents

`orchi-plan` (research → agreed, ready Issues) and `orchi-deliver` (Issue → PR)
are optional explicit entry points: `/orchi-plan` and `/orchi-deliver`. The
rules above apply without them. The main session may delegate to the installed
subagents defined in [roles](roles/README.md): `orchi-scout` retrieves,
`orchi-implementer` executes one ready Task, `orchi-fixer` makes one small,
fully specified change (a simple Task or a confirmed defect repair),
`orchi-designer` executes one ready UI Task or audits a UI diff with the
installed design skills, and `orchi-reviewer` reviews.
Subagents never talk to the user, change Issues, push, or merge; their reports
are claims to verify. Delegation is optional; the readiness checklists are not.

## Tools

Both scripts are read-only and use only Git, `gh`, and the Python standard
library. Run them from the repository root with the installed skill path.

- `python3 .claude/skills/orchi/scripts/status.py` lists open Epics and standalone
  Tasks with their owners, blockers, and readiness.
- `python3 .claude/skills/orchi/scripts/knowledge.py` searches documentation,
  reads exact snapshots, and checks local links.
