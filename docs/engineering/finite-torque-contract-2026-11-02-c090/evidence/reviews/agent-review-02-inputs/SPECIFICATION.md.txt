# Finite Cartesian torque — source and numerical contract

**Identity:** `OK-LANG-022/0.1.0`  
**Preparation state:** review draft; adoption is a separate hash-bound decision  
**Source basis:** C089 `655097f016af17434b9b26fae22491f5f302aa18`; unchanged runtime from C088 `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`  
**Date:** November 2, 2026 (America/Denver)

## 1. Explicit scope and bindings

This finite extension represents a constant external couple about a named positive Cartesian world axis acting on an actually free homogeneous spherical body. Its scalar sign determines direction. It supports acceleration, braking, reversal, overlapping intervals, unchanged center-of-mass translation, and asymmetric massless visual markers. It does not represent a constrained motor, reaction housing, compound inertia, general rigid body, contact, collision or live engine physics. C089's utility decision is complete; this contract supplies its missing implementation inputs.

| Binding | Explicit value |
| --- | --- |
| Source version and profile | `0.22` / `torque-0.1` |
| Agent | `ontokin.agent/0.22` |
| Recorded output | `ontokin.glb/0.22` |
| Durable store filename | `torque-program-agent.sqlite3` |
| Durable store identity | `ontokin.torque-program-agent-store/0.1` |
| Immutable transports | Existing `ontokin.bundle/0.2` and `ontokin.files/0.2` |
| Diagnostic envelope | Existing `ontokin.diagnostic/0.2` |

The new source profile inherits every .21 construction, surface, texture, keyed operation, impulse, force, reach and budget meaning. It introduces torque only through the explicit new statement. Defaults remain CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1. Earlier source, Agent, output and store bindings do not acquire torque or its restrictions. The declaring source unit owns its language rules; a .22 entry may import an explicitly enumerated existing definition-module version .2 through .21 or .22 with its matching adopted profile. Older importers reject .22. Existing edges and old contextual identifiers are preserved. No numeric-version ordering is an admission algorithm.

Torque is allowed only in the entry scene's existing event sequence. It is not an ordinary function, component initializer, user-function body, callback, generated loop, library-side scene or mutable host command. Imported components and keyed generated occurrence targets remain supported through their existing source-owned occurrence paths. Definition modules may supply pure scalar Torque and Time computations, preserving their declaring version's arithmetic. The existing Torque dimension is `kg*m^2/s^2`; generic division by Inertia still produces inverse Time squared, not AngularAcceleration. Only this physical operation interprets its mechanical quotient in radians per second squared. Angle remains a distinct language dimension.

## 2. Additive grammar and source identity

```ontokin
ontokin "0.22";
module TorqueDemo @ "torque-demo";
profile "torque-0.1";
// Inside an existing scene with a free homogeneous sphere named ball
at 0[s] sequence {
    torque ball @ "spin" about world_z using 2[N*m] for 1[s];
}
```

The complete additive production is in [ontokin-torque.ebnf](ontokin-torque.ebnf). `torque` is contextual only at a sequence-statement start in a .22 declaring unit. `about`, `using`, `for` and the axis identifiers receive their torque-specific interpretation only in that production. The inherited reserved status and existing uses of `using` and `for` are unchanged; this extension does not make them ordinary identifiers. No globally reserved ordinary variable or function name is added. The target has the inherited object occurrence path syntax, including literal keyed selection; `@` and its stable key are mandatory. The axis slot parses one identifier and admits exactly `world_x`, `world_y` or `world_z`. These denote positive unit world X/Y/Z, never a body axis, a mutable frame or a vector expression. A different identifier receives the axis diagnostic; an expression in that slot is an ordinary syntax refusal.

Torque and duration are ordinary pure elaboration expressions. Evaluate the torque child and check its Torque type before evaluating the duration child and checking its Time type, matching the inherited force helper. Each child executes once; a first-child type failure precedes a second-child evaluation failure. Inherited name, frame, abstract and callback rules still apply. Require exactly Torque and Time, without implicit dimension coercion; require a finite signed canonical binary64 torque and a finite strictly positive canonical duration. A child expression's error retains its existing span and precedence. Type/domain checks occur in source order after the inherited structural/name pass. Torque intervals use the existing stable-key grammar `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Keys are unique among all torque statements in the entry scene, independently of force/action keys. They are never merged, restarted or silently renamed.

