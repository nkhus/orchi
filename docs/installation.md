# Installation

## Install

Run the installer from the target repository:

```bash
npx --yes github:nkhus/orchi
```

The current directory is the installation target; `--project /path/to/project` chooses another one.

The installer installs the `orchi` skill (its instructions, references, subagent roles, the read-only knowledge and status tools, and the installer itself) and the explicit entry skills `orchi-explore`, `orchi-plan`, `orchi-deliver`, `orchi-planner`, and `orchi-orchestrator` for Claude Code. It renders the Orchi subagents, adds a managed section to `CLAUDE.md`, and reports whether `git` and `gh` are available. It does not install or authenticate Claude Code or the GitHub CLI.

Requirements: Git, the GitHub CLI (`gh`) for Issue and PR work, and Python 3.11 or newer for the bundled scripts, which use only the standard library. The npm wrapper also needs Node.js/npm and `uv`. Linux, macOS, and WSL are supported.

## Skills and instructions

Each skill is installed as a directory in `.claude/skills/` (`orchi`, `orchi-explore`, `orchi-plan`, `orchi-deliver`, `orchi-planner`, `orchi-orchestrator`), where Claude Code discovers it. The skills move and clone with the repository.

The installer appends an Orchi workflow section to the target root `CLAUDE.md`. Its rules route implementation through the Orchi skill, require research and agreement before tracking or changes, and keep merge and deployment within the user's authority. It never copies this repository's contributor `AGENTS.md` into another project, and it does not change an existing root `AGENTS.md`. When `CLAUDE.md` is a symlink to root `AGENTS.md`, the section goes into `AGENTS.md`, which Claude Code reads through the link.

Sections are delimited by `<!-- orchi:begin -->` and `<!-- orchi:end -->`. Existing content outside these markers is preserved byte-for-byte, including line endings. Reinstallation updates only an unchanged managed section and never duplicates it. Edited or malformed sections cause installation to stop before mutation, even with `--replace-orchi`; preserve custom rules outside the managed section. A managed instruction file you delete is dropped from the manifest on the next run instead of blocking uninstallation; an installation recreates it.

Instruction discovery improves routing but does not prove model compliance. More specific instructions, explicit user instructions, disabled skills, instruction-size limits, and application settings can affect behavior. Start a fresh session and verify the entrypoint is exposed: `/orchi` in Claude Code, or the IDE's skill selection interface.

## Subagents

Each role in `.claude/skills/orchi/roles/` is rendered to `.claude/agents/`: `orchi-scout.md`, `orchi-implementer.md`, `orchi-fixer.md`, `orchi-reviewer.md`, and `orchi-designer.md`.

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
| Labels `Initiative`, `Epic`, `Task`, `in-progress`, `Exploration`, `needs-planning` | Created with `gh` when missing; existing labels are not changed |

The template and workflow files are recorded in the manifest with their hashes, so they follow the same rules as the skill: unmodified files update in place, edited or pre-existing files need `--replace-orchi`, and uninstalling refuses edited files. Label creation needs a GitHub remote and an authenticated `gh`. If either is missing, the installation still completes and reports the error in `labels`; rerun it later to create them. Uninstalling leaves labels in place.

To skip the documentation check workflow, add `--no-docs-workflow`. The manifest records the choice (`docs_workflow`) and later installations keep it until `--docs-workflow` turns the workflow back on. Opting out removes an installed, unmodified workflow; an edited one is a conflict that needs `--replace-orchi`, which keeps a backup. Without either flag, the workflow is installed, including for manifests written before the option existed.

Broken links that already exist on the base branch are reported as pre-existing and do not fail a PR, so the workflow can be enabled in a repository with documentation debt. Run `python3 .claude/skills/orchi/scripts/knowledge.py lint` to see that debt. Make the check required in branch protection if it should block merges.

## Team setup

A team is optional: one planner session, one orchestrator session, and worker sessions, as the [team reference](../skills/orchi/references/team.md) describes. To set it up in a project:

