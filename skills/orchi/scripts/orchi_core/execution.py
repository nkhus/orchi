"""Bounded execution, immutable candidates and optimistic exact-head integration.

No long-running verification holds the aggregate's global operation slot. SQLite
acceptance is a compare-and-swap, not an assertion that isolated tests compose.
"""
from __future__ import annotations

import copy
from pathlib import Path, PurePosixPath
import time
import uuid

from . import context
from .common import OrchiError, canonical, digest, path, protected, require, safe_text, secret_path, sha
from .models import EpicPlan, ScopeRequest, WorkerResult

LIVE = {"claimed", "running", "checking", "validated", "integrating"}


def execution_allowed(state: dict, task_id: str) -> bool:
    if state["phase"] == "EXECUTING":
        return True
    pending = state.get("pending")
    return bool(pending and pending["request"]["kind"] == "tasks-amend"
                and task_id not in pending["request"]["inputs"]["affected"])


def submit(engine, ticket_id: str, raw: dict) -> dict:
    result = WorkerResult.model_validate(raw).model_dump()
    with engine.store.transaction("task.submission.freeze") as state:
        existing = state["tickets"].get(ticket_id)
        require(existing is not None, "UNKNOWN_TICKET", ticket_id)
        require(execution_allowed(state, existing["task_id"]), "WRONG_PHASE", state["phase"])
        ticket = engine._ticket(state, ticket_id, {"running", "validated"})
        result_id = engine.store.artifact(result)
        if ticket["status"] == "validated":
            require(result_id == ticket["result"], "RESULT_CHANGED", "Integrate the frozen candidate or explicitly retry the task")
            resume = True
        else:
            resume = False
            if result["status"] != "completed" or result["deviations"]:
                ticket.update(status="blocked", result=result_id)
                state["active"]["tasks"][ticket["task_id"]].update(status="blocked", reason=result["summary"])
                return {"status": "blocked", "reason": result["summary"]}
            for name in result["extra_reads"]:
                require(not secret_path(name) and not name.startswith(("docs/", "intent/", "initiatives/", ".git/")),
                        "SOURCE_SCOPE", "Use ticket-scoped knowledge reads for authority-managed sources: " + name)
                ticket["reads"].update(engine.repo.hashes(ticket["start_commit"], [name]))
            engine._fresh_reads(state, ticket)
            task = engine._task(state, ticket["task_id"])
            candidate = engine.repo.snapshot(Path(ticket["workspace"]), ticket["start_commit"], set(ticket["writes"]))
            changed = engine.repo.diff(ticket["start_commit"], candidate)
            require(bool(changed) if task["kind"] == "implementation" else not changed,
                    "EMPTY_CANDIDATE" if task["kind"] == "implementation" else "INVESTIGATION_PRODUCT_WRITE",
                    "Implementation requires product changes; investigations must not alter product files")
            require(task["kind"] != "investigation" or bool(result["observations"]),
                    "OBSERVATIONS_REQUIRED", "An investigation must preserve its findings as evidence")
            require(set(changed) <= set(ticket["writes"]), "SCOPE_VIOLATION", "Candidate escaped accepted scope")
            for proposal in result["documentation_proposals"]:
                safe_text(proposal["content"].encode(), proposal["target"])
            engine._assert_core(state, candidate)
            # Controller-owned evidence is not a worker edit and not Current documentation.
            report_path = (engine._prefix(state) + "epics/" + ticket["epic_id"]
                           + "/observations/" + ticket_id + ".json")
            candidate = engine.repo.write(candidate, {report_path: canonical({
                "task": task["id"], "ticket": ticket_id, "result": result,
                "scope_grants": ticket.get("scope_grants", []), "read_events": ticket.get("read_events", []),
                "imports": ticket.get("imports", []), "authority": "evidence-only",
            })}, "Orchi task evidence")
            task_checks = sorted({c for v in task["verification"] for c in v["checks"]})
            token = uuid.uuid4().hex
            ticket.update(status="checking", candidate=candidate, result=result_id, validation_id=token,
                          task_checks=task_checks)
            state["active"]["tasks"][ticket["task_id"]].update(status="checking", candidate=candidate)
    if not resume:
        isolated = engine._checks(candidate, task_checks, "task")
        with engine.store.transaction("task.isolated.accept") as state:
            ticket = engine._ticket(state, ticket_id, {"checking"})
            require(ticket["validation_id"] == token, "STALE_VALIDATION", "Another attempt owns this validation")
            state["evidence"].append(isolated)
            ticket["isolated"] = isolated["id"]
            meta = state["active"]["tasks"][ticket["task_id"]]
            if not isolated["passed"]:
                ticket["status"] = "blocked"
                meta.update(status="blocked", reason="Isolated checks failed", candidate=candidate)
                return {"status": "blocked", "isolated": isolated["id"], "combined": None}
            ticket["status"] = meta["status"] = "validated"
    return integrate(engine, ticket_id)


