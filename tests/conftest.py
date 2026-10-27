"""Shared fixtures: local Git repositories that stand in for the design skills' GitHub repositories."""
import os
from pathlib import Path
import subprocess

import pytest

from orchi_core import installation

# Each fake repository holds its skill at the published path, plus a file outside it that must not be installed.
# Every version is one commit; tests pin the first and may move the pin to a later one.
DESIGN_TREES = {
    "hallmark": [
        {"skills/hallmark/SKILL.md": "---\nname: hallmark\ndescription: Fake Hallmark\nversion: 2.0.0\n---\nFake\n",
         "skills/hallmark/references/craft.md": "# Craft\n", "README.md": "Repository readme\n"},
        {"skills/hallmark/SKILL.md": "---\nname: hallmark\ndescription: Fake Hallmark\nversion: 2.1.0\n---\nFake\n",
         "skills/hallmark/references/craft.md": "# Craft, revised\n", "README.md": "Repository readme\n"},
    ],
    "prototype": [
        {"skills/prototype/SKILL.md": "---\nname: prototype\ndescription: Fake prototype\n"
                                      "disable-model-invocation: true\n---\nFake\n",
         "skills/prototype/PICKER.md": "# Picker\n", "skills/other/README.md": "Another folder\n"},
    ],
}
GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV}, check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture(scope="session")
def design_repos(tmp_path_factory):
    """Bare repositories at <base>/<repo> for each design skill; returns the base URL and each skill's commits."""
    base = tmp_path_factory.mktemp("design-git")
    commits = {}
    for name, versions in DESIGN_TREES.items():
        work = tmp_path_factory.mktemp("design-work-" + name)
        git("init", "-q", "-b", "main", cwd=work)
        commits[name] = []
        for files in versions:
            for relative, text in files.items():
                (work / relative).parent.mkdir(parents=True, exist_ok=True)
                (work / relative).write_text(text)
            git("add", "-A", cwd=work)
            git("commit", "-q", "-m", "version", cwd=work)
            commits[name].append(git("rev-parse", "HEAD", cwd=work))
        bare = base / installation.DESIGN_SKILLS[name]["repo"]
        bare.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "-q", "--bare", str(work), str(bare), cwd=base)
    return {"base": base.as_uri() + "/", "commits": commits, "trees": DESIGN_TREES}


@pytest.fixture(autouse=True)
def design_skills(design_repos, monkeypatch):
    """Point every installation at the local repositories, with each skill pinned to its first commit."""
    monkeypatch.setenv(installation.DESIGN_GIT_BASE_ENV, design_repos["base"])
    monkeypatch.setattr(installation, "DESIGN_SKILLS", {
        name: {**spec, "commit": design_repos["commits"][name][0]} for name, spec in installation.DESIGN_SKILLS.items()})
    return design_repos


def pin(monkeypatch, name, commit):
    """Move one design skill's pin, as a later Orchi release would."""
    monkeypatch.setattr(installation, "DESIGN_SKILLS", {
        **installation.DESIGN_SKILLS, name: {**installation.DESIGN_SKILLS[name], "commit": commit}})


def expected_tree(name, version=0):
    """The files a design skill version installs, relative to its skill directory."""
    prefix = installation.DESIGN_SKILLS[name]["path"] + "/"
    return {relative[len(prefix):]: text for relative, text in DESIGN_TREES[name][version].items()
            if relative.startswith(prefix)}


def tree(folder: Path) -> dict:
    return {path.relative_to(folder).as_posix(): path.read_text() for path in sorted(folder.rglob("*")) if path.is_file()}
