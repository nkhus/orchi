# Per-axis sub-reviewers

Orchi does not start a separate reviewer per review axis (Spec, Standards,
Tests).

## Why

One reviewer per axis plus the coordinating review cost four opus runs per
Epic. Keeping the axes apart matters, so a pass on one cannot hide a failure on
another, but separate sections in one report keep them apart too.

## Instead

`orchi-reviewer` reviews all three axes itself, in separate sections, and marks
a shared cause as `same cause as …`.

## Decided in

- [nkhus/orchi#28](https://github.com/nkhus/orchi/pull/28).
