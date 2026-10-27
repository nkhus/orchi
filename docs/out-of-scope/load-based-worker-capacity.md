# Load-based worker capacity

Orchi does not estimate how many workers a machine or account can run, and does
not ask before starting each worker.

## Why

A `capacity.py` that checked machine load before starting workers was drafted
during the team-role work and dropped at the maintainer's request before it
shipped, in favor of a fixed pool that is filled without asking. Asking before
every start would add a question the user has already answered by sizing the
pool.

## Instead

The pool is the limit: Orchi builds a fixed number of crews and workers (2 and 2
unless the user names others) and assigns free crews without asking; more come
only when the user asks.

## Decided in

- 2026-10-09, while agreeing the team roles that shipped in
  [nkhus/orchi#24](https://github.com/nkhus/orchi/pull/24) with a fixed limit.
- [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34): the fixed limit
  became the team list in the repository's instructions.
- [nkhus/orchi#42](https://github.com/nkhus/orchi/pull/42): the pool size
  replaced the team list.
