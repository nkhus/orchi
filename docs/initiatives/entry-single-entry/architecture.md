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
  turn.

### 3.2 Crew

- **Created by** Orchi at setup, detached to the top level, in its own worktree.
- **Title:** `crew-<k>` when free, `<role>-<topic>` when assigned. `<topic>` is
  the tag of the Issue it holds, for example `planner-pay` or `dev-lead-pay-token`.
- **Does:** holds one assignment in one role, talks to the user (interactive) or
  Orchi (auto), and delegates all writing to its workers. It may run read-only
  subagents (`orchi-scout`, `orchi-reviewer`, `orchi-researcher`) for checks.
- **Never:** writes product code or documents itself, takes a second assignment,
  or starts sessions after setup.

### 3.3 Worker

- **Created by** its crew in the user's turn that the crew's setup button starts;
  nested under the crew, in its own worktree. Title always `worker-<n>`.
- **Does:** one task at a time from its crew, on the branch the crew names; may
  run read-only subagents.
- **Talks** to its crew only, by message; never to the user.

### 3.4 Roles

| Role | Skill | Holds | Workers do | Ends with |
| --- | --- | --- | --- | --- |
| Researcher | `orchi-explore` | An idea, as a challenger, with the user | Local and web research, option design, vision documents | Committed vision documents and an Exploration Issue |
| Planner | `orchi-plan` | One plan with the user | Retrieval, drafting Issue bodies | `delivery-ready` Task, Epic, or Initiative |
| Designer | `orchi-design` (new) | Product context and direction with the user, through Impeccable | UI built against the approved direction | Approved direction, `PRODUCT.md`/`DESIGN.md`, design Tasks |
| Dev lead | `orchi-deliver` | One Epic, Initiative, or standalone Task | One Task each on `task/*` | A reviewed PR, merged per mode |

A worker runs `orchi-work` (new), which carries the writer contracts that the
`orchi-implementer`, `orchi-fixer`, and `orchi-designer` subagent roles carry
today: readiness check, red evidence, one commit per run, the report format.

Adding a role means adding its skill and one row to the role table in
`references/pool.md`; Orchi routes by that table.

## 4. Package

| Skill | Today | Target |
| --- | --- | --- |
| `orchi` | Core workflow, references, roles, scripts | The entry: `/orchi` makes a session Orchi (`disable-model-invocation: true`). Still holds references, subagent roles, and scripts |
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
holds the authority to build the pool and to merge in auto mode.

## 5. State model

### 5.1 GitHub

Kept: type labels, sub-issues, `blocked by`, `in-progress`, assignees,
`Exploration`, `needs-planning`, `delivery-ready`, `retro`, `Requested by:`,
decision logs, PR sections.

Changed or added:

| Item | Meaning | Written by |
| --- | --- | --- |
| Work reference `Assigned to crew-<k> (<session id>) by Orchi on <date>` | Which crew holds the Issue; replaces `Dispatched to` and `Planning by` | Orchi; the crew adopts it |
| Label `needs-user` | A crew waits for the user; the question is the latest comment | The crew; removed when answered |
| Label `research`, `design` | Epic type, beside `Epic` | The planner |
| Field `Estimate` in the Task and Epic forms | Size for the board | The planner |
| Comment `Task <n> on worker-<m>, branch task/<slug>` | Which worker holds a Task | The dev lead |

### 5.2 Host

- **Pool membership:** Orchi files every crew into the sidebar group
  `Orchi pool · <repo>`; `list_sessions` with that group lists the crews after any
  restart. Workers are found through their crew (`parentSessionId`).
- **Free crew:** no open Issue claim names it and its conversation is empty.
- **Free worker:** its crew holds no task for it and its conversation is empty.

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
- **waiting-for-user:** the crew adds `needs-user` and asks; in auto mode it asks
  Orchi instead.
- **done:** planner → `planned` or `declined`; researcher → documents committed;
  designer → direction approved; dev lead → PR merged.
- **releasing:** the crew releases its workers (§6.3), clears itself as the last
  action of its turn, and Orchi renames it `crew-<k>`.

### 6.3 Worker

```
free ──task──► working ──► reported ──rework──► working
  ▲                            │
  │                            ▼ (the crew's PR is merged, or the task is dropped)
  └──── cleared ◄────────── releasing
```

