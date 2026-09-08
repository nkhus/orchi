# Knowledge curation and graph

Search before creating a new node; edit the authoritative existing node when possible. Classify load-bearing documents and link them to meaningful neighbors/implementation paths. Maintain area README/index entry points. Do not invent implemented facts to complete a graph.

```yaml
---
kind: component
area: orders
artifacts: [src/orders/**]
relations:
  depends_on: [docs/reference/events.md]
  relates_to: [docs/orders/idempotency.md]
---
```

Kinds: `index`, `component`, `reference`, `decision`, `runbook`, `guide`, `requirements`, `architecture`. Use `architecture` only for accepted target architecture; Core architecture uses `component`/`reference`. No author-written `role`, `view`, `layer`, `authority`, `current`, `target`, `status` or `lifecycle` fields are allowed.

Relations: `depends_on`, `relates_to`, `part_of`, `documents`, `implemented_by`, `addresses`, `realizes`, `verified_by`. Knowledge targets are logical document paths/anchors or registered requirement IDs. Implementation relations use safe repo-relative paths/globs. Known `evidence:<id>` references can support claims; a string or link alone does not prove verification.

Requirements use `kind: requirements`, a metadata `requirements: [req-example]` list and a matching `<a id="req-example"></a>` or heading. IDs are stable across reorganizations and unique within accepted Intent. Epic Design declares selected `addresses`/`realizes` links. Roadmap-derived graph edges need not be duplicated in Markdown.

Run `lint --initiative <id> --view all` after accepted changes. Plain incidental Markdown may lack kinds initially; load-bearing metadata, accepted Target/design and changed final Core require known kinds. Broken links/anchors, invalid relation names, unsafe artifact paths and authority fields are errors. Unmatched planned Target artifacts and orphan pages are warnings. Areas with multiple direct pages need a README/index; changed final areas enforce that rule.

Lint resolves explicit cross-view links only within the same initiative. A single-view graph does not pull excluded nodes into scope to satisfy a link; use `all` for cross-view navigation. Graph authority is resolved before projection, so obsolete Core relationships disappear with replaced/retired nodes.

`related <target> --relation <type> --depth 1 --direction both` explores typed neighbors. `map --view all` creates a self-contained HTML navigator; `map --format json` returns structured nodes/edges. Graphs are rebuilt in memory and outputs are disposable, confidential context. They are not an authoring database or permission to change canonical docs.

`coverage --initiative <id>` derives traceability from accepted contracts, closed checkpoints and final evidence. Planned/implemented links are not semantic proof. Requirement-document changes conservatively mark old implementation bindings stale; final satisfied dispositions need registered checks actually executed on the candidate.
