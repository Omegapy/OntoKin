# Production reach arithmetic and source pose basis

This is a separately identified implementation derivation for the adopted
OK-LANG-006/0.1.0 contract. It does not replace the frozen preparation oracle,
expected coordinates, quantization contract or release gate. Implementation
files are `ontokin/reach_numeric.py`, `ontokin/reach_kinematics.py` and
`ontokin/reach_pose.py`. The implementation's `source_numeric_basis` returns
their actual SHA-256 input identities, an ordered combined implementation
digest, this derivation's hash and the method identity
`ontokin.source-pose-projective-dyadic/0.2`.

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

For canonical integer endpoint cells, sign monotonicity selects the same
product and quotient extrema as evaluating all four corners. If at least one
product interval does not cross zero, only its two extremal products and two
outward divisions are computed. Two point cells require one product. A divisor
interval that excludes zero likewise requires only the two extremal scaled
quotients, with integer floor for the lower bound and negative floor of the
negative ratio for the upper bound, including negative denominators. Products
of two cells that both cross zero retain the original four-corner calculation.
Exact zero and scale-one identities omit all unchanged scalar arithmetic.
Squaring a cell containing zero requires only the largest endpoint square and
its upward division. These are exact replacements of the original outward
integer cells; they introduce no narrower assumed error or changed tolerance.

Every call retains its interval-operation charge and the original complete
input and prospective-width guard, including the widths of omitted corners.
Thus an exact zero cannot make an oversized sibling admissible. Constituent
charges cover the arithmetic actually performed: four for two selected
products or scaled quotients and their outward divisions, three for one point
product and both divisions, and two for a single upper square and division.
The ordinary interval charge covers the bounded endpoint/sign selection.
All constituent callbacks run before allocation, and the complete original
operand/width guard is repeated afterward to enforce a changed live cap.
Callback exceptions retain their exact identity. No cache is added, and the
per-admission interval/series counters and request limits are unchanged.

Caches are request-local, bounded to 256 entries, and may stop inserting when
full. Hits still check cancellation and consume lookup work. An IK hit freshly
checks the current closed limits: the geometry-only proof compares its targets
against those limits, while the complete proof described below admits all four
actual limit bit patterns as part of its key. Topology, modes and claims always
remain the caller's fresh responsibility. Cached counters describe the current
lookup, not the historical solve. Actual source/Agent tests and execution logs
must identify their code revision separately from this derivation.

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

### Exact integer planar arithmetic

The scalar/Z Hamilton product and each single-axis homogeneous rotation may
use bounded common-denominator integers. This is an exact evaluation of the
same rational formulas and the same final 96-bit nearest-even projection. It
adds no approximation, changes no angular or position allowance, and does
not reassociate a sequence of quaternion compositions. The general rational
algorithm remains the fallback.

The integer path admits only exact `Fraction` components on the existing
2^-96 grid, quaternion components of magnitude at most one, and the full
32,768-bit operand cap. A vector component, when expressed as an integer
multiple of 2^-96, must have at most 256 bits. The ordinary public operand
checks run before every cache lookup. A bounded charged domain check selects
the integer algorithm; any other value, scale, grid or cap uses the original
rational arithmetic and its original prospective-allocation checks.

For a scalar/Z product, write the two nonzero component pairs as
`(Aw,Az)/2^ea` and `(Bw,Bz)/2^eb`, with `ea,eb <= 96`. The exact Hamilton
numerators are `W=Aw*Bw-Az*Bz` and `Z=Aw*Bz+Az*Bw`. They share denominator
`2^(ea+eb)`. Let `L=bit_length(max(abs(W),abs(Z)))`. The old power-of-two
rescaling sends the exact pair to `(W,Z)/2^L`: its scale cancels the shared
input denominator exactly. Therefore the old final grid integers are exactly
nearest-even of `(W,Z)/2^(L-96)` when `L>96`, the unchanged pair when `L=96`,
or the exact left-shifted pair when `L<96`. The original canonical sign is
applied after rounding. Negative halfway cases retain the same even parity.
The result still adds both operand error allowances and one `PRODUCT_ERROR`;
it clears the frozen projection just as the ordinary product does.

