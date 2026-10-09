"""Installation behavior in disposable project and home directories."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from orchi_core import installation, roles
from orchi_core.agents import SKILLS

ROLES = ("orchi-designer", "orchi-fixer", "orchi-implementer", "orchi-reviewer", "orchi-scout")
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
    skill = str(tmp_path.resolve() / ".claude/skills/orchi") if global_scope else ".claude/skills/orchi"
    assert sorted(p.name for p in (tmp_path / ".claude/agents").iterdir()) == [name + ".md" for name in ROLES]
    for path in (tmp_path / ".claude/agents").glob("*.md"):
        text = path.read_text()
        assert "{{" not in text and (f'"{skill}/scripts/' in text or f"`{skill}/references/" in text)
    assert f"`{skill}/SKILL.md`" in instructions.read_text()
    assert installation.install(tmp_path, global_scope=global_scope)["status"] == "unchanged"
    installation.install(tmp_path, global_scope=global_scope, uninstall=True)
    assert not [path for path in (tmp_path / ".claude").rglob("*") if path.is_file()]


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
    assert not list((tmp_path / ".claude/skills").iterdir())


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
    assert "CLAUDE.md" in result["changes"] and ".claude/skills/orchi" in result["changes"]
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
    assert list(json.loads((tmp_path / MANIFEST).read_text())["instructions"]) == ["AGENTS.md"]
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
    (tmp_path / ".claude/skills/orchi").write_text("not a skill")
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
    script = root / ".claude/skills/orchi/scripts/orchi_install.py"
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
    skill = tmp_path / ".claude/skills/orchi/SKILL.md"
    skill.write_text(skill.read_text() + "\nLocal rule\n")
    result = run_installed_copy(tmp_path)
    assert result.returncode == 2 and "Existing Orchi content differs: orchi." in json.loads(result.stdout)["error"]
    assert json.loads(run_installed_copy(tmp_path, "--dry-run").stdout)["conflicts"] == ["orchi"]
    assert manifest_path.read_bytes() == recorded
    # The next upstream upgrade still sees the edit instead of overwriting it.
    with pytest.raises(ValueError, match="differs: orchi"):
        installation.install(tmp_path)
    assert skill.read_text().endswith("Local rule\n")


def test_installed_copy_replace_accepts_the_edited_skill(tmp_path):
    installation.install(tmp_path)
    skill = tmp_path / ".claude/skills/orchi/SKILL.md"
    skill.write_text(skill.read_text() + "\nLocal rule\n")
    result = run_installed_copy(tmp_path, "--replace-orchi")
    assert result.returncode == 0, result.stdout + result.stderr
    assert skill.read_text().endswith("Local rule\n")
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert manifest["skills"]["orchi"] == installation.inventory(tmp_path / ".claude/skills/orchi")


@pytest.mark.parametrize("argv", [["--agents", "claude"], ["--global"]])
def test_cli_rejects_removed_selection_and_mixed_scope_without_mutation(tmp_path, argv):
    with pytest.raises(SystemExit):
        installation.main(["--project", str(tmp_path), *argv])
    assert not list(tmp_path.iterdir())


def test_uninstall_refuses_locally_modified_runtime(tmp_path):
    installation.install(tmp_path)
    (tmp_path / ".claude/skills/orchi/SKILL.md").write_text("Local customization")
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
    assert (home / ".claude/skills/orchi/SKILL.md").is_file()
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
    assert sorted(p.name for p in (tmp_path / ".claude/skills").iterdir()) == sorted(SKILLS)
    for name in SKILLS:
        folder = tmp_path / ".claude/skills" / name
        assert not folder.is_symlink() and installation.inventory(folder) == installation.inventory(installation.SOURCE / name)
    assert not list((tmp_path / ".codex/agents").iterdir())
    assert sorted(p.name for p in (tmp_path / ".claude/agents").iterdir()) == [name + ".md" for name in ROLES]
    assert "{{" not in (tmp_path / ".claude/agents/orchi-scout.md").read_text()
    assert (tmp_path / "AGENTS.md").read_text() == "# Team rules"
    assert (tmp_path / ".github/copilot-instructions.md").read_text() == "Copilot rules"
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert claude.startswith("Claude rules\n\n<!-- orchi:begin -->\n## Orchi workflow") and "@AGENTS.md" not in claude
    assert (tmp_path / ".codex/config.toml").read_text() == 'model = "operator-model"\n'
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert set(manifest) == {"version", "scope", "github", "docs_workflow", "skills", "instructions", "files"}
    assert list(manifest["instructions"]) == ["CLAUDE.md"]
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
                     "ISSUE_TEMPLATE/orchi-initiative.yml", "workflows/orchi-docs.yml"):
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
    (tmp_path / ".claude/skills/orchi/SKILL.md").write_text("Local edit")
    result = installation.install(tmp_path, dry=True)
    assert result["conflicts"] == ["orchi"] and result["requires_replace"] is True
    assert (tmp_path / ".claude/skills/orchi/SKILL.md").read_text() == "Local edit"


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
        assert (tmp_path / ".claude/agents" / (role.name + ".md")).read_text() == roles.render_claude(role, ".claude/skills/orchi")


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
