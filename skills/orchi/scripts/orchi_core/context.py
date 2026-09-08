"""Sparse knowledge overlay, exact context materialization, deterministic task packets."""
from __future__ import annotations
import fnmatch
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from .common import canonical, digest, sha, require, path, safe_text, secret_path, OrchiError, integration_base
from .repository import Repository
from . import retrieval, intent, ontology
from .ontology import frontmatter, artifact_paths



def core(repo: Repository, commit: str, *, diagnostic: bool = False) -> dict[str, dict]:
    result = {}
    for p in sorted(repo.files(commit)):
        if not p.startswith("docs/") or not p.endswith(".md") or secret_path(p):
            continue
        text = safe_text(repo.read(commit, p), p)
        try:
            fm = frontmatter(text)
        except OrchiError:
            if not diagnostic:
                raise
            fm = {}
        if not diagnostic and (fm.get("lifecycle") in {"history", "proposed"} or fm.get("status") in {"superseded", "rejected", "archived", "draft"}):
            continue
        result[p] = {"target": p, "content": text, "source_path": p, "source_commit": commit,
                     "content_hash": sha(text.encode()), "role": "current", "view": "current", "layer": "canonical",
                     "kind": fm.get("kind"), "area": fm.get("area"), "artifacts": artifact_paths(fm)}
    return result


def effective(repo: Repository, s: dict, initiative_id: str | None = None, view: str = "current", *, diagnostic: bool = False) -> dict[str, dict]:
    require(view in {"current", "target", "all"}, "INVALID_VIEW", view)
    if initiative_id is None:
        require(view != "target", "TARGET_SCOPE_REQUIRED", "Target requires an explicitly selected initiative")
        return core(repo, repo.resolve(s["policy"]["canonical_ref"]), diagnostic=diagnostic)
    require(s.get("spec") is not None and initiative_id == s["spec"]["id"], "INITIATIVE_SCOPE", "Explicit initiative id does not match controller")
    result = {}
    if view in {"current", "all"}:
        result = core(repo, integration_base(s), diagnostic=diagnostic)
        for target, record in sorted(s["knowledge"].items()):
            # Mask even retired/stale records: never fall back to obsolete canonical facts.
            result.pop(target, None)
            fresh = repo.hashes(s["knowledge_head"], list(record["artifact_hashes"])) == record["artifact_hashes"]
            if record["action"] == "retire":
                result[target] = {**record, "role": "current", "view": "current", "layer": "retired", "stale": not fresh, "content": None}
            else:
                text = safe_text(repo.read(record["source_commit"], record["source_path"]), target)
                require(sha(text.encode()) == sha(record["content"].encode()), "WORKING_CONTENT_CHANGED", target)
                fm = frontmatter(text)
                result[target] = {**record, "role": "current", "view": "current", "layer": "working", "stale": not fresh,
                                  "content": text, "content_hash": sha(text.encode()), "kind": fm.get("kind"), "area": fm.get("area"),
                                  "initiative_id": initiative_id, "knowledge_revision": s["knowledge_revision"],
                                  "artifacts": list(record["artifact_hashes"])}
    if view in {"target", "all"}:
        bundle = intent.accepted(repo, s)
        result.update(intent.records(bundle, s["intent"]["commit"], "initiatives/active/" + initiative_id + "/"))
    return result