For a single-axis quaternion, use one common dyadic denominator for its
scalar and axial components and call the resulting integers `w,z`. That
denominator cancels from all homogeneous rotation factors. Keep the exact
integer triple `C=w*w-z*z`, `S=2*w*z`, `D=w*w+z*z`, where `D>0`. For the two
perpendicular vector components `U/2^96,V/2^96`, the old unrounded outputs are
`(C*U-S*V)/(D*2^96)` and `(S*U+C*V)/(D*2^96)`. Their final grid integers are
therefore exactly nearest-even of `(C*U-S*V)/D` and `(S*U+C*V)/D`. The same
cyclic axis order and exact-zero branches are retained. The axial component
is already on the grid and is unchanged. The formula works for either sign,
zero scalar component, and nonunit projective scales in the admitted domain.

Every executed integer multiplication, addition, subtraction and left shift
has a precharged cancellation checkpoint and a prospective width guard. Each
nearest-even quotient uses the same bounded `divmod` and parity rule as the
ordinary integer-rounding primitive. Its arguments already represent grid
integers, so no separate 96-bit numerator shift is executed. Exact `Fraction`
construction from the rounded integer and the fixed grid denominator is
guarded within the rounding or canonical-result checkpoint. The domain,
scale and sign steps are also charged. No arithmetic skipped by the exact
algebra is charged as though it were still executed.

Each admitted quaternion integer has at most 97 bits. Hamilton products and
their sums need fewer than 196 bits, and the final grid integers need at most
97 bits. The original rational Hamilton products, cross-denominator addition
preflights, exact rescale and grid projection are all below 512 bits in this
domain. For vector rotation, `C`, `S` and `D` have at most 194 bits, the scaled
vector integers at most 256, the product/sum preflights at most 451, and the
nearest-even quotient preflight at most 452. The old rational factors need
at most 194 numerator/denominator bits, their vector products at most 450
numerator and 291 denominator bits, their unreduced addition preflight at
most 742 bits, and their final grid shift at most 548. These are all below
1,024 bits and hence below the unchanged full cap. Thus the new algebra
cannot admit an operand that the omitted old rational operations would have
rejected within this domain. Error-allowance arithmetic is still performed
by the original exact helper.

The integer rotation factors replace the two rational factors in the same
single bounded `axis_rotation_factors` LRU entry. Its tag prevents shape
confusion. A later off-grid vector replaces that entry with the original
rational representation, and later grid vectors may reuse that rational
entry. There is no second per-quaternion slot, new cache, or retained numeric
map. Product, factor, rotated-vector, raw-normalization and general-matrix
keys include the method, complete numeric operands and originating cap. A
callback that changes the cap before
an integer operation causes the rational fallback; a change during lookup
or publication restarts from the ordinary operand guards under the current
cap. The restart retains the original inputs, so a small normalized quaternion
cannot hide an oversized raw quaternion after its normalization cache narrows
the cap. Every restart consumes the existing request budget. Callback exceptions
propagate by identity, including an exception whose type matches the private
fallback signal.

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

## Finite recording-only rotation recurrence

Version 0.2 adds a distinct sampled-transform algorithm. Complete source
evaluation, exact canonical joint coordinates, release/boundary anchors,
rates and the continuous source bounds above retain their direct evaluator.
Only recording samples in one fixed source phase may use rotation increments.
The implementation and derivation aggregate also identifies `reach_export.py`,
which supplies the finite sampling context and endpoint error certificates.

