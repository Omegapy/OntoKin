# Bounded numerical admission for planar reach

Document: **OK-LANG-006 numerical admission**, `0.1.0-draft.2`, reconstruction `recovery14`, October 20, 2026. Status: **proposed; not adopted or implemented**.

This is a newly identified reconstruction of the missing numerical proposal work. Its mathematical checks are fresh. It is not the lost document, checker or certificate, and none of their earlier passing reports is evidence for these bytes. The [reconstruction record](numeric-review/reconstruction.json) separates the preserved original inputs, the unavailable predecessor and the new evidence. The exact recovered [D25 counter clarification](numeric-counter-units.md) retains its own history; its recurrence-step interpretation is also the interpretation used here.

The original [41-case corpus](acceptance.json), [Decimal preparation oracle](oracle.py), source programs and expected values remain unchanged. This supplement supplies a bounded method for establishing a selected binary64 joint pair without treating a host `acos`, `atan2`, `sin` or `cos` call as a rounding proof. It does not implement the source evaluator or any Agent or destination behavior.

## 1. Fixed bounds and outcome order

| Quantity | Fixed maximum or schedule |
| --- | --- |
| Canonical site lengths | Each in `[0.125, 4]` meters, inherited from the proposal |
| Canonical target components | Each planar component in `[-8, 8]` meters; exact zero Z in the required frame |
| Precision passes | `96, 192, 384, 768, 1536` fractional bits, in this order |
| Series terms per admission | 12,000 **series recurrence steps**, accumulated across all passes |
| Outward interval operations per admission | 100,000, subject to the shared remaining program work budget |
| Standalone combined declared proof operations | 100,000 interval plus explicitly counted exact proof helper operations, accumulated across all passes |
| Integer/rational operands and preflight intermediate widths | 32,768 bits per numerator, denominator or integer |
| Real forward residual of the rounded pair | Squared base-frame distance at most the exact rational `1 / 10^18` square meters |

The historical names `MAX_SERIES_TERMS`, `max_series_terms`, `series_terms`, `per_admission_series_terms` and `maximum_observed_series_terms_per_case` count recurrence steps. One step adds one arctangent term, or advances and adds one **paired sine/cosine** recurrence. Every constituent interval operation in that step is separately charged. The [D25 clarification](numeric-counter-units.md) resolves this unit without changing the 12,000 bound.

The standalone checker has a finite combined proof counter as an additional guard. Production does not receive a separate 100,000-operation numerical allowance. Actual numerical work consumes the same inherited semantic-work budget as construction, evaluation and other work. Smaller request budgets may fail earlier. Classification, algebraic comparisons, integer square roots, rounding, serialization and other work require their own counts or conservative precharges; the standalone helper counters do not certify that complete runtime accounting.

The enclosing runtime preserves the adopted order: typing and immutable frame/chain/domain checks, current mode and conflicting claims, exact geometric reachability, singularity, the canonical target rounding proof, closed canonical limits, and the required residual proof. No target may be compared against a limit using an approximate branch solution. Numeric proof artifacts can prepare both the pair and residual together, but this does not change diagnostic precedence. An exhausted work/operand budget is `reach_resource`; an interrupted request remains cancellation. If every listed precision pass remains inconclusive without resource exhaustion or cancellation, report `reach_numeric`. Do not relabel an inconclusive proof as unreachable, singular, limited, satisfied or successfully evaluated.

## 2. Exact source inputs and geometric classification

All inputs to these equations are exact rational representations of already canonical binary64 source values. Decimal spellings are not treated as exact decimal geometry after source canonicalization. A binary64 finite value can be decoded from its integer significand and power of two; no transcendental arithmetic is involved. The original preparation code uses `Fraction.from_float` for the same meaning. Python's [Fractions documentation](https://docs.python.org/3.12/library/fractions.html) describes this conversion; the independent proof additionally decodes the binary64 bit fields itself.

Let the positive lengths be `a,b`, the target components `x,y`, the radius squared `r2 = x*x + y*y`, and `s` be `+1` for the positive branch or `-1` for the negative branch. Compute all products, sums and comparisons exactly. Reject `r2 < (a-b)^2` or `r2 > (a+b)^2` as unreachable; use no epsilon and no clamping. If `a == b` and `r2 == 0`, reject the underdetermined shoulder as singular. These are different outcomes. The remaining admissible annulus has `r2 > 0`.

Define exact rationals:

```text
c = (r2 - a*a - b*b) / (2*a*b)
d = 1 - c*c
t = a + b*c
```

