"""Deterministic retrieval quality, projection safety, and exact-source tests."""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3

import pytest

from orchi_core import context, diagnostics, retrieval
from orchi_core.common import OrchiError, sha


@pytest.fixture
def corpus(world):
    texts = {
        "docs/auth.md": "---\nartifacts: [src/left.py]\n---\n# Identity\nAuthentication overview.\n\n## Callback validation\nVerify authentication callback signatures before accepting a login.\n\n## Session expiry\nExpire sessions after their deadline.\n",
        "docs/cache.md": "# Caching\nThe cache stores responses.\n\n## Firecracker isolation\nA firecracker microVM isolates the worker.\n",
        "docs/noise.md": "# Other notes\n" + "authentication " * 120 + "\n",
        "docs/hidden.md": "---\nstatus: draft\n---\n# Secret proposed account\nDraftsentinel\n",
        "docs/retired.md": "---\nlifecycle: history\n---\n# Old account\nArchivesentinel\n",
        "docs/credentials/private.md": "# Private\nCredentialssentinel\n",
        "initiatives/active/other/knowledge/docs/proposed.md": "# Other initiative\nOthersentinel\n",
        "README.md": "# Project\nRootsentinel\n",
    }
    repo = world.e.repo
    commit = repo.write(world.baseline, {p: t.encode() for p, t in texts.items()}, "Search fixtures")
    repo.git("update-ref", "refs/heads/main", commit)
    state = {**world.e.state(), "spec": {"id": "feature"}, "baseline": commit,
             "head": commit, "knowledge_head": commit, "knowledge_revision": 0, "knowledge": {}}
    return repo, state, world.root / "retrieval-cache"


def search(corpus, query, initiative=None, **kwargs):
    repo, state, cache = corpus
    return context.search(repo, state, query, initiative, cache_root=cache, **kwargs)


def replace(corpus, text="# Identity\nNewsemantics uses signed callback tokens.\n", action="replace"):
    """Synthetic accepted checkpoint for retrieval-only tests, not a gate bypass API."""
    repo, state, _ = corpus
    source = "initiatives/active/feature/knowledge/docs/auth.md"
    head = repo.write(state["knowledge_head"], {source: text.encode() if action != "retire" else None}, "Checkpoint fixture")
    state["knowledge"]["docs/auth.md"] = {
        "target": "docs/auth.md", "action": action, "content": text if action != "retire" else None,
        "artifact_hashes": repo.hashes(head, ["src/left.py"]), "checks": ["baseline"], "evidence": "fixture-evidence",
        "verified_code_commit": state["head"], "source_path": source, "source_commit": head,
    }
    state.update(head=head, knowledge_head=head, knowledge_revision=state["knowledge_revision"] + 1)


def test_ranked_section_has_exact_provenance_and_readback(corpus):
    result = search(corpus, "authentication callback")
    hit = result["results"][0]
    assert hit["target"] == "docs/auth.md" and hit["heading"] == "Callback validation"
    assert hit["heading_path"] == ["Identity", "Callback validation"]
    assert hit["line"] == 7 and hit["snippet_line"] == 8
    assert hit["matched_terms"] == 2 and "bm25" in hit["via"]
    assert "signatures" in hit["snippet"]
    exact = context.get(corpus[0], corpus[1], hit["target"], content_hash=hit["content_hash"])
    assert exact["source_commit"] == hit["source_commit"]
    assert hit["snippet"] in exact["content"]


@pytest.mark.parametrize("query,target,channel", [
    ("microV", "docs/cache.md", "bm25"),
    ("cracker", "docs/cache.md", "trigram"),
    ("firecraker", "docs/cache.md", "fuzzy"),
    ("authetication", "docs/auth.md", "fuzzy"),
])
def test_prefix_substring_and_typo_retrieval(corpus, query, target, channel):
    hits = search(corpus, query)["results"]
    assert any(h["target"] == target and channel in h["via"] for h in hits)


@pytest.mark.parametrize("query", ["Draftsentinel", "Archivesentinel", "Credentialssentinel", "Othersentinel", "Rootsentinel"])
def test_only_current_core_is_searchable(corpus, query):
    assert search(corpus, query)["results"] == []


def test_uncommitted_edits_never_enter_the_projection(corpus):
    repo, _, _ = corpus
    (repo.root / "docs/auth.md").write_text("# Uncommittedsentinel\n")
    assert search(corpus, "Uncommittedsentinel")["results"] == []
    assert search(corpus, "callback")["results"]


