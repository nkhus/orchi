# Installation

## Install

Run the installer from the target repository:

```bash
npx --yes github:nkhus/orchi
```

The current directory is the installation target; `--project /path/to/project` chooses another one.

The installer installs the `orchi` skill (its instructions, references, subagent roles, the read-only knowledge and status tools, and the installer itself) and the entry skills `orchi-explore`, `orchi-plan`, `orchi-deliver`, `orchi-work`, and `orchi-pm` for Claude Code. It renders the Orchi subagents, adds a managed section to `CLAUDE.md`, and reports whether `git` and `gh` are available. It does not install or authenticate Claude Code or the GitHub CLI.

Requirements: Git, the GitHub CLI (`gh`) for Issue and PR work, and Python 3.11 or newer for the bundled scripts, which use only the standard library. The npm wrapper also needs Node.js/npm and `uv`. Linux, macOS, and WSL are supported.

## Skills and instructions

Each skill is installed as a directory in `.claude/skills/` (`orchi`, `orchi-explore`, `orchi-plan`, `orchi-deliver`, `orchi-work`, `orchi-pm`), where Claude Code discovers it. The skills move and clone with the repository.

The installer appends an Orchi workflow section to the target root `CLAUDE.md`. Its rules route implementation through the Orchi skill, require research and agreement before tracking or changes, and keep merge and deployment within the user's authority. It never copies this repository's contributor `AGENTS.md` into another project, and it does not change an existing root `AGENTS.md`. When `CLAUDE.md` is a symlink to root `AGENTS.md`, the section goes into `AGENTS.md`, which Claude Code reads through the link.

Sections are delimited by `<!-- orchi:begin -->` and `<!-- orchi:end -->`. Existing content outside these markers is preserved byte-for-byte, including line endings. Reinstallation updates only an unchanged managed section and never duplicates it. Edited or malformed sections cause installation to stop before mutation, even with `--replace-orchi`; preserve custom rules outside the managed section. A managed instruction file you delete is dropped from the manifest on the next run instead of blocking uninstallation; an installation recreates it.

Instruction discovery improves routing but does not prove model compliance. More specific instructions, explicit user instructions, disabled skills, instruction-size limits, and application settings can affect behavior. Start a fresh session and verify the entrypoint is exposed: `/orchi` in Claude Code, or the IDE's skill selection interface.

## Subagents

Each role in `.claude/skills/orchi/roles/` is rendered to `.claude/agents/`: `orchi-scout.md`, `orchi-researcher.md`, `orchi-implementer.md`, `orchi-fixer.md`, `orchi-reviewer.md`, and `orchi-designer.md`.

`orchi-designer` uses the design skills installed in the project or for the user (Impeccable, Taste Skill, SmoothUI) and the repository's own design system otherwise. Orchi does not install them; see [design skills](../skills/orchi/roles/README.md#design-skills) for their install commands.

Rendered agents name the installed skill as `.claude/skills/orchi` in a project installation and by its absolute path in a user-wide one. They are recorded in the manifest with their hashes: unmodified files update in place on reinstall, a locally edited or pre-existing unmanaged file needs `--replace-orchi` (which keeps a backup), and uninstalling removes them and refuses edited ones. Agent files do not depend on `--github`.

Claude Code lets subagents start their own, up to three layers below the main conversation, by default, which is the nesting Orchi uses. Subagent models are pinned in the roles; if a pinned model is unavailable, the main session performs the step itself.

## GitHub setup

```bash
npx --yes github:nkhus/orchi --github
```

`--github` is opt-in and applies to project installations. Once chosen, later installations keep it. It adds:

| File or resource | Purpose |
| --- | --- |
| `.github/ISSUE_TEMPLATE/orchi-initiative.yml`, `orchi-epic.yml`, `orchi-task.yml`, `orchi-exploration.yml` | Issue forms that apply the matching type label; the Task, Epic, and Initiative forms have a field for every item of the [readiness checklists](../skills/orchi/references/readiness.md), and the Exploration form prepares an Initiative's first five |
| PR template section | Summary, Verification, Merge risk, Documentation impact, and Handoff, as a managed section in an existing template (`.github/pull_request_template.md` or another location GitHub reads) or a new one |
| `.github/workflows/orchi-docs.yml` | On every PR, fails on broken local links the PR introduces (`knowledge.py lint --since` the base branch) or a missing or empty Documentation impact section; omitted with `--no-docs-workflow` |
| Labels `Initiative`, `Epic`, `Task`, `in-progress`, `Exploration`, `needs-planning`, `delivery-ready`, `retro` | Created with `gh` when missing; existing labels are not changed |

