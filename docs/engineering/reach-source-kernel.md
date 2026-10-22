# Reach source and lifecycle implementation

This implementation note describes the explicit `planar-reach-0.1` source path.
It does not change the adopted contract, its frozen corpus, or any earlier
profile's numerical behavior. Runtime and release acceptance are separate from
the static implementation checkpoints recorded in Git.

## Source authority and the transaction

The builder produces an immutable description with source identities, two joint
references, the tip, framed target, duration and selected branch. Actual named
descriptions are structurally bound after the ordinary relation validation.
Construction performs no inverse-kinematics admission.

`ReachSimulator` extends the inherited force transaction. Both coordinate claims
and the selected target are admitted together. Natural completions and all
ordered source statements operate on one staged state. Complete reach maps and
incoming-release records pass their output guards before that state is committed.
An exception retains the incoming state, both original claims and the event index.
The released sphere receives the saved incoming pose and velocity, including
the reach's exact slopes and root motion even when the reach completes at that
same clock. Public goal outcomes are pending, active, interrupted and satisfied.

Each before/after side contains every named reach, including pending actions.
Stopped and completed terminal results remain latched while the current physical
coordinates can subsequently move under a different owner. Source-only inspection
cannot synthesize a run; it returns the adopted `run_required` availability.
Agent acceptance and issued run identities are bound by the Agent publication
layer, rather than inferred from a zero timestamp or modified in historical data.

Ordinary move/spin target projections in a 0.6 prefix use the same controlled
arithmetic as its source poses and share its request cache. An exactly overflowing
move target retains the inherited unavailable-target result; resource failures
and callback interruptions remain failures. Explicit non-world inspection accepts
the same work context and interprets sampled canonical quaternions as proper
projective rotations. It rotates world-measured velocities into the requested
axes without subtracting carrier motion. World inspection preserves the original
sampled tuples. The default inspection path for older profiles is unchanged.

## Work and output counting

The compiler owns a transient `ReachExecutionWork` whose external callback charges
the same `ConstructionBudget` that counted the preceding compilation. Evaluation
and delivery accept this object explicitly for the same request. A separate direct
evaluation creates a fresh bounded context. Neither the immutable model nor a
saved run stores the elapsed clock, proof cache or request counter.

Numerical helpers charge every actual arithmetic constituent through that shared
work context. The separately capped admission recurrence count never creates a
second 100,000-operation allowance. Callback exceptions keep their original identity.
Fixed phase sums/products of at most eight exact fractions first charge a
domain check and guard every operand, including operands beside a zero factor.
They then omit exact zero summands, unit factors, and the artificial initial
zero/one accumulator. A zero product is returned only after every operand has
passed its width guard. Every remaining arithmetic operation is charged as
before; other input shapes retain the general guarded reduction. This changes
no phase-bound value or tolerance.
Ordinary scalar tweens in a 0.6 scene also use the guarded exact helpers. A narrow
force-aggregation hook preserves the inherited order (exact force sum, canonical
net force, exact gravity plus canonical net force divided by mass, canonical
acceleration), while charging each executed decode, arithmetic and rounding
operation. Earlier profiles retain the original helper body and callback counts.

JSON traversal has different units. `measure_reach_json` still counts every
recursive value/container occurrence and every compact UTF-8 byte, including
repeated identities and descriptions. It batches at most 128 traversal callbacks
into one cooperative work checkpoint, matching the inherited bounded-data
strategy. A remaining partial batch is flushed on completion. Traversals retain
the finite 100,000-entry, 4 MiB and depth limits, and numerical arithmetic never
uses this batching adapter. This does not waive any intermediate or final Agent
logical-entry budget, including the adopted exact `N`/`N−1` publication probe.

The source 0.6 force-history projection uses this same traversal adapter.
Every object is still visited in the inherited order, each active/latest force
record is freshly projected, and every repeated JSON value is measured against
the same remaining cumulative entry and byte limits. Depth, scalar finiteness,
container type, Unicode and cycle checks remain the original JSON walk. The
inherited force diagnostic still translates an exceeded output bound. Only
short-string traversal callbacks are grouped into the existing bounded batches;
the object/force iteration checks and numerical force arithmetic are unchanged.
Earlier source profiles continue to use their original force implementation.

