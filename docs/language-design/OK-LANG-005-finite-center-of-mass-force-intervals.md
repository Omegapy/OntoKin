---
project: OntoKin
document_id: OK-LANG-005
title: Finite Center-of-Mass Force Intervals
version: 0.1-recovery-proposal
date: 2026-10-19
status: proposed-language-contract
document_type: normative-language-proposal
language_version: "0.5"
profile: force-0.1
implementation_status: not-implemented
---

# OK-LANG-005: Finite center-of-mass force intervals

## 1. Authority, status and scope

This is a published proposal, not an adopted contract or a completed implementation. [The recovery record](force-v0.1/RECOVERY.md) preserves the earlier unpublished draft identifiers. This proposal does not claim to reproduce its unavailable bytes. Review the actual source fixtures and expected outcomes before publishing an adoption record. Runtime work starts only after that explicit decision.

The finite scope is a constant world force applied at the center of mass of an actually free homogeneous sphere for an authored positive duration. Overlapping forces add. Existing gravity, release, source impulses, native surfaces, ownership, source revisions and immutable program bundles retain their meanings. The force has no lever arm and adds no torque, body, geometry or independent motion authority. It is an external influence on the existing free-sphere trajectory.

The proposal extends [OK-LANG-004](OK-LANG-004-source-impulses-and-free-sphere-dynamics.md), which inherits [OK-LANG-001](OK-LANG-001-core-language-specification.md), [OK-LANG-002](OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) and [OK-LANG-003](OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md). All remaining [GOAL](../../GOAL.md) domains stay required.

| Binding | New explicit value |
| --- | --- |
| Source | `ontokin "0.5"; profile "force-0.1";` |
| Agent | `ontokin.agent/0.5` |
| Recorded delivery | `ontokin.glb/0.5` |
| Durable store file | `force-program-agent.sqlite3` |
| Store schema | `ontokin.force-program-agent-store/0.1` |
| Bundle and revision domain | Existing `ontokin.bundle/0.1`, unchanged |
| Diagnostic envelope | Existing `ontokin.diagnostic/0.2`, unchanged |

Earlier source, Agent, GLB and database bindings do not acquire force support or changed defaults. A source unit declares its own profile. A 0.5 unit may import pinned definition modules declaring 0.2, 0.3, 0.4 or 0.5; older units must reject new upward edges without tightening previously supported edges. The complete offline dependency closure remains authoritative.

## 2. Source spelling and identity

Add a contextual statement inside the existing ordered event sequence:

```ontokin
at 1[s] sequence {
    force ball @ "push-right"
        using vector(world, 4[N], 0[N], 0[N]) for 1[s];
}
```

This requests activation at the enclosing boundary and completion after one second. `force` is contextual only at an event-statement start. It remains an identifier in other contexts and earlier profiles. The target uses the existing member/literal-key occurrence path. The explicit `@` string is mandatory and follows the existing stable-ID lexical rules. Force keys must be unique among force statements in the entry scene, including statements at different times. Duplicate keys are rejected, not merged or silently restarted.

The vector and duration are pure elaboration-time expressions. The target must resolve to an actual object occurrence. Require a world-frame `Vector3<Force>` with finite canonical newtons, and a finite strictly positive `Time`. The `for` operand is a duration, not an absolute end timestamp. This proposal deliberately reuses the existing canonical source-time conversion instead of introducing exact decimal literals.

A force identity contains the stable scene ID and authored force key. Its record also names the resolved occurrence identity, source ID, complete accepted program revision, exact source-file revision, full UTF-8 statement span and zero-based sequence index among all statements. Moving an unchanged statement need not change its stable force key. Changing its target or operands changes its source/program revision. Identity does not authorize an edit outside the accepted source span.

## 3. Exact clocks and the requested horizon

Convert the enclosing activation time and positive duration to the inherited exact rational values of their canonical binary64 seconds. Let these rationals be `s` and `d`. The completion clock is the exact rational sum `e = s + d`, with no intervening float conversion and no epsilon. Consequently `e` may differ from a separately authored rounded decimal expression or exceed binary64 magnitude. The existing bounded rational-time serializer applies.

Activation remains within `[0, scene.duration]`. Completion may be beyond the scene duration. In that case a requested scene prefix can finish while the force remains active; do not synthesize a completion or clamp its end time to the scene boundary. No physics is evaluated beyond the requested horizon merely to predict that completion. The active interval is `[s, e)`: the before-side at `s` has not activated it; the after-side at `s` has. The before-side at `e` still has it, and the after-side at `e` does not.

Canonical clocks that are equal form one atomic boundary. Different rationals are different boundaries even when an external float format would collapse them. Two source blocks at one canonical activation time still require one authored ordered sequence, as in the inherited contract. A coincident automatic force completion does not require a second source block.

