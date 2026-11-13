# C230 independent outcome review

Decision: **ACCEPT_FINITE_DIAGNOSTIC_RESULT**. The fixed diagnosis completed and directly demonstrated an identity-reuse failure in the instrumented journal case. This accepts the evidence and its limited interpretation; it does not accept the defective ledger behavior or close R02.

The independent result verifier passed **313 assertions**. It read raw results, retained bytes, event records, source hashes, invocation/save receipts and Git metadata. It imported no product module and performed no method replay, replacement probe, aggregate or native application start. The reproducible script is `check_outcome.py`; complete checks and input hashes are in `OUTCOME-REVIEW.json`, with stdout/stderr retained separately.

## Execution and immutable bindings

The root used the approved fully absolute outer command once. The source before and after is clean commit `e19acb44784ba5654f24bd3d87fb7310249f6d05`, tree `24a3af6da34dc5cce7e6813734fb65958791f712`, with all nine exact reviewed inputs. Fresh independent readback found those same bytes and clean state. Plan digest `17f895542e68f99d06ca6b3771049b180308e380762f8bdd972b3ed8f80fbcd9` and approval digest `cb16f268953c491e149835fa5d9a94e9b934d0cca2e9531d2db47c63fc6f868c` match the invocation and launcher receipt. The frozen worker and corrected launcher hashes remain exact.

The prelaunch evidence save succeeded as recovery version 2, file `file_00000000b6ac81f4ad5cbfe139621e75`, with archive SHA-256 `3ae9f1baca68dde06332c2e509b55a8c5414f0affa53443c8349aabcf9902cf8`. The immutable build/save and root-invocation receipts agree. The separate short-checkpoint replacement returned a recorded conflict; this did not change the successful evidence-archive save. The current recovery ZIP is mutable and may now contain a later version; no continued byte equality with that current path is claimed.

Both planned workers started and exited within their 60-second ceilings. Their process IDs and groups agree across worker environment and launcher records. Both were reaped, with no remaining process-group members observed. Original fixture cleanup was observed empty; retained control descriptors closed. The run used Linux x86-64 / CPython 3.12.14 with bytecode writes disabled. No worker child attempt, native start, aggregate or retry was recorded. The launcher completed in approximately 0.407 seconds. Its exit code 0 means the diagnosis completed; the original test worker exited 1 because its two expected failures reproduced.

## Original unchanged method

The selected method ran exactly once and produced ten subtests: **eight passed and two failed**. Both failures were the original same-content replacement mutation, one for the invocation marker and one for the journal. Both report `LedgerError not raised` at the unchanged assertion. There were no errors or skips. The raw unittest stderr and structured callbacks agree, and the failure names/assertion match the two preserved C228 failure records.

No file-identity observation was inserted into that original method. Its marker and journal allocation sequences therefore remain unobserved. Because the first rejection assertion failed, those two subtests did not reach the later stopped-capability check. They reproduce missing rejection without independently measuring subsequent poisoning.

## Four instrumented cases

All identities below are the observed `(device, inode)` pair. Original and recreated file bytes agree in every case, and each unlink left the selected path absent before recreation.

| Case | Original identity | Recreated identity | First reservation | Poison check |
| --- | --- | --- | --- | --- |
| Marker, no held descriptor | `(27, 4080869)` | `(27, 4080853)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected with `STOPPED` |
| Journal, no held descriptor | `(27, 4080855)` | `(27, 4080855)` | Returned; `stopped=false`, uncertainty false | Not run because the first reservation succeeded |
| Marker, held-descriptor control | `(27, 4080874)` | `(27, 4080858)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected with `STOPPED` |
| Journal, held-descriptor control | `(27, 4080877)` | `(27, 4080878)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected with `STOPPED` |

For the journal case without a held descriptor, the original path was removed, the path was observed absent, and a same-content recreation reused the original numeric identity. The next reservation returned, appended a valid `RESERVED` record, and left the capability live. The journal grew from 286 to 692 bytes; independent hash-chain checks confirm its original `INVOKED` record and added `RESERVED` record. This is direct evidence that numeric identity and byte equality can accept a recreated authority file under the observed conditions.

The instrumented marker case received a different inode and rejected correctly. It therefore does not independently demonstrate marker inode reuse, even though the uninstrumented original marker subtest reproduced missing rejection.

In both held-descriptor controls, the descriptor retained the original identity while its link count fell to zero. The recreated path received a different identity. The first reservation rejected, the snapshot was stopped and uncertain, and the conditional second reservation rejected with `STOPPED`. The descriptor was then closed. Holding that descriptor deliberately changed the object's lifetime; these controls are not the original operation or a product repair.

## Evidence consistency and accounting

The sixteen raw event records agree with all four final observations. Their original/recreated/post-first-reservation hex bytes agree with all corresponding retained files. All **32 retained binary files** match their recorded sizes and hashes. Final authority-file bytes agree with the retained post-poison snapshots. Descriptor inventories establish no retained original-file handle in the no-held cases and the single declared handle in each held case. All recorded native-readiness/admission flags remain false. The handoff copy of the complete run matches the original run bytes.

The unchanged method's complete outcomes and static control flow account for ten ledger creations and eighteen reservation calls. The four observed cases account for four creations and seven calls. Combined: **14 creations and 25 reservation calls**, within the reviewed maxima of 14 and 28. These are control-flow-derived counts reconciled to complete outcomes, not additional inserted counters.

## Supported conclusion and next boundary

The instrumented journal result establishes the identity-reuse mechanism in this run. C228 did not preserve an inode sequence, so its exact historical allocation cause remains unproved. The original marker failure reproduced, but its allocation was not measured; the instrumented marker rejected correctly with a new inode. Additional stats, reads and evidence synchronization affect timing, and the two held controls are explicit interventions. No cross-platform or universal failure-rate claim follows from these four cases.

R02 remains blocked, the original assertions remain unchanged, and all historical failures retain their meaning. The selected diagnosis is complete and consumed. The next thread may select a bounded ledger replacement-identity repair with explicit resource-lifetime behavior and focused verification that preserves rejection and poisoning expectations. Such a repair and any later aggregate are separate work; no further product execution belongs to C230.
