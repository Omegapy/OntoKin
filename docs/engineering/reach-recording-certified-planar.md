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
applies unchanged. The production native graph may separately opt into the
complete scalar/Z carrier recurrence proved below. It accepts the phase's
fresh source-law witnesses, never an ordinary cursor's approximate private
operand. Unsupported complete paths use the ordinary sampler with its current
angular proof; a whole-phase replay has a fresh context. The strict stored-cell
diagnostic keeps the preceding native local-factor algorithm.

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

## Exact affine root positions

A prescribed root translation continues to evaluate the exact source equation
`p_i = initial_i + rate_i*elapsed`. The native graph can retain the completed
exact decoding of the two immutable three-component source vectors in the
existing 256-entry LRU. Its key contains every actual component's concrete
type and value, including binary64 zero signs, and the current operand cap.
The current elapsed clock is admitted on every call and never substitutes a
previous sample's position. Mutable vectors, malformed operands, unusually
large exact values and non-Fraction clocks retain the ordinary source helper.

The optional path requires the full 32,768-bit cap. Every original exact
numerator and denominator has at most 2,048 bits; any finite binary64 operand
needs at most 1,075 bits after exact decoding. An exact `rate_i*elapsed`
therefore has a prospective multiplication width of at most 4,096 bits. Its
sum with `initial_i` has numerator width at most 6,145 and denominator width
at most 6,144. These bounds also cover the original multiplication by an exact
zero component. Omitting that product cannot hide a prospective operand-limit
refusal in this admitted domain. Nonzero multiplications and additions use
the unchanged charged source exact-arithmetic helper. The ordinary whole-vector
zero and unit-scale decisions retain their admission charges.

The exact equation finishes at the original call site, before root orientation
work. A private immutable wrapper carries only that current exact result to
native pose construction. Every nonzero component then uses the unchanged
round-to-nearest-even binary64 kernel. An exact zero has the same canonical
positive-zero image without executing the rounding kernel. Nonzero subnormal
values, midpoint ties, cancellation, and finite-exposure refusal therefore
retain their original results. No intermediate position projection or completed
per-clock vector projection is added to a cache. Existing complete-pose slots
still use the current immutable position as part of their complete signature.

The current cap is checked after each cache callback, identity admission and
actual arithmetic/projection sequence. An original exact-kernel exception is
never translated or retried. A cancelled projection cannot publish a partial
position; already completed immutable source-vector decoding can remain in
the same shared bounded cache. For identical current source operands, this
position path preserves every exposed position bit. It changes no source
position equation, rounding allowance or certificate inequality; the other
recording recurrences retain their separate existing bounds.

`tests/test_reach_recording_exact_affine_position.py` compares exact values and
binary64 bits for rational and binary64 laws, zero/unit clocks, cancellation
and subnormal ties. It exercises actual moving-source graph samples, mutable
and large-input fallbacks, invalid inputs, exposure overflow, changed operands,
LRU eviction, live cap changes, cancellation, original exception identity and
actual work reduction. Executed evidence must identify the tested revision;
the test definitions alone do not establish a passed recording or release gate.

## Native complete carrier recurrence

The production native graph can replace the local hinge recurrence and its
two world compositions at a hinge whose child-site translation is exactly
zero. The optional `RecordingAngularProof` must identify an exact constant
ideal body rate about Z, or an exact zero rate, for that complete carrier.
Its program revision, closed phase clocks, typed local source witness and
already checked parent witness are checked during the current graph traversal.
The same actual source coordinates, claims, initial and ideal values, durations,
axis, child pose, root laws and topology remain inputs to this proof. An absent
or changed witness retains the native local-factor path. Other alternate
recording arithmetic cannot acquire this capability implicitly; native carrier
cursors require a separate explicit opt-in, disabled for the strict diagnostic.

