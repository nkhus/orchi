"""Foreground multi-process worker adapter; stops at review, human or knowledge boundaries."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import copy
import json
import os
from pathlib import Path
import shutil
import time
from .common import OrchiError, digest, read_json, require, write_json
from .engine import Engine
from .models import Readiness, WorkerResult
from .process import run
from .agents import AGENTS
from .worker_adapters import invocation, structured_result


def output_schema(model) -> dict:
    schema = model.model_json_schema()
    def strict(node):
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["required"] = list(node.get("properties", {}))
                node["additionalProperties"] = False
            for v in node.values():
                strict(v)
        elif isinstance(node, list):
            for v in node:
                strict(v)
    strict(schema)
    return schema


def validate_adapter(adapter: dict) -> dict:
    require(isinstance(adapter, dict), "INVALID_ADAPTER", "Expected an adapter object")
    require(set(adapter) <= {"kind", "argv", "model", "executable", "pass_env", "allowed_tools"}, "INVALID_ADAPTER", "Unknown adapter keys")
    require(isinstance(adapter.get("kind"), str) and adapter["kind"] in {*AGENTS, "command"}, "INVALID_ADAPTER", "Use codex, copilot, claude, or command")
    for field in ("pass_env", "allowed_tools"):
        require(isinstance(adapter.get(field, []), list) and all(isinstance(x, str) and x and "\x00" not in x for x in adapter.get(field, [])),
                "INVALID_ADAPTER", f"{field} must be a list of nonempty strings")
    if "allowed_tools" in adapter:
        require(adapter["kind"] in {"claude", "copilot"} and bool(adapter["allowed_tools"]), "INVALID_ADAPTER", "allowed_tools is for Claude/Copilot execution only")
    if "model" in adapter:
        require(isinstance(adapter["model"], str) and bool(adapter["model"]) and "\x00" not in adapter["model"], "INVALID_ADAPTER", "model must be a nonempty string")
    if adapter["kind"] == "command":
        require(isinstance(adapter.get("argv"), list) and adapter["argv"] and all(isinstance(x, str) and x for x in adapter["argv"]),
                "INVALID_ADAPTER", "Provide an argv list, never shell text")
    else:
        require("argv" not in adapter, "INVALID_ADAPTER", "argv is only for command adapters")
        exe = adapter.get("executable", AGENTS[adapter["kind"]]["executable"])
        require(isinstance(exe, str) and bool(exe) and "\x00" not in exe, "INVALID_ADAPTER", "executable must be a nonempty path or command name")
        require(shutil.which(exe) is not None, adapter["kind"].upper() + "_NOT_INSTALLED", "Install and authenticate " + adapter["kind"] + " before a live run")
    require(all(isinstance(k, str) and "=" not in k for k in adapter.get("pass_env", [])), "INVALID_ADAPTER", "Pass environment names, not secrets")
    return adapter


def _phase(engine: Engine, ticket: dict, adapter: dict, phase: str) -> dict:
    home = Path(ticket["workspace"]).parent
    out = home / "output"
    out.mkdir(exist_ok=True)
    output = out / (phase + ".json")
    require(not output.exists() and not output.is_symlink(), "EXISTING_WORKER_RESULT", "Refusing to reuse an existing phase result")
    schema = home / "input" / (phase + ".schema.json")
    model = Readiness if phase == "prepare" else WorkerResult
    contract = output_schema(model)
    write_json(schema, contract)
    packet_file = Path(ticket["packet"])
    env = {k: os.environ[k] for k in adapter.get("pass_env", []) if k in os.environ}
    env.update(ORCHI_PHASE=phase, ORCHI_PACKET=str(packet_file), ORCHI_OUTPUT=str(output), ORCHI_SCHEMA=str(schema),
               ORCHI_WORKSPACE=ticket["workspace"], ORCHI_TICKET=ticket["id"])
    if adapter["kind"] != "command":
        argv, stdin = invocation(adapter, phase, (home / "input/TASK.md").read_text(), contract, schema, output, home / "input")
    else:
        argv = list(adapter["argv"])
        stdin = b""
    observation = run(argv, Path(ticket["workspace"]), engine.policy.max_process_seconds,
                      engine.policy.max_output_bytes, env=env, stdin=stdin)
    observation_id = engine.store.artifact({"ticket": ticket["id"], "phase": phase, "adapter_digest": digest(adapter),
                                             "observation": observation})
    require(observation["passed"], "WORKER_PROCESS_FAILED", f"{phase} process failed; inspect artifact {observation_id}")
    if adapter["kind"] in {"claude", "copilot"}:
        result = model.model_validate(structured_result(adapter["kind"], observation["stdout"]))
        require(not output.exists() and not output.is_symlink(), "EXISTING_WORKER_RESULT", "The adapter owns the phase output file")
        write_json(output, result.model_dump(mode="json"))
    require(output.is_file() and not output.is_symlink(), "MISSING_WORKER_RESULT", str(output))
    return model.model_validate(read_json(output)).model_dump(mode="json")


def execute_ticket(control: str, ticket: dict, adapter: dict) -> dict:
    e = Engine(control)
    try:
        readiness = _phase(e, ticket, adapter, "prepare")
        # Reject preparation that wrote product files, independently of adapter sandbox claims.
        e.repo.snapshot(Path(ticket["workspace"]), ticket["start_commit"], set())
        e.activate(ticket["id"], readiness)
        result = _phase(e, ticket, adapter, "execute")
        while True:
            try:
                return {"task_id": ticket["task_id"], **e.submit(ticket["id"], result)}
            except OrchiError as err:
                if err.code != "INTEGRATOR_BUSY":
                    raise
                require(time.time() < ticket["expires_at"], "LEASE_EXPIRED", "Waited too long for integrator")
                time.sleep(0.05)
    except Exception as exc:
        # run() has already terminated its subprocess group. Do not claim success or restart a paid session.
        try:
            state = e.state()
            if state["operation"] is None:
                e.release(ticket["id"], True, "Foreground process ended: " + str(exc)[:500])
        except OrchiError:
            pass
        return {"task_id": ticket["task_id"], "status": "blocked", "code": getattr(exc, "code", type(exc).__name__), "message": str(exc)}


def run_ready(engine: Engine, adapter: dict) -> dict:
    adapter = validate_adapter(adapter)
    futures, outcomes = {}, []
    with ThreadPoolExecutor(max_workers=engine.policy.max_workers) as pool:
        while True:
            while len(futures) < engine.policy.max_workers:
                if engine.state()["phase"] != "EXECUTING":
                    break
                try:
                    ticket = engine.claim()
                except OrchiError as err:
                    if err.code in {"NO_READY_TASK", "PARALLEL_LIMIT", "BUDGET_EXHAUSTED"}:
                        break
                    raise
                f = pool.submit(execute_ticket, str(engine.store.root), ticket, adapter)
                futures[f] = ticket["id"]
            if not futures:
                break
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for f in done:
                outcomes.append(f.result())
                del futures[f]
    return {"outcomes": outcomes, "next": engine.next(), "notice": "Foreground execution finished; no background agent was scheduled."}
