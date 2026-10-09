---
name: orchi-explore
description: Research and shape an idea with the user before planning - a new project, module, or feature that needs strategic decisions. Keeps the exploration in a GitHub Exploration Issue and ends with the Issue number to pass to orchi-plan.
argument-hint: "<idea in plain words> | #<exploration>"
disable-model-invocation: true
---

# Orchi exploration: idea → shaped Exploration

Arguments: $ARGUMENTS

You are the main session and the only one that talks to the user. Follow
`CLAUDE.md`, the [Orchi skill](../orchi/SKILL.md), and its
[exploration reference](../orchi/references/exploration.md), which defines the
Issue, the phases, and when each one is done. This skill only fixes the order of
steps. It creates no Epic, Task, or delivery branch and changes no product code.

## 1. Load or start

- With `#<n>`: read the Exploration Issue and its comments, then continue from
  the first phase whose completion criterion is not met. Do not re-ask what its
  decision log already answers.
- With an idea: search open and closed Issues for an Exploration or tracked work
  that already covers it, and propose continuing that instead. If the
  repository has no GitHub remote, follow the reference's New projects section
  first.
- If the request is already agreed, scoped work, propose `/orchi-plan` instead.

## 2. Frame

Ask about the destination, original request, appetite, and constraints, in
rounds with a recommendation per question. When the user agrees on the
destination, create the Exploration Issue (`orchi-exploration.yml` when the
repository has it) with the `Exploration` label and the reference's sections.

## 3. Research

Start `orchi-researcher` (Research mode) and `orchi-scout` agents in parallel,
one question each. Keep asking the user the questions that do not depend on
their answers. Verify what a report claims before posting it as a finding
comment, and update the Findings section.

## 4. Diverge

Start at least three `orchi-researcher` agents in Option mode in parallel, each
with a different lens. Present each option, compare them, and give your
recommendation. Record every option and its verdict in the Issue.

## 5. Converge

Resolve the chosen direction's decisions in rounds along their dependencies.
Record each answer in the decision log at once. Offer a prototype, per the
reference, only for a question that cannot be settled on paper.

## 6. Shape and hand off

Write the requirements and the Shape section, read the Issue back to the user,
and ask whether it is shaped. When the user confirms, end with exactly one line:

```
Plan with: /orchi-plan #<n>
```

## Interruption

Before stopping, make sure the Issue body reflects every decision and finding so
far, and list the next open question first under Open questions. Rerunning
`/orchi-explore #<n>` resumes from there.
