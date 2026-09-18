"""Read-only checks for a complete skill installation and local prerequisites."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .retrieval import capabilities
from .agents import AGENTS, SKILLS, agent_names
from .installation import START, END, safe_destination


def doctor(repo: str | None = None, require_codex: bool = False, require_agents: list[str] | None = None) -> dict:
    """Inspect prerequisites without creating a repository, key, or control store.

    This reports executable availability, not authentication or sandbox strength.
    Paths are returned so an operator can diagnose a partial installation.
    """
    root = Path(__file__).resolve().parents[2]
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    add("platform", os.name == "posix", "POSIX process groups are required")
    add("python", sys.version_info >= (3, 11), sys.executable)
    git = shutil.which("git")
    add("git", git is not None, git or "Install Git and make it available on PATH")
    search_caps = capabilities()
    add("sqlite:fts5", search_caps["fts5"], "SQLite FTS5 is required for documentation search")
    for module in ("pydantic", "cryptography", "yaml"):
        add("dependency:" + module, importlib.util.find_spec(module) is not None, module)
    for name in SKILLS:
        add("skill:" + name, (root.parent / name / "SKILL.md").is_file(), str(root.parent / name))
    for relative in ("scripts/orchi_operator.py", "scripts/orchi_install.py", "scripts/requirements.txt", "references/operator-guide.md",
                     *(f"assets/{name}-adapter.json" for name in AGENTS)):
        add("resource:" + relative, (root / relative).is_file(), str(root / relative))
    if repo is not None:
        try:
            if git is None:
                raise ValueError("Git is not available")
            result = subprocess.run(
                [git, "rev-parse", "--show-toplevel"], cwd=Path(repo),
                capture_output=True, text=True, timeout=10, check=False,
            )
            add("repository", result.returncode == 0, result.stdout.strip() or result.stderr.strip())
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            add("repository", False, str(exc))
    warnings = ["This check does not verify authentication, trusted policy, worker isolation, or model behavior."]
    required = agent_names([*(require_agents or []), *(["codex"] if require_codex else [])]) if require_agents or require_codex else []
    selected = []
    # Registrations are optional for third-party copying tools, but must be intact when present.
    installation_root = root.parents[2]
    manifest_path = installation_root / ".agents/.orchi-install.json"
    if root.parent.name == "skills" and root.parent.parent.name == ".agents" and manifest_path.exists():
        try:
            safe_destination(installation_root, ".agents/.orchi-install.json")
            manifest = json.loads(manifest_path.read_text())
            selected = agent_names(manifest.get("agents", ["codex"]))
            for name in selected:
                if name == "claude":
                    for skill in SKILLS:
                        link = installation_root / ".claude/skills" / skill
                        add("registration:claude:" + skill, link.is_symlink() and link.resolve() == root.parent / skill, str(link))
            for relative, section in manifest.get("instructions", {}).items():
                target = safe_destination(installation_root, relative)
                text = target.read_text() if target.is_file() else ""
                add("instructions:" + relative, text.count(START) == 1 and text.count(END) == 1 and section["block"] in text, str(target))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            add("registration", False, str(exc))
    available = {name: shutil.which(info["executable"]) for name, info in AGENTS.items()}
    for name in required:
        add(name, available[name] is not None, available[name] or "Install and authenticate " + name + ": " + AGENTS[name]["install_url"])
    for name in selected:
        if not available[name] and name not in required:
            warnings.append(name + " CLI is absent; skills are installed, but automatic workers need it: " + AGENTS[name]["install_url"])
    if search_caps["fts5"] and not search_caps["trigram"]:
        warnings.append("SQLite trigram is unavailable; search uses token/prefix BM25 without substring or fuzzy matching.")
    if not selected and not available["codex"] and not require_codex:
        warnings.append("Codex is absent; other installed assistants and command/manual adapters remain available.")
    return {"status": "ready" if all(item["passed"] for item in checks) else "blocked",
            "skill_directory": str(root), "selected_agents": selected, "executables": available,
            "checks": checks, "warnings": warnings}
