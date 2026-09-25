# Plan the next verifiable result

Use after research and direction agreement. Read the actual integration branch,
relevant code, owning documentation, and completed dependency results. A plan
describes intended behavior; it is not evidence that behavior exists.

Plan proportionately. A fix needs only an outcome, acceptance, and verification in
its Task. An Epic needs the design below in its issue or a linked branch document,
then its Tasks. Do not create a planning Task per field or empty design documents.

## Initiative

Record the plan in `docs/initiatives/<key>-<slug>/README.md` on the Initiative branch,
or in an existing project location that already serves this purpose. Capture the
original request faithfully, the agreed outcome, exclusions, observable
acceptance, constraints, major decisions, and remaining unknowns. Keep the source
request distinguishable from later decisions. Link existing requirements and
stable IDs instead of copying them or inventing IDs for every sentence.

Outline Epics as independently verifiable outcomes. Explain each direct dependency
through the result or contract it supplies. Keep future Epics at outcome level and
expand an Epic into Tasks only when preparing to execute it. GitHub stores the
hierarchy and status; the document stores reasoning and requirements. Do not keep
a second child or status checklist.

Check that every agreed requirement has a planned home in an Epic. A short mapping
is enough when coverage is hard to see. Do not silently drop requirements.

## Epic design

Before coding, write enough design for the owner and reviewer to agree on what
the result means:

- outcome, boundaries, and requirements addressed;
- relevant current implementation and the change needed;
- public interfaces, data and ownership boundaries, and invariants;
- chosen approach and significant tradeoffs, including an explicit
  no-architecture-change statement when that is the decision;
- observable acceptance, relevant failure and recovery cases, and verification;
- affected documentation, direct dependencies, and unresolved material questions.

Resolve questions that affect the approach before dependent implementation. A
bounded investigation Task can answer a later technical unknown; it produces
findings and a recommendation, not silently adopted product code. Discuss a
material change of direction with the user; ordinary implementation choices
within the agreed approach need no new approval.

## Tasks

Derive sequential Tasks from the design. Each owns one reviewable result and
states acceptance, verification, and relevant sources and constraints. Name likely
affected areas to orient the implementer, not as a permission list. Order Tasks by
real dependencies; native child order or brief ordering text is enough.

Design shared contracts before independent Epics depend on them. When a contract
is not implemented yet, make its producer Epic a native blocker instead of
assuming its output exists. Check coverage from Epic acceptance to Tasks, avoiding
both missing integration work and Tasks that merely restate template fields.

A documentation-only outcome needs no fake code Tasks. If the decomposition changes
within the agreed direction, update pending Tasks and links in place, preserving
completed history and explaining why.
