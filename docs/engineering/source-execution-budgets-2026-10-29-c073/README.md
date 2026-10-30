# C073: configurable source and CLI execution budgets

October 29, 2026, America/Denver; executions dated October 30 UTC. This implements the source/CLI increment selected in [C072](../language-execution-budgets-2026-10-29-c072/NEXT-TASK.md), under [OK-LANG-007/0.1.0-experimental.1](../../language-design/execution-budgets-v0.1/ADOPTION-C073.md).

**Validated source candidate:** `e072906f664cd605bc3052b786961b9a292d4d9b`  
**Source tree:** `7bef230867bb876f3a26a85b01c872d5299a05d1`  
**Complete core/force-agent status and exact totals:** `Passed: 3,129 tests; all 11 selected local steps; zero failures, errors or skips`  
**Immutable validation ZIP:** `OntoKin_C073_Validation_Evidence_2026-10-29.zip`  
**ZIP SHA-256:** `476b84584161e6b4a4779254fe8a0c1ae3d04dcd5f52ccfbbfc3e694c6903ec9`

The [archive descriptor](evidence-archive.json), [complete core record](results/core-summary.json), [acceptance record](results/acceptance-summary.json), [destination record](results/destination-summary.json), and [review index](reviews.json) identify the evidence. The complete portable handoff will also include this archive. Final delivery links will be recorded in [PR #71](https://github.com/Omegapy/OntoKin/pull/71). Development integration remains separate from complete feature release; the later integration record identifies the actual merge and resulting-main checks.

## Implemented contract

Explicit source `0.7` / `planar-reach-budget-0.1` may request `max_operations` and exact whole-millisecond `max_elapsed` in an entry-header `execution` block. Omitted fields retain 100,000 operations and 30,000 ms. A trusted, immutable `HostPolicy` supplies independent ceilings; explicit caller caps can only reduce the source request. Oversized requests fail without silent clamping or automatic retry. Imported modules cannot declare or replenish a budget.

Bounded grammar-aware admission starts the clock before scanning, then promotes the same ledger once. Header work, linking, construction, numerical operations, evaluation, recording, GLB encoding, independent supplied-byte readback and result checks share that ledger and original deadline. Cancellation retains the caller's exception identity. Computation time is separate from modeled duration and playback time. Other source, object, value, numerical, cache and output limits remain in force.

The route requires explicit `ontokin.glb/0.7`; Agent/0.7 is unavailable. Discovery describes the new destination under `execution_budget_interface.export_targets`, preserving the six original top-level descriptors. The [adoption decision](../../language-design/execution-budgets-v0.1/ADOPTION-C073.md) and [debit map](DEBIT-MAP.md) specify the admission bounds, diagnostics, inherited physical semantics and finite 0.7-only numerical corrections. Original C072 proposal, grammar and conformance-plan bytes remain unchanged.

## Trusted host usage

An authorized operator can use the [example launcher](../../../tools/ontokin_budget_host.py), whose Python configuration fixes ceilings of 400,000 operations and 80,000 ms:

```bash
python3 tools/ontokin_budget_host.py export \
  examples/execution-budgets/larger-workload.ok \
  --target ontokin.glb/0.7 --fps 60 --end 3 --no-helpers \
  --output /tmp/ontokin-budget-workshop/workshop.glb
```

The ordinary `python3 -m ontokin` retains default ceilings. No CLI flag grants a larger ceiling; `--max-operations` and `--max-elapsed-ms` supply reductions only. A trusted embedding can call `execute_budgeted_export(bundle, policy=HostPolicy(400000, 80000), options=...)` with an immutable `ProgramBundle`; the [example guide](../../../examples/execution-budgets/README.md) explains the API and receipts.

Successful computation returns verified bytes and an external receipt identifying source, implementation, policy, limits, consumed work and artifact hash. CLI persistence follows computation. Handled write failures restore previous outputs or retain recovery backups; a process crash between two file replacements still requires checking the artifact hash.

## Frozen acceptance and destination evidence

The [new frozen workshop](../../../examples/execution-budgets/larger-workload.ok), [independent expectations](../../../examples/execution-budgets/larger-workload.expected.json) and [freeze record](../../../examples/execution-budgets/acceptance-freeze.json) precede execution. Six two-material lofts move as independent 2 kg spherical bodies under a two-second center force and a center impulse at one second. Dimensions, material regions and analytic `F/m` and `J/m` motion were derived independently.

On the exact candidate, the default control selects 100,000 operations/30,000 ms through explicit reductions and fails on attempted operation **100,001**, with no artifact. The authorized 400,000-operation/80,000-ms attempt succeeds after **193,424 operations**, including independent supplied-byte validation. Its GLB is **1,737,552 bytes**, SHA-256 `c6a1e94dab7c1536aa8749e0e34132effc9f8fc27650bbafa70ed6567a91f8b1`.

The independent checker consumes that artifact: **six lofts**, each with 96 triangles and two material regions; **78 native and 78 browser pose comparisons**; **zero Khronos errors or warnings**. Six fresh front/side captures at 0, 1.5 and 3 seconds passed actual image inspection and recorded fit checks. They establish the named artifact and views, not universal delivery or live destination physics. Native and browser observations use the same pinned Three.js library; the analytic triangle/material oracle runs in the native checker.

## Verification and review

Verification used Linux x86-64, Python **3.12.14**, Node **22.23.4**, Three.js **0.180.0**, Khronos glTF Validator **2.0.0-dev.3.10**, Playwright **1.56.1**, esbuild **0.25.10** and Chromium **141.0.7390.37**. The [local driver](../../../tools/check_local.py), [acceptance runner](../../../tools/run_budget_acceptance.py) and [destination checker](../../../tools/verify_budget_glb.mjs) have separate recorded roles. The direct local wrapper used the unchanged driver's command plan and execution rules on one frozen checkout. Only one Python version was executed.

The [case results](conformance-results.json) map **24 C073 cases** to **64 new methods**—26 admission, 20 runtime, 18 export—and the external evidence. Five Agent lifecycle cases remain deferred. The runtime-candidate preservation audit found **3,817 protected original files** byte- and mode-identical, with zero forbidden drift; 65 resource definitions and 934 existing defaults were unchanged. That audit identifies the runtime candidate, before the later publication/handoff edits. Independent reviews cover admission/runtime, export/numerical behavior, the discovery repair, frozen physics/geometry and the external checker. Authored contributions are excluded from each contributor's independent approval.

Passing the selected local roles does not complete their separate release gates: **16 inherited external cases remain pending—construction 1, surface 11, impulse 4**. The retained reports identify each obligation; this source/CLI increment closes none by inference.

Failures remain retained. Candidate `a23b0b2` completed 3,128 unit tests with **nine failures and one error**; its ten other selected steps passed. Eight failures and the error exposed the changed legacy budget layout. Restoring that class exactly and selecting a separate 0.7 adapter repaired the cause without changing the native guard. The remaining failure exposed the expanded legacy discovery map; moving the new descriptor into its explicit interface repaired that contract. Earlier callback, rollback, numerical and screenshot-carryforward failures also remain recorded; fresh evidence replaces no failed record.

An exec-server transport interruption then stopped the first e072 full run after 2,831 `ok` lines; its incomplete summary and log remain preserved. The replacement full run does not bracket the earlier completed acceptance/native/browser/visual work. Explicit source inventories and hashes establish eligibility to retain that evidence; they do not replace the required completed regression.

## Preserved obligations and next step

Historical original28 remains **failed at 24/28**, with P11/P16/P23/L03 unresolved. M1 remains rejected; comparison accounting/passive authority remains open. C035 remains held, including adverse timing. C068 remains unadopted, C069's existing-list receipt rejected, and C070's isolated angular-cache proposal unselected. C057, complete reach acceptance, historical LFS migration and the full [GOAL](../../../GOAL.md) remain open. This larger-budget cohort cannot pass the original fixed-budget gate retroactively.

C074 is the separately versioned Agent lifecycle: candidate authorization and rollback, saved-program reauthorization, evaluate/export/retrieve, cancellation, request isolation and idempotent retries. After that bounded integration, select the next representative modeling, animation or simulation capability from GOAL; another optimization investigation is not a prerequisite.

## Transport recovery binding

The [terminal interruption record](results/transport-interruption.json) preserves the incomplete first e072 full run. The [recovery eligibility record](results/recovery-eligibility.json) proves the same clean source, tree and inventory across acceptance, interruption reconciliation and the later complete regression. The recovery run begins after acceptance; it does not bracket that earlier execution. The original acceptance binding remains preserved with its original timing context.
