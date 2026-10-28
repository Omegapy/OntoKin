# Source world-rate acceptance decision 0.1

## Decision and authority

Decision identity: **`ontokin.reach-source-rate-acceptance/0.1`**.
Review date: **2026-10-21**.
Review method: independent static mathematical and source review by the
`docs_acceptance` engineering worker, separate from the implementation worker.

The exact point-to-interval-box rule in
[the proposal](reach-rate-acceptance.md) is accepted as the numerical comparison
method for the two derived world-frame inspection vectors
`velocity_m_per_s` and `angular_velocity_rad_per_s`. Its allowance must be
the independently reconstructed source arithmetic error for the identified
source, canonical carrier, exact time, event side and reviewed implementation.
An arbitrary caller-supplied allowance is not release evidence.

This decision supplies the previously missing acceptance method for these
derived vectors. It adopts no new constant tolerance. The mathematical basis is
the error derivation below, not a sample count or an observed maximum error.
It does not establish a passed `source_execution` role or a passed finite
release. Both remain subject to actual, complete, identified execution and the
[adopted release contract](../language-design/planar-reach-v0.1/release-contract.md).
`full_product_goal_completed` remains false.

The frozen language, corpus, expected values and original oracle remain
unchanged. The language's exact binary64 comparisons for resolved targets,
sampled joint coordinates, physical joint rates and per-action joint rates
continue to apply. Source residual and derived-pose limits, destination limits,
request budgets, supported domains and failure semantics retain their existing
values. This decision does not authorize a different source trajectory.

The distinction matters because the adopted profile specifies metres and
radians for its derived-pose comparison limits, but supplies no dimensioned
tolerance for the derived world-rate fields. Applying either pose limit to a
rate would be unjustified. The existing
[source case map](reach-source-acceptance-validation/source-case-map.json)
therefore correctly records world-rate comparisons as measurements pending an
explicit method. This decision addresses that gap without treating a preparation
oracle's binary64 output as an exact real derivative.

## Reviewed input scope

The review began at `bbfddddb8ecea939cb75b975250805a53cd3c6c5` and then
reviewed the independent rate worker's candidate `c5aeeb1e82223b793908859abd2980033894129c`, including its
selected observation and guarded state-sharing changes. The immutable member
identities at the end of this document determine applicability; a branch name
or a passing old report does not.

The production path reviewed is `ReachPoseOps.compose`, its exact vector
helpers and public projections, `joint_phase`/`phase_bounds`, and
`ReachSimulator`'s root, release, force and impulse handling. The independent
path reviewed is `ReachReference`'s interval arithmetic, event ledger,
`_root_pose`, `_pose_map`, `_source_basis`, `_release`, `_aggregate` and
`_impulse`. The comparison and observation paths are in
`tools/reach_source_rates.py`.

The independent implementation imports no production solver, pose kernel,
source sampler, recording planner or certificate generator to select an
expected derivative. It does use the compiled source model. Consequently,
source typing, compilation, full source closure, actual geometry and inspection
semantics require their separately mapped checks. Source hashes identify a
model's origin; they do not prove compiler correctness.

No runtime tests were executed by this review worker. Execution evidence must
identify its actual commands, interpreter, inputs, results and output members.
The proposal's old `proposed_not_adopted` report field is retained as historical
producer metadata; a release collector must explicitly bind this separate
decision and verify its applicable input identities. It must not rewrite an old
report into a fresh execution.

## Exact comparison

For the observed binary64 vector `a`, convert each component exactly to a
rational. Let the independent ideal vector `i` belong to the rational box
`B = product([l_j,h_j])`, and let `E >= 0` be its independently justified
Euclidean source error allowance in the same physical units. Define

```
d_j = max(l_j - a_j, 0, a_j - h_j)
D_j = max(abs(a_j - l_j), abs(a_j - h_j))
L2  = sum(d_j*d_j)
U2  = sum(D_j*D_j).
```

For every `i` in `B`, `L2 <= norm(a-i)^2 <= U2`. Each component interval
contributes its exact nearest and farthest distance; the maximizing corner may
mix low and high endpoints. Thus:

| Exact relation | Numerical result | Release handling |
| --- | --- | --- |
| `U2 <= E*E` | `proved` | Eligible numerical evidence, subject to identity and completeness checks. |
| `L2 > E*E` | `contradicted` | Failed numerical evidence; preserve the actual contradiction. |
| Otherwise | `unresolved` | Pending numerical evidence; it cannot count as a pass. |

