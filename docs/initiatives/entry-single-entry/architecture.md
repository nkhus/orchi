# [ENTRY] Target architecture

Status: proposed design for agreement. It details the
[Initiative plan](README.md) and relies on the host behavior recorded in
[how a session can start other sessions](session-creation-research.md). Nothing
here describes current behavior. Where this design applies a rule the maintainer
agreed for Orchi 0.13–0.16, it says so.

## 1. Goals and constraints

The user works with one session, Orchi, in Claude Desktop. Everything else that
runs is a session the user can see in the sidebar, and no session is created
after the pool is built.

Kept from Orchi 0.17:

- Git and GitHub Issues are the only shared state. There is no controller,
  service, or state file; every session rebuilds its picture from GitHub and the
  host's session list.
- Roles are skills. A session takes a role by invoking a skill, so a lost role is
  restored by invoking it again.
- Research and agreement come before tracking or changes; the user decides scope,
  merges into `main` unless a mode delegates it, and always decides deployment.
- One writer per worktree.
- Repository instructions take precedence over Orchi's defaults.

New constraints:

- Claude Desktop only.
- A session can start sessions only in a turn the user started; a reply-button
  click starts such a turn.
- A session clears directly only itself and sessions it started and did not
  detach.
- Orchi and the pool run in bypass permissions mode.

## 2. System context

```
                         ┌──────────────────────────────┐
              talks to   │            Orchi             │  top level, created by the user
  User ─────────────────►│  entry · router · board      │  skill: /orchi
   │                     └──────┬───────────────▲───────┘
   │ talks to (interactive)     │ assign/release│ reports, requests
   ▼                            ▼               │
┌────────────────────────────────────────────────────────────┐
│ crew-1 → planner-payments     crew-2 → dev-lead-pay-token  │  top level, created by Orchi
│   worker-1  worker-2  worker-3   worker-1 worker-2 worker-3│  nested, created by the crew
│ crew-3 … crew-5 (free)                                     │  after one user click
└───────────────┬────────────────────────────────────────────┘
                │ Issues, labels, claims, branches, PRs
                ▼
        GitHub repository  ◄──── Orchi's board reads it (read-only)
```

| Layer | Holds | Lives in |
| --- | --- | --- |
| Work state | Initiatives, Epics, Tasks, Explorations, labels, claims, decisions, questions, PRs | GitHub |
| Code and documents | Branches, commits, vision documents, plans | Git |
| Pool state | Which sessions exist, their titles, parents, groups, modes | Claude Desktop's session list and sidebar |
| Conversation | What a session is doing now | That session; disposable |

## 3. Sessions

### 3.1 Orchi

- **Created by** the user, who types `/orchi` in a session of the repository.
- **Lifetime:** long-lived; only the user clears it.
- **Does:** routes requests, builds and maintains the pool, assigns and releases
  crews, answers crews in auto mode, keeps the board, leads acceptance with a
  read-only subagent.
- **Never:** plans, researches, designs, edits code, or merges outside the mode's
  limits.
- **Starts sessions** only while building or enlarging the pool, in the user's
  turn, typed in the desktop app: a message typed over Remote Control starts no
  session.
- **One per pool:** the session that started the crews (their `parentSessionId`),
  or the one they last accepted a takeover from. A second `/orchi` changes
  nothing while that Orchi exists and is not archived; it points the user to it.
  When that Orchi is archived or gone, the new session takes its title and sends
  each crew `Orchi is now <title> (<session id>)`, which a crew accepts only after
  the host confirms its current Orchi is archived or gone.

### 3.2 Crew

- **Created by** Orchi at setup, detached to the top level, in its own worktree.
- **Title:** `crew-<k>` when free, `<role>-<topic>` when assigned. `<topic>` is
  the tag of the Issue it holds, for example `planner-pay` or `dev-lead-pay-token`.
