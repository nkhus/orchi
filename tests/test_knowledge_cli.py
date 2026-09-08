"""Agent-facing commands expose explicit views and derived navigation."""
import json
from pathlib import Path
import pytest
from orchi_core.cli import main


def call(capsys, args):
    code = main(args)
    result = json.loads(capsys.readouterr().out)
    return code, result


def test_build_target_search_related_map_lint_and_coverage(world, tmp_path, capsys):
    directory = tmp_path / "intent-proposal"
    for relative, text in world.bundle["documents"].items():
        p = directory / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    code, built = call(capsys, ["intent-build", "--directory", str(directory), "--initiative", "feature"])
    assert code == 0 and built["result"]["intent"] == world.spec["intent"]
    spec_path = tmp_path / "initiative.json"
    spec_path.write_text(json.dumps(world.spec))
    control = ["--control", str(world.e.store.root)]
    code, begun = call(capsys, control + ["begin", "--file", str(spec_path), "--intent", str(directory)])
    assert code == 0
    world.approve(begun["result"])
    code, found = call(capsys, control + ["search", "API", "--initiative", "feature", "--view", "target", "--kind", "requirements"])
    assert code == 0 and found["result"]["primary_matches"]
    hit = found["result"]["primary_matches"][0]
    assert hit["role"] == "target" and hit["kind"] == "requirements"
    code, read = call(capsys, control + ["get", "req-user", "--initiative", "feature", "--view", "target", "--content-hash", hit["content_hash"]])
    assert code == 0 and read["result"]["anchor"] == "req-user"
    code, relations = call(capsys, control + ["related", "req-user", "--initiative", "feature", "--view", "target", "--relation", "addressed_by"])
    assert code == 0 and {n["id"] for n in relations["result"]["related"]} == {"epic:values", "epic:api"}
    code, mapped = call(capsys, control + ["map", "--initiative", "feature", "--view", "all"])
    assert code == 0 and Path(mapped["result"]["path"]).is_file()
    code, linted = call(capsys, control + ["lint", "--initiative", "feature", "--view", "target"])
    assert code == 0 and linted["result"]["ok"]
    code, coverage = call(capsys, control + ["coverage", "--initiative", "feature"])
    assert code == 0 and coverage["result"]["requirements"][0]["state"] == "planned"
    code, forbidden = call(capsys, control + ["map", "--initiative", "feature", "--out", str(world.repo / "docs/map.html")])
    assert code == 2 and forbidden["code"] == "DERIVED_OUTPUT_BOUNDARY"


def test_standalone_target_and_unscoped_coverage_fail_safely(world, capsys):
    code, failed = call(capsys, ["search", "API", "--repo", str(world.repo), "--view", "target"])
    assert code == 2 and failed["code"] == "TARGET_SCOPE_REQUIRED"
    code, failed = call(capsys, ["--control", str(world.e.store.root), "coverage"])
    assert code == 2 and failed["code"] == "INITIATIVE_SCOPE"
