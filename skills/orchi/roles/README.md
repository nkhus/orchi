# Orchi subagent roles

Each `orchi-*.md` file defines one subagent once for Claude Code and Codex: TOML
front matter between `+++` lines (`name`, `description`, `[claude]` `model`,
`effort`, `tools`, and `[codex]` `model`, `model_reasoning_effort`), then the
instructions. The installer renders them to `.claude/agents/<name>.md` when Claude
Code is selected and `.codex/agents/<name>.toml` when Codex is selected. Rendered
files are managed: reinstall to update them instead of editing them.

Instructions write the installed Orchi skill directory as `{{ORCHI_SKILL}}`. The
installer substitutes `.agents/skills/orchi` for a project installation and the
absolute skill path for a user-wide one. No other `{{NAME}}` placeholder is
allowed.

| Agent | Claude model / effort | Codex model / effort | Writes |
| --- | --- | --- | --- |
| [`orchi-scout`](orchi-scout.md) | haiku / medium | gpt-6-luna / medium | nothing |
| [`orchi-implementer`](orchi-implementer.md) | opus / low | gpt-6-sol / low | one commit per Task |
| [`orchi-reviewer`](orchi-reviewer.md) | opus / high | gpt-6-sol / medium | nothing |
