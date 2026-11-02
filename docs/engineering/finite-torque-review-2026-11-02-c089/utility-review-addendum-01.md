# C089 review addendum: legacy anchors and offset-marker delivery

Date: 2026-11-02  
Source: `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`  
Status: independent review correction and concrete next-contract decisions; no adoption or runtime change

This addendum preserves [the original review](utility-review.md). It qualifies the original recommendation about COM-force boundaries and extends the recording requirements for offset descendants. Where those descriptions differ, this addendum supplies the more precise recommendation.

## 1. Preserve legacy dynamics before a real torque changes rotation

The existing force-only implementation deliberately reanchors a **complete** `_DynamicInitial` when canonical linear acceleration changes. `ForceSimulator._aggregate` calls `_dynamic_kinematics` and replaces that complete anchor. The current `.21` dynamics use `ReachSimulator`, whose `_aggregate` calls that inherited method and additionally maintains numeric error/transfer state. `ReachSimulator._dynamic_kinematics` still reads translation and constant angular velocity from the same anchor. Consequently, splitting all anchors unconditionally could change the canonical orientation of a force-only control even without an applied torque. [Source: `force_runtime.py`, `_aggregate`; `reach_runtime.py`, `_aggregate` and `_dynamic_kinematics`.][force-runtime] [Current reach implementation.][reach-runtime]

**Recommended route:** Keep every existing profile on its exact existing path. Within the new profile, keep a carrier on the inherited kinematic path until its first successfully committed **nonzero canonical angular acceleration**. A zero-torque activation, cancellation whose final canonical net is zero, or same-net neutral replacement updates axis lock and history without entering split rotational dynamics. A nonzero canonical torque whose canonical acceleration rounds to zero also stays on the inherited path if that underflow is admitted by the final numerical contract. A new axis lock is an admission/provenance property, not a reason to recalculate an unchanged trajectory.

At the first nonzero activation, initialize the separate rotation state from the correctly ordered, current staged angular pose and speed. Leave the translational anchor and its inherited rounding path untouched. From then on, COM-force-only boundaries may update the translation anchor but must not introduce extra rotation-anchor rounding. Keep this split rotation route through later zero-acceleration intervals until reset or revision replacement; switching back would introduce another state-conversion and rounding rule with no demonstrated benefit. Any angular impulse still follows its explicitly adopted ordered state transfer. The new contract must carry the existing numerical-error state and provenance along each route; copying only public position/quaternion values is insufficient.

This recommendation distinguishes axis admission from physical integration. A zero torque can lock an axis and therefore make a later off-axis impulse invalid under the new profile, even though it causes no physical acceleration. Neutral-motion comparisons only apply to inputs that satisfy those explicit admission rules; they cannot promise identical acceptance of all future inputs.

### Comparison classes to freeze

| Class | Required comparison |
| --- | --- |
| Unchanged predecessor input under its original source/Agent/GLB binding | Preserve the existing complete controls, exact streams and outcomes at their original limits. No new profile metadata or changed source is introduced. |
| Same accepted program and binding, repeated or resumed requests | Preserve the binding's existing determinism, prefix/state and artifact rules, including current authority and cancellation checks. |
| New profile, no torque ever active; or only zero canonical torque-acceleration intervals before the first nonzero one | Use the inherited kinematic route. Compare frozen physical fields at exact common clocks; permit only enumerated binding/source/provenance/torque-history differences. Explicit axis-domain refusals remain separate expected outcomes. |
| Torque-only variant versus its torque-free translational control | Require equal carrier COM position, linear velocity and relevant translational anchor fields at the frozen clocks, with identical forces, releases and linear impulse inputs. Do not require equal angular fields. Offset visual descendants naturally change world positions when their carrier rotates. |
| Equivalent nonzero torque schedules, including cancellation or same-net replacement within an established split-rotation route | Compare angular/linear trajectories and numerical-error obligations under the adopted canonical event rules. Preserve changed identities, counts, times and active/recent records rather than erasing them to obtain equality. |
| Different source, profile or torque history exported to GLB | Do not require whole-file byte identity. Freeze the exact allowed metadata/provenance differences, unchanged geometry/material/image streams, and pose comparisons on common exact clocks. Extra semantic boundaries may change the sampling clock and accessor lengths. |

The last distinction matters: a different source revision or a new profile cannot have an identical source-bound GLB. Likewise, the motion array of an export with additional mandatory event times need not have the same bytes or length as its control. Whole-artifact equality remains appropriate for the unchanged predecessor streams; scoped comparisons must be explicit elsewhere. This is a comparison rule, not permission to weaken a physical or numerical tolerance.

## 2. Offset descendants need a translation bound

The exporter does **not** preserve a glTF parent-child transform hierarchy for these carriers. `scene._build_scene` samples each node's semantic frame and stores its world position/orientation. `gltf.decode_glb` requires every node to be a root and rejects `children`; metadata declares `all_nodes_are_roots_with_baked_world_poses`. Translation channels interpolate linearly independently of rotation. A rigidly following marker's offset origin therefore follows a curved world path that must be bounded as a translation track. [Scene construction.][scene] [GLB construction and reader.][gltf]

For a fixed rigid offset `r(t) = R(t) r0` from a carrier COM `c(t)`,

`p(t) = c(t) + r(t)`

`p''(t) = c''(t) + alpha(t) × r(t) + omega(t) × (omega(t) × r(t))`.

