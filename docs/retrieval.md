---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/retrieval.py
  - skills/orchi/scripts/orchi_core/context.py
relations:
  part_of: [docs/README.md]
---
# Authority-first retrieval


## Resolve, search, read

```text
scope + view -> effective authority snapshot -> lexical index
                                          -> typed graph
lexical primary matches + separate structural neighbors -> exact Git read
```

Canonical access reads committed `docs/` at the configured branch. Initiative Current reads the accepted integration base plus last verified Working overlay; Target reads the accepted Intent Git commit. `all` preserves both roles. No dirty local proposal, active partial implementation or other initiative is silently indexed as documentation authority.

Search preserves heading-aware SQLite FTS5 BM25/token-prefix matching, trigram substring retrieval and bounded fuzzy candidates with word-similarity filtering. Queries are plain text, not raw FTS syntax. This is lexical search, not embedding-based semantic or cross-language retrieval. Missing SQLite trigram support explicitly disables substring/fuzzy paths; `doctor` reports availability.

## Commands

The following assumes the installed entrypoint is available as `orchi` through the operator guide's shell function:

```bash
orchi search "idempotency" --initiative feature --view all
orchi search "orders" --initiative feature --view target --kind architecture --related-limit 6
orchi get req-order-idempotency --initiative feature --view target --content-hash <hash>
orchi get docs/orders.md --initiative feature --view current --content-hash <hash>
orchi related req-order-idempotency --initiative feature --view all --relation addressed_by
orchi owners src/orders/service.py --initiative feature --view current
orchi lint --initiative feature --view all
orchi map --initiative feature --view all
orchi coverage --initiative feature
```

For standalone Current, omit control and initiative and pass `--repo .`; canonical defaults to `refs/heads/main`, with `--ref` for another exact ref. Standalone Target is invalid. Controller-backed and standalone modes must not be mixed.

Search filters include `--view`, `--kind` and `--area`. `--limit` bounds primary section hits to 1-100 (default 8). `--related-limit` is 0-100 (default 8); zero disables graph expansion. `--relation` restricts structural neighbors. Filters on kind/area constrain primary matches; related context can include differently classified connected knowledge within the selected authority view.

## Output and exact source binding

`primary_matches` contains lexical section hits; `results` is the same primary list. `related_context` contains graph neighbors with explicit distance/edge provenance and no lexical relevance score. A structural neighbor must never be described as a matching search result. Deterministic graph traversal is independent of lexical ranking.

Every readable hit includes target, role/layer, kind/area when declared, source commit/path, SHA256 and authority revision where applicable. Primary matches additionally carry heading hierarchy, bounded snippets and source line ranges including frontmatter. One document may have multiple section hits.

Inspect diagnostics first. Stale replacements stay masked and exact reads fail; retired targets are absent. `get` resolves again and verifies the optional content hash. Requirement aliases and anchors select an addressable source; exact read returns the complete document with the requested anchor identity, not a cached snippet. A revalidation can retain identical text while changing evidence; always inspect returned provenance.

Tasks use explicit `knowledge` sources with `view: current` or `view: target`. The packet builder rereads accepted Git sources independently of any search cache and includes complete required content. If a packet exceeds policy size, split or refine the accepted plan rather than truncating mandatory context.

## Projection lifecycle

The index fingerprint includes authority identity, view, selected filters, accepted Intent digest, Working revision, source contents/provenance, ontology implementation and retrieval implementation. Search, `index` and `stat` ensure a matching projection; `index --force` explicitly rebuilds it. Cache corruption or a mismatched cached chunk triggers rebuild; unavailable cache storage falls back to memory.

Controller caches use `$ORCHI_CONTROL/cache/retrieval/`; standalone caches live under the worktree's Git metadata. Graphs are rebuilt in memory, with only requested HTML/JSON outputs written. Delete projections freely, never the controller store or Git source objects. Caches and maps contain private repository context and need appropriate access controls.
