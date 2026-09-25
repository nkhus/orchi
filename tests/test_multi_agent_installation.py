"""Installation behavior in disposable project and home directories."""
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from orchi_core import installation
from orchi_core.agents import AGENTS, LEGACY_SKILLS, SKILLS

COMBINATIONS = [list(items) for count in (1, 2, 3) for items in itertools.combinations(AGENTS, count)]


@pytest.mark.parametrize("agents", COMBINATIONS)
@pytest.mark.parametrize("global_scope", [False, True])
def test_each_selection_and_scope(tmp_path, agents, global_scope):
    result = installation.install(tmp_path, agents=agents, global_scope=global_scope)
    assert result["agents"] == agents
    for name in SKILLS:
        assert (tmp_path / ".agents/skills" / name / "SKILL.md").is_file()
        if "claude" in agents:
            link = tmp_path / ".claude/skills" / name
            assert link.is_symlink() and link.resolve() == tmp_path / ".agents/skills" / name
    if not global_scope:
        assert "Orchi workflow" in (tmp_path / "AGENTS.md").read_text()
        assert (tmp_path / "CLAUDE.md").exists() == ("claude" in agents)
        assert (tmp_path / ".github/copilot-instructions.md").exists() == ("copilot" in agents)
    else:
        assert not (tmp_path / "AGENTS.md").exists()
        for agent, relative in {"codex": ".codex/AGENTS.md", "copilot": ".copilot/copilot-instructions.md", "claude": ".claude/CLAUDE.md"}.items():
            assert (tmp_path / relative).exists() == (agent in agents)
    assert installation.install(tmp_path, agents=agents, global_scope=global_scope)["status"] == "unchanged"


def test_add_selection_and_uninstall_preserves_user_content(tmp_path):
    existing = {"AGENTS.md": b"# User\r\nRules without final newline", "CLAUDE.md": b"My Claude rules\n",
                ".github/copilot-instructions.md": b"My Copilot rules\n"}
    for name, content in existing.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    installation.install(tmp_path, agents=["copilot"])
    result = installation.install(tmp_path, agents=["claude"])
    assert result["agents"] == ["copilot", "claude"]
    for name, content in existing.items():
        assert (tmp_path / name).read_bytes().startswith(content)
    assert (tmp_path / "CLAUDE.md").read_text().count("@AGENTS.md") == 1
    with (tmp_path / "AGENTS.md").open("ab") as file:
        file.write(b"\nLater user rule\n")
    installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "AGENTS.md").read_bytes() == existing["AGENTS.md"] + b"\nLater user rule\n"
    for name in ("CLAUDE.md", ".github/copilot-instructions.md"):
        assert (tmp_path / name).read_bytes() == existing[name]
    assert not (tmp_path / ".agents/.orchi-install.json").exists()
    assert not list((tmp_path / ".claude/skills").iterdir())


def test_project_can_move_with_all_claude_references(tmp_path):
    project = tmp_path / "before"; project.mkdir()
    installation.install(project, agents=["all"])
    project.rename(tmp_path / "after")
    moved = tmp_path / "after"
    for name in SKILLS:
        assert (moved / ".claude/skills" / name / "SKILL.md").is_file()
        assert (moved / ".claude/skills" / name / "scripts/knowledge.py").is_file()


