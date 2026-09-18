# Authoring contracts

Export current JSON Schemas with `schemas --out /tmp/orchi-schemas`; use these contracts when authoring every workflow document.
Source authority is Python models plus generated schemas. JSON is persisted only after successful validation.
All schemas forbid unknown fields and coercion. IDs are lowercase dotted/hyphenated identifiers.

| File | Command | Owner |
|---|---|---|
| initiative.json | begin / roadmap | planning agent + human decision |
| epic.json | plan / amend | planning agent + human decision |
| readiness.json | activate | worker; structural checks by controller |
| result.json | submit | worker claim, not verified completion |
| review.json | review-record | independent reviewer + triage |
| checkpoint.json | checkpoint | reconciler after verified epic |
| finalization.json | finalize | reconciler after all epics |

Initiative root includes request/outcome/acceptance/constraints/direction/epics. Roadmap epics have
id/title/outcome/depends_on/contributes_to/risks; no embedded tasks.
Epic root includes initiative_id/epic_id/based_on/goal/shared_design/acceptance/acceptance_checks/mode/tasks.
`based_on` is the exact current internal head when submitted, not initial main.
Tasks contain their own complete technical design; packet files are generated and never maintained manually.

Source kinds: `knowledge` points to a logical docs/*.md target resolved through the initiative overlay;
`code` points to an existing exact source; `dependency` names a producer task and promised output/contract.
Each hard dependency must have an output source. Add all additional known reads to read_paths.
Verification references operator-registered check IDs; exact CLI commands are not worker authority.

Checkpoint entries use target/action/content/artifacts/checks/reason. Replacement has content; revalidate and
retire do not. Every actual changed executable path appears once in dispositions, with impacted targets or
an explicit reason for none. Finalization maps every original acceptance criterion to final check IDs.
