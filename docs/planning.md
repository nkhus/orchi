---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/authoring.py
  - skills/orchi/scripts/orchi_core/preflight.py
  - skills/orchi/scripts/orchi_core/models.py
relations:
  part_of: [docs/README.md]
  depends_on: [docs/knowledge-model.md]
---
# Planning and proportionate authoring

Depth follows uncertainty and consequences, not line count. A one-line authorization change can require a substantial design. An existing-interface fix can use a short architecture/no-change statement rather than inventing a new subsystem.

## Intent and compact briefs

A ChangeBrief contains exact original request, stable `req-*` outcomes, architecture or no-change statement, selected design, fixed decisions, invariants, registered checks and bounded tasks. `brief-expand` writes ordinary authoring files without accepting them; `start` requests one initial direction-and-plan gate. Expansion is deterministic. It does not infer requirements, choose architecture or configure checks.

Use normal `begin` for a larger roadmap. Intent Markdown and its manifest bind requirements and target architecture to exact bytes. Original request text is immutable. Requirements may evolve only through accepted revisions; removed IDs have explicit dispositions and are not reused.

## Epic as a verified result

An epic is the nearest jointly integrable, verifiable result. It is not necessarily an entire horizontal layer. Design against the actual accepted code head, latest verified Working Knowledge and accepted Target. Resolve the common interface before parallel frontend/backend or producer/consumer implementation. A future implementation is not an available dependency output.

Task DAG dependencies express required producer results. Ontology `depends_on` expresses a knowledge relationship; it is not automatically a scheduler dependency. Each dependency source names a producer and contract and is materialized only after that producer integrates.

## Bounded execution decisions

Every task declares outcome/acceptance, current-state interpretation, approach, fixed decisions, invariants, delegated local choices, failure modes, initial exact edits, sources, verification and escalation. Implementation requires edits; investigation forbids product edits and later returns observations. Unresolved material design questions block execution. Bounded research is allowed as an explicit outcome, not as a blank authorization to improvise architecture.

Initial edits are commitments. Optional `write_scope` rules declare exact directories, allowed actions and named `allowed_choices`. A worker can acquire a technical addition inside that envelope after mechanical conflict checks. Folder membership does not prove semantic permission; a new public API, persistence/security boundary or requirement must be escalated even inside an allowed directory. Protected paths remain protected.

## Context and preflight

Sources declare explicit Current/Target views, inline/on-demand delivery and fixed/snapshot consistency for implementation observations. Mandatory write before-images and applicable instructions retain fixed hashes. Ownership does not add hidden read locks. The packet binds a source manifest; exact additional reads use the dispatch snapshot rather than the latest branch.

Preflight detects known source failures and oversized packets before approval. Missing outputs of declared dependencies are explicitly deferred. Runtime checks repeat after dependencies exist, and repair/handoff context still counts toward the packet limit. Preflight does not promise future tool/service availability or semantic plan success.

## No-code and existing-work entry points

A `knowledge-only` epic has no tasks and uses checks/review/checkpoint to reconcile documentation. A task `kind: investigation` can investigate without writing product files; observations and proposed documentation remain Evidence until separately verified and accepted as knowledge. A final non-software architecture disposition can be `not-applicable` only for an accepted knowledge/investigation outcome with candidate checks. An unchanged software architecture still cites existing artifacts and checks.

For an existing branch, first accept the actual outcome/design. Claim and activate the task, then import its exact approved diff. Never fabricate historical approvals or call an existing branch already verified merely because it was produced outside Orchi.
