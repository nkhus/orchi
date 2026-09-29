# Installation

## Select assistants

Run the installer from the target repository. Select one or several assistants:

```bash
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot claude
npx --yes github:nkhus/orchi --project "$PWD" --agents all
```

`codex`, `copilot`, and `claude` are the canonical names. Comma-separated names, repeated `--agent` options, `github-copilot`, and `claude-code` also work. Without a selection, an interactive terminal offers a numbered picker. Noninteractive installation retains the existing selection or defaults to Codex. Adding an assistant preserves previously selected assistants.

The installer installs the `orchi` skill (its instructions, references, subagent roles, the read-only knowledge and status tools, and the installer itself) and the explicit entry skills `orchi-plan` and `orchi-deliver`. It renders the Orchi subagents for Claude Code and Codex, registers the selected assistants, and reports whether `git` and `gh` are available. It does not install or authenticate the assistants or the GitHub CLI.

Requirements: Git, the GitHub CLI (`gh`) for Issue and PR work, and Python 3.11 or newer for the bundled scripts, which use only the standard library. The npm wrapper also needs Node.js/npm and `uv`. Linux, macOS, and WSL are supported.

## Shared files and instruction discovery

One canonical copy of each skill lives in `.agents/skills/` (`orchi`, `orchi-plan`, `orchi-deliver`). Codex and Copilot discover this directory. Selecting Claude creates a relative symlink per skill at `.claude/skills/<name>`. Project links survive moving or cloning the repository on a symlink-capable filesystem.

Selection configures integrations; it is not an access restriction. An unselected assistant that already searches `.agents/skills/` may still discover the shared skills.

The installer appends an Orchi workflow section to the target root `AGENTS.md`. Its rules route implementation through the Orchi skill, require research and agreement before tracking or changes, and keep merge and deployment within the user's authority. It never copies this repository's contributor `AGENTS.md` into another project.

Additional selected-agent integration:

| Assistant | Instructions |
| --- | --- |
| Codex | Root `AGENTS.md` |
| Copilot | A managed pointer in `.github/copilot-instructions.md` directs IDE/CLI sessions to root `AGENTS.md` |
| Claude Code | A managed `@AGENTS.md` import in root `CLAUDE.md` |

Sections are delimited by `<!-- orchi:begin -->` and `<!-- orchi:end -->`. Existing content outside these markers is preserved byte-for-byte, including line endings. Reinstallation updates only an unchanged managed section and never duplicates it. Edited or malformed sections cause installation to stop before mutation, even with `--replace-orchi`; preserve custom rules outside the managed section. An existing `CLAUDE.md` symlink directly to root `AGENTS.md` is preserved. If `AGENTS.override.md` exists, its managed section is updated too so Codex does not skip the workflow.

Instruction discovery improves routing but does not prove model compliance. More specific instructions, explicit user instructions, disabled skills, instruction-size limits, and application settings can affect behavior. Start a fresh session and verify the entrypoint is exposed: `$orchi` in Codex CLI, `/orchi` in Claude Code and Copilot CLI, or the IDE's skill selection interface.

## Subagents and Codex configuration

Each role in `.agents/skills/orchi/roles/` is rendered for the selected assistants that support custom agents:

| Assistant | Files |
| --- | --- |
| Claude Code | `.claude/agents/orchi-scout.md`, `orchi-implementer.md`, `orchi-fixer.md`, `orchi-reviewer.md` |
| Codex | `.codex/agents/orchi-scout.toml`, `orchi-implementer.toml`, `orchi-fixer.toml`, `orchi-reviewer.toml`, and a managed block in `.codex/config.toml` |
| Copilot | None; Copilot follows the workflow without subagents |

Rendered agents name the installed skill as `.agents/skills/orchi` in a project installation and by its absolute path in a user-wide one. They are recorded in the manifest with their hashes: unmodified files update in place on reinstall, a locally edited or pre-existing unmanaged file needs `--replace-orchi` (which keeps a backup), and uninstalling removes them and refuses edited ones. Adding Claude Code or Codex later adds its agents. Agent files do not depend on `--github`.