An interval's stable identity is `[module_id, scene_id, "torque", torque_key]`. Its immutable source record binds target element/occurrence identity, entry source ID and source revision, full program revision and dependency closure, the complete UTF-8 statement span, the zero-based sequence index among all event kinds, axis, canonical signed torque, activation and completion. The operand and duration spans are additional repair locations, not permission to edit a library, sibling, generated expanded source or unrelated text. Revision identity is computed by the unchanged bundle algorithm; whitespace changes remain source changes.

## 3. Exact time and physical admission

Activation `s` and duration `d` are the exact rationals represented by their canonical binary64 seconds. End `e=s+d` is exact rational addition, with no intermediate float, epsilon or clamp. Use the inherited finite-decimal exact-clock serializer. The interval is `[s,e)`. Before-side at activation is inactive and before-side at completion remains active; after-side reflects the complete committed boundary. Completion may exceed scene duration or binary64 magnitude. An unrequested future completion is neither evaluated nor manufactured at the requested endpoint. Distinct exact clocks remain distinct even if binary32 output cannot distinguish them; recorded output then refuses that clock set.

At each activation, the ordered tentative target must exist, be dynamic, have no active incoming motion/following/connection authority, and have its own homogeneous sphere body. An earlier release in the same sequence may make it eligible. A torque does not release or switch a body's motion mode. Mass, radius and inertia are the existing finite positive canonical own-body quantities. Inertia remains the inherited single canonical rounding of exact `2*m*r*r/5`; the torque path must use the already admitted model inertia, not recompute it with floating intermediate products. Descendant ownership contributes no extra matter. Invalid body construction is rejected at its original physical-property source location before evaluation.

The first successfully committed torque activation latches the selected axis, even for zero torque or cancellation. Every individual later interval must use that axis. Incoming canonical angular velocity must have exactly zero orthogonal components; signed zero counts as zero and published zeros are canonical positive zero. Test every ordered intermediate impulse result against an already latched axis; a later cancelling impulse cannot conceal an invalid intermediate state. A mismatched axis is refused even when the resulting net torque would be zero. Axis lock survives empty active sets, zero speed and reversal, and is cleared only by reset or accepted revision replacement. This first domain has no supported dynamic-to-constrained-to-dynamic relatching operation; inherited unsupported motion-authority changes remain refused.

For a body at a complete boundary, sum all active canonical scalar torques exactly, in canonical torque-key order for charging and provenance:

`S = sum(Fraction(tau_i)); net = RN64(S); alpha_c = RN64(Fraction(net)/Fraction(I))`.

`RN64` means finite IEEE-754 binary64 nearest, ties to even, then canonical positive zero. Neither net nor acceleration may be infinite or NaN. Cancellation is applied before either rounding; an overflowing partial float sum is never evaluated. A finite subnormal result is allowed. Underflow to zero is allowed, recorded and used for the canonical transition decision. The separate ideal reference acceleration is `alpha_ref=S/Fraction(I)`, before the exposed net rounding. It supplies a numerical error bound and does not replace exposed canonical dynamics.

## 4. Atomic ordered boundaries

All affected bodies share one transaction at each exact inherited source/action/force/reach/torque-completion boundary within the requested prefix. Preserve inherited action completion and incoming release semantics. The additive order is:

