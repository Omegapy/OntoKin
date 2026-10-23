# First-release finite-cell envelope: scoped correction design

Status: **the current implementation has passed its complete short P16 export
test and all 21 dedicated methods; original P16 remains operation-budget blocked,
and a test-fixture follow-up still needs execution.** These results identify
`dca4a9045ae28f650deac478c654299a6386d7da`, not an untested follow-up or the
complete recording corpus. The starting implementation is
`115adf5cfb528f65b5ccf9a2640f01b39486d029`. The first proposed domain is a
release from a prescribed ancestry whose root values and action initials still
come directly from canonical source constants. Earlier completed or stopped
root moves/spins are outside this first domain. The ordinary path remains
available for those sources; its finite-cell allowance has not been proved by
this correction.

This is a source allowance correction. It changes no source position,
orientation, velocity, angular velocity, force, native anchor clock, action
clock, recorded key, tolerance, operation limit or cache limit. It does not
replace the mandatory interpolation equations or quarter allocations in the
[quantization contract](../language-design/planar-reach-v0.1/quantization.md).
The underlying physical source bounds remain those in the
[source kernel derivation](reach-source-kernel.md).

## 1. The independently reproduced discrepancy

A test-only P16 source variant moves the release/force statement from two
seconds to one eighth of a second. Its complete original-settings recording
fails the independent source-position allowance check on both the exact old
`6b44da06e9c2303fb916c2a9930b725c0606341e` implementation and the separate
final-after-state selection correction. The latter correctly removes the
rotation discrepancy but leaves the position discrepancy.

The final-position extent difference is exactly

```
11570523268759427 / 5070602400912917605986812821504
```

The independent dynamic source basis uses the supremum of the actual anchor's
finite cells. The producer uses the canonical native anchor tuple. Release
widens an incoming cell by the established source allowance and rounds its
endpoints to binary64; these endpoints can have greater magnitudes than that
native tuple. The extra magnitude is multiplied by `2^-53` in subsequent
publication allowances. It is small but is not identically zero.

Raw failing artifacts and complete input inventories are retained in the
external execution records `final-source-base6b44-release`,
`final-source-1333450-release-observer`, and
`final-source-1333450-release-point`. These remain failed recordings. Their
existence establishes neither an original P16 pass nor release acceptance.

## 2. Why the existing magnitude alone is insufficient

`PhaseBound.max_position_l1_m` bounds the represented source trajectory.
It is not automatically a bound on every independently computed finite
endpoint. A tiny nonzero input can acquire a full outward grid cell in a
later product, quotient or square root. Adding a fixed multiple of the
binary64 source allowance to that magnitude, without a derivation of those
cells, does not establish the required premise.

The proposed proof instead carries a scalar radius for each physical field.
For a true ideal three-vector `x`, a cell box `X` has radius `D` when

```
sum_i max(abs(X_i.lo - x_i), abs(X_i.hi - x_i)) <= D.
```

The same definition applies to four quaternion components, with a coherent
unit ideal quaternion as the center. Each retained radius covers both the
actual and ideal finite boxes. Taking one common radius is conservative;
it avoids retaining eight separate numerical radii. The proof carries no
sampled pose, quaternion components, independent interval object or second
trajectory evaluator.

Temporary ancestry records contain four radii and three upper bounds on the
ideal position, velocity and angular-velocity L1 magnitudes. They are discarded
after the transition. An admitted dynamic anchor retains four radii, three
common actual/ideal-cell magnitude bounds, its proof clock, and immutable source receipts.
This is transition proof state, not an additional numerical-result cache.

## 3. Arithmetic facts and explicit grid accounting

Write `g = 2^-128`, `u = 2^-53`, and `eta = 2^-1075`. The relevant finite
kernel admits rational points exactly, including tiny binary64 components;
it does **not** round point admission to the `g` grid. Every performed outward
addition, subtraction, multiplication or division contributes less than `g`
to each output endpoint. Exact zero and identity branches contribute no more.
Every square-root result, including an exact square and zero, is an integer
multiple of `g`: the algorithm returns `root / 2^128` or
`(root + 1) / 2^128`. Consequently a successful positive square-root lower
endpoint is at least `g`.

