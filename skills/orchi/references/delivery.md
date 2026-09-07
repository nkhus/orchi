# Two different completion boundaries

Epic completion: tasks integrated → checks → bounded review → checkpoint proposal → Working Knowledge update.
No Core edits, canonical merge, deployment or initiative archive. Internal head is preserved for the next epic.
Checkpoint dispositions cover every and only actual changed executable path. No-impact is an explicit claim,
not an inference from a missing ownership mapping. Existing known mappings must all be addressed.

Initiative completion: all epics close → cumulative reconciliation → final candidate tests → final review →
human approval → operator fast-forward publication → record actual canonical commit.
`final-draft` produces inputs, not permission to publish: replace its marker report with actual reconciliation.
Every working target needs a final disposition. The final candidate changes code + docs + initiative archive
and has exactly the original canonical baseline as its sole parent; intermediate commits stay internal.

Reconciliation must describe the actual cumulative result, not copy successive designs into Core.
Check cross-epic naming, retired concepts, artifact references, operational consequences and root acceptance.
Checks are rerun on the exact final candidate. Any changed final tree needs renewed checks/review/approval.
Final human approval binds the candidate and verification, not a movable branch name.

`publication` is an instruction, not a write. If canonical moved, stop; automatic rebasing is not supported.
An operator may merge only the exact approved candidate with normal fast-forward semantics, then call
`record-publication`. No deployment is implied. Back up/export the external audit store along with Git refs.
