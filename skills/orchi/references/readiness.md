# Readiness checklists

Use before starting or delegating a Task or Epic, and when planning creates them.
The Issue is the specification for an owner who never saw the planning
conversation. A project's own stricter checklist, if its instructions define one,
applies in addition to these.

## Task readiness checklist

A Task is ready only when its body, together with the linked sources, answers
every applicable item below without relying on chat history. Each item is a
presence check that can be answered yes or no. A Task that fails any item is not
ready: do not start or delegate it. Record what is missing and fix the Issue
first. Items marked "when applicable" may be answered "not applicable" for a
standalone small fix.

1. States one concrete, reviewable outcome.
2. States its purpose and the output that later work or users consume.
3. Lists prerequisites, with Task/Epic references, or states "None".
4. Names the parent Epic as a native sub-issue (when applicable).
5. Links the exact design sections, requirement/decision IDs, or documents it
   implements (when applicable), and the code or issues inspected while planning.
6. Names at least one likely code, schema, contract, test, or documentation
   surface, using concrete symbols, routes, migrations, tables, or file paths
   where known.
7. States constraints and non-goals.
8. Describes at least one success scenario and at least one failure scenario,
   each with expected behavior, or states explicitly why no failure case exists.
9. Gives observable acceptance and the exact checks or commands that verify it.
10. States its documentation impact: the owning pages named by the project's
    documentation routing, or why none change.
11. Lists no open question in the Task or its parent Epic that is marked as
    affecting this Task's approach; resolve such a question, or move it to a
    bounded investigation Task, first.

## Epic readiness checklist

An Epic is ready for delivery only when every item below holds. A future Epic in
an Initiative may answer a field with `Deferred until #<n>: <reason>` only for a
decision that depends on that predecessor's result; it is not ready for delivery
until the deferral is resolved.

1. States one bounded outcome, with in-scope and out-of-scope lists.
2. Links its sources (exact sections, requirement/decision IDs), and names its
   parent Initiative when applicable.
3. Describes current state with evidence: files, symbols, or behavior.
4. Contains a design, or a link to one, covering approach, interfaces and
   boundaries, invariants, and tradeoffs; or states "no architecture change".
5. Names affected code, schema, contract, test, and documentation surfaces.
6. Describes success and failure scenarios, inputs and outputs, risks, and
   expected recovery.
7. Names its branch and PR target, and has native blocked-by relationships for
   every direct dependency. Each blocker is merged into the target branch.
8. Gives exit criteria mapped to requirements, with verification.
9. Contains no `Deferred until` answer and no open question marked as affecting
   the approach.
10. Has native sub-issue Tasks in execution order, each passing the Task
    readiness checklist.
