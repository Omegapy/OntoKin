# C227 — A08 CPU diagnostic result

The unchanged original torque setup **succeeded once in isolation**. A separate cProfile invocation reached the original 30-second export deadline. The profile identifies substantial repeated sampling, execution-budget and authority-check work, but does not establish why the earlier C226 aggregate timed out. **R02 remains blocked.**

This completes the predeclared two-invocation measurement schedule. The remaining blocker is causal attribution: the historical aggregate failure was not reproduced by the current uninstrumented setup, and cProfile changes the cost and amount of work completed before the deadline. No repair or aggregate retry was performed.

## Exact execution and observed outcomes

Both children executed clean source `da007e1466c14812441bb8b18f8d2f8f01cbf1f6`, tree `32ac0f19681ea90d8d2c55cc3e5e1daaeca4ae54`, on Linux x86-64 / CPython 3.12.14. The implementation digest was `sha256:920575745f5661c85c64cd6ff172812df82a9808fda3abb8cf55e16d66bb2d80`. Product source, the original setup test, frozen inputs and Git identity remained unchanged. The original real clock and **1,000,000-operation / 30,000-ms** request and host limits remained active.

| Observation | Original setup | Actual `seed-export` response | Export operations | Process exit |
| --- | --- | --- | ---: | ---: |
| Uninstrumented baseline | Succeeded; 25.215785 s wall, 25.173158 s CPU | Succeeded in 24,590.682498 ms | 452,627 | 0 |
| Separate cProfile invocation | Original assertion; 31.365762 s wall, 31.308744 s CPU | Failed in 30,002.297467 ms; `execution_deadline_exceeded` | 140,127 | 1, expected for this observed failure |

The setup times include both `seed-create` and `seed-export`. The product deadline applies separately to each request, so the profiled setup's total duration above 30 seconds does not indicate that the export deadline was raised. The recorded diagnostic first detected the profiled export limit at **30,000.041033 ms**; its final response includes the small subsequent failure-reporting interval. Both requests retain their actual recorded outcomes.

The baseline produced one **2,447,148-byte** artifact with SHA-256 `6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`. Its stored digest and artifact identifier both match the actual database bytes. The accepted program was `sha256:b54065f44f34220abef40fa4615a12deb6ad11b7f0e613e4903b35bd7a68b8d7`; the baseline retained one run and one artifact.

The profiled failure retained **zero runs and zero artifacts**, while preserving that same accepted program. These are observed transaction results from the real durable service. They do not replace the thirteen artifact-read test methods that C226 could not start.

Sources: the [baseline receipt](evidence/run/1-baseline/SETUP-RESULT.json), [profiled receipt](evidence/run/2-cprofile/SETUP-RESULT.json), [baseline raw database](evidence/run/1-baseline/store-raw/torque-program-agent.sqlite3), and [profiled raw database](evidence/run/2-cprofile/store-raw/torque-program-agent.sqlite3). The [measured summary](evidence/MEASURED-SUMMARY.json) extracts the actual SQLite request rows and confirms they match the saved setup receipts. It preserves full-precision values and source hashes.

## What the profile measures

The profile covers the second setup, including its create request and the export prefix that ran before the deadline. It records **115,700,600 function calls**, including **115,612,660 primitive calls**. Function-call counts are profiler events; they are distinct from the product's operation charges.

| Profiled function | Calls | Self time, s | Cumulative time, s |
| --- | ---: | ---: | ---: |
| `execution_budget.tick` | 147,665 | 0.473487 | 28.863165 |
| `execution_budget.admit_callback` | 295,320 | 0.596665 | 27.732989 |
| `scene.build_scene` | 1 | 0.000010 | 27.294559 |
| `torque_recording._sample_recording_nodes` | 1 | 0.006226 | 26.083513 |
| `torque_runtime.recording_frames` | 155 | 0.009131 | 25.509925 |
| `torque_runtime.guard` at line 470 | 139,334 | 0.364333 | 24.334767 |
| `torque_canonical_spin._admit_simulator_runtime` | 140,468 | 0.244210 | 11.081692 |
| `torque_runtime._context_after_dispatch` | 140,456 | 0.565513 | 5.187746 |
| `torque_runtime._source_watches_current` | 140,944 | 0.674374 | 4.027828 |

