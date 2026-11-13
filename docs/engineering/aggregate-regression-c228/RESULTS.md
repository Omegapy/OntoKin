# C228 aggregate result

**The aggregate failed; R02 remains blocked.** One default seven-step attempt ran on published commit `fc500331ce789eb6f9c1210ea4f3b394d45e507c`, tree `8eba004b6b08a00449663d868674c9fc8521469f`, using Linux x86-64 / CPython 3.12.14. The unchanged driver finished in 1,315.673 seconds. Its 3,600-second per-command ceiling was not reached, and original product limits were preserved. [Independent result](evidence/OUTCOME-REVIEW.json).

## Complete method accounting

| Outcome | Count |
|---|---:|
| Discovered and executed methods | 4,662 |
| Passed methods | 4,661 |
| Failed methods | 1 |
| Failed subtests within that method | 2 |
| Method errors, skips, timeouts or unrun methods | 0 |
| Setup/module fixture errors or import placeholders | 0 |

The terminal `FAILED (failures=2)` counts the two failed subtests. Both belong to one method; the method inventory therefore contains one failed method. Independent raw-log reconciliation agrees with the complete accounting. Passing subtests are not individually enumerated by ordinary unittest output. [Method summary](evidence/METHOD-OUTCOMES-SUMMARY.json).

## Observed failure

`LedgerControls.test_corrupt_replaced_aliased_or_missing_files_poison_live_capability` failed for `mutation='replace'` on:

- `C201-Q01-A01-A04-v0.1.0.invocation.json`
- `C201-Q01-A01-A04-v0.1.0.ledger.jsonl`

The unchanged test deletes each authority file and writes its original bytes back to the same path, then expects reservation through the existing capability to raise `LedgerError`. At line 503, both subtests reported **`LedgerError not raised`**. The exact assertions and tracebacks are preserved in [the failure record](evidence/LEDGER-FAILURE.json) and [raw trace](evidence/LEDGER-FAILURE-TRACE.txt). The tested source is [identified here](https://github.com/Omegapy/OntoKin/blob/fc500331ce789eb6f9c1210ea4f3b394d45e507c/tests/test_static_tray_admission_c201_ledger.py).

This establishes the observed rejection failure. Its underlying cause remains unproven. C228 performs no repair, focused rerun or second aggregate.

## A08 and the remaining default steps

All thirteen `TorqueArtifactReadTests` methods passed in this same attempt. Their original class setup therefore completed successfully under the unchanged 1,000,000-operation / 30,000-ms policy. Ordinary successful unittest output does not separately retain its setup duration, operation count or artifact digest. C227's isolated timing and artifact hash are not attributed to this run. [A08 outcome](evidence/A08-SETUP-OUTCOME.json).

| Default step | Result | Preserved scope |
|---|---|---|
| Unit tests | Failed | 4,661 passing methods; one failed method with two failed subtests |
| Source conformance | Passed | 43 cases / 694 assertions |
| Agent conformance | Passed | 10 cases |
| Construction conformance | Passed command | 19 passed cases; one external case pending |
| Surface conformance | Passed command | One passed case; eleven external cases pending |
| Impulse conformance | Passed command | Eight passed cases; four external cases pending |
| Documentation | Passed | 29 preserved sources / 4,759 local links |

All sixteen external cases remain pending. Their exact identities and reasons are retained in [the result summary](evidence/RESULT-SUMMARY.json).

The three CPU readback methods also passed within the aggregate. Review checked their actual process receipts and all 6,180 numerical rows: two positive cases passed, and the deliberately changed reference produced its expected rejection. All three processes were reaped and their groups were absent. These synthetic controls establish no native receiving or rendering result. [Readback artifact audit](evidence/READBACK-ARTIFACT-AUDIT.json).

## Stability and remaining gates

All 15,764 source-inventory entries and the source Git identity remained unchanged. The supervisor recorded no timeout, cleanup signal or unexpected surviving process. The complete attempt is retained with its failure. [Execution receipt](evidence/RUN-EXECUTION.json), [independent review](REVIEW.md).

The nine recommendation records and all 41 acceptance criteria retain their definitions. R00/R01 keep their recorded completed scopes; R02 remains blocked; R03-R08 retain their pending scopes. R07 second-target preparation remains later work after reliability. Historical C224 timeout, C226 setup failure, C227 isolated/profile distinction, original strict Blender-normal failure and Godot limitations remain preserved. Other interpreters, optional visual and dedicated force-agent roles, and wider release acceptance were not added to this attempt.