For a `d`-component finite vector of L1 magnitude at most `M`, monotone
binary64 nearest-even endpoint rounding contributes at most

```
publication_d(M) = u*M + d*eta.
```

An endpoint that overflows remains an error; this inequality does not admit a
nonfinite endpoint. All scalar arithmetic and numerical branches consume the
existing request's bounded work context. Typed structural snapshots are charged
per bounded source row, and the final receipt comparison introduces no callback.

For common radii `D`, ideal magnitudes `M`, and exact scalar `s`:

| Operation | Radius bound |
| --- | --- |
| Three-vector addition | `D_left + D_right + 3g` |
| Three-vector scaling | `abs(s)*D + 3g` |
| Exact component negation | `D` |
| Three-vector cross product | `M_left*D_right + M_right*D_left + D_left*D_right + 9g` |
| Three-vector expansion by `E` per component | `D + 3E + 3g` |
| Four-vector expansion by `E` per component | `D + 4E + 4g` |

After expansion, add `publication_d(M + D_expanded)` if endpoints are rounded.
The cross product has two products and one subtraction per component. The
table counts all of them, even when a supported special case omits a zero.

### Quaternion product

The Hamilton product is submultiplicative in L1. Each unit quaternion has
L1 norm at most two. For radii `D_left,D_right`, the product radius is at most

```
2*D_left + 2*D_right + D_left*D_right + 28g.
```

There are sixteen products and twelve sums/subtractions. A product may retain
dependency overestimation; the radius inequality covers independent choices
of every input component and does not assume those dependencies survive.

### Normalization

For a four-component input box within radius `D < 1` of a unit quaternion,
the exact box norm differs from one by at most `D`. The three additions of
the exact component-square ranges add at most `3g`; the square root adds at
most `g`. A sufficient norm-endpoint error is

```
b = D + 3g/(1-D) + g.
```

If `b < 1`, the normalized quaternion radius is bounded by

```
(D + 2b)/(1-b) + 4g.
```

The denominator is positive by the explicit test. If that test is not
established, successful normalization still has denominator at least `g`,
so a coarse bound is

```
M_input/g + 2 + 4g.
```

The coarse branch can make a recording unprovable at its original tolerance.
It is not permission to claim a useful small bound or to bypass the normal
numeric error when the actual normalization fails.

For an exact nonzero canonical `d`-vector, let `m=max(abs(component))` and
`b=(d-1)g/m+g`. If `m>b`, its normalized cell radius around its true normalized
vector is at most `2b/(m-b)+d*g`, for `d` equal to three or four. Otherwise
the same positive-grid coarse bound applies. Scalar signed quaternion
identities retain an exact zero radius.

### Rotation

Let `Dq` be the quaternion radius, `Dv` the vector radius, and `Mv` the ideal
vector L1 magnitude. A sufficient bound covering both the two-Hamilton-product
expression and the direct Cartesian-axis factor expression is

```
4*Dv + (4*Dq + Dq*Dq)*(Mv + Dv)
      + 8g*(Mv + Dv) + 100g*(1 + Dq).
```

The factor four on `Dv` is deliberate. Two successive interval Hamilton
products can lose the correlations that would permit the true rotation's
smaller L1 operator bound. Assuming that proper-rotation bound for the
intermediate boxes would be unsound.

For the general expression, the first product's `28g` is multiplied by a
quaternion with L1 at most `2+Dq`; the second product adds `28g`, for a total
at most `28g*(3+Dq)`. For the Cartesian factor expression, each squared,
cross or summed coefficient has endpoint rounding error at most `3g`.
Across all output rows its contribution is at most `6g*(Mv+Dv)`, and the
remaining output products and sums add at most `7g`. The displayed bound
dominates both. The nonlinear quaternion term follows directly by expanding
`(q+delta_left) * v * conjugate(q+delta_right)` and bounding L1 products.

### Finite sine and cosine cells

The Machin enclosure's exact alternating tails are less than `g/256`.
Accounting for both arctangent output grids and the two scales/subtraction
gives a pi endpoint error less than `24g`; its lower endpoint exceeds two.
For a half-angle box whose endpoints are within `H` of the true half-angle,
let `K` bound the absolute selected quadrant. It is sufficient to take
`K = M_half_angle + H + 1`. Outward reduction adds at most `12*K*g+2g`.
The exact midpoint Taylor tail is less than `g/256`; sine and cosine are
globally 1-Lipschitz. A conservative common output endpoint error is