For a fixed axis a and the actual canonical binary64 joint angles c_i, the
increment is the **exact rational difference** `d_i = c_i - c_(i-1)`.
It is not a second rounded coordinate or a rounded approximation to the
authored rate. Fixed-axis rotations obey
`R(a,c_i) = R(a,d_i) R(a,c_(i-1))` exactly. The first sample uses the ordinary
axis constructor. A following sample composes its ordinary increment rotation
with the previous private quaternion, using the same guarded exact Hamilton
product and projective grid projection as every other source composition.
For a fixed world angular velocity, exact elapsed differences obey the same
group law; a direct first orientation already includes its immutable initial
orientation. Its original SpinPlan must certify each current elapsed value
and every evaluated increment. Changed angular velocity, initial orientation
or phase plan cannot reuse a different cursor.

Let A = 2^-74 and P = 2^-91. One direct axis/spin constructor contributes at
most A+P in rotation angle. Each subsequent increment and its composition
contribute at most A+2P. Bi-invariance and the triangle inequality for proper
rotation distance therefore bound j successive increments by
`(j+1)*A + (2*j+1)*P`, plus any original initial-orientation allowance.
The source bound already counts the direct seed and its ordinary surrounding
products. With at most K samples per cursor, the additional angular error is
at most `(K-1)*(A+2P)` per trigonometric occurrence. A zero increment has no
additional error; counting it as a step is conservative. The implementation
reseeds directly before a cursor would exceed K, where
`1 <= K <= MAX_KEYFRAMES = 10000`. Cache eviction also reseeds directly and
cannot enlarge this bound.

For a complete source path, the recorded endpoint excess is

```
Delta_R = N_trig * (10000-1) * (2^-74 + 2*2^-91)
Delta_P = L_total * Delta_R.
```

Every private sampled rotation remains a proper rotation, so the existing
orientation-independent position extents, vector grid errors and public
projection bounds remain valid. Applying the maximum additional angular error
at every local offset bounds all descendant carrier-origin shifts by Delta_P.
The final certificate separately multiplies its complete angular error by
the promised landmark/vertex radius, covering local points as well as carrier
origins. Unit-quaternion chord discrepancy is at most the corresponding
rotation angle, so using Delta_R itself as the endpoint quaternion excess is
conservative. No unit-quaternion or zero-radius assumption removes that term.

The exporter takes maxima of these excesses over every phase admitted for the
group's actual endpoints, including an adjacent after-state. It adds Delta_P
and Delta_R to the measured binary64-to-binary32 endpoint errors **before**
the existing direct-source allowances are added and before computing the
stored-arc and interpolation certificates. All maxima, exact operations and
outward projections retain their existing guards and charged work. The
continuous `n_sp`/`n_sr` evaluator allowances and the quarter-allocation
inequalities are unchanged. The independent reader evaluates every stored
endpoint against its independently reconstructed ideal source pose and
rejects an insufficient endpoint claim; it does not trust the producer's
recurrence or path counts to establish that comparison.

One fresh opaque context identifies each source phase in each baking pass.
Cursor keys include this context, source path, complete axis or initial
orientation/angular velocity/phase-plan operands, finite step ceiling and
current operand cap. All cursor and increment values use the same existing
256-entry request LRU; no separate numerical map or allowance is introduced.
Every warm call rechecks input widths and cancellation. Spin calls recheck
the complete current elapsed/omega/plan domain before reusing an increment.
Only a fully computed value can replace a cursor. Cancellation leaves no
successful recording or partially published arithmetic result.

If a caller changes the operand cap on an existing work context, the next
lookup/insertion first invalidates that context's complete LRU under a charged
cancellation checkpoint. This includes nested direct-axis, sine/cosine and
product results, whose original keys predate the recording cursor. Therefore
an identical previously warmed angle cannot bypass a newly narrower domain.
Cancellation before invalidation leaves the prior cache untouched. Normal
fixed-cap requests retain the same lookup/insertion charge and capacity.

## Recording identity products