Complete source snapshots also pass through inherited `bounded_data` before
publication. This expands internal geometry dataclasses into their complete
JSON contents under the same recursive entry/byte/depth guards. It preserves
every geometry field and counts repeated occurrences; applying a JSON-only
counter directly to an internal `LoftSection` is not a valid materialization.

`reach_record_bound` uses the maximal complete lifecycle shape rather than pending
null fields. `boundary_history_bound` implements `H06`: both inherited side
weights, both complete reach maps, the wrapper and source clock, and the full
incoming-release array. Contributor bounds follow the actual finite topology and
include every potentially contributing named action. The prefix horizon prevents
later authored force/impulse histories from entering the bound. Actual output is
still measured after this conservative preflight.

The first integrated lifecycle run demonstrated real shared-work exhaustion,
despite valid individual samples. The next implementation reuses immutable
constant transforms and one replaceable pose slot per source path inside the
same bounded request cache. A slot is valid only when its private parent and all
local numerical operands match. Paused states therefore reuse the same actual
arithmetic result across different clocks. Changed coordinates, exact slopes,
root motion, attachment or dynamic anchors invalidate the corresponding input
signature. Each lookup and insertion is charged, while arithmetic actually
avoided by reuse is not invented as executed work. Cache capacity and all
per-output occurrence counts remain unchanged.

One complete reach-map projection may contain many named actions describing
the same current physical chain. A transient map reuses only immutable
physical operands for an identical ordered shoulder/elbow pair, base frame,
tip and target coordinates. The map belongs to one exact state/time/side call
and is discarded when that call ends; it never crosses an event boundary or
another requested observation. Its capacity is at most the smaller of the
128-action bound and the current request's cache capacity. Each lookup and
insertion is charged and remains cancellable.

Every action is still visited separately. Its own admission, lifecycle, elapsed
clock, solution, claims, identity, source span, context and terminal history
are projected freshly. Cached physical tuples become distinct mutable output
lists, and every complete action projection passes the same repeated-value,
byte and entry accounting. Pending actions sharing an active physical chain
therefore retain pending/null admission fields while observing that chain's
actual current motion. Reuse neither performs an unrequested admission nor
substitutes one action's provenance or ownership for another's.

## Controlled poses and continuous ideal state

Only source 0.6 dispatches to the controlled pose helpers. Private projective
rotations and exact derivative values remain private through parent/child
composition. Canonical tuples are exposed at samples and true event anchors;
older profiles retain their existing arithmetic. The separate numerical derivation
identifies each controlled helper and its error bound.

`reach_phase.py` derives a uniform bound from the actual incoming topology,
exact phase operands and retained anchor errors. `phase_bounds(start, end,
state=None)` returns immutable `PhaseBound` records for objects and frames, plus
`JointPhase` records for resolved scalar joints. The caller must split at every
authored event, action completion and force completion; an interval crossing one
of those boundaries is rejected. A point interval is useful for transferring
anchor error, but is never substituted for the subsequent whole interval.

Every action retains an ideal initial coordinate or position separately from its
actual canonical initial value. The ideal reference is continuous at a stop or
replacement. Both paths subsequently approach the same canonical admitted target.
For a scalar action of duration D, with actual initial a, continuous ideal initial
i, canonical target g and exact lifecycle elapsed clock u:

```
actual affine coordinate = a + (g-a)*u/D
ideal coordinate         = i + (g-i)*u/D
actual slope             = (g-a)/D
ideal slope              = (g-i)/D.
```

These slopes apply while running; held phases have zero derivatives. The source
hinge receives the separately rounded actual affine coordinate, while its spatial
derivative receives the exact actual slope. `JointPhase.actual_start` and
`actual_end` name the exact affine values before scalar exposure, not a sampled
binary64 result. The maximum affine discrepancy on a phase is attained at an
endpoint. Its coordinate bound adds `max(abs(actual endpoints))*2^-53 +
3*2^-1075` for exposure. An unclaimed held coordinate uses the exact discrepancy
between its canonical coordinate and retained ideal coordinate. Completion at
the common canonical target removes the initial-coordinate discrepancy; stopping
partway retains it for the next action.