def test_frontmatter_is_not_body_search_content(corpus):
    assert search(corpus, "artifacts")["results"] == []
    owners = context.owners(corpus[0], corpus[1], "src/left.py")
    assert "docs/auth.md" in {o["target"] for o in owners["owners"]}


def test_heading_parser_handles_fences_setext_and_line_offsets():
    text = "---\nlabel: ignored\n---\nPage\n====\nintro\n\nSubsection\n----------\n~~~python\n# not a heading\n```\n~~~\n## Real\ntext\n"
    parts = retrieval.chunks(text)
    assert [(c.line, c.heading) for c in parts] == [(4, "Page"), (8, "Subsection"), (14, "Real")]
    assert parts[1].heading_path == ("Page", "Subsection")
    assert "# not a heading" in parts[1].body
    for chunk in parts:
        assert chunk.body == "\n".join(text.splitlines()[chunk.line - 1:chunk.end_line])


def test_long_sections_split_at_source_line_boundaries():
    text = "# Long section\n" + "an explanatory line\n" * 250
    parts = retrieval.chunks(text)
    assert len(parts) == 3 and all(c.end_line - c.line < retrieval.CHUNK_LINES for c in parts)
    assert all(c.heading == "Long section" for c in parts)
    assert "\n".join(c.body for c in parts) == text.rstrip("\n")


def test_unicode_case_accents_and_substrings(corpus):
    # Non-English test data is escaped so repository prose remains English.
    repo, state, _ = corpus
    text = "# Caf\u00e9\nR\u00e9sum\u00e9 Stra\u00dfe.\n\n## Identity\n\u0410\u0443\u0442\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f\n\n## Events\n\u7cfb\u7edf\u7528\u6237\u8ba4\u8bc1\u670d\u52a1\n"
    commit = repo.write(state["baseline"], {"docs/unicode.md": text.encode()}, "Unicode fixture")
    repo.git("update-ref", "refs/heads/main", commit)
    for query in ("CAFE", "resume", "re\u0301sume\u0301", "strasse", "\u0442\u0438\u0444\u0438\u043a\u0430", "\u7528\u6237\u8ba4"):
        hits = search(corpus, query)["results"]
        assert hits and hits[0]["target"] == "docs/unicode.md"
        assert hits[0]["snippet"] in text


def test_scope_isolation_masking_and_retirement(corpus):
    canonical = search(corpus, "callback")
    replace(corpus)
    initiative = search(corpus, "Newsemantics", "feature")
    assert initiative["results"][0]["layer"] == "working"
    assert initiative["results"][0]["source_path"].startswith("initiatives/active/feature/")
    assert canonical["index"]["path"] != initiative["index"]["path"]
    assert search(corpus, "Newsemantics")["results"] == []
    assert not any(h["target"] == "docs/auth.md" for h in search(corpus, "signatures", "feature")["results"])
    replace(corpus, action="retire")
    assert search(corpus, "Newsemantics", "feature")["results"] == []
    assert any(h["target"] == "docs/auth.md" for h in search(corpus, "signatures")["results"])


def test_stale_cache_cannot_resurrect_a_masked_canonical_record(corpus):
    replace(corpus)
    before = search(corpus, "Newsemantics", "feature")
    repo, state, _ = corpus
    state["knowledge_head"] = repo.write(state["head"], {"src/left.py": b"VALUE = 99\n"}, "Artifact drift")
    after = search(corpus, "Newsemantics", "feature")
    assert not after["results"]
    assert after["index"]["fingerprint"] != before["index"]["fingerprint"]
    assert {"target": "docs/auth.md", "code": "STALE_WORKING_KNOWLEDGE"} in after["diagnostics"]
    assert not any(h["target"] == "docs/auth.md" for h in search(corpus, "signatures", "feature")["results"])


def test_active_epic_code_does_not_advance_verified_search(corpus):
    replace(corpus)
    before = search(corpus, "Newsemantics", "feature")
    repo, state, _ = corpus
    state["head"] = repo.write(state["head"], {"src/left.py": b"VALUE = 100\n"}, "Active epic result")
    after = search(corpus, "Newsemantics", "feature")
    assert before["results"] == after["results"] and after["index"]["status"] == "reused"
    assert before["snapshot"]["knowledge_head"] == after["snapshot"]["knowledge_head"]


