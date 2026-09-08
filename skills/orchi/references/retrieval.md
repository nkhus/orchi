# Authority-first retrieval

Use `search -> inspect role/provenance and diagnostics -> exact get -> related when useful`.
Search snippets are discovery aids, not task contracts, current facts, evidence or acceptance.

`<orchi>` means `uv run <skills>/orchi/scripts/orchi.py`; add `--control "$ORCHI_CONTROL"` before the command for controller access.

```bash
# Committed canonical Core without a controller; ORCHI_CONTROL must be unset.
<orchi> search "authentication callback" --repo . --format text
<orchi> get docs/authentication.md --repo . --content-hash <hash>

# Explicit accepted initiative knowledge.
<orchi> --control "$ORCHI_CONTROL" search "authentication" --initiative feature --view all
<orchi> --control "$ORCHI_CONTROL" search "callback" --initiative feature --view target --kind architecture
<orchi> --control "$ORCHI_CONTROL" get req-authentication --initiative feature --view target --content-hash <hash>
<orchi> --control "$ORCHI_CONTROL" get docs/authentication.md --initiative feature --view current --content-hash <hash>
<orchi> --control "$ORCHI_CONTROL" related req-authentication --initiative feature --view all --relation addressed_by
<orchi> --control "$ORCHI_CONTROL" owners src/authentication.py --initiative feature --view current
<orchi> --control "$ORCHI_CONTROL" map --initiative feature --view all
<orchi> --control "$ORCHI_CONTROL" lint --initiative feature --view all
<orchi> --control "$ORCHI_CONTROL" coverage --initiative feature
```

Current is canonical Core or baseline + last verified Working. Target is accepted requirements/architecture/decisions. All preserves both roles. A canonical query does not expose active Intent. Standalone Target and unknown/other initiative IDs fail; `--repo` cannot be combined with controller access. Standalone canonical defaults to `refs/heads/main`; use `--ref` consistently for a different branch.

## Read results correctly

`primary_matches` (also `results`) are lexical matches. `related_context` contains structural neighbors, not additional lexical matches and not proof of relevance. Read every result's `role`, `layer`, logical target, source commit/path, SHA256 and revision identity. Working freshness is against the last checkpoint; partial active code and accepted dependency outputs are separate sources.

Use `get` in the same initiative/view, preferably with the returned content hash. It returns exact complete source bytes and anchor identity, independently of the cache. A hash mismatch requires rediscovery. Stale Working remains masked and reports `STALE_WORKING_KNOWLEDGE`; never substitute obsolete Core. A retired node is not readable. Original `intent/source.md` is provenance, not default Target search content.

Tasks declare `kind: knowledge`, explicit `view: current|target`, logical path/requirement alias and reason. The packet builder rereads full exact sources, adds selected accepted Target and Epic Design, and fails rather than truncating mandatory context. A graph edge or ranking score does not authorize worker read scope.

## Bounded discovery

Queries are plain text. Heading-aware BM25/token-prefix, trigram substring and filtered fuzzy candidates are lexical heuristics, not semantic or cross-language retrieval. Default primary limit is 8, configurable 1-100; a document can have several section hits. `--kind`/`--area` filter primary matches, while neighbors may cross those classifications within the selected view. `--related-limit 0` disables graph expansion; otherwise it is bounded to 100. `--relation` restricts structural neighbors.

`related` supports incoming/outgoing/both traversal, depth 1-3 and limit 1-100. `map --format json` exposes deterministic graph data; ordinary `map` writes self-contained HTML outside tracked authority. Use [ontology](ontology.md) for relation and lint conventions.

## Disposable projections

`index`, `stat` and search ensure a projection for the exact authority/view/filter identity. `index --force` rebuilds. Cache fingerprints include accepted Intent, Working checkpoint, source hashes/provenance and implementation signatures. Corruption rebuilds automatically; unavailable cache storage falls back to memory. Graphs are rebuilt in memory rather than stored as authoritative state.

Controller FTS caches live under `$ORCHI_CONTROL/cache/retrieval/`; standalone caches live in Git metadata. Delete only derived outputs, never the store or Git objects. These files/maps contain private source context. FTS5 is required; missing trigram disables substring/fuzzy behavior with a warning. `get` and direct ownership lookup do not need a search index.

## Ticket reads and human projections

Task on-demand sources retain exact role, commit/path and full-source hash. Additional `ticket-read` calls bind the dispatch authority snapshot, not latest main. Line slices include a separate slice hash. Foreground workers use the ticket-only `worker_request.py` channel instead of control-store access. An explicitly selected snapshot code observation is not a fixed equality assumption; drift is recorded and compatibility checked.

`views --out /new/external/path --view current|target|all` creates immutable, read-only IDE files and a provenance manifest. Regenerate after accepted checkpoint/sync/Target changes; do not edit or commit the derived tree. `get` remains a full exact knowledge read; line slicing is exposed through ticket-read.
