# Security and operating limits

## Trust boundaries

The human operator controls the signing key, policy, check registry, adapter configuration, canonical publication, and access to the control store. Workers receive bounded task packets and assigned worktrees, not operator privileges. The coordinator may relay controller operations only within the permissions assigned by the operator.

Putting files in different directories is not access isolation. A worker process launched under the controller's operating-system identity may still read or modify resources that identity can access. Orchi's local runner does not automatically change users, enter a container, or make shared Git metadata inaccessible. Enforce these boundaries through operating-system/container policy and a trusted adapter wrapper or external relay where necessary.

Never give workers the private key, operator home directory, privileged cloud credentials, unrestricted control-state access, or canonical write permissions. Review the actual runtime sandbox, not merely the adapter's name. A prompt, skill instruction, signature format, or Git worktree is not an adversarial security boundary.

## What the controller enforces

Strict contracts reject unknown fields, unresolved task-design questions, unsafe paths, forbidden write targets, unknown check IDs, and incomplete acceptance mappings. Task packets bind exact sources, plan identity, and start state. Readiness must precede execution acceptance. Fenced tickets and transactional reservations prevent conflicting legitimate claims; candidates must pass scope checks and actual verification.

Core and accepted initiative definitions cannot be modified by ordinary task candidates. Checkpoints require actual impact dispositions and evidence. Finalization requires completed roadmap epics and root acceptance coverage. Publication identifies one exact approved candidate based on the original canonical parent.

These checks are acceptance controls within a trusted local controller. They do not prevent a process with broader system access from bypassing the controller, modifying external systems, reading undeclared files, or corrupting the controller itself.

## Untrusted material and processes

Treat repository prose, code comments, retrieved text, process output, and worker reports as task data rather than authorization. They cannot grant permission to reveal secrets, change policy, sign approvals, or expand task scope.

Commands use argument arrays, not shell interpolation. Checks and workers have process time/output limits and a minimal inherited environment. Every allowed environment variable is an explicit operator choice. A command that executes repository code still executes potentially dangerous code; absence of a shell does not make it safe.

Additional reads are reported cooperatively. Review authorship, independence, coverage, and semantic quality are not proven by a JSON report. Use genuine independent review and human scrutiny for consequential changes.

## Keys and state

Use an operator-owned external directory with restrictive permissions. `operator.py keygen` refuses existing key paths and writes the private key with restrictive permissions. Only the public key belongs in policy. `operator.py sign` is a human/operator command following inspection of the exact request; workers must never call it on the human's behalf.

Keep private keys and active state out of Git and worker-visible prompts. Audit exports may contain full source and process output. Apply access, retention, and backup controls accordingly. Do not assume Git alone contains the complete execution audit.

## Supported operating scope

The controller is local and POSIX-dependent. It manages one repository and one initiative per control directory, with parallel tasks inside one active epic. It is not a distributed or multi-tenant service. Native Windows execution, automatic baseline rebasing, automatic deployment, protected-branch pull-request orchestration, and autonomous operator approval are outside the implementation.

Project portability means that the installed skills and controller do not depend on the target application's language. It does not mean every toolchain works without preparation: trusted checks, per-worktree dependencies, external services, credentials, branch workflow, and sandbox policies must be configured for each project.

Deterministic tests validate the protocol and its mechanical boundaries. Live model behavior, authentication, and real worker isolation require separate operator validation; see [testing](testing.md).
