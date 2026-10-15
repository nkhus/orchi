# Load-based worker capacity

Orchi does not estimate how many workers a machine or account can run, and does
not ask before starting each worker.

## Why

A `capacity.py` that checked machine load before starting workers was drafted
during the team-role work and dropped at the maintainer's request before it
shipped, in favor of a fixed maximum that the orchestrator fills without asking. Asking before every start would add a
question the user has already answered by listing the team.

## Instead

The repository's instructions list the team's sessions by title. The listed
workers are the limit: a hub gives work to a free listed worker without asking.

## Decided in

- 2026-10-09, while agreeing the team roles that shipped in
  [nkhus/orchi#24](https://github.com/nkhus/orchi/pull/24) with a fixed limit.
- [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34): the fixed limit
  became the team list in the repository's instructions.
