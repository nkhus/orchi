# Installation

## Distribution contract

Orchi is distributed directly from its Git repository using the Agent Skills directory format. Each of its five skill directories contains `SKILL.md`; the `orchi` directory also contains the shared runtime, dependency declarations, operator tooling, references, and assets. Keep the five directories as siblings.

The primary installer is the Skills CLI. Its repository discovery and agent-specific locations are documented in [the upstream project](https://github.com/vercel-labs/skills). Orchi does not require an independently published npm or Python package. The application's language and package manager do not determine how Orchi is installed.

## Project-local installation

From the repository in which the assistant will work:

```bash
npx skills add nkhus/orchi --skill '*' --agent codex --yes
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
```

`--skill '*'` selects the complete skill set, `--agent codex` selects the agent, and the absence of `--global` keeps installation local to this project. To review the discovered skills first:

```bash
npx skills add nkhus/orchi --list
```

Review the resulting diff. Commit the installed skill files and any project-local lockfile written by the Skills CLI when the setup should be shared with the team. Orchi's own installer does not modify `AGENTS.md`, `.codex/config.toml`, application manifests, or unrelated skills. Review the behavior of any third-party installer before running it in a sensitive repository.

The [Codex skill documentation](https://developers.openai.com/codex/skills/) describes `.agents/skills` discovery. Start a fresh agent session when the current session does not expose the installed skills.

## User-wide installation

To make the same skills available across repositories on your machine:

```bash
npx skills add nkhus/orchi --skill '*' --agent codex --global --yes
uv run "$HOME/.codex/skills/orchi/scripts/orchi.py" doctor
```

The Skills CLI documents `~/.codex/skills` as its global Codex location and may link it to a shared canonical copy. Use the path printed by your installer when its configuration differs. User-wide installation is convenient for personal use; project-local installation makes the team's selected skill content explicit in Git. Avoid installing duplicate names at both scopes unless you deliberately manage the ambiguity. Global skill installation does not create a shared workflow database: each initiative still needs its own external control directory.

## Other agents

The Skills CLI can place the same instructions in other supported agents' skill locations:

```bash
npx skills add nkhus/orchi --skill '*' --agent claude-code --yes
```

Use the actual installed `orchi/scripts/orchi.py` path for commands. The CLI may use a canonical `.agents/skills` copy with agent-specific symlinks; its `--copy` option requests independent copies where needed.

Skill-format compatibility does not imply a native execution adapter for every agent. Orchi includes a Codex adapter and a generic command/manual packet protocol. Another assistant must follow that protocol, and its invocation syntax and sandbox behavior must be checked separately. All five skills are required; the Skills CLI does not install Orchi's sibling dependencies merely because `orchi` was selected.

## Python runtime

Run the installed scripts with `uv`:

```bash
uv run .agents/skills/orchi/scripts/orchi.py --help
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo . --require-codex
uv run .agents/skills/orchi/scripts/operator.py --help
```

Both entrypoints declare Python requirements and dependencies through inline script metadata. [Astral's script guide](https://docs.astral.sh/uv/guides/scripts/) explains the isolated environment: a target project's dependency set is not loaded when the script has inline metadata. Orchi does not create or modify that project's application environment. Initial execution requires access to the declared Python packages and a suitable Python interpreter; pre-provision them for restricted networks.

To select a suitable interpreter explicitly, add `--python 3.11` before the script path in `uv run`; this is useful when a local Python selection conflicts with the script requirements.

For an existing managed Python environment or offline provisioning, install the bundled requirements through your approved package mirror or wheelhouse, then use `python` directly:

```bash
python -m pip install -r .agents/skills/orchi/scripts/requirements.txt
python .agents/skills/orchi/scripts/orchi.py doctor --repo .
```

Choose a dedicated environment, not the application's environment. Orchi's dependencies do not include your project's compiler, test runner, packages, or services. Those must work inside the verification worktrees under the operator's trusted check configuration.

## Installation from a local checkout

With Node.js/npm available:

```bash
# Run in the target project; point to an existing Orchi checkout.
npx skills add /absolute/path/to/orchi --skill '*' --agent codex --yes
```

Without Node.js, run the bundled standard-library-only copying tool from an Orchi checkout:

```bash
python3 tools/install.py --project /absolute/path/to/project --dry-run
python3 tools/install.py --project /absolute/path/to/project
```

This copies the complete skill set to `.agents/skills`, verifies file hashes, and records a local installation manifest. An unchanged installation is a no-op. Conflicting Orchi files require explicit `--replace-orchi`; replaced content is backed up beside the target project. Unrelated skills are neither removed nor rewritten. Symlinked destination skill directories are refused by this copying tool; use the Skills CLI to manage its own symlinks.

## Maintenance and removal

Re-run the installation command to select the repository content again. Review and commit the diff rather than silently changing an installation used by active work. The Skills CLI also supplies management commands; consult `npx skills --help` for its supported options.

```bash
npx skills remove orchi orchi-plan orchi-work orchi-review orchi-deliver --agent codex
```

Add `--global` when removing a user-wide installation. Removing skills does not delete external audit data, operator keys, or control databases. Stop active workers and preserve required audit material before removing an installation used by an initiative.

## Operational setup

A successful installation or `doctor` result is not permission to run coding tasks. The human operator selects trusted checks, creates a protected keypair, sets `ORCHI_CONTROL`, initializes a fresh external control store, and verifies worker isolation. Continue with the bundled [operator guide](../skills/orchi/references/operator-guide.md).
