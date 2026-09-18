# Knowledge lifecycle

## Publication rule

Core documentation under `docs/` changes only when the complete initiative is implemented and finalized. Intermediate code is not published to canonical. At each epic boundary, agents reconcile verified Working Knowledge instead of updating Core. Finalization assembles and checks the cumulative code-and-docs result; the operator publishes it after review and exact approval.

Only behavior or knowledge that actually changes needs a documentation edit. An unaffected Core file need not be rewritten. A finalization with no required documentation changes can still verify that Core correctly describes the result.

## Authority layers

| Layer | Content | Visibility |
| --- | --- | --- |
| Core | Published canonical behavior | Default `search`, `get`, and `owners` |
| Verified Working Knowledge | Checked intermediate changes within one initiative | Explicit initiative scope only |
| Proposal | Active epic/task design and future roadmap outcomes | Explicit planning or task context |
| Evidence and observations | Process results, checks, disagreements, and review | Audit and relevant task/review context |

Working Knowledge is a sparse overlay addressed by logical `docs/...md` targets, not a second full documentation tree or an unrestricted agent notebook. A replacement masks the corresponding Core entry. Retirement suppresses it. Revalidation binds still-correct content to current evidence. A stale replacement fails instead of silently falling back to obsolete Core text.

Unchanged entries inherit from the initiative's canonical baseline. A baseline before-image can be inspected explicitly, but it is not presented as a simultaneous competing rule. Another initiative's proposal or archive is not automatically imported as authority.

## Storage

```text
docs/                                      Canonical Core
initiatives/active/<initiative>/
  initiative.json                          Accepted intent and roadmap
  epics/<epic>/plans/<revision>.json        Immutable accepted plans
  epics/<epic>/tasks/<revision>/<task>.json Portable task definitions
  epics/<epic>/results.json                 Accepted results
  epics/<epic>/checkpoint.json              Reconciliation and impact
  knowledge/manifest.json                  Sources, evidence, and artifact hashes
  knowledge/docs/...md                     Sparse verified replacements
```

These initiative files are written on internal commits, not into the canonical working checkout during an epic. Finalization moves the active subtree into `initiatives/archive/<initiative>/`. The archive is history, not current authority.

Complete packets, logs, signatures, and observations live in the external control store and can be exported separately. Git history and artifact hashes do not reconstruct a missing external audit store. Audit exports can contain private source and require appropriate access and retention controls.

## Responsibilities

The planner records direction and task designs; the human approves material scope and decisions. Workers propose code and report observations without changing Core, accepted definitions, or the knowledge manifest. The integrator verifies and accepts code, but does not convert individual task notes into verified knowledge.

After combined checks and review, the reconciler examines the actual epic diff and proposes knowledge edits and impact dispositions. The controller validates and records the checkpoint, closes the epic, and advances `knowledge_head`. The next planner reads that checkpoint and the actual accepted code.

After all epics, the reconciler and reviewer produce coherent cumulative Core documentation. The operator publishes one accepted code, documentation, and archive commit. Publication is not deployment.

## An epic in progress

Working Knowledge describes the last closed epic. When task A has already changed code and task B depends on A, B receives the last checkpoint, the approved active-epic delta, and A's actual integrated result. Packets distinguish `knowledge_head` from `start_commit`. A partial implementation is not relabeled as a verified knowledge checkpoint.

## Checkpoint requirements

Every actually changed executable path requires a disposition: affected documentation targets, or an explicit and reasoned no-documentation-impact statement. Known ownership mappings cannot be silently omitted. Previously mapped artifacts that change require related working entries to be replaced, revalidated, or retired.

Entries bind to exact artifacts and passed verification identifiers. Missing ownership mappings do not prove there is no semantic impact; the reconciler must inspect new areas. Hashes and check IDs establish provenance, not the truth or completeness of prose.

Core documents can declare artifact ownership in YAML frontmatter:

```yaml
---
artifacts:
  - src/example.py
---
```

Use exact repository-relative paths. The context resolver validates frontmatter and rejects unsafe constructs; see the contracts and context tests for the complete accepted format.

## Resolve discrepancies by cause

Stale descriptive prose requires evidence and a verified knowledge correction. Code that violates an effective requirement needs a code fix, not a rewritten rule that legitimizes the defect. A changed requirement needs human-approved amendment. A source from the wrong commit requires regenerated context against the correct snapshot.

`final-draft` is only a starting assembly. Reconciliation must check cumulative semantics, cross-epic compatibility, root acceptance, retirements, and links. Plans are not copied into Core as if intended behavior were already verified. The exact final code-and-docs tree passes checks, final review, and human approval before publication.