The separately identified recurring recording sampler may omit a Hamilton
product when either actual projective quaternion is `(w,0,0,0)` with nonzero
`w`. Its represented proper rotation is exactly the identity, independently
of the sign and scale of `w`. The result keeps the other quaternion's exact
components and any already materialized projection. It retains the **sum of
both input angular error allowances**: an actual identity rotation can still
have an uncertain ideal orientation. There is no new `PRODUCT_ERROR` because
this path allocates no quaternion product or quaternion grid projection.
The triangle inequality for the rotation metric proves the retained sum.

Position arithmetic keeps its original exact terms and 96-bit projections.
For a zero local translation, it projects the parent position directly; for
an identity parent rotation it uses the projected local translation directly.
These are the same values that the original rotation/addition helpers return.
Other translations execute the ordinary guarded homogeneous rotation. When
both rotations are nonidentity, the entire original composition executes.
Thus the existing uniform vector and product error counts remain conservative;
the endpoint recurrence excess and continuous source allowances are unchanged.

The fast path checks both complete private positions, quaternions and angular
allowances before elision, rejects a zero quaternion, and is limited to
immutable values owned by the current request at the adopted 32,768-bit cap.
Narrower caps, foreign ownership or other input representations execute the
original guarded composition. Cancellation is checked before inspecting or
publishing a result. No new numerical cache is introduced. Full source poses,
their derivatives, anchors and the direct recording algorithm retain their
original multiplication/projection sequence.

## Finiteness of unused recording-boundary projections

Complete recording-boundary validation still visits every source frame,
including sites absent from the delivered scene. H06 retains its complete
authority, force, impulse, joint, action and reach histories; it does not retain
the public p/q/v/omega tuples of every unused site. `ensure_finite` can prove
that the original projection of such a private pose succeeds without allocating
those tuples. Required observations and release anchors still execute their
ordinary projections, and ordinary complete source snapshots are unchanged.

The fast proof applies only to an exact, locally owned `PoseValue`, its ordinary
projection dictionary, exact three/four-component tuples of `Fraction` values,
and the full 32,768-bit operand cap. A quaternion must be an exact
`RotationValue`, nonzero, and have no frozen public projection. Each numerator
and denominator has at most 512 bits. Components, current cap and cancellation
are checked in the same position, orientation, velocity, omega order. A cap
changed by the callback is observed before choosing the proof. Every shape,
domain, frozen-value, narrowed-cap or width case outside these conditions uses
the original field property. Existing actual projections retain the original
`_expose` behavior. The proof creates no computed public result or additional
request value cache. A completed proof may be retained on its existing source
pose as described below.

A nonzero vector component has absolute value between 2^-512 and 2^512. Its
binary64 result is therefore finite and normal; the original exact exponent,
significand division and rounding intermediates need fewer than 2,048 bits.
Zero has the original canonical zero result. For quaternion normalization,
each exact square has numerator and denominator widths at most 1,024 bits.
An unreduced sum of four such positive fractions has a denominator width at
most 4,096 bits and numerator width at most 4,098 bits; the stepwise addition
preflight is at most 4,099 bits. The normalized square ratio has numerator
width at most 5,120 bits and denominator width at most 5,122 bits. Every
nonzero ratio lies in `(2^-2052, 1]`: the numerator component's square exceeds
2^-1024, and the sum of at most four squares is less than 2^1026.

Thus the original square-root extractor shifts by at most 2,148 bits, including
its subnormal branch. Its allocation preflight is at most
`5120 + 2148 + 4 = 7272` bits; the exponent and squared-midpoint preflights are
also below 8,192 bits. All are below the unchanged 32,768-bit cap. The norm is
strictly positive and every normalized component has magnitude at most one,
so the public quaternion is finite. This proves admissibility of the original
algorithm, rather than substituting an approximate overflow test. Values near
binary64 overflow, exceptionally small values and larger exact denominators
take the original algorithm. The proof changes neither public values nor any
source, endpoint or interpolation allowance.