For an actual immutable tuple of three binary64 zeros, the native graph can
admit the zero child origin directly at the existing charged origin checkpoint.
Both zero signs decode to exact rational zero, so all ordinary decoding and
prospective operand checks fit the unchanged full domain. This omits the
otherwise redundant source-vector decoding and cache lookup. A callback-induced
cap change makes the cursor ineligible; the final atomic source admission still
checks the complete current child pose. Every nonzero, noncanonical or narrowed
input keeps the original exact vector path. No small-offset threshold is used.
`tests/test_reach_recording_child_origin.py` covers actual graph equality and
work avoidance, both zero signs, subnormal nonzero offsets, malformed operands,
lowered caps, cancellation, and the unchanged shared operation limit.

Production additionally selects only hinges whose actual current local
coordinate law varies. The existing complete-ancestry classification reads the
current claimant, running status, initial coordinate and target for each hinge;
an absent/nonrunning claim or equal endpoints retains its local factor. A
moving parent does not make a constant local hinge eligible. When none of the
classified native hinges varies, the graph omits the optional carrier proof
walk entirely. The selected relation names form a temporary structural set for
this one graph, never a retained numeric table. This is solely a choice between
two independently bounded algorithms: every selected hinge still passes the
complete fresh chained witness, clock, child-origin and arithmetic-domain
checks. A completion or release rebuilds the selection from its current state.

Before either exact or native complete-carrier publication, each ancestor's
current-source comparison is precharged. The final cache admission then reads
the complete actual witness chain without callbacks, after all insertion,
promotion, eviction and operand-scope callbacks and before changing any cache
value or order. It also binds the actual model and root-state identities.
Persistent source changes cannot publish a cursor for the captured old curve;
an original source-kernel or admission refusal keeps its original exception
identity even if the operand cap changes. The shared cache remains bounded at
256 entries. This admission follows the mechanism proved in
[the carrier derivation](reach-carrier-rotation-cursors.md) and adds no
numerical allowance.

### Independent direct seeds and native arithmetic

For each eligible complete ideal orientation, the phase proof establishes

```
Q_ideal(t) = Q_ideal(s) * Rz(r*(t-s)).
```

The native cursor's seed at `s` comes from an ordinary private complete-world
`RotationValue`, evaluated from the admitted immutable witness chain by the
same direct source coordinate/quaternion kernels. This orientation-only recipe
omits unused source positions and never rereads a mutable action or attachment
during seed arithmetic. A temporary callback mutation therefore cannot poison
the completed cursor under its preceding proof token. Neither a parent native
cursor, an ordinary local recurrence nor an exposed quaternion can supply this
seed. Its private rotation is then projected
to binary64 by the existing correctly rounded unit projection, with structural
zero claims disabled. Every later nonzero step postmultiplies by the controlled
axis kernel at the exact signed increment `r*(t-last)`. Repeated exact clock
differences reuse that already completed increment; zero rates and repeated
clocks require no new increment. Reversed clocks use their actual negative
difference. No host trigonometric operation or normalization is introduced.

The direct seed counts as one of at most 127 samples. Before sample 128, after
eviction, or under a fresh phase/proof token, the cursor independently reseeds
from the current direct private source graph. At most 126 binary64 complex
products can therefore follow any seed. The native seed projection contributes
at most `2u`; each controlled increment and its projection contribute at most
`3u`. The existing complex-product induction below consequently bounds this
one cursor's native discrepancy from its unit reference by `2^-41`. Source
kernel errors inside the complete direct seed are accounted for separately by
the source bound; they are not treated as native arithmetic errors.

Every hinge contributes one existing source trig count, even for a zero ideal
rate. Replacing that hinge's local native factor by one complete native cursor
does not add a second factor at that hinge. Each still-used ancestor root spin
or local hinge factor also has its own existing trig contribution. Consequently
there are at most `T` native cursor errors along any source path, including the
prefixes whose orientations rotate intermediate offsets. A complete cursor's
seed projection belongs to its `2^-41` term. Ordinary constant projections and
remaining leaf products retain their existing `C+1` allocation. This preserves
the same `E`, `P` and `Q`; it does not enlarge any source count or allowance.

