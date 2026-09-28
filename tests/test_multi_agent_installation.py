"""Installation behavior in disposable project and home directories."""
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import tomllib

from orchi_core import installation, roles
from orchi_core.agents import AGENTS, LEGACY_SKILLS, SKILLS

ROLES = ("orchi-implementer", "orchi-reviewer", "orchi-scout")

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
    root = tmp_path.resolve()
    skill = str(root / ".agents/skills/orchi") if global_scope else ".agents/skills/orchi"
    claude_agents = sorted(p.name for p in (tmp_path / ".claude/agents").iterdir()) if (tmp_path / ".claude/agents").exists() else []
    codex_agents = sorted(p.name for p in (tmp_path / ".codex/agents").iterdir()) if (tmp_path / ".codex/agents").exists() else []
    assert claude_agents == ([name + ".md" for name in ROLES] if "claude" in agents else [])
    assert codex_agents == ([name + ".toml" for name in ROLES] if "codex" in agents else [])
    for path in [*(tmp_path / ".claude/agents").glob("*.md"), *(tmp_path / ".codex/agents").glob("*.toml")]:
        text = path.read_text()
        assert "{{" not in text and (f'"{skill}/scripts/' in text or f"`{skill}/references/" in text)
    if "codex" in agents:
        implementer = tomllib.loads((tmp_path / ".codex/agents/orchi-implementer.toml").read_text())
        assert f"`{skill}/references/readiness.md`" in implementer["developer_instructions"]
        assert tomllib.loads((tmp_path / ".codex/config.toml").read_text()) == {"agents": {"max_depth": 3}}
    else:
        assert not (tmp_path / ".codex/config.toml").exists()
    trust = "Trust the project in Codex so .codex/config.toml and .codex/agents load."
    assert (trust in result["next_steps"]) == ("codex" in agents and not global_scope)
    assert installation.install(tmp_path, agents=agents, global_scope=global_scope)["status"] == "unchanged"
    installation.install(tmp_path, global_scope=global_scope, uninstall=True)
    for directory in (".claude/agents", ".codex"):
        assert not [path for path in (tmp_path / directory).rglob("*") if path.is_file()]


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
    assert (moved / ".claude/skills/orchi/scripts/knowledge.py").is_file()


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


FORMER_STAGE_SKILLS = ("orchi-plan", "orchi-work", "orchi-review", "orchi-deliver")


def write_legacy_installation(root, edited=None):
    """Simulate a manifest written by the former five-skill installer."""
    skills = {}
    for name in FORMER_STAGE_SKILLS:
        folder = root / ".agents/skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("Legacy " + name)
        skills[name] = installation.inventory(folder)
        (root / ".claude/skills").mkdir(parents=True, exist_ok=True)
        (root / ".claude/skills" / name).symlink_to("../../.agents/skills/" + name, target_is_directory=True)
    manifest = {"scope": "project", "agents": ["claude"], "skills": skills, "instructions": {},
                "links": {f".claude/skills/{name}": f"../../.agents/skills/{name}" for name in FORMER_STAGE_SKILLS}}
    (root / ".agents/.orchi-install.json").write_text(json.dumps(manifest))
    if edited:
        (root / ".agents/skills" / edited / "SKILL.md").write_text("User edit")


def test_upgrade_removes_unmodified_legacy_stage_skills(tmp_path):
    write_legacy_installation(tmp_path)
    result = installation.install(tmp_path)
    assert result["agents"] == ["claude"]
    assert LEGACY_SKILLS == ("orchi-work", "orchi-review")
    for name in LEGACY_SKILLS:
        assert not (tmp_path / ".agents/skills" / name).exists()
        assert not (tmp_path / ".claude/skills" / name).is_symlink()
    for name in SKILLS:
        assert (tmp_path / ".claude/skills" / name / "SKILL.md").is_file()
    manifest = json.loads((tmp_path / ".agents/.orchi-install.json").read_text())
    assert list(manifest["skills"]) == list(SKILLS)
    assert sorted(manifest["links"]) == sorted(f".claude/skills/{name}" for name in SKILLS)
    assert installation.install(tmp_path)["status"] == "unchanged"


