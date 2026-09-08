---
kind: reference
area: orchi
artifacts: [skills/orchi/scripts/orchi_core/synchronization.py]
relations:
  part_of: [docs/README.md]
  depends_on: [docs/knowledge-model.md, docs/verification-and-finalization.md]
---
# Synchronizing a moving canonical branch

`baseline` records where the initiative began. `integration_base` records the latest canonical commit whose interaction with this initiative has been accepted. Canonical movement does not mutate Current, Target, tickets or old evidence automatically.

## Operator/planner sequence

```bash
orchi sync-status
orchi sync-draft --out /operator/drafts/sync.json
# Replace draft markers; resolve actual code and knowledge impacts.
orchi sync-check --file /operator/drafts/sync.json
# Review the returned exact sync review request and candidate.
orchi sync-review --file /operator/drafts/sync-review.json
orchi inspect
# Operator signs and applies this exact request ID.
```

Prepare only at a closed boundary with no active epic, tickets, pending gate or aggregate operation. A fully verified/final-approved but unpublished initiative can sync; its final candidate is invalidated only after the new sync is accepted. For an active epic, close it or explicitly stop/release work and accept the stopped-epic boundary first. Candidate history is retained.

## Three-way code composition

Compare old accepted base, initiative head and exact new canonical commit. Disjoint changes are composed. If both sides changed the same path differently, require exactly one explicit resolution: replacement bytes/mode, deletion or an exact regular file from a specified commit. Protected-path conflicts fail closed and require operator-managed resolution. No automatic rebase, last-writer-wins or hidden text-conflict resolution occurs.

The new canonical must descend from the previous accepted integration base. Rewritten/unrelated history and initiative archive ID collisions require operator recovery. Ordinary sync is not a repair tool for rewritten provenance.

## Knowledge composition

Affected knowledge includes Working records whose logical Core document or tracked implementation artifacts changed upstream. It also includes inherited upstream Core that documents implementation this initiative already changed, including newly added documents. Every affected record needs an explicit disposition:

| Disposition | Effect |
| --- | --- |
| `update` | Author reconciled Current text, artifact coverage and registered checks |
| `revalidate` | Retain the Working assertion with new artifact hashes and fresh checks |
| `retire` | Explicitly suppress the logical document with reason and checks |
| `use-upstream` | Remove this overlay and explicitly accept the new Core statement, with checks |

`revalidate` cannot hide an upstream edit to the same logical document. The planner must merge the meaning, retire it, or deliberately adopt upstream after checking it. Artifact associations are impact hints, not semantic proof; a reviewer must assess untracked relationships and the Target impact. No automatic architecture inference is claimed.

## Checks, review, approval and atomic promotion

The prospective candidate includes exact code, upstream Core, revised Working manifest and the sync proposal. Run accumulated completed checks, policy sync checks and declared knowledge checks; lint prospective Current links and ontology. Failed checks leave the old head, base and Working authority unchanged.

Review covers the entire prospective diff, every code resolution, knowledge disposition and the explicit Target assessment. Passing review creates a human gate binding candidate/tree, new upstream, old accepted state, Working digest and evidence. Acceptance checks that canonical still equals the inspected upstream. If it moved, withdraw/discard and prepare a new exact snapshot.

Only accepted sync promotes code, integration base and verified Working Knowledge together. Completed epic contracts, original request, Intent history and prior evidence remain unchanged. A required Target revision blocks new design/finalization until `revise-intent` is accepted. Any previous final review/candidate/approval is retained as invalidated history and cannot authorize the new result.

`withdraw-gate` returns to the reviewed prospective state; `sync-discard` abandons that prospective candidate without changing Current. A rejected sync also remains inspectable/discardable. No target publication or deployment happens in this sequence.
