# Orchi development workflow implementation plan

## Accepted direction and delivery boundary

The deliverable is a complete installable source pack, not an add-on patch. The design inputs are the supplied Target Vision, Target Implementation Plan, target ZIP, and the subsequent accepted development-flow review. Preserve the knowledge authority model and progressively designed epics. Make the same workflow practical for bounded fixes, research, knowledge work, large software initiatives, humans and agents, and a moving shared Git target.

Atomic initiative is the supported delivery contract: all of this initiative's code and Core are reconciled at its final publication boundary. Other initiatives may publish independently. An initiative does not freeze the repository. Incremental publication of portions of a single request is deliberately not enabled; that would change the agreed authority contract. Deployment, distributed transactions across repositories, and a universal cloud scheduler are not implied by publication.

The original baseline is immutable provenance. The accepted integration base can advance only through an exact, reviewed, checked, human-approved synchronization. Working Knowledge is composed against that accepted base, never blindly layered onto a newer canonical branch.

## Workstream 1 — Contracts and proportionate authoring

**Outcome:** One execution model can be authored at different levels of detail without weakening acceptance.

1. Add a compact change brief with the user's request, stable requirements, architecture/no-change statement, selected design, decisions, invariants, trusted check IDs and bounded tasks.
2. Expand the brief deterministically into normal Intent, initiative and Epic Plan contracts. Do not infer missing requirements, choose tools, or invent implementation facts.
3. Provide a combined initial direction-and-first-epic approval for the exact same initial product snapshot. Keep final approval independent.
4. Distinguish software, knowledge and investigation outcomes. Investigations produce observations/evidence, not product edits. A documentation-only epic needs no fake coding task.
5. Keep one active epic and a task DAG. Parallel branches share accepted interfaces; task dependencies reference exact producer outputs.
6. Introduce explicit inline/on-demand source delivery, fixed/snapshot assumptions, bounded write envelopes and delegable local choices.
7. Reject unresolved material decisions; permit bounded investigation and explicitly delegated local implementation choices.

**Acceptance:** Contract/schema tests; compact single-gate flow; unchanged-architecture fix; read-only investigation; documentation-only publication; invalid scopes and unsupported incremental delivery fail explicitly.

## Workstream 2 — Snapshot context and scope

**Outcome:** Context is exact and navigable without becoming a coarse locking system.

1. Remove ontology artifacts/ownership from scheduler locks and hard read assumptions. Keep ownership for navigation and checkpoint impact analysis.
2. Keep exact write ownership and true shared resource reservations. Reading an immutable snapshot does not reserve other workers' files.
3. Build bounded packets with a source manifest. On-demand sources retain commit, path, hash, role and delivery metadata.
4. Add ticket-scoped exact reads, including source sections/line ranges, against the dispatch snapshot. Never resolve an additional read against the latest branch accidentally.
5. Record fixed read assumptions separately from snapshot observations. Changed fixed assumptions reject integration; snapshot observations trigger broad compatibility revalidation and remain visible to review.
6. Add a scope-acquisition operation bounded by the approved directory/action/choice envelope. Reject protected paths, another task's output, and semantic design/target changes. Return newly applicable instruction sources.
7. Preflight known packets and sources before approval. Mark future dependency outputs as deferred, not guaranteed. Repeat runtime validation.
8. Generate read-only Current/Target trees with exact manifests outside the repository authority tree. Never commit derived views as documentation truth.

**Acceptance:** Ownership does not serialize independent tasks; read/write concurrency tests; fixed-read staleness; lazy source hash/range checks; snapshot isolation after other task integration; protected and overlapping scope denial; preflight size failure before approval; generated view provenance and filesystem-boundary tests.

## Workstream 3 — Execution, recovery, handoff and import

**Outcome:** A candidate survives session changes and can be produced by a person or an agent.

1. Freeze submission into an immutable candidate before trusted validation. Evidence and documentation proposals remain non-authoritative.
2. Preserve candidate, notes, read assumptions and scope grants when an explicitly stopped attempt is handed off. Fence the old ticket; create a new attempt and readiness boundary.
3. Allow import of an existing exact commit's approved-path diff into a clean task worktree. Do not import historical approval claims or bypass readiness/checks/review.
4. Preserve stopped-epic snapshots and candidates as provenance; a replan can explicitly reuse/import them. Do not automatically promote abandoned code.
5. Allow targeted amendment only when the shared design remains byte-identical and unaffected tasks/contracts remain identical. Impact includes transitive dependents; integrated or live affected work requires explicit stop/correction. Unaffected candidate execution may finish while acceptance is pending, but no head changes bypass that gate.
6. Keep attempt budgets, lease expiry, stop attestations, process recovery and human approval explicit. No silent duplicate dispatch.

**Acceptance:** Handoff reuses product changes and fences old results; imports reject protected or out-of-scope files; observations never become Current; interrupted checks cannot accept after release; unrelated work survives targeted amendment; shared-design changes require a full design revision.

## Workstream 4 — Optimistic integration and verification

**Outcome:** Parallel coding is not defeated by a single long-running integration lock.

