# Bounded planar recording and optional stored-cell diagnostics

This is an optional recording implementation, identified by
`ontokin.recording-planar-binary64-enclosures/0.5`. It does not change
source poses, coordinates, rates, events, release anchors, source error bounds,
sampling inequalities, tolerances, operation limits or the 256-entry cache.
The ordinary projective-grid recording algorithm remains the fallback.

The production path returns native binary64 positions/quaternions with the
explicit `P` and `16Q` endpoint allowances derived below. Its actual binary32
conversion error remains an additional certificate term. It does not promise
identical accessors to a preceding recording algorithm. Every actual stored
endpoint, phase, interval inequality and requested tolerance must still pass
the independent supplied-byte reader. The adopted source target/coordinate
requirements and their canonical values are unchanged.

The preceding `0.1` algorithm additionally demanded an identical binary32 cell.
That stronger diagnostic remains available as `sample_certified_frames`; it is
not the production gate. A cell boundary no longer discards otherwise bounded
production samples. Unsupported arithmetic domains still replay the complete
phase with the original recorder, retaining all attempted work. This versioned
implementation decision changes no frozen source, expectation or tolerance.

## Recovered implementation and current integration

Version `0.5` recovers the bounded candidate from the previously unpublished
`1d7cac2dd91421ef6639bf4faf2bea61aaada45b` finish checkout. It also retains
the stricter identity-leaf and frozen-projection guards from the divergent
`64fcadf295803876f60c475ba3f12cb30cdeded5` checkout. Those original checkouts
and their earlier passing and failed runs remain historical evidence. Their
results do not verify this combined implementation.

A frozen source quaternion is a separate actual operand. Its complete public
tuple must be finite, planar, canonically signed and have positive zeros; its
exact decoded components must match the private components. Its squared-norm
defect must be at most `2^-51`. Correctly rounded unit components have defect
at most `2u+u^2`, so this larger `4u` admission margin covers materialized source
anchors while rejecting arbitrary nonunit frozen tuples. All these comparisons
retain the current domain and original callback exception. An exact identity
leaf may omit projection only when it has no frozen operand, all private types
are exact, and its scalar projective numerator and denominator have at most
512 bits. This last condition preserves the omitted square/ratio preflights.

The ordinary recording fallback may use the separately proved complete carrier
cursor in [the carrier derivation](reach-carrier-rotation-cursors.md). Every
such carrier seeds from a direct private complete orientation, and its excess
above the same uniform source path remains at most the `G` below. Therefore
the comparison through the common ideal path, including both `Sp`/`Sq` terms,
applies unchanged. Native graphs do not accept the carrier proof or its
approximate private operands. Unsupported complete paths use the ordinary
sampler with its current angular proof; a whole-phase replay has a fresh context.

Every actual rational ordering in the affine, dynamic and enclosure gates uses
the charged exact comparison helper and its prospective operand guards. A
zero/sign admission can inspect an already guarded exact numerator directly.
Completed enclosure and outward-radius cache hits recheck the current domain
after lookup callbacks. No callback can turn a proof from the full 32,768-bit
domain into an admission for a narrower one.

The exporter also charges hemisphere-lift arithmetic. With eight finite
binary64 components in the full domain, uniformly signed nonzero component
pairs determine the exact rational dot-product sign without products or sums.
No overlapping nonzero pair means exact zero. When all product signs agree
and one pair has both magnitudes at least `1/2`, the dot magnitude is at least
`1/4`, proving the optional strict `2^-16` margin. Mixed signs and smaller
margin cases use all four charged exact products and additions. Narrowed
domains retain that exact path, including its original prospective guards.
Every actual component negation is charged before execution. Signed zeros
continue to follow the selected quaternion lift.

## Scope and implementation domain

The candidate graph accepts only complete dependency paths with scalar/Z
rotations. Production may also use the bounded dynamic-root domain proved
below when supplied the actual source phase interval. General rotation paths,
dynamic roots outside that domain, and dynamic roots in the strict stored-cell
diagnostic retain the ordinary recorder. An approximate parent is never passed
into ordinary composition as an exact input.

