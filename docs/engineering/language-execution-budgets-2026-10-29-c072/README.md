# C072: language execution budgets become the next feature

October 29, 2026. **The owner has changed the active development priority to configurable execution budgets.** This checkpoint evaluates the current source and records the feature design and next implementation task. It does not implement the new syntax or increase any runtime limit.

## Decision and scope

OntoKin remains a language for AI agents to create and reuse increasingly capable 3D objects, animations and simulations. Programs should be able to request larger execution budgets within ceilings independently authorized by their environment. Preserve defaults of 100,000 operations and 30,000 ms and every existing acceptance test's limits. Computational efficiency remains a continuing engineering concern; a successful optimization investigation is not a prerequisite for this feature.

The [proposed language contract](../../language-design/OK-LANG-007-configurable-execution-budgets.md) separates source requests, defaults, optional per-call reductions and trusted host ceilings. It defines a literal entry-header declaration, bounded admission, one shared operation ledger/deadline, explicit new bindings and honest execution reporting. The [source map](SOURCE-MAP.md) identifies the actual implementation boundaries. The [new conformance plan](../../language-design/execution-budgets-v0.1/conformance-plan.json) states expectations, not test results.

The next task is [C073 implementation](NEXT-TASK.md): a working source/CLI path from a requested budget through construction, evaluation, recording and independent supplied-byte validation. Do not substitute another optimization feasibility review for this task.

## Why the existing code needs an explicit feature

Current Agent request fields can lower a budget but cannot exceed the fixed maxima. The maxima appear in protocol validation, the outer service check, runtime and construction meters, reach arithmetic and standalone fallback work. Larger host ceilings therefore need explicit propagation through the complete path. Raising a constant or adding a CLI flag alone would leave other rejection points and could change old contracts.

The 30,000-ms value measures computation time. Scene duration is a separate source value; its positive-time check and export interval check do not impose a 30-second animation limit. Increasing computational resources does not increase the other output or numeric caps automatically.

## Relationship to C071 and earlier work

Baseline main is `814a0d84ff49b9fe28af9564d4e07314eb955de4`, tree `3d930c608136e138b53f4d5bf73d65c76eca3c65`. The supplied C071 metadata and recovered original complete packet identify 3,804 tracked files / 623,146,522 bytes. Its original ZIP has SHA-256 `cc54aa5c42f046c310fbbd18ecfa63830111e2ec1ffdb36767a1878404e35410`; fresh source packet verification passed. The complete source was materialized and its actual Git tree and raw final commit verified. It is a shallow source recovery, not a full-history clone.

[C071's historical next-task nomination](../reach-group-key-projection-2026-10-29-c071/NEXT-TASK.md) proposed a native execution/immutable-decoder optimization boundary. It was unstarted. The owner's current direction supersedes that nomination as the active next step. Preserve its document as history. This checkpoint neither adopts C068 nor revives C069's rejected list receipt or C070's unselected angular cache. It does not claim to resolve C057.

C071 explicitly released its technical/checker/packet scope in [Issue #26 comment 6512937667](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6512937667). C072's bounded documentation scope is recorded in [comment 6513542199](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6513542199). The separate image-download request and historical LFS migration are outside this feature scope.

## Preserved status and validation meaning

Historical original recordings remain **24/28, failed**, with **P11/P16/P23/L03 unresolved**. M1 remains rejected; C035 remains held including adverse timing; C057, complete reach release and historical LFS migration remain open. Earlier released capabilities and all remaining domains in [GOAL](../../../GOAL.md) retain their meanings.

C072 changes only selected active project documents and new design/checkpoint files. Existing runtime, tests, fixtures, contracts, preservation manifests and workflows remain byte-identical. Product imports, runtime test suites, executions, meshes and hosted jobs are not part of this documentation checkpoint. Documentation validation and independent source/design review establish the quality of the proposed next step, not implementation or release acceptance.

The exact source bindings, final reviews and executed documentation checks are recorded in `source-binding.json`, `reviews.json` and `validation.json` in this directory. Publication and handoff metadata identify actual candidate/final commits separately; no hypothetical merge identity is used.
