"""Hash-bound target authority, immutable provenance and safe accepted revisions."""
import copy
from pathlib import Path
import pytest

from orchi_core import context, graph, intent
from orchi_core.common import OrchiError, digest, sha
from orchi_core.models import Source
from orchi_core.signing import sign


def spec_for(bundle):
    return {"id": bundle["manifest"]["initiative_id"], "outcome": "Deliver the accepted target",
            "intent": {"revision": bundle["manifest"]["revision"], "digest": digest(bundle["manifest"])},
            "epics": [{"id": "first", "title": "First", "outcome": "Implement the target", "contributes_to": ["req-one"],
                       "realizes": ["intent/architecture/README.md"]}]}


@pytest.fixture
def bundle():
    return intent.build("new-system", {
        "source.md": "Original request, preserved exactly.\n",
        "requirements.md": '---\nkind: requirements\nrequirements: [req-one]\n---\n# Requirements\n<a id="req-one"></a>\n## Outcome\nReturn one.\n',
        "architecture/README.md": "---\nkind: architecture\nrelations:\n  addresses: [req-one]\n---\n# System\nOne local module, no remote dependency.\n",
    })


def test_manifest_and_registry_match_exact_documents(bundle):
    assert intent.validate(bundle, spec_for(bundle)) == bundle
    changed = copy.deepcopy(bundle)
    changed["documents"]["requirements.md"] += "Changed acceptance.\n"
    with pytest.raises(OrchiError, check=lambda e: e.code == "INTENT_CONTENT_CHANGED"):
        intent.validate(changed, spec_for(bundle))


def test_manifest_cannot_omit_an_accepted_requirement(bundle):
    bad = copy.deepcopy(bundle)
    bad["manifest"]["requirements"]["req-one"] = "intent/requirements.md#different"
    with pytest.raises(OrchiError, check=lambda e: e.code == "INTENT_REGISTRY_MISMATCH"):
        intent.validate(bad, spec_for(bad))


def test_roadmap_must_cover_and_resolve_requirements(bundle):
    spec = spec_for(bundle)
    spec["epics"][0]["contributes_to"] = ["req-missing"]
    with pytest.raises(OrchiError, check=lambda e: e.code == "UNKNOWN_REQUIREMENT"):
        intent.validate(bundle, spec)


def test_requirement_ids_unique_across_documents(bundle):
    docs = {**bundle["documents"], "requirements/other.md": bundle["documents"]["requirements.md"]}
    with pytest.raises(OrchiError, check=lambda e: e.code == "DUPLICATE_REQUIREMENT"):
        intent.build("new-system", docs)


def test_original_request_is_immutable(bundle):
    changed = intent.build("new-system", {**bundle["documents"], "source.md": "Rewrite history"}, 2)
    with pytest.raises(OrchiError, check=lambda e: e.code == "IMMUTABLE_REQUEST_SOURCE"):
        intent.validate_revision(bundle, changed)


def test_removed_requirement_needs_accepted_resolution(bundle):
    docs = copy.deepcopy(bundle["documents"])
    docs["requirements.md"] = docs["requirements.md"].replace("req-one", "req-two")
    docs["architecture/README.md"] = docs["architecture/README.md"].replace("req-one", "req-two")
    changed = intent.build("new-system", docs, 2)
    with pytest.raises(OrchiError, check=lambda e: e.code == "UNRESOLVED_REMOVED_REQUIREMENT"):
        intent.validate_revision(bundle, changed)
    changed = intent.build("new-system", docs, 2, {"req-one": "Replaced by the accepted second outcome"})
    revision = intent.validate_revision(bundle, changed)
    assert revision["resolved_requirements"] == changed["manifest"]["resolved_requirements"]


@pytest.mark.parametrize("source", [
    {"kind": "knowledge", "path": "docs/a.md", "reason": "Needs a view"},
    {"kind": "knowledge", "view": "current", "path": "intent/requirements.md", "reason": "Wrong authority"},
    {"kind": "knowledge", "view": "target", "path": "initiatives/active/other/intent/requirements.md", "reason": "Wrong initiative"},
    {"kind": "code", "view": "current", "path": "app.py", "reason": "Role cannot be implicit"},
])
def test_sources_are_view_explicit_and_scope_safe(source):
    with pytest.raises(OrchiError):
        Source.model_validate(source)


def test_proposal_freezes_exact_bytes_before_signature(world):
    req = world.e.begin(world.spec, world.bundle)
    world.bundle["documents"]["requirements.md"] += "Unapproved local edit.\n"
    with pytest.raises(OrchiError, check=lambda e: e.code == "NO_ACCEPTED_INTENT"):
        context.get(world.e.repo, world.e.state(), "req-user", "feature", view="target")
    world.approve(req)
    accepted = context.get(world.e.repo, world.e.state(), "req-user", "feature", view="target")
    assert "Unapproved local edit" not in accepted["content"]
    assert req["inputs"]["intent_manifest_digest"] == world.spec["intent"]["digest"]
    assert accepted["content_hash"] == sha(accepted["content"].encode())


