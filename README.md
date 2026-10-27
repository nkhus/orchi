# Orchi

### One workflow for Claude Code.

**Research first. Agree the scope. Deliver through branches and GitHub Issues.**

Orchi is a development convention for Claude Desktop with one command, `/orchi`: you talk to Orchi, and it runs the work through a pool of sessions, role skills, and six model-tiered subagents. Git stores code and documentation; GitHub Issues store ownership, hierarchy, dependencies, and status. There is no controller, state database, approval receipt, or mandatory command facade. It installs into **Claude Code**.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Skills and subagents](#skills-and-subagents) · [Project instructions](#project-instructions) · [Documentation](#documentation)

---

## Quick start

### 1. Install from your project

Run this in the repository where you want to use Orchi:

```bash
npx --yes github:nkhus/orchi
```

The current directory is the installation target; use `--project /path/to/project` to choose another one.

**Prerequisites:** Git, the GitHub CLI (`gh`, authenticated) for Issue and PR work, Python 3.11+ for the bundled standard-library scripts, and Node.js 18.19+ with `npx`, which installs [Impeccable](https://impeccable.style/), the design skill Orchi installs with itself. The `npx` installer also needs `uv`. Use macOS, Linux, or WSL.

<details>
<summary><strong>Install across projects, preview changes, or remove Orchi</strong></summary>

```bash
npx --yes github:nkhus/orchi --global
```

| Option | Effect |
| --- | --- |
| `--github` | Also add issue templates, a PR template, documentation, design, and standards check workflows, and Orchi labels (project scope) |
| `--no-docs-workflow` | With `--github`, skip the documentation check workflow; `--docs-workflow` restores it |
| `--dry-run` | Show planned file changes, conflicts, and the labels `--github` would create, without writing |
| `--replace-orchi` | Back up and replace locally edited Orchi files, and replace an Impeccable of another version with the pinned one |
| `--version` | Show the installed and bundled versions and the upgrade command |
| `--uninstall` | Remove the complete managed Orchi installation at the selected scope |

To upgrade, rerun the same `npx` command; unmodified managed files update in place. See the [installation guide](docs/installation.md) for paths, conflict handling, upgrading from earlier versions, offline installation, and removal.

</details>

You do not need to commit or push it: the first `/orchi` commits and pushes the installation to `main`, which Orchi's sessions, branches, and CI start from.

### 2. Start Orchi

In Claude Desktop, open a session in the repository, switch it to bypass permissions mode, and type:

```text
/orchi
```

That session becomes Orchi. It builds its pool of crews; click `Create workers` in each crew once. Then tell Orchi what you want, for example "add CSV export to the orders page". `/orchi` is the only command you type: Orchi gives each request to a crew, which talks to you in its own session, and brings back what needs your decision. See [pool setup](docs/installation.md#pool-setup).

## How it works

```mermaid
flowchart TD
    O[You tell Orchi] --> R{Orchi routes to a crew}
    R -->|Idea| Y[Researcher: frame, research, compare options, decide, shape]
    R -->|Request| B
    Y --> B[Planner: research code, docs, and issues]
    B --> C[Propose approach and scope]
    C --> D{User agrees?}
    D -->|No| B
    D -->|Yes| Q[Clarify readiness gaps with the user; log decisions]
    Q --> E{Scope}
    E -->|Task| F[fix/* branch → PR to main]
    E -->|Epic| G[epic/* branch; Tasks in sequence → PR to main]
    E -->|Initiative| H[initiative/* branch; one epic/* PR per Epic → final PR to main]
    F --> I[Dev lead and workers: verify, review, PR; you or Orchi at Auto merge]
    G --> I
    H --> I
```

- **Explore before planning when the direction is open.** For a new project, module, or feature that needs strategic decisions, a researcher crew (`orchi-explore`) frames the idea with the user, sends `orchi-researcher` agents to primary sources and to design at least three different options, records each decision, and keeps the whole map in one `Exploration` Issue. Planning takes that Issue as agreed input for an Initiative, Epic, or Task.
- **Design with you, then build what you approved.** Orchi installs [Impeccable](https://impeccable.style/) as its design engine. Planning gives work that changes a user interface a design depth: none, a brief the planner shapes with you, or a `design` Epic a designer crew runs with you. You choose every direction and approve every comp, at every autonomy level; writers build only against them, and the review adds Impeccable's audit. A new project gets `PRODUCT.md` from its exploration and `DESIGN.md` from its first design Epic.
- **Standards by default, enforced by tools.** Orchi assumes agents write the code and nobody reads it, so tools do the code review. You answer product questions (who uses it, where it runs, what data it holds, the budget, proof of concept or lasting); a planner (`orchi-standards`) derives the stack and checks from Orchi's [defaults](skills/orchi-core/references/standards.md) (strict TypeScript, or Python for data work) and plans a foundation Epic that every other Epic waits for. It commits `ENGINEERING.md` with the checks it declares, each a blocking CI job: format, lint, strict types, tests with 90% coverage of changed lines, an acceptance test per criterion, accessibility, module boundaries, size limits, dead code, secrets, dependency and static security analysis, and licenses. Writers check their own diffs and the review checks the whole range for a weakened gate (a suppression, a loosened check or configuration, a skipped or deleted test, a workflow step that no longer fails); each needs an exception recorded in `ENGINEERING.md`, and each exception reaches you in plain words. The scripts only check structure. An existing project gets an audit and one standards Epic.
- **Agree before tracking.** Research, a proposed scope, and then the proposed breakdown into Epics or Tasks come first. Branches, Issues, and changes follow the user's agreement, not an agent's guess. A request that was declined before is proposed with its earlier reason, and a new refusal is recorded.
- **Scale the ceremony to the work.** A small fix is one Task and one PR. An Epic is one branch and one PR with sequential Tasks. An Initiative integrates several Epic PRs on its own branch before one final PR to main.
- **Every title shows its lineage.** Initiatives and Epics have short tags, and titles start with them: Initiative `[PAY] Card payments`, Epic `[PAY][TOKEN] Tokenize stored cards`, Task `[PAY][TOKEN] Add token column`. Labels carry the type, and branches reuse the tags (`epic/pay-token-tokenize-cards`).
- **Learn from each delivery.** The final report proposes up to three lessons, each tied to an observed event and placed on the most deterministic rung that fits: a check, a readiness item or form field, a reviewer rule, a pointer in `CLAUDE.md`, or an Orchi Issue. Nothing changes until the user accepts it as a `retro` Issue.
- **One entry: `/orchi`.** In Claude Desktop, type `/orchi` in one session in bypass permissions mode, and that session becomes Orchi: your single entry; you never type another command. It builds a pool of crews at the top level of the sidebar, and one click in each crew creates its workers, nested under it; no session is created after that. Orchi does no work itself. It routes each request to a crew: a researcher (`orchi-explore`) for an idea, a planner (`orchi-plan`, or `orchi-standards` for the project's standards) for a request or a fix, a designer (`orchi-design`) for a `design` Epic, and a dev lead (`orchi-deliver`) for other `delivery-ready` work you ask it to take. It renames the crew after its role and topic and links you to it. A crew talks to you and gives all repository work to its workers (`orchi-work`), which talk only to their crew; a dev lead runs Tasks that touch different files in parallel on `task/*` branches. When the work is done, workers and crews clear themselves and return to the pool. In interactive mode you answer crews in their sessions; in auto mode Orchi answers within the autonomy level, and merges reviewed PRs with passing checks. Exploration stays a conversation, and deployment, access, and destructive actions always wait for you. Claims, Issues, and PRs stay the state, so any session can restart and catch up. See [pool](skills/orchi-core/references/pool.md) and [pool setup](docs/installation.md#pool-setup).
- **GitHub is the shared state.** `Initiative`, `Epic`, and `Task` labels, native sub-issues and `blocked by` dependencies, assignees, and `in-progress` describe hierarchy and ownership. Several Claude Code sessions can work on independent Epics in parallel, each in its own branch and worktree. `scripts/status.py` shows which Epics are ready, blocked, or claimed.
- **Context stays current.** Main holds only how the product behaves and is built now: a map in `docs/README.md` assigns code to area pages and to behavior pages written for you, each criterion with its acceptance test, and each area page keeps only the decisions still in force, with the reason and the rejected alternatives. Research findings, options, decision logs, and plans are working documents in `docs/work/` on the work's branch: an exploration starts it on `explore/<slug>`, planning continues it on the Initiative or Epic branch and gives each research decision its fate, each Epic merge moves what is settled into the current pages, and the folder is deleted before main. With `--github`, CI fails on broken links, an empty Documentation impact, or working documents in a PR into main; writers and the review check that changed code kept its pages current against the map.
- **Verify once, repair precisely.** Every new test is shown failing before the change. Each Epic gets one full review along three separate axes (Spec, including scope creep; Standards; Tests), with a design audit by `orchi-designer` when it changes user interface; demonstrated blockers are repaired, by the writer that already holds the Task's context when it can be continued, and rechecked with a targeted follow-up. After two misses on the same Task, the main session changes the Task's boundary instead of retrying it, and an Initiative steps back after each Epic merge to check that the remaining plan still fits. Verification reports each acceptance claim as established, limited, or not established. Each PR states its merge risk: a one-way or two-way door, and the blast radius. Interrupted work leaves a fixed Handoff section in the PR. Merging and deployment stay within the user's authority.

The [skill](skills/orchi-core/SKILL.md) is the complete workflow. Stage references cover [exploration](skills/orchi-core/references/exploration.md), [planning](skills/orchi-core/references/planning.md), [readiness](skills/orchi-core/references/readiness.md), [execution](skills/orchi-core/references/execution.md), [testing](skills/orchi-core/references/testing.md), [knowledge](skills/orchi-core/references/knowledge.md), [review and delivery](skills/orchi-core/references/review-delivery.md), [GitHub conventions](skills/orchi-core/references/github.md), [documentation retrieval](skills/orchi-core/references/retrieval.md), and [working as a session pool](skills/orchi-core/references/pool.md).

## Skills and subagents

You type only `/orchi`. The other skills are role skills that Orchi's sessions invoke, hidden from the slash-command menu:

| Skill | Run by | Does |
| --- | --- | --- |
| `orchi` | You (`/orchi [request]`) | Makes a long-lived session Orchi: builds the pool, routes each request to a crew, assigns and releases crews, and tells you only about decisions, merges, and questions waiting for you. Never plans, researches, or edits code |
| `orchi-explore` | A researcher crew | Researches and shapes an idea with you before any scope exists, in an `Exploration` Issue and an `explore/<slug>` branch, then continues into planning |
| `orchi-plan` | A planner crew | Proposes a scope and waits for your agreement, clarifies in rounds, shows the breakdown, creates ready Issues, and labels them `delivery-ready` |
| `orchi-standards` | A planner crew | Sets a project's engineering standards from your product constraints: a foundation Epic for a new project, or an audit and a standards Epic |
| `orchi-design` | A designer crew | Runs a `design` Epic with you through [Impeccable](https://impeccable.style/): every direction and comp is yours; builds go to workers |
| `orchi-deliver` | A dev lead crew | Delivers a Task, Epic, or Initiative through its workers, one review, and a PR; never merges into main |
| `orchi-work` | A worker | Implements, fixes, or designs one ready Task, or answers one research question, as the matching subagent role; talks only to its crew |
| `orchi-core` | Every pool session | The workflow itself: scope, readiness, execution, testing, review, knowledge, standards, and the pool |

`orchi-plan` and `orchi-deliver` enforce the [readiness checklists](skills/orchi-core/references/readiness.md) for Tasks, Epics, and Initiatives: the planner checks every Issue it creates, and the dev lead checks the work again before delivering it.

The installer renders six Claude Code subagents from one definition each in [`skills/orchi-core/roles/`](skills/orchi-core/roles/README.md). Crews and workers may delegate retrieval, research and option design, one Task or defect repair at a time, UI design, and review to them.

| Agent | Model / effort | Writes | Role |
| --- | --- | --- | --- |
| `orchi-scout` | haiku / medium | nothing | Returns paths, line ranges, and excerpts |
| `orchi-researcher` | opus / medium | nothing | Answers an exploration question from cited primary sources, or designs one option under a given lens |
| `orchi-implementer` | opus / medium | one commit per run | Runs the Task readiness gate, then implements and verifies one Task, standalone or in an Epic |
| `orchi-fixer` | sonnet / medium | one commit per run (Task or repair) | Makes one small, fully specified change — a simple Task or a confirmed defect repair — and escalates anything larger |
| `orchi-reviewer` | opus / high | nothing | Reviews a standalone Task, an assembled Epic, or a final Initiative candidate |
| `orchi-designer` | opus / medium | one commit per UI Task run; nothing in Audit mode | Builds one ready UI Task against the approved comp or direction contract, or audits a UI diff, with Impeccable; never asks the user |

Implementers, fixers, designers, and reviewers may start `orchi-scout` or `orchi-reviewer` for independent sub-questions, researchers start scouts or other researchers, and scouts only other scouts; only the session that owns the work starts the writers `orchi-implementer`, `orchi-fixer`, and `orchi-designer`, and nested agents never talk to the user, change Issues, push, or merge. Claude Code allows subagents to start their own, up to three layers below the main conversation, by default ([Claude Code subagents](https://code.claude.com/docs/en/sub-agents)).

## Project instructions

| File or directory | Purpose |
| --- | --- |
| `.claude/skills/orchi-core/` | The Orchi skill |
| `.claude/skills/orchi/` | The `/orchi` entry |
| `.claude/skills/orchi-explore/`, `orchi-plan/`, `orchi-design/`, `orchi-standards/`, `orchi-deliver/`, `orchi-work/` | Role skills Orchi's sessions invoke, hidden from the menu |
| Root `CLAUDE.md` | Managed Orchi workflow instructions |
| `.claude/agents/orchi-*.md` | Rendered subagents |
| `.claude/skills/impeccable/`, `.claude/agents/impeccable-*.md` | Impeccable at the version Orchi pins, installed by its own installer without hooks |
| `.impeccable/config.json` | Impeccable's project settings; the installer turns telemetry off unless the file already sets it |
| `.gitignore` | A managed section that ignores Impeccable's runtime files |
| `.github/ISSUE_TEMPLATE/orchi-*.yml`, `.github/workflows/orchi-docs.yml`, `orchi-design.yml`, `orchi-standards.yml` | Issue forms, documentation check, design check, and standards check, with `--github`; reinstalling replaces unmodified files; edited ones are conflicts that need `--replace-orchi` |
| PR template | Managed Summary, Verification, Merge risk, Exceptions, Documentation impact, and Handoff sections, with `--github` |
| `.claude/.orchi-install.json` | Installation manifest: the installed version, options, and the managed files (with hashes) and sections that reinstalling and uninstalling rely on |

The installer preserves your existing instruction text. It maintains only the section between `<!-- orchi:begin -->` and `<!-- orchi:end -->` and refuses to overwrite a locally edited managed section. Repository instructions take precedence over Orchi's defaults, so an existing issue template or check command keeps working.

Commit the installed skills, rendered agents, instruction changes, and installation manifest to share the setup with your team.

## Documentation

| Guide | Read it to… |
| --- | --- |
| [Documentation map](docs/README.md) | Find the page that describes each part of Orchi and the decisions in force |
| [Installation](docs/installation.md) | Install, upgrade, or remove the skill |
| [Subagent roles](skills/orchi-core/roles/README.md) | Choose a writer, see each role's model and tools, and find the design skills `orchi-designer` uses |
| [Testing](docs/testing.md) | Validate the package and run the installed-skill smoke test |
| [External references](docs/references.md) | Find the skill standards and Claude Code documentation |

## Contributing

The installable skills live in `skills/`; subagent roles live in `skills/orchi-core/roles/`. Repository-only validation, tests, and documentation live in `tools/`, `tests/`, and `docs/`.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

See [contributing](CONTRIBUTING.md). Deterministic tests establish installer and tool behavior, not live model quality.