### Private prefix errors and positions

Write the existing uniform private angular recurrence as

```
R_private = anchor_rotation_error + coordinate_angle_error
            + T*AXIS_ERROR + C*PRODUCT_ERROR.
```

All its terms are nonnegative and accumulate along a source dependency path.
The bound for any prefix is thus at most that for its descendant. A direct
private seed at any clock in the continuous phase has angular error at most
its prefix `R_private` from that prefix's independently defined ideal
orientation. Right multiplication by a unit ideal increment preserves that
error. Different ancestors may seed at different clocks: each has its own
uniform source bound, and no ancestor cursor seeds a descendant cursor. A
reseed replaces, rather than adds to, a preceding seed's error.

At each unchanged fixed/site/follow offset, this private source angular error
contributes at most the offset's L1 length times the corresponding prefix
`R_private`. Their sum is at most `L*R_private`, the term already present in
`Sp`. The native seed projection and recurrence add the separate `3E*L` term.
The public quaternion allowance `2^-50` is added only after the source position
recurrence; it is never fed back into this position argument. In particular,
the newly projected native seed spends its projection error in `E`, not in
that public bonus. Ordinary leaf/source position errors and native position
rounding keep the other existing terms of `Sp` and `P`.

A zero child-site offset leaves the carrier origin exactly at its independently
computed parent-site origin. The two omitted native joint compositions both
have zero local translation, so their native position arithmetic is an exact
identity. The carrier retains that parent's current native position and zero
flags, while its depth increases by two as before. The unchanged ceiling of
64 source leaf compositions still applies. Nonzero child-site translations
retain the existing compositions. No approximate compound local origin enters
the right side of the position recurrence.

### Cache extent, live domains and verification

The cursor keeps only one complete clock/rotation/count and one repeated
increment in the existing shared 256-entry LRU. Its key includes the native
algorithm selector, phase context, carrier path, opaque frame-proof token,
phase endpoints, exact body rate, axis, step ceiling and live operand cap.
Every current scalar, quaternion, parent position and depth is admitted before
reuse; the current phase and graph witnesses remain fresh. Each actual scalar
operation, native constituent, lookup and publication retains its work charge.
A callback-induced cap change disallows a native return or publication and
requests the ordinary phase path. Callback exceptions retain their identity;
cancellation cannot replace a completed cursor with a partial result or mutate
the authoritative source state. No new per-frame numeric table is retained.

`tests/test_reach_recording_native_body.py` covers independent interval
comparisons, reseeds and reversed/repeated clocks, changed cursor identities,
fresh witnesses and child offsets, exact source-seed ancestry, live caps and
cancellation, source-state preservation, the separate strict diagnostic, and
complete short GLBs checked by the independent reader with writer sampling
disabled. Test results belong to separately identified executed revisions.

### Same-clock aliases of complete orientation laws

In a broad native recording graph, repeated translated assemblies can have
identical complete orientation laws. A temporary structural index may refer
to an already required current graph frame with the same law. It stores a
frame path, not another numerical result, and is discarded at the end of that
single graph resolution. The persistent numerical cache and its 256-entry
limit are unchanged. The strict stored-cell diagnostic does not enter this
path.

The equality key retains the ordered root, site, follow and joint recipe.
Root mode, public and private initial rotation, private projection, anchor
error and full orientation claim remain operands. Each fixed step retains
its actual typed quaternion. A joint retains its kind, signed axis, both
limits, inverse child quaternion, current actual and ideal coordinate, and
all numerical action fields: duration, vector/goal, status, actual and ideal
initial values, target solution, saved elapsed time, running clock, initial
private rotation and its error. A reach's shoulder/elbow paths become its
proved selected pair index; that index remains in the key. The key also
contains every frame's signed body rate and trig count, and the index binds
the closed phase interval. Only identity names and translations absent from
the ordered orientation calculation are omitted. Unknown recipe shapes use
the existing independent carrier cursor.

