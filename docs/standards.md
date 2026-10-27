# Standards

The user steers and agents write the code, so tools take the place of a human
code review. `orchi-standards` gives a project `ENGINEERING.md` and blocking
checks from Orchi's defaults, planned as a one-Task foundation Epic for a new
project, with a hardening Epic beside the product work when it is meant to last,
or a standards Epic after an audit; `standards.py` keeps the checks from being
lowered quietly.

## Structure

| Part | Defined in |
| --- | --- |
| Premise, product constraints, default stack, check catalog, gate integrity, audit sorting | `skills/orchi-core/references/standards.md` |
| New-project and audit routes | `skills/orchi-standards/SKILL.md` |
| The `ENGINEERING.md` template with the default Checks table | `skills/orchi-core/assets/standards/ENGINEERING.md` |
| `check` and `ruleset` | `skills/orchi-core/scripts/standards.py` |
| Checks on pull requests and the weekly drift run | `skills/orchi-core/assets/github/workflows/orchi-standards.yml`, installed with `--github` |

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| `orchi-standards` invoked with an Exploration continues into `orchi-plan` for the rest of the plan, and only `orchi-plan` closes the Exploration; it takes the Exploration's Stack section as stated | Closing the Exploration after the foundation alone left the design Epic and the rest unplanned, and deriving the stack twice let the two drift | Closing the Exploration from `orchi-standards` | [#49](https://github.com/nkhus/orchi/pull/49) |
| The user is asked only product constraints; Orchi applies the defaults for stack, tools, thresholds, and layout without asking and records why | The user never reads the code and cannot weigh tooling choices | Orchi confirming the stack with the user | [#44](https://github.com/nkhus/orchi/pull/44) |
| The foundation Epic has one Task and adds the checks every change needs (format, lint and its limits, types, tests with 90% coverage of changed lines, acceptance and accessibility, the design detector, secrets, and `standards.py check`), each blocking from the commit that adds it; for a project meant to last, a hardening Epic adds module boundaries, dead code, dependency, static analysis, and license checks, Dependabot, and mutation tests, blocked by the foundation and blocking nothing | In a live run, a foundation with every check took five sequential Tasks and most of an hour before any product work, for a proof of concept; the core checks are cheap, and the rest guard a codebase that lives | Every check from the first commit, in five foundation Tasks; coverage and audits starting as warnings | [#44](https://github.com/nkhus/orchi/pull/44), [#55](https://github.com/nkhus/orchi/pull/55) |
| One strict TypeScript stack for web apps, services, and CLIs; Python for data and ML | Static types are the cheapest check an agent gets, and one language keeps one toolchain | Choosing the language per project | [#44](https://github.com/nkhus/orchi/pull/44) |
| CI runs on every pull request, whatever its base, and a dev lead pushes a writer's commit without rerunning its checks locally | Delivery relies on CI for each Task, so an Epic PR into an Initiative branch must be checked too | CI only on pull requests into main | [#55](https://github.com/nkhus/orchi/pull/55) |
| Lowering a threshold, turning off a rule, adding a suppression, skipping or deleting a test, or changing what a check runs is a review blocker unless `ENGINEERING.md` records an exception with its reason and expiry; agents decide exceptions (the writer records the one its Task names or reports another, the dev lead decides it, and the review confirms no change avoids it), and the user hears of each in plain words as information; writers check their own diffs and the review checks the range, and no script guesses at it | An agent under pressure to pass a check can weaken the check instead; a heuristic ratchet both missed real bypasses and blocked normal work; the user cannot weigh a license or a lint rule | `standards.py ratchet`, removed after an independent review bypassed it many ways; asking the user to decide an exception, which in a live run put a dependency's license to a user who never reads code | [#44](https://github.com/nkhus/orchi/pull/44), [#48](https://github.com/nkhus/orchi/pull/48), [#55](https://github.com/nkhus/orchi/pull/55) |
| After a foundation, hardening, or standards Epic merges into main, the delivering session applies or replaces the branch ruleset with `gh` without asking (for a standards Epic, the scope the user agreed includes it), and tells the user; when GitHub refuses, it says in one line what enforcing the checks needs | The ruleset makes the agreed checks binding, a step no skill owns never happens, and the user cannot weigh it | Asking the user once; printing the command for the user to run | [#44](https://github.com/nkhus/orchi/pull/44), owner in [#47](https://github.com/nkhus/orchi/pull/47), [#55](https://github.com/nkhus/orchi/pull/55) |
| A weekly workflow runs the slow checks and opens one Issue with what slipped | Drift appears without anyone asking, and no session starts unattended | Checking drift only when the user asks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi ships an `ENGINEERING.md` template with the default Checks table, not tool configuration files; the foundation Epic writes the configurations with current tool versions | Configuration files in Orchi would go stale between releases; `check` ties the written ones to CI, and planted violations prove they bite | Shipping per-ecosystem configuration templates | [#44](https://github.com/nkhus/orchi/pull/44) |
| `ENGINEERING.md` lands with the checks it declares, in the foundation or standards Epic; `orchi-standards` only plans | A declared check without its job would fail `check` and mislead the next session | Writing `ENGINEERING.md` ahead of the checks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Static analysis defaults to Semgrep CE, with CodeQL where GitHub Code Security is available; production dependencies' licenses are checked against a command-line allowlist that includes CC-BY-4.0, MPL-2.0, and BlueOak-1.0.0 | The defaults must work in private repositories without paid features, and a narrower list failed every Next.js app on `caniuse-lite` and `axe-core` | CodeQL as the only default | [#44](https://github.com/nkhus/orchi/pull/44), [#55](https://github.com/nkhus/orchi/pull/55) |
| A new project's first Epic is the foundation Epic; only it scaffolds the stack, and it blocks the work that writes product code, while the design Epic's steps with the user run beside it and only its builds wait | The checks exist before the first feature code, and the user's design work need not wait for tooling | Blocking the design Epic on the foundation; the design Epic scaffolding the stack | [#44](https://github.com/nkhus/orchi/pull/44), [#55](https://github.com/nkhus/orchi/pull/55) |
| Orchi borrows ideas from other standards projects and depends on none | They keep their own state folders, and Spec Kit's constitution overrides the repository's own instructions, which conflicts with Git and Issues as the only shared state | Adopting BMAD, Spec Kit, or Kiro steering; copying Trail of Bits' share-alike text | [#44](https://github.com/nkhus/orchi/pull/44) |
