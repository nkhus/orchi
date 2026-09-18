"""Assistant identities shared by installation, diagnostics, and worker execution."""
from __future__ import annotations

AGENTS = {
    "codex": {"executable": "codex", "install_url": "https://developers.openai.com/codex/cli/"},
    "copilot": {"executable": "copilot", "install_url": "https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli"},
    "claude": {"executable": "claude", "install_url": "https://code.claude.com/docs/en/setup"},
}
ALIASES = {"github-copilot": "copilot", "claude-code": "claude"}
SKILLS = ("orchi", "orchi-plan", "orchi-work", "orchi-review", "orchi-deliver")


def agent_names(values: list[str] | tuple[str, ...]) -> list[str]:
    names = set()
    for value in values:
        for item in value.split(","):
            name = ALIASES.get(item.strip(), item.strip())
            if name == "all":
                names.update(AGENTS)
            elif name in AGENTS:
                names.add(name)
            else:
                raise ValueError("Unknown assistant: " + name + "; choose codex, copilot, claude, or all")
    if not names:
        raise ValueError("Select at least one assistant")
    return [name for name in AGENTS if name in names]
