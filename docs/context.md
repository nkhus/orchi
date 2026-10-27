# Context

A project's context stays current through the life of the product: main holds
only how it behaves and is built now, grouped by area, and work in progress
keeps its research, options, decision log, and plan in a working folder on its
branch until it settles.

## Structure

| Part | Defined in |
| --- | --- |
| Current documentation, decisions, working documents, promotion, freshness | `skills/orchi-core/references/knowledge.md` |
| Searching and reading documentation | `skills/orchi-core/references/retrieval.md` |
| `lint`, `search`, `get`, `impact`, `stale`, `work`, `behavior` | `skills/orchi-core/scripts/knowledge.py` |
| Templates for the map, an area page, and a behavior page | `skills/orchi-core/assets/docs/` |
| Documentation checks on pull requests | `skills/orchi-core/assets/github/workflows/orchi-docs.yml`, installed with `--github` |

Orchi's own documentation follows the same rules: [the map](README.md) assigns
its code to these pages.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Each piece of work keeps one working folder, `docs/work/<tag>-<slug>/`, on its branch; an exploration starts it on `explore/<slug>`, and the Initiative or Epic branch that plans it is created from that branch, so the folder carries on | Working documents change several times before they settle and must move smoothly into the current documentation | `docs/initiatives/` plans committed to main; research kept only in Issue comments | [#45](https://github.com/nkhus/orchi/pull/45) |
| Settled content moves into the current documentation at each Epic merge; the working folder is deleted before the merge into main, and `knowledge.py work` keeps `docs/work/` out of main | Main must describe only the present, and what is still changing stays where it can change | Keeping plans on main after delivery | [#45](https://github.com/nkhus/orchi/pull/45) |
| A decision is kept only while it holds, in the Decisions section of its area page, with the reason, the rejected alternatives, and the PR; a replaced decision is deleted | Readers need the decisions in force, and Git and the PRs keep the history | An ADR folder that keeps every decision ever made | [#45](https://github.com/nkhus/orchi/pull/45) |
| Current documentation is grouped by area through an ownership map in `docs/README.md`; `knowledge.py stale` flags a page whose code changed without it, and behavior pages name the acceptance test for each criterion | Pages grouped by the work that produced them become a dump of unrelated decisions; the map makes the owning page checkable | Grouping documents by Initiative or by date | [#45](https://github.com/nkhus/orchi/pull/45) |
