# C061 measured evidence integrity review

Date: 2026-10-28. Reviewer: `/root/handoff_integrity`.

## Disposition

**The retained first-round evidence supports publishing C061 as a completed diagnostic attribution checkpoint. Both original product requests still fail.** The successful pair audits, expected negative-audit rejections and exact restoration of the original captured inputs are internally consistent. No contradictory product-pass or savings claim was found in the inspected evidence.

This review read existing JSON, source, command logs and raw retained bytes, and compared their recorded identities with standard-library hashes. It did not run a product request, auditor, test, numerical replay, archive operation, compression, SQLite operation or remote command. The only write was this review. The reviewer previously authored the new audit adapter; separate review of that code was performed by root and `/root/c060_review`.

The documentation check inspected here is the initial `documentation-before` attempt. It failed with 17 missing local targets. A later check after recovery of real tracked directory children is pending at this review boundary; no final documentation pass is asserted.

## Executed source and materialization

The product requests and successful audits identify:

- Source commit: `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`.
- Source tree: `037157a58442ba1956597d32e1e540802f9ed896`.
- Parent: C060 `00533b953ed345cbf5fa13eaa56aafa3a2f052a8`.
- Execution directory: `ontokin-c061-run`.
- Materialized source: 491 tracked files, 9,527,653 bytes, including all 65 runtime files.
- Omitted source: 2,890 tracked entries. Their payload bytes were not verified.
- Shallow source history and `complete_stock_harness: false` are disclosed.

The retained raw Git commit object hashes to the reported commit and names the reported tree. The explicit `execution-checkout.json` inventory agrees with the request snapshot on every materialized path, byte count, SHA-256, Git blob and mode, and on the omitted-path set. All eight before/after snapshots from the four product requests are byte-identical.

All 65 runtime Git blob identities in the executed snapshot match the retained C060 tree inventory. Among the 491 materialized source entries, the only additions or changed identities relative to that inventory are the new collector and auditor. The source-binding evidence supports a tooling-only execution increment, not a runtime optimization.

The separately expanded documentation worktree had 1,271 materialized and 2,110 omitted tracked files at its initial check. That count must not replace or be conflated with the 491-file product execution scope.

## Successful pair audit evidence

| Observation | P11 | L03 |
| --- | ---: | ---: |
| Original control raw exit | 1 | 1 |
| Instrumented capture raw exit | 1 | 1 |
| Offline pair audit raw exit | 0 | 0 |
| Pair audit result | passed | passed |
| Recorded assertions | 381,009 | 677,251 |
| Final shared operations | 100,001 | 100,001 |
| Final admitted Reach operations | 93,277 | 95,767 |
| Reader-setup shared/Reach operations | 23,171 / 23,171 | 17,185 / 17,185 |
| Setup spans / balanced events | 93 / 188 | 83 / 168 |
| Unwrapped setup residual | 1,027 | 1,069 |
| Stored keys / entered keys | 52 / 37 | 178 / 154 |
| Returned provisional keys | 36 | 153 |
| Partial failed key index | 36 | 153 |
| Actual carriers / interval certificates | 20 / 1,020 | 6 / 1,062 |

The recorded commands are sequential and not timed out. The successful audits explicitly preserve the original 100,000-operation allowance and classify the final shared tick at 100,001 as the operation-limit refusal. Audit success validates the retained diagnostics, not the failed product request.

I checked the byte count and SHA-256 of all six emitted member files for each successful audit. All 12 match their enclosing `audit.json` records. The executed new auditor and unchanged C060 dependency match their declared and previously reviewed hashes. Product stdout/stderr descriptors and both external successful-audit stdout/stderr/runner descriptors also match the files inspected.

For each case, all three retained reader-input GLBs are byte-identical: the uninstrumented postfailure copy, instrumented diagnostic postfailure copy and collector copy. Their byte descriptors match. This review did not decode or validate those GLBs; they remain explicitly unvalidated artifacts from failed requests.

### Binding hashes