Equal recipes therefore describe the same direct source quaternion kernels
and ideal orientation at every clock in this phase, including their source
error operands. The donor's immutable native rotation is already a result
at this exact clock in this graph. Its seed clock and finite recurrence
history may differ from a receiver's earlier cursor. The existing uniform
source allowance and maximum 126-product native recurrence bound cover that
history independently of its seed clock. No new approximation allowance is
introduced, and no donor value is installed in a receiver's persistent cursor
with unrelated step metadata. Its structural-zero flags remain those of the
complete native recurrence, whose seed disables structural-zero inference.
The receiver preserves its own current parent origin and composition depth.

Before reuse, the receiver charges its complete ancestry comparison, admits
the full live cap after the final callback, and reads every current source
witness without callbacks. It then checks the actual immutable rotation's
types, finiteness, magnitude and Boolean zero fields. Changed authority,
topology, law, source state or program identity cannot substitute a stale
curve. Cancellation and source refusal occur before any receiver cursor
publication; this path has no such publication. Optional initial witness
construction is now lazy: only a candidate carrier and its actual complete
ancestry are visited. An unrelated selected leaf has no body proof to use,
so its omitted witness construction provides no numerical credit or proof.
The final complete ancestry admission is retained for every receiver.

`tests/test_reach_recording_graph_sharing.py` covers equality and separation
of the full numeric recipes, selected pair indices, ordered fixed rotations,
current cap and cancellation, actual repeated-arm samples and work, lazy
ancestry scope, final callback source mutations, cache order and the separate
strict diagnostic. These definitions do not claim an executed release result.

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

## Direct projection of literal identity source leaves

The native `recording_constant_pose` can construct a source leaf directly
when all seven source components are actual finite binary64 values, the
rotation is exactly `(1,0,0,0)`, and each translation magnitude is at most
the existing `2^500` native position limit. The original domain checkpoint,
complete tuple-shape checks, inverse-selector check and current operand
admissions still precede this path. It requires the full 32,768-bit domain.
An inverse leaf is eligible only when all three source position values are
zero; every nonzero inverse retains the original rotated 96-bit projection.

For a forward leaf, the ordinary constructor first decodes each finite
binary64 translation into its exact rational value, then applies the source
binary64 projection to that same value. The result is therefore the original
binary64 value. An exact zero is canonically positive, including an authored
negative zero. There is no intervening translation-grid rounding in the
ordinary forward-leaf constructor. Its literal identity quaternion remains
the exact unit quaternion through private source normalization and public
projection, with structural flags `zero_w=False` and `zero_z=True`.
The zero-translation inverse has the same exact position and rotation.
Their result is a depth-zero native leaf with precisely these existing bits
and structural zero flags.

Every finite input rational representation fits 1,075 bits. At these literal
identity operands the original quaternion, zero-inverse and projection
preflights fit the full domain. The shortcut therefore cannot avoid an
original numeric-domain failure within its admitted range. Other source
types, rotations, excessive positions and nonzero inverses retain the
literal existing cached calculation and its failures.

This direct result executes no numerical conversion, rational reconstruction,
grid rounding, source transform construction, cache lookup or cache promotion.
Those omitted operations are consequently not charged. The original native
domain checkpoint remains charged and cancellable. Its callback completes
before the actual source tuples are captured; no callback occurs between
that fresh capture and returning the closed-form transform. There is no new
retained receipt or cache entry, and existing cache values and order are left
untouched. Narrowing the cap or cancelling at that checkpoint retains the
original refusal or exact callback exception.

