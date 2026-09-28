---
name: orchi-plan
description: Turn a user request into agreed, tracked, delivery-ready Orchi work (standalone Task, Epic, or Initiative). Ends with the Issue number to pass to orchi-deliver.
argument-hint: <request in plain words>
disable-model-invocation: true
---

# Orchi intake: request → ready Issues

Arguments: $ARGUMENTS

In Codex, take the arguments from the user's message after `$orchi-plan`.

You are the main session: planner and orchestrator. Follow `AGENTS.md`, the
[Orchi skill](../orchi/SKILL.md), its [readiness checklists](../orchi/references/readiness.md)
and [GitHub conventions](../orchi/references/github.md), and the repository's own
issue rules, which take precedence. This skill only fixes the order of steps. It
does not replace those rules.

## 1. Research (no tracking yet)

- Inspect the branch and worktree. Search open and closed Issues and PRs for
  existing or overlapping work. If this continues tracked work, stop and propose
  `/orchi-deliver #<n>` (Claude Code) or `$orchi-deliver #<n>` (Codex) instead.
- Send `orchi-scout` agents for independent retrieval questions (in parallel
  when independent). Read the key files they point to yourself. A scout "not
  found" is not proof of absence.
- Keep research proportional. Ask focused questions only where the answer would
  change the outcome or scope.

## 2. Propose scope

Present the findings, approaches with tradeoffs, and a recommended scope:

| Scope | Choose when |
| --- | --- |
| Standalone Task | One reviewable result, no design decision, one small PR |
| Epic | One outcome that needs several Tasks or a design; one PR |
| Initiative | Several independently verifiable outcomes, needs more than one PR, or Epics could run in parallel |

Do not create branches, Issues, or documents until the user agrees. Silence is
not agreement.

## 3. Create tracking (after agreement)

Follow the Orchi [planning](../orchi/references/planning.md)
and [GitHub](../orchi/references/github.md) references for
titles, tags, labels, branches, and native relationships.

- **Task:** one Issue, following the `orchi-task.yml` template when the
  repository has it.
- **Epic:** the Epic (`orchi-epic.yml` when present), then its Tasks in execution
  order as native sub-issues.
- **Initiative:** create the Initiative Issue (tag, outcome, integration branch,
  completion criteria, requirement-to-Epic coverage). Create the Initiative branch
  and write the plan at `docs/initiatives/<tag>-<slug>/README.md` on it. Create
  every Epic as a native sub-issue with meaningful scenarios, boundaries,
  inputs/outputs, likely surfaces, acceptance, risks, and open questions. A field
  that depends on a predecessor's result may say `Deferred until #<n>: <reason>`.
  Add native blocked-by relationships. Split into Tasks only the Epics that are
  ready to deliver now. The rest are split during delivery.

Only the Initiative branch is created during intake. Epic and fix branches are
named in their Issues and created at delivery.

The Issue is the specification for owners who never see this conversation.
Put every agreed decision, source, and constraint into it; do not leave it in
chat.

## 4. Readiness gate

Check every created Task against the Task readiness checklist. Check every Epic
against items 1–8 of the Epic readiness checklist (deferrals allowed as that
section defines), and every Epic ready for delivery against all items. Apply the
repository's own stricter checklist too, if it defines one. Fix failures in the
Issues. Read back labels, parents, and blockers from GitHub.

## 5. Hand off

Report the created Issue URLs, which Epics are ready and which are deferred, and
end with exactly one line:

```
Deliver with: /orchi-deliver #<n>
```

(In Codex the same line reads `Deliver with: $orchi-deliver #<n>`.)

For an Initiative, suggest `--merge-epics` if the user wants reviewed Epic PRs
merged into the Initiative branch without asking each time.