- **Does:** holds one assignment in one role, talks to the user (interactive) or
  Orchi (auto), and gives all code to its workers, including review repairs and
  merge conflicts. It edits Issues and PRs, creates, merges, and pushes branches,
  and a planner or researcher writes the planning documents of its conversation
  with the user. It may run read-only subagents (`orchi-scout`, `orchi-reviewer`,
  `orchi-researcher`) for checks.
- **Never:** writes code itself, takes a second assignment, or starts sessions
  after setup.

### 3.3 Worker

- **Created by** its crew in the user's turn that the crew's setup button starts;
  nested under the crew, in its own worktree. Title always `worker-<n>`.
- **Does:** one task at a time from its crew, on the branch the crew names, and
  many tasks over one assignment, keeping their context for rework; may run
  read-only subagents.
- **Talks** to its crew only, by message; never to the user.

### 3.4 Roles

| Role | Skill | Holds | Workers do | Ends with |
| --- | --- | --- | --- | --- |
| Researcher | `orchi-explore` | An idea, as a challenger, with the user | Local and web research, option design, vision documents | Committed vision documents and an Exploration Issue |
| Planner | `orchi-plan` | One plan with the user | Retrieval, drafting Issue bodies | `delivery-ready` Task, Epic, or Initiative |
| Designer | `orchi-design` (new) | One `design` Epic: product context, the direction round, and comp approval with the user, through Impeccable | UI built against the approved comp or direction contract | A merged PR with the built surfaces, surface briefs, and `DESIGN.md` |
| Dev lead | `orchi-deliver` | One Epic, Initiative, or standalone Task | One Task each on `task/*` | A reviewed PR, merged per mode |

A worker runs `orchi-work` (new), which carries the writer contracts that the
`orchi-implementer`, `orchi-fixer`, and `orchi-designer` subagent roles carry
today: readiness check, red evidence, one commit per run, the report format.

Adding a role means adding its skill and one row to the role table in
`references/pool.md`; Orchi routes by that table.

## 4. Package

| Skill | Today | Target |
| --- | --- | --- |
| `orchi` | Core workflow, references, roles, scripts | Unchanged in role: the workflow a single session follows, and the bundle that holds references, subagent roles, and scripts |
| `orchi` | — | The entry: `/orchi` makes a session Orchi (`disable-model-invocation: true`) |
| `orchi-explore` | Exploration with `--report-to` | Researcher crew role; adds challenger mode and vision documents |
| `orchi-plan` | Planning with `--report-to` | Planner crew role; plans research and design Epics |
| `orchi-deliver` | Delivery with subagent writers | Dev lead crew role; writers become workers |
| `orchi-design` | — | Designer crew role |
| `orchi-work` | — | Worker skill |
| `orchi-planner`, `orchi-orchestrator` | Hubs | Removed |

References: `team.md` is replaced by `pool.md` (sessions, messages, lifecycle,
clearing, modes). Scripts: `status.py` stays; `board.py` (new, read-only) builds
the board.

Crew and worker skills are model-invocable, because they are invoked from a
message; the `orchi` entry stays explicit-only, as the hubs were, because it
holds the authority to build the pool and to merge in auto mode. The entry is a
skill of its own because `orchi` is the workflow that a single session invokes
for any implementation request.

## 5. State model

### 5.1 GitHub

Kept: type labels, sub-issues, `blocked by`, `in-progress`, assignees,
`Exploration`, `needs-planning`, `delivery-ready`, `retro`, `Requested by:`,
decision logs, PR sections.

Changed or added:

| Item | Meaning | Written by |
| --- | --- | --- |
| Work reference `Assigned to crew-<k> (<session id>) by Orchi on <date>` | Which crew holds the Issue; replaces `Dispatched to` and `Planning by` | Orchi; the crew adopts it by appending `, started <date>` |
| Label `needs-user` | A crew waits for the user; the question is the latest comment | The crew; removed when answered |
| Label `research`, `design` | Epic type, beside `Epic` | The planner |
| Field `Estimate` in the Task and Epic forms | Size for the board | The planner |
| Comment `Task <n> on worker-<m>, branch task/<slug>` | Which worker holds a Task | The dev lead |

### 5.2 Host