[`test_reach_recording_identity_leaves.py`](../../tests/test_reach_recording_identity_leaves.py)
compares the retained cached path's actual bits for ordinary, subnormal,
signed-zero and maximum eligible positions, plus inverse and unsupported
operands. It also checks current-source mutation, cancellation, cache
preservation, the shared operation limit, and actual GLB byte/independent
validation equality. Execution evidence identifies the tested revision
separately; this derivation does not assert an unexecuted recording pass.

## Captured prescribed and free-root phases

The optional complete-phase sampler can retain immutable source inputs for
prescribed moving roots and actual selected free dynamic roots. It admits a
finite, strictly ordered sequence of interior exact clocks and the current
full 32,768-bit domain with the existing 256-entry cache. Source boundaries
still use the ordinary recorder. The captured graph contains source operands
and receipts; completed arithmetic remains in the existing work cache. A
phase retains only its required working constants and its latest private
cursor for each complete recipe, with the same 256-entry ceiling. All keys
must be consumed and all ordinary output callbacks must complete before that
cursor group can be published.

A prescribed root retains its complete current move/spin law and angular
source witness, including initial values, active claimant, status, exact
elapsed/running clocks, duration and ideal inputs. Its translation evaluates
the existing exact affine helper and binary64 projection. Its orientation
uses the existing scalar/Z spin helper and its complete copied source plan.
Spin increments multiply on the world side, and the existing 127-sample
native reseed ceiling is unchanged. A captured child body seed reads that
same copied source plan and the complete frozen angular lineage. Every source
plan field is admitted and compared again at publication; neither a temporary
law change nor a temporary plan mutation enters later numeric calculations.

Dynamic roots have no `RecordingAngularFrame`. Capturing one does not invent
an angular witness, rate proof or body-cursor token. The root must be an actual
selected free object with no incoming relation or prescribed claim. Its
separate receipt binds the actual anchor and force-history identities, exact
anchor and release clocks, complete private/native anchor operands and saved
public projections, scene duration and gravity, effective acceleration and
net force, active/latest force rows, anchor errors, error clock, ideal
acceleration and mass. Force rows retain their source target, activation,
key, vector, duration and sequence index; their original objects remain bound
as well. The finite row counts are checked and precharged before capture and
again before final admission. Dynamic descendants and unsupported rotations,
spins, anchors or history shapes keep the ordinary complete sampler.

A private anchor copy is assembled without intervening callbacks. Its public
position, velocity and omega are projected once by the original source
helpers, preserving materialized public bits. Only those actual source
operand tuples and the private initial rotation remain in the immutable
graph. This temporary projection object is discarded; no additional retained
projection cache is introduced. Later callbacks cannot replace a live anchor
field inside the captured calculation.

Each dynamic key evaluates the unchanged exact elapsed subtraction, original
ballistic law/extent proof and native `p0+t*(v0+a*t/2)` operation order. Its
current exact clock keeps the original small-operand admission and elapsed
horizon comparisons. The phase preflight already proves each key lies between
the same fixed endpoints. Every endpoint, anchor, duration and current clock
has at most 1,024 operand bits in this optional domain, so the omitted repeated
phase-membership cross-products fit the unchanged 32,768-bit cap. The existing
world-left spin recurrence consumes the copied anchor rotation, omega and
source plan. No actual ballistic product, addition, rounding, spin increment
or reseed is omitted from operation accounting.

The selected free root uses its actual whole-phase extent and the existing
dynamic `2^-47*(M+L+1)` position allowance. The complete source `Sp`, `Sq`,
path counts and offsets remain in the frozen allowance inputs. Each identical
phase allowance is computed once and retained only by that phase's existing
output stream; its source-bound object and every consumed field are checked
at completion. No tolerance or error expression changes.

Final source admission follows every publication callback and precedes the
atomic cache update without another callback. It compares the complete current
source fields, identities, topology, claims, plans, bounds and live domain.
Persistent changes reject the entire pending cursor group. Temporary changes
that are restored cannot affect calculations because those calculations use
only copied operands. Cancellation preserves the original exception and
publishes no partial group. A newer reentrant completion is retained rather
than overwritten by an older private group.

