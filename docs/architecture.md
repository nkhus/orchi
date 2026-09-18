# Architecture

## Domain model

An **Initiative** represents the complete user request: original intent, outcome, root acceptance criteria, constraints, architectural direction, and an ordered epic roadmap. It is the only canonical publication boundary.

An **Epic** is the next internal milestone. Its executable plan is designed against the actual accepted initiative head after the preceding epic's verified knowledge checkpoint. Future roadmap entries describe outcomes, dependencies, contributions, and risks, not task definitions.

A **Task** is a designed, portable unit of work for one coding assistant. A **Ticket** authorizes one attempt with a specific plan, packet, starting commit, scope, resource reservation, epoch, and expiry.

One epic is active at a time. Independent tasks in that epic may execute in parallel; integration is serialized and verified. A small initiative may contain only one epic.

## Components

```text
User / coordinator
       |
Five focused agent skills
       |
JSON CLI -> Engine
              |-- Strict Pydantic contracts and generated JSON Schemas
              |-- Context resolver and task-packet builder
              |-- SQLite state and content-addressed audit artifacts
              |-- Git object access, candidate construction, and worktrees
              |-- Trusted check runner
              `-- Foreground worker runner
                     |-- Codex prepare/execute adapter
                     `-- Command adapter / manual packet handoff

Human operator -> signed exact gate requests
Human operator -> normal fast-forward publication -> publication receipt
```

Skills define the reasoning procedure and division of responsibilities. The controller enforces mechanical invariants, persists transitions, and observes checks. It does not call a hidden planning model, choose product requirements, or decide architectural trade-offs on the user's behalf.

The Python modules under `skills/orchi/scripts/orchi_core/` separate contracts, context, persistence, Git operations, subprocess execution, signatures, worker orchestration, and CLI routing. Both executable entrypoints and their dependency declarations are bundled in the installed skill.

## Commit identities

| Identity | Meaning |
| --- | --- |
| `baseline` | Canonical commit on which the initiative started |
| `head` | Latest accepted internal result, including integrated tasks in the active epic |
| `knowledge_head` | Last closed epic checkpoint whose Working Knowledge is verified |

These identities intentionally differ during an active epic. A worker must not treat a checkpoint's description as a claim about subsequent partial implementation.

```text
canonical: C0 ------------------------------------------------ C1
             \                                                  ^
              direction -> epic plan -> accepted tasks          |
                            -> knowledge checkpoint             |
                            -> next epic -> checkpoint          |
                            -> final Core + archive -> candidate
```

Internal commits remain reachable through Orchi refs. The final candidate has exactly one parent: `baseline`. Canonical publication therefore exposes one completed code-and-docs state rather than intermediate epic states. The internal `docs/` tree remains equal to baseline Core until final candidate construction.

## Sources of truth

Git stores exact code and documentation snapshots, accepted definition revisions, checkpoints, and the archived initiative. SQLite stores workflow acceptance: current phase, active epic, tickets, counters, pending approvals, accepted heads, review ledgers, and in-flight operations. A ref preserves reachability but does not by itself prove workflow acceptance.

Content-addressed artifacts preserve packets, process observations, checks, reviews, requests, and signatures. A model's completion message is a proposal, not verification evidence. Check results are associated with exact commits, trees, check identifiers, and policy.

A knowledge manifest records source code identity and artifact hashes; its own commit is assigned externally. Final approvals and publication receipts similarly remain outside the commit they identify, avoiding self-referential hashes.

## Durable local execution

SQLite `BEGIN IMMEDIATE` serializes claims and acceptance. Long-running checks and integrations execute outside write transactions, between reservation and acceptance. Acceptance checks that the operation identifier and expected head still match. A lost process leaves an unresolved operation, not a successful result.

Ticket fencing uses the ticket identifier, epoch, plan digest, status, packet fingerprint, start commit, and expiry. An amendment invalidates outstanding authorization without resetting budgets or erasing history. Lease expiry does not automatically start a replacement worker.

## Human decisions

The human approves initiative direction, each exact epic plan, material amendments, and the exact final candidate. Ordinary tasks within an approved plan do not require another approval. Ed25519 signatures bind decisions to the request and its policy/head context; protecting the key and the operator channel establishes the meaningful trust boundary.

## Operating scope

Orchi operates on one Git repository, one host, and one initiative per control directory. `run` is a foreground drain of ready tasks that stops at review, knowledge, approval, or blocked boundaries. There is no background daemon, distributed scheduler, multi-repository coordinator, automatic deployment, or automatic baseline rebase.

A worktree separates file trees, not operating-system identities or privileges. See [security](security.md) before configuring worker access.
