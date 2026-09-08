# Explicit code-and-knowledge sync

Run at a closed boundary: no active epic, live ticket, pending gate or aggregate operation. Preserve original baseline, source request, Intent and completed-epic history. Never rewrite old evidence as though it ran on the new canonical commit.

1. `sync-status` identifies actual upstream, file conflicts and affected knowledge; it does not change authority.
2. `sync-draft --out ...` enumerates exact obligations. Replace markers with reason, Target assessment, resolutions, knowledge decisions and trusted checks.
3. `sync-check --file ...` composes and checks a prospective checkpoint. On failure Current remains unchanged.
4. Review the returned exact `review_request`, including code conflict resolutions, document semantics, Target impact and every required path.
5. `sync-review --file ...` creates the exact human gate only for complete blocker-free review.
6. Human inspect/decide accepts only if canonical still matches the reviewed upstream. Then code, integration base and verified Working promote together.

Resolve each same-path code conflict exactly once through replacement, deletion or a regular file from an exact commit. Protected conflicts and rewritten/unrelated canonical history fail closed. No implicit textual or semantic merge.

For each affected Working record or inherited upstream Core that documents locally changed code, choose update, revalidate, retire or use-upstream with explicit reasoning and checks. Revalidate cannot hide upstream changes to the same logical document. New upstream docs can also conflict with local semantics even when no Working entry existed before; reconcile them explicitly.

A required Target revision blocks subsequent plan/finalization. Accepted sync invalidates a previous final candidate/review/signature. Rebuild final reconciliation before publication. A rejected sync remains prospective; withdraw any pending gate before `sync-discard`. Canonical movement during approval requires a new preparation/review, not reuse of the old signature.

Ownership metadata finds mechanical impact, not every semantic relationship. Review the actual system assumptions. Sync does not fetch a remote, publish a branch, deploy or coordinate another machine's process locks.
