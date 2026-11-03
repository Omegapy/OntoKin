# Numerical and continuous-bound argument

This document is normative with `OK-LANG-022-CANONICAL-SPIN/0.1.0`.
It changes plan selection, not the controlled arithmetic or its allowances.
The unchanged derivation is [reach-numeric-kernel.md](../../../engineering/reach-numeric-kernel.md),
especially its finite source trig/spin, spatial derivative and continuous-bound
sections. The original torque [source](../../torque-v0.1/SPECIFICATION.md) and
[recording](../../torque-v0.1/RECORDING.md) contracts retain their other rules.

## Deterministic point value and finite termination

At each precision the scaled-axis and Machin enclosures are fixed functions
of immutable canonical inputs and the fixed stage. The guard expression uses
only those operands and the exact `abs(d)`. Its ordered five-member search has
one first certifying stage or the specified finite refusal. Once selected, the
controlled reduction, polynomial, grid operations and multiplication have
fixed inputs and operation order. Thus every successful evaluation has one
canonical result, independent of request order, horizon and cache history.
Current resource/callback failures remain failures of the actual admitted
execution and cannot select a different canonical answer.

The later reduced-enclosure check remains mandatory and any observed failure
is terminal; the implementation cannot try another stage. For valid unchanged
native operands whose guarded arithmetic completes, the certification guard
also proves this later mathematical check succeeds, as shown below. Defensive
failure and actual resource/context failure do not enlarge the mathematical
domain. Producer and reader use the same prescribed domain and refusal rule.

The algorithm performs at most five stage certifications using the unchanged
32,768-bit prospective/result guards and the original charged primitives.
It adds no unbounded loop or operand allocation. Existing request resource
limits remain the final execution bound. No universal fixed work saving is
claimed; the actual regression workload must fit its original authority.

## The selected guard also covers actual point reduction

Let `[lo,hi]` be the sorted half-angle enclosure, let `x=(lo+hi)/2`,
`P=(PiL+PiH)/2`, and let `k` be the inherited nearest-even integer rounding of
`2*x/P`. Therefore `abs(x-k*P/2)<=P/4`. Each of the five fixed Machin
enclosures satisfies `0<PiL<=P<=PiH<22/7`; these exact stage-only bounds are
included in the independent frozen derivation. After 96-bit midpoint rounding,
`abs(middle)<=11/14+2^-97<1`.

The reduced interval radius before midpoint rounding is exactly
`(M*abs(d)*(H-L)+abs(k)*(PiH-PiL))/4`. Moreover,
`abs(k)<=floor(M*abs(d)*H/PiL)+1<=K` from the stage certification.
The midpoint's additional rounding distance is at most `2^-97`, so its actual
enclosure error is at most the certified `E<=2^-86`. Both later reduction
predicates therefore hold for every such valid point, including negative
elapsed time and clocks at a precision switch. The 13-term polynomial is
evaluated only within its proved `[-1,1]` argument domain.

This is a complete mathematical implication for the fixed native enclosure
method, not a sampled observation or permission to skip admission. Every
later guard, operand check, callback and charge remains in execution, with
its original failure identity and no retry after selection.

## Existence of a certifying point stage over a whole phase

Fix `w` and one precision's enclosures. For `T>=0`, `M*T*(H-L)` is
nondecreasing. `floor(M*T*H/PiL)+2` is nondecreasing because `PiL>0`, and its
multiplier `PiH-PiL` is nonnegative. Hence the stage guard expression is
nondecreasing in `T`. If a whole-phase certificate at `Tmax` passes, that
stage's certification comparison passes at every `abs(d)<=Tmax`. The point
selector may choose an earlier stage there; it never needs a later stage to
satisfy that comparison. Together with the preceding reduction lemma, the
selected mathematical kernel is defined throughout the phase. Actual
reduced-enclosure and resource checks still run under their inherited rules;
the theorem does not grant an execution budget or make changed native operands
eligible.

Stage boundaries can change rounded canonical quaternion components. No claim
of continuity or differentiability is made for the rounded point map, and
finite samples cannot establish a uniform bound across a switch.

## One discrepancy envelope covers every selected stage

Every selected stage satisfies the same `2^-86` argument guard and uses the
same 96-bit source grid, polynomial and rescaling. The inherited derivation
therefore gives the same conservative `AXIS_ERROR=2^-74` radians for each
axis/spin constructor, plus each separately counted
`PRODUCT_ERROR=2^-91` projective import/product allowance. Public materialized
rotation retains the `EXPOSED_ROTATION_ERROR=2^-50` allowance. Rounded vector
stages retain their `2^-96` Euclidean allowance and the exact existing path
counts. These constants hold for all five permitted certifying stages, not
just the stage of a chosen sample.

Let `Q(t)` denote the continuous ideal rotation for the fixed source origin
and exact constant angular velocity. At any admitted point, the chosen
controlled rotation is within the inherited per-path uniform discrepancy
`R` of `Q(t)`. This statement is pointwise for every clock in the closed phase
with the same uniform `R`; it includes both one-sided limits of a stage
switch. Two canonical values near a switch may differ, but their separate
distances to the continuous ideal reference are already covered. The proof
does not differentiate the rounded values or add a fictitious physical event.

For a composed path retain the inherited bounds, including
`R_internal=R_anchor+R_coordinate+N_trig*2^-74+N_product*2^-91`,
`P_internal=P_anchor+L_total*R_internal+N_vector*2^-96`,
`n_sr=R_internal+2^-50`, and
`n_sp=P_internal+M_position*2^-53+3*2^-1075` where their original hypotheses
hold. Carry the complete actual anchor errors and source path extents.
Do not omit a constructor or product merely because its rounded result looks
neutral. Existing proved exact fast paths retain their original allowances.

## Transfers, split rotation and recorded delivery

At a real release, impulse or other materialization, independently propagate
the old continuous reference/error history, then include every actual source
kernel, vector, binary64 and materialization discrepancy. The canonical
rotation origin and reference/error origin remain distinct. A reference-only
acceleration change never replaces the canonical source recipe. A zero impulse
retains inherited neutrality; a nonzero impulse preserves the split rotation
origin only when the split-route canonical angular vector is unchanged.
Before split, its inherited legacy materialization remains. Every applicable
nonzero impulse retains its complete independent transfer uncertainty.

Split rotation retains its existing exact polynomial, `2^20` complete-segment
phase cap, stationary-point test and binary64 phase/speed rounding envelopes.
Its anchor can now contain a deterministic pre-latch constant-spin value;
that value's complete inherited error is carried forward without resetting it.

The original recording chord argument differentiates the continuous ideal
trajectory. Its angular speed/acceleration maxima and source discrepancy then
bound the actual controlled samples and stored interpolation. Keep all endpoint
rounding cells, coherent quaternion lift checks, stored-width quarter tests,
primitive minima and dependent interval inequalities. The existing separate
source-numeric terms cover the rounded point map's discrepancy throughout the
phase; replacing them with endpoint-only checks would be invalid.

Retain both distinct radii: COM-to-marker-origin radius `rho` contributes
`V_marker<=V_COM+rho*Omega` and
`A_marker<=A_COM+rho*(Alpha+Omega^2)`; local landmark radius `r` multiplies the
complete rotation discrepancy in the final point bound. No allowance, radius,
actual transfer or final after-boundary contribution is removed by this
amendment. Destination arithmetic and its independent identity are unchanged.