The template and workflow files are recorded in the manifest with their hashes, so they follow the same rules as the skill: unmodified files update in place, edited or pre-existing files need `--replace-orchi`, and uninstalling refuses edited files. Label creation needs a GitHub remote and an authenticated `gh`. If either is missing, the installation still completes and reports the error in `labels`; rerun it later to create them. Uninstalling leaves labels in place.

To skip the documentation check workflow, add `--no-docs-workflow`. The manifest records the choice (`docs_workflow`) and later installations keep it until `--docs-workflow` turns the workflow back on. Opting out removes an installed, unmodified workflow; an edited one is a conflict that needs `--replace-orchi`, which keeps a backup. Without either flag, the workflow is installed, including for manifests written before the option existed.

Broken links that already exist on the base branch are reported as pre-existing and do not fail a PR, so the workflow can be enabled in a repository with documentation debt. Run `python3 .claude/skills/orchi/scripts/knowledge.py lint` to see that debt. Make the check required in branch protection if it should block merges.

## Pool setup

A session pool is optional and needs Claude Desktop: Orchi, the entry you talk to, and crews with nested workers that do the work, as the [pool reference](../skills/orchi/references/pool.md) describes. To set it up in a project:

1. Install with `--github`, so the `Exploration`, `needs-planning`, `delivery-ready`, and `retro` labels exist. Planner crews add `delivery-ready` when work passes its readiness gate; Orchi gives a dev lead nothing without it.
2. Protect `main` with branch protection. The pool runs in bypass permissions mode, so its sessions run every tool without a prompt; role instructions, the dev lead's checks, the review, and branch protection are what remain.
3. In Claude Desktop, open one session in the repository, switch it to bypass permissions mode, and type `/orchi-pm`. That session becomes Orchi. In that turn it starts five crews (`--crews <n>` for another number), detaches them to the top level, and files them into the sidebar group `Orchi pool · <repo>`.
4. Click `Create workers` in each crew. In that turn the crew starts three workers (`--workers <n>` on `/orchi-pm` for another number), nested under it. A session can start other sessions only in a turn you started, so these clicks are the only manual steps; no session is created after setup.
5. Bring every request to Orchi. It gives each to a free crew, renames the crew after its role and topic (`planner-pay`, `dev-lead-pay-token`), and links you to it. In interactive mode, answer the crew in its own session.
6. Ask Orchi to take planned work ("take #12"). Follow-ups a dev lead files come back planned and are taken without asking.
7. Merge PRs into main yourself or tell Orchi to. When you step away, tell Orchi "mode auto": crews then ask Orchi instead of you, and Orchi merges reviewed PRs with passing checks; deployment, access, and destructive actions still wait for you. The mode holds through compaction until you change it or type `/orchi-pm` again.
8. When work is done, workers and crews clear themselves and return to the pool as `worker-<n>` and `crew-<k>`. Nothing is archived or deleted.

Pool sessions run with Remote Control off, because a session served over Remote Control cannot be cleared; Orchi itself can stay on it. A clear is also refused while you have the session open on screen or pinned; the clearing session retries later. Type `/orchi-pm`, click `Create workers`, and ask for more crews in the desktop app: a message typed over Remote Control cannot start sessions. Rerunning `/orchi-pm` in Orchi is safe: it finds its crews by the sidebar group and adds only what is missing. In another session it changes nothing and points you to the pool's Orchi; it takes the pool over only when that Orchi is archived or gone.

## User-wide installation

```bash
npx --yes github:nkhus/orchi --global
```

