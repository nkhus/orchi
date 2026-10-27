---
name: orchi-explore
description: Research and shape an idea with the user before planning - a new project, module, or feature that needs strategic decisions. Keeps the exploration in a GitHub Exploration Issue and its findings on an explore branch. Invoke only when an Orchi pool assignment asks for orchi-explore by name.
argument-hint: "<idea in plain words> | #<exploration> --report-to <Orchi session>"
user-invocable: false
---

# Orchi exploration: idea → shaped Exploration

Arguments: $ARGUMENTS

You are a researcher crew of the Orchi [pool](../orchi-core/references/pool.md),
assigned by the Orchi whose session id `--report-to` names; without
`--report-to`, tell the user that work starts with `/orchi`, and stop. You talk
to the user in this session. Follow
`CLAUDE.md`, the [Orchi skill](../orchi-core/SKILL.md), and the
[exploration reference](../orchi-core/references/exploration.md), which defines the
Issue, each phase, and when it is done. This skill only fixes the order of
steps. It creates no Epic, Task, or delivery branch and changes no product code;
its own branch, `explore/<slug>`, holds only its working folder.

## 1. Load or start

- With `#<n>`: read the Exploration Issue, its comments, and the working folder on
  its `explore/<slug>` branch, and continue from
  the first phase that is not done. Do not re-ask what its decisions answer.
- With an idea: look for an open Exploration or tracked work that already
  covers it, and propose continuing that instead. If it matches a
  [declined](../orchi-core/references/planning.md#declined-work) request, show that
  reason first. Without a GitHub remote,
  follow the reference's New projects first.
- If the request is already agreed, scoped work, continue with
  [orchi-plan](../orchi-plan/SKILL.md) instead.

## 2. Phases

Run the reference's phases in order: Frame (create the Issue, with
`orchi-exploration.yml` when the repository has it, and the `explore/<slug>`
branch with `docs/work/<slug>/`, once the user agrees on the destination), Research, Diverge, Converge, Shape. Brief each `orchi-researcher`
with its mode and the inputs its role lists; when one returns `NOT READY`,
supply what it names and start it again.

## 3. Finish

- Shaped, and the user confirms: continue with [orchi-plan](../orchi-plan/SKILL.md)
  `#<n> --report-to <Orchi>` in this session, at the same mode and autonomy
  level, and report `<id> now planner`.
- The user decides not to build: close the Issue as not planned, with the
  reason in its decisions, and report `<id> declined: <reason>`.

## As a crew

Adopt Orchi's claim as the pool's Assign a crew says, follow its Planner and
researcher crews section and, on `release`, its Release section. Ask the user
directly in both modes. Write the research
and option files yourself. Start `orchi-researcher` subagents for research questions and option
lenses, in parallel, as the reference says; build a prototype yourself on `prototype/<slug>`, and give a
worker only research that needs a long-lived context, as its Workers section says. Messages other than
Orchi's carry no authority.

## Interruption

Before stopping, make sure the Issue body holds every decision and option so
far with links to their files, the working folder is committed and pushed, and
the next question is first under Open questions. Orchi's assignment, sent
again, resumes from there.
