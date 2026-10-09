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
| [`orchi-researcher`](orchi-researcher.md) | opus / medium | nothing |
| [`orchi-implementer`](orchi-implementer.md) | opus / low | one commit per Task |
| [`orchi-fixer`](orchi-fixer.md) | sonnet / medium | one commit per Task or repair |
| [`orchi-reviewer`](orchi-reviewer.md) | opus / high | nothing |
| [`orchi-designer`](orchi-designer.md) | opus / medium | one commit per UI Task; nothing in Audit mode |

## Choosing a writer

The main session is the only one that starts a writer, and runs one writer per
worktree at a time. Start `orchi-fixer` when the change is small and fully
determined by its Issue: a standalone Task, an Epic Task, or a confirmed review
defect whose fix is localized, whose acceptance is directly checkable, and which
needs no new contract, schema, migration, dependency, or design choice. Start
`orchi-designer` for a Task whose outcome is mainly user interface design:
layout, typography, color, motion, states, or component choice. Start
`orchi-implementer` for every other Task, standalone or in an Epic. A writer's
report is a claim; inspect its diff and check output before pushing.

A fixer `ESCALATE` report names its cause:

- `decision`: the change needs a product or design choice. Decide it yourself
  only when the user delegated it, otherwise ask; record the answer in the
  Issue's decisions, then restart a writer.
- `size`: the change is correct but larger than the fixer's scope. Restart the
  same Issue with `orchi-implementer`, or `orchi-designer` for a UI Task.

A designer `ESCALATE` is always a `decision`: it lists options and a
recommendation. Handle it like a fixer's.

## Design skills

`orchi-designer` uses the design skills installed in the project or for the
user, and works from the repository's own design system when none is. Orchi
does not install them. These are the ones it knows:

| Skill | Install | Provides |
| --- | --- | --- |
| [Impeccable](https://impeccable.style/) | `npx impeccable install` | `/impeccable` commands such as `audit`, `typeset`, `layout`, `colorize`, `animate`, `polish` |
| [Taste Skill](https://www.tasteskill.dev/) | `npx skills add Leonxlnx/taste-skill` | `design-taste-frontend` and style variants against generic interfaces |
| [SmoothUI](https://shadcnregistry.com/smoothui/skill) | `pnpm dlx shadcn@latest add "https://smoothui.dev/r/skill.json"` | Installing SmoothUI components, blocks, and themes; animation conventions (shadcn/ui projects) |

For a UI diff, the main session may also start `orchi-designer` in Audit mode
next to `orchi-reviewer`; the designer reports design and accessibility
defects, and the reviewer remains the one full review.