The recording-prefix planner also uses this same proof at the complete graph's
object-finiteness checkpoint. Its internal `PlanningSimulator` overrides only
that checkpoint: every object and site is still resolved, every object is
checked before entering the complete graph, and H06 retains the same boundary
records. The ordinary `ReachSimulator` checkpoint still requests all four
actual public fields in their original order. No caller-controlled flag,
weaker input domain or new arithmetic is introduced.

Planning does not retain ordinary object p/q/v/omega tuples in its H06 output.
It may therefore leave unrequested fields in an admissible `PoseValue` lazy.
Reach observations still read their actual base/tip/target components;
incoming release records, impulses and materialized trajectory anchors still
request their actual p/q/v/omega values through the unchanged getters. These
operations receive identical exact components and ordinary projections. The
existing proof's field-by-field cancellation, current-cap check and fallback
remain in force, including overflow, zero quaternions, foreign private values,
frozen projections and lowered operand caps. A failure prevents the pending
object graph from being published. Sampled recording transforms retain their
separate derivative-free path. This removes only incidental public extraction
from validated planning work; source observations, boundary admission, W,
numeric allowances and all fixed resource limits keep their prior meanings.

### Reusing a completed source-pose finiteness proof

The current complete signature is itself a sufficient proof when all four
fields pass the strict small-domain predicates above. At the original full
operand cap, the single `pose_finiteness_proof` checkpoint precedes the read
of all four actual immutable payloads. If every payload has the required
exact type/shape, every component has at most 512 numerator/denominator bits,
and the private quaternion is nonzero and has no frozen projection, the
existing uniform theorem already proves every omitted projection operation
admissible. Repeating those same per-field predicates adds no information.
The complete receipt can therefore be constructed directly from that current
signature, without allocating any public tuple or executing exact arithmetic.

This is one bounded predicate over the fixed four-field pose, with no
callback between its current operand read and publication. It uses no old
numeric equality or caller-provided projected values as evidence. Invalid
own/shared receipt metadata still takes the original ordered path before
this decision. Any unsupported field, mutable payload, frozen quaternion,
larger operand or narrowed cap retains the existing individual-field path,
including its original guards and failure order. The single callback remains
cancellable and can narrow the cap or change the payload before it is read;
such changes are checked in the current domain. Interruption cannot publish
a partial own or family receipt. No cache or limit changes.

[`test_reach_complete_finiteness.py`](../../tests/test_reach_complete_finiteness.py)
compares original binary64 projections and complete P23 boundary/phase
records, current caps, changed fields and exact cancellation identity. The
older receipt/family tests also exercise their retained individual-field
path separately; their layer-specific assertions are unchanged.

Each retained `PoseValue` can retain one private, comparison-independent proof
record alongside its existing projection state. The record contains its request
owner, the full operand cap and immutable fingerprints of the fields proved by
the 512-bit argument above. It contains no computed p/q/v/omega tuple, does not
add an entry to the request arithmetic cache, and cannot keep a pose alive after
that pose is released. The actual projection dictionary and getters are unchanged.

A repeated check first executes one charged cancellation checkpoint, then checks
the live cap and every current field fingerprint. Only unchanged exact immutable
tuples, or the complete unchanged immutable `RotationValue`, can reuse a proof.
Matching uses object identity after the typed bounded fingerprint admission;
it does not introduce exact rational equality on an unused rotation allowance.
An existing actual projection still follows the original finiteness-check semantics; merely
finding such a tuple never proves its private operands. Clearing that projection
therefore restores the original field check unless an independent private proof
was completed. Frozen or mutable private values and larger operands continue to
use the original projection.

An exactly translated source occurrence may carry this completed record. Its
changed position is checked in the original field order; unchanged orientation
and spatial-rate proofs can be reused. `dataclasses.replace` starts with no
proof. If a later field callback narrows the operand cap, all original fields
are checked again under the live cap, including fields reused earlier in the
call. Malformed or reentrant proof state uses the original ordered checks.
Publication occurs only after all fields succeed; cancellation and failure
retain the earlier completed record without publishing a partial proof. These
records memoize admission of the original exact projection algorithms, so they
do not change public bits, error allowances, or the complete set of observed
source occurrences.

