# Documentation

How Orchi behaves and is built now. Planned work is in GitHub Issues and, while
it is under way, in `docs/work/` on its branch; the
[knowledge reference](../skills/orchi-core/references/knowledge.md) sets the
rules. The installed skills' `SKILL.md` files and references define the
behavior; these pages describe how the areas fit together and keep the decisions
still in force.

| Page | Covers |
| --- | --- |
| [`README.md`](../README.md) | What Orchi is, how it works, and how to start |
| [`docs/workflow.md`](workflow.md) | The core workflow: exploration, planning, delivery, review, subagent roles, Issue forms |
| [`docs/pool.md`](pool.md) | The session pool: Orchi, crews, workers, messages, modes, clearing |
| [`docs/design.md`](design.md) | User interface design with Impeccable: design depth, designer crews, the design audit |
| [`docs/standards.md`](standards.md) | Engineering standards: `ENGINEERING.md`, the default stack and checks, gate integrity |
| [`docs/context.md`](context.md) | Project context: current documentation, working documents, the ownership map and its checks |
| [`docs/installation.md`](installation.md) | Installing, upgrading, and removing Orchi and Impeccable |
| [`docs/testing.md`](testing.md) | Package validation, the test suite, the smoke test, and live checks |
| [`docs/references.md`](references.md) | External standards and tools Orchi relies on |
| [`docs/out-of-scope/`](out-of-scope/README.md) | Proposals Orchi does not adopt, and why |

## Ownership

| Code | Pages | Area |
| --- | --- | --- |
| `skills/orchi-core/SKILL.md` | `docs/workflow.md`, `README.md` | Workflow |
| `skills/orchi-explore/**` | `docs/workflow.md` | Workflow |
| `skills/orchi-plan/**` | `docs/workflow.md` | Workflow |
| `skills/orchi-deliver/**` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/execution.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/exploration.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/github.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/planning.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/readiness.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/review-delivery.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/references/testing.md` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/roles/**` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/scripts/status.py` | `docs/workflow.md` | Workflow |
| `skills/orchi-core/assets/github/ISSUE_TEMPLATE/**` | `docs/workflow.md` | Workflow |
| `skills/orchi/**` | `docs/pool.md` | Pool |
| `skills/orchi-work/**` | `docs/pool.md` | Pool |
| `skills/orchi-dashboard/**` | `docs/pool.md` | Pool |
| `skills/orchi-core/scripts/dashboard.py` | `docs/pool.md` | Pool |
| `skills/orchi-core/references/pool.md` | `docs/pool.md` | Pool |
| `skills/orchi-design/**` | `docs/design.md` | Design |
| `skills/orchi-core/roles/orchi-designer.md` | `docs/design.md` | Design |
| `skills/orchi-core/assets/github/workflows/orchi-design.yml` | `docs/design.md` | Design |
| `skills/orchi-standards/**` | `docs/standards.md` | Standards |
| `skills/orchi-core/references/standards.md` | `docs/standards.md` | Standards |
| `skills/orchi-core/scripts/standards.py` | `docs/standards.md` | Standards |
| `skills/orchi-core/assets/standards/**` | `docs/standards.md` | Standards |
| `skills/orchi-core/assets/github/workflows/orchi-standards.yml` | `docs/standards.md` | Standards |
| `skills/orchi-core/references/knowledge.md` | `docs/context.md` | Context |
| `skills/orchi-core/references/retrieval.md` | `docs/context.md` | Context |
| `skills/orchi-core/scripts/knowledge.py` | `docs/context.md` | Context |
| `skills/orchi-core/assets/docs/**` | `docs/context.md` | Context |
| `skills/orchi-core/assets/github/workflows/orchi-docs.yml` | `docs/context.md` | Context |
| `skills/orchi-core/scripts/orchi_install.py` | `docs/installation.md` | Installation |
| `skills/orchi-core/scripts/orchi_core/**` | `docs/installation.md` | Installation |
| `tools/install.py` | `docs/installation.md` | Installation |
| `bin/**` | `docs/installation.md` | Installation |
| `package.json` | `docs/installation.md` | Installation |
| `tools/validate_package.py` | `docs/testing.md` | Testing |
| `tools/smoke_install.py` | `docs/testing.md` | Testing |
| `tests/**` | `docs/testing.md` | Testing |
| `.github/workflows/**` | `docs/testing.md` | Testing |