Root translations use exact affine arithmetic from separately retained actual
and ideal starts. A stopped root spin retains an angular discrepancy and the
actual materialized projective quaternion. A subsequent spin begins at that
same canonical quaternion without an extra normalization of its elapsed-zero
public bits. All ideal state lives inside the staged boundary transaction, so a
failed admission also rolls back these proof inputs.

### Reusing completed phase operands

Each occurrence still resolves its own incoming relation, coordinate claimant,
action status, initial values, canonical target and exact elapsed clocks. The
completed pure `JointPhase` or local `PhaseBound` may then be shared under a key
containing all of its numerical inputs. Under the ordinary 32,768-bit domain,
strict immutable integer, Fraction and finite binary64 operands can identify
that completed result before repeating their scalar decoding. Every input is
checked for its current type, finiteness and width before lookup; every returned
field is guarded again. At most sixteen scalar operands enter one such key.
All finite binary64 decoding uses at most 1,075 prospective bits. Narrower
domains and unusual operands follow the original scalar decoder. A callback
that changes the domain during lookup or publication forces that ordinary path;
an interrupted callback retains its original exception.

Translated constant poses can also share the completed zero-extent bound. For
constant input extent `m`, the normal position allowance is the base allowance
plus `m*2^-53`. An inverse constant has `M = 2*m + 2*e`, `L = m`, and its
position allowance is the inverse zero-extent base plus
`m*(2^-91 + 2^-52)`. These are algebraic substitutions in the uniform equations
below; every other bound field is identical. This factorization requires the
ordinary operand cap and an exact extent of at most 2,048 bits. The extent and
fixed allowances leave room for every prospective operation in the original
constant proof. Larger extents and narrowed domains use those original equations.

Completed operands and the two constant templates use the same existing
256-entry request LRU as all other numerical reuse. There is no occurrence
cache, persistent proof state or additional capacity. Complete object, frame and
joint maps, source identities, admission decisions and event histories retain
their original meanings. This removes repeated decoding and fixed constant
arithmetic without changing a bound, tolerance or operation limit. Signed
coaxial derivative proofs and optional recording-law witnesses execute normally
after the same generic local bounds have been obtained.

This implementation recovers the independent native-operand and constant-template
part of `9d31ea4369f7d003a255a905aa74f442818119ed`. Its older deferred-location
representation is not required by these equations. Historical verification of
that other source revision does not establish verification of this port.

## Uniform path counts and extents

All quantities below are exact Fractions. `e = 2^-96` is one private vector
rounding allowance. Position extents are L1 upper bounds; position, angular and
derivative errors bound Euclidean norms or proper-rotation angles. For a proper
rotation, an output L1 norm is at most twice the input L1 norm, and a rounded
three-vector adds less than `2*e` in L1 norm. These deliberately conservative
inequalities avoid a host square root in the path proof.

| Local operation | Trig count | Product count | Position-vector rounds |
| --- | ---: | ---: | ---: |
| Canonical root or constant local pose | 0 | 1 | 0 |
| Root/dynamic spin with nonzero angular velocity and elapsed extent | 1 | 3 | 0 |
| Hinge local pose | 1 | 1 | 0 |
| Slider local pose | 0 | 1 | 0 |
| Inverse constant child site | 0 | 1 | 1 |
| Compose two private poses | sum of children | sum of children + 1 | sum of children + 2 |

The counts bound all imports, axis/spin constructors, Hamilton products and
position-vector stages, including a constructor's own rescale. An exact or
cached fast path may execute less arithmetic; that does not invalidate the
conservative error allowance. Fixed identity joints add no local constructor.
The actual relation path includes parent sites, follows, both joint site
transforms and the selected final site. It is not just the two reach hinges.

Let M denote a private position's L1 extent and L the accumulated offset extent.
A constant pose has its exact canonical position L1 norm as M and zero L. Its
inverse has `M <= 2*input_M + 2*e`, `L = input_M`. For a composition of parent p
and local l, the recurrences are

```
M = M_p + 2*M_l + 4*e
L = L_p + L_l + M_l.
```