```
epsilon = 2H + (24K + 6)g.
```

This retains the large-angle term. No fixed small-angle approximation or
host transcendental function is used in the proof.

### Spin and hinge quaternion radii

For an angular-velocity box with common radius `Domega`, true L1 magnitude
at most `Momega`, and a positive true norm lower bound `l > Domega`, set

```
dnorm = Domega + 3g/(l-Domega) + g.
```

If `l > dnorm`, a normalized-axis radius is

```
Daxis = (Domega + 2*dnorm)/(l-dnorm) + 3g.
```

At exact elapsed `t`, use `H=abs(t)*dnorm/2+g` and the sine/cosine rule above.
The resulting spin quaternion radius is at most

```
Daxis*(1+epsilon) + 3*epsilon + 3g.
```

A useful source-only lower bound is `l=max(abs(native_omega))-Eomega`, where
`Eomega` is the existing proved Euclidean source error. Its corresponding
upper bound is `Momega=L1(native_omega)+2*Eomega`.

If the positive tight branch is unavailable, use
`dnorm=Domega+2^-63+g`, because `sqrt(3g)<2^-63`, and the successful-divisor
grid bound. A universally conservative quaternion radius is then

```
(1+epsilon)*(1+(Momega+Domega)/g+3g) + 2 + 3g.
```

This also covers a zero true angular velocity with nonzero finite actual
cells. Exact zero elapsed or an exact zero angular-velocity box can retain
the exact identity shortcut. A hinge uses its independently normalized
canonical axis and the source coordinate discrepancy in `H`; its raw-axis
actual angular-rate discrepancy is included in the common omega radius.

## 4. Complete first-release ancestry

The first proof must capture the complete selected child's actual dependency
path: object, parent frame/site, follow or joint, coordinate law, child-site
inverse, and the root's separate translation and orientation laws. Admission
includes source collection identity and membership, active grips, selected
source record identities, typed finite operands, canonical source constants,
complete claims and action clocks, and arithmetic/model/state ownership.

An ancestry root is eligible only if:

- it is prescribed and has no dynamic anchor;
- every move/spin targeting it is pending or is the currently claimed running
  or paused action; no completed or stopped move/spin is admitted;
- its retained positions/orientations are still the exact canonical placement,
  ideal position is its exact rational value, and no private rotation latch
  or inherited rotation error is present;
- any active move/spin's complete initial operand is that same canonical
  placement, with the expected ideal initial and zero inherited rotation error.

This condition excludes earlier no-op latches too. Equality of the latest
canonical tuple alone is not proof of equality of its finite-cell history.
All five model source tables together contain at most 256 records, each
relevant state table contains at most 256 records, the ancestry contains at
most 256 nodes and its active traversal depth is at most 64. These are optional
proof-domain ceilings; larger ordinary source graphs keep their existing path.
All source tables and the ancestry walk are bounded before copying. The
optional proof retains no extra cross-clock node or numerical cache.

The recording planner is a subclass of the ordinary source simulator. It
overrides only pose-finiteness observation and snapshot presentation; its
source and transition equations are inherited unchanged. Eligibility therefore
requires the exact ordinary implementations of the fixed native source,
numeric, boundary and transfer method list, rather than an exact simulator
class name. Instance method shadows, foreign method overrides, custom
attribute access and descriptors for context-owner fields are unsupported.
Resolution reads raw dictionaries along the bounded method-resolution order;
it does not invoke a descriptor's class accessor, which could disguise a
different instance method or context owner as the expected class value.
The actual simulator class and every admitted function identity enter the
lineage receipt and are rechecked after all callbacks. The source class may
not change during a proof even if its replacement inherits the same methods.
Unknown overrides retain the ordinary path before admission; changes after
admission reject the in-flight proof. No export method or observation hook is
changed by this allowance helper.

