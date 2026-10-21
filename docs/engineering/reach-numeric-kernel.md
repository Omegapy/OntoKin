# Production reach arithmetic and source pose basis

This is a separately identified implementation derivation for the adopted
OK-LANG-006/0.1.0 contract. It does not replace the frozen preparation oracle,
expected coordinates, quantization contract or release gate. Implementation
files are `ontokin/reach_numeric.py`, `ontokin/reach_kinematics.py` and
`ontokin/reach_pose.py`. The implementation's `source_numeric_basis` returns
their actual SHA-256 input identities, an ordered combined implementation
digest, this derivation's hash and the method identity
`ontokin.source-pose-projective-dyadic/0.1`.

## Scope and request work

`ReachExecutionWork` belongs to one compilation/evaluation/delivery request.
Its callback consumes the inherited remaining construction/Agent work and
checks cancellation once for every charged unit. Numeric work cannot reset
that inherited counter or claim a new allowance after compilation. Direct
evaluation must also use a bounded request object. The independent local cap
is 100,000 operations and 30,000 ms; callers may lower either. A count is a
declared bounded arithmetic/helper operation, not a CPU instruction count.
Fraction gcd and integer operations are additionally bounded by a conservative
32,768-bit preflight on inputs and unreduced intermediate widths.

Each outward interval operation is charged, as are its integer constituent
operations, exact Fraction helpers, binary encodings, rounding, square roots,
series recurrences, cache operations and pose projections. Precharged loops
call the inherited callback separately for every unit; a bulk construction
tick is insufficient because its outer callback may run only once. Expensive
integer square roots have cancellation checkpoints immediately before and
after them. The original callback exception propagates by identity. There is
no successful result or partially published pair on interruption.

The per-admission 12,000 `series_terms` count means recurrence steps: an atan
term or one paired sine/cosine recurrence. Initial terms do not constitute a
recurrence. The 100,000 interval-operation cap also accumulates over all
precision attempts. Extra exact and integer constituents consume the shared
request allowance in addition to these local ceilings. A shared-work,
deadline or operand-width failure is `reach_resource`. Failure to certify
after the five finite precision passes is `reach_numeric`. These are distinct
from exact geometry, frame, singularity and limit outcomes.

Caches are request-local, bounded to 256 entries, and may stop inserting when
full. Hits still check cancellation and consume lookup work. An IK hit rechecks
the current closed limits; topology, modes and claims always remain the
caller's fresh responsibility. Cached counters describe the current lookup,
not the historical solve. Actual source/Agent tests and execution logs must
identify their code revision separately from this derivation.

The source pose implementation additionally reuses immutable axis reductions,
stationary poses, stationary compositions and constant inverse frames in that
same bounded cache. Valid exact Fraction tuples are width-checked without a
redundant numeric decode. Zero vectors and identity rotations skip operations
whose exact results are already known. Sparse Hamilton products preserve the
dense formula's final exact rescale, sign and grid result. A scalar scale is
removed only after proving it is a nonzero signed power of two; other scalar
scales retain their exact products. No path assumes a unit quaternion. Grid
rounding is omitted independently for each component already exactly on the
grid, including exact zero; an off-grid sibling does not require rounding an
unchanged grid value again. The complete input tuple retains its width guard.
These paths retain the original canonical output bits and conservative error
records while charging their actual checks and executed arithmetic. They do
not reduce the IK counters, reset request work or promise that every scene
below the independent pose-count limit fits the shared operation allowance.

## Independently implemented correctly rounded IK

The retained proposal oracle uses Fraction interval endpoints. Production
uses outward **integer** endpoints at scale `2**p`, with the fixed schedule
96, 192, 384, 768 and 1536. It imports no proposal code or expected corpus.
Every source geometry binary64 is decoded exactly as a rational. The exact
closed annulus test precedes transcendental work. Equal lengths at the origin
are a separately classified singular shoulder.

For links a and b, target (x,y), radius squared r², and branch sign s, compute

```
c = (r²-a²-b²)/(2ab), d = 1-c², t = a+bc
X = tx + sby sqrt(d), Y = ty - sbx sqrt(d).
```

