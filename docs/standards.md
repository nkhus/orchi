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
| `check` and `ruleset` | `skills/orchi-core/scripts/standards.py` |
| Checks on pull requests and the weekly drift run | `skills/orchi-core/assets/github/workflows/orchi-standards.yml`, installed with `--github` |

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| `orchi-standards` invoked with an Exploration continues into `orchi-plan` for the rest of the plan, and only `orchi-plan` closes the Exploration; it takes the Exploration's Stack section as stated | Closing the Exploration after the foundation alone left the design Epic and the rest unplanned, and deriving the stack twice let the two drift | Closing the Exploration from `orchi-standards` | [#49](https://github.com/nkhus/orchi/pull/49) |
| The user is asked only product constraints; Orchi applies the defaults for stack, tools, thresholds, and layout without asking and records why | The user never reads the code and cannot weigh tooling choices | Orchi confirming the stack with the user | [#44](https://github.com/nkhus/orchi/pull/44) |
| Every check blocks from the first commit, including 90% coverage of changed lines and high and critical dependency and static analysis findings | Tools are the only review the code gets, and gates added later find a backlog | Coverage and audits starting as warnings | [#44](https://github.com/nkhus/orchi/pull/44) |
| One strict TypeScript stack for web apps, services, and CLIs; Python for data and ML | Static types are the cheapest check an agent gets, and one language keeps one toolchain | Choosing the language per project | [#44](https://github.com/nkhus/orchi/pull/44) |
| Lowering a threshold, turning off a rule, adding a suppression, skipping or deleting a test, or changing what a check runs is a review blocker unless `ENGINEERING.md` records an exception with its reason and expiry, and every exception reaches the user in plain language; writers check their own diffs and the review checks the range, and no script guesses at it | An agent under pressure to pass a check can weaken the check instead; a heuristic ratchet both missed real bypasses and blocked normal work | `standards.py ratchet`, removed after an independent review bypassed it many ways and the maintainer chose agents' checks and the final review over scripts | [#44](https://github.com/nkhus/orchi/pull/44), [#48](https://github.com/nkhus/orchi/pull/48) |
| After a foundation or standards Epic merges into main, the delivering session (`orchi-deliver`, or its dev lead crew through Orchi) asks the user once and applies the branch ruleset with `gh` on their yes, at every autonomy level | One click is all the user should need, the ruleset makes the checks binding, and a step no skill owns never happens | Printing the command for the user to run; leaving the step to whichever session talks to the user | [#44](https://github.com/nkhus/orchi/pull/44), owner in [#47](https://github.com/nkhus/orchi/pull/47) |
| A weekly workflow runs the slow checks and opens one Issue with what slipped | Drift appears without anyone asking, and no session starts unattended | Checking drift only when the user asks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi ships an `ENGINEERING.md` template with the default Checks table, not tool configuration files; the foundation Epic writes the configurations with current tool versions | Configuration files in Orchi would go stale between releases; `check` ties the written ones to CI, and planted violations prove they bite | Shipping per-ecosystem configuration templates | [#44](https://github.com/nkhus/orchi/pull/44) |
| `ENGINEERING.md` lands with the checks it declares, in the foundation or standards Epic; `orchi-standards` only plans | A declared check without its job would fail `check` and mislead the next session | Writing `ENGINEERING.md` ahead of the checks | [#44](https://github.com/nkhus/orchi/pull/44) |
| Static analysis defaults to Semgrep CE, with CodeQL where GitHub Code Security is available; licenses are checked against a command-line allowlist | The defaults must work in private repositories without paid features | CodeQL as the only default | [#44](https://github.com/nkhus/orchi/pull/44) |
| A new project's first Epic is the foundation Epic; every other Epic and Task, the design Epic included, is blocked by it, and only it scaffolds the stack | The checks exist before the first feature code | The design Epic scaffolding the stack | [#44](https://github.com/nkhus/orchi/pull/44) |
| Orchi borrows ideas from other standards projects and depends on none | They keep their own state folders, and Spec Kit's constitution overrides the repository's own instructions, which conflicts with Git and Issues as the only shared state | Adopting BMAD, Spec Kit, or Kiro steering; copying Trail of Bits' share-alike text | [#44](https://github.com/nkhus/orchi/pull/44) |