def integrate(engine, ticket_id: str) -> dict:
    for _ in range(engine.policy.max_integration_retries):
        with engine.store.transaction("task.integration.prepare") as state:
            ticket = engine._ticket(state, ticket_id, {"validated"})
            if state["phase"] != "EXECUTING" or state["operation"] is not None:
                return {"status": "validated", "ticket": ticket_id, "candidate": ticket["candidate"],
                        "reason": "Integration deferred until the pending gate/operation is resolved"}
            engine._fresh_reads(state, ticket)
            head = state["head"]
            try:
                combined = engine.repo.merge_candidate(head, ticket["start_commit"], ticket["candidate"])
            except OrchiError as exc:
                if exc.code != "INTEGRATION_CONFLICT":
                    raise
                ticket["status"] = "blocked"
                state["active"]["tasks"][ticket["task_id"]].update(status="blocked", reason=str(exc), candidate=ticket["candidate"])
                return {"status": "blocked", "code": exc.code, "candidate": ticket["candidate"], "reason": str(exc)}
            observations = ticket.get("snapshot_reads", {})
            now = engine.repo.hashes(head, list(observations))
            changed_observations = sorted(p for p in observations if observations[p] != now[p])
            if engine.policy.verification_strategy == "cumulative":
                checks = set(engine._all_checks(state)) | set(ticket["task_checks"])
            else:
                checks = set(engine.policy.baseline_checks + engine.policy.integration_checks + ticket["task_checks"])
            if changed_observations:
                # An operator-declared snapshot observation is not a hard equality assumption.
                # Broaden checks, expose its drift to review, and keep exact before/after provenance.
                checks.update(engine._all_checks(state))
                checks.update(engine.policy.integration_checks)
                # Do not run acceptance for unfinished tasks early. The mandatory
                # full epic review/checkpoint establishes the final joint contract.
            token = uuid.uuid4().hex
            ticket.update(status="integrating", integration_id=token, integration_head=head)
            state["active"]["tasks"][ticket["task_id"]]["status"] = "integrating"
        checked = engine._checks(combined, sorted(checks), "combined")
        with engine.store.transaction("task.integration.compare-and-swap") as state:
            ticket = engine._ticket(state, ticket_id, {"integrating"})
            require(ticket["integration_id"] == token, "STALE_VALIDATION", "Integration token was fenced")
            state["evidence"].append(checked)
            meta = state["active"]["tasks"][ticket["task_id"]]
            attempt = {"head": head, "candidate": combined, "evidence": checked["id"],
                       "changed_snapshot_reads": changed_observations}
            if state["head"] != head or state["phase"] != "EXECUTING" or state["operation"] is not None:
                attempt["disposition"] = "superseded"
                ticket["integration_attempts"].append(attempt)
                ticket["status"] = meta["status"] = "validated"
                continue
            if not checked["passed"]:
                attempt["disposition"] = "failed"
                ticket["integration_attempts"].append(attempt)
                ticket["status"] = "blocked"
                meta.update(status="blocked", reason="Combined compatibility checks failed", candidate=ticket["candidate"])
                return {"status": "blocked", "isolated": ticket["isolated"], "combined": checked["id"]}
            engine._fresh_reads(state, ticket)
            engine._assert_core(state, combined)
            attempt["disposition"] = "accepted"
            ticket["integration_attempts"].append(attempt)
            state["head"] = combined
            ticket["status"] = "integrated"
            meta.update(status="integrated", commit=combined, evidence=checked["id"],
                        snapshot_revalidation=changed_observations)
            engine._pin(state, "head", combined)
            return {"status": "integrated", "head": combined, "evidence": checked["id"],
                    "isolated": ticket["isolated"], "recompositions": len(ticket["integration_attempts"]) - 1}
    return {"status": "validated", "ticket": ticket_id, "reason": "Recomposition budget reached; integrate the frozen candidate later without rerunning the worker"}