def get(repo: Repository, s: dict, target: str, initiative_id: str | None = None,
        content_hash: str | None = None, view: str = "current") -> dict:
    requested = target
    if target.startswith("req-") and "/" not in target:
        require(initiative_id is not None and view in {"target", "all"}, "TARGET_SCOPE_REQUIRED", target)
        require((s.get("spec") or {}).get("id") == initiative_id, "INITIATIVE_SCOPE", initiative_id)
        target = intent.accepted(repo, s)["manifest"]["requirements"].get(target, target)
    document, separator, anchor = target.partition("#")
    record = effective(repo, s, initiative_id, view).get(path(document))
    require(record is not None, "MISSING_KNOWLEDGE", target)
    require(not record.get("stale"), "STALE_WORKING_KNOWLEDGE", target)
    require(record["layer"] != "retired", "RETIRED_KNOWLEDGE", target)
    if separator:
        require(anchor in ontology.anchors(record["content"])[0], "MISSING_KNOWLEDGE_ANCHOR", target)
    if content_hash is not None:
        require(re.fullmatch(r"[0-9a-f]{64}", content_hash) is not None, "INVALID_CONTENT_HASH", "Expected a SHA256 digest")
        require(record["content_hash"] == content_hash, "KNOWLEDGE_CHANGED", "Search again before reading changed knowledge: " + target)
    # Anchors identify an exact document section; the read returns the whole exact source, not a cached snippet.
    return {**record, "requested_target": requested, "anchor": anchor or None}


def retrieval_snapshot(repo: Repository, s: dict, initiative_id: str | None = None, view: str = "current") -> retrieval.Snapshot:
    """Resolve authority before any projection, including freshness on every request."""
    if initiative_id is None:
        canonical_commit = repo.resolve(s["policy"]["canonical_ref"])
        frozen = {**s, "policy": {**s["policy"], "canonical_ref": canonical_commit}}
    else:
        require(s.get("spec") is not None and initiative_id == s["spec"]["id"],
                "INITIATIVE_SCOPE", "Explicit initiative id does not match controller")
        canonical_commit, frozen = integration_base(s), s
    records, diagnostics = {}, []
    for target, record in effective(repo, frozen, initiative_id, view).items():
        if record.get("stale"):
            diagnostics.append({"target": target, "code": "STALE_WORKING_KNOWLEDGE"})
        elif record["layer"] != "retired":
            records[target] = record
    identity = {"repository": str(repo.root), "kind": "initiative" if initiative_id else "canonical",
                "scope": initiative_id or "canonical", "initiative_id": initiative_id, "view": view,
                "canonical_ref": s["policy"]["canonical_ref"], "canonical_commit": canonical_commit,
                "ontology_signature": sha(Path(ontology.__file__).read_bytes())}
    if initiative_id is not None:
        identity.update(knowledge_head=s["knowledge_head"], knowledge_revision=s["knowledge_revision"],
                        knowledge_manifest_digest=digest(s["knowledge"]), intent_digest=s.get("intent", {}).get("digest"))
    return retrieval.Snapshot(records, identity, diagnostics)


def search(repo: Repository, s: dict, query: str, initiative_id: str | None = None, *,
           view: str = "current", kind: str | None = None, area: str | None = None,
           related_limit: int = 8, relation: str | None = None,
           limit: int = 8, cache_root: Path | None = None) -> dict:
    retrieval.query_terms(query)
    require(isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= retrieval.MAX_RESULTS,
            "INVALID_LIMIT", "limit must be between 1 and 100")
    require(kind is None or kind in ontology.KINDS, "INVALID_KIND", str(kind))
    require(isinstance(related_limit, int) and not isinstance(related_limit, bool) and 0 <= related_limit <= 100,
            "INVALID_LIMIT", "related_limit must be between 0 and 100")
    from . import graph
    require(relation is None or relation in graph.RELATIONS, "INVALID_RELATION", str(relation))
    snapshot = retrieval_snapshot(repo, s, initiative_id, view)
    selected = snapshot
    if kind is not None or area is not None:
        selected = retrieval.Snapshot({p: r for p, r in snapshot.records.items()
            if (kind is None or r.get("kind") == kind) and (area is None or r.get("area") == area)},
            {**snapshot.identity, "filters": {"kind": kind, "area": area}}, snapshot.diagnostics)
    result = retrieval.search(selected, query, limit, cache_root)
    result["primary_matches"] = result["results"]
    result["related_context"] = []
    if related_limit and result["primary_matches"]:
        projection = graph.project(repo, s, snapshot)
        result["related_context"] = graph.related_context(projection, result["primary_matches"], related_limit, relation)
        result["graph_fingerprint"] = projection["fingerprint"]
    return result


