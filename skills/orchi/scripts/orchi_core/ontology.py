"""Small Markdown ontology. It validates structure; it never assigns authority.

Frontmatter is optional for incidental Markdown. A kind is required for documents
with ontology fields, accepted Intent, accepted designs, and changed final Core.
No YAML lifecycle/status field can override the controller's Current/Target roles.
"""
from __future__ import annotations

from collections import Counter
import fnmatch
import posixpath
import re
from pathlib import PurePosixPath
from urllib.parse import unquote
import yaml

from .common import OrchiError, path, require, secret_path

KINDS = frozenset({"index", "component", "reference", "decision", "runbook", "guide", "requirements", "architecture"})
RELATIONS = frozenset({"depends_on", "relates_to", "part_of", "documents", "implemented_by", "addresses", "realizes", "verified_by"})
AUTHORITY_FIELDS = frozenset({"role", "layer", "view", "authority", "current", "target", "lifecycle", "status"})
IMPLEMENTATION_RELATIONS = frozenset({"documents", "implemented_by"})


class _UniqueLoader(yaml.SafeLoader):
    """Duplicate YAML keys must not silently overwrite accepted metadata."""


def _mapping(loader, node, deep=False):
    result = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        require(isinstance(key, str) and key not in result, "INVALID_FRONTMATTER", "Duplicate/non-string YAML mapping key")
        result[key] = loader.construct_object(v, deep=deep)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def frontmatter(text: str) -> dict:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    match = re.search(r"^---[ \t]*$", text[4:], re.M)
    require(match is not None and match.start() < 16384, "INVALID_FRONTMATTER", "Missing/oversized frontmatter")
    raw = text[4:4 + match.start()]
    try:
        require(not any(isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)) for t in yaml.scan(raw)),
                "INVALID_FRONTMATTER", "YAML aliases are not accepted")
        fm = yaml.load(raw, Loader=_UniqueLoader)
    except yaml.YAMLError as exc:
        raise OrchiError("INVALID_FRONTMATTER", "Invalid YAML") from exc
    require(isinstance(fm, dict), "INVALID_FRONTMATTER", "Expected mapping")
    return fm


def artifact_paths(fm: dict) -> list[str]:
    value = fm.get("artifacts", [])
    if isinstance(value, dict):
        value = [x for group in value.values() if isinstance(group, list) for x in group]
    if not isinstance(value, list):
        return []
    return [v if isinstance(v, str) else v["path"] for v in value
            if isinstance(v, str) or isinstance(v, dict) and isinstance(v.get("path"), str)]


def body(text: str, *, strip_inline: bool = True) -> str:
    text = text.replace("\r\n", "\n")
    if text.startswith("---\n"):
        match = re.search(r"^---[ \t]*$", text[4:], re.M)
        if match:
            text = text[4 + match.end():]
    lines, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            lines.append("")
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            lines.append("")
        else:
            lines.append(re.sub(r"`+[^`]*`+", "", line) if strip_inline else line)
    return "\n".join(lines)


def anchors(text: str) -> tuple[set[str], set[str]]:
    """GitHub-style heading slugs plus explicit HTML id/name anchors."""
    prose = body(text, strip_inline=False)
    explicit = re.findall(r'<(?:a|h[1-6])\b[^>]*\b(?:id|name)=[\"\']([^\"\']+)[\"\']', prose, re.I)
    used = set(explicit)
    duplicates = {key for key, count in Counter(explicit).items() if count > 1}
    counts = Counter()
    lines = prose.splitlines()
    for i, line in enumerate(lines):
        heading = re.match(r"^ {0,3}#{1,6}\s+(.*?)(?:\s+#+)?\s*$", line)
        setext = i + 1 < len(lines) and line.strip() and re.fullmatch(r" {0,3}(?:=+|-+)\s*", lines[i + 1])
        if not heading and not setext:
            continue
        title = heading[1] if heading else line.strip()
        title = re.sub(r"<[^>]+>", "", title)
        slug = re.sub(r"[^\w\-\s]", "", title.lower()).replace(" ", "-")
        n = counts[slug]
        counts[slug] += 1
        slug = slug + ("-" + str(n) if n else "")
        if slug in used:
            duplicates.add(slug)
        used.add(slug)
    return used, duplicates


def artifact_pattern(value: str) -> str:
    require(isinstance(value, str) and bool(value), "INVALID_ARTIFACT", "Expected an implementation path or glob")
    # Validate path structure independently of glob metacharacters.
    cleaned = re.sub(r"[\*?\[\]]", "x", value)
    path(cleaned)
    require(not value.startswith(("docs/", "intent/", "epics/", "initiatives/", "history/", "changes/")) and
            ".git" not in value.split("/") and not secret_path(value), "INVALID_ARTIFACT", value)
    return value


def reference(origin: str, value: str, requirements: dict[str, str] | None = None) -> str:
    """Resolve a logical reference, never a physical other-initiative path."""
    require(isinstance(value, str) and bool(value), "INVALID_RELATION_TARGET", origin)
    if value in (requirements or {}):
        return requirements[value]
    require(not re.match(r"[A-Za-z][\w+.-]*:", value) and not value.startswith("/"),
            "INVALID_RELATION_TARGET", value)
    value = unquote(value)
    require(not value.startswith(("initiatives/", "changes/", "history/")), "CROSS_SCOPE_RELATION", value)
    document, separator, anchor = value.partition("#")
    if not document:
        document = origin
    elif not document.startswith(("docs/", "intent/", "epics/")):
        document = posixpath.normpath(str(PurePosixPath(origin).parent / document))
    path(document)
    require(not document.startswith(("initiatives/", "changes/", "history/")), "CROSS_SCOPE_RELATION", value)
    require(not separator or bool(anchor) and "#" not in anchor, "INVALID_ANCHOR", value)
    return document + ("#" + anchor if separator else "")


def markdown_links(text: str) -> list[str]:
    prose = body(text)
    links = re.findall(r"!?\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+[^)]*)?\)", prose)
    definitions = {k.strip().casefold(): v for k, v in re.findall(r"^\s*\[([^\]]+)\]:\s*<?([^\s>]+)>?", prose, re.M)}
    for label, key in re.findall(r"!?\[([^\]]+)\]\[([^\]]*)\]", prose):
        links.append(definitions.get((key or label).strip().casefold(), "missing-reference-definition/" + (key or label)))
    # Definitions can also be used through CommonMark shortcut links.
    links.extend(definitions.values())
    return list(dict.fromkeys(links))