@pytest.mark.parametrize("relative", ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"])
def test_edited_managed_section_is_not_silently_overwritten(tmp_path, relative):
    installation.install(tmp_path, agents=["all"])
    target = tmp_path / relative
    target.write_text(target.read_text().replace("Orchi", "Customized Orchi", 1))
    before = target.read_bytes()
    for kwargs in ({"replace": True}, {"uninstall": True}):
        with pytest.raises(ValueError, match="instruction section was edited"):
            installation.install(tmp_path, **kwargs)
        assert target.read_bytes() == before


def test_dry_run_reports_all_files_without_writes(tmp_path):
    result = installation.install(tmp_path, dry=True, agents=["copilot,claude"])
    assert "AGENTS.md" in result["changes"] and "CLAUDE.md" in result["changes"]
    assert ".claude/skills/orchi" in result["changes"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("relative", [".claude", ".claude/skills", "AGENTS.md", ".github"])
def test_symlink_escape_refused_before_any_mutation(tmp_path, relative):
    project = tmp_path / "project"; project.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    target = project / relative; target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        installation.install(project, agents=["all"])
    assert not (project / ".agents").exists() and not list(outside.iterdir())


def test_existing_claude_import_symlink_is_preserved(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Existing rules")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    installation.install(tmp_path, agents=["claude"])
    installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert (tmp_path / "AGENTS.md").read_text() == "Existing rules"


@pytest.mark.parametrize("relative", [".github/skills/orchi", ".claude/skills/orchi"])
def test_preexisting_conflicting_skill_preserved(tmp_path, relative):
    target = tmp_path / relative; target.mkdir(parents=True)
    (target / "SKILL.md").write_text("User skill")
    with pytest.raises(ValueError):
        installation.install(tmp_path, agents=["all"], replace=True)
    assert (target / "SKILL.md").read_text() == "User skill"
    assert not (tmp_path / "AGENTS.md").exists()


def test_failure_after_instructions_rolls_back_all_changes(tmp_path, monkeypatch):
    (tmp_path / "AGENTS.md").write_text("Original")
    original_move = installation.shutil.move
    def fail_last_file(source, destination):
        if ".orchi-stage-" in str(source) and str(source).endswith(".orchi-install.json"):
            raise OSError("Injected manifest failure")
        return original_move(source, destination)
    monkeypatch.setattr(installation.shutil, "move", fail_last_file)
    with pytest.raises(OSError, match="Injected"):
        installation.install(tmp_path, agents=["all"])
    assert (tmp_path / "AGENTS.md").read_text() == "Original"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["AGENTS.md"]


def test_installed_installer_adds_agent_without_source_checkout(tmp_path):
    installation.install(tmp_path, agents=["copilot"])
    script = tmp_path / ".agents/skills/orchi/scripts/orchi_install.py"
    result = subprocess.run([sys.executable, str(script), "--project", str(tmp_path), "--agents", "claude"],
                            capture_output=True, text=True, cwd=tmp_path,
                            env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"})
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["agents"] == ["copilot", "claude"]
    assert (tmp_path / ".claude/skills/orchi/scripts/knowledge.py").is_file()


def test_cli_rejects_invalid_selection_and_scope_without_mutation(tmp_path, capsys):
    assert installation.main(["--project", str(tmp_path), "--agents", "unknown"]) == 2
    assert not list(tmp_path.iterdir())
    with pytest.raises(SystemExit):
        installation.main(["--project", str(tmp_path), "--global"])


def test_uninstall_refuses_locally_modified_runtime(tmp_path):
    installation.install(tmp_path, agents=["all"])
    (tmp_path / ".agents/skills/orchi/SKILL.md").write_text("Local customization")
    with pytest.raises(ValueError, match="Modified skill"):
        installation.install(tmp_path, uninstall=True)
    assert (tmp_path / "AGENTS.md").exists()


def test_existing_override_instructions_receive_and_release_managed_block(tmp_path):
    override = tmp_path / "AGENTS.override.md"
    override.write_text("Override rules")
    installation.install(tmp_path, agents=["codex"])
    assert "Orchi workflow" in override.read_text()
    installation.install(tmp_path, uninstall=True)
    assert override.read_text() == "Override rules"


def test_global_staging_and_backup_stay_inside_home(tmp_path, monkeypatch):
    home = tmp_path / "home"; home.mkdir()
    (home / ".claude").mkdir()
    (home / ".claude/CLAUDE.md").write_text("User instructions")
    original_mkdtemp = installation.tempfile.mkdtemp
    def check_staging(*args, **kwargs):
        assert kwargs["dir"] == home
        return original_mkdtemp(*args, **kwargs)
    monkeypatch.setattr(installation.tempfile, "mkdtemp", check_staging)
    result = installation.install(home, agents=["claude"], global_scope=True)
    assert Path(result["backup"]).parent == home


def test_interactive_selection_accepts_multiple_numbers(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(installation.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda: "2, 3")
    assert installation.main(["--project", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["agents"] == ["copilot", "claude"]


def test_global_cli_uses_home_without_editing_current_project(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"; home.mkdir()
    project = tmp_path / "project"; project.mkdir()
    monkeypatch.setattr(installation.Path, "home", lambda: home)
    monkeypatch.chdir(project)
    assert installation.main(["--global", "--agents", "copilot,claude"]) == 0
    assert not list(project.iterdir())
    assert (home / ".claude/skills/orchi/SKILL.md").is_file()


def write_legacy_installation(root, edited=None):
    """Simulate a manifest written by the former five-skill installer."""
    skills = {}
    for name in LEGACY_SKILLS:
        folder = root / ".agents/skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("Legacy " + name)
        skills[name] = installation.inventory(folder)
        (root / ".claude/skills").mkdir(parents=True, exist_ok=True)
        (root / ".claude/skills" / name).symlink_to("../../.agents/skills/" + name, target_is_directory=True)
    manifest = {"scope": "project", "agents": ["claude"], "skills": skills, "instructions": {},
                "links": {f".claude/skills/{name}": f"../../.agents/skills/{name}" for name in LEGACY_SKILLS}}
    (root / ".agents/.orchi-install.json").write_text(json.dumps(manifest))
    if edited:
        (root / ".agents/skills" / edited / "SKILL.md").write_text("User edit")


def test_upgrade_removes_unmodified_legacy_stage_skills(tmp_path):
    write_legacy_installation(tmp_path)
    result = installation.install(tmp_path)
    assert result["agents"] == ["claude"]
    for name in LEGACY_SKILLS:
        assert not (tmp_path / ".agents/skills" / name).exists()
        assert not (tmp_path / ".claude/skills" / name).is_symlink()
    assert (tmp_path / ".claude/skills/orchi/SKILL.md").is_file()
    manifest = json.loads((tmp_path / ".agents/.orchi-install.json").read_text())
    assert list(manifest["skills"]) == ["orchi"] and list(manifest["links"]) == [".claude/skills/orchi"]
    assert installation.install(tmp_path)["status"] == "unchanged"


def test_upgrade_updates_unmodified_managed_entrypoint_without_replace(tmp_path):
    write_legacy_installation(tmp_path)
    folder = tmp_path / ".agents/skills/orchi"; folder.mkdir()
    (folder / "SKILL.md").write_text("Former controller entrypoint")
    manifest_path = tmp_path / ".agents/.orchi-install.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["skills"]["orchi"] = installation.inventory(folder)
    manifest_path.write_text(json.dumps(manifest))
    result = installation.install(tmp_path)
    assert result["status"] == "installed"
    assert (folder / "scripts/knowledge.py").is_file()
    assert sorted(p.name for p in (tmp_path / ".agents/skills").iterdir()) == ["orchi"]


def test_upgrade_preserves_edited_legacy_skill_until_replace(tmp_path):
    write_legacy_installation(tmp_path, edited="orchi-plan")
    with pytest.raises(ValueError, match="orchi-plan"):
        installation.install(tmp_path)
    assert (tmp_path / ".agents/skills/orchi-plan/SKILL.md").read_text() == "User edit"
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".agents/skills/orchi-plan/SKILL.md").read_text() == "User edit"
    assert not (tmp_path / ".agents/skills/orchi-plan").exists()


def test_unmanaged_skill_with_legacy_name_is_left_alone(tmp_path):
    folder = tmp_path / ".agents/skills/orchi-plan"; folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("User skill")
    installation.install(tmp_path, agents=["codex"])
    assert (folder / "SKILL.md").read_text() == "User skill"
