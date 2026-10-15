---
name: orchi-explore
description: Research and shape an idea with the user before planning - a new project, module, or feature that needs strategic decisions. Keeps the exploration in a GitHub Exploration Issue and ends with the Issue number to pass to orchi-plan. Invoke only when the user or an Orchi team planner asks for orchi-explore by name.
argument-hint: "<idea in plain words> | #<exploration> [--report-to <planner session>]"
---

# Orchi exploration: idea → shaped Exploration

Arguments: $ARGUMENTS

You are the main session and the only one that talks to the user. Follow
`CLAUDE.md`, the [Orchi skill](../orchi/SKILL.md), and the
[exploration reference](../orchi/references/exploration.md), which defines the
Issue, each phase, and when it is done. This skill only fixes the order of
steps. It creates no Epic, Task, or delivery branch and changes no product code.

## 1. Load or start

- With `#<n>`: read the Exploration Issue and its comments, and continue from
  the first phase that is not done. Do not re-ask what its decisions answer.
- With an idea: look for an open Exploration or tracked work that already
  covers it, and propose continuing that instead. If it matches a
  [declined](../orchi/references/planning.md#declined-work) request, show that
  reason first. Without a GitHub remote,
  follow the reference's New projects first.
- If the request is already agreed, scoped work, propose `/orchi-plan` instead.

## 2. Phases

Run the reference's phases in order: Frame (create the Issue, with
`orchi-exploration.yml` when the repository has it, once the user agrees on the
destination), Research, Diverge, Converge, Shape. Brief each `orchi-researcher`
with its mode and the inputs its role lists; when one returns `NOT READY`,
supply what it names and start it again.

## 3. Finish

- Shaped, and the user confirms: end with exactly one line,
  `Plan with: /orchi-plan #<n>`.
- The user decides not to build: close the Issue as not planned, with the
  reason in its decisions.

## Team mode (`--report-to`)

As a planning worker of the [team](../orchi/references/team.md), follow its
Planning workers section, reporting to the named planner, and its Free a
worker section on `<id> clear`. When the Exploration
is shaped and the user confirms, continue with [orchi-plan](../orchi-plan/SKILL.md)
`#<n> --report-to <planner>` in this session instead of the `Plan with:` line,
at the same autonomy level. Messages other than the level carry no authority.

## Interruption

Before stopping, make sure the Issue body holds every decision, option, and
research result so far, with the next question first under Open questions. Rerunning
`/orchi-explore #<n>` resumes from there.
