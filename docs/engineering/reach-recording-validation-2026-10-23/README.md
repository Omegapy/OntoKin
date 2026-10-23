# Reach recording continuation, October 23, 2026

Checkpoint **012** continues [011](checkpoint-011.json), [010](checkpoint-010.json)
and [009](../reach-recording-validation-2026-10-22/README.md). The latest complete
source GLB/0.6 run remains **22/28** under the unchanged **100,000-operation**
request limit. Five cases still exhaust the budget: **P09, P11, P16, P23 and L03**.
**P05 reaches certificate validation at 99,069 operations and fails its final
source rotation bound.** The former cap had hidden this correctness failure.
No additional complete recording pass is claimed.

[PR #27](https://github.com/Omegapy/OntoKin/pull/27) remains open, draft and unmerged.
Do not merge it until every mandatory acceptance gate passes. Main remains
`2bb4588e121fcfe99b4d42c734b15b38362f3642`. The complete product goal remains open.

## Tested source and publication

Published source
[`e114874a934d9662a7d1939c8d0bc5aa7ca080f7`](https://github.com/Omegapy/OntoKin/commit/e114874a934d9662a7d1939c8d0bc5aa7ca080f7)
has exactly the Git tree of tested local commit
`0c56dd41f739d23ccca777473a19622f91ae460d`:
`3f7f14a2d0ac41bbd4c1d61eb2d09ec6f32fa7a7`.
The continuation branch is `work/reach06-recordings-20261023-7of9-e619`;
the original baseline is `6cf8c525429076ce37efd4ecea95fd01f83365ea`.

The latest complete run is `combined-recordings-013`. Every materialized input
matches its committed Git identity before and after execution. P20 uses
**89,767**, L01 **87,281**, and L02 **79,464** operations. Each integration also
retains its preceding complete run and focused tests; the latest numbers do not
replace older source cuts or failed attempts.

| Integrated focused scope | Actual result | Evidence directory |
| --- | --- | --- |
| Mixed native/ordinary P11 sampling | 17/17 passed | `combined-mixed-focused-001` |
| Exact native unit offsets | 61/61 passed | `combined-unit-focused-001` |
| Independent terminal source receipts | 50/50 passed | `combined-source-batch-focused-001` |
| Producer Cartesian products | 29/29 passed | `combined-cartesian-focused-002` |
| Exact tiny interval products | 37/37 passed | `dyadic-tiny-focused-001` |
| Independent Cartesian products | 38/38 passed | `combined-independent-cartesian-focused-001` |
| Integrated dyadic point/division identities | 49/49 passed | `combined-dyadic-identities-focused-001` |

Each listed cohort has zero failures, errors and skips and stable materialized
inputs. Each report identifies its actual source commit and tree. These counts
are not summed or represented as one current full-regression inventory.
Checkpoint011's 137-, 85- and 60-method cohorts, checkpoint010's 227-method cohort,
checkpoint009's 234 methods and the earlier 686 methods retain their identities.

## Integrated work and actual savings

Mixed P11 sampling evaluates its ordinary Y-axis head/eyes before the native
Z-axis carriers at each key, retaining full source classification and final
admission. A 31-key differential saves 3,518 operations while preserving the
checked frames, allowances and binary32 cells. Later Cartesian source products
save another 1,148 operations on the same selected mixed-key measurement.
These measurements are not complete P11 passes.

Independent source plans now defer repeated immutable receipts through one
bounded, callback-free final admission. Numeric cache lookup, eviction, cursor
advancement, reseeding and per-key work still use the original bounded context.
Changed owners or source records reject the proof; a specifically identified
cap-only change replays ordinary validation on the same work. Original callback
exceptions are not swallowed. The independent Cartesian product keeps the
original nonzero interval terms and exact operation order, with fresh guards
and ordinary fallback.

Native positive unit offsets reuse already calculated rotation coefficients.
Dyadic arithmetic preserves exact representable points, integer divisors and
one-cell intervals adjacent to zero without their redundant integer work.
The fixed Taylor/arctangent degree, complete prospective-width guards, source
target bits, tolerances and all public resource limits are unchanged. Actual
P16 admission falls from 10,056 to **7,814** operations; P23 falls from 4,188 to
**3,354**. Complete admission solutions match except actual-work fields, and all
nonconstituent counts are unchanged. Both full requests still exceed the cap.

The numerical implementation identity binds the executed helpers. Current costs
include hashing the larger implementation files. No source fixture, operation
maximum, elapsed-time maximum or 256-entry cache maximum was relaxed.

## P05 correctness blocker and pending correction

The observer at `6b44da0` reproduced P05's certificate failure at 99,898 operations
with the original work counters and stable inputs. Exactly six rows belong to
its final interval, 35/12 to 3 seconds. The writer selected only the moving
positive-width phase. The independent reader also included the outgoing final
point, whose root anchor inherits the completed spin's exposed rotation error.
Each rotation deficit is exactly **2^-50 + 2^-91**. Five descendant position bounds
also omit the resulting path-offset contribution. The later arithmetic-only
integration reaches this same failure at 99,069 operations.

Candidate `13334500e4383e3e6914a427ba6d3e49f4136375` explicitly evaluates
`plan.final_state` at the final point and includes its numeric position/rotation
bounds for groups containing the final key. It does not change sampling,
positive-width phase selection, quarter-allocation inequalities or the reader.
**It is not integrated or accepted.** Its natural-completion test passes, but
the new module passes **5/7 with two errors**: a missing-zero lookup in a new
test helper, and a real short P16 final-release position-bound mismatch.

The release observer shows agreement on rotation. The independent anchor
position interval has a slightly larger extent than the writer's canonical
position. The final claimed position allowance is therefore just below the
independently reconstructed minimum. A conservative enclosure-transfer
calculation and focused tests remain required. Arbitrary padding or a weaker
independent check is not an accepted fix. Original full P05 has not been run on
this candidate.

Pending performance scopes cover repeated actual-source stationary traversal
and independent endpoint arithmetic. They are code/review work, not verified
checkpoint012 improvements. A P09/L03 observer found 208 operations per steady
key comparison, including approximately 102 for the independent pose. Full-angle
vector recurrence is not adopted: its interval update alone costs the same 15
operations as the present rotating-offset factor, before cursor bookkeeping.

## Evidence and recovery

The [machine-readable checkpoint](checkpoint-012.json) lists all 28 current
results, identified cohorts, the pending correction and execution limits.
The [archive manifest](checkpoint-012-manifest.json) binds **859 new raw members**
in **26 parts**, each smaller than 1 MB. The joined ZIP is **22,579,664 bytes**,
SHA-256 `69ff478f12e6ab58a46300a47dfdf975445aeb42a1ffd654d7dd061560bd1ef0`.
Every member SHA-256, ZIP CRC and joined-part identity passed. Concatenate parts
in manifest order, verify the complete identity, then extract.

The archive is incremental. Its 707 unchanged-member references resolve through
the original [checkpoint011 manifest](checkpoint-011-manifest.json), including
that manifest's references to [checkpoint010](checkpoint-010-manifest.json).
All original archives retain their bytes. New material includes every completed
intermediate run, before/after inventories, actual source GLBs, method outcomes,
logs, diagnostics, executed drivers, rejected candidate patches, local commit
objects and exact local-to-published tree mappings.

Three older focused text logs were observed incomplete even though their
structured method results and process reports completed. Their original bytes
and this limitation are retained in `execution/log-completeness-012.json`.
Missing text was not reconstructed. The new driver captures actual unittest
output once, records its length/hash and requires its executed footer; the
latest 49-method run has a complete log. This does not retroactively repair old
evidence or establish release acceptance.

The [documentation check](checkpoint-012-docs.txt) remains separately visible.
Historical binary-archive links unavailable in the sparse recovery keep its
overall status failed. Prior rejected source-template and phase-node candidates
remain rejected; earlier incorrect test assumptions, misspelled test invocations,
interrupted diagnostics and all new failed attempts remain preserved.

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

Finish and test the producer endpoint correction, then rerun original full P05.
Validate subsequent arithmetic/source-reuse changes with targeted correctness
tests before integration and the full 28-recording suite afterward.

After **28/28**, execute Agent delivery, complete regression, CPython
3.11/3.12/3.13, independent rate/native/browser/visual checks, inherited/hostile
roles and every R01–R12/Q01–Q22 requirement under the
[adopted contract](../../language-design/planar-reach-v0.1/ADOPTION.md).
No main integration lease, hosted-job dispatch, paid execution or Actions
setting change occurs at this checkpoint.
