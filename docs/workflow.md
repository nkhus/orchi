# Workflow

The core workflow every Orchi session follows: research and agree scope with the
user, track proportional work as a Task, Epic, or Initiative in GitHub Issues,
deliver it on Git branches, review it once, and leave merging and deployment to
the user's authority. A solo session runs it directly; a [pool](pool.md) runs the
same workflow through crews and workers.

## Structure

| Part | Defined in |
| --- | --- |
| Routing, scope, and core rules | `skills/orchi-core/SKILL.md` |
| Exploration of an idea before any scope | `skills/orchi-explore/SKILL.md`, `references/exploration.md` |
| Planning, readiness, and Issue conventions | `skills/orchi-plan/SKILL.md`, `references/planning.md`, `references/readiness.md`, `references/github.md` |
| Delivery, review, and verification | `skills/orchi-deliver/SKILL.md`, `references/execution.md`, `references/review-delivery.md`, `references/testing.md` |
| Subagent roles | `skills/orchi-core/roles/`, rendered to `.claude/agents/` by the installer |
| Readiness of tracked work | `scripts/status.py`, read-only, from GitHub |
| Issue forms | `skills/orchi-core/assets/github/ISSUE_TEMPLATE/`, installed with `--github` |

Paths under `references/`, `roles/`, and `scripts/` are inside
`skills/orchi-core/`. Each detailed rule has one home in a reference, and
`SKILL.md` files link to it instead of repeating it.

## Contracts

- Git branches and GitHub Issues are the only shared state; the bundled scripts
  only read.
- Branches: `fix/<slug>` from main for a standalone Task; `epic/<tag>-<slug>`
  from main for a standalone Epic; `initiative/<tag>-<slug>` from main with one
  `epic/<tag>-<epic-tag>-<slug>` branch per Epic into it; Tasks on their Epic
  branch, and `task/<slug>` for a pool dev lead's parallel Tasks;
  `explore/<slug>` for an exploration's working documents.
- A target repository's own instructions take precedence over Orchi's defaults.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| The branch hierarchy stays: Initiative branch from main, Epic branches from it, Tasks on their Epic branch | Working documents change several times before they settle; a branch per level lets each settle locally and move into the current documentation at its merge | Flat branches from main for every piece of work, which leave nowhere to settle a plan before main | [#45](https://github.com/nkhus/orchi/pull/45) |
| `orchi-reviewer`'s own instructions carry every check the review must make, including `ENGINEERING.md` and gate integrity, exceptions, acceptance evidence, and the documentation map; it reports the exceptions for the PR | Nobody reads the code after the reviewer, and an agent reads its role file, not the whole review reference | Relying on the review reference alone | [#47](https://github.com/nkhus/orchi/pull/47) |
| `orchi-implementer`, the main writer, runs at medium effort | Tools and one review are the only checks on its work, so its first attempt carries more weight | Low effort, which saved tokens on the most consequential step | [#47](https://github.com/nkhus/orchi/pull/47) |
| The core skill is `orchi-core`, hidden from the slash-command menu and loaded by sessions themselves; `/orchi` is the pool entry | Every session reads the core workflow, while the entry holds the authority to build a pool and to merge in auto mode, so it stays explicit-only | `orchi` as the core skill with the entry as `/orchi-pm` | [#43](https://github.com/nkhus/orchi/pull/43) |
| A rule stays in skill text only if it prevents an observed or near-certain costly error and is the cheapest way to do so; new roles aside, skill text does not grow | Every line costs context in every session, and rules nobody needed dilute the ones that matter | Adding a rule for each anticipated mistake | 2026-10-09, kept in [#42](https://github.com/nkhus/orchi/pull/42) |
