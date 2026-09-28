# Testing

## Deterministic validation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

`tools/validate_package.py` checks skill metadata (only `orchi` loads implicitly; the entry skills are explicit-only), that every subagent role renders to a Claude Code agent and a Codex agent that round-trips its instructions, local Markdown links (installed references must stay inside the bundle), Python syntax, standard-library-only installed scripts, JSON/YAML syntax, the npm publish allowlist, English-only text, and absence of product release markers.

Role tests cover rendering, TOML and YAML escaping, placeholder substitution, and rejection of malformed roles. Installer tests cover all seven assistant selections in project and user scopes, including the rendered subagents per assistant and the Codex nesting block (preserved user configuration, an existing `[agents]` table, invalid TOML, edits, and removal), additive selection, managed instruction preservation and removal, relative Claude links, rollback, backups on explicit replacement, symlink refusal, upgrade from the five-skill and single-skill layouts, and registration from an installed bundle without a source checkout. The `--github` tests cover managed template and workflow files, opting out of and back into the documentation check workflow, extending an existing PR template, conflicts, persistence, and reporting when labels cannot be created. Issue template tests check that the forms are valid with unique field ids and that every readiness checklist item maps to a Task or Epic field. Knowledge tests cover snapshot isolation, exact reads with hash checks, corpus scope, link/anchor validation, new-error-only linting against a base ref, and the documentation impact check. Status tests cover readiness classification (ready, check, blocked, claimed), standalone Task selection, ordering, and pagination against a fake `gh`.

## Installed-skill smoke test

```bash
python tools/smoke_install.py --out /tmp/orchi-installation
```

Add `--github` to also install and check the GitHub setup files and the documentation impact check; label creation reports an error in the disposable project because it has no GitHub remote. The output directory must not exist. The default `--installer npm` mode runs the npm wrapper for all three assistants in a new Git project, checks that existing user files survive, that the selected assistants received exactly the Orchi subagents and the Codex nesting block, and runs the installed knowledge tool. `--installer local` uses the Python installer directly. `--installer skills` checks the third-party Skills CLI, which does not install Orchi's managed instruction sections.

## Live behavior

Tests do not establish that an assistant follows the workflow. When changing the skill or role text, try it in a disposable repository with each supported assistant: a read-only question, a small fix, and an Epic with Tasks; in Claude Code and Codex, also `orchi-plan` and `orchi-deliver` with delegation to the subagents. Check that the assistant researches and agrees scope before creating branches or Issues, uses the right branch and label conventions, and does not merge without authority.
