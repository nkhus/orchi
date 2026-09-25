# Plan the next verifiable result

Use after initial research and direction agreement. Read the actual integration
branch, relevant code, owning documentation, and completed dependency results.
A plan describes intended behavior; it is not evidence that behavior exists.

## Initiative

Capture the original request faithfully, agreed outcome, exclusions, observable
acceptance, constraints, major decisions, and remaining unknowns in the initiative
document. Keep the source request distinguishable from later decisions. Retain
useful stable requirement IDs and links, without inventing IDs for every sentence.

Outline Epics as independently verifiable outcomes. Explain direct dependencies
through the result or contract they supply. Keep future Epics at outcome level;
expand an Epic into Tasks when preparing to execute it. GitHub stores the native
hierarchy and status; documentation stores reasoning and requirements. Do not
maintain a second child/status checklist.

Check that every agreed requirement has a planned home in an Epic. A short mapping
in the existing plan is enough when coverage is hard to see; no coverage database
or mandatory matrix is needed. Do not silently drop requirements during decomposition.

## Epic design

Before coding, write enough design in the Epic issue or a linked branch document
for its owner and reviewer to agree on what the result means:

- outcome, boundaries, and requirements addressed;
- relevant current implementation and the change needed;
- public interfaces, data/ownership boundaries, and invariants that must hold;
- chosen approach and significant tradeoffs, including a no-architecture-change
  statement when that is the actual decision;
- observable acceptance, relevant failure/recovery cases, and verification;
- affected documentation, direct dependencies, and unresolved material questions.

Resolve questions that affect the chosen approach before dependent implementation.
A bounded investigation Task can answer a technical unknown discovered later;
it produces findings and a recommendation, not silently adopted product code.
Discuss a material change of direction with the user. Ordinary implementation
choices within the agreed approach do not need a new approval.

## Tasks

Derive sequential Tasks from that design. Each owns one reviewable result and
states the acceptance/verification plus relevant sources and constraints. Use
likely affected areas to orient the implementer, not a permission list of files.
Task order should follow real dependencies; GitHub's native child order or concise
ordering text is sufficient. All Tasks share the Epic branch and PR.

Design shared contracts before independent Epics depend on them. When a contract
is not yet implemented, model its producer Epic as a blocker rather than claiming
its output exists. Check coverage from Epic acceptance to Tasks before starting;
avoid both missing integration work and tasks that merely duplicate template fields.

A documentation-only outcome needs no fake code Tasks. A small fix needs only its
Task's outcome, acceptance, and verification. Do not create empty design documents.
If the decomposition changes within the agreed direction, update affected pending
Tasks and links in place, preserving completed history and explaining why.
