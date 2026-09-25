# Contributing

Use English for source documentation, instructions, examples, diagnostics, and tests. Describe the implemented system directly. Keep product release labels, changelogs, historical design comparisons, and generated logs out of the source package.

## Development environment

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

The repository is a skill distribution with a dependency-free npm installation wrapper, not a Python application package. `pyproject.toml` contains test configuration only.

## Source ownership

Everything needed after installation lives in `skills/orchi/`: `SKILL.md`, `references/`, `agents/openai.yaml`, the GitHub setup files in `assets/github/`, the read-only tools `scripts/knowledge.py` and `scripts/status.py`, and the installer in `scripts/orchi_core/`. Keep `VERSION` in `orchi_core/agents.py` equal to the `package.json` version. Root `docs/`, `tests/`, and `tools/` serve contributors; installed files must not rely on them.

Keep `SKILL.md` to routing and core rules (at most 100 lines, enforced by validation) and give each detailed rule exactly one home in a reference; link instead of repeating. Keep references free of project-specific paths, commands, and tools; a target repository's own instructions take precedence and supply those.

## Behavioral changes

Preserve research-and-agree before tracking, proportional scope, GitHub Issues as shared state, documentation alongside code, bounded review, and user-controlled merge. A claimed installer or tool invariant needs a meaningful test. A skill-text change needs a try-out with each supported assistant in a disposable repository; see [testing](docs/testing.md).

## Before committing

Run source validation and the full test suite, then run `python tools/smoke_install.py --out <new directory>`. Keep caches, environments, and generated reports out of the commit.