Equality is allowed. Exact rational squares retain subnormal differences and
avoid a floating-point norm's underflow or rounding. No selected midpoint,
per-component epsilon or floating-point square root enters the verdict. A
finite interval can be too wide to decide the question; that is an honest
unresolved result, not a justification to enlarge `E`.

## Why the independent enclosure contains the ideal rate

The reference reconstructs exact event clocks, source topology, action claims,
actual canonical starts and separately retained continuous ideal starts. A
running scalar action uses `(g-i0)/D` as its ideal slope, where `g` is the same
canonical admitted target as production. Pause/stop/completion sides use their
defined zero or incoming slopes. Stops retain ideal state; a successor starts
from it. The saved incoming state remains available when an event's outgoing
transaction fails.

Independent interval arithmetic rounds every rational endpoint outward. Its
square-root enclosure uses integer roots with an explicit next-grid upper
endpoint. Its reduced sine/cosine enclosure evaluates an exact rational Taylor
sum and bounds both the alternating tail and the input interval's half-width;
sine and cosine are globally 1-Lipschitz. Machin's identity and alternating
arctangent tails enclose pi. A quadrant is merely a reduction choice: the
resulting complete reduced interval must lie in the proved series range, or
the request fails. No host transcendental supplies an expected answer.

Quaternion imports normalize interval enclosures and mathematical composition
uses the rigid-body equations. Quaternions denote proper rotations up to a
global sign. A source quaternion's canonical sign can differ from the
reference's representative; this does not change rotated positions or rates.
The anchor enclosure only needs to contain a representative of the same proper
rotation. For relative rotation angle `R`, an aligned unit-quaternion chord is
at most `R/2`, so component expansion by the documented `R` is conservative.
The reference does not establish literal component equality by that expansion.
An uncertain normalization that could contain zero fails explicitly.

The reference's finite precision, operand and work guards limit the calculation.
Failure to construct the enclosure is not a numerical pass. The callback's
exception identity and the caller's existing work allowance remain intact.

## Composition derivative proof

Use subscripts `p` and `l` for parent and local frames, and `s` and `i` for
the private source arithmetic and the ideal motion. One composition obeys

```
r = R_p p_l
v = v_p + omega_p cross r + R_p v_l
omega = omega_p + R_p omega_l.
```

All magnitudes below bound Euclidean norms unless explicitly called L1.
`M_l` bounds the private local position's L1 norm. `e = 2^-96` bounds one
private vector rounding. `P_l` and `R_p` bound the local position and parent
proper-rotation discrepancies. `v_p`, `w_p`, `v_l`, `w_l` bound actual private
rate magnitudes. The documented source position/rotation allowances include
their private error plus a nonnegative final-publication term; they therefore
bound both the private and exposed values. The derivative recurrence has the
same stronger invariant. It is not inferred from a measured public error that
might accidentally cancel an internal error.

Proper rotations preserve Euclidean norm and satisfy
`norm(R_s-R_i) <= angle(R_s,R_i)`. Consequently the ideal local radius is at
most `M_l + P_l`, and the rotated local-offset error is bounded by

```
E_offset = P_l + R_p*M_l + e.
```

For the cross term, add and subtract `omega_s cross r_i`:

```
omega_s cross r_s - omega_i cross r_i
  = (omega_s-omega_i) cross r_i
    + omega_s cross (r_s-r_i).
```

Its norm is at most `E_w_p*(M_l+P_l) + w_p*E_offset`. For a rotated local
rate, add and subtract `R_i*v_s`; the error is at most `E_v_l + R_p*v_l`.
These choices explain why the recurrence uses an ideal radius with the omega
error and an actual omega with the offset error. Mixing those operands without
the associated discrepancy would leave a gap.

The actual implementation rounds the rotated offset, the rotated local rate
and the final vector sum. All other vector products and sums are exact guarded
rational operations. Thus its private magnitude bounds are

```
v = v_p + w_p*(M_l+e) + v_l + 2*e
w = w_p + w_l + 2*e.
```

For a three-vector, L1 is at most `sqrt(3)` times its Euclidean norm, hence
less than twice it. Define `round(x) = x*2^-53 + 3*2^-1075`. This bounds the
L1, and therefore Euclidean, error of binary64 component publication for an
L1 magnitude bound `x`, including subnormals. The following reviewed recurrence
is conservative for both private and public derivatives:

```
E_v = E_v_p + E_w_p*(M_l+P_l) + w_p*E_offset
      + E_v_l + R_p*v_l + 4*e + round(2*v)
E_w = E_w_p + E_w_l + R_p*w_l + 2*e + round(2*w).
```

The four-`e` velocity allowance exceeds the remaining vector-rounding stages;
it is not an estimated sampled error. Exact-zero and cached paths can omit
arithmetic only after validating their complete operands, and the ordinary
final grid projection remains where an inherited rate may be off-grid. These
optimizations do not change the recurrence.

The corresponding ideal speed, acceleration and angular acceleration bounds
follow by differentiating rigid-body composition. With `d = M_l+P_l`, they are
`V_p+W_p*d+V_l`, `A_p+(B_p+W_p^2)*d+2*W_p*V_l+A_l`,
`W_p+W_l`, and `B_p+W_p*W_l+B_l`. They are separate from numerical errors.
This pointwise decision does not replace their complete-phase delivery proof.

## Local motions and anchors

Constant transforms have zero rates. Authored root translation/spin vectors
are already canonical binary64 values and their exact rate is retained.
For running joint motion, actual and ideal slopes may differ because a previous
stop exposed a rounded actual coordinate while retaining a continuous ideal
coordinate. Both slopes and their difference are exact rational expressions;
the error is retained rather than reset at a new action.

For an auxiliary hinge with canonical nonzero axis `a`, production retains its
inherited raw-axis rate while ideal rotation uses `a/norm(a)`. The discrepancy
is at most `L1(a)*abs(s_s-s_i) + abs(norm(a)-1)*abs(s_i)`.
Since `abs(norm(a)-1) <= abs(sum(a_j*a_j)-1)`, the implemented exact square
defect is safe. Reach's own axes are exact +Z. A slider uses the corresponding
linear slope error with its actual canonical axis.

An incoming release captures the full incoming world derivative even at natural
completion. Its actual exposed anchor inherits the position, rotation, velocity
and omega error records from that same incoming topology. Natural completion
then affects only the outgoing attached state. No proof error is reset merely
because a new canonical anchor is materialized.

For a free body, let `T` measure from its proof clock, and let `Ea` bound the
L1 difference between actual canonical acceleration and ideal acceleration.
The ideal uses canonical gravity and the exact active force sum divided by
canonical mass. Then position error grows by `Ev0*T + Ea*T*T/2`, velocity
error by `Ea*T` plus publication, and rotation error by `Ew0*T` plus the
current controlled rotation arithmetic. Constant omega error remains `Ew0`.
These are integrations of a constant vector discrepancy, not a sampled fit.

When a force change preserves canonical acceleration, production keeps its
actual trajectory anchor while the independent ideal phase can change. The
proof clock therefore moves separately. The implementation adds the exact
publication discrepancy, and the independent reference adds a conservative
publication bound, to convert the incoming public error to the continuing
private trajectory. A changed acceleration materializes the real public
anchor and retains the incoming errors. Both paths preserve ideal continuity.

For a nonzero impulse, rotating the self lever contributes the orientation
error times its L1 radius, private vector rounding and lever publication.
Crossing that lever with the canonical impulse multiplies the lever error by
the impulse L1 norm; angular-impulse publication adds its own error. Division
by positive canonical inertia and final omega publication give the propagated
angular-rate error. The linear increment uses canonical impulse/mass and adds
the final velocity rounding discrepancy. Each term retains its physical units.
Position and orientation errors persist; a zero impulse preserves both anchors.
The reference independently encloses these operations, including each public
rounding, and derives its rate allowance from those enclosures.

## Observation scope and state-sharing review

The candidate selected-rate observer uses ordinary source boundary transactions,
dynamic-extrema checks and staged validation. Its current complete graph has
already exposed every object's position, orientation, velocity and omega; the
observer additionally exposes every site, including unselected sites. It then
copies only the requested rates. A cached complete object graph was checked
before cache publication, and every observation retains a cancellation check.
This avoids unrequested final geometry/history output without dropping a source
boundary or admitting a nonfinite unselected frame. Complete snapshot, Agent
and recording output limits remain separate obligations.

