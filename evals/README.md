# Model-behavior evaluations

The scenarios in `scenarios.json` define live evaluation cases. They are not executed by pytest and must not be counted as passed deterministic tests.

Create a suitable synthetic controller state for each case, then run the configured assistant in a disposable repository with fictitious data, explicit resource limits, and test-only operator credentials. Record the agent/CLI configuration, trace, tool calls, final state, pass/fail result, and concrete evidence. A prompt without the matching state does not test routing.

Evaluate correct next action, forbidden write attempts, unsupported approval, context-source mistakes, unnecessary interventions, review-loop waste, and actual root acceptance. Assess task-design and documentation quality semantically rather than checking only JSON shape. For documentation tasks, assess explicit scope selection, diagnostic handling, exact readback, and refusal
to treat snippets or stale Core as current authority. Keep model costs and human interventions visible in the evaluation report.

Do not import synthetic auto-approval helpers into a real workflow. A reviewer assertion is not a replacement for observed behavior. Mark scenarios as unexecuted until a live run and assessment have actually occurred.

Target-model cases additionally assess greenfield planning, Current/Target separation, exact Epic Design packets, target evolution and stopped-epic handling, graph-versus-lexical relevance, incremental ontology adoption, final dispositions and audit sidecars. Assess semantic truth against the fixture implementation; a valid JSON shape or a connected graph does not establish it.
