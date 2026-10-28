# Private centered recording proof

This candidate is not integrated acceptance evidence. The initial code-only
checkpoint `1e3da520ed03f35db6a761d04218c639b3a6febd` contained a private module
without a reader call site. The subsequent development connects its distinct
private API to the complete supplied-byte endpoint reader; its focused tests
and unchanged original recordings now have separately identified execution evidence in [checkpoint019](reach-recording-validation-2026-10-23/checkpoint-019.json). The integrated292-method cohort passes; the full original suite remains23/28.
The existing public interval observation API, tolerances, 100,000-operation
allowance, 32,768-bit operand cap, 256-entry caches and 64-update reseed limit
remain unchanged.

The design continues the independently archived derivation in checkpoint 014,
`git/candidates-014/reference-center-derivation-only.patch`. The neutral
observer `diagnostics/reference_plan_observer_v1.py` was run against source
`9ace186c27be5ea71cb26984a2c56455fca88dbe` with the original P09, P11 and L03
requests. All three retained their complete unobserved work, diagnostic and
operation counts and still exhausted the unchanged operation allowance. Their
evidence is in `evidence/reference-plan-observer-001` and
`evidence/reference-plan-observer-002`; this observation is not a centered
candidate performance measurement.

## Distinct private representation

`_CenteredPose` carries an exact grid position and quaternion center together
with separate Euclidean error radii. It is not an `Interval`, and no public
pose observer may return it. The intended consumer is an optional sufficient
endpoint proof inside an existing complete supplied-byte source batch. An
unsupported domain or insufficient inequality must request the original full
independent enclosure on the same work context.

The initial source domain has static exact root translations with L1 norm at
most 64 and exact identity root orientations. All local attachment rotations
are identity. Local offsets are exact 128-bit-grid source vectors with L1 norm
at most one, except for the separately proved identity translations below. The existing independent body recipe proves the Cartesian
right-action and complete affine source rate. Independently computed seed
cells must prove that both inactive quaternion components are exactly zero;
merely containing zero is insufficient. The complete source graph, state,
claim, action and owner receipts remain subject to final batch admission.

No producer pose, derivative, numerical allowance, host transcendental result
or prepared recording answer supplies a center or radius.

## Quaternion recurrence

Let `g = 2^-128`, `E = 2^-112` and `R = 2^-104`. The two active components of an
independent direct seed or Taylor increment must have grid-aligned endpoints
whose interval widths sum to at most `E`. Choosing their lower endpoints gives
a point at Euclidean distance at most that sum from the true enclosed pair.
An exactly zero radius is available only when every actual seed width is zero.

For a true unit complex orientation `u`, its center `c`, a true unit increment
`d` and the independently enclosed increment center `a`, suppose
`||u-c||2 <= r` and `||d-a||2 <= E`. Four exact point products and two Hamilton
sums/differences form `c*a`; flooring only its final two components contributes
Euclidean error at most `2g`. Unit complex multiplication is an isometry, so

```
||u*d - floor_g(c*a)||2 <= r + (1+r)E + 2g.
```

This uses the Euclidean isometry; it does not treat an L1 componentwise
recurrence as an isometry. From an admitted direct seed `r0 <= E`, at most 64
updates satisfy

```
rn <= 2E + 128(E+2g) = 130E + 256g < 256E = R.
```

The bound follows from `(1+E)^64 <= 1/(1-64E) <= 2`. Increment clocks may change
provided each independently computed increment meets the same width bound.
A cursor with nonzero accumulated radius must retain its actual update count;
it cannot be relabeled as a fresh zero-step seed. Rewinds, changed source
witnesses, missing/evicted cursors and the existing 64-step limit use direct
independent seeds again. Zero-rate cancellation preserves the old radius.

## General small offsets

The true quaternion is independently unit. Its approximate center is not
assumed unit. Decompose the exact source offset into its axis component and
its orthogonal-plane component. Compute the two planar coordinates from the
raw Hamilton expression `c*v*c*`, retaining exact intermediate factors and
rounding only the final coordinates. Keep the exact source axial coordinate.

Projection cannot increase Euclidean distance. Quaternion norm
multiplicativity therefore bounds the planar error by

```
(2R + R^2) * ||v_perp||2 + 2g < 4R,
```

because `||v_perp||2 <= ||v||1 <= 1`, `R < 1` and `2g < R`. A purely axial
offset is exactly fixed by the true source rotation, regardless of the
center's norm. This is an explicit source identity rather than normalization
of a center.

Every exact grid position addition is exact. Compile a conservative count `k`
of every nonzero attachment offset on the ancestry, including paused or
completed nonzero-angle hinges. Then `k*4R` bounds position error. A zero-radius
exact identity or axial-only step can retain its parent's honest radius.
Depth at most 128 and root L1 norm at most 64 bound position-center magnitude
below 256; quaternion/offset bounds alone would not bound an arbitrary root.

## Bounded translations under exact identity parents

The new candidate admits a larger local offset only when its independent
source ancestry proves exact positive identity orientation throughout the
current source plan. The admitted root already has exact identity orientation
and no orientation action. Identity site/follow/fixed/grip transforms preserve
that fact. A hinge preserves it only when the existing `identity_relative`
recipe proves a zero child origin and an identically zero coordinate law.
That recipe checks both affine endpoints, including paused laws; a zero rate,
a sampled identity center or cancellation of nonzero rates is insufficient.