Every candidate composition has an accumulated parent on the left and a source
leaf on the right. Native composition depth is limited to 64. Native positions
and local offsets have magnitude at most `2^500` per component. Quaternion
components have magnitude at most two. Native intermediate finiteness and the
unchanged 32,768-bit operand cap are checked; a different domain requests
ordinary phase replay. Every binary64 arithmetic constituent is charged before
execution. A callback exception propagates unchanged. Numerical cursors and
completed projection/rounding proofs use the existing bounded work cache.

For graphs selecting more than 16 changing frames, the same cache may also
hold completed native complex products and local-offset rotations. These are
pure operations keyed by every binary64 operand bit, structural-zero flag and
the live operand cap. This shares identical arithmetic among translated arms;
each caller still resolves its own topology, coordinate, cursor history,
parent position and final position addition. A hit skips only already completed
identical arithmetic, so it changes neither candidate bits nor the enclosure.
Operand and domain guards precede reuse, cancellation remains observable, and
the existing 256-entry limit applies to these entries with every other cache
entry. Small graphs retain the direct operations to avoid useless bookkeeping.

The cache also retains a completed controlled axis kernel plus its native unit
projection by exact axis, exact coordinate or increment, structural-zero mode,
and live operand cap. Each caller still checks its own coordinate, cursor and
step count. This pure proof may be shared when rounded coordinate increments
alternate among a few previously completed values. A cache miss executes the
original controlled kernel and projection. Both cache publication and hits
recheck the live native domain after their callbacks. The private immutable
`ZERO` default of a newly constructed native leaf has the exact binary64 image
`(0,0,0)` directly; other supplied vectors retain ordinary decoding/projection.

The cache also retains the complete projection of a constant source leaf by
its actual position, rotation, inverse selector and live operand cap. Its cold
path executes the original source constant/inverse construction and the same
native projection. A hit first checks every actual operand's type, finiteness
and admissible exact decoding width. This removes a second cache lookup for
the intermediate source pose; it does not reuse the accumulated parent or a
previous clock's placement. Only the source model's immutable numeric tuples
enter these keys.

The first key of a phase and final boundary use the ordinary recorder. In
production, a claimed hinge interior uses the private exact actual affine law
derived below. The strict stored-cell diagnostic retains the original exact,
binary64-rounded coordinate. Each seed and new exact increment uses the
existing controlled axis kernel and correctly rounded unit projection. No
host trigonometric or square root function is introduced. Subsequent scalar/Z products use four binary64
multiplications and two additions/subtractions. A candidate cursor starts from
the direct kernel at least once every 127 keys; counting its seed as one means
there are at most 126 subsequent native products. The original recurrence
still has its separate 10,000-key limit. No normalization is needed inside the
bounded candidate sequence.

## Exact affine interior coordinates

### Reusing completed source and phase proofs

Fixed hinge axes and root angular velocities use the existing shared exact
vector decoder. Each use still admits the actual shape, finite scalar types
and live operand cap. A hit reuses only the identical binary64-to-rational
conversion; the source vector, normalization, controlled kernel and candidate
bits remain unchanged.

A successful spin cursor has already completed the ordinary reconstruction
`omega = scaled_omega * maximum` for its supplied `SpinPlan`. Its existing
bounded-cache key includes the actual omega, every immutable plan field,
initial rotation, recording context, path, step ceiling and operand cap. A
warm cursor with the same fully typed exact plan can reuse that reconstruction
proof. Every current plan field is guarded again, and the new absolute elapsed
clock still performs its own prospective-guarded comparison with the plan's
horizon. An absent cursor, changed plan or velocity, or a call without a
supplied exact plan retains the ordinary complete admission. A new direct seed
or changed angular increment also retains its ordinary controlled kernel.
No separate identity-result cache is introduced.

The existing cached ballistic law similarly retains the completed ordering
of its exact anchor, phase start/end and optional scene-duration clocks. Those
clocks, every coefficient's actual binary64 bits, root extent, context and path
all enter its key. Signed zeros remain distinct because the native Horner
result can retain their signs after underflow. Each call checks the fresh
operands and live cap before reuse. The current sample still checks both phase
endpoints; the ballistic-position helper checks the current elapsed domain
before any native arithmetic. A caller need not perform those same elapsed
comparisons a second time.

The completed ballistic law also retains the exact bound against which its
root extent was proved. A dynamic descendant presenting that identical
canonical Fraction reuses the already completed comparison under the unchanged
full cap. Equality here compares normalized integer fields, with no rational
cross-products. A different descendant bound performs its own charged,
prospective-guarded comparison. The existing per-graph root index holds only
references to those completed laws and is discarded after the sampler call;
all retained results remain in the same 256-entry cache.

