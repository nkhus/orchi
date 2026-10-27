# [STD] Project standards by default

Status: implemented on `feat/standards-track`. The skill, its
[standards reference](../../../skills/orchi-core/references/standards.md), and
`standards.py` describe current behavior; this document keeps the reasoning.
It builds on the [design track](../entry-single-entry/design-track.md) and
follows the same pattern: decisions in a committed document, enforced by tools.

## Request

The maintainer's requests, translated from Russian (2026-10-27):

> We should have a skill that defines all the best practices for a project, to
> enforce its quality from the beginning. It sets the language choice and the
> guardrails under it. Are there good examples we can reuse?

> We are moving to AI agent-first development: the user will never look at the
> code, so we need default best practices.

## Premise

The user steers and agents write every line. Nobody reads the code, so:

1. **Tools are the only code review a person would have done.** Every rule a
   tool can check is a blocking check from the first commit; prose rules are
   kept for what no tool can check.
2. **Defaults, not questions.** Orchi chooses the stack, tools, thresholds, and
   layout from this plan's defaults and records why. The user is asked about
   the product and its constraints, never about tooling.
3. **Gates cannot be lowered quietly.** An agent under pressure to pass a check
   can weaken the check instead. Lowering a threshold, disabling a rule, adding
   an inline suppression, or deleting a test fails CI unless it is a recorded
   exception, and every exception is reported to the user in plain language.
4. **The user accepts behavior, not code.** Acceptance criteria are written as
   what a user can see or do; each has an automated acceptance test, and the PR
   shows the evidence: test results, screenshots, a recording, or a preview.
5. **The repository is the agents' only memory.** Decisions reached in a
   conversation go into `ENGINEERING.md` or a tool configuration, or they are
   lost for the next session.

## Prior work

Surveyed on 2026-10-27 from primary sources where reachable. No project both
decides the stack and turns the decision into enforced checks; Orchi borrows
ideas and depends on none of them.

