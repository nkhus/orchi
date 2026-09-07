# Working on the Orchi repository

This file governs contributions to Orchi itself. Installation must not copy it over another project's `AGENTS.md`.

Read `README.md` and the documentation for the component being changed. Use English and describe current behavior without release narratives. Keep skills concise and shared code in `skills/orchi/scripts/orchi_core/`; installed resources must not depend on repository-root tools or documentation.

Preserve iterative epic planning, designed task packets, exact approvals, bounded execution/review, final-only Core reconciliation, and operator-controlled publication. Do not silently weaken a gate to make a test pass. Update documentation only where the mechanism or contract changes.

Validate with `python tools/validate_package.py` and `python -m pytest -q` in the development environment. Regenerate schemas after model changes. Use disposable repositories and test-only keys; never apply demo auto-approvals to real work. Do not claim that deterministic tests establish live model behavior.