The candidate independent ledger shares state only when it has no dynamic
anchors and the boundary writes coordinate-action state alone. Every action
that `_finish` or `_event` can mutate is copied. Completion/stop copy both
coordinate maps; claims are private. Root lifecycle writes, release, force,
impulse and any existing dynamic anchor select the full-copy path. Without a
dynamic anchor there can be no admitted force history: this language has no
transition from dynamic back to prescribed. Shared untouched records are read
only, elapsed clocks are pure, and caches retain state/time identity. The
original logical retained-state cap still applies even when physical storage
is shared. These optimizations change no numeric recurrence or expected value.

## Evidence required to use this decision

A source-execution collector must retain the complete predetermined inventory:
all original and supplementary sample sides, the separate incoming release
and released-body observations, exact source/time/side/carrier identities, and
every frozen world-rate field's measurement link. The current inventory is
362 fresh bounded requests mapping 724 frozen fields; each requested carrier
also checks both supported vectors. Counts alone cannot establish closure:
the actual identities and mapped fields must match the frozen inventory.

Only `proved` results from the fresh execution interface, or independently
authenticated equivalent observations, can contribute numerical acceptance.
Resource failure, cancellation, missing output or unresolved comparison remains
pending or failed according to its actual cause. The original 100,000-operation
request limit, 32,768-bit operand bound and 256-entry caches remain in force.
Neither a new work object between stages nor an increased allowance can close
the gate. Actual source inputs must remain stable before and after the request.

Retain the original frozen expected rates, exact-bit comparison and exact
actual-minus-frozen differences as supplemental measurements. Their own oracle
error is not bounded by the production allowance, so they do not acquire this
allowance or determine its verdict. A frozen expectation's semantic defect
would require the release contract's separate old/new identity and review
process; it cannot be repaired by silently editing the fixture.

The full source cohort, compiler/source closure, exact joint comparisons,
Agent protocols, all hostile probes, native/browser validation, visual review,
compatibility matrix, inherited workflows and final integration audit remain
mandatory. Revisions to any applicability member below require input equality
or an explicit reviewed successor record before this decision can support a
different implementation.

## Applicability member identities

The following table is generated only from named bytes after static review.
It is an input identity record, not an execution result.

<!-- Reviewed input identities follow. -->

| Named input | Bytes | SHA-256 |
| --- | ---: | --- |
| `ontokin/reach_numeric.py` | 20138 | `3088f4447c7be89c56043e236213c7e5537e32878f7afc1e82742be29dd59f3e` |
| `ontokin/reach_kinematics.py` | 9005 | `94224673ed4d5f48b52710b4fa761a6e94283e53fec2f1c900bbd8ebe6a24b4f` |
| `ontokin/reach_pose.py` | 42987 | `4719840da2d56b68842b3bd2051be9349e21fcc46567c63c5db77599baabf9b0` |
| `ontokin/reach_phase.py` | 19367 | `ca48ee809562ee5b16b98fb5c6cc4af25baa998da0e53ef5bf43cb95bd521d27` |
| `ontokin/reach_runtime.py` | 56721 | `0534ad43541335bddcb49053c03f10adf1380a34a90e294342e351792473175c` |
| `ontokin/reach_reference.py` | 121750 | `462339eecc46af344bacbae4d9c3fe909d0de9310b4aabc8f7e34be7a55552a2` |
| `tools/reach_source_rates.py` | 29103 | `865fd385147a391a98f93ca1ed62d47373eafba2276eca68962c0355188e41d9` |
| `docs/engineering/reach-numeric-kernel.md` | 28055 | `90c82ae3e3d4461e31eefc3425278c72dcc863909085d0102eacb2c4938515f1` |
| `docs/engineering/reach-source-kernel.md` | 19910 | `74e80ca2191e8b146cd94b97d7a18ff9317802a685dc2b9d30a2248fb0f4d6db` |
| `docs/engineering/reach-rate-acceptance.md` | 18863 | `4d7627ca4d2c7542dd43cba4426b29cd7a7c40376847e4a08a7b1493a38a0b93` |
| `docs/language-design/planar-reach-v0.1/ADOPTION.md` | 5938 | `ded24c5a10ebfb57e6578299845606f770283d5fc090145e2cc206f94f6a65fe` |
| `docs/language-design/planar-reach-v0.1/profile-draft2.json` | 14085 | `5d9cf6474ccdc0dfa09c034c50aa63e3cce17e9a8de1d680a5d9932786a9b1e9` |
| `docs/language-design/planar-reach-v0.1/release-contract.md` | 14750 | `c7d7be836a9e6e4116c872d0a0f62e99b785d1d2a5a549915d129b86a5f00191` |