| Source | What Orchi borrows | What it leaves |
| --- | --- | --- |
| [OpenAI, Harness engineering](https://openai.com/index/harness-engineering/) (2026-02), reported by [InfoQ](https://www.infoq.com/news/2026/02/openai-harness-engineering-codex) and [The Neuron](https://www.theneuron.ai/explainer-articles/openais-harness-engineering-playbook-how-to-ship-1m-lines-of-code-without-writing-any/) | A product built with no hand-written code: layer rules enforced by structural tests; custom lint rules that encode taste; a short agent instructions file that points into `docs/`; agents that run the app and read its telemetry to validate their work; a recurring agent task that finds pattern drift and opens cleanup PRs | Codex-specific tooling |
| [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) `bmad-project-context`, `bmad-architecture` | A checkable rule becomes a tool's configuration, not a sentence; the stack table with pinned versions; sorting existing instructions into retain, rewrite, relocate, automate, or delete | Its `_bmad/` state and scripts |
| [GitHub Spec Kit](https://github.com/github/spec-kit) `/speckit.constitution` | MUST and SHOULD rules with reasons; plans checked against them | Its `.specify/` state and versioning; the constitution overriding the repository's own instructions |
| [Kiro steering, cc-sdd](https://github.com/gotalab/cc-sdd) | Separate documents for product, technology, and structure | Its `.kiro/` state |
| [Impeccable](https://github.com/pbakaus/impeccable) | `PRODUCT.md` and `DESIGN.md` beside a deterministic checker | — |
| [Trail of Bits skills](https://github.com/trailofbits/skills) `modern-python` | Recommended as an optional install for Python projects | Its text: CC-BY-SA-4.0 is share-alike |
| [Anthropic plugins](https://github.com/anthropics/claude-plugins-official) `security-guidance` | Recommended as an optional install | — |

## What the user decides

At exploration, in product terms only:

- who uses the product and on which devices;
- where it must run, and any platform, vendor, or language the user's
  organization mandates;
- what data it holds, and how sensitive it is;
- the budget for hosting and paid services;
- whether it is a disposable proof of concept or meant to last. A proof of
  concept keeps every blocking check and drops the slow ones (mutation tests,
  the weekly sweep) until it is promoted.

Orchi derives everything else and states it once, with reasons, in the
exploration's Stack section. The user may override any choice; Orchi does not
ask them to make one.

## Defaults

### Stack

| Project kind | Default |
| --- | --- |
| Web app | TypeScript (strict), React with Next.js, Tailwind CSS 4, shadcn/ui and SmoothUI, pnpm |
| Service or API | TypeScript (strict) on Node.js LTS with Hono, Zod at every boundary, pnpm |
| Data, ML, scripting | Python 3.13 with uv |
| CLI | TypeScript, or Python when the project is already Python |
| Mobile | Out of the first version |

One language across a product unless a domain needs another. Static types
everywhere: they are the cheapest check an agent gets. Runtime and package
manager versions are pinned in the repository.

### Checks

Every check is its own CI job and is required by branch protection.

| Check | TypeScript | Python | Blocks |
| --- | --- | --- | --- |
| Format | Prettier | ruff format | yes |
| Lint | ESLint with typescript-eslint `strictTypeChecked` | ruff with a broad rule set | yes |
| Types | `tsc --noEmit`, `strict`, no `any` | pyright strict | yes |
| Unit and integration tests | Vitest | pytest | yes |
| Coverage | 90% of changed lines; the project floor only rises | same, with coverage.py | yes |
| Acceptance tests | Playwright, one per acceptance criterion | pytest, or Playwright for a UI | yes |
| Accessibility | axe in the Playwright run, WCAG 2.2 AA | same | yes, with a UI |
| UI quality | `impeccable detect` (the design track) | same | yes, with a UI |
| Module boundaries | dependency-cruiser | import-linter | yes |
| Size and complexity | lint limits on file length, function length, and complexity | ruff limits | yes |
| Dead code | knip | vulture | yes |
| Secrets | gitleaks | gitleaks | yes |
| Dependencies | `pnpm audit`, high and critical | pip-audit, high and critical | yes |
| Static security analysis | CodeQL default setup | CodeQL default setup | yes, high and critical |
| Licenses | an allowlist of permissive licenses | same | yes |
| Gate integrity | `standards.py ratchet` | same | yes |
| Mutation tests | Stryker on changed code | mutmut on changed code | weekly, reported |

Lint messages from custom rules say how to fix the violation, because the
reader is an agent.

### Architecture

- Layers in one direction, by default `types → config → data → domain → api → ui`,
  enforced by the module boundary check; a new module states its layer.
- Validation at every boundary (requests, files, environment, third-party
  responses); domain code trusts its types.
- Structured logs, and one command that boots the app in a worktree with seeded
  data, so an agent can run it, reproduce a bug, and read what happened.
- Configuration from the environment, documented in an example file; no secret
  in the repository.

### Repository

- `ENGINEERING.md` at the root, beside `PRODUCT.md` and `DESIGN.md`; the managed
  `CLAUDE.md` section stays short and points to it.
- Lockfiles committed; Dependabot grouped weekly; Conventional Commits.
- Branch protection on the default branch: every check required, linear
  history, no force push.

## Gate integrity

`standards.py ratchet` compares the PR head with its base and fails when the PR:

- lowers a threshold or a coverage floor, or turns off a lint, type, or
  boundary rule;
- removes a check from CI or from `ENGINEERING.md`;
- adds an inline suppression (`eslint-disable`, `@ts-ignore`, `@ts-expect-error`,
  `# noqa`, `# type: ignore`, `pragma: no cover`, a skipped or expected-failure
  test);
- deletes a test, or an assertion from a test, without deleting the code it
  covers;

unless `ENGINEERING.md` Exceptions records that change with its reason and an
expiry. The delivery review lists every new or changed exception in the PR
description in plain language, and Orchi relays them to the user. An exception
is the one code-level decision the user ever sees.

## How it works

### New project

1. **Exploration** records the product constraints above and Orchi's derived
   stack, with reasons, in its Stack section.
2. **`orchi-standards`** writes `ENGINEERING.md` from the defaults and the
   exploration, and plans the foundation Epic. It asks nothing the defaults
   answer.
3. **The foundation Epic** scaffolds the stack, commits every tool
   configuration, the CI workflow, the ratchet, Dependabot, and the boot
   command. It is accepted when CI passes on the empty project and fails on a
   planted violation of each blocking check, including a planted suppression.
4. **Branch protection** is applied as [Decisions](#decisions)
   item 4 settles.
5. **Then** the design Epic and the feature plan, both blocked by the foundation
   Epic; the stack scaffold moves there from the design Epic.

### Existing project

1. **`orchi-standards`** in audit mode inventories tool configurations, CI jobs,
   branch protection, and the rules in `CLAUDE.md` and `AGENTS.md`, and sorts
   each rule: retain, rewrite, relocate, automate, or delete.
2. It writes `ENGINEERING.md` from what the project already enforces and
   measures the distance to the defaults.
3. It proposes one standards Epic that closes the gaps, in product terms: what
   becomes safer and how much work it is. The user agrees its scope like any
   Epic; the Tasks inside are Orchi's.

### During delivery

- Planning writes acceptance criteria as user-visible behavior and names the
  acceptance test for each.
- Writers run the commands in `ENGINEERING.md` before committing; a change that
  needs an exception is an `ESCALATE` to the crew, which records it.
- The review checks the diff against `ENGINEERING.md`, checks that tests assert
  the acceptance criteria rather than the implementation, and reports the
  evidence for each criterion in the PR.

### Drift

A weekly workflow runs the full suite, mutation tests on code changed that
week, and the expired-exception check, and opens one Issue labelled
`needs-planning` with what slipped. Orchi plans it like any other request; no
session starts unattended.

## `ENGINEERING.md`

| Section | Content |
| --- | --- |
| Product constraints | The answers from exploration, linked |
| Stack | Language, runtime, framework, package manager: pinned version and reason |
| Commands | Set up, boot, format, lint, type-check, test, build |
| Checks | Table of `check`, `tool`, `command`, `CI job`, `threshold`, `blocking`: the part `standards.py` reads |
| Architecture | Layers and MUST and SHOULD rules, each naming the tool that enforces it, or "reviewed" |
| Dependencies | Adding, pinning, updating, auditing; license allowlist |
| Security | Secrets, scanning, data handling |
| Conventions | Only what no tool can check |
| Exceptions | Each waived rule: where, why, until when |

## Tasks

| Task | Outcome |
| --- | --- |
| T1 Standards reference | `orchi-core/references/standards.md`: the premise, defaults per project kind and ecosystem with sources, the check catalog, gate integrity, and the audit sorting. |
| T2 Template and checker | An `ENGINEERING.md` template and per-ecosystem configuration templates in assets; `scripts/standards.py` with `check` (every declared check has a CI job, a committed configuration, and a required status) and `ratchet` (the gate integrity rules); fixture tests for both. |
| T3 `orchi-standards` | The entry skill: new-project and audit routes, crew mode for a planner crew. |
| T4 Exploration and planning | Product constraints and a derived Stack section in the exploration; behavior-level acceptance criteria with named acceptance tests; the foundation Epic first, the design Epic blocked by it and no longer scaffolding the stack. |
| T5 Delivery and review | Writers, readiness, and the review read `ENGINEERING.md`; exceptions are escalated, recorded, and reported in plain language; PRs carry per-criterion evidence. |
| T6 Installer, workflows, documentation | `--github` installs `orchi-standards.yml` (check and ratchet on PRs, the weekly drift run); README, installation, testing; the next version. |

## Acceptance

- A disposable project goes from an idea to a foundation Epic with no question
  about tooling, and its CI fails on a planted violation of each blocking check,
  including a planted suppression and a lowered threshold, and passes without
  them.
- An audit of an existing repository writes `ENGINEERING.md` from what it
  enforces and proposes one standards Epic in product terms.
- `standards.py check` and `ratchet` pass and fail on fixtures as specified.
- A Task delivered after the foundation shows evidence per acceptance criterion
  in its PR, and the review reports exceptions in plain language.
- Each claim is reported as established, limited, or not established; text
  tests do not establish live behavior.

## Decisions

The maintainer accepted all six recommendations on 2026-10-27 ("I accept all
six recommendations; implement STD as a separate PR on top of #43").

1. **Premise**: the user is asked only product constraints, and Orchi applies
   the defaults without asking (recommended), or Orchi still confirms the stack.
2. **Strictness from the first commit**: every check in the table blocks,
   including 90% coverage of changed lines and high and critical dependency and
   CodeQL findings (recommended), or coverage and audits start as warnings.
3. **TypeScript first**: one strict TypeScript stack for web apps, services,
   and CLIs, Python only for data and ML (recommended), or the language chosen
   per project.
4. **Branch protection**: Orchi applies the ruleset with `gh` after one yes from
   the user in the foundation Epic (recommended), or Orchi prints the command
   and the user runs it.
5. **Drift**: a weekly workflow opens one Issue (recommended), or drift is
   checked only when the user asks.
6. **Delivery**: a separate PR stacked on the design track (recommended), or
   part of it.

## Implementation notes

Choices made while implementing, within the accepted decisions:

- Orchi ships an `ENGINEERING.md` template with the default Checks table, not
  tool configuration files: the foundation Epic writes the configurations from
  it with current tool versions, `standards.py check` ties them to CI, and the
  planted-violation acceptance proves they bite. Configuration files in Orchi
  would go stale between releases.
- `ENGINEERING.md` lands with the checks it declares, in the foundation or
  standards Epic, never ahead of them; `orchi-standards` only plans.
- Static analysis defaults to Semgrep CE, with CodeQL where GitHub Code Security
  is available, and licenses to a command-line allowlist check, so the defaults
  work in private repositories without paid features.
- The Checks table gains a `Config` column, which `check` and `ratchet` read.
- The exploration gets a Stack section for the product constraints and the
  derived stack.

## Open questions

- Preview deployments per PR depend on the hosting the exploration picks; the
  foundation Epic sets one up when the host offers it.
- A monorepo with several stacks: one `ENGINEERING.md` with a section per
  package, or one per package.
