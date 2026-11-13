# C226 aggregate result

## Outcome and method accounting

The single default core attempt is **failed**; **R02 remains blocked**. All seven planned commands finished, with no outer 3,600-second command timeout. Independent discovery and two outcome readers account for every selected method:

| Method outcome | Count |
| --- | ---: |
| Discovered | 4,662 |
| Passed | 4,649 |
| Failed or errored methods | 0 |
| Skipped, expected failures, failed imports or timed-out methods | 0 |
| Unrun after class-setup error | 13 |

One separate `setUpClass` error prevents all thirteen `TorqueArtifactReadTests` methods from starting. It is not thirteen failed methods or skipped tests. No method outcome is unknown; no subtest outcome event was reported. The raw unittest footer reports 4,649 tests in 1,390.574 seconds and `FAILED (errors=1)`. [Complete accounting summary](evidence/METHOD-OUTCOMES-SUMMARY.json).

## Exact execution and unchanged inputs

The tested revision is `3f17a523b5d5c435f71525a499d2f071ca6e4e96`, tree `324d7a23d67d0c23f5dfba968a63a5c12cb7bcff`. It used Linux x86-64 / CPython 3.12.14 and the exact seven-package native-reader lock. The separate documentation-preparation checkpoint `4df4558e68e717d230cf7a782671649bdb397cce` was not the execution source.

The unchanged default driver used its predeclared 3,600-second limit per command. Total driver duration was 1,523.210 seconds; the external launcher recorded 1,523.324 seconds and reaped its child with exit 1. Original source and isolated workspace input inventories remained equal, and the Git revision remained unchanged. The checked inventory contains 15,690 files. [Driver record](evidence/DRIVER-SUMMARY.json) and [process receipt](evidence/RUN-EXECUTION.json).

| Driver step | Observed result |
| --- | --- |
| Unit tests | Failed: 4,649 passed methods, thirteen unrun, one setup error |
| Source conformance | 43 passed cases / 694 assertions |
| Agent conformance | 10 passed cases |
| Construction conformance | 19 passed / 1 pending |
| Surface conformance | 1 passed / 11 pending |
| Impulse conformance | 8 passed / 4 pending |
| Documentation | Preservation/link check passed |

The last six commands returned success at their procedural scopes. Construction, surface and impulse still retain **sixteen external cases pending**. Successful command handling, including `--allow-pending`, does not complete those release gates.

## Concrete setup failure

The unchanged setup creates a fresh durable store and calls the frozen A08 export through `TorqueAgentService`. It failed with `OKL-E-RESOURCE`, reason `execution_deadline_exceeded`, at `recording_export_readback`. Request, effective and host limits remained **1,000,000 operations / 30,000 ms**. The response reports 430,069 consumed operations and approximately 30,000.901 ms elapsed. This internal product-request deadline is separate from the outer 3,600-second validation-command limit. [Exact response](evidence/SETUP-ERROR.json) and [original traceback](evidence/setup-error.txt).

The retained C191/C193 failure shares the diagnostic category, program/entry/policy identities and limits. Its implementation digest differs: current `sha256:920575745f5661c85c64cd6ff172812df82a9808fda3abb8cf55e16d66bb2d80`, historical `sha256:3e6ef2df6a7e8837050abb949075bff9b65f6a4aa4a9f1587850d7ddd59bce56`. The full fingerprints are therefore different. The underlying cause, performance equivalence and absence of regression are not established. [Exact comparison](evidence/HISTORICAL-COMPARISON.json).

## Readback prerequisites and retained limits

All three previously prepared CPU readback methods passed within this aggregate. The two positive probes passed; the changed-reference negative probe rejected its intended discrepancy. Independent review checked 6,180 numeric rows with 18,613 assertions and verified the three reader receipts: reaped processes, absent groups and closed handles. These are synthetic controls, not native receiving or rendering evidence. [Readback review](evidence/READBACK-OUTCOME-REVIEW.json).

C224's original 900-second timeout and partial accounting remain unchanged. Other Python versions, optional visual and dedicated force-agent roles, external conformance cases, pending Godot proof and release acceptance remain separate. No new receiving schedule was launched. C226 adds no product repair, tolerance change or retry. Follow the [next bounded diagnosis](NEXT-TASK.md) after the verified saved handoff.