For Codex, the installer appends this block to `.codex/config.toml` so Orchi subagents can start their own agents (Claude Code's default nesting depth is already 3):

```toml
# orchi:begin
# Let Orchi subagents start their own agents (Claude Code's default depth is also 3).
[agents]
max_depth = 3
# Add your own settings above this block.
# orchi:end
```

Content outside the markers is preserved byte-for-byte. The block ends inside the `[agents]` table, so a key appended after `# orchi:end` belongs to `[agents]`; keep your own settings above the block. Reinstallation refreshes an unedited block to the current version. If the file already defines an `agents` table outside the block, the installer writes no block and reports a note in `notes`: set `max_depth = 3` under your own `[agents]` table instead. A configuration file that is not valid TOML stops the installation before any change. An edited block stops installation and uninstallation, like an edited instruction section. Uninstalling removes the block, and the file too if Orchi created it and nothing else remains; a file that existed before Orchi, even an empty one, is kept. Without Codex selected, the installer does not read or change `.codex/config.toml`.

Codex loads the project's `.codex/config.toml` and `.codex/agents/` only for a trusted project: trust the project in Codex after installing. Subagent models are pinned in the roles; if a pinned model is unavailable, the main session performs the step itself.

## GitHub setup

```bash
npx --yes github:nkhus/orchi --agents all --github
```

`--github` is opt-in and applies to project installations. Once chosen, later installations keep it. It adds:

| File or resource | Purpose |
| --- | --- |
| `.github/ISSUE_TEMPLATE/orchi-initiative.yml`, `orchi-epic.yml`, `orchi-task.yml` | Issue forms that apply the matching type label; the Task, Epic, and Initiative forms have a field for every item of the [readiness checklists](../skills/orchi/references/readiness.md) |
| PR template section | Summary, Verification, Documentation impact, and Handoff, as a managed section in an existing template (`.github/pull_request_template.md` or another location GitHub reads) or a new one |
| `.github/workflows/orchi-docs.yml` | On every PR, fails on broken local links the PR introduces (`knowledge.py lint --since` the base branch) or a missing or empty Documentation impact section; omitted with `--no-docs-workflow` |
| Labels `Initiative`, `Epic`, `Task`, `in-progress` | Created with `gh` when missing; existing labels are not changed |

The template and workflow files are recorded in the manifest with their hashes, so they follow the same rules as the skill: unmodified files update in place, edited or pre-existing files need `--replace-orchi`, and uninstalling refuses edited files. Label creation needs a GitHub remote and an authenticated `gh`. If either is missing, the installation still completes and reports the error in `labels`; rerun it later to create them. Uninstalling leaves labels in place.

To skip the documentation check workflow, add `--no-docs-workflow`. The manifest records the choice (`docs_workflow`) and later installations keep it until `--docs-workflow` turns the workflow back on. Opting out removes an installed, unmodified workflow; an edited one is a conflict that needs `--replace-orchi`, which keeps a backup. Without either flag, the workflow is installed, including for manifests written before the option existed.

Broken links that already exist on the base branch are reported as pre-existing and do not fail a PR, so the workflow can be enabled in a repository with documentation debt. Run `python3 .agents/skills/orchi/scripts/knowledge.py lint` to see that debt. Make the check required in branch protection if it should block merges.

## User-wide installation

```bash
npx --yes github:nkhus/orchi --global --agents copilot claude
```

This stores the skills in `~/.agents/skills/`, adds Claude skill links in `~/.claude/skills/`, renders subagents in `~/.claude/agents/` and `~/.codex/agents/` (with the nesting block in `~/.codex/config.toml`) for the selected assistants, and installs managed instructions only for selected assistants:

| Assistant | User instructions |
| --- | --- |
| Codex | `~/.codex/AGENTS.md` |
| Copilot | `~/.copilot/copilot-instructions.md` |
| Claude Code | `~/.claude/CLAUDE.md` |

User instructions and rendered subagents reference the absolute shared skill path. No project's root files are edited in global mode. Use project installation when root `AGENTS.md` registration or team sharing is required. Global integration uses these standard home locations; custom assistant configuration roots require explicit registration in those roots. Local home files do not provision remote or cloud environments; install in each execution environment.

## Inspect, update, and remove

```bash
npx --yes github:nkhus/orchi --project "$PWD" --agents all --dry-run
npx --yes github:nkhus/orchi --project "$PWD" --agents all --replace-orchi
npx --yes github:nkhus/orchi --project "$PWD" --uninstall
```

Dry-run lists file changes and conflicts (`conflicts`, `requires_replace`) without writing. A manifest at `.agents/.orchi-install.json` records selection, hashes, links, managed files, and managed sections. Identical installation is a no-op. Rerunning the installer updates unmodified managed files. Skill files edited since installation, or unmanaged files in the Orchi destination, require `--replace-orchi`; changed files are backed up beside the project, or inside the home directory for user-wide installation. Skills, links, instructions, and manifest are staged together and rolled back on an ordinary installation error. A process or host crash during mutation requires inspecting the backup and target before retrying.

The installer refuses symlinked canonical skill destinations, unrelated conflicting skill directories, symlinked agent or configuration files it manages, and instruction symlinks other than the explicit Claude-to-AGENTS bridge. It preserves unrelated skills and agents, assistant settings, and application manifests; in `.codex/config.toml` it edits only its marked block. Do not alternate installers to manage the same installation.

`--uninstall` removes the complete managed Orchi installation at the selected project/user scope, including its instruction sections. It preserves surrounding user instructions and refuses modified skill files or managed sections. It does not remove assistant programs, authentication, GitHub Issues, branches, or backups.

Commit project skill files, Claude symlinks, rendered agents, `.codex/config.toml`, instruction changes, and the installation manifest when sharing the setup with the team.

## Local and offline installation

From a checkout:

```bash
python3 tools/install.py --project /absolute/path/to/project --agents copilot claude --dry-run
python3 tools/install.py --project /absolute/path/to/project --agents copilot claude
```

The Python installer uses only the standard library. The npm wrapper invokes the same implementation through `uv`. From an already installed bundle, add an assistant without a source checkout:

```bash
python3 .agents/skills/orchi/scripts/orchi_install.py --project "$PWD" --agents claude
```

## Upgrading

Rerun the installation command. The manifest records the installed version; `python3 .agents/skills/orchi/scripts/orchi_install.py --version` prints it with the bundled version and the upgrade command. An installed copy can add assistants but cannot fetch a newer version, so upgrades come from `npx` or a source checkout.

### From the single-skill layout

Versions 0.2.x installed only the `orchi` skill. Reinstalling adds the entry skills, the rendered subagents, and, for Codex, the `.codex/config.toml` block. A repository that added its own `.agents/skills/orchi-plan/` or `orchi-deliver/`, or its own `orchi-scout`, `orchi-implementer`, or `orchi-reviewer` agent files, gets a conflict: review the differences, move project-specific rules into the repository's own instructions (Orchi's readiness checklists apply together with any stricter project checklist), then rerun with `--replace-orchi`, which backs the files up first.