Scaling X and Y by positive r² improves interval conditioning without
changing their direction. The sign of a rational plus a rational radical is
resolved exactly using rational squares when signs oppose. Thus a narrow
outward interval cannot invent an axis or choose the wrong atan quadrant.
The elbow uses the signed angle `atan2(sqrt(d),c)`. The shoulder uses the
principal representative in [-pi,pi). A positive rounded Pi64 shoulder maps
to negative Pi64; elbow positive and negative Pi64 retain their branch signs.

Integer square root bounds use `isqrt(floor(n*2**(2p)/d))`, with exact-square
equality checked. Machin's identity bounds pi through outward alternating
arctangents. Reciprocal and pi/4 reductions bring every atan series argument
within [-1/2,1/2]. The omitted alternating term bounds its tail. All outward
operations retain their endpoint directions for negative and positive inputs.

Binary64 extraction rounds each exact interval endpoint with an independent
integer quotient and ties-to-even rule. If both endpoints round to the same
canonical encoding, monotonicity proves that the entire enclosure belongs to
that binary64 rounding cell. This includes midpoint parity, binade changes,
subnormals and the canonical positive-zero cell. A single unconstrained
floating approximation would not establish this property.

The canonical pair is then checked against actual closed joint limits before
any forward-residual series. Sine/cosine Taylor enclosures on [-8,8] use fixed
precision-specific degrees and an explicitly checked Lagrange remainder.
The upper bound of the rounded pair's real forward residual squared must be
at most 10^-18 m². No limit clamp, nearest approximate branch, tolerance-based
annulus or unbounded precision retry is used. The solver certificate is not a
claim about the complete scene's evaluated source pose.

`sample_pair` retains the exact rational clock and exact slope
`(canonical_target-canonical_start)/duration`. It rounds the inspection
coordinate and inspection rate separately once. Pose composition consumes
the exact slope. Held states expose zero rates. Event ordering and atomic
two-coordinate claims remain evaluator obligations.

## Controlled proper rotations

The source kernel uses projective quaternions: a nonzero private q represents
the proper rotation `v -> vector(q*(0,v)*conjugate(q))/(q dot q)`. It does not
use a unit-quaternion matrix with an approximately unit q. Consequently the
private rotation's non-rigid operator defect is exactly zero.

Quaternion multiplication uses exact rational Hamilton products. An exact
power-of-two rescaling places the largest component in [1/2,1), followed by
round-to-nearest-even on a 96-bit dyadic grid. A half-grid rounding is
rho = 2^-97. The four-component perturbation norm is at most 2rho = 2^-96.
The unrounded rescaled norm is at least 1/2, so the relative perturbation is
at most 2^-95. For nonzero vectors a and a+e, normalization changes direction
by at most `2*||e||/||a||`; converting unit-quaternion chord distance to SO(3)
angle adds a factor below three in this range. Thus the conservative
`2^-91` radians per import/product safely bounds the actual rounding error.
Canonical sign selection changes no rotation. Inverse conjugation is exact.

If either Hamilton operand is the exact scalar quaternion `(s,0,0,0)` with
`s = +/-2^k`, its dense product is `s*q`. The power-of-two scale chosen from
`max(abs(s*q))` cancels `abs(s)` exactly. Nearest-even rounding is odd under
sign reversal, including ties, and the final canonical sign cancels `sign(s)`.
Thus applying the same rescale to `q` gives identical grid components. A tuple
is returned directly only after checking that all four components are exact
Fractions on the 96-bit dyadic grid, its maximum is in `[1/2,1)`, and its first
nonzero component is positive. Off-grid tuples, negative first components,
and a maximum rounded to exactly one use the ordinary rescale. Both paths
still add the incoming error allowances and the unchanged `2^-91` product
allowance, clear any materialized public projection, check operand widths,
and charge their actual canonical/grid checks. Non-power-of-two scalar
quaternions keep the exact multiplication path.

Every homogeneous rotation dot product and division is exact rational
arithmetic, followed by one 96-bit dyadic rounding per output component.
Its Euclidean vector perturbation is at most sqrt(3)rho < 2^-96 in the
vector's units. Addition stages that round a resulting vector each incur
the same bound. Private positions, orientations and derivatives survive
through the whole parent-child chain; reading a public projection cannot
change subsequent private composition.

