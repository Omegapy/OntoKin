# C227 independent outcome review

## Verdict

**The completed two-slot diagnostic is correctly accounted for and independently verified.** The original uninstrumented setup succeeded under the unchanged 1,000,000-operation / 30,000-ms limits. Its export published the exact historical A08 GLB. The separately profiled setup reached the product deadline after substantial work in the frame-sampling path and published neither a run nor an artifact.

These results complete the selected diagnosis scope. They do not pass R02, run the thirteen artifact-read methods, repair the product, or explain why the earlier C226 aggregate timed out. The source fingerprint difference is resolved: only the added, unused `semantic_export.py` changes package identity; all inherited implementation and frozen setup bytes remain equal.

The next useful bounded task is **one separately selected fresh immutable default R02 aggregate**, with its original product limits and complete inventory accounting. Another setup experiment or a speculative guard optimization is not justified by the present evidence.

## Independent checks

`audit_outcome.py` performed **4,779 assertions** with zero product imports or executions. It checked all 22 sealed evidence payloads, all 558 protected source/input bindings, the approval and one-use process records, both raw SQLite stores through separate read-only copies, and all 1,771 function/caller records against the original binary cProfile data.

The audit rechecked exact request payloads and source/module/asset bytes, transaction outcomes, accepted source identity, artifact hashes, closed sessions, process-group absence and original raw-file preservation. `OUTCOME-REVIEW.json` contains every assertion and measured result. `AUDIT.stdout.log` and `AUDIT.stderr.log` retain the actual audit outcome.

No extra product invocation, native process, repair, aggregate or parameter change occurred during review.

## Three results with different meanings

| Observation | Export outcome | Export elapsed | Export operations | Meaning |
| --- | --- | ---: | ---: | --- |
| Retained C226 complete aggregate | Failed at original deadline | 30,000.900981 ms | 430,069 | Historical aggregate remains failed; thirteen methods did not run. |
| C227 uninstrumented setup | Succeeded | 24,590.682498 ms | 452,627 | One current standalone original setup passed; thirteen test methods were not selected. |
| C227 cProfile setup | Failed at original deadline | 30,002.297467 ms | 140,127 | Instrumented execution stopped much earlier in the workload; not a comparable baseline timing. |

All three bind the same current implementation digest `sha256:920575745f5661c85c64cd6ff172812df82a9808fda3abb8cf55e16d66bb2d80`, authoritative program `sha256:b54065f44f34220abef40fa4615a12deb6ad11b7f0e613e4903b35bd7a68b8d7`, and original source/host limits. C227 executed source `da007e1466c14812441bb8b18f8d2f8f01cbf1f6`, tree `32ac0f19681ea90d8d2c55cc3e5e1daaeca4ae54`. Subsequent documentation and integration commits are separate identities.

The full baseline setup took 25.215785456 seconds wall time and 25.173158091 seconds process CPU time. The profiled setup took 31.365762256 seconds wall time and 31.308744107 seconds process CPU time. These setup measurements also contain source creation and class setup overhead; they must not be substituted for the product export receipts in the table.

The supervisor correctly accepted baseline child exit 0 and profiled child exit 1 as their distinct expected outcomes. Its exit 0 means the finite diagnostic was fully accounted for, not that both product requests succeeded. Both process groups were absent, no outer 90-second timeout occurred, and no termination signal was needed. The independent audit subsequently confirmed both groups remained absent.

## Baseline artifact and durable state

The baseline store contains one accepted original source, exactly two requests (`seed-create` and `seed-export`), one completed run, and one artifact. Both requests have succeeded receipts. The artifact is:

- Length: **2,447,148 bytes**.
- SHA-256: `6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`.
- Artifact ID: `artifact:6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`.
- Source revision: the unchanged authoritative A08 program above.

Independent hashing of the actual SQLite BLOB agrees with the artifact ID, stored digest, successful response and historical original-source artifact digest recorded in C157–C160. The GLB header is valid for version 2 and its declared byte length equals the actual payload.

The product's retained exporter report records successful source-aware numerical validation: 188 sample points, 1,504 node-pose comparisons and 1,496 interval certificates. This audit verified the report's exact binding to the original artifact and response; it did not replay the numerical validator or any external destination.

