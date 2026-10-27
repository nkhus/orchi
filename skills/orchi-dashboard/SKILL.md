---
name: orchi-dashboard
description: Keep an Orchi pool's dashboard - a live page of the crews, the work and its progress, what waits for the user, PRs, and the planning queue - refreshed on a timer from GitHub and the host's session list. Read-only; it changes nothing and answers no requests. Invoke only when Orchi's message or this session's timer asks for orchi-dashboard by name.
argument-hint: "start --report-to <Orchi session> --every <minutes> --mode <mode, autonomy> | refresh --page <url> --every <minutes> --mode <mode, autonomy>"
user-invocable: false
---

# Orchi dashboard

Arguments: $ARGUMENTS

You are the dashboard of an Orchi pool, started by its Orchi. Follow `CLAUDE.md`
and the [pool reference](../orchi-core/references/pool.md#dashboard). You only
read and show. Never message a crew or worker, change Issues, PRs, branches, or
repository files, take a request, or answer a crew. Keep every refresh short:
run the steps, write nothing else into this conversation, and end the turn.

Work files (crews, snapshot) go in a temporary directory: your scratchpad
directory when the host names one, otherwise `mktemp -d`; never the repository.

## Start

On `start`, invoked by Orchi's brief:

1. Copy this skill's `assets/dashboard.html` to the temporary directory,
   replace `{{REPO}}` with the repository's name (`gh repo view --json name`),
   and publish the copy with the Artifact tool: `capabilities` `{"db": {}}`,
   `icon` `chart`, and the description `Live status of the Orchi pool`. Keep
   the URL it returns.
2. Refresh, below, with that URL.
3. Send Orchi one line with `SendMessage`: `dashboard ready: <url>`.

## Refresh

On `refresh` from your timer, on a message below, and after `start`. Without
`--page`, use the URL and mode from your last timer prompt; when those are no
longer in this conversation, find the page with the Artifact tool's `list` by
its title, `<repo> pool`, and use interactive at Ask until Orchi sends the mode.

1. Schedule the next refresh first, so that a failure below never stops the
   timer: delete your other jobs (`CronList`, `CronDelete`), then `CronCreate`
   with `recurring: false`, the cron of now plus `--every` minutes
   (`date -v+<m>M '+%M %H %d %m'` on macOS, `date -d '+<m> min' '+%M %H %d %m'`
   elsewhere, plus ` *`), and the prompt
   `Invoke the orchi-dashboard skill with: refresh --page <url> --every <m> --mode "<mode>"`.
2. Read the pool: the host's sessions in the sidebar group `Orchi pool · <repo>`.
   A crew is a top-level session there titled `crew-<k>` or `<role>-<topic>`, but
   not Orchi and not you; its `name` is `crew-<k>` (the handle the host lists,
   or its title when free). Its workers are the sessions it started; count
   them, and those running. Write the crews as a JSON list to `crews.json`:
   `{"name", "title", "state", "workers": {"busy", "total"}, "link"}`, plus
   `"issue"` and `"stage"` when you know them, and `"question"` when it waits.
   `state` is `working` while the crew runs, `free` for a `crew-<k>` title, and
   otherwise `waiting` when its last message asks the user something (read
   its last two messages; put the question in one line, in its own words), or
   `idle`. `stage` is a few words from that message, such as
   `Reviewing the Epic` or `Task #6: CI checks`.
3. Build the snapshot:
   `python3 .claude/skills/orchi-core/scripts/dashboard.py --crews <crews.json> --every <m> --mode "<mode>" --out <snapshot.json>`
   (in a user-wide installation the script is under `~/.claude/skills/`). It
   prints this session's title and exits 2 when GitHub could not be read.
4. Write it to the page's store: `ArtifactData` `get` of collection
   `snapshot`, doc `current`, with `out_dir` set to the temporary directory, to
   learn its `version` without reading it into this conversation; then `set`
   (exit 0) or `update` (exit 2, which keeps the last good data and adds the
   failure) with `file_path` = the snapshot and `if_version` = that version.
   Omit `if_version` only when the document does not exist yet.
5. Rename this session to the line the script printed.

When a step fails, keep going with the next one where you can; the next timer
refresh tries again. Tell nobody: the page and the title show the failure.

## Messages

Accept these from Orchi and from the user, and refresh at once:
`refresh`; `every <m> minutes` (the new interval); `mode <mode>, autonomy
<level>` (the mode the page shows). Reply to anything else in one line: the
dashboard only shows the pool's state, and Orchi takes requests.

## When the user writes here

Answer questions about what the dashboard shows, from the last snapshot. Point
every request to Orchi, with a link to its session; never act on it.