In spatial derivative composition, a canonical immutable zero local velocity
has exactly zero rotated velocity. Omitting that term leaves the parent's
velocity plus its angular-velocity cross the already computed world offset.
If either that offset or the parent's angular velocity is the canonical zero
tuple, this cross term is also exactly zero. A canonical zero local angular
velocity similarly leaves only the parent's angular velocity. Shortened paths
still validate the surviving parent vectors and apply the same final 96-bit
grid projection: a non-dyadic parent rate or a value at a half-grid tie cannot
be returned without that rounding. Noncanonical vectors use the original
validating helpers. These reductions retain the complete operand width guard,
position/rotation construction, cache identity, conservative position-error
propagation and charged cancellation decision. No derivative-only shortcut
changes the original position or rotation allowance.

Axis normalization at the fixed 96-bit precision depends only on the exact
axis, not the requested angle. Its immutable grid tuple is reused through the
same bounded request cache after validating the current axis again; hits
retain their cancellation and work checks. On a miss the existing scaled
axis and outward square-root enclosure still determine the same midpoint,
exact component divisions and nearest-even grid values. When that enclosure
is exactly `[1,1]`, the scaled vector's norm is exactly one. Scaling by its
largest component already makes at least one component have magnitude one,
so every other component must be zero. The signed principal-axis tuple is
already a 96-bit grid value and is the exact result of the omitted division
by one and grid projection. Zero axes remain inadmissible, including at zero
angle. The rotation's existing axis and product error allowances are
unchanged, and no angle-dependent state or result from another request is
reused.

For an exact quaternion with one nonzero imaginary component, let that axis
be `a`, and let `(u,v)` be the cyclically ordered transverse vector components
`((a+1) mod 3, (a+2) mod 3)`. With scalar `w`, axial component `z`, and
`d = w^2+z^2 > 0`, the dense homogeneous matrix reduces exactly to
`(u,v) -> (A*u-B*v, B*u+A*v)`, where `A = (w^2-z^2)/d` and `B = 2*w*z/d`.
The axial component is unchanged. This formula is valid for all three axes,
either sign, and nonunit scales. The same final grid projection follows all
executed exact products and sums; a vector already on the axis needs only
that projection. General homogeneous matrix products can omit exact zero
terms for the same reason. These reductions do not change pose-error
propagation, source observations or the independent destination comparison.

Public quaternion components are each rounded from the exact normalized
private component `sign(q_i)*sqrt(q_i²/(q dot q))`. Integer square root plus
an exact squared-midpoint comparison proves nearest-even binary64 extraction.
No `math.sqrt`, `math.hypot`, `math.sin`, `math.cos`, libm accuracy assumption
or machine-epsilon guess supplies the source proof.

The projection checks all component widths before its bounded cache lookup.
For each nonzero component it computes the exact square once, uses the
nonzero squares to form the exact positive denominator, and reuses that
component's square in the normalized ratio. Zero terms and the initial
addition to zero are exact identities, so omitting them changes no rational
operand passed to the correctly rounded square-root extractor. An exactly
zero component gives canonical positive binary64 zero; this is also the old
extractor/sign rule's result. Each such return still charges a cancellation
checkpoint. The all-zero quaternion remains invalid, and a cancelled partial
projection is never published to either cache. Materialized anchors retain
their separately charged, already exposed bit pattern, including any signed
zero. None of these exact reductions changes the exposed-rotation allowance.

Each unit component has absolute binary64 error at most 2^-54. The vector
error is at most 2^-53, and the resulting projective SO(3) error is safely
below **2^-50 radians**. This is charged even though most actual errors are
smaller. If a destination later uses a naive nonunit-quaternion matrix, its
additional defect is not zero: it must separately bound
`||M_naive(q)-R(q)|| <= 2*|q dot q-1|` and multiply by the relevant source and
stored local radius. The proper-rotation source result does not waive that
destination term.

## Finite source trig and spin phase reduction