Every identity leaf in the source, method and state receipts retains its
actual owner strongly. An immutable one-owner tuple compares the contained
objects with `is`; it never invokes a model's value equality. A bare numeric
address would be insufficient because a callback could remove an owner and
allow its address to be reused by an equal-valued replacement. The current
dynamic state, its eight source tables and the four current anchor/error/force
owners use a fixed strong tuple and the same elementwise identity rule.
These changes add no numeric operation, alter no witness value and keep the
existing charged source-row counts.

The persistent `CellAnchor` lineage retains only the bounded model, current
arithmetic owners, class/storage/method identities and the admitted model
tables/records/poses. First-release state tables and dynamic-transfer owners
are held by temporary guards only; no historical state or anchor chain enters
the persistent lineage. Copy and deepcopy of an owner token return that token
itself. Copying a saved state therefore keeps the model authority shared while
copying the ordinary mutable state and its native anchor as before. It cannot
clone a model, arithmetic context or callback through a receipt. The existing
numeric witness must still match the copied native anchor before use.

Primitive poses use the explicit scalar, normalization, hinge and spin rules.
For composition, ideal magnitude bounds may be deliberately coarse because
they multiply cell radii; they must not replace the dynamic source speed.
Let the true rotated local offset have magnitude at most `2*M_local_position`.
Then the four output radii are:

```
D_offset = rotate_radius(parent.q, local.position)
D_position = parent.D_position + D_offset + 3g
D_orientation = hamilton_radius(parent.q, local.q)
D_velocity = parent.D_velocity
             + cross_radius(parent.omega, offset)
             + rotate_radius(parent.q, local.velocity) + 6g
D_omega = parent.D_omega
          + rotate_radius(parent.q, local.omega) + 3g.
```

Both actual and ideal coordinate inputs are covered. Current scalar source
allowances remain in force; a cell radius does not erase an existing source
error. The final source/owner/cap admission is callback-free and occurs after
all arithmetic and publication callbacks. Failure cannot publish partial
proof metadata or use a mixture of pre- and post-mutation inputs.

## 5. Release and dynamic transfers

Let `E_position,E_rotation,E_velocity,E_omega` be the already established
incoming source allowances. A release expands the incoming actual finite
box by each corresponding allowance and rounds endpoints; the quaternion
also normalizes. The ideal box is retained. The expansion/rounding/normalizing
rules above produce a common radius covering both. The actual source's native
materialized anchor remains unchanged.

For each three-vector field, the actual native tuple differs from the true
ideal vector in Euclidean norm by at most its established source error `E`.
Since `sqrt(3)<2`, an actual finite-cell magnitude bound is

```
M_cell = L1(native_tuple) + 2E + D_common.
```

This bound uses the actual tuple and a proved radius; it does not inflate
source rates by substituting a coarse ancestry L1 magnitude. Dynamic source
formulas take the maximum of their existing native expression and the
cell-based expression. The latter uses the retained **proof clock**, while
the native trajectory keeps its original clock.

At elapsed `t`, dynamic point-cell radii are bounded by

```
D_position(t) = D_position(0) + abs(t)*D_velocity(0)
                + Ea*t*t/2 + 12g
D_velocity(t) = D_velocity(0) + abs(t)*Ea + 6g
D_omega(t) = D_omega(0),
```

where `Ea` is the L1 discrepancy between canonical and ideal accelerations.
Orientation uses the spin/product recurrences. The ideal acceleration itself
is exact; the common recurrence also covers the actual acceleration.

All later transitions of an admitted anchor must be handled:

| Transition | Required envelope/error update |
| --- | --- |
| Changed canonical force acceleration | Evaluate old point radii, round actual position/velocity/omega cells, and normalize the rounded ideal quaternion expanded by the old rotation allowance. Retain the old point source errors, new magnitude bounds and new proof clock. |
| Equal canonical acceleration | Retain evaluated point cells and the native trajectory anchor. Add the maximum of the existing exact publication discrepancy and `publication_3(M_actual_point_cell)` to position/velocity source errors; retain the established rotation increment. Move only the proof clock and scalar proof state. |
| Nonzero impulse | Start from ideal point cells, apply the established expansions, actual lever/cross/scales and endpoint rounds, and the corresponding ideal operations. Bound each resulting stored actual-versus-ideal vector distance by `2*D_common+3g`; the three subtraction cells contribute the final `3g`. Take the maximum with the existing physically derived impulse error. |
| Zero impulse | Retain the previous anchor, errors, proof clock and proof metadata unchanged. |

