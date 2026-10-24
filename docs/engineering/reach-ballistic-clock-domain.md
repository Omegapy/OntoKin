# Ballistic elapsed-clock range proof

This candidate was prepared source-only from published checkpoint 024 at
`d055612277945ea6822e9ad43c7b4b14f0a544d7`, on
`work/reach06-ballistic-clock-domain-20261023-1bda`. Its scope is the nonzero
elapsed-clock range admission in `ontokin/reach_recording_fast.py`, the dedicated
`tests/test_reach_ballistic_clock_domain.py` cohort, and this derivation.
It does not change a source fixture, horizon, sample schedule, precision,
tolerance, numerical cache, or work limit. The original maximums remain
100,000 operations, 30,000 milliseconds, 32,768 operand bits and 256 numerical
cache entries.

Checkpoint 024 records 329/329 focused integration tests and 23/28 original
recordings. P09, P11, P16, P23 and L03 remain budget failures. Those earlier
results do not execute this candidate. The dedicated execution records below
identify the failed first attempt, its test-only corrections, and the passing
fresh second attempt.

## The repeated calculation and bounded opportunity

The native ballistic sampler already has an exact elapsed Fraction `e` and a
completed source law with exact horizon `H`. Before each sample, it retains the
existing clock-domain charge, native-domain check, actual input guards, and
small-clock admission. It also retains the original `e <= H` comparison.
For nonzero elapsed time it currently follows that comparison with the two
exact orderings `e >= 2^-250` and `e <= 2^250`.

The preserved checkpoint 023 P16 diagnostic, `diagnostic-001/P16.json`, reports
98 `recording_ballistic_clock_domain` entries and 98 corresponding dynamic-law
entries on source `465cf884c58ee54512da4f994bb95b3bae73398e`. That run completed
producer work and failed during independent retained-clock processing. These
counts support a maximum gross opportunity of 196 eliminated range comparisons
on that observed request. They do not establish candidate savings, an unchanged
count on a later implementation, or completion of the remaining independent
certificate work. The original four-second recording remains the acceptance
gate.

This change does not repeat the already integrated exact-zero clock or
constant-hinge optimizations. It proves the range of a live nonzero elapsed
operand without calculating the two rational cross-product orderings. Every
operation that still occurs retains its ordinary charge.

## Exact sufficient proof

Let `e=n/d`, where `n` and `d` are positive native integers. Write
`B=n.bit_length()` and `D=d.bit_length()`. The integer bit-length definition gives

```
2^(B-1) <= n < 2^B
2^(D-1) <= d < 2^D
```

and therefore

```
2^(B-D-1) < n/d < 2^(B-D+1).
```

Consequently, the sufficient condition

```
-249 <= B-D <= 249
```

proves strict membership in `(2^-250, 2^250)`. The proof does not approximate,
decode, normalize, reduce, or replace the actual Fraction. It also does not
claim that every supported elapsed value satisfies this bit-width condition.
Both inclusive boundary values and unsupported width shapes continue through
the original lower-then-upper comparisons, with their original short circuit.
The mandatory horizon comparison remains even when the sufficient proof holds.
The zero elapsed path retains the original direct anchor behavior.

