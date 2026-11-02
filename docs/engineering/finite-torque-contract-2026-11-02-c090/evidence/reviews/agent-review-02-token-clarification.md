# Agent review addendum: inherited token status

**Passed, exact scoped delta only.** `agent-review-01` remains bound to its original input snapshot. This addendum extends that review to SPECIFICATION.md SHA-256 `1df5fe712760d3e0af6614f6fbd200708bae76a1191e1aa5829dff8382e74ced`.

An exact whole-file comparison verified one replacement from the prior specification SHA-256 `f46327fb246c904f584e5d8ae1a42c5962e43d8cff073ee5530a20d7ef531050`. The revised sentence says torque-specific interpretation is contextual while inherited `using` and `for` remain reserved with their existing uses. It does not make those tokens ordinary identifiers. No other byte differs, and the other ten reviewed source/Agent inputs remain unchanged.

Independent static inspection of unchanged C088 confirms `syntax.py` already reserves `using`, `syntax02.py` adds `for` to `RESERVED_02` and consumes it in generated-parts syntax, and `.21` inherits that parser chain. The clarification aligns the prose with inherited grammar and preserves the extension's promise not to introduce global reserved identifiers.

No runtime or schema checks were rerun for this prose-only clarification. The original 565 schema probes and their hashes remain unchanged. This addendum changes no schema, new-state requirement, numerical contract, Agent lifecycle, source repair, recording or release claim. The prior review's scope limits still apply. The JSON companion binds the exact prior review, before/after specification, clarification receipt and inherited syntax-source hashes.