**These cumulative values overlap.** A caller includes time spent inside its callees; the rows must not be added. Self time excludes callees but still comes from the instrumented process. The [binary profile](evidence/run/2-cprofile/setup.prof), [complete function/caller table](evidence/run/2-cprofile/profile-functions.json), and [bounded rankings](evidence/run/2-cprofile/profile-top.txt) preserve these measurements.

The repeated guard and admission calls establish concrete locations for subsequent investigation. The observed paths also clarify the broad `recording_export_readback` ledger label: it includes building and sampling the scene before final artifact encoding and readback. The label alone does not identify a decoder bottleneck.

cProfile adds substantial call-accounting work to this call-heavy path. The profiled run performed fewer export operations and ended with a different outcome from the baseline. Its times cannot be used as uninstrumented baseline shares, a speedup estimate, or evidence of historical performance equivalence. Removing a guard or changing a callback based on this profile would require its own reviewed design and evidence that all authority, budget, cancellation, transaction and byte-integrity behavior is preserved.

## Integrity, cleanup and environment

The two child processes returned within the separate 90-second process ceiling: **25.740132 seconds** for the baseline and **31.899990 seconds** for the profile. Neither needed a termination signal; both process groups were observed absent. Each original class cleanup completed.

The raw database bytes were copied before inspection. Read-only inspection of separate copies reported `PRAGMA integrity_check = ok` for both stores. The preserved originals remained unchanged, and all recorded service sessions were closed. The baseline database is 2,682,880 bytes with SHA-256 `f53145f8e5673f165332397e362e66e9132268227087ce5c18a7cb3293abb383`; the profiled database is 131,072 bytes with SHA-256 `f405191e22fe8ecd398b0030c39b80c34db6768c40c25772927b381ad3c08a2b`.

Neither process imported `ontokin.semantic_export`. That observation is consistent with the independent static implementation-identity reconciliation. It concerns these two actual processes and does not substitute for the static inventory comparison.

Both observations reported nine logical CPUs and affinity to CPUs 0–8. Process CPU time was close to wall time, which is consistent with CPU-intensive work during these measured calls. Endpoint load averages and CPU affinity do not prove exclusive CPU access. The inspected cgroup `cpu.max` and `cpu.stat` files were unavailable, so CPU quota and throttling are unknown. These current observations do not establish the host conditions during C226.

Sources: the [baseline process receipt](evidence/run/1-baseline/PROCESS.json), [profile process receipt](evidence/run/2-cprofile/PROCESS.json), setup-receipt CPU contexts, [protected input inventory](evidence/run/INPUTS.json), and [original evidence manifest](evidence/run/EVIDENCE-SHA256.json). All **22** entries in the original evidence manifest were rechecked while deriving the measured summary. This derivation executed no product workflow and left the stored evidence unchanged.

## Remaining work and stopping point

Exactly **two child/setup invocations** and **four original service requests** were observed. **Zero test methods, full aggregates, native starts or repairs** occurred. The frozen plan is consumed and must not be replayed.

The C226 aggregate failure, its thirteen unrun methods and blocked R02 remain unchanged. One successful isolated setup does not establish a complete class pass, a reliable deadline margin, or a complete aggregate pass. The next separately bounded decision is to review one fresh default R02 aggregate attempt on immutable inputs, with a new recorded plan and schedule, unchanged product limits, complete outcome accounting and retained host context. Its execution and acceptance remain unperformed here. The isolated pass supplies no demonstrated repair requirement and does not establish why the historical aggregate failed. Preserve the current findings and hand off without another attempt.

The [independent outcome review](REVIEW.md) verifies the complete two-slot result. [Scope #186](https://github.com/Omegapy/OntoKin/issues/186) records exact publication and final handoff delivery separately.