The existing [ballistic finite-domain derivation](reach-recording-certified-planar.md#checked-domain-and-finite-intermediates)
requires at most 1,024 bits in each clock field, the full 32,768-bit operand
domain, and the same elapsed interval. Those conditions are rechecked on the
actual current operand at the omission point. The original native comparison
would guard both operands and then the prospective cross-product width. For
the lower bound the width is `max(B+251, D+1)`; for the upper it is
`max(B+1, D+251)`. Each is at most 1,275 bits under the admitted field bounds.
The helper executes both original operand guards and both prospective-width
guards in order before returning its proof. These original native guards are
callback-free. No cross product is performed and no charge is discounted.

## Live admission, dispatch and fallback order

The helper runs only after the original horizon comparison returns. A callback
at that comparison can change the elapsed numerator or denominator, work owner,
operand cap or dispatch. Admission uses the current fields and current owner
after that callback. No earlier successful range or source-clock result is
retained.

Only exact native recording/work/Fraction types, positive native integer fields,
unchanged literal bound objects and fields, the original comparison helpers,
and original work and field-access dispatch can omit the orderings. Original
class storage is checked before the helper reads an instance dictionary. Work
method overrides, custom descriptors, foreign subclasses, changed bound values,
wider fields and narrower caps decline the proof and leave the original calls
at their original positions. The helper does not invoke a foreign work getter
while deciding whether to decline. In particular, the fallback still binds
the comparison callable before reading its `self.work` argument, as Python did
in the original expression.

A narrower work owner can be installed during the horizon callback. The helper
then declines without eagerly executing a prospective guard. The original lower
comparison's callback can restore the domain before its ordinary guard, or the
ordinary guard can report the original finite-domain failure. The upper
comparison remains part of that complete fallback even if the lower comparison
restores the full domain. A source callback or resource exception propagates
unchanged from its original surviving operation.

The proof introduces no callback, observer, cursor, saved operand or numeric
cache entry. Existing external callbacks and source observers retain their
identity and their order at every surviving charge. The removed comparison
charges and their callbacks disappear with the removed calculations; they are
not simulated or subtracted after execution. Binary64 clock rounding and all
native Horner operations, finite-result checks, structural-zero decisions and
endpoint error allowances remain unchanged.

## Prepared correctness and cost controls

The dedicated cohort covers exact candidate bits and structural
zeros against the complete original comparison path, ordinary and extreme
interior clocks, inclusive boundaries, sufficient-proof soundness against exact
Fraction ordering, negative and tiny rejection, retained horizon rejection,
malformed fields, signed zero, literal-bound mutation, custom module/work/
Fraction dispatch, descriptor evaluation order, callback mutation, live cap and
owner replacement, cancellation identity, observer preservation, unchanged
remaining request budget, and unchanged cache contents and capacity.

The P16 paired control compiles the original `p16.files.json` source and samples
its actual release/force phase from 2 to 3 seconds and coast phase from 3 to
4 seconds. Both paths include fresh construction, simulator initialization,
advance, phase bounds, ordinary phase-start recording setup and all real
callbacks. Each compares the complete returned sampler value and allowance
records, packed binary64 position/orientation bytes, and unchanged source state.
It requires a positive reduction in the complete shared construction budget,
the same reduction in numeric work and actual callback count, and no count
change other than the eliminated exact comparisons.

This is a sampler-level comparison. It does not produce or certify a GLB, an
independent supplied-byte report, or a completed four-second recording. The
usual quarter-second P16 prefix ends before release and cannot measure this
optimization. The dedicated control therefore includes real dynamic samples
and reports its whole setup cost honestly, without increasing a budget to make
the full recording finish.

## Execution and integration handoff

The dedicated module is prepared for the unchanged
`reach_development_probe_v2.py` driver with `--test
test_reach_ballistic_clock_domain`. Its execution requires the coordinator's
exclusive runtime grant, a clean identified source cut, a fresh output directory
outside the checkout, retained stdout/stderr/exit receipt, and before/after
tracked-input identities. Every attempt must be retained.

After source review and the dedicated result, related dynamic, captured-dynamic,
captured-input, native-reuse and source-recovery tests remain required, followed
by the full original 28 recordings on the accepted integrated source. A positive
local saving is not evidence that P16 or any other failed recording now passes.
The Agent, complete regression, Python 3.11/3.12/3.13, independent validation,
native/browser/visual and R01-R12/Q01-Q22 release gates retain their prior status.
Both PRs remain draft and `main` is unchanged by this worker.

## First dedicated attempt and test-only corrections

After independent source review, the coordinator granted one exclusive run on
clean commit `5193ea877eba0d738e12c3cf3a5c2a6fa9203e32`, tree
`4d9a12d1be32979c08fc94a5110f006c08b9b536`. Attempt
`evidence025/ballistic/ballistic-focused-001` ran the dedicated module with the
unchanged driver on CPython 3.12.14. The launch ran from
`2026-10-24T01:00:26.064070+00:00` to `2026-10-24T01:00:29.282228+00:00`
and exited 1. All tracked inputs were stable. Of 22 test methods, 20 passed;
three failure records affected two methods. There were no errors or skips.
The complete 8,762-byte test log has SHA256
`097f46d3df099f6327ef3d11f6b680ff7f6b80ab7be1b13365439c0216485fa3`.
The run directory, sibling stdout/stderr and launch receipt are preserved.

Two failures were the P16 release/coast subtests' comparison of complete
states from independently constructed requests. Complete sampler values and
binary64 bytes had matched, and each request's before/after state equality
had passed. The cross-request mismatch was the explicit `_OwnerRef` tokens
inside `state.dynamic_cells["payload"].lineage`. Those tokens intentionally
retain each request's model, work, pose-ops, source tables and source objects;
their equality is owner identity, and deepcopy preserves that identity.

The corrected assertion compares every other state and CellAnchor field
directly. Within the lineage's explicit model-snapshot layout it compares all
literal source values and shared native method receipts directly, and requires
each corresponding request-local owner to have the same type but a different
identity. Optional `None` payload owners remain `None`. It additionally binds
each header's model/work/pose-ops owners to that actual request. No state field
is broadly normalized or discarded; the original within-request state and
complete sampler/binary64 assertions remain.

The third failure expected a 252-bit prospective-width rejection under a
128-bit cap. The original lower-bound operand guard correctly rejected its
251-bit denominator first. The corrected control covers both a 128-bit cap
with the original 251-bit operand failure and a 251-bit cap with the subsequent
252-bit prospective failure. Both retain comparison with the full original
path, and both also exercise restoration at the original lower-comparison
callback.

The failed run logged whole-request sampler totals of 27,826 versus 27,820
operations for phase 2-3, and 33,161 versus 33,155 for phase 3-4. Numeric work
and callback totals each differed by six as well. The later saving assertions
were not reached after the cross-request equality failure, so these logged
observations are not a passing dedicated result. Production code is unchanged
by the corrections. The fresh second attempt below executes those corrections.

## Passing dedicated execution and integration handoff

The coordinator independently reviewed the test-only correction and executed
`ballistic-focused-002` in a fresh exclusive window. The exact executed source
is `3b66cbcf67da49b9796295f54499be4424e7d078`, tree
`ec1594147679998f9c9ee2a9208bb1c888abc604`. The checkout was clean and all tracked
inputs were stable before and after execution. The dedicated result is
**22/22 passed**, with zero failures, errors or skips. The original failed
attempt remains retained and has not been replaced by the passing result.

The unchanged driver was invoked as follows:

```text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3
/workspace/scratch/1bda36804e7d/evidence023/drivers/reach_development_probe_v2.py
--root /workspace/scratch/1bda36804e7d/OntoKin-ballistic
--output /workspace/scratch/1bda36804e7d/evidence025/ballistic/ballistic-focused-002
--test test_reach_ballistic_clock_domain
```

The launch wrapper is `/workspace/scratch/1bda36804e7d/run_focused_candidate.py`.
The actual child command and its stdout/stderr are preserved beside the run
directory. The launch started at `2026-10-24T01:04:24.967126+00:00`, finished at
`2026-10-24T01:04:27.199722+00:00`, and exited 0 after 2.233 seconds. The reported
environment is CPython 3.12.14, Clang 22.1.3, on
`Linux-6.18.55-x86_64-with-glibc2.39`. The driver SHA256 is
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.

| P16 sampler phase | Original whole request | Candidate whole request | Original numeric work | Candidate numeric work | Eliminated comparisons |
| --- | ---: | ---: | ---: | ---: | ---: |
| Release/force, 2-3 seconds | 27,826 | 27,820 | 23,466 | 23,460 | 6 |
| Coast, 3-4 seconds | 33,161 | 33,155 | 28,801 | 28,795 | 6 |

Whole-request counts include construction, simulator initialization, advance,
phase bounds, recording setup and every actual callback. Callback counts equal
the displayed whole-request totals in both controls. Each completed control
asserted identical complete sampler values and allowances, identical packed
binary64 output, unchanged state within each request, equal source-state values
with explicit distinct request-owner receipts, and exactly six fewer operations
and callbacks. No other counted operation changed. The original 100,000/
30,000-ms/32,768-bit/256-entry limits remained unchanged.

The retained directory is
`/workspace/scratch/1bda36804e7d/evidence025/ballistic/ballistic-focused-002`.
It includes the executed drivers, before/after input identities, structured
test results, complete log and report. Its sibling files retain the launch
receipt and stdout/stderr. Exact evidence identities are:

| Evidence | SHA256 |
| --- | --- |
| `tests.log` (5,145 bytes) | `3ba0f07f07d34bd4e91f31a68ccf8b6843ffeaa2f69fd507acb4f93ae9f238bd` |
| `tests.json` | `43e98bb50f79c6bdc1dd79f4ddd78ab91b4c611f9064cc61323cf07e8a612214` |
| `report.json` | `e0c2bc037e9a93b970502f010e106dd01a75c4fd530d98d0b150ec638fcef09b` |
| `ballistic-focused-002.launch.json` | `011431f5a4c8d2e4de491edb8e43a582aeda5a6bc48109964231be5b0cdaa705` |

This passing result establishes only the dedicated cohort on its identified
Python 3.12 source cut. It is not a full-recording result, independent GLB
acceptance, release input-closure attestation, compatibility matrix, or completed
release. The coordinator owns publication and fresh related tests plus the
original 28-recording suite on the accepted integrated source. No additional
worker runtime was performed after the second execution.