def test_wrong_initiative_is_rejected_before_building_cache(corpus):
    with pytest.raises(OrchiError, check=lambda e: e.code == "INITIATIVE_SCOPE"):
        search(corpus, "callback", "other")
    assert not corpus[2].exists()


def test_initiative_inherits_baseline_not_current_canonical(corpus):
    repo, state, _ = corpus
    before = search(corpus, "signatures", "feature")
    new = repo.write(state["baseline"], {"docs/auth.md": b"# Canonicalsentinel\nChanged independently\n"}, "Canonical advances")
    repo.git("update-ref", "refs/heads/main", new)
    assert search(corpus, "Canonicalsentinel")["results"]
    assert search(corpus, "Canonicalsentinel", "feature")["results"] == []
    after = search(corpus, "signatures", "feature")
    assert after["results"] == before["results"] and after["index"]["status"] == "reused"


def test_cache_reuse_invalidation_revalidation_and_deletion(corpus):
    first = search(corpus, "callback")
    file = Path(first["index"]["path"])
    mtime = file.stat().st_mtime_ns
    second = search(corpus, "callback")
    assert second["index"]["status"] == "reused" and file.stat().st_mtime_ns == mtime
    assert first["results"] == second["results"]
    replace(corpus)
    a = search(corpus, "Newsemantics", "feature")
    # Same text, newly verified provenance and knowledge checkpoint.
    replace(corpus)
    b = search(corpus, "Newsemantics", "feature")
    assert a["index"]["fingerprint"] != b["index"]["fingerprint"] and b["index"]["status"] == "rebuilt"
    file.unlink()
    third = search(corpus, "callback")
    assert third["index"]["status"] == "built" and third["results"] == first["results"]
    assert len(list(corpus[2].glob("*.sqlite"))) == 2


def test_canonical_content_change_forces_rebuild_and_old_read_hash_fails(corpus):
    repo, state, _ = corpus
    before = search(corpus, "callback")
    hit = before["results"][0]
    commit = repo.write(state["baseline"], {hit["target"]: b"# Replacedsentinel\nDifferent semantics\n"}, "New Core")
    repo.git("update-ref", "refs/heads/main", commit)
    after = search(corpus, "Replacedsentinel")
    assert after["results"] and after["index"]["status"] == "rebuilt"
    assert before["index"]["fingerprint"] != after["index"]["fingerprint"]
    with pytest.raises(OrchiError, check=lambda e: e.code == "KNOWLEDGE_CHANGED"):
        context.get(repo, state, hit["target"], content_hash=hit["content_hash"])


def test_corrupt_cache_recovers_without_altering_authority(corpus):
    before = search(corpus, "callback")
    Path(before["index"]["path"]).write_bytes(b"Not a SQLite database")
    after = search(corpus, "callback")
    assert before["results"] == after["results"]
    assert any(d["code"] == "CACHE_REBUILT" for d in after["diagnostics"])


def test_cached_source_forgery_is_not_returned(corpus):
    before = search(corpus, "callback")
    with sqlite3.connect(before["index"]["path"]) as con:
        con.execute("UPDATE chunks SET body='Forged snippet' WHERE target='docs/auth.md'")
    after = search(corpus, "callback")
    assert before["results"] == after["results"]
    assert "Forged snippet" not in json.dumps(after)
    assert any(d["code"] == "CACHE_REBUILT" for d in after["diagnostics"])


def test_missing_fts_table_is_rebuilt(corpus):
    before = search(corpus, "callback")
    with sqlite3.connect(before["index"]["path"]) as con:
        con.execute("DROP TABLE lex")
    assert search(corpus, "callback")["results"] == before["results"]


def test_engine_change_invalidates_cache(corpus, monkeypatch):
    before = search(corpus, "callback")
    monkeypatch.setattr(retrieval, "engine_signature", lambda: "different-parser-or-ranking")
    after = search(corpus, "callback")
    assert after["index"]["status"] == "rebuilt" and after["results"] == before["results"]


def test_unwritable_or_symlinked_cache_uses_memory(corpus, tmp_path):
    expected = search(corpus, "callback")["results"]
    blocked = tmp_path / "blocked"
    blocked.write_text("Keep me")
    result = context.search(corpus[0], corpus[1], "callback", cache_root=blocked / "cache")
    assert result["results"] == expected and result["index"]["status"] == "memory"
    assert blocked.read_text() == "Keep me"
    outside = tmp_path / "outside"; outside.mkdir()
    link = tmp_path / "link"; link.symlink_to(outside, target_is_directory=True)
    result = context.search(corpus[0], corpus[1], "callback", cache_root=link)
    assert result["results"] == expected and not list(outside.iterdir())


