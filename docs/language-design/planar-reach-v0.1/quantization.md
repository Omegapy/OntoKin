# Proposed stored-motion and quantization contract

This is an **unadopted** companion to OK-LANG-006 `0.1.0-draft.2`.
It fixes the finite recorded GLB/0.6 proof obligations before implementation.
This text was reconstructed after the October 20 workspace rollback; its new
hash and fresh review are authoritative for this revision. It is not presented
as an exact recovery of the missing earlier document or as runtime evidence.
The [sampling derivation](sampling-bound.md) supplies ideal phase bounds;
this document accounts for actual clocks, stored endpoints, native vertices,
source numerical behavior and the identified destination's numerical behavior.

## 1. Reference paths and the actual destination

The ideal path is the real-valued rigid kinematics determined by the exact
canonical binary64 source operands, exact rational clocks, correctly rounded
admitted coordinate targets and the prescribed unwrapped coordinate interpolation.
For this reference path only, interpret the affine coordinate expression over
the reals before its exposed per-sample binary64 rounding. A controlled source
numerical bound must cover the difference between that continuous reference
and the actual evaluator, including coordinate rounding, trigonometry, quaternion
products/normalization, positions and site composition. Treating an already
rounded function as differentiable is invalid.

glTF `LINEAR` translation is componentwise linear interpolation. Its `LINEAR`
rotation is shortest-arc spherical interpolation of unit quaternions, as defined
by [Khronos glTF 2.0, Appendix C.3–C.4](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#appendix-c-animation-sampler-interpolation-modes).
The [Three.js QuaternionLinearInterpolant documentation](https://threejs.org/docs/pages/QuaternionLinearInterpolant.html)
also identifies SLERP. These format statements do not prove that a particular
floating-point destination exactly implements ideal unit-quaternion SLERP.

The mathematical comparison interpolant in this contract normalizes the actual
stored finite nonzero endpoint quaternions in exact real arithmetic, chooses a
coherent short-path lift, and performs exact SLERP. The actual identified
destination may have normalization, interpolation, time-parameter and matrix
arithmetic error. Bound that difference separately and uniformly over each
whole interval, including endpoint and near-coincident branches. The writer
cannot label an untested target or arbitrary glTF player numerically certified.

Default tolerances remain `0.001 m` position and `0.001 rad` rotation. The time
tolerance is positive and at most `1e-6 s`. Tighter caller settings remain binding.
Source goal residual remains `1e-9 m`; it is not a delivery interpolation budget.

## 2. Exact rational clocks and direct binary32 conversion

Keep every authored clock as a reduced nonnegative rational. Source decimal
literals first undergo the inherited canonical binary64 conversion; subsequent
event, elapsed, completion and subdivision arithmetic uses exact ratios of those
canonical values. Do not replace a computed rational completion by a decimal
approximation or round it through a host binary64 before storage.

The sole clock conversion is
`clock_conversion = "binary32_rne_ties_to_even_from_exact_rational"`.
Round the exact rational directly to nearest IEEE binary32 with ties to the
even significand. Include subnormals, ties at zero, exponent transitions and
overflow in the conversion definition. Reject overflow/nonfinite output;
canonical zero is positive zero. An integer quotient/remainder implementation
can decide a midpoint exactly, without calling host trigonometry or first
converting the rational to binary64. For nonnegative values, compare twice
the remainder with the denominator; at equality select the even quotient.

Each retained key records `authored_seconds`, the exact decoded binary32
`stored_seconds`, `stored_binary32_bits`, and whether it is a semantic boundary.
The independent reader derives the bits from both the rational and actual
accessor bytes. JSON labels, a small time error or equality after binary64
conversion cannot substitute for exact bit equality. Require strictly increasing
stored clocks, at most 10,000 retained keys, and an endpoint time shift within
the requested tolerance. Distinct semantic boundaries that collapse to one
stored clock cause explicit failure. Do not delete a boundary to make an
otherwise unrepresentable request succeed.

Q18's nonsemantic authored clock is exactly `1 + 2^-24 + 2^-80`. Direct conversion
is bits `3f800001`. Rounding through binary64 first loses the final term and
then incorrectly selects `3f800000`. The otherwise valid hostile artifact
changes only the relevant stored clock and dependent consistency labels;
the intended rejection must be direct-rounding mismatch, not an unrelated
parse, object-set or hash failure.

The separate Q16 source uses canonical literals `0.50000002[s]` and
`1.50000002[s]`, not original L01's exactly representable `0.5` and `1.5`.
Its pause ratio is `4503599807514481/9007199254740992`, its resume ratio is
`6755399531127737/4503599627370496`, and its exact completion is
`27021597764222977/9007199254740992 = 3 + 2^-53`.
Their stored bits are respectively `3f000000`, `3fc00000`, `40400000`.
The recovered [recording probes](draft2-supplements/recording-probes.json)
identify the source, complete bundle and exact boundary-crossing mutation.

## 3. Which source phases a stored interval covers

For adjacent authored clocks `a0 < a1`, let `h_a = a1-a0`. Let their actual
decoded stored clocks be `s0 < s1`, with `h_s = s1-s0`, and
`delta = max(abs(s0-a0), abs(s1-a1))`. Subdivide authored intervals at every
semantic event/completion/release/force change before choosing ordinary keys.
Each authored pair is within one smooth source phase. Its source bounds are
`A` for carrier acceleration and `W` for the sum of absolute angular rates
on the supported actual transform path.

All `A`, `W`, `V_E`, `A_E` and `W_E` bounds refer to the **ideal continuous
reference path** derived from exact canonical operand ratios. In particular,
derive a moving coordinate's slope from exact `(target-start)/duration` and
round any reported bound outward. An exposed inspection rate may round down;
it cannot automatically serve as a conservative derivative bound.

Let `E` enclose both `[a0,a1]` and `[s0,s1]` within the requested valid prefix.
Reconstruct every source phase touched between the two parameterized clocks,
not merely the phase at the stored midpoint. Obtain enclosing bounds
`V_E`, `A_E`, `W_E` for carrier speed, carrier acceleration and angular speed.
Where the interval is not twice differentiable across a boundary, apply the
derivative bounds on each smooth piece; the time-shift estimate uses continuity
and the sum/integral of the speed bounds. Complete before/after metadata retains
the discontinuous derivatives and actions. No after-state exists at a failed
boundary. A pose jump, unsupported phase, missing side or unproved bound fails.

An interval certificate lists the actual phase indices. It may conservatively
include additional touching phases, but must not omit any positive-width phase
covered by the enclosing interval. For Q16 the stored post-pause pair from `0.5`
to `1` overlaps the preceding moving phase by
`180143985/9007199254740992` seconds. Both moving and paused phase bounds are
required even though the authored pair starts at the exact pause and its
midpoint is paused. Removing only the moving phase from an otherwise valid
certificate is the required Q16 hostile probe.

An authored final clock may round slightly beyond the valid prefix. Define the
comparison source extension only on that final rounded tail as the held valid
endpoint pose. The tail does not evaluate a future event or solve a future reach;
it is a recording clamp with zero extension speed. Include the actual interior
prefix phases in the enclosing bounds. Apply the symmetric held-endpoint rule
when a stored start lies before the valid requested start. If the delivery
interface requires a different policy or cannot express this clamp, reject it.
Interior semantic states can never be clamped away.

## 4. Endpoint, radius and numerical bounds

For a carrier, let `p*(t)` be its ideal world origin and `q*(t)` a continuous
unit-quaternion lift over the authored phase. Let `p0,p1` be actual stored
translations and `q0,q1` the exact normalized actual stored quaternions after
coherent sign choice. Let `theta_s` bound their short quaternion arc length,
`acos(abs(dot(q0,q1)))`. Reject zero/nonfinite quaternions, inconsistent lifts,
an unavailable arc bound or an arc larger than `pi/4`. Legitimate binary32
rounding normally makes a stored quaternion slightly nonunit: it is allowed
only under the defined normalization comparison and proved actual-destination
error. Assuming that arbitrary nonunit values are harmless is invalid.

Independently establish the following nonnegative upper bounds:

| Symbol | Certificate quantity and meaning |
| --- | --- |
| `e_p` | `max_endpoint_position_error_m`: maximum Euclidean difference of stored translations from ideal authored endpoint origins. |
| `e_q` | `max_endpoint_unit_quaternion_error`: maximum Euclidean difference of normalized stored endpoints from the coherent ideal authored endpoint lift. |
| `r` | `landmark_radius_m`: maximum norm of every source native vertex and promised site/landmark about its actual delivered carrier origin, after local visual placement. |
| `e_v` | `local_vertex_error_bound_m`: maximum local Euclidean error of the actual stored occurrence geometry, including required placement and attribute conversions relevant to positions. |
| `n_sp`, `n_sr` | Uniform source numerical position/rotation bounds from the exact reference path to the actual evaluator. |
| `n_dp`, `n_dr` | Uniform actual-destination position/rotation bounds from exact stored translation/normalized-endpoint SLERP, including its time parameter, normalization, interpolation, transforms and endpoint branches. |

The positional numerical allowances also cover every promised transformed local
point, not just the carrier origin. Sum the origin error and any residual
matrix/vertex arithmetic error beyond the compared proper rotation, uniformly
over the complete source and stored radius `r + e_v`. In particular, a nonunit
quaternion or floating matrix can produce a nonorthonormal transform. Its
operator-norm defect times `r + e_v`, or an independently proved tighter bound,
must be charged to `n_sp` or `n_dp` as applicable. A rotation-angle bound alone
does not bound that non-rigid deviation. If the implementation cannot establish
these positional terms for its actual transform algorithm, reject delivery.

Endpoint errors include the real endpoint computation and storage effects;
they are not assigned a fixed number merely because binary32 has 24 significand
bits. Translation magnitude, transform depth and conditioning matter. Use exact
rational operations and rigorously outward-rounded intervals as appropriate.
The separately charged uniform source error compares the entire actual evaluated
path to the reference; possible conservative double charging is permitted.
Never subtract a sampled error from an upper bound to reclaim tolerance.

Both `source_numeric_bound_basis` and `destination_numeric_bound_basis` identify
the actual algorithm name, version, implementation SHA-256, method and derivation
SHA-256. These
identities must resolve to retained reviewable evidence for the claimed
algorithm, operand ranges and arithmetic assumptions. An arbitrary label,
unverified host `sin/acos/sqrt`, a sampled maximum, comparison of two related
implementations, or the unused portion of a requested tolerance is not a
uniform numerical proof. Unknown terms require rejection. An exact-arithmetic
test example may set an exactly proved term to zero; production code may not
borrow that zero without satisfying the same proof.

## 5. Nonzero-endpoint SLERP proof and complete inequalities

For normalized parameter `u` in `[0,1]`, define authored time
`a(u) = (1-u)*a0 + u*a1` and stored time `s(u)` analogously. Then
`abs(a(u)-s(u)) <= delta`. On the authored phase,
`||d²q*(a(u))/du²|| <= W²*h_a²/4`.
The zero-endpoint vector interpolation error bound gives

```text
||q*(a(u)) - ((1-u)*q*(a0) + u*q*(a1))|| <= W²*h_a²/32.
```

The chord between the two normalized stored endpoints differs from that ideal
chord by at most `e_q`. Exact stored-endpoint SLERP `S(u)` has
`||S''(u)|| = theta_s²`, hence its difference from its own chord is at most
`theta_s²/8`, including the constant coincident-endpoint limit. The triangle
inequality therefore proves, without a SLERP endpoint-Lipschitz assumption,

```text
D = e_q + W²*h_a²/32 + theta_s²/8
||q*(a(u)) - S(u)|| <= D.
```

Require `D <= 1/2`. For such nearby coherent unit quaternions the rotation
distance is `4*asin(d/2) <= 4*d`; this yields `4*D`. Integrating angular speed
along the time displacement gives the complete bound

```text
total_rotation_bound_rad = 4*D + n_sr + n_dr + W_E*delta.
```

The exact carrier translation chord differs from its source authored path by
at most `A*h_a²/8`. Endpoint error and source/destination arithmetic add by the
triangle inequality, and the shifted-time term is at most `V_E*delta`:

```text
carrier_position_bound_m = e_p + A*h_a²/8 + n_sp + n_dp + V_E*delta
total_position_bound_m = carrier_position_bound_m
                        + r*total_rotation_bound_rad + e_v.
```

Rotation angle `B` moves a point of norm at most `r` by
`2*r*sin(B/2) <= r*B`; decomposition into a source point and its storage error
justifies adding `e_v` once. Require both carrier and total position bounds
within the position tolerance, and total rotation within rotation tolerance.
All recorded quantities are outward upper bounds; a rounded JSON scalar may
not understate an independently established exact bound.

The ideal planning conditions remain mandatory and are checked twice:
for `(h_a,A,W)` and for `(h_s,A_E,W_E)`:

```text
W*h <= pi/4
B = W²*h²/4 <= rotation_tolerance/4
A*h²/8 <= position_tolerance/4
A*h²/8 + r*B <= position_tolerance/4.
```

The stored-gap check is a conservative planning requirement, not a replacement
for the authored error derivation or for the phase/time-shift terms. Require
`theta_s <= pi/4` too. Quarter allocations reserve room; they do not certify
the remaining three quarters. Every final sum above must pass. Failed
representability or an unresolved numerical proof cannot be fixed by loosening
the caller's tolerance or reporting a lower output level.

## 6. Coverage, preflight and supplied-byte verification

There is exactly one interval certificate for each actual delivered carrier
and adjacent retained key pair. A static/zero-duration recording has its
required single-pose/identity check and no invented positive-width interval.
Reject missing, duplicate, nonadjacent, wrong-carrier and out-of-range rows.
All expected source objects, native primitive occurrences, materials, geometry
and retained semantic boundaries remain independently required. A certificate
cannot compensate for a missing eye, leg, sibling or released sphere.

Use [budget-counting.md](budget-counting.md)'s distinct units: the 100,000
weighted source-history limit, 100,000 interval-certificate cap, 64 MiB GLB
byte/metadata-entry guards, and inherited key/pose/vertex limits are different
constraints. Shared input or output accessors do not exempt repeated decoded
components or object poses. Charge and bound counts before allocating expanded
arrays, then check actual totals. Cancellation applies during planning, source
proof, geometry, decoding and serialization.

The independent reader reconstructs phase bounds and ideal states from immutable
source with independent equations. It verifies direct clock rounding from actual
bytes, complete source/Agent/artifact identity, normalized stored endpoints,
source geometry radius, vertex conversion, numeric method identity, every
certificate inequality and all required metadata. It must recompute values;
`all_values_independently_recomputed: true` is not evidence by itself. A valid
writer's certificate is an input to check, not an oracle. Required fixed,
boundary-neighbor and dense source/destination samples remain additional
regression checks and never replace the continuous proof.

Q13–Q20 separately target understated endpoint error, unproved source numerical
error, changed destination identity, omitted neighboring phase, understated
radius/vertex error, direct double rounding, invalid quaternion normalization/
lift and missing/duplicate certificate coverage. Mutations must isolate the
intended rejection stage on otherwise valid artifacts. Q21/Q22 independently
exercise terminal history and stale run/source identity rather than numerical
certificates. The effective [requirements](requirements-draft2.json) and
[release gate](release-contract.md) define their actual execution obligations.

## 7. Pure contract checks and implementation boundary

[verify_quantization_contract.py](verify_quantization_contract.py) checks exact
clock rounding, the fixed double-rounding counterexample, nonbinary semantic
phase coverage, endpoint clamping, rational bound arithmetic and explicit
failure conditions. It calls no OntoKin evaluator, exporter or destination.
Its synthetic bound examples assume their input bounds; they do not prove an
actual source or destination kernel. The actual kernel derivations, source-built
and Agent-retrieved artifacts, hostile-byte reader, independent browser playback
and reviewed whole-asset images remain mandatory implementation/release work.