def index(repo: Repository, s: dict, initiative_id: str | None = None, *, view: str = "current",
          cache_root: Path | None = None, force: bool = False) -> dict:
    return retrieval.index(retrieval_snapshot(repo, s, initiative_id, view), cache_root, force)


def owners(repo: Repository, s: dict, artifact: str, initiative_id: str | None = None, view: str = "current") -> dict:
    path(artifact)
    hits, diagnostics = [], []
    for p, rec in effective(repo, s, initiative_id, view).items():
        patterns = rec.get("artifacts", list(rec.get("artifact_hashes", {})))
        if not any(fnmatch.fnmatchcase(artifact, pattern) for pattern in patterns):
            continue
        if rec.get("stale"):
            diagnostics.append({"target": p, "code": "STALE_WORKING_KNOWLEDGE"})
        elif rec["layer"] != "retired":
            hits.append({"target": p, "role": rec["role"], "layer": rec["layer"], "kind": rec.get("kind"),
                         "source_commit": rec["source_commit"], "content_hash": rec["content_hash"]})
    return {"scope": initiative_id or "canonical", "view": view, "artifact": artifact, "owners": hits, "diagnostics": diagnostics}


def lint(repo: Repository, s: dict, initiative_id: str | None = None, view: str = "current") -> dict:
    # Diagnostic resolution preserves masked lifecycle-marked Core and malformed
    # metadata for linting only. Normal retrieval never promotes them as authority.
    commit = s["knowledge_head"] if initiative_id else repo.resolve(s["policy"]["canonical_ref"])
    frozen = s if initiative_id else {**s, "policy": {**s["policy"], "canonical_ref": commit}}
    requested = effective(repo, frozen, initiative_id, view, diagnostic=True)
    validation = effective(repo, frozen, initiative_id, "all", diagnostic=True) if initiative_id and s.get("intent") else requested
    valid = {p: r for p, r in validation.items() if r.get("content") is not None and not r.get("stale")}
    selected = {p for p, r in requested.items() if r.get("content") is not None and not r.get("stale")}
    requirements = intent.accepted(repo, s)["manifest"]["requirements"] if initiative_id and s.get("intent") else {}
    evidence = [e["id"] for e in s.get("evidence", [])]
    report = ontology.lint(valid, repo.files(commit), requirements=requirements, evidence=evidence,
                           lookup=lambda p: safe_text(repo.read(commit, p), p))
    report["diagnostics"] = [d for d in report["diagnostics"] if d["target"] in selected or
        any(p.startswith(d["target"] + "/") for p in selected)]
    report["diagnostics"].extend({"target": p, "code": "STALE_WORKING_KNOWLEDGE", "severity": "error",
                                  "message": "Obsolete Core remains masked"} for p, r in requested.items() if r.get("stale"))
    report["diagnostics"].sort(key=lambda d: (d["target"], d["severity"], d["code"], d["message"]))
    report.update(scope=initiative_id or "canonical", view=view, documents=len(selected),
                  ok=not any(d["severity"] == "error" for d in report["diagnostics"]))
    return report


