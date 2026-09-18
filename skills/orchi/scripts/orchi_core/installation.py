"""Standard-library-only, transactional installation of the shared skill bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from .agents import AGENTS, SKILLS, agent_names

NAMES = SKILLS
SOURCE = Path(__file__).resolve().parents[3]
START = "<!-- orchi:begin -->"
END = "<!-- orchi:end -->"
MANIFEST = ".agents/.orchi-install.json"


def inventory(directory: Path) -> dict[str, str]:
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Refusing symlink: " + str(path))
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def safe_destination(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Destination must stay within the installation root")
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("Refusing symlink: " + str(part))
    return path


def block_span(text: str) -> tuple[int, int] | None:
    if START not in text and END not in text:
        return None
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
        raise ValueError("Malformed Orchi instruction markers; repair them before installing")
    return text.index(START), text.index(END) + len(END)


def instruction_blocks(root: Path, agents: list[str], global_scope: bool) -> dict[str, str]:
    skill = str(root / ".agents/skills/orchi/SKILL.md") if global_scope else ".agents/skills/orchi/SKILL.md"
    body = (
        "## Orchi workflow\n\n"
        f"For implementation work and Orchi continuation, read and follow `{skill}` before planning or editing.\n"
        "Use Orchi's controller state to route planning, execution, review, and delivery.\n"
        "For documentation-only questions, use its retrieval procedure without starting an initiative.\n"
        "If assigned an Orchi task packet, follow TASK.md and return the requested phase result; do not start a coordinator.\n"
        "Preserve exact human approvals, bounded task scope, final-only Core reconciliation, and operator-controlled publication.\n"
        "If Orchi is unavailable or not configured, report the missing setup; do not invent approvals or silently bypass the workflow."
    )
    if global_scope:
        locations = {"codex": ".codex/AGENTS.md", "copilot": ".copilot/copilot-instructions.md", "claude": ".claude/CLAUDE.md"}
        blocks = {locations[name]: body for name in agents}
        if "codex" in agents and (root / ".codex/AGENTS.override.md").exists():
            blocks[".codex/AGENTS.override.md"] = body
        return blocks
    blocks = {"AGENTS.md": body}
    if (root / "AGENTS.override.md").exists():
        blocks["AGENTS.override.md"] = body
    if "claude" in agents:
        blocks["CLAUDE.md"] = "# Shared Orchi instructions\n\n@AGENTS.md"
    if "copilot" in agents:
        blocks[".github/copilot-instructions.md"] = (
            "## Orchi\n\nRead and follow the Orchi workflow in the repository root `AGENTS.md` before implementation.\n"
            "The entrypoint is `.agents/skills/orchi/SKILL.md`. Assigned packet workers follow TASK.md instead."
        )
    return blocks


def install(project: Path, replace: bool = False, dry: bool = False,
            agents: list[str] | None = None, global_scope: bool = False,
            uninstall: bool = False) -> dict:
    if project.is_symlink():
        raise ValueError("Installation root must not be a symlink")
    root = project.resolve()
    if not root.is_dir():
        raise ValueError("Installation root must already exist")
    manifest_path = safe_destination(root, MANIFEST)
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if not isinstance(previous, dict) or (previous and previous.get("scope", "project") != ("user" if global_scope else "project")):
        raise ValueError("Installation manifest has the wrong scope or format")
    for field in ("skills", "links", "instructions"):
        if not isinstance(previous.get(field, {}), dict):
            raise ValueError("Invalid installation manifest field: " + field)
    if not isinstance(previous.get("agents", []), list) or not all(isinstance(name, str) for name in previous.get("agents", [])):
        raise ValueError("Invalid assistant list in installation manifest")
    if uninstall and not previous:
        raise ValueError("No Orchi installation manifest; nothing can be safely removed")
    selected = agent_names(agents or previous.get("agents") or ["codex"])
    # Selection is additive: adding Claude must not remove a working Copilot setup.
    selected = agent_names([*previous.get("agents", []), *selected])
    desired = {} if uninstall else {name: inventory(SOURCE / name) for name in NAMES}
    replacements: dict[str, tuple[str, object]] = {}
    conflicts = []
    skill_changes = []
    for name in NAMES:
        relative = ".agents/skills/" + name
        target = safe_destination(root, relative)
        if target.exists() and not target.is_dir():
            raise ValueError("Expected a skill directory: " + str(target))
        existing = inventory(target) if target.exists() else None
        if uninstall:
            if existing is not None:
                if existing != previous.get("skills", {}).get(name):
                    raise ValueError("Modified skill must be preserved before uninstalling: " + name)
                replacements[relative] = ("remove", None)
        elif existing != desired[name]:
            if existing is not None:
                conflicts.append(name)
            skill_changes.append(name)
            replacements[relative] = ("directory", SOURCE / name)
    if conflicts and not replace:
        raise ValueError("Existing Orchi content differs: " + ", ".join(conflicts) + ". Review and use --replace-orchi; a backup will be kept.")

    links = dict(previous.get("links", {}))
    if not uninstall and "claude" in selected:
        links.update({f".claude/skills/{name}": f"../../.agents/skills/{name}" for name in NAMES})
    if not uninstall and "copilot" in selected:
        for name in NAMES:
            alias = root / (".copilot/skills" if global_scope else ".github/skills") / name
            if alias.exists() or alias.is_symlink():
                if not alias.is_symlink() or alias.resolve() != root / ".agents/skills" / name:
                    raise ValueError("Conflicting Copilot skill shadows Orchi: " + str(alias))
    for relative, destination in links.items():
        if relative not in {f".claude/skills/{name}" for name in NAMES} or destination != "../../.agents/skills/" + Path(relative).name:
            raise ValueError("Invalid managed link in installation manifest")
        safe_destination(root, str(Path(relative).parent))
        target = root / relative
        if target.is_symlink():
            if os.readlink(target) != destination:
                raise ValueError("Conflicting skill link: " + str(target))
            if uninstall:
                replacements[relative] = ("remove", None)
        elif target.exists():
            raise ValueError("Refusing to replace an existing agent skill: " + str(target))
        elif not uninstall:
            replacements[relative] = ("link", destination)

    managed = {}
    bodies = instruction_blocks(root, selected, global_scope)
    old_blocks = previous.get("instructions", {})
    for relative in old_blocks:
        if relative not in bodies:
            raise ValueError("Managed instruction location is missing or inconsistent: " + relative)
    for relative, body in bodies.items():
        candidate = root / relative
        if relative == "CLAUDE.md" and candidate.is_symlink() and candidate.resolve() == root / "AGENTS.md":
            continue
        target = safe_destination(root, relative)
        before = target.read_bytes() if target.exists() else b""
        text = before.decode("utf-8")
        span = block_span(text)
        block = START + "\n" + body + "\n" + END
        old = old_blocks.get(relative)
        if span:
            current = text[span[0]:span[1]]
            if current != (old or {}).get("block", block):
                raise ValueError("Orchi instruction section was edited; preserve or restore it before installing: " + relative)
        elif old:
            raise ValueError("Orchi instruction section was removed; restore it or remove its manifest entry: " + relative)
        separator = old.get("separator", "") if old else ("" if not text or span else "\n\n")
        if uninstall:
            if not old:
                continue
            start, end = span
            if separator and text[:start].endswith(separator):
                start -= len(separator)
            updated = text[:start] + text[end:]
            if not old.get("existed", True) and not updated:
                replacements[relative] = ("remove", None)
                continue
        else:
            updated = text[:span[0]] + block + text[span[1]:] if span else text + separator + block
            managed[relative] = {"block": block, "separator": separator, "existed": old.get("existed", True) if old else target.exists()}
        if updated.encode("utf-8") != before:
            replacements[relative] = ("file", updated.encode("utf-8"))

    manifest = {"scope": "user" if global_scope else "project", "agents": selected,
                "skills": desired, "links": links, "instructions": managed}
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if uninstall:
        replacements[MANIFEST] = ("remove", None)
    elif not manifest_path.exists() or manifest_path.read_bytes() != encoded:
        replacements[MANIFEST] = ("file", encoded)
    report = {"project": str(root), "scope": manifest["scope"], "agents": selected, "install": skill_changes,
              "changes": list(replacements), "preserved": ["unmanaged instruction content", "assistant settings", "non-Orchi skills"],
              "adapters": {name: str(root / f".agents/skills/orchi/assets/{name}-adapter.json") for name in selected},
              "prerequisites": [{"agent": name, "executable": shutil.which(AGENTS[name]["executable"]),
                                 "install_url": AGENTS[name]["install_url"]} for name in selected]}
    report["next_steps"] = ["Install/authenticate any missing selected assistant CLI before automatic worker execution.",
                            "Run the installed doctor; complete operator setup before starting an initiative."] if not uninstall else []
    if dry:
        return {**report, "dry_run": True}
    if not replacements:
        return {**report, "status": "unchanged"}
    return {**report, **apply_changes(root, replacements, desired, global_scope), "status": "removed" if uninstall else "installed"}


def apply_changes(root: Path, changes: dict, desired: dict, global_scope: bool = False) -> dict:
    """Stage first; roll back skill directories, links, instructions, and manifest together."""
    staging = Path(tempfile.mkdtemp(prefix=".orchi-stage-", dir=root if global_scope else root.parent))
    backup = (root if global_scope else root.parent) / ((".orchi-backup-" if global_scope else root.name + "-orchi-backup-") + uuid.uuid4().hex[:10])
    created_dirs = []
    moved = []
    added = []
    try:
        for relative, (kind, value) in changes.items():
            stage = staging / relative
            stage.parent.mkdir(parents=True, exist_ok=True)
            if kind == "directory":
                shutil.copytree(value, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                if inventory(stage) != desired[Path(relative).name]:
                    raise ValueError("Staging integrity failed: " + relative)
            elif kind == "file":
                stage.write_bytes(value)
                target = root / relative
                if target.exists():
                    shutil.copymode(target, stage)
            elif kind == "link":
                stage.symlink_to(value, target_is_directory=True)
        for relative, (kind, _) in changes.items():
            target = root / relative
            if target.exists() or target.is_symlink():
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(saved))
                moved.append(relative)
            if kind != "remove":
                missing = []
                parent = target.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for parent in reversed(missing):
                    parent.mkdir()
                    created_dirs.append(parent)
                shutil.move(str(staging / relative), str(target))
                added.append(relative)
    except BaseException:
        for relative in reversed(added):
            target = root / relative
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        for relative in reversed(moved):
            shutil.move(str(backup / relative), str(root / relative))
        for directory in reversed(created_dirs):
            directory.rmdir()
        if backup.exists():
            shutil.rmtree(backup)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return {"backup": str(backup) if moved else None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install one shared Orchi bundle for selected coding assistants.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--project", type=Path, help="Target project (defaults to the current directory)")
    scope.add_argument("--global", dest="global_scope", action="store_true", help="Install for this user across projects")
    parser.add_argument("--agents", "--agent", nargs="+", action="extend", help="codex, copilot, claude, or all; comma-separated names also work")
    parser.add_argument("--replace-orchi", action="store_true", help="Back up and replace differing shared skill files")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true", help="Remove the managed bundle and instruction sections; refuse modified content")
    args = parser.parse_args(argv)
    try:
        agents = args.agents
        if agents is None and sys.stdin.isatty() and not args.uninstall:
            print("Assistants: 1 Codex, 2 Copilot, 3 Claude Code. Enter names/numbers separated by spaces, or all [codex]:", file=sys.stderr)
            choices = input().replace(",", " ").split() or ["codex"]
            agents = [{"1": "codex", "2": "copilot", "3": "claude"}.get(item, item) for item in choices]
        result = install(Path.home() if args.global_scope else args.project or Path.cwd(),
                         args.replace_orchi, args.dry_run, agents, args.global_scope, args.uninstall)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