These changes omit only exact arithmetic or decoding whose complete result is
already proved, or the explicit zero identities below. Every helper that runs
keeps its original charge and callback. Cancellation before cursor publication
retains the previous completed cursor; a successful operand-cap change clears
the wider-domain cache and disallows a native return. The candidate arithmetic,
127-key reseed ceiling, strict stored-cell diagnostic and all enclosure
equations are unchanged.

For a claimed hinge, let `a0` be the actual initial scalar, `i0` the separately
retained ideal initial scalar, `g` the canonical target, `d>0` the duration and
`e` the current exact elapsed clock. The unchanged source equations are

```
s = (g-a0)/d                 si = (g-i0)/d
a(e) = a0+s*e               i(e) = i0+si*e.
```

The ordinary source and ordinary recorder expose `RN64(a(e))`. The optional
production interior instead rotates by the unexposed `a(e)`. It never supplies
that scalar through the source `_coordinate` or `PairSample` API. The exact
target shortcut at `e=d` is algebraically identical. The source rate and its
published rounding also remain unchanged outside this private recording path.

The existing `joint_phase` proof derives, on each continuous closed phase,
`I=max(|a(start)-i(start)|, |a(end)-i(end)|)` and an exposure allowance `R`
from the maximum actual affine endpoint magnitude. Both scalar differences
are affine in the elapsed clock. Their absolute maxima occur at endpoints,
including paused phases, so throughout the phase

```
|a(e)-i(e)| <= I
|RN64(a(e))-i(e)| <= I+R = coordinate_error.
```

Thus the new unexposed scalar is contained in the *same* existing coordinate
error, with no added source uncertainty. `joint_local` already includes that
error in `coordinate_angle_error_rad`, and `uniform_source_bounds` propagates
its sum into source angular error and into position error through the complete
path offset. Unclaimed coordinates, root prescribed spins, ordinary/general
paths and all source anchors keep their existing behavior.

The private law caches only the exact `(a0,g,d)` operands and slope, under the
live cap and running/paused state. Every occurrence resolves its own current
claim and runtime before reuse. For reach pairs it reads the current shoulder
or elbow component; it does not call, replace, mutate or cache a `PairSample`.
Every call reads the actual elapsed base, requested clock and running-since
clock. Their subtraction and addition are guarded and charged before execution.
The resulting elapsed clock must remain in `[0,d]`. A paused action uses its
retained elapsed value without reading unused running-clock operands. Resume
and changed ownership therefore cannot inherit a previous request's clock.
When an admitted exact running-since clock is zero, the difference is the
current clock itself; when the admitted elapsed base is zero, the subsequent
sum is that difference itself. Those identities perform no scalar arithmetic.
The same 1,024-bit input and resulting-clock restrictions below prove that the
original omitted subtraction/addition preflights fit the full live domain.

For two cursor clocks, the rotation increment is exactly `s*(e_new-e_old)`.
The sum of these increments telescopes to `a(e_new)-a(e_seed)`, also for
nonuniform spacing, repeated clocks and clock reversal within `[0,d]`. All
rotations use the same normalized scalar/Z axis, so their ideal quaternion
products represent that exact accumulated angle. The native recurrence error
proof below consequently applies unchanged. Cursor identity includes the full
exact law, axis, context, path, step limit, running state and live operand cap.
Its count still forces a direct seed at least every 127 keys. An affine
cancellation cannot prove that the earlier history-dependent original recorder
has a structural zero, so these seeds and increments never claim one.

This alternate factorization is confined to the full 32,768-bit domain, with
the numerator and denominator of each exact law operand and actual elapsed
clock at most 1,024 bits. Actual raw running-clock operands have the same
limit before arithmetic. A difference has at most 2,049 numerator / 2,048
denominator bits; the slope has at most 3,073 / 3,072; a seed's affine value,
or a slope times an elapsed difference, has at most 5,122 / 5,120. These bounds
cover the prospective unreduced products in both original source evaluation
orders: slope-then-elapsed for a reach pair and difference-times-elapsed before
division for an ordinary joint. The original binary64 projection preflights
need fewer than 6,200 bits, including the 1,074-bit subnormal shift. This is a
domain proof, not a change to any configured limit. Wider operands or a narrowed
live domain request the original complete-phase fallback; attempted work remains
charged. Exact arithmetic that is actually performed still uses the ordinary
charged helpers and their prospective/result guards.

