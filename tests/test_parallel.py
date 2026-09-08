from pathlib import Path
import json
import subprocess
import sys
import time
import pytest
from orchi_core.common import OrchiError
from orchi_core.engine import Engine
from orchi_core.runner import run_ready


def test_real_foreground_process_workers_overlap(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    result = run_ready(world.e, {"kind": "command", "argv": [sys.executable, str(Path(__file__).with_name("fake_agent.py")), "--parallel-barrier", str(world.repo.parent / "barrier")]})
    assert {o["status"] for o in result["outcomes"]} == {"integrated"}
    assert result["next"]["action"] == "request_epic_review"
    timings = [json.loads((Path(t["workspace"]).parent / "output/timing.json").read_text()) for t in world.e.state()["tickets"].values()]
    assert len(timings) == 2
    assert max(t["start"] for t in timings) < min(t["end"] for t in timings)


def test_two_os_processes_cannot_claim_same_task(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    tool = Path(__file__).parents[1] / "tools/orchi.py"
    argv = [sys.executable, str(tool), "--control", str(world.e.store.root), "claim", "--task", "left"]
    procs = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    results = [(p.communicate(timeout=20), p.returncode) for p in procs]
    assert sorted(code for _, code in results) == [0, 2]
    assert len(world.e.state()["tickets"]) == 1


def test_independent_candidate_not_invalidated_by_other_integration(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    a = world.e.claim("left"); b = world.e.claim("right")
    world.activate(a); world.activate(b)
    (Path(a["workspace"]) / "src/left.py").write_text("VALUE=1\n")
    (Path(b["workspace"]) / "src/right.py").write_text("VALUE=2\n")
    assert world.e.submit(a["id"], {"status": "completed", "summary": "left"})["status"] == "integrated"
    assert world.e.submit(b["id"], {"status": "completed", "summary": "right"})["status"] == "integrated"


def test_isolated_pass_is_not_combined_pass(world):
    with world.e.store.transaction("test-policy") as s:
        s["policy"]["checks"]["joint"] = {"argv": [sys.executable, "-c", "import runpy; assert not(runpy.run_path('src/left.py')['VALUE']==1 and runpy.run_path('src/right.py')['VALUE']==2)"], "timeout_seconds": 30}
        s["policy"]["baseline_checks"].append("joint")
    world.e = Engine(world.e.store.root)
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    a = world.e.claim("left"); b = world.e.claim("right")
    world.activate(a); world.activate(b)
    (Path(a["workspace"]) / "src/left.py").write_text("VALUE=1\n")
    (Path(b["workspace"]) / "src/right.py").write_text("VALUE=2\n")
    assert world.e.submit(a["id"], {"status": "completed", "summary": "left"})["status"] == "integrated"
    prior = world.e.state()["head"]
    result = world.e.submit(b["id"], {"status": "completed", "summary": "right"})
    assert result["status"] == "blocked"
    assert world.e.store.get_artifact(result["isolated"])["passed"]
    assert not world.e.store.get_artifact(result["combined"])["passed"]
    assert world.e.state()["head"] == prior


def test_new_read_dependency_detects_stale_result(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    a = world.e.claim("left"); b = world.e.claim("right")
    world.activate(a); world.activate(b)
    (Path(a["workspace"]) / "src/left.py").write_text("VALUE=1\n")
    (Path(b["workspace"]) / "src/right.py").write_text("VALUE=2\n")
    world.e.submit(a["id"], {"status": "completed", "summary": "left"})
    with pytest.raises(OrchiError) as err:
        world.e.submit(b["id"], {"status": "completed", "summary": "right", "extra_reads": ["src/left.py"]})
    assert err.value.code == "STALE_READS"


def test_resources_serialize_without_inventing_dependencies(world):
    world.begin(); p = world.plan1()
    for t in p["tasks"]:
        t["exclusive_resources"] = ["shared-test-database"]
    world.approve(world.propose_plan(p))
    world.e.claim("left")
    with pytest.raises(OrchiError) as err:
        world.e.claim("right")
    assert err.value.code == "NO_READY_TASK"
    assert world.e.next()["status"] == "WAIT"


def test_expired_worker_not_reissued_automatically(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    ticket = world.e.claim("left")
    with world.e.store.transaction("test-clock") as s:
        s["tickets"][ticket["id"]]["expires_at"] = time.time() - 1
    assert world.e.next()["action"] == "stop_and_release_expired_worker"
    with pytest.raises(OrchiError):
        world.e.claim("left")
    with pytest.raises(OrchiError):
        world.e.release(ticket["id"], False, "not actually stopped")
    world.e.release(ticket["id"], True, "operator stopped process")
    world.e.retry("left", "retry after confirmed stop")
    new = world.e.claim("left")
    assert new["id"] != ticket["id"]
    assert world.e.state()["attempts"]["values/left"] == 2
