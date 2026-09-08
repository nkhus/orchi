"""Installed CLI behavior and retrieval against real accepted epic checkpoints."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from orchi_core import context, diagnostics
from orchi_core.cli import main

ROOT = Path(__file__).resolve().parents[1]


def call(capsys, *args):
    code = main(list(args))
    return code, json.loads(capsys.readouterr().out)


def test_standalone_search_get_stat_and_force_index(world, monkeypatch, capsys):
    monkeypatch.delenv("ORCHI_CONTROL", raising=False)
    before = world.e.repo.git("status", "--porcelain")
    code, payload = call(capsys, "search", "zero", "--repo", str(world.repo))
    assert code == 0
    hit = payload["result"]["results"][0]
    assert payload["result"]["index"]["status"] == "built"
    assert Path(payload["result"]["index"]["path"]).is_relative_to(world.repo / ".git")
    code, payload = call(capsys, "get", hit["target"], "--repo", str(world.repo), "--content-hash", hit["content_hash"])
    assert code == 0 and "zero" in payload["result"]["content"]
    code, payload = call(capsys, "stat", "--repo", str(world.repo))
    assert code == 0 and payload["result"]["index"]["status"] == "reused"
    code, payload = call(capsys, "index", "--repo", str(world.repo), "--force")
    assert code == 0 and payload["result"]["index"]["status"] == "rebuilt"
    assert world.e.repo.git("status", "--porcelain") == before


def test_controlled_search_does_not_change_workflow_state_or_events(world, capsys):
    state = world.e.state()
    with world.e.store.connect() as con:
        events = con.execute("SELECT count(*) FROM events").fetchone()[0]
    code, payload = call(capsys, "--control", str(world.e.store.root), "search", "Architecture")
    assert code == 0 and payload["result"]["results"]
    assert Path(payload["result"]["index"]["path"]).is_relative_to(world.e.store.root / "cache/retrieval")
    assert world.e.state() == state
    with world.e.store.connect() as con:
        assert con.execute("SELECT count(*) FROM events").fetchone()[0] == events


def test_optional_text_format_and_limit(world, monkeypatch, capsys):
    monkeypatch.delenv("ORCHI_CONTROL", raising=False)
    assert main(["search", "zero", "--repo", str(world.repo), "--format", "text", "-k", "1"]) == 0
    text = capsys.readouterr().out
    assert "docs/architecture.md:5-6" in text and "The left value starts at zero." in text
    assert "sha256:" in text


@pytest.mark.parametrize("tail", [
    ["--repo", ".", "--initiative", "feature"],
    ["--ref", "main"],
])
def test_ambiguous_scopes_are_rejected_before_work(world, monkeypatch, capsys, tail):
    monkeypatch.setenv("ORCHI_CONTROL", str(world.e.store.root))
    code, payload = call(capsys, "search", "zero", *tail)
    assert code == 2 and payload["code"] == "AMBIGUOUS_SCOPE"


def test_standalone_search_with_explicit_canonical_ref(world, monkeypatch, capsys):
    monkeypatch.delenv("ORCHI_CONTROL", raising=False)
    world.e.repo.git("update-ref", "refs/heads/trunk", world.baseline)
    code, payload = call(capsys, "search", "zero", "--repo", str(world.repo), "--ref", "refs/heads/trunk")
    assert code == 0 and payload["result"]["snapshot"]["canonical_ref"] == "refs/heads/trunk"


def test_invalid_limits_and_queries_have_structured_errors(world, monkeypatch, capsys):
    monkeypatch.delenv("ORCHI_CONTROL", raising=False)
    for query, more, expected in [("callback", ["--limit", "0"], "INVALID_LIMIT"), ("", [], "INVALID_QUERY")]:
        code, payload = call(capsys, "search", query, "--repo", str(world.repo), *more)
        assert code == 2 and payload["code"] == expected


def test_doctor_reports_missing_search_capabilities(monkeypatch):
    monkeypatch.setattr(diagnostics, "capabilities", lambda: {"fts5": False, "trigram": False})
    result = diagnostics.doctor()
    assert result["status"] == "blocked"
    assert any(c["name"] == "sqlite:fts5" and not c["passed"] for c in result["checks"])
    monkeypatch.setattr(diagnostics, "capabilities", lambda: {"fts5": True, "trigram": False})
    result = diagnostics.doctor()
    assert result["status"] == "ready" and any("trigram" in w for w in result["warnings"])


def test_installed_search_works_without_source_checkout(world, tmp_path):
    spec = importlib.util.spec_from_file_location("local_installer", ROOT / "tools/install.py")
    installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
    installer.install(world.repo)
    entrypoint = world.repo / ".agents/skills/orchi/scripts/orchi.py"
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "ORCHI_CONTROL"}}
    result = subprocess.run([sys.executable, str(entrypoint), "search", "zero", "--repo", "."],
                            cwd=world.repo, env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["results"][0]["target"] == "docs/architecture.md"
    assert (entrypoint.parent.parent / "references/retrieval.md").is_file()
    assert not list((world.repo / ".agents").rglob("__pycache__"))


def test_real_checkpoints_refresh_overlay_and_leave_core_unchanged(world):
    cache = world.e.store.root / "cache/retrieval"
    world.begin()
    initial = context.search(world.e.repo, world.e.state(), "zero", "feature", cache_root=cache)
    world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"})
    world.perform("right", {"src/right.py": "VALUE = 2\n"})
    # Accepted tasks are not yet verified Working Knowledge.
    before_checkpoint = context.search(world.e.repo, world.e.state(), "zero", "feature", cache_root=cache)
    assert before_checkpoint["results"] == initial["results"] and before_checkpoint["index"]["status"] == "reused"
    world.pass_review()
    world.e.checkpoint(world.checkpoint1())
    after_first = context.search(world.e.repo, world.e.state(), "one", "feature", cache_root=cache)
    assert after_first["results"][0]["layer"] == "working"
    assert after_first["index"]["fingerprint"] != initial["index"]["fingerprint"]
    assert not context.search(world.e.repo, world.e.state(), "one", cache_root=cache)["results"]
    world.finish_second()
    after_second = context.search(world.e.repo, world.e.state(), "answer", "feature", cache_root=cache)
    assert after_second["results"][0]["target"] == "docs/api.md"
    assert after_second["index"]["fingerprint"] != after_first["index"]["fingerprint"]
    assert world.e.repo.resolve("refs/heads/main") == world.baseline
    assert "zero" in context.get(world.e.repo, world.e.state(), "docs/architecture.md")["content"]
    # Packet materialization still reads authority even with a destroyed cache.
    for p in cache.glob("*.sqlite"):
        p.write_bytes(b"destroyed projection")
    rec = context.get(world.e.repo, world.e.state(), "docs/api.md", "feature")
    assert rec["content"] == "---\nkind: component\n---\n# API\nThe answer is three.\n"
