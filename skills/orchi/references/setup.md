# Operator setup

Install all five skill directories as siblings. Use `uv run <skills>/orchi/scripts/orchi.py doctor` to inspect prerequisites; the script declares its own dependencies. A managed Python environment can instead install `scripts/requirements.txt` and run the scripts directly.

Control state, the private signing key, trusted checks, and adapter configuration belong outside worker access. The human operator selects the repository, canonical branch, verification commands, process limits, and real isolation boundaries. Installation and diagnostics do not make those decisions or authorize execution.

Follow the bundled [operator guide](operator-guide.md). Key generation and signing use `<skills>/orchi/scripts/operator.py`, not a tool from an external source checkout. Only the public key belongs in policy. Never create or use a private signing key on the human's behalf inside a worker session.

Initialize a fresh external control directory with `setup --repo /project --policy /operator/policy.json`. Pass `--control` explicitly or set `ORCHI_CONTROL`; the explicit option wins. One control directory manages one initiative with one active epic and bounded parallel tasks. Do not reuse its database for a different initiative.

Greenfield requires a canonical baseline commit but no existing product code or `docs/`. Choose baseline checks according to actual prerequisites, retain meaningful final checks, and author accepted Intent before planning the first epic. For existing docs, use [bootstrap](bootstrap.md); during an initiative, its unshipped Core changes remain in Working Knowledge until final reconciliation. Other canonical deliveries are adopted only through accepted code-and-knowledge sync.

Policy defaults to atomic exact-commit publication and cumulative checks. Configure an explicit squash/merge shape, scoped integration checks or shared local check resource directory before setup when needed. No active-store conversion, hosted PR creation or distributed resource coordinator is implied.
