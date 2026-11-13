# C230 finite CPU replacement diagnosis

## Observed result

One independently reviewed invocation completed on Linux x86-64 / CPython 3.12.14 from immutable source `e19acb44784ba5654f24bd3d87fb7310249f6d05`, tree `24a3af6da34dc5cce7e6813734fb65958791f712`. The two workers completed in 0.407266689 seconds. The launcher exited 0 because the declared diagnostic schedule completed; **the original product method failed**. Its ten subtests produced eight passes and the same two `LedgerError not raised` replacement failures retained by C228. There were no method errors or skips.

The following four additional observations used the same original unlink/rewrite operation and exact original bytes. An inode is a filesystem object number; the operating system can reuse it after the old file is deleted and no descriptor keeps that object alive. Here device number 27 was unchanged throughout.

| Fixed observation | Inode before → recreated | First reservation | Subsequent poisoning check |
| --- | --- | --- | --- |
| Marker, no held descriptor | 4080869 → 4080853 | Rejected with PERSISTENCE caused by INTEGRITY | Rejected with STOPPED |
| Journal, no held descriptor | 4080855 → 4080855 | Returned a reservation; stopped and uncertain both false | Not run, because initial rejection did not occur |
| Marker, held-descriptor control | 4080874 → 4080858 | Rejected with PERSISTENCE caused by INTEGRITY | Rejected with STOPPED |
| Journal, held-descriptor control | 4080877 → 4080878 | Rejected with PERSISTENCE caused by INTEGRITY | Rejected with STOPPED |

The journal path was observed absent after unlink, then recreated with identical bytes and the same device/inode pair. The current ledger accepted its first reservation. The two held-descriptor controls kept the old unlinked object alive with link count zero; both recreated paths had a different identity and were rejected. The no-held marker also received a different identity and was correctly rejected in that observed case.

## Supported mechanism and limits

The unchanged ledger closes its creation descriptors and retains the marker/journal bytes plus numeric `(st_dev, st_ino)` pairs. It later compares those values. The new journal observation establishes that numeric identity reuse plus identical content can pass this check after replacement. Holding a descriptor changes the old object's lifetime, so those controls support a lifetime-sensitive explanation; they are separately labeled interventions.

Both original replacement failures were reproduced, but the original method does not record its inode sequence. The instrumented marker did not reuse its inode. Therefore this result directly establishes the journal mechanism in the new case; it does not establish an observed marker reuse or reconstruct C228's absent allocation history. Additional observations change timing and filesystem state. No retries or extra cases were used to obtain a preferred result.

Poisoning means the capability stops and refuses later reservations. The journal case never rejected the first reservation, so its second reservation was deliberately not attempted: a stage-order error would not establish replacement rejection or poisoning. All three initially rejected cases subsequently returned STOPPED.

## Preparation, accounting and cleanup

The launcher resolves the plan, approval, source, output, interpreter and derived scripts before changing the child's working directory. It verifies exact script bytes, refuses a mismatched running launcher and preserves one-use output claiming. Twenty-four author controls passed, including an inert reproduction of C229's old failure. Independent qualification passed eight controls with 88 assertions; 29 static/binding conditions passed before approval. These were harmless stand-in executions, separate from the product counts.

The exact approved plan, source bundle and approval were confirmed saved as recovery evidence version 2 before invocation. That save succeeded; a separate short-checkpoint replacement conflict was retained and later reconciled without bypassing its version guard. Source commit/tree, clean status and all nine pinned inputs remained unchanged before/after the diagnostic run. Both workers were reaped, no remaining process-group members were observed, no worker child starts occurred, original unittest fixtures were removed, and retained control descriptors were closed.

The four observed cases account for four ledger creations and seven reservations. Original method control flow and callbacks reconstruct ten creations and eighteen reservations: fourteen creations and twenty-five reservations total, below the reviewed maxima of fourteen and twenty-eight. Those totals are reconstructed, not runtime instrumentation counters. Sixteen raw observation events and thirty-two binary snapshots preserve the actual case evidence.

## Independent outcome review

[Independent review](evidence/OUTCOME-REVIEW.md) accepted the finite result after 313 read-only assertions. The checker reconciled the exact plan/source/approval/invocation, preexecution save receipts, ten subtests, four cases, sixteen raw events, thirty-two binary snapshots and cleanup. It executed no product code. The separate author result analysis passed 65 consistency checks. The full reproducible review and raw observations are preserved in the saved recovery evidence and included in the successor handoff; final delivery remains tracked by scope #192.

## Scope disposition

This increment changes only diagnostic source, documentation and evidence. No ledger product repair, product assertion change, budget increase, aggregate attempt or native start occurred. C229's old schedule and this new C230 schedule are consumed and closed. C228 remains a failed aggregate: 4,662 methods ran, 4,661 passed and one failed with two replacement subtests. **R02 remains blocked.** The original A08 failure, sixteen external conformance cases, other interpreter/optional roles, all nine recommendations/41 criteria, held drafts and consumed native schedules keep their recorded meaning.

The [next bounded step](NEXT-TASK.md) is a narrow ledger file-identity repair supported by this diagnosis. The actual complete regression must be established later; this diagnostic completion does not pass it.
