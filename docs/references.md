# External references

The sources below describe external standards and tools used by Orchi. Orchi's own behavior is defined by its skill and installer.

| Source | Relevance |
| --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) | `SKILL.md` metadata, directory structure, scripts, references, and assets |
| [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Self-contained bundled scripts |
| [Skills CLI](https://github.com/vercel-labs/skills) | Git repository installation, project/user scope, and copy/symlink handling |
| [Vercel agent-skill guide](https://vercel.com/kb/guide/agent-skills-creating-installing-and-sharing-reusable-agent-context) | Publishing and sharing skills through a repository |
| [Claude Code skills](https://code.claude.com/docs/en/skills) | Skill discovery and invocation |
| [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) | Subagent definitions, models, and nesting |
| [Claude Code memory](https://code.claude.com/docs/en/memory) | `CLAUDE.md` instruction discovery |
| [Hallmark](https://github.com/Nutlope/hallmark) | One of the two design skills Orchi installs; strongest on pages that are read |
| [prototype](https://github.com/emilkowalski/skills) (Emil Kowalski) | One of the two design skills Orchi installs; builds divergent variants behind a picker, strongest on screens that are worked in |
| [SmoothUI](https://smoothui.dev/) | Animated React components a project's stack may name; added through the shadcn CLI or MCP server |
| [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/) | An agent-first codebase: rules enforced by structural tests and lint rules, the repository as the agents' memory, recurring cleanup of drift |
| [GitHub rulesets](https://docs.github.com/en/rest/repos/rules) | The ruleset `standards.py ruleset` prints for required checks |
| [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) | Native Initiative/Epic/Task hierarchy |
| [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) | Native `blocked by` relationships between Epics |

Orchi's distribution uses the standard `skills/` layout and repository-based installation. Bundled scripts use only the Python standard library. Review upstream documentation periodically: skill discovery, instruction files, and GitHub relationship support can change independently of this repository.
