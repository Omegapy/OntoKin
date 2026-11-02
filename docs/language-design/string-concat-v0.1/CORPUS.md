# C087 frozen source and workflow corpus

The [input manifest](freeze/INPUTS-MANIFEST.json) identifies 546 independent files totaling 11,313,625 bytes. The manifest is separate from that count. The packet was independently authored and reviewed; its original control states were preflighted on unchanged C086 before publication, readback and C087 runtime implementation. This guide adds navigation without changing the frozen corpus.

## Representative component task

The [panel-task file manifest](../../../examples/string-concat/agent/panel-task.files.json) binds the [entry source](../../../examples/string-concat/agent/sources/panel-task.ok), four pinned libraries and a PNG asset. Two independent occurrences supply different prefixes to the same reusable panel library. Its String expression computes each occurrence's stable keys. A separate orange marker has its own recorded motion.

```bash
python3 -m ontokin export examples/string-concat/agent/panel-task.files.json --bundle --target ontokin.glb/0.20 --output /tmp/ontokin-namespaced-panels.glb
```

Related frozen entry states change a prefix, insert or remove a member, reorder declarations, restore the original source, exercise an invalid prefix or width, and distinguish an authorized larger request from an ungranted one. The [Agent expectations](../../../examples/string-concat/agent/expected.json) supply exact source transitions, expected identities, payloads and dependency relationships. Each entry continues to bind its original library and asset bytes.

The eleven actual workflow roles cover discovery, construction, scoped repair, immutable old-artifact retrieval, idempotence/retry, durability/reopening, publication interruption and recovery, cancellation, current host/caller authority, and member insertion/removal/reordering/restoration. The recorded workflow evidence and independent verdicts are identified in the [engineering record](../../engineering/string-concat-2026-11-01-c087/README.md); the expectations alone do not establish execution.

## Separate verification scopes

| Frozen scope | Meaning |
| --- | --- |
| [108 core source cases](../../../examples/string-concat/expected.json) | 72 valid and 36 intended refusals: exact types and declaring versions; Unicode/UTF-8 boundaries; evaluation order; per-result/cumulative limits; static checking; dependencies and generated-value restrictions. |
| Ten Agent source states | Seven valid states and three intended refusals for the reusable panel task. |
| 85 explicit `.19` literal controls | 78 core controls and seven panel exports independently authored before implementation. |
| 28 inherited negative controls | Preserve the existing diagnostic outcomes for previously invalid operations. |
| [Runtime boundaries](../../../examples/string-concat/runtime-boundaries.json) | Independently specified scalar-width vectors, operation stopping prefixes, cancellation, real elapsed-time exhaustion, current authority, missing context and staged taint guards. |
| Hostile delivered evidence | 75 supplied-byte GLB adversaries and two coherent Agent-history adversaries, with positive controls. |

The [preflight gate record](freeze/PREFLIGHT-GATES.json) reports 122 passing observations across 115 distinct control states on C086. Some controls have multiple independent observations; counts from these scopes are not summed as unique tests or release gates. Earlier failed drafts and preflights retain their own identities in the complete handoff.

The [adopted specification](SPECIFICATION.md) defines semantics. The [grammar overlay](ontokin-string-concat.ebnf) preserves inherited tokens and precedence. Existing `.ok` sources, revisions and dependencies remain the repair basis; no expected value is inferred from a candidate-produced result.
