"""Standard-library-only, transactional installation of the shared skill bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

from .agents import LEGACY_SKILLS, SKILLS, VERSION, agent_names

NAMES = SKILLS
SOURCE = Path(__file__).resolve().parents[3]
START = "<!-- orchi:begin -->"
END = "<!-- orchi:end -->"
MANIFEST = ".agents/.orchi-install.json"
GITHUB_ASSETS = SOURCE / "orchi/assets/github"
LABELS = {
    "Initiative": ("5319e7", "Orchi: a request decomposed into Epics"),
    "Epic": ("0e8a16", "Orchi: an outcome decomposed into Tasks"),
    "Task": ("1d76db", "Orchi: one reviewable result"),
    "in-progress": ("fbca04", "Orchi: owned work in progress"),
}
# GitHub reads the first PR template it finds; extend an existing one instead of adding a rival.
PR_TEMPLATE_PATHS = (".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "pull_request_template.md",
                     "PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md")
PR_TEMPLATE = """## Summary

<!-- What changed and why. Link issues; closing keywords only work for PRs into the default branch. -->

## Verification

<!-- Commands, results, and the candidate commit. -->

## Documentation impact

<!-- Required: the pages updated, or why no documentation changes. The Orchi documentation check fails when this is empty. -->

## Handoff