def acquire_scope(engine, ticket_id: str, raw: dict) -> dict:
    request = ScopeRequest.model_validate(raw).model_dump()
    require(request["change_kind"] == "local", "AMEND_REQUIRED", "Design/target changes require their explicit approval boundary")
    with engine.store.transaction("task.scope.acquire") as state:
        ticket = engine._ticket(state, ticket_id, {"claimed", "running"})
        require(execution_allowed(state, ticket["task_id"]), "WRONG_PHASE", state["phase"])
        task = engine._task(state, ticket["task_id"])
        edit, choice = request["edit"], request["choice"]
        name = edit["path"]
        require(task["kind"] == "implementation", "INVESTIGATION_PRODUCT_WRITE", "Investigations do not acquire product writes")
        require(name not in ticket["writes"], "SCOPE_ALREADY_GRANTED", name)
        require(len(ticket["scope_grants"]) < task["max_scope_additions"], "SCOPE_BUDGET", "Amend or split the task")
        require(any(name.startswith(rule["directory"] + "/") and edit["action"] in rule["actions"]
                    and choice in rule["choices"] for rule in task["write_scope"]),
                "SCOPE_NOT_DELEGATED", "No accepted directory/action/local-choice rule covers " + name)
        require(choice in task["allowed_choices"], "UNDELEGATED_CHOICE", choice)
        # Even an inactive producer's planned output is a contract, not an available path.
        others = {e["path"] for t in state["active"]["plan"]["tasks"] if t["id"] != task["id"] for e in t["edits"]}
        others.update(p for t in state["tickets"].values() if t["id"] != ticket_id and t["status"] in LIVE for p in t["writes"])
        require(name not in others, "SCOPE_CONFLICT", "Another task owns or promises " + name)
        files = engine.repo.files(ticket["start_commit"])
        require((edit["action"] == "create") == (name not in files), "INVALID_EDIT_ACTION", name)
        require(engine.repo.files(state["head"]).get(name) == files.get(name), "STALE_WRITE", "The proposed path changed since dispatch")
        required_reads = [name]
        instructions = []
        parent = PurePosixPath(name).parent
        for directory in [PurePosixPath("."), *reversed(list(parent.parents)[:-1]), parent]:
            for instruction in ("AGENTS.override.md", "AGENTS.md"):
                item = str(directory / instruction)
                if item in files:
                    text = safe_text(engine.repo.read(ticket["start_commit"], item), item)
                    required_reads.append(item)
                    instructions.append({"path": item, "source_commit": ticket["start_commit"], "content_hash": sha(text.encode()), "content": text})
                    break
        ticket["reads"].update(engine.repo.hashes(ticket["start_commit"], required_reads))
        ticket["writes"] = sorted(set(ticket["writes"]) | {name})
        grant = {**request, "ticket": ticket_id, "start_commit": ticket["start_commit"],
                 "instructions": [{k: v for k, v in i.items() if k != "content"} for i in instructions]}
        ticket["scope_grants"].append(engine.store.artifact(grant))
        return {"status": "granted", "path": name, "grant": ticket["scope_grants"][-1], "instructions": instructions,
                "notice": "This is a mechanical envelope grant, not permission to alter fixed decisions or accepted requirements."}


