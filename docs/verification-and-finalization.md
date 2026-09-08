---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/engine.py
  - skills/orchi/scripts/orchi_core/reconciliation.py
  - skills/orchi/scripts/orchi_core/publication.py
relations:
  part_of: [docs/README.md]
  depends_on: [docs/concurrency.md, docs/security.md]
---
# Verification, review and atomic publication

## Evidence and review

Only operator-registered commands become trusted check IDs. They execute without importing project modules into the controller, in fresh worktrees of the exact candidate. Check execution rejects changes to tracked candidate contents. A passing command establishes only what that command and its test actually check. It is not a universal proof of a business requirement or architecture.

Workers report structured results; their claimed success does not accept a candidate. Isolated results and speculative combined results retain separate commit identities. Unsuccessful and superseded combinations remain evidence. A full epic checkpoint runs all required checks after joint integration. Final validation adds policy final checks and every final disposition's declared checks on the exact code/docs/archive tree.

Review is independent, read-only, causal and bounded. A blocker needs criterion, root cause, consequence and evidence. Unrelated pre-existing problems are advisory. Zero findings is successful review. Omitted prior blockers are not resolution. Subsequent passes target repairs and their effects; an unresolved round/attempt limit stops rather than silently passing.

## Final reconciliation

Every accepted requirement receives one disposition: satisfied with registered candidate checks, changed only through a prior accepted Intent resolution, or explicitly unresolved only under operator policy. Every target architecture document is realized, deviated, unchanged or explicitly unresolved according to policy. An unchanged architecture cites existing implementation artifacts and checks; `not-applicable` is reserved for accepted knowledge/investigation outcomes and still requires candidate checks.

Reconcile every Working entry and check final Core ontology, links, artifacts and absence of target/lifecycle authority markers. The candidate archives initiative source, designs, task observations, sync history, attempts, metadata, completed checkpoints and available evidence. Final check/review/signature sidecars stay outside that self-referential tree and are included in controller export. A normal clone has archived authoring and audit metadata, not necessarily every internal Git object or full source packet; retain exports when exact internal replay is required.

## Three Git publication shapes, one atomic request

Policy chooses before execution:

| Mode | Required published identity |
| --- | --- |
| `exact` (default) | The exact signed candidate commit, parent = accepted integration base |
| `squash` | Exact approved candidate tree, one parent = accepted integration base |
| `merge` | Exact approved candidate tree, ordered parents = accepted base and exact candidate |

These are history shapes, not incremental delivery modes. All publish the whole reconciled request. Additional changes, another base, unexpected parents or a different tree are rejected. A hosted queue that recomposes code on a new base needs sync, final validation/review and a fresh signature; an old branch approval is not approval of arbitrary future combinations.

`publication` returns the structured local/PR handoff without changing Git or creating a remote PR. The operator can publish through the repository's allowed workflow and then `record-publication --commit`. Recording accepts a correctly shaped commit in canonical ancestry even when another commit arrived afterwards. It does not confuse that later head with this initiative's checked result.

The local operator `publish` helper uses `git update-ref` with the expected old commit and refuses to mutate a branch checked out in any worktree. Detach the branch or use the operator's normal merge/hosting workflow. It cannot overwrite a concurrently advanced canonical ref. Merge mode constructs the exact two-parent tree first; squash mode is completed externally and recorded. Relevant primary Git semantics are documented by [git update-ref](https://git-scm.com/docs/git-update-ref).

Publication is not deployment, successful migration, feature-flag activation or atomic cross-repository release. Those operations need their own accepted runtime evidence and authority boundaries.
