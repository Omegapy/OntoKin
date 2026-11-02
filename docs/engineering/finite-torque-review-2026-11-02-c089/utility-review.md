# C089 independent utility and physical-contract review

Date: 2026-11-02  
Reviewer role: independent utility and mechanics review  
Inspected source: `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`  
Disposition: **Useful bounded capability; proceed to a complete reviewed contract and independent input freeze. This review does not adopt a source profile or authorize runtime implementation by itself.**

## 1. Product decision

A finite external torque is worth specifying. It gives an agent a direct, physically meaningful way to request spin-up, braking and reversal over a duration. The existing impulse input changes angular velocity instantaneously. The existing COM force input changes translation without adding torque. Authored visual rotation can show movement but does not establish the angular momentum or work of an applied couple. A succession of impulses can approximate finite torque, but its timing and accuracy would depend on the chosen subdivision and could increase authored events and validation work. None of those alternatives supplies the same source-level physical input. These distinctions follow the current [impulse contract, sections 4 and 7][impulse], [force contract, sections 1 and 4][force], and the actual force trajectory in [`ForceSimulator._dynamic_kinematics`][force-runtime].

The representative task should use two occurrences of one pinned component definition. Each occurrence owns one homogeneous spherical physical carrier and an asymmetric, visibly readable massless marker assembly. The marker may use `no_body` descendants; it must not silently change the carrier inertia or create a compound body. Use different colors or an offset marker so orientation is visible without relying on a symmetric sphere. Apply torque to one occurrence, repair its magnitude or duration through a source patch, and verify unchanged sibling state, geometry, materials, images and library bytes. Include invalid repair, rejection and successful repair in the same documented Agent workflow.

The finite scope is useful as a rotational-physics and source-repair building block. It does not establish a wheel, constrained motor, reaction body, contact force, friction, suspension, propulsion, general rigid body or live engine simulation. A nominal visual flywheel on a free spherical carrier must be described as such. No measured authoring advantage follows from this qualitative utility decision; that still needs a direct-tool baseline, unseen variants, repair effort and cost/quality evidence.

## 2. Recommended smallest coherent axis scope

The first profile should explicitly select **one persistent world Cartesian axis per torque-enabled carrier**, with signed scalar torque and signed angular speed. The allowed axes are the positive world X, Y or Z basis directions; negative torque and negative speed express reversal. This narrower fixed-axis subset is sufficient for the representative spin-up/braking task and is closed under the existing binary64 component representation. It should be named accurately in source capability discovery and diagnostics.

An arbitrary world axis is a reasonable later extension, but it needs an additional authoritative axis/scalar representation and a reviewed ingress/projection rule. Normalizing a vector and then testing exact collinearity on independently rounded public components does not solve that problem. A simple independent arithmetic example shows why:

- Canonical axis components: `(0.6, 0.8, 0)`.
- Componentwise binary64 multiplication by three: `(1.7999999999999998, 2.4000000000000004, 0)`.
- The exact rational Z component of their cross product is `1 / 4503599627370496`, which is nonzero.

This is a review calculation using Python 3.12.14 `Fraction`, not an OntoKin runtime test. It demonstrates that intended collinearity is not preserved by an exact predicate over these rounded outputs. A new tolerance chosen after observing candidate results would also be unacceptable. If general axes are a required first-profile use case, stop at the contract review until the representation, allowed input domain and state-preserving conversion are specified independently.

For the Cartesian subset, keep the axis through zero torque, zero speed, complete cancellation and reversal. Do not infer a new axis from the current sign of angular velocity. Each active torque input must use the carrier's selected axis, including inputs whose final vector sum would cancel. Accepting only a collinear net vector would hide unsupported individual inputs and allow admission to change when one interval expires. A source-level axis choice is an exact restriction, not a numerical near-collinearity test.

Require initial or released angular velocity to have exactly zero components orthogonal to the selected axis at the first torque activation. Recommend a sticky axis lock beginning at the first successfully committed torque activation, including a zero-torque activation, and lasting until run reset or revision replacement. Completing the last interval does not unlock it. Later torque statements use that same axis, and any later impulse whose intermediate resulting angular velocity has a nonzero orthogonal component is refused. Before the first torque activation, inherited impulse behavior remains unchanged. This explicit restriction avoids an implicit axis-change mechanism and remains confined to the new profile. A future arbitrary-axis or unlock feature needs its own versioned decision.

## 3. Units, clocks and canonical state

Use the existing finite positive canonical sphere mass, radius and inertia domain. The stored sphere inertia is the canonical form of `I = 2 m r² / 5`; a new operation must not replace it with a different ideal or recomputed value. The source torque quantity has dimension `N*m`. The mechanical kernel interprets the numeric ratio `tau / I` as radians per second squared, as the impulse kernel already interprets angular impulse divided by inertia as radians per second. This is an operation-specific mechanical conversion. Generic source arithmetic must retain the distinct Angle dimension established in [`values.py`][values] and [OK-LANG-004 section 4][impulse].