For the proposed fixed-axis interval, let `A` bound carrier COM acceleration, `Omega` bound absolute angular speed across the whole interval, `Alpha` bound absolute angular acceleration, and `rho` bound the offset radius. Then the conservative origin-acceleration bound is

`A_marker <= A + rho * (Alpha + Omega²)`.

The ideal linear-interpolation chord error is at most `A_marker * h² / 8`. Use the complete fixed-transform path to obtain the radius; ownership alone is not a rigid-follow relationship. Fixed descendant chains can use a conservatively composed radius. Independently moving descendants require the full additional local acceleration and Coriolis terms, or must be explicitly outside this first torque-delivery scope. The contract must cover every delivered carrier/helper it accepts rather than infer correctness from the root sphere alone.

The angular bound `Alpha*h²/8` is therefore **not sufficient on its own** for an offset marker, even if it meets the rotation tolerance and angular-travel limit. For an analytic example, use a stationary root, a marker at radius `100 m`, `alpha = 1/512 rad/s²`, `omega0 = -1/1024 rad/s`, and a one-second interval. Endpoint orientations and marker positions agree. The midpoint phase is `-1/4096 rad`, about `0.00024414 rad`, within one quarter of a `0.001 rad` rotation tolerance. The marker midpoint moves about `0.024414 m`, exceeding a `0.001 m` position tolerance. The radius-aware acceleration bound gives chord allowance `51225/2097152 m`, about `0.024426 m`. The exact inputs and calculation are in [offset-marker-calculation.json](offset-marker-calculation.json).

This demonstrates insufficient planning, not a claim that the old reader falsely accepts the example: existing finite intermediate-pose checks could reject an inadequate exported stream. A new contract should plan sufficient keys before allocation and independently verify the adopted complete bound, rather than depend on an accidental probe to discover the omission.

For geometry baked into a single carrier's local mesh, the carrier origin does not have this offset trajectory. However, a promised world-space vertex/site position guarantee still needs the carrier's orientation error multiplied by the local landmark radius, in addition to translation, vertex and timing errors. A local geometry tolerance alone does not establish world-space landmark accuracy.

## 3. Extend the actual `.21` recording path

The original review referenced `force_export.py` as the inherited force recorder. That file correctly demonstrates the missing constant-spin assumption, but it is **not the complete current `.21` delivery path**. `scene.REACH_TARGETS` includes `.21`; `scene.build_scene` routes it to `reach_export.build_reach_scene`; `gltf.validate_export` routes it to the independent reach conformance reader. [Routing and target sets.][scene] [Reader dispatch.][gltf]

The current path already contains useful machinery:

- `reach_phase.PhaseBound` has angular-speed and angular-acceleration bounds. Its composition recurrence includes `(parent_alpha + parent_omega²) * offset`, local acceleration and Coriolis terms. This can support offset descendants once torque-aware source bounds and numerical errors are supplied. The current `dynamic()` construction assumes constant angular velocity and leaves its angular-acceleration field at zero. [Phase bounds.][phase]
- `reach_export.node_geometry_bounds` includes actual local vertex/site radii. `reach_timeline` and the interval certificates combine per-frame acceleration, angular travel, endpoint errors and radius-scaled rotation. Those existing certificates must be extended under the new binding; they must not be replaced by the narrower `.5` planner. [Recording implementation.][reach-export]
- The current `MotionBound` stores speed, acceleration and angular speed, but not angular acceleration. `complete_interval_bounds` uses an angular source-chord term proportional to `Omega²*h²`. Torque requires a separately derived acceleration term and its presence in the producer, serialized proof schema and independent supplied-byte reconstruction. An ideal fixed-axis phase proof supplies `Alpha*h²/8`; a quaternion-chord proof may instead use the independent derivative bound `||q''|| <= Alpha/2 + Omega²/4`, with a corresponding source chord term `Alpha*h²/16 + Omega²*h²/32`. These are alternative proof ingredients, not interchangeable adopted final tolerance allocations. [Motion bound and certificate formulas.][reach-export]

**Recommended delivery scope:** Retain flat world-pose output, the current radius-aware certification architecture and fixed rigid marker descendants. Extend torque-aware dynamic phase/error bounds and independent reconstruction, propagate angular acceleration through every accepted frame path, and update the interpolation/certificate contract explicitly. Do not introduce a new glTF hierarchy as an unreviewed shortcut. If independently articulated marker descendants are not covered, reject that composition explicitly in the first profile while preserving earlier bindings.

## 4. Effect on the next adoption stage

The utility decision remains **GO**. The next contract/freeze must now include (a) the legacy-versus-split per-carrier route and transition; (b) the six comparison classes above; (c) neutral controls with COM-force changes and preexisting spin; (d) offset and nested fixed markers, with several radii and reversal; and (e) the new angular-acceleration/landmark certificate inputs and independent reconstruction. These are concrete additions to the already listed adoption artifacts, not a reason to repeat the utility review or begin runtime work prematurely.

Eight additional exact source snapshots are retained under `baseline-addendum/`, with their SHA-256 and verified native Git blob hashes in its `SOURCE-SNAPSHOT-RECEIPT.json`. No original review, baseline source, old test, runtime or remote repository file was modified by this addendum.

[force-runtime]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/force_runtime.py
[reach-runtime]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/reach_runtime.py
[scene]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/scene.py
[gltf]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/gltf.py
[phase]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/reach_phase.py
[reach-export]: https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/reach_export.py
