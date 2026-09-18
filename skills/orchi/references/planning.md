# Planning boundaries

Initiative = full user request. Epic = internal verified increment. Task = portable execution unit.
First record initiative outcome, root acceptance, constraints, architectural direction and ordered epic roadmap.
Do not detail future tasks. A roadmap change is explicit and signed; completed contracts are immutable history.
A small request may use one epic; a complex request uses multiple sequential epics.

At each epic: inspect actual internal head and last verified knowledge checkpoint; choose shared design;
decompose; design every task; validate; ask the human to approve the exact plan. Do not ask for another
approval per normal task. Workers may run independently inside the approved envelope.
Read enough actual code to settle consequential choices. General architecture decisions belong in the epic;
file-specific mechanisms, failure handling and tests belong in the task. Do not duplicate long source docs.

A task needs exact paths and actions, current behavior, approach, fixed decisions, invariants, allowed local
choices, failure modes, sources with reasons, criteria-to-check mapping, dependency output contracts and
escalation conditions. `open_questions: []` is an explicit readiness claim, not a substitute for research.
Future outputs are `dependency` sources with producer and contract; do not present nonexistent code as current.
Shared public interfaces must be fixed before parallel workers begin. Paths are exact, not broad write globs.
Use exclusive resources for shared ports/databases/registries that Git cannot isolate.

If a later task needs new read scope or a public-interface decision, stop affected work and amend.
For substantial unknowns, choose a bounded investigation epic before implementation; mode `knowledge-only`
has no write tasks, uses trusted checks on actual state and closes through review/checkpoint.