def ticket_read(engine, ticket_id: str, target: str, *, view: str = "code", content_hash: str | None = None,
                start_line: int = 1, end_line: int | None = None, consistency: str = "fixed") -> dict:
    require(view in {"code", "current", "target", "epic-design"}, "INVALID_VIEW", view)
    require(consistency in {"fixed", "snapshot"}, "INVALID_CONSISTENCY", consistency)
    require(isinstance(start_line, int) and not isinstance(start_line, bool) and start_line >= 1,
            "INVALID_RANGE", "Lines are one-based")
    with engine.store.transaction("task.source.read") as state:
        ticket = engine._ticket(state, ticket_id, {"claimed", "running"})
        frozen = engine.store.get_artifact(ticket["authority_snapshot"])
        if view == "code":
            name = path(target)
            require(not secret_path(name) and not name.startswith(("docs/", "intent/", "initiatives/", "history/", ".git/", ".agents/")),
                    "SOURCE_SCOPE", "Read authority-managed knowledge with its explicit view")
            text = safe_text(engine.repo.read(ticket["start_commit"], name), name, 8_000_000)
            record = {"target": name, "source_path": name, "source_commit": ticket["start_commit"],
                      "content_hash": sha(text.encode()), "role": "implementation", "content": text}
            hashes = engine.repo.hashes(ticket["start_commit"], [name])
            if consistency == "fixed":
                ticket["reads"].update(hashes)
            else:
                ticket["snapshot_reads"].update(hashes)
        elif view == "epic-design":
            packet = engine.store.get_artifact(ticket["packet_id"])
            candidates = [s for s in packet["sources"] if s["role"] == "epic-design" and s["target"] == target]
            require(len(candidates) == 1, "MISSING_SOURCE", target)
            record = candidates[0]
            text = safe_text(engine.repo.read(record["source_commit"], record["source_path"]), target)
        else:
            record = context.get(engine.repo, frozen, target, frozen["spec"]["id"], view=view)
            text = record["content"]
        if content_hash is not None:
            require(record["content_hash"] == content_hash, "KNOWLEDGE_CHANGED", "Expected exact source hash does not match")
        lines = text.splitlines(keepends=True)
        if not lines and end_line is None and start_line == 1:
            lines = [""]
        end_line = len(lines) if end_line is None else end_line
        require(isinstance(end_line, int) and not isinstance(end_line, bool)
                and 1 <= start_line <= end_line <= len(lines), "INVALID_RANGE", "Requested lines do not exist")
        selected = "".join(lines[start_line - 1:end_line])
        require(len(selected.encode()) <= 128_000, "READ_TOO_LARGE", "Select a narrower line range")
        result = {k: record[k] for k in ("target", "source_path", "source_commit", "content_hash", "role")}
        result.update(content=selected, start_line=start_line, end_line=end_line, total_lines=len(lines),
                      slice_hash=sha(selected.encode()), consistency=consistency,
                      notice="content_hash binds the complete source; slice_hash binds the returned exact lines")
        ticket["read_events"].append(engine.store.artifact({k: v for k, v in result.items() if k != "content"}))
        return result


