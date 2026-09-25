# External references

The sources below describe external standards and tools used by Orchi. Orchi's own behavior is defined by its skill and installer.

| Source | Relevance |
| --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) | `SKILL.md` metadata, directory structure, scripts, references, and assets |
| [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Self-contained bundled scripts |
| [Skills CLI](https://github.com/vercel-labs/skills) | Git repository installation, project/user scope, agent selection, and copy/symlink handling |
| [Vercel agent-skill guide](https://vercel.com/kb/guide/agent-skills-creating-installing-and-sharing-reusable-agent-context) | Publishing and sharing skills through a repository |
| [Codex skills](https://developers.openai.com/codex/skills/) | Local skill discovery and agent-specific interface metadata |
| [GitHub Copilot agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | Shared skill-format support and portability boundaries |
| [Claude Code skills](https://code.claude.com/docs/en/skills) | Skill discovery, invocation, and directory symlinks |
| [Claude Code memory](https://code.claude.com/docs/en/memory) | Shared AGENTS.md imports through CLAUDE.md |
| [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) | Native Initiative/Epic/Task hierarchy |
| [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) | Native `blocked by` relationships between Epics |

Orchi's distribution uses the standard `skills/` layout and repository-based installation. Bundled scripts use only the Python standard library. Review upstream documentation periodically: skill discovery, instruction files, and GitHub relationship support can change independently of this repository.
