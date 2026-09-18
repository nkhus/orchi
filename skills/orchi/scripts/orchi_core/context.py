"""Sparse knowledge overlay, exact context materialization, deterministic task packets."""
from __future__ import annotations
import fnmatch
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import yaml
from .common import canonical, digest, sha, require, path, safe_text, secret_path, OrchiError
from .repository import Repository
from . import retrieval


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    require(0 < end < 16384, "INVALID_FRONTMATTER", "Missing/oversized frontmatter")
    raw = text[4:end]
    try:
        require(not any(isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)) for t in yaml.scan(raw)),
                "INVALID_FRONTMATTER", "YAML aliases are not accepted")
        fm = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise OrchiError("INVALID_FRONTMATTER", "Invalid YAML") from e
    require(isinstance(fm, dict), "INVALID_FRONTMATTER", "Expected mapping")
    return fm


def artifact_paths(fm: dict) -> list[str]:
    value = fm.get("artifacts", [])
    if isinstance(value, dict):
        value = [x for group in value.values() if isinstance(group, list) for x in group]
    if not isinstance(value, list):
        return []
    return [v if isinstance(v, str) else v["path"] for v in value if isinstance(v, str) or isinstance(v, dict) and isinstance(v.get("path"), str)]


def core(repo: Repository, commit: str) -> dict[str, dict]:
    result = {}
    for p in sorted(repo.files(commit)):
        if not p.startswith("docs/") or not p.endswith(".md") or secret_path(p):
            continue
        text = safe_text(repo.read(commit, p), p)
        fm = frontmatter(text)
        if fm.get("lifecycle") in {"history", "proposed"} or fm.get("status") in {"superseded", "rejected", "archived", "draft"}:
            continue
        result[p] = {"target": p, "content": text, "source_path": p, "source_commit": commit,
                     "content_hash": sha(text.encode()), "layer": "canonical", "artifacts": artifact_paths(fm)}
    return result


def effective(repo: Repository, s: dict, initiative_id: str | None = None) -> dict[str, dict]:
    if initiative_id is None:
        return core(repo, repo.resolve(s["policy"]["canonical_ref"]))
    require(s.get("spec") is not None and initiative_id == s["spec"]["id"], "INITIATIVE_SCOPE", "Explicit initiative id does not match controller")
    result = core(repo, s["baseline"])
    for target, record in sorted(s["knowledge"].items()):
        # Mask even retired/stale records: never fall back to superseded canonical semantics.
        result.pop(target, None)
        fresh = repo.hashes(s["knowledge_head"], list(record["artifact_hashes"])) == record["artifact_hashes"]
        if record["action"] == "retire":
            result[target] = {**record, "layer": "retired", "stale": not fresh, "content": None}
        else:
            result[target] = {**record, "layer": "working", "stale": not fresh,
                              "content_hash": sha(record["content"].encode()), "artifacts": list(record["artifact_hashes"])}
    return result


def get(repo: Repository, s: dict, target: str, initiative_id: str | None = None,
        content_hash: str | None = None) -> dict:
    record = effective(repo, s, initiative_id).get(path(target))
    require(record is not None, "MISSING_KNOWLEDGE", target)
    require(not record.get("stale"), "STALE_WORKING_KNOWLEDGE", target)
    require(record["layer"] != "retired", "RETIRED_KNOWLEDGE", target)
    if content_hash is not None:
        require(re.fullmatch(r"[0-9a-f]{64}", content_hash) is not None, "INVALID_CONTENT_HASH", "Expected a SHA256 digest")
        require(record["content_hash"] == content_hash, "KNOWLEDGE_CHANGED", "Search again before reading changed knowledge: " + target)
    return record