1. Certify the incoming prefix under the old laws; save complete incoming poses, source numeric bounds, authority and release-transfer data. An incoming-prefix failure precedes any new boundary event.
2. Stage the existing state without mutating accepted state. Complete inherited actions and remove force and torque intervals ending exactly here, preserving complete tentative histories. Within torque completion history use ascending torque keys. Do not test intermediate aggregate sums.
3. Execute the authored event sequence in written order. Each release and impulse retains its inherited effect and checks. Each torque checks free mode/body, axis spelling/lock, incoming spin and complete identity before staging its start. Every impulse on a latched carrier checks the resulting orthogonal angular components immediately, including before the first nonzero torque acceleration. A zero impulse retains its inherited neutrality.
4. Apply inherited final force aggregation and translation transfer first, in inherited object order. Then aggregate final torque sets in ascending stable object path. Validate final canonical net and acceleration and reference bounds. A force failure therefore precedes a torque aggregate failure at the same boundary. No source-event ordering is inferred from torque-key sorting.
5. Apply the rotation transition and anchor rules below using the fully ordered staged angular state. Validate all staged state/history/resource projections, then commit all bodies and every source count together. The final commit check must use the original request deadline and cancellation callback.

A semantic, numeric, work, deadline, callback or cancellation failure discards the whole boundary: starts, completions, locks, forces, releases, impulses, anchors, counts and recent history. The consumed work/failure record remains observable, but there is no accepted partial boundary. Keep the exact previously certified prefix and before/after meaning. A failed completion identifies its original interval statement; it is not assigned a fabricated source location. A later failure cannot invalidate an already accepted shorter request or label an uncomputed state valid.

## 5. Legacy versus split rotation

Each carrier begins with `rotation_route="legacy"`. Axis admission and torque history are independent of this kinematic choice. Preserve the exact inherited ReachSimulator route until the first committed boundary whose **final canonical** angular acceleration is nonzero. Zero torque, underflowed acceleration, complete cancellation and same-net replacement cannot change motion anchors. Removing one member of a cancelling pair can be the transition boundary without any new source statement.

At that transition, retain the full staged internal rotation representation and canonical signed component of angular velocity, at time `tr`. This establishes `(tr,q_r,omega_r,alpha_c)` plus its independent numeric error/reference records. It does not normalize or reconstruct `q_r` from public quaternion JSON. Leave the entire inherited translation anchor, dynamic-since time, force state, translation error, ideal acceleration and transfer-cell records unchanged except changes independently required by that boundary's inherited release/force/linear impulse. Switching route creates no mass, force or translation influence.

The split route persists through later zero acceleration. Reanchor canonical rotation only when final canonical alpha changes, or an inherited nonzero angular impulse requires a speed discontinuity. If an impulse changes only translation, retain the rotation anchor exactly. If a source boundary changes only torque identity/history and canonical alpha is unchanged, retain the anchor even if ideal-reference acceleration changes. Multiple impulses at one boundary must each be checked in sequence, but one final rotational anchor represents their accepted final state. A pre-transition COM-force change still follows the complete inherited anchor path; splitting every carrier at initialization is prohibited.

Once split, pure COM-force changes can reanchor inherited translation but cannot reanchor rotation. Inherited motion consumers, release/impulse transfer, phase bounds, inspection and recording must read the split angular state, not stale angular fields on the legacy translation record. Direct or cached reads of that legacy field are not an alternate authority. A full runtime audit must cover each such consumer before implementation acceptance.

## 6. Canonical phase, speed and bounded numerical evaluation

For exact `u=t-tr`, compute the following directed arithmetic graph from canonical anchor operands:

`u2=u*u; linear=Fraction(omega_r)*u; curved=Fraction(alpha_c)*u2/2; P=linear+curved; phi=RN64(P)`.

`W=Fraction(omega_r)+Fraction(alpha_c)*u; omega=RN64(W)`.

Products, sums and division are exact bounded rationals; each exposed scalar is rounded only once at the stated point. Preserve prospective operand-width checks before multiplication/shift/allocation and the actual result guards. Evaluate P, W and every prospective operand only within the requested prefix. At exact zero u or zero P, return the full saved rotation unchanged; do not incur an extra normalization step. Otherwise evaluate `ReachPoseOps.axis_rotation(positive_axis,phi)` and left multiply it by `q_r`, using the inherited internal `RotationValue`, rescaling, sign, publication and finite-domain rules. Its axis, trigonometric, multiplication and public quaternion allowances remain explicit. A libm-only calculation or an old constant-rate recording cursor is not an eligible substitute.

