# [STD] Project standards from the start

Status: proposed plan for agreement. Nothing here describes current behavior.
It builds on the [design track](../entry-single-entry/design-track.md) and
follows the same pattern: decisions in a committed document, enforced by tools.

## Request

The maintainer's request, translated from Russian (2026-10-27):

> We should have a skill that defines all the best practices for a project, to
> enforce its quality from the beginning. It sets the language choice and the
> guardrails under it. Are there good examples we can reuse?

## Outcome

Every Orchi project has an `ENGINEERING.md` that records its stack and the
rules it follows, and every rule a tool can check is enforced by a tool: a
formatter, linter, type checker, tests, boundary and security checks, run in CI
as required checks. A new project gets them before its first feature; an
existing project gets an audit and Issues for what is missing. Planning, writers,
and the review read `ENGINEERING.md`, so the tenth Task follows the same rules as
the first.

## Prior work

Surveyed on 2026-10-27 from primary sources. No project both decides the stack
and turns the decision into enforced checks; Orchi borrows ideas and depends on
none of them.

| Source | What Orchi borrows | What it leaves |
| --- | --- | --- |
| [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) `bmad-project-context`, `bmad-architecture` | A rule a tool can check becomes the tool's configuration or a CI step, not a sentence; the stack table with pinned versions; sorting existing instructions into retain, rewrite, relocate, automate, or delete | Its `_bmad/` state and `uv`-run scripts |
| [GitHub Spec Kit](https://github.com/github/spec-kit) `/speckit.constitution` | Declarative MUST and SHOULD rules with reasons; plans checked against them | Its `.specify/` state, versioning, and the rule that the constitution overrides everything (in Orchi the repository's own instructions come first) |
| [Kiro steering, cc-sdd](https://github.com/gotalab/cc-sdd) | Separate documents for product, technology, and structure | Its `.kiro/` state |
| [Impeccable](https://github.com/pbakaus/impeccable) | `PRODUCT.md` and `DESIGN.md` beside a deterministic checker | — |
| [Trail of Bits skills](https://github.com/trailofbits/skills) `modern-python` | Recommended as an optional install for Python projects | Its text: CC-BY-SA-4.0 is share-alike, so it is not copied |
| [Anthropic plugins](https://github.com/anthropics/claude-plugins-official) `security-guidance`, `hookify` | Recommended as optional installs | — |
| import-linter, dependency-cruiser, OpenSSF Scorecard | Proposed as project checks for module boundaries and repository hygiene | — |

## Proposed decisions

Each needs the maintainer's confirmation (see [Decisions needed](#decisions-needed)).

| # | Proposal |
| --- | --- |
| P1 | A new entry skill, `orchi-standards`: set the standards of a new project, or audit an existing one. |
| P2 | The decisions live in `ENGINEERING.md` at the repository root, beside `PRODUCT.md` and `DESIGN.md`. The managed `CLAUDE.md` section tells every session to follow it. |
| P3 | The language and stack are chosen in the exploration, as options with tradeoffs; `orchi-standards` records them. |
| P4 | In the pool, a planner crew runs `orchi-standards`: it is planning with the user, and its output is `ENGINEERING.md` and a foundation Epic. A dev lead crew delivers that Epic. No new crew role. |
| P5 | From scratch, the foundation Epic comes first and the design Epic is blocked by it; the stack scaffold moves from the design Epic to the foundation Epic. |
| P6 | The stack and which checks block a merge are the user's decisions at every autonomy level; tool choices inside an agreed stack follow the autonomy level. |
| P7 | An audit of an existing project changes nothing by itself: it reports the gaps and files Issues for the ones the user picks. |
| P8 | A standard-library script, `standards.py`, checks that every check `ENGINEERING.md` declares exists in the CI workflows and that its configuration file is committed. |
| P9 | Recommended defaults per ecosystem live in a reference with sources; Orchi copies no third-party rule text. |
| P10 | Orchi proposes the branch protection command; the user runs it or approves it. |

## How it works

### New project

1. **Exploration** compares stack options with the user (language, framework,
   package manager, hosting constraints) and records the choice in the Product
   section with its reason.
2. **`orchi-standards`** reads the Exploration, proposes the checks for the
   project's kind (library, service, web app, CLI, mobile) from the standards
   reference, agrees them with the user, writes `ENGINEERING.md`, and plans the
   foundation Epic.
3. **The foundation Epic** scaffolds the stack and commits the tool
   configurations, the CI workflow with each check as its own job, the
   dependency update configuration, and the lockfile. Its acceptance is a CI run
   in which every check passes on an empty project and fails on a planted
   violation.
4. **The user** makes the checks required in branch protection (P10).
5. **Then** the design Epic and the feature plan, both blocked by the foundation
   Epic.

### Existing project

1. **`orchi-standards`** in audit mode inventories what exists: tool
   configurations, CI jobs, branch protection, `CLAUDE.md` and `AGENTS.md` rules.
2. It sorts each existing instruction: retain, rewrite, relocate (to the owning
   document), automate (it belongs in a tool), or delete (a tool already enforces
   it).
3. It writes `ENGINEERING.md` from what the project already enforces, as
   Impeccable's `document` records an incumbent design, and reports the gaps
   against the standards reference.
4. The user picks gaps; each becomes an Issue labelled `needs-planning`.

### During delivery

- Planning cites `ENGINEERING.md` in each Epic's design and each Task's
  verification; Task readiness item 11 names checks from its table.
- Writers run its commands before committing; a change that needs a new rule or
  an exception is an `ESCALATE`.
- The review's Standards axis checks the diff against `ENGINEERING.md`, and an
  exception is recorded there with its reason and an expiry.

## `ENGINEERING.md`

| Section | Content |
| --- | --- |
| Stack | Language, runtime, framework, package manager, each with a pinned version and the reason |
| Commands | Exact commands to set up, format, lint, type-check, test, build, and run |
| Checks | A table of `check`, `tool`, `command`, `CI job`, `blocking`: the part `standards.py` reads |
| Architecture | MUST and SHOULD rules with reasons; each names the tool that enforces it, or says it is reviewed by hand |
| Dependencies | How dependencies are added, pinned, updated, and audited |
| Security | Secret handling, scanning, and what never goes into the repository |
| Conventions | Only what no tool can check: naming, error handling, logging, documentation |
| Exceptions | Each waived rule, where, why, and until when |

## Standards reference

`orchi-core/references/standards.md`:

- the check catalog by category (format, lint, types, tests and coverage,
  module boundaries, secrets, dependencies and supply chain, commit messages,
  repository hygiene) and by project kind, marking which are proposed as
  blocking;
- recommended defaults for the ecosystems the maintainer picks (D4), each with a
  link to its source;
- the rule that a check a tool can run is never written as prose;
- the audit's retain, rewrite, relocate, automate, and delete sorting.

## Tasks

| Task | Outcome |
| --- | --- |
| T1 Standards reference | `references/standards.md`: the check catalog, defaults per ecosystem, and the audit sorting. |
| T2 `ENGINEERING.md` and checker | The document format, a template in the skill's assets, and `scripts/standards.py check` (standard library): every declared check has a CI job running its command and a committed configuration. Tests against fixtures. |
| T3 `orchi-standards` | The entry skill: new-project and audit routes, as above, with crew mode for a planner crew. |
| T4 Exploration and planning | The exploration compares stack options; planning puts the foundation Epic first and blocks the design Epic on it; the design Epic stops scaffolding the stack. |
| T5 Delivery and review | Readiness, writers, and the review's Standards axis read `ENGINEERING.md`; exceptions are recorded there. The managed `CLAUDE.md` section points to it. |
| T6 Installer and documentation | `--github` adds an optional `orchi-standards.yml` workflow that runs `standards.py check`; README, installation, testing; the next version. |

## Acceptance

- A new disposable project goes from an idea to a foundation Epic whose CI fails
  on a planted formatting, lint, type, test, and secret violation and passes
  without them.
- An audit of an existing repository writes `ENGINEERING.md` from what it
  enforces, sorts its instructions, and files only the gaps the user picks.
- `standards.py check` fails when a declared check has no CI job or no
  configuration file, and passes otherwise.
- A Task delivered after the foundation cites the checks it ran from
  `ENGINEERING.md`, and the review reports Standards against it.
- Each claim is reported as established, limited, or not established; text
  tests do not establish live behavior.

## Decisions needed

1. **Skill or step** (P1): a separate `orchi-standards` skill, which also audits
   existing repositories (recommended), or only a step inside planning.
2. **Document** (P2): `ENGINEERING.md` at the root (recommended), or a section in
   `AGENTS.md` or `CLAUDE.md`.
3. **Who runs it in the pool** (P4): a planner crew (recommended), or a new
   architect crew role.
4. **Ecosystems in the first version** (P9): Python and TypeScript
   (recommended); add Go, Swift, Kotlin, or others the maintainer uses.
5. **Blocking by default**: formatting, lint, type checks, tests, and secret
   scanning block (recommended); a coverage threshold and the dependency audit
   start as warnings.
6. **Coverage threshold**: none by default, agreed per project (recommended),
   or a fixed number.
7. **Checker** (P8): ship `standards.py` and its optional workflow
   (recommended), or rely on the CI jobs alone.
8. **Branch protection** (P10): Orchi proposes the command and the user runs it
   (recommended), or Orchi runs it after the user's approval.
9. **Order with design** (P5): the foundation Epic first, the design Epic blocked
   by it (recommended), or both in parallel.
10. **Delivery**: a separate PR stacked on the design track (recommended), or
    part of it.

## Open questions

- Whether the audit should also read GitHub settings (branch protection, secret
  scanning) through `gh`, which needs admin scope on some repositories.
- How a monorepo with several stacks records them: one `ENGINEERING.md` with a
  section per package, or one per package.