def handoff(engine, ticket_id: str, stopped: bool, reason: str, executor: str = "human") -> dict:
    require(stopped and bool(reason.strip()), "STOP_ATTESTATION_REQUIRED", "Confirm the previous executor and checks stopped")
    require(executor in {"human", "agent", "pair"}, "INVALID_EXECUTOR", executor)
    safe_text(reason.encode(), "handoff")
    with engine.store.transaction("task.handoff.preserve") as state:
        require(state["phase"] == "EXECUTING" and state["operation"] is None, "WRONG_PHASE", "Handoff inside an idle execution phase")
        ticket = state["tickets"].get(ticket_id)
        require(ticket and ticket["status"] in LIVE | {"blocked"}, "STALE_TICKET", ticket_id)
        require(ticket["epoch"] == state["epoch"] and state["active"]["tasks"][ticket["task_id"]]["ticket"] == ticket_id,
                "STALE_TICKET", "Only the owning attempt can hand off")
        candidate = ticket.get("candidate")
        if candidate is None:
            candidate = engine.repo.snapshot(Path(ticket["workspace"]), ticket["start_commit"], set(ticket["writes"]))
        notes = {"ticket": ticket_id, "candidate": candidate, "base": ticket["start_commit"], "reason": reason,
                 "executor": executor, "reads": ticket["reads"], "scope_grants": ticket["scope_grants"],
                 "read_events": ticket.get("read_events", []), "result": ticket.get("result")}
        record = engine.store.artifact(notes)
        ticket.update(status="released", stop_reason=reason, handoff=record, candidate=candidate)
        state["active"]["tasks"][ticket["task_id"]].update(status="blocked", candidate=candidate,
                                                          handoff=record, reason=reason)
        task_id = ticket["task_id"]
    engine.retry(task_id, "Explicit handoff: " + reason)
    new_ticket = engine.claim(task_id)
    with engine.store.transaction("task.handoff.assign") as state:
        state["tickets"][new_ticket["id"]]["executor"] = executor
        state["tickets"][new_ticket["id"]]["handoff_from"] = record
    reacquired, blocked_grants = [], []
    for grant_id in notes["scope_grants"]:
        old = engine.store.get_artifact(grant_id)
        try:
            reacquired.append(acquire_scope(engine, new_ticket["id"], {k: old[k] for k in ("edit", "choice", "reason", "change_kind")}))
        except OrchiError as exc:
            blocked_grants.append({"prior_grant": grant_id, "code": exc.code, "reason": str(exc)})
    return {"status": "claimed", "ticket": engine.state()["tickets"][new_ticket["id"]], "handoff": notes,
            "reacquired_scope": reacquired, "blocked_scope": blocked_grants,
            "next": "Read the new packet and notes, activate, then import-candidate using the preserved base/candidate. No edits are silently promoted."}


def import_candidate(engine, ticket_id: str, commit: str, base: str, reason: str) -> dict:
    require(bool(reason.strip()), "REASON_REQUIRED", "Explain the existing diff's origin")
    commit, base = engine.repo.resolve(commit), engine.repo.resolve(base)
    with engine.store.transaction("task.candidate.import") as state:
        ticket = engine._ticket(state, ticket_id, {"running"})
        require(execution_allowed(state, ticket["task_id"]), "WRONG_PHASE", state["phase"])
        if ticket.get("handoff_from"):
            old = engine.store.get_artifact(ticket["handoff_from"])
            if old["candidate"] == commit and old["base"] == base:
                require(engine.repo.hashes(ticket["start_commit"], list(old["reads"])) == old["reads"],
                        "IMPORT_ASSUMPTIONS_STALE", "Preserved fixed assumptions changed; reconcile manually against the new packet rather than importing the old diff")
        changes = engine.repo.diff(base, commit)
        # Internal observations from a prior Orchi attempt are reused as notes, never as edits.
        changes = [p for p in changes if not p.startswith(engine._prefix(state))]
        require(bool(changes), "EMPTY_CANDIDATE", "No product diff to import")
        require(all(not protected(p) for p in changes), "PROTECTED_PATH", "Import documents as proposals, never as product writes")
        require(set(changes) <= set(ticket["writes"]), "SCOPE_VIOLATION", "Import exceeds the accepted task writes")
        workspace = Path(ticket["workspace"])
        current = engine.repo.snapshot(workspace, ticket["start_commit"], set(ticket["writes"]))
        require(not engine.repo.diff(ticket["start_commit"], current), "WORKSPACE_DIRTY", "Import only into a clean activated worktree")
        old, start, after = engine.repo.files(base), engine.repo.files(ticket["start_commit"]), engine.repo.files(commit)
        require(all(old.get(p) == start.get(p) for p in changes), "IMPORT_CONFLICT", "Imported before-images differ; reconcile manually")
        contents = {}
        for name in changes:
            path(name)
            target = workspace / name
            require(not any(p.is_symlink() for p in [target, *target.parents]), "UNSAFE_PATH", name)
            contents[name] = engine.repo.read(commit, name) if name in after else None
        for name, content in contents.items():
            target = workspace / name
            if content is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                target.chmod(0o755 if after[name][0] == "100755" else 0o644)
        record = {"commit": commit, "base": base, "reason": reason, "paths": changes, "ticket": ticket_id}
        ticket.setdefault("imports", []).append(engine.store.artifact(record))
        return {"status": "imported", **record, "notice": "Imported work is unverified. Submit runs local checks and combined checks; review and approval are still required."}


