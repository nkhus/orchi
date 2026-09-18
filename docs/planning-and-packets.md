# Planning and task packets

## Plan progressively

For the complete request, establish the outcome, root acceptance criteria, constraints, architectural direction, and ordered epic roadmap. Each roadmap entry states an outcome, dependencies, contribution to acceptance, and risks. It must not contain a task list or a file-by-file implementation plan.

`RoadmapEpic` has no task field, and contracts reject unknown fields. The controller admits an executable plan only for the selected next epic. A new planning cycle uses the actual accepted `head` and verified `knowledge_head`, not the original canonical checkout or an agent's recollection.

Future roadmap scope may change through an explicitly approved proposal between epics. Completed epic definitions remain immutable history. Material active-epic changes require an amendment after affected workers are stopped and released.

## Design the active epic

Inspect scoped Working Knowledge and the actual affected implementation. Choose shared boundaries, interfaces, invariants, and consequential trade-offs before decomposing the work. Build a task dependency graph, then investigate and design every task. Validate compatibility among task designs, scopes, dependency contracts, and registered checks before presenting the exact plan to the human.

Readiness is a preflight check of the approved task's applicability; it is not a second independent design phase. Workers receive fixed decisions and explicitly delegated local choices. Substantive unresolved questions block implementation. A bounded `knowledge-only` epic can investigate unknowns or reconcile documentation without manufacturing code tasks.

## Task contract

| Fields | Required meaning |
| --- | --- |
| `goal`, `acceptance` | Observable task result and criteria |
| `current_state`, `approach` | Observed implementation and chosen mechanism |
| `decisions`, `invariants` | Fixed decisions and properties that must hold |
| `allowed_choices` | Local decisions intentionally delegated to the worker |
| `failure_modes` | Important errors, races, and alternate outcomes |
| `edits` | Exact path, create/modify/delete action, and implementation intent |
| `context`, `read_paths` | Required sources, reasons, and read assumptions |
| `depends_on`, dependency sources | Required producer results and promised contracts |
| `verification` | Criterion, scenario, expected result, and trusted check IDs |
| `escalation`, `open_questions` | Stop conditions and an explicit absence of unresolved design questions |

Contracts establish structural completeness. They cannot prove that a planner discovered every unknown or selected a correct mechanism. Human review and subsequent implementation verification remain necessary.

## Generate packets at dispatch

The controller builds a task packet when the task is ready, using the actual accepted head. The packet includes initiative outcome and constraints, shared epic design, complete task design, resolved documentation, source content, edit before-images, repository instructions, dependency output, hashes, and binding metadata.

`TASK.md` is the readable handoff; `packet.json` is the machine envelope. Both are derived from the accepted plan and exact source snapshots. Edit the approved definition through an amendment, not a packet copy. The corresponding checkout is part of the handoff; a packet alone is not a replacement for the repository.

Context retrieval is file-level rather than AST- or section-level. The default packet budget is 96,000 UTF-8 bytes, not a token count or a measurement of all automatically loaded agent context. Required content is never silently summarized or truncated. Oversized packets stop dispatch: narrow the task, select smaller precise source files, or have the operator size the budget before initialization.

## Parallel work and integration

A dependent task becomes ready only after its producer is verified and integrated. An ended process or reported completion does not satisfy the dependency. Declared read/write conflicts and exclusive resources serialize otherwise ready tasks. Shared public interfaces must be settled before parallel implementation begins.

Workers report additional source reads in `extra_reads`. Changed read assumptions invalidate stale results. Reporting is cooperative; Orchi does not instrument every filesystem read. Unknown semantic dependencies still require combined-tree checks and scoped review.

Candidate checks run first on the isolated result. Integration then verifies the combination with accepted work, including required regression checks. Two independently passing candidates are not accepted together merely because each passed alone.

## Stop rather than improvise

A missing material decision, incompatible source, required scope expansion, stale assumption, or unresolved acceptance issue stops the affected task. Preserve evidence and choose a bounded retry, approved amendment, or human resolution. Do not hide redesign inside execution, weaken verification, or convert an exhausted budget into success.