def test_atomic_concurrent_builds_use_their_own_scope_snapshot(corpus):
    repo, state, cache = corpus
    a = context.retrieval_snapshot(repo, state)
    b = copy.deepcopy(a)
    record = b.records["docs/auth.md"]
    record["content"] = "# Identity\nA concurrently updated callback.\n"
    record["content_hash"] = sha(record["content"].encode())
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda snap: retrieval.search(snap, "callback", cache_root=cache), [a, b, a, b]))
    for snap, output in zip([a, b, a, b], outputs):
        assert output["index"]["fingerprint"] == snap.fingerprint
        assert output["results"][0]["content_hash"] == snap.records["docs/auth.md"]["content_hash"]
    assert len(list(cache.glob("*.sqlite"))) == 1 and not list(cache.glob(".retrieval-*"))


def test_no_fts5_fails_clearly_but_exact_reads_work(corpus, monkeypatch):
    monkeypatch.setattr(retrieval, "capabilities", lambda: {"fts5": False, "trigram": False})
    with pytest.raises(OrchiError, check=lambda e: e.code == "FTS5_UNAVAILABLE"):
        search(corpus, "callback")
    assert context.get(corpus[0], corpus[1], "docs/auth.md")["content"]


def test_missing_trigram_reports_degraded_matching(corpus, monkeypatch):
    monkeypatch.setattr(retrieval, "capabilities", lambda: {"fts5": True, "trigram": False})
    result = search(corpus, "callback")
    assert result["results"] and all(h["via"] == ["bm25"] for h in result["results"])
    assert any(d["code"] == "TRIGRAM_UNAVAILABLE" for d in result["diagnostics"])
    assert search(corpus, "firecraker")["results"] == []


@pytest.mark.parametrize("query", ["", "  ", '"() * :', "x" * 513, "x" * 65, "a\x00b", " ".join(f"term{i}" for i in range(17))])
def test_invalid_queries_are_bounded(corpus, query):
    with pytest.raises(OrchiError, check=lambda e: e.code == "INVALID_QUERY"):
        search(corpus, query)
    assert not corpus[2].exists()


@pytest.mark.parametrize("limit", [0, -1, 101, True])
def test_invalid_limits_are_bounded(corpus, limit):
    with pytest.raises(OrchiError, check=lambda e: e.code == "INVALID_LIMIT"):
        search(corpus, "callback", limit=limit)


def test_fts_metacharacters_are_plain_text_not_executable_syntax(corpus):
    expected = search(corpus, "callback")["results"]
    assert search(corpus, '"callback" () : ***')["results"] == expected
    assert search(corpus, 'callback"; DROP TABLE chunks; --')["results"]
    assert search(corpus, "callback")["results"] == expected


def test_limits_snippets_deduplication_and_determinism(corpus):
    a = search(corpus, "authentication", limit=2)
    b = search(corpus, "authentication", limit=2)
    assert len(a["results"]) == 2 and a["results"] == b["results"]
    assert len({(h["target"], h["line"]) for h in a["results"]}) == len(a["results"])
    assert all(len(h["snippet"]) <= retrieval.SNIPPET_CHARS for h in a["results"])


def test_empty_corpus_has_valid_stats_and_no_results(corpus):
    repo, state, cache = corpus
    commit = repo.write(state["baseline"], {p: None for p in repo.files(state["baseline"]) if p.startswith("docs/")}, "Remove docs")
    repo.git("update-ref", "refs/heads/main", commit)
    result = search(corpus, "callback")
    assert result["results"] == [] and result["index"]["documents"] == 0 and result["index"]["chunks"] == 0


def test_force_index_has_no_workflow_or_source_mutation(corpus):
    repo, state, cache = corpus
    before_state, before_ref = copy.deepcopy(state), repo.resolve("refs/heads/main")
    before_status = repo.git("status", "--porcelain")
    first = context.index(repo, state, cache_root=cache)
    second = context.index(repo, state, cache_root=cache, force=True)
    assert first["index"]["fingerprint"] == second["index"]["fingerprint"]
    assert second["index"]["status"] == "rebuilt"
    assert state == before_state and repo.resolve("refs/heads/main") == before_ref
    assert repo.git("status", "--porcelain") == before_status