Translated sites can be constructed before any of their public finiteness
checks. Those already-retained poses may share a single private metadata cell,
which points to one completed immutable proof record and never to another pose
or to a public value. The first successful check publishes that record; later
siblings still compare their complete current fingerprints and check changed
positions. Each pose also retains its own completed proof. This is one slot per
existing translation family, not a new request-wide map or a list of historical
values. Cancellation cannot publish a partial own or shared record, and a live
cap change replays all fields even when an earlier field used a sibling's proof.

### Reusing exact interval clock digits

Authored clocks retain the original guarded decimal serialization. Repeated
authored/stored interval widths may reuse a completed pair of immutable decimal
strings in the existing bounded request cache. Every invocation still performs
the original exact operand decode, nonnegative check and live width guard; the
cache key includes that exact fraction and its current operand cap. Every
certificate receives a fresh dictionary, so modifying an output row cannot
alter a later result. No new cache or capacity is added.

A cold entry executes the original chunked conversion and publishes only its
completed numerator/denominator strings. Cache lookup, promotion, insertion and
eviction retain their original charges and cancellation callbacks. A callback
that changes the operand cap restarts admission before returning or publishing
digits. Caller exceptions retain their identity. Reusing already completed
digits changes no exact clock, serialized byte, common accessor or independent
clock obligation. The focused checks are in
`tests/test_reach_clock_record_reuse.py`; execution evidence remains separate.

## Identified implementation and derivation aggregates

The source numerical basis identifies the complete controlled arithmetic and
the phase/anchor recurrence that supplies its uniform inputs. Its ordered
implementation input list is:

1. `ontokin/reach_numeric.py`
2. `ontokin/reach_kinematics.py`
3. `ontokin/reach_pose.py`
4. `ontokin/reach_phase.py`
5. `ontokin/reach_runtime.py`
6. `ontokin/reach_export.py`
7. `ontokin/reach_recording_fast.py`

Its separately ordered derivation input list is:

1. `docs/engineering/reach-numeric-kernel.md`
2. `docs/engineering/reach-source-kernel.md`
3. `docs/engineering/reach-coaxial-phase-bounds.md`
4. `docs/engineering/reach-carrier-rotation-cursors.md`
5. `docs/engineering/reach-recording-certified-planar.md`
6. `docs/engineering/reach-deferred-phase-locations.md`
7. `docs/engineering/reach-planning-reuse.md`

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

## Exact source composition across translated occurrences

The full source resolver may reuse a completed site, follow or joint
composition when two independently resolved occurrences differ only in their
parent translation and inherited position allowance. This recovery follows
the implementation retained at `e454547bf654a8d1e3402e6f054335fcb26229f0`;
the current continuation additionally requires the parent pose to belong to
the same request's pose arithmetic. It does not reuse recording-only graphs
or source identities, claims, lifecycle results, histories or output records.

Let `R` be nearest-even rounding to the private 96-bit dyadic grid. For every
integer `m`, `R(x + 2*m*2^-96) = R(x) + 2*m*2^-96`, including exact halfway
inputs. A rounded source composition contains its parent's translation only
as an additive position term. A joint's two compositions preserve that same
equivariance. The cache therefore retains each parent coordinate's low grid
bit, as well as the complete parent rotation (including its error and frozen
projection), spatial rates, joint axis/coordinate/slope and local placement.
Equal keys establish an even grid translation in every coordinate. Values
outside the 96-bit dyadic grid keep the ordinary composition path.

The completed result's exact difference from its parent position is retained.
A new occurrence adds that difference to its own current parent position;
orientation, velocity and angular velocity remain those of the same original
equations. The inherited position allowance enters composition additively too,
so its completed difference is retained and added to the occurrence's actual
allowance. This factors a term of the existing bound and changes no bound.
Only already materialized orientation/rate projections may be copied; each
occurrence's position and all public finiteness checks remain current.

