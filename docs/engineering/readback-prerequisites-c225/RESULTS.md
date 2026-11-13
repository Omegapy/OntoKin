# C225 prerequisite result

## Completed scope

One legitimate prerequisite restoration and one focused CPU cohort passed on Linux x86-64 / CPython 3.12.14. The actual tested commit is `c76a7622dadb0bdd7cb514840ee1747aabe8eae7`, tree `445f66ac776477051121d80665b9109f94aa8207`. Recorded Node is `v24.22.1`. Documentation publication occurs later and is identified separately.

The original C199 host inventory is retained at `docs/engineering/static-tray-qualification-c199/evidence/preflight/HOST-RUNTIME-INVENTORY.json`. The C195 recorded-evidence archive contains the exact 24 dependency files identified by C199's immutable `EXTERNAL-INPUTS.json`. Before restoration, both required historical destinations were absent. The helper verified all source hashes, each dependency hash/size, ten current runtime bindings/modes and ten aliases. It restored the exact files without replacement, then checked the installed bytes again. The host inventory remains historical evidence; it is not a new whole-host attestation.

## Executed checks

| Check | Observed result |
| --- | --- |
| Exact retained dependency files | 24 of 24 match |
| Required current runtime files | 10 of 10 match; aliases agree |
| Unchanged focused CPU methods | 3 passed; 0 failures, errors or skips |
| Cohort duration | 1.314 seconds |
| Source state | Clean before/after; same commit/tree and 29 executable-input hashes |
| Actual checker process receipts | 3, all reaped with closed handles and absent process groups |
| Independent numerical audit | 6,180 rows reconciled |
| Aggregate runs in C225 | 0 |

The Q01 and Q03 positive probes passed. The negative test preserved the same Q01 geometry and altered its reference translation by 0.001; the checker rejected the intended single comparison against the unchanged 0.000005 tolerance. Its exit code 1 is the expected successful negative-test result. The five recorded subprocess events describe attempted launches: Node version, ldd and three readers. Actual PID/process receipts independently establish all three reader starts. Successful setup and retained outputs establish the two setup commands.

The [outcome](evidence/OUTCOME.json), [raw unittest log](evidence/focused-cohort-01.stderr.log), [method summary](evidence/focused-cohort-01/SUMMARY.json), [commands](evidence/EXECUTION-COMMANDS.json) and [independent review](REVIEW.md) support these claims. Complete probes, synthetic artifacts and reference audits remain in the confirmed saved recovery and successor handoff, bound by [the raw-evidence manifest](evidence/RAW-EVIDENCE-BINDINGS.json) and [location receipt](evidence/RAW-EVIDENCE-LOCATION.json).

## Original review finding

Before installation, independent review found that a rejected report destination could still receive a failure report. The helper was corrected before use; six report-destination refusal controls passed. The original helper/finding and corrected helper remain preserved. Approval binds corrected helper SHA-256 `eed7a35d7e9faa82a6bef42e8c8ee05ee0f189195af2f60b07efee27022b497b`; the observational runner is `fcb2963d828f5ea446047916b48c52288eb00628998ead4b14884d05554d464b`. No unsafe invocation or unknown installation occurred.

## Remaining obligations

R02 remains blocked until one fresh declared aggregate completes with accurate whole-inventory accounting. C224 retains 3,451 passed, one interrupted and 1,210 unrun methods; these three new focused results do not rewrite that earlier attempt or form a stitched aggregate pass. All nine recommendations and 41 acceptance criteria remain. R00/R01 retain their completed scopes; R03-R08 and remaining R07 Godot work remain pending.

No native application, product-source program, exporter, renderer or closed native/trial schedule ran. Synthetic GLBs are CPU test inputs, not a native receiving proof. Historical Blender normal fidelity, Godot lineage/rendering limits, external conformance roles, optional visual/force plans and other Python runtimes retain their recorded limitations. Follow [NEXT-TASK.md](NEXT-TASK.md).