The first finite .22 split domain requires `abs(P)<=2^20` radians throughout each requested open segment and at its one-sided endpoints. Equality is admitted. Check the exact stationary point `u=-omega_r/alpha_c` when it lies in the segment, in addition to both endpoints; no such extra check is needed for alpha zero. W is affine, so finite canonical endpoints and inherited continuous finite guards suffice for speed. The phase-domain restriction is a new explicit .22 capability boundary; it does not restrict any earlier binding or a .22 carrier still on its legacy route. It concerns phase since its actual canonical rotation anchor, not cumulative revolutions of the entire scene. Refuse with `torque_reason="phase_domain"`; do not wrap P, clamp it or silently reset the anchor. A shorter valid prefix remains usable.

Range reduction and trigonometry reuse the exact C088 ReachPoseOps source algorithm: 96-bit dyadic source arithmetic; the fixed precision schedule `(96,192,384,768,1536)` for interval pi reduction; the existing Machin pi enclosure, bounded quadrant selection, `abs(reduced_midpoint)<=1` and argument-error guard, fixed polynomial and published error constants. Complete source/derivation hashes are in the implementation basis. No host `pi` constant replaces that enclosure. Failure to certify reduction is an explicit numeric refusal, not a request for additional unbounded precision. The numerical operand ceiling remains 32,768 bits, cache 256 entries, existing series/interval ceilings and 64-step recording cursor policy; .22 does not increase any of them. The torque path initially disables constant-rate cursor reuse on split affected paths.

## 7. Independent reference and error transport

Maintain a reference rotation/signed-speed law distinct from the canonical anchor, using `alpha_ref` and the inherited actual canonical mass/inertia. It carries inherited angular input error and ordered impulse/release transfer error. It does not claim exact source-decimal mass or the inertia of a compound body. A change in alpha_ref may split this reference/error history without changing the canonical anchor. Store its exact start clock, signed reference speed and acceleration, and its angle/speed discrepancy bounds at that clock. Do not replace the reference derivative using a rounded sample of canonical speed.

For one interval with a common error origin and width d, a sufficient discrepancy contribution is `Etheta + Eomega*d + abs(alpha_c-alpha_ref)*d*d/2`. Add actual phase RN error and the inherited axis/product/publication terms. A whole-phase RN bound is `M*2^-53 + 2^-1075`, where M is a source-derived bound on absolute exact P over the complete interval, including its vertex. The speed RN contribution has the analogous bound from W. At a changed reference boundary, evaluate and carry the previous bound before changing the reference acceleration. At a genuine canonical reanchor, carry the old reference discrepancy and the actual canonical speed/phase publication errors; resetting an accumulated error to zero is forbidden. No additional physical rounding is introduced just to compute these bounds.

The reference update is executable without a new physical anchor. At the first latch, set the reference/error origin e to the boundary clock, its reference speed center to the staged canonical signed component, and Etheta/Eomega to the complete inherited angular pose/velocity bounds at that clock, including orthogonal uncertainty. Reference orientation is the corresponding staged rotation center with that inherited enclosure. Do not reset those inherited bounds. At each later reference/error origin `e`, retain exact reference speed `wr_e`, reference acceleration `ar`, and bounds `Etheta_e` and `Eomega_e` comparing the reference law to the **unrounded smooth canonical law**. The latter has speed `wc(e)=Fraction(omega_r)+Fraction(alpha_c)*(e-tr)`, even if its canonical anchor tr is older than e. For `d=t-e`, advance `wr=wr_e+ar*d`, `Eomega=Eomega_e+abs(alpha_c-ar)*abs(d)`, and `Etheta=Etheta_e+Eomega_e*abs(d)+abs(alpha_c-ar)*d*d/2`, using guarded exact arithmetic. A shadow-only acceleration change retains these propagated bounds, replaces e/wr/ar, and never samples RN speed to seed wr. If an enclosure was obtained around a rounded sample rather than the smooth law, add that sample's actual phase/kernel/publication discrepancy before adopting it as a smooth-law enclosure. The canonical finite-domain and projection allowances are then added only for the actual requested sample or uniform phase proof.

