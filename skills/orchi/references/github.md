# GitHub conventions

Use when creating, editing, relating, claiming, or closing Issues and PRs. A
repository's own issue rules and templates take precedence; these are defaults.
Prefer current `gh` help over remembered flags, since relationship support changes.

## Hierarchy and dependencies

Label each issue with exactly one type: `Initiative`, `Epic`, or `Task`. Create
missing labels deliberately. Title parents by outcome, for example
`Epic: <bounded delivery result>`. Attach children as native sub-issues
(`gh issue create --parent <n>` or `gh issue edit <parent> --add-sub-issue <n>`);
do not maintain a second checklist of the same children in the body.

A parent relationship means "part of this outcome", not "blocked by". Use native
`blocked by`/`blocking` relationships only for real ordering constraints, and add
only direct ones. Create all issues first, then add dependencies, then verify with
`gh issue view <n> --json parent,subIssues,blockedBy,blocking`. Report any
relationship the API could not establish.

Search open and closed issues for duplicates before creating. Never close, delete,
or rewrite existing issues merely to tidy the hierarchy without user authorization.

## Issue content

Keep bodies short and link authoritative documents and stable requirement IDs
instead of copying them.

- **Epic:** outcome; source documents; in-scope and out-of-scope; approach and
  design (or a link to it); direct dependencies; exit criteria; open questions.
- **Task:** parent; one reviewable outcome; sources; acceptance and verification;
  dependencies when they are not implied by Task order.
- **Initiative:** original request, agreed outcome, and a link to
  `docs/initiatives/<slug>/README.md` on the initiative branch.

## Ownership and status

`in-progress` marks owned work. Record the owner as an assignee plus a work
reference in the body: assistant session or identifier, branch, and PR. Re-read
the issue after claiming; resolve races rather than overwriting another claim.
Close with the reason that distinguishes completed from cancelled work.

## Pull requests

Use Conventional Commits for commit subjects, PR titles, and squash titles:
`<type>(<scope>)<!>: <imperative description>`. Squash-merge. Describe the whole
reviewed outcome in the squash message, not an intermediate commit. Closing
keywords only work for PRs into the default branch; close issues explicitly after
merging into an Initiative branch.