def amend_tasks(engine, raw: dict, design: str, affected: list[str], reason: str) -> dict:
    """Narrow amendment: identical shared design, unchanged unaffected contracts."""
    plan = EpicPlan.model_validate(raw).model_dump()
    require(bool(affected) and bool(reason.strip()), "INVALID_AMENDMENT", "Identify affected tasks and reason")
    with engine.store.transaction("tasks.amend.propose") as state:
        require(state["phase"] == "EXECUTING" and state["pending"] is None and state["operation"] is None,
                "WRONG_PHASE", "Amend pending tasks inside an executing epic")
        active = state["active"]
        old = active["plan"]
        old_tasks, new_tasks = ({t["id"]: t for t in p["tasks"]} for p in (old, plan))
        require(set(new_tasks) == set(old_tasks), "FULL_AMENDMENT_REQUIRED", "Adding/removing tasks requires a full epic amendment")
        require(plan["shared_design"] == old["shared_design"] and sha(design.encode()) == old["design"]["content_hash"],
                "FULL_AMENDMENT_REQUIRED", "Shared design changed")
        require(all(plan[k] == old[k] for k in ("goal", "acceptance", "acceptance_checks", "mode", "intent_digest")),
                "FULL_AMENDMENT_REQUIRED", "Shared acceptance/Intent changed")
        impacted = set(affected)
        require(impacted <= set(old_tasks), "UNKNOWN_TASK", "Unknown impacted task")
        while True:
            expanded = impacted | {t["id"] for t in [*old_tasks.values(), *new_tasks.values()] if set(t["depends_on"]) & impacted}
            if expanded == impacted:
                break
            impacted = expanded
        require(all(new_tasks[t] == old_tasks[t] for t in old_tasks.keys() - impacted),
                "UNDECLARED_IMPACT", "An unaffected contract changed")
        require(all(active["tasks"][t]["status"] in {"pending", "blocked"} for t in impacted),
                "AFFECTED_WORK_ACTIVE", "Stop/release affected work; integrated work needs a corrective design")
        require(not any(t["task_id"] in impacted and t["status"] in LIVE for t in state["tickets"].values()),
                "WORKERS_ACTIVE", "Stop affected workers before amendment")
        # Current implementation may already contain completed creates. Validate the full
        # definition against the original product snapshot, then bind it to the actual head.
        preview = copy.deepcopy(state)
        preview["head"] = active["initial_head"]
        checked_plan = {**plan, "based_on": preview["head"]}
        engine._validate_plan(preview, checked_plan, design)
        require(plan["based_on"] == state["head"], "STALE_PLAN", "Bind amendment to the current accepted head")
        return engine._request(state, "tasks-amend", {"plan": plan, "affected": sorted(impacted), "reason": reason,
                             "design_artifact": engine.store.artifact({"content": design})})


def accept_amendment(engine, state: dict, inputs: dict):
    active = state["active"]
    prior = copy.deepcopy(active)
    tasks = copy.deepcopy(active["tasks"])
    for task_id in inputs["affected"]:
        tasks[task_id] = {"status": "pending", "ticket": None, "repair": False,
                          "candidate": tasks[task_id].get("candidate")}
    state["plan_history"].append(prior)
    # _accept_epic writes the exact accepted definitions. Do not advance the epoch:
    # unchanged task+design identities remain valid for unrelated in-flight workers.
    engine._accept_epic(state, inputs, "epic")
    active = state["active"]
    active["initial_head"] = prior["initial_head"]
    active["tasks"] = tasks
    active["compatible_plan_digests"] = [*prior.get("compatible_plan_digests", []), prior["digest"]]
