---
project: OntoKin
document_id: OK-LANG-006
title: Reusable planar reach actions
version: 0.1.0-draft.2
date: 2026-10-20
status: proposed-for-peer-review
document_type: proposed-language-contract
language_version: "0.6"
profile: planar-reach-0.1
implementation_status: not-implemented
---

# OK-LANG-006: Reusable planar reach actions

## 1. Authority, dependency and intended task

This is a review draft, not an adoption or implementation record. Its original corpus was prepared on force candidate `06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a`; the effective Draft 2 dependency is verified main `59b937d16ec0c82c9bc1395bd0c9bcc63e597261`, following accepted [PR #17](https://github.com/Omegapy/OntoKin/pull/17), complete F01–F12 evidence and fresh resulting-main verification. The [explicit amendments](planar-reach-v0.1/draft2-amendments.json) preserve the original corpus and distinguish recovered files from freshly reconstructed contract work after the executor rollback. Do not infer that the current parser accepts the proposed built-ins. The [companion directory](planar-reach-v0.1/README.md) separates proposed source and independent expected results from future executed evidence.

The proposed capability is a reusable two-link articulated part that reaches an authored point through two prescribed hinge coordinates. OntoKin derives the joint solution, supplies the motion and lifecycle, and reports the actual goal residual. A complete bench tool arm and a segmented exterior character use the same pinned component library. Parameter variants, repeated keyed limbs, coordinated independent actions and local repairs are required. The fixture entries must not contain solved joint angles or task-specific inverse-kinematics equations.

This advances the [GOAL](../../GOAL.md) and finite portions of CAP-01–03, CAP-08–09, CAP-13–16; LNG-003–006; OBJ-004/006/013–015; MEC-008; BIO-005/008/011; and ANM-003/004/014. The broader [CAP](../product/OK-CAP-001-modeling-motion-and-object-structure.md) and [PRD](../product/OK-PRD-001-product-requirements.md) retain their review status. The new profile does not promise dynamic actuators, torque limits, load-bearing joints, acquired grips, collisions, balance, walking, surface skinning, or live target physics.

Earlier [core](OK-LANG-001-core-language-specification.md), [construction](OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md), [surface](OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md), [impulse](OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) and [force](OK-LANG-005-finite-center-of-mass-force-intervals.md) meanings and fixtures remain unchanged. Their classes, pure methods, pinned bundles, source authority, prescribed joints, one-sided state, force/impulse semantics and limitations are inherited unless an explicit clause below adds a new meaning.

## 2. Proposed bindings and source interface

| Binding | Proposed value |
| --- | --- |
| Source | `ontokin "0.6"; profile "planar-reach-0.1";` |
| Agent | `ontokin.agent/0.6` |
| Recorded delivery | `ontokin.glb/0.6` |
| Durable store | `planar-reach-program-agent.sqlite3`, schema `ontokin.planar-reach-program-agent-store/0.1` |
| Bundle/revision and diagnostic envelope | Existing `ontokin.bundle/0.1` and `ontokin.diagnostic/0.2` |
| New source type | Opaque enum `ReachBranch` with predefined values `elbow_positive` and `elbow_negative` |
| New pure builder | `reach_planar(JointRef, JointRef, SiteRef, Point3, Time, ReachBranch) -> Action` |

A 0.6 unit may import exact pinned definition modules declaring 0.2 through 0.6. Older units cannot acquire upward import edges or new built-ins. Imports retain their full existing byte and version checks. `ReachBranch` is not a String or Int, and no implicit conversion from either is permitted. The new names are predefined symbols only in this profile, not new global reserved keywords in earlier profiles.

The document's draft version is separate from package identity. Proposed library package IDs use the `proposal.reach-*` namespace and exact package version `0.1.0`; inherited bundle versions do not accept prerelease suffixes.

The first two builder arguments identify the shoulder and elbow joints in that order. The third names the end site. A public method encapsulates these internal references:

```ontokin
public method reach_to @ "reach-to"(
    target: Point3, duration: Time, branch: ReachBranch
) -> Action {
    return reach_planar(self.shoulder, self.elbow, self.forearm.tip,
                        target, duration, branch);
}
```

Construction of an Action is pure: it captures immutable references, target, duration and branch and does not query or change a run. The target frame is the exact frame identity of the shoulder parent site. The example library exposes that frame through a public `reach_frame: FrameRef` derived property, so a client can use `point(arm.reach_frame, x, y, 0[m])`. A different frame with a coincident transform is still different. No implicit conversion, world-target tracking or future frame sampling occurs.

The full new source spelling is specified in [grammar.ebnf](planar-reach-v0.1/grammar.ebnf). Its additions use existing class, method, expression, action and event grammar; proposed source files are complete programs in that proposed grammar.

## 3. Supported chain and explicit limits

At construction, resolve actual source instances, sites, relations, types and defaults. A claimed component name alone is insufficient. Require:

1. Two distinct prescribed hinge joints and three distinct objects: base, upper link and forearm. Shoulder parent belongs to the base; shoulder child and elbow parent belong to the upper link; elbow child and end site belong to the forearm. Both links are prescribed and have the inherited unique incoming pose authority. Ownership may organize these objects independently of the joint edges.
2. The shoulder child site and elbow child site have zero local translation and identity local rotation. The elbow parent site is `(L1, 0, 0)` in the upper-link frame with identity rotation. The end site is `(L2, 0, 0)` in the forearm frame with identity rotation. Both joint axes are exactly canonical `(0, 0, 1)` after inherited axis validation. These actual site conditions establish the finite planar model; reversed axes or general chains require another profile.
3. Each canonical length lies in `[0.125, 4]` meters. The links' site geometry, independently of visible surface placement, determines these lengths. Joint initial coordinates and closed limits lie in `[-P, P]`, where `P` is the inherited binary64 value of `180[deg]`. Limits and all initial conditions must already be valid under the baseline.
4. The target has finite canonical meter components, exact local `z = 0`, and `abs(x), abs(y) <= 8`. The duration lies in `[1/1024, 60]` seconds. This is a supported authoring range, not an actuator-speed guarantee.
5. The base may be static or prescribed. Its incoming chain may contain fixed transforms and massless following, ending at a static root or a free prescribed root with the inherited move/spin actions. An intervening articulated/dynamic base dependency is unsupported for this first reach profile. Root translation/rotation may run concurrently with the reach.
6. Outgoing massless visual followers and an inherited initial grip on the forearm are allowed; they add no actuator or contact model. Another action may not control either claimed joint. Existing relation cycle, extra incoming authority and physical compatibility checks still apply.

The new hard maxima are 32 distinct structural chain triples bound by constructed named reach actions per program, 128 named reach Action instances, and 32 simultaneously running/paused reaches. A triple is the ordered occurrence identity tuple `(shoulder joint, elbow joint, end site)`; aliases to the same tuple count once. Uncalled method bodies do not construct actions or triples. Distinct tuples are counted even if their backing descriptions share storage. Repeated named actions over one tuple each consume the action count. P23/N11 bind and start all 32/33 actual chains, while P24/N13 bind 128/129 named actions to one chain. No quadratic enumeration of unrelated site combinations is required. All inherited maxima also apply, including 1,000 objects, 100,000 semantic operations/materialized logical entries, 4 MiB Agent envelopes, finite snapshots and cooperative elapsed-work limits. Smaller request budgets are permitted; larger requests cannot raise profile maxima. Unsupported or resource-limited output must not be labeled a complete assembly/action.

## 4. Reachability, branch, wrapping and numerical meaning

Let canonical target components be `x,y` and canonical site lengths be `L1,L2`. Compute the exact rational values of `r2 = x*x + y*y`, `(L1-L2)^2`, and `(L1+L2)^2` before classifying reachability. No epsilon or rounded partial product enlarges this interval. If `r2` is outside the closed interval, the target is geometrically unreachable. Do not clamp it onto the reachable boundary or present a best-effort pose as successful reach.

When `L1 == L2` and `r2 == 0`, the shoulder solution is underdetermined. Return the singular-goal diagnostic for both branches, with no claimed motion; do not call this geometric impossibility. Unequal-link inner-boundary solutions and outer full extension are supported. At full extension, both branch values resolve to the same zero elbow angle. At the unequal-link inner boundary, the two branches select positive or negative half-turn respectively.

For the remaining reachable targets, over exact real mathematics of the canonical inputs:

```text
c2 = (r2 - L1^2 - L2^2) / (2*L1*L2)
q2_exact = branch_sign * acos(c2)
q1_exact = atan2(y, x) - atan2(L2*sin(q2_exact), L1 + L2*cos(q2_exact))
```

`branch_sign` is +1 for `elbow_positive`, -1 for `elbow_negative`. `atan2` is in the usual mathematical interval `(-pi, pi]`; signed zero has no independent source meaning. Normalize `q1_exact` modulo exact `2*pi` into `[-pi, pi)`, then round each exposed joint target once to binary64. If rounded `q1` equals `P`, canonicalize it to `-P`. Do not normalize `q2` across its chosen sign: its positive and negative half-turn values remain `P` and `-P`. There is no nearest-current-angle choice, alternative winding search, branch fallback or shortest-arc rewriting.

Compare these final canonical target coordinates against the closed canonical joint limits. A selected-branch limit failure remains a failure even if the other branch could reach the target. Accepted interpolation runs directly from the current unwrapped canonical coordinate to the resolved canonical target. In particular, an initially positive near-half-turn shoulder may move almost a full turn to a negative principal target. That is the specified motion, is bounded by the limits, and must be recorded honestly.

A future implementation must use the bounded [numerical admission strategy](planar-reach-v0.1/numeric-admission.md) and independently checked rounding-cell and residual evidence. Exact classification and radical signs precede outward interval passes at 96, 192, 384, 768 and 1,536 bits. Prove selected canonical targets before closed-limit comparison, bound rational operands and work, and report numeric failure if the finite passes cannot establish the result. Exhausted work reports resource failure; cancellation is interruption. The [counter clarification](planar-reach-v0.1/numeric-counter-units.md) defines 12,000 series recurrence steps, with every constituent interval operation charged separately against the 100,000 interval-operation cap and inherited remaining semantic work. Those caps are not extra program allowances. Host-library names alone are not evidence for correct rounding. The original high-precision corpus oracle and independent interval checker are preparation, not production execution.

Canonical resolved targets and the exact-rational coordinate interpolation have exact binary64 expectations. The companion's separate numerical tolerance is only for derived pose/orientation comparisons; it cannot permit several-ULP solver differences, move a hard limit, or merge exact clocks.

The final site residual must be at most `1e-9 m` in the chain-base frame for source evaluation. This numerical output criterion does not relax reachability or joint limits. A finite solution that fails the residual criterion returns a numerical goal failure. All diagnostics name the chain, target/frame, selected branch, responsible source spans and the failed condition.

## 5. Atomic action and boundary lifecycle

At `start`, validate the pending action and supported structural chain, capture the two current coordinates from the staged state, resolve the canonical target pair and residual, then claim both joint coordinates as one operation. A failure must leave neither a partial claim nor a changed coordinate. The action is the motion authority; hidden generated tween actions must not appear as independently authored sources or independently cancellable effects.

For local elapsed time `u` and duration `d`, each coordinate is the final rounding of `q_start + (q_target - q_start) * u/d`, using exact representations of canonical operands and exact rational time. Each open-interval rate is the final rounding of `(q_target-q_start)/d`. Their complete relative transform chain determines actual world poses, angular rates and end-site velocity. The two coordinates share one elapsed clock.

The inherited lifecycle applies to the whole reach:

| Event | Required effect |
| --- | --- |
| Start | Claim both coordinates, capture starts, resolve target, become running |
| Pause | Hold both current coordinates and elapsed time; retain both claims |
| Resume | Continue the originally resolved targets over the remaining local duration |
| Stop | Hold both current coordinates, release both claims, report interrupted goal |
| Natural completion | Latch both exact target coordinates, measure the final goal, release both claims, report completed only when residual passes |
| Reset | Reconstruct the accepted initial state and pending actions without modifying source |

A second action sharing either coordinate conflicts even if its numerical target is equal. Disjoint reaches and independent root/head actions compose. An ordered `stop old; start new;` is permitted; a later failure rolls back the entire exact boundary under inherited force-profile transaction rules. Natural completions, source events and automatic force completions share that atomic boundary. A failed boundary certifies only its valid incoming side and prior prefix; no partial after-state is published. Inherited evaluation still creates or advances a failed run descriptor with that valid incoming prefix. The accepted source and failed-boundary state stay unchanged; the prior run receipt need not stay unchanged. Cancellation or request-wide termination before publication has its separate inherited no-advancement outcome.

Pause/resume/stop and repeated action descriptions keep the exact clock and one-start-per-named-instance rules. A requested prefix before a future failed reach admission remains valid. Future goals must not be solved against future run state merely to validate an earlier requested prefix; complete source typing and immutable operand-domain checks still apply.

## 6. Goal inspection and source repair

Every named reach action has the proposed bounded revision-bound [projection schema](planar-reach-v0.1/schema-drafts/reach-projection.schema.json). It identifies the requested `program_revision`, action/chain identities, source unit/hash/span, target Point3 and frame identity, branch and duration. In an Agent response, `accepted_program_revision` identifies the actual accepted head and `candidate_only` reports whether the inspected source has ever been accepted. A different requested candidate does not become the accepted revision merely because inspection succeeds. A source-only recorded artifact uses `context_origin: source_recording` and null service-acceptance fields; it cannot invent an Agent acceptance.

Inspection without an actual sampled state returns `current = {available: false, reason: "run_required", value: null}`, including candidate-only inspection. It does not fabricate a pending action. An actual before-zero/reset sample, or a valid run sample before that named action's admission, can report pending. In such a sampled pending state, `resolved_joint_targets_rad`, `start_coordinates_rad`, `start_time_seconds`, `elapsed_seconds`, `completion_time_seconds`, `current_residual_m` and `terminal_result` are null. After successful admission, include the canonical resolved pair, captured start pair, exact start/elapsed/completion clocks as applicable, both claimed joint identities, effective limits, actual end-site pose and measured residual. A paused action has no predicted world completion until resumed; do not present an obsolete absolute end time as fact.

Use exactly four current goal outcomes: `pending`, `active`, `satisfied`, and `interrupted`, separately from request transport status. Stopped actions report `interrupted` even if their current pose happens to meet the target; only the defined completion certifies `satisfied`. Failed admission belongs to the failed request/boundary record and does not replace the valid incoming action state or introduce a fifth current outcome. Report classification and any failed condition, not a synthetic successful approximation.

`joint_coordinates_rad` and `joint_rates_rad_per_s` describe the two actual sampled coordinates. The proposed `action_joint_rates_rad_per_s` describes this action's own contribution and is zero while pending, paused, stopped or completed. A later action may move the same joints after this action stops or completes; even a pending action may observe another owner. Therefore current physical rates and current residual are not permanently zero or satisfied merely because this action is terminal. `terminal_result` latches the terminal time, coordinates, base-frame tip pose and measured residual. Only its satisfied completion residual must remain at most `1e-9 m`. The stopped terminal result remains interrupted. The [Draft 2 supplements](planar-reach-v0.1/draft2-supplements/acceptance.json) fix both-moving-joint pause/resume and stop-to-new-action samples before implementation.

A target remains fixed in its base-site coordinates. If the base moves, inspection reports both base-frame residual and the equivalent current world target/site, with their frame identities. Relevant inherited velocity meanings remain explicit.

The actual Agent gate must discover the typed reusable capability, create both complete assets, inspect effective lengths/sites/limits, perform a goal request through source, diagnose a seeded error, atomically repair one generated occurrence's length or limit, evaluate, deliver and retrieve the exact artifact. A changed length requires reconstruction of the actual sites and a newly solved reach for the new revision. Follow the inspected property's `source.initializer_target` to the writable root occurrence and its exact source span. For P13/P20 this is the `rig` root identity, not the generated arm or property identity. Reject otherwise identical patches submitted through either unauthorized identity. Sibling instance data and unchanged pinned-library bytes remain exact. Old runs/artifacts cannot be attributed to the repaired source. A different concrete part class retains the baseline new-key/rebinding requirement; this proposal does not add compatible replacement.

The proposed [operation mapping](planar-reach-v0.1/agent-operations.md) preserves the twelve inherited operation names and source-only mutation authority. It retains the global 4 MiB JSON envelope and lowered `budgets.max_value_entries` check on complete successful responses; globally bounded failure receipts remain deliverable under a tiny success budget. No new `max_response_bytes` request field is proposed. Q03 fixes actual sampled P24 at `1.5`, after-side, `selector.kind="action"`, `fields=["actions"]`, `limit=128`: all 128 complete items without a cursor. Measure the entire successful envelope's logical entries as `N`; budget `N` must succeed including cumulative constructor/intermediate charges, and `N-1` must fail at the final publication guard with no effects. Fewer items, an inner-array count or adaptive pagination cannot substitute. [Distinct budget units](planar-reach-v0.1/budget-counting.md) and their actual counting rules apply.

Failed-prefix inspection, reset and recovery remain separate from atomic source repair. After LP01's new L04 run through `0.25`, actually export with `options.end="0.25"` and retrieve the exact bytes under the fresh delivery run produced by export and the unchanged L04 program revision; retain the reset/evaluation run IDs separately. This is the separately required tenth Agent artifact, additional to nine ordinary deliveries and the 42 protocol steps. Q22 performs an actual same-project source edit from accepted L04 to exact L02 under its writable source authority, then rejects inspection of the retained L04 run using the new L02 revision. Creating another project cannot satisfy that stale-source probe.

## 7. Incoming release state

The initial-grip semantics are unchanged. A held sphere released at a reach completion reads the complete saved incoming world state, including the two nonzero incoming joint rates, even though natural completion latches the joint coordinates with zero outgoing rates. Do not use the outgoing held pose derivative or only the root velocity.

For a fixed base and zero child-site offsets, the end-site derivative in base coordinates is:

```text
vx = -L1*sin(q1)*dq1 - L2*sin(q1+q2)*(dq1+dq2)
vy =  L1*cos(q1)*dq1 + L2*cos(q1+q2)*(dq1+dq2)
omega_z = dq1 + dq2
```

Compose the actual root/base transform and root translational/angular velocity, including `omega_root cross displacement`, once. A local prop offset adds its own rotated lever contribution. Whole-boundary release/force/impulse ordering and failure rollback retain OK-LANG-004/005 meaning. A later successful world COM force affects the freed sphere only. No capture during motion or contact-based grasp is introduced.

## 8. Curved world motion and recorded delivery

GLB/0.6 must retain native geometry/PBR, whole-program source identities, per-boundary complete force/impulse/authority state, and the reach projection and goal result. It stores recorded rigid transforms, without executable IK or live joint physics. Every true source/action/force boundary inside the requested prefix is retained, including pause/resume and multi-coordinate completion. Preserve exact clocks; reject distinct boundaries that collapse in binary32.

Default delivered carrier/landmark position and rotation tolerances remain the inherited `0.001 m` and `0.001 rad`. The source goal-residual limit remains the separate stricter `1e-9 m`. Explicit caller settings and local surface tolerances retain the inherited rules; a fixture cannot loosen a tolerance merely to make a difficult path pass.

A linear coordinate tween generally creates curved world-space motion. Sampling only endpoints, or applying an angular criterion without a position bound, is insufficient. On each semantic interval, let `W0` conservatively bound the ideal constant root-spin norm and `W1,W2` bound the exact absolute coordinate slopes (zero for held coordinates). Derive slopes from exact canonical start/target differences and duration; a rounded inspection rate cannot understate a derivative bound. For a tracked carrier or landmark let `R` conservatively bound its distance along the constant root-to-base offset plus chain/site/local offsets. The supported fixed-transform/constant-root-motion assumptions permit conservative bounds `W = W0+W1+W2` and `A = R*W*W`. A tighter independently justified per-vector bound is allowed; unknown geometry/offsets cannot be omitted. Root translation has zero acceleration within such an interval. Independently freed spheres retain their force-profile canonical acceleration bound.

The [sampling derivation](planar-reach-v0.1/sampling-bound.md) proposes independently reviewable bounds over the allowed transform chain. On every retained interval require ideal carrier chord error `A*h*h/8 <= position_tolerance/4` and angular step `W*h <= pi/4`. The angular step alone does not establish orientation accuracy when root and joint rotations have different axes. glTF rotation tracks with `LINEAR` use shortest-arc spherical linear interpolation (SLERP), as specified in [Khronos glTF 2.0 Appendix C.4](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#c4-spherical-linear-interpolation). For that interpolation, the proposed conservative angular error is `B = W*W*h*h/4`; require `B <= rotation_tolerance/4`. If a visible landmark is at local radius `r` from its carrier origin, also require `A*h*h/8 + r*B <= position_tolerance/4`. Account for every delivered carrier and native geometry radius before allocating samples. A tighter independently justified bound is permitted.

Apply the bounds to exact source intervals and actual stored binary32 gaps, selecting the correct semantic phase; an exact boundary lying at a rounded gap midpoint must not select the following phase for the preceding interval. The proposed [quantization contract](planar-reach-v0.1/quantization.md) defines an independently recomputable bound using actual normalized stored endpoints, source/stored time gaps, all touched source phases and separately justified numerical errors. Its nonzero-endpoint difference proof uses no SLERP endpoint-Lipschitz assumption. Finite representability and exact binary32 conversion are mandatory; the time tolerance cannot exceed `1e-6 s`. Unknown or unproved error terms require rejection. The [metadata schema](planar-reach-v0.1/schema-drafts/glb-metadata.schema.json) applies at the inherited `document.extras.ontokin` location. These bounds and shapes do not authorize changing source motion or tolerances. Peer review must accept the derivation and quantization allocation before the engineering profile is adopted.

Preserve existing GLB maxima (10,000 keys, 250,000 baked poses, 1,000,000 validation poses, 250,000 native occurrence vertices and 64 MiB bytes). The 100,000 source-history limit counts weighted state records as defined in [budget-counting.md](planar-reach-v0.1/budget-counting.md), including full reach maps and complete incoming releases. It is distinct from Agent recursive JSON entries, whole GLB metadata entries and the new 100,000 interval-certificate cap. Preflight source histories and supplied-byte aggregate accessor expansion before decoded copies. Check cancellation in solving, claims, history, planning, geometry, decoding and serialization. A full-source future failure may not invalidate a delivered valid short prefix.

Independent acceptance checks the actual source-built source/Agent-retrieved GLBs in Khronos and Three.js, exact and intermediate source poses, goal residuals, joint limits and world landmark trajectories, plus reviewed browser captures of both complete assets. A valid format report, metadata or endpoint alone cannot establish this gate. Required inherited release roles use the current local validation policy and identified execution provider.

## 9. Diagnostic precedence and review gate

Use the inherited diagnostic envelope, with a new structured `reach_code` detail. Resolve malformed syntax/types and missing references first; immutable frame/operand/chain-domain failures next; then at admission check current mode and existing channel conflicts, exact reachability/singularity, prove selected correctly rounded canonical targets, compare closed canonical limits, and certify residual. Precharge/check work and cancellation throughout every phase; these are not deferred until after an unbounded numerical calculation. Cancellation is an execution interruption, not a geometric proof. The effective [profile](planar-reach-v0.1/profile-draft2.json), [diagnostic schema](planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json) and original acceptance records fix codes, phases and outcomes.

The first review must settle the explicit decisions already proposed here: strict canonical chain geometry, fixed target frame, principal shoulder wrapping, branch-preserving elbow half-turns, singular origin rejection, support/resource maxima, canonical transcendental rounding, two-coordinate transaction/lifecycle, goal projection shape, and curved-motion bound derivation. Any revision changes the draft version and fixture expectations through a visible decision record. Do not edit expected values merely to accommodate implementation output.

Adoption requires peer review of the complete source/expected closure, resolved issues, exact member hashes and accepted force dependency. Only a separately published adoption record may change this draft's status. The effective [R01–R12 and Q01–Q22 matrix](planar-reach-v0.1/requirements-draft2.json), L01–L04 and fixed protocol supplements, and [provider-neutral release contract](planar-reach-v0.1/release-contract.md) define full implementation acceptance. Actual source, Agent, decoded destination, browser, compatibility and inherited roles remain necessary for the identified implementation. Contract preparation does not complete those roles, the remaining GOAL areas, or the documented direct-tool authoring comparison.