"""Deterministic Markdown ontology and disposable graph navigation."""
import copy
import json
import pytest

from orchi_core import graph, ontology, retrieval
from orchi_core.common import OrchiError, sha


def record(target, text, role="current", commit="a" * 40):
    fm = ontology.frontmatter(text)
    return {"target": target, "content": text, "content_hash": sha(text.encode()), "role": role,
            "view": role, "layer": "canonical" if role == "current" else "intent", "source_commit": commit,
            "source_path": target, "kind": fm.get("kind"), "area": fm.get("area"),
            "artifacts": ontology.artifact_paths(fm)}


@pytest.mark.parametrize("metadata,code", [
    ("kind: unknown", "INVALID_KIND"),
    ("kind: component\nrole: target", "FORBIDDEN_AUTHORITY_METADATA"),
    ("kind: component\nstatus: draft", "FORBIDDEN_AUTHORITY_METADATA"),
    ("kind: component\nrelations: {made_up: []}", "INVALID_RELATION"),
    ("kind: component\nrelations: {depends_on: [docs/missing.md]}", "BROKEN_RELATION"),
    ("kind: component\nrelations: {depends_on: [docs/a.md#missing]}", "BROKEN_ANCHOR"),
    ("kind: component\nartifacts: [../secret.py]", "UNSAFE_PATH"),
    ("kind: component\nartifacts: [src/missing.py]", "UNMATCHED_ARTIFACT"),
    ("kind: component\nrelations: {depends_on: [initiatives/active/other/intent/requirements.md]}", "CROSS_SCOPE_RELATION"),
])
def test_invalid_ontology_diagnosed(metadata, code):
    report = ontology.lint({"docs/a.md": record("docs/a.md", "---\n" + metadata + "\n---\n# Component\n")})
    assert not report["ok"] and any(d["code"] == code for d in report["diagnostics"])


def test_plain_markdown_is_bootstrappable_not_silently_classified():
    report = ontology.lint({"docs/plain.md": record("docs/plain.md", "# Existing docs\nPlain Markdown.\n")})
    assert report["ok"] and any(d["code"] == "MISSING_KIND" and d["severity"] == "warning" for d in report["diagnostics"])
    assert not ontology.lint({"docs/plain.md": record("docs/plain.md", "# Existing docs\n")}, strict_paths=["docs/plain.md"])["ok"]


def test_duplicate_yaml_keys_and_aliases_rejected():
    for text in ("---\nkind: guide\nkind: component\n---\n", "---\na: &a []\nb: *a\n---\n"):
        with pytest.raises(OrchiError, check=lambda e: e.code == "INVALID_FRONTMATTER"):
            ontology.frontmatter(text)


def test_markdown_link_anchors_reference_links_and_fences():
    docs = {"docs/a.md": record("docs/a.md", '---\nkind: guide\n---\n# Start\n[See](b.md#details)\n[Reference][ref]\n[ref]: b.md#details\n```md\n[not-a-link](missing.md)\n```\n'),
            "docs/b.md": record("docs/b.md", "---\nkind: reference\n---\n# Details\nDescription.\n")}
    assert ontology.lint(docs)["ok"]
    docs["docs/a.md"]["content"] += "[Broken](b.md#no-such-anchor)\n"
    assert any(d["code"] == "BROKEN_ANCHOR" for d in ontology.lint(docs)["diagnostics"])


def test_explicit_duplicate_anchor_is_an_error():
    text = '<a id="same"></a>\n<a id="same"></a>\n'
    assert ontology.anchors(text)[1] == {"same"}


def test_area_index_is_enforced_for_changed_multi_page_core():
    docs = {p: record(p, "---\nkind: guide\n---\n# Topic\n") for p in ("docs/area/a.md", "docs/area/b.md")}
    assert ontology.lint(docs)["ok"]
    assert not ontology.lint(docs, strict_paths=list(docs))["ok"]
    docs["docs/area/README.md"] = record("docs/area/README.md", "---\nkind: index\n---\n# Area\n[a](a.md)\n[b](b.md)\n")
    assert ontology.lint(docs, strict_paths=list(docs))["ok"]


class ProjectionRepository:
    def files(self, commit):
        return {"src/service.py": ("100644", "f" * 40)}


def snapshot(records):
    return retrieval.Snapshot(records, {"scope": "canonical", "view": "current", "canonical_commit": "a" * 40}, [])


@pytest.fixture
def projected():
    records = {
        "docs/a.md": record("docs/a.md", "---\nkind: component\nartifacts: [src/service.py]\nrelations:\n  depends_on: [docs/b.md]\n---\n# Service\nA lexical unicorn lives here.\n"),
        "docs/b.md": record("docs/b.md", "---\nkind: reference\n---\n# Contract\nDifferent vocabulary.\n"),
        "docs/README.md": record("docs/README.md", "---\nkind: index\n---\n# Documentation\n"),
    }
    return graph.project(ProjectionRepository(), {}, snapshot(records))


def test_graph_related_is_deterministic_and_typed(projected):
    result = graph.related(projected, "docs/a.md", "depends_on")
    assert [n["target"] for n in result["related"]] == ["docs/b.md"]
    assert result == graph.related(projected, "docs/a.md", "depends_on")
    assert any(e["relation"] == "implemented_by" and e["target"] == "implementation:src/service.py" for e in projected["edges"])
    with pytest.raises(OrchiError, check=lambda e: e.code == "MISSING_GRAPH_NODE"):
        graph.related(projected, "intent/architecture/README.md")


def test_related_context_has_no_lexical_score(projected):
    result = graph.related_context(projected, [{"target": "docs/a.md"}], relation="depends_on")
    assert len(result) == 1 and result[0]["target"] == "docs/b.md"
    assert result[0]["primary_match"] is False and "score" not in result[0]


def test_replacement_projection_does_not_keep_old_edges():
    old = {"docs/a.md": record("docs/a.md", "---\nkind: component\nrelations: {depends_on: [docs/b.md]}\n---\n# A\n"),
           "docs/b.md": record("docs/b.md", "---\nkind: reference\n---\n# B\n")}
    new = {**old, "docs/a.md": record("docs/a.md", "---\nkind: component\n---\n# Replacement\n", commit="b" * 40)}
    result = graph.project(ProjectionRepository(), {}, snapshot(new))
    assert not any(e["relation"] == "depends_on" for e in result["edges"])
    assert next(n for n in result["nodes"] if n["target"] == "docs/a.md")["source_commit"] == "b" * 40
    assert result["fingerprint"] != graph.project(ProjectionRepository(), {}, snapshot(old))["fingerprint"]


def test_map_is_self_contained_reproducible_and_escapes_untrusted_labels(projected):
    projection = copy.deepcopy(projected)
    projection["nodes"][0]["label"] = "</script><script>alert('unsafe')</script>"
    rendered = graph.html(projection)
    assert rendered == graph.html(projection)
    assert "</script><script>alert" not in rendered
    assert "\\u003c/script\\u003e" in rendered
    assert 'src="http' not in rendered and 'href="http' not in rendered
    encoded = rendered.split('<script id="data" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert json.loads(encoded) == projection
