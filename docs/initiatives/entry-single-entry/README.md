# [ENTRY] Orchi as a single entry with a crew pool

Status: proposed plan for agreement. Nothing here describes current behavior;
the current Orchi works as the [README](../../../README.md) describes. The host
behavior this plan relies on is recorded in
[how a session can start other sessions](session-creation-research.md), and the
[target architecture](architecture.md) details the design.

## Request

The maintainer's requests, translated from Russian (2026-10-25 and 2026-10-26),
in the order they were made:

> I need a universal tool with several entry points for a person: research with
> a challenger that ends in a set of documents describing the vision; planning
> from research or from a request to fix something; UI/UX design as an Epic the
> planner creates; development run by a tech lead who takes the plan and runs
> researchers, designers, and developers.
>
> Orchi is the single entry, like a product manager. It does no planning itself:
> it starts a planner session for a task, a research session when there is only an
> idea, hands work from the backlog to development, and leads acceptance. The
> development lead closes small single-threaded work itself and runs developers in
> parallel when there is more. A new role later should be one more capability of
> Orchi.
>
> Orchi creates the sessions. There are two modes, set at the Orchi level:
> interactive, where the user talks in the sessions Orchi created and Orchi does
> not track them; and auto, for long autonomous work, where the sessions ask Orchi
> instead of the user. Workers always ask their parent session, never the user.
>
> Everything must always be visible in Claude Desktop. On its first command Orchi
> creates blank sessions; each blank session asks for permission to create its
> workers, which are nested sessions under it. When Orchi needs a planner, it takes
> a blank session and turns it into a planner; when the work is done, the session
> is cleared and becomes available again. Workers keep the names `worker-#`. A
> blank session that becomes a planner is named `planner-<topic>`. Five blank
> sessions with three workers each; Remote Control off. The user gives permission
> by clicking a button rather than typing.

Impeccable must always be installed with Orchi, so that design work never runs
without it.

## Outcome

In Claude Desktop the user talks to one session, Orchi. On its first command Orchi
builds a pool of crews at the top level of the sidebar; one click in each crew
creates its three workers, nested under it. Orchi turns a free crew into the role
a request needs, the crew runs the work through its workers, and both return to
the pool when it is done. No session is created after setup, so the pool works
without the user's turns.

## Sessions

```
Orchi                         top level, created by the user
crew-1 → planner-payments     top level, created by Orchi
  worker-1                    nested, created by its crew after the user's click
  worker-2
  worker-3
crew-2 … crew-5               the same
```

| Session | Created by | Sidebar | Talks to | Does the work itself |
| --- | --- | --- | --- | --- |
| Orchi | the user | top level | the user; in auto mode it answers crews for the user | no |
| Crew `crew-#`, assigned `<role>-<topic>` | Orchi, at setup | top level | the user in interactive mode, Orchi in auto mode, and its workers | no: it delegates to its workers |
| Worker `worker-#` | its crew, at setup, after the user's click | nested under its crew | its crew only | yes |

A crew takes one of these roles:

| Role | Holds | Its workers do |
| --- | --- | --- |
| Planner | One Initiative, Epic, or Task plan with the user: Issues, the breakdown, research and design Epics, a "detail the plan" Epic | Code and Issue retrieval |
| Researcher | Exploring an idea with the user as a challenger, over many rounds; the vision documents | Local and web research, option design |
| Designer | Product context and visual direction with the user through Impeccable (`init`, `shape`, direction choice, comps) | Building UI against the approved direction |
| Dev lead | Delivering an Epic or Initiative: its `epic/*` branch, Task assignment, decisions, merging, review, the PR | One Task each, on a `task/*` branch |

Several crews may hold the same role for independent work. A role is a skill the
crew invokes; adding a role adds a skill and a line to Orchi's role list, and
changes no other session.

## Pool lifecycle

1. **Setup.** On the user's first command, Orchi starts 5 crews, each in its own
   worktree and in bypass permissions mode, and detaches them to the top level.
   Orchi itself runs in bypass permissions mode, because a session can start
   others only in its own mode or a lower one; when it does not, Orchi asks the
   user to switch it before building the pool.
2. **Workers.** Each crew ends its first turn with one reply button, "Create
   workers". The user's click is a user turn, in which the crew starts its three
   workers, each in its own worktree and nested under it, and turns their Remote
   Control off where it is on. When the host shows no button, the crew proposes
   its workers as three cards instead; a worker the user starts from a card is
   nested under the crew the same way.
3. **Assign.** Orchi takes a free crew, renames it `<role>-<topic>`, and sends it
   the assignment: the role skill to invoke, the Issue, and its new title,
   because a renamed session does not learn its title.
4. **Work.** The crew gives its workers tasks by message, with the branch to use.
   Workers report to the crew and ask it, never the user. The crew is told when
   each worker's turn ends.
5. **Worker done.** A worker keeps its context until the PR with its work is
   merged, so rework goes to the same worker. Then it checks that nothing would be
   lost, returns its worktree to a detached `origin/<default>`, and the crew
   clears it. Its title stays `worker-#`.