def lint(records: dict[str, dict], files=(), *, requirements=None, evidence=(),
         strict_paths=(), lookup=None, check_indexes=True) -> dict:
    """Lint only supplied authority records. Extra file names permit Markdown links,
    but typed knowledge relations must resolve to the supplied knowledge snapshot.
    """
    file_set = set(files) | set(records)
    evidence = set(evidence)
    requirements = requirements or {}
    strict_paths = set(strict_paths)
    diagnostics, metadata, incoming = [], {}, set()

    def report(code, target, message, severity="error"):
        diagnostics.append({"severity": severity, "code": code, "target": target, "message": message})

    def exists(origin, raw, typed=False):
        ref = reference(origin, raw, requirements)
        doc, _, anchor = ref.partition("#")
        require(doc in (records if typed else file_set) or not typed and
                any(p.startswith(doc.rstrip("/") + "/") for p in file_set), "BROKEN_RELATION" if typed else "BROKEN_DOC_LINK", raw)
        if anchor:
            text = records.get(doc, {}).get("content")
            if text is None and lookup is not None:
                text = lookup(doc)
            require(text is not None and anchor in anchors(text)[0], "BROKEN_ANCHOR", raw)
        incoming.add(doc)
        return ref

    for target, rec in sorted(records.items()):
        try:
            fm = frontmatter(rec["content"])
            metadata[target] = fm
            load_bearing = target in strict_paths or rec.get("role") in {"target", "epic-design"} or any(k in fm for k in ("kind", "area", "artifacts", "relations", "requirements"))
            if not fm.get("kind"):
                report("MISSING_KIND", target, "Classify load-bearing knowledge with a known kind", "error" if load_bearing else "warning")
            else:
                require(isinstance(fm["kind"], str) and fm["kind"] in KINDS, "INVALID_KIND", str(fm["kind"]))
            require(not (set(fm) & AUTHORITY_FIELDS), "FORBIDDEN_AUTHORITY_METADATA", "Authority is assigned by Orchi, not frontmatter")
            if "area" in fm:
                require(isinstance(fm["area"], str) and bool(fm["area"].strip()), "INVALID_AREA", target)
            if "artifacts" in fm:
                values = fm["artifacts"]
                require(isinstance(values, list) and all(isinstance(v, str) for v in values), "INVALID_ARTIFACT", "Use a list of implementation paths/globs")
                for pattern in values:
                    artifact_pattern(pattern)
                    if not any(fnmatch.fnmatchcase(p, pattern) for p in file_set):
                        report("UNMATCHED_ARTIFACT", target, pattern, "warning" if rec.get("role") == "target" else "error")
            ids = fm.get("requirements", [])
            require(isinstance(ids, list) and all(isinstance(v, str) and re.fullmatch(r"req-[a-z0-9]+(?:[-.][a-z0-9]+)*", v) for v in ids),
                    "INVALID_REQUIREMENT", "Use stable req-* IDs")
            require(len(ids) == len(set(ids)), "DUPLICATE_REQUIREMENT", target)
            valid_anchors, duplicates = anchors(rec["content"])
            require(not duplicates, "DUPLICATE_ANCHOR", ", ".join(sorted(duplicates)))
            require(set(ids) <= valid_anchors, "MISSING_REQUIREMENT_ANCHOR", target)
            relations = fm.get("relations", {})
            require(isinstance(relations, dict), "INVALID_RELATIONS", "Expected a typed mapping of lists")
            for relation, values in sorted(relations.items()):
                require(relation in RELATIONS, "INVALID_RELATION", relation)
                require(isinstance(values, list) and all(isinstance(v, str) for v in values), "INVALID_RELATIONS", relation)
                for raw in values:
                    if relation in IMPLEMENTATION_RELATIONS:
                        artifact_pattern(raw)
                        if not any(fnmatch.fnmatchcase(p, raw) for p in file_set):
                            report("UNMATCHED_ARTIFACT", target, raw, "warning" if rec.get("role") == "target" else "error")
                    elif relation == "verified_by" and raw.startswith("evidence:"):
                        require(raw[9:] in evidence, "UNKNOWN_EVIDENCE", raw)
                    else:
                        exists(target, raw, typed=True)
            for link in markdown_links(rec["content"]):
                if re.match(r"(?:https?|mailto):", link, re.I):
                    continue
                require(not re.match(r"[A-Za-z][\w+.-]*:", link), "UNSAFE_DOC_LINK", link)
                exists(target, link)
        except OrchiError as exc:
            report(exc.code, target, str(exc))
    if check_indexes:
        directories = {str(PurePosixPath(p).parent) for p in records}
        for directory in sorted(directories):
            members = [p for p in records if str(PurePosixPath(p).parent) == directory]
            # Small flat areas bootstrap without ceremony. Multi-page areas require an entry point.
            if len(members) >= 2 and directory + "/README.md" not in records and not any(metadata.get(p, {}).get("kind") == "index" for p in members):
                report("MISSING_AREA_INDEX", directory, "Add an area README.md or index node",
                       "error" if any(p in strict_paths for p in members) else "warning")
    for target in sorted(records):
        if target not in incoming and metadata.get(target, {}).get("kind") != "index":
            report("ORPHAN_NODE", target, "No incoming authored knowledge link in this snapshot", "warning")
    diagnostics.sort(key=lambda d: (d["target"], d["severity"], d["code"], d["message"]))
    return {"ok": not any(d["severity"] == "error" for d in diagnostics),
            "documents": len(records), "diagnostics": diagnostics}
