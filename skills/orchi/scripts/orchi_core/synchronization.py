"""Reviewed code-and-knowledge synchronization at a closed initiative boundary.

Original baseline and all old evidence remain immutable. A prepared candidate is
not Current until checks, review, human signature, and upstream equality succeed.
"""
from __future__ import annotations

import copy
import fnmatch
import json
import uuid
from . import context, ontology
from .common import canonical, digest, integration_base, protected, require, safe_text
from .models import ReviewReport, SyncProposal

BOUNDARIES = {"PLANNING", "FINALIZING", "FINAL_REVIEW", "READY_TO_PUBLISH"}


def status(engine, state: dict | None = None) -> dict:
    state = state or engine.state()
    require(state.get("spec") is not None, "NO_INITIATIVE", "Start an initiative before synchronization")
    base = integration_base(state)
    upstream = engine.repo.resolve(engine.policy.canonical_ref)
    changes = engine.repo.diff(base, upstream)
    _, conflicts = engine.repo.three_way(base, state["head"], upstream)
    affected = []
    for target, entry in sorted(state["knowledge"].items()):
        artifact_changes = sorted(set(entry["artifact_hashes"]) & set(changes))
        if target in changes or artifact_changes:
            affected.append({"target": target, "upstream_document_changed": target in changes,
                             "changed_artifacts": artifact_changes, "working_action": entry["action"]})
    # Upstream can introduce new authoritative documentation for code this initiative
    # already changed. Such new Core must also be reconciled, not blindly inherited.
    local_changes = {p for p in engine.repo.diff(base, state["head"]) if not p.startswith(("initiatives/", "docs/"))}
    for target, record in context.core(engine.repo, upstream).items():
        if target in state["knowledge"]:
            continue
        overlaps = sorted(p for p in local_changes if any(fnmatch.fnmatchcase(p, pattern) for pattern in record.get("artifacts", [])))
        if overlaps:
            affected.append({"target": target, "upstream_document_changed": target in changes,
                             "changed_artifacts": overlaps, "working_action": "inherit"})
    affected.sort(key=lambda r: r["target"])
    return {"origin_baseline": state["baseline"], "integration_base": base, "head": state["head"],
            "upstream": upstream, "moved": upstream != base, "upstream_changes": changes,
            "code_conflicts": conflicts, "affected_knowledge": affected,
            "at_closed_boundary": state["phase"] in BOUNDARIES and state["active"] is None and state["pending"] is None,
            "notice": "Canonical movement never changes this initiative's Current until an explicit accepted sync."}


def draft(engine) -> dict:
    state = engine.state()
    impact = status(engine, state)
    return {"format": "orchi-sync", "based_on": state["head"], "upstream": impact["upstream"],
            "reason": "REPLACE: why this upstream snapshot is needed",
            "target_assessment": "REPLACE: assess accepted requirements, interfaces and future design assumptions",
            "target_revision_required": False,
            "resolutions": [{"path": p, "action": "replace", "content": "REPLACE: explicitly reconcile both versions\n",
                             "reason": "REPLACE: explain the merge resolution"} for p in impact["code_conflicts"]],
            "knowledge": [{"target": r["target"], "action": "update", "reason": "REPLACE: reconcile upstream and Working knowledge",
                           "content": "REPLACE: author the reconciled Current statement\n",
                           "artifacts": list(state["knowledge"].get(r["target"], {}).get("artifact_hashes", r["changed_artifacts"])),
                           "checks": state["knowledge"].get(r["target"], {}).get("checks", sorted(set(engine._all_checks(state))))} for r in impact["affected_knowledge"]],
            "checks": list(engine.policy.sync_checks)}


def _concrete(value: str, label: str):
    require(not value.strip().startswith("REPLACE:"), "UNRECONCILED_SYNC", label)