| Retained object | SHA-256 |
| --- | --- |
| P11 successful `audit-001/audit.json` | `84cbd12d7ce539d77b451be8c55859094711825bc8a2447d2a8dfcfad0c15fb6` |
| L03 successful `audit-001/audit.json` | `927698c0839abdc8a0f13c2e3f245bbd787e30759eba0f2efbc2a1cb2cf3ebc7` |
| P11 original/restored `reader-setup.json` | `49fa81a134a14e962d21737197faa1ad32b0d148a15422757275958279f4f55a` |
| L03 original/restored `reader-setup.json` | `c86c6bd6c32f0294907a32b01a8f468824cf425e6b0eb36d59ecc1f020a8ffb5` |
| Executed collector | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` |
| Executed C061 auditor | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` |
| Unchanged C060 audit dependency | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` |

## Meaning of the measured structural costs

P11 has 60 observed `_phase` calls, totaling 6,006 shared/Reach/checkpoint operations in reader setup. It has no observed `_axial_derivatives`, axial-only `_l1` or axial-only `_axis_transport` spans in this interval.

L03 has 24 `_phase` calls with an inclusive cost of 3,300. Four nested axial calls cost 376 in total. Within those axial calls, 22 `_l1` calls account for 132 and 14 `_axis_transport` calls account for 70; the axial exclusive remainder is 174. The phase exclusive remainder is 2,924. The inclusive phase, axial and helper totals overlap and must not be added as separate total work.

These figures identify the actually observed target. They do not establish removable work or a positive saving after replacement admission, lookup, insertion, invalidation and cache displacement. P11's zero observed axial calls applies to this source and reader-setup interval, not every future case or later endpoint work. L03's 376-operation inclusive axial total is an observed gross scope bound, not an optimization result.

The results retain full-category reconciliation at coarse boundaries and explicit scalar-only nested attribution. Repeated typed inputs and process-local IDs remain observations, not source equivalence or reusable proof authority. The evidence correctly leaves optimization savings, complete-request costs and unexecuted tail costs unspecified.

## Negative audit controls and restoration

Two existing offline corruption controls were inspected. Neither runs a product request.

| Control | Exact altered field | Observed result |
| --- | --- | --- |
| P11 duplicate entry event | `/spans/1/entry_event`: 3 to 1 | Raw exit 1; `Duplicate or out-of-scope setup event` |
| L03 checkpoint-map mismatch | `/spans/0/exit/checkpoint`: 4,060 to 4,061 | Raw exit 1; `Setup checkpoint scalar differs from the full category map` |

The saved original and altered files match their control-record hashes. A structural JSON comparison found only the one intended value change in each altered document. The actual audit failure messages match the expected reasons, and command stdout/stderr hashes match. Both live capture paths now contain bytes identical to their saved originals and original successful-audit inputs.

The negative audits' `status: failed` and `all_analysis_inputs_stable: false` must remain intact. They are expected rejection records, not successful diagnostic artifacts. The control result is the intended rejection plus exact restoration. These two targeted controls do not certify every validator rejection path.

## Documentation check boundary

The initial documentation command returned 1 without timeout. Its receipt and JSON result agree, and its before/after input snapshots are byte-identical. It verified 29 preserved sources and 233 sections, but reported 17 local-link failures: 12 omitted historical archives and five links into four absent validation directories.

The four directories are `checkpoint-034-validation`, `checkpoint-035-validation`, `checkpoint-038-validation` and `checkpoint-042-validation`; the last is referenced twice. Root's planned repair is to materialize real tracked children so those paths exist. This review does not approve creating empty placeholders or changing old links to conceal missing evidence.

The initial failed attempt must remain published even if a later attempt narrows the failure set. A later outcome can supersede the current navigation assessment, but it cannot retroactively make this command successful. The final documentation check and its exact materialization scope require their own retained receipt.

## Publication caveats

The product and audit receipts use absolute paths from this execution environment. Retain them unchanged as historical commands; do not silently rewrite them to a future extraction directory. A separate recovery guide may explain how to recreate the checkout or inspect results elsewhere. Re-executing the audit in another path is not established by this review.

External runner scripts are outside the tested Git tree. Their descriptors are meaningful only if their bytes are retained with the evidence. Preserve `run_recorded_command.py`, `run_evidence_command.py`, `run_negative_audits.py`, `prepare_execution_checkout.py` and `execution-checkout.json` in the source-binding/evidence package. The first two match the command-receipt hashes inspected here. Their identities are:

| Runner | Bytes | SHA-256 |
| --- | ---: | --- |
| `run_recorded_command.py` | 3,232 | `37327efd8d3b11affba97055dfc67f23fba34ead640869dd98dee2a89fdd1626` |
| `run_evidence_command.py` | 1,969 | `cd6448a9d811904214902b193645a55679a9ce4ae6adf65e6cc537fd0a272379` |
| `run_negative_audits.py` | 2,915 | `83aaef26cc4e9c41d7de0bed3bace68cda4ff66f418e3a6d5669db02c0639d50` |
| `prepare_execution_checkout.py` | 3,158 | `061e6ff5e0bc0a4a95c220c065dfbc4833615d9685cd0f285df82859563d135d` |

A later publication or integration commit must distinguish its identity from the tested source commit above. The evidence establishes neither a completed full harness, a new passed recording, a runtime speedup, completed LFS migration nor a release. Preserve the experimental 24/28 baseline, four unresolved recordings, C035's held state and exact M1's rejection unless separately changed by future authorized evidence.

No evidence-publishing, archive-completeness, remote-head or merge result is certified by this static review. Root retains those completion tasks. This reviewer now pauses all commands, edits and transfers; no process is running.
