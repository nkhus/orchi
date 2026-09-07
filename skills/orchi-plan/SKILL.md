---
name: orchi-plan
description: "Define an Orchi initiative roadmap or design the next epic and all of its coding tasks. Use for requirements, architectural planning, task design, accepted amendments, or explicit roadmap changes. Do not implement code or plan all future tasks."
compatibility: "Requires Git and POSIX; use uv or Python with bundled dependencies. Install all five Orchi skills together."
---

# Plan the next epic

Read `next`; follow only `define_initiative` or `design_next_epic`.
Use the installed sibling entrypoint: `uv run <skills>/orchi/scripts/orchi.py --control "$ORCHI_CONTROL" …`.
Read [planning contract](../orchi/references/planning.md) and [authoring](../orchi/references/authoring.md).

## Initiative direction

Recover the user's original outcome, acceptance, constraints and architectural direction.
Use [retrieval](../orchi/references/retrieval.md) to search Core and read exact sources before code investigation.
Distinguish observed facts, approved requirements and open questions.
Create an ordered epic roadmap with outcomes, dependencies, risks and contribution to root acceptance.
Keep future epics at roadmap level: no task lists, file-level plans or invented future implementation.
Submit `begin --file initiative.json`; present the returned direction request to the human and stop.

## Next epic

Inspect the actual initiative `head` and verified `knowledge_head`, not merely canonical code.
Search and get with `--initiative <id>`; inspect diagnostics, then the exact affected code and tests.
Use logical knowledge paths in task context; snippets are discovery aids, not packet sources.
Choose the shared epic design and contracts before task decomposition.
Create a task DAG; for every task specify approach, decisions, invariants, failure behavior,
exact edits, sufficient sources, dependency-output contracts, verification and escalation.
Leave only explicitly delegated local choices to workers; `open_questions` must be `[]`.
If essential design uncertainty remains, ask a focused question or propose a bounded research epic.
Use `knowledge-only` mode for a read-only investigation/documentation correction, not fake implementation.
Validate schemas and registered checks; submit `plan --file epic.json`.
Explain key decisions, parallelism, risk and scope to the human; stop at the exact plan approval request.

## Amend, do not silently redesign

Use `roadmap --file ... --reason ...` only between epics for material future-scope changes.
Use `amend --file ... --reason ...` for material active-epic changes after workers are stopped/released.
Read [recovery](../orchi/references/recovery.md); revisions invalidate old authorization but retain budgets/history.
