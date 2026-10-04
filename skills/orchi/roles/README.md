# Orchi subagent roles

Each `orchi-*.md` file defines one Claude Code subagent: TOML front matter
between `+++` lines (`name`, `description`, and `[claude]` `model`, `effort`,
`tools`), then the instructions. The installer renders them to
`.claude/agents/<name>.md`. Rendered files are managed: reinstall to update them
instead of editing them.

Instructions write the installed Orchi skill directory as `{{ORCHI_SKILL}}`. The
installer substitutes `.claude/skills/orchi` for a project installation and the
absolute skill path for a user-wide one. No other `{{NAME}}` placeholder is
allowed.

| Agent | Model / effort | Writes |
| --- | --- | --- |
| [`orchi-scout`](orchi-scout.md) | haiku / medium | nothing |
| [`orchi-implementer`](orchi-implementer.md) | opus / low | one commit per Task |
| [`orchi-fixer`](orchi-fixer.md) | sonnet / medium | one commit per Task or repair |
| [`orchi-reviewer`](orchi-reviewer.md) | opus / high | nothing |

## Choosing a writer

The main session is the only one that starts a writer, and runs one writer per
worktree at a time. Start `orchi-fixer` when the change is small and fully
determined by its Issue: a standalone Task, an Epic Task, or a confirmed review
defect whose fix is localized, whose acceptance is directly checkable, and which
needs no new contract, schema, migration, dependency, or design choice. Start
`orchi-implementer` for every other Task, standalone or in an Epic. Either
writer's report is a claim; inspect its diff and check output before pushing.

A fixer `ESCALATE` report names its cause:

- `decision`: the change needs a product or design choice. Decide it yourself
  only when the user delegated it, otherwise ask; record the answer in the
  Issue's decisions, then restart a writer.
- `size`: the change is correct but larger than the fixer's scope. Restart the
  same Issue with `orchi-implementer`.