Source pose trigonometry has a separate purpose from IK target rounding: it
needs a rigorously bounded uniform approximation. It uses 13-term sine and
cosine polynomials after certified pi/2 range reduction. Their coefficients
are exact factorial rationals; the variable is rounded onto the 96-bit grid,
and the square of that grid variable is kept exact. Every Horner multiply-add
and the sine's final multiplication are exact rational arithmetic. Each final
sine/cosine value is rounded once to the 96-bit grid.

The coefficients run from k=0 through k=12. The exact polynomials have degrees
25 for sine and 24 for cosine. Their alternating terms decrease in absolute
value on |x| <= 1, so the first omitted terms bound their respective tails by
1/27! and 1/26!. Negative sine arguments have the same absolute bound by
oddness; cosine is even. No coefficient is rounded before evaluation,
including the highest coefficient that initializes Horner's rule.

There are no intermediate arithmetic errors: the coefficients and all twelve
Horner multiply-adds are exact, followed by one nearest-even grid projection
per function. Thus **rho** is a common arithmetic allowance, and **1/26!** is
a common truncation allowance. The exact polynomial and final grid projection
depend only on the admitted argument, including after cache eviction or a
different request history. Avoiding intermediate projections changes some
private approximation bits within the unchanged published error allowance;
fresh implementation and derivation hashes identify the executed algorithm.

The helper explicitly admits only exact Fraction values x with |x| <= 1 and
denominator 2^b, 0 <= b <= 96. Every coefficient denominator divides 25!, and
25! < 2^84. A partial polynomial with m remaining powers of x² therefore has
a denominator dividing `25! * 2^(2*b*m)`, m <= 12. Its absolute value is below
two: the sum of the absolute cosine coefficients is less than
`1 + sum(2^-k, k>=1) = 2`, and the sine coefficients are no larger. The
largest inner denominator consequently has at most 2,388 bits and its
numerator at most 2,389 bits. The completed sine denominator divides
`25! * 2^2400`; the cosine denominator divides `24! * 2^2304`.

The existing prospective guards run before every exact operation. Even using
the full 84-bit factorial denominator for each add, the largest guarded
cross-product bound is at most 2,474 bits. The final multiplication by x has
prospective width at most 2,486 bits; its reduced result's numerator has at
most 2,485 bits. Final 96-bit grid extraction, including the integer quotient
guard, requires at most 2,582 bits. All are below 2,600 and the unchanged
32,768-bit request maximum. A caller's smaller operand limit still applies to
every executed intermediate. No enlarged limit or hidden fallback is used.
Completed grid results and immutable coefficient tables use the bounded
request cache. Every executed recurrence, exact operation, final projection
and coefficient construction charges the same request and cancellation
callback.

### Exact paired integer evaluation

The same two polynomials can be evaluated together with integer arithmetic
when the caller's operand limit admits the complete packed layout. This is
an exact change of representation, with the original Fraction recurrence
retained for smaller operand limits. It does not change the argument grid,
polynomial coefficients, degree, final projection or error allowances.

Write the reduced grid argument as `x = n/d`, where `d = 2^e`, and put
`N = n^2`, `D = d^2`, `m = 12` and `M = 25!`. The nonnegative integers
`a_k = M/(2k+1)!` and `b_k = M/(2k)!` are exact. Define the integer Horner
numerators by

```
S_m = a_m,                     C_m = b_m,
S_k = a_k * D^(m-k) - N*S_(k+1),
C_k = b_k * D^(m-k) - N*C_(k+1).
```

Then the original sine polynomial is `x*S_0/(M*D^m)` and the original cosine
polynomial is `C_0/(M*D^m)`. Since `0 <= N <= D` and both factorial coefficient
sequences are nonincreasing, downward induction gives
`0 <= S_k <= a_k*D^(m-k)` and `0 <= C_k <= b_k*D^(m-k)`.
This also covers `x = 0`, `x = +/-1` and `d = 1`.

Choose `B = bit_length(M) + 2*e*m + 1`, so `2^B > M*D^m` strictly.
The single recurrence

```
H_m = (a_m << B) + b_m,
H_k = (((a_k << B) + b_k) << (2*e*(m-k))) - N*H_(k+1)
```

