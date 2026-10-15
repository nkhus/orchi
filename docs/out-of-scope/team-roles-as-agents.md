# Team roles as agents

Orchi does not define the planner, orchestrator, or worker roles as Claude Code
agents started with `--agent`, and does not ship a dedicated skill per worker
type.

## Why

Claude Desktop cannot pass `--agent` when it starts a session, and the user runs
the team there. A role defined as a skill works in any session: the user types
the hub command, or a hub sends a worker a message to invoke `orchi-explore`,
`orchi-plan`, or `orchi-deliver`. Claude Code re-attaches an invoked skill's text
after compaction, so the role survives it. Separate worker skills would repeat
the entry skills with a `--report-to` flag.

## Instead

The hubs are the explicit-only skills `orchi-planner` and `orchi-orchestrator`.
Workers run the ordinary entry skills with `--report-to <hub>`.

## Decided in

- [nkhus/orchi#24](https://github.com/nkhus/orchi/pull/24): roles became skills
  after `--agent` was dropped.
- [nkhus/orchi#33](https://github.com/nkhus/orchi/pull/33): planning workers run
  `orchi-explore` or `orchi-plan`, without dedicated worker skills.
