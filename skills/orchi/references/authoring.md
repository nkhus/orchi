# Authoring contracts

Export strict schemas with `schemas --out <directory>`. Unknown fields fail. JSON defines executable structure; Markdown is durable knowledge. Packets/gates are generated, not manually patched.

| Input | Entry point | Bound identity |
| --- | --- | --- |
| Policy | `setup --repo ... --policy ...` | Operator public key, branch, checks, publication/verification policy and budgets |
| ChangeBrief | `start --file ...` | Exact original request, required decisions, normal generated Intent plus first plan |
| Initiative + Intent | `begin --file ... --intent ...` | Contract, manifest, target bytes, original base |
| EpicPlan + design | `plan` / `amend` with `--file --design` | Current head, Target digest, exact design |
| Narrow plan revision | `amend-tasks --affected ... --reason ...` | Same shared design/acceptance and unaffected task contracts |
| ScopeRequest | `scope-acquire --ticket ... --file ...` | Approved directory/action/local choice and ticket snapshot |
| Readiness / WorkerResult | `activate` / `submit` | Fenced task identity and exact packet |
| SyncProposal / ReviewReport | `sync-check` / `sync-review` | Old checkpoint, new upstream, prospective code/knowledge and exact review |
| Checkpoint / Finalization | `checkpoint` / `finalize` | Verified implementation, Current/Target reconciliation and exact candidate |

## Intent

`intent-build --directory ... --initiative ... [--revision N] [--resolutions file.json]` returns the exact `intent` reference. Required files are source, requirements and architecture/README Markdown. Requirement pages declare `kind: requirements`, `requirements: [req-...]` and one matching explicit anchor or heading per ID; do not duplicate the same anchor as a heading slug. Target architecture uses `kind: architecture`. Original source is immutable; removed requirement IDs retain accepted reasons/history.

Initiative fields include ID, outcome, result_kind (`software`, `knowledge`, `investigation`), delivery (`atomic` only), Intent reference and ordered epics. Roadmap entries declare dependencies, contributions, realizations and risks, never future tasks/files. Compact briefs are small authoring inputs, not a weaker lifecycle. Example [fix](../assets/examples/brief-fix.json), [investigation](../assets/examples/brief-investigation.json), [knowledge](../assets/examples/brief-knowledge.json).

## Epic and task sources

EpicPlan binds `based_on`, `intent_digest`, `design: {path: design/N.md, content_hash}`, shared design, acceptance/check mapping, mode and tasks. Markdown uses `kind: reference` and typed requirement/architecture links. A knowledge-only epic has no tasks; an implementation-mode epic has a task DAG, including explicit investigation tasks where useful.

Task fields retain fixed decisions, invariants, delegated choices, current-state understanding, approach, acceptance/check mapping, failure modes, escalation and explicit empty material `open_questions`. Implementation has initial edits; investigation has none. `executor` is agent/human/pair. `write_scope` lists exact directories, actions and allowed-choice names; `max_scope_additions` bounds grants.

Knowledge sources require `view: current` with logical `docs/...md`, or `view: target` with an Intent path/anchor or `req-*`. Code is an exact path; dependency names its producer, path and contract. `delivery: on-demand` retains exact metadata without inline content. `consistency: fixed` rejects changed assumptions; explicit snapshot observations trigger compatibility revalidation. Writes, instructions, read_paths and producer outputs stay fixed. A file source cannot bypass knowledge namespaces.

## Results and knowledge

WorkerResult reports completed/blocked, summary, deviations, extra fixed code reads, observations and optional `documentation_proposals` (target/content/reason). Observations are mandatory for investigations. Proposed docs are Evidence, not permission to write Core.

Checkpoint entries name logical target, replace/retire/revalidate action, content where appropriate, artifact paths, registered checks and reason. Empty artifact lists support knowledge-only results. Every changed product path has one impact disposition; known ownership cannot be silently omitted.

SyncProposal binds actual head and exact upstream, reason, Target assessment/revision flag, exactly required file-conflict resolutions, exactly affected knowledge decisions and registered checks. `sync-draft` enumerates unresolved work; replace markers, do not approve them as content. See [synchronization](synchronization.md).

Finalization disposes every requirement and target architecture node plus cumulative Working entries. `changed` requires accepted Intent history. `unchanged` software architecture cites existing artifacts/checks; `not-applicable` is limited to accepted non-software outcomes with checks. Draft completeness is not semantic proof; independent review remains required.
