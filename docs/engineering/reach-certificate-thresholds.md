# Independent per-member certificate thresholds

Development scope: the existing supplied-byte certificate batch in
`ontokin/reach_conformance.py`. This candidate starts from `d2169986` and is
**not integrated** at this worker checkpoint. The execution record below
identifies its tested source and remaining failures. The original 28-recording release gate, all
tolerances and the 100,000-operation limit remain unchanged. This document
states the proof, its validation obligations and the measured development results.

## Existing work and the omitted operation

Every adjacent-key/carrier row still obtains its independently computed source
phase bounds, actual stored arc, endpoint position and orientation errors,
time shift, geometry bounds, and numeric source bounds. Every supplied row is
still checked for its own identity, source phase coverage and exact clock
widths. The implementation does not reuse the writer's certificate grouping.

The existing batch holds at most 64 groups of identical reported quantities.
For a repeated group it previously calculated an exact maximum of each
changing independent minimum before comparing that maximum with the reported
quantity at flush. Equal reduced fractions already avoided this comparison.

The proposed change discharges a fresh, changing minimum directly when a
strict sufficient inequality establishes that it is below the actual reported
quantity. That occurrence no longer needs an exact maximum. The retained
maximum still covers every non-discharged occurrence and is compared normally
at flush. The reported quantity is a threshold for an independent proof; it
never replaces the independently calculated minimum. The initial member is
retained normally. Width, stored width and magnitude always retain their exact
maxima because they enter the later nonlinear inequalities.

## Native exponent proof

Let the current nonnegative independent minimum be the native fraction
`m = b / d`, with `d > 0`. For `b > 0`, if `B` and `D` are the native numerator
and denominator bit lengths, then

\[
0 < m < 2^{B-D+1}.
\]

The actual positive reported quantity `q = n / e` was independently decoded
from a finite binary64 or integer. Its sealed denominator is explicitly
required to be a power of two. Writing `N` and `E` for its field bit lengths,

\[
q \ge 2^{N-E}.
\]

Consequently `B-D+1 <= N-E` proves `m < q`. Zero also satisfies the inequality
when `q > 0`. Neither power is constructed. No rational product, subtraction,
normalization, float approximation, or assumed writer bound establishes the
inequality: only exact native integer fields and their bit lengths do.

The sufficient domain uses native `Fraction` objects with native integer
fields of at most 2,048 bits and a positive denominator. This is a smaller
domain than the existing 32,768-bit cap. Before omitting an exact maximum the
implementation admits **both** its retained old operand and fresh operand,
including the original prospective cross-product bit lengths. It also admits
the direct fresh/claim comparison domain. A scalar fitting individually is
insufficient. Unsupported fractions, zero claims, negative minima, insufficient
gaps, wider operands and narrower live domains retain the ordinary exact
maximum and flush comparison.

An omitted occurrence can still have larger integer fields than the retained
exact maximum. Each existing group therefore also keeps, per discharged field,
lower and upper native numerator and denominator bit lengths for the positive
possible original maxima. The original running maximum must be either the retained exact
maximum or one of the discharged occurrences. This bounded metadata envelope
admits every possible original prospective comparison against each subsequent
minimum, including wider unsupported inputs, and against the actual claim at
flush. Admission runs before and immediately after a surviving exact compare,
so a narrowed cap cannot pass through a smaller retained operand and then be
restored by a later callback.

The upper envelope is intentionally conservative: its widest fields may belong
to different discarded occurrences or to a discarded value that would not be
the original maximum. If the upper envelope fits, every original continuation
fits. If even the lower widths fail and equality is excluded, every possible
original maximum comparison would fail. A scalar failure retains its position
before the original comparison callback; a prospective-product failure is
checked after that callback returns, preserving its exception and any live
domain change. Zero is removed from the possible maxima once a positive
minimum occurs; this allows an isolated discarded positive maximum to retain
its exact width obligation. The original maximum also skips comparisons for
equal fractions. When the width envelope cannot exclude equality, a failing
prospective domain requests exact replay instead of rejecting. Flush has no
equality shortcut and always admits the original comparison domain.

An inconclusive envelope requests complete exact replay instead of adding a
new rejection. A distinct exact-identity signal belongs to the active batch
and records that the batch actually requested it. The supplied-byte verifier
then rebuilds every endpoint and certificate accumulator with only the
threshold optimization disabled, on the same remaining request work. The
threshold replay retains the actual arithmetic and batch objects, their live
dispatch, and the originally decoded and admitted tolerances; it clears only
provisional result accumulators and uses a new recording context. Thus an
instance-level comparison replacement cannot disappear when the replay starts,
and mutable options cannot silently supply new tolerance inputs. This differs
from an initial source-domain-only restart, which retains its existing ordinary
reader reconstruction. If source admission also declines after threshold
replay, that replay still retains its actual arithmetic owner. Original
callback exceptions, including a caller-created instance of the private
restart type, are not interpreted as this request. Before abandoning an active
source batch, the verifier precharges and admits that batch's original source
receipt ledger. A changed source cannot become a newly captured premise for
the replay. The existing independent source restart remains in force; a source
domain restart while admitting an abandoned threshold batch disables both
optional scopes on the same request. Each optimization can be disabled only
once, so the replay loop cannot retry indefinitely.

There is no enlarged operand limit or additional numeric cache. Within the
original full cap and the 2,048-bit sufficient domain, every envelope
comparison is at most 4,096 bits, so it needs neither a new rejection nor replay.

## Ownership, callbacks and storage