The annulus proves `-1 <= c <= 1` and `d >= 0`. The mathematical elbow is `s * atan2(sqrt(d), c)`. At `d=0,c=1`, both branches have canonical zero elbow. At `d=0,c=-1`, the positive branch retains `+pi` and the negative branch retains `-pi` before their one binary64 rounding.

Source typing, frame identity, actual chain topology, claim ownership and action lifetime are outside this numeric helper. A numerical record cannot validate them. The immutable proof cache key must contain every canonical length and target component, the branch, and the numerical method identity; reuse never exempts current source identity, claims, start coordinates, limits, cancellation or output accounting from fresh checks.

## 3. A cancellation-safe shoulder direction

Computing the shoulder as a difference of two approximately evaluated angles can hide an exact zero or choose the wrong side of the principal cut. Instead use the exact algebraic direction:

```text
X = t*x + s*b*y*sqrt(d)
Y = t*y - s*b*x*sqrt(d)
```

This is the real and imaginary part of `(x+i*y) * (t-i*s*b*sqrt(d))`. Its argument is exactly the required difference modulo `2*pi`. Because `t*t + b*b*d = r2`, its squared norm is `r2*r2`; it is nonzero on every admitted geometry. Consequently dividing both components by positive `r2` changes neither argument nor sign. The reconstructed checker performs that exact scaling before its interval arithmetic. This preserves useful magnitudes for very small targets, including the separately tested smallest positive binary64 subnormal.

Each unscaled component has the form `A+B*sqrt(d)`. Its sign is exact:

1. For `d=0` or `B=0`, use the sign of `A`.
2. For `A=0`, use the sign of `B`; equal nonzero signs also settle the result immediately.
3. For opposed signs, compare `A*A` with `B*B*d`. Equality establishes exact cancellation. Otherwise the result is `sign(A) * sign(A*A-B*B*d)`.

No approximate tolerance decides a zero, quadrant or principal-cut side. The checker replaces an algebraically zero component with the exact interval `[0,0]`. The final `atan2` uses these proved signs. For nonzero components it divides by a magnitude whose lower bound is positive, choosing either `atan(|Y|/|X|)` or `pi/2-atan(|X|/|Y|)` before applying the quadrant. If neither denominator is separated from zero at the current precision, that pass is inconclusive and must refine or fail.

The shoulder principal value is in `[-pi,pi)`: the exact negative real axis with zero imaginary component selects `-pi`. For all other quadrants, the exact component signs determine the open side of the cut. After rounding, a positive `Pi64` shoulder value becomes negative `Pi64`, as required by the original proposal. The certificate separately records the proved pre-canonical rounding cell and the final canonical bits. The elbow never receives this shoulder remapping.

## 4. Outward dyadic arithmetic

At precision `p`, an interval endpoint is an integer multiple of `2^-p`. For an exact rational `n/m` with `m>0`, its lower grid bound is `floor(n*2^p/m) / 2^p`; its upper bound is `ceil(n*2^p/m) / 2^p`. Negative values use the same directed integer division rules. Every arithmetic result is enclosed before the next interval operation.

Addition and subtraction use the appropriate endpoint sums. Multiplication evaluates all four endpoint products and takes their minimum and maximum. Division does the same with four quotients only after the divisor interval is proved not to contain zero. Squaring uses a zero lower bound when the interval crosses zero; otherwise it uses the smaller endpoint square. The checker preflights a conservative intermediate-width bound and remaining counter before the bounded arithmetic, and guards resulting numerator and denominator widths.

For nonnegative exact rational `v`, let `k = isqrt(floor(v*2^(2*p)))`. Then `k/2^p <= sqrt(v) < (k+1)/2^p`, unless exact integer squaring proves equality with the lower endpoint. In that case the upper endpoint equals the lower. This uses only the integer square root specified by Python's [math documentation](https://docs.python.org/3.12/library/math.html#math.isqrt), with bounded input size and cancellation checks immediately before and after the native call. A budget cannot cancel inside that native primitive, so the operand cap is part of its latency bound; runtime latency measurements remain required.

Inductively, every operation encloses its corresponding exact expression. Directed rounding can widen an interval and make a proof inconclusive. It cannot justify accepting a cell or residual that the full interval fails to satisfy.

## 5. Arctangent and pi enclosures

For `|z| <= 1/2`, use `N = floor((p+5)/2)` terms of the alternating arctangent series. The omitted absolute remainder is at most:

```text
|z|^(2*N+1)/(2*N+1) <= 2^-(2*N+1)/(2*N+1).
```

The checker accumulates every term through outward interval arithmetic and widens the final sum by that exact rational upper bound. The [NIST DLMF arctangent series](https://dlmf.nist.gov/4.24#E3) supplies the series identity; the remainder inequality here follows from its decreasing alternating terms on the declared real interval.

Odd symmetry reduces negative arguments. For positive arguments greater than one, use `atan(u)=pi/2-atan(1/u)`. For `1/2 < u <= 1`, use `atan(u)=pi/4+atan((u-1)/(u+1))`; the reduced argument lies in `[-1/3,0]`. These identities follow from tangent addition on the specified quadrants. For an interval input, arctangent is monotone, so the lower endpoint's lower enclosure and upper endpoint's upper enclosure enclose the whole result. There is no unbounded convergence loop or precision growth.

Pi uses the Machin identity `pi=16*atan(1/5)-4*atan(1/239)`. This identity is independently checkable by exact tangent arithmetic: `tan(2*atan(1/5))=5/12`, `tan(4*atan(1/5))=120/119`, and subtracting `atan(1/239)` gives tangent exactly one. The angle lies in `(0,0.8)`, within the first tangent branch: `atan(1/5)>5/26`, `atan(1/239)<1/239`, and `pi/2>1` follow from the elementary arctangent integral bounds. It therefore equals `pi/4`. The checker never starts from a decimal pi approximation.

The independent mathematical probes also enclose pi from `pi=4*(atan(1/2)+atan(1/3))`, using separate exact-rational sums without the outward-arithmetic implementation. Their tangent addition is exactly one and their positive sum is below one, fixing the same branch. Agreement is a finite independent check, not a replacement for the derivation above.

## 6. Binary64 rounding cells

For any positive exact rational, determine its binary exponent using integer bit lengths and exact comparisons. Scale the rational into the normal 53-bit significand or the subnormal `2^-1074` grid. Integer quotient and remainder decide nearest rounding; an exact half increments only an odd quotient. Handle a significand carry, the normal/subnormal boundary and the overflow midpoint explicitly. Negation is symmetric, and every rounded zero is canonical positive zero. No intermediate binary64 conversion chooses the result.

For a finite candidate `v`, let `v-` and `v+` be its adjacent representable values. Its rounding cell has exact midpoint boundaries `(v-+v)/2` and `(v+v)/2`. Include both boundaries only when the candidate significand's low bit is even. Canonical zero combines the two signed-zero cells and includes both endpoints `-2^-1075` and `+2^-1075`. The largest finite cell uses the virtual next value `2^1024` to define the overflow midpoint; the finite maximum has an odd low bit, so the midpoint itself belongs to infinity.

Both enclosure endpoints must round to the same finite candidate, and the **whole** closed enclosure must fit its exact cell with the correct tie inclusivity. This also handles exact midpoint results. A midpoint-straddling enclosure refines; choosing the midpoint's rounding and ignoring an endpoint is invalid. A coordinate's proof contains its enclosure, both cell boundaries, the tie rule, pre-canonical bits and final canonical bits. Zero and the principal shoulder remap are explicit.

The checker compares all 54 original primary-action target bits against the preserved corpus and checks their cells independently using `math.nextafter` only to identify adjacent binary64 values. It does not use `math.nextafter` to calculate a transcendental target. Twenty-five nonzero-pair cases additionally receive a one-ULP wrong-cell mutation that must fail the independent inclusion check. Separate probes cover midpoint ties of both signs, subnormals, canonical zero, the smallest normal and overflow thresholds.

## 7. Residual after canonical rounding

Correctly rounding the exact inverse solution does not make the rounded pair an exact geometric solution. The residual must be established for those final canonical angles, including a shoulder remapped from positive to negative `Pi64`.

For exact rational canonical `q1,q2`, enclose sine and cosine at `q1` and `q1+q2`. Their magnitudes are less than eight under the original angle domain. At each precision choose a finite Taylor degree using the uniform interval `[-8,8]`; the cosine remainder is at most `8^(2*N)/(2*N)!`, and the sine remainder at most `8^(2*N+1)/(2*N+1)!`. Choose `N>=5` with both at most `2^-(p+8)`. The recurrence-count, exact-work and operand guards apply throughout degree selection and summation. This selection is an explicitly bounded computation, not permission to run until an arbitrary floating-point term looks small.

The paired loop evaluates the two polynomials with outward interval operations and adds the exact Lagrange remainder bounds. The derivative magnitudes of sine and cosine are at most one on the real line, which establishes these remainders. Initial zero has the exact sine/cosine pair `[0,1]`.

Form enclosed real forward kinematics:

```text
px = a*cos(q1) + b*cos(q1+q2)
py = a*sin(q1) + b*sin(q1+q2)
residual2 = (px-x)^2 + (py-y)^2
```

Admission is numerically certified only when the upper bound of `residual2` is at most exact `1/10^18`. No approximate square root is needed for that comparison. A final runtime completion must still measure and validate the actual evaluated end site as specified by the action contract. This mathematical residual proof does not establish the error of an unrelated host trigonometric implementation.

The sine/cosine enclosure here is only for the bounded two-angle calculation. It does not prove arbitrary root-spin argument reduction, noncommuting quaternion composition, normalization, source-pose error, destination SLERP error or a complete recorded-geometry error bound. Those require their own identified implementation and uniform numerical evidence before delivery acceptance.

## 8. Exact interpolation, limits and runtime obligations

After admission, canonical start and target coordinates and duration remain exact binary64 rationals. For exact local elapsed time `u` and duration `d`, compute `start + (target-start)*u/d` and `(target-start)/d` exactly, then apply nearest-even binary64 rounding once to each exposed coordinate and rate. Do not convert an exact rational clock through binary64 before the expression. Natural completion publishes the admitted target bits exactly. Pause holds both coordinates and claims; stop or completion releases both claims under the separately specified atomic boundary transaction.

The numeric helper must not commit a coordinate, claim, goal result or action state. The runtime stages both coordinates together and commits only after all same-boundary operations succeed. Cached immutable mathematical evidence cannot establish a later request's source authority or current physical state. A lower work budget or cancellation during any constituent phase must leave that transaction unpublished according to the inherited rules.

Before production acceptance, implement and exercise all of the following against the adopted contract:

- Preflight exact rational widths before multiplying, shifting, dividing or invoking integer square root; enforce the finite schedule and all counters across retries within one admission.
- Charge every interval operation, classification/sign/rounding operation and other required work against the program's **remaining shared** work budget. Record actual omitted work when a bounded immutable proof cache is reused; do not deduct fictitious work or waive fresh dynamic checks.
- Check cooperative cancellation at bounded helper boundaries, before and after native integer square root, while constructing histories and while preparing outputs. Measure the chosen bounded primitives' practical latency.
- Verify exact canonical target bits, selected closed-limit behavior, whole-boundary rollback, repeated-admission/cache behavior, lowered budgets and cancellation with actual runtime execution. The standalone mathematical verifier does not execute these source-level effects.
- Establish a uniform numerical error contract for the actual source-pose and recorded-destination implementations. Dense sampled agreement alone does not prove all-time error bounds.

The bounded method proves a result when its complete enclosure succeeds. It does not claim that every mathematically admissible binary64 input will be resolved by the five passes. A hard case outside the finite numerical proof capacity must return the declared numerical/resource outcome without geometric relabeling. The full original target corpus and the separately identified smallest-subnormal-target probe are explicitly checked; unexecuted inputs are not silently certified.

## 9. Reproduction and evidence scope

The independent [interval checker](interval_oracle.py) imports neither the runtime nor the original Decimal oracle. [verify_rounding.py](verify_rounding.py) consumes the original prescribed inputs and expected bits, regenerates the [certificate](rounding-certificates.json) byte-for-byte, checks adjacent cells independently, and runs mathematical, wrong-cell and resource probes. The certificate's exact input inventory includes this document and both scripts. The [fresh check report](numeric-review/check-report.json) identifies interpreter/platform, start/end times, the checkout head, all actual input hashes, measured counters and its limited scope.

From the repository root:

```bash
python3 docs/language-design/planar-reach-v0.1/verify_rounding.py
python3 docs/language-design/planar-reach-v0.1/verify_rounding.py --emit-certificate /tmp/reach-rounding-rebuilt.json
```

The emitted path must not already exist. Its bytes must equal the retained certificate. A report output also refuses to overwrite an existing report. The original corpus and expected values are never regenerated by these commands. A mismatch is a discrepancy to investigate and preserve, not permission to edit the expected coordinate.

This closes only the identified proposed mathematical-preparation checks. Separate review, publication and an adoption record are required before runtime work, followed by actual source, Agent, native destination, browser, compatibility and complete release gates. The full [GOAL](../../../GOAL.md) remains open.
