# C089 decision: proceed with Cartesian fixed-axis torque specification

**Decision identity:** `C089-TORQUE-REVIEW/1`  
**Date:** 2026-11-02  
**State:** reviewed engineering recommendation; no language adoption or runtime support

## Decision and purpose

Proceed to a complete versioned contract and an independently authored input freeze for finite torque on a free homogeneous spherical carrier. Use a persistent named positive world X, Y or Z axis and signed scalar torque and angular speed for the first domain. This provides a useful physical input for spin-up, braking and reversal while keeping the orientation law analytically tractable.

The C088 proposal requested a utility and contract review before runtime work. This record completes that review with a selected direction and concrete numerical witnesses. It does not promote a proposal into an implemented profile. C090 should write and freeze the specified contract artifacts, without repeating the utility review. [The independent utility review](utility-review.md) and [mathematical review](math/MATH-REVIEW-02.md) support this decision.

## The representative modeling and Agent task

Use two independent occurrences of one pinned component library. Each has one free homogeneous spherical body and an asymmetric massless visual marker assembly. The carrier alone supplies mass and inertia. An Agent repairs the magnitude or duration of a finite external couple on one occurrence, then inspects angular state and recorded motion. The sibling, source library, geometry, materials, images and unrelated translation must retain their predetermined invariants. Include acceleration, braking through zero, reversal, an invalid edit and its successful repair.

This is an external rotational input on a free body. It does not establish a physical motor attached to a housing, an equal reaction body, a wheel-ground contact, a joint or a compound body's inertia. Those are separate product requirements. The marker is necessary because a uniformly colored sphere can rotate without a visible change.

The existing alternatives have different meanings. An impulse changes angular momentum at one clock. A center-of-mass force changes translation. An authored visual rotation prescribes motion. A train of impulses introduces a discretization choice rather than a continuous constant-torque interval. These distinctions justify the proposed source operation qualitatively; they do not establish a measured authoring benefit. The full GOAL still requires a direct-tool comparison with unseen variants, repair effort, cost and quality.

## Selected design recommendations

| Concern | Recommended first-contract decision | Reason |
| --- | --- | --- |
| Body | Actually free homogeneous spherical carrier with existing positive canonical mass, radius and inertia admission | Reuses an established finite physical model |
| Axis | Positive named world X, Y or Z; one persistent selection per torque-enabled free epoch | Gives exact zero orthogonal components and avoids tolerance-based axis admission |
| Direction | Signed scalar torque and speed | Handles braking and reversal without changing the axis |
| Axis lifetime | First committed torque activation latches the axis, including zero torque; retain it until reset or accepted revision replacement | Prevents an empty active set or a zero crossing from silently changing the rotational domain |
| Active inputs | Every interval must name the latched axis, including cancelling intervals | A collinear net input cannot hide unsupported individual inputs |
| Incoming spin | Require exactly zero canonical components orthogonal to the selected Cartesian axis at first activation | Avoids silently projecting or changing incoming angular momentum |
| Later impulses | Check each staged impulse's intermediate angular result against the latched axis | A later cancelling impulse cannot hide an out-of-domain intermediate state |
| Torque units | Existing Torque dimension, N·m; operation-specific mechanical conversion to radians per second squared | Preserves the source language's distinct Angle dimension |
| Inertia | Use the inherited canonical own-sphere inertia derived from 2mr²/5 | Avoids changing the physical model through a new recomputation path |
| Clocks | Existing exact canonical-source seconds, rational start-plus-duration completion, and half-open intervals | Retains exact boundaries and before/after meaning |
| Aggregation | Exact rational sum of canonical signed torques, one canonical net rounding, canonical acceleration from that net and inherited inertia | Makes overlap and cancellation order independent within the final active set |
| State | Signed speed and phase refer to an identified rotational anchor; sample requests do not become new motion anchors | Keeps continued and segmented requests comparable |
| Pure torque | Preserve the inherited translational path and its canonical rounding | Torque adds no linear force |
| Transactions | Stage all completions and written-order source events; validate and publish the whole boundary atomically | A later failure must retain the last accepted prefix |
| Recorded motion | Add an angular-acceleration interpolation bound and retain angular-travel protection | Endpoint agreement alone can erase a reversal |

These decisions constrain the next contract. Exact syntax, canonical phase conversion/range reduction, binding identifiers, closed schemas, refusal precedence and charge counts require reviewed specification bytes before adoption. They are not selected by this table. In particular, no `.22` runtime catalog entry is created by this review.

## What the independent calculations establish

The review uses exact rational arithmetic and explicit binary64 rounding examples. These are mathematical design checks, not tests of an implemented torque feature and not a frozen release corpus.