has the exact invariant `H_k = 2^B*S_k + C_k`. Multiplication may carry
between lanes temporarily, but the integer identity and the proved final
lane bounds give `divmod(H_0, 2^B) = (S_0, C_0)` without approximation.
Two exact Fraction constructions, the original final multiplication by x
and the original two nearest-even grid projections therefore reproduce every
output bit of the Fraction recurrence.

All packed allocations and arithmetic are preflighted before construction.
The conservative bound `2*B + 2*e + 4` covers coefficient shifts, the full
integer product, subtraction and extraction. With `e <= 96`, it is below
5,000 bits and the unchanged 32,768-bit maximum. The fast path also requires
`2*bit_length(M) + 2*e*m + e + 96 + 16` bits, which dominates the original
Fraction path's prospective cross-products and final rounding: every reduced
partial denominator divides `M*D^(m-k)`, its numerator has at most one extra
bit by the absolute-value bound above, adding a factorial coefficient adds
at most `bit_length(M)+1` prospective bits, multiplication by x adds at most
`e+1`, and grid extraction adds at most `96+2`. Thus the fast path cannot
newly admit an operand limit for which the old arithmetic would reject.
If either bound exceeds the actual caller limit, the original Fraction path
runs with its original operation-by-operation guards and diagnostics.

An immutable table of the thirteen shifted integer coefficient pairs is
keyed by method, term count, reduced denominator exponent, lane width and
current operand limit in the same 256-entry request cache. Its values are
width-checked again on use. Each executed integer division, shift, packing
addition, multiply, subtraction, extraction and Fraction construction is
precharged, as are recurrence and cache operations. Cancellation propagates
unchanged, and an incomplete table or result is never inserted.

When both complete bounds for `e = 96` fit the actual operand cap, a smaller
reduced denominator is promoted exactly to that one common layout by shifting
its numerator by `96-e`. This shift is width-checked and charged before
allocation. The final sine multiplication still uses the original exact x.
All ordinary grid arguments can then reuse one table; the unchanged smaller
cap path still uses its actual reduced exponent or the Fraction fallback.

Pi is enclosed with exact alternating sums in Machin's identity, with a
fixed term count for each permitted precision, then outwardly projected to
that precision's dyadic grid. The reducer chooses an integer quadrant from
the midpoint. It need not prove that this is the unique nearest quadrant:
it directly proves the chosen reduced argument lies within the polynomial
range. The exact reduced argument must be within **2^-86 radians** of its
grid representative. Restoration by permutation and sign changes is exact.
Sine and cosine are 1-Lipschitz, and the exact rational inequality

```
2^-86 + 2^-97 + 1/26! < 2^-80
```

proves the stated component error for every admitted source angle. The direct
|angle| <= 1 path has at most rho input-rounding error, already smaller than
the common 2^-86 argument allowance. Rounding an input in [-1,1] to this grid
cannot leave that interval because both endpoints are grid values. The
separate exact target-admission series and its rounding proof are unchanged.

An axis is scaled by its largest absolute component before its norm is
bounded. Its scaled norm is in [1,sqrt(3)], so division cannot become
ill-conditioned. The midpoint norm and 96-bit unit-axis rounding contribute
far less than the 2^-80 trig component allowance. Converting the resulting
four-component quaternion perturbation to SO(3) error is bounded by
**2^-74 radians** per axis/spin constructor; subsequent projective rescaling
also incurs the separately counted product allowance.

For a spin, the kernel never rounds `norm(omega)` or `norm(omega)*elapsed`
through binary64. Let m=max|omega_i|, u=omega/m and lambda=||u||. A phase plan
bounds lambda, pi and the maximum absolute elapsed time T. Its half-angle is
`m*lambda*t/2`. If lambda interval width is Dlambda and pi width is Dpi,
the chosen quadrant satisfies

```
|k| <= floor(m*T*lambda_upper/pi_lower)+2 = K.
```

The reducer's total argument uncertainty is bounded uniformly by
`(m*T*Dlambda + K*Dpi)/4 + rho`. The phase plan is admitted only if this is
at most 2^-86. Every sample verifies it belongs to that exact omega and time
range, then also verifies the actual reduced enclosure. The fixed precision
schedule ends in an explicit numeric failure if the bound remains unproved.
There is no hidden enlargement of the source domain or unbounded fallback.
An extremely large input may instead consume the shared work or operand cap;
that is correctly classified as a resource failure.