This optional path applies only to full source graphs larger than the existing
cache capacity and only at the unchanged 32,768-bit operand cap. Complete
typed operands are freshly admitted before access. The 8,192-bit margins on
retained and translated coordinates/allowances keep the additional exact
subtractions and additions within that full cap. A callback that changes the
cap before or after building, publishing or reconstructing an entry abandons
the optional result and executes the original current-domain path. Caller
exceptions propagate unchanged. Entries share the same request-local bounded
256-entry LRU; the complete topology is still traversed and all 32 P23 arms
keep distinct physical state and source records. The differential, halfway,
changed-input, cap and cancellation checks are in
`tests/test_reach_source_translation.py`; execution evidence is recorded
separately.

## Component reduction of actual recording endpoints

The endpoint certificate may reduce component errors across one already
defined source/enclosing-phase group before forming its exact L1 bounds. Every
actual endpoint is still freshly admitted as three finite binary64 position
components and four finite binary64 quaternion components. Each is converted
through the ordinary binary32 writer, and every stored quaternion must remain
nonzero. This changes no stored pose, clock, geometry or source trajectory.

For component `j` and retained endpoint `k`, let `a[k,j]` be its actual source
binary64 value and `b[k,j]` its correctly rounded stored binary32 value. The
subtraction `a[k,j] - b[k,j]` is exact in binary64: either the stored value is
zero, or same-sign nonzero operands satisfy the Sterbenz range (including the
boundary half-way cases). A subnormal difference remains an exact multiple
of the binary64 minimum subnormal. Define `D[j] = max_k |a[k,j]-b[k,j]|` and,
for positions, `B[j] = max_k |b[k,j]|`. Both reductions compare finite
nonnegative binary64 values exactly. Consequently every endpoint's position
conversion L1 error is at most `sum_j D[j]`, and its stored-position L1
magnitude is at most `sum_j B[j]`. Form these sums as exact rationals once per
output carrier and group. Maxima may occur at different keys; this only makes
the bound larger and cannot exclude an actual endpoint.

For this reduction, every actual source quaternion must have some component
of magnitude at least one half. Its Euclidean norm is therefore at least one
half, so the existing normalized-vector comparison gives a unit-quaternion
chord error at most `4 * sum_j D[j]`, plus the same two normalization allowances
as the original calculation. A quaternion lacking that sufficient component
test replays the original complete group, including its exact norm proof and
normalization fallback. The original group reduction also remains active for
empty groups and every narrowed arithmetic domain.

The optimized scan runs only at the unchanged 32,768-bit cap. All ordinary
binary64 decodes fit 1,075 bits, and sums of at most four such nonnegative
components have fewer than 2,101 numerator bits and at most 1,075 denominator
bits; the original prospective exact-operation guards fit comfortably below
the full cap. A scope checks that full cap immediately after every actual
request checkpoint, including final exact sums. A changed cap abandons the
incomplete reduction and replays the original group under the current domain,
retaining attempted work. Caller exceptions propagate by identity, including
an exception of the private fallback class. No partial reduction is published.

The ten component maxima per output carrier are bounded reduction state, just
as the original three completed endpoint maxima were. They are neither a
cross-group lookup table nor an additional retained numerical cache. All
existing cache limits remain unchanged. Group membership, every endpoint,
every interval row, quarter-allocation checks and final original position and
rotation tolerances remain mandatory. The separately implemented supplied-byte
reader still verifies the emitted bounds against its own source reconstruction
and the actual stored values. `tests/test_reach_endpoint_reduction.py` covers
exact component identities, subnormals, changed data/domains, original fallback,
callback identity, cache preservation and actual artifact equivalence; executed
results belong to a subsequent identified checkpoint.

## Complete canonical admission and observed-target input reuse

