"""Human-facing projections. Every file/view is derived; none changes authority."""
from __future__ import annotations

import json
from pathlib import Path
import os
import tempfile
import shutil

from . import context
from .common import digest, integration_base, require, write_json


def gate(engine) -> dict:
    state = engine.state()
    require(state["pending"] is not None, "NO_APPROVAL_PENDING", "No human decision is pending")
    request = state["pending"]["request"]
    inputs = request["inputs"]
    result = {"request_id": request["id"], "request_digest": digest(request), "kind": request["kind"],
              "initiative": state["spec"]["id"], "expires_at": request["expires_at"],
              "origin_baseline": state["baseline"], "integration_base": integration_base(state), "head": state["head"],
              "policy_digest": request["policy_digest"], "outcome": state["spec"]["outcome"],
              "canonical_ref": engine.policy.canonical_ref, "publication_mode": engine.policy.publication_mode}
    if "intent_bundle" in inputs:
        bundle = engine.store.get_artifact(inputs["intent_bundle"])
        result["intent_documents"] = bundle["documents"]
        result["roadmap"] = inputs["spec"]["epics"]
    plan = inputs.get("plan") or inputs.get("first_plan")
    if plan:
        result["epic"] = plan["epic_id"]
        result["design"] = engine.store.get_artifact(inputs["design_artifact"])["content"]
        result["tasks"] = [{"id": t["id"], "goal": t["goal"], "kind": t["kind"], "executor": t["executor"],
                            "depends_on": t["depends_on"], "writes": [e["path"] for e in t["edits"]],
                            "scope": t["write_scope"], "decisions": t["decisions"],
                            "allowed_choices": t["allowed_choices"], "acceptance": t["acceptance"]} for t in plan["tasks"]]
        result["initial_parallel_frontier"] = [t["id"] for t in plan["tasks"] if not t["depends_on"]]
        result["preflight"] = inputs.get("preflight")
    for key in ("reason", "affected", "candidate", "tree", "upstream", "proposal", "verification", "review", "reconciliation", "publication_mode"):
        if key in inputs:
            result[key] = inputs[key]
    if "candidate" in inputs:
        result["diff"] = engine.repo.patch(integration_base(state), inputs["candidate"])
    result["decision_command"] = "operator.py decide --control <control> --request-id " + request["id"] + " --private <operator-key> --operator <name> --decision approve|reject"
    return result


def render_gate(value: dict) -> str:
    lines = ["# " + value["kind"] + " approval: " + value["initiative"],
             "Request: " + value["request_id"], "Request SHA256: " + value["request_digest"],
             "Canonical ref: " + value["canonical_ref"], "Integration base: " + value["integration_base"], "Accepted head: " + value["head"],
             "\n## Outcome\n" + value["outcome"]]
    for name, content in value.get("intent_documents", {}).items():
        lines.append("\n## Target source: " + name + "\n<source-data>\n" + content + "\n</source-data>")
    if value.get("design"):
        lines.append("\n## Exact selected design\n<source-data>\n" + value["design"] + "\n</source-data>")
    for key in ("tasks", "initial_parallel_frontier", "preflight", "reason", "affected", "candidate", "tree", "upstream", "proposal", "verification", "review", "reconciliation", "publication_mode", "diff"):
        if key in value:
            body = value[key] if isinstance(value[key], str) else json.dumps(value[key], ensure_ascii=False, indent=2)
            lines.append("\n## " + key.replace("_", " ").title() + "\n" + body)
    lines.append("\n" + value["decision_command"])
    return "\n".join(lines) + "\n"


def overview(engine) -> dict:
    state = engine.state()
    result = {"next": engine.next(), "original_baseline": state.get("baseline"),
              "integration_base": integration_base(state) if state.get("spec") else None,
              "knowledge_head": state.get("knowledge_head"), "target_revision_required": state.get("target_revision_required", False),
              "completed_epics": [e["epic_id"] for e in state["completed"]], "tasks": []}
    if state.get("active"):
        for task in state["active"]["plan"]["tasks"]:
            meta = state["active"]["tasks"][task["id"]]
            ticket = state["tickets"].get(meta.get("ticket"), {})
            result["tasks"].append({"id": task["id"], "goal": task["goal"], "status": meta["status"],
                                    "executor": ticket.get("executor", task["executor"]), "depends_on": task["depends_on"],
                                    "reason": meta.get("reason"), "candidate": ticket.get("candidate"),
                                    "ticket": ticket.get("id"), "scope_grants": ticket.get("scope_grants", []),
                                    "integration_attempts": ticket.get("integration_attempts", [])})
    if state.get("spec"):
        result["upstream"] = engine.sync_status()
    return result


def materialize(engine, directory: str | Path, view: str = "all") -> dict:
    require(view in {"current", "target", "all"}, "INVALID_VIEW", view)
    state = engine.state()
    require(state.get("spec") is not None and state.get("intent") is not None, "NO_ACCEPTED_INTENT", "Accept the initiative before materializing its views")
    dest = Path(directory).absolute()
    require(not any(p.is_symlink() for p in [dest, *dest.parents]), "UNSAFE_PATH", str(dest))
    require(not dest.resolve().is_relative_to(engine.repo.root), "DERIVED_OUTPUT_BOUNDARY", "Generated views must be outside the tracked repository")
    require(not dest.exists(), "OUTPUT_EXISTS", "Use a new immutable projection directory")
    snapshot = context.retrieval_snapshot(engine.repo, state, state["spec"]["id"], view)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".orchi-view-", dir=dest.parent))
    manifest = {"derived": True, "identity": snapshot.identity, "diagnostics": snapshot.diagnostics,
                "records": {}, "notice": "Read-only derived snapshots. Edit authoritative source through its lifecycle, not this projection."}
    try:
        for name, record in snapshot.records.items():
            relative = record["role"] + "/" + name
            output = temporary / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(record["content"], encoding="utf-8")
            manifest["records"][relative] = {k: record[k] for k in ("target", "role", "source_commit", "source_path", "content_hash")}
        write_json(temporary / "manifest.json", manifest)
        (temporary / "README.md").write_text("# Orchi knowledge view\n\n" + manifest["notice"] + "\n\nCurrent and Target remain distinct. See manifest.json for exact provenance and any masked/stale diagnostics.\n", encoding="utf-8")
        # Data is exact; role labels live in directories and a separate manifest.
        for file in temporary.rglob("*"):
            if file.is_file():
                file.chmod(0o444)
        os.rename(temporary, dest)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"status": "blocked" if snapshot.diagnostics else "ready", "path": str(dest), "derived": True,
            "records": len(manifest["records"]), "manifest_digest": digest(manifest), "diagnostics": snapshot.diagnostics}
