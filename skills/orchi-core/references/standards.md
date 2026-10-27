# Engineering standards

Use when setting up a new project, auditing an existing one, planning work in a
project with `ENGINEERING.md`, writing code there, or reviewing it. The
repository's own instructions take precedence over these defaults.

## Premise

The user steers and agents write the code; nobody is expected to read it.

1. **Tools are the code review.** Every rule a tool can check is a blocking
   check from the first commit; prose rules cover only what no tool can check.
2. **Defaults, not questions.** Orchi chooses the stack, tools, thresholds, and
   layout from this reference and records why. The user is asked about the
   product and its constraints, never about tooling; they may override any
   choice.
3. **Gates are not lowered quietly.** Lowering a threshold, disabling a rule,
   adding a suppression, or deleting a test fails CI unless `ENGINEERING.md`
   records it as an exception, and every exception reaches the user in plain
   language.
4. **The user accepts behavior.** Acceptance criteria say what a user can see or
   do; each has an automated acceptance test, and the PR shows the evidence.
5. **The repository is the memory.** A decision reached in a conversation goes
   into `ENGINEERING.md` or a tool's configuration, or the next session loses it.

## Product constraints

The only questions the user answers, in the exploration or before a foundation
Epic:

- who uses the product, and on which devices;
- where it must run, and any platform, vendor, or language their organization
  mandates;
- what data it holds, and how sensitive it is;
- the budget for hosting and paid services;
- whether it is a disposable proof of concept or meant to last.

A proof of concept keeps every blocking check and drops the weekly ones
(mutation tests and the drift run) until the user says it is meant to last.

## Stack

| Project kind | Default |
| --- | --- |
| Web app | TypeScript (strict), React with Next.js, Tailwind CSS 4, shadcn/ui and SmoothUI, pnpm |
| Service or API | TypeScript (strict) on Node.js LTS with Hono, Zod at every boundary, pnpm |
| Data, ML, scripting | Python 3.13 with uv |
| CLI | TypeScript, or Python when the project is already Python |

Use one language across a product unless a domain needs another. Mobile apps
have no default yet: propose a stack with its reasons, as an override. A
mandated platform or language replaces the matching default and keeps the
checks. Pin the runtime and package manager versions in the repository.

## Checks

Every check is its own CI job, named in the `CI job` column, and the blocking
ones are required by branch protection.

| Check | TypeScript | Python | Blocking |
| --- | --- | --- | --- |
| Format | Prettier | ruff format | yes |
| Lint | ESLint with typescript-eslint `strictTypeChecked` | ruff with the `ALL` rule set minus documented conflicts | yes |
| Types | `tsc --noEmit` with `strict`, no explicit `any` | pyright `strict` | yes |
| Unit and integration tests | Vitest | pytest | yes |
| Coverage | `>= 90%` of changed lines; the project floor only rises | coverage.py, same rule | yes |
| Acceptance tests | Playwright, one test per acceptance criterion | pytest, or Playwright for a UI | yes |
| Accessibility | axe in the Playwright run, WCAG 2.2 AA | same | yes, with a UI |
| UI quality | `impeccable detect` (the design workflow) | same | yes, with a UI |
| Module boundaries | dependency-cruiser | import-linter | yes |
| Size and complexity | ESLint `max-lines` 300, `max-lines-per-function` 50, `complexity` 10 | ruff `C90` 10, `PLR0915` 50 statements | yes |
| Dead code | knip | vulture | yes |
| Secrets | gitleaks | gitleaks | yes |
| Dependencies | `pnpm audit --audit-level high` | pip-audit, every known vulnerability | yes |
| Static security analysis | Semgrep CE with `p/default`, or CodeQL where GitHub Code Security is available | same | yes, errors |
| Licenses | license-checker-rseidelsohn `--onlyAllow` a permissive list | pip-licenses `--allow-only` the same list | yes |
| Gate integrity | `standards.py ratchet` (the standards workflow) | same | yes |
| Mutation tests | Stryker on files changed that week | mutmut on files changed that week | weekly |