`--replace-orchi` does not resolve conflicting skill links or aliases. A real directory or a link to another target at `.claude/skills/orchi-plan` or `.claude/skills/orchi-deliver` (or `~/.claude/skills/...` user-wide), or a Copilot skill under `.github/skills/` or `~/.copilot/skills/` with one of those names, stops the installation; move or remove it by hand, then rerun. A relative symlink to `../../.agents/skills/<name>` is adopted as is.

### From the five-skill layout

Earlier versions installed `orchi-plan`, `orchi-work`, `orchi-review`, and `orchi-deliver` alongside `orchi`, plus a controller runtime. Reinstalling removes `orchi-work` and `orchi-review` and their Claude links when the manifest records them and they are unmodified, and updates unmodified `orchi-plan` and `orchi-deliver` in place to the current entry skills. Edited stage skills stop the installation until you review them and pass `--replace-orchi`, which backs them up first. Removed stage skills that the manifest does not record are left untouched. Controller state directories, operator keys, and adapter configuration live outside the installation and are not touched; remove them yourself once no longer needed.

## Upstream contracts

- [Codex skills](https://developers.openai.com/codex/skills/)
- [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Claude Code skills and symlinks](https://code.claude.com/docs/en/skills)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code imports of AGENTS.md](https://code.claude.com/docs/en/memory)
- [Copilot custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)
- [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
