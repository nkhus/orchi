# Plan the next verifiable result

Use after research and direction agreement. Read the actual integration branch,
relevant code, owning documentation, and completed dependency results. A plan
describes intended behavior; it is not evidence that behavior exists.

Plan proportionately. A fix still needs a Task that passes the Task readiness
checklist; keep each answer short. An Epic needs the design below in its issue or a linked branch document,
then its Tasks. Do not create a planning Task per field or empty design documents.

## Declined work

Before proposing, look for the same request among Issues closed as not planned
and in the repository's out-of-scope records, if it keeps them. When it was
declined before, put the earlier reason, with its link, into the proposal: new
evidence can reopen it, asking again cannot. When the user declines a request
for a lasting reason, record it with the user's words so the next session finds
it: close its Issue or Exploration as not planned with the reason. When no Issue
exists, add a record where the repository keeps out-of-scope records, or else
open an Issue with the request and close it as not planned at once. A request
parked for later is not declined.

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
- **Ask once.** Before asking, read the decision log, the Issue, and its
  comments: never ask again what is decided, and never ask to confirm a step the
  agreed plan already covers. A question still waiting for an answer is not
  repeated; a later report says only who waits.
- **Decide what the user delegated.** When the user agrees that the main session
  may decide a class of questions itself — in this conversation or in the
  repository's instructions — decide those questions instead of asking. Record
  each such decision as made by the main session under that delegation, citing
  it (who delegated, when, their words, and its limits), with the options
  considered and the reason. Ask about anything outside the delegation; a
  delegation never covers merge or deployment authority the user has not
  granted separately. In a pool, the [autonomy level](pool.md#modes-and-autonomy) the
  user set is such a delegation; cite it as that section says.
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

Record the plan in the working folder's `docs/work/<tag>-<slug>/README.md` on the
Initiative branch ([working documents](knowledge.md#working-documents)), or in an
existing project location that already serves this purpose. Capture the
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

From an exploration, give each of its decisions (D1, D2, ...) a fate in the plan:
a requirement it becomes, an area decision to record with the code that
implements it (name the area page), or none. A decision without a fate is a
gap in the plan.

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

## User interface design

Work that changes a user interface gets a design depth in its Epic or Task. The
design engine is Impeccable; the steps that need the user run in the session
that talks to them, and writers build only against what the user approved.

| Depth | When | Planning does |
| --- | --- | --- |
| None | The change stays within existing components and screens | Nothing more; the writer finishes with `polish` and the review audits it |
| Brief | A new screen or feature inside an established visual world (`DESIGN.md` exists) | Run `/impeccable shape` with the user, keep its brief as the surface brief in `.impeccable/surfaces/`, and link it; run the direction round only when the composition stays materially open |
| Epic | A new product, a redesign, or several screens whose composition is open | Plan a standalone `design` Epic (labels `Epic` and `design`) for a designer crew, outside any Initiative, and make the Epic or Initiative that builds on it blocked by it |

- A design Epic names the surfaces it designs, what must stay, and whether it
  replaces `DESIGN.md`. Its Tasks are the builds of the approved surfaces; the
  designer splits them after the user approves each comp, so plan them at
  outcome level.
- From scratch, the design Epic for the key surfaces comes right after the
  foundation Epic and builds on the stack it set up; the result is kept. Plan the rest of development as one Issue labelled
  `needs-planning`, with `Requested by: <Orchi's title>` in a pool, blocked by
  the design Epic, carrying the Exploration's requirements, decisions, and fates
  it covers: when the design merges, a planner details it from those,
  `PRODUCT.md`, `DESIGN.md`, the surface briefs, and the built surfaces.
- Without `PRODUCT.md`, the design Epic starts with `/impeccable init`; for a
  redesign without `DESIGN.md`, with `/impeccable document`, so the incumbent
  look is recorded as evidence.
- Every Task that builds UI links the `DESIGN.md` sections, surface brief, and
  approved comp it builds against, and names its states, breakpoints, themes,
  and accessibility level. A brief that turns out to need a new world or a
  redesign is raised to a design Epic, and the user is told why.
- Only the user chooses a direction and approves a comp or a generated asset,
  at every autonomy level. In auto mode, Orchi may answer `shape` questions that
  `PRODUCT.md`, `DESIGN.md`, or the Issues already settle; the rest wait for the
  user.

## Engineering standards

- A new project's first Epic is the foundation Epic that `orchi-standards`
  plans; every other Epic and Task, the design Epic included, is blocked by it,
  and only it scaffolds the stack. An existing project without `ENGINEERING.md`
  gets a standards Epic the same way when the user agrees to it.
- Never ask the user to choose a tool, threshold, or code layout: the
  [standards defaults](standards.md) decide, and the decision log records the
  choice with its reason. Ask only for the product constraints.
- State user-facing acceptance as what a user can see or do, and name the
  acceptance test for each criterion.
- With `ENGINEERING.md`, take each Task's checks from its Checks table and plan
  within its Architecture rules. A Task that needs an exception names it with its
  reason, so the user hears of it before delivery.

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
the user agrees; a list is cheaper to change than Issues. When the breakdown is
already known while the scope is proposed, agree both in one question. At pool
autonomy Decide or Auto, show the breakdown and proceed.

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
