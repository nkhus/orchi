# [CTX] Project context that stays current

Status: implemented on `feat/context-track`, stacked on the
[standards track](../std-project-standards/README.md). The
[knowledge reference](../../../skills/orchi-core/references/knowledge.md) and
`knowledge.py` describe current behavior; this document keeps the reasoning.

## Request

The maintainer's requests, translated from Russian (2026-10-27):

> We lack a place to keep research artifacts, and what we pass on to planning.

> The task is to keep the project's context current: what was decided during
> research with the user, how it went into planning and development, ADRs, and
> so on. At the same time the information must stay current through the whole
> life of the project.

> Research must be grouped somehow, or it becomes a dump of unrelated
> decisions. Old ADRs should be deleted: we keep only the current state. Do we
> still create Initiative branches, Epic branches from them, and Task branches
> from those? That was the right decision: we need local working documents that
> move smoothly into the target documentation, because locally we may change
> things several times.

## Decisions

Accepted by the maintainer on 2026-10-27 ("I accept all four
recommendations"):

| # | Decision |
| --- | --- |
| C1 | One working folder per piece of work, `docs/work/<tag>-<slug>/`, on its branch. An exploration gets an `explore/<slug>` branch; the Initiative or Epic branch that plans it is created from that branch, so the folder carries on. It replaces `docs/initiatives/` in target projects. |
| C2 | Settled content moves into the current documentation at each Epic merge; the working folder is deleted before the merge into main, and a check keeps `docs/work/` out of main. |
| C3 | Decisions are kept only while they hold, in the Decisions section of the page of the area they belong to, with the reason, the rejected alternatives, and the PR that made them. A replaced decision is deleted; Git and the PRs keep the history. There is no separate ADR folder. |
| C4 | Current documentation is grouped by area through an ownership map in `docs/README.md`; `knowledge.py stale` flags a page whose code changed without it, and product behavior pages name the acceptance test for each criterion. |

The branch hierarchy stays: `initiative/*` from main, `epic/*` from the
Initiative branch, Tasks on their Epic branch (`task/*` for a pool dev lead's
parallel Tasks).

## Design

### Two kinds of documents

| | Current documentation | Working documents |
| --- | --- | --- |
| Where | Normal paths on main: `docs/README.md`, `docs/<area>/`, `docs/product/`, `ENGINEERING.md`, `PRODUCT.md`, `DESIGN.md` | `docs/work/<tag>-<slug>/` on the work's branch only |
| Changes | With the code, in the same PR | Freely, as often as the work needs |
| Holds | How the product behaves and is built now, and the decisions in force | Research findings, options, the decision log, the plan |
| Ends | Never; replaced content is deleted | Deleted before the merge into main |

### Flow

1. **Exploration** creates `explore/<slug>` from main with
   `docs/work/<slug>/`: `research/<question>.md` per finding, `options/<option>.md`
   per direction. The Issue stays the map and holds decisions with ids (D1, D2).
2. **Planning** creates the Initiative or Epic branch from the exploration
   branch, so the folder continues; it gives every decision a fate (a
   requirement, a decision to record in an area page with the code, or none) and
   writes the plan as the folder's `README.md`.
3. **Each Epic merge** moves what is settled into the current documentation on
   the target branch: behavior pages, area pages, and their Decisions sections.
4. **The merge into main** happens only after the folder is deleted. An
   exploration that ends in "do not build" records that decision in its area
   page through a PR from its branch, with the folder deleted.

### Checks

| Command | Fails when |
| --- | --- |
| `knowledge.py stale --since <base>` | Code the ownership map assigns to a page changed, the page did not, and the PR's Documentation impact does not name the page with a reason |
| `knowledge.py stale` | Lists pages whose owned code has a later commit than the page (the weekly drift run) |
| `knowledge.py work` | A file under `docs/work/` exists (run on PRs into the default branch) |
| `knowledge.py behavior` | A behavior page names an acceptance test whose file does not exist or does not contain its name |

## Tasks

| Task | Outcome |
| --- | --- |
| T1 Checks | `stale`, `work`, and `behavior` in `knowledge.py`, with tests |
| T2 Knowledge reference | Layout, working documents, promotion, decisions, freshness; templates for the map, an area page, and a behavior page |
| T3 Exploration | `explore/<slug>` with the working folder, findings as files, decision ids, hand-off by branch |
| T4 Planning and delivery | Working folder instead of `docs/initiatives/`, decision fates, promotion at Epic merge, folder deletion before main, Task readiness item 12 from the ownership map |
| T5 Workflows and installer | `orchi-docs.yml` runs the new checks; the weekly drift run lists stale pages; `ENGINEERING.md` declares the documentation checks; the managed `CLAUDE.md` section points to the map |
| T6 Documentation | README, installation, testing; the next version |

## Not in scope

Orchi's own repository keeps its `docs/initiatives/` records under its
`AGENTS.md` for now; moving them follows separately.
