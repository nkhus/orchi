# Working on the Orchi repository

This file governs contributions to Orchi itself. Installation must not copy it over another project's `AGENTS.md`.

Read `README.md` and the documentation for the component being changed. Use English and describe current behavior without release narratives. Keep the skill concise: `SKILL.md` holds the workflow, `references/` hold stage guidance, and installed resources must not depend on repository-root tools or documentation. Bundled scripts use only the Python standard library.

Preserve the core flow: research and agree scope with the user before tracking or changes; proportional Task/Epic/Initiative scope; Git branches and GitHub Issues as the only shared state; documentation updated with the code; one full review with targeted follow-up; merge and deployment within the user's authority. Do not reintroduce a controller, state database, approval receipts, or mandatory command facades. Repository instructions in a target project take precedence over Orchi's defaults; keep project-specific paths and tools out of the skill.

Keep Codex, Copilot, and Claude Code installation support working together. Validate with `python tools/validate_package.py` and `python -m pytest -q`. Do not claim that deterministic tests establish live model behavior.
