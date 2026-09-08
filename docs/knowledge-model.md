---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/context.py
  - skills/orchi/scripts/orchi_core/intent.py
  - skills/orchi/scripts/orchi_core/views.py
relations:
  part_of: [docs/README.md]
  depends_on: [docs/synchronization.md]
---
# Knowledge authority

## Roles

**Core** is canonical current-state documentation under `docs/`. This initiative does not edit it during task/epic execution. Other accepted canonical deliveries may change it; this initiative adopts their new Core only through accepted sync.

**Intent** is accepted Target: immutable original request, stable requirements, target architecture and decisions bound by a manifest and signed initiative identity. It is not implemented reality. Revision history preserves previous accepted snapshots.

**Epic Design** is exact detailed implementation design for the selected epic, stored as revisioned Markdown and bound by the executable plan's hash. It is neither general Target nor verified Current.

**Working Knowledge** is a sparse verified overlay at the last closed checkpoint. `replace` masks and replaces a logical Core document; `retire` masks it; `revalidate` establishes a checked assertion's continued applicability. It never describes partial active-epic progress as verified Current.

**Evidence** is check output, review, observations, proposed documentation, process records and acceptance. Evidence supports claims but is not current-state or target documentation. Task documentation proposals can be drafted early and promoted only after checkpoint/final reconciliation.

## Views and provenance

```text
canonical Current = actual published Core
initiative Current = accepted integration-base Core + verified Working overlay
initiative Target = exact accepted Intent
all = Current + Target, with roles preserved
```

A greenfield baseline may contain no Core. Target remains searchable and exact before code exists. A stale/retired Working entry masks obsolete Core rather than falling back. Every exact read exposes source commit/path/hash and role. Search and graph are derived after resolution; snippets and graph proximity do not override authority.

`head` may advance while an epic executes; `knowledge_head` does not. Task code reads bind the dispatch head, while Current comes from the verified knowledge snapshot. Target and the accepted design have their own exact source commits. An additional ticket read never accidentally resolves against latest canonical.

## Synchronization

The original baseline remains provenance even after sync. A prospective sync cannot update Current before checks/review/signature. The controller reconciles affected Core/Working claims against new upstream and records exact old/new identities. Fresh code alone does not justify rebasing the overlay mechanically. See [synchronization](synchronization.md).

## Authoring and human access

Search before creating nodes; prefer updating an existing authority over duplicating it. Use known kinds, valid typed relations, anchors and area indexes. Keep future-state claims out of Core and verified Current; don't turn implementation observations into Target decisions implicitly.

`views --out /new/external/path --view all` materializes exact read-only files under separate `current/` and `target/` directories with a provenance manifest. These are disposable snapshots for an IDE. Their filesystem read-only flag is convenience, not a sandbox. Regenerate into a new directory after a checkpoint/sync/revision; never edit or commit them as authority.

## Final Core

Finalization reconciles each accepted requirement, target architecture document and Working disposition. Core is authored from checked implementation, not copied from Target prose. The active subtree is archived. Archived Intent, task proposals and observations remain provenance; canonical retrieval does not treat them as competing Current documentation.