This stores the skills in `~/.claude/skills/`, renders subagents in `~/.claude/agents/`, and adds the managed section to `~/.claude/CLAUDE.md`. Instructions and rendered subagents reference the absolute skill path. No project's root files are edited in global mode. Use project installation when team sharing is required. Local home files do not provision remote or cloud environments; install in each execution environment.

## Inspect, update, and remove

```bash
npx --yes github:nkhus/orchi --project "$PWD" --dry-run
npx --yes github:nkhus/orchi --project "$PWD" --replace-orchi
npx --yes github:nkhus/orchi --project "$PWD" --uninstall
```

Dry-run lists file changes and conflicts (`conflicts`, `requires_replace`) without writing; with `--github` it also lists the labels the installation would create (`labels.create`), read with `gh` and never created. A manifest at `.claude/.orchi-install.json` records hashes, options, managed files, and managed sections. Identical installation is a no-op. Rerunning the installer updates unmodified managed files. Skill files edited since installation, or unmanaged files in the Orchi destination, require `--replace-orchi`. When an installation replaces content Orchi did not install unchanged (edited files, or existing files such as a `CLAUDE.md` it adds a section to), the replaced files are backed up beside the project, or inside the home directory for user-wide installation, and the result names the backup; a clean update of unmodified managed files keeps no backup. Skills, agents, instructions, and manifest are staged together and rolled back on an ordinary installation error. A process or host crash during mutation requires inspecting the backup and target before retrying.

The installer refuses symlinked skill destinations, symlinked agent files it manages, and instruction symlinks other than `CLAUDE.md` linking to root `AGENTS.md`. It preserves unrelated skills and agents, settings, and application manifests. Do not alternate installers to manage the same installation.

`--uninstall` removes the complete managed Orchi installation at the selected project/user scope, including its instruction sections. It preserves surrounding user instructions and refuses modified skill files or managed sections. It does not remove Claude Code, authentication, GitHub Issues, branches, or backups.

Commit the project skill files, rendered agents, instruction changes, and the installation manifest when sharing the setup with the team.

## Local and offline installation

From a checkout:

```bash
python3 tools/install.py --project /absolute/path/to/project --dry-run
python3 tools/install.py --project /absolute/path/to/project
```

The Python installer uses only the standard library. The npm wrapper invokes the same implementation through `uv`. An installed bundle can reinstall or remove itself without a source checkout:

```bash
python3 .claude/skills/orchi/scripts/orchi_install.py --project "$PWD"
```

## Upgrading

Rerun the installation command. The manifest records the installed version; `python3 .claude/skills/orchi/scripts/orchi_install.py --version` prints it with the bundled version and the upgrade command. An installed copy cannot fetch a newer version, so upgrades come from `npx` or a source checkout. Running from the installed copy still treats local edits to the installed skills as conflicts; there, `--replace-orchi` records the edited copy as installed.

### From 0.7.x to 0.18.x

Reinstalling adds and updates everything below; rendered agents and unmodified managed files update in place.

