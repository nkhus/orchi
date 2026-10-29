---
name: orchi-dashboard
description: Keep an Orchi pool's dashboard - a page of every crew, ordered by state (waiting for the user, working, idle and doing nothing, free), with what it does now and the Initiative and Epic of its work, and the backlog as a tree of Initiatives, Epics, and Tasks with their progress, PRs, and the planning queue - published by Orchi and refreshed by a Haiku subagent from GitHub and the host's session list. Read-only; it changes nothing and takes no requests. Invoke only when Orchi's instructions or a dashboard subagent's task asks for orchi-dashboard by name.
argument-hint: "publish | refresh | collect --page <url> --mode <on or off> --dir <path>"
user-invocable: false
---

# Orchi dashboard

Arguments: $ARGUMENTS

Orchi keeps the pool's dashboard itself, as the [pool reference](../orchi-core/references/pool.md#dashboard)
says; no session of its own holds it. Orchi publishes the page and starts each refresh, and a Haiku subagent
does the reading and writing, so Orchi's conversation never holds the crews' messages. The dashboard only
shows: never message a crew or worker, change Issues, PRs, branches, or repository files, or take a request.

The work directory holds the page copy, `crews.json`, and `snapshot.json`, and
every refresh reuses it: `.orchi-tmp/dashboard/` in Orchi's own worktree, which Git
ignores. Write nowhere else.

## Publish

On `publish`: when the user asks for the dashboard or turns autonomous mode on and there is no page yet, and
when Orchi is updated.

1. Copy this skill's `assets/dashboard.html` to the work directory and replace
   `{{REPO}}` with the repository's name (`gh repo view --json name`).
2. Publish the copy with the Artifact tool: `capabilities` `{"db": {}}`, `icon`
   `chart`, and the description `Status of the Orchi pool`. When a page already exists, pass its URL, so the
   link stays: the one in this conversation, or else the most recently updated one the Artifact tool's
   `list` finds by its title, `<repo> pool`.
3. Refresh, below, and give the user the link.

## Refresh

On `refresh`: after `publish`, before Orchi answers the user about status, when the user asks, and when
something changed for the user (a crew asks them something, starts or finishes work, or is released; a PR
opens or merges; the mode changes). Refresh only then; never schedule a timer. Use the page URL from this
conversation, or find it by its title as Publish says.

1. Start one general-purpose subagent with the model `haiku`, in the background, with the task
   `Invoke the orchi-dashboard skill with: collect --page <url> --mode "<on or off>" --dir <work directory>`.
2. Wait for it only before answering the user about status; otherwise go on. Its reply is one line,
   `📊 <time> · <n> active · <n> wait for you · <n> PRs`; tell the user only when it reads `refresh failed`
   twice in a row.

## Collect

Run by the Haiku subagent. Never rename a session or message anyone, and write
only in `--dir`; reply with only the line the script prints.

Load the host's session tools and `ArtifactData` with `ToolSearch` when they are deferred.

1. Read the pool: the host's sessions in the sidebar group `Orchi pool · <repo>`.
   A crew is a top-level session there titled `crew-<k>` or `[<role>] <topic>`,
   but not `Orchi`; its `name` is `crew-<k>` (the handle the host
   lists, or its title when free). Its workers are the sessions whose
   `startedBy` is the crew: `total` counts them, `busy` those with `isRunning`
   true. Write the crews as a JSON list to `<dir>/crews.json`: `{"name",
   "title", "state", "workers": {"busy", "total"}, "last_activity", "remote"}`
   (`last_activity` is the host's `lastActivityAt`, `remote` its `remoteControlActive`), plus `"stage"` when
   you know it and `"question"` when it waits; the script adds the role and the
   Issue. `state` is `working` while the crew runs (`isRunning`), `free` while
   its title is `crew-<k>`, and otherwise `waiting` or `idle`, decided from the
   crew's newest assistant text: read its recent messages (`list_events`, 6)
   and skip tool calls. It is `waiting` when that text asks the user something
   (the question in one line, in its own words), else `idle`; `stage` is a few
   words from it on what the crew does, or last did, such as `Reviewing the Epic`, and no text means no
   `stage`; `question` only while it waits. Read messages only for an assigned crew that is new or whose
   `last_activity` differs from the previous `crews.json`; otherwise copy its `stage` and `question` from that
   file, and its `state` unless it runs now.
2. Build the snapshot:
   `python3 .claude/skills/orchi-core/scripts/dashboard.py --crews <dir>/crews.json --mode "<on or off>" --out <dir>/snapshot.json`
   (under `~/.claude/skills/` in a user-wide installation). It prints the
   summary line and exits 2 when GitHub could not be read.
3. Write it to the page's store: `ArtifactData` `get` of collection `snapshot`,
   doc `current`, on `--page`, with `out_dir` = `<dir>`, which names its
   `version` without returning the document; then `set` (exit 0) or `update`
   (exit 2, which keeps the last good data and adds the failure) with
   `file_path` = the snapshot and `if_version` = that version. Omit
   `if_version` only when the document does not exist yet.

When a step fails, go on where you can; the next refresh tries again.

## The page

Every crew is in one list, ordered by state: waiting for the user, working, idle, then free. An idle crew is
not running, asks nothing, and has no busy worker: its card says `Idle · doing nothing`, shows its stage as
the last step, and says since when nothing has run; a crew whose workers run counts as working. A crew with
Remote Control on is marked, because it cannot be cleared. The page links Issues and PRs, never sessions:
it runs sandboxed, and the sandbox blocks links into the Claude app.