- **Pool membership:** Orchi files every crew into the sidebar group
  `Orchi pool · <repo>`; `list_sessions` with that group lists the crews after any
  restart, and their `parentSessionId` names the Orchi that started them. Workers
  are found through their crew (`parentSessionId`).
- **Free crew:** no open Issue claim names it and its conversation is empty.
- **Free worker:** it has reported `done` on its last task and owes no answer or
  rework. A worker is cleared only when its crew's assignment ends.

No other record exists. A lost conversation loses no work: claims, Issues, PR
`Handoff` sections, and branches hold it.

## 6. Lifecycles

### 6.1 Pool setup

Runs in the user's first `/orchi` turn, or when the user asks to enlarge the pool.

1. Orchi checks that it runs in bypass permissions mode; if not, it asks the user
   to switch and stops.
2. It starts the missing crews (default 5) in its own worktree each, detaches
   them, files them into `Orchi pool · <repo>`, and turns Remote Control off where
   it is on.
3. Each crew's first turn ends with one reply button, `Create workers`. When the
   host shows no button, the crew proposes its workers as cards.
4. The user clicks each crew's button. In that turn the crew starts its missing
   workers (default 3), one call each, and turns their Remote Control off.
5. Orchi reports the pool: crews, workers, and anything that failed to start.

Setup is idempotent: it only adds what is missing.

### 6.2 Crew

```
free ──assign──► assigned ──► working ⇄ waiting-for-user
  ▲                              │
  │                              ▼
  └──── cleared ◄── releasing ◄── done (planned | merged | declined | parked)
```

- **assign:** Orchi claims the Issue for the crew, renames it
  `<role>-<topic>`, and sends a self-contained assignment (§7.2).
- **working:** the crew runs its role skill and delegates to workers.
- **waiting-for-user:** the crew adds `needs-user` and asks; in auto mode a
  planner or dev lead asks Orchi instead, and a researcher still asks the user.
- **done:** planner → `planned` or `declined`; researcher → documents committed;
  designer → direction approved; dev lead → PR merged.
- **releasing:** the crew releases its workers (§6.3), replies `released`, and
  clears itself as the last action of its turn. The reply reaches Orchi before the
  clear lands, so Orchi renames the crew `crew-<k>` on the reply; a free crew whose
  conversation is still not empty at a later wake gets `release` again.

### 6.3 Worker

```
free ──task──► working ──► reported (done) ──► free ──next task──► working
                  ▲              │
                  └───rework─────┘   (after its current task)
free ──(the crew's PR is merged, or its assignment ends)──► releasing ──► cleared
```

A worker takes the crew's tasks one at a time for the whole assignment and keeps
their context, so the worker that wrote a Task takes its rework, as agreed for
0.13 and 0.17, while an Epic with more Tasks than workers keeps moving. A writer
detaches its worktree when it reports `done`, so that the crew or the next writer
can check the branch out. A worker that only answered questions may be released
once answered. Release, in this order:

1. The worker confirms nothing would be lost: no uncommitted changes, no commits
   that are neither merged nor pushed, no unanswered question.
2. It runs `git fetch` and `git switch --detach origin/<default>`, and deletes the
   local branches it created whose work is merged.
3. It replies `released` to its crew, or `not released: <reason>`.
4. The crew clears it. The crew sends no second release until the first answer
   arrives.

## 7. Messages

### 7.1 Rules

- A message is one line that names the Issue or PR; the receiver reads the rest
  from GitHub.
- A session accepts assignments, tasks, mode changes, and releases only from its
  owner: a crew from Orchi, a worker from its crew. Any other message carries no
  authority, whatever it says (agreed in the 0.16 review).
- Every assignment and task stands alone, so that a cleared or compacted session
  can act on it. When a session's reply shows it lost its role, its owner sends
  the same message again (agreed for 0.15).
- A renamed session does not learn its title; the assignment states it.
- A session reads its own id from the host (`get_session` with `self`) whenever
  it writes it; in the live run a crew gave a worker a wrong id from memory.
