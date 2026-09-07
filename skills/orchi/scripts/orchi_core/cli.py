"""One JSON CLI for the skills and operator; never parse human text for workflow state."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from pydantic import ValidationError
from . import context
from .diagnostics import doctor
from .common import OrchiError, read_json, write_json
from .engine import Engine
from .models import CONTRACTS
from .runner import run_ready


def parser():
    p = argparse.ArgumentParser(prog="orchi", description="Initiative → iterative epics → portable tasks → one canonical publication")
    p.add_argument("--control", default=os.environ.get("ORCHI_CONTROL"), help="Operator-owned control directory; defaults to ORCHI_CONTROL")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("doctor", help="Inspect installation and prerequisites without initializing state")
    d.add_argument("--repo", help="Optionally check a target Git repository")
    d.add_argument("--require-codex", action="store_true", help="Fail when the Codex executable is missing")
    s = sub.add_parser("setup"); s.add_argument("--repo", required=True); s.add_argument("--policy", required=True)
    for name in ["begin", "plan", "apply-decision", "review-record", "checkpoint", "finalize"]:
        x = sub.add_parser(name); x.add_argument("--file", required=True)
    for name in ["roadmap", "amend"]:
        x = sub.add_parser(name); x.add_argument("--file", required=True); x.add_argument("--reason", required=True)
    for name in ["next", "status", "publication", "repair", "refresh-gate"]:
        sub.add_parser(name)
    for name in ["gate", "final-draft"]:
        x = sub.add_parser(name); x.add_argument("--out")
    x = sub.add_parser("claim"); x.add_argument("--task")
    for name in ["activate", "submit"]:
        x = sub.add_parser(name); x.add_argument("--ticket", required=True); x.add_argument("--file", required=True)
    x = sub.add_parser("release"); x.add_argument("--ticket", required=True); x.add_argument("--stopped", action="store_true"); x.add_argument("--reason", required=True)
    x = sub.add_parser("retry"); x.add_argument("--task", required=True); x.add_argument("--reason", required=True)
    x = sub.add_parser("run"); x.add_argument("--adapter", required=True)
    x = sub.add_parser("review-request"); x.add_argument("--scope", choices=["epic", "initiative"], default="epic"); x.add_argument("--out")
    x = sub.add_parser("record-publication"); x.add_argument("--commit", required=True)
    for name in ["pause", "resume-request"]:
        x = sub.add_parser(name); x.add_argument("--reason", required=True)
    x = sub.add_parser("recover-operation"); x.add_argument("--stopped", action="store_true"); x.add_argument("--reason", required=True)
    x = sub.add_parser("search"); x.add_argument("query"); x.add_argument("--initiative")
    for name in ["get", "owners"]:
        x = sub.add_parser(name); x.add_argument("path"); x.add_argument("--initiative")
    x = sub.add_parser("export"); x.add_argument("--out", required=True)
    x = sub.add_parser("schemas"); x.add_argument("--out", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        c = args.command
        if c == "doctor":
            result = doctor(args.repo, args.require_codex)
        elif c == "schemas":
            for name, model in CONTRACTS.items():
                write_json(Path(args.out) / (name + ".schema.json"), model.model_json_schema())
            result = {"schemas": list(CONTRACTS), "directory": args.out}
        else:
            if not args.control:
                raise OrchiError("CONTROL_REQUIRED", "Specify --control before the command")
            if c == "setup":
                e = Engine.setup(args.control, args.repo, read_json(args.policy)); result = e.next()
            else:
                e = Engine(args.control)
                if c == "status": result = e.state()
                elif c == "next": result = e.next()
                elif c == "begin": result = e.begin(read_json(args.file))
                elif c == "plan": result = e.plan(read_json(args.file))
                elif c == "roadmap": result = e.propose_roadmap(read_json(args.file), args.reason)
                elif c == "amend": result = e.amend(read_json(args.file), args.reason)
                elif c == "apply-decision": result = e.approve(read_json(args.file))
                elif c == "gate": result = (e.state().get("pending") or {}).get("request")
                elif c == "refresh-gate": result = e.refresh_gate()
                elif c == "claim": result = e.claim(args.task)
                elif c == "activate": result = e.activate(args.ticket, read_json(args.file))
                elif c == "submit": result = e.submit(args.ticket, read_json(args.file))
                elif c == "release": result = e.release(args.ticket, args.stopped, args.reason)
                elif c == "retry": result = e.retry(args.task, args.reason)
                elif c == "run": result = run_ready(e, read_json(args.adapter))
                elif c == "review-request": result = e.review_request(args.scope)
                elif c == "review-record": result = e.record_review(read_json(args.file))
                elif c == "repair": result = e.repair()
                elif c == "checkpoint": result = e.checkpoint(read_json(args.file))
                elif c == "final-draft": result = e.final_draft()
                elif c == "finalize": result = e.finalize(read_json(args.file))
                elif c == "publication": result = e.publication()
                elif c == "record-publication": result = e.record_publication(args.commit)
                elif c == "pause": e.pause(args.reason); result = e.next()
                elif c == "resume-request": result = e.propose_resume(args.reason)
                elif c == "recover-operation": result = e.recover_operation(args.stopped, args.reason)
                elif c == "search": result = context.search(e.repo, e.state(), args.query, args.initiative)
                elif c == "get": result = context.get(e.repo, e.state(), args.path, args.initiative)
                elif c == "owners": result = context.owners(e.repo, e.state(), args.path, args.initiative)
                elif c == "export": result = e.export(args.out)
                else: raise OrchiError("UNKNOWN_COMMAND", c)
        if getattr(args, "out", None) and c in {"gate", "final-draft", "review-request"}:
            write_json(args.out, result)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
        return 3 if isinstance(result, dict) and result.get("status") in {"blocked", "BLOCKED"} else 0
    except (OrchiError, ValidationError, ValueError, OSError) as err:
        detail = err.errors(include_input=False) if isinstance(err, ValidationError) else str(err)
        print(json.dumps({"ok": False, "code": getattr(err, "code", "INVALID_CONTRACT" if isinstance(err, ValidationError) else "INPUT_ERROR"), "message": detail}, ensure_ascii=False, default=str))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