def test_upgrade_updates_unmodified_former_entry_skills_in_place(tmp_path):
    write_legacy_installation(tmp_path)
    link = tmp_path / ".claude/skills/orchi-plan"
    result = installation.install(tmp_path)
    assert {"orchi-plan", "orchi-deliver"} <= set(result["install"])
    for name in ("orchi-plan", "orchi-deliver"):
        folder = tmp_path / ".agents/skills" / name
        assert installation.inventory(folder) == installation.inventory(installation.SOURCE / name)
        assert "Legacy" not in (folder / "SKILL.md").read_text()
    assert link.is_symlink() and link.resolve() == tmp_path / ".agents/skills/orchi-plan"
    assert result["backup"] and (Path(result["backup"]) / ".agents/skills/orchi-plan/SKILL.md").read_text() == "Legacy orchi-plan"


def test_unrecorded_repository_entry_skill_needs_replace(tmp_path):
    folder = tmp_path / ".agents/skills/orchi-plan"; folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("Repository-local plan skill")
    with pytest.raises(ValueError, match="orchi-plan"):
        installation.install(tmp_path, agents=["codex"])
    assert (folder / "SKILL.md").read_text() == "Repository-local plan skill"
    result = installation.install(tmp_path, agents=["codex"], replace=True)
    assert (Path(result["backup"]) / ".agents/skills/orchi-plan/SKILL.md").read_text() == "Repository-local plan skill"
    assert "name: orchi-plan" in (folder / "SKILL.md").read_text()


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
    assert sorted(p.name for p in (tmp_path / ".agents/skills").iterdir()) == sorted(SKILLS)


def test_upgrade_preserves_edited_legacy_skill_until_replace(tmp_path):
    write_legacy_installation(tmp_path, edited="orchi-review")
    with pytest.raises(ValueError, match="orchi-review"):
        installation.install(tmp_path)
    assert (tmp_path / ".agents/skills/orchi-review/SKILL.md").read_text() == "User edit"
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".agents/skills/orchi-review/SKILL.md").read_text() == "User edit"
    assert not (tmp_path / ".agents/skills/orchi-review").exists()


def test_upgrade_preserves_edited_former_entry_skill_until_replace(tmp_path):
    write_legacy_installation(tmp_path, edited="orchi-plan")
    with pytest.raises(ValueError, match="orchi-plan"):
        installation.install(tmp_path)
    assert (tmp_path / ".agents/skills/orchi-plan/SKILL.md").read_text() == "User edit"
    result = installation.install(tmp_path, replace=True)
    assert (Path(result["backup"]) / ".agents/skills/orchi-plan/SKILL.md").read_text() == "User edit"
    assert "name: orchi-plan" in (tmp_path / ".agents/skills/orchi-plan/SKILL.md").read_text()


def test_unmanaged_skill_with_legacy_name_is_left_alone(tmp_path):
    folder = tmp_path / ".agents/skills/orchi-work"; folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("User skill")
    installation.install(tmp_path, agents=["codex"])
    assert (folder / "SKILL.md").read_text() == "User skill"


@pytest.fixture
def labels(monkeypatch):
    calls = []
    monkeypatch.setattr(installation, "ensure_labels", lambda root: calls.append(root) or {"created": ["Epic"]})
    return calls


def test_github_setup_installs_managed_files_and_persists(tmp_path, labels):
    result = installation.install(tmp_path, agents=["codex"], github=True)
    assert result["labels"] == {"created": ["Epic"]} and labels == [tmp_path.resolve()]
    for relative in ("ISSUE_TEMPLATE/orchi-epic.yml", "ISSUE_TEMPLATE/orchi-task.yml",
                     "ISSUE_TEMPLATE/orchi-initiative.yml", "workflows/orchi-docs.yml"):
        assert (tmp_path / ".github" / relative).is_file()
    assert "## Documentation impact" in (tmp_path / ".github/pull_request_template.md").read_text()
    # A later installation without the flag keeps the GitHub setup.
    assert installation.install(tmp_path, agents=["claude"])["github"] is True
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
    assert workflow.read_text() == "user workflow" and not (tmp_path / ".agents").exists()
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
    (tmp_path / ".agents/skills/orchi/SKILL.md").write_text("Local edit")
    result = installation.install(tmp_path, dry=True)
    assert result["conflicts"] == ["orchi"] and result["requires_replace"] is True
    assert (tmp_path / ".agents/skills/orchi/SKILL.md").read_text() == "Local edit"