Root affine and dynamic parabolic extents use the triangle bound over the full
absolute elapsed interval, not endpoint samples. Slider extent is its canonical
axis L1 norm times the maximum absolute affine coordinate. Coordinate-angle and
anchor errors sum through composition. The shared numerical derivation then
gives, including final source exposure,

```
R_internal = R_anchor + R_coordinate + N_trig*2^-74 + N_product*2^-91
n_sr       = R_internal + 2^-50
n_sp       = P_anchor + L*R_internal + N_vector*e + M*2^-53 + 3*2^-1075.
```

`PhaseBound` exposes every input to these formulas as well as `position_error_m`
and `rotation_error_rad`. No successful inverse-kinematics residual or point pose
certificate supplies a missing path term. Root and dynamic spins register a
`spin_plan(omega, maximum_absolute_elapsed)` over the complete phase. Sampling
may reuse that plan only for the same canonical angular velocity and within its
proved elapsed range; a point reduction never establishes uniform coverage.
The finite reducer certifies an error bound, not exactly rounded transcendental
values. A larger phase extent can select a different precision and change the
last source pose bits. Comparisons across independently chosen reduction plans
therefore use the explicit source allowance. Actual materialized event anchors
always retain their original canonical tuples and are never regenerated from a
later plan.

## Ideal derivative and source derivative bounds

The path recursion retains ideal bounds V, A, W and B for linear speed, linear
acceleration, angular speed and angular acceleration. With `d = M_l + n_sp_l`,
one composition obeys

```
V = V_p + W_p*d + V_l
A = A_p + (B_p + W_p^2)*d + 2*W_p*V_l + A_l
W = W_p + W_l
B = B_p + W_p*W_l + B_l.
```

These follow by differentiating the actual parent/local pose relation. They
cover moving local joints and a moving carrier together. Constant poses have
zero ideal derivatives. A hinge has ideal W equal to the absolute exact ideal
slope. A slider has V bounded by axis L1 norm times that slope. Root translation
and spin use the canonical authored velocity vectors; free dynamics use the
ideal acceleration and propagated anchor velocity discrepancy.

Separate `actual_speed_upper_m_per_s` and
`actual_angular_speed_upper_rad_per_s` bound private source derivatives. Denote
these by v and w. The source composition bounds include private rounding:

```
v = v_p + w_p*(M_l + e) + v_l + 2*e
w = w_p + w_l + 2*e.
```

With source derivative errors E_v and E_w, let
`E_offset = n_sp_l + n_sr_p*M_l + e` and
`round(x) = x*2^-53 + 3*2^-1075`. Then

```
E_v = E_v_p + E_w_p*(M_l+n_sp_l) + w_p*E_offset
      + E_v_l + n_sr_p*v_l + 4*e + round(2*v)
E_w = E_w_p + E_w_l + n_sr_p*w_l + 2*e + round(2*w).
```

The factor two converts a Euclidean derivative bound to a safe L1 bound before
public component rounding. These error quantities remain separate from ideal
V/A/W: numerical error is not presented as intended physical motion.

Reach axes are exact +Z. An auxiliary hinge can have a canonical axis whose norm
differs from one, while the controlled rotation normalizes its axis. Its inherited
raw-axis velocity convention therefore contributes the additional discrepancy
`abs(norm(axis)-1)*abs(ideal_slope)`. The implementation bounds this without a
square root by `abs(sum(axis_i^2)-1)*abs(ideal_slope)`, since the positive norm
plus one is at least one. It also includes axis L1 norm times the actual/ideal
slope difference. A slider includes the corresponding linear slope discrepancy.

## Release, force and impulse anchors

An incoming release transfers the actual exposed position, orientation, velocity
and angular velocity at the incoming side, even if a contributing action naturally
completes at that clock. Its four source error bounds are captured from the same
incoming topology and carried into the free trajectory. They are not reset to
zero when the new actual canonical anchor is created.

For a dynamic phase, let P0/R0/Ev0/Ew0 be the retained errors at its proof clock,
T the maximum elapsed distance from that clock, and Ea the L1 difference between
actual canonical acceleration and exact ideal acceleration. The ideal acceleration
uses canonical gravity plus the exact sum of all active canonical forces divided
by canonical mass. The source retains the inherited canonical net-force and
acceleration arithmetic. Consequently

