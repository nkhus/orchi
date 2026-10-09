# Plan the next verifiable result

Use after research and direction agreement. Read the actual integration branch,
relevant code, owning documentation, and completed dependency results. A plan
describes intended behavior; it is not evidence that behavior exists.

Plan proportionately. A fix still needs a Task that passes the Task readiness
checklist; keep each answer short. An Epic needs the design below in its issue or a linked branch document,
then its Tasks. Do not create a planning Task per field or empty design documents.

## Clarify with the user

The questions and answers with the user are the most valuable input to an Issue.
Only the main session talks to the user; a delegated agent that drafts Issues
returns its questions instead of guessing, and the main session asks them and
continues that agent with the answers.

- **Find the gaps first.** Check what you know against the readiness checklist
  for the planned scope. Every item you would otherwise have to guess becomes a
  question.
- **Look up facts; ask for decisions.** Never ask the user what the code,
  documentation, Issues, or an external source can answer: send scouts, and
  keep asking the questions that do not depend on what they find.
- **Ask only what changes the result.** Ask when the answer changes
  requirements, approach, scope, acceptance, or risk. Decide ordinary
  implementation choices yourself and record them as decisions with a reason.
- **Decide what the user delegated.** When the user agrees that the main session
  may decide a class of questions itself — in this conversation or in the
  repository's instructions — decide those questions instead of asking. Record
  each such decision as made by the main session under that delegation, citing
  it (who delegated, when, their words, and its limits), with the options
  considered and the reason. Ask about anything outside the delegation; a
  delegation never covers merge or deployment authority the user has not
  granted separately.
- **Make each question easy to answer.** Give one or two sentences of context,
  two to four concrete options with their consequences, and your recommendation
  first, worded so that "yes" accepts it; always allow a free answer. Use the assistant's structured question
  tool when it has one.
- **Ask in rounds along dependencies.** A round holds open questions whose
  prerequisites are settled, most consequential first, a few at a time; a
  question that depends on another open question waits for a later round.
  Follow up when an answer opens a new gap or contradicts earlier evidence.
  Clarifying ends when no open question would change the requirements,
  approach, scope, acceptance, or risk.
- **Record answers at once.** Keep a decision log: question, answer, who decided
  (the user, or the main session with or without a delegation), date, and
  reason. Quote the user's answers
  faithfully; do not drop their qualifiers. Carry the log into the Issues.
- **Never present a guess as a fact.** An unanswered question stays an open
  question; if it affects the approach, the work is not ready.

## Write Issues for agents

The owner of an Issue is usually an agent that never saw the planning
conversation; the user must still be able to read and approve it.

- **Self-contained.** Put every requirement, decision, source, and constraint in
  the body. Link exact sections, not whole documents. Never refer to "as
  discussed".
- **Context before instructions.** Say why the work exists, where it fits, and
  how the system behaves today, with evidence (`path:line`, symbols, routes,
  tables, commands).
- **Separate facts, intent, and decisions.** Current behavior and evidence,
  numbered requirements (R1, R2, ...), the solution vision, and the decision log
  are distinct sections.
- **Solution vision is guidance.** Describe the intended approach and change
  points and why they were chosen. The owner may deviate within the
  requirements and records the deviation; it is not a permission list.
- **Plain, precise language.** Short sentences; one requirement per item; "must"
  and "must not" for requirements; define project terms on first use; exact
  values, names, and commands instead of descriptions of them.

## Initiative

Record the plan in `docs/initiatives/<tag>-<slug>/README.md` on the Initiative branch,
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

- outcome, boundaries, and numbered requirements addressed;
- the decisions that shape it, with the user's answers from the decision log;
- relevant current implementation and the change needed;
- public interfaces, data and ownership boundaries, and invariants;
- test seams: where tests go, what each seam catches and misses, and an
  existing test to follow ([testing](testing.md#seams));
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
carries its own context, requirements, solution vision, relevant decisions,
acceptance, verification, sources, and constraints, so that its owner does not
have to reconstruct them from the Epic. Name likely
affected areas to orient the implementer, not as a permission list. Order Tasks by
real dependencies; native child order or brief ordering text is enough.

Slice Tasks vertically: each is a narrow but complete path through the layers it
touches (data, logic, interface, tests, documentation) that can be verified on
its own, small enough for one owner to finish in one fresh context. Put the
refactoring that makes the change easy in its own first Task. Sequence a wide
mechanical change, such as a rename with many call sites, as expand, migrate in
batches, then contract, so that checks stay green after every Task.

## Agree the breakdown

Before creating Issues, show the user the proposed Epics or Tasks: for each, its
title, what it delivers, and what blocks it. Ask whether the granularity is
right, whether each blocker is real, and what to merge or split. Revise until
the user agrees; a list is cheaper to change than Issues.

Check every Task against the [Task readiness checklist](readiness.md#task-readiness-checklist)
and every Epic against the [Epic readiness checklist](readiness.md#epic-readiness-checklist)
before anyone starts or delegates it; a project's own stricter checklist applies
in addition.

Design shared contracts before independent Epics depend on them. When a contract
is not implemented yet, make its producer Epic a native blocker instead of
assuming its output exists. Check coverage from Epic acceptance to Tasks, avoiding
both missing integration work and Tasks that merely restate template fields.

A documentation-only outcome needs no fake code Tasks. If the decomposition changes
within the agreed direction, update pending Tasks and links in place, preserving
completed history and explaining why.
