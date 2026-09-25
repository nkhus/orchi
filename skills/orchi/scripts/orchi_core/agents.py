"""Assistant identities and skill names shared by installation."""
from __future__ import annotations

AGENTS = ("codex", "copilot", "claude")
ALIASES = {"github-copilot": "copilot", "claude-code": "claude"}
SKILLS = ("orchi",)
# Stage skills from the former controller workflow; removed on upgrade when unmodified.
LEGACY_SKILLS = ("orchi-plan", "orchi-work", "orchi-review", "orchi-deliver")


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