## 4. Physical admission and canonical acceleration

At activation the selected target must be dynamic, free of an active incoming following/connection authority, and have its own supported homogeneous sphere body. An earlier successful release in the same sequence can make it eligible. A force never releases a connection or changes motion mode itself. Ownership descendants are not a compound rigid body and do not contribute to the selected body's mass.

For each free dynamic sphere let `S` be its final active-force set after the complete boundary, `m` its canonical own mass and `g` the canonical world gravity. For each Cartesian component compute:

```text
exact_sum = sum(exact_binary64(F_i) for i in S)
net_force = round_binary64(exact_sum)
acceleration = round_binary64(exact_binary64(g) + exact_binary64(net_force) / exact_binary64(m))
```

The net force is an exposed canonical quantity and must be finite. Sum with exact rational arithmetic before rounding; never reject an overflowing partial float sum when the complete sum is representable. The acceleration calculation combines gravity and the quotient before its final rounding, so an unexposed `net_force/m` overflow cannot by itself reject a finite final acceleration. A nonrepresentable final net force or acceleration is `OKL-E-NUMERIC`, not a clamp, infinity, ignored influence or smaller requested output level. This two-stage rounding policy is explicit: acceleration uses the canonical exposed net force, not an undisclosed higher-precision aggregate.

The inherited finite positive mass, radius and inertia requirements remain unchanged. COM force cannot alter angular velocity. Existing source impulses can still change linear and angular velocity using their established ordered canonical update.

## 5. Atomic boundary algorithm

For every exact source, action-completion or active-force-completion boundary up to the requested horizon:

1. Evaluate and save the complete incoming pose and derivatives under the old acceleration. Preserve the inherited incoming-release semantics and action-completion order.
2. Copy the accepted state into a tentative state. Remove forces whose exact end is this boundary. Retain their completion records tentatively.
3. Execute the authored sequence in written order. A force activation checks its target against the current tentative mode and connections and stages its source record. Releases and impulses keep their existing ordering, conflict and rollback rules. A force contributes no instantaneous velocity change.
4. After the sequence, calculate each affected object's final active set and canonical acceleration. Do not validate transient force sums after individual activations or individual expirations. All intermediate *impulse* states still obey OK-LANG-004.
5. If an object's acceleration changed, anchor its next trajectory at the boundary with the tentative pose and velocities, including successful impulses or release. If acceleration is unchanged, preserve its existing trajectory anchor unless an independent inherited nonzero impulse or release already changed that anchor.
6. Validate finite state and charge the complete output/work budget before committing the entire boundary. Any semantic, numeric, resource or cancellation failure discards tentative force starts, completions, release, impulses, counts and anchor changes together.

A zero force is still admitted, identified, counted, retained while active and completed at its exact endpoint. It alone does not reanchor the trajectory. Opposite simultaneous forces can cancel without an anchor change. Replacing an expiring force with the same canonical force at the same clock likewise preserves the anchor while updating provenance. None of these rules erase the actual activation/completion history.

## 6. Piecewise analytic evaluation and failures

Between boundaries use the canonical acceleration stored with the trajectory anchor:

```text
position(t) = round_binary64(p0 + v0 * dt + acceleration * dt^2 / 2)
velocity(t) = round_binary64(v0 + acceleration * dt)
dt = exact_rational(t - anchor_time)
```

Each component's affine/quadratic expression combines exact representations of canonical operands before final rounding. Orientation retains the inherited constant-world-angular-velocity solution. Check interior quadratic extrema within each requested segment, not just its endpoints. A trajectory that leaves the finite representable domain and returns is not valid throughout that segment.

Keep separately the time dynamic mode began and the latest trajectory-anchor time. Inspection must not label a force activation as the origin of an already dynamic body. A later failure preserves the accepted source and the previously certified evaluation prefix. It must not label an uncomputed later state valid. A valid short evaluation cannot fail solely because a later activation, completion or trajectory segment would overflow. Structural source/type/domain validation still examines the authored program; this prefix rule does not permit invalid source operands.

Use existing diagnostic categories and codes: `OKL-E-TYPE` for operand or target types, `OKL-E-FRAME` for nonworld force axes, `OKL-E-NAME` for missing references or duplicate stable keys, `OKL-E-EVENT-ORDER` for a nonpositive duration or invalid source activation clock, `OKL-E-MOTION-MODE` for a target that is not currently free and dynamic, `OKL-E-PHYSICAL-DOMAIN` for invalid body parameters, `OKL-E-NUMERIC` for nonfinite canonical/exposed results, and existing resource/cancellation envelopes. Diagnostics identify the actual source and boundary side. Automatic completion failures retain the originating statement identities. Precise fixture expectations must settle any ambiguous precedence before adoption.