def task_sources(repo: Repository, s: dict, task: dict, *, preflight: bool = False) -> tuple[list[dict], dict]:
    records, seen, reads = [], set(), set(task["read_paths"])
    declared = list(task["context"])
    epic = next(e for e in s["spec"]["epics"] if e["id"] == s["active"]["plan"]["epic_id"])
    manifest = intent.accepted(repo, s)["manifest"]
    for ref in [*(manifest["requirements"][r] for r in epic["contributes_to"] if r in manifest["requirements"]), *epic["realizes"]]:
        declared.append({"kind": "knowledge", "view": "target", "path": ref, "reason": "Accepted target selected by the active epic roadmap"})
    # Before-image for each existing edit and the relevant repository instructions are mandatory.
    files = repo.files(s["head"])
    for edit in task["edits"]:
        if edit["path"] in files:
            declared.append({"kind": "code", "path": edit["path"], "reason": "Before-image of assigned write"})
        reads.add(edit["path"])
        parent = PurePosixPath(edit["path"]).parent
        for d in [PurePosixPath("."), *reversed(list(parent.parents)[:-1]), parent]:
            for name in ("AGENTS.override.md", "AGENTS.md"):
                p = str(d / name)
                if p in files:
                    declared.append({"kind": "code", "path": p, "reason": "Applicable repository instructions; stop on conflicts"})
                    reads.add(p)
                    break
    for p in task["read_paths"]:
        declared.append({"kind": "code", "path": p, "reason": "Explicit read assumption"})
    for src in declared:
        p = path(src["path"])
        require(not secret_path(p), "SECRET_PATH", p)
        if src["kind"] == "knowledge":
            rec = get(repo, s, p, s["spec"]["id"], view=src["view"])
            key = (src["view"], rec["target"])
            # Ownership and ontology relations are navigation/impact metadata, not read locks.
        else:
            if src["kind"] == "dependency":
                dep = s["active"]["tasks"][src["producer"]]
                if dep["status"] != "integrated" and preflight:
                    records.append({"target": p, "source_path": p, "source_commit": None,
                                    "content_hash": None, "role": "implementation", "layer": "dependency",
                                    "delivery": "deferred", "reason": src["reason"], "contract": src["contract"]})
                    continue
                require(dep["status"] == "integrated", "DEPENDENCY_NOT_INTEGRATED", src["producer"])
            if preflight and p not in files:
                records.append({"target": p, "source_path": p, "source_commit": None,
                                "content_hash": None, "role": "implementation", "layer": "implementation",
                                "delivery": "deferred", "reason": src["reason"]})
                continue
            text = safe_text(repo.read(s["head"], p), p,
                             8_000_000 if src.get("delivery") == "on-demand" else 512_000)
            rec = {"target": p, "content": text, "content_hash": sha(text.encode()),
                   "source_path": p, "source_commit": s["head"], "role": "implementation", "layer": "implementation"}
            key = ("code", p)
            if src.get("consistency", "fixed") == "fixed" or src["kind"] == "dependency":
                reads.add(p)
        if key not in seen:
            record = {**rec, "reason": src["reason"], "contract": src.get("contract", ""),
                      "delivery": src.get("delivery", "inline"), "consistency": src.get("consistency", "fixed")}
            if record["delivery"] == "on-demand":
                record.pop("content", None)
            records.append(record)
            seen.add(key)
    design = s["active"]["design_source"]
    text = design["preview_content"] if preflight else safe_text(repo.read(design["source_commit"], design["source_path"]), design["source_path"])
    require(sha(text.encode()) == design["content_hash"], "DESIGN_CONTENT_CHANGED", design["source_path"])
    records.append({**{k: v for k, v in design.items() if k != "preview_content"}, "content": text, "role": "epic-design", "layer": "epic-design",
                    "reason": "Exact accepted just-in-time epic implementation design"})
    return records, repo.hashes(s["head"], list(reads))


