"""Installation behavior in disposable project and home directories."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from orchi_core import installation, roles
from orchi_core.agents import SKILLS

from conftest import npx_calls

ROLES = ("orchi-designer", "orchi-fixer", "orchi-implementer", "orchi-researcher", "orchi-reviewer", "orchi-scout")
MANIFEST = ".claude/.orchi-install.json"


@pytest.mark.parametrize("global_scope", [False, True])
def test_each_scope(tmp_path, global_scope):
    result = installation.install(tmp_path, global_scope=global_scope)
    assert result["status"] == "installed" and "agents" not in result
    for name in SKILLS:
        folder = tmp_path / ".claude/skills" / name
        assert not folder.is_symlink() and (folder / "SKILL.md").is_file()
    instructions = tmp_path / (".claude/CLAUDE.md" if global_scope else "CLAUDE.md")
    assert "Orchi workflow" in instructions.read_text()
    assert not (tmp_path / "AGENTS.md").exists() and not (tmp_path / ".agents").exists()
    assert not (tmp_path / ".codex").exists() and not (tmp_path / ".github").exists()
    skill = str(tmp_path.resolve() / ".claude/skills/orchi-core") if global_scope else ".claude/skills/orchi-core"
    assert sorted(p.name for p in (tmp_path / ".claude/agents").glob("orchi-*")) == [name + ".md" for name in ROLES]
    for path in (tmp_path / ".claude/agents").glob("orchi-*.md"):
        text = path.read_text()
        assert "{{" not in text and (f'"{skill}/scripts/' in text or f"`{skill}/references/" in text)
    assert f"`{skill}/SKILL.md`" in instructions.read_text()
    assert installation.impeccable_version(tmp_path) == installation.IMPECCABLE
    assert installation.install(tmp_path, global_scope=global_scope)["status"] == "unchanged"
    installation.install(tmp_path, global_scope=global_scope, uninstall=True)
    left = sorted(path.relative_to(tmp_path).as_posix() for path in (tmp_path / ".claude").rglob("*") if path.is_file())
    assert left == [".claude/agents/impeccable-documenter.md", ".claude/skills/impeccable/SKILL.md"]


def test_uninstall_preserves_user_content(tmp_path):
    existing = {"CLAUDE.md": b"# User\r\nRules without final newline", "AGENTS.md": b"Other assistant rules\n"}
    for name, content in existing.items():
        (tmp_path / name).write_bytes(content)
    installation.install(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_bytes().startswith(existing["CLAUDE.md"])
    assert (tmp_path / "AGENTS.md").read_bytes() == existing["AGENTS.md"]
    with (tmp_path / "CLAUDE.md").open("ab") as file:
        file.write(b"\nLater user rule\n")
    installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "CLAUDE.md").read_bytes() == existing["CLAUDE.md"] + b"\nLater user rule\n"
    assert (tmp_path / "AGENTS.md").read_bytes() == existing["AGENTS.md"]
    assert not (tmp_path / MANIFEST).exists()
    # Impeccable stays installed after Orchi is removed.
    assert [p.name for p in (tmp_path / ".claude/skills").iterdir()] == ["impeccable"]


def test_project_can_move(tmp_path):
    project = tmp_path / "before"; project.mkdir()
    installation.install(project)
    project.rename(tmp_path / "after")
    moved = tmp_path / "after"
    for name in SKILLS:
        assert (moved / ".claude/skills" / name / "SKILL.md").is_file()
    assert installation.install(moved)["status"] == "unchanged"


def test_edited_managed_section_is_not_silently_overwritten(tmp_path):
    installation.install(tmp_path)
    target = tmp_path / "CLAUDE.md"
    target.write_text(target.read_text().replace("Orchi", "Customized Orchi", 1))
    before = target.read_bytes()
    for kwargs in ({"replace": True}, {"uninstall": True}):
        with pytest.raises(ValueError, match="instruction section was edited"):
            installation.install(tmp_path, **kwargs)
        assert target.read_bytes() == before


def test_dry_run_reports_all_files_without_writes(tmp_path):
    result = installation.install(tmp_path, dry=True)
    assert "CLAUDE.md" in result["changes"] and ".claude/skills/orchi-core" in result["changes"]
    assert ".claude/agents/orchi-scout.md" in result["changes"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("relative", [".claude", ".claude/skills", ".claude/agents", "CLAUDE.md"])
def test_symlink_escape_refused_before_any_mutation(tmp_path, relative):
    project = tmp_path / "project"; project.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    target = project / relative; target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        installation.install(project)
    assert not list(outside.iterdir()) and not (project / MANIFEST).exists()


def test_claude_link_to_agents_receives_the_managed_section(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Existing rules")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    installation.install(tmp_path)
    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert "Orchi workflow" in (tmp_path / "AGENTS.md").read_text()
    assert list(json.loads((tmp_path / MANIFEST).read_text())["instructions"]) == [".gitignore", "AGENTS.md"]
    installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert (tmp_path / "AGENTS.md").read_text() == "Existing rules"


@pytest.mark.parametrize("name", ["orchi", "orchi-plan"])
def test_unrecorded_repository_skill_needs_replace(tmp_path, name):
    folder = tmp_path / ".claude/skills" / name; folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("Repository-local skill")
    with pytest.raises(ValueError, match=name):
        installation.install(tmp_path)
    assert (folder / "SKILL.md").read_text() == "Repository-local skill"
    assert not (tmp_path / "CLAUDE.md").exists()
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".claude/skills" / name / "SKILL.md").read_text() == "Repository-local skill"
    assert f"name: {name}" in (folder / "SKILL.md").read_text()


def test_skill_path_that_is_a_file_is_refused(tmp_path):
    (tmp_path / ".claude/skills").mkdir(parents=True)
    (tmp_path / ".claude/skills/orchi-core").write_text("not a skill")
    with pytest.raises(ValueError, match="Expected a skill directory"):
        installation.install(tmp_path, replace=True)


def test_failure_after_instructions_rolls_back_all_changes(tmp_path, monkeypatch):
    (tmp_path / "CLAUDE.md").write_text("Original")
    original_move = installation.shutil.move
    def fail_last_file(source, destination):
        if ".orchi-stage-" in str(source) and str(source).endswith(".orchi-install.json"):
            raise OSError("Injected manifest failure")
        return original_move(source, destination)
    monkeypatch.setattr(installation.shutil, "move", fail_last_file)
    with pytest.raises(OSError, match="Injected"):
        installation.install(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text() == "Original"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["CLAUDE.md"]


def run_installed_copy(root, *args):
    script = root / ".claude/skills/orchi-core/scripts/orchi_install.py"
    return subprocess.run([sys.executable, str(script), "--project", str(root), *args], capture_output=True, text=True,
                          cwd=root, env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"})


def test_installed_installer_runs_without_source_checkout(tmp_path):
    installation.install(tmp_path)
    result = run_installed_copy(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "unchanged"


def test_installed_copy_keeps_local_skill_edits_as_conflicts(tmp_path):
    installation.install(tmp_path)
    manifest_path = tmp_path / MANIFEST
    recorded = manifest_path.read_bytes()
    skill = tmp_path / ".claude/skills/orchi-core/SKILL.md"
    skill.write_text(skill.read_text() + "\nLocal rule\n")
    result = run_installed_copy(tmp_path)
    assert result.returncode == 2 and "Existing Orchi content differs: orchi-core." in json.loads(result.stdout)["error"]
    assert json.loads(run_installed_copy(tmp_path, "--dry-run").stdout)["conflicts"] == ["orchi-core"]
    assert manifest_path.read_bytes() == recorded
    # The next upstream upgrade still sees the edit instead of overwriting it.
    with pytest.raises(ValueError, match="differs: orchi-core"):
        installation.install(tmp_path)
    assert skill.read_text().endswith("Local rule\n")


def test_installed_copy_replace_accepts_the_edited_skill(tmp_path):
    installation.install(tmp_path)
    skill = tmp_path / ".claude/skills/orchi-core/SKILL.md"
    skill.write_text(skill.read_text() + "\nLocal rule\n")
    result = run_installed_copy(tmp_path, "--replace-orchi")
    assert result.returncode == 0, result.stdout + result.stderr
    assert skill.read_text().endswith("Local rule\n")
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert manifest["skills"]["orchi-core"] == installation.inventory(tmp_path / ".claude/skills/orchi-core")


@pytest.mark.parametrize("argv", [["--agents", "claude"], ["--global"]])
def test_cli_rejects_removed_selection_and_mixed_scope_without_mutation(tmp_path, argv):
    with pytest.raises(SystemExit):
        installation.main(["--project", str(tmp_path), *argv])
    assert not list(tmp_path.iterdir())


def test_uninstall_refuses_locally_modified_runtime(tmp_path):
    installation.install(tmp_path)
    (tmp_path / ".claude/skills/orchi-core/SKILL.md").write_text("Local customization")
    with pytest.raises(ValueError, match="Modified skill"):
        installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "CLAUDE.md").exists()


def test_uninstall_without_manifest_is_refused(tmp_path):
    with pytest.raises(ValueError, match="nothing can be safely removed"):
        installation.install(tmp_path, uninstall=True)


@pytest.mark.parametrize("uninstall", [False, True])
def test_deleted_managed_instructions_are_dropped_from_the_manifest(tmp_path, uninstall):
    installation.install(tmp_path)
    (tmp_path / "CLAUDE.md").unlink()
    result = installation.install(tmp_path, uninstall=uninstall)
    assert result["status"] == ("removed" if uninstall else "installed")
    if uninstall:
        assert not (tmp_path / MANIFEST).exists() and not (tmp_path / "CLAUDE.md").exists()
    else:
        assert "Orchi workflow" in (tmp_path / "CLAUDE.md").read_text()
        assert installation.install(tmp_path)["status"] == "unchanged"


def test_global_staging_and_backup_stay_inside_home(tmp_path, monkeypatch):
    home = tmp_path / "home"; home.mkdir()
    (home / ".claude").mkdir()
    (home / ".claude/CLAUDE.md").write_text("User instructions")
    original_mkdtemp = installation.tempfile.mkdtemp
    def check_staging(*args, **kwargs):
        assert kwargs["dir"] == home
        return original_mkdtemp(*args, **kwargs)
    monkeypatch.setattr(installation.tempfile, "mkdtemp", check_staging)
    result = installation.install(home, global_scope=True)
    assert Path(result["backup"]).parent == home


def test_global_cli_uses_home_without_editing_current_project(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"; home.mkdir()
    project = tmp_path / "project"; project.mkdir()
    monkeypatch.setattr(installation.Path, "home", lambda: home)
    monkeypatch.chdir(project)
    assert installation.main(["--global"]) == 0
    assert not list(project.iterdir())
    assert (home / ".claude/skills/orchi-core/SKILL.md").is_file()
    assert json.loads((home / MANIFEST).read_text())["scope"] == "user"


def test_manifest_scope_mismatch_is_refused(tmp_path):
    installation.install(tmp_path)
    with pytest.raises(ValueError, match="wrong scope"):
        installation.install(tmp_path, global_scope=True)


def test_unmanaged_shared_skill_is_left_alone(tmp_path):
    folder = tmp_path / ".agents/skills/orchi"; folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("Skill for another assistant")
    installation.install(tmp_path)
    assert (folder / "SKILL.md").read_text() == "Skill for another assistant"


# The former shared layout: one copy of each skill in .agents/skills/, Claude links to it, root AGENTS.md
# instructions imported by CLAUDE.md, Copilot and Codex registrations, and a Codex nesting block.
SHARED_SKILLS = ("orchi", "orchi-plan", "orchi-deliver", "orchi-work")
INSTRUCTIONS = "<!-- orchi:begin -->\n## Orchi workflow\n\nRead `.agents/skills/orchi/SKILL.md`.\n<!-- orchi:end -->"
CODEX_BLOCK = "# orchi:begin\n[agents]\nmax_depth = 3\n# orchi:end"


def write_shared_installation(root, github=False, docs_workflow=True):
    skills, files = {}, {}
    (root / ".claude/skills").mkdir(parents=True)
    for name in SHARED_SKILLS:
        folder = root / ".agents/skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("Shared " + name)
        skills[name] = installation.inventory(folder)
        (root / ".claude/skills" / name).symlink_to("../../.agents/skills/" + name, target_is_directory=True)
    for relative, text in {**{f".claude/agents/{name}.md": "claude " + name for name in ROLES},
                           **{f".codex/agents/{name}.toml": "codex " + name for name in ROLES}}.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text)
        files[relative] = installation.digest(root / relative)
    sections = {"AGENTS.md": ("# Team rules", INSTRUCTIONS), ".github/copilot-instructions.md": ("Copilot rules", INSTRUCTIONS),
                "CLAUDE.md": ("Claude rules", "<!-- orchi:begin -->\n# Shared Orchi instructions\n\n@AGENTS.md\n<!-- orchi:end -->")}
    instructions = {}
    for relative, (user, block) in sections.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(user + "\n\n" + block)
        instructions[relative] = {"block": block, "separator": "\n\n", "existed": True}
    (root / ".codex/config.toml").write_text('model = "operator-model"\n' + CODEX_BLOCK + "\n")
    config = {".codex/config.toml": {"block": CODEX_BLOCK, "separator": "", "existed": True}}
    manifest = {"version": "0.6.0", "scope": "project", "agents": ["codex", "copilot", "claude"], "github": github,
                "docs_workflow": docs_workflow, "skills": skills, "instructions": instructions, "files": files,
                "config": config, "links": {f".claude/skills/{name}": f"../../.agents/skills/{name}" for name in SHARED_SKILLS}}
    (root / ".agents/.orchi-install.json").write_text(json.dumps(manifest))


def test_shared_layout_migrates_to_claude_code_only(tmp_path):
    write_shared_installation(tmp_path)
    result = installation.install(tmp_path)
    assert result["status"] == "installed" and result["version"]["installed"] == "0.6.0" and result["notes"] == []
    assert not (tmp_path / ".agents/.orchi-install.json").exists() and not list((tmp_path / ".agents/skills").iterdir())
    assert sorted(p.name for p in (tmp_path / ".claude/skills").glob("orchi*")) == sorted(SKILLS)
    for name in SKILLS:
        folder = tmp_path / ".claude/skills" / name
        assert not folder.is_symlink() and installation.inventory(folder) == installation.inventory(installation.SOURCE / name)
    assert not list((tmp_path / ".codex/agents").iterdir())
    assert sorted(p.name for p in (tmp_path / ".claude/agents").glob("orchi-*")) == [name + ".md" for name in ROLES]
    assert "{{" not in (tmp_path / ".claude/agents/orchi-scout.md").read_text()
    assert (tmp_path / "AGENTS.md").read_text() == "# Team rules"
    assert (tmp_path / ".github/copilot-instructions.md").read_text() == "Copilot rules"
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert claude.startswith("Claude rules\n\n<!-- orchi:begin -->\n## Orchi workflow") and "@AGENTS.md" not in claude
    assert (tmp_path / ".codex/config.toml").read_text() == 'model = "operator-model"\n'
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert set(manifest) == {"version", "scope", "github", "docs_workflow", "skills", "instructions", "files", "impeccable"}
    assert list(manifest["instructions"]) == [".gitignore", "CLAUDE.md"]
    assert (Path(result["backup"]) / ".agents/skills/orchi-work/SKILL.md").read_text() == "Shared orchi-work"
    assert installation.install(tmp_path)["status"] == "unchanged"
    installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "CLAUDE.md").read_text() == "Claude rules"


def test_shared_layout_keeps_github_choices(tmp_path, labels):
    write_shared_installation(tmp_path, github=True, docs_workflow=False)
    result = installation.install(tmp_path)
    assert result["github"] is True and result["docs_workflow"] is False
    assert (tmp_path / ".github/ISSUE_TEMPLATE/orchi-task.yml").is_file()
    assert not (tmp_path / ".github/workflows/orchi-docs.yml").exists()


def test_shared_layout_preserves_edited_skill_until_replace(tmp_path):
    write_shared_installation(tmp_path)
    (tmp_path / ".agents/skills/orchi-work/SKILL.md").write_text("User edit")
    with pytest.raises(ValueError, match=".agents/skills/orchi-work"):
        installation.install(tmp_path)
    assert (tmp_path / ".agents/.orchi-install.json").exists() and (tmp_path / ".claude/skills/orchi").is_symlink()
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".agents/skills/orchi-work/SKILL.md").read_text() == "User edit"
    assert not (tmp_path / ".agents/skills/orchi-work").exists()


def test_shared_layout_preserves_edited_codex_agent_until_replace(tmp_path):
    write_shared_installation(tmp_path)
    (tmp_path / ".codex/agents/orchi-scout.toml").write_text("Local agent edit")
    assert installation.install(tmp_path, dry=True)["conflicts"] == [".codex/agents/orchi-scout.toml"]
    with pytest.raises(ValueError, match="orchi-scout.toml"):
        installation.install(tmp_path)
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".codex/agents/orchi-scout.toml").read_text() == "Local agent edit"


def test_shared_layout_leaves_an_edited_codex_block_with_a_note(tmp_path):
    write_shared_installation(tmp_path)
    config = tmp_path / ".codex/config.toml"
    config.write_text(config.read_text().replace("max_depth = 3", "max_depth = 4"))
    before = config.read_bytes()
    result = installation.install(tmp_path)
    assert config.read_bytes() == before
    assert result["notes"] == ["Orchi no longer manages the edited block in .codex/config.toml; remove it by hand if unused."]


def test_shared_codex_config_created_by_orchi_is_removed(tmp_path):
    write_shared_installation(tmp_path)
    (tmp_path / ".codex/config.toml").write_text(CODEX_BLOCK + "\n")
    manifest_path = tmp_path / ".agents/.orchi-install.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["config"][".codex/config.toml"]["existed"] = False
    manifest_path.write_text(json.dumps(manifest))
    installation.install(tmp_path)
    assert not (tmp_path / ".codex/config.toml").exists()


def test_shared_layout_can_be_uninstalled_directly(tmp_path):
    write_shared_installation(tmp_path)
    assert installation.install(tmp_path, uninstall=True)["status"] == "removed"
    assert not (tmp_path / ".agents/.orchi-install.json").exists() and not (tmp_path / MANIFEST).exists()
    assert not list((tmp_path / ".claude/skills").iterdir()) and not list((tmp_path / ".claude/agents").iterdir())
    assert (tmp_path / "CLAUDE.md").read_text() == "Claude rules"
    assert (tmp_path / "AGENTS.md").read_text() == "# Team rules"


def test_shared_layout_with_a_foreign_link_is_refused(tmp_path):
    write_shared_installation(tmp_path)
    link = tmp_path / ".claude/skills/orchi"
    link.unlink()
    link.symlink_to("../elsewhere", target_is_directory=True)
    with pytest.raises(ValueError, match="Conflicting skill link"):
        installation.install(tmp_path, replace=True)


def test_version_reports_a_shared_layout_installation(tmp_path, capsys):
    write_shared_installation(tmp_path)
    assert installation.main(["--project", str(tmp_path), "--version"]) == 0
    assert json.loads(capsys.readouterr().out)["installed"] == "0.6.0"


@pytest.fixture
def labels(monkeypatch):
    calls = []
    monkeypatch.setattr(installation, "ensure_labels", lambda root: calls.append(root) or {"created": ["Epic"]})
    return calls


def test_github_setup_installs_managed_files_and_persists(tmp_path, labels):
    result = installation.install(tmp_path, github=True)
    assert result["labels"] == {"created": ["Epic"]} and labels == [tmp_path.resolve()]
    for relative in ("ISSUE_TEMPLATE/orchi-epic.yml", "ISSUE_TEMPLATE/orchi-task.yml",
                     "ISSUE_TEMPLATE/orchi-initiative.yml", "ISSUE_TEMPLATE/orchi-exploration.yml",
                     "workflows/orchi-docs.yml", "workflows/orchi-design.yml", "workflows/orchi-standards.yml"):
        assert (tmp_path / ".github" / relative).is_file()
    template = (tmp_path / ".github/pull_request_template.md").read_text()
    assert "## Documentation impact" in template and "## Merge risk" in template
    # A later installation without the flag keeps the GitHub setup.
    assert installation.install(tmp_path)["github"] is True
    installation.install(tmp_path, uninstall=True)
    assert not (tmp_path / ".github").exists() or not list((tmp_path / ".github").rglob("*.*"))


def test_github_setup_extends_existing_pr_template_and_preserves_edits(tmp_path, labels):
    template = tmp_path / ".github/PULL_REQUEST_TEMPLATE.md"
    template.parent.mkdir(parents=True)
    template.write_text("Team checklist\n")
    installation.install(tmp_path, github=True)
    text = template.read_text()
    assert text.startswith("Team checklist\n") and text.count("<!-- orchi:begin -->") == 1
    assert sorted(p.name for p in template.parent.iterdir() if p.is_file()) == ["PULL_REQUEST_TEMPLATE.md"]
    workflow = tmp_path / ".github/workflows/orchi-docs.yml"
    workflow.write_text("# customized\n")
    with pytest.raises(ValueError, match="orchi-docs.yml"):
        installation.install(tmp_path)
    with pytest.raises(ValueError, match="Modified managed file"):
        installation.install(tmp_path, uninstall=True)
    installation.install(tmp_path, replace=True)
    assert "knowledge.py impact" in workflow.read_text()
    installation.install(tmp_path, uninstall=True)
    assert template.read_text() == "Team checklist\n"


def test_github_setup_refuses_unmanaged_file_and_global_scope(tmp_path, labels):
    workflow = tmp_path / ".github/workflows/orchi-docs.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("user workflow")
    with pytest.raises(ValueError, match="differs"):
        installation.install(tmp_path, github=True)
    assert workflow.read_text() == "user workflow" and not (tmp_path / ".claude").exists()
    with pytest.raises(ValueError, match="--global"):
        installation.install(tmp_path / ".github", github=True, global_scope=True)


def test_label_setup_reports_unavailable_github(tmp_path, monkeypatch):
    def missing(*args, **kwargs):
        raise OSError("gh not found")
    monkeypatch.setattr(installation.subprocess, "run", missing)
    result = installation.ensure_labels(tmp_path)
    assert result["created"] == [] and "gh not found" in result["error"]


def test_dry_run_reports_conflicts_instead_of_failing(tmp_path):
    installation.install(tmp_path)
    (tmp_path / ".claude/skills/orchi-core/SKILL.md").write_text("Local edit")
    result = installation.install(tmp_path, dry=True)
    assert result["conflicts"] == ["orchi-core"] and result["requires_replace"] is True
    assert (tmp_path / ".claude/skills/orchi-core/SKILL.md").read_text() == "Local edit"


def test_manifest_records_version_and_cli_reports_upgrade(tmp_path, capsys):
    from orchi_core.agents import VERSION
    installation.install(tmp_path)
    assert json.loads((tmp_path / MANIFEST).read_text())["version"] == VERSION
    assert installation.main(["--project", str(tmp_path), "--version"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == {"installed": VERSION, "bundle": VERSION, "upgrade": "npx --yes github:nkhus/orchi"}


def test_agent_files_install_without_github_setup(tmp_path):
    result = installation.install(tmp_path)
    assert result["github"] is False and not (tmp_path / ".github").exists()
    assert (tmp_path / ".claude/agents/orchi-reviewer.md").read_text().startswith("---\nname: orchi-reviewer\n")


def test_edited_agent_file_needs_replace_and_blocks_uninstall(tmp_path):
    relative = ".claude/agents/orchi-implementer.md"
    installation.install(tmp_path)
    target = tmp_path / relative
    rendered = target.read_bytes()
    target.write_text("Local agent edit")
    with pytest.raises(ValueError, match=relative):
        installation.install(tmp_path)
    assert installation.install(tmp_path, dry=True)["conflicts"] == [relative]
    with pytest.raises(ValueError, match="Modified managed file"):
        installation.install(tmp_path, uninstall=True)
    result = installation.install(tmp_path, replace=True)
    assert target.read_bytes() == rendered
    assert (Path(result["backup"]) / relative).read_text() == "Local agent edit"


def test_preexisting_unmanaged_agent_file_is_a_conflict(tmp_path):
    target = tmp_path / ".claude/agents/orchi-scout.md"
    target.parent.mkdir(parents=True)
    target.write_text("Repository-local scout")
    with pytest.raises(ValueError, match="orchi-scout.md"):
        installation.install(tmp_path)
    assert target.read_text() == "Repository-local scout" and not (tmp_path / ".claude/skills").exists()


def test_installed_agents_match_bundled_roles(tmp_path):
    installation.install(tmp_path)
    for role in roles.load_roles():
        assert (tmp_path / ".claude/agents" / (role.name + ".md")).read_text() == roles.render_claude(role, ".claude/skills/orchi-core")


def test_docs_workflow_opt_out_persists_and_can_be_reenabled(tmp_path, labels):
    workflow = tmp_path / ".github/workflows/orchi-docs.yml"
    result = installation.install(tmp_path, github=True, docs_workflow=False)
    assert result["docs_workflow"] is False and not workflow.exists()
    assert (tmp_path / ".github/ISSUE_TEMPLATE/orchi-task.yml").is_file()
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert manifest["docs_workflow"] is False and ".github/workflows/orchi-docs.yml" not in manifest["files"]
    # Later runs keep the choice until it is reversed explicitly.
    assert installation.install(tmp_path)["docs_workflow"] is False and not workflow.exists()
    assert installation.install(tmp_path)["status"] == "unchanged"
    installation.install(tmp_path, docs_workflow=True)
    assert "knowledge.py impact" in workflow.read_text()
    assert installation.install(tmp_path)["docs_workflow"] is True
    installation.install(tmp_path, uninstall=True)
    assert not workflow.exists() and not (tmp_path / ".github/ISSUE_TEMPLATE/orchi-task.yml").exists()


def test_docs_workflow_opt_out_removes_an_unmodified_installed_workflow(tmp_path, labels):
    installation.install(tmp_path, github=True)
    workflow = tmp_path / ".github/workflows/orchi-docs.yml"
    assert workflow.is_file()
    result = installation.install(tmp_path, docs_workflow=False)
    assert ".github/workflows/orchi-docs.yml" in result["changes"] and not workflow.exists()
    assert (tmp_path / ".github/ISSUE_TEMPLATE/orchi-epic.yml").is_file()


def test_docs_workflow_opt_out_of_an_edited_workflow_is_a_conflict(tmp_path, labels):
    installation.install(tmp_path, github=True)
    workflow = tmp_path / ".github/workflows/orchi-docs.yml"
    workflow.write_text("# customized\n")
    with pytest.raises(ValueError, match="orchi-docs.yml"):
        installation.install(tmp_path, docs_workflow=False)
    assert workflow.read_text() == "# customized\n"
    assert installation.install(tmp_path, docs_workflow=False, dry=True)["conflicts"] == [".github/workflows/orchi-docs.yml"]
    result = installation.install(tmp_path, docs_workflow=False, replace=True)
    assert not workflow.exists() and (Path(result["backup"]) / ".github/workflows/orchi-docs.yml").read_text() == "# customized\n"


def test_manifest_without_docs_workflow_field_keeps_the_workflow(tmp_path, labels):
    installation.install(tmp_path, github=True)
    manifest_path = tmp_path / MANIFEST
    manifest = json.loads(manifest_path.read_text())
    del manifest["docs_workflow"]
    manifest_path.write_text(json.dumps(manifest))
    result = installation.install(tmp_path)
    assert result["docs_workflow"] is True and (tmp_path / ".github/workflows/orchi-docs.yml").is_file()


def test_cli_docs_workflow_flags(tmp_path, labels, capsys):
    assert installation.main(["--project", str(tmp_path), "--github", "--no-docs-workflow"]) == 0
    assert json.loads(capsys.readouterr().out)["docs_workflow"] is False
    assert not (tmp_path / ".github/workflows/orchi-docs.yml").exists()
    assert installation.main(["--project", str(tmp_path), "--docs-workflow"]) == 0
    assert json.loads(capsys.readouterr().out)["docs_workflow"] is True
    assert (tmp_path / ".github/workflows/orchi-docs.yml").is_file()
    with pytest.raises(SystemExit):
        installation.main(["--project", str(tmp_path), "--docs-workflow", "--no-docs-workflow"])


def test_clean_update_leaves_no_backup(tmp_path):
    installation.install(tmp_path)
    # Simulate an older, unmodified installed version of a managed agent.
    agent = tmp_path / ".claude/agents/orchi-scout.md"
    agent.write_text("older managed version\n")
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    manifest["files"][".claude/agents/orchi-scout.md"] = hashlib.sha256(agent.read_bytes()).hexdigest()
    (tmp_path / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
    result = installation.install(tmp_path)
    assert result["status"] == "installed" and result["backup"] is None
    assert not list(tmp_path.parent.glob(tmp_path.name + "-orchi-backup-*"))
    assert agent.read_text() != "older managed version\n"


def test_dry_run_lists_the_labels_github_setup_would_create(tmp_path, monkeypatch):
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps([{"name": "Task"}, {"name": "epic"}]), stderr="")
    monkeypatch.setattr(installation.subprocess, "run", fake_run)
    result = installation.install(tmp_path, github=True, dry=True)
    assert result["labels"]["create"] == [name for name in installation.LABELS if name not in ("Task", "Epic")]
    assert all(args[:3] == ["gh", "label", "list"] for args in calls)
    assert not (tmp_path / ".github").exists()

    def failing(args, **kwargs):
        raise OSError("gh not found")
    monkeypatch.setattr(installation.subprocess, "run", failing)
    planned = installation.install(tmp_path, github=True, dry=True)["labels"]
    assert planned["create"] == list(installation.LABELS) and "gh not found" in planned["error"]


def retired_skill(tmp_path, text="---\nname: orchi-planner\n---\nFormer hub\n", global_scope=False):
    """Record a skill that an earlier version installed and this one no longer ships."""
    installation.install(tmp_path, global_scope=global_scope)
    folder = tmp_path / ".claude/skills/orchi-planner"
    folder.mkdir()
    (folder / "SKILL.md").write_text(text)
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    manifest["skills"]["orchi-planner"] = installation.inventory(folder)
    (tmp_path / MANIFEST).write_text(json.dumps(manifest))
    return folder


@pytest.mark.parametrize("global_scope", [False, True])
def test_retired_skill_is_removed_on_update(tmp_path, global_scope):
    folder = retired_skill(tmp_path, global_scope=global_scope)
    planned = installation.install(tmp_path, global_scope=global_scope, dry=True)
    assert "orchi-planner" in planned["install"] and folder.is_dir()
    result = installation.install(tmp_path, global_scope=global_scope)
    assert "orchi-planner" in result["install"] and not folder.exists()
    assert "orchi-planner" not in json.loads((tmp_path / MANIFEST).read_text())["skills"]


def test_retired_skill_is_removed_on_uninstall(tmp_path):
    folder = retired_skill(tmp_path)
    installation.install(tmp_path, uninstall=True)
    assert not folder.exists() and not (tmp_path / MANIFEST).exists()


def test_edited_retired_skill_blocks_uninstall(tmp_path):
    folder = retired_skill(tmp_path)
    (folder / "SKILL.md").write_text("Local edit")
    with pytest.raises(ValueError, match="Modified skill must be preserved"):
        installation.install(tmp_path, uninstall=True)
    assert (folder / "SKILL.md").read_text() == "Local edit"


def test_edited_retired_skill_needs_replace(tmp_path):
    folder = retired_skill(tmp_path)
    (folder / "SKILL.md").write_text("Local edit")
    with pytest.raises(ValueError, match=".claude/skills/orchi-planner"):
        installation.install(tmp_path)
    result = installation.install(tmp_path, replace=True)
    assert not folder.exists()
    assert (Path(result["backup"]) / ".claude/skills/orchi-planner/SKILL.md").read_text() == "Local edit"


def test_impeccable_is_installed_pinned_without_hooks_and_telemetry(tmp_path, fake_node):
    result = installation.install(tmp_path)
    assert result["impeccable"] == {"version": installation.IMPECCABLE, "installed": installation.IMPECCABLE}
    (call,) = npx_calls(fake_node)
    assert call.split() == ["--yes", "impeccable@" + installation.IMPECCABLE, "install", "-y", "--providers=claude",
                            "--scope=project", "--no-hooks"]
    assert json.loads((tmp_path / ".impeccable/config.json").read_text()) == {"telemetry": False}
    ignore = (tmp_path / ".gitignore").read_text()
    assert ignore.startswith("# orchi:begin\n") and ".impeccable/mocks/" in ignore and "**/skills/impeccable/scripts/bin/" in ignore
    assert json.loads((tmp_path / MANIFEST).read_text())["impeccable"] == installation.IMPECCABLE
    assert installation.install(tmp_path)["status"] == "unchanged" and len(npx_calls(fake_node)) == 1
    installation.install(tmp_path, uninstall=True)
    assert not (tmp_path / ".gitignore").exists() and (tmp_path / ".impeccable/config.json").is_file()


def test_global_impeccable_goes_to_the_user_scope(tmp_path, fake_node):
    installation.install(tmp_path, global_scope=True)
    assert "--scope=global" in npx_calls(fake_node)[0].split()
    assert json.loads((tmp_path / ".impeccable/config.json").read_text()) == {"telemetry": False}
    assert not (tmp_path / ".gitignore").exists()


def test_missing_or_old_node_fails_before_any_change(tmp_path, monkeypatch, fake_node):
    (tmp_path / "CLAUDE.md").write_text("Original")
    monkeypatch.setenv("FAKE_NODE_VERSION", "v18.18.2")
    with pytest.raises(ValueError, match="Node.js v18.18.2 is too old"):
        installation.install(tmp_path)
    monkeypatch.setattr(installation.shutil, "which", lambda name: None)
    with pytest.raises(ValueError, match="Node.js is missing"):
        installation.install(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["CLAUDE.md"] and not npx_calls(fake_node)


def test_existing_telemetry_choice_and_config_are_kept(tmp_path):
    config = tmp_path / ".impeccable/config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"buildPath": "code"}))
    installation.install(tmp_path)
    assert json.loads(config.read_text()) == {"buildPath": "code", "telemetry": False}
    config.write_text(json.dumps({"telemetry": True}))
    installation.install(tmp_path)
    assert json.loads(config.read_text()) == {"telemetry": True}


def test_users_own_impeccable_is_kept_until_replace(tmp_path, fake_node):
    skill = tmp_path / ".claude/skills/impeccable/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: impeccable\nversion: 4.5.0\n---\n")
    result = installation.install(tmp_path)
    assert installation.impeccable_version(tmp_path) == "4.5.0" and not npx_calls(fake_node)
    assert any("Impeccable 4.5.0 was installed outside Orchi" in note for note in result["notes"])
    assert "impeccable" not in json.loads((tmp_path / MANIFEST).read_text())
    installation.install(tmp_path, replace=True)
    assert installation.impeccable_version(tmp_path) == installation.IMPECCABLE
    assert npx_calls(fake_node)[0].split()[-1] == "--force"


def test_orchi_updates_the_impeccable_it_installed(tmp_path, fake_node):
    installation.install(tmp_path)
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    manifest["impeccable"] = "4.7.0"
    (tmp_path / MANIFEST).write_text(json.dumps(manifest))
    (tmp_path / ".claude/skills/impeccable/SKILL.md").write_text("---\nversion: 4.7.0\n---\n")
    installation.install(tmp_path)
    assert installation.impeccable_version(tmp_path) == installation.IMPECCABLE and len(npx_calls(fake_node)) == 2


def test_impeccable_failure_is_reported_after_orchi_installs(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_NPX_FAIL", "registry unreachable")
    assert installation.main(["--project", str(tmp_path)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert "registry unreachable" in report["impeccable"]["error"] and report["status"] == "installed"
    monkeypatch.delenv("FAKE_NPX_FAIL")
    assert installation.main(["--project", str(tmp_path)]) == 0


def test_dry_run_plans_impeccable_without_running_npx(tmp_path, fake_node):
    planned = installation.install(tmp_path, dry=True)
    assert planned["impeccable"] == {"version": installation.IMPECCABLE, "installed": None, "action": "install"}
    assert not npx_calls(fake_node) and not list(tmp_path.iterdir())


def test_design_workflow_pins_the_installed_impeccable():
    workflow = (installation.GITHUB_ASSETS / "workflows/orchi-design.yml").read_text()
    assert f"npx --yes impeccable@{installation.IMPECCABLE} detect --github" in workflow
    assert "design" in installation.LABELS


def test_update_moves_the_core_skill_to_orchi_core_and_the_entry_to_orchi(tmp_path):
    installation.install(tmp_path)
    skills = tmp_path / ".claude/skills"
    # Lay out the earlier names: the core skill at orchi/ and the pool entry at orchi-pm/.
    shutil.move(str(skills / "orchi"), str(skills / "orchi-pm"))
    shutil.move(str(skills / "orchi-core"), str(skills / "orchi"))
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    manifest["skills"] = {path.name: installation.inventory(path) for path in skills.iterdir() if path.name != "impeccable"}
    (tmp_path / MANIFEST).write_text(json.dumps(manifest))
    result = installation.install(tmp_path)
    assert result["status"] == "installed" and not result.get("backup")
    assert (skills / "orchi/SKILL.md").read_text().startswith("---\nname: orchi\n")
    assert (skills / "orchi-core/SKILL.md").read_text().startswith("---\nname: orchi-core\n")
    assert not (skills / "orchi-pm").exists()
    assert "`.claude/skills/orchi-core/SKILL.md`" in (tmp_path / "CLAUDE.md").read_text()