Recommended aggregation and trajectory policy for the Cartesian signed-scalar scope:

1. Sum exact rational representations of all canonical active signed torques, then round once to expose a finite canonical net torque.
2. Divide that canonical net torque by canonical positive inertia, then round once to expose finite canonical angular acceleration.
3. Between actual acceleration-changing or angular-impulse boundaries, compute signed speed as one exact rational affine expression over canonical anchor values, then round its exposed value once.
4. Compute signed phase from the anchor as `omega0*dt + alpha*dt²/2` using exact rational intermediate arithmetic. Feed the inherited reviewed rotation machinery through an explicitly bounded angle-conversion rule. Do not accumulate one rounded angle per requested sample.
5. Preserve the rotation anchor when the final canonical acceleration is unchanged. Zero torque, cancelling overlap and same-net replacement still update identity/history without changing motion.

The complete contract must specify finite phase/range reduction behavior and numerical error, not merely the mathematical equation. A finite source time and finite angular acceleration can generate an unrepresentable intermediate if implemented with unchecked floats. Inherited operand-bit, work, output and cancellation limits still apply. A valid short prefix must not fail because of an unrequested later interval. Axis, torque, signed speed and phase are separate concepts; projecting a world angular-velocity vector for inspection must not replace the authoritative signed scalar state.

Reuse the existing force clock semantics: activation and duration are exact rationals of canonical binary64 source seconds; completion is their exact rational sum; the active interval is `[start, end)`. Preserve before/after sides, exact coincident clocks, beyond-horizon completion and whole-boundary rollback. Do not add an epsilon or make execution deadlines into animation times. These rules already have concrete definitions in [OK-LANG-005 sections 3, 5 and 6][force].

## 4. Translation and event integration

Separate translation and rotational anchors in the new profile. In the current implementation, `_DynamicInitial` holds a complete kinematic state, and [`ForceSimulator._aggregate`][force-runtime] reanchors the complete state when linear acceleration changes. Merely reusing that operation at a torque boundary could change subsequent translation through an extra canonical rounding, even though pure torque contributes no linear force.

The required invariant is stronger than approximate physical agreement: a torque-only event must preserve the inherited translational path and canonical rounding. A no-torque program and its torque-only variant should produce the same position, linear velocity and relevant source-independent translation fields at all frozen inspection times, under gravity, active COM force, zero force, cancelling overlap and replacement. Conversely, an unrelated COM-force boundary must not create an extra rotation-anchor rounding when angular acceleration is unchanged.

The rounding risk has a small exact example. Let position be `1`, velocity be `2^-52`, and acceleration be zero. Direct evaluation at `t=1` gives the next binary64 number above one (`0x1.0000000000001p+0`). Reanchoring at `t=1/2` rounds the midpoint to one; advancing from that rounded anchor for another half second rounds to one again (`0x1.0000000000000p+0`). The resulting one-ULP difference arises solely from the extra anchor. This independent `Fraction`/binary64 calculation is retained in `review-calculations.json`; it is not a measured candidate defect.

A proposed transaction must establish the incoming state once, stage natural completions, stage torque/force completions, execute source statements in written order, aggregate the final active influence sets, validate the whole boundary and commit only after complete work/output admission. The contract must decide when the fixed-axis condition is checked. The most defensible restriction is to validate every inherited impulse's intermediate angular result against a currently active axis, not allow an unsupported out-of-axis impulse to be hidden by a later cancellation. Releases must keep the inherited saved incoming derivatives and can qualify a carrier only after an earlier successful release in the same sequence.

Before implementation, freeze the exact refusal precedence and source spans for: unsupported frame, non-sphere target, nonfree motion, off-axis initial/released spin, off-axis torque, axis-changing impulse, invalid duration, nonfinite exposed net torque/acceleration and bounded-work failure. A failed final statement or final aggregation must roll back starts, completions, records, counts, anchors and artifacts together. The old profiles keep their existing accepted impulse behavior; a new explicit profile must disclose its additional rotational domain.

## 5. Recording must handle acceleration and reversal

[`force_export._motion_bounds`][force-export] states that all primitive angular contributions are constant on each true-boundary interval. [`force_interval_violation`][force-export] checks linear-acceleration chord error and angular travel, but has no angular-acceleration interpolation term. Torque cannot simply reuse that proof. Preserve the existing sampling/resource policies in [OK-ENG-007][recording] and add an independent angular-acceleration bound.

