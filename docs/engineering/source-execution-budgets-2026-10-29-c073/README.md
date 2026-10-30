# C073: configurable source and CLI execution budgets

October 29, 2026, America/Denver. This increment implements the source/CLI task selected in [C072](../language-execution-budgets-2026-10-29-c072/NEXT-TASK.md). Its implementation status, exact candidate, executed evidence and integration are recorded here when validation finishes. This working record does not itself claim integration or a complete release.

## Implemented path

Explicit source `0.7` / `planar-reach-budget-0.1` requests operations and computation time in an entry header. A trusted `HostPolicy` authorizes finite ceilings; optional caller caps may only reduce the source request. Omitted fields stay at 100,000 operations and 30,000 ms. The source/CLI path produces GLB/0.7 and independently checks the supplied bytes using the same remaining work and original deadline.

The [adoption decision](../../language-design/execution-budgets-v0.1/ADOPTION-C073.md) defines the concrete grammar, boundaries, diagnostics and limited corrections. The [debit map](DEBIT-MAP.md) identifies each participating adapter. [The example guide](../../../examples/execution-budgets/README.md) explains trusted host setup, caller reductions and the frozen physical workload.

## Evidence boundaries

The original tests and fixtures remain unchanged. New conformance tests cover the 24 C073 cases; five Agent lifecycle cases remain deferred. Candidate and resulting-main evidence must identify actual source commits, inputs, commands, interpreter and failures. Preliminary development results and failed attempts are retained separately and cannot stand in for the final candidate.

The new larger-workload cohort preserves a default-limit refusal and an authorized success only when both are actually observed. Its six vessels use frozen geometry and an independent force/impulse oracle. Khronos, Three.js and browser checks supplement the interpreter's supplied-byte validator; reviewed captures establish only their named artifact and views.

## Preserved obligations

Historical original28 remains 24/28 failed, with P11/P16/P23/L03 unresolved. M1 is rejected. C035 remains held including adverse timing. C057, complete reach acceptance, historical LFS migration and the full GOAL remain open. Higher-budget results cannot pass the original fixed-budget gate retroactively. Earlier proposal rejections and held runtime changes retain their prior meanings.

The next increment is the separately versioned Agent/0.7 lifecycle: discovery, candidate-source authorization, create/edit rollback, saved-program reauthorization, evaluate/export/retrieve, cancellation, request isolation and idempotent retries. After that bounded integration, choose the next representative modeling, animation or simulation capability from GOAL. Another optimization investigation is not a prerequisite.
