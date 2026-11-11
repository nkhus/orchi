---
name: orchi-dashboard
description: Keep an Orchi pool's dashboard - a Crews tab with what waits for the user, Orchi's questions, a summary of how things are going, and every crew by state with a page of its questions and options; and a Board tab with the work as a kanban by level (Initiatives, Epics, Tasks) in columns from the real state, with each item's page and history - published by Orchi and refreshed only when the user asks, by a Haiku subagent from GitHub and the host's session list; beside Orchi's conversation, its buttons send the user's confirmed requests to Orchi (refresh, answer, merge, hold or request changes, status, mode, take or queue by the pool's load, plan, defer, explain an Issue). The refresh changes nothing. Invoke only when Orchi's instructions or a dashboard subagent's task asks for orchi-dashboard by name.
argument-hint: "publish | refresh | collect [--page <url> --language <name>] --mode <on or off> --limit <n> --dir <path>"
user-invocable: false
---

# Orchi dashboard

Arguments: $ARGUMENTS

Orchi keeps the pool's dashboard itself, as the [pool reference](../orchi-core/references/pool.md#dashboard) says; no
session of its own holds it. Orchi publishes the page and starts each refresh, and a Haiku subagent does the reading and
writing, so Orchi's conversation never holds the crews' messages. The refresh only shows: never message a crew or
worker, change Issues, PRs, branches, or repository files, or take a request. The page's buttons send requests to Orchi
alone, as the pool reference's Requests from the dashboard says.

The work directory holds the page copy, `crews.json`, `snapshot.json`, `board.json`, and `summary.json`, and every refresh
reuses it: `.orchi-tmp/dashboard/` in Orchi's own worktree, which Git ignores. Write nowhere else.

## Publish

On `publish`: when the user asks for the dashboard or turns autonomous mode on and there is no page yet, and when Orchi
is updated.

1. Copy this skill's `assets/dashboard.html` to the work directory and replace `{{REPO}}` with the repository's name
   (`gh repo view --json name`).
2. Publish the copy with the Artifact tool: `capabilities` `{"db": {}, "room": {}}`, `icon` `chart`, and the description
   `Status of the Orchi pool`. When a page already exists, pass its URL, so the link stays: the one in this
   conversation, or else the most recently updated one the Artifact tool's `list` finds by its title, `<repo> pool`.
3. Refresh, below, and give the user the link.

## Refresh

On `refresh`: after `publish`, on the page's `Refresh` request, and when the user asks in words; never on a change or a
timer. The pool reference's stall check runs `collect` without `--page`, which leaves the page as it is. Use the page URL
from this conversation, or find it by its title as Publish says.

1. Start one general-purpose subagent with the model `haiku`, in the background, with the task `Invoke the
   orchi-dashboard skill with: collect --page <url> --mode "<on or off>" --limit <pool size> --language <the user's
   language> --dir <work directory>`. For the stall check, leave out `--page` and `--language`.
2. Wait for it only before answering the user about status; otherwise go on. Its reply is one line, `📊 <time> · <n>
   active · <n> wait for you · <n> PRs`, ending with `· <n> need a look` when a crew looks stuck; then act on the
   snapshot's `attention` as the pool reference's Stalls says. Tell the user only when it reads `refresh failed` twice
   in a row.

## Collect

Run by the Haiku subagent. Never rename a session or message anyone, and write only in `--dir`; reply with only the line
the script prints. Load the host's session tools and `ArtifactData` with `ToolSearch` when they are deferred.

1. Read the pool: the host's sessions in the sidebar group `Orchi pool · <repo>`. A crew is a top-level session there
   titled `crew-<k>` or `[<role>] <topic>`, but not `Orchi`; its `name` is `crew-<k>` (the handle the host lists, or its
   title when free). Its workers are the host's sessions titled `worker-<k>.<n>` for its `crew-<k>` (in an older pool,
   those whose `startedBy` is the crew): `total` counts them, `busy` those with `isRunning` true. Write the crews as a
   JSON list to `<dir>/crews.json`: `{"name", "title", "state", "workers": {"busy", "total"}, "last_activity",
   "remote", "cwd"}` (`last_activity` is the host's `lastActivityAt`, `remote` its `remoteControlActive`, `cwd` its
   `cwd`: the script reads the crew's running subagents and commands from it), plus `"stage"` when you know it and
   `"question"` and `"ask"` when it waits; the script adds the role and the Issue. `state` is `working` while the crew
   runs (`isRunning`), `free` while its title is `crew-<k>`, and otherwise `waiting` or `idle`, decided from the crew's
   newest assistant text: read its recent messages (`list_events`, 6) and skip tool calls. It is `waiting` when that
   text asks the user something (`question`: the question in one line, in its own words, keeping a `(user)` or `(user,
   here)` mark as written; `ask`: the text from its first `Question:` line to its end, copied exactly), else `idle`;
   `stage` is a few words from it on what the crew does, or last did, such as `Reviewing the Epic`, and no text means no
   `stage`; `"worker_runs"`, the text after `Background:` in the newest text of each of its workers that does not run
   now, when it ends with that line; `"background"`, the text after `Background:` with its `(pid …)` ending, when an
   idle crew's newest text ends with that line. Read messages only for an assigned crew that is new or whose
   `last_activity` differs from the previous `crews.json`; otherwise copy its `stage`, `question`, `ask`, and
   `background` from that file, and its `state` unless it runs now.
2. Build the snapshot: `python3 .claude/skills/orchi-core/scripts/dashboard.py --crews <dir>/crews.json --mode "<on or
   off>" --out <dir>/snapshot.json --notes <dir>/../orchi/notes.md --limit <n>` (under `~/.claude/skills/` in a
   user-wide installation). It prints the summary line and exits 2 when GitHub could not be read.
3. Without `--page`, stop here. Otherwise, after exit 0, write the summary: read the snapshot's `digest`, `waiting`,
   `attention`, and `questions`, and each crew's `title`, `state`, `stage`, and `questions`, and write
   `<dir>/summary.json`, a JSON list of 3 to 5 `{"lead", "text"}` in `--language` that answers `How are things going?`
   in order: what moved forward, what is in progress, what is stuck and why, what waits for the user, what comes next.
   `lead` is one sentence, `text` one or two plain ones; use only those facts, and no code, file paths, or jargon. Add it
   with `dashboard.py --summary <dir>/summary.json --out <dir>/snapshot.json`.
4. Write the snapshot to the page's store: `ArtifactData` `get` of collection `snapshot`, doc `current`, on `--page`,
   with `out_dir` = `<dir>`, which names its `version` without returning the document; then `set` (exit 0) or `update`
   (exit 2, which keeps the last good data and adds the failure) with `file_path` = the snapshot and `if_version` = that
   version. Omit `if_version` only when the document does not exist yet.

When a step fails, go on where you can; the next refresh tries again.

## The page

The pool reference's Dashboard says what each tab shows. The page says how old it is, links Issues and PRs but never
sessions (it runs sandboxed, and the sandbox blocks links into the Claude app), and needs nothing from you beyond the
snapshot. Opened beside Orchi's conversation in the Claude app, it shows buttons, and each sends Orchi one request,
which the app asks the user to confirm: `Refresh`; an answer to a crew's or Orchi's question, its chosen option and a
note (none for a `(user, here)` question, which counts only in the crew); `Merge`, `Hold`, or `Request changes` on a PR
that waits for the user's yes (`Merge PR #<n>?` in Orchi's notes); `What's up?` on a crew (`Wake it` when it needs a
look); the mode switch; `Explain` on every Issue; and `Take`, `Plan`, `Defer`, or `Resume` on work no crew holds. The
Board says how many crews are busy against the pool size (`--limit`), and `Take` shows while a crew is free or fewer
crews are busy than that; otherwise it reads `Queue`. Elsewhere the page shows no buttons.
