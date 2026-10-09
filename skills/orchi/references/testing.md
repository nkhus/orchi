# Test and diagnose

Use when planning, writing, or reviewing tests, and when a Task fixes a defect.
The repository's own testing rules and commands take precedence.

## Seams

A seam is the public interface where a test observes behavior without reaching
inside: a module's entry points, a route, a command, a rendered screen. Prefer
the highest existing seam that reaches the behavior; add a seam only when no
existing one can observe it. When planning names the seams, test there.

## Good tests

- Assert observable behavior through the seam, so the test survives a refactor
  that keeps the behavior.
- Take expected values from an independent source: a literal, a worked example,
  or the requirement, never a recomputation the way the code computes them.
- Mock only system boundaries: third-party services, time, randomness, and the
  network, database, or file system when no local stand-in exists. Run the
  project's own modules for real.
- Build one behavior at a time: a failing test, the smallest change that makes
  it pass, then the next behavior.

A test is suspect when it mocks the project's own modules, asserts calls or
their order on internal collaborators, verifies through a side channel (reading
the database instead of reading back through the interface), or would still
pass with the change reverted.

## Red evidence

A new or changed test proves something only if it fails without the change. Run
it before the change, or against the base commit, and record the command and the
failure it showed:

`Red: <command> -> <failing assertion or symptom>`

When no test can fail first (a refactor that keeps behavior, configuration,
documentation), record the reason instead. If you forced a failure by breaking
code or a fixture, check with `git diff` that the change reached the tested path,
and restore it before committing.

## Defects

A defect Task starts from a reproduction: one command that has already failed on
the reported symptom, gives the same result on every run, finishes in seconds,
and runs without a person. Planning records it in the Task's scenarios, or states
why none exists and which evidence replaces it.

1. Run the reproduction and confirm that it shows the reported symptom, not a
   nearby failure.
2. Shrink it until every remaining input, step, and setting is needed for the
   failure.
3. Write three to five ranked hypotheses, each with a prediction that would
   prove it wrong.
4. Test one prediction at a time. Tag temporary logging with a unique prefix,
   such as `[DEBUG-a4f2]`, so one search removes it. For a performance
   regression, measure a baseline before changing anything.
5. Turn the minimal reproduction into a regression test at a seam that runs the
   real failure path: red, fix, green, then rerun the original reproduction. If
   no seam reaches that path, report it as a finding instead of adding a shallow
   test.
6. Remove temporary logging and harnesses, and state the confirmed cause in the
   commit and the PR.

## Review the tests

For each changed behavior, check that tests exist at the planned seams, assert
behavior rather than implementation, and have red evidence or a stated reason,
and that each defect fix has a regression test or a reported missing seam. A
suspect test is a defect when it leaves a requirement unverified; otherwise it
is advisory.
