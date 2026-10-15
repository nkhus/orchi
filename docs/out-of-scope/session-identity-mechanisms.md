# Session identity mechanisms

Orchi does not pin a worker's role with an identity line derived from the
session title, an output style, or a `SessionStart` hook.

## Why

The maintainer declined all three in favor of re-sending. The claim, Issue,
and PR already record what a worker holds, so one message restores the role,
while each mechanism would add installed configuration that also runs in
sessions that are not team workers.

## Instead

When a worker no longer knows its role, its hub re-sends the work message. The
worker re-invokes the skill and rebuilds its state from GitHub.

## Decided in

- 2026-10-12, while designing the worker pool that shipped in
  [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34).
