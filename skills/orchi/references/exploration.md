# Explore and shape an idea

Use when a request is an idea rather than agreed work: a new project, module, or
feature whose direction needs research, a comparison of approaches, or
strategic decisions before anyone can propose a scope. An exploration produces
decisions, not code. It ends when the idea is shaped enough for
[planning](planning.md) to turn it into an Initiative, Epic, or Task without
reopening its decisions.

## The Exploration Issue

One Issue labelled `Exploration` holds the exploration, so it survives across
sessions. Create it once the user agrees on the destination. Its body is the
current map; detail lives in comments and linked branches, and the body links
to it.

| Section | Content |
| --- | --- |
| Destination | What is being decided and what the end of the exploration looks like |
| Request | The original idea in the user's words, kept apart from later decisions |
| Appetite | How much the outcome is worth: Task, Epic, or Initiative size, and any time limit |
| Constraints and no-gos | Fixed limits, and what is explicitly out of scope |
| Findings | One line per research comment: the question, the answer, a link |
| Options | Each direction considered: its shape, what it makes easy and hard, and the verdict with its reason |
| Decisions | The decision log ([clarify](planning.md#clarify-with-the-user)); mark a decision that is hard to reverse, surprising, and a real tradeoff as a decision record candidate |
| Requirements | Numbered requirements (R1, R2, ...) of the chosen direction, each observable at completion |
| Shape | The chosen direction, and candidate Epics as outcomes with the result or contract each supplies to the next |
| Not yet specified | Questions you can see coming but cannot phrase precisely yet |
| Open questions | Questions you can phrase now, with what each one blocks |

## Phases

Each phase ends on its completion criterion. Return to an earlier phase when an
answer changes the destination or invalidates options.

1. **Frame.** Ask about the destination, the original request, the appetite, and
   the constraints. Done when the user agrees on the destination; then create
   the Issue.
2. **Research.** Facts are the agent's job. Start `orchi-researcher` in Research
   mode for each external question and `orchi-scout` for code and Issues, in
   parallel, and keep asking the user what does not depend on their answers.
   Post each verified finding as a comment with its sources, and list it under
   Findings. Done when every option-shaping question is answered or recorded as
   not established.
3. **Diverge.** Start `orchi-researcher` in Option mode, at least three times in
   parallel, each with a different lens: minimal; most flexible; best for the
   most common case; buy or reuse rather than build; or the smallest useful
   step, including not building. Present the options one at a time, compare
   them, and recommend one or a hybrid. Ask open questions here rather than
   offering a menu. Done when the user has picked a direction.
4. **Converge.** Resolve the chosen direction's decisions in rounds along their
   dependencies, as planning's clarify rules describe, and record each one at
   once. When a question cannot be settled on paper (how a state model behaves,
   what a screen should look like), offer a prototype. Done when no open
   question affects the approach.
5. **Shape.** Write the requirements and the Shape section, then read the whole
   Issue back to the user. Done when the user confirms it is shaped.

## Prototypes

A prototype is throwaway code that answers one question. With the user's
agreement, build it on a `prototype/<slug>` branch from main, mark it as a
prototype in its name and first lines, make it run with one command, keep its
state in memory, and skip tests and polish. Record the question and the verdict
in the Issue with a link to the branch. Never merge the branch; the decision,
not the code, carries into planning.

## New projects

Exploration needs a Git repository with a GitHub remote, because the Issue is
its state. If none exists, offer to create one (`git init`, `gh repo create`)
and to install Orchi there before framing; creating a remote repository needs
the user's agreement. The first Initiative of a new project usually establishes
its foundation, and the decision record candidates land with it.

## Hand off

When the user confirms the shape, end with `Plan with: /orchi-plan #<n>`.
Planning takes the destination, requirements, decisions, and Epic candidates as
agreed, links the Exploration as the source request, and asks only what the
exploration left open. After the tracked work exists, close the Exploration as
completed with a link to it. An exploration that ends in "do not build" closes
as not planned, with the reason in its decision log.
