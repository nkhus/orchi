"""Bound known inputs before approval; explicitly do not guarantee future dependency outputs."""
from __future__ import annotations

import copy
from . import context
from .common import OrchiError, digest


def inspect(engine, state: dict, plan: dict, design: str) -> dict:
    preview = copy.deepcopy(state)
    preview["active"] = {
        "plan": plan, "digest": digest(plan),
        "tasks": {t["id"]: {"status": "pending"} for t in plan["tasks"]},
        "design_source": {
            "target": "epics/" + plan["epic_id"] + "/" + plan["design"]["path"],
            "source_commit": state["head"],
            "source_path": engine._prefix(state) + "epics/" + plan["epic_id"] + "/" + plan["design"]["path"],
            "content_hash": plan["design"]["content_hash"], "preview_content": design,
        },
    }
    rows = []
    for task in plan["tasks"]:
        try:
            packet = context.packet(engine.repo, preview, task, preflight=True)
            deferred = [r["target"] for r in packet["sources"] if r.get("delivery") == "deferred"]
            rows.append({"task": task["id"], "ok": True,
                         "known_packet_bytes": len(context.render_packet(packet).encode()),
                         "budget_bytes": state["policy"]["max_packet_bytes"],
                         "deferred_sources": deferred,
                         "on_demand_sources": [r["target"] for r in packet["sources"] if r.get("delivery") == "on-demand"],
                         "status": "known-inputs-ready" if not deferred else "dependency-output-checks-deferred"})
        except OrchiError as exc:
            rows.append({"task": task["id"], "ok": False, "code": exc.code, "message": str(exc)})
    return {"ok": all(r["ok"] for r in rows), "tasks": rows,
            "notice": "Checks known source/packet constraints only. Dependency outputs, runtime services and retry context are validated again before use."}
