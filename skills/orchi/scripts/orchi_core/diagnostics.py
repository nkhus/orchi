"""Read-only checks for a complete skill installation and local prerequisites."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .retrieval import capabilities

SKILLS = ("orchi", "orchi-plan", "orchi-work", "orchi-review", "orchi-deliver")


def doctor(repo: str | None = None, require_codex: bool = False) -> dict:
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
    for relative in ("scripts/operator.py", "scripts/requirements.txt", "references/operator-guide.md", "assets/codex-adapter.json"):
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
    codex = shutil.which("codex")
    if require_codex:
        add("codex", codex is not None, codex or "Install and authenticate Codex before a live run")
    warnings = ["This check does not verify authentication, trusted policy, worker isolation, or model behavior."]
    if search_caps["fts5"] and not search_caps["trigram"]:
        warnings.append("SQLite trigram is unavailable; search uses token/prefix BM25 without substring or fuzzy matching.")
    if not codex and not require_codex:
        warnings.append("Codex is absent; command/manual adapters and deterministic tests remain available.")
    return {"status": "ready" if all(item["passed"] for item in checks) else "blocked",
            "skill_directory": str(root), "checks": checks, "warnings": warnings}