def prepare(engine, raw: dict) -> dict:
    proposal = SyncProposal.model_validate(raw).model_dump()
    _concrete(proposal["reason"], "Explain the synchronization")
    _concrete(proposal["target_assessment"], "Assess the target")
    with engine.store.transaction("initiative.sync.prepare") as state:
        require(state["phase"] in BOUNDARIES and state["active"] is None
                and state["pending"] is None and state["operation"] is None,
                "SYNC_BOUNDARY_REQUIRED", "Close or explicitly stop the epic and resolve pending approvals before sync")
        require(not any(t["status"] in {"claimed", "running", "checking", "validated", "integrating"} for t in state["tickets"].values()),
                "WORKERS_ACTIVE", "Stop/release all workers before synchronization")
        require(proposal["based_on"] == state["head"], "STALE_SYNC", "Prepare against the actual initiative head")
        impact = status(engine, state)
        upstream, base = proposal["upstream"], integration_base(state)
        require(upstream == impact["upstream"] and upstream != base, "STALE_UPSTREAM", "Select the current advanced canonical commit")
        require(engine.repo.is_ancestor(base, upstream), "UPSTREAM_REWRITE", "Rewritten/unrelated upstream needs explicit operator recovery, not ordinary synchronization")
        collision = "initiatives/archive/" + state["spec"]["id"] + "/"
        require(not any(p.startswith(collision) for p in impact["upstream_changes"]),
                "INITIATIVE_ID_COLLISION", "Another publication uses this initiative ID; never overwrite its provenance")
        edits, conflicts = engine.repo.three_way(base, state["head"], upstream)
        require({r["path"] for r in proposal["resolutions"]} == set(conflicts),
                "INCOMPLETE_SYNC_RESOLUTION", "Provide exactly one resolution per conflicted path")
        for resolution in proposal["resolutions"]:
            name = resolution["path"]
            _concrete(resolution["reason"], name)
            require(not protected(name), "PROTECTED_SYNC_CONFLICT", "Resolve protected-path conflicts through the operator-managed canonical workflow: " + name)
            if resolution["action"] == "replace":
                _concrete(resolution["content"], name)
                safe_text(resolution["content"].encode(), name, 8_000_000)
                edits[name] = (resolution["mode"], engine.repo.blob(resolution["content"].encode()))
            elif resolution["action"] == "delete":
                edits[name] = None
            else:
                source = engine.repo.files(resolution["commit"]).get(name)
                require(source is not None and source[0] in {"100644", "100755"}, "UNSAFE_SOURCE", name)
                edits[name] = source
        code_candidate = engine.repo.compose(state["head"], edits, "Orchi upstream synchronization candidate")
        affected = {r["target"]: r for r in impact["affected_knowledge"]}
        decisions = {r["target"]: r for r in proposal["knowledge"]}
        require(set(decisions) == set(affected), "INCOMPLETE_SYNC_KNOWLEDGE",
                "Reconcile exactly the affected Working records; never silently mask upstream Core edits")
        knowledge = copy.deepcopy(state["knowledge"])
        contents = {}
        check_ids = set(engine._all_checks(state)) | set(engine.policy.sync_checks) | set(proposal["checks"])
        files = engine.repo.files(code_candidate)
        for target, decision in decisions.items():
            _concrete(decision["reason"], target)
            if target not in knowledge:
                upstream_record = context.core(engine.repo, upstream)[target]
                knowledge[target] = {"target": target, "action": "replace", "content": upstream_record["content"],
                                     "artifact_hashes": engine.repo.hashes(code_candidate, affected[target]["changed_artifacts"]),
                                     "source_path": engine._prefix(state) + "knowledge/" + target}
            entry = knowledge[target]
            action = decision["action"]
            if action == "use-upstream":
                require(bool(decision["checks"]), "UNVERIFIED_KNOWLEDGE", target)
                check_ids.update(decision["checks"])
                contents[entry["source_path"]] = None
                knowledge.pop(target)
                continue
            if action == "revalidate":
                require(not affected[target]["upstream_document_changed"], "UPSTREAM_DOC_MASK",
                        "Revalidate cannot hide upstream changes to the same document; update, retire or use-upstream: " + target)
                artifacts = list(entry["artifact_hashes"])
            else:
                artifacts = decision["artifacts"]
                entry["action"] = "replace" if action == "update" else "retire"
                entry["content"] = decision["content"] if action == "update" else None
            require(bool(decision["checks"]), "UNVERIFIED_KNOWLEDGE", target)
            for name in artifacts:
                require(name in files or name in engine.repo.files(base), "MISSING_ARTIFACT", name)
            if entry["content"] is not None:
                _concrete(entry["content"], target)
                safe_text(entry["content"].encode(), target)
                fm = ontology.frontmatter(entry["content"])
                require(not set(fm) & ontology.AUTHORITY_FIELDS and fm.get("kind") not in {"requirements", "architecture"},
                        "PROPOSAL_AS_KNOWLEDGE", target)
            entry.update(artifact_hashes=engine.repo.hashes(code_candidate, artifacts), checks=decision["checks"],
                         reason=decision["reason"], verified_code_commit=code_candidate, evidence=None)
            contents[entry["source_path"]] = entry["content"].encode() if entry["action"] == "replace" else None
            check_ids.update(decision["checks"])
        require(check_ids <= set(engine.policy.checks), "UNKNOWN_CHECK", "Sync checks must be registered by the operator")
        prospective = context.core(engine.repo, upstream)
        for target, entry in knowledge.items():
            prospective.pop(target, None)
            if entry["action"] == "replace":
                prospective[target] = {"target": target, "content": entry["content"], "role": "current"}
        lint = ontology.lint(prospective, files, strict_paths=[t for t, d in decisions.items() if d["action"] == "update"],
                             lookup=lambda p: safe_text(engine.repo.read(code_candidate, p), p),
                             evidence=[e["id"] for e in state["evidence"]])
        require(lint["ok"], "SYNC_KNOWLEDGE_ONTOLOGY", json.dumps(lint["diagnostics"]))
        revision = state["knowledge_revision"] + 1
        contents[engine._prefix(state) + "knowledge/manifest.json"] = canonical({
            "format": "orchi-working-knowledge", "initiative_id": state["spec"]["id"], "revision": revision,
            "integration_base": upstream, "verified_code_commit": code_candidate,
            "entries": {t: {k: v for k, v in e.items() if k != "source_commit"} for t, e in knowledge.items()},
        })
        contents[engine._prefix(state) + "sync/" + str(len(state["sync_history"]) + 1) + "/proposal.json"] = canonical(proposal)
        candidate = engine.repo.write(code_candidate, contents, "Orchi prospective synchronized checkpoint")
        check_state = {**state, "integration_base": upstream}
        engine._assert_core(check_state, candidate)
        for target in decisions:
            if target in knowledge:
                knowledge[target]["source_commit"] = candidate
        op = {"id": uuid.uuid4().hex, "kind": "sync-checks", "head": state["head"]}
        state["operation"] = op
        prior_phase = state["phase"]
        before = {"head": state["head"], "integration_base": base, "knowledge_head": state["knowledge_head"],
                  "knowledge_revision": state["knowledge_revision"], "knowledge_digest": digest(state["knowledge"])}
    evidence = engine._checks(candidate, sorted(check_ids), "upstream-sync")
    with engine.store.transaction("initiative.sync.checked") as state:
        require(state["operation"] == op and state["head"] == op["head"], "STALE_SYNC", "Sync authority changed while checking")
        state["operation"] = None
        state["evidence"].append(evidence)
        if not evidence["passed"]:
            return {"status": "blocked", "candidate": candidate, "evidence": evidence["id"], "reason": "Sync checks failed; existing Current remains unchanged"}
        for target in decisions:
            if target in knowledge:
                knowledge[target]["evidence"] = evidence["id"]
        request = {"format": "orchi-review-request", "id": uuid.uuid4().hex, "scope": "sync", "key": "@sync",
                   "base": before["head"], "candidate": candidate, "mode": "full", "round": 1,
                   "required_paths": engine.repo.diff(before["head"], candidate),
                   "all_changed_paths": engine.repo.diff(before["head"], candidate),
                   "verification": evidence["id"], "checks": sorted(check_ids), "proposal": proposal,
                   "impact": impact, "diff": engine.repo.patch(before["head"], candidate),
                   "instructions": "Review the exact upstream composition, code conflicts, Current/Working decisions and Target impact. Check that no upstream knowledge is hidden. Observations are not automatic proof."}
        state["sync"] = {"candidate": candidate, "upstream": upstream, "knowledge": knowledge,
                         "knowledge_revision": revision, "before": before, "prior_phase": prior_phase,
                         "proposal": proposal, "evidence": evidence["id"], "review_request": request}
        state["phase"] = "SYNC_REVIEW"
        engine.store.artifact(request)
        return {"status": "sync_review_required", "candidate": candidate, "evidence": evidence["id"], "review_request": request}