Such an offset must still be an exact native 128-bit-grid vector, now with
L1 norm at most 64. Preparation retains a typed, sealed requirement for exact
identity transport in its source-only recipe. Evaluation freezes the actual
parent pose and requires quaternion `(1,0,0,0)` and orientation radius zero.
The check also precedes a stationary-pose cache hit and is repeated at offset
use after any body update. Radius, source and owner mutation retain the
existing callback and final source-batch rejection behavior.

For this domain, the true rotation is exactly identity, so transporting the
offset performs no quaternion products and adds zero position error. The
parent's honest position radius survives unchanged. Every offset transported
by an uncertain rotation still has L1 norm at most one and uses the unchanged
`4R` proof. Counting all nonzero offsets remains conservative even when some
larger exact offsets add no error.

To preserve the original finite position premise, preparation sums the root
L1 norm and every local offset L1 norm along each ancestry, using the existing
guarded arithmetic. Each sum must be at most 192, the former root bound 64
plus at most 128 unit offsets. Euclidean triangle inequalities give true
position norm at most 192; accumulated error is at most `128*4R`. Therefore
the center remains below 256 and retains the existing native numerator and
denominator limits. This is a sufficient domain for optional evaluation;
larger cumulative extents use the original full independent intervals on the
same work context.

## Actual supplied endpoints

For stored position `x`, center `c_p` and radius `R_p`,

```
||x-p||2 <= ||x-c_p||1 + R_p.
```

For a true source unit quaternion `q`, an antipodally aligned center `c_q`
and nonzero stored raw quaternion `x`,

```
||x/||x||2 - q||2 <= 2 * (||x-c_q||1 + R_q).
```

A bound at most one half proves the raw norm is nonzero. Actual adjacent-row
certificate claims are only comparison thresholds; they supply no expected
value or radius. A completed sufficient result must bind the center, radius,
typed actual supplied vector, current cap and claim. A failed sufficient
comparison invokes the original interval/normalization proof on the same
work. Stored-arc checks, continuous certificate inequalities, fresh supplied
bytes, source history and final source admission remain mandatory.

## Arithmetic and callback obligations

Every performed exact scalar product, sum, difference, final grid floor,
endpoint difference and bound addition is charged and prospectively guarded.
Skipped corner products do not execute: the private mathematical object is an
exact point with a separately proved radius. Source recipe captures contain
source operands and static radius counts, never a second numeric pose table.
Numeric cursors and any completed stationary pose remain in the existing
bounded arithmetic cache; no side ledger recovers evicted numeric values.

Native Fraction operands are copied from their integer fields before new
arithmetic callbacks. Live operand/record receipts are rechecked after every
remaining callback, including cache synchronization. A cap or precision change
invalidates that optional attempt even if a later callback restores it.
Source and owner changes must reject rather than be relabeled as domain
fallback. Original callback exceptions propagate. Existing pending-cursor
publication must reject nested writers and must not publish partial centers.

Source capture also detaches admitted native Fraction/Interval/tuple leaves
from the live source. The complete typed integer-field signature is saved at
capture, before later arithmetic callbacks. Thus the unchanged independent
direct/Taylor formulas consume captured operands even if a live source object
is temporarily mutated and restored. Final centered batch admission compares
both those copied receipt values and fresh live source values with the saved
signature. It does not rely solely on equality of two aliases to one Fraction.
No additional evaluation or producer arithmetic enters this source copy.

The inherited direct/Taylor oracle keeps its original check callback and
operation charges. A scoped private observer runs after each of those original
callbacks, before the inherited arithmetic continues. Precision, scale and
owner changes reject at that boundary. Operand-cap departures are latched but
do not preempt the oracle's own prospective finite checks: an actual original
resource error must still propagate unchanged. A successful oracle return
after any cap departure declines the optional center. The observer is captured
before the caller callback and restored only while still owned, so replacing
it or reentering cannot silently remove or overwrite that admission.

Fresh source signatures retain the original 16-field outer record, eight-item
nested tuple and three-level nesting limits; native interval endpoints add no
tuple depth. Fixed center/cursor vector arities and native leaves are admitted
before sealing. Changed source or cached records therefore cannot turn a new
metadata comparison into an unbounded recursive traversal. Endpoint claim
decodes, comparisons and magnitude additions also expose their separate
original callbacks to the same live admission, so a later callback cannot
restore an earlier narrowed domain unnoticed.

Completed stationary centered poses are included in the existing rejection
ledger alongside body cursors. A rejected optional attempt discards owned
centered writes; final batch rejection also removes them. The ledger is never
consulted to recover a numerical value after LRU eviction. Successful endpoint
position/orientation receipts are retained only in the already required
endpoint result map, with the center and radius in their complete typed seals.

Required validation includes finer independent oracle containment; exact
point-kernel differentials; 0/1/63/64/65 updates, rewinds and eviction; all axes
and signed/axial/general offsets; narrow or nongrid source domains; truthful
cold radii; mutation/restore, cap, owner and nested-reader boundaries; tight and
hostile supplied endpoint claims; unchanged public observations; real source
prefix bytes and independent supplied-byte checks; and the complete unchanged
original recordings. The checkpoint records each actual execution and failed attempt; this derivation alone does not establish release acceptance.

The identity-translation worker cut `e74f2edde0e9f43805a0141ea7e210731bf3c995` passes305/305 methods, including13 dedicated boundary/source/callback tests. Its unchanged full P11 request activates the new domain but still exhausts100,000 operations. Current-source integration and the full original28 remain separate execution obligations.