def test_corrupted_pending_bundle_cannot_be_approved(world):
    req = world.e.begin(world.spec, world.bundle)
    artifact = world.e.store.root / "artifacts" / (req["inputs"]["intent_bundle"] + ".json")
    artifact.write_text('{"tampered":true}')
    with pytest.raises(OrchiError, check=lambda e: e.code == "ARTIFACT_CORRUPT"):
        world.approve(req)
    assert world.e.state()["phase"] == "AWAITING_APPROVAL"


def test_exact_target_views_and_scope_isolation(world):
    world.begin()
    repo, state = world.e.repo, world.e.state()
    assert all(r["role"] == "current" for r in context.effective(repo, state, "feature").values())
    target = context.effective(repo, state, "feature", "target")
    assert set(target) == {"intent/requirements.md", "intent/architecture/README.md"}
    assert all(r["role"] == "target" for r in target.values())
    both = context.search(repo, state, "API", "feature", view="all", cache_root=world.root / "cache")
    assert both["primary_matches"] and all("role" in r and "source_commit" in r for r in both["primary_matches"])
    for view in ("current", "target", "all"):
        with pytest.raises(OrchiError, check=lambda e: e.code == "INITIATIVE_SCOPE"):
            context.effective(repo, state, "other", view)
    canonical = graph.project(repo, state, context.retrieval_snapshot(repo, state))
    assert all(n["role"] not in {"target", "workflow", "evidence"} for n in canonical["nodes"])
    with pytest.raises(OrchiError, check=lambda e: e.code == "KNOWLEDGE_CHANGED"):
        context.get(repo, state, "req-user", "feature", content_hash="0" * 64, view="target")


def test_revision_preserves_completed_history_and_invalidates_target_projection(world):
    world.finish_first()
    state = world.e.state()
    old = context.search(world.e.repo, state, "API", "feature", view="target", cache_root=world.root / "cache")
    old_hit = context.get(world.e.repo, state, "req-user", "feature", view="target")
    bundle = intent.accepted(world.e.repo, state)
    documents = {**bundle["documents"], "requirements.md": bundle["documents"]["requirements.md"] + "Document the public interface explicitly.\n"}
    new = intent.build("feature", documents, 2)
    spec = {**state["spec"], "intent": {"revision": 2, "digest": digest(new["manifest"])}}
    gate = world.e.revise_intent(spec, new, "Clarified the interface acceptance condition", ["evidence:" + state["completed"][0]["evidence"]])
    assert gate["inputs"]["revision"]["impacted_requirements"] == ["req-user"]
    world.approve(gate)
    updated = world.e.state()
    assert updated["completed"] == state["completed"] and updated["knowledge_head"] == state["knowledge_head"]
    fresh = context.search(world.e.repo, updated, "API", "feature", view="target", cache_root=world.root / "cache")
    assert fresh["index"]["fingerprint"] != old["index"]["fingerprint"]
    with pytest.raises(OrchiError, check=lambda e: e.code == "KNOWLEDGE_CHANGED"):
        context.get(world.e.repo, updated, "req-user", "feature", content_hash=old_hit["content_hash"], view="target")
    coverage = graph.coverage(world.e.repo, updated, "feature")
    assert coverage["requirements"][0]["stale_target_epics"] == ["values"]
    old_path = "initiatives/active/feature/intent-history/1/requirements.md"
    assert world.e.repo.read(updated["head"], old_path).decode() == bundle["documents"]["requirements.md"]


def test_active_target_change_requires_explicit_stop_and_replan(world):
    world.begin()
    world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"})
    state = world.e.state()
    old = intent.accepted(world.e.repo, state)
    new = intent.build("feature", old["documents"], 2)
    spec = {**state["spec"], "intent": {"revision": 2, "digest": digest(new["manifest"])}}
    with pytest.raises(OrchiError, check=lambda e: e.code == "EPIC_ACTIVE"):
        world.e.revise_intent(spec, new, "Revise the target", ["Operator decision"])
    world.approve(world.e.stop_epic(True, "Stop before revising the accepted target"))
    stopped = world.e.state()
    assert stopped["active"] is None and stopped["epoch"] > state["epoch"]
    assert world.e.repo.read(stopped["head"], "src/left.py") == b"VALUE = 0\n"
    assert stopped["attempts"] == state["attempts"]
    world.approve(world.e.revise_intent(spec, new, "Accepted target clarification", ["Operator decision"]))
    plan = world.plan1()
    assert plan["design"]["path"] == "design/2.md"
    world.approve(world.propose_plan(plan))
    assert world.e.state()["active"]["plan"]["intent_digest"] == digest(new["manifest"])


