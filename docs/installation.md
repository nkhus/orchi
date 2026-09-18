# Installation

## Select assistants

Run the installer from the target repository. Select one or several assistants:

```bash
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot
npx --yes github:nkhus/orchi --project "$PWD" --agents copilot claude
npx --yes github:nkhus/orchi --project "$PWD" --agents all
```

`codex`, `copilot`, and `claude` are the canonical names. Comma-separated names, repeated `--agent` options, `github-copilot`, and `claude-code` also work. Without a selection, an interactive terminal offers a numbered picker. Noninteractive installation retains the existing selection or defaults to Codex. Adding an assistant preserves previously selected assistants.

The installer installs all five Orchi skills, the shared Python controller, operator tools, references, and adapter templates together. It registers the selected assistants and reports their installed executable paths or official installation links. It does not install or authenticate the assistants themselves. An IDE can consume the skills directly; automatic workers require the corresponding terminal program (`codex`, `copilot`, or `claude`).

Requirements: Git, POSIX, Python 3.11 or newer, and `uv` for the npm wrapper and isolated runtime. Node.js/npm is needed for `npx`, not for the controller. Linux, macOS, and WSL are supported; native Windows process execution is not supported.

## Shared files and instruction discovery

One canonical copy lives in `.agents/skills/`. Codex and Copilot discover this directory. Selecting Claude creates relative per-skill symlinks in `.claude/skills/`. All five directories remain siblings, including through those links. Project links survive moving or cloning the repository on a symlink-capable filesystem.

Selection configures integrations; it is not an access restriction. An unselected assistant that already searches `.agents/skills/` may still discover the shared skills.

The installer appends an Orchi workflow section to the target root `AGENTS.md`. Its rules route implementation through the Orchi entrypoint, exempt assigned packet workers from starting a coordinator, and preserve operator approvals and publication. It never copies this repository's contributor `AGENTS.md` into another project.

Additional selected-agent integration:

| Assistant | Instructions |
| --- | --- |
| Codex | Root `AGENTS.md` |
| Copilot | A managed pointer in `.github/copilot-instructions.md` directs IDE/CLI sessions to root `AGENTS.md` |
| Claude Code | A managed `@AGENTS.md` import in root `CLAUDE.md` |

Sections are delimited by `<!-- orchi:begin -->` and `<!-- orchi:end -->`. Existing content outside these markers is preserved byte-for-byte, including line endings. Reinstallation updates only an unchanged managed section and never duplicates it. Edited or malformed sections cause installation to stop before mutation, even with `--replace-orchi`; preserve custom rules outside the managed section. An existing `CLAUDE.md` symlink directly to root `AGENTS.md` is preserved. If `AGENTS.override.md` exists, its managed section is updated too so Codex does not skip the workflow.

Instruction discovery improves routing but does not prove model compliance. More specific instructions, explicit user instructions, disabled skills, instruction-size limits, and application settings can affect behavior. Start a fresh session and verify the entrypoint is exposed: `$orchi` in Codex CLI, `/orchi` in Claude Code and Copilot CLI, or the IDE's skill selection interface.

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

Dry-run lists file changes without writing. A manifest at `.agents/.orchi-install.json` records selection, hashes, links, and managed sections. Identical installation is a no-op. Differing existing skill files require `--replace-orchi`; changed files are backed up beside the project, or inside the home directory for user-wide installation. Skills, links, instructions, and manifest are staged together and rolled back on an ordinary installation error. A process or host crash during mutation requires inspecting the backup and target before retrying.

The installer refuses symlinked canonical skill destinations, unrelated conflicting skill directories, and instruction symlinks other than the explicit Claude-to-AGENTS bridge. It preserves unrelated skills, assistant settings, and application manifests. Do not alternate installers to manage the same installation.

`--uninstall` removes the complete managed Orchi installation at the selected project/user scope, including its instruction sections. It preserves surrounding user instructions and refuses modified skill files or managed sections. It does not remove assistant programs, authentication, operator keys, control stores, audit data, or backups. Stop active workers before updating or removing an installation.

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

For offline runtime provisioning, install `scripts/requirements.txt` in a dedicated managed environment through an approved package mirror. Do not add Orchi dependencies to the application's environment.

## Runtime and workers

```bash
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo . --require-agent copilot claude
uv run .agents/skills/orchi/scripts/orchi_operator.py --help
```

The runtime entrypoints declare isolated Python dependencies. The default diagnostic reports missing selected CLIs as warnings, while `--require-agent` makes absence blocking. `--require-codex` remains an alias for requiring Codex. Diagnostics inspect registrations, resources, local executables, and optional repository state; they do not verify authentication, model behavior, or isolation.

Each assistant has a bundled `assets/<agent>-adapter.json` template. Copy the chosen template into an operator-owned configuration directory and review its environment and execution permissions. Run `orchi.py --control "$ORCHI_CONTROL" run --adapter /operator/adapter.json`. Multiple installed integrations coexist; one foreground run uses one explicitly selected adapter. Installation selection does not dispatch mixed-provider workers automatically.

Installation never authorizes execution. A human operator selects trusted checks, provisions authentication and actual worker isolation, creates a protected signing key, and initializes the external control store. Continue with the bundled [operator guide](../skills/orchi/references/operator-guide.md).

## Upstream contracts

- [Codex skills](https://developers.openai.com/codex/skills/)
- [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Claude Code skills and symlinks](https://code.claude.com/docs/en/skills)
- [Claude Code imports of AGENTS.md](https://code.claude.com/docs/en/memory)
- [Copilot custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [Astral isolated script environments](https://docs.astral.sh/uv/guides/scripts/)