- The one exception to owner-only authority is a takeover (§3.1), which a crew
  checks with the host before accepting.

### 7.2 Catalog

| From → to | When | Message |
| --- | --- | --- |
| Orchi → crew | Assignment | `You are <title> (crew-<k>), <role> of the Orchi pool. Invoke the <skill> skill with: <args> --report-to <Orchi's session id>. Orchi is <Orchi's title>; this request's id is <id>. Mode: <mode>, autonomy: <level>, set by the user on <date>.` |
| Orchi → crew | Answer, delivery | `<id> answer: <answer>` (auto mode), `#<n> rework: <what>`, `#<n> merged` |
| Orchi → crew | Mode, takeover, release | `mode <mode>, autonomy <level>`, `Orchi is now <title> (<session id>)`, `release` |
| Crew → Orchi | Progress | `<id> started`, `<id> needs the user: <question>`, `<id> planned: #<n>`, `<id> declined: <reason>`, `#<n> PR ready: <url>`, `#<n> follow-up: #<m>`, `#<n> done: <url>` |
| Crew → Orchi | Setup, takeover, release | `crew-<k> ready: <n> workers`, `crew-<k> refused: Orchi is <title> (<session id>)`, `crew-<k> released`, `crew-<k> not released: <reason>` |
| Crew → worker | Task | `You are worker-<n> of <crew title>. Invoke the orchi-work skill with: <mode> #<task> --branch <branch> --base <base>. Report to <crew session id>.`; for `research` and `retrieve`, `<mode> <id>: <question>` with no branch |
| Crew → worker | Answer, rework, release | `#<task> answer: <answer>`, `#<task> rework: <what>`, `release` |
| Worker → crew | Progress | `#<task> question: <q>`, `#<task> done: <commit>`, `#<task> blocked: <reason>`, `#<task> not ready: <what>`, `worker-<n> released`, `worker-<n> not released: <reason>` |

### 7.3 Delivery

All pool sessions run in one permission mode, so messages are not held. A message
from a session outside the pool in another mode is held for approval; Orchi tells
the user which session it came from rather than resending.

## 8. Flows

### 8.1 Greenfield idea

1. User → Orchi: the idea.
2. Orchi assigns a free crew as researcher and shows the user the crew's link.
3. The researcher frames the idea with the user, challenges it, and has its workers
   research locally and on the web. It writes the vision documents itself on a
   `docs/vision-<slug>` branch and records the Exploration Issue.
4. Crew → Orchi: `done`. Orchi assigns a planner crew with the Exploration as input
   and releases the researcher.

### 8.2 Feature with research

1. Orchi assigns a planner crew. The planner asks whether research is needed.
2. If yes, it plans an Initiative whose first Epic is `research`, second
   `detail the plan` blocked by it, and later Epics at outcome level.
3. Orchi assigns a researcher crew to the research Epic. When it closes, Orchi
   assigns a planner crew to `detail the plan`.

### 8.3 Delivery of an Epic

1. Orchi assigns a dev lead crew to a `delivery-ready` Epic.
2. The dev lead creates `epic/<tag>-<slug>` from `main`, and for each ready Task a
   `task/<slug>` from the Epic branch. Tasks that touch the same files run one
   after another.
3. Each worker implements its Task with red evidence and one commit, and reports.
4. The dev lead checks each result (branch, base, checks), merges `task/*` into the
   Epic branch, and runs one `orchi-reviewer` pass on the assembled range, with an
   Impeccable design audit when it changes user interface.
5. Confirmed defects go back to the worker that wrote the code as `rework`.
6. The dev lead opens the PR. It is merged per mode (§9). Then the dev lead releases
   its workers and reports `done`.

### 8.4 More planning during delivery

A dev lead files `needs-planning` with `Requested by: <Orchi's title>` and reports
`#<n> follow-up: #<m>` to Orchi. Orchi assigns a free planner crew; when the work
is `delivery-ready`, Orchi gives it to a free dev lead crew by itself.

### 8.5 Design

The [design track](design-track.md) holds the three paths (from scratch,
changing a design, a feature with UI) and the design depth the planner sets.

