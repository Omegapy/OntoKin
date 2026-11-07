# Deterministic .22 constant-spin point semantics

**Normative identity:** `OK-LANG-022-CANONICAL-SPIN/0.1.0`  
**Effectiveness:** only through the separate reviewed and published adoption

## 1. Exact scope and precedence

This additive amendment changes only constant-angular-velocity point-plan
selection within an explicitly selected source `0.22` / `torque-0.1` scene.
It applies before and after torque latch, including source dependencies whose
definitions were imported under older declaring versions. Their construction,
expression and declaration meanings remain unchanged. Earlier entry profiles,
Agent bindings, recording bindings and ordinary defaults retain their existing
semantics and implementation bytes.

For this scope, the phrases "exact inherited ReachSimulator route" in source
SPECIFICATION section 5 and "actual inherited legacy law" / "preserve the
inherited canonical path exactly" in section 7 retain all inherited anchor,
composition, rounding, transfer and error rules, **with point-plan selection
replaced by section 2 below**. This is the only numerical inheritance exception.
Source sections 1, 3, 4, 6 and 8 otherwise remain unchanged. In particular,
every nonzero canonical orthogonal angular component still refuses; no epsilon,
interval-containing-zero rule or later cancellation is introduced.

Recording sections 3, 9 and 11 shall reconstruct these amended point semantics
from immutable source. A phase proof plan, producer state or cursor does not
select a point's canonical operands. The continuous interpretation in
[NUMERICAL-PROOF.md](NUMERICAL-PROOF.md) is additive to the original complete
certificate inequalities. [COMPATIBILITY.md](COMPATIBILITY.md) defines the
bounded C3 exception, identities and durable compatibility decision.

## 2. Executable selection rule

A constant-spin point operation is identified by the canonical angular vector
`w`, the complete actual source rotation origin (including its internal
`RotationValue`, error and retained projection), and the exact rational elapsed
`d` of that source operation under its existing lifecycle. Dynamic spin uses
`requested_scene_clock - actual_source_anchor_clock`. Prescribed spin uses
the action's accumulated elapsed time, excluding paused intervals: saved
elapsed plus `requested_scene_clock - running_since` while running, or saved
elapsed while paused. Its complete original rotation origin remains unchanged.
No public quaternion, sampled pose, cache clock, proof endpoint or error-only
origin replaces the actual rotation origin or action clock law.

Perform the inherited current admission and scalar/vector/rotation checks in
their existing order. In `advance_orientation`, zero elapsed time or an exactly
zero vector returns the complete initial rotation unchanged after the existing
stationary checks. This does not construct or normalize another anchor.

For a nonstationary operation let `T=abs(d)` and consider exactly
`(96, 192, 384, 768, 1536)` in that order. At each stage `p`:

1. Use the existing guarded exact scaled-axis construction on `w`: let
   `M=max(abs(w_i))`, `s=w/M`, and let `[L,H]` be that stage's outward enclosure
   of `norm(s)`. Construct its existing Machin enclosure `[PiL,PiH]`.
2. In the existing exact operation order compute
   `extent=(M*T)*H`, `quotient=extent/PiL`,
   `K=floor(quotient)+2`, `a=(M*T)*(H-L)`, `b=K*(PiH-PiL)`, and
   `E=((a+b)/4)+2^-97`. These are bounded exact rationals and integers;
   they are not binary64 intermediate calculations.
3. Select this first stage if `E <= 2^-86`, including equality. Only the
   completed comparison `E > 2^-86` advances to the next stage. An inherited
   domain, operand, resource, callback, cancellation or deadline failure
   retains its original refusal and precedence; it is not a stage retry.
4. If all five completed comparisons exceed the guard, return the inherited
   finite source-spin phase-reduction refusal. There is no extra stage,
   widened guard, libm substitution or unbounded precision fallback.

Use the selected stage's exact scaled vector, norm and pi operands in the
unchanged controlled half-angle reduction, 13-term polynomial, 96-bit unit-axis
projection, projective rescaling and world-left quaternion multiplication.
Retain the unchanged rounding, sign, allowance and finite-publication rules.
If the selected stage's later reduced-enclosure check fails, return the
inherited finite refusal. Do not retry another stage or search for an axis
result that happens to pass admission.

`spin_rotation` remains an increment constructor; `advance_orientation` applies
that increment to the complete actual initial rotation. Signed elapsed values
have this mathematical primitive meaning where already supported; this
amendment grants no new public backwards-simulation operation.

## 3. Every relevant source operation uses the rule

The .22 implementation must dispatch at all constant-spin point consumers,
including the inherited equivalents of ordinary spin targets, prescribed
root/body spin, dynamic legacy orientation, hinge/reach parent dependencies,
ordinary action completion/latching, release materialization, ordered impulse
lever/frame calculation and subsequent genuine motion reanchors. The same
rule applies to actual point transforms used by the .22 recorder, including
unaffected branches of that .22 scene. A change only in the torque statement
or split polynomial evaluator is insufficient.