A custom lint rule's message says how to fix the violation: its reader is an
agent. Add a custom rule when review finds the same judgement twice, as the
[lessons](review-delivery.md#lessons) ladder says.

## Architecture

- Layers in one direction, by default `types → config → data → domain → api → ui`,
  enforced by the module boundary check; a new module states its layer.
- Validate at every boundary (requests, files, environment, third-party
  responses); code inside a boundary trusts its types.
- Structured logs, and one command that boots the app in a worktree with seeded
  data, so an agent can run it, reproduce a bug, and read what happened.
- Configuration comes from the environment and is documented in an example file;
  no secret is committed.

## Repository

- `ENGINEERING.md` at the root, beside `PRODUCT.md` and `DESIGN.md`.
- Lockfiles committed; Dependabot grouped weekly; Conventional Commits.
- A ruleset on the default branch: every blocking check required, pull requests
  required, linear history, no force push, no deletion.

## `ENGINEERING.md`

The [template](../assets/standards/ENGINEERING.md) holds the sections and the
defaults above. Two tables have a fixed shape, because `standards.py` reads them:

- **Checks**: `Check`, `Tool`, `Command`, `CI job`, `Config`, `Threshold`,
  `Blocking`. `Config` lists the committed configuration files, comma-separated,
  or `-`. `Threshold` is `-` or an operator and a number (`>= 90`, `<= 300`).
  `Blocking` is `yes`, `no`, or `weekly`.
- **Exceptions**: `Rule`, `Where`, `Reason`, `Expires`. `Rule` names the waived
  rule or suppression (`no-console`, `eslint-disable`, `test deleted`,
  `threshold`); `Where` is a path or glob; `Expires` is a date (`YYYY-MM-DD`).

`ENGINEERING.md` describes what the repository enforces now: it lands in the
same commit as the checks it declares, never ahead of them.

## Checker

`python3 <skill>/scripts/standards.py <command>`, from the repository root:

| Command | Does |
| --- | --- |
| `check` | Every declared check has its CI job in `.github/workflows/`, the job runs its command, and its configuration files exist; no exception has expired |
| `ratchet --base <ref>` | Fails when the changes since `<ref>` remove a check, make one non-blocking, loosen a threshold, add a suppression, weaken a listed configuration, delete a test file, or remove assertions, without an exception covering it; lists the exceptions the changes add |
| `ruleset` | Prints the GitHub ruleset that requires every blocking check |

Both checks exit 1 with their findings and 0 when clean. Without
`ENGINEERING.md` they report that and exit 0.

## Gate integrity

An exception covers a finding when its `Where` matches the file and its `Rule`
names the suppression kind or appears in the changed line. Record one only for
a reason the change cannot avoid, with the shortest expiry that fits. The
delivery review lists each exception the PR adds or changes in the PR's
Exceptions section in plain words (what is waived, where, why, until when), and
the session that talks to the user relays them; an exception is the one
code-level decision the user sees.

## New project

`orchi-standards` derives the stack and checks from the product constraints and
plans a foundation Epic, which every other Epic of the project is blocked by.
Its Tasks:

1. Scaffold the stack, the boot command with seeded data, and `ENGINEERING.md`
   with format, lint, types, and size checks in CI, and the documentation map
   with its first area and behavior pages from the
   [templates](knowledge.md#current-documentation).
2. Unit, coverage, and acceptance test harnesses, with one passing acceptance
   test of the empty app, and accessibility with a UI.
3. Module boundaries and dead code.
4. Secrets, dependencies, static analysis, licenses, and Dependabot.
5. The standards workflow, `standards.py check` passing, and, when the project
   is meant to last, the weekly mutation test job.

Its acceptance: CI passes on the empty project and fails on a planted violation
of each blocking check, including a planted suppression and a loosened
threshold; the planted violations never land. After its PR merges, the session
that talks to the user asks once to apply the ruleset, and applies it on a yes:

```
python3 <skill>/scripts/standards.py ruleset | gh api -X POST repos/{owner}/{repo}/rulesets --input -
```

## Audit

For a project without `ENGINEERING.md`, inventory tool configurations, CI jobs,
the default branch's rulesets and protection (when `gh` can read them), and the
rules in `CLAUDE.md`, `AGENTS.md`, and scoped instruction files. Sort each rule:

| Verdict | When |
| --- | --- |
| Retain | Only a person can check it, and it is still true |
| Rewrite | It is true but vague or out of date |
| Relocate | It belongs in another document (`ENGINEERING.md`, `PRODUCT.md`, `DESIGN.md`) |
| Automate | A tool can check it; it becomes that tool's configuration |
| Delete | A tool already enforces it, or it is no longer true |

Then plan one standards Epic: its first Task writes `ENGINEERING.md` for what
the project enforces today and applies the sorting; each later Task closes one
gap to the defaults and updates `ENGINEERING.md` with it. Present it to the user
in product terms: what becomes safer, and how much work it is.

## Drift

With `--github`, the standards workflow runs `standards.py check` and
`knowledge.py stale` weekly and keeps one open Issue, labelled
`needs-planning`, listing what drifted, such as an expired exception, a check
that lost its job, or a page older than its code. Planning takes it like any
request; no session starts unattended.
