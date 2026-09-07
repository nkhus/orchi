# Documentation retrieval

## Authority before relevance

Retrieval is a projection of effective knowledge, not a second knowledge store. The resolver selects an
immutable view before any text is indexed:

```text
Canonical scope: current canonical Core
Initiative scope: baseline Core + verified replacements - retired/stale targets
                                  |
                          resolved knowledge snapshot
                                  |
                       disposable SQLite section index
                                  |
                   BM25 + substring + fuzzy candidates
                                  |
                  ranked source-bound headings and excerpts
                                  |
                     exact get / task-source resolution
```

Only readable `docs/**/*.md` records from the selected view enter the index. Canonical discovery retains
the context resolver's lifecycle, status, unsafe-file, secret-path, frontmatter, and text checks. Proposals,
archives, task observations, arbitrary repository Markdown, and other initiatives do not enter the view.
An index must not independently walk the filesystem or infer document authority from relevance.

`context.py` owns authority, scope, freshness, ownership, and task materialization. `retrieval.py` accepts
resolved snapshots and owns section extraction, disposable cache management, ranking, and excerpts.
Neither indexing nor searching changes controller state, approvals, accepted commits, or Core documents.

## Sections and ranking

Sections follow ATX and Setext headings and retain their heading hierarchy. YAML frontmatter is not body
search content. Fenced-code headings do not create sections. Source line ranges include frontmatter and
are 1-based and inclusive. Long sections split at line boundaries after 100 lines or approximately 8,000
characters; an indivisible long line can exceed the character target. This is focused section extraction,
not a full Markdown renderer.

The searchable fields are logical path, document title, heading hierarchy, and body. Token/prefix matching
uses SQLite FTS5 with `unicode61` and BM25 field weights of 1.5, 2, 4, and 1 respectively. A trigram channel
finds substrings. A fuzzy channel retrieves shared four-character windows, then requires sufficient window
coverage and a word-level similarity check. Normalization casefolds Unicode, normalizes compatibility
characters, and folds Latin accents. Original source text is retained for result excerpts.

Candidate sets are combined by weighted reciprocal-rank fusion: BM25 weight 1, substring weight 0.6, fuzzy
weight 0.3, and denominator `60 + rank`. Results sort first by matched query-term count, then fused score,
then logical path and line. Raw BM25 scores from different tokenizers are not compared directly. A score
is a local relevance heuristic, not confidence, verification, or proof that a document is complete.

Queries are plain text, not executable FTS syntax. Tokens are quoted and MATCH expressions are bound
parameters. Limits are 512 query characters, 16 distinct terms, 64 characters per term, and 1-100 results
(default 8). Each channel considers at most `max(64, 8 * result_limit)` candidates. This is bounded retrieval,
not an exhaustive repository scan or a semantic/cross-language search engine. Short token/prefix matches
work; substring matching requires at least three characters. Typo recovery is heuristic, not guaranteed.

## Result and read contract

The default CLI response preserves the JSON `ok/result` envelope. Search results include:

| Field | Meaning |
| --- | --- |
| `target`, `layer` | Logical documentation path and selected authority layer |
| `source_path`, `source_commit`, `content_hash` | Original source location, immutable Git commit, and SHA256 of complete text |
| `title`, `heading`, `heading_path` | Document title and section context |
| `line`, `end_line` | Inclusive source section range |
| `snippet`, `snippet_line` | At most 280 characters from an original source line and that line's number |
| `via`, `matched_terms`, `score` | Matching channels, term coverage, and fused relevance |

Hits for the same source section are merged; different sections of one document can appear separately.
`scope`, `snapshot`, `index`, and `diagnostics` accompany the results. `truncated` indicates additional
accepted candidates beyond the returned limit; it is not an exhaustive total-hit count. A false value does
not establish that the bounded candidate pools covered every possible match. Human-readable output is
available through `--format text`; JSON remains the agent protocol.

Cache rows propose candidates only. Returned section text and provenance are checked and reconstructed
against the freshly resolved source records. Read a hit with `get <target>` in the same scope; supplying
`--content-hash` rejects changed content with `KNOWLEDGE_CHANGED`. The resulting read exposes current
provenance even when a revalidation retains identical text. Search and read are separate snapshots, not
a transaction spanning commands. Task packets independently bind their full exact sources and start state.

Ownership remains a direct `artifacts`-metadata lookup. A search match is not an ownership declaration,
and no search hit is not evidence of no documentation impact.

## Disposable cache

Controller-backed projections live at `$ORCHI_CONTROL/cache/retrieval/<scope-digest>.sqlite`.
Standalone projections live under `orchi-retrieval/` in the worktree's Git directory. Both locations stay
outside the tracked project tree. The cache contains document text; protect it like other repository data.
Do not put it in task packets or export it as authoritative audit evidence.

One cache file is replaced per repository/scope identity. Its fingerprint includes the resolved canonical
commit or initiative baseline, knowledge checkpoint and revision, full knowledge-manifest digest, and
readable document hashes and provenance. The implementation's source digest, linked SQLite build, and
available tokenizers are also checked for reuse. There is no product release counter or index migration.

Every request resolves the authority view and checks working-artifact freshness before considering cache
reuse. This includes reading authoritative documentation; the cache accelerates matching, not authority
validation. An active epic's code `head` does not invalidate the last verified knowledge view merely because
some tasks have integrated. A knowledge checkpoint, revalidation, retirement, stale artifact, or canonical
publication does invalidate the corresponding projection.

Search, `index`, and `stat` build or refresh as needed. `index --force` forces rebuilding. Builders write to
a temporary file and publish with atomic replacement; a reader keeps its own snapshot connection during
concurrent builds. Corrupt, missing, incompatible, or candidate-mismatched indexes are rebuilt. If cache
storage is unavailable or unsafe, retrieval uses an in-memory projection and reports a diagnostic.
Deleting only the retrieval cache is safe. Controller state, audit artifacts, and Git are not disposable.

Python's linked SQLite must have FTS5. Missing FTS5 raises `FTS5_UNAVAILABLE`; `get` and `owners` remain
usable. Missing trigram support keeps token/prefix BM25 and reports `TRIGRAM_UNAVAILABLE` rather than
silently claiming substring or fuzzy matching. `doctor` checks these capabilities. Retrieval adds no
third-party Python dependency, service, embeddings, model call, or runtime network request.

## Use from an installed skill

The complete command procedure is bundled in [the retrieval reference](../skills/orchi/references/retrieval.md).
It covers controller-backed scope, standalone canonical reads, exact readback, and cache diagnostics.
Standalone mode defaults to `refs/heads/main`; select the project's canonical ref explicitly when different.
Do not mix standalone `--repo` with `--control`, `ORCHI_CONTROL`, or initiative scope.
