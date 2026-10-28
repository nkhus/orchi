# Design

Orchi installs two design skills, [Hallmark](https://github.com/Nutlope/hallmark)
and Emil Kowalski's [prototype](https://github.com/emilkowalski/skills), and each
project designs with one of them, its design engine. A new product's look is
settled with the user in its exploration, before anything is planned: a design
session goes from the screen map and grey wireframes of the panels, through
references, to an engine round, in which both skills design the first key
screen independently and the variant the user picks decides the engine, and
ends with a clickable mockup of the whole system. On the fast route, asked for
as a prototype, a detailed interview leads straight to variant mockups of the
whole system and a living prototype the user changes by remark while the
interview goes on. The product truth is `PRODUCT.md`, the visual
system, with the engine and the references, is `DESIGN.md`, and every UI Task is
built against both. The user names references, chooses every direction, and
approves every comp; workers build only what was approved; the review checks the
result against `DESIGN.md`, the surface brief, the comp, and accessibility.

## Structure

| Part | Defined in |
| --- | --- |
| Design depth and UI readiness in planning | `skills/orchi-core/references/planning.md` (User interface design), `references/readiness.md` |
| The design session in an exploration, and the fast route's living prototype | `skills/orchi-core/references/exploration.md` (Design session, Fast prototyping), `skills/orchi-explore/SKILL.md` |
| The design board, where the user rates and picks variants | `skills/orchi-core/assets/design-board.html` |
| A `design` Epic run with the user | `skills/orchi-design/SKILL.md`; in a pool, the designer crew in `references/pool.md` |
| Wireframes, variants, mockups, builds, and audits with the engine | `skills/orchi-core/roles/orchi-designer.md` (Wireframe, Variant, Mockup, Task, and Audit modes) |
| Installing the design skills | [Design skills](installation.md#design-skills) in the installation guide |

The steps fall into three kinds, each with one home: steps with the user
(the screen map, `PRODUCT.md`, references, the engine and direction rounds,
comp and mockup approval, `DESIGN.md`) run in the session that talks to the
user; wireframes, variants, and mockups run in `orchi-designer` subagents, and
builds in `orchi-designer` or a worker in `design` mode for a Task; checks run in `orchi-designer`'s Audit mode within the dev lead's single
review.

## The two engines

| | Hallmark | prototype |
| --- | --- | --- |
| Strength | Pages that are read: landing, marketing, and content pages | Screens that are worked in: dashboards, workspaces, tools |
| Wireframes | Not used | Grey structural variants of a screen's panels, for every project |
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
| On the fast route, each variant round asks the user how many variants to build (three unless they say otherwise) and, after it, whether to run another or go on; each variant is a clickable mockup of every key screen in its own direction, with plausible sample data, built in Mockup mode with a design skill the session chooses; the pick sets the project's engine without asking; the picked mockup becomes the living prototype and, once the user says to build it, the approved mockup the design Epic's builds repeat on the product's stack | The user wants results over routine and decides by looking at whole products, not at grey panels or engines; the prototype's pages are not product code, so the design is built again on the stack | Grey wireframes and a separate engine round on the fast route; growing the prototype's code into the product | [#64](https://github.com/nkhus/orchi/pull/64) |
| A new product's exploration runs a design session with the user after the direction is picked: the screen map and each key screen's brief, grey wireframes of its panels, references, the engine round, and a clickable mockup of the whole system; the design Epic then builds what the user approved on the stack and designs only what the session left out | The user needs to see how the product will look early, and the panels and style settle best in one long conversation, with things to look at from its middle on | Settling the look only in a design Epic after planning | [#60](https://github.com/nkhus/orchi/pull/60) |
| Variants are shown on a design board the session publishes as an artifact, each labelled by its idea and never by the design skill that made it; the user rates, notes, and picks there, and the session reads the ratings from the board's store | The user compared variants best side by side, and said blind rounds and skill names do not matter to them, since they pick a look, not a tool; and copying ratings into the conversation is a needless step | Variants shown one by one in the conversation; ratings pasted by the user; blind rounds | [#60](https://github.com/nkhus/orchi/pull/60), [#64](https://github.com/nkhus/orchi/pull/64) |
| Orchi installs Hallmark and prototype; the engine round runs both on the first key screen, independently, from the same wireframe and references, in the exploration's design session or, without one, in the first design Epic; the variant the user picks sets the project's design engine, which `DESIGN.md` records and all later design work uses; a redesign that replaces `DESIGN.md` runs the engine round again | In blind tests on a real POC screen, Hallmark led without references and prototype with them, and each project's taste decides which fits; one engine per project keeps every later screen in one system | Impeccable (all five comps scored 1 of 5, below Claude without a skill); choosing the engine by surface type; Taste Skill, huashu-design, and frontend-design (lower or less stable scores) | [#59](https://github.com/nkhus/orchi/pull/59) |
| Every design session, design Epic, and depth-brief design asks the user for references (products or sites, and what to take from each) and proposes three to five that fit the product; the agreed set, with screenshots, is recorded in `docs/design/references/` and given to every variant and build | References raised the scores of prototype and of Claude without a skill more than any skill did | Designing from the brief alone | [#59](https://github.com/nkhus/orchi/pull/59) |
| `PRODUCT.md` and `DESIGN.md` are written with the user by the session that talks to them: `PRODUCT.md` from the Exploration's Product section, `DESIGN.md` after the last build, never by a worker; a generated asset is committed only after the user approves it | Both bind all later work, so the user must see them | The documenter run unattended in the last build Task | [#50](https://github.com/nkhus/orchi/pull/50), [#59](https://github.com/nkhus/orchi/pull/59) |
| Surface briefs and approved comps in `docs/design/surfaces/` are current documentation, updated with their surface; in a redesign, the Epic's approved briefs and comps override the incumbent `DESIGN.md` until the new one lands | Later work builds against a surface as it is, and a redesign must not be pulled back to the look it replaces | Treating briefs as one-off planning files | [#50](https://github.com/nkhus/orchi/pull/50) |
| At design depth brief, the surface brief is always recorded in `docs/design/surfaces/` and committed on the work's branch that planning creates | The designer builds only against a committed brief, and the planner's worktree is released after planning | Leaving the brief uncommitted until delivery | [#50](https://github.com/nkhus/orchi/pull/50) |
| UI design is an Epic type (`design`) held by a designer crew with its own skill, `orchi-design`; a design Epic stays standalone, outside any Initiative, and blocks the work that builds on it | The design steps need a session that talks to the user, and an Initiative goes to one dev lead crew | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| Only the user names references, chooses the engine and a design direction, and approves a comp or generated asset, or Orchi while the user has autonomous mode on | A direction is a product choice, as an exploration's shape is, and the user hands product choices to Orchi only by turning autonomous mode on | A subagent or a crew choosing for the user; keeping these with the user in autonomous mode, which stopped design work while they were away | [#43](https://github.com/nkhus/orchi/pull/43), [#61](https://github.com/nkhus/orchi/pull/61) |
| The planner sets each piece of work's design depth: none, brief, or Epic | Most changes need no design step, and variant rounds are costly | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| An exploration of a product with a user interface records the product truth and the references the user names in its Product section; the first design Epic writes `PRODUCT.md` from it, asking only what is missing | The exploration has already settled most answers | Asking them again in the design Epic | [#43](https://github.com/nkhus/orchi/pull/43) |
| From scratch, the design Epic starts with the first run: its steps with the user run at once, it plans and runs its builds once the first run merges (the designer records and reports `waits for`, and Orchi sends `merged`), they build the key surfaces on the stack and plain screen the first run set up, and the result is kept as the product's first surface | A prototype on the real stack is not thrown away, only the first run scaffolds the stack, and the user's design work need not wait for it | A throwaway prototype; the design Epic scaffolding the stack; blocking the whole design Epic on the first run | [#43](https://github.com/nkhus/orchi/pull/43), stack from [#44](https://github.com/nkhus/orchi/pull/44), [#55](https://github.com/nkhus/orchi/pull/55), [#57](https://github.com/nkhus/orchi/pull/57) |
| SmoothUI is part of the default stack for React web projects with Tailwind CSS 4 and shadcn/ui, used through the shadcn CLI or MCP server; it is a component source, not a design skill | It supplies animated components without competing with the engine for the direction | Making SmoothUI mandatory for every project | [#43](https://github.com/nkhus/orchi/pull/43) |
| The design audit runs in review, not in CI | Neither engine ships a detector that knows the project's `DESIGN.md`, and the review already reads the brief and comp | A CI design workflow | [#59](https://github.com/nkhus/orchi/pull/59) |