At a genuine canonical anchor change, first propagate the old bounds to that boundary. Add the actual phase rounding discrepancy and new axis/product error for any newly constructed anchor rotation, plus the inherited exposed-rotation error only when a public materialization actually occurs. Carry the inherited full RotationValue error; neither its public quaternion alone nor a zero error is an eligible replacement. Add the actual speed rounding discrepancy and inherited impulse transfer error to the speed bound. Reference angular impulses use the existing independent transfer law; retain its complete vector uncertainty, including orthogonal components, in Eomega. A boundary with multiple impulses uses each ordered transfer and check. Double-counting a conservative bound is permissible if reported, but omission is not.

Before split, the canonical angular law is the actual inherited legacy law. A latched underflow/cancellation history still maintains the separate torque reference/error origin with canonical torque acceleration zero. Propagate the torque-induced discrepancy by the same recurrence with alpha_c=0, add inherited legacy anchor/materialization discrepancies at actual inherited boundaries, and preserve the inherited canonical path exactly. Thus a minimum-subnormal torque divided by inertia two may leave canonical motion unchanged while requiring a nonzero reference/error projection. These angular shadow records do not change translational errors or cause canonical anchors.

Pure torque preserves all translational anchor/error records. Fixed marker translation and landmark errors are then derived from the full rotation bound and their actual radii as specified in [RECORDING.md](RECORDING.md). New samples neither advance canonical state nor reset error. Repeated, segmented and resumed requests must preserve their inherited state/identity semantics and calculate the same fields at common exact clocks, subject to the explicitly frozen comparison class.

Ideal work/energy assertions use `Delta K=I*(omega1^2-omega0^2)/2` and `Work=tau*(omega0*d+alpha*d*d/2)` with the specified exact ideal law. Runtime canonical results need a predetermined discrepancy envelope. For a canonical/reference angular-velocity vector discrepancy e, `abs(Kc-Kr)<=I*(2*norm(wr)*e+e*e)/2` (the norm reduces to absolute value on an exact scalar-axis reference); for one constant interval, work discrepancy is bounded by `abs(tau_ref)*Ephase + abs(tau_c-tau_ref)*abs(phi_c)`, with exact sums over reference intervals and inherited impulse work reported separately. Here Ephase bounds the signed **unwrapped phase displacement** difference, including phase rounding; a shortest quaternion angle modulo a revolution cannot bound mechanical work. When impulse/release uncertainty requires a vector bound, retain the complete inherited transfer enclosure. The frozen small dyadic examples may have exact equalities; no universal exact-energy claim applies to rounded outputs. Tolerances cannot be chosen from candidate results.

## 8. Real work, limits and cancellation

Every stage uses the admitted complete-request `SharedExecutionBudget` and its original start/deadline/cancellation callback. Current host policy bounds source requests; caller caps only reduce them. Missing/unadmitted execution context has the inherited `execution_context_required` refusal. No direct simulator call, cache hit, resumed store or historical accepted program supplies a fallback grant. Preserve callback exception object identity. Stage wrappers restore the prior stage in `finally`.

One stage tick polls original cancellation before incrementing/checking operations and then checks original elapsed time, in the existing order. The tick must succeed before the bounded work described here. Numerical primitives additionally use their unchanged exact decode, prospective guard, operation and result charges. No table row replaces or double-counts those primitive operations; structural ticks and arithmetic charges are separate real work categories.

