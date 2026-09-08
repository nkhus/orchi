# Knowledge authority

| Role | Meaning |
| --- | --- |
| Core | Published current system under docs/ |
| Intent | Exact accepted requirements, target architecture and target decisions |
| Epic Design | Exact detailed design of the selected epic |
| Working Knowledge | Last verified checkpoint's sparse Current overlay |
| Evidence | Checks, review, observations, proposals and acceptance; never automatically Current |

Current(initiative) = accepted integration-base Core + verified Working overlay. Original baseline remains provenance; it does not have to equal the accepted integration base after a checked sync. Target = exact accepted Intent. All preserves both roles. Canonical defaults to Current; greenfield may start with empty Current.

Replacement/retirement masks the logical Core target first. Stale Working never falls back to obsolete Core. `knowledge_head` remains the last checked checkpoint while `head` advances through tasks. Explicit code sources use task dispatch snapshots; partial implementation is not a reason to publish premature Core.

Search discovers; exact reads bind role, source commit/path/hash. On-demand task sources remain bound even when fetched later. Target requirements are not proof the behavior exists. Workers can return observations and proposed documentation; those stay Evidence until reconciled at a verified checkpoint/final boundary.

Original `intent/source.md` is immutable provenance and excluded from Target search. Accepted revisions retain source and completed history; only the current accepted Intent is Target. A past epic may refer to a reorganized historical Target node without making it effective again. Future roadmap references must resolve to the currently accepted Target.

At sync, reconcile both upstream code and affected Core/Working. A Working replacement cannot hide a new upstream edit through an automatic overlay or revalidation shortcut. Prospective code/knowledge is not Current before checks/review/signature. A required Target revision blocks later design/finalization.

At finalization, dispose every requirement/architecture/Working node and author Core from actual implementation. Archive Target/Working/evidence outside Core. Exact final attestation is exported as sidecars; preserve the export for full replay. `views --out /new/external/path` creates a read-only IDE projection, not editable authority.

Use [ontology](ontology.md), [retrieval](retrieval.md), [bootstrap](bootstrap.md) and [synchronization](synchronization.md). Ontology cannot assign authority roles or invent another document lifecycle.
