# E4 Design track

Status: implemented on the `feat/design-track` branch. Part of the
[single-entry Initiative](README.md); the [architecture](architecture.md) holds
the pool this track runs in. The [planning](../../../skills/orchi-core/references/planning.md#user-interface-design)
and [pool](../../../skills/orchi-core/references/pool.md#designer-crews) references and
`orchi-design` describe the behavior; this page keeps the reasoning.

## Request

The maintainer's request, translated from Russian (2026-10-27):

> Build Impeccable into the pipeline so that it is an organic part of the
> development cycle, along three paths:
>
> 1. From scratch: Orchi starts research, the planner makes an Epic for UI
>    prototyping, then from all of it the planner writes the full development
>    plan, and development starts.
> 2. Changing an existing design: planning, design, development.
> 3. A feature with UI: planning, design, development.

## Outcome

Every project with a user interface designs through Impeccable. The product
truth comes out of research and becomes `PRODUCT.md` at the start of the first
design Epic, the visual system (`DESIGN.md`) comes out of a design Epic, and
every UI Task is built against both. The user chooses
every direction and approves every comp; workers build only what was approved;
the review checks the result with Impeccable's audit, critique, and detector.

## Decisions

| # | Decision | Source |
| --- | --- | --- |
| D19 | The designer is the fourth crew role, with its own skill `orchi-design`. | 2026-10-27 |
| D20 | Only the user chooses a design direction and approves a comp, in every mode, as only the user shapes an exploration. | 2026-10-27 |
| D21 | Impeccable is the only design engine. Taste Skill leaves the pipeline: it chooses a direction alone, keeps no design system, and its rules conflict with Impeccable's. | 2026-10-27, comparison below |
| D22 | SmoothUI is part of the default stack for web projects on React, Tailwind CSS 4, and shadcn/ui, used through the shadcn MCP server. It is a component source, not a design skill. | 2026-10-27 |
| D23 | The Orchi installer installs Impeccable at a pinned version, in project scope, for Claude only, without hooks, with telemetry off. | 2026-10-27 |
| D24 | With `--github`, a workflow runs `impeccable detect` on changed UI files in pull requests. | 2026-10-27 |
| D25 | A greenfield prototype is built on the real stack and kept as the product's first surface. | 2026-10-27 |
| D26 | The planner sets each piece of work's design depth: none, brief, or Epic. | 2026-10-27 |

D21 replaces "Making Taste Skill or SmoothUI mandatory" in the Initiative's
exclusions: Taste Skill is removed, SmoothUI becomes a stack default.

## Impeccable in the pipeline

Impeccable 4.8.0 (2026-10-26) is one skill, `/impeccable <command>`, with
project files and four subagents of its own. Its steps fall into three kinds,
and each kind has one home in the pool:

| Kind | Impeccable | Runs in |
| --- | --- | --- |
| With the user | `init` (`PRODUCT.md`), `shape` (discovery and brief), the direction round (directions on a local decision page), comp approval, approval of generated assets | The crew that talks to the user: researcher, planner, or designer |
| Build | Comp-led build from an approved comp, or code-led build from a direction contract; focused commands (`layout`, `typeset`, `colorize`, `animate`, `adapt`, `clarify`, `harden`, `onboard`, `optimize`); `polish`; the finish reviewer; the documenter (`DESIGN.md`) | A worker in `design` mode (`orchi-designer`) |
| Check | `audit`, `critique`, `detect` | The dev lead's single review, through `orchi-designer` in Audit mode; `detect` also in CI |

Files: `PRODUCT.md`, `DESIGN.md` with its `design.json` sidecar,
`.impeccable/config.json`, surface briefs in `.impeccable/surfaces/`, and
approved comps are committed. `.impeccable/build/`, `.impeccable/review/`, and
`.impeccable/mocks/` are ignored, except approved comps.

Impeccable resists unattended runs: it probes for a user even when told it is
autonomous, and a comp-led build waits for approval of the comp and of generated
assets. So a worker gets only settled input: the approved comp or the direction
contract, `PRODUCT.md`, and `DESIGN.md`. When Impeccable asks a question during
a build, the worker sends it to its crew as `#<task> question`, and a designer
crew passes a design question to the user.

## Design depth

The planner sets the depth during planning and records it in the Epic or Task:

| Depth | When | Design work |
| --- | --- | --- |
| None | Changes within existing components and screens | No design step. The worker builds with `polish`; the review runs `audit` |
| Brief | A new screen or feature inside an established world (`DESIGN.md` exists) | The planner runs `/impeccable shape` with the user; the brief becomes a surface brief, linked from the Epic. No direction round unless the composition stays materially open |
| Epic | A new product, a redesign, or several screens whose composition is open | A `design` Epic held by a designer crew, blocking the delivery Epics that build on it |

A brief that turns out to need a new world or a redesign is raised to a design
Epic, and the planner tells the user why.

## The three paths

### 1. From scratch

1. **Research.** Orchi assigns a researcher crew. When the product has a user
   interface, the exploration's Product section records what Impeccable's
   `init` asks: users, purpose, positioning, platform, stack (SmoothUI for a
   React web project, D22), constraints, and brand commitments. Exploration
   keeps its state in the Issue, so `PRODUCT.md` itself is written in step 3.
2. **Plan.** A planner crew plans from the Exploration:
   - a standalone `design` Epic for the UI prototype of the key surfaces; it
     stays outside any Initiative, so a designer crew can hold it;
   - an Issue labelled `needs-planning` and `Requested by: <Orchi>`, blocked by
     the design Epic: detail the development plan from `PRODUCT.md`,
     `DESIGN.md`, the surface briefs, and the prototype.
3. **Design.** Orchi assigns a designer crew (`orchi-design`) to the design Epic.
   It runs `init` from the Product section, asking only what is missing. For
   each key surface it runs `shape` and the direction round with the user, gets
   the comp approved, and records the direction contract in the surface brief.
   It then plans the builds and continues with `orchi-deliver`: its workers
   scaffold the stack and build the surfaces against the approved comps; the
   finish reviewer gates each build and the last Task writes `DESIGN.md`. One PR
   into main, merged per mode. The prototype stays as the first surface (D25).
4. **Detail the plan.** When the design Epic closes, its blocker is gone and Orchi assigns
   a planner crew to the `needs-planning` Issue. The planner writes the
   development Epics; every UI Task links the `DESIGN.md` sections, surface
   brief, and comp it builds against.
5. **Develop.** Dev lead crews deliver. UI Tasks go to workers in `design` mode;
   the review includes the design audit.

### 2. Changing an existing design

1. **Plan.** A planner crew agrees with the user which surfaces change and what
   must stay, and plans a `design` Epic; a large rollout gets delivery Epics
   blocked by it.
2. **Design.** A designer crew runs `init` when `PRODUCT.md` is missing and
   `document` when `DESIGN.md` is missing, so the incumbent world is recorded as
   evidence. With the user it runs the direction round for the replacement
   world and gets the comp approved. Its workers rebuild one reference surface,
   and the documenter replaces `DESIGN.md`.
3. **Develop.** Dev lead crews carry the new world to the remaining surfaces, one
   Task per surface, each closed with `polish`.

### 3. A feature with UI

1. **Plan.** A planner crew plans the feature and sets the depth. At depth brief
   it runs `shape` with the user and links the surface brief from the Epic; at
   depth Epic the feature follows path 2's design step first.
2. **Develop.** A dev lead crew delivers. UI Tasks go to workers in `design`
   mode; the review includes the design audit.

## Modes

The direction round, comp approval, and asset approval go to the user in both
modes (D20); in auto mode the designer crew also reports
`<id> needs the user` to Orchi, as a researcher does. `init` and `shape` ask
what only the user knows, so in auto mode Orchi answers only what `PRODUCT.md`,
`DESIGN.md`, or the Issues already settle and leaves the rest for the user.
Choices inside an approved direction (spacing, states, copy within the brief)
follow the autonomy level like any other reversible choice.

## Taste Skill and Impeccable compared

Read on 2026-10-27 from both repositories (Taste Skill 2.1.5, Impeccable 4.8.0),
one third-party single-run test, Taste Skill's own tests, and GitHub issues. No
blind comparison of the current versions exists; Taste Skill 2 was rewritten on
2026-10-13.

| | Taste Skill 2.1.5 | Impeccable 4.8.0 |
| --- | --- | --- |
| Direction | A script deals 3 of 20 directions; the agent picks one without the user | An interview, then directions on a decision page; the user picks; optional image comps |
| Kept in the project | A direction file and CSS tokens | `PRODUCT.md`, `DESIGN.md`, surface briefs with direction contracts |
| Later screens | Nothing enforces consistency | The detector flags drift from `DESIGN.md` |
| Checks | Headless Chrome at three widths, self-critique of screenshots | 62 detector rules (CLI, CI), a fresh-context finish reviewer, comp-to-build pixel comparison |
| Unattended | By design | No: direction and comps need a person |

- Marketing pages: in the one third-party test Impeccable was bolder and invented
  no product facts; Taste Skill was cheaper and invented features. Taste Skill's
  own model-judged blind tests scored it below the no-skill baseline in four of
  five rounds.
- App UI and redesign: no comparison exists. Taste Skill's notes call its app
  screens "a well-applied kit"; Impeccable replaces and then enforces
  `DESIGN.md`.
- Combining them conflicts: Taste Skill bans shadows and glass and deals fonts
  that Impeccable treats as defaults to avoid, and both insist on their own
  direction step.

Sources: [Impeccable](https://github.com/pbakaus/impeccable),
[Taste Skill](https://github.com/Leonxlnx/taste-skill),
[third-party test](https://dev.to/skillgild/impeccable-vs-taste-skill-which-claude-design-skill-to-use-tested-3d6i).

## Known Impeccable issues to handle

- `impeccable context` can print about 61K characters, which Claude Code
  truncates ([#1018](https://github.com/pbakaus/impeccable/issues/1018)).
- Several references push small tasks into the full-cost path
  ([#985](https://github.com/pbakaus/impeccable/issues/985)); at depth none,
  workers use only `polish` and the review only `audit`.
- The comp-led build needs a frontier model; smaller models stall at its hero
  gate. Comps need image generation (a host tool or an API key that
  `impeccable context` reports); without it the build is code-led.

## Tasks

In order; T5 and T6 can run in parallel after T4.

| Task | Outcome |
| --- | --- |
| T1 Install Impeccable | The installer installs Impeccable as D23 says, records it in the manifest, adds the ignore rules, and fails before any change when Node is missing; with `--github` it adds the `detect` workflow (D24) and the `design` label. Uninstall leaves Impeccable and says so. The smoke test accepts Impeccable's subagents beside Orchi's six. To verify first: the npm version that matches skill 4.8.0, the pinned install flags, and the scope of `telemetry off`. |
| T2 Designer worker | `orchi-designer` uses Impeccable only: Task mode builds comp-led from an approved comp or code-led from a direction contract, runs focused commands and `polish`, and sends Impeccable's questions to its crew; Audit mode runs `audit`, `critique`, and `detect`. SmoothUI is used through the shadcn MCP server where the project's stack names it. Taste Skill is removed from the role, the roles README, and the references. |
| T3 Planning | Planning and readiness gain design depth; a UI Task's readiness requires links to the `DESIGN.md` sections, surface brief, and comp, and the states, breakpoints, and themes it covers. The Epic and Task forms gain a design field. `orchi-plan` runs `shape` at depth brief and plans a `design` Epic with a blocked `needs-planning` Issue at depth Epic. |
| T4 Designer crew | `orchi-design` runs a `design` Epic: `init` and `document` when missing, `shape`, the direction round, comp and asset approval with the user, builds through its workers, the finish reviewer, `DESIGN.md`, and the PR. The pool reference gains the role, its routing (a `design` Epic goes to a designer crew), its mode rule (D20), and the files it may write itself: `PRODUCT.md`, surface briefs, and approved comps. |
| T5 Research hand-off | An exploration of a product with a user interface fills a Product section with what `init` asks; the first design Epic writes `PRODUCT.md` from it. (Planned as `init` at the end of research; changed because an exploration keeps its state in the Issue and has no branch to commit `PRODUCT.md` on.) |
| T6 Delivery and review | `orchi-deliver` gives UI Tasks to workers in `design` mode, and its single review adds `orchi-designer`'s audit for changes that touch the user interface. |
| T7 Documentation and release | README, installation, testing (a live checklist for the three paths), and the design guide; version 0.19.0. |

One PR from `feat/design-track`, stacked on the pool PR.

## Acceptance

- A fresh install has Impeccable at the pinned version, without hooks, with
  telemetry off, and the ignore rules; uninstall leaves it and reports it.
- Path 1 in a disposable repository: research ends with a Product section; the
  plan has a standalone `design` Epic and a blocked planning Issue; the designer crew gets the
  direction and comp from the user, its workers build the prototype, and
  `DESIGN.md` is written; the detailed plan's UI Tasks link them.
- Path 2: `DESIGN.md` is replaced after the user approves the new direction, and
  the rollout Tasks build against it.
- Path 3: a depth-brief feature gets a surface brief from `shape` and is
  delivered with a design audit in its review.
- In auto mode no direction or comp is chosen without the user.
- Each claim is reported as established, limited, or not established; text
  tests do not establish live behavior.

## Open questions

- Which image generation the maintainer has for comps.
- Whether the `detect` workflow should fail a pull request or only comment.
- Whether Impeccable's own subagents need instructions that keep them from
  asking the user when a worker starts them.
