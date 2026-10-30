# Source execution budgets: C073 adoption

**Identity:** `OK-LANG-007/0.1.0-experimental.1`  
**Decision date:** October 29, 2026, America/Denver  
**Scope:** Explicit source `0.7` / `planar-reach-budget-0.1`, direct source/CLI execution and recorded `ontokin.glb/0.7`. `ontokin.agent/0.7` is unavailable.

This decision adopts the C073 implementation contract below. It advances the [GOAL](../../../GOAL.md): programs can request enough computation for their modeled objects and behavior, subject to the execution environment's authorization. The ordinary defaults remain 100,000 operations and 30,000 milliseconds. Development integration and complete feature release remain separate decisions under [OK-ENG-009](../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md).

The [C072 proposal](../OK-LANG-007-configurable-execution-budgets.md), [proposed grammar](grammar.ebnf) and [29-case conformance plan](conformance-plan.json) retain their original bytes and preparation status. This separate record supplies the implemented bounds, API and destination decisions. [The C073 engineering record](../../engineering/source-execution-budgets-2026-10-29-c073/README.md) identifies actual source revisions, execution results, review and remaining gates. This document does not certify a complete release or an unrun acceptance case.

## 1. Source declaration and identity

The [implemented grammar](grammar-c073.ebnf) keeps the proposed declaration shape:

```ontokin
ontokin "0.7";
module Workshop @"workshop";
profile "planar-reach-budget-0.1";

execution {
    max_operations = 400000;
    max_elapsed = 80[s];
}

// Imports, definitions and the scene follow
```

The entry may contain one optional block, after every `requires` declaration and before imports, definitions or its scene. A block contains one or both fields, each once, in either order. Empty, repeated, unknown and misplaced declarations fail. Imported modules cannot declare a budget, including a smaller one. The name `execution` is contextual in the new header; earlier reserved-word sets remain unchanged.

`max_operations` is a positive decimal integer literal. `max_elapsed` is a positive decimal seconds literal with `[s]`. Its value must convert exactly to whole milliseconds: `60[s]`, `75[s]`, `80[s]`, `0.5[s]` and `0.001[s]` are valid representations. Extra fractional zeroes are permitted when the result is integral; `0.5000[s]` means 500 ms. Signs, exponent notation, arithmetic, names, calls, booleans, null values, wrong units and nonintegral milliseconds fail. No rounding repairs a request.

The declaration belongs to the immutable source bytes and changes their ordinary revision hash. Policy and caller caps are execution context and do not alter that hash. Compilation requires the same entry revision that was admitted. The implementation does not rewrite a source `0.6` header or infer behavior from numerical version order.

## 2. Defaults, requests and host authority

Each of the two fields resolves independently:

1. Use the source field when present; otherwise use its language default.
2. An explicit caller cap must be no larger than that source request. When valid, it becomes the effective limit.
3. The effective limit must fit the host ceiling. Otherwise reject before body evaluation.

There is no silent clamping, larger-budget retry or unlimited value. An omitted field keeps its default even when the host permits more. A host below the defaults requires an explicitly smaller source request or caller cap. A caller cap can reduce a larger source request enough to fit the host, but cannot enlarge an omitted default.

The trusted host constructs [`HostPolicy`](../../../ontokin/execution_budget.py). Its default ceilings are 100,000 operations and 30,000 ms. Both policy values and accepted effective values must be exact positive Python integers through `2**53 - 1`; booleans and floats are rejected. This is the representable input range, not a claim that every workload or runtime duration in that range has been tested. An optional bounded policy label identifies host configuration; an omitted label becomes a deterministic SHA-256 identity of the ceiling values.

The source, imported libraries, command arguments and artifact metadata cannot create policy. This boundary contains an untrusted OntoKin program inside its host interpreter. It does not sandbox Python code that can replace interpreter objects or its process.

## 3. Bounded entry admission

[`SharedExecutionBudget`](../../../ontokin/execution_budget.py) records the original monotonic start before scanning the entry header. Its provisional limits are the per-field minimum of the ordinary default, host ceiling and any already supplied caller cap. Authorization promotes this same ledger once; it retains every consumed operation and the original start time.