6. **Crew done.** The crew reports to Orchi. On Orchi's request it clears its
   workers, then clears itself, and Orchi renames it back to `crew-#`.
7. **Pool exhausted.** A session can be created only in a turn the user started.
   When no crew is free, the request waits on Orchi's board, and Orchi offers to
   enlarge the pool in the user's next turn.

The pool size (5 crews of 3 workers) is a setting.

## Clearing

A session can clear only itself and the sessions it started and has not
detached. Clearing empties the conversation and nothing else.

| Event | Cleared by | How |
| --- | --- | --- |
| A worker's work is merged or dropped | its crew | directly, after the worker confirms nothing would be lost and returns its worktree to a detached `origin/<default>` |
| A crew finished its assignment | the crew itself | on Orchi's request: its workers directly, then itself with `self`; Orchi then renames it |
| Orchi | the user | `/clear` |

- Orchi cannot clear a crew, because it detached it; a crew cannot clear another
  crew's workers.
- A clear is refused while the session is pinned, open on the user's screen,
  holds an unprocessed message or live work, or serves a Remote Control client.
  The clearing session retries later and reports a refusal it cannot resolve.
- A self-clear happens when the turn ends and is dropped if the user sends a
  message first or the session is stopped or archived.
- A cleared session keeps its title, parent, folder, branch, settings, and Remote
  Control state. Clearing does not touch the worktree, and the user can bring the
  old conversation back.
- After clearing itself, a crew finds its workers again among the sessions it
  started.

## Modes

These are Orchi's work modes, separate from the permission mode (D17).

| | Interactive | Auto |
| --- | --- | --- |
| Who answers a crew | The user, in the crew's session | Orchi |
| Orchi follows crews | No: a crew comes to Orchi when it needs something | Yes: Orchi decides for the user |
| Workers | Ask their crew only | Ask their crew only |
| Set by | Default | The user asking Orchi |

## Branches

| Branch | Held by | Created from |
| --- | --- | --- |
| `epic/<tag>-<slug>` | the dev lead crew | `main` |
| `task/<slug>` | one worker | the Epic branch |
| `fix/<slug>` | one worker | `main` |

Each worker switches its own worktree to the branch its crew names and returns it
to a clean state before it is cleared. The dev lead merges each `task/*` branch
into the Epic branch after checking that the worker's commits sit on the expected
branch and base, and opens one PR from the Epic branch to `main`. Parallel Tasks
must not touch the same files; planning splits them that way.

## Journeys

1. **Greenfield idea.** The user tells Orchi the idea. Orchi assigns a crew as
   researcher and sends the user to it. The vision documents go to a planner
   crew, which plans from them.
2. **Feature.** Orchi assigns a planner crew. The planner asks whether research is
   needed; if so, the plan starts with a research Epic and a "detail the plan"
   Epic blocked by it.
3. **Fix.** Orchi assigns a planner crew for one Task.
4. **Running a plan.** Orchi assigns a dev lead crew to a `delivery-ready`
   Epic or Initiative. Research and design Epics go to researcher and designer
   crews.
5. **More planning during delivery.** A dev lead crew sends Orchi the request;
   Orchi assigns a planner crew.
6. **More hands.** A crew uses all of its workers; it never creates sessions
   after setup.
7. **Acceptance.** Orchi checks finished work with a read-only subagent and
   brings the result to the user.

## Decisions

| # | Decision | Source |
| --- | --- | --- |
| D1 | Orchi is the single entry, a product manager that does no planning, research, design, or development itself. | 2026-10-26 |
| D2 | Crew roles: planner, researcher, designer, dev lead. Several crews may hold one role. | 2026-10-26 |
| D3 | Crews talk to the user and delegate all work to their workers; workers talk only to their crew. | 2026-10-26 |
| D4 | Modes interactive and auto, set at the Orchi level. | 2026-10-26 |
| D5 | Everything is visible in the Desktop sidebar; no work runs in sessions outside it. | 2026-10-26 |
| D6 | A pool built once at setup: 5 crews of 3 workers, reused by renaming and clearing. | 2026-10-26 |
| D7 | Crews sit at the top level; each crew's workers are nested under it. | 2026-10-26 |
| D8 | The user creates a crew's workers with one click on a reply button; proposal cards are the fallback. | 2026-10-26 |
| D9 | Names: `crew-#` when free, `<role>-<topic>` when assigned, `worker-#` always. | 2026-10-26 |
| D10 | Clearing: a crew clears its workers directly and itself on Orchi's request; only the user clears Orchi. | 2026-10-26 |
| D11 | Remote Control is off for pool sessions. | 2026-10-26 |
| D12 | The planner never starts research; research is an Epic in the plan. | 2026-10-26 |
| D13 | Research ends in a set of vision documents. | 2026-10-25 |
| D14 | UI/UX design is an Epic type; Impeccable is always installed (pinned version, no hooks). | 2026-10-25 |
| D15 | Claude Desktop only. | 2026-10-26 |
| D16 | The maintainer migrates existing projects by hand. | 2026-10-26 |
| D17 | Orchi and the whole pool run in bypass permissions mode, so that the auto mode classifier cannot deny setup or clearing. Pool sessions then run every tool without a prompt; role instructions and the crews' checks are the only guards. | 2026-10-26 |
| D18 | Interactive mode uses the 0.16 autonomy levels Ask and Decide; auto mode uses Auto, with Orchi answering crews. At every level the user decides deployment, destructive and irreversible actions, access, and scope; a merge that deploys waits. | 0.16, 2026-10-14 |

