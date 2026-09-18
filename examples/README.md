# Examples

The examples are bundled with the installable skill so they remain available in a consuming project:

| Example | Purpose |
| --- | --- |
| [Initiative](../skills/orchi/assets/examples/initiative.json) | A complete request with an ordered two-epic roadmap |
| [Values epic](../skills/orchi/assets/examples/epic-values.json) | An active epic with two independent designed tasks |
| [API epic](../skills/orchi/assets/examples/epic-api.json) | A later epic planned against actual accepted state |
| [Policy template](../skills/orchi/assets/policy.example.json) | Operator-selected canonical branch, public key, checks, and limits |
| [Codex adapter](../skills/orchi/assets/codex-adapter.json) | Native Codex worker execution configuration |

The all-zero `based_on` values are explicit placeholders. Replace them with the current accepted head when authoring a plan, and replace every source path, check identifier, and requirement with project-specific content. The examples do not authorize work and must not be submitted unchanged to an unrelated controller.

The policy template requires a real operator public key and trusted test command. Adapter credentials and `HOME`/`CODEX_HOME` must belong to the intended worker identity, not to a privileged operator.

For an executable demonstration, run `python tools/demo.py --out /tmp/orchi-demo` from a provisioned Orchi checkout. Use a new output directory. The demo emits a task packet bound to its disposable checkout and an audit report. Neither its synthetic workers nor its automatic test approvals are production components.
