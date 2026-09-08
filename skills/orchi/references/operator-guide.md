# Operator guide

This guide and both command entrypoints are bundled in the installed `orchi` skill. A separate Orchi repository checkout is not required. The human/operator performs key management, trusted setup, approvals, and publication; coding workers do not.

## Locate the installed tools

For a project-local Codex installation:

```bash
export PROJECT="/absolute/path/to/project"
export ORCHI_SKILLS="$PROJECT/.agents/skills"
export CONTROL_HOME="/absolute/path/to/operator-data"
export ORCHI_CONTROL="$CONTROL_HOME/feature-control"

orchi() { uv run "$ORCHI_SKILLS/orchi/scripts/orchi.py" --control "$ORCHI_CONTROL" "$@"; }
orchi_operator() { uv run "$ORCHI_SKILLS/orchi/scripts/operator.py" "$@"; }

orchi doctor --repo "$PROJECT"
```

For a user-wide Codex installation through the Skills CLI, set `ORCHI_SKILLS="$HOME/.codex/skills"`, or use the location printed by your installer. For another agent, use the actual directory containing all five installed skills. Orchi's Python environment is separate from the project's test/build environment.

The target must be a Git repository with an existing commit and the intended canonical branch. Installation need not have initialized a workflow. An empty baseline commit is sufficient for greenfield; do not invent Core before Target. Baseline checks are policy-controlled; use an empty list only when appropriate, while keeping meaningful final checks. Reserve the `initiatives/` namespace for Orchi's internal initiative records and inspect the path protection rules before adopting the workflow.

## Establish access boundaries

Use a dedicated operator-owned directory outside the repository. Protect the key, registry, control database, and canonical write access from workers using OS/container permissions or a trusted adapter/relay. Separate paths alone are insufficient; the local runner does not automatically switch operating-system users.

```bash
umask 077
mkdir -p "$CONTROL_HOME"
orchi_operator keygen \
  --private "$CONTROL_HOME/operator.pem" \
  --public "$CONTROL_HOME/operator.pub"
```

The operator's private key is never placed in a worker checkout, prompt, environment, or worker-readable home directory. `keygen` refuses existing files. Review the exact commands before running them; a coding agent must not create and wield a human approval identity on its own.

## Select trusted verification

Create a fixed registry of real project checks before setup. Use stable suite/lint/type-check commands that work inside a fresh verification worktree and exercise that snapshot's current tests. Provision application dependencies and services separately; `uv` provisioning for Orchi does not install the application's dependencies.

The following is a **pytest example**, not a universal project default. Replace the argument array with the approved command for the actual project. Use absolute tool paths when the minimal subprocess environment cannot locate a project-local executable.

```bash
export ORCHI_CHECK_ARGV='["/absolute/path/to/project/.venv/bin/python", "-m", "pytest", "-q"]'
python3 - <<'PYCODE'
import json, os
from pathlib import Path
root = Path(os.environ["CONTROL_HOME"])
argv = json.loads(os.environ["ORCHI_CHECK_ARGV"])
if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
    raise SystemExit("ORCHI_CHECK_ARGV must be a non-empty JSON array of arguments")
policy = {
    "public_key": (root / "operator.pub").read_text(),
    "canonical_ref": "refs/heads/main",
    "checks": {"suite": {"argv": argv, "timeout_seconds": 120}},
    "baseline_checks": ["suite"], "final_checks": ["suite"],
    "max_workers": 4, "max_process_seconds": 900, "lease_seconds": 3600
}
with (root / "policy.json").open("x") as handle:
    json.dump(policy, handle, indent=2)
PYCODE

orchi setup --repo "$PROJECT" --policy "$CONTROL_HOME/policy.json"
```

The template at `../assets/policy.example.json` lists the same categories with explicit placeholders. Policy is fixed for the control store; workers cannot register arbitrary check commands. Choose branch and budgets intentionally. Each initiative uses a fresh control directory.

## Define and approve the initiative

Export schemas and author planning files in an operator-approved location:

```bash
orchi schemas --out "$CONTROL_HOME/schemas"
orchi intent-build --directory /path/to/intent --initiative feature
# Set initiative.json intent to the exact returned result.intent.
orchi begin --file /path/to/initiative.json --intent /path/to/intent
orchi gate --out "$CONTROL_HOME/request-direction.json"
```

Inspect the full exact request and its inputs. Approve or reject it as the human operator:

```bash
orchi_operator sign --request "$CONTROL_HOME/request-direction.json" \
  --private "$CONTROL_HOME/operator.pem" --decision approve \
  --operator your-operator-id --out "$CONTROL_HOME/decision-direction.json"
orchi apply-decision --file "$CONTROL_HOME/decision-direction.json"
orchi next
```

The normal interactive operator path does not require request/decision files:

```bash
orchi inspect
orchi_operator decide --control "$ORCHI_CONTROL" --request-id "$REVIEWED_REQUEST_ID" \
  --private "$CONTROL_HOME/operator.pem" --operator your-operator-id --decision approve
```

Use only the exact ID you inspected. The signature still binds the complete request and policy; it is not an approval of whatever happens to be latest. `orchi_operator inspect --control "$ORCHI_CONTROL"` is an equivalent operator entrypoint. The explicit file sign/apply path remains supported for separated approval transport.

A bounded request can start with `orchi start --file /operator/drafts/brief.json`, producing a combined direction-and-first-plan gate. Larger requests keep separate direction and progressive epic gates. Use unique request/decision filenames when choosing the file workflow. Signing refuses an existing decision output. Repeat the protocol for the exact next epic plan submitted with `plan --file /path/to/epic.json --design /path/to/design.md`, material amendments, and final acceptance. Never sign an arbitrary request without checking its provenance and actual content. The readable inspector and direct decision command below remove file transport from the normal path; no managed operator service is required.

Use [retrieval](retrieval.md) to search Current and Target explicitly, inspect roles/diagnostics, and read exact sources in the intended scope. A design file needs the exact hash and typed requirement/architecture links described in [authoring](authoring.md). Indexing
and lookup do not authorize or advance work.

The planner reads actual internal commits and initiative-scoped knowledge. Use `git show <head>:<path>` when inspecting internal code; do not move the canonical checkout to simulate progress.

## Configure workers

The bundled Codex adapter template is `../assets/codex-adapter.json`:

```json
{
  "kind": "codex",
  "executable": "codex",
  "pass_env": ["HOME", "CODEX_HOME"]
}
```

Install and authenticate Codex for the intended worker identity using its official instructions. Inspect `codex exec --help` for required flags. An optional `model` field selects a model; no model is selected by Orchi. `HOME` and `CODEX_HOME` must not expose operator keys or privileged configuration. Permit additional environment names only after reviewing their contents and authority.

Copy and review the adapter in the operator configuration directory:

```bash
cp "$ORCHI_SKILLS/orchi/assets/codex-adapter.json" "$CONTROL_HOME/adapter.json"
orchi run --adapter "$CONTROL_HOME/adapter.json"
```

The runner uses a read-only preparation session and a workspace-write execution session, with structured output, JSON events, ephemeral sessions, and noninteractive approval settings. It does not bypass the sandbox. Verify that the actual executable and outer isolation policy enforce the intended access boundaries. `run` is foreground and returns at review, checkpoint, approval, or blocker boundaries; continue through `next`.

## Command adapter or manual handoff

A trusted command adapter supplies `kind: "command"` and an `argv` array. It runs without a shell. The process receives `ORCHI_PHASE`, `ORCHI_PACKET`, `ORCHI_OUTPUT`, `ORCHI_WORKSPACE`, and `ORCHI_TICKET`. It must write the phase's JSON result to `ORCHI_OUTPUT`. Prepare/execute output schemas are in the ticket's input directory. The command adapter does not itself provide a sandbox; its executable or external runtime must enforce access restrictions. Each foreground phase also receives a ticket-bound Unix-socket capability plus `ORCHI_WORKER_REQUEST` and `ORCHI_WORKER_PYTHON`. The helper allows exact reads and, after readiness, delegated scope requests only; it never exposes the control store or signing key. Permit the channel explicitly in the outer sandbox; report an unavailable channel rather than weakening sandbox policy. Use `scope --file -` with JSON stdin to avoid writing scratch request files into the product checkout.

For initial manual assignment, `claim --task <id>` returns a workspace, packet, and ticket. Give the assistant only the assigned checkout and inputs. Relay its readiness using `activate --ticket <id> --file readiness.json` before execution. Relay its result using `submit --ticket <id> --file result.json`. Do not give a worker the entire control store merely to simplify CLI access.

