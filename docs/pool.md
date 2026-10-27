# Pool

In Claude Desktop, one session becomes Orchi, the user's single entry, and runs
every request through a pool of crews and their workers. The pool adds roles and
a message protocol on top of the [workflow](workflow.md), not a controller:
GitHub holds every fact it relies on, and any session can restart and catch up.

## Structure

| Part | Defined in |
| --- | --- |
| The entry: building the pool, routing, assigning, answering in auto mode | `skills/orchi/SKILL.md` |
| Sessions, roles, messages, modes, workers, release, and clearing | `skills/orchi-core/references/pool.md` |
| A worker's task in a mode (`implement`, `fix`, `design`, `research`, `retrieve`) | `skills/orchi-work/SKILL.md` |
| Crew roles | `orchi-explore` (researcher), `orchi-plan` and `orchi-standards` (planner), `orchi-design` (designer), `orchi-deliver` (dev lead) |

Setup steps for a project are in [pool setup](installation.md#pool-setup).

## Limits

The host behavior the pool depends on, observed in live runs in Claude Desktop
on macOS (2026-10-26, Claude Code 2.1.285):

- A session can start sessions only in a turn the user started, typed in the
  desktop app; a reply-button click starts such a turn, and a message typed over
  Remote Control does not.
- No tool nests a session under another one after it starts; a starter can
  detach a session it started to the top level.
- A session clears directly only itself and the sessions it started and has not
  detached. A clear is refused for a session that is pinned, open on screen,
  holding an unprocessed message or live work, or served over Remote Control.
- A renamed session does not learn its title.
- A message from a session in another permission mode is held for approval.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Orchi is the single entry, a product manager: it routes, assigns, answers crews in auto mode, and leads acceptance, and does no planning, research, design, or development itself | The user talks to one session, and every piece of work runs in a session the user can open | The two symmetric hubs (planner and orchestrator), which made the user choose a hub per request | [#42](https://github.com/nkhus/orchi/pull/42) |
| Crew roles are researcher, planner, designer, and dev lead; several crews may hold one role; a role is a skill the crew invokes, and adding one adds a skill and a row to the pool reference's role table | Invoking the skill again restores a lost role, and a new role changes no other session | Roles as `--agent` agents ([out of scope](out-of-scope/team-roles-as-agents.md)) | [#42](https://github.com/nkhus/orchi/pull/42), designer in [#43](https://github.com/nkhus/orchi/pull/43) |
| Crews talk to the user and give all repository work to their workers, including review repairs and merge conflicts; workers talk only to their crew | The crew keeps the conversation with the user while each worker keeps one worktree and the context of its tasks | None recorded | [#42](https://github.com/nkhus/orchi/pull/42) |
| All work runs in sessions in the Desktop sidebar; the pool supports Claude Desktop only | The user must be able to see and open everything that runs | `claude --bg` background sessions and long-lived subagents as workers, which do not appear in the sidebar | [#42](https://github.com/nkhus/orchi/pull/42) |
| The pool is built once, in the user's turn: 5 crews of 3 workers unless the user names other numbers; sessions are reused by renaming and clearing, and none is created after setup | A session can start others only in a turn the user started, so a pool built later could not grow unattended | Starting sessions on demand, which the app refuses in turns a message started; archiving or deleting sessions ([out of scope](out-of-scope/session-lifecycle.md)) | [#42](https://github.com/nkhus/orchi/pull/42) |
| Crews sit at the top level in the sidebar group `Orchi pool · <repo>`; each crew's workers are nested under it | No tool nests a session later, so only the crew can start its workers nested; the group lets Orchi find its crews after a restart | None recorded | [#42](https://github.com/nkhus/orchi/pull/42) |
| The user creates a crew's workers with one click on a `Create workers` reply button; start cards, then a typed `yes`, are the fallbacks | The click is the user's turn in which the crew may start sessions | Asking the user to type a command in each crew | [#42](https://github.com/nkhus/orchi/pull/42) |
| Titles: `crew-<k>` when free, `<role>-<topic>` when assigned, `worker-<n>` always; the assignment states the crew's new title | The user reads the sidebar to find work; a renamed session does not learn its title | None recorded | [#42](https://github.com/nkhus/orchi/pull/42) |
| A crew clears its workers after they reply `released`, and clears itself as the last action of its turn on Orchi's `release`; Orchi renames it back on its `released` reply; only the user clears Orchi | A session can clear only itself and the sessions it started and kept nested, and the reply reaches Orchi before the self-clear lands | Orchi clearing crews, which it cannot do once it detached them; renaming after the conversation is empty, which never happened without another wake | [#42](https://github.com/nkhus/orchi/pull/42) |
| Remote Control is off for pool sessions | A session served over Remote Control cannot be cleared | None recorded | [#42](https://github.com/nkhus/orchi/pull/42) |
| Orchi and the whole pool run in bypass permissions mode; role instructions, the dev lead's checks, the single review, and branch protection are the guards | In auto mode the classifier denied about half of the session starts in user turns; in bypass permissions mode none was denied | Auto mode for pool sessions | [#42](https://github.com/nkhus/orchi/pull/42) |
| Two work modes, set at Orchi for the whole pool: interactive (autonomy Ask or Decide) and auto (autonomy Auto, Orchi answers crews); at every level the user decides deployment, destructive and irreversible actions, access, and scope, and a merge that deploys waits | Long autonomous work needs someone to answer crews, and the user's authority must not depend on the mode | None recorded | [#42](https://github.com/nkhus/orchi/pull/42), levels from [#36](https://github.com/nkhus/orchi/pull/36) |
| A session accepts assignments, tasks, mode changes, and releases only from its owner: a crew from Orchi, a worker from its crew | Any other message could come from anywhere and carries no authority | None recorded | [#36](https://github.com/nkhus/orchi/pull/36), kept in [#42](https://github.com/nkhus/orchi/pull/42) |
| A pool has one Orchi, the session that started its crews or the one they last accepted a takeover from; a second `/orchi` points to it and takes over only when the host shows it archived or gone | In a live run a second `/orchi` silently adopted a pool whose crews reported to the first | Any session adopting the pool | [#42](https://github.com/nkhus/orchi/pull/42) |
| A session reads its own id from the host each time it writes it | In a live run a crew gave a worker a wrong id from memory | Ids from memory or from other messages | [#42](https://github.com/nkhus/orchi/pull/42) |
| A worker keeps its context until the PR with its work is merged and takes the crew's next tasks meanwhile; rework goes to the worker that wrote the Task | Rework reaches the session that has the context, and an Epic with more Tasks than workers keeps moving | Releasing a worker when it reports `done` | [#42](https://github.com/nkhus/orchi/pull/42) |
| A dev lead runs Tasks in parallel only when they touch different files, each on `task/<slug>` from the Epic branch, and merges a worker's branch only after checking its commits and base | Git lets one worktree check out a branch at a time, and disjoint files keep parallel merges clean | One worker for a whole Initiative, as the team roles had it | [#42](https://github.com/nkhus/orchi/pull/42) |
