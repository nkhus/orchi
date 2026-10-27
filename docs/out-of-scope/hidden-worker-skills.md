# Hidden worker skills

Orchi does not hide `orchi-explore`, `orchi-plan`, or `orchi-deliver` from the
skill menu with `user-invocable: false`.

## Why

`user-invocable: false` also blocks typing `/<name>`, which solo use and worker
sessions rely on.

## Instead

The skills stay visible. Their descriptions limit model invocation to requests
that name the skill, and the pool entry `orchi-pm` stays explicit-only with
`disable-model-invocation: true`.

## Decided in

- [nkhus/orchi#33](https://github.com/nkhus/orchi/pull/33): skills stay visible
  in the menu.
- [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34): the worker skills no
  longer disable model invocation, so a worker can invoke them from a hub's
  message.