For an existing branch, import only after activation with `import-candidate --ticket ... --commit ... --base ... --reason ...`; no historical approvals are inferred. For a transfer, `handoff --ticket ... --stopped --executor human --reason ...` preserves a candidate/notes and fences the old attempt. The new executor reads a new packet, activates and explicitly imports/reconciles the prior diff. Changed fixed assumptions or unavailable scope prevent blind reuse. `overview` exposes these conditions.

## Review and checkpoint an epic

```bash
orchi review-request --scope epic --out /path/to/review-request.json
# Independent read-only review and triage produce an evidence-based report.
orchi review-record --file /path/to/review.json
# Reconcile actual code changes, knowledge entries, and impact dispositions.
orchi checkpoint --file /path/to/checkpoint.json
orchi next
```

When the controller requests repair, use `repair` and then execute the resulting ready tasks. Material redesign requires an amendment. The next epic plan must use the new actual `head`; a successful checkpoint is mandatory before advancing. This initiative's Core remains the accepted integration-base snapshot throughout epic work; another initiative may publish independently.

## Synchronize upstream

Use `sync-status` at closed boundaries. When canonical advanced, follow the bundled [synchronization procedure](synchronization.md). Prepare exact code and affected Core/Working decisions with `sync-draft` and `sync-check`; review the returned sync request and submit `sync-review`; inspect and sign the exact human gate. No Current changes before acceptance. A ready final candidate becomes invalid after accepted sync and needs final reconciliation/check/review/approval again. `withdraw-gate` and `sync-discard` abandon a prospective stale candidate without promoting it.

Multiple initiatives use unique IDs and separate control directories, not one shared global scheduler. Shared local check resources need the same operator-owned absolute `resource_directory` and check-level `resources`. These locks do not cover another host or unmanaged external jobs. Task resource labels are only controller-local.

## Finalize and publish

After all roadmap epics close:

```bash
orchi final-draft --out /path/to/finalization.json
# Reconcile every requirement, architecture document and Working entry; replace all draft markers.
orchi finalize --file /path/to/finalization.json
orchi review-request --scope initiative --out /path/to/final-review-request.json
orchi review-record --file /path/to/final-review.json
# Export, inspect, sign, and apply the exact final gate using the approval protocol.
orchi publication
```

`publication` returns the exact tree/candidate, accepted integration base and policy-selected history shape; it does not mutate the branch or create a hosted PR. Default `exact` publication can use a normal operator `git merge --ff-only` with repository protections, then record the exact commit. Explicit `squash` and `merge` policy shapes still require the approved tree and base; a different queue composition must be synchronized and approved again.

`orchi_operator publish --control "$ORCHI_CONTROL"` is an optional local CAS helper for exact/merge mode. It refuses a canonical branch checked out in any worktree; detach the branch first or use the normal operator/hosting workflow. It cannot overwrite a racing upstream commit. Squash is created by the operator/host and then recorded. Do not manually force a stale result onto main.

```bash
orchi record-publication --commit <published-commit>
orchi export --out /new/private/audit-directory
```

Publication is not deployment. Store audit exports under suitable access and retention controls. Interrupted operations require observed process termination and explicit recovery; use `next`, `status`, and the [recovery reference](recovery.md) rather than resetting state or inventing successful evidence.

To open effective knowledge in an IDE, use `orchi views --out /new/external/view --view all`. Files are role-separated read-only projections with a provenance manifest. They must not be edited/committed as authoritative docs.

## Revise accepted Target

Only between closed epics, prepare the next Intent revision and updated future roadmap, preserving `source.md` and completed epic contracts. Removed requirement IDs need accepted resolutions.

```bash
orchi intent-build --directory /path/to/revised-intent --initiative feature --revision 2
# Bind the returned Intent reference into the revised initiative contract.
orchi revise-intent --file /path/to/revised-initiative.json --intent /path/to/revised-intent \
  --reason "Observed evidence requires this target change" --evidence "<exact-check-or-source-reference>"
# Inspect, sign and apply the returned exact gate using unique files.
```

Evidence/reference text explains the revision; it is not automatically trusted check proof. Before changing Intent during an active epic, terminate workers and release tickets, then propose `stop-epic --stopped --reason ...`. Its signed acceptance returns to the last closed boundary, abandoning unverified code while preserving history and consumed attempts. Then revise Target and replan. Use `amend --file ... --design ... --reason ...` instead when only the selected implementation plan changes.

A `roadmap --file ... --reason ... --evidence ...` command is a convenience for the same target-revision gate when target Markdown itself remains unchanged. It advances the accepted target revision; it is not a silent roadmap edit.
