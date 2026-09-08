---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/ontology.py
  - skills/orchi/scripts/orchi_core/graph.py
relations:
  part_of: [docs/README.md]
---
# Ontology and graph


## Metadata contract

```yaml
---
kind: component
area: orders
artifacts:
  - src/orders/**
relations:
  depends_on:
    - docs/reference/events.md
  relates_to:
    - docs/orders/idempotency.md
---
```

Kinds: `index`, `component`, `reference`, `decision`, `runbook`, `guide`, `requirements`, `architecture`. Accepted target architecture uses `architecture`; implemented Core architecture uses `component` or `reference`. There is no draft/active/deprecated documentation state machine. `role`, `view`, `layer`, `authority`, `current`, `target`, `lifecycle` and `status` cannot override controller authority.

Authored relations: `depends_on`, `relates_to`, `part_of`, `documents`, `implemented_by`, `addresses`, `realizes`, `verified_by`. Document relations accept logical `docs/...` / `intent/...` references, relative paths, anchors and registered requirement IDs. `documents` and `implemented_by` point to implementation paths/globs. `verified_by: [evidence:<id>]` resolves only against known controller evidence; arbitrary labels do not establish proof.

Typed links cannot cross into another initiative. Explicit same-initiative cross-view links are checked by lint against both views, but a graph never imports an out-of-view node merely to complete an edge. Such an edge yields a diagnostic; use `--view all` when cross-view navigation is needed.

## Curation and lint

Search before creating documents; prefer updating the existing authoritative node. Classify load-bearing pages, declare meaningful ownership, add typed links and maintain area entry points. Plain incidental Markdown can be adopted gradually: missing kind is initially a warning, while metadata-bearing pages, accepted Target/Epic Design and newly replaced final Core require a known kind.

The linter checks safe frontmatter, kinds, authority fields, artifact patterns, requirement anchors, typed relationships, Markdown links and area indexes. YAML duplicate keys and aliases are rejected. Anchors include heading slugs and explicit HTML IDs; Markdown code fences are excluded from link scanning. This is a deliberately small Markdown parser, not complete rendering of every extension.

An area containing at least two direct Markdown children needs `README.md` or an `index` node. Missing area indexes are warnings during bootstrap; changed final areas enforce the rule. Orphans are warnings. Target artifact paths need not exist yet and generate warnings rather than fabricated implementation facts. Existing obsolete status-marked pages remain excluded from ordinary retrieval but are visible to lint for correction.

## Graph construction

The graph is a deterministic in-memory projection built after Current/Target authority resolution. It includes readable document/anchor nodes, target requirements, roadmap epics, implementation artifacts and trusted evidence as applicable to the view. Retired or stale Current nodes are removed before projection. A replacement contributes its own relationships rather than inheriting the obsolete Core edges.

Authored edges, area hierarchy, declared ownership and workflow contracts produce the graph. Controller edges include requirement `addressed_by` epic, epic `realizes` architecture, and closed epic `implemented_by` artifacts / `verified_by` checks. Planned target artifacts are visibly Target nodes, not evidence that a file exists. Explicit final reconciliation adds verified realization links when exact candidate checks pass.

`related` provides deterministic breadth-first traversal, depth 1-3, limit 1-100, relation filters and incoming/outgoing/both directions. `map --format json` returns the graph. `map` writes a self-contained SVG/HTML navigator with role-distinct nodes, searchable labels and provenance. The display bounds rendered nodes while retaining full graph data; narrow a large graph with search. No external scripts or network access are required. Map output is derived confidential repository data and must stay outside tracked authority paths.

## Coverage is not semantic proof

`coverage --initiative <id>` derives planned/implemented/verified or unresolved disposition from the accepted registry, roadmap, closed checkpoints and final reconciliation evidence. Planned means an epic addresses the requirement. Implemented means a relevant closed epic is still bound to the accepted requirement document. Verified requires a satisfied final disposition and passing registered checks on the exact candidate. The final review and approval gates remain necessary.

Changing a requirement document invalidates previous document-hash bindings conservatively, even if only a neighboring requirement changed. Removed IDs retain accepted resolutions. Coverage never infers satisfaction from search similarity or the presence of an `implemented_by` label. Architecture coverage is document-level; semantic completeness of component boundaries, acceptance conditions and target deviations remains a reviewer responsibility.