## Host facts this plan relies on

Observed in live runs on 2026-10-26, detailed in
[how a session can start other sessions](session-creation-research.md):

- A session can start sessions only in a turn the user started, in any
  permission mode. A reply button's click starts a user turn; a proposal card
  starts its session on the user's click, nested under the proposer.
- In auto mode the classifier denied about half of the starts in user turns. In
  bypass permissions mode none was denied.
- A starter can detach a session to the top level; its own nested sessions stay
  nested under it. No tool nests a session under another one later.
- A session clears directly only itself and sessions it started and has not
  detached; any session can ask another to clear itself, and rename and message
  it.

## Requirements

- R1. Orchi builds the crews in the user's first command and reports which ones it
  could not start; each crew offers one button that creates its three nested
  workers, and reports which ones it could not start.
- R2. Orchi routes each request to a crew role and assigns a free crew, renaming
  it.
- R3. Orchi keeps a board: crews and their assignments, who waits for the user,
  what is ready, and what waits for a merge, read from GitHub and the pool.
- R4. Crews delegate all work to their workers and give each task by message with
  its branch; workers ask only their crew.
- R5. Finished workers and crews are cleared as the clearing rules say and return
  to their free names; a refused clear is retried and, if it still fails,
  reported.
- R6. A researcher crew challenges the idea, runs local and web research through
  its workers, iterates with the user without a question limit, and commits a set
  of vision documents.
- R7. A planner crew asks whether research is needed for a feature and can plan
  research, design, and delivery Epics with dependencies.
- R8. A dev lead crew runs Tasks in parallel on `task/*` branches, merges them into
  the Epic branch after checking each, and opens the PR.
- R9. The Orchi installer always installs Impeccable at a pinned version without
  hooks and fails before mutation when Node is missing; a designer crew runs
  Impeccable's interactive steps with the user and never chooses a direction
  alone.
- R10. In auto mode crews ask Orchi, and Orchi answers within the limits the user
  set.

## Exclusions

- Hosts other than Claude Desktop (D15).
- Sessions outside the sidebar, such as `claude --bg` workers (D5).
- Migrating existing projects such as Mirivis (D16).
- A controller, state database, or approval receipts: GitHub stays the shared
  state, and the pool is visible in the sidebar.
- Making Taste Skill or SmoothUI mandatory.

## Records this reopens

- [Managing session lifecycles](../../out-of-scope/session-lifecycle.md): Orchi
  and crews create, rename, and clear sessions; the user no longer creates a pool
  by hand.
- [Team roles as agents](../../out-of-scope/team-roles-as-agents.md): roles stay
  skills, but a crew invokes its role when Orchi assigns it instead of the user
  typing a hub command.
- [Load-based worker capacity](../../out-of-scope/load-based-worker-capacity.md):
  the pool size replaces the team list as the limit.
- The two symmetric hubs of 0.14 give way to Orchi and crew roles.

## Epics

| Epic | Outcome | Depends on |
| --- | --- | --- |
| E1 Pool | Orchi builds and assigns crews; crews create their nested workers on one click; clearing and release (R1, R2, R5) | none |
| E2 Crew delegation | Crews run all work through their workers; workers ask only their crew; modes (R4, R10) | E1 supplies the pool |
| E3 Research | Researcher crews and vision documents (R6) | E2 supplies delegation |
| E4 Design | Impeccable always installed; designer crews (R9) | E2 supplies delegation |
| E5 Planning and delivery | Planner and dev lead crews, typed plans, parallel `task/*` branches (R7, R8) | E2 supplies delegation |
| E6 Board | Orchi's board of crews, waiting decisions, readiness, and merges (R3) | E1, E5 supply the state it shows |

## Acceptance

- In a fresh repository, one command to Orchi and one click in each crew build
  the pool: five top-level crews, each with three workers nested under it.
- A greenfield idea told to Orchi reaches committed vision documents and a plan
  whose first Epic is research, with no session created after setup.
- A plan with research, design, and delivery Epics runs to merged PRs, and every
  crew and worker involved returns to its free name with an empty conversation.
- Each claim is reported as established, limited, or not established; a passing
  text test does not establish live behavior.

## Open questions

- Whether Orchi can still show (split view, focus) a crew it detached, or gives the
  user a link instead.
- Whether a crew finds its workers again after clearing itself; not yet observed.
- Where vision documents live (proposed: `docs/vision/<slug>/`) and which
  documents the set holds.
- The board's form: a sidebar panel, a local page, or a claude.ai page; and the
  unit and owner of estimates.
- Whether projects can add their own crew roles.