1. Install with `--github`, so the `needs-planning` and `Exploration` labels exist.
2. Decide how far workers may run alone. A worker stops at every permission prompt until someone answers it, so give the project a permission mode and an allowlist that fit your risk, in `.claude/settings.json`, for example `{"permissions": {"defaultMode": "auto"}}` with `allow` rules for the repository's `git`, `gh`, and check commands. Orchi does not change these settings.
3. Start one session in the repository in that same permission mode and run `/orchi-planner`; keep the planner and orchestrator sessions in the mode workers get from the settings. It names itself and, when no orchestrator is running, offers to start one with `/orchi-orchestrator`.
4. Talk to the planner. When it reports work as ready, the orchestrator claims it and starts a worker per Issue: in Claude Desktop it offers a one-click session for you to accept; in a terminal signed in to the Claude Code CLI it starts `claude --bg` sessions (`claude agents` lists them, `claude attach <id>` opens one).
5. Open a worker when the orchestrator says it needs you, and merge PRs into main yourself or tell the orchestrator to.

Background sessions need the folder to be trusted and the CLI to be signed in (`claude auth login`); Claude Desktop and the CLI sign in separately. Workers start in fresh worktrees from main, so commit the permission settings to main. Sessions in different permission modes cannot exchange messages: the message is held and, in a session that cannot ask its user, expires. The orchestrator runs at most five workers at once; the repository's instructions can set another limit. A role skill's text is re-attached after compaction, and each role rebuilds its state from GitHub, so rerunning `/orchi-planner` or `/orchi-orchestrator` is safe.

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

Dry-run lists file changes and conflicts (`conflicts`, `requires_replace`) without writing. A manifest at `.claude/.orchi-install.json` records hashes, options, managed files, and managed sections. Identical installation is a no-op. Rerunning the installer updates unmodified managed files. Skill files edited since installation, or unmanaged files in the Orchi destination, require `--replace-orchi`; changed files are backed up beside the project, or inside the home directory for user-wide installation. Skills, agents, instructions, and manifest are staged together and rolled back on an ordinary installation error. A process or host crash during mutation requires inspecting the backup and target before retrying.

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

### From 0.10.x to 0.11.x

