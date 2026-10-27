# How a session can start other sessions

Research for the [ENTRY] Initiative, 2026-10-26, on Claude Code 2.1.285 and
Claude Desktop on macOS. "Observed" means a live run in this research; "documented"
means the Claude Code documentation at code.claude.com/docs/en/, read the same
day; "not established" means neither.

## Question

Can a session that no person is typing into start further sessions, keep talking
to them, and show them to the user? Orchi needs this for its entry session, for a
dev lead that runs developers in parallel, and for auto mode.

## Findings

| Mechanism | Starts without a person | Long-lived, messageable | Seen by the user | Evidence |
| --- | --- | --- | --- | --- |
| Desktop `start_session`, from a turn the user started | yes | yes, both ways | sidebar, split view, focus | observed |
| Desktop `start_session`, from a session's first turn (started by its parent's brief) | **no**: the app refuses | — | — | observed |
| Desktop `start_session`, from a turn started by another session's message | **no**: the auto mode classifier denied it | — | — | observed |
| Desktop `start_session` with `own_initiative` (proposal card), from a turn started by another session's message | the card is shown; the session starts only when the user clicks it | yes; it reports to the proposing session | sidebar, nested under the proposer | observed |
| Desktop `detach_session` on a started session with its own worktree | — | unchanged | moves to the top level of the sidebar; no longer archived with its starter, and the starter is no longer told when its turns end | observed |
| Desktop scheduled task created and run by a session | not established: creating the task was denied by the auto mode classifier | — | — | observed denial |
| `claude -p` from Bash | yes | one-shot per call; continued with `--resume <id>` | no | observed |
| `claude --bg` from Bash, in a trusted folder | yes | yes; SendMessage both ways | not in the Desktop sidebar; `ListAgents`, `claude agents --json`; `claude attach <id>` in the Desktop Terminal panel shows and drives it | observed |
| `claude --bg` started by a `--bg` session in auto mode | yes | yes | as above | observed |
| `claude --bg` started by a Desktop core session in its first turn, then `claude attach <id>` in a Terminal tab the core opened | yes | yes; the worker's SendMessage reply reached the core | the core session's Terminal panel tab | observed |
| `claude --bg --remote-control <name>` | yes | yes | claude.ai/code (a `claude.ai/code/session_…` link); not the Desktop sidebar | observed |
| Subagent (Agent tool) | yes, from any turn | resumable by SendMessage to its id or name; cannot talk to the user | the parent's tasks pane | documented |
| Agent teams | yes, from the lead | teammates message each other | not documented for Desktop | documented; experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| Workflow tool | yes, as a background run | one consolidated result, no mid-run input | the parent session | documented |

### Desktop sessions

- The refusal in a child's first turn read: "Start sessions only on the user's own
  words to you here; this turn runs an automated event, another session's message,
  or the task another session gave you. Propose the session instead (initiation
  "own_initiative"), or start it once the user asks you here."
- In a turn started by a message, the same call was denied by the auto mode
  classifier without an explanation. The proposal card (`own_initiative`) was not
  tried; it needs a click by definition.
- A started session reported `parentSessionId` and the starter's permission mode
  (`auto`). A session can show only itself or sessions it started.

### Background sessions

- `claude --bg` in an untrusted folder fails with `Workspace not trusted`; in the
  project's worktree it printed `backgrounded · <id>`.
- A message sent with SendMessage reached the background session, which replied
  by SendMessage; the reply arrived in the sender.
- A background session in auto mode ran `claude --bg …` through Bash on its own
  and the grandchild finished its task.
- Documented: an idle unattended background session's process stops after about
  an hour and resumes on attach or reply; a dispatched session takes the
  directory's `permissions.defaultMode`, else its source session's mode, and moves
  into `.claude/worktrees/` before editing. The feature is a research preview.

### Subagents

Documented: `isolation: "worktree"`, three nesting layers by default
(`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`), 20 running at once
(`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`), no `AskUserQuestion`, permission prompts
surface in the main session.

## Consequences for Orchi

1. **Desktop sessions are created only in the user's turn.** The entry session can
   create the sessions the user will talk to (research, planner, dev lead,
   designer) while the user talks to it. No Desktop session can create one
   unattended, so auto mode cannot rely on Desktop sessions created later.
