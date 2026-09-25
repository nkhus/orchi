# Installation

## Select assistants

Run the installer from the target repository. Select one or several assistants:

```bash
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot claude
npx --yes github:nkhus/orchi --project "$PWD" --agents all
```

`codex`, `copilot`, and `claude` are the canonical names. Comma-separated names, repeated `--agent` options, `github-copilot`, and `claude-code` also work. Without a selection, an interactive terminal offers a numbered picker. Noninteractive installation retains the existing selection or defaults to Codex. Adding an assistant preserves previously selected assistants.

The installer installs the single `orchi` skill: its instructions, references, the read-only knowledge tool, and the installer itself. It registers the selected assistants and reports whether `git` and `gh` are available. It does not install or authenticate the assistants or the GitHub CLI.

Requirements: Git, the GitHub CLI (`gh`) for Issue and PR work, and Python 3.11 or newer for the bundled scripts, which use only the standard library. The npm wrapper also needs Node.js/npm and `uv`. Linux, macOS, and WSL are supported.

## Shared files and instruction discovery

One canonical copy lives in `.agents/skills/orchi/`. Codex and Copilot discover this directory. Selecting Claude creates a relative symlink at `.claude/skills/orchi`. Project links survive moving or cloning the repository on a symlink-capable filesystem.

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

## GitHub setup

```bash
npx --yes github:nkhus/orchi --agents all --github
```

`--github` is opt-in and applies to project installations. Once chosen, later installations keep it. It adds:

| File or resource | Purpose |
| --- | --- |
| `.github/ISSUE_TEMPLATE/orchi-initiative.yml`, `orchi-epic.yml`, `orchi-task.yml` | Issue forms that apply the matching type label |
| PR template section | Summary, Verification, Documentation impact, and Handoff, as a managed section in an existing template (`.github/pull_request_template.md` or another location GitHub reads) or a new one |
| `.github/workflows/orchi-docs.yml` | On every PR, runs `knowledge.py lint` and fails when the Documentation impact section is missing or empty |
| Labels `Initiative`, `Epic`, `Task`, `in-progress` | Created with `gh` when missing; existing labels are not changed |

The template and workflow files are recorded in the manifest with their hashes, so they follow the same rules as the skill: unmodified files update in place, edited or pre-existing files need `--replace-orchi`, and uninstalling refuses edited files. Label creation needs a GitHub remote and an authenticated `gh`. If either is missing, the installation still completes and reports the error in `labels`; rerun it later to create them. Uninstalling leaves labels in place.

The workflow lints every project Markdown file, so enabling it in a repository with existing broken links fails until they are fixed. Run `python3 .agents/skills/orchi/scripts/knowledge.py lint` first to see what it reports. Make the check required in branch protection if it should block merges.

## User-wide installation

```bash
npx --yes github:nkhus/orchi --global --agents copilot claude
```

This stores one bundle in `~/.agents/skills/`, adds Claude skill links in `~/.claude/skills/`, and installs managed instructions only for selected assistants:

| Assistant | User instructions |
| --- | --- |
| Codex | `~/.codex/AGENTS.md` |
| Copilot | `~/.copilot/copilot-instructions.md` |
| Claude Code | `~/.claude/CLAUDE.md` |

User instructions reference the absolute shared skill path. No project's root files are edited in global mode. Use project installation when root `AGENTS.md` registration or team sharing is required. Global integration uses these standard home locations; custom assistant configuration roots require explicit registration in those roots. Local home files do not provision remote or cloud environments; install in each execution environment.

## Inspect, update, and remove

```bash
npx --yes github:nkhus/orchi --project "$PWD" --agents all --dry-run
npx --yes github:nkhus/orchi --project "$PWD" --agents all --replace-orchi
npx --yes github:nkhus/orchi --project "$PWD" --uninstall
```

Dry-run lists file changes and conflicts (`conflicts`, `requires_replace`) without writing. A manifest at `.agents/.orchi-install.json` records selection, hashes, links, and managed sections. Identical installation is a no-op. Rerunning the installer updates unmodified managed files. Skill files edited since installation, or unmanaged files in the Orchi destination, require `--replace-orchi`; changed files are backed up beside the project, or inside the home directory for user-wide installation. Skills, links, instructions, and manifest are staged together and rolled back on an ordinary installation error. A process or host crash during mutation requires inspecting the backup and target before retrying.

The installer refuses symlinked canonical skill destinations, unrelated conflicting skill directories, and instruction symlinks other than the explicit Claude-to-AGENTS bridge. It preserves unrelated skills, assistant settings, and application manifests. Do not alternate installers to manage the same installation.

`--uninstall` removes the complete managed Orchi installation at the selected project/user scope, including its instruction sections. It preserves surrounding user instructions and refuses modified skill files or managed sections. It does not remove assistant programs, authentication, GitHub Issues, branches, or backups.

Commit project skill files, Claude symlinks, instruction changes, and the installation manifest when sharing the setup with the team.

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

### From the five-skill layout

Earlier versions installed `orchi-plan`, `orchi-work`, `orchi-review`, and `orchi-deliver` alongside `orchi`, plus a controller runtime. Reinstalling removes those stage skills and their Claude links when the manifest records them and they are unmodified. Edited stage skills stop the installation until you review them and pass `--replace-orchi`, which backs them up first. Stage skills that the manifest does not record are left untouched. Controller state directories, operator keys, and adapter configuration live outside the installation and are not touched; remove them yourself once no longer needed.

## Upstream contracts

- [Codex skills](https://developers.openai.com/codex/skills/)
- [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Claude Code skills and symlinks](https://code.claude.com/docs/en/skills)
- [Claude Code imports of AGENTS.md](https://code.claude.com/docs/en/memory)
- [Copilot custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)
- [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
