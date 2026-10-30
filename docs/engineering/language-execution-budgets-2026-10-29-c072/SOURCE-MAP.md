# Current budget boundaries and implementation touchpoints

Inspected baseline: C071 main `814a0d84ff49b9fe28af9564d4e07314eb955de4`, tree `3d930c608136e138b53f4d5bf73d65c76eca3c65`. These are source observations, not new execution results. `source-binding.json` records the inspected file hashes. The [proposed contract](../../language-design/OK-LANG-007-configurable-execution-budgets.md) and [next task](NEXT-TASK.md) select future work.

## Fixed limits are enforced at several layers

| Current source | Observed responsibility | New-route requirement |
| --- | --- | --- |
| [agent_protocol.py](../../../ontokin/agent_protocol.py), `MAX_BUDGETS` and `validate_request` | Positive request values cannot exceed 100,000 operations / 30,000 ms. | Preserve the old protocol; distinguish defaults from host ceilings in an explicit new binding. |
| [program_protocol.py](../../../ontokin/program_protocol.py), `MAX_BUDGETS`, binding and validation | Reuses fixed core maxima and adds the logical-value cap. | Add new-route request validation without interpreting caller input as authorization. |
| [agent.py](../../../ontokin/agent.py), `_Check` | The outer service meter takes protocol defaults plus supplied reductions and checks time/work before runtime calls finish. | Resolve and propagate the same accepted context; raising an inner limit alone is insufficient. Preserve cancellation polling. |
| [agent_runtime.py](../../../ontokin/agent_runtime.py), `_Budget` | Rejects values above fixed maxima; starts a monotonic timer; counts work and preserves callback interruption. | Keep the old constructor behavior; use an explicit new authorized path. |
| [program_runtime.py](../../../ontokin/program_runtime.py), `_Budget`, `_compile`, `prepare_delivery` | Adds bounded value/JSON handling, passes limits and callbacks to compilation, retains compiler context for reach delivery. | Trace all adapters and reuse the resolved context rather than restart counters/deadlines. |
| [construction.py](../../../ontokin/construction.py), `LIMITS`, `ConstructionBudget`, `compile_construction` | Constructs a fixed-cap meter before linking/parsing the bundle; numerical work receives compilation limits and its callback. | Admit the entry header before expensive body work, then keep its consumed count/start time. |
| [reach_numeric.py](../../../ontokin/reach_numeric.py), `ReachExecutionWork` | Explicitly permits only reductions of 100,000 operations / 30,000 ms; numerical charges call inherited work and maintain categories. | Accept the new route's authorized context while preserving per-charge cancellation and legacy constructors. |
| [reach_export.py](../../../ontokin/reach_export.py), `_LocalArithmeticWork` | Standalone helpers impose their own fixed arithmetic bound when shared work is absent. | Supply accepted work in the new full path; do not accidentally enter a fresh or fixed-limit fallback. |
| [gltf.py](../../../ontokin/gltf.py), `export_glb`, `validate_export`, `read_glb` | Carries or creates work contexts and independently reads supplied bytes. | Propagate the actual remaining allowance; artifact budget metadata is never reader authority. |
| [reach_conformance.py](../../../ontokin/reach_conformance.py), `validate_reach_export` | Performs independent supplied-byte validation with numerical and output guards. | Keep the equations/oracles/guards; receive actual shared work for validation inside the request. |

The operation counters are semantic work units, not an instruction count, CPU-time measurement or memory quota. Existing nested counters and callbacks need an explicit debit map so the new route neither omits work nor accidentally adds a second charge for an adapter's bookkeeping.

## Syntax, binding and lifecycle

| Current source | Observed boundary | Implementation implication |
| --- | --- | --- |
| [syntax02.py](../../../ontokin/syntax02.py), `Parser02.program`, `parse_source_unit` | Ordered version/module/profile header, then requirements, imports, definitions and scene; explicit parser selection. | Place one contextual literal block after requirements and before imports in the new version only. |
| [syntax06.py](../../../ontokin/syntax06.py), `Parser06` | Requires exactly 0.6 / planar-reach-0.1. | Do not edit this contract to accept the new declaration implicitly. |
| [bundle.py](../../../ontokin/bundle.py) and [linker.py](../../../ontokin/linker.py) | Immutable source identity, designated entry, pinned modules, profile admission. | The entry owns the request; imports cannot change limits. A declaration changes the program revision normally. |
| [program_bindings.py](../../../ontokin/program_bindings.py) | Protocols select explicit contracts; `PROFILE_BINDINGS` holds one binding per profile. | Do not overwrite the existing profile by assigning it another Agent binding. Reserve new explicit identities. |
| [construction.py](../../../ontokin/construction.py), [linker.py](../../../ontokin/linker.py), [scene.py](../../../ontokin/scene.py), [gltf.py](../../../ontokin/gltf.py) | Many exact-profile branches select physical semantics, permitted imports, surfaces, histories and output behavior. | An explicit capability mapping must enumerate inherited behavior for the new profile. A new string alone is insufficient. |
| [program_agent.py](../../../ontokin/program_agent.py), `ProgramAgentService` | Versioned store/service selection, source edits, retained-prefix and artifact lifecycle. | Host policy is a trusted service input; candidate source controls its own request; saved state carries no permanent authority. |
| [agent_cli.py](../../../ontokin/agent_cli.py), `run` | Exact protocol routing; currently supplies protocol to the program service. | Agent/0.7 requires actual routing, policy configuration and lifecycle tests before discovery advertises it. |
| [cli.py](../../../ontokin/cli.py), `_program_export` and capabilities | Direct program/GLB path and fixed resource disclosures. | Add an explicit source/CLI binding that reports defaults separately from allowed ceilings and shares work through export. |

Budget syntax is a request, not an environment-control API. Do not introduce a source flag, mutable global maximum or inferred native-data stamp as permission to exceed host ceilings. The new implementation does not depend on the deferred C071 decoder-boundary proposal.

## Computation time is not animation length

[ConstructionCompiler.scene_fields](../../../ontokin/construction.py) checks that `scene.duration` is a positive Time. The core [Validator.scene_fields](../../../ontokin/validator.py) performs the corresponding check. [ExportOptions.checked_end](../../../ontokin/scene.py) requires a positive end within the scene duration. CLI `--end` and Agent `until_seconds`/export options operate on modeled time. These checks do not impose the 30,000-ms computation limit on an animation timeline.

The monotonic checks in `_Check`, `_Budget`, `ConstructionBudget` and `ReachExecutionWork` are cooperative elapsed-computation guards. A larger requested timeout does not change scene duration, sampling rate, output length or cancellation guarantees.

## Original evidence and limits remain separate

[tools/build_reach_source_artifacts.py](../../../tools/build_reach_source_artifacts.py) builds the original source recording cohort and checks its unchanged 100,000-operation setting. Preserve it and its fixtures. Use a new higher-budget cohort with explicit policy/source/result identities.

[test_reach_numeric.py](../../../tests/test_reach_numeric.py) covers numerical work charging, callback identity and admission context behavior. [test_reach_accounting.py](../../../tests/test_reach_accounting.py) covers shared accounting in ordinary tween and force work. Existing protocol/runtime/export tests are inherited regression obligations, not places to rewrite expected values for the new feature.

Keep separate caps separate. Examples include 32,768 operand bits, 256 cache entries, 64 cursor updates, fixed precision/series or interval-admission work, 100,000 certificates, logical value/JSON counts, retained state records, GLB bytes, key counts and validation poses. These are not aliases for the configurable request operation budget. The new conformance cases must demonstrate that a larger execution budget still respects such caps.
