# Impeccable as the design engine

Orchi does not install Impeccable or design through it, and does not run its
detector in CI.

## Why

Impeccable was Orchi's only design engine. On 2026-10-27 the
maintainer compared design skills blind on one real proof-of-concept screen
(a hotel general manager's morning view, same brief and data for every skill)
and scored each mockup from 1 to 5:

| Skill | Without references | With references |
| --- | --- | --- |
| Impeccable (its five direction sketches from a real Orchi run) | 1, 1, 1, 1, 1 | not run |
| Claude without a design skill | 3 | 4 |
| Hallmark | 4, 3, 4, 2, 4 | 2 |
| prototype (Emil Kowalski) | 3, 3, 4 | 4, 4, 4 |
| frontend-design (Anthropic) | 4, 2, 4 | 3 |
| huashu-design | 3, 2, 3 | 3, 3, 4 |
| Taste Skill | 3 | 2 |

Impeccable scored below Claude without a skill, and its interactive flow cost
the most of the user's time. The maintainer judged Hallmark strongest for
landing pages and prototype for interfaces, and chose to let each project pick
one of the two in its first design Epic.

## Instead

Orchi installs Hallmark and prototype at pinned commits. A project's first
design Epic runs both on its first surface, the user's pick sets the project's
design engine, and `DESIGN.md` records it. References are agreed with the user
before every design round. The design audit runs in review; see
[design](../design.md).

## Decided in

- 2026-10-27, after the blind comparison, in
  [nkhus/orchi#59](https://github.com/nkhus/orchi/pull/59).