On a cold law, finite endpoint projections prove that the convex actual affine
values stay representable throughout `[0,d]`. A running law also completes the
original correctly rounded rate projection before it can be reused. Paused laws
do not project an unused rate; their original source behavior permits a finite
coordinate even if that unused derivative would overflow. Running state is part
of this completed-proof cache identity. All cache hits and publications recheck
the live native domain after callbacks, and callback exceptions propagate with
their original identity.

Prescribed scalar/Z root spins use the same candidate recurrence. Their
absolute seeds come from the ordinary controlled `advance_orientation`,
including the complete initial projective rotation. Their increments come
from the ordinary `spin_rotation` at the exact elapsed difference. Every key
retains the ordinary requested elapsed, angular velocity and `SpinPlan`
validation before cursor reuse, and separately checks a changed increment's
domain. The cursor identity includes the initial rotation, angular velocity,
phase plan, context and operand cap. Stationary/zero-elapsed branches preserve
the original direct initial orientation. A moving absolute seed or increment
does not infer a baseline structural zero from an interior cancellation.
Full source states, derivatives, anchors and ordinary recording paths continue
to use their existing arithmetic.

## Bounded dynamic-root interiors

The production-only dynamic candidate uses the actual current source anchor,
its canonical binary64 position `p0` and velocity `v0`, and the current canonical
binary64 acceleration `a`. For exact elapsed time `e` after that anchor, the
ordinary private position polynomial is exactly

```
p(e) = p0 + v0*e + a*e^2/2.
```

The source evaluator, incoming release state, force aggregation, reanchoring,
source observations and rates continue to use their existing exact arithmetic.
Only a recording interior evaluates the same polynomial using this native
Horner order, independently in each component:

```
t = RN64(e)
h = t/2
b = RN64(a*h)
c = RN64(v0+b)
d = RN64(t*c)
p_candidate = RN64(p0+d).
```

The division by two is an exact binary64 multiplication in the supported
domain. Both appearances of time use that same `t`; the proof below includes
the discrepancy from exact `e` in both appearances. Exact zero coefficients
may skip unused arithmetic. An identically zero component requires all three
actual coefficients to be zero. Cancellation does not establish a structural
zero. For `e=0`, the candidate returns the actual anchor position directly.

### Checked domain and finite intermediates

Put `K=2^250`. Each actual coefficient must be a finite, exact-type binary64
number with magnitude at most `K`. The exact elapsed time must be zero or lie
in `[2^-250,K]`. Its exact numerator and denominator, and those of the actual
anchor, phase boundaries and requested clock, have at most 1,024 bits. The
live operand cap must remain the original 32,768 bits. The candidate first
checks

```
0 <= anchor_time <= phase_start <= requested_time <= phase_end <= scene_end.
```

It charges and guards the exact elapsed subtraction before using native
arithmetic. A cold law also derives and checks the exact horizon
`H=phase_end-anchor_time`, with `0<=H<=K`; every sample must satisfy `e<=H`.
A narrower domain or a wider clock requests the original complete-phase
fallback with all attempted work retained.

Rounding monotonicity and the exactly representable interval endpoints imply
`2^-250<=t<=K` for nonzero elapsed time. Thus `h=t/2` is normal and exact,
and `2^-251<=h<=2^249`. In each component:

```
|a*h| <= 2^499        => |b| <= 2^499
|v0+b| < 2^500       => |c| <= 2^500
|t*c| <= 2^750       => |d| <= 2^750
|p0+d| < 2^751       => |p_candidate| <= 2^751.
```

These power-of-two bounds are themselves exactly representable. Every
intermediate is consequently strictly below `2^752`, so binary64 overflow
is impossible within the proved input domain. Each actual multiplication or
addition still has its own work charge, live-domain check and finite-result
check. The completed candidate must additionally fit the existing `2^500`
position composition domain or request fallback.