The new admission policy makes the proposal's unspecified bounds concrete:

| Boundary | Implemented rule |
| --- | --- |
| Header prefix | At most 65,536 UTF-8 bytes, including skipped comments, whitespace and the first lookahead token needed to end header admission. |
| Header identifiers and decoded strings | At most 256 characters per token. Strings retain the existing supported escape forms; Unicode escape notation is unsupported. |
| Budget number token | At most 32 characters before integer conversion. The checked value must also fit the positive representable range. |
| Header byte work | One operation for each started group of 64 UTF-8 bytes consumed. |
| Header token work | One operation for each emitted prefix token, including a consumed end marker when applicable. |
| Deadline checks | Cancellation is polled before a charge. An observed elapsed value equal to the limit is valid; a value above it fails. |
| Operation checks | An exact consumed limit is valid. The next charged operation fails and is reported as the attempted excess. |

The scanner recognizes comments, strings and the ordered header grammar. It does not use a whole-source expression search, evaluate a value, resolve imports or lex the body to discover authorization. Long comments and fake declarations inside strings remain bounded. Full parsing subsequently checks the unchanged source/token limits and pays for its actual work, including reparsing the header. A requested limit already below consumed header work or elapsed time fails at promotion.

## 4. Trusted host and CLI entry points

The direct Python entry is [`execute_budgeted_export`](../../../ontokin/budget_runtime.py). It accepts an immutable `ProgramBundle`, a host `policy`, optional `caller_caps`, recording `options`, a cancellation `check` callback and an optional clock used by deterministic host tests. It returns `BudgetedExport(data, report)`. A success contains independently verified GLB bytes; a normal source, authorization, numerical or resource failure contains `data=None` and a bounded report.

The CLI uses this path only when `--target ontokin.glb/0.7` is selected. It accepts a single `.ok` file or the existing explicit `--bundle` file manifest. A trusted operator can provide a launcher such as:

```python
from ontokin.cli import main
from ontokin.execution_budget import HostPolicy

raise SystemExit(main(host_policy=HostPolicy(400000, 80000)))
```

The host controls this launcher and its policy. `python3 -m ontokin` retains the default host ceilings. There is no command flag that grants a larger ceiling. The new `--max-operations` and `--max-elapsed-ms` flags supply caller reductions only, and are rejected for older destination selections. A source requesting 400,000 operations cannot obtain them by merely passing the same number as a caller cap on an ordinary host.

`capabilities(host_policy=...)` reports the defaults, current ceilings, policy identity, supported fields and experimental source/CLI status separately. Earlier command defaults and Agent selections retain their meanings. The newly reserved Agent contract is not advertised as available.

## 5. Shared computation, reporting and failure

One accepted ledger covers header admission, linking, construction, numerical work, evaluation, recorded export, independent supplied-byte verification and the product result checks. Internal stages, imported modules, sampled frames and helper adapters cannot acquire another full allowance. Numerical category counters describe work already debited to the ledger; they do not grant extra operations. [The debit map](../../engineering/source-execution-budgets-2026-10-29-c073/DEBIT-MAP.md) describes the actual adapters.

The receipt identifies source and program revisions, implementation identity, language/profile/destination, policy identity, source request, caller caps, ceilings, effective limits, consumed operations, elapsed time, stage and terminal status. Unresolved source/effective values are null on early admission failure. Budget metadata is descriptive; a later reader must receive real host-authorized work. A separately initiated readback request is a separate authorization and must be reported as such.

Cancellation preserves the caller's exception object and order. Deadline checks are cooperative; they cannot interrupt an arbitrary blocking callback. The host controls aggregate concurrency, process memory and any required process termination. A larger computation timeout changes neither `scene.duration` nor the chosen recording endpoint, sample rate or physical equations.

Failure returns no completed artifact bytes. A reported prefix identifies only state already established as valid; a missing prefix makes no retained-state claim. This direct path does not store or edit accepted Agent revisions. Those rollback, saved-program, retry and resume lifecycles belong to the deferred Agent increment.

