"""Standard-library-only, transactional installation of the Orchi skills and subagents for Claude Code."""
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

from .agents import SKILLS, VERSION
from .roles import agent_files

NAMES = SKILLS
SOURCE = Path(__file__).resolve().parents[3]
START = "<!-- orchi:begin -->"
END = "<!-- orchi:end -->"
SKILLS_DIR = ".claude/skills/"
MANIFEST = ".claude/.orchi-install.json"
# The former multi-assistant layout: shared skills in .agents/skills/, Claude links to them, and an
# optional Codex configuration block. Installing migrates it; nothing new is written there.
SHARED_MANIFEST = ".agents/.orchi-install.json"
SHARED_SKILLS_DIR = ".agents/skills/"
SHARED_CONFIG = ".codex/config.toml"
CONFIG_START = "# orchi:begin"
CONFIG_END = "# orchi:end"
GITHUB_ASSETS = SOURCE / "orchi/assets/github"
DOCS_WORKFLOW = ".github/workflows/orchi-docs.yml"
LABELS = {
    "Initiative": ("5319e7", "Orchi: a request decomposed into Epics"),
    "Epic": ("0e8a16", "Orchi: an outcome decomposed into Tasks"),
    "Task": ("1d76db", "Orchi: one reviewable result"),
    "in-progress": ("fbca04", "Orchi: owned work in progress"),
    "Exploration": ("c5def5", "Orchi: an idea being researched and shaped before planning"),
}
# GitHub reads the first PR template it finds; extend an existing one instead of adding a rival.
PR_TEMPLATE_PATHS = (".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "pull_request_template.md",
                     "PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md")