For a single fixed axis with constant angular acceleration over a key gap of width `h`, ideal short-arc spherical linear interpolation has angle error at most `abs(alpha) * h² / 8`. This follows directly by subtracting the line connecting the quadratic phase's endpoint values: the error is `alpha * t * (t-h) / 2`, whose greatest magnitude occurs at `h/2`. It is an ideal analytic term only. Canonical source state, quaternion normalization/sign, binary32 clocks and components, quantized boundary displacement and the actual destination interpolation must be treated separately. The angular-travel bound remains necessary to avoid short-arc aliasing.

Use an independent reversal control with `omega0 = -1 rad/s`, `alpha = 2 rad/s²`, and duration `1 s`. The exact signed phase relative to its starting orientation is `theta(t) = -t + t²`:

| Time (s) | Signed speed (rad/s) | Signed phase (rad) |
| --- | --- | --- |
| 0 | -1 | 0 |
| 1/4 | -1/2 | -3/16 |
| 1/2 | 0 | -1/4 |
| 3/4 | 1/2 | -3/16 |
| 1 | 1 | 0 |

The endpoint orientations are equal, while the carrier moves one quarter radian away at the midpoint. An endpoint-only or net-angle recording would erase real motion. These numbers are independently derived review controls; they are not adopted expected files and no candidate has been measured against them.

On an affine-speed interval, `max(abs(omega(start)), abs(omega(end)))` bounds speed, and its product with gap width conservatively bounds travel even through reversal. Split at all exact physical event boundaries; inserting the zero crossing as a sampling landmark can aid diagnosis but is not a substitute for the acceleration error bound. Test both source and stored-clock intervals, preserve actual complete-stream checks, and require native/browser playback evidence of the identified artifacts.

## 6. Required independent freeze and integration evidence

The future freeze must include numerical cases for several masses/radii, both signs, zero/nonzero initial spin, acceleration, braking, reversal, overlap, cancellation, adjacent intervals, same-net replacement, simultaneous completion/release/impulse, exact nondecimal clocks, continued prefixes and equivalent segmented requests. It must check rotational work/energy where applicable and distinguish canonical expectations from ideal physical values.

Freeze the actual source and pinned component closure; all hashes and UTF-8 repair spans; sibling and translation invariants; closed source/state/Agent/GLB schemas; diagnostics and refusal precedence; exact staged charges and caller/host authority; cancellation and callback exception identity; stale/retried edits; reopened stores; interrupted publication; chunk retrieval/EOF; and complete source-to-state provenance. A count of generated fixtures is not enough. Each has to test a requirement under independently authored expectations.

Before runtime work, publish and read back the reviewed contract and exact independent input freeze, and preflight unchanged C088 controls on the identified C088 source. After runtime work, the source/Agent/recording readers must be independently executable and must reject actual supplied corruptions while accepting their original controls. Re-run the applicable inherited roles and actual named destination checks without changing their original gates. Preserve Original28's current 24/28 overall-failed disposition, the external attestations, interpreter-coverage limits and all other retained obligations.

## 7. Decision boundary for this review

**Proceed with the specification work for finite torque, using the explicit Cartesian fixed-axis signed-scalar subset as the recommended first contract.** A broader arbitrary-axis profile is not justified by the present representation alone. This is a scope and implementation-risk judgment, not a claim that the larger scope is impossible.

A complete adoption must produce these concrete artifacts next:

| Adoption artifact | Required content |
| --- | --- |
| Versioned language contract and additive grammar | Exact statement spelling, Cartesian axis and sticky-lock rules, signed scalar torque, compatible pinned-import matrix and explicit profile selection |
| Numerical and transaction appendix | Canonical inertia/net torque/acceleration/speed/phase rules; exact clocks; separate anchors; stage order; failure precedence; bounded phase reduction; inherited limits |
| Source, Agent and recorded-delivery bindings | Exact version identifiers, catalog availability, closed projections and diagnostic rules, separate store identity, source-span repair authority, provenance and current request authority |
| Recording proof and delivery specification | Angular-acceleration error allocation, travel bound, quaternion and clock quantization treatment, encoded probes, independently rebuilt plan and actual destination evidence requirements |
| Independently authored frozen corpus | Exact source closures, analytic expected values, refusals, repair spans, unchanged sibling/translation controls, resource/cancellation/store/transport cases and all hashes/modes |
| Predecessor preflight and adoption/readback receipt | Exact C088 source and untouched controls; actual preflight outcomes; independent review dispositions; published contract/input identities verified before runtime work |

This review intentionally provides no executable-looking proposed syntax and does not reserve `.22`, change catalog availability, create fixtures that purport to be frozen, or certify implementation. The next work is to write and freeze these specified artifacts, not to repeat the utility decision. Once they are reviewed and frozen, the finite runtime can be implemented under its explicit binding. The full product mission remains unchanged.

[impulse]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md
[force]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md
[force-runtime]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/force_runtime.py
[force-export]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/force_export.py
[values]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/values.py
[recording]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/docs/engineering/OK-ENG-007-native-force-glb-export.md