def retrieval_snapshot(repo: Repository, s: dict, initiative_id: str | None = None) -> retrieval.Snapshot:
    """Resolve authority before indexing, including freshness checks on every request."""
    if initiative_id is None:
        canonical_commit = repo.resolve(s["policy"]["canonical_ref"])
        # Resolve a mutable ref once; all reads and identity describe the same snapshot.
        frozen = {**s, "policy": {**s["policy"], "canonical_ref": canonical_commit}}
    else:
        require(s.get("spec") is not None and initiative_id == s["spec"]["id"],
                "INITIATIVE_SCOPE", "Explicit initiative id does not match controller")
        canonical_commit, frozen = s["baseline"], s
    records, diagnostics = {}, []
    for target, record in effective(repo, frozen, initiative_id).items():
        if record.get("stale"):
            diagnostics.append({"target": target, "code": "STALE_WORKING_KNOWLEDGE"})
        elif record["layer"] != "retired":
            records[target] = record
    identity = {"repository": str(repo.root), "kind": "initiative" if initiative_id else "canonical",
                "scope": initiative_id or "canonical", "initiative_id": initiative_id,
                "canonical_ref": s["policy"]["canonical_ref"], "canonical_commit": canonical_commit}
    if initiative_id is not None:
        identity.update(knowledge_head=s["knowledge_head"], knowledge_revision=s["knowledge_revision"],
                        knowledge_manifest_digest=digest(s["knowledge"]))
    return retrieval.Snapshot(records, identity, diagnostics)


def search(repo: Repository, s: dict, query: str, initiative_id: str | None = None, *,
           limit: int = 8, cache_root: Path | None = None) -> dict:
    # Reject excessive input before reading the authority corpus.
    retrieval.query_terms(query)
    require(isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= retrieval.MAX_RESULTS,
            "INVALID_LIMIT", "limit must be between 1 and 100")
    return retrieval.search(retrieval_snapshot(repo, s, initiative_id), query, limit, cache_root)


def index(repo: Repository, s: dict, initiative_id: str | None = None, *,
          cache_root: Path | None = None, force: bool = False) -> dict:
    return retrieval.index(retrieval_snapshot(repo, s, initiative_id), cache_root, force)


def owners(repo: Repository, s: dict, artifact: str, initiative_id: str | None = None) -> dict:
    path(artifact)
    hits, diagnostics = [], []
    for p, rec in effective(repo, s, initiative_id).items():
        patterns = rec.get("artifacts", list(rec.get("artifact_hashes", {})))
        if not any(fnmatch.fnmatchcase(artifact, pattern) for pattern in patterns):
            continue
        if rec.get("stale"):
            diagnostics.append({"target": p, "code": "STALE_WORKING_KNOWLEDGE"})
        elif rec["layer"] != "retired":
            hits.append({"target": p, "layer": rec["layer"], "source_commit": rec["source_commit"]})
    return {"scope": initiative_id or "canonical", "artifact": artifact, "owners": hits, "diagnostics": diagnostics}


def task_sources(repo: Repository, s: dict, task: dict) -> tuple[list[dict], dict]:
    records, seen, reads = [], set(), set(task["read_paths"])
    declared = list(task["context"])
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
            rec = get(repo, s, p, s["spec"]["id"])
            key = ("knowledge", p)
            reads.update(rec.get("artifacts", []))
            # Patterns are useful for ownership, but task read reservations use exact expanded paths.
            expanded = set()
            for pattern in rec.get("artifacts", []):
                expanded.update(x for x in files if fnmatch.fnmatchcase(x, pattern))
            reads.difference_update(rec.get("artifacts", []))
            reads.update(expanded)
        else:
            if src["kind"] == "dependency":
                dep = s["active"]["tasks"][src["producer"]]
                require(dep["status"] == "integrated", "DEPENDENCY_NOT_INTEGRATED", src["producer"])
            text = safe_text(repo.read(s["head"], p), p)
            rec = {"target": p, "content": text, "content_hash": sha(text.encode()),
                   "source_path": p, "source_commit": s["head"], "layer": "implementation"}
            key = ("code", p)
            reads.add(p)
        if key not in seen:
            records.append({**rec, "reason": src["reason"], "contract": src.get("contract", "")})
            seen.add(key)
    return records, repo.hashes(s["head"], list(reads))