| New stage | Exact structural charge | Work after the tick |
| --- | ---: | --- |
| `torque_source` | 1 per encountered torque statement | Admit its bounded parsed shape; inherited expression/linker checks remain separately charged |
| `torque_boundary_scan` | 1 per active interval visited during next-boundary selection | Compare its exact end with the current minimum |
| `torque_completion` | 1 per ending interval | Stage its removal/count/recent record |
| `torque_activation` | 1 per source torque event | Mode/body/axis/spin checks and stage the bounded identity |
| `torque_impulse_axis` | 1 per impulse on a latched carrier | Check all three already canonical components against the selected axis |
| `torque_aggregate_begin` | 1 per affected carrier | Admit native bounded active-set metadata and own inertia |
| `torque_aggregate_term` | 1 per active interval | Read admitted scalar/axis/key; then charge exact decode/add through inherited primitives |
| `torque_aggregate_publish` | 1 per affected carrier | After separately charged net/alpha/reference calculations, stage exposed results |
| `torque_reference_origin` | 1 per actual reference/error origin initialization, acceleration change or anchor/materialization transfer | Propagate the old exact law/error, then stage the new shadow origin; no canonical anchor is implied |
| `torque_rotation_anchor` | 1 per actual canonical rotation transition/reanchor | Retain full rotation, clock, signed speed and error/reference state |
| `torque_segment` | 1 per carrier/requested segment | Admit endpoints and the bounded exact polynomial graph; charge each primitive separately |
| `torque_segment_vertex` | 1 when a nonzero-alpha exact stationary point is tested | Charge calculation and interval/domain comparison; no new public clock |
| `torque_projection` | 1 per emitted active/recent record and 1 per object header, including empty noncarrier headers | Build only the admitted bounded closed projection; normal JSON accounting remains |
| `torque_boundary_commit` | 1 per complete boundary with a torque-state change | Recheck current request context before replacing accepted state |

For n active intervals the aggregate-specific structural cost is exactly n+2 per affected carrier, excluding real numerical work and inherited iteration. A zero/cancelling term is still visited and charged. A failed early stage prevents later visits/publication. No presorted foreign iterable, custom native wrapper, callback-created mutable history, malformed type or changed owner may bypass admission. Snapshot complete exact native immutable entries before any callback-driven traversal; revalidate context after callbacks. Scalar/root/schema widths and inherited total source-event/object limits bound allocation before iteration; large histories also consume the unchanged 100,000 record and 8,388,608 JSON-byte limits. Do not truncate a successful projection.

Defaults remain 100,000 operations and 30,000 ms. Source authorizations for higher ceilings remain the adopted .7 feature. Original fixtures, horizons, rates, tolerances, execution roles and failure dispositions stay unchanged. The test packet must execute cancellation/deadline/operation-cap failures at every newly reachable stage with successful original controls, and ensure failed boundary/state/artifact publication remains atomic.

## 9. Diagnostics and deterministic precedence

Retain complete inherited diagnostics, phases and child spans before the new checks. New torque semantic diagnostics use the full torque statement as primary, the target declaration as related for mode/body/spin errors, and ordinary immutable source/program identities. Required additional details are `torque_key`, `target_path`, `sequence_index`, and `torque_reason`; staged activation, impulse-axis, aggregate and commit diagnostics include exact boundary time and `side="after"`. Incoming-segment and phase-domain failures keep the actual requested side and inherited requested-time/last-valid-prefix fields; a before-side request is never mislabeled after. Axis-lock details also contain `expected_axis` and `actual_axis`. For an off-axis impulse use the actual impulse statement and its inherited identity plus `torque_reason="impulse_axis"`, `expected_axis` and actual canonical angular vector. Automatic aggregate/completion errors choose the lexically first changed torque key as primary and retain all changed identities in sorted details; if none, use the body declaration. Do not expose an unbounded source literal in an error.