1. A `design` Epic goes to a designer crew.
2. With the user, the designer runs Impeccable `init` and `document` when
   `PRODUCT.md` or `DESIGN.md` is missing, then `shape`, the direction round, and
   comp approval, and records each direction contract in a surface brief.
3. Its workers build against the approved comp or contract; a question from
   Impeccable during a build reaches the designer as `#<task> question`, and a
   worker that would need a new direction stops with `blocked`. The designer asks
   the user in both modes.

## 9. Modes and autonomy

The user sets one mode at Orchi; Orchi passes it in every assignment.

| | Interactive | Auto |
| --- | --- | --- |
| Who answers a crew | The user, in the crew | Orchi (`<id> answer:`); the user still answers a researcher |
| Autonomy level | Ask (default) or Decide, as in 0.16 | Auto, as in 0.16 |
| Orchi follows crews | Only when a crew comes to it | Yes |

- Every crew asks once per decision and chains no confirmation gates (0.16).
- At every level the user decides deployment; anything destructive or
  irreversible; access, credentials, and money; changes of outcome or scope; and
  what only the user knows. In auto mode Orchi merges a reviewed PR whose checks
  pass, unless the merge deploys (0.16).
- Exploration stays a conversation with the user in both modes; in auto mode a
  greenfield idea waits for the user.
- The mode holds through compaction and resets to interactive when the user runs
  `/orchi` again.

## 10. Branches and worktrees

- Each session has one worktree for its whole life, created at setup.
- Git lets only one worktree check out a branch, so a session holds a branch only
  while it writes on it. A crew creates branches without checking them out
  (`git branch <branch> origin/<base>`) and checks out the Epic branch only to
  merge its workers' branches. A writer detaches when it reports `done`.
- Parallel Tasks run on `task/<slug>` from the Epic branch; the implementer's
  branch check accepts such a branch when its base is the Epic branch.
- On release, every session returns its worktree to a detached `origin/<default>`.
- The dev lead merges a worker's branch only after checking that its commits sit on
  the expected branch above the expected base.
- Workers never push to `main` or open PRs; the dev lead pushes and opens the PR.

## 11. Clearing

| Event | Cleared by | How |
| --- | --- | --- |
| A worker's work is merged or dropped | Its crew | After the worker reports `released` (§6.3) |
| A crew's assignment is done | The crew itself | Last action of its turn, after its workers are cleared; Orchi renames it on its `released` reply |
| Orchi | The user | `/clear`, then `/orchi` |

- A clear is refused for a pinned session, one open on the user's screen, one with
  an unprocessed message or live work, or one that serves Remote Control. The
  clearing session retries on its next wake and reports a refusal that persists.
- A self-clear is dropped when a message arrives before the turn ends, so it is
  always the last action, and the session waits for nothing after it.
- A cleared session keeps its title, parent, folder, branch, and settings.

## 12. Permissions and safety

- Orchi and the pool run in bypass permissions mode, so the classifier cannot deny
  setup or clearing. Every pool session therefore runs every tool without a
  prompt.
- Guards that remain:
  - role skills forbid pushing to `main`, deploying, and destructive actions
    outside the mode's limits;
  - the dev lead's checks before every merge into the Epic branch;
  - the single review before the PR;
  - repository branch protection on `main`, which Orchi recommends at setup;
  - the user's decisions listed in §9.
- Remote Control is off for pool sessions, because a session served over it
  cannot be cleared. The pool cannot be followed from the phone; Orchi can.

## 13. Failure handling

