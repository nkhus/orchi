# Orchi subagent roles

Each `orchi-*.md` file defines one Claude Code subagent: TOML front matter
between `+++` lines (`name`, `description`, and `[claude]` `model`, `effort`,
`tools`), then the instructions. The installer renders them to
`.claude/agents/<name>.md`. Rendered files are managed: reinstall to update them
instead of editing them.

Instructions write the installed Orchi skill directory as `{{ORCHI_SKILL}}`. The
installer substitutes `.claude/skills/orchi-core` for a project installation and the
absolute skill path for a user-wide one. No other `{{NAME}}` placeholder is
allowed.

| Agent | Model / effort | Writes |
| --- | --- | --- |
| [`orchi-scout`](orchi-scout.md) | haiku / medium | nothing |
| [`orchi-researcher`](orchi-researcher.md) | opus / medium | nothing |
| [`orchi-implementer`](orchi-implementer.md) | opus / low | one commit per run |
| [`orchi-fixer`](orchi-fixer.md) | sonnet / medium | one commit per run (Task or repair) |
| [`orchi-reviewer`](orchi-reviewer.md) | opus / high | nothing |
| [`orchi-designer`](orchi-designer.md) | opus / medium | one commit per UI Task run; nothing in Audit mode |

## Choosing a writer

The main session is the only one that starts a writer, and runs one writer per
worktree at a time. Start `orchi-fixer` when the change is small and fully
determined by its Issue: a standalone Task, an Epic Task, or a confirmed review
defect whose fix is localized, whose acceptance is directly checkable, and which
needs no new contract, schema, migration, dependency, or design choice. Start
`orchi-designer` for a Task whose outcome is mainly user interface design
(layout, typography, color, motion, states, or component choice) and for every
Task that builds against a surface brief or an approved comp. Start
`orchi-implementer` for every other Task, standalone or in an Epic. A writer's
report is a claim; inspect its diff and check output before pushing.

A fixer `ESCALATE` report names its cause:

- `decision`: the change needs a product or design choice. Decide it yourself
  only when the user delegated it, otherwise ask; record the answer in the
  Issue's decisions, then continue the writer with the answer.
- `size`: the change is correct but larger than the fixer's scope. Restart the
  same Issue with `orchi-implementer`, or `orchi-designer` for a UI Task; for a
  repair, first reopen the owning Task (or create a repair Task) with the
  defect in its requirements.

A designer `ESCALATE` is always a `decision`: it lists options and a
recommendation. Handle it like a fixer's, except that a direction, a comp, or a
generated asset goes to the user whatever they delegated and whatever the
autonomy level.

## Continue a writer

When a writer's own Task needs more work in the same delivery — the answer to
its `NOT READY`, `BLOCKED`, or `ESCALATE` (`decision`) report, or a confirmed
defect in its result — continue that writer instead of starting a new one: send
the answer or the defect, as the Issue now records it, with `SendMessage` to the
agent ID its start returned. It keeps the context it already built and adds a
commit on the same branch. Start a new writer when the old one cannot be
continued (its agent ID is gone after compaction or in a resumed session), when
the work belongs to another role (a `size` escalation), or when the Task
[changed course](../references/execution.md#change-course).

## Design skills

Orchi designs with one engine, [Impeccable](https://impeccable.style/), which
its installer installs at a pinned version without hooks. Its steps split by
who can take them:

| Steps | Who runs them |
| --- | --- |
| `init` (`PRODUCT.md`), `document`, `shape`, the direction round, and comp and asset approval | The session that talks to the user: the main session, or a researcher, planner, or designer crew |
| Builds from an approved comp or a direction contract, the focused commands (`layout`, `typeset`, `colorize`, `animate`, `adapt`, `clarify`, `harden`), `polish`, the finish reviewer, and the documenter (`DESIGN.md`) | `orchi-designer` in Task mode |
| `audit`, `critique`, and `detect` | `orchi-designer` in Audit mode, and the `--github` design workflow |

`orchi-designer` never asks the user: what Impeccable would ask it returns as
`ESCALATE`. [SmoothUI](https://smoothui.dev/), a library of animated React
components, is a component source rather than a design skill: where
`PRODUCT.md` or `DESIGN.md` names it (React with Tailwind CSS 4 and shadcn/ui),
the designer adds its components through the shadcn CLI or MCP server and
restyles them with the project's tokens.

For a UI diff, the main session may also start `orchi-designer` in Audit mode
next to `orchi-reviewer`; the designer reports design and accessibility
defects, and the reviewer remains the one full review.
