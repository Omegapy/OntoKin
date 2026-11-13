# C227 finite A08 CPU diagnostic plan

## Question and completion

Identify the work that reaches the frozen A08 export deadline in `TorqueArtifactReadTests.setUpClass`. A class setup creates the source and artifact needed by thirteen later test methods. This scope executes the original setup itself; it does not execute those methods or establish a complete regression result.

The selected evidence consists of one uninstrumented setup invocation and one separate profile of the same original setup. Complete the scope with a supported diagnosis or a precise remaining blocker, independent review, and the successor handoff. No repair or aggregate retry belongs to this plan.

## Required review before execution

The machine-readable authority is `RUN-PLAN.json`. The parent keeps the product checkout at the exact clean baseline and runs this external harness. Independent approval must identify the harness and plan SHA-256 hashes, that actual execution commit and tree, and the SHA-256 of the completed implementation-identity review. Save the complete harness, plan, approval and review durably before execution; publish the diagnostic documentation and evidence afterward. `APPROVAL-TEMPLATE.json` is explicitly unapproved and cannot start a workflow.

Admission verifies the whole protected `ontokin/` tree, the original test file and the complete frozen torque inputs against baseline `da007e1466c14812441bb8b18f8d2f8f01cbf1f6`. It verifies actual working-file bytes against Git blobs, rejects source changes and product bytecode, and recomputes the exact current package digest. The test, workflow and source-manifest hashes are separately fixed in the plan. The executed source commit and tree remain exactly the recorded baseline. Root coordinates the pause of other CPU-heavy work before starting.

## Exactly two ordered child slots

| Slot | Execution | Meaning |
| --- | --- | --- |
| 1 — baseline | Import the exact original test class and call `setUpClass()` once without profiling, tracing, patches or clock replacement. | Current uninstrumented setup outcome under the frozen product limits. |
| 2 — cProfile | Call that same original method once in a fresh process and store, with standard-library cProfile enabled only around the method. | An overhead-affected function/caller profile. This is not another baseline or a performance comparison. |

The original method loads its frozen source bundle, constructs the real durable service, calls `seed-create`, copies the frozen A08 request and calls `seed-export`. It uses the unchanged host policy and source request: **1,000,000 operations / 30,000 ms**. The default real product clock, callbacks, execution checks, transaction handling and artifact-byte checks remain active. No functions are monkeypatched; no prebuilt artifact is supplied.

Each child receives a fresh temporary directory outside the checkout. The supervisor consumes its slot before starting and writes process identity, command, cwd, limited environment overrides, wall time, exit status and process-group cleanup. The **90-second outer process ceiling** covers imports, the setup, evidence collection and cleanup. It does not change either product request's 30-second limit. On an outer timeout the supervisor terminates the process group, escalates to SIGKILL if necessary, preserves partial output and stops. It does not retry.

The second slot is allowed only after a fully observed first result: either setup succeeds or the original `seed-export` response reports the expected real-clock deadline with exact program identity and limits. Unknown response, another failure, source change, dirty worktree, incomplete store evidence, integrity failure, failed original cleanup or process residue stops the plan before slot two.

## Evidence and integrity

The harness preserves the raw assertion dictionary and traceback immediately after the setup finishes. It records setup wall and process-CPU times separately, actual Python/platform identity, process identifiers, CPU count and affinity, load averages and available cgroup `cpu.max` / `cpu.stat` observations before and after the setup. These host records describe the observed environment; they are not proof of exclusive CPU access or an explanation of earlier runs.

After the method's service context closes, the harness copies the complete seed store, including any SQLite WAL/SHM files, into `store-raw`. It hashes these original retained bytes before deriving conclusions. Database inspection uses a second private copy with read-only SQL and `query_only`; it records `PRAGMA integrity_check`, accepted projects, source identities, request payloads/responses, run descriptors and artifact byte hashes. It then verifies the original retained bytes remain unchanged. Raw store evidence remains available even if derived inspection fails. The original class cleanup runs after capture.

The child records whether `ontokin.semantic_export` was actually imported. A negative result concerns the observed process only; static identity reconciliation supplies the broader code comparison. Protected source and fixture bytes and Git identity are checked before/after each child and between slots.

The profiled slot preserves the binary `.prof`, all function/caller costs as JSON, and bounded text rankings by cumulative and self time. The supervisor preserves a file-integrity manifest and a two-slot outcome summary. A product failure remains a failure even if the diagnostic supervisor successfully accounts for it.

## Interpretation limits and stop

`recording_export_readback` is a broad ledger stage. It includes scene construction, sampling/certification, GLB encoding and byte validation; that label alone cannot identify the hotspot.

cProfile adds call-accounting overhead and can reach the unchanged real-clock deadline earlier, after less work, or in another stage. Its shares and timings describe the profiled prefix only. Do not report them as baseline percentages, claim historical performance equivalence, infer an exact speedup, or claim that the two observations prove a regression. Any remaining causal uncertainty is a valid explicit blocker for this bounded diagnosis.

After both slots finish, or after any stop condition, preserve the evidence and close this scope. No additional setup attempt, extended budget, repair, full aggregate, native application/version probe, receiving operation or later feature is authorized by this plan.

## Parent command

Use the reviewed external harness path, actual clean checkout, a new evidence destination, and the independent approval and identity report. All paths below are placeholders to be replaced by observed absolute paths:

```bash
python3 -I -B /absolute/reviewed/diagnose_a08.py \
  --repository /absolute/OntoKin \
  --output /absolute/new-c227-diagnostic-output \
  --plan /absolute/reviewed/RUN-PLAN.json \
  --approval /absolute/independent-APPROVAL.json \
  --identity-review /absolute/BYTE-IDENTITY-RECONCILIATION.json
```

Appending `--preflight-only` performs admission with zero product starts and no output creation. Do not reuse an existing consumed output directory or run either private child command manually.