CLI file persistence follows successful computation and is a separate transport step. The new writer stages both complete files and restores prior destinations after a handled publication failure. If restoration itself fails, it retains the remaining recovery backups and reports their locations. Two filesystem paths do not become a crash-atomic transaction: a process crash between replacements still requires checking the report's exact artifact hash. Budget exhaustion during computation publishes neither output file. Final transport reports retain the existing JSON output bounds.

## 6. Explicit GLB/0.7 destination

Source `0.7` explicitly inherits the construction, surface, impulse, force and planar-reach capabilities enumerated in [`profile_capabilities.py`](../../../ontokin/profile_capabilities.py). The new source may import the permitted earlier profile modules; earlier declaring modules cannot import a source `0.7` dependency. Actual source versions and profiles remain available to their semantic checks.

Recorded output uses `ontokin.glb/0.7`, metadata schema `0.7`, source profile `planar-reach-budget-0.1` and that same profile in reach-source metadata. The ordinary geometry, material, physical-history, exact-clock, sampling and continuous certificate checks remain required. An earlier or omitted destination selection rejects the new contract. Source execution and in-request readback require an admitted shared context with its actual remaining work; neither a fresh default meter nor metadata can replace it. The execution receipt remains outside artifact bytes and identifies the returned artifact by hash.

Two numerical details are adopted only for the new binding:

- The independent impulse reference retains the exact identity `R * 0 = 0` when the authored point is exactly the target's center. Its lever error is zero in that case. Every rotation product and sum is then exactly zero; no angular impulse can arise from that lever. Nonzero levers retain their previous bound, and earlier source profiles retain their behavior and charges.
- Before normal outward binary64 conversion, the GLB/0.7 writer multiplies each source position and source rotation error bound by the exact factor `2`. The independent impulse reference propagates incoming vector uncertainty on each coordinate and then sums the resulting intervals; its required error width can therefore exceed the production kernel's bound around its actual rounded anchor by more than one rounding step. A separate exact factor `1 + 2^-48` applies to five derivative bounds: carrier acceleration and angular speed, plus enclosing carrier speed, acceleration and angular speed. Exact zero derivatives remain zero. Per carrier and certificate group, the source reserves add two `recording_exact_mul` charges, the derivative reserves add five `recording_budget_reserve` checkpoints, and each nonzero derivative adds one `recording_exact_mul` charge. Chord, arc and total bounds are recomputed from the enlarged primitives and rounded outward. These are finite conservative publication reserves; they do not guarantee that every history is deliverable. The requested tolerances and the independent reader's minimum-bound and complete-inequality checks remain unchanged.

These details do not change physical equations, original fixture expectations, old destination behavior or the recorded playback scope. Independent destination tools and visual checks provide their own identified evidence. No live destination physics or general game-engine compatibility is claimed by producing a valid GLB.

## 7. Diagnostics and preserved obligations

[diagnostics-c073.json](diagnostics-c073.json) records the new reason values within the existing `OKL-E-RESOURCE` family. The proposal's five reasons are retained, with `execution_context_required` added for a missing, mismatched or unadmitted shared context. Host configuration type/value errors fail at the trusted API boundary. Existing source, numerical, destination and output-cap diagnostics retain their separate meanings.

All unrelated limits remain in force, including object/source/output counts, 32,768-bit operands, the 256-entry numerical cache, the independent reference's 64-step cursor reseed bound, JSON/GLB limits and local admission bounds. Raising execution operations does not raise another resource whose cap happens to use the same number. Agent cursor services remain outside this source/CLI increment.

The unchanged original 28-recording gate remains a separate obligation at its original settings. Higher-budget evidence does not retroactively pass it. Complete reach acceptance, C035's hold, C057, historical LFS migration, the Agent lifecycle and the rest of GOAL remain separately recorded. The C073 conformance portion is the 24 planned cases assigned to this increment; five Agent cases remain assigned to C074. Actual test inventories and results belong to the identified engineering evidence, including failed attempts and recoveries.