The alternate order cannot evade a source operand-bit failure in this domain.
A decoded coefficient needs at most 251 numerator bits and 1,075 denominator
bits; an elapsed square needs at most 2,048 bits in each. The original exact
`p0 + v0*e + a*(e*e/2)` order, including prospective unreduced additions and
the final binary64 projection shift, fits within 10,000 bits. All performed
exact arithmetic still runs through the ordinary guarded helpers. Native
orientation continues to run the existing controlled scalar/Z spin-plan and
cursor checks.

### Error from rounded time and gradual underflow

Let `u=2^-53`, `eta=2^-1075`, and let `P0,V,A` denote the L1 norms of the exact
dyadic input vectors. Define the nonnegative polynomial magnitude

```
B(e) = P0 + V*e + A*e^2/2.
```

For nonzero supported `e`, normal rounding gives `|t-e|<=u*e`. Comparing the
exact polynomial at the two clocks, without assuming that either time use is
exact, gives

```
|p(t)-p(e)|_1
    <= u*V*e + (2*u+u^2)*A*e^2/2
    < 3*u*B(e).
```

The sum of exact term magnitudes at `t` is
`S(t)=P0+V*t+A*t^2/2 <= (1+u)^2*B(e) <= (1+3u)*B(e)`.
Every rounded native operation, including a subnormal result, admits
`RN64(x)=x*(1+delta)+epsilon`, where `|delta|<=u` and `|epsilon|<=eta`.
This representation includes the smallest subnormal coefficients; it does
not rely on a relative-error model for an underflowed product.

In the four rounded Horner operations, any input term accumulates at most
four relative factors. Their contribution is at most `gamma4*S(t)`, where
`gamma4=4*u/(1-4*u)<5*u`, hence less than `6*u*B(e)`. In one component the
four additive underflow terms are bounded by

```
eta * (t*((1+u)^3+(1+u)^2) + (1+u) + 1)
    < 4*eta*(1+t).
```

The first two underflow terms are multiplied by the later `t`; the last two
are not. Summing all three components yields less than
`12*eta*(1+K)<u`. Combining clock and arithmetic errors therefore gives

```
|p_candidate-p(e)|_1 < 9*u*B(e)+u <= 64*u*(B(e)+1).
```

Omitted zero-coefficient operations only remove factors and additive errors,
so the same bound covers those branches. The zero-time branch is exact.

### Whole-phase propagation and identities

The existing dynamic `PhaseBound.max_position_l1_m` is exactly `B(H)` for
the actual phase and anchor: its former maximum absolute elapsed expression
reduces to `H` under the checked clock ordering. A cold native law independently
recomputes `B(H)` from the actual source coefficient tuples and exact horizon,
then requires that the supplied dynamic-root bound enclose it. Because every
coefficient in `B` is nonnegative and `0<=e<=H`, `B(e)<=B(H)`.

Each source composition updates its maximum position bound by adding the
parent bound, twice the nonnegative local extent and a nonnegative vector
allowance. The translated and deferred implementations are exact
factorizations of that same equation. Every descendant bound `M` therefore
dominates the dynamic root's `B(H)`. The sampler nevertheless makes an actual
charged comparison of the completed root extent to each selected descendant's
`M` before attaching the dynamic allowance. It cannot use a different root's
proof or an undersized descendant claim.

Native composition places the accumulated parent on the left and a source
leaf on the right. Consequently a dynamic root's position error propagates
only by addition along the path; it is never rotated as an approximate local
compound transform. The native position induction below retains its `2D`
premise with the extra `64uD`, since
`M+3E*L+(128u*65+64u)*D<2D`. For each dynamic-dependent selected frame the
additional position allowance is therefore

```
64*u*(M+L+1) = 2^-47*(M+L+1).
```

Before this native position error, the candidate uses the identical exact
actual root polynomial as the ordinary private source evaluator. The existing
`Sp` includes its anchor, velocity, acceleration and final exposure errors
against the ideal source path. Removing an exposure does not require a larger
source bound. Scalar/Z orientation uses the already proved native spin path,
with the same actual initial rotation, angular velocity and exact elapsed
clock. Existing source `Sq`, trig/product counts and the quaternion allowance
remain unchanged.