def test_manifest_records_version_and_cli_reports_upgrade(tmp_path, capsys):
    from orchi_core.agents import VERSION
    installation.install(tmp_path)
    assert json.loads((tmp_path / ".agents/.orchi-install.json").read_text())["version"] == VERSION
    assert installation.main(["--project", str(tmp_path), "--version"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == {"installed": VERSION, "bundle": VERSION, "upgrade": "npx --yes github:nkhus/orchi"}


def test_adding_a_host_adds_its_agent_files(tmp_path):
    installation.install(tmp_path, agents=["copilot"])
    assert not (tmp_path / ".claude/agents").exists() and not (tmp_path / ".codex").exists()
    result = installation.install(tmp_path, agents=["claude"])
    assert ".claude/agents/orchi-scout.md" in result["changes"]
    assert not (tmp_path / ".codex").exists()
    installation.install(tmp_path, agents=["codex"])
    assert sorted(p.name for p in (tmp_path / ".codex/agents").iterdir()) == [name + ".toml" for name in ROLES]
    manifest = json.loads((tmp_path / ".agents/.orchi-install.json").read_text())
    assert len([path for path in manifest["files"] if "/agents/" in path]) == 6
    assert list(manifest["config"]) == [".codex/config.toml"]


def test_agent_files_install_without_github_setup(tmp_path):
    result = installation.install(tmp_path, agents=["claude"])
    assert result["github"] is False and not (tmp_path / ".github").exists()
    assert (tmp_path / ".claude/agents/orchi-reviewer.md").read_text().startswith("---\nname: orchi-reviewer\n")


@pytest.mark.parametrize("relative", [".claude/agents/orchi-implementer.md", ".codex/agents/orchi-scout.toml"])
def test_edited_agent_file_needs_replace_and_blocks_uninstall(tmp_path, relative):
    installation.install(tmp_path, agents=["all"])
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
        installation.install(tmp_path, agents=["claude"])
    assert target.read_text() == "Repository-local scout" and not (tmp_path / ".agents").exists()


def test_codex_config_block_preserves_user_settings(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    user = b'model = "operator-model"\r\n\n[profiles.fast]\nmodel_reasoning_effort = "low"'
    config.write_bytes(user)
    installation.install(tmp_path, agents=["codex"])
    text = config.read_text()
    assert text.count("# orchi:begin") == 1
    assert text.endswith("max_depth = 3\n# Add your own settings above this block.\n# orchi:end\n")
    assert tomllib.loads(text)["agents"] == {"max_depth": 3}
    assert tomllib.loads(text)["profiles"] == {"fast": {"model_reasoning_effort": "low"}}
    with config.open("ab") as file:
        file.write(b"\n[mcp_servers.docs]\ncommand = \"docs\"\n")
    installation.install(tmp_path, uninstall=True)
    assert config.read_bytes() == user + b"\n[mcp_servers.docs]\ncommand = \"docs\"\n"
    assert not (tmp_path / ".codex/agents").exists() or not list((tmp_path / ".codex/agents").iterdir())


def test_codex_config_created_by_orchi_is_removed_on_uninstall(tmp_path):
    installation.install(tmp_path, agents=["codex"])
    assert (tmp_path / ".codex/config.toml").is_file()
    installation.install(tmp_path, uninstall=True)
    assert not (tmp_path / ".codex/config.toml").exists()


@pytest.mark.parametrize("existing", ['[agents]\nmax_depth = 5\n', 'agents.max_threads = 4\n'])
def test_existing_agents_table_is_left_to_the_user(tmp_path, existing):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text(existing)
    result = installation.install(tmp_path, agents=["codex"])
    assert config.read_text() == existing
    assert result["notes"] == ["Set max_depth = 3 under [agents] in .codex/config.toml to allow nested Orchi agents."]
    assert (tmp_path / ".codex/agents/orchi-scout.toml").is_file()
    assert json.loads((tmp_path / ".agents/.orchi-install.json").read_text())["config"] == {}
    assert installation.install(tmp_path)["status"] == "unchanged"


def test_user_agents_table_added_later_replaces_the_managed_block(tmp_path):
    installation.install(tmp_path, agents=["codex"])
    config = tmp_path / ".codex/config.toml"
    config.write_text("[agents]\nmax_threads = 2\n\n" + config.read_text())
    result = installation.install(tmp_path)
    assert config.read_text() == "[agents]\nmax_threads = 2\n\n"
    assert result["notes"] and tomllib.loads(config.read_text()) == {"agents": {"max_threads": 2}}


def test_global_note_names_the_home_configuration(tmp_path):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex/config.toml").write_text("[agents]\n")
    result = installation.install(tmp_path, agents=["codex"], global_scope=True)
    assert result["notes"] == ["Set max_depth = 3 under [agents] in ~/.codex/config.toml to allow nested Orchi agents."]


def test_invalid_codex_config_stops_before_mutation(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text("model = \n")
    with pytest.raises(ValueError, match="Invalid TOML in .codex/config.toml"):
        installation.install(tmp_path, agents=["codex"])
    assert config.read_text() == "model = \n" and not (tmp_path / ".agents").exists()


def test_edited_codex_config_block_is_not_overwritten(tmp_path):
    installation.install(tmp_path, agents=["codex"])
    config = tmp_path / ".codex/config.toml"
    config.write_text(config.read_text().replace("max_depth = 3", "max_depth = 4"))
    before = config.read_bytes()
    for kwargs in ({"replace": True}, {"uninstall": True}):
        with pytest.raises(ValueError, match="section was edited"):
            installation.install(tmp_path, **kwargs)
        assert config.read_bytes() == before


def test_codex_block_markers_do_not_confuse_instruction_sections(tmp_path):
    installation.install(tmp_path, agents=["codex", "claude"])
    assert installation.block_span((tmp_path / ".codex/config.toml").read_text()) is None
    assert installation.block_span((tmp_path / "AGENTS.md").read_text()) is not None


def test_installed_agents_match_bundled_roles(tmp_path):
    installation.install(tmp_path, agents=["claude", "codex"])
    for role in roles.load_roles():
        assert (tmp_path / ".claude/agents" / (role.name + ".md")).read_text() == roles.render_claude(role, ".agents/skills/orchi")
        assert (tmp_path / ".codex/agents" / (role.name + ".toml")).read_text() == roles.render_codex(role, ".agents/skills/orchi")


@pytest.mark.parametrize("global_scope", [False, True])
def test_codex_config_is_ignored_without_codex(tmp_path, global_scope):
    outside = tmp_path / "outside.toml"
    outside.write_bytes(b"\xff not utf-8 # orchi:begin")
    home = tmp_path / "root"; (home / ".codex").mkdir(parents=True)
    (home / ".codex/config.toml").symlink_to(outside)
    for agents in (["claude"], ["copilot"]):
        result = installation.install(home, agents=agents, global_scope=global_scope)
        assert ".codex/config.toml" not in result["changes"] and result["notes"] == []
    assert json.loads((home / ".agents/.orchi-install.json").read_text())["config"] == {}
    installation.install(home, global_scope=global_scope, uninstall=True)
    assert (home / ".codex/config.toml").is_symlink() and outside.read_bytes() == b"\xff not utf-8 # orchi:begin"
    with pytest.raises(ValueError, match="symlink"):
        installation.install(home, agents=["codex"], global_scope=global_scope)


def test_preexisting_empty_codex_config_is_kept_on_uninstall(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_bytes(b"")
    installation.install(tmp_path, agents=["codex"])
    assert tomllib.loads(config.read_text()) == {"agents": {"max_depth": 3}}
    assert json.loads((tmp_path / ".agents/.orchi-install.json").read_text())["config"][".codex/config.toml"]["existed"] is True
    installation.install(tmp_path, uninstall=True)
    assert config.is_file() and config.read_bytes() == b""


def test_unedited_codex_block_is_refreshed(tmp_path, monkeypatch):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text('model = "operator-model"\n')
    monkeypatch.setattr(installation, "CODEX_CONFIG_BODY", "[agents]\nmax_depth = 2")
    installation.install(tmp_path, agents=["codex"])
    assert "max_depth = 2" in config.read_text()
    monkeypatch.undo()
    result = installation.install(tmp_path)
    assert result["status"] == "installed" and ".codex/config.toml" in result["changes"]
    text = config.read_text()
    assert text.startswith('model = "operator-model"\n\n# orchi:begin\n') and "max_depth = 2" not in text
    assert tomllib.loads(text) == {"model": "operator-model", "agents": {"max_depth": 3}}
    assert installation.install(tmp_path)["status"] == "unchanged"
    installation.install(tmp_path, uninstall=True)
    assert config.read_text() == 'model = "operator-model"\n'
