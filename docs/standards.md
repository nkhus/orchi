# Standards

The user steers and agents write the code, so tools take the place of a human
code review. `orchi-standards` gives a project `ENGINEERING.md` and blocking
checks from Orchi's defaults, planned as a foundation Epic for a new project or
a standards Epic after an audit; `standards.py` keeps the checks from being
lowered quietly.

## Structure

| Part | Defined in |
| --- | --- |
| Premise, product constraints, default stack, check catalog, gate integrity, audit sorting | `skills/orchi-core/references/standards.md` |
| New-project and audit routes | `skills/orchi-standards/SKILL.md` |
| The `ENGINEERING.md` template with the default Checks table | `skills/orchi-core/assets/standards/ENGINEERING.md` |
| `check`, `ratchet`, and `ruleset` | `skills/orchi-core/scripts/standards.py` |
| Checks on pull requests and the weekly drift run | `skills/orchi-core/assets/github/workflows/orchi-standards.yml`, installed with `--github` |

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| The user is asked only product constraints; Orchi applies the defaults for stack, tools, thresholds, and layout without asking and records why | The user never reads the code and cannot weigh tooling choices | Orchi confirming the stack with the user | [#44](https://github.com/nkhus/orchi/pull/44) |
| Every check blocks from the first commit, including 90% coverage of changed lines and high and critical dependency and static analysis findings | Tools are the only review the code gets, and gates added later find a backlog | Coverage and audits starting as warnings | [#44](https://github.com/nkhus/orchi/pull/44) |
| One strict TypeScript stack for web apps, services, and CLIs; Python for data and ML | Static types are the cheapest check an agent gets, and one language keeps one toolchain | Choosing the language per project | [#44](https://github.com/nkhus/orchi/pull/44) |
| Lowering a threshold, turning off a rule, adding a suppression, or deleting a test fails `standards.py ratchet` unless `ENGINEERING.md` records an exception with its reason and expiry, and every exception reaches the user in plain language | An agent under pressure to pass a check can weaken the check instead | None recorded | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi applies the branch protection ruleset with `gh` after one yes from the user in the foundation Epic | One click is all the user should need, and the ruleset makes the checks binding | Printing the command for the user to run | [#44](https://github.com/nkhus/orchi/pull/44) |
| A weekly workflow runs the slow checks and opens one Issue with what slipped | Drift appears without anyone asking, and no session starts unattended | Checking drift only when the user asks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi ships an `ENGINEERING.md` template with the default Checks table, not tool configuration files; the foundation Epic writes the configurations with current tool versions | Configuration files in Orchi would go stale between releases; `check` ties the written ones to CI, and planted violations prove they bite | Shipping per-ecosystem configuration templates | [#44](https://github.com/nkhus/orchi/pull/44) |
| `ENGINEERING.md` lands with the checks it declares, in the foundation or standards Epic; `orchi-standards` only plans | A declared check without its job would fail `check` and mislead the next session | Writing `ENGINEERING.md` ahead of the checks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Static analysis defaults to Semgrep CE, with CodeQL where GitHub Code Security is available; licenses are checked against a command-line allowlist | The defaults must work in private repositories without paid features | CodeQL as the only default | [#44](https://github.com/nkhus/orchi/pull/44) |
| A new project's first Epic is the foundation Epic; every other Epic and Task, the design Epic included, is blocked by it, and only it scaffolds the stack | The checks exist before the first feature code | The design Epic scaffolding the stack | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi borrows ideas from other standards projects and depends on none | They keep their own state folders, and Spec Kit's constitution overrides the repository's own instructions, which conflicts with Git and Issues as the only shared state | Adopting BMAD, Spec Kit, or Kiro steering; copying Trail of Bits' share-alike text | [#44](https://github.com/nkhus/orchi/pull/44) |