The C091 baseline's principal dispatch seam is
`ReachSimulator._advance_orientation`; its callers include
`ordinary_target`, `_dynamic_kinematics`, `_resolve_kinematics` and
`_latch_ordinary`. The .22 subclass may use a narrow override that calls the
unchanged point primitives without a history-selected phase plan. Review must
also audit direct point calls in recording/capture paths and the independent
source recipes. This seam description does not authorize changes to the nine
predecessor numerical-basis modules.

Preserve source event order, actual angular impulses and exact materialization
points. A zero impulse retains its inherited neutrality on every route. On an
already split route, a nonzero impulse that leaves canonical angular velocity
unchanged keeps the split rotation origin while transporting the full
independent error history. Before split, preserve the inherited legacy
materialization of a nonzero impulse even when its angular vector is unchanged.
A force/torque error-origin
change without a canonical rotation change preserves the complete older
source rotation recipe. Merely remembering its sampled quaternion at the new
error time would create an unauthorized motion anchor.

## 4. Plans, caches and complete current authority

A whole-phase plan may prove numerical coverage or support bounded planning.
It must not supply different stage operands to a point operation. A longer
scene horizon, sibling event, proof request, earlier query or cache residency
cannot alter successful canonical point values at a common exact clock.

Pure reuse is permitted only for the identical normative computation. Its
identity includes every input on which that result depends, the selected
method and applicable live domain/cap. A spin-plan result depends on `w` and
`abs(d)`; a rotation result also depends on signed `d` and the complete origin.
Derive `d` from the current admitted source action/dynamic lifecycle before
lookup; scene time alone is not an action's accumulated elapsed time.
An equal plan key does not authorize reuse of an unrelated rotation origin.
Retained values must be admitted under current immutable source ownership,
native scalar shapes, original execution ledger, operand limit, cache limit,
cancellation callback and deadline. Revalidate after any callback before use
or publication as required by the inherited .22 guards. Mutable private plans
and callback-writable objects are not independent source authority.

The 256-entry cache, 32,768-bit operand cap, finite schedule and original
100,000-operation / 30,000-ms defaults remain fixed. Every actual primitive
and structural operation retains its original charge. Cache hits may change
actual consumed work, which must be reported honestly. They cannot grant a
fresh budget or suppress current admission. A resource refusal remains
possible when the shared remaining allowance is exhausted; repeatability does
not promise identical counters or success after exhaustion.

## 5. Independent source reconstruction

The independent reader must implement the selected controlled point algorithm
without importing producer numerical primitives or inspecting producer plans,
state, phase tables, reported minima or artifact values as its authority. It
may read the identified immutable source/model through the existing guarded
source route and use its own exact arithmetic.

The canonical recipe must retain the complete real rotation origin, ordered
quaternion products/permutations, 96-grid vector operations, binary64
materialization and every source-derived velocity update. It must handle
evolving nonidentity parents, exact cancelling nonzero cross products,
release, ordinary completion, both changing and neutral force boundaries,
torque transitions and ordered impulses over the supported source domain.
The reference's smooth physical/error trajectory remains separate. Error
intervals establish discrepancy; they do not decide an exact-zero predicate.

Recipe representation must stay within the existing source graph/history,
operand and admitted-work bounds. Count actual source-derived nodes and
operations. An arbitrary smaller recursion limit introduced by a convenient
recipe encoding must not exclude an otherwise supported source graph. Shared
immutable subexpressions may reduce work, but may not retain unbounded hidden
history or bypass current source ownership and charge checks.

The existing all-eligible-plan WIP and Boolean support overapproximation are
not complete substitutes. A reader may refuse an actually unsupported domain
under the existing rule; it may not relabel a supported deterministic case as
unsupported solely because its recipe implementation is unfinished.

## 6. Permitted change boundary and effectiveness

Before implementation, preserve all 399 C090 frozen files and three C091
overlays, freeze the new independent regression sources/expectations, complete
source/numerical, independent-reader, recording/continuous-bound and
Agent/durable-state reviews, and publish/read back the exact authority bytes
and modes through the repository's expected-head process. An effective
adoption receipt binds those observations. A local favorable result does not
make this document effective.

Implementation may add .22-only spin/source-recipe helpers and change
`torque_runtime`, `torque_phase`, `torque_recording`, `torque_reference`,
`torque_axis_exact`, `torque_axis_reference`, `torque_transfer_bounds` and
`torque_conformance` only as required for this rule, its complete source/error
reconstruction and synchronized identities. New focused tests and independent
verification tools may be added. Existing tests, original fixtures, tolerances,
budgets and predecessor numerical-basis files remain exact. A necessary change
outside this boundary needs an explicit reviewed scope extension before code.

This authority does not waive any source, recording, resource, hostile-byte,
Agent, native-playback, interpreter, inherited local or main-integration gate.
Every failure keeps its exact original input, source revision, settings and
result. No implementation or release is accepted by adoption alone.