PR_TEMPLATE = """## Summary

<!-- What changed and why. Link issues; closing keywords only work for PRs into the default branch. -->

## Verification

<!-- Commands, results, red evidence for new tests, and the candidate commit. Before/after output or screenshots for a visible change. -->

## Merge risk

<!-- One-way door (hard to undo) or two-way door (a revert undoes it), and the blast radius if it is wrong. -->

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


def block_span(text: str, start: str = START, end: str = END) -> tuple[int, int] | None:
    if start not in text and end not in text:
        return None
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) > text.index(end):
        raise ValueError("Malformed Orchi instruction markers; repair them before installing")
    return text.index(start), text.index(end) + len(end)


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


def skill_path(root: Path, global_scope: bool) -> str:
    """How installed instructions and agents name the Orchi skill directory."""
    return str(root / SKILLS_DIR / "orchi") if global_scope else SKILLS_DIR + "orchi"


def load_manifest(path: Path, global_scope: bool) -> dict:
    previous = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(previous, dict) or (previous and previous.get("scope", "project") != ("user" if global_scope else "project")):
        raise ValueError("Installation manifest has the wrong scope or format: " + str(path))
    for field in ("skills", "links", "instructions", "files", "config"):
        if not isinstance(previous.get(field, {}), dict):
            raise ValueError("Invalid installation manifest field: " + field)
    if not isinstance(previous.get("docs_workflow", True), bool):
        raise ValueError("Invalid installation manifest field: docs_workflow")
    return previous


def shared_config_removal(root: Path, old: dict) -> tuple[tuple | None, str | None]:
    """Remove the Codex nesting block a shared-layout installation recorded.

    Returns the replacement (None when nothing changes) and a note for the user.
    """
    target = safe_destination(root, SHARED_CONFIG)
    if not target.is_file():
        return None, None
    try:
        text = target.read_bytes().decode("utf-8")
        span = block_span(text, CONFIG_START, CONFIG_END)
    except (UnicodeDecodeError, ValueError):
        span = None
    if not span:
        return None, None
    if text[span[0]:span[1]] != old.get("block"):
        return None, "Orchi no longer manages the edited block in " + SHARED_CONFIG + "; remove it by hand if unused."
    start, end = span
    if old.get("separator") and text[:start].endswith(old["separator"]):
        start -= len(old["separator"])
    if text[end:end + 1] == "\n":
        end += 1
    updated = text[:start] + text[end:]
    if not old.get("existed", True) and not updated:
        return ("remove", None), None
    return ("file", updated.encode("utf-8")), None


def pr_template_path(root: Path, managed: dict) -> str:
    recorded = [path for path in PR_TEMPLATE_PATHS if path in managed]
    if recorded:
        return recorded[0]
    # Compare exact names: on case-insensitive filesystems both spellings would appear to exist.
    def present(path: str) -> bool:
        parent = (root / path).parent
        return parent.is_dir() and Path(path).name in os.listdir(parent)
    return next((path for path in PR_TEMPLATE_PATHS if present(path)), PR_TEMPLATE_PATHS[0])


def instructions_path(root: Path, global_scope: bool) -> str:
    """The Claude memory file that carries the managed section."""
    if global_scope:
        return ".claude/CLAUDE.md"
    claude = root / "CLAUDE.md"
    # A CLAUDE.md that links to AGENTS.md is read through the link; edit the file it names.
    if claude.is_symlink() and claude.resolve() == root / "AGENTS.md":
        return "AGENTS.md"
    return "CLAUDE.md"


def instruction_blocks(root: Path, global_scope: bool, pr_template: str | None = None) -> dict[str, str]:
    skill = skill_path(root, global_scope) + "/SKILL.md"
    body = (
        "## Orchi workflow\n\n"
        f"For implementation work and Orchi continuation, read and follow `{skill}` before planning or editing.\n"
        "Research first and agree the outcome, approach, and scope (Task, Epic, or Initiative) with the user before creating branches, issues, or changes.\n"
        "Track work in Git branches and GitHub Issues; resume from the existing issue, branch, and PR instead of duplicating work.\n"
        "For documentation-only questions, use its retrieval guidance without creating tracking.\n"
        "Do not infer merge or deployment permission from permission to implement."
    )
    blocks = {instructions_path(root, global_scope): body}
    if pr_template:
        blocks[pr_template] = PR_TEMPLATE
    return blocks


def install(project: Path, replace: bool = False, dry: bool = False, global_scope: bool = False,
            uninstall: bool = False, github: bool = False, docs_workflow: bool | None = None) -> dict:
    if project.is_symlink():
        raise ValueError("Installation root must not be a symlink")
    root = project.resolve()
    if not root.is_dir():
        raise ValueError("Installation root must already exist")
    manifest_path = safe_destination(root, MANIFEST)
    previous = load_manifest(manifest_path, global_scope)
    # A shared-layout installation is migrated: everything it recorded is removed or taken over.
    shared_path = root / SHARED_MANIFEST
    shared = load_manifest(safe_destination(root, SHARED_MANIFEST), global_scope) if shared_path.is_file() else {}
    if uninstall and not previous and not shared:
        raise ValueError("No Orchi installation manifest; nothing can be safely removed")
    desired = {} if uninstall else {name: inventory(SOURCE / name) for name in NAMES}
    replacements: dict[str, tuple[str, object]] = {}
    conflicts = []
    skill_changes = []
    for name, recorded in shared.get("skills", {}).items():
        relative = SHARED_SKILLS_DIR + name
        target = safe_destination(root, relative)
        if not target.exists():
            continue
        if not target.is_dir():
            raise ValueError("Expected a skill directory: " + str(target))
        if inventory(target) != recorded:
            if uninstall:
                raise ValueError("Modified skill must be preserved before uninstalling: " + name)
            # Edited shared copies are removed only with --replace-orchi, which keeps a backup.
            conflicts.append(relative)
        replacements[relative] = ("remove", None)
    # Claude links into the shared copies make way for the skill directories themselves.
    shared_links = set()
    for relative, destination in shared.get("links", {}).items():
        name = Path(relative).name
        if relative != SKILLS_DIR + name or destination != "../../" + SHARED_SKILLS_DIR + name:
            raise ValueError("Invalid managed link in installation manifest")
        safe_destination(root, SKILLS_DIR)
        target = root / relative
        if target.is_symlink():
            if os.readlink(target) != destination:
                raise ValueError("Conflicting skill link: " + str(target))
            shared_links.add(relative)
            replacements[relative] = ("remove", None)
    for name in NAMES:
        relative = SKILLS_DIR + name
        if relative in shared_links:
            existing = None
        else:
            target = safe_destination(root, relative)
            if target.exists() and not target.is_dir():
                raise ValueError("Expected a skill directory: " + str(target))
            existing = inventory(target) if target.exists() else None
        if uninstall:
            if existing is not None:
                if existing != previous.get("skills", {}).get(name):
                    raise ValueError("Modified skill must be preserved before uninstalling: " + name)
                replacements[relative] = ("remove", None)
        elif existing is not None and (SOURCE / name).resolve() == target.resolve():
            # Run from this installed copy: its files are not a pristine bundle, so keep the recorded hashes and
            # treat local edits as conflicts; --replace-orchi accepts the edited copy as the installed bundle.
            recorded = previous.get("skills", {}).get(name)
            if existing != recorded:
                conflicts.append(name)
            desired[name] = existing if replace else recorded
        elif existing != desired[name]:
            # An unmodified managed copy updates in place; local edits need explicit replacement.
            if existing is not None and existing != previous.get("skills", {}).get(name):
                conflicts.append(name)
            skill_changes.append(name)
            replacements[relative] = ("directory", SOURCE / name)
    # GitHub setup is opt-in and, once chosen, kept by later installations.
    github = bool(github or previous.get("github") or shared.get("github"))
    if github and global_scope:
        raise ValueError("--github applies to a project installation, not --global")
    # The documentation check is on by default; an opt-out is kept until explicitly re-enabled.
    if docs_workflow is None:
        docs_workflow = (previous or shared).get("docs_workflow", True)
    github_wanted = {relative: content for relative, content in github_files().items()
                     if docs_workflow or relative != DOCS_WORKFLOW} if github else {}
    # Rendered subagents are managed like GitHub files: hash-tracked, replaced only when unmodified.
    wanted = {} if uninstall else {**github_wanted, **agent_files(skill_path(root, global_scope))}
    old_files = {**shared.get("files", {}), **previous.get("files", {})}
    managed_files = {}
    for relative in sorted(set(old_files) | set(wanted)):
        target = safe_destination(root, relative)
        current = digest(target)
        content = wanted.get(relative)
        if content is None:
            if current is not None:
                if current != old_files.get(relative):
                    if uninstall:
                        raise ValueError("Modified managed file must be preserved before uninstalling: " + relative)
                    # A file Orchi no longer wants but the user edited: remove only with --replace-orchi.
                    conflicts.append(relative)
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

    managed = {}
    # A managed instruction file the user deleted has nothing left to update or remove.
    old_blocks = {relative: entry for relative, entry in {**shared.get("instructions", {}), **previous.get("instructions", {})}.items()
                  if (root / relative).exists() or (root / relative).is_symlink()}
    bodies = {} if uninstall else instruction_blocks(root, global_scope, pr_template_path(root, old_blocks) if github else None)
    for relative in sorted(set(bodies) | set(old_blocks)):
        target = safe_destination(root, relative)
        before = target.read_bytes() if target.exists() else b""
        text = before.decode("utf-8")
        span = block_span(text)
        body = bodies.get(relative)
        block = START + "\n" + body + "\n" + END if body is not None else None
        old = old_blocks.get(relative)
        if span:
            current = text[span[0]:span[1]]
            if current != (old or {}).get("block", block):
                raise ValueError("Orchi instruction section was edited; preserve or restore it before installing: " + relative)
        elif old:
            raise ValueError("Orchi instruction section was removed; restore it or remove its manifest entry: " + relative)
        separator = old.get("separator", "") if old else ("" if not text or span else "\n\n")
        if block is None:
            # Uninstalling, or a location Orchi no longer uses, such as AGENTS.md from the shared layout.
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

    notes = []
    old_config = shared.get("config", {}).get(SHARED_CONFIG)
    if old_config is not None:
        if not isinstance(old_config, dict):
            raise ValueError("Invalid installation manifest field: config")
        config_change, note = shared_config_removal(root, old_config)
        if config_change:
            replacements[SHARED_CONFIG] = config_change
        if note:
            notes.append(note)

    manifest = {"version": VERSION, "scope": "user" if global_scope else "project", "github": github,
                "docs_workflow": docs_workflow, "skills": desired, "instructions": managed, "files": managed_files}
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if uninstall:
        if previous:
            replacements[MANIFEST] = ("remove", None)
    elif not manifest_path.exists() or manifest_path.read_bytes() != encoded:
        replacements[MANIFEST] = ("file", encoded)
    if shared:
        replacements[SHARED_MANIFEST] = ("remove", None)
    report = {"project": str(root), "scope": manifest["scope"], "github": github, "docs_workflow": docs_workflow,
              "version": {"installed": (previous or shared).get("version"), "bundle": VERSION}, "install": skill_changes,
              "changes": list(replacements), "preserved": ["unmanaged instruction content", "non-Orchi skills and agents"],
              "prerequisites": {tool: shutil.which(tool) for tool in ("git", "gh")}, "notes": notes}
    report["next_steps"] = ["Commit the installed files to share them with your team.",
                            "Authenticate the GitHub CLI (gh auth login) so Claude Code can manage Issues and PRs.",
                            "Open a new Claude Code session and ask it to use Orchi."] if not uninstall else []
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
    parser = argparse.ArgumentParser(description="Install the Orchi skills and subagents for Claude Code.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--project", type=Path, help="Target project (defaults to the current directory)")
    scope.add_argument("--global", dest="global_scope", action="store_true", help="Install for this user across projects")
    parser.add_argument("--replace-orchi", action="store_true", help="Back up and replace differing Orchi skill, agent, and GitHub files; "
                        "edited instruction sections must be restored by hand")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true", help="Remove the managed bundle and instruction sections; refuse modified content")
    parser.add_argument("--github", action="store_true",
                        help="Also install issue templates, a PR template, a documentation check workflow, and Orchi labels")
    workflow = parser.add_mutually_exclusive_group()
    workflow.add_argument("--no-docs-workflow", dest="docs_workflow", action="store_const", const=False,
                          help="With --github, do not install the documentation check workflow; later runs keep this choice")
    workflow.add_argument("--docs-workflow", dest="docs_workflow", action="store_const", const=True,
                          help="Install the documentation check workflow again after --no-docs-workflow")
    parser.add_argument("--version", action="store_true", help="Show installed and bundled versions and the upgrade command")
    args = parser.parse_args(argv)
    if args.version:
        root = Path.home() if args.global_scope else (args.project or Path.cwd())
        manifest = next((root / path for path in (MANIFEST, SHARED_MANIFEST) if (root / path).is_file()), None)
        installed = json.loads(manifest.read_text()).get("version") if manifest else None
        print(json.dumps({"installed": installed, "bundle": VERSION,
                          "upgrade": "npx --yes github:nkhus/orchi" + (" --global" if args.global_scope else "")}, indent=2))
        return 0
    try:
        root = Path.home() if args.global_scope else args.project or Path.cwd()
        result = install(root, args.replace_orchi, args.dry_run, args.global_scope, args.uninstall, args.github,
                         args.docs_workflow)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
