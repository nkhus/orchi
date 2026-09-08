---
kind: component
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/engine.py
  - skills/orchi/scripts/orchi_core/execution.py
  - skills/orchi/scripts/orchi_core/synchronization.py
  - skills/orchi/scripts/orchi_core/publication.py
relations:
  part_of: [docs/README.md]
  depends_on: [docs/knowledge-model.md, docs/concurrency.md]
---
# Architecture

## Authority and actors

The human operator owns the signing key, check registry, policy, canonical write permissions and outer isolation. The planner authors decisions. Workers propose candidates. Independent reviewers assess exact diffs and evidence. The controller accepts transitions; it does not decide semantic correctness or sign on the human's behalf.

One external controller store manages one initiative and at most one active epic. Multiple controllers may share a repository without a mandatory repository scheduler. Advisory refs are namespaced by controller identity and initiative ID; publication relies on actual Git history and the accepted base, not awareness of every other developer.

## Snapshot identities

| Identity | Meaning |
| --- | --- |
| `baseline` / `origin_baseline` | Immutable canonical commit at initiative creation |
| `integration_base` | Canonical commit explicitly accepted for composition |
| `head` | Accepted initiative implementation, which may include active-epic progress |
| `knowledge_head` | Last verified checkpoint; partial active-epic code is not Current knowledge |
| `intent.commit` / digest | Exact accepted Target snapshot, independent of Current |
| task `start_commit` | Frozen implementation and dispatch source identity |
| final candidate | Exact reconciled code/docs/archive tree proposed for publication |

A sync may promote `integration_base`, `head`, `knowledge_head` and the Working overlay together. It never retcons old check provenance, original source text or completed epic contracts. Reconciliation produces a candidate whose first parent is the accepted integration base, not necessarily the original baseline.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `models`, `authoring`, `preflight` | Strict contracts, deterministic compact expansion, bounded known-input checks |
| `intent`, `context` | Exact target bundle and role-aware Current/Target authority resolution |
| `ontology`, `graph`, `retrieval` | Markdown semantics and disposable graph/lexical projections |
| `engine`, `execution` | Signed workflow gates, task fencing, local scopes, candidates and exact-head integration |
| `synchronization`, `reconciliation`, `publication` | Code/knowledge synchronization and checked atomic delivery |
| `repository` | Immutable Git object/tree access, file-level composition and refs |
| `store`, `signing` | Transactional workflow acceptance and content-addressed audit; never documentation authority |
| `runner`, `process`, `relay`, `resources` | Bounded foreground executors, ticket-only RPC and same-host check exclusion |
| `views`, `cli`, `operator_cli` | Derived human views, machine commands and explicit human signing |

Markdown/Git remain durable knowledge. SQLite stores accepted workflow state and audit identities. Search indexes, graphs, maps and materialized Current/Target trees are disposable. Check/review evidence is bound to exact commits; neither graph proximity nor prose is manufactured proof.

## Execution transaction boundaries

Claim binds the task definition, exact context, before-images, lease and attempt budget. Readiness precedes writes. Submission freezes a candidate and evidence-only observations. Isolated checks and combined checks run outside the aggregate's global operation slot. A short transactional compare-and-swap accepts a checked combination only when the accepted head, task ownership, epoch and validation token still match.

A losing combination is retained as superseded evidence, recomposed and rechecked. The worker and isolated validation are not restarted. Conflicting writes or stale fixed assumptions fail closed. Full checkpoint/final operations and sync reserve their own explicit global operation; recovery requires observed process termination.

## Delivery boundaries

Atomic publication contains all of this initiative's reconciled code and Core. Another initiative may publish independently. Local CAS publication or a verified externally created commit must match the approved tree, base and policy-selected parent shape. Final attestation is a sidecar because a commit cannot contain a signature over itself. Hosted PR creation, deployment and cross-repository transactions remain external.
