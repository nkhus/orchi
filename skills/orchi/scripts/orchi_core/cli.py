"""One JSON CLI for the skills and operator; never parse human text for workflow state."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from pydantic import ValidationError
from . import context, retrieval, graph, intent, ontology, views, authoring
from .repository import Repository
from .diagnostics import doctor
from .common import OrchiError, read_json, write_json, safe_text, require
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
        if name == "begin": x.add_argument("--intent", required=True, help="Directory containing exact Intent documents and manifest.json")
        if name == "plan": x.add_argument("--design", required=True, help="Exact Epic Design Markdown referenced by the plan hash")
    for name in ["roadmap", "amend", "revise-intent"]:
        x = sub.add_parser(name); x.add_argument("--file", required=True); x.add_argument("--reason", required=True)
        if name == "amend": x.add_argument("--design", required=True)
        else: x.add_argument("--evidence", action="append", required=name == "revise-intent", help="Exact check/source reference or an explicit operator decision; repeatable")
        if name == "revise-intent": x.add_argument("--intent", required=True)
    x = sub.add_parser("intent-build", help="Build the manifest from target Markdown metadata")
    x.add_argument("--directory", required=True); x.add_argument("--initiative", required=True)
    x.add_argument("--revision", type=int, default=1); x.add_argument("--resolutions", help="JSON mapping of removed requirement IDs to accepted resolution reasons")
    x = sub.add_parser("stop-epic", help="Propose an approved return to the last closed epic boundary")
    x.add_argument("--stopped", action="store_true"); x.add_argument("--reason", required=True)
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
    for name in ["search", "get", "owners", "index", "stat", "related", "map", "lint", "coverage"]:
        x = sub.add_parser(name, help="Retrieve or inspect the resolved knowledge scope")
        x.add_argument("--initiative", help="Explicit initiative scope; requires a controller")
        x.add_argument("--repo", help="Read canonical documentation without controller setup")
        x.add_argument("--ref", help="Canonical ref for --repo (default: refs/heads/main)")
        x.add_argument("--view", choices=["current", "target", "all"], default="current")
        if name == "search":
            x.add_argument("query", help="Plain text terms, not raw FTS syntax")
            x.add_argument("-k", "--limit", type=int, default=8, help="Maximum section hits (1-100)")
            x.add_argument("--format", choices=["json", "text"], default="json")
            x.add_argument("--kind", choices=sorted(ontology.KINDS)); x.add_argument("--area")
            x.add_argument("--related-limit", type=int, default=8); x.add_argument("--relation", choices=sorted(graph.RELATIONS))
        elif name in {"get", "owners", "related"}:
            x.add_argument("path")
            if name == "get":
                x.add_argument("--content-hash", help="Require the SHA256 returned by search")
            elif name == "related":
                x.add_argument("--relation", choices=sorted(graph.RELATIONS)); x.add_argument("--depth", type=int, default=1)
                x.add_argument("--limit", type=int, default=40); x.add_argument("--direction", choices=["in", "out", "both"], default="both")
        elif name == "map":
            x.add_argument("--out"); x.add_argument("--format", choices=["html", "json"], default="html")
        elif name == "index":
            x.add_argument("--force", action="store_true", help="Rebuild even when the cached snapshot matches")
    for name in ("sync-status", "overview"):
        sub.add_parser(name)
    x = sub.add_parser("inspect", help="Show the exact pending human decision")
    x.add_argument("--format", choices=["text", "json"], default="text")
    for name in ("start", "sync-check", "sync-review"):
        x = sub.add_parser(name); x.add_argument("--file", required=True)
    x = sub.add_parser("brief-expand"); x.add_argument("--file", required=True); x.add_argument("--out", required=True)
    x = sub.add_parser("plan-preflight"); x.add_argument("--file", required=True); x.add_argument("--design", required=True)
    x = sub.add_parser("sync-draft"); x.add_argument("--out")
    for name in ("sync-discard", "withdraw-gate"):
        x = sub.add_parser(name); x.add_argument("--reason", required=True)
    x = sub.add_parser("integrate"); x.add_argument("--ticket", required=True)
    x = sub.add_parser("scope-acquire"); x.add_argument("--ticket", required=True); x.add_argument("--file", required=True)
    x = sub.add_parser("ticket-read"); x.add_argument("--ticket", required=True); x.add_argument("path")
    x.add_argument("--view", choices=["code", "current", "target", "epic-design"], default="code")
    x.add_argument("--content-hash"); x.add_argument("--start-line", type=int, default=1); x.add_argument("--end-line", type=int)
    x.add_argument("--consistency", choices=["fixed", "snapshot"], default="fixed")
    x = sub.add_parser("handoff"); x.add_argument("--ticket", required=True); x.add_argument("--stopped", action="store_true")
    x.add_argument("--reason", required=True); x.add_argument("--executor", choices=["human", "agent", "pair"], default="human")
    x = sub.add_parser("import-candidate"); x.add_argument("--ticket", required=True); x.add_argument("--commit", required=True)
    x.add_argument("--base", required=True); x.add_argument("--reason", required=True)
    x = sub.add_parser("amend-tasks"); x.add_argument("--file", required=True); x.add_argument("--design", required=True)
    x.add_argument("--affected", action="append", required=True); x.add_argument("--reason", required=True)
    x = sub.add_parser("views"); x.add_argument("--out", required=True); x.add_argument("--view", choices=["current", "target", "all"], default="all")
    x = sub.add_parser("export"); x.add_argument("--out", required=True)
    x = sub.add_parser("schemas"); x.add_argument("--out", required=True)
    return p


def knowledge_command(args: argparse.Namespace) -> dict:
    if args.repo:
        if args.control or args.initiative:
            raise OrchiError("AMBIGUOUS_SCOPE", "Use either --repo for standalone Core or --control with optional --initiative; unset ORCHI_CONTROL for standalone reads")
        repo = Repository(args.repo)
        state = {"policy": {"canonical_ref": args.ref or "refs/heads/main"}}
        cache = Path(repo.git("rev-parse", "--absolute-git-dir").decode().strip()) / "orchi-retrieval"
    else:
        if args.ref:
            raise OrchiError("AMBIGUOUS_SCOPE", "--ref only applies with --repo; controller policy fixes its canonical ref")
        if not args.control:
            raise OrchiError("CONTROL_REQUIRED", "Specify --control before the command or use --repo for standalone Core")
        engine = Engine(args.control)
        repo, state = engine.repo, engine.state()
        cache = engine.store.root / "cache" / "retrieval"
    if args.command == "search":
        return context.search(repo, state, args.query, args.initiative, view=args.view, kind=args.kind, area=args.area,
                              related_limit=args.related_limit, relation=args.relation, limit=args.limit, cache_root=cache)
    if args.command == "get":
        return context.get(repo, state, args.path, args.initiative, args.content_hash, view=args.view)
    if args.command == "owners":
        return context.owners(repo, state, args.path, args.initiative, view=args.view)
    if args.command == "coverage":
        require(bool(args.initiative), "INITIATIVE_SCOPE", "Coverage requires --initiative")
        return graph.coverage(repo, state, args.initiative)
    if args.command == "lint":
        result = context.lint(repo, state, args.initiative, args.view)
        result["status"] = "ready" if result["ok"] else "blocked"
        return result
    if args.command in {"related", "map"}:
        projection = graph.project(repo, state, context.retrieval_snapshot(repo, state, args.initiative, args.view))
        if args.command == "related":
            return graph.related(projection, args.path, args.relation, depth=args.depth, limit=args.limit, direction=args.direction)
        if args.format == "json" and not args.out:
            return projection
        out = Path(args.out) if args.out else cache.parent / "maps" / ((args.initiative or "canonical") + "-" + args.view + ".html")
        git_dir = Path(repo.git("rev-parse", "--absolute-git-dir").decode().strip())
        require(not out.resolve().is_relative_to(repo.root) or out.resolve().is_relative_to(git_dir),
                "DERIVED_OUTPUT_BOUNDARY", "Write generated maps outside the tracked repository (or inside its Git metadata directory)")
        if args.format == "json":
            require(not any(p.is_symlink() for p in [out, *out.parents]), "UNSAFE_PATH", str(out))
            write_json(out, projection)
            return {"path": str(out), "fingerprint": projection["fingerprint"], "derived": True}
        return graph.write_map(projection, out)
    return context.index(repo, state, args.initiative, view=args.view, cache_root=cache, force=getattr(args, "force", False))


def read_design(file: str) -> str:
    p = Path(file)
    require(not any(part.is_symlink() for part in [p, *p.parents]), "UNSAFE_PATH", file)
    return safe_text(p.read_bytes(), file)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        c = args.command
        if c == "doctor":
            result = doctor(args.repo, args.require_codex)
        elif c == "intent-build":
            result = intent.build_directory(args.directory, args.initiative, args.revision,
                                             read_json(args.resolutions) if args.resolutions else None)
        elif c in {"search", "get", "owners", "index", "stat", "related", "map", "lint", "coverage"}:
            result = knowledge_command(args)
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
                elif c == "overview": result = views.overview(e)
                elif c == "inspect": result = views.gate(e)
                elif c == "start": result = e.begin_brief(read_json(args.file))
                elif c == "brief-expand":
                    out = Path(args.out).absolute()
                    require(not out.exists() and not any(p.is_symlink() for p in [out, *out.parents]), "OUTPUT_EXISTS", "Use a new non-symlinked authoring directory")
                    require(not out.resolve().is_relative_to(e.repo.root), "AUTHORING_BOUNDARY", "Create drafts outside the canonical project worktree")
                    spec, bundle, plan, design = authoring.expand(read_json(args.file), e.repo.resolve(e.policy.canonical_ref))
                    write_json(out / "initiative.json", spec); write_json(out / "plan.json", plan)
                    write_json(out / "intent/manifest.json", bundle["manifest"])
                    for name, text in bundle["documents"].items():
                        target = out / "intent" / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding="utf-8")
                    (out / "design.md").write_text(design, encoding="utf-8")
                    result = {"path": str(out), "accepted": False}
                elif c == "plan-preflight": result = e.plan_preflight(read_json(args.file), read_design(args.design))
                elif c == "sync-status": result = e.sync_status()
                elif c == "sync-draft": result = e.sync_draft()
                elif c == "sync-check": result = e.synchronize(read_json(args.file))
                elif c == "sync-review": result = e.sync_review(read_json(args.file))
                elif c == "sync-discard":
                    from .synchronization import discard
                    result = discard(e, args.reason)
                elif c == "withdraw-gate": result = e.withdraw_gate(args.reason)
                elif c == "integrate": result = e.integrate(args.ticket)
                elif c == "scope-acquire": result = e.acquire_scope(args.ticket, read_json(args.file))
                elif c == "ticket-read": result = e.ticket_read(args.ticket, args.path, view=args.view, content_hash=args.content_hash,
                                                                start_line=args.start_line, end_line=args.end_line, consistency=args.consistency)
                elif c == "handoff": result = e.handoff(args.ticket, args.stopped, args.reason, args.executor)
                elif c == "import-candidate": result = e.import_candidate(args.ticket, args.commit, args.base, args.reason)
                elif c == "amend-tasks": result = e.amend_tasks(read_json(args.file), read_design(args.design), args.affected, args.reason)
                elif c == "views": result = views.materialize(e, args.out, args.view)
                elif c == "next": result = e.next()
                elif c == "begin": result = e.begin(read_json(args.file), intent.load(args.intent))
                elif c == "plan": result = e.plan(read_json(args.file), read_design(args.design))
                elif c == "roadmap": result = e.propose_roadmap(read_json(args.file), args.reason, args.evidence)
                elif c == "revise-intent": result = e.revise_intent(read_json(args.file), intent.load(args.intent), args.reason, args.evidence)
                elif c == "stop-epic": result = e.stop_epic(args.stopped, args.reason)
                elif c == "amend": result = e.amend(read_json(args.file), args.reason, read_design(args.design))
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
                elif c == "export": result = e.export(args.out)
                else: raise OrchiError("UNKNOWN_COMMAND", c)
        if getattr(args, "out", None) and c in {"gate", "final-draft", "review-request", "sync-draft"}:
            write_json(args.out, result)
        if c == "inspect" and args.format == "text":
            print(views.render_gate(result))
        elif c == "search" and args.format == "text":
            print(retrieval.format_text(result))
        else:
            print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
        return 3 if isinstance(result, dict) and result.get("status") in {"blocked", "BLOCKED"} else 0
    except (OrchiError, ValidationError, ValueError, OSError) as err:
        detail = err.errors(include_input=False) if isinstance(err, ValidationError) else str(err)
        print(json.dumps({"ok": False, "code": getattr(err, "code", "INVALID_CONTRACT" if isinstance(err, ValidationError) else "INPUT_ERROR"), "message": detail}, ensure_ascii=False, default=str))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
