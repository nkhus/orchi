# Testing

## Deterministic validation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

`tools/validate_package.py` checks skill metadata (only `orchi` loads implicitly; the entry skills are explicit-only), that every subagent role renders to a Claude Code agent that carries its instructions, local Markdown links and their heading anchors through the `knowledge.py` lint (installed references must stay inside the bundle), Python syntax, standard-library-only installed scripts, JSON/YAML syntax, the npm publish allowlist (every file the installer copies must match a `files` entry, every entry must match a file, and nothing else is published), English-only text, and absence of product release markers. The CI workflow in `.github/workflows/ci.yml` runs this validation, the test suite, and `knowledge.py lint` on every pull request and every push to main; it belongs to this repository and is not installed.

Role tests cover rendering, YAML escaping, placeholder substitution, and rejection of malformed roles. Installer tests cover project and user scopes with the rendered subagents, managed instruction preservation and removal, a `CLAUDE.md` link to `AGENTS.md`, rollback, backups on explicit replacement, symlink refusal, migration from the shared multi-assistant layout (skills, links, instruction sections, Codex agents and configuration, edits, and direct removal), and reinstallation from an installed bundle without a source checkout. The `--github` tests cover managed template and workflow files, opting out of and back into the documentation check workflow, extending an existing PR template, conflicts, persistence, and reporting when labels cannot be created. Issue template tests check that the forms are valid with unique field ids and that every readiness checklist item maps to a Task, Epic, or Initiative field. Packaging tests prove, on a disposable copy of the source, that a renamed heading and an installed file missing from the npm `files` list fail validation, and, when npm is available, that `npm pack --dry-run` publishes exactly the files validation expects. Knowledge tests cover snapshot isolation, exact reads with hash checks, corpus scope, link/anchor validation, new-error-only linting against a base ref, and the documentation impact check. Status tests cover readiness classification (ready, check, blocked, claimed), standalone Task selection, ordering, and pagination against a fake `gh`.

## Installed-skill smoke test

```bash
python tools/smoke_install.py --out /tmp/orchi-installation
```

Add `--github` to also install and check the GitHub setup files and the documentation impact check; label creation reports an error in the disposable project because it has no GitHub remote. The output directory must not exist. The default `--installer npm` mode runs the npm wrapper in a new Git project, checks that existing user files (including an `AGENTS.md`) survive, that `.claude/agents/` received exactly the Orchi subagents and nothing was written outside Claude Code locations, and runs the installed knowledge tool. `--installer local` uses the Python installer directly. `--installer skills` checks the third-party Skills CLI, which does not install Orchi's managed instruction sections.

## Live behavior

Tests do not establish that Claude Code follows the workflow. When changing the skill or role text, try it in a disposable repository: a read-only question, a small fix, an Epic with Tasks, and `orchi-plan` and `orchi-deliver` with delegation to the subagents. Check that the assistant researches and agrees scope before creating branches or Issues, uses the right branch and label conventions, and does not merge without authority.