Every graph classification reads the actual current incoming relations and
anchor. A completed law is keyed by context identity, root path, anchor time,
both phase boundaries, all actual coefficient tuples, the supplied root
extent and the live cap. Changed force, anchor, phase or context cannot reuse
an incompatible proof. Pure equal operands may reuse only a completed law;
the current clock and the current descendant bound are checked again on every
occurrence. The root-to-descendant index lasts for one sampler graph and is
not an additional retained numerical cache. Publication and reuse use the
same bounded 256-entry work cache and recheck the live domain after callbacks.
Original callback exceptions propagate unchanged, and interrupted publication
cannot replace a previous completed proof.

## Quaternion enclosure

Let `u = 2^-53`. A correctly rounded planar unit projection is within `2u` in
Euclidean norm of the represented unit quaternion. The controlled axis error
is less than `u`; taking `3u` covers a seed or increment's combined discrepancy.

For a complex product, Cauchy–Schwarz bounds each component's sum of absolute
products by the product of the operand norms. Two correctly rounded products
and their sum therefore contribute less than `5u` in Euclidean norm while the
norms are within `1+2^-20` of one. Inductively, after `n <= 127` steps the
error is bounded by `(3u+8nu) exp(3nu)`. For at most 127 native products, the
looser `4u + 32nu` allowance is less than `2^-41` because
`(4 + 32*127)u < 4096u = 2^-41`. (The implementation actually performs at
most 126 products between seeds.) This induction establishes the norm premise;
the numerical domain checks provide an independent finite-execution guard.
Canonical sign changes do not change the norm or represented rotation. The
quaternion error is projective: it is the smaller of the distances to `q` and
`-q`, with one common sign for all components. Near a nonstructural zero leading
component, the candidate and original canonical signs can differ. Production
uses the resulting rotation-distance bound and chooses its actual stored lift;
only the optional same-cell diagnostic must refine or fall back in this case.

Let `T` and `C` be the existing whole-source-path `trig_count` and
`product_count`. Each hinge contributes a trig count; each source constant,
joint, and composition contributes product counts. Thus these counts dominate
the candidate cursor factors, constant projections, and native products. With
at most 64 leaf compositions and the checked local error range, a conservative
unnormalized quaternion enclosure is

```
E = 2 * (T * 2^-41 + (C+1) * 2^-47).
```

The factor two covers propagation of factor errors and their cross products;
`2^-47 = 64u` exceeds one native product and constant projection allowance.
The implementation requires `E <= 1/64`. Normalization changes the comparison
by at most a further factor four; the chosen `16E` component allowance also
dominates the corresponding local rotation-angle comparison.

## Position and baseline enclosures

For a planar complex quaternion `q`, native position rotation uses `q^2`:
`c = w*w-z*z`, `s = 2*w*z`. If the ideal quaternion has unit norm and the
quaternion error is at most `E <= 1`, then the matrix discrepancy is at most
`3E`. Each local origin is a source leaf, so its effect is added along the
existing whole-path offset bound rather than recursively rotating an already
approximate local origin.

Let `L` be the existing `path_offset_l1_m`, `M` its `max_position_l1_m`, and
`Sp,Sq` the existing source position and angular error bounds. Put
`D = M+L+1`; the extra one covers gradual-underflow absolute errors.
`PhaseBound.product_count` increases by at least one for each composition,
as well as the source constants and joints. Therefore `C` bounds the native
composition depth, and `C+1` covers source leaf projections including the
initial root.

The quaternion enclosure gives `|q| <= 65/64`. Its native `q^2` matrix
coefficients have magnitude below two; their floating construction errors
are at most `4u` plus the covered underflow allowance. Source-leaf projection,
the two products and sum in a matrix row, and addition to the parent position
together contribute less than `32u*D` per composition when
`|p_candidate| <= 2D`. This last inequality follows inductively from the exact
path magnitude, the existing `3E*L` rotation-error allowance, and at most 64
leaf compositions: `M + 3E*L + 128u*65*D < 2D`. The same induction covers
propagation of earlier point-addition rounding. There is no approximate
right-hand compound transform whose position error could be rotated again.
The conservative native-rounding allowance is consequently
`128u*(C+1)*D = 2^-46*(C+1)*(M+L+1)`.

The original recurrence contributes

```
G = 9999 * T * (AXIS_ERROR + 2*PRODUCT_ERROR).
```