The pure planar helper may retain a completed admission under all nine actual
binary64 inputs: two link lengths, three target coordinates and both closed
limit pairs. The key also contains the branch, proof method and the unchanged
32,768-bit operand cap. Only exact immutable tuple containers, exact finite
binary64 scalar objects and the ordinary branch strings use this additional
receipt. The source transaction still checks the current action, topology,
motion modes, both claims, active-count limit and initial coordinates before
calling the numeric helper. The receipt contains no source or run authority.

The existing admission-entry callback precedes all input reads. Each of the
nine current scalar bit patterns then has its own charged admission check,
followed immediately by the current full-cap check. All finite binary64
decodes have prospective width at most 1,075 bits, so that unchanged domain
admits the original decodes without constructing their Fractions again. Exact
bit identity also implies identity of their original canonical rational values;
signed zeros deliberately receive distinct raw keys even though the ordinary
numeric result canonicalizes zero. Matching both complete limit pairs proves
that the already completed closed-limit comparisons still have precisely the
same operands. A different limit takes the retained geometry-only path, which
performs the ordinary comparisons and preserves their diagnostic ordering.

The cached result includes the same canonical target bits, coordinate
enclosures, residual upper bound, precision and numerical method as the
original successful proof. Its old counters never stand in for current work.
Every returned `PlanarSolution.work` is rebuilt after the current call's actual
arithmetic and cache publication; its local `operations` plus the initial
admission unit equals that call's shared operation delta. A complete warm hit
executes nine input checks, a lookup and a promotion, in addition to the entry
unit. It performs no Fraction decode, canonical round trip, repeated limit
comparison or proof series. These omitted computations are genuinely avoided;
all executed operations retain their own charges.

The complete receipt shares the existing 256-entry request LRU with the
geometry-only solver proof and pose results. There is no second numerical
cache or larger capacity. Current narrower caps, mutable containers, scalar
subclasses, noncanonical inputs and nonfinite values retain the original
numeric path. A cap change at an input or lookup callback prevents the wider
receipt from returning; the ordinary current-domain calculation supplies any
failure. At publication, the work cache rechecks its cap and generation after
all callbacks and declines a changed-domain insertion. As with its existing
bookkeeping contract, a caller may receive a proof completed before that
publication callback, but it cannot become a reusable proof for the new
domain. No arithmetic exception is caught and retried, so a failing original
operation retains its exact exception even if external code then widens the
cap. Cancellation leaves source admission and its whole boundary uncommitted.

The observed-target helper applies the same finite-input argument to one
immutable three-float target. It keeps the original charged vector-domain
admission, including current dimension, exact scalar type and finiteness
checks. Its existing translated-component cache key receives the actual three
binary64 bit patterns in a distinct typed namespace. The already bounded
entry also retains the exact decoded target alongside its rotated offset and
last projected point. On a miss, the three original scalar decodes execute;
on a hit, their immutable completed values are width-checked with all current
rotation, position and retained component operands. Six scalar decode charges
are avoided because those three rational/bitfield conversions are not repeated.
The fresh vector admission, cache access, rotation guard, exact translation,
grid rounding and binary64 projection keep their existing accounting.

The target optimization applies only at the full operand cap and to exact
immutable native tuples. Narrower domains and foreign or mutable targets use
the original vector helper. A complete native key cannot collide with a
decoded-vector key, including through Python's Boolean/integer equality.
Replacing a payload's target field after its local immutable tuple was
captured cannot poison a numerical entry: both the key and its exact result
derive solely from that same captured tuple, with no payload identity in the
key. A later call freshly captures the then-current target. Missing older
decoded-target receipts replay the original scalar conversions. The cache
still retains only one last translated point per actual rotation/target pair,
and all current-domain, cancellation and publication guards remain active.

`tests/test_reach_complete_admission.py` covers complete operand binding,
original error precedence, actual counters, narrowed domains, exception
identity, bounded capacity and source-boundary rollback.
`tests/test_reach_world_target_input_reuse.py` compares canonical point bits,
raw signed-zero keys, original fallback, callback reads and partial-publication
safety. Executed results are recorded separately from this derivation.

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