def test_design_hash_and_intent_identity_are_approval_inputs(world):
    world.begin()
    plan = world.plan1()
    with pytest.raises(OrchiError, check=lambda e: e.code == "DESIGN_CONTENT_CHANGED"):
        world.e.plan(plan, world.design_text(plan) + "Unbound change")
    stale = {**plan, "intent_digest": "0" * 64}
    with pytest.raises(OrchiError, check=lambda e: e.code == "STALE_PLAN"):
        world.e.plan(stale, world.design_text(plan))
    world.approve(world.e.plan(plan, world.design_text(plan)))
    ticket = world.e.claim("left")
    packet = world.e.store.get_artifact(ticket["packet_id"])
    roles = {r["role"] for r in packet["sources"]}
    assert {"current", "target", "epic-design", "implementation"} <= roles
    design = next(r for r in packet["sources"] if r["role"] == "epic-design")
    assert design["content_hash"] == plan["design"]["content_hash"]
    assert world.e.repo.read(design["source_commit"], design["source_path"]).decode() == design["content"]


def test_pending_requirement_alias_fails_with_scope_error_not_exception(world):
    with pytest.raises(OrchiError, check=lambda e: e.code == "INITIATIVE_SCOPE"):
        context.get(world.e.repo, world.e.state(), "req-user", "feature", view="target")


def test_revised_target_can_link_verified_working_and_known_evidence(world):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    world.perform("left", {"src/left.py": "VALUE = 1\n"})
    world.perform("right", {"src/right.py": "VALUE = 2\n"})
    world.pass_review()
    checkpoint = world.checkpoint1()
    checkpoint["entries"][0]["content"] += "\n## Verified checkpoint\nThe verified value is implemented.\n"
    world.e.checkpoint(checkpoint)
    state = world.e.state()
    old = intent.accepted(world.e.repo, state)
    documents = copy.deepcopy(old["documents"])
    documents["architecture/README.md"] = documents["architecture/README.md"].replace(
        "  addresses: [req-user]", "  addresses: [req-user]\n  depends_on: [docs/architecture.md#verified-checkpoint]")
    documents["decisions/verification.md"] = "---\nkind: decision\nrelations:\n  verified_by: [evidence:" + state["completed"][0]["evidence"] + "]\n---\n# Decision\nThe checked current boundary guides the next epic.\n"
    revised = intent.build("feature", documents, 2)
    spec = {**state["spec"], "intent": {"revision": 2, "digest": digest(revised["manifest"])}}
    world.approve(world.e.revise_intent(spec, revised, "Learned from the verified checkpoint", [state["completed"][0]["evidence"]]))
    assert context.lint(world.e.repo, world.e.state(), "feature", "all")["ok"]
    assert "verified-checkpoint" in context.get(world.e.repo, world.e.state(), "intent/architecture/README.md", "feature", view="target")["content"]


def test_architecture_reorganization_keeps_completed_bindings_historical(world):
    documents = copy.deepcopy(world.bundle["documents"])
    documents["architecture/value-boundary.md"] = "---\nkind: architecture\n---\n# Values boundary\nIndependent immutable values.\n"
    world.bundle = intent.build("feature", documents)
    world.spec["intent"]["digest"] = digest(world.bundle["manifest"])
    world.spec["epics"][0]["realizes"] = ["intent/architecture/value-boundary.md"]
    original_design = world.design_text
    world.design_text = lambda plan: original_design(plan).replace("intent/architecture/README.md", "intent/architecture/value-boundary.md")
    world.finish_first()
    state = world.e.state()
    del documents["architecture/value-boundary.md"]
    documents["architecture/README.md"] += "The value boundary is now documented here.\n"
    revised = intent.build("feature", documents, 2)
    spec = {**state["spec"], "intent": {"revision": 2, "digest": digest(revised["manifest"])}}
    world.approve(world.e.revise_intent(spec, revised, "Consolidate target architecture without rewriting completed work", [state["completed"][0]["evidence"]]))
    current = world.e.state()
    assert current["completed"] == state["completed"]
    assert "intent/architecture/value-boundary.md" not in context.effective(world.e.repo, current, "feature", "target")
    projection = graph.project(world.e.repo, current, context.retrieval_snapshot(world.e.repo, current, "feature", "all"))
    assert any(d["code"] == "HISTORICAL_TARGET_REFERENCE" for d in projection["diagnostics"])
    assert not any(n.get("target") == "intent/architecture/value-boundary.md" for n in projection["nodes"])


@pytest.mark.parametrize("target", ["docs/architecture.md", "initiatives/active/feature/intent/requirements.md"])
def test_task_cannot_write_current_or_target_authority(world, target):
    world.begin(); world.approve(world.propose_plan(world.plan1()))
    ticket = world.e.claim("left"); world.activate(ticket)
    head = world.e.state()["head"]
    (Path(ticket["workspace"]) / target).write_text("Unauthorized authority edit\n")
    with pytest.raises(OrchiError):
        world.e.submit(ticket["id"], {"status": "completed", "summary": "Attempts an unauthorized write"})
    assert world.e.state()["head"] == head