For impulse, the lever allowance remains exactly the adopted source formula
`E_rotation*L1(point_self)+2^-96`. Its ideal rotated point uses the rotation
radius rule. Every cross product, inverse mass/inertia scale, vector sum and
actual binary64 endpoint round is counted. No impulse response or source
history record is rewritten by this proof.

After the initial release, common magnitude bounds can advance directly to
the new proof clock with the same `12g`/`6g` ballistic operation counts.
Their acceleration magnitude is the maximum of the exact canonical and ideal
L1 acceleration magnitudes, so both sets of point cells are covered. Changed
force additionally applies the endpoint rounding magnitude bound. Equal force
retains those newly evaluated point magnitudes. Reusing the older unchanged
native anchor tuple as if it were a tuple at the new proof clock would be
incorrect; the native anchor itself keeps its original clock and values.

### Bounded outward representation of proof scalars

The recurrences above define conservative real upper bounds. Retaining every
exact rational quotient indefinitely is unnecessary and can exceed the fixed
32,768-bit operand ceiling during repeated normalization and transfer. Proof
radii and magnitude bounds therefore use a fixed `h = 2^-256` grid:

```
U(x) = ceil(x / h) * h, for x >= 0.
x <= U(x) < x + h.
```

Exact zero and values already on this grid remain exact. Each rounded radius
or magnitude is an integer multiple of `h`, so its reduced denominator has at
most 257 bits. The numerator, all source operands and every prospective
arithmetic intermediate still face the unchanged operand ceiling. This is not
a guarantee that every legal source input or coarse fallback bound fits.

The code applies `U` to scalar radius primitive results, the intermediate
upper norm-error terms, completed ancestry/transition envelope fields, and
retained cell-magnitude bounds. An exact recurrence is evaluated on
the current conservative inputs before this upward rounding. Its local added
slack is less than `h`; subsequent recurrences propagate that slack through
their existing formulas. No unproved fixed total-slack estimate is substituted.

Every polynomial bound uses nonnegative coefficients and operands. Increasing
an input radius or magnitude therefore preserves the bound. For the tight
normalization branches, an upper `b` is used in both the numerator and the
**exact** subtraction `1-b` or `m-b`. The explicit positivity test remains;
increasing `b` enlarges the numerator and decreases the positive denominator,
so the quotient is conservative. Likewise, spin uses an upper `dnorm` in the
numerator and the exact positive subtraction `l-dnorm`. If upward rounding
prevents a positivity test from succeeding, the existing coarse branch is
used. No lower bound or denominator is rounded upward.

Signed source values, coordinate laws and rates, source error operands used
to identify a transition, native tuples, phase clocks, equality tests and
force matching remain exact and unchanged. The underlying finite-cell grid
is still `2^-128`; `h` controls only the producer's proof representation. It
is substantially finer than that grid and changes neither source accuracy
nor accepted tolerances. The binary64 publication formula retains its exact
`u*M+d*eta` value before the enclosing radius or magnitude is rounded. Uniform
phase queries evaluate their original exact magnitude expressions from the
bounded retained fields and exact clocks; they do not retain a new anchor.

Each executed integer shift and directed quotient is charged separately. The
integer operands are copied before the first callback; prospective widths are
guarded before the shift and again after the quotient callback. Grid-aligned
values use one charged admission and perform no shift or quotient. A callback
that narrows a cap or cancels cannot publish a partially rounded proof. The
existing final source/owner/receipt admission follows all of this work.

The initial exact-rational candidate
`dff2ac1244b9b0ad62aa669c55ef4daee186278d` passed four arithmetic methods and
the short planar/nonplanar release-containment method. Its next transition
cohort passed one method and raised four `numeric_operand_bits` errors during
later force/impulse proofs. Execution stopped there. These three complete raw
records remain `release-cells-dff2ac1-arithmetic`,
`release-cells-dff2ac1-first-release`, and `release-cells-dff2ac1-transitions`.
They do not establish a pass for the rounded follow-up or for original P16.

