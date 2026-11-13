# C225 independent execution outcome review

## Decision

**Accept the bounded prerequisite restoration and focused CPU cohort result.** All three unchanged ReadbackCPUControls methods passed once, with zero failures, errors or skips. This review did not repeat the tests or restore anything. Full R02 aggregate acceptance remains pending.

Execution used `c76a7622dadb0bdd7cb514840ee1747aabe8eae7`, tree `445f66ac776477051121d80665b9109f94aa8207`, on recorded Linux x86-64 / CPython 3.12.14. The before/after identity, clean status and 29 executable-input hashes agree. The reviewer independently compared all 29 hashes with the actual tested Git objects and current unchanged executable inputs. Later documentation work is separate from that tested revision.

## Prerequisite result

The actual restoration receipt records two non-replacing installations: the exact 24 dependency files and the unchanged original HOST document. Both locations were absent initially and complete afterward; no unknown operation is recorded. Fresh independent inspection confirms the complete installed file and directory sets, no symlinks or extra files, every expected dependency hash/size, exact historical HOST bytes, and all ten current runtime file bindings/modes and aliases.

The HOST document remains historical evidence. It has not become a current full-host attestation. Only the required runtime closure and loader-configuration paths are freshly verified. The helper and runner hashes equal the versions approved before execution.

## Actual method and process evidence

The saved inventory, raw unittest log and machine-readable summary independently agree on the same three method IDs. The suite ran three tests in 1.314 seconds and finished OK. Expected-failure and unexpected-success lists are also empty.

| Case | Checker exit | Probe result | Method outcome | Numerical rows |
| --- | --- | --- | --- | --- |
| Q01 positive | 0 | passed | passed | 2,060 passing |
| Q03 positive | 0 | passed | passed | 2,060 passing |
| Q01 changed reference | 1 | rejected as expected | passed | 2,059 passing; one intended rejection |

The five subprocess.Popen audit events are attempted-launch observations. Two cover Node `--version` and `/usr/bin/ldd`; successful unchanged class setup and the resulting manifest contain their completed outputs. They have no separate PID receipts.

Three separate checker process receipts establish actual observed Node checker starts, with PIDs/process groups 37, 45 and 53. Their argv/cwd exactly match the corresponding audit events and generated job commands. All three receipts record reaping, absent process groups, closed handles and successful cleanup. Raw stdout/stderr sizes equal both observed and retained log-byte counts. The negative check exits 1 with the expected rejected-backend result; this is the intended successful negative test.

## Artifact and rejection checks

The reviewer independently recalculated the 6,180 recorded scalar differences and threshold outcomes. Every report is bound to its exact synthetic GLB, reference audit and supplemental-manifest hashes. Khronos reports zero errors, warnings, infos or hints for all three artifacts. Three.js observes 14 nodes, 12 meshes and zero animations in each case.

The negative control uses byte-identical Q01 GLB geometry. Its reference audit differs only in explanatory scope and the designated left/base matrix translation, from -0.3 to -0.299. The checker reports the corresponding 0.001 difference against the unchanged 0.000005 threshold. There is exactly one failed numerical row and one finding, both at that intended field. No fixture expectation or tolerance was weakened.

## Scope limits

The unused native-schedule path remains absent. The exact commands and reviewed unchanged cohort create synthetic GLBs and launch only the CPU readers; there is no observed Blender/native/product-source/export/render start or closed-schedule replay. A generator string embedded in a synthetic GLB is not evidence of a native export in this run.

No aggregate run occurred. C224's original timeout, three previously unrun methods, historical receiving limits and all other pending recommendation criteria retain their meaning. This result removes the immediate prerequisite obstruction for the next separately bounded aggregate attempt; it does not convert historical attempts into passes.

## Evidence

`OUTCOME-REVIEW.json` contains the independent machine-readable decision, exact post-run input bindings and case results. `audit_outcome.py` reproduces this read-only audit without importing project modules or starting tests/Node/native tools. Its stdout/stderr are retained.

`REVIEWED-WORKER-BINDINGS.json` binds all 53 frozen worker files (4,747,801 bytes), including original commands, raw logs, process receipts, probes, artifacts and the rejected helper/control history. Every binding was rechecked; no extra worker file was present apart from its manifest. Root owns subsequent documentation publication and final package closure.