`spin_plan(omega,T)` is a uniform phase certificate. Calling `spin_rotation`
without a plan proves only its requested point using |elapsed| as T. A
recording planner must supply or separately derive the whole phase bound.

## Spatial derivatives, release and continuous bounds

For a parent and local pose, composition uses

```
p = p_parent + R_parent*p_local
v = v_parent + omega_parent cross (R_parent*p_local) + R_parent*v_local
omega = omega_parent + R_parent*omega_local.
```

Products and sums use guarded exact arithmetic before private grid rounding
and final binary64 extraction. Hinge angular velocity is supplied from the
exact coordinate slope. Root affine/parabolic helpers retain exact rational
elapsed times. A release does not substitute the solver's endpoint for the
actual evaluated frame. `relative_point` uses the private base rotation and
position to evaluate the actual tip in that base frame, avoiding a separate
rounded world inverse.

After both complete private three-vectors have been validated, the charged
fixed-size vector zero check also identifies exact zero components in mixed
vectors. The identities `0 + y = y` and `x + 0 = x` permit reusing that
component's exact Fraction instead of performing an addition. Every pair of
nonzero components still takes the guarded exact addition, and any subsequent
grid projection is unchanged. This does not infer that an entire vector is
zero from only one component or admit unchecked public inputs.

When all four input derivative tuples are validated exact zero vectors, both
derivative expressions above are exactly zero: a zero cross product and a
rotated zero vector remain zero before and after every grid projection. The
composition may therefore return that same exact zero tuple without executing
the derivative-only helpers. The immutable private `ZERO` establishes this
directly. Other tuples first receive charged dimension and numeric-domain
checks before any cache lookup; numerical equality alone cannot admit boolean
components or a short zero tuple. The composition still guards
every input operand, checks and charges its work, and computes the identical
position, rotation and conservative error records. Pose-only recording uses
these exact zero derivatives internally without exposing them as source rates;
complete source evaluation continues to compute actual moving-frame rates.

After the recording planner has validated the complete source prefix and
derived every whole-phase bound, key sampling needs only actual position and
orientation. Its separate `RecordedTransform` type retains exact position,
the private `RotationValue`, and their canonical projections. Composition
executes the same homogeneous rotation of the local offset, exact parent
translation addition, final 96-bit grid projection, and quaternion product
(including the original rotation-error recurrence). Spatial derivatives and
the sampled position-error recurrence do not enter either p/q equation, so
this path does not construct them. The result deliberately has no derivative
or position-error fields and is rejected by full source pose composition.
It occupies a separate recording slot namespace and cannot enter the complete
kinematics cache. Complete boundary validation, terminal observations, release
anchors, whole-phase error formulas, every retained key, and independent
supplied-byte verification continue to use their existing paths and bounds.
This is an omission of unused sampled calculations, not a zero-error claim.

`materialize` deliberately freezes all four actual exposed state tuples at
an event anchor. Its elapsed-zero successor returns those exact orientation
bits without another normalization. It retains a private projective proper
rotation and adds the explicit exposed-orientation discrepancy to its error
record. Its position rounding discrepancy is computed exactly and added.
Deepcopy returns the immutable pose value itself, never a copied compiler,
request counter or cancellation callback. The evaluator still must propagate
anchor discrepancies across stops, replacements, releases and dynamic phases.
An anchor reset is not proof that two independent ideal phase formulas agree.

Suppose R is a rotation error bound in radians, P a position error bound,
and L the L1 norm of a private local position. For one composition,

```
R_new <= R_parent + R_local + 2^-91
P_new <= P_parent + P_local + L*R_parent + 2*2^-96.
```

The matrix difference of two proper rotations is at most their relative
angle. Using the private local position in the radius term is valid by
writing the discrepancy as an orientation difference applied to that private
vector plus the rotated local position error. Two vector-rounding stages
account for offset rotation and final position addition.