The rounded follow-up `463e2c94e0bd64ada4e2eb582cb2aad19adc783b` passed all
five arithmetic, six transition and six admission methods. Its complete short
export still failed. A separate unchanged observer reproduced exactly one
understated final-position row in 46,946 operations and recorded one
`transfer_release_domain` fallback with no proof capture or publication. The
old exact-class admission had excluded the internal recording planner, so the
end-to-end export was still using the earlier ordinary allowance. These raw
records remain under `release-cells-463e2c9-*`, including the complete rejected
GLB and exact independent minimum.

The inherited-method receipt follow-up
`dca4a9045ae28f650deac478c654299a6386d7da` passed its three added admission
methods, then the complete short-export method with explicit release, anchor
and dynamic proof-use assertions. That method also retained the independent
reader's rejection of a deliberately understated source-position claim. The
complete dedicated module subsequently passed **21/21** on the same source cut.
The records are `release-cells-dca4a90-method-admission`,
`release-cells-dca4a90-short-export`, and `release-cells-dca4a90-all21`.

The same cut's existing regression cohort passed **55 of 56 methods**; one
method had two subcase errors, retained in `release-cells-dca4a90-existing56`.
Those subcases deliberately replaced a released native anchor's rotation or
spin to test optional-sampler fallback. They left the new `CellAnchor` witness
attached to the former native operands, so its source admission correctly
rejected the changed anchor. The test-only follow-up removes the inapplicable
proof from those synthetic unsupported anchors and separately requires the
retained stale proof to reject before future-clock work or cursor publication.
Production source-proof admission is unchanged. The test/doc follow-up
`3f358c80f0cc2c15c0eb4235e1684da0b0f9be49` subsequently passed **22/22**
dedicated methods and the same **56/56** existing regression methods, with
stable before/after source inventories. These separate completed records are
`release-cells-3f358c8-all22` and `release-cells-3f358c8-existing56`.

Integration review then identified the bare-address lifetime gap described
above. Its follow-up replaces every helper identity receipt with strong
identity authority, preserving the previous arithmetic and charge semantics.
Five new methods cover actual weak-reference lifetime, copy/deepcopy, equal
source/model/state/anchor replacements during callbacks, deterministic
simulated address collisions, and the absence of historical state owners from
persistent lineage. These new methods and the current full cohort remain
**unexecuted** in this source record; the earlier 78 passing methods do not
certify this follow-up.

Original frozen P16 was also executed on `dca4a90`, with its original source
revision, four-second endpoint, settings and **100,000-operation** limit. It
reached producer encoding, then failed at **100,001 operations** during the
independent release's ideal pose-map construction, before certificate checking.
`release-cells-dca4a90-P16` retains the exact inputs, full counters and failure.
This is not an original-P16 certificate pass or release acceptance. All named
completed runs retained stable before/after input inventories.

## 6. Retained authority and verification still required

The metadata must bind the native anchor, its clock, the four source errors,
the proof clock, canonical/ideal acceleration, force/gravity context, model
identity, and the immutable source lineage. A copied state can carry the
same immutable proof values only with its matching copied anchor values.
Replacing an owner, changing a cap or changing any bound operand invalidates
the optional proof before use. Unsupported first lineage must not borrow
metadata from another object or earlier anchor. Whole-boundary failure rolls
back the new proof state together with existing dynamic state.

Implementation and review must establish these scoped correctness cases on the
current source cut before integration:

- exact tiny/native-grid and signed-axis arithmetic containment for the scalar
  rules, with coherent quaternion signs and no invented zero;
- incoming release equality and complete short-P16 independent acceptance;
- changed/equal force, release-plus-force at one clock, nonzero/zero impulse,
  repeated transfer, unsupported root-history and nonplanar cases;
- source/model/state/owner replacement, force/gravity/error/anchor changes,
  narrowing caps, cancellation, callback failure and reentry;
- stable original inputs, all executed logs and both earlier failed artifacts.

Original P16 and the full recording corpus still have to pass under the
unchanged 100,000-operation limit. The correction's incremental cost against
the prior allowance path has not yet been measured. A correctness proof does
not permit omitting its work to keep a recording below budget. The earlier
estimate of roughly one to three thousand extra operations is provisional and
must be replaced by an actual charged comparison. The full source corpus,
later delivery roles and release acceptance remain separate gates.