<!-- Only while work is interrupted: branch/commit, done, remaining, uncommitted changes, checks, next step. -->"""


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


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def github_files() -> dict[str, bytes]:
    return {".github/" + path.relative_to(GITHUB_ASSETS).as_posix(): path.read_bytes()
            for path in sorted(GITHUB_ASSETS.rglob("*")) if path.is_file()}


def ensure_labels(root: Path) -> dict:
    """Create missing Orchi labels with gh; report rather than fail when GitHub is unavailable."""
    try:
        existing = {item["name"].casefold() for item in json.loads(subprocess.run(
            ["gh", "label", "list", "--limit", "500", "--json", "name"], cwd=root,
            check=True, capture_output=True, text=True).stdout)}
        created = []
        for name, (color, description) in LABELS.items():
            if name.casefold() not in existing:
                subprocess.run(["gh", "label", "create", name, "--color", color, "--description", description],
                               cwd=root, check=True, capture_output=True, text=True)
                created.append(name)
        return {"created": created}
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        return {"created": [], "error": (getattr(exc, "stderr", "") or str(exc)).strip(),
                "fix": "Check that the repository has a GitHub remote and gh is authenticated, then rerun the installer."}


def pr_template_path(root: Path, managed: dict) -> str:
    recorded = [path for path in PR_TEMPLATE_PATHS if path in managed]
    if recorded:
        return recorded[0]
    # Compare exact names: on case-insensitive filesystems both spellings would appear to exist.
    def present(path: str) -> bool:
        parent = (root / path).parent
        return parent.is_dir() and Path(path).name in os.listdir(parent)
    return next((path for path in PR_TEMPLATE_PATHS if present(path)), PR_TEMPLATE_PATHS[0])


def instruction_blocks(root: Path, agents: list[str], global_scope: bool, pr_template: str | None = None) -> dict[str, str]:
    skill = str(root / ".agents/skills/orchi/SKILL.md") if global_scope else ".agents/skills/orchi/SKILL.md"
    body = (
        "## Orchi workflow\n\n"
        f"For implementation work and Orchi continuation, read and follow `{skill}` before planning or editing.\n"
        "Research first and agree the outcome, approach, and scope (Task, Epic, or Initiative) with the user before creating branches, issues, or changes.\n"
        "Track work in Git branches and GitHub Issues; resume from the existing issue, branch, and PR instead of duplicating work.\n"
        "For documentation-only questions, use its retrieval guidance without creating tracking.\n"
        "Do not infer merge or deployment permission from permission to implement."
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
    if pr_template:
        blocks[pr_template] = PR_TEMPLATE
    if "copilot" in agents:
        blocks[".github/copilot-instructions.md"] = (
            "## Orchi\n\nRead and follow the Orchi workflow in the repository root `AGENTS.md` before implementation.\n"
            "The entrypoint is `.agents/skills/orchi/SKILL.md`."
        )
    return blocks


def install(project: Path, replace: bool = False, dry: bool = False,
            agents: list[str] | None = None, global_scope: bool = False,
            uninstall: bool = False, github: bool = False) -> dict:
    if project.is_symlink():
        raise ValueError("Installation root must not be a symlink")
    root = project.resolve()
    if not root.is_dir():
        raise ValueError("Installation root must already exist")
    manifest_path = safe_destination(root, MANIFEST)
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if not isinstance(previous, dict) or (previous and previous.get("scope", "project") != ("user" if global_scope else "project")):
        raise ValueError("Installation manifest has the wrong scope or format")
    for field in ("skills", "links", "instructions", "files"):
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
    legacy = [name for name in LEGACY_SKILLS if name in previous.get("skills", {})]
    for name in (*NAMES, *legacy):
        relative = ".agents/skills/" + name
        target = safe_destination(root, relative)
        if target.exists() and not target.is_dir():
            raise ValueError("Expected a skill directory: " + str(target))
        existing = inventory(target) if target.exists() else None
        if name in legacy and not uninstall:
            # Retired stage skill: remove it, keeping a backup when it was edited.
            if existing is not None:
                if existing != previous["skills"][name]:
                    conflicts.append(name)
                skill_changes.append(name)
                replacements[relative] = ("remove", None)
            continue
        if uninstall:
            if existing is not None:
                if existing != previous.get("skills", {}).get(name):
                    raise ValueError("Modified skill must be preserved before uninstalling: " + name)
                replacements[relative] = ("remove", None)
        elif existing != desired[name]:
            # An unmodified managed copy updates in place; local edits need explicit replacement.
            if existing is not None and existing != previous.get("skills", {}).get(name):
                conflicts.append(name)
            skill_changes.append(name)
            replacements[relative] = ("directory", SOURCE / name)
    # GitHub setup is opt-in and, once chosen, kept by later installations like the assistant selection.
    github = bool(github or previous.get("github"))
    if github and global_scope:
        raise ValueError("--github applies to a project installation, not --global")
    wanted = {} if uninstall or not github else github_files()
    old_files = previous.get("files", {})
    managed_files = {}
    for relative in sorted(set(old_files) | set(wanted)):
        target = safe_destination(root, relative)
        current = digest(target)
        content = wanted.get(relative)
        if content is None:
            if current is not None:
                if current != old_files.get(relative):
                    raise ValueError("Modified managed file must be preserved before uninstalling: " + relative)
                replacements[relative] = ("remove", None)
            continue
        managed_files[relative] = hashlib.sha256(content).hexdigest()
        if current == managed_files[relative]:
            continue
        if current is not None and current != old_files.get(relative):
            conflicts.append(relative)
        replacements[relative] = ("file", content)
    if conflicts and not replace and not dry:
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
    managed_links = {f".claude/skills/{name}" for name in (*NAMES, *LEGACY_SKILLS)}
    for relative, destination in list(links.items()):
        if relative not in managed_links or destination != "../../.agents/skills/" + Path(relative).name:
            raise ValueError("Invalid managed link in installation manifest")
        safe_destination(root, str(Path(relative).parent))
        target = root / relative
        if target.is_symlink():
            if os.readlink(target) != destination:
                raise ValueError("Conflicting skill link: " + str(target))
            if uninstall or Path(relative).name in LEGACY_SKILLS:
                replacements[relative] = ("remove", None)
        elif target.exists():
            raise ValueError("Refusing to replace an existing agent skill: " + str(target))
        elif not uninstall and Path(relative).name not in LEGACY_SKILLS:
            replacements[relative] = ("link", destination)
    links = {relative: destination for relative, destination in links.items() if Path(relative).name not in LEGACY_SKILLS}

    managed = {}
    old_blocks = previous.get("instructions", {})
    bodies = instruction_blocks(root, selected, global_scope, pr_template_path(root, old_blocks) if github else None)
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

    manifest = {"version": VERSION, "scope": "user" if global_scope else "project", "agents": selected,
                "github": github, "skills": desired, "links": links, "instructions": managed, "files": managed_files}
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if uninstall:
        replacements[MANIFEST] = ("remove", None)
    elif not manifest_path.exists() or manifest_path.read_bytes() != encoded:
        replacements[MANIFEST] = ("file", encoded)
    report = {"project": str(root), "scope": manifest["scope"], "agents": selected, "github": github,
              "version": {"installed": previous.get("version"), "bundle": VERSION}, "install": skill_changes,
              "changes": list(replacements), "preserved": ["unmanaged instruction content", "assistant settings", "non-Orchi skills"],
              "prerequisites": {tool: shutil.which(tool) for tool in ("git", "gh")}}
    report["next_steps"] = ["Commit the installed files to share them with your team.",
                            "Authenticate the GitHub CLI (gh auth login) so assistants can manage Issues and PRs.",
                            "Open a new assistant session and ask it to use Orchi."] if not uninstall else []
    if dry:
        return {**report, "dry_run": True, "conflicts": conflicts, "requires_replace": bool(conflicts and not replace)}
    result = {**report, "status": "unchanged"}
    if replacements:
        result = {**report, **apply_changes(root, replacements, desired, global_scope),
                  "status": "removed" if uninstall else "installed"}
    if github and not uninstall:
        result["labels"] = ensure_labels(root)
    return result


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
    parser.add_argument("--github", action="store_true",
                        help="Also install issue templates, a PR template, a documentation check workflow, and Orchi labels")
    parser.add_argument("--version", action="store_true", help="Show installed and bundled versions and the upgrade command")
    args = parser.parse_args(argv)
    if args.version:
        root = Path.home() if args.global_scope else (args.project or Path.cwd())
        manifest = root / MANIFEST
        installed = json.loads(manifest.read_text()).get("version") if manifest.is_file() else None
        print(json.dumps({"installed": installed, "bundle": VERSION,
                          "upgrade": "npx --yes github:nkhus/orchi" + (" --global" if args.global_scope else "")}, indent=2))
        return 0
    try:
        agents = args.agents
        if agents is None and sys.stdin.isatty() and not args.uninstall:
            print("Assistants: 1 Codex, 2 Copilot, 3 Claude Code. Enter names/numbers separated by spaces, or all [codex]:", file=sys.stderr)
            choices = input().replace(",", " ").split() or ["codex"]
            agents = [{"1": "codex", "2": "copilot", "3": "claude"}.get(item, item) for item in choices]
        result = install(Path.home() if args.global_scope else args.project or Path.cwd(),
                         args.replace_orchi, args.dry_run, agents, args.global_scope, args.uninstall, args.github)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