```
P_anchor = P0 + Ev0*T + Ea*T^2/2
R_anchor = R0 + Ew0*T
E_v      = Ev0 + Ea*T + round(actual_speed_upper)
E_w      = Ew0.
```

The current phase's controlled spin and final source pose exposure are added by
the uniform formulas above. Ideal speed and angular speed are bounded by their
actual magnitudes plus the corresponding errors. Ideal acceleration uses the
exact active-force sum. A force change that leaves canonical acceleration equal
retains the original actual trajectory anchor, as inherited semantics require.
Its proof clock may still move: exact ideal force sums can differ even when both
round to the same acceleration. The incoming public-point bound is converted
back to the continuing private trajectory by adding the exactly measured
position/velocity publication discrepancies and the quaternion exposure bound.
Actual anchor time and proof anchor time are distinct fields.

A nonzero impulse preserves incoming position/orientation discrepancies. Its
lever error is bounded by incoming rotation error times the self-point L1 norm,
controlled rotation error and actual lever publication error. Multiplying by the
impulse L1 norm and adding angular-impulse publication error bounds the applied
angular-momentum discrepancy. Division by canonical inertia and the exactly
measured final angular-velocity rounding are added to incoming angular-velocity
error. Linear impulse propagation analogously adds the exact final velocity
rounding to incoming error. A zero impulse does not replace either actual or
proof trajectory anchors.

All phase arithmetic, width guards, cache operations and source traversal checks
consume the same request work context. The implementation and focused tests are
separately identified code inputs; source-to-recording, independent destination
and visual acceptance still require their actual release execution evidence.

## Recording samples after complete prefix validation

The direct `recording_frames(time, state, selected_paths)` path, with neither
an optional `recording_context` nor alternate `recording_pose_ops`, consumes an
already validated phase state and its previously derived uniform bounds. It
returns immutable records containing only canonical `position` and
`orientation` tuples. The canonical bit-identity claim in this section applies
only to that direct path. Recurring and bounded native recording paths return
private recording endpoints with their separately derived endpoint allowances;
they do not imply identical canonical source bits or an earlier recorder's
binary32 accessors. No recording path advances events, materializes action
histories, or substitutes partial output for a complete source observation.
Full prefix replay, complete boundary records and the complete uniform proof
remain required before any recording sampler.

The direct sampler shares the full resolver's topology and controlled position/rotation
expressions. Position and rotation are algebraically independent of the spatial
derivative components. Its private intermediate derivative vectors are therefore
zero, allowing the existing exact-zero arithmetic paths to avoid unused cross
products, rotations and final derivative projections. Those private zeros are
never returned as source velocities. The selected frame ancestry alone is
resolved, and only selected final p/q tuples are exposed. Given the same source
state and reduction plan, this direct path's canonical position and quaternion
bits match the complete resolver. Frozen event anchors remain their original
tuples.

Recording pose slots have a distinct cache namespace, so a derivative-free value
cannot replace a complete lifecycle pose. Both namespaces and immutable topology
maps use the same finite request cache. The topology key contains the complete
program revision and active grip set: only grip activity can change this
profile's relation graph. Each key/lookup remains charged, and a changed release
state cannot hit the earlier topology. A full source observation still resolves
and checks every required object, frame, derivative and lifecycle field.

The optional production implementation
`ontokin.recording-planar-binary64-enclosures/0.5` uses bounded native planar
interiors after the first ordinary key of each phase. The
[complete candidate derivation](reach-recording-certified-planar.md) covers
its exact affine laws, native complex products, supported dynamic roots,
structural zeros and complete-phase fallback. Its explicit `P` and `16Q`
recording allowances are added to endpoint certificate terms; the actual
binary32 conversion remains a separate term. Source `Sp`/`Sq`, canonical
coordinates and rates, quarter-allocation inequalities, caller tolerances,
the 100,000-operation limit and the shared 256-entry cache remain unchanged.
The supplied-byte reader independently derives source poses and verifies the
actual delivered endpoints and interval bounds. No native helper supplies
expected values to that reader. The implementation and derivation both belong
to the complete numerical-basis hash closure.
