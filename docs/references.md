# External references

The sources below describe external standards and tools used by Orchi. Orchi's own behavioral contracts are defined by its code, schemas, skills, and project documentation.

| Source | Relevance |
| --- | --- |
| [OntoShip](https://github.com/vakovalskii/ontoship) | Markdown-first, disposable, heading-aware lexical retrieval patterns |
| [SQLite FTS5](https://www.sqlite.org/fts5.html) | BM25, Unicode tokenization, trigram substring matching, and MATCH syntax |
| [Agent Skills specification](https://agentskills.io/specification) | `SKILL.md` metadata, directory structure, scripts, references, and assets |
| [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Self-contained script dependencies and inline Python metadata |
| [Skills CLI](https://github.com/vercel-labs/skills) | Git repository installation, project/user scope, agent selection, and copy/symlink handling |
| [Vercel agent-skill guide](https://vercel.com/kb/guide/agent-skills-creating-installing-and-sharing-reusable-agent-context) | Publishing and sharing skills through a repository |
| [Codex skills](https://developers.openai.com/codex/skills/) | Local skill discovery and agent-specific interface metadata |
| [GitHub Copilot agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | Shared skill-format support and portability boundaries |
| [Astral: running scripts](https://docs.astral.sh/uv/guides/scripts/) | `uv run`, inline dependency declarations, and isolation from project dependencies |
| [Codex non-interactive execution](https://developers.openai.com/codex/noninteractive/) | Structured output and automated CLI execution |
| [Codex CLI reference](https://developers.openai.com/codex/cli/reference/) | Supported execution flags and operator configuration |
| [Codex security](https://developers.openai.com/codex/security/) | Sandbox and approval configuration |

Orchi's distribution uses the standard `skills/` layout and repository-based installation. Its executable scripts declare their dependencies rather than assuming the consuming project is a Python package. The bundled runtime remains local; skill-format support by an agent does not establish a native execution adapter or a verified sandbox for that agent.

Review upstream documentation when preparing an execution environment. Tool flags, installation behavior, and agent integration can change independently of the repository's source contracts.