The full charged composition operand guard precedes each caller's position
error calculation. When both private input errors are Fractions and either
is exactly zero, their inherited sum is exactly the other input and needs no
arithmetic operation. The final addition of the offset allowance remains
guarded and charged even for a cached relative composition. Both nonzero
errors retain their original exact addition. The resulting error bound,
rounding allowances and its dependence on each caller are therefore identical.

For complete continuous phases, `uniform_source_bounds` requires actual path
counts, sum of whole-phase local offset L1 extents, coordinate-rounding
allowances, propagated anchor position/rotation errors and a whole-phase L1
position extent M. It uses the conservative closed formulas

```
R_internal = R_anchor + R_coordinate + N_trig*2^-74 + N_product*2^-91
P_internal = P_anchor + L_total*R_internal + N_vector*2^-96
n_sr = R_internal + 2^-50
n_sp = P_internal + M*2^-53 + 3*2^-1075.
```

Every rescale/import is included in N_product, including the one performed
inside an axis/spin constructor. N_vector covers every rounded position-vector
stage. L_total sums every relevant local offset extent on the path. Using
the final maximum angular error at every offset is conservative. A binary64
rounded hinge coordinate in [-Pi64,Pi64] contributes at most 2^-52 radians;
if exact unrounded coordinates drive the source pose, that particular term
is zero. The caller must describe which expression is the ideal reference
and charge the actual source-reference difference.

For a finite exact value x, nearest-even binary64 absolute error is bounded
by `2^-53*|x| + 2^-1075`, including subnormals. The three-coordinate L1 sum
therefore bounds Euclidean position extraction by the expression above.
These are magnitude- and path-dependent bounds, not universal small constants
for arbitrarily distant or deeply nested scenes. An optional radius r returns
`point_m = n_sp + r*n_sr`; stored vertex and matrix terms remain separately
required by the adopted quantization contract.

The point helper `source_bounds(pose,...)` cannot certify unsampled phase
offsets merely because its final projection extent is uniform. Its API and
documentation explicitly retain that distinction. The exporter must derive
all whole-phase arguments from its actual analytical source path, including
both sides of positive-width event neighbors and exact unrounded slopes.
Unproved or disconnected ideal anchors must fail explicitly.

## Identified implementation and derivation aggregates

The source numerical basis identifies the complete controlled arithmetic and
the phase/anchor recurrence that supplies its uniform inputs. Its ordered
implementation input list is:

1. `ontokin/reach_numeric.py`
2. `ontokin/reach_kinematics.py`
3. `ontokin/reach_pose.py`
4. `ontokin/reach_phase.py`
5. `ontokin/reach_runtime.py`

Its separately ordered derivation input list is:

1. `docs/engineering/reach-numeric-kernel.md`
2. `docs/engineering/reach-source-kernel.md`

For each input, compute the lowercase hexadecimal SHA-256 of its exact bytes.
For each list separately, concatenate the ASCII records
`path + NUL + hex_sha256 + newline` in the listed order, then take the SHA-256
of those concatenated bytes. The implementation and derivation identities are
respectively these two aggregate hashes, each prefixed by `sha256:`. Individual
input digests remain available in the immutable basis record. No file embeds
its own digest. Missing files or a file exceeding 262,144 bytes fail explicitly;
bounded reads, hashing and cache lookups consume the same request work.

The independent supplied-byte reader reconstructs the two lists and aggregates
without calling the writer's identity helper. The execution procedure must
preserve these exact input bytes throughout one request; a request-local cache
does not authorize changing code or derivations during execution.

## Verification and remaining scope

The focused tests retain the original 54 target encodings, exact geometric
classifications, closed-limit ordering, cache cancellation, halfway parity,
subnormals, huge-operand precharge and shared callback accounting. Pose tests
compare separate source polynomials against the retained independent rational
oracle, prove the polynomial error inequality exactly, check private chain
composition, exact slopes, uniform phase identity, anchor bit preservation,
explicit finite failure and source-basis hashes.

Executed results and code hashes are recorded in subsequent identified
implementation checkpoints; merely writing these tests is not a pass. This
derivation does not establish completed lifecycle integration, all Agent
operations, delivery/native/browser behavior, compatibility roles, the finite
release or the full OntoKin goal. Those remain independently measured gates.