2. **Unattended creation exists outside the Desktop sidebar.** `claude --bg`
   sessions start, nest, and exchange messages without a person, in auto mode,
   and the user can open any of them with `claude attach` in the Desktop Terminal
   panel. They are absent from the sidebar and from split view.
3. **Workers that never talk to the user fit subagents.** A dev lead can run
   developers in parallel worktrees and continue each by SendMessage, within 20
   concurrent and three nesting layers.

Options for the design:

| Option | User-facing roles | Unattended workers | Auto mode | Cost |
| --- | --- | --- | --- | --- |
| A. Desktop only | Desktop sessions from the entry, in the user's turn | subagents | entry pre-creates sessions when the user switches to auto; reuses them by message | Workers invisible as sessions; no new sessions while unattended |
| B. Background sessions | `claude --bg`, opened with `claude attach` | `claude --bg` or subagents | fully autonomous | Not in the sidebar; research preview; trusted folder needed |
| C. Hybrid | Desktop sessions from the entry, in the user's turn | subagents; `claude --bg` when a worker needs its own long context | the entry starts `claude --bg` sessions when no idle Desktop session fits | Two kinds of session to track |

No observed mechanism creates a session in the Desktop sidebar without a person:
`start_session` needs the user's turn or a click on a proposal card, and every CLI
session (`-p`, `--bg`, `--bg --remote-control`) stays out of the sidebar.

### Session pool

Observed in later runs the same day:

- A session started in bypass permissions mode is still refused by the app in
  its first turn and in a turn started by a message, so the refusal does not
  depend on the permission mode.
- In a turn the user typed, a pool session in auto mode created 6 of 15 workers;
  the auto mode classifier denied the rest without explanation, also when the
  calls were made one at a time.
- No tool nests a session under another one after it starts. A session can
  rename any session, message it, and ask it to clear itself (`clear_session`
  with `self`); it can clear directly only itself and sessions it started, and a
  starter can no longer clear a session it detached.
- A renamed session does not learn its new title.
- In one user turn, a session in bypass permissions mode started six sessions,
  moved them to the top level, created two sidebar groups, and filed a crew with
  its two workers into each group, without a refusal or an approval prompt. Each
  crew then directed its workers by message.
- Sessions started in bypass permissions mode had Remote Control off; sessions
  started in auto mode had it on.
- The app reuses worktree folder names of earlier sessions for new sessions.
- A crew in bypass permissions mode that ended its first turn with a reply
  button created all three workers, nested under it, when the user clicked the
  button: the click sends the user's message and starts a user turn.
- A crew that proposed its three workers as cards in its first turn got all
  three nested under it when the user started the cards, and cleared them
  directly like workers it started itself.
- A crew cleared its nested workers directly, and then cleared itself with
  `self` on Orchi's request; each transcript was empty afterwards. A cleared
  session keeps its title, parent, folder, branch, and settings, and its Remote
  Control state; clearing does not touch its worktree.

Observed in the first full pool run (Orchi 0.18, a disposable repository):

- A message typed over Remote Control, in a session the user started, could not
  start sessions; the same request typed in the desktop app could.
- A detached crew still reports its starter as `parentSessionId`, which
  identifies the pool's Orchi.
- `/orchi` in a second session adopted the existing pool without a word,
  although the crews reported to the first Orchi.
- A crew wrote a wrong session id for itself into a worker's brief and corrected
  it by message; reading the id from the host avoids the guess.
- A crew's `released` reply reached Orchi before the crew's self-clear landed, so
  a rename that waited for an empty conversation never happened unless another
  event woke Orchi.

## Not established

- Whether a core session can start a sub-session in a turn the user started by
  typing into it.
- Whether a turn started by a sub-session's completion event, right after the
  user's turn, may start further sub-sessions, so that one user request lets a
  core create workers one after another.
- Whether `run_scheduled_task` can start a session from a message-started turn.
- Whether the auto mode classifier denies `start_session` consistently or only
  for this brief.
- How a `--bg` session behaves after compaction and after the one-hour idle stop.