| Condition | Code and phase | Exact torque-specific message / reason |
| --- | --- | --- |
| Torque operand has wrong dimension | `OKL-E-TYPE`, `type` | `A torque interval requires a scalar Torque value.` / `operand_type` |
| Duration has wrong dimension | `OKL-E-TYPE`, `type` | `A torque interval requires a Time duration.` / `duration_type` |
| Axis identifier outside the three names | `OKL-E-FRAME`, `compile` | `A torque axis must be world_x, world_y or world_z.` / `axis_name` |
| Nonpositive duration | `OKL-E-EVENT-ORDER`, `compile` | `A torque interval requires a strictly positive duration.` / `duration_nonpositive` |
| Duplicate torque key | `OKL-E-NAME`, `compile` | `Torque interval keys must be unique within the entry scene.` / `duplicate_key` |
| Target is not a free dynamic sphere | `OKL-E-MOTION-MODE`, `admission` | `A torque requires a currently free dynamic sphere.` / `target_mode` |
| Unsupported or nonpositive own body at activation | `OKL-E-PHYSICAL-DOMAIN`, `admission` | `A torque requires positive own sphere mass, radius and inertia.` / `target_body` |
| Different axis after lock | `OKL-E-FRAME`, `admission` | `A torque interval must use the carrier's latched world axis.` / `axis_lock` |
| Incoming angular velocity is off-axis | `OKL-E-FRAME`, `admission` | `Angular velocity must lie on the selected torque axis.` / `incoming_axis` |
| Ordered impulse result is off-axis | `OKL-E-FRAME`, `admission` | `An impulse must preserve the carrier's latched torque axis.` / `impulse_axis` |
| Final canonical net or alpha is nonfinite | `OKL-E-NUMERIC`, `evaluation` | `A canonical torque result exceeds the finite binary64 domain.` / `net_overflow` or `acceleration_overflow` |
| Split phase exceeds its complete-segment domain | `OKL-E-NUMERIC`, `evaluation` | `A torque rotation segment exceeds the supported phase domain.` / `phase_domain` |

Malformed stable keys, invalid source clocks, unknown targets, invalid physical declarations, failed pure children, operand-width/execution limits, finite speed/refinement faults and transport failures keep the inherited diagnostic constructor and actual source location. The freeze supplies their complete expected projections. New token syntax errors remain ordinary parser errors. For independent defects in one torque statement, inherited structural/name checks precede torque-child evaluation/type, duration-child evaluation/type, axis-name admission and positive-duration admission in that order; for activation use mode, physical body, axis lock and incoming spin in that order. Numeric aggregate order is net, canonical alpha, reference/error domain. Source ordering settles multiple statements; stable object order settles multiple final aggregates. The recording contract separately defines `OKE-E-TORQUE-COMPOSITION` before pose/key allocation for an unsupported affected path.

## 10. Agent, state and delivery linkage

[AGENT.md](AGENT.md) and the [Agent/0.22 schemas](../agent-v0.22/README.md) define exact closed new projections and inherited operation transport. Every source, state and artifact record binds the actual accepted program/source closure, target and interval identities. The torque state is present on every .22 object, including an empty state; no inferred missing-field default is permitted. Complete histories and physical quantities remain world-referenced under a self-frame inspection request. Current host/caller authorization, original callbacks, exact source-span edits, store isolation, cancellation, retries, reopening and artifact chunk/EOF behavior remain mandatory.

[RECORDING.md](RECORDING.md) extends the actual reach recorder and independent supplied-byte reader. It retains flat baked world poses, exact mandatory boundaries, source/endpoint/clock/quaternion bounds, angular travel, fixed-offset and landmark radii, independent reconstruction and explicit unsupported-composition refusal. A new controlled destination binding is required for .22; older .6-only playback is not relabeled. A valid source state, a valid GLB, controlled playback and a complete release are separate claims.

## 11. Predetermined comparison and acceptance

The [independent packet](freeze/README.md) contains literal sources, source/library/image identities and modes, expectations, exact repairs and complete case procedures. Six comparison classes are mandatory: unchanged predecessor complete streams; same-program repeated/resumed requests; new-profile neutral legacy-route physical fields; torque-only carrier COM translation; equivalent nonzero schedules on an established split route; and different-source delivery with enumerated metadata/sampling differences plus equal geometry/material/image streams and common-clock physical checks. A new source/program/target cannot have identical complete source-bound GLB bytes. Conversely, unchanged predecessor inputs cannot be excused by a looser scoped comparison.

Adoption requires unchanged C088 preflight, independent complete specification/corpus/schema/numerical review, a hash-bound decision, and publication/readback of every frozen byte and mode. Draft labels remain historical after adoption. Runtime implementation starts only after that readback; implementation requires the frozen cases, independent readers/hostile mutations, actual Agent and destination workflows, full applicable inherited regression and resulting-main checks. This contract-only checkpoint does not execute torque, close a finite torque release, alter Original28's 24/28 overall failure, supply missing external/interpreter attestations or complete any unverified GOAL domain.
