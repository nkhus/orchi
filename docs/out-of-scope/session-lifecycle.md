# Archiving or deleting sessions

Orchi does not delete sessions, does not archive a pool crew, and does not make
the user paste a command into a session to start it. It archives only a crew it
started on demand, once that crew has released its work.

## Why

Pool sessions belong to the user, who may still read or reuse them; archiving or
deleting one loses that, and archiving also removes its worktree. A pasted
command is a manual step a message can replace.

## Instead

By default Orchi starts a crew per request and archives it when its work is
done; archiving is reversible, and the user may still reopen the crew. For
autonomous development Orchi builds a pool once and reuses it: a finished worker
or crew returns its worktree to the default branch and is cleared, and Orchi
renames a crew back to `crew-<k>`. Work is given by message, and the session
invokes the skill itself.

## Decided in

- [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34): the reusable worker
  pool replaced archiving.
- [nkhus/orchi#42](https://github.com/nkhus/orchi/pull/42): Orchi creates,
  renames, and clears pool sessions; the user no longer creates and titles them.
- [nkhus/orchi#58](https://github.com/nkhus/orchi/pull/58): crews start on
  demand and are archived when done; the pool is built only for autonomous
  development, and its crews are still cleared and reused.
