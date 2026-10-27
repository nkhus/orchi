# Design

Every project with a user interface designs through
[Impeccable](https://impeccable.style/), which Orchi installs with itself. The
product truth becomes `PRODUCT.md`, the visual system becomes `DESIGN.md`, and
every UI Task is built against both. The user chooses every direction and
approves every comp; workers build only what was approved; the review checks the
result with Impeccable's audit, critique, and detector.

## Structure

| Part | Defined in |
| --- | --- |
| Design depth and UI readiness in planning | `skills/orchi-core/references/planning.md` (User interface design), `references/readiness.md` |
| A `design` Epic run with the user | `skills/orchi-design/SKILL.md`; in a pool, the designer crew in `references/pool.md` |
| Building and auditing with Impeccable | `skills/orchi-core/roles/orchi-designer.md` (Task and Audit modes) |
| The detector on pull requests | `skills/orchi-core/assets/github/workflows/orchi-design.yml`, installed with `--github` |
| Installing Impeccable | [Impeccable](installation.md#impeccable) in the installation guide |

Impeccable's steps fall into three kinds, each with one home: steps with the
user (`init`, `shape`, the direction round, comp and asset approval) run in the
session that talks to the user; builds (comp-led or code-led, the focused
commands, `polish`, the documenter) run in a worker in `design` mode; checks
(`audit`, `critique`, `detect`) run in the dev lead's single review and, for
`detect`, in CI.

## Limits

- `impeccable context` can print about 61K characters, which Claude Code
  truncates ([pbakaus/impeccable#1018](https://github.com/pbakaus/impeccable/issues/1018)).
- Several Impeccable references push small tasks into the full-cost path
  ([pbakaus/impeccable#985](https://github.com/pbakaus/impeccable/issues/985)),
  so at design depth none the worker uses only `polish` and the review only
  `audit`.
- A comp-led build needs a frontier model, and comps need image generation (a
  host tool or an API key that `impeccable context` reports); without it the
  build is code-led.
- Impeccable probes for a user even when told it runs unattended, so a worker
  gets only settled input and sends Impeccable's questions to its crew.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Impeccable is the only design engine | It interviews the user, keeps `PRODUCT.md`, `DESIGN.md`, and surface briefs in the project, and its detector flags drift from `DESIGN.md` | Taste Skill, which picks a direction without the user, keeps no design system, scored below the no-skill baseline in its own blind tests, and conflicts with Impeccable's rules when combined | [#43](https://github.com/nkhus/orchi/pull/43) |
| UI design is an Epic type (`design`) held by a designer crew with its own skill, `orchi-design`; a design Epic stays standalone, outside any Initiative, and blocks the work that builds on it | The design steps need a session that talks to the user, and an Initiative goes to one dev lead crew | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| Only the user chooses a design direction and approves a comp or generated asset, in every mode and at every autonomy level | A direction is a product choice, as an exploration's shape is | An autonomy level choosing for the user | [#43](https://github.com/nkhus/orchi/pull/43) |
| The planner sets each piece of work's design depth: none, brief, or Epic | Most changes need no design step, and the full Impeccable flow is costly | None recorded | [#43](https://github.com/nkhus/orchi/pull/43) |
| An exploration of a product with a user interface records what `init` asks in its Product section; the first design Epic writes `PRODUCT.md` from it with `init`, asking only what is missing | `init` runs with the user in the designer's session, and the exploration has already settled most answers | Running `init` at the end of research | [#43](https://github.com/nkhus/orchi/pull/43) |
| From scratch, the design Epic comes after the foundation Epic, builds the key surfaces on the stack it set up, and the result is kept as the product's first surface | A prototype on the real stack is not thrown away, and only the foundation Epic scaffolds the stack | A throwaway prototype; the design Epic scaffolding the stack | [#43](https://github.com/nkhus/orchi/pull/43), stack from [#44](https://github.com/nkhus/orchi/pull/44) |
| SmoothUI is part of the default stack for React web projects with Tailwind CSS 4 and shadcn/ui, used through the shadcn CLI or MCP server; it is a component source, not a design skill | It supplies animated components without competing with Impeccable for the direction | Making SmoothUI mandatory for every project | [#43](https://github.com/nkhus/orchi/pull/43) |
| With `--github`, a workflow runs `impeccable detect` on the UI files a pull request changes | Drift from `DESIGN.md` is caught on every change, without hooks in every session | Impeccable's hooks after every edit | [#43](https://github.com/nkhus/orchi/pull/43) |
