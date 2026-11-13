# C229 independent static review

## Evidence and scope

The inspected clean source is exact published C228 main `d578a30dab9a112895d2e3c09561a17866d9c464`, tree `080b9d00bc340dfd9728601147d11816fab4375d`. `STATIC-INPUTS.json` binds the inspected implementation, test, schedule and contract. This review executed no product imports, tests, filesystem replacement probes or native processes.

C228 retains two failures in one unchanged test method: same-content unlink/recreation of the invocation marker and journal did not raise `LedgerError` on the next reservation. Its logs do not preserve the filesystem identity sequence. A specific historical inode-reuse cause is therefore unproven before new observations.

## Static findings

1. `ledger._identity` returns only `st_dev` and `st_ino`. Creation handles for marker and journal are closed in `Ledger.begin`; `_read_regular` also closes its read handles. The live capability retains byte strings and numeric identity pairs, not open file objects.
2. Before an append, `_append` verifies directory identities, file types/link counts/bounds, marker/journal bytes and those numeric pairs. The final append handle additionally checks journal identity and one link. Mode, change time and generation/lifetime are not part of `_identity`.
3. The original test uses `path.read_bytes()`, `path.unlink()`, then `path.write_bytes(original)` with no retained handle. It expects a rejected reservation followed by a permanently stopped capability. The recreated marker can have a different permission mode, but permission mode is not the replacement guard's declared identity.
4. If the filesystem reuses the numeric inode for the recreated same-content file, every compared value can match. That supplies a concrete hypothesis explaining a missed replacement; static inspection alone does not show that reuse occurred in C228 or will occur in the finite diagnosis.
5. `_append` wraps an underlying `INTEGRITY` or `OSError` as a `PERSISTENCE` `LedgerError`, setting stopped and uncertain. An observed rejection must preserve the nested cause and must be checked against this actual error contract.
6. In the original unittest method, an `assertRaises` failure exits its `subTest` before `self.stopped(ledger)`. C228's missing rejection is directly observed; later poisoning is not independently observed in those two failed subtests. For diagnostic cases, run the stopped/retry check only after the first reservation rejects. A retry after an unexpected successful reservation could fail for a different ordering reason and must not be counted as successful replacement poisoning.

## Plan review requirements

Keep the original single-method replay unmodified and isolated. A separate instrumented invocation may compare exactly four marker/journal × no-held-descriptor/held-descriptor cases. The held-descriptor condition is an intervention that preserves the original file object's lifetime; it must not be described as the unmodified test. No adaptive repetitions or trial-until-failure loop is permitted.

Bind a fresh temporary-directory root on the actual workspace filesystem for both invocations and record its path, filesystem identity and available mount details. C228's plan used `/workspace/scratch/a9488c5c1afa/aggregate-run/tmp`; a new path has no guarantee of its historical allocation sequence. Preserve original bytes before mutation, content hashes, device/inode, size, links, mode, nanosecond times, exact absence/recreation observations, relevant open-descriptor facts, returned exceptions/state and journal changes. Do not hold a descriptor across unlink in the no-held-descriptor condition. Keep instrumentation effects explicit.

Approve only a hash-bound finite plan/harness with two maximum diagnostic child starts, original product limits, per-command host ceilings, exclusive one-use output, source before/after equality, complete cleanup, and no native execution. A passing replay cannot erase C228. Inconclusive finite observations must remain inconclusive, with a precise next investigation rather than another unapproved attempt.