1. Execute isolated checks independently per immutable candidate without the global operation lock.
2. Compose and verify a combined candidate against an exact accepted head. Keep this speculative while checks run.
3. Accept with a short transactional compare-and-swap of head, ticket, epoch and definition. If another result wins, retain the evidence as a superseded attempt and recompose/recheck; do not repeat coding or isolated validation.
4. Bound recomposition retries and retain validated candidates for an explicit later integration call.
5. Preserve fail-closed write conflicts. A clean file-level composition is not evidence of semantic independence.
6. Default to cumulative checks. Permit an operator-selected scoped integration policy only with explicit integration checks; full checkpoint/final verification stays mandatory.
7. Add common-directory, process-held locks for named check resources. Require explicit operator configuration and document that local filesystem locks do not coordinate separate machines or external jobs automatically.
8. Retain all exact-candidate isolated/combined evidence, including unsuccessful and superseded combinations.

**Acceptance:** Real overlap of isolated and combined checks; deterministic race with both candidates eventually accepted; no stale acceptance; no isolated success misreported as combined success; resource exclusion; retry budget; recovery after release/expiry.

## Workstream 5 — Moving target and knowledge-aware synchronization

**Outcome:** Multiple initiatives can publish safely without a mandatory central coordinator.

1. Track original baseline, accepted integration base, verified knowledge checkpoint and actual target ref separately.
2. Expose upstream status, changed paths, code conflicts and affected Working Knowledge.
3. Prepare synchronization only at a closed boundary, after pending work/approvals are explicitly resolved. Final candidates can be invalidated through this explicit path.
4. Compose old base, initiative result and new canonical snapshot. Require resolutions for same-path conflicts; reject silent last-writer-wins behavior.
5. Require an explicit decision for a Working replacement whose document or implementation artifacts changed upstream. Offer update, retire, revalidate or use-upstream; prohibit revalidate from hiding upstream edits to the same logical document.
6. Preserve original request, accepted Intent, completed-epic records and previous check provenance. Archive accepted sync records and invalidated final candidates.
7. Run policy/cumulative checks and knowledge lint on the exact prospective checkpoint. Require review of the exact changed paths and a signed acceptance.
8. At acceptance, ensure upstream is still the inspected commit. Promote code, integration base and knowledge together; invalidate final approval and dependent planning assumptions.
9. Record a required Target revision when upstream invalidates a target assumption. Block further plans/finalization until an explicit Intent revision clears it.
10. Scope reachability refs by controller identity to avoid unrelated stores overwriting advisory refs.

**Acceptance:** Moving-main code-only and documentation changes; same-document Core/Working conflict; upstream movement during approval; sync check failure; retired nodes; immutable history; two independent initiatives publish in sequence; final reapproval; old Target no longer silently used when revision is required.

## Workstream 6 — Publication and operator UX

**Outcome:** Human decisions concern actual changes, not clerical JSON transport.

1. Provide a readable gate inspection containing exact identities, design, scope, task/dependency summary, relevant diffs and verification references.
2. Add operator-side direct signing/applying of an exact displayed request ID. Never give worker adapters the signing key.
3. Support exact commit publication by default, plus explicitly policy-selected squash-equivalent and merge-commit boundaries. In every case bind the inspected base, exact tree and permitted parents; never accept additional unreviewed code.
4. Recognize a correctly published commit even after the canonical ref has subsequently advanced, if the commit is still in its ancestry.
5. Provide a safe local operator publication command and structured PR/MR handoff. Do not claim a remote PR exists or completed unless an actual external operator performs it and the Git result is verified.
6. Keep deployment separate. Preserve final checks/review/approval as audit sidecars to avoid self-referential candidate hashes.
7. Show actionable states for validated candidates, required sync, pending Target revision, handoff, conflicts and blockers.

**Acceptance:** Exact mode regression; explicit squash/merge modes; wrong tree/base/parents rejection; publication visibility after later commits; stale request rejection; operator key boundary; no automatic deployment or remote write.

## Workstream 7 — Skills, examples, validation and package

1. Rewrite current-state README, architecture, workflow, execution, context, concurrency, synchronization, security and operator references in English. Keep installed skills concise; put procedures in references.
2. Include compact-fix, investigation, documentation-only, parallel-contract and upstream-sync authoring examples. Keep examples tied to actual supported contracts.
3. Regenerate every JSON schema and validate all source links, metadata and installed paths.
4. Add deterministic end-to-end and adversarial tests for each new boundary; retain existing authority/retrieval/signature/review/finalization tests.
5. Run the complete suite, package validator, multi-epic demo and installed-runtime smoke. Record actual commands/environment/results, not inherited results from the input archive.
6. Expand live-agent scenarios but report them separately from deterministic tests. Do not claim model/tool authentication, remote-hosted CI, cross-machine locks or production sandboxing were tested locally.
7. Build a clean archive with no Git metadata, credentials, mutable controller stores, worktrees or caches. Re-extract and verify file hashes and source validity.

## Non-goals and explicit boundaries

- No automatic conversion of existing active controller stores. New contracts use a new state version and a fresh control directory.
- No multiple active epics inside one initiative, mandatory repository-wide scheduler, or speculative future detailed designs.
- No incremental publication of one request, graph database, hosted orchestration server or forced TUI dependency.
- No claim of atomic multi-repository publication, database rollback, production deployment or semantic proof from passing shell checks.
- Native cloud PR creation, hosted merge queue execution and live coding-model evaluations require external tools/accounts and are not represented by local synthetic tests.

## Completion evidence

The accompanying implementation report maps these workstreams to shipped commands/modules, records executed validation, and identifies any residual limits. The source manifest and clean extraction check bind the delivered ZIP to those exact source files.