The existing charged member inspection remains. Its bounded temporary receipt
records exact typed reported values, including binary64 bits, all current
minimum fields, authored/stored widths, magnitude and the original arithmetic
owner. These fields are captured before that original callback. Every
remaining exact maximum on native fractions has one original cancellation
callback. The original comparison and its prospective resource guards execute;
immediately afterward the original operand fields and member receipt are
checked. An original callback or resource exception is never translated. An
observed narrowed operand cap disables the optional proof for the rest of that
member, even if a later callback restores it.

The sufficient domain also requires the native batch maximum, arithmetic
compare/bits/value/tick and work charge/guard dispatch. Initial foreign dispatch
keeps the ordinary reader. A later dispatch departure latches the optional
proof off; if the group already discharged any minimum, it requests the owned
exact replay so the changed operation and its exception still execute. This
optional departure is separate from a changed source or numeric operand, which
invalidates its receipt.

The threshold proof itself invokes no cancellation callback and allocates no
cross product. Its field/domain admission is checked again before accepting
the sufficient inequality. Input mutation cannot supply one value to the
member admission and a different value to this optional proof.

Receipts for the already decoded common reported quantities and the retained
exact minima, width, stored width and magnitude live only in the existing
groups. Retained values are resealed only after legitimate exact maximum
updates, so a callback cannot erase an earlier hostile minimum or change a
retained width or magnitude before flush. These receipts
are bounded metadata; there is no additional numeric
result cache, group allowance, retained per-row history, or request work
budget. When a group has discharged at least one member, its unchanged flush
algebra reads detached native copies of those reported quantities and its
retained width, stored width and magnitude. The live group fields remain bound
to their original exact receipt. This prevents live quantity or extent aliases
from changing the threshold or the quantities used by the
complete inequalities. The original complete inequality algorithm, its
nonnegative domain checks and its existing arithmetic callbacks remain.

This optimization does not replace the final independent source-batch
admission. A changed live source still rejects or follows the existing complete
same-request source replay; the per-member threshold establishes only its
current numeric inequality.

## Required evidence

Dedicated tests must cover strict exponent boundaries, zero and exact equality,
non-dyadic independent minima, underreported later minima, all 13 actual
minimum fields, unsupported or wider inputs, narrow prospective old/fresh
domains, callback exception identity, operand/quantity/owner changes, and
narrow-then-restore callbacks. Group limit/flush behavior, exact widths and
destination magnitude failures must remain. Source-prefix exports must retain
identical bytes and complete independent validation reports under an exact
maximum control; forged supplied-byte certificate quantities must still fail.

Execution must identify the exact source/tree and stable input hashes. A
neutral per-field observer should attribute actual omitted comparisons on the
unchanged original recordings, with complete work counts/diagnostics matching
its unobserved run. No recording-level saving or release success is claimed
before those executions.

## Executed development checkpoint

The corrected candidate was executed on
`d89c2ff3fafaf0a0d72e35ee123158f5e4ed5b66`, tree
`dfac6c27a568e8f435aeaac27695377c11f5eae3`, using CPython 3.12.14 and the
unchanged sparse development driver with SHA-256
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.
Each run retained stable before/after input snapshots and the exact source
identity. The 37 historical unmaterialized binary archives remain explicitly
disclosed; this is not release input closure.

| Raw run | Result |
| --- | --- |
| `certificate-threshold-focused-001` | 36/37 on `cb6bc6dc`, with one control-reachability assertion failure; full failed output retained. |
| `certificate-threshold-focused-002` | Corrected dedicated cohort: 37/37, no failures, errors or skips, complete log. |
| `certificate-threshold-combined-001` | 206/206 relevant methods including the dedicated 37, no failures, errors or skips, complete log. |
| `certificate-threshold-originals-001` | Original P09, P11 and L03 all still exhaust the unchanged 100,000-operation cap at 100,001. |

The first failed fixture supplied `(2^400-1)/2^400` below a claim of one and
therefore correctly omitted the comparison whose callback the test intended
to reach. The separate test correction uses `(2^400+1)/2^400`, requires that
callback and verifies the original 913-bit prospective failure under a
500-bit temporary cap. A separate production correction preserves prospective
guard ordering after the original comparison callback. No production numeric
limit or expected acceptance result was relaxed.

The actual quarter-second source-prefix differentials retain identical GLB
bytes and complete independent validation reports. P09 uses 35,940 operations
versus 36,067 with exact maxima (127 saved); P11 uses 61,559 versus 61,591
(32 saved); L03 uses 31,623 versus 31,666 (43 saved). These are prefix results
on this worker source, not complete-recording savings or results from the
newer continuation integration.

At the full-request cap, P09 has charged 1,152 independent key/carrier checks
and 1,146 certificate members; P11 has charged 480 and 457; L03 has charged
828 and 821. A charge can precede an unfinished operation, so these are partial
progress counters. No complete supplied-byte proof or accepted recording is
reported for these three requests. Neutral full-recording per-field attribution,
latest-source integration and the complete original 28-recording suite remain
pending with the coordinator; no overall release gate is closed here.

## Continuation integration

The coordinator reviewed the tested production and test bytes at `d89c2ff3`
and the documentation-only worker handoff `b60f932e`. The existing continuation
has no intervening changes to `reach_conformance.py`. These three files are
integrated after checkpoint021 before separate current-source 206-method and
complete original28 execution. Worker prefix savings and capped progress do
not establish an integrated recording result. All failed attempts remain in
checkpoint021; mandatory release gates and the unchanged operation cap remain.