**Arbitrary axes need more than exact cross-product admission.** The canonical vector `(0.6, 0.8, 0)` and its independently rounded componentwise triple have a nonzero exact rational cross product. A trajectory intended to remain on one axis can therefore leave an exact collinearity predicate after rounding. A general-axis extension would need an authoritative axis/scalar representation and a state-preserving ingress rule. The Cartesian restriction avoids this particular closure failure.

**Extra anchors can change otherwise identical translation.** With position 1 m, velocity 2^-52 m/s, no acceleration, a split at 1/2 s and an endpoint at 1 s, direct evaluation produces the next binary64 value above 1. An unnecessary midpoint anchor rounds a half-ULP increment to 1; the next half-ULP rounds to 1 again. All these inputs and clocks are exactly representable. The one-ULP difference is a concrete reason to preserve translational anchors at pure torque boundaries, not a general accuracy claim about current OntoKin.

**Equal endpoint orientations do not imply no motion.** For initial signed speed -1 rad/s, angular acceleration 2 rad/s² and duration 1 s, phase is -t+t². Both endpoint phases are zero, but the midpoint is -1/4 radian. A recording that keeps only the endpoints loses the interior reversal.

For constant acceleration over a key gap h, subtracting the chord of the quadratic phase gives error alpha*t*(t-h)/2. Its maximum magnitude is |alpha|h²/8 at the midpoint. This proves the ideal fixed-axis short-arc interpolation term. It does not by itself cover quaternion error, clock quantization, descendant position tracks, composed rotations or a named destination's interpolation implementation. Those require their own reviewed terms and actual delivery checks.

## Numerical and lifecycle obligations for adoption

The next contract must distinguish ideal physical equations from canonical runtime values. Exact energy/work identities in the mathematical witness set are ideal reference results; rounded runtime states need predetermined error treatment. Do not select an error tolerance from candidate output.

Keep every old profile unchanged. In the proposed profile, preserve the inherited kinematic route for each carrier until its first committed nonzero canonical angular acceleration. Neutral torque events can update the persistent axis restriction and source history without switching its motion representation. At the first committed boundary whose final canonical angular acceleration is nonzero, initialize separate rotation state from the ordered staged angular state while leaving the inherited translational anchor untouched. Keep that split rotation route thereafter, including zero-acceleration intervals. Carry the current reach error and state-transfer metadata; public pose fields alone are insufficient.

The [independent addendum](utility-review-addendum-01.md) defines six comparison classes. Unchanged predecessor inputs retain exact full-stream comparisons. Changed source/profile/history uses predetermined physical-field, geometry/material/image and permitted metadata/sampling comparisons. The transition may be caused by an activation, a completion that removes one member of a cancelling pair, or another adopted boundary change; it is not limited to a newly started interval. A zero torque may preserve motion while changing the validity of a later off-axis impulse. Do not turn that semantic difference into a false claim of identical whole-program behavior.

A velocity zero crossing may have a nonterminating rational clock even when source clocks are canonical dyadic values. Do not require it to become a public source-time boundary unless the publication format can represent it. A conservative endpoint-speed travel bound and the acceleration error term can cover a reversal without exposing that derived clock.

The actual `.21` delivery path uses the reach recorder and independent reach reader. It exports flat root nodes with baked world poses. An offset marker therefore has a separate translation track. For a rigid offset radius rho, its acceleration can be bounded by A_COM + rho*(Alpha + Omega²), including tangential and centripetal terms. Its ideal translation chord error is bounded by that quantity times h²/8. Orientation accuracy alone does not establish this position bound.

Retain the current flat output and radius-aware certification architecture. The existing `PhaseBound` recurrence already carries angular acceleration and offset terms, but current dynamic-sphere bounds assume constant spin and the recording `MotionBound`/certificate path omits the torque acceleration contribution. The next contract must extend that actual source-bound proof and its independent supplied-byte reconstruction. Updating only `force_export.py` would miss the current path. Start with fixed rigid marker descendants; independently articulated compositions require their complete derivative/error proof or an explicit new-profile refusal. The [addendum and offset-marker witness](utility-review-addendum-01.md) record the exact source findings and comparison requirements.

Freeze final boundary admission, source spans, exact diagnostic ordering, complete history/provenance, current host and reducing caller authority, original deadline/cancellation callbacks, store recovery, failed-edit rollback, interrupted artifact publication and exact chunk/EOF behavior. Keep all inherited fixtures, budgets, tolerances and failed gates at their original meanings.

## Completion boundary and next action

C089 completes the utility and design-risk review. It selects the first useful domain and supplies independently executable witnesses for the contract risks. It introduces no production behavior. The next actionable unit is [C090 contract and independent input freeze](NEXT-TASK.md), followed by implementation only after reviewed adoption is published and read back.
