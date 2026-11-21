# Run 001 independent failure review

## Decision

Run001 is a preserved failed attempt on candidate003. Implementation acceptance remains unavailable. All 64 unittest error records, across 39 distinct test methods, fail during the same shared observation-fixture setup. The one-line fixture correction is sufficient to address this established failure mechanism; it does not establish that the previously blocked observation controls pass.

The appropriate next validation is one fresh run of all 135 mapped focused methods on a separately frozen, reviewed and cleanly published candidate. The shared helper participates in observation routes and nested fault injection, so a complete focused result is preferable to combining old passing methods with a partial repair run. This is the existing bounded focused suite. It does not authorize the original seven methods, full routine, actual host qualification, runtime preparation, Node/ldd execution, or integration.

## Observed result and evidence

The retained OUTCOME records exit1, no timeout, no wrapper exception, one outer harness child, failfast false, and a five-second elapsed run within its 180-second bound. The unittest footer reports 135 methods, 64 errors, zero assertion failures and zero skips. Independent parsing identifies 39 methods with one or more error records and 96 methods without error records. The difference between errors and methods is caused by failing subtests; subtracting 64 from 135 would be incorrect.

All 64 full traceback bodies and their ordered method names match FAILURE-INVENTORY-002.json. Every traceback reaches test_current_host_inspection_v01.py line468 and raises the same AttributeError for the module attribute `_EvidenceStore.write`. None reaches the production observation frame. Thus the affected observation controls remain unexercised, even where their method performed some setup or assertions before entering that context. The 96 other methods retain their recorded no-error results; these do not compensate for the blocked controls.

The guarded runner result agrees with both stdout and the embedded OUTCOME result. Every reported process-operation guard counter is zero. This supports zero actual project process operations within the instrumented test boundary. The single outer Python harness launch is separately recorded and is not a project operation.

The reviewer verified the retained stdout, stderr, result and all twelve run input snapshots against their recorded identities. Historical source postflight identities match retained snapshots, including the candidate003 test bytes. The reviewer also verified all 135 per-method fixture manifests at `runs/run-001/fixtures/manifests`: the selected method set is exact; all 12,174 entries match their recorded metadata and contents. These entries comprise 8,240 regular files, 3,922 directories, 11 symlinks and one special entry. File hashing covered 291,887,872 bytes. There were no fixture discrepancies.

Author FAILURE-INVENTORY-002 preserves its earlier inventory and corrects only the method-versus-error-record interpretation. That report history remains intact.

## Failure mechanism and minimal correction

The original call is `patch.object(inspection, "_EvidenceStore.write", new=writing)`. `patch.object` treats its attribute argument as a single attribute name; it does not traverse the dot. The existing class is therefore never selected, and context entry fails before its yield.

The exact correction is `patch.object(inspection._EvidenceStore, "write", new=writing)`. The new function remains the same wrapper around the original class method. Its write logging, delegated atomic writer and fault-injection behavior remain unchanged. Production bytes, fixture inputs, assertions, expected states and counts remain unchanged. The proposal and candidate004 contain only that one test-source line change.

This fixture defect was missed in the independent static pre-execution review. The earlier approval was permission for a bounded attempt, not implementation acceptance. The failed result is retained rather than relabeled as successful coverage.

## Reviewer bookkeeping history

The first local VERIFICATION.json is preserved as provisional history. It used an incorrect run-root `manifests` location and compared a run001 historical descriptor with the subsequently authorized candidate004 working-tree test file. Those assumptions produced zero discovered manifests and a false live-file mismatch. VERIFICATION-002.json corrects the path and compares version-specific retained snapshots. It supersedes only those audit assumptions; it does not alter run evidence. The large initial directory listing and first displayed audit output were truncated, so this report relies on the complete retained parse and the explicit corrected audit, not truncated display output.

No candidate import, compilation, test execution, runtime action, source edit, Git operation or replay was performed by the reviewer.

## Exact references

- Run OUTCOME: SHA256 2a35f611b1b206c55d40c0c5d35a8ba3fc2e77408201060579eed5647da5a680.
- stderr: SHA256 646103713d66bb79edb1f732ea5db0f1ed36d1fec44bf66054742017096ed48a.
- Corrected author failure inventory: SHA256 72bb22a73400f799d30fdda3815b9f986653cacab7ac21c0b570c84905b353e8.
- Independent corrected verification: SHA256 db7ec8d4cc3967fbff09b0215a12d5e4d674799e414b97d15cc2eb6cfa931b4b.
- Inert minimal proposal: SHA256 4374313a987eceef2b09e703f0838324aed31c85ede9558da6ef0072d134d189.

The complete detailed trace classification, manifest identities, counts and correction history are in VERIFICATION-002.json; the original audit remains in VERIFICATION.json.
