"""Greenfield is the same approval/checkpoint/publication workflow, with empty Core."""
import json
from pathlib import Path
import sys
import pytest

from conftest import git
from orchi_core import context, graph, intent
from orchi_core.common import OrchiError, digest, sha
from orchi_core.engine import Engine
from orchi_core.signing import keygen, sign


def test_empty_core_through_target_design_checkpoint_and_one_parent_publication(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Synthetic Test")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "commit", "--allow-empty", "-m", "Empty baseline")
    baseline = git(repo, "rev-parse", "HEAD")
    key = tmp_path / "operator.pem"
    public = keygen(key)
    policy = {"public_key": public, "checks": {"verify": {"argv": [sys.executable, "-c", "import runpy; assert runpy.run_path('app.py')['ANSWER'] == 42"]}},
              "baseline_checks": [], "final_checks": ["verify"], "max_process_seconds": 30, "lease_seconds": 120}
    engine = Engine.setup(tmp_path / "control", repo, policy)
    bundle = intent.build("minimal", {
        "source.md": "Deliver a local module exposing the answer forty-two.\n",
        "requirements.md": '---\nkind: requirements\nrequirements: [req-answer]\n---\n# Requirements\n<a id="req-answer"></a>\n## Answer\nExpose the integer forty-two without network access.\n',
        "architecture/README.md": "---\nkind: architecture\nartifacts: [app.py]\nrelations:\n  addresses: [req-answer]\n---\n# Target architecture\nA local Python module is the sole implementation boundary. No service or persistence is needed.\n",
    })
    spec = {"id": "minimal", "outcome": "Expose forty-two locally", "intent": {"revision": 1, "digest": digest(bundle["manifest"])},
            "epics": [{"id": "module", "title": "Local module", "outcome": "Expose the accepted answer", "contributes_to": ["req-answer"],
                       "realizes": ["intent/architecture/README.md"]}]}
    def approve(request):
        return engine.approve(sign(request, key, "approve", "synthetic-operator"))
    def review(scope="epic"):
        request = engine.review_request(scope)
        return engine.record_review({"request_id": request["id"], "reviewer": "synthetic-independent-reviewer", "complete": True,
            "covered_paths": request["required_paths"], "findings": [], "summary": "Checked the exact implementation and claimed semantics"})
    approve(engine.begin(spec, bundle))
    state = engine.state()
    assert context.search(engine.repo, state, "forty", "minimal")["primary_matches"] == []
    target = context.search(engine.repo, state, "forty", "minimal", view="target")
    assert target["primary_matches"] and all(h["role"] == "target" for h in target["primary_matches"])
    assert context.effective(engine.repo, state) == {}
    before = graph.coverage(engine.repo, state, "minimal")
    assert before["requirements"][0]["state"] == "planned"
    design = "---\nkind: reference\nrelations:\n  addresses: [req-answer]\n  realizes: [intent/architecture/README.md]\n---\n# Selected epic design\nCreate app.py exporting ANSWER as the integer 42. Imports have no effects. The registered verify check reads the value.\n"
    task = {"id": "implement", "goal": "Expose the accepted answer", "acceptance": {"ac-answer": "Expose 42"},
        "current_state": "No implementation or Core documents exist", "approach": "Create a single Python module",
        "decisions": ["Use a module-level integer constant"], "invariants": ["No network or import effects"],
        "allowed_choices": [], "failure_modes": ["Reject a changed accepted answer"],
        "edits": [{"path": "app.py", "action": "create", "how": "Define ANSWER = 42"}],
        "context": [{"kind": "knowledge", "view": "target", "path": "req-answer", "reason": "Exact accepted requirement"}],
        "verification": [{"criterion": "ac-answer", "scenario": "Load the module", "expected": "ANSWER is the integer 42", "checks": ["verify"]}],
        "escalation": ["Stop if a service or persistence becomes necessary"], "open_questions": []}
    plan = {"initiative_id": "minimal", "epic_id": "module", "based_on": state["head"], "goal": "Expose the answer", "shared_design": "One pure Python module",
            "design": {"path": "design/1.md", "content_hash": sha(design.encode())}, "intent_digest": spec["intent"]["digest"],
            "acceptance": {"ac-module": "Accepted answer available"}, "acceptance_checks": {"ac-module": ["verify"]}, "tasks": [task]}
    approve(engine.plan(plan, design))
    ticket = engine.claim("implement")
    packet = engine.store.get_artifact(ticket["packet_id"])
    assert {r["role"] for r in packet["sources"]} == {"target", "epic-design"}
    assert all(r["source_commit"] and r["content_hash"] for r in packet["sources"])
    engine.activate(ticket["id"], {"packet_fingerprint": packet["fingerprint"], "understood_goal": task["goal"],
                                  "fixed_decisions": task["decisions"], "acceptance_ids": ["ac-answer"], "questions": []})
    (Path(ticket["workspace"]) / "app.py").write_text("ANSWER = 42\n")
    assert engine.submit(ticket["id"], {"status": "completed", "summary": "Implemented exact answer"})["status"] == "integrated"
    assert context.effective(engine.repo, engine.state(), "minimal") == {}
    review()
    engine.checkpoint({"epic_id": "module", "based_on": engine.state()["head"], "report": "The verified module exposes forty-two",
        "entries": [{"target": "docs/app.md", "action": "replace", "content": "---\nkind: component\n---\n# Application module\napp.py exposes ANSWER = 42 without effects.\n",
                     "artifacts": ["app.py"], "checks": ["verify"], "reason": "New verified implementation"}],
        "dispositions": [{"path": "app.py", "targets": ["docs/app.md"], "reason": "Adds the documented module"}]})
    current = context.get(engine.repo, engine.state(), "docs/app.md", "minimal")
    assert current["role"] == "current" and current["layer"] == "working"
    assert not any(p.startswith("docs/") for p in engine.repo.files(engine.state()["head"]))
    projected = graph.project(engine.repo, engine.state(), context.retrieval_snapshot(engine.repo, engine.state(), "minimal", "all"))
    requirement_edges = graph.related(projected, "req-answer", "addressed_by")
    assert requirement_edges["related"][0]["id"] == "epic:module"
    assert graph.coverage(engine.repo, engine.state(), "minimal")["requirements"][0]["state"] == "implemented"
    proposal = engine.final_draft()
    proposal["report"] = "The implementation realizes the target. Final Core describes the verified module, not a future service."
    proposal["requirements"][0].update(disposition="satisfied", reason="The exact candidate verify check proves the accepted value", checks=["verify"], core_targets=["docs/app.md"])
    proposal["architecture"][0].update(disposition="realized", reason="The module is the actual implementation boundary", artifacts=["app.py"], core_targets=["docs/app.md"], checks=["verify"])
    finalized = engine.finalize(proposal)
    assert finalized["status"] == "final_review_required"
    coverage = graph.coverage(engine.repo, engine.state(), "minimal")
    assert coverage["requirements"][0]["state"] == "verified" and coverage["requirements"][0]["final_evidence"] == finalized["evidence"]
    final_graph = graph.project(engine.repo, engine.state(), context.retrieval_snapshot(engine.repo, engine.state(), "minimal", "all"))
    assert any(e["source"] == "target:intent/architecture/README.md" and e["target"] == "implementation:app.py" and e["origin"] == "controller" for e in final_graph["edges"])
    graph.write_map(final_graph, tmp_path / "derived-map.html")
    with pytest.raises(OrchiError, check=lambda e: e.code == "APPROVAL_REQUIRED"):
        engine.publication()
    approve(review("initiative"))
    publication = engine.publication()
    equivalent = engine.repo.commit(engine.repo.tree(publication["candidate"]), baseline, "Not the exact approved candidate")
    git(repo, "update-ref", "refs/heads/main", equivalent, baseline)
    with pytest.raises(OrchiError, check=lambda e: e.code == "WRONG_PUBLICATION_COMMIT"):
        engine.record_publication(equivalent)
    git(repo, "update-ref", "refs/heads/main", baseline, equivalent)
    git(repo, "merge", "--ff-only", publication["candidate"])
    engine.record_publication(publication["candidate"])
    assert git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:] == [baseline]
    files = engine.repo.files(publication["candidate"])
    assert not any(p.startswith("initiatives/active/") for p in files)
    assert engine.repo.read(publication["candidate"], "initiatives/archive/minimal/intent-history/1/source.md").decode() == bundle["documents"]["source.md"]
    canonical = context.search(engine.repo, engine.state(), "answer")
    assert canonical["primary_matches"] and all(r["role"] == "current" for r in canonical["primary_matches"])
    engine.export(tmp_path / "audit")
    assert json.loads((tmp_path / "audit/state.json").read_text())["final"]["verified"]["commit"] == publication["candidate"]
