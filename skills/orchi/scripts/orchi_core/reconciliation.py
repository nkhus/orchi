"""Final target dispositions. Structural completeness is mechanical; semantics are reviewed.

Every declared verification check is executed by the trusted controller on the
exact final candidate. Neither prose, graph links nor user-provided evidence IDs
can manufacture a passed check.
"""
from __future__ import annotations

from .common import require
from . import intent


def draft(repo, state: dict, final_checks: list[str]) -> dict:
    manifest = intent.accepted(repo, state)["manifest"]
    entries = [{"target": t, "action": r["action"], "content": r["content"], "artifacts": list(r["artifact_hashes"]),
                "checks": r["checks"], "reason": r["reason"]} for t, r in sorted(state["knowledge"].items())]
    requirements = [{"requirement_id": rid, "disposition": "unresolved", "reason": "REPLACE: assess acceptance conditions against final implementation",
                     "checks": list(final_checks), "core_targets": []} for rid in sorted(manifest["requirements"])]
    requirements += [{"requirement_id": rid, "disposition": "changed", "reason": reason,
                      "checks": [], "core_targets": []} for rid, reason in sorted(manifest["resolved_requirements"].items())]
    architecture = [{"target": ref, "disposition": "unresolved", "reason": "REPLACE: reconcile component boundaries and intentional deviations",
                     "artifacts": [], "core_targets": [], "checks": list(final_checks)} for ref in manifest["architecture"]]
    return {"format": "orchi-finalization", "initiative_id": state["spec"]["id"], "based_on": state["head"],
            "intent_digest": state["spec"]["intent"]["digest"],
            "report": "REPLACE: reconcile cumulative verified semantics, omissions, target deviations and final Core.",
            "entries": entries, "requirements": requirements, "architecture": architecture}


def validate(repo, state: dict, proposal: dict, policy) -> list[str]:
    manifest = intent.accepted(repo, state)["manifest"]
    require(proposal["intent_digest"] == state["spec"]["intent"]["digest"], "STALE_FINALIZATION", "Accepted target changed")
    known = set(manifest["requirements"]) | set(manifest["resolved_requirements"])
    require({r["requirement_id"] for r in proposal["requirements"]} == known,
            "INCOMPLETE_ACCEPTANCE", "Every active or explicitly resolved accepted requirement needs one final disposition")
    require({a["target"] for a in proposal["architecture"]} == set(manifest["architecture"]),
            "INCOMPLETE_ARCHITECTURE", "Reconcile every accepted target architecture document")
    checks = set()
    for requirement in proposal["requirements"]:
        rid = requirement["requirement_id"]
        require(not requirement["reason"].startswith("REPLACE:"), "UNRECONCILED_REQUIREMENT", rid)
        if rid in manifest["resolved_requirements"]:
            require(requirement["disposition"] == "changed", "INVALID_REQUIREMENT_DISPOSITION", "Use the accepted resolution for " + rid)
        else:
            require(requirement["disposition"] != "changed", "INTENT_REVISION_REQUIRED", "An active accepted requirement cannot be changed silently at finalization: " + rid)
            if requirement["disposition"] == "satisfied":
                require(bool(requirement["checks"]), "UNVERIFIED_REQUIREMENT", rid)
            else:
                require(policy.allow_unresolved_requirements, "UNRESOLVED_REQUIREMENT", rid)
        checks.update(requirement["checks"])
    files = repo.files(state["head"])
    for architecture in proposal["architecture"]:
        require(not architecture["reason"].startswith("REPLACE:"), "UNRECONCILED_ARCHITECTURE", architecture["target"])
        if architecture["disposition"] == "not-applicable":
            require(state["spec"].get("result_kind", "software") in {"knowledge", "investigation"}
                    and bool(architecture["checks"]), "INVALID_ARCHITECTURE_DISPOSITION",
                    "Not-applicable requires an accepted non-software outcome and candidate checks")
        elif architecture["disposition"] == "unchanged":
            require(bool(architecture["artifacts"]) and bool(architecture["checks"]),
                    "UNVERIFIED_ARCHITECTURE", "Unchanged architecture needs existing implementation references and candidate checks")
        elif architecture["disposition"] == "unresolved":
            require(policy.allow_unrealized_architecture, "UNREALIZED_ARCHITECTURE", architecture["target"])
        else:
            require(bool(architecture["artifacts"]) and bool(architecture["core_targets"]) and bool(architecture["checks"]),
                    "UNVERIFIED_ARCHITECTURE", "Realization/deviation needs implementation, Core and candidate checks: " + architecture["target"])
        for p in architecture["artifacts"]:
            require(p in files and files[p][0] in {"100644", "100755"}, "MISSING_ARTIFACT", p)
        checks.update(architecture["checks"])
    require(checks <= set(policy.checks), "UNKNOWN_CHECK", "Final dispositions may reference only operator-registered checks")
    return sorted(checks)


def validate_core_targets(repo, commit: str, proposal: dict) -> None:
    files = repo.files(commit)
    for item in [*proposal["requirements"], *proposal["architecture"]]:
        for target in item["core_targets"]:
            require(target in files, "MISSING_FINAL_CORE", target)
