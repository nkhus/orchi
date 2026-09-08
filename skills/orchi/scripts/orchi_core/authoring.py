"""Deterministic compact authoring. Inputs describe decisions; this module invents none."""
from __future__ import annotations

import yaml
from . import intent
from .models import ChangeBrief, Initiative, EpicPlan
from .common import digest, sha


def expand(raw: dict, baseline: str) -> tuple[dict, dict, dict, str]:
    brief = ChangeBrief.model_validate(raw).model_dump()
    ids = list(brief["requirements"])
    requirements = "---\n" + yaml.safe_dump({"kind": "requirements", "requirements": ids}, sort_keys=False) + "---\n# Requirements\n"
    for rid, text in brief["requirements"].items():
        requirements += f'\n<a id="{rid}"></a>\n## Requirement {rid}\n{text}\n'
    bundle = intent.build(brief["id"], {
        "source.md": brief["request"],
        "requirements.md": requirements,
        "architecture/README.md": "---\nkind: architecture\n---\n# Target boundaries\n" + brief["architecture"] + "\n",
    })
    spec = Initiative.model_validate({
        "id": brief["id"], "outcome": brief["outcome"], "result_kind": brief["result_kind"],
        "intent": {"revision": 1, "digest": digest(bundle["manifest"])},
        "epics": [{"id": "delivery", "title": brief["outcome"], "outcome": brief["outcome"],
                   "contributes_to": ids, "realizes": ["intent/architecture/README.md"]}],
    }).model_dump()
    design = ("---\n" + yaml.safe_dump({"kind": "reference", "relations": {
        "addresses": ids, "realizes": ["intent/architecture/README.md"]}}, sort_keys=False)
        + "---\n# Selected epic design\n" + brief["design"] + "\n\n## Fixed decisions\n"
        + "\n".join("- " + d for d in brief["decisions"]) + "\n\n## Invariants\n"
        + "\n".join("- " + d for d in brief["invariants"]) + "\n")
    tasks = []
    for item in brief["tasks"]:
        task = {k: v for k, v in item.items() if k != "checks"}
        task.update(
            acceptance=brief["requirements"], current_state="Read the exact bound implementation and knowledge sources.",
            approach=brief["design"], decisions=brief["decisions"], invariants=brief["invariants"],
            failure_modes=["Report evidence when an acceptance condition cannot be established."],
            verification=[{"criterion": rid, "scenario": item["goal"], "expected": text, "checks": item["checks"]}
                          for rid, text in brief["requirements"].items()],
            escalation=["Escalate changes to accepted requirements, fixed decisions or invariants."], open_questions=[],
        )
        tasks.append(task)
    plan = EpicPlan.model_validate({
        "initiative_id": spec["id"], "epic_id": "delivery", "based_on": baseline,
        "goal": brief["outcome"], "shared_design": brief["design"],
        "design": {"path": "design/1.md", "content_hash": sha(design.encode())},
        "intent_digest": spec["intent"]["digest"], "acceptance": brief["requirements"],
        "acceptance_checks": {rid: brief["checks"] for rid in ids},
        "mode": "implementation" if tasks else "knowledge-only", "tasks": tasks,
    }).model_dump()
    return spec, bundle, plan, design
