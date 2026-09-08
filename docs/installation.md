---
kind: guide
area: orchi
artifacts:
  - tools/install.py
  - tools/smoke_install.py
  - skills/orchi/scripts/orchi.py
  - skills/orchi/scripts/operator.py
relations:
  part_of: [docs/README.md]
---
# Installation


## Complete skill bundle

Install all five sibling directories: `orchi`, `orchi-plan`, `orchi-work`, `orchi-review`, `orchi-deliver`. `orchi` contains the shared runtime, operator tooling, references and assets. The npm package is an installation wrapper, not the Orchi runtime. The receiving project's language and package manager do not determine the Orchi runtime.

Install the bundle with the dependency-free npm wrapper:

```bash
npx --yes github:nkhus/orchi --project /absolute/path/to/project
python -m pip install -r /absolute/path/to/project/.agents/skills/orchi/scripts/requirements.txt
python /absolute/path/to/project/.agents/skills/orchi/scripts/orchi.py doctor --repo /absolute/path/to/project
```

Omit `--project` to install into the current directory. `--dry-run` previews the operation. `--replace-orchi` explicitly backs up and replaces differing Orchi skill directories. The npm package has no dependencies or lifecycle installation scripts; it invokes the bundled Python copy installer and does not modify the consuming project's package metadata.

For a source checkout or an offline archive, invoke the same installer directly:

```bash
python /absolute/path/to/orchi/tools/install.py --project /absolute/path/to/project
```

Provision Python dependencies in a dedicated environment or approved wheelhouse, not by changing application dependencies. The copy installer preserves existing project instructions, configuration and unrelated skills, refuses symlink installation paths, and refuses silent overwrite of modified Orchi skills. Review the resulting diff before committing installed skills.

The Skills CLI can also discover the source directory:

```bash
npx skills add /absolute/path/to/orchi --skill '*' --agent codex --yes
```

Use the printed installation directory for commands; a third-party installer may choose canonical copies and agent-specific links. A repository locator can replace the local path when it refers to the exact source content you intend to install. The ZIP itself does not update or publish a remote repository.

## Isolated script runtime

The controller and operator entrypoints carry inline Python dependency metadata. The ticket worker helper uses the provisioned interpreter and only the standard library. With a provisioned `uv` installation:

```bash
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
uv run .agents/skills/orchi/scripts/operator.py --help
```

The scripts require Python 3.11+, Git, POSIX process support and the pinned dependencies in `scripts/requirements.txt`. FTS5 is required for search; optional trigram support adds substring/fuzzy retrieval. Node/npm is needed only for npm or Skills CLI installation, not controller execution. A live Codex adapter additionally needs the actual CLI, authentication and an operator-validated isolation policy.

A managed Python environment with the bundled requirements can run `python <installed-script>` directly. Orchi does not install target-project build/test dependencies, initialize services or certify authentication. `doctor --require-codex` checks executable availability, not a live model call.

## Initialize authority, not invented implementation

Installation alone does not authorize execution. The operator configures an external controller directory, signing key and trusted check policy; follow the installed [operator guide](../skills/orchi/references/operator-guide.md). Keep private keys and canonical write permissions outside worker access.

A new repository requires a canonical branch with a baseline commit. An intentionally empty Git commit is sufficient for greenfield when policy prerequisites are valid. There is no need to create fake Core architecture first. For existing unstructured docs, use the installed [bootstrap procedure](../skills/orchi/references/bootstrap.md).

## Verification and removal

Run `python tools/smoke_install.py --installer local --runner python --out /new/disposable/path` from a provisioned source checkout to verify the copied runtime against an unrelated application environment. The smoke exercises schema export, Current/Target retrieval, exact reads, graph/map/lint/coverage and synthetic approval in a disposable project.

To remove a local installation, remove only the five Orchi skill directories or use the installer that placed them. Inspect links and lockfiles before removal; do not delete unrelated skills, project instructions, controller audit data or Git metadata. Each initiative uses its own external control directory even with user-wide skill installation.