def packet(repo: Repository, s: dict, task: dict, *, preflight: bool = False) -> dict:
    sources, read_hashes = task_sources(repo, s, task, preflight=preflight)
    body = {"format": "orchi-task-packet", "initiative_id": s["spec"]["id"], "epic_id": s["active"]["plan"]["epic_id"],
            "plan_digest": s["active"]["digest"], "canonical_baseline": s["baseline"], "integration_base": integration_base(s), "start_commit": s["head"],
            "knowledge_revision": s["knowledge_revision"], "knowledge_head": s["knowledge_head"], "initiative_outcome": s["spec"]["outcome"],
            "initiative_intent": s["spec"]["intent"], "initiative_constraints": [], "epic_design": s["active"]["plan"]["shared_design"],
            "task": task, "sources": sources, "read_hashes": read_hashes,
            "snapshot_reads": repo.hashes(s["head"], [r["source_path"] for r in sources
                if r.get("consistency") == "snapshot" and r["role"] == "implementation"]),
            "preflight": preflight,
            "dependencies": {p: s["active"]["tasks"][p].get("commit") for p in task["depends_on"]},
            "instructions": "Use this exact checkout. Core docs describe the accepted integration base; working replacements are initiative-only facts. "
                            "Working knowledge describes the last closed epic, not unfinished work in the active epic; apply the approved delta and actual dependency outputs explicitly. "
                            "Target sources describe accepted requirements and architecture, not implemented state. Escalate material target changes; never edit accepted Intent. "
                            "Follow the task design and delegated choices. Readiness precedes writes. Use ticket-scoped reads for on-demand sources. Do not commit, merge, edit docs/ or proposal definitions. "
                            "Report new read dependencies and material deviations. Material design changes require escalation; bounded local choices and investigation are allowed. Documentation proposals and observations are evidence, never Current authority."}
    body["fingerprint"] = digest(body)
    rendered = render_packet(body)
    require(len(rendered.encode()) <= s["policy"]["max_packet_bytes"], "CONTEXT_TOO_LARGE", "Required packet exceeds hard byte budget; split task/select narrower exact sources")
    return body


def render_packet(p: dict) -> str:
    blocks = ["# Task " + p["task"]["id"], p["instructions"],
              "## Identity\n" + json.dumps({k: p[k] for k in ("initiative_id", "epic_id", "canonical_baseline", "integration_base", "knowledge_head", "start_commit", "plan_digest", "fingerprint")}, indent=2),
              "## Initiative\n" + p["initiative_outcome"] + "\n" + "\n".join(p["initiative_constraints"]),
              "## Approved epic design\n" + p["epic_design"],
              "## Complete task design\n```json\n" + json.dumps(p["task"], ensure_ascii=False, indent=2) + "\n```"]
    if p.get("previous_candidate"):
        blocks.append("## Previous rejected candidate\n" + p["previous_candidate"] + "\n" + p["retry_instruction"])
    if p.get("handoff"):
        blocks.append("## Preserved handoff (unverified)\n" + json.dumps(p["handoff"], ensure_ascii=False, indent=2))
    if p.get("repair_findings"):
        blocks.append("## Targeted repair findings\n" + json.dumps(p["repair_findings"], ensure_ascii=False, indent=2))
    for src in p["sources"]:
        header = ("## Source: " + src["target"] + "\nRole: " + src["role"] + " | Layer: " + src["layer"] +
                  "\nCommit: " + str(src["source_commit"]) + "\nSource path: " + src["source_path"] +
                  "\nSHA256: " + str(src["content_hash"]) + "\nReason: " + src["reason"])
        if "content" in src:
            blocks.append(header + "\n\n<source-data>\n" + src["content"] + "\n</source-data>")
        else:
            blocks.append(header + "\nDelivery: " + src.get("delivery", "on-demand") +
                          "\nRead this exact source through ticket-read; never substitute the latest branch.")
    return "\n\n".join(blocks) + "\n"


def validate_final_docs(repo: Repository, commit: str, strict_paths=()) -> None:
    records = core(repo, commit)
    # Do not let authority markers hide a final document from validation.
    for p in repo.files(commit):
        if p.startswith("docs/") and p.endswith(".md") and not secret_path(p):
            text = safe_text(repo.read(commit, p), p)
            fm = frontmatter(text)
            require(not (set(fm) & ontology.AUTHORITY_FIELDS), "FINAL_DOC_AUTHORITY", p)
            require(fm.get("kind") not in {"requirements", "architecture"}, "TARGET_AS_CORE", "Final Core uses component/reference/decision kinds, not initiative target kinds: " + p)
    report = ontology.lint(records, repo.files(commit), strict_paths=strict_paths,
                           lookup=lambda p: safe_text(repo.read(commit, p), p))
    require(report["ok"], "FINAL_DOC_ONTOLOGY", json.dumps([d for d in report["diagnostics"] if d["severity"] == "error"]))
