# Maintain knowledge alongside delivery

Use for requirements, design, Core updates, or branch synchronization. Follow the
repository's documentation rules and ownership map when it has them. "Core" means
the project's canonical documentation of current behavior at its normal paths.

| Material | Meaning and location |
| --- | --- |
| Main Core | Implemented, integrated behavior on main; integration is not deployment evidence |
| Initiative plan | Agreed target, decisions, and open questions in `docs/initiatives/<key>-<slug>/` on its branch |
| Branch Core | Normal Core paths updated with implemented branch behavior, read with that branch's code and checks |
| Evidence | Checks, reviews, and observations in issues and PRs; supports claims without becoming requirements |

Read integrated facts from main, Initiative working facts from its branch, and an
Epic candidate from its branch; state the branch or commit when the distinction
matters. Use [retrieval](retrieval.md) for documentation and `rg` for code. Read the
owning source, not only search snippets. Proposed requirements do not prove
implementation, and a passing unit test does not establish external provider
behavior, production rollout, or operational readiness.

## Update with the code

For each behavioral or architectural change, identify the owning pages and update
them in the same branch. Fix indexes and links when pages move or appear. Check
whether examples, public contracts, runbooks, and known limitations change too.
Record the result in the PR's `Documentation impact` section; if nothing changes,
give the reason there instead of creating a no-op Task.

When an Epic merges, its Core changes become the Initiative branch's working Core;
they reach main only with final Initiative integration. Keep plans and unresolved
decisions in the Initiative documentation, label proposed behavior clearly, and
never present unimplemented plans as current behavior. The
`docs/initiatives/<key>-<slug>/` area is delivery history, not another product owner;
link it as such if indexed. A standalone Epic can keep its plan in its issue.

## Reconcile

Before an Epic merge, compare its implementation and acceptance with its changed
Core pages. Before the Initiative merge, check all agreed requirements and
cross-Epic contracts against the combined result. Resolve omissions, or agree any
deferred or changed outcome explicitly instead of marking it implemented. Preserve
the original request and meaningful decisions in the Initiative history.

When main or the Initiative target moves, inspect both sides of code and docs,
reconcile overlapping meaning, and rerun affected checks. Never overwrite newer
target docs with a wholesale branch copy, or present an untested combination as
verified. Git records history; documents need not mirror process states.