def review(engine, raw: dict) -> dict:
    report = ReviewReport.model_validate(raw).model_dump()
    with engine.store.transaction("initiative.sync.review") as state:
        require(state["phase"] == "SYNC_REVIEW" and state["pending"] is None, "WRONG_PHASE", "Review the pending exact synchronization")
        sync = state["sync"]
        request = sync["review_request"]
        require(report["request_id"] == request["id"], "STALE_REVIEW", "Review request changed")
        require(set(request["required_paths"]) <= set(report["covered_paths"]), "INCOMPLETE_REVIEW", "Cover the complete synchronization diff")
        review_id = engine.store.artifact(report)
        sync.setdefault("review_history", []).append(review_id)
        if not report["complete"] or any(f["disposition"] == "blocker" for f in report["findings"]):
            return {"status": "blocked", "review": review_id, "reason": "Resolve synchronization blockers; Current is unchanged"}
        sync["review"] = review_id
        return engine._request(state, "sync", {"candidate": sync["candidate"], "upstream": sync["upstream"],
                             "tree": engine.repo.tree(sync["candidate"]), "knowledge_digest": digest(sync["knowledge"]),
                             "proposal": sync["proposal"], "verification": sync["evidence"], "review": review_id,
                             "before": sync["before"]})


def accept(engine, state: dict, inputs: dict, request: dict, approval: dict):
    sync = state["sync"]
    require(sync and inputs["candidate"] == sync["candidate"] and inputs["knowledge_digest"] == digest(sync["knowledge"]),
            "STALE_SYNC", "Prepared code/knowledge changed")
    require(engine.repo.resolve(engine.policy.canonical_ref) == sync["upstream"], "STALE_UPSTREAM", "Upstream moved again; withdraw this gate and prepare against its actual head")
    require(state["head"] == sync["before"]["head"], "STALE_SYNC", "Initiative moved")
    if state.get("final"):
        state["final_history"].append({"final": state["final"], "review": state["reviews"].get("@initiative"),
                                       "invalidated_by_sync": sync["candidate"]})
    state["reviews"].pop("@initiative", None)
    record = {"before": sync["before"], "candidate": sync["candidate"], "upstream": sync["upstream"],
              "knowledge_revision": sync["knowledge_revision"], "proposal": sync["proposal"],
              "evidence": sync["evidence"], "review": sync["review"], "gate": request,
              "approval": engine.store.artifact(approval)}
    state["sync_history"].append(record)
    state.update(head=sync["candidate"], integration_base=sync["upstream"], knowledge_head=sync["candidate"],
                 knowledge_revision=sync["knowledge_revision"], knowledge=sync["knowledge"], final=None,
                 target_revision_required=sync["proposal"]["target_revision_required"], sync=None)
    state["phase"] = "PLANNING" if engine.next_epic(state) is not None else "FINALIZING"


def discard(engine, reason: str) -> dict:
    require(bool(reason.strip()), "REASON_REQUIRED", "Explain why this prospective sync is discarded")
    with engine.store.transaction("initiative.sync.discard") as state:
        require(state["phase"] == "SYNC_REVIEW" and state["pending"] is None and state["operation"] is None,
                "WRONG_PHASE", "Withdraw a pending sync gate before discarding its candidate")
        sync = state["sync"]
        engine.store.artifact({"discarded_sync": sync, "reason": reason})
        state["phase"] = sync["prior_phase"]
        state["sync"] = None
        return {"status": "discarded", "head": state["head"], "phase": state["phase"]}