| Failure | Detected by | Response |
| --- | --- | --- |
| A start fails at setup | Orchi or the crew | Report it; setup can be repeated and adds only what is missing |
| A crew or worker lost its role (compaction, manual clear) | Its owner, from its reply | Send the assignment or task again; the skill resumes from GitHub |
| A crew does not answer | Orchi, on its next wake | Check the session; tell the user which crew to open |
| A clear is refused | The clearing session | Retry on the next wake; then tell the user the cause |
| A crew's self-clear did not land | Orchi, at a later wake: a free crew's conversation is not empty | Send `release` again |
| `/orchi` runs in a second session | The new session, from the crews' `parentSessionId` | Point the user to the pool's Orchi and stop; take over only when it is archived or gone (§3.1) |
| No free crew | Orchi | Keep the request on the board; offer to enlarge the pool in the user's next turn |
| A message is held | The sender | Tell the user which session and why |
| The user types into a worker | The worker | Answer the user, then tell its crew what changed |
| Desktop restarts | Orchi, on its next turn | Rebuild from `Orchi pool · <repo>`, claims, and PRs |

## 14. Board

`board.py` reads GitHub and prints JSON; Orchi renders it on request and in its
reports.

| Section | Source |
| --- | --- |
| Initiatives and Epics with progress | Sub-issues closed / total |
| Estimates | The `Estimate` field |
| Waiting for the user | Open Issues labelled `needs-user`, with their last question |
| Blocked by the user | Issues `blocked by` a `needs-user` Issue |
| Ready and waiting for a crew | `delivery-ready` without a claim |
| PRs waiting for a merge | Open PRs linked to claimed Issues |
| Crews | Claims naming `crew-<k>`, joined with the pool group's session list |

## 15. Design track

- The installer always installs Impeccable at a pinned version, in project
  scope, for Claude only, without hooks and with telemetry off, and fails before
  mutation when Node is missing. With `--github` a workflow runs
  `impeccable detect` on changed UI files.
- Impeccable is the only design engine; Taste Skill is not used. SmoothUI is a
  stack default for React web projects, through the shadcn MCP server.
- The designer crew runs Impeccable's interactive steps with the user. Workers use
  `context`, `craft-floor`, the focused commands, and `polish`, and stop with
  `blocked` instead of choosing a direction.
- The dev lead's design audit uses `audit`, `detect`, and `critique` without its
  questions.
- The planner sets design depth (none, brief, Epic), as the
  [design track](design-track.md#design-depth) says.
- `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, and `.impeccable/config.json`
  are committed; `.impeccable/build/`, `review/`, and `mocks/` are ignored except
  an approved comp.

## 16. Installation and migration

- New: `orchi-design`, `orchi-work`, `references/pool.md`, `scripts/board.py`,
  labels `needs-user`, `research`, `design`, the `Estimate` form field,
  Impeccable.
- Removed: `orchi-planner`, `orchi-orchestrator`, `references/team.md`.
- The managed `CLAUDE.md` section stays as it is; the repository's own team list,
  where a project added one, is no longer read and can be removed.
- `docs/out-of-scope/`: delete or rewrite the records this Initiative reopens, in
  the same PR as the change.
- Existing projects are migrated by the maintainer.

## 17. Verification

- **Deterministic tests:** installer (Impeccable step with a fake `npx`, dry run,
  missing Node, idempotence); `board.py` against a fake `gh`; text checks that
  every role in `pool.md` has a skill and that message names agree across skills.
  These prove wording and scripts, not behavior.
- **Live run before the next Epic starts,** on a disposable repository:
  1. `/orchi` builds the pool; five clicks create the workers.
  2. A greenfield idea reaches vision documents and a plan.
  3. A two-Task Epic runs in parallel to a merged PR, with one rework round.
  4. `/compact` in a crew and in a worker mid-task; the role is restored by
     re-sending.
  5. Every crew and worker returns to its free name with an empty conversation.
- **Size:** a rule stays only if it prevents an observed or near-certain costly
  error and is the cheapest way to do so (agreed when features were frozen on
  2026-10-09). The target is no net growth of skill text beyond the new roles.

## 18. Open questions

- Whether Orchi can still show a detached crew in split view, or gives a link.
- Where vision documents live and which documents the set holds.
- The board's form and the unit of estimates.
- Whether projects can add their own roles.
- Whether a crew finds its workers again after clearing itself.
- How the parallel `task/*` protocol avoids the defects that made 0.13 give a whole
  Initiative to one worker.
