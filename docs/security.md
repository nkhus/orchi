---
kind: reference
area: orchi
artifacts:
  - skills/orchi/scripts/orchi_core/process.py
  - skills/orchi/scripts/orchi_core/relay.py
  - skills/orchi/scripts/orchi_core/signing.py
relations:
  part_of: [docs/README.md]
---
# Security and operating boundaries

## Authority ownership

The operator owns policy, registered check commands, signing keys, adapters, canonical write access and actual OS/container permissions. Workers receive an assigned worktree, packet and bounded communication capability. A planner/reviewer does not inherit authority to sign or publish. The controller rejects protected writes, stale identities, unknown checks and unapproved transitions; it does not make untrusted execution safe by itself.

Keep the private signing key outside the repository and worker workspaces and inaccessible to worker identities. Direct operator `decide` binds the exact displayed request ID and rejects in-project/worktree keys. Separate paths alone do not isolate processes sharing an OS account. Do not expose a whole controller store merely to let a worker call a read command.

## Worktree and process limits

Git worktrees share objects, refs and repository configuration. They are not sandboxes. The repository may contain trusted checkout filters; hooks and several implicit Git features are disabled for controller object operations, but repository/project code still executes through operator-registered checks. A worker with broad filesystem access can attack control state, sibling worktrees or credentials unless the outer runtime prevents it.

Foreground processes have wall-clock/output limits and POSIX process-group termination. This cannot stop remote jobs or prove every external side effect terminated. Confirm observed termination before `--stopped` recovery. No private key, arbitrary approval identity or canonical push credential belongs in an agent environment. Provision build/test dependencies separately and consider running hostile repositories in isolated disposable environments.

## Ticket-bound worker relay

The foreground runner creates a temporary local Unix socket with a per-phase capability. Its allowlist is exact snapshot `read` and, only after readiness, bounded `scope`. Requests are bound server-side to one ticket; a client cannot specify another ticket or invoke setup, arbitrary shell checks, approval, sync or publication. Requests/responses are bounded; repeated IDs cannot change their arguments. The channel ends when the foreground phase ends.

The standalone `worker_request.py` helper needs only the channel environment, not the controller database. Capabilities and socket access must be restricted by the outer runtime. Same-user sibling processes are not isolated by random paths or file modes. Sandboxes that block Unix IPC must relay manually or configure a permitted narrow channel; Orchi must report the blocker rather than disable the sandbox. Live Codex IPC behavior is an environment-specific validation, not asserted by local command-adapter tests.

## Concurrency and resources

Scope envelopes provide mechanical checks, not proof of semantic permission. Workers must escalate fixed decision/Target changes even inside allowed directories; independent review checks the actual diff. Snapshot reads require explicit consistency choices. Passing tests or nonoverlapping paths never prove arbitrary semantic independence.

Named check resource locks require a shared operator-owned directory on the same supported host. They neither coordinate unrelated machines nor fence external database/deployment jobs. Operator-managed isolation is preferred. Task-exclusive resource labels remain local to a controller.

## Git and publication

Controllers use unique internal ref namespaces. Original provenance is immutable; explicit sync advances an accepted integration base without editing historical evidence. Rewritten upstream fails closed. Final publication checks exact tree/base/parent shape and visibility. Local CAS refuses checked-out target branches and cannot overwrite a racing canonical commit. Hosted protections and credentials remain with the operator; a local handoff is not a created remote PR.

Audit exports may contain proprietary source context, logs, candidate objects and observations. Store them privately with appropriate retention. Source manifests and archived attempts preserve identity; full internal replay requires retained export objects and packets. Final attestation is necessarily outside its own signed candidate tree.

## Platform and non-goals

This pack targets Python 3.11+, POSIX, SHA-1 Git repositories and SQLite FTS5. Windows process/resource isolation, automatic active-store conversion, remote job execution, hosted PR creation, distributed scheduling, cross-repository atomicity and production deployment are not implemented. Incremental publication of one request is not a supported delivery mode. Initialize a fresh operator control directory for these contracts.
