# Other assistants

Orchi does not install for assistants other than Claude Code, such as Codex or
GitHub Copilot.

## Why

Orchi once installed for Codex, Copilot, and Claude Code from one shared copy of
each skill. Every target needed its own agent rendering, configuration block,
and instruction section in the installer and its tests. The maintainer chose
Claude Code as the only target.

## Instead

Orchi installs into Claude Code only. The installer migrates an older
multi-assistant installation to the Claude Code layout.

## Decided in

- [nkhus/orchi#18](https://github.com/nkhus/orchi/pull/18): Codex and Copilot
  targets were removed.
- `AGENTS.md`: do not add installation targets for other assistants.
