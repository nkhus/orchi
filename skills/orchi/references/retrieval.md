# Retrieve project knowledge

Search discovers relevant sections; `get` reads authoritative content. Neither command advances the workflow.
Read documentation in the correct scope before inspecting the exact affected code. Do not use snippets as a
replacement for task sources, evidence, requirements, or approvals.

## Commands

`<orchi>` below means `uv run <skills>/orchi/scripts/orchi.py`.

```bash
# Published Core, using the controller's canonical ref.
<orchi> --control "$ORCHI_CONTROL" search "authentication callback" --limit 8
<orchi> --control "$ORCHI_CONTROL" get docs/authentication.md --content-hash <hash-from-hit>
<orchi> --control "$ORCHI_CONTROL" owners src/authentication.py

# Explicit initiative scope: baseline Core plus verified Working Knowledge.
<orchi> --control "$ORCHI_CONTROL" search "authentication callback" --initiative <id>
<orchi> --control "$ORCHI_CONTROL" get docs/authentication.md --initiative <id> --content-hash <hash-from-hit>
<orchi> --control "$ORCHI_CONTROL" owners src/authentication.py --initiative <id>

# Optional prebuild, diagnostics, and disposable-cache recovery.
<orchi> --control "$ORCHI_CONTROL" index --initiative <id>
<orchi> --control "$ORCHI_CONTROL" stat --initiative <id>
<orchi> --control "$ORCHI_CONTROL" index --initiative <id> --force
```

Use concrete terms, identifiers, or a short phrase. Input is plain text, not an FTS expression.
Token/prefix BM25, substring matching, and four-character-window fuzzy candidates are combined.
Fuzzy candidates must also pass word-similarity filtering. This is lexical retrieval, not semantic or
cross-language search. Exact token/prefix queries can be short; substring matching needs three characters.
Fuzzy matching is heuristic and does not correct every possible typo.

Default output is JSON. Use `--format text` for a human-readable `target:line-end_line`, heading, snippet,
and source identity. The default limit is 8 section hits; `--limit` accepts 1-100. A file can have several
hits for different sections. Duplicate hits for the same section are merged. Refine a broad query instead
of loading the whole knowledge base.

## Read in the same scope

Inspect `diagnostics` even when there are hits. Stale replacements stay masked and produce
`STALE_WORKING_KNOWLEDGE`; no fallback to older Core is allowed. Retired entries are not searchable.
An unknown initiative fails. During an active epic, Working Knowledge still describes the last checkpoint,
not partial task results. Apply approved active-epic changes and actual dependency outputs separately.

Each hit identifies the logical `target`, original `source_path`, exact `source_commit`, `content_hash`,
`layer`, heading hierarchy, and source line range. Line numbers refer to the indicated source, including
its frontmatter, not necessarily the canonical working-tree file. Read the logical target with `get` in
the same scope. `--content-hash` rejects changed text with `KNOWLEDGE_CHANGED`; search again in that case.
A revalidation can change evidence while retaining the same text hash; `get` returns its current provenance.

Use the resulting logical paths in task `knowledge` references. The packet builder independently resolves
and embeds full exact sources. It never reads SQLite search rows or treats a ranking score as authority.
`owners` remains a direct metadata lookup, not a text-search heuristic.

## Standalone Core lookup

No initiative, operator key, or controller setup is required to search published documentation:

```bash
# Run with ORCHI_CONTROL unset; do not mix --repo and --control.
<orchi> search "authentication callback" --repo .
<orchi> get docs/authentication.md --repo . --content-hash <hash-from-hit>
<orchi> owners src/authentication.py --repo .
<orchi> stat --repo .
```

The default canonical ref is `refs/heads/main`. Use `--ref refs/heads/trunk` (or the project's actual
canonical ref) on every standalone command when it differs. This reads committed Core, never dirty files.
Standalone mode rejects `--initiative`; an initiative requires its controller's accepted state.

## Cache and runtime

Search, `index`, and `stat` automatically ensure a matching projection. It lives under
`$ORCHI_CONTROL/cache/retrieval/`, or `orchi-retrieval/` inside the worktree's Git directory in standalone
mode. It contains derived document text and must have repository-appropriate access controls. Do not
commit, authorize from, or manually curate it. Removing the retrieval directory is safe; deleting controller
state or the whole Git directory is not.

The cache is bound to repository identity, canonical commit or initiative baseline, knowledge checkpoint,
manifest, readable source hashes/provenance, and retrieval implementation. It is atomically replaced,
not migrated. A corrupt cache is rebuilt; unavailable cache storage uses an in-memory projection.
Python's SQLite must support FTS5. Missing trigram support disables substring/fuzzy matching with an
explicit warning; `doctor` reports capabilities. No embeddings, external service, or additional package
is required for retrieval. `get` and `owners` do not require a search index.
