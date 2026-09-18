# Installation

## Distribution contract

Orchi is distributed directly from its Git repository using the Agent Skills directory format. Each of its five skill directories contains `SKILL.md`; the `orchi` directory also contains the shared runtime, dependency declarations, operator tooling, references, and assets. Keep the five directories as siblings.

The repository includes a dependency-free npm wrapper that installs the complete bundle locally without changing the target application's dependencies. The installed runtime is Python and does not depend on Node or a separately published Python application package.

## Project-local installation

From the repository in which the assistant will work:

```bash
npx --yes github:nkhus/orchi --project "$PWD"
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
```

To inspect the operation first, use the bundled installer's dry-run mode from a checkout:

```bash
python3 tools/install.py --project /absolute/path/to/project --dry-run
```

Review the resulting diff. Commit the installed skill files and any project-local lockfile written by the Skills CLI when the setup should be shared with the team. Orchi's own installer does not modify `AGENTS.md`, `.codex/config.toml`, application manifests, or unrelated skills. Review the behavior of any third-party installer before running it in a sensitive repository.

The [Codex skill documentation](https://developers.openai.com/codex/skills/) describes `.agents/skills` discovery. Start a fresh agent session when the current session does not expose the installed skills.

## Other installation locations

The installer targets a project's `.agents/skills` directory. For a user-wide or another agent-specific installation, copy all five sibling directories to that agent's documented skill location and run `doctor` from the actual installed path. Skill-format compatibility does not imply a native execution adapter: Orchi includes a Codex adapter and a generic command/manual packet protocol.

## Python runtime

Run the installed scripts with `uv`:

```bash
uv run .agents/skills/orchi/scripts/orchi.py --help
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo . --require-codex
uv run .agents/skills/orchi/scripts/orchi_operator.py --help
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
npx --yes /absolute/path/to/orchi --project "$PWD"
```

Without Node.js, run the bundled standard-library-only copying tool from an Orchi checkout:

```bash
python3 tools/install.py --project /absolute/path/to/project --dry-run
python3 tools/install.py --project /absolute/path/to/project
```

This copies the complete skill set to `.agents/skills`, verifies file hashes, and records a local installation manifest. An unchanged installation is a no-op. Conflicting Orchi files require explicit `--replace-orchi`; replaced content is backed up beside the target project. Unrelated skills are neither removed nor rewritten. Symlinked destination skill directories are refused by this copying tool; use the Skills CLI to manage its own symlinks.

## Maintenance and removal

Re-run the installation command with `--replace-orchi` to replace a differing installation after reviewing it; the installer keeps a backup. Removing the five installed skill directories does not delete external audit data, operator keys, or control databases. Stop active workers and preserve required audit material before removing an installation used by an initiative.

## Operational setup

A successful installation or `doctor` result is not permission to run coding tasks. The human operator selects trusted checks, creates a protected keypair, sets `ORCHI_CONTROL`, initializes a fresh external control store, and verifies worker isolation. Continue with the bundled [operator guide](../skills/orchi/references/operator-guide.md).