The profiled store retains the same accepted source and the successful create request. Its failed export response equals the raw assertion dictionary. There are **zero runs and zero artifacts**, consistent with the required failure transaction. Both stores pass an independent SQLite integrity check; all sessions are closed, no requests remain running, and the copied raw database bytes remain unchanged.

## What the profile localizes

The complete binary profile and its JSON function/caller table agree exactly. The profiled attempt entered scene construction and `torque_recording._sample_recording_nodes`. Its instrumented prefix includes:

| Function | Calls | Cumulative seconds |
| --- | ---: | ---: |
| `SharedExecutionBudget.tick` | 147,665 | 28.863165497 |
| `admit_callback` | 295,320 | 27.732989112 |
| `_sample_recording_nodes` | 1 | 26.083513401 |
| `TorqueSimulator.recording_frames` | 155 | 25.509925190 |
| Simulator `guard` | 139,334 | 24.334767339 |
| `_source_watches_current` | 140,944 | 4.027827514 |
| Durable-service `_poll` | 147,665 | 0.242738369 |

These cumulative intervals are nested and overlap. **Do not add them or report them as baseline percentages.** Generated authority predicates, dictionary identity lookups and source-watch scans contribute substantial work inside the guarded sampling path. The profile has no calls to GLB `_encode`, `read_glb`, `validate_export`, torque interval-certificate construction, or `TorqueValidationScope.__enter__`. The profiled timeout therefore preceded encoding and independent supplied-byte validation.

This localizes the costly instrumented prefix to repeated frame/kinematic sampling with its required authority and callback checks, before encoding or complete byte validation. It does not identify the exact final Python instruction. It does not establish the precise stopping subroutine in C226: that earlier run reached 430,069 operations, while this instrumented run reached only 140,127. cProfile changes the timing and observed prefix. No exact baseline cost share, proposed speedup or causal regression is established.

## Historical studies and rejected shortcuts

The current observations agree with the direction of earlier evidence while retaining its limits. C157 reported variable original-deadline outcomes and separated Agent, direct-export and configured-budget work. C158 identified expensive source checks but demonstrated that removing repeated bindings or substituting a native scan can change callback-visible behavior. C159 rejected extra lookups, helper reuse and altered callable lifetime because they changed the escaping exception or charged work. C160 rejected descriptor-membership/observer-eligibility substitutions for related observable differences.

Those candidates remain closed. A profile showing time in the same guards is not new evidence that those substitutions are safe. None of the old 80-second controls, modified backends, native probes, rendering steps or callback experiments ran in C227.

The inherited C157–C160 records were reviewed as historical observations. Their cited original commits are not all available in the local restored object database, so this review does not add an unverified claim of exact source equality to those early executions. The direct C193/C226 byte equality is separately established by `../BYTE-IDENTITY-RECONCILIATION.json`.

## What remains unknown

One current standalone success cannot reproduce the preceding 4,000-plus-method process state from an aggregate. It cannot separate physical-host differences, CPU scheduling, warm interpreter state, memory/allocator effects or other execution-context variability. Current wall and CPU times are close, but that is only this run's observation. The harness could not read `/sys/fs/cgroup/cpu.max` or `cpu.stat`; CPU quota and throttling are therefore unknown. No timing guarantee or absence of historical regression follows.

The supported finding is narrower: unchanged original inputs and inherited implementation can succeed on this observed current host, and the instrumented prefix spends substantial time enforcing source/context authority during sampling. The cause of C226's particular 30-second miss remains unresolved. Historical failures remain failed; R02 remains blocked.

## Exact next bounded action

After confirming the C227 successor ZIP is saved, reconcile current main, branches, ownership and any newer work. Restore the exact retained validation dependencies and readback prerequisites. Select **one immutable complete default R02 driver attempt** on the actual current published revision, using a predeclared 3,600-second per-command ceiling as in C226 and unchanged product limits, fixtures, tolerances and expectations.

Record the complete discovered inventory before execution and account for every method, class-setup failure and later driver step afterward. Let the original setup run in its ordinary suite order. Do not replace it with the C227 artifact, omit the thirteen methods, stitch standalone success into the aggregate, increase its 30-second product allowance, or retry automatically.

If that attempt passes its actual default scope, update R02 only to the acceptance the complete result supports. Optional visual/force-Agent roles, other interpreters and sixteen external cases remain distinct obligations. If it fails, preserve the exact result and stop at a concrete blocker. No repair, native receiving step or later feature belongs to that aggregate thread.

