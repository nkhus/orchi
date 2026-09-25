# Maintain knowledge alongside delivery

Use for requirements, design, Core updates, or branch synchronization. Follow the
repository's documentation rules and ownership map when it has them. "Core" means
the project's canonical documentation of current behavior at its normal paths.

| Material | Meaning and location |
| --- | --- |
| Main Core | Implemented, integrated behavior at normal owning documentation paths on main; integration is not deployment evidence |
| Initiative requirements/design | Agreed target, decisions, and unresolved questions in initiative documentation on its branch |
| Branch Core | Normal Core paths updated with implemented branch behavior, read together with branch code and verification |
| Evidence | Checks, reviews, and observations in issues/PRs or existing evidence locations; supports claims without becoming requirements |

Retain useful source/requirement links from planning through Tasks and the PR.
Read the owning source, not only search snippets. State branch or commit when
comparing current main, initiative integration, and an Epic candidate. Proposed
requirements do not prove implementation; a passing unit test does not establish
external provider behavior, production rollout, or operational readiness.

For each behavioral or architectural change, identify affected owning pages,
update them alongside implementation, and fix navigation/index links when pages
move or appear. Check whether examples, public contracts, runbooks, and known
limitations also change. If documentation is unaffected, explain why briefly in
the PR rather than creating a no-op documentation Task.

Keep target-only plans outside the current-state corpus. The
`docs/initiatives/<slug>/` area is delivery planning/history, not another product
owner; link it as such if adding it to a documentation index. In a standalone
Epic, its issue can hold the plan. Follow existing area ownership for Core.
Do not add a metadata ontology, duplicate Working overlay, or generated knowledge
store merely to classify these distinctions.

Before an Epic merge, compare its implementation and acceptance with its changed
Core pages. Before the Initiative merge, inspect all agreed requirements and
cross-Epic contracts against the combined result. Resolve omissions; explicitly
agree any deferred or changed outcome rather than marking it implemented. Preserve
the original request and meaningful decisions in initiative history.

When main or the initiative target moves, inspect both sides of code and docs,
reconcile overlapping semantics, and rerun checks affected by that integration.
Update stale references and limitations. Never overwrite newer target docs with
a wholesale branch copy or present an untested combined result as verified.
