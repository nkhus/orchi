# Orchi

**Turn one user request into a verified implementation through iterative epics, parallel tasks, and one final code-and-documentation publication.**

Orchi is a local orchestration workflow for coding assistants. Five focused agent skills coordinate a Python controller that records approvals, builds task packets, manages Git worktrees, executes checks, and preserves recoverable state. Codex has a built-in execution adapter; other assistants can consume the same packets through a command adapter or manual handoff.

## Install in a project

Run this from the target repository:

```bash
npx skills add nkhus/orchi --skill '*' --agent codex --yes
uv run .agents/skills/orchi/scripts/orchi.py doctor --repo .
```

Install **all five skills together**. The controller, Python dependency declarations, operator tools, references, and example templates travel with the skills. You do not need a separate Orchi clone, npm package, or Python package installation in the target project. `uv` manages Orchi's Python environment without adding dependencies to the application's environment.

Requirements: Git, a POSIX environment, and `uv`; Python 3.11 or newer is required by the scripts. Documentation search requires Python's SQLite FTS5; trigram support enables substring and fuzzy matching. Node.js/npm is needed for the `npx` installation command, not for the controller. A live Codex run also needs an installed and authenticated Codex CLI. Use Linux, macOS, or a Linux environment under WSL; native Windows execution is not supported by the process controller.

Installation does **not** authorize execution. Before starting an initiative, a human operator configures an external control directory, signing key, trusted project checks, and worker access boundaries. Follow the [operator guide](skills/orchi/references/operator-guide.md). `doctor` checks local prerequisites; it does not certify authentication or isolation.

[Installation options](docs/installation.md) cover user-wide installation, other agents, local/offline copying, and removal.

## Start a request

In a coding-agent session that has loaded the skills:

```text
$orchi Implement <the requested change>. Agree on the outcome and epic roadmap first.
Design only the next epic, then execute its approved independent tasks in parallel.
Update Core documentation only after the entire request is implemented and verified.
```

The workflow is:

```text
Understand the request and agree on direction
  -> Design and approve the next epic and its tasks
  -> Execute ready tasks in parallel; integrate verified results serially
  -> Review the combined implementation
  -> Checkpoint verified Working Knowledge
  -> Repeat for the next epic using the actual result
  -> Reconcile Core documentation for the completed request
  -> Review and approve the exact final candidate
  -> Operator publishes one code + docs + initiative archive commit
```

A small request can use one epic. Larger requests keep future epics at roadmap level instead of designing every task upfront. Material uncertainty returns to the human; normal tasks within an approved epic do not require repeated approval.

## Skills

| Skill | Responsibility |
| --- | --- |
| `orchi` | User entrypoint; route according to controller state |
| `orchi-plan` | Define the initiative; design and amend the next epic |
| `orchi-work` | Execute approved tasks through generated packets and bounded workers |
| `orchi-review` | Review exact candidates and triage bounded, causal findings |
| `orchi-deliver` | Checkpoint Working Knowledge; reconcile Core and prepare publication |

Use `$orchi` to start or continue. The other skills are explicit stages, not competing entrypoints. A packet worker follows its assigned task rather than starting another coordinator.

## Documentation during development

**Core** is the canonical `docs/` tree. It remains unchanged during intermediate epic work. **Verified Working Knowledge** is a sparse, initiative-scoped overlay describing completed, checked epics. **Proposals** describe the active epic and its tasks; they are not current system facts.

Workers receive the last knowledge checkpoint, the approved active-epic design, and actual accepted dependency results. At finalization, Orchi produces a coherent cumulative Core update and verifies the exact code-and-docs tree. It does not publish intermediate epics or automatically deploy anything.

## Search project documentation

Search committed Core without initializing an initiative (run with `ORCHI_CONTROL` unset):

```bash
uv run .agents/skills/orchi/scripts/orchi.py search "authentication callback" --repo . --format text
```

Standalone lookup defaults to `refs/heads/main`; use `--ref` for another canonical branch. For an active
initiative, use its accepted knowledge scope explicitly:

```bash
uv run .agents/skills/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" search "authentication callback" --initiative <id>
uv run .agents/skills/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" get docs/authentication.md --initiative <id> --content-hash <hash-from-hit>
```

Retrieval combines heading-aware BM25, substring matching, and typo-tolerant candidates. Hits contain
bounded snippets, exact line ranges, and source provenance. Its local SQLite index is automatically built
and disposable; Git, verified Working Knowledge, and the controller remain authoritative. Stale or retired
replacements never fall back to obsolete Core. [Retrieval](docs/retrieval.md) explains commands and limits.

## Repository layout

```text
skills/                  Installable skills, bundled runtime, references, templates
  orchi/scripts/         Controller and operator entrypoints; shared Python modules
  orchi/references/      Focused agent instructions and the installed operator guide
  orchi/assets/          Policy, adapter, and authoring examples
  orchi-*/               Planning, execution, review, and delivery skills
docs/                    Project architecture, protocols, installation, and security
schemas/                 JSON Schemas generated from the Python contracts
tests/                   Deterministic unit, integration, and packaging tests
evals/                   Model-behavior scenarios; separate from automated tests
examples/                Guide to the bundled examples and synthetic demonstration
tools/                   Repository validation, local copying, and demonstration
.github/workflows/       Continuous integration checks
```

## Develop and test

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
python tools/demo.py --out /tmp/orchi-demo
```

The demo requires a new output directory. It creates a disposable repository, synthetic workers, and a test-only signing key. Its automatic approvals are fixtures, not a production approval mechanism. No model credentials are needed for deterministic tests.

See [contributing](CONTRIBUTING.md) and [testing](docs/testing.md) for validation procedures and the distinction between protocol tests and live model evaluation.

## Documentation

| Read | For |
| --- | --- |
| [Architecture](docs/architecture.md) | Domain model, components, storage, and publication boundary |
| [Planning and task packets](docs/planning-and-packets.md) | Iterative design, context, task contracts, and parallelism |
| [Knowledge lifecycle](docs/knowledge-lifecycle.md) | Core, Working Knowledge, reconciliation, and provenance |
| [Retrieval](docs/retrieval.md) | Scoped documentation search, source-bound excerpts, and disposable indexes |
| [Protocol](docs/protocol.md) | State transitions, approvals, checks, review, and recovery |
| [Operator guide](skills/orchi/references/operator-guide.md) | End-to-end setup, approvals, execution, and publication |
| [Security](docs/security.md) | Trust boundaries and explicit operational limitations |
| [External references](docs/references.md) | Skill distribution, script dependencies, and agent documentation |

Orchi enforces mechanical acceptance conditions, not the semantic correctness of every design or document. A worktree is not a security sandbox. Keep keys, control state, and privileged operations outside worker access.
