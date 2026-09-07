# Knowledge authority

Canonical Core is docs/ at the canonical branch. It stays unchanged for the full initiative.
Verified Working Knowledge is a sparse, initiative-scoped overlay at the last closed epic checkpoint.
Proposal is the approved design of the active epic and its tasks; it is not current knowledge.
Code is read from the actual task start/accepted dependency commits, not from a fictional target architecture.

Default search/get/owners use only canonical Core. Pass `--initiative <id>` explicitly to use the overlay.
Use [retrieval](retrieval.md) for heading-level discovery and exact readback. The disposable index neither
changes authority nor supplies packet content; read diagnostics and resolve sources in the same scope.
`knowledge` task references are logical docs paths. A verified replacement masks the older Core record;
a retirement suppresses it; a stale record fails rather than falling back to the superseded text.
Unchanged documents inherit from the original canonical baseline. Unrelated initiative material never joins.

After an epic passes integrated checks and review, reconcile actual changed paths into Working Knowledge.
Changes to already mapped artifacts require update/revalidate/retire. A report cannot omit known impact.
Working claims carry source commit, artifact hashes and passed verification IDs. Their semantic correctness
is still a reviewer/reconciler responsibility; schema validity is not a proof that prose matches behavior.

During the next active epic, the working layer still describes the last checkpoint. Apply the approved
epic delta and actual dependency outputs explicitly. Do not promote partial task notes into verified knowledge.
Workers return findings/deviations in results; the coordinator can preserve them in the signed amendment
or audit artifacts. Avoid a second mutable informal wiki.

A discrepancy is not permission to rewrite a requirement to match buggy code. Determine whether it is
stale descriptive prose, a code defect, or a changed requirement; require a human amendment for the latter.
After the full initiative, reconcile cumulative verified semantics into Core, then verify exact code + docs.