- **New entry skills and agent.** `orchi-explore`, `orchi-work`, and `orchi-pm`, the [exploration](../skills/orchi/references/exploration.md), [testing](../skills/orchi/references/testing.md), and [pool](../skills/orchi/references/pool.md) references, and the read-only `orchi-researcher` agent. An existing skill or agent with one of these names that Orchi did not install is a conflict that needs `--replace-orchi`.
- **Changed behavior.** Writers report red evidence; `orchi-reviewer` reports Spec (with scope creep), Standards, and Tests as separate sections and accepts a Recheck input; `orchi-plan` shows the breakdown before creating Issues and takes a shaped Exploration; `orchi-deliver` accepts `--report-to` for a dev lead crew and ends with up to three [lessons](../skills/orchi/references/review-delivery.md#lessons).
- **Readiness.** Task item 10 asks a defect for a reproduction command; Task item 11 and Epic item 5 ask for test seams. Open Issues written earlier may get `NOT READY` until a line is added.
- **Pool hand-off.** Orchi gives a dev lead crew only Issues labelled `delivery-ready`: add the label to already planned standalone Tasks, standalone Epics, and Initiatives you want the pool to deliver. It takes them when you name them, and by itself only when they say `Requested by:` Orchi. An Initiative goes to one dev lead crew with its Epics.
- **Fewer questions and autonomy levels (0.16).** Sessions ask a question once, never re-ask what the decision log answers, and agree the scope and breakdown in one question when they can. The pool gets three [autonomy levels](../skills/orchi/references/pool.md#modes-and-autonomy), Ask, Decide, and Auto, set by telling Orchi; at Auto, Orchi merges reviewed PRs with passing checks. A repository rule that makes ready work wait for the user still applies on top.
- **Course corrections (0.17).** A writer whose Task needs more work is continued with `SendMessage` instead of restarted; after two misses on the same Task, the main session changes the Task's boundary instead of retrying it. An Initiative steps back after each Epic merge to check the remaining plan. Planning shows the reason when a request was declined before, and records a new refusal. Testing adds observation aids for behavior no check can see, verification reports each acceptance claim as established, limited, or not established (with `--github`, the managed PR template's Verification comment says so), and `orchi-researcher` may read a dependency's source from a temporary shallow clone.
- **Session pool (0.18).** The team hubs `orchi-planner` and `orchi-orchestrator`, the team list in the repository's instructions, and the team reference are gone. `/orchi-pm` makes one Claude Desktop session Orchi, which builds a pool of crews with nested workers and routes every request; see [pool setup](#pool-setup). `orchi-work` runs a worker's task. Claims read `Assigned to crew-<k> (<session id>)`; finish or release work held under the old `Dispatched to` and `Planning by` claims before updating. Reinstalling removes the two hub skills; an edited copy is a conflict that needs `--replace-orchi`.
- **Installer.** `--dry-run` with `--github` lists the labels it would create, a clean update keeps no backup directory, and skills a release no longer ships are removed.
- **GitHub setup.** With `--github`: the `orchi-exploration.yml` form, a `Merge risk` section and acceptance verdicts in the managed PR template, and the `Exploration`, `needs-planning`, `delivery-ready`, and `retro` labels.

### From 0.6.x to 0.7.x

Versions before 0.7.0 installed for Codex, GitHub Copilot, and Claude Code together: one copy of each skill in `.agents/skills/`, Claude links to it in `.claude/skills/`, the workflow section in root `AGENTS.md` with an `@AGENTS.md` import in `CLAUDE.md`, and, depending on the selection, a pointer in `.github/copilot-instructions.md`, Codex agents in `.codex/agents/`, and a block in `.codex/config.toml`. The manifest was `.agents/.orchi-install.json`.

Rerunning the installer migrates such an installation (project or user-wide, including the single-skill and five-skill layouts) to Claude Code only, in one staged change:

- The skills recorded in the old manifest are removed from `.agents/skills/`, and the Claude links become the skill directories themselves. Skills that the old manifest does not record are left untouched.
- The workflow section moves from root `AGENTS.md` into `CLAUDE.md`, replacing the import; the Copilot and Codex instruction sections are removed. Text outside the sections stays as it was.
- Codex agents are removed, Claude Code agents are updated, and the `.codex/config.toml` block is removed (with the file, if Orchi created it and nothing else remains). An edited block is left in place with a note in `notes`.
- The GitHub setup and the documentation check workflow choice carry over. The old manifest is replaced by `.claude/.orchi-install.json`.

Edited skills, agents, or instruction sections stop the migration as they would an upgrade: review them, then pass `--replace-orchi` for files (which backs them up first) or restore edited sections by hand. A link at `.claude/skills/<name>` to anything other than the recorded shared copy stops the installation. `--uninstall` also removes a shared-layout installation directly. Empty `.agents/skills/` and `.codex/agents/` directories may remain; remove them if nothing else uses them.

The same upgrade adds the `orchi-designer` agent, which takes UI Tasks and audits UI diffs; see [choosing a writer](../skills/orchi/roles/README.md#choosing-a-writer). An existing `.claude/agents/orchi-designer.md` that Orchi did not install is a conflict that needs `--replace-orchi`.

Notes for versions before 0.6 are in the Git history of this file.

## Upstream contracts

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code memory](https://code.claude.com/docs/en/memory)
- [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)
- [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