def packet(repo: Repository, s: dict, task: dict) -> dict:
    sources, read_hashes = task_sources(repo, s, task)
    body = {"format": "orchi-task-packet", "initiative_id": s["spec"]["id"], "epic_id": s["active"]["plan"]["epic_id"],
            "plan_digest": s["active"]["digest"], "canonical_baseline": s["baseline"], "start_commit": s["head"],
            "knowledge_revision": s["knowledge_revision"], "knowledge_head": s["knowledge_head"], "initiative_outcome": s["spec"]["outcome"],
            "initiative_constraints": s["spec"]["constraints"], "epic_design": s["active"]["plan"]["shared_design"],
            "task": task, "sources": sources, "read_hashes": read_hashes,
            "dependencies": {p: s["active"]["tasks"][p].get("commit") for p in task["depends_on"]},
            "instructions": "Use this exact checkout. Core docs remain canonical-baseline facts; working replacements are initiative-only facts. "
                            "Working knowledge describes the last closed epic, not unfinished work in the active epic; apply the approved delta and actual dependency outputs explicitly. "
                            "Follow the task design. Readiness precedes writes. Do not commit, merge, edit docs/ or proposal definitions. "
                            "Report new read dependencies and material deviations. A missing design decision requires escalation, not guessing."}
    body["fingerprint"] = digest(body)
    rendered = render_packet(body)
    require(len(rendered.encode()) <= s["policy"]["max_packet_bytes"], "CONTEXT_TOO_LARGE", "Required packet exceeds hard byte budget; split task/select narrower exact sources")
    return body


def render_packet(p: dict) -> str:
    blocks = ["# Task " + p["task"]["id"], p["instructions"],
              "## Identity\n" + json.dumps({k: p[k] for k in ("initiative_id", "epic_id", "canonical_baseline", "knowledge_head", "start_commit", "plan_digest", "fingerprint")}, indent=2),
              "## Initiative\n" + p["initiative_outcome"] + "\n" + "\n".join(p["initiative_constraints"]),
              "## Approved epic design\n" + p["epic_design"],
              "## Complete task design\n```json\n" + json.dumps(p["task"], ensure_ascii=False, indent=2) + "\n```"]
    if p.get("previous_candidate"):
        blocks.append("## Previous rejected candidate\n" + p["previous_candidate"] + "\n" + p["retry_instruction"])
    if p.get("repair_findings"):
        blocks.append("## Targeted repair findings\n" + json.dumps(p["repair_findings"], ensure_ascii=False, indent=2))
    for src in p["sources"]:
        blocks.append("## Source: " + src["target"] + "\nLayer: " + src["layer"] +
                      "\nCommit: " + src["source_commit"] + "\nSource path: " + src["source_path"] +
                      "\nSHA256: " + src["content_hash"] + "\nReason: " + src["reason"] +
                      "\n\n<source-data>\n" + src["content"] + "\n</source-data>")
    return "\n\n".join(blocks) + "\n"


def validate_final_docs(repo: Repository, commit: str) -> None:
    files = repo.files(commit)
    for p in files:
        if not p.startswith("docs/") or not p.endswith(".md"):
            continue
        text = safe_text(repo.read(commit, p), p)
        fm = frontmatter(text)
        require(fm.get("lifecycle") not in {"proposed", "history"} and fm.get("status") not in {"draft", "archived", "rejected"},
                "FINAL_DOC_AUTHORITY", p)
        stripped = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.S)
        for href in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", stripped):
            if re.match(r"[a-zA-Z][\w+.-]*:", href) or href.startswith("#"):
                continue
            rel = href.split("#")[0]
            target = posixpath.normpath(str(PurePosixPath(p).parent / rel))
            require(not target.startswith(("../", "/", "initiatives/active/", "changes/active/")), "INVALID_DOC_LINK", p + " -> " + href)
            require(target in files or any(f.startswith(target.rstrip("/") + "/") for f in files), "BROKEN_DOC_LINK", p + " -> " + href)
