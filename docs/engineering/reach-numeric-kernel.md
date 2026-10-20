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

Every homogeneous rotation dot product and division is exact rational
arithmetic, followed by one 96-bit dyadic rounding per output component.
Its Euclidean vector perturbation is at most sqrt(3)rho < 2^-96 in the
vector's units. Addition stages that round a resulting vector each incur
the same bound. Private positions, orientations and derivatives survive
through the whole parent-child chain; reading a public projection cannot
change subsequent private composition.

Public quaternion components are each rounded from the exact normalized
private component `sign(q_i)*sqrt(q_i²/(q dot q))`. Integer square root plus
an exact squared-midpoint comparison proves nearest-even binary64 extraction.
No `math.sqrt`, `math.hypot`, `math.sin`, `math.cos`, libm accuracy assumption
or machine-epsilon guess supplies the source proof.

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
needs a rigorously bounded uniform approximation. It uses 20-term sine and
cosine polynomials after certified pi/2 range reduction. Their coefficients
are exact factorial rationals; the variable is rounded onto the 96-bit grid,
and the square of that grid variable is kept exact. Each Horner multiply-add
rounds once to the grid. The sine's final multiplication rounds once more.
For |x| <= 1, previous Horner errors do not amplify, so 21rho is a safe common
arithmetic allowance. The omitted Taylor tail is bounded by 1/40!.

Pi is enclosed with exact alternating sums in Machin's identity, with a
fixed term count for each permitted precision, then outwardly projected to
that precision's dyadic grid. The reducer chooses an integer quadrant from
the midpoint. It need not prove that this is the unique nearest quadrant:
it directly proves the chosen reduced argument lies within the polynomial
range. The exact reduced argument must be within **2^-86 radians** of its
grid representative. Restoration by permutation and sign changes is exact.
Sine and cosine are 1-Lipschitz, and the exact rational inequality

```
2^-86 + 21*2^-97 + 1/40! < 2^-80
```

proves the stated component error for every admitted source angle.

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
