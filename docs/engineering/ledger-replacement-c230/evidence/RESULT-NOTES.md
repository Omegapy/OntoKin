# C230 measured result

The corrected launcher completed its one finite two-worker diagnosis in
0.407267 seconds. Both workers were reaped, no process-group members remained,
and the exact source commit, tree, clean status and nine bound files were
unchanged. The schedule is consumed. This analysis reads the existing results;
it performs no additional product execution.

## Original failure reproduced

The original, unmodified ledger method ran all ten subtests. Eight passed;
the invocation-marker replacement and journal replacement subtests failed
because `LedgerError` was not raised. The worker exited 1, correctly retaining
that test failure. It had no errors, skips or child-start attempts, and its
original temporary fixtures were cleaned. The launcher allowed the planned
observation worker because these two failures were the expected diagnostic
outcome. A successful diagnostic launcher exit does not make the method pass.

This replay observed test results without recording live file identities.
Neither replacement failure in this original method directly proves which
inode allocation occurred.

## Four direct replacement observations

Every case observed a successful unlink, an absent path, and recreation with
identical bytes. The table reports the measured device/inode pairs, not an
assumption about the filesystem.

| Case | Old identity | Recreated identity | First reservation | Subsequent poison check |
| --- | --- | --- | --- | --- |
| Marker, no held descriptor | `(27, 4080869)` | `(27, 4080853)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected: `STOPPED` |
| Journal, no held descriptor | `(27, 4080855)` | `(27, 4080855)` | Accepted; stopped and uncertain both false | Not run because the first reservation succeeded |
| Marker, held-descriptor control | `(27, 4080874)` | `(27, 4080858)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected: `STOPPED` |
| Journal, held-descriptor control | `(27, 4080877)` | `(27, 4080878)` | Rejected: `PERSISTENCE` caused by `INTEGRITY` | Rejected: `STOPPED` |

The journal case directly demonstrates the failure mechanism: an unlinked
file's numeric device/inode identity was reused by its same-content
replacement, and the unchanged ledger accepted a reservation. The source
stores those numeric identities after closing its creation descriptors;
later checks compare both identity and bytes. In this observed case both
comparisons matched despite the intervening unlink.

Both held-descriptor controls kept the old file object alive with zero links,
received different identities for the replacement paths, and triggered the
existing rejection and terminal poisoning behavior. Both retained descriptors
were closed. These controls deliberately changed object lifetime. They are
evidence about the proposed mechanism, not an implemented repair.

The direct marker observation received a different identity and rejected.
That does not contradict the original marker subtest's missing rejection:
they are different allocations, and the uninstrumented replay did not retain
its identity sequence. C228's historical sequence also remains unavailable.

## Accounting and preserved evidence

The observation worker produced 16 synchronized event records and 32 retained
binary snapshots. Their reported hashes, event bytes and final case records
agree. Four first reservations and three poison checks establish seven
observed reservation calls. The unchanged original method's control flow and
complete callbacks establish ten ledger creations, ten first reservations and
eight subsequent `stopped()` checks: eighteen reservation calls. Combined
counts are fourteen ledger creations and twenty-five reservation calls,
within the declared ceilings. These counts are reconstructed from recorded
outcomes and exact control flow; the calls were not separately instrumented.

`MEASURED-SUMMARY.json` records 65 passing read-only consistency checks and
the hashes of the raw input results. It separates observed facts from the
control-flow-derived counters.

## Meaning and next recommendation

This finite diagnosis establishes one directly observed journal mechanism and
reproduces both original rejection failures. It does not reconstruct each
C228 failure, measure inode-reuse frequency, or establish other-platform
behavior. Instrumentation changes timing and allocation; four cases are a
finite observation.

The next separately selected scope should repair ledger authority-file
identity, including explicit retained-handle lifecycle and cleanup where
chosen, and provide deterministic same-content replacement controls while
preserving original rejection and poisoning expectations. The product ledger
is unchanged here. R02 remains blocked, and a full aggregate retry requires
its own later scope after relevant repair evidence.
