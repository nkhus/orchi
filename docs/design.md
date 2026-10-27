# Design

Orchi installs two design skills, [Hallmark](https://github.com/Nutlope/hallmark)
and Emil Kowalski's [prototype](https://github.com/emilkowalski/skills), and each
project designs with one of them, its design engine. The user picks the engine
in the project's first design Epic: both skills design the first surface
independently from the same brief and references, and the variant the user
chooses decides the engine. The product truth is `PRODUCT.md`, the visual
system, with the engine and the references, is `DESIGN.md`, and every UI Task is
built against both. The user names references, chooses every direction, and
approves every comp; workers build only what was approved; the review checks the
result against `DESIGN.md`, the surface brief, the comp, and accessibility.

## Structure

| Part | Defined in |
| --- | --- |
| Design depth and UI readiness in planning | `skills/orchi-core/references/planning.md` (User interface design), `references/readiness.md` |
| A `design` Epic run with the user | `skills/orchi-design/SKILL.md`; in a pool, the designer crew in `references/pool.md` |
| Variants, builds, and audits with the engine | `skills/orchi-core/roles/orchi-designer.md` (Variant, Task, and Audit modes) |
| Installing the design skills | [Design skills](installation.md#design-skills) in the installation guide |

The steps fall into three kinds, each with one home: steps with the user
(`PRODUCT.md`, references, the engine and direction rounds, comp approval,
`DESIGN.md`) run in the session that talks to the user; variants and builds run
in `orchi-designer` in Variant mode, or in a worker in `design` mode for a
Task; checks run in `orchi-designer`'s Audit mode within the dev lead's single
review.

## The two engines

| | Hallmark | prototype |
| --- | --- | --- |
| Strength | Pages that are read: landing, marketing, and content pages | Screens that are worked in: dashboards, workspaces, tools |
| Variants | One per run; three runs on the three themes it deals for the brief | Three divergent variants in one run, behind a picker |
| With references | Holds to its own themes | Adapts to them |
| Locked system | Reads `DESIGN.md` at the root as a locked system | Reads the project's tokens and components |
| Checks | Its `audit` and `sloplint` | The designer's audit |

## Limits

- prototype is marked for the user's invocation only
  (`disable-model-invocation`), so a session cannot start it with the Skill
  tool; the designer reads `.claude/skills/prototype/SKILL.md` and follows it.
- Both skills ask the user before they build. A designer in Variant or Task mode
  gives them the brief and references as settled input and tells them to go
  ahead without questions.
- Hallmark's floor forbids middle-dot meta strings; a project format that needs
  them (a source label, say) wins, and the designer records the conflict.
- Variants are self-contained HTML until the first run has set up the stack;
  builds then move the approved comp onto the stack.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Orchi installs Hallmark and prototype, and a project's first design Epic runs both on its first surface, independently, from the same brief and references; the variant the user picks sets the project's design engine, which `DESIGN.md` records and all later design work uses; a redesign that replaces `DESIGN.md` runs the engine round again | In blind tests on a real POC screen, Hallmark led without references and prototype with them, and each project's taste decides which fits; one engine per project keeps every later screen in one system | Impeccable (all five comps scored 1 of 5, below Claude without a skill); choosing the engine by surface type; Taste Skill, huashu-design, and frontend-design (lower or less stable scores) | [#59](https://github.com/nkhus/orchi/pull/59) |
| Every design Epic, and every depth-brief design, starts by asking the user for references (products or sites, and what to take from each) and proposing three to five that fit the product; the agreed set, with screenshots, is recorded in `docs/design/references/` and given to every variant and build | References raised the scores of prototype and of Claude without a skill more than any skill did | Designing from the brief alone | [#59](https://github.com/nkhus/orchi/pull/59) |
| `PRODUCT.md` and `DESIGN.md` are written with the user by the session that talks to them: `PRODUCT.md` from the Exploration's Product section, `DESIGN.md` after the last build, never by a worker; a generated asset is committed only after the user approves it | Both bind all later work, so the user must see them | The documenter run unattended in the last build Task | [#50](https://github.com/nkhus/orchi/pull/50), [#59](https://github.com/nkhus/orchi/pull/59) |
| Surface briefs and approved comps in `docs/design/surfaces/` are current documentation, updated with their surface; in a redesign, the Epic's approved briefs and comps override the incumbent `DESIGN.md` until the new one lands | Later work builds against a surface as it is, and a redesign must not be pulled back to the look it replaces | Treating briefs as one-off planning files | [#50](https://github.com/nkhus/orchi/pull/50) |
| At design depth brief, the surface brief is always recorded in `docs/design/surfaces/` and committed on the work's branch that planning creates | The designer builds only against a committed brief, and the planner's worktree is released after planning | Leaving the brief uncommitted until delivery | [#50](https://github.com/nkhus/orchi/pull/50) |
| UI design is an Epic type (`design`) held by a designer crew with its own skill, `orchi-design`; a design Epic stays standalone, outside any Initiative, and blocks the work that builds on it | The design steps need a session that talks to the user, and an Initiative goes to one dev lead crew | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| Only the user names references, chooses the engine and a design direction, and approves a comp or generated asset, in every mode and at every autonomy level | A direction is a product choice, as an exploration's shape is | An autonomy level choosing for the user | [#43](https://github.com/nkhus/orchi/pull/43) |
| The planner sets each piece of work's design depth: none, brief, or Epic | Most changes need no design step, and variant rounds are costly | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| An exploration of a product with a user interface records the product truth and the references the user names in its Product section; the first design Epic writes `PRODUCT.md` from it, asking only what is missing | The exploration has already settled most answers | Asking them again in the design Epic | [#43](https://github.com/nkhus/orchi/pull/43) |
| From scratch, the design Epic starts with the first run: its steps with the user run at once, it plans and runs its builds once the first run merges (the designer records and reports `waits for`, and Orchi sends `merged`), they build the key surfaces on the stack and plain screen the first run set up, and the result is kept as the product's first surface | A prototype on the real stack is not thrown away, only the first run scaffolds the stack, and the user's design work need not wait for it | A throwaway prototype; the design Epic scaffolding the stack; blocking the whole design Epic on the first run | [#43](https://github.com/nkhus/orchi/pull/43), stack from [#44](https://github.com/nkhus/orchi/pull/44), [#55](https://github.com/nkhus/orchi/pull/55), [#57](https://github.com/nkhus/orchi/pull/57) |
| SmoothUI is part of the default stack for React web projects with Tailwind CSS 4 and shadcn/ui, used through the shadcn CLI or MCP server; it is a component source, not a design skill | It supplies animated components without competing with the engine for the direction | Making SmoothUI mandatory for every project | [#43](https://github.com/nkhus/orchi/pull/43) |
| The design audit runs in review, not in CI | Neither engine ships a detector that knows the project's `DESIGN.md`, and the review already reads the brief and comp | A CI design workflow | [#59](https://github.com/nkhus/orchi/pull/59) |
