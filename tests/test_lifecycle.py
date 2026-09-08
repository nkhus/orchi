from pathlib import Path
import copy
import json
import pytest
from orchi_core.common import OrchiError
from orchi_core import context
from conftest import git


def test_two_epics_then_one_canonical_publication(world):
    w = world
    original = w.e.repo.read(w.baseline, "docs/architecture.md")
    w.finish_first()
    s = w.e.state()
    assert s["phase"] == "PLANNING"
    assert w.e.next()["epic"]["id"] == "api"
    assert w.e.repo.resolve("main") == w.baseline
    assert w.e.repo.read(s["head"], "docs/architecture.md") == original
    assert "zero" in context.get(w.e.repo, s, "docs/architecture.md")["content"]
    working = context.get(w.e.repo, s, "docs/architecture.md", "feature")
    assert working["layer"] == "working" and "one" in working["content"]
    w.finish_second()
    assert w.e.state()["phase"] == "FINALIZING"
    assert w.e.repo.resolve("main") == w.baseline
    assert w.e.repo.read(w.e.state()["head"], "docs/architecture.md") == original
    draft = w.final()
    draft["report"] = "Reconciled the cumulative actual implementation and end-to-end acceptance"
    result = w.e.finalize(draft)
    assert result["status"] == "final_review_required"
    assert "one" in w.e.repo.read(result["candidate"], "docs/architecture.md").decode()
    assert w.e.repo.read(w.e.state()["head"], "docs/architecture.md") == original
    final_gate = w.pass_review("initiative")
    w.approve(final_gate)
    instruction = w.e.publication()
    assert instruction["expected_parent"] == w.baseline
    git(w.repo, "merge", "--ff-only", instruction["candidate"])
    w.e.record_publication(instruction["candidate"])
    assert w.e.next()["status"] == "DONE"
    assert "one" in context.get(w.e.repo, w.e.state(), "docs/architecture.md")["content"]
    assert not any(p.startswith("initiatives/active/") for p in w.e.repo.files(instruction["candidate"]))
    assert len(git(w.repo, "rev-list", w.baseline + "..main").splitlines()) == 1


def test_future_epic_cannot_be_materialized(world):
    world.begin()
    plan = world.plan1(); plan["epic_id"] = "api"
    with pytest.raises(OrchiError, match="next selected epic"):
        world.propose_plan(plan)


def test_second_epic_must_use_actual_checkpoint_not_initial_baseline(world):
    world.finish_first()
    plan = world.plan1(); plan["epic_id"] = "api"; plan["based_on"] = world.baseline
    with pytest.raises(OrchiError) as e:
        world.propose_plan(plan)
    assert e.value.code == "STALE_PLAN"


def test_checkpoint_is_mandatory_before_next_epic(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"})
    world.perform("right", {"src/right.py": "VALUE = 2\n"})
    world.pass_review()
    assert world.e.next()["action"] == "checkpoint_epic"
    with pytest.raises(OrchiError):
        world.propose_plan(world.plan1())


def test_core_writes_rejected_in_worker_candidate(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    t = world.e.claim("left"); world.activate(t)
    (Path(t["workspace"]) / "src/left.py").write_text("VALUE=1\n")
    (Path(t["workspace"]) / "docs/architecture.md").write_text("Future falsely current")
    with pytest.raises(OrchiError) as e:
        world.e.submit(t["id"], {"status": "completed", "summary": "done"})
    assert e.value.code == "SCOPE_VIOLATION"


def test_checkpoint_requires_actual_impact_dispositions(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"}); world.perform("right", {"src/right.py": "VALUE = 2\n"})
    world.pass_review()
    cp = world.checkpoint1(); cp["dispositions"].pop()
    with pytest.raises(OrchiError) as e:
        world.e.checkpoint(cp)
    assert e.value.code == "INCOMPLETE_IMPACT"


def test_known_core_ownership_cannot_be_hidden_as_nonsemantic(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"}); world.perform("right", {"src/right.py": "VALUE = 2\n"})
    world.pass_review()
    cp = world.checkpoint1(); cp["dispositions"][0]["targets"] = []
    with pytest.raises(OrchiError) as e:
        world.e.checkpoint(cp)
    assert e.value.code == "MISSING_KNOWLEDGE_IMPACT"


def test_no_finalization_before_all_epics(world):
    world.finish_first()
    with pytest.raises(OrchiError):
        world.final()


def test_canonical_movement_blocks_publication(world):
    world.finish_first(); world.finish_second()
    git(world.repo, "commit", "--allow-empty", "-m", "unrelated canonical update")
    draft = world.final(); draft["report"] = "Reviewed cumulative result"
    with pytest.raises(OrchiError) as e:
        world.e.finalize(draft)
    assert e.value.code == "CANONICAL_MOVED"
