# Reach recording continuation, October 23, 2026

Checkpoint **013** continues [012](checkpoint-012.json), [011](checkpoint-011.json),
[010](checkpoint-010.json) and [009](../reach-recording-validation-2026-10-22/README.md).
The latest complete source GLB/0.6 run passes **23/28** under the unchanged
**100,000-operation** request limit. **P05 now passes at 99,039 operations**.
Five cases still exhaust the budget: **P09, P11, P16, P23 and L03**.

[PR #27](https://github.com/Omegapy/OntoKin/pull/27) remains open, draft and unmerged.
Do not merge it until every mandatory acceptance gate passes. Main remains
`2bb4588e121fcfe99b4d42c734b15b38362f3642`. The complete product goal remains open.

## Tested source and publication

Published source
[`911756ae865a415b3fece6c1c35fa2d92fd7b5a8`](https://github.com/Omegapy/OntoKin/commit/911756ae865a415b3fece6c1c35fa2d92fd7b5a8)
has exactly the Git tree of tested local commit
`115adf5cfb528f65b5ccf9a2640f01b39486d029`:
`a8e80bacdd5d086bbc78fa8ad794608ed8ee7dbe`.
The continuation branch is `work/reach06-recordings-20261023-7of9-e619`;
the original baseline is `6cf8c525429076ce37efd4ecea95fd01f83365ea`.

The latest complete run is `combined-recordings-016`. Every materialized input
matches its committed Git identity before and after execution. P20 uses
**86,659**, L01 **85,576**, and L02 **78,151** operations. The machine-readable
checkpoint lists all 28 results. Each integration retains its preceding complete
run and focused tests; the latest numbers do not replace older source cuts or
failed attempts.

| Integrated focused scope | Actual result | Evidence directory |
| --- | --- | --- |
| Retained final after-source bounds | 33/33 passed | `combined-final-source-focused-001` |
| Independent endpoint order and factor-two arithmetic | 48/48 passed | `combined-endpoint-order-focused-001` |
| Actual-source stationarity through covering plans | 51/51 passed | `combined-stationary-focused-001` |

Each listed cohort has zero failures, errors and skips and stable materialized
inputs. Each report identifies its actual source commit and tree. Separate
worker endpoint and stationary cohorts passed 71 and 96 methods respectively.
The stationary count comprises 15 new and 81 relevant methods on its final
candidate. These counts are not summed or represented as one current full
regression inventory. Checkpoint012's 49-, 50-, 29-, 37- and 38-method integrated
cohorts and all earlier cohorts retain their original source identities.

## P05 correction and remaining P16 correctness work

The earlier P05 observer reproduced its certificate failure with the original
work counters and stable inputs. Exactly six rows belong to its final interval,
35/12 to 3 seconds. The writer selected only the moving positive-width phase.
The independent reader also included the outgoing final point, whose root anchor
inherits the completed spin's exposed rotation error. Each rotation deficit was
exactly **2^-50 + 2^-91**. Five descendant position bounds also omitted the
resulting path-offset contribution.

Integrated worker candidate `1a12060d4790f7133a46b69a42a217e9ebba78f1` explicitly
evaluates `plan.final_state` at the final point and includes its numeric position
and rotation bounds for certificate groups containing the final key. Sampling,
positive-width phase selection, quarter-allocation inequalities and the reader
are unchanged. Full run014 reaches final certificate checking but still exceeds
the cap. After the endpoint arithmetic integration, run015 passes P05 at 99,033
operations; the latest combined run passes at 99,039. The original failed 5/7
test attempt and its repaired test harness remain archived.

A distinct short P16 release diagnostic still exposes a position-bound mismatch.
The independent anchor interval has a slightly larger extent than the writer's
canonical position. The final-source correction makes the rotation claim
sufficient but leaves a small position deficit. A conservative finite-grid
transfer proof is being developed for supported exact source lineage, including
later force reanchors and impulses. It is **not integrated or verified**.
Arbitrary padding or a weaker independent check is not an accepted fix.

## Exact arithmetic and source-reuse changes

Worker `3525b74657dfb43deb77a9e1b3fef58658886aca` uses already calculated endpoint
subtraction signs to select the farther endpoint when the exact cell is wholly
outside the independent interval. Both original subtraction callbacks, full
operand guards and ordinary fallback remain. Exact factor-two multiplication
uses a detached native Fraction after checking its actual fields, so mutation
of the module constant cannot change the local operand after admission.
Paired original P09/L03 observers measure **10 fewer operations per eligible
steady key**: eight exact comparisons and two bound decodes. Full work records
and diagnostics match ordinary unprofiled execution.

Worker `9c1027cfb64dfcab52a482ee9ff7b9f3e32a3263` reuses actual-source stationarity
through an already registered covering plan for the same captured state and
context. The actual-source proof is distinct from ideal constancy. A running
zero coordinate requires identical actual initial, ideal initial and target
values. Candidate owners and complete carriers remain admitted through the
existing bounded source batch and terminal receipt check. No new history,
numeric cache or source capture is introduced. Paired observers measure
**12 fewer operations per eligible steady key**, preserving cold/boundary work.
The final source batch still has two plans/26 receipts for P09 and four/52 for
L03. Short-prefix artifacts and reports match the ordinary path exactly.

These changes retain the fixed Taylor/arctangent degree, complete prospective
width guards, source target bits, tolerance allocations, callback/cancellation
behavior and the 256-entry numeric cache maximum. They follow the earlier mixed
P11 sampling, source receipts, Cartesian products, native unit offsets and exact
dyadic identities documented in checkpoint012. Implementation hashing still
charges for the actual executed helper files. No public limit was relaxed.

A new producer sampling observer preserves complete original work records and
diagnostics for P09/L03. It identifies further costs in native body sampling,
phase proofs and encoding. These measurements support investigation; they do
not establish future savings. Unverified scopes include P23 final static proof
and graph reuse, and phase-specialized independent composition. Earlier rejected
source-template candidates and the equal-cost full-angle recurrence remain
rejected.

## Evidence and recovery

The [machine-readable checkpoint](checkpoint-013.json) lists all 28 current
results, identified cohorts, the pending correction and execution limits.
The [archive manifest](checkpoint-013-manifest.json) binds **403 new raw members**
in **12 parts**, each smaller than 1 MB. The joined ZIP is **9,911,041 bytes**,
SHA-256 `7a8bacf913c08e48778b158032c8afbefccce5ba1bd8473e70a5db236713e10b`.
Every member SHA-256, ZIP CRC and joined-part identity passed. Concatenate parts
in manifest order, verify the complete identity, then extract.

The archive is incremental. Its **1,562 unchanged-member references** resolve
through the original [checkpoint012 manifest](checkpoint-012-manifest.json),
including that manifest's references to [011](checkpoint-011-manifest.json)
and [010](checkpoint-010-manifest.json). All original archives retain their bytes.
New material includes intermediate runs, before/after inventories, source GLBs,
method outcomes, logs, diagnostics, executed drivers, rejected candidate patches,
local commit objects and exact local-to-published tree mappings.

Three older focused text logs were observed incomplete even though their
structured method results and process reports completed. Their original bytes
and this limitation remain in `execution/log-completeness-013.json`. Missing text
was not reconstructed. The development driver captures actual unittest output
once, records its length/hash and requires its executed footer; the latest
51-method run has a complete log. This does not retroactively repair old
evidence or establish release acceptance.

The [documentation check](checkpoint-013-docs.txt) remains separately visible.
Historical binary-archive links unavailable in the sparse recovery keep its
overall status failed. Prior rejected candidates, incorrect test assumptions,
misspelled invocations, interrupted diagnostics and failed attempts are preserved.

## Execution limits and next gate

All runtime, test, tool, fixture and specification inputs are materialized and
Git-verified. **37 historical binary evidence archives/parts remain
unmaterialized**, with exact Git blob identities retained in the tree and every
execution inventory. Missing runtime or fixture inputs stop the development
driver. The stock release collectors are unchanged.

The development schema is `ontokin.reach-sparse-development-execution/0.1`;
`release_acceptance` and `release_input_closure` remain false. No current full
regression, compatibility, historical archive closure or finite release pass
is claimed. Runtime, test, SQLite, workflow and archive execution is serialized.

Complete the P16 source enclosure correction and reduce repeated computation
affecting P09, P11, P16, P23 and L03. Run targeted correctness tests before each
integration, followed by the original full 28-recording suite.

After **28/28**, execute Agent delivery, complete regression, CPython
3.11/3.12/3.13, independent rate/native/browser/visual checks, inherited/hostile
roles and every R01–R12/Q01–Q22 requirement under the
[adopted contract](../../language-design/planar-reach-v0.1/ADOPTION.md).
No main integration lease, hosted-job dispatch, paid execution or Actions
setting change occurs at this checkpoint.
