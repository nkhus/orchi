"""Accepted target bundles: exact Markdown bytes, stable references and Git provenance.

A manifest is a hash-bound inventory, not a second source of target prose. The
controller freezes proposals before asking for approval; local edits cannot
alter a pending or already accepted snapshot.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import canonical, digest, path, require, safe_text, sha, write_json
from .models import Initiative, IntentManifest
from . import ontology


def document_path(value: str) -> str:
    path(value)
    require(value.endswith(".md") and not value.startswith(("intent/", "initiatives/", "docs/")),
            "INVALID_INTENT_PATH", value)
    require(value in {"source.md", "requirements.md", "README.md"} or
            value.startswith(("architecture/", "decisions/", "requirements/")), "INVALID_INTENT_PATH", value)
    return value


def records(bundle: dict, commit: str = "", prefix: str = "") -> dict[str, dict]:
    m = bundle["manifest"]
    return {"intent/" + p: {"target": "intent/" + p, "role": "target", "view": "target", "layer": "intent",
            "content": text, "content_hash": sha(text.encode()), "source_commit": commit,
            "source_path": prefix + "intent/" + p, "initiative_id": m["initiative_id"],
            "intent_revision": m["revision"], "intent_digest": digest(m),
            "kind": ontology.frontmatter(text).get("kind"), "area": ontology.frontmatter(text).get("area"),
            "artifacts": ontology.artifact_paths(ontology.frontmatter(text))}
            for p, text in sorted(bundle["documents"].items()) if p != "source.md"}


def build(initiative_id: str, documents: dict[str, str], revision: int = 1,
          resolved_requirements: dict[str, str] | None = None) -> dict:
    requirements, architecture = {}, []
    for p, text in sorted(documents.items()):
        document_path(p)
        safe_text(text.encode(), p)
        if p == "source.md":
            continue
        fm = ontology.frontmatter(text)
        ids = fm.get("requirements", [])
        require(isinstance(ids, list) and all(isinstance(r, str) for r in ids), "INVALID_REQUIREMENT", p)
        for rid in ids:
            require(rid not in requirements, "DUPLICATE_REQUIREMENT", rid)
            requirements[rid] = "intent/" + p + "#" + rid
        if fm.get("kind") == "architecture":
            architecture.append("intent/" + p)
    manifest = IntentManifest.model_validate({"initiative_id": initiative_id, "revision": revision,
        "documents": {p: sha(text.encode()) for p, text in sorted(documents.items())},
        "requirements": requirements, "architecture": architecture,
        "resolved_requirements": resolved_requirements or {}}).model_dump()
    return {"manifest": manifest, "documents": dict(documents)}


def load(directory: str | Path) -> dict:
    root = Path(directory)
    require(root.is_dir() and not root.is_symlink(), "INVALID_INTENT_DIRECTORY", str(root))
    require(not any(p.is_symlink() for p in [root, *root.parents]), "UNSAFE_PATH", str(root))
    docs = {}
    total = 0
    for file in sorted(root.rglob("*")):
        require(not file.is_symlink(), "UNSAFE_PATH", str(file))
        if file.is_file() and file != root / "manifest.json":
            relative = file.relative_to(root).as_posix()
            document_path(relative)
            data = file.read_bytes()
            total += len(data)
            require(total <= 8_000_000, "INTENT_TOO_LARGE", "Intent bundle exceeds 8 MB")
            docs[relative] = safe_text(data, relative)
    manifest = root / "manifest.json"
    require(manifest.is_file() and not manifest.is_symlink(), "MISSING_INTENT_MANIFEST", str(manifest))
    return {"manifest": json.loads(safe_text(manifest.read_bytes(), "intent/manifest.json", 1_000_000)), "documents": docs}


def build_directory(directory: str | Path, initiative_id: str, revision: int = 1,
                    resolved_requirements: dict[str, str] | None = None) -> dict:
    root = Path(directory)
    require(root.is_dir() and not any(p.is_symlink() for p in [root, *root.parents]), "INVALID_INTENT_DIRECTORY", str(root))
    docs = {}
    for file in sorted(root.rglob("*")):
        require(not file.is_symlink(), "UNSAFE_PATH", str(file))
        if file.is_file() and file != root / "manifest.json":
            relative = file.relative_to(root).as_posix()
            document_path(relative)
            docs[relative] = safe_text(file.read_bytes(), relative)
    bundle = build(initiative_id, docs, revision, resolved_requirements)
    # Full scope-aware link validation occurs when the controller sees baseline Current.
    write_json(root / "manifest.json", bundle["manifest"])
    return {"manifest": bundle["manifest"], "intent": {"revision": revision, "digest": digest(bundle["manifest"])}}


def validate(bundle: dict, spec: dict, current: dict | None = None, files=(), *, evidence=(), completed=()) -> dict:
    require(isinstance(bundle, dict) and set(bundle) == {"manifest", "documents"}, "INVALID_INTENT_BUNDLE", "Expected manifest and exact documents")
    manifest = IntentManifest.model_validate(bundle["manifest"]).model_dump()
    spec = Initiative.model_validate(spec).model_dump()
    require(manifest["initiative_id"] == spec["id"] and manifest["revision"] == spec["intent"]["revision"],
            "INTENT_IDENTITY", "Initiative and Intent identity differ")
    require(digest(manifest) == spec["intent"]["digest"], "INTENT_DIGEST_MISMATCH", "Accepted Intent manifest digest differs")
    docs = bundle["documents"]
    require(isinstance(docs, dict) and set(docs) == set(manifest["documents"]), "INTENT_INVENTORY", "Manifest must cover every and only bundled document")
    require({"source.md", "requirements.md", "architecture/README.md"} <= set(docs), "INCOMPLETE_INTENT", "Source, requirements and architecture/README.md are required")
    total = 0
    for p, text in docs.items():
        document_path(p)
        require(isinstance(text, str) and bool(text.strip()), "EMPTY_INTENT_DOCUMENT", p)
        total += len(text.encode())
        safe_text(text.encode(), p)
        require(sha(text.encode()) == manifest["documents"][p], "INTENT_CONTENT_CHANGED", p)
    require(total <= 8_000_000, "INTENT_TOO_LARGE", "Intent bundle exceeds 8 MB")
    generated = build(spec["id"], docs, manifest["revision"], manifest["resolved_requirements"])["manifest"]
    require(generated == manifest, "INTENT_REGISTRY_MISMATCH", "Requirement/architecture registry must match document metadata")
    require(ontology.frontmatter(docs["requirements.md"]).get("kind") == "requirements", "INVALID_KIND", "requirements.md must have kind: requirements")
    require(ontology.frontmatter(docs["architecture/README.md"]).get("kind") == "architecture", "INVALID_KIND", "architecture/README.md must have kind: architecture")
    for p, text in docs.items():
        if p.startswith("decisions/"):
            require(ontology.frontmatter(text).get("kind") in {"decision", "index"}, "INVALID_KIND", p)
    target = records({"manifest": manifest, "documents": docs})
    report = ontology.lint({**(current or {}), **target}, files,
                          requirements=manifest["requirements"], evidence=evidence, check_indexes=False)
    errors = [d for d in report["diagnostics"] if d["severity"] == "error" and d["target"] in target]
    require(not errors, "INVALID_INTENT_ONTOLOGY", json.dumps(errors))
    known = set(manifest["requirements"]) | set(manifest["resolved_requirements"])
    covered = set()
    historical = {e["epic_id"]: e for e in completed}
    for epic in spec["epics"]:
        require(set(epic["contributes_to"]) <= known, "UNKNOWN_REQUIREMENT", epic["id"])
        covered.update(epic["contributes_to"])
        for ref in epic["realizes"]:
            document, _, anchor = ref.partition("#")
            current_ref = document in manifest["architecture"] and (not anchor or anchor in ontology.anchors(target[document]["content"])[0])
            # Completed contracts keep historical references when target documents are
            # reorganized or removed. Engine separately enforces immutable contracts.
            historical_ref = document in historical.get(epic["id"], {}).get("target_bindings", {}).get("architecture", {})
            require(current_ref or historical_ref, "UNKNOWN_ARCHITECTURE", ref)
    require(set(manifest["requirements"]) <= covered, "INCOMPLETE_ROADMAP", "Every active root requirement needs a contributing epic")
    return {"manifest": manifest, "documents": dict(docs)}


def accepted(repo, state: dict) -> dict:
    receipt = state.get("intent")
    require(receipt is not None, "NO_ACCEPTED_INTENT", "Accept the initiative target before reading Target")
    prefix = "initiatives/active/" + state["spec"]["id"] + "/intent/"
    commit = receipt["commit"]
    manifest = json.loads(safe_text(repo.read(commit, prefix + "manifest.json"), "intent/manifest.json", 1_000_000))
    require(digest(manifest) == state["spec"]["intent"]["digest"] == receipt["digest"], "INTENT_DIGEST_MISMATCH", "Accepted Git manifest identity differs")
    require(manifest["initiative_id"] == state["spec"]["id"] and manifest["revision"] == state["spec"]["intent"]["revision"], "INTENT_IDENTITY", "Accepted manifest scope differs")
    documents = {}
    for p, content_hash in manifest["documents"].items():
        document_path(p)
        text = safe_text(repo.read(commit, prefix + p), p)
        require(sha(text.encode()) == content_hash, "INTENT_CONTENT_CHANGED", p)
        documents[p] = text
    return {"manifest": manifest, "documents": documents}


def commit_contents(bundle: dict, prefix: str, previous: dict | None = None) -> dict:
    result = {prefix + "intent/" + p: text.encode() for p, text in bundle["documents"].items()}
    result[prefix + "intent/manifest.json"] = canonical(bundle["manifest"])
    if previous:
        for p in set(previous["documents"]) - set(bundle["documents"]):
            result[prefix + "intent/" + p] = None
    return result


def validate_revision(old: dict, new: dict) -> dict:
    a, b = old["manifest"], new["manifest"]
    require(b["revision"] == a["revision"] + 1, "INVALID_INTENT_REVISION", "Increment the accepted Intent revision by exactly one")
    require(old["documents"]["source.md"] == new["documents"]["source.md"], "IMMUTABLE_REQUEST_SOURCE", "Original request provenance cannot be rewritten")
    removed = set(a["requirements"]) - set(b["requirements"])
    require(set(b["resolved_requirements"]) == set(a["resolved_requirements"]) | removed and
            all(b["resolved_requirements"].get(k) == v for k, v in a["resolved_requirements"].items()),
            "UNRESOLVED_REMOVED_REQUIREMENT", "Removed IDs need explicit accepted resolutions; existing resolutions are immutable")
    changed_documents = sorted(p for p in a["documents"].keys() | b["documents"].keys() if a["documents"].get(p) != b["documents"].get(p))
    def fingerprint(manifest, rid):
        ref = manifest["requirements"].get(rid)
        return (ref, manifest["documents"].get(ref.split("#")[0].removeprefix("intent/"))) if ref else None
    affected = sorted(r for r in a["requirements"].keys() | b["requirements"].keys() if fingerprint(a, r) != fingerprint(b, r))
    return {"old_digest": digest(a), "new_digest": digest(b), "impacted_requirements": affected,
            "impacted_targets": ["intent/" + p for p in changed_documents if p != "source.md"],
            "resolved_requirements": {r: b["resolved_requirements"][r] for r in sorted(removed)}}