A worker keeps its context until the PR that contains its work is merged, so the
same worker takes rework, as agreed for 0.13 and 0.17. Release, in this order:

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

### 7.2 Catalog

| From → to | When | Message |
| --- | --- | --- |
| Orchi → crew | Assignment | `You are <title> (crew-<k>). Invoke the <role skill> skill with: <args>. Mode: <mode>, autonomy: <level>, set by the user on <date>.` |
| Orchi → crew | Mode change | `mode <mode>, autonomy <level>` |
| Orchi → crew | Release | `release` |
| Crew → Orchi | Progress | `<id> started`, `<id> needs the user: <question>`, `<id> needs planning: #<n>`, `<id> ready: #<n>`, `<id> PR ready: <url>`, `<id> done: <url>`, `released`, `not released: <reason>` |
| Crew → worker | Task | `You are worker-<n> of <crew title>. Invoke the orchi-work skill with: <mode> #<task> --branch <branch> --base <base>. Report to <crew session id>.` |
| Crew → worker | Rework, release | `#<task> rework: <what>`, `release` |
| Worker → crew | Progress | `#<task> question: <q>`, `#<task> done: <commit>`, `#<task> blocked: <reason>`, `released`, `not released: <reason>` |

### 7.3 Delivery

All pool sessions run in one permission mode, so messages are not held. A message
from a session outside the pool in another mode is held for approval; Orchi tells
the user which session it came from rather than resending.

## 8. Flows

### 8.1 Greenfield idea

1. User → Orchi: the idea.
2. Orchi assigns a free crew as researcher and shows the user the crew's link.
3. The researcher frames the idea with the user, challenges it, and has its workers
   research locally and on the web. It commits vision documents through a
   worker on a `docs/vision-<slug>` branch and records the Exploration Issue.
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

A dev lead files `needs-planning` with `Requested by: <crew title>` and reports
`needs planning: #<n>` to Orchi. Orchi assigns a free planner crew; when the work
is `delivery-ready`, Orchi gives it to the dev lead that asked.

### 8.5 Design

1. A `design` Epic goes to a designer crew.
2. With the user, the designer runs Impeccable `init` (when `PRODUCT.md` is
   missing), `shape`, and the direction choice, and records the brief and the
   approved comp in the Issue.
3. Its workers build against the approved direction; a worker that would need a
   new direction stops with `blocked`, and the designer asks the user.

## 9. Modes and autonomy

The user sets one mode at Orchi; Orchi passes it in every assignment.

| | Interactive | Auto |
| --- | --- | --- |
| Who answers a crew | The user, in the crew | Orchi |
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
- A crew and its workers switch their worktrees to the branch of the current
  assignment or task, and return them to a detached `origin/<default>` on release.
- Two sessions never check out the same branch; Git refuses it.
- The dev lead merges a worker's branch only after checking that its commits sit on
  the expected branch above the expected base.
- Workers never push to `main` or open PRs; the dev lead pushes and opens the PR.

## 11. Clearing

| Event | Cleared by | How |
| --- | --- | --- |
| A worker's work is merged or dropped | Its crew | After the worker reports `released` (§6.3) |
| A crew's assignment is done | The crew itself | Last action of its turn, after its workers are cleared; Orchi then renames it |
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

- The installer always installs Impeccable at a pinned version, for Claude only,
  without hooks, and fails before mutation when Node 18.19+ is missing.
- The designer crew runs Impeccable's interactive steps with the user. Workers use
  `context`, `craft-floor`, the focused commands, and `polish`, and stop with
  `blocked` instead of choosing a direction.
- The dev lead's design audit uses `audit`, `detect`, and `critique` without its
  questions.
- `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, and `.impeccable/config.json`
  are committed; `.impeccable/build/`, `review/`, and `mocks/` are ignored except
  an approved comp.

## 16. Installation and migration

- New: `orchi-design`, `orchi-work`, `references/pool.md`, `scripts/board.py`,
  labels `needs-user`, `research`, `design`, the `Estimate` form field,
  Impeccable.
- Removed: `orchi-planner`, `orchi-orchestrator`, `references/team.md`.
- The managed `CLAUDE.md` section drops the team list and says: type `/orchi` in
  one session in bypass permissions mode.
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