`tests/test_reach_recording_captured_roots.py` and
`tests/test_reach_recording_captured_dynamic.py` compare native bits and exact
allowances with ordinary scalar sampling, including both P16 release/force
phases, native reseeding, source mutations, unsupported descendants and
atomic callback failures. These are verification obligations; identified
execution evidence establishes which checks and full recordings have passed.

## Mixed complete-path captured phases

A source phase can contain both supported planar paths and paths that require
the ordinary recorder. P11 is such a composition: its arm hinges use the
scalar/Z kernel, while its head turns about Y and carries a nonzero child-site
offset and eye followers. A Y-axis source does not acquire a planar witness,
and no sampled head pose becomes a native parent.

The optional mixed wrapper applies only after the existing complete capture
declines. It runs the existing `_planar_paths` classifier on a frozen copy of
the actual classifier operands. Each copied dependency keeps its complete
current source witness, original object/action/runtime identities and actual
topology. The view supplies the same root modes and rotations, claimant spin
vectors and initial rotations, joint axes, child-site rotations, follow
rotations and frame ownership as the original classifier. All relevant input
fields are read without an intervening callback, copied before the next
callback and admitted again after classification. An unsupported mutable
shape, dynamic lineage or custom topology implementation declines the whole
optional wrapper. Both the visited graph and the selected tuple retain the
256-node/entry limit. Before copying any unselected source names or topology,
the optional domain also requires each object, site, joint, follow and action
collection, and the active grip set, to contain at most 256 entries. Larger
valid scenes keep the scalar sampler under the unchanged public limits.
The source maps retain their actual identities, and the bounded object/site
name sets are copied once and compared at final admission. A same-size rename
or replacement cannot change whether a selected dependency names an object
or a site. All retained extra records describe source inputs.

The resulting two tuples preserve their order in the original selection.
Every unsupported path calls the original, dynamically dispatched
`recording_frames` method at every exact key, with the same live state,
angular proof and phase context. Ordinary sampling runs before captured
native sampling, matching the previous partition. The merged output retains
the original ordinary-then-native order and every selected frame. The wrapper
retains no ordinary sampled position or orientation across keys. Ordinary
paths receive exactly zero additional native error; the captured paths use
their unchanged source and native arithmetic allowances. The original
boundary samples and strict-cell diagnostic route are unchanged.

Only the supported complete dependency paths enter the existing captured
graph. The full selection still determines its arithmetic-sharing choice.
Its immutable source operands, working constants, exact clocks, cursor
increments and reseeds remain the previously admitted implementation. If
that entire supported subset cannot be captured, the wrapper declines and
the complete selection uses the prior scalar partition. It never drops an
unsupported member of either tuple to obtain a partial success.

The native cursor group's final publication receipt additionally checks the
complete mixed source/classifier records, all ordinary allowance input
fields and original bound objects, current model/state/arithmetic ownership,
topology, active grips and operand domain. That callback-free comparison runs
after the last ordinary traversal, selected-pose output, hemisphere and cache
publication callback. A persistent mutation rejects the complete pending
native group. Temporary live changes cannot enter the copied classifier or
native operands. Ordinary paths continue to use the ordinary live evaluator
and its own admission; this wrapper does not claim to freeze their numerical
calculation. Cancellation keeps the original exception, changed cache limits
retain the existing fallback/publication behavior, and a newer reentrant
completion cannot be overwritten by the older group.

`tests/test_reach_recording_captured_mixed.py` specifies exact binary64 and
stored binary32 equality to the old P11 partition, allowance and output-order
equality, ordinary subclass dispatch, whole-selection fallback, immutable
classifier/native inputs, current source/bound/owner changes, cancellation,
cache changes and reentrant publication. Its source-to-GLB comparison uses
the actual frozen P11 program. Measured operation savings and recording
outcomes require separately identified execution evidence.