Both the original and candidate paths retain the source error contribution.
For the affine candidate, the scalar inequalities above prove this step:
before the new native recurrence/rounding errors, its path is within the same
`Sq` and `Sp` of the independently defined ideal source path. The original
recorder is within `Sq+G` in rotation and `Sp+L*G` in position of that path.
The candidate adds at most `16E` to the quaternion component comparison and
`3E*L` plus the native-rounding term to position. Applying the triangle
inequality through that common ideal path produces the two source contributions
below; it does not presume the exact and rounded scalar paths are identical.
The position and sign-aligned quaternion component enclosures against the
original recurring binary64 outputs are

```
Q = 2*Sq + G + 16*E
P = 2*Sp + L*(G+3*E) + 2^-46*(C+1)*(M+L+1).
```

For a selected path depending on a supported native dynamic root, add the
separately proved `2^-47*(M+L+1)` term to `P`. Other paths retain the expression
above; `Q` is identical in both cases.

The implementation also requires `Q <= 1/64`. It returns explicit
`position_m=P`, `quaternion_component=Q`, and `rotation_rad=16*Q`. The last
conversion deliberately covers four sign-aligned component errors and
normalized rotation comparison. For a unit original quaternion and a candidate
whose component errors are at most `Q <= 1/64`, their aligned Euclidean distance
is at most `2Q`; normalizing the candidate increases this to at most `4Q`.
The represented rotation distance is `4*asin(chord/2) <= 16Q` in this domain.
Source bounds themselves are unchanged. The exporter must include
these actual candidate allowances in its endpoint certificates. Its existing
independent supplied-byte validator still checks the delivered endpoints.

## Optional diagnostic: unchanged stored components

For a candidate binary64 component `v`, let `s` be its nearest binary32 value.
The difference `d=v-s` is exact by Sterbenz; the zero/subnormal cases also have
exact differences. Binary32 rounding-cell boundaries are exact binary64
numbers. At a power of two, only the side toward zero has half the usual cell
width; the implementation conservatively uses the smaller symmetric cell.
The normal/subnormal transition retains its actual equal spacing.

The error radius is converted upward to `e`. Let `h` be the exact symmetric
half-cell width and compute `t = RN(h-e)` in binary64. The gate requires
`abs(d) < t`. If `t <= h-e`, this directly proves strict containment. If `t`
rounded upward, every binary64 smaller than `t` is at most its predecessor,
which is strictly smaller than the exact `h-e` that rounded to `t`. This also
proves strict containment at midpoint ties and subnormal boundaries. A
nonpositive threshold cannot pass. Consequently every value in the component
enclosure, including the original recurring binary64 output, rounds to the
same stored binary32 bits. Structural zeros are
propagated only from source leaves, constant coordinate laws, and identically
zero algebraic terms; cancellation of two nonzero terms is not a zero proof.
Structural zero outputs are canonical positive zero.
An enclosure crossing zero cannot certify a signed binary32 zero; the gate
explicitly checks this distinction rather than treating both zero bit patterns
as equal.

In the strict-cell diagnostic, each immutable cached path enclosure retains its completed upward
binary64 position and quaternion radii. The cache identity contains all exact
source-bound operands and the current operand cap. Both conversions finish
before the enclosure is published, with a final domain check; a cancellation
cannot publish a half-completed pair. Subsequent components use these same
proved radii without two additional numerical-cache lookups. The exact
rational fields remain the values supplied to the endpoint certificate.

An identity composition can share the same immutable candidate rotation with
several selected frames. Within one completed graph, those actual identities
may share a quaternion rounding proof using the largest of their independently
validated path radii. The key also retains the structural-zero flags. A failed
group proof makes every member try its own radius before direct refinement;
it cannot create an ambiguity merely by borrowing a larger radius. Positions
retain their own component checks. This temporary index is discarded after
the sampler call and retains no prior coordinates or extra persistent cache.

An ambiguous candidate is reevaluated by the ordinary direct recording
kernel. This refinement is not asserted equal to the history-dependent
recurrence: it must independently certify its stored cell using
`2*Sp+L*G` and `2*Sq+G`. If refinement is still ambiguous, the exporter discards
all candidate keys from that phase, resets a fresh original recording context,
and replays the complete phase. Work already consumed remains charged. No
coordinate history or alternative unbounded numerical cache is retained.

Consequently the diagnostic's stored position and quaternion accessor values
remain the original values. Production instead retains the explicit endpoint
enclosures and independent stored-byte acceptance described above. Its exact
rational bounds do not need auxiliary float radii for cell comparisons.
