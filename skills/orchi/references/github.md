# GitHub conventions

Use when creating, editing, relating, or closing Issues and PRs. A repository's
own issue rules and templates take precedence; these are defaults. Prefer current
`gh` help over remembered flags, since relationship support changes. Ownership and
claiming are in [execution](execution.md).

## Setup

Orchi uses the labels `Initiative`, `Epic`, `Task`, and `in-progress`. A project
installed with `--github` already has them, plus issue templates, a PR template,
and a documentation check workflow. Otherwise, create missing labels deliberately
with a stable description; do not invent variants.

## Hierarchy and dependencies

Give each tracked issue exactly one type label. Title parents by outcome, for
example `Epic: <bounded delivery result>`. Attach children as native sub-issues
(`gh issue create --parent <n>` or `gh issue edit <parent> --add-sub-issue <n>`);
do not keep a second checklist of the same children in the body.

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

- **Initiative:** original request, agreed outcome, and a link to the plan on the
  Initiative branch.
- **Epic:** outcome; sources; in and out of scope; design or a link to it; direct
  dependencies; exit criteria; open questions.
- **Task:** parent; one reviewable outcome; sources; acceptance and verification;
  dependencies not implied by Task order.

## Pull requests

Use Conventional Commits for commit subjects, PR titles, and squash titles:
`<type>(<scope>)<!>: <imperative description>`. Squash-merge, describing the whole
reviewed outcome rather than an intermediate commit. The PR body contains:

- **Summary** and linked issues;
- **Verification:** commands, results, and the candidate commit;
- **Documentation impact:** pages updated, or why none change (required);
- **Handoff:** filled only while work is interrupted, in the format from
  [execution](execution.md#hand-off-and-resume).