## 7. Agent inspection, repair and bounded work

Agent/0.5 inherits the accepted/candidate revision model, atomic UTF-8 source patches, per-file preconditions, idempotent retries, changed-payload rejection, cancellation, reset and immutable artifacts. There is no host-only operation that applies a force behind the accepted source. A new binding uses a separate store; older bindings reject it.

Each object's force projection contains: active records in canonical force-key order; canonical net world force; canonical world acceleration for free dynamic objects, otherwise null; cumulative activation and completion counts; the most recent force-changing boundary and all its successful starts/completions. Initial counts are zero and the recent boundary is null. Retain that recent list through unrelated boundaries and replace it only on the next force-changing boundary for that object. Preserve explicit world coordinates in force records even under a self-frame inspection request. Revision-bound triangle pages retain the inherited visual geometry contract.

Every active/recent record includes source identity, target identity, key, original sequence index, world force, exact activation and completion clocks. Do not duplicate geometry into these records. Count all nested records and encoded bytes against the inherited work/output limits before publishing a result. Check cancellation during force enumeration, boundary selection, exact summation, history construction, serialization and export planning. Lowered caller limits must produce explicit failures with accepted-state preservation, not truncated success. Snapshot count and nested record limits remain those of the reference profile unless a later explicit engineering decision changes them.

The actual Agent workflow must create valid and invalid candidates; inspect active influences; diagnose and reject a stale or invalid repair; atomically repair one generated occurrence's mass and one force operand/duration; prove unchanged sibling and pinned-library bytes; evaluate; export; and retrieve the exact resulting artifact. A changed duration revises the program; it does not mutate an existing run's clocks.

## 8. Recorded GLB/0.5 delivery

GLB/0.5 compiles actual .ok surfaces and retains all GLB/0.4 identity, geometry, PBR, placement and impulse requirements. It adds a complete after-side force projection for every object at every retained boundary, including empty projections. Record supported COM force assumptions explicitly. It is recorded pose animation, not live destination force simulation.

Preserve exact activation and completion boundaries that lie in the recording interval. A force extending beyond the recording stays active in the final metadata. Reject float32 timestamp collapse or unrepresentable geometry/transforms under the inherited delivery limits. Use a conservative position-error bound for every piecewise constant-acceleration segment: ideal linear chord error is at most `norm(acceleration) * h^2 / 8`. Account separately for float32 storage and inherited declared position tolerance; the ideal bound alone does not certify encoded output. Preserve conservative impulse/angular sampling. Check source boundary metadata and independently decoded intermediate poses, not only exporter-produced reference samples. Charge force history in both planning and byte validation.

Independent Khronos, Three.js and browser checks must inspect the same source-built artifacts and record their exact identities. An image alone cannot establish acceleration, event ordering or source repair. A numerical result alone cannot establish usable rendered geometry.

## 9. Predetermined acceptance gates

| Gate | Required evidence |
| --- | --- |
| F01 | Native parsing, contextual spelling, typed world-force operands, stable keys, actual occurrence resolution and supported pinned imports |
| F02 | Single COM interval: independent acceleration, position, velocity, momentum and work/energy checks |
| F03 | Additive overlap, exact cancellation and canonical final-set aggregation independent of declaration order |
| F04 | Automatic completion, replacement, zero force and unchanged-anchor cases |
| F05 | Gravity, off-center impulses, release at action completion and ordered admission/rollback |
| F06 | Zero/duration boundaries, nondecimal canonical clocks, exact rational endpoint addition and beyond-horizon completion |
| F07 | Positive/negative physical, type, frame, numeric, interior-extremum and prefix-validity cases |
| F08 | Generated composition and scoped mass/force/duration repair with unchanged siblings, visuals and library bytes |
| F09 | Actual Agent/0.5 authoring, inspection, retries, stale revisions, cancellation and store isolation |
| F10 | Nested history/work limits, cancellation, boundary planning and export/byte-reader budget parity |
| F11 | Actual source-to-GLB/0.5 geometry/PBR/motion, independent intermediate-pose checks and reviewed browser captures |
| F12 | Current inherited core, Agent, construction, surface and impulse release gates, every existing regression identity and exact-implementation CI |

The fixture corpus must distinguish predetermined expectations, authoring/audit results and measured execution results. Adopted numerical limits cannot be silently widened. This profile does not implement continuous torque, time-varying fields, drag, contacts/collisions, compound or nonspherical rigid dynamics, dynamic mechanisms, controllers or live engine behavior. These and every other remaining GOAL requirement remain open.
