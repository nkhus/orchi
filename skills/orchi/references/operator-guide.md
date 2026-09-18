# Operator guide

This guide and both command entrypoints are bundled in the installed `orchi` skill. A separate Orchi repository checkout is not required. The human/operator performs key management, trusted setup, approvals, and publication; coding workers do not.

## Locate the installed tools

For a project-local installation:

```bash
export PROJECT="/absolute/path/to/project"
export ORCHI_SKILLS="$PROJECT/.agents/skills"
export CONTROL_HOME="/absolute/path/to/operator-data"
export ORCHI_CONTROL="$CONTROL_HOME/feature-control"

orchi() { uv run "$ORCHI_SKILLS/orchi/scripts/orchi.py" --control "$ORCHI_CONTROL" "$@"; }
orchi_operator() { uv run "$ORCHI_SKILLS/orchi/scripts/orchi_operator.py" "$@"; }

orchi doctor --repo "$PROJECT"
```

For a user-wide installation through Orchi, set `ORCHI_SKILLS="$HOME/.agents/skills"`. For third-party installers, use the location printed by that installer. For another agent, use the actual directory containing all five installed skills. Orchi's Python environment is separate from the project's test/build environment.

The target must be a Git repository with an existing commit and the intended canonical branch. Installation need not have initialized a workflow. Reserve the `initiatives/` namespace for Orchi's internal initiative records and inspect the path protection rules before adopting the workflow.

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
orchi begin --file /path/to/initiative.json
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

Use unique request/decision filenames for each gate. Signing refuses an existing decision output. Repeat the protocol for the exact next epic plan submitted with `plan --file /path/to/epic.json`, material amendments, and final acceptance. Never sign an arbitrary request without checking its provenance and actual content. The package does not provide an approval UI or managed operator service.

Use [retrieval](retrieval.md) to find documentation and read exact sources in the intended scope. Indexing
and lookup do not authorize or advance work.

The planner reads actual internal commits and initiative-scoped knowledge. Use `git show <head>:<path>` when inspecting internal code; do not move the canonical checkout to simulate progress.

## Configure workers

The bundle includes `codex-adapter.json`, `copilot-adapter.json`, and `claude-adapter.json` under `assets/`. Select a worker provider independently of the assistant coordinating the initiative. One foreground run uses one adapter; installing multiple integrations does not automatically mix worker providers.

Install and authenticate the selected terminal program under the intended worker identity. Check executable availability with `orchi doctor --require-agent codex`, `copilot`, or `claude`. Inspect the installed CLI's help for the flags described below. No model is selected by Orchi; an optional adapter `model` field makes the operator's choice explicit.

Copy and review the selected template outside worker access:

```bash
cp "$ORCHI_SKILLS/orchi/assets/copilot-adapter.json" "$CONTROL_HOME/adapter.json"
orchi run --adapter "$CONTROL_HOME/adapter.json"
```

The native adapters accept `kind`, optional `executable`, optional `model`, and `pass_env`. Claude and Copilot additionally accept `allowed_tools`, applied only during execution. Without explicit rules, their execution defaults permit reading and editing but do not approve shell commands. Bundled templates include shell permission so trusted task checks can run; narrow these rules to the project and use real OS/container isolation. Tool allowlists cannot enforce filesystem isolation for shell commands.

`pass_env` lists environment names, never secret values. The templates pass `HOME` and the provider's configuration-root variable. These must point to a worker identity's configuration, never an operator home containing signing keys. Environment-token authentication requires the operator to add the intended variable explicitly. Orchi does not copy credentials or configure login.

| Adapter | Prepare | Execute and result |
| --- | --- | --- |
| Codex | `codex exec` with `read-only` sandbox | `workspace-write`, ephemeral session, output schema and result file |
| Claude | `claude -p`, only Read/Glob/Grep tools | Coding tools with `dontAsk` and explicit allowed tools; validates successful JSON envelope and `structured_output` |
| Copilot | Piped noninteractive prompt, only view/glob/grep; denies shell and writes | Coding tools with explicit allow rules; silent non-streaming text must be one schema-valid JSON object |

Claude worker skills and MCP servers are disabled so a packet cannot recursively start orchestration. Copilot's available-tool list excludes delegation and skill invocation, and built-in MCP servers are disabled. These restrictions do not replace inspection of provider hooks, managed policy, and outer isolation. No blanket permission-bypass flag is set.

Each phase receives the exact packet and input directory. Process errors, invalid output, unresolved readiness, or preparation writes block progression. Controller activation occurs before an execution process starts; ordinary scope and verification gates still apply. No provider response can substitute for a passed check or signed approval.

The runner preserves process time/output limits and records observations before parsing results. It does not automatically retry malformed output or resume provider sessions. `run` is foreground and returns at review, checkpoint, approval, or blocker boundaries; continue through `next`.

## Command adapter or manual handoff

A trusted command adapter supplies `kind: "command"` and an `argv` array. It runs without a shell. The process receives `ORCHI_PHASE`, `ORCHI_PACKET`, `ORCHI_OUTPUT`, `ORCHI_SCHEMA`, `ORCHI_WORKSPACE`, and `ORCHI_TICKET`. It must write the phase's JSON result to `ORCHI_OUTPUT`. Prepare/execute output schemas are in the ticket's input directory. The command adapter does not itself provide a sandbox; its executable or external runtime must enforce access restrictions.

For manual handoff, `claim --task <id>` returns a workspace, packet, and ticket. Give the assistant only the assigned checkout and inputs. Relay its readiness using `activate --ticket <id> --file readiness.json` before execution. Relay its result using `submit --ticket <id> --file result.json`. Do not give a worker the entire control store merely to simplify CLI access.

## Review and checkpoint an epic

```bash
orchi review-request --scope epic --out /path/to/review-request.json
# Independent read-only review and triage produce an evidence-based report.
orchi review-record --file /path/to/review.json
# Reconcile actual code changes, knowledge entries, and impact dispositions.
orchi checkpoint --file /path/to/checkpoint.json
orchi next
```

When the controller requests repair, use `repair` and then execute the resulting ready tasks. Material redesign requires an amendment. The next epic plan must use the new actual `head`; a successful checkpoint is mandatory before advancing. Core remains unchanged throughout epic work.

## Finalize and publish

After all roadmap epics close:

```bash
orchi final-draft --out /path/to/finalization.json
# Reconcile cumulative behavior and root acceptance; replace the draft report marker.
orchi finalize --file /path/to/finalization.json
orchi review-request --scope initiative --out /path/to/final-review-request.json
orchi review-record --file /path/to/final-review.json
# Export, inspect, sign, and apply the exact final gate using the approval protocol.
orchi publication
```

`publication` returns the exact candidate and expected canonical parent; it does not mutate the branch. On a clean canonical checkout at the expected parent, the operator uses a normal `git merge --ff-only <candidate>`, observing repository protection rules. Do not force-update refs or silently rebase a candidate when canonical has moved.

```bash
orchi record-publication --commit <published-commit>
orchi export --out /new/private/audit-directory
```

Publication is not deployment. Store audit exports under suitable access and retention controls. Interrupted operations require observed process termination and explicit recovery; use `next`, `status`, and the [recovery reference](recovery.md) rather than resetting state or inventing successful evidence.