- **Finishing workers.** A team worker stays until its PR is merged and takes rework in its own session (`#<n> rework`, `#<n> incomplete`). The orchestrator checks that a PR is complete before calling the user to merge, tells the worker `#<n> merged` after a merge, and after `done` archives the worker with its worktree when the PR is merged, the Issue closed, and the worktree clean. See [finish a worker](../skills/orchi/references/team.md#finish-a-worker).

### From 0.9.x to 0.10.x

- **Team roles.** The `orchi-planner` and `orchi-orchestrator` entry skills and the [team reference](../skills/orchi/references/team.md) are new; `orchi-deliver` accepts `--report-to <orchestrator>`. See [team setup](#team-setup). Reinstalling adds them; nothing changes for work outside a team.
- **GitHub setup.** With `--github`, reinstalling creates the `needs-planning` label.

### From 0.8.x to 0.9.x

- **Exploration.** The new `orchi-explore` entry skill and [exploration reference](../skills/orchi/references/exploration.md) research and shape an idea in an `Exploration` Issue before planning, and `orchi-plan #<exploration>` turns a shaped one into tracked work. Reinstalling adds the skill.
- **`orchi-researcher` agent.** A read-only subagent for cited research and option design. An existing `.claude/agents/orchi-researcher.md` that Orchi did not install is a conflict that needs `--replace-orchi`.
- **GitHub setup.** With `--github`, reinstalling adds the `orchi-exploration.yml` form and the `Exploration` label.

### From 0.7.x to 0.8.x

- **Testing and review.** The new [testing reference](../skills/orchi/references/testing.md) defines seams, test quality, red evidence, and the defect diagnosis steps. Writers report red evidence (each new or changed test failing before the change), and `orchi-reviewer` reports Spec (with scope creep), Standards, and Tests as separate axes, starting one reviewer per axis in Epic and Initiative mode. Reinstalling updates the rendered agents in place.
- **Defect readiness.** Task readiness item 10 now asks a defect's failure scenario for a reproduction command that has already failed, or the reason none exists. Open defect Tasks written earlier may get `NOT READY` until that is added. With `--github`, reinstalling replaces an unmodified `orchi-task.yml` form.
- **Planning.** `orchi-plan` shows the proposed Epics or Tasks and waits for agreement before creating Issues. Clarifying asks along dependencies and looks facts up instead of asking for them. Tasks are sliced vertically, and Epic designs name test seams: Epic readiness item 5 and Task readiness item 11 now ask for them, so earlier open Issues may need a line added. Decisions that are hard to reverse, surprising, and a real tradeoff go into the project's decision records with the code.
- **PR template.** With `--github`, the managed PR template gains a `Merge risk` section, and Verification asks for red evidence. An unmodified managed section updates in place; an edited one is a conflict, as before.

### From 0.6.x to 0.7.x

Versions before 0.7.0 installed for Codex, GitHub Copilot, and Claude Code together: one copy of each skill in `.agents/skills/`, Claude links to it in `.claude/skills/`, the workflow section in root `AGENTS.md` with an `@AGENTS.md` import in `CLAUDE.md`, and, depending on the selection, a pointer in `.github/copilot-instructions.md`, Codex agents in `.codex/agents/`, and a block in `.codex/config.toml`. The manifest was `.agents/.orchi-install.json`.

Rerunning the installer migrates such an installation (project or user-wide, including the single-skill and five-skill layouts) to Claude Code only, in one staged change:

- The skills recorded in the old manifest are removed from `.agents/skills/`, and the Claude links become the skill directories themselves. Skills that the old manifest does not record are left untouched.
- The workflow section moves from root `AGENTS.md` into `CLAUDE.md`, replacing the import; the Copilot and Codex instruction sections are removed. Text outside the sections stays as it was.
- Codex agents are removed, Claude Code agents are updated, and the `.codex/config.toml` block is removed (with the file, if Orchi created it and nothing else remains). An edited block is left in place with a note in `notes`.
- The GitHub setup and the documentation check workflow choice carry over. The old manifest is replaced by `.claude/.orchi-install.json`.

Edited skills, agents, or instruction sections stop the migration as they would an upgrade: review them, then pass `--replace-orchi` for files (which backs them up first) or restore edited sections by hand. A link at `.claude/skills/<name>` to anything other than the recorded shared copy stops the installation. `--uninstall` also removes a shared-layout installation directly. Empty `.agents/skills/` and `.codex/agents/` directories may remain; remove them if nothing else uses them.

The same upgrade adds the `orchi-designer` agent, which takes UI Tasks and audits UI diffs; see [choosing a writer](../skills/orchi/roles/README.md#choosing-a-writer). An existing `.claude/agents/orchi-designer.md` that Orchi did not install is a conflict that needs `--replace-orchi`.

### From 0.5.x to 0.6.x

- **Writers and review.** `orchi-implementer` also accepts standalone Tasks, `orchi-reviewer` has a Task mode, and `orchi-deliver` reviews every standalone Task once before its PR. A fixer `ESCALATE` names its cause (`decision` or `size`), routed per [choosing a writer](../skills/orchi/roles/README.md#choosing-a-writer). Reinstalling updates the rendered agents in place.
- **Epic readiness.** "Each blocker is merged into the target branch" moved from item 9 to item 11, so future Initiative Epics with open blockers pass intake and are held back only at delivery.

### From 0.3.x or 0.4.x to 0.5.x

- **Issue forms.** With `--github`, reinstalling replaces unmodified `orchi-task.yml`, `orchi-epic.yml`, and `orchi-initiative.yml` forms with the current ones, which have a field for every readiness checklist item. A locally edited form is a conflict: review the differences, keep project-specific fields in your own template, then rerun with `--replace-orchi`, which backs the form up first.
- **Readiness checklists.** The Task checklist now has 13 items and the Epic checklist 12, including numbered requirements, a solution vision, and a decision log, and Initiatives have their own checklist. `orchi-implementer` and `orchi-fixer` may report `NOT READY` for open Issues written against the earlier checklists. Re-check open Task, Epic, and Initiative Issues against the [readiness checklists](../skills/orchi/references/readiness.md) and fill the gaps before delivering them.
- **`orchi-fixer` agent.** Added in 0.4.0; reinstalling from 0.3.x renders it. An existing agent file with that name is a conflict that needs `--replace-orchi`.

## Upstream contracts

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code memory](https://code.claude.com/docs/en/memory)
- [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)
- [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
