"""Final traceability cannot substitute prose or similarity for candidate checks."""
import copy
import pytest
from orchi_core import reconciliation, context, ontology
from orchi_core.common import OrchiError
from orchi_core.models import Policy


@pytest.fixture
def target_case(monkeypatch):
    manifest = {"requirements": {"req-one": "intent/requirements.md#req-one"}, "resolved_requirements": {},
                "architecture": ["intent/architecture/README.md"]}
    monkeypatch.setattr(reconciliation.intent, "accepted", lambda repo, state: {"manifest": manifest})
    class Repo:
        def files(self, commit):
            return {"src/app.py": ("100644", "a" * 40), "docs/app.md": ("100644", "b" * 40)}
    policy = Policy(public_key="synthetic-test-key-not-used-for-signing", checks={"suite": {"argv": ["python", "-c", "pass"]}}, final_checks=["suite"])
    state = {"spec": {"intent": {"digest": "a" * 64}}, "head": "b" * 40}
    proposal = {"intent_digest": "a" * 64,
                "requirements": [{"requirement_id": "req-one", "disposition": "satisfied", "reason": "Observed accepted behavior", "checks": ["suite"], "core_targets": ["docs/app.md"]}],
                "architecture": [{"target": "intent/architecture/README.md", "disposition": "realized", "reason": "Existing module realizes the boundary", "artifacts": ["src/app.py"], "checks": ["suite"], "core_targets": ["docs/app.md"]}]}
    return Repo(), state, proposal, policy


@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.update(requirements=[]), "INCOMPLETE_ACCEPTANCE"),
    (lambda p: p.update(architecture=[]), "INCOMPLETE_ARCHITECTURE"),
    (lambda p: p.update(intent_digest="c" * 64), "STALE_FINALIZATION"),
    (lambda p: p["requirements"][0].update(checks=[]), "UNVERIFIED_REQUIREMENT"),
    (lambda p: p["requirements"][0].update(disposition="changed"), "INTENT_REVISION_REQUIRED"),
    (lambda p: p["requirements"][0].update(disposition="unresolved"), "UNRESOLVED_REQUIREMENT"),
    (lambda p: p["architecture"][0].update(disposition="unresolved"), "UNREALIZED_ARCHITECTURE"),
    (lambda p: p["architecture"][0].update(artifacts=[]), "UNVERIFIED_ARCHITECTURE"),
    (lambda p: p["architecture"][0].update(core_targets=[]), "UNVERIFIED_ARCHITECTURE"),
    (lambda p: p["architecture"][0].update(artifacts=["src/nonexistent.py"]), "MISSING_ARTIFACT"),
    (lambda p: p["requirements"][0].update(checks=["unregistered"]), "UNKNOWN_CHECK"),
    (lambda p: p["architecture"][0].update(reason="REPLACE: invent realization"), "UNRECONCILED_ARCHITECTURE"),
])
def test_incomplete_or_unverified_final_claims_fail(target_case, mutate, code):
    repo, state, proposal, policy = target_case
    mutate(proposal)
    with pytest.raises(OrchiError, check=lambda e: e.code == code):
        reconciliation.validate(repo, state, proposal, policy)


def test_deviation_is_explicit_and_still_requires_proof(target_case):
    repo, state, proposal, policy = target_case
    proposal["architecture"][0].update(disposition="deviated", reason="Reviewed evidence favors the implemented module boundary")
    assert reconciliation.validate(repo, state, proposal, policy) == ["suite"]
    proposal["architecture"][0]["checks"] = []
    with pytest.raises(OrchiError, check=lambda e: e.code == "UNVERIFIED_ARCHITECTURE"):
        reconciliation.validate(repo, state, proposal, policy)


def test_policy_exceptions_remain_explicitly_unresolved(target_case):
    repo, state, proposal, policy = target_case
    policy = policy.model_copy(update={"allow_unresolved_requirements": True, "allow_unrealized_architecture": True})
    for item in [*proposal["requirements"], *proposal["architecture"]]:
        item.update(disposition="unresolved", reason="Explicit operator-accepted exception", checks=[])
    assert reconciliation.validate(repo, state, proposal, policy) == []
    assert all(item["disposition"] == "unresolved" for item in [*proposal["requirements"], *proposal["architecture"]])


@pytest.mark.parametrize("text,code", [
    ("---\nkind: architecture\n---\n# Future system\n", "TARGET_AS_CORE"),
    ("---\nkind: component\nrole: target\n---\n# Mixed authority\n", "FINAL_DOC_AUTHORITY"),
    ("---\nkind: component\nrelations: {invalid_relation: [docs/README.md]}\n---\n# Current\n", "FINAL_DOC_ONTOLOGY"),
    ("---\nkind: component\n---\n# Current\n[Broken](missing.md)\n", "FINAL_DOC_ONTOLOGY"),
])
def test_final_core_ontology_rejects_target_markers_and_broken_claim_links(world, text, code):
    commit = world.e.repo.write(world.baseline, {"docs/architecture.md": text.encode()}, "Invalid final-doc fixture")
    with pytest.raises(OrchiError, check=lambda e: e.code == code):
        context.validate_final_docs(world.e.repo, commit, strict_paths=["docs/architecture.md"])


def test_lint_exposes_invalid_and_hidden_metadata_without_indexing_it(world):
    commit = world.e.repo.write(world.baseline, {
        "docs/malformed.md": b"---\nkind: [\n---\n# Malformed\n",
        "docs/draft.md": b"---\nstatus: draft\n---\n# Proposed\n",
    }, "Metadata diagnostic fixture")
    state = {"policy": {"canonical_ref": commit}}
    report = context.lint(world.e.repo, state)
    assert not report["ok"]
    assert {"INVALID_FRONTMATTER", "FORBIDDEN_AUTHORITY_METADATA"} <= {d["code"] for d in report["diagnostics"]}
    with pytest.raises(OrchiError, check=lambda e: e.code == "INVALID_FRONTMATTER"):
        context.search(world.e.repo, state, "Malformed")


def test_code_formatted_headings_keep_addressable_anchors():
    assert "public-api" in ontology.anchors("## `Public API`\n")[0]
