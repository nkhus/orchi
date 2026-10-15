# Managing session lifecycles

Orchi does not rename, archive, or delete sessions, and does not make the user
paste a command into a worker to start it.

## Why

Team sessions belong to the user. Their titles are the addresses the team list
names, so renaming breaks routing; archiving or deleting removes a session the
user may still read or reuse. A pasted command is a manual step the hub can
replace with a message.

## Instead

Each session keeps the title the user gave it. A hub gives work by message and
the worker invokes the skill itself. A finished worker updates its checkout to
the latest main and clears its own conversation when its hub asks.

## Decided in

- [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34): the reusable worker
  pool replaced renaming and archiving.
