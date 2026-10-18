---
project: OntoKin
document_id: OK-LANG-004
title: Source Impulses and Free-Sphere Dynamics
version: 0.1
date: 2026-10-18
status: adopted-language-contract
document_type: normative-language-contract
language_version: "0.4"
profile: impulse-0.1
implementation_status: implemented-release-verification-in-progress
---

# OK-LANG-004: Source impulses on free homogeneous spheres

## 1. Authority and scope

This contract was **adopted on October 18, 2026 before impulse implementation**, after review of proposal `0f051affc211b996b38531873a146f54fdf442b6` and its predetermined source corpus. The [adoption record](impulse-v0.1/adoption.json) identifies the unchanged acceptance bytes. Adoption itself does not pass a test or release gate. The immutable source fixtures and independently derived expectations are in [impulse-v0.1](impulse-v0.1/README.md). Their expected outcomes must not be changed merely to fit an implementation.

This contract adds authored instantaneous linear impulses, including off-center angular response, to free homogeneous spheres. It inherits the units, frames, motion authority, ownership, source identity, rational event clock and atomic boundary rules of [OK-LANG-001](OK-LANG-001-core-language-specification.md), the offline construction model of [OK-LANG-002](OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md), and the native visual surfaces of [OK-LANG-003](OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md). Existing meanings remain in force except for the explicit new-profile additions below. The broader [GOAL](../../GOAL.md), including contact, finite forces and other physics domains, remains open.

| Binding | Explicit new value |
| --- | --- |
| Source header | `ontokin "0.4"; profile "impulse-0.1";` |
| Program Agent protocol | `ontokin.agent/0.4` |
| Binary delivery target | `ontokin.glb/0.4` |
| Durable database filename | `impulse-program-agent.sqlite3` |
| Durable database schema | `ontokin.impulse-program-agent-store/0.1` |
| Source bundle schema and hash domain | Existing `ontokin.bundle/0.1`, unchanged |
| Source diagnostic schema | Existing `ontokin.diagnostic/0.2`, unchanged |

Old language, Agent, GLB and database bindings retain their exact behavior, defaults, schemas and identities. Selection of `0.4` is explicit. A geometry declaration does not add a body, mass, inertia, contact, a second pose authority or a force law.

## 2. Minimal source spelling and representation

Add one event statement, available only under the new source binding:

```ontokin
at 1[s] sequence {
    impulse rack.props["first"]
        using vector(world, 0[N*s], 2[N*s], 0[N*s])
        at point(rack.props["first"].frame, 0.5[m], 0[m], 0[m]);
}
```

The [additive grammar](impulse-v0.1/grammar.ebnf) reuses the current literal-key occurrence path and pure expression grammar. `impulse` is contextual at an event-statement start in `0.4`; it remains an ordinary identifier elsewhere. There is no global reserved-word change. The target is the existing member/literal-key path, not a new arbitrary target expression form. Both payload expressions are evaluated during elaboration. This does not introduce time-dependent source expressions or host callbacks.

The syntax node has kind `impulse`, `path` containing the existing `PathStep` sequence, `vector` and `point` expression nodes, and the entire statement's exact UTF-8 source span. Lowering resolves the target through the existing construction reference machinery to an actual object occurrence. It must not synthesize an occurrence from the spelling of a path. Generated references, aliases and inherited members preserve their established identity rules.

The runtime representation is additive: an event may carry an impulse payload containing `impulse_world_n_s`, `point_self_m`, `sequence_index` and `source`. `sequence_index` is **zero-based among all statements in that sequence**, including starts, stops and releases. Payload source metadata and the resolved target occurrence support the diagnostics and inspection record below. An impulse has no action handle, duration, pause/resume lifecycle or persistent action ownership.

## 3. Types, frames and import compatibility

The target must resolve to `Ref<Object>`. The impulse expression must be `Vector3<Quantity[N*s]>`, dimension `(length=1, mass=1, time=-1, angle=0)`, expressed exactly in `world`. `N*s` uses the inherited compound-unit grammar; no new globally available type alias is required. A length or force vector is not an impulse.

The application expression must be `Point3` in the resolved target's **own object frame**, with the inherited fixed Length components. `Point3<Length>` is an internal type description, not new source generic syntax: source declarations continue to spell `Point3`. A world, sibling or site frame is rejected even if it happens to coincide numerically. An alias of the very same resolved object frame is valid. The point's three components are finite canonical meters. The point may lie inside, on or outside the physical sphere: it specifies the lever arm of an ideal externally supplied wrench, not detected contact or a claim about visible surface membership. No hidden point-to-radius restriction is introduced.

A `0.4` entry or module may import exact hash-pinned definition modules declaring `0.2`, `0.3` or `0.4`. Every source unit is compiled under its own declared version/profile. An older declaring module may not import a `0.4` dependency; reject that new unsupported edge at its import span. Existing `0.2`/`0.3` import behavior is not retrospectively tightened. Surface types remain unavailable to a `0.2` declaration. Standalone `0.1` is not made into a new bundled dependency format. The complete reachable, acyclic, offline closure, one-version-per-package rule and single entry-scene rule are unchanged.

## 4. Physical admission and exact boundary update

An impulse can execute only on an object that is **currently dynamic and free** in the staged event state and has the supported homogeneous `sphere_body`. Initial dynamic spheres qualify. A prescribed sphere qualifies after an earlier successful `release ... using incoming` in the same sequence. A static or still-prescribed target fails with `OKL-E-MOTION-MODE`; an impulse never silently changes its mode or disconnects it. A dynamic `no_body` object already fails the inherited physical-domain checks. Unsupported physical models remain explicit domain/capability failures.

Only the selected occurrence's own mass and inertia enter the update. Ownership descendants are not a rigid aggregate body. Let the current staged world pose, linear velocity and angular velocity be `p, R, v, omega`, the authored self-frame application point be `q`, and the world impulse be `J`. The sphere's existing canonical inertia is `I = (2/5) m r²`. At the boundary:

```text
lever_arm_world = R q
application_point_world = p + lever_arm_world
angular_impulse_world = lever_arm_world × J
v_after = v_before + J / m
omega_after = omega_before + angular_impulse_world / I
p_after = p_before
R_after = R_before
```

There is no moving-frame velocity term in an instantaneous momentum update. For nonzero `J`, anchor the next free trajectory at this exact event time with the complete updated state. Between boundaries retain the inherited analytic uniform-gravity translation and constant-world-angular-velocity rotation. Impulses add no finite force, torque, damping or gravity integration step.

The physical kernel interprets the numeric components of `angular_impulse_world / I` as radians per second under the classical angular-momentum convention. This is an explicit mechanical conversion, not a change to user dimensional arithmetic: the source type system retains its distinct Angle/radian tag and ordinary expressions cannot erase that tag.

For exactly zero `J`, still validate and record the application, but preserve `p`, `R`, `v`, `omega` **and the existing trajectory anchor exactly**. A valid zero operation increments the count. Two opposite nonzero operations remain two ordered applications; their intermediate canonical states are observable within the retained record list.

### 4.1 Existing mass, radius and numeric domain

Mass and radius must be finite, strictly positive canonical values, and the derived canonical inertia must be finite and positive under the inherited `sphere_body` checks. Zero or negative input and inertia underflow to zero are `OKL-E-PHYSICAL-DOMAIN`; nonfinite arithmetic remains `OKL-E-NUMERIC`. This profile adds no arbitrary minimum mass/radius, world-coordinate cutoff, time epsilon or solver tolerance.

Use the inherited robust canonical rotation, affine-sum and cross-product operations. The **exposed** lever arm, world application point and angular impulse must each be finite. Compute each final velocity component as one exact rational sum over its canonical operands, then round that final component once: do not round the unexposed quotient `J/m` or `L/I` before adding it to the incoming component. Thus a finite final result obtained by cancellation is permitted even when that quotient alone would overflow binary64. A final component that cannot be represented fails. An exposed angular impulse that would overflow fails even if a hypothetical subsequent division would be finite.

The zero-impulse case still fails if its resolved world point is nonfinite; successful inspection cannot contain a nonfinite coordinate. Any numeric failure discards the entire tentative sequence. Positive finite-cancellation and actual final-overflow fixtures are separate predetermined cases, not permission to silently clamp values. Some valid evaluated states, including the extreme cancellation fixture, exceed GLB float32 delivery capability; evaluation success does not promise export success.

### 4.2 Written order and atomicity

Keep the exact rational source event clock, before/after boundary sides and existing simultaneous-boundary rules. Natural action completions are staged before source statements. A release continues to transfer the **saved incoming preboundary** pose and derivatives, including at an exact action-completion time. Each impulse instead reads the **current tentative state after previous statements**. Therefore `release; impulse` adds to the transferred velocity and spin; two impulses accumulate; `impulse; release` on a still-prescribed object fails.

A later failed statement rolls back all earlier statements and all new impulse records at that boundary. Previously accepted source, valid earlier run prefixes, prior application counts and prior record lists remain intact. Constructed state is before time-zero events. A `before` sample excludes that boundary's impulses; its `after` sample includes all successfully committed statements. No new endogenous times or collision event queue is introduced.

## 5. Observable state and resource accounting

All added state fields are limited to `impulse-0.1`. Old-profile snapshot shapes do not change. A dynamic object's existing `pose_authority.since_seconds` now explicitly remains the time it became dynamic, either zero or its release time. Add `pose_authority.trajectory_anchor_seconds` to distinguish the latest release/nonzero-impulse trajectory anchor. A later impulse must not relabel the dynamic origin.

Every object's state under the new profile contains this initially empty projection:

```json
{
  "impulses": {
    "applied_count": 0,
    "last_application_time_seconds": null,
    "last_applications": []
  }
}
```

`applied_count` counts that object's successful applications in the evaluated run prefix. `last_application_time_seconds` uses the inherited exact decimal timestamp representation. `last_applications` contains **all that object's applications at its latest impulse-bearing boundary**, in written order. Unrelated boundaries retain this list. A later impulse boundary replaces the list for that object; other objects' lists persist. Before-side samples and failed sequences retain the earlier projection. This is bounded recent influence state, not an unbounded historical log; earlier states remain accessible through existing exact-time inspection.

Each list member has exactly these fields, formalized in [impulses.schema.json](impulse-v0.1/impulses.schema.json):

| Field | Meaning |
| --- | --- |
| `sequence_index` | Zero-based index among all statements at this boundary |
| `source_location` | Exact `source_id`, `source_revision`, `start_byte`, `end_byte` of the impulse statement |
| `target_element_id`, `target_path` | Resolved source occurrence identity and canonical path |
| `impulse_world_n_s` | Authored impulse, expressed in world |
| `application_point_self_m` | Authored point, expressed in target self frame |
| `lever_arm_world_m` | Current staged rotation applied to the self point |
| `application_point_world_m` | Current staged origin plus lever arm |
| `angular_impulse_world_n_m_s` | World lever arm cross world impulse |
| `linear_velocity_before_world_m_per_s`, `linear_velocity_after_world_m_per_s` | Incoming and resulting staged linear velocity |
| `angular_velocity_before_world_rad_per_s`, `angular_velocity_after_world_rad_per_s` | Incoming and resulting staged angular velocity |

Every vector is a three-element finite JSON number array. Source offsets are UTF-8 byte offsets and source revisions are hashes of exact source bytes. These explicit world/self fields **are not re-expressed** when an inspection asks to express the ordinary top-level pose/velocity in another frame. They do not require a new inspection field group or host operation.

Apply existing source, event, object, work, output-record, serialized-byte, value-entry, deadline and cancellation limits. Charge the nested empty impulse projection and every retained application record **before** snapshot duplication/allocation, including repeated sample output. For arbitrary-time batch planning, compute a conservative complete-history maximum: visit authored boundaries in order, group full record weights by target, replace only each touched target's retained group, retain untouched groups and take the maximum total. Record weights use the same logical nested-entry accounting as the emitted shape, including source/target identities and all vector entries. Before-time-zero construction charges empty projections only, not unexposed future applications. This bounds all actual sampled record lists without silently shortening them.

For this exact record shape, inherited logical-entry counting gives an empty impulse projection weight of `4`, and an application weight of `45 + len(target_element_id)` (object keys are not entries). The conservative sampling weight is therefore the unchanged legacy base plus `4 * object_count` plus the maximum retained application weight, omitting that last future-history term for before-time-zero construction.

Cooperative checks must occur during new event/record/bound iterations and serialization. A resource or cancellation failure produces an explicit bounded failure and preserves accepted source/run/artifact transaction state. Agent `max_result_items` limits top-level rows and does not substitute for nested-record accounting. The complete final successful response, including implementation, progress and cursors, must satisfy the selected request's lowered `max_value_entries` before publication, with the existing atomic rollback behavior.

## 6. Typed failures and source-local diagnostics

Reuse existing diagnostic codes and `ontokin.diagnostic/0.2`; no new diagnostic schema is implied by a new language profile. Unit mismatch is `OKL-E-UNIT`, nonobject/wrong expression kind is `OKL-E-TYPE`, unknown name/key is `OKL-E-NAME`, wrong world/self binding is `OKL-E-FRAME`, unsupported binding/import edge is `OKL-E-CAPABILITY-UNSUPPORTED`, disallowed current mode is `OKL-E-MOTION-MODE`, invalid mass/body domain is `OKL-E-PHYSICAL-DOMAIN`, nonfinite arithmetic is `OKL-E-NUMERIC`, and exceeded work/output bounds use `OKL-E-RESOURCE`. Existing export/protocol-specific error families remain unchanged.

For an application-time failure on a known object, report that object's occurrence identity, the exact impulse statement span, the **actual failed application boundary time**, `side="after"`, and `details.sequence_index`. This is a failed after-side transaction; its before state remains valid. A numeric event error uses category `numerical_failure`; it must not be wrapped as an anonymous model-span error at the requested sample endpoint. Diagnostic details describe the failed operation/quantity without emitting nonfinite JSON values. Static type/frame errors may identify the offending payload expression span more narrowly. The corpus separates compile-time and event-admission failures and does not assert identical incidental error messages.

Use stable rule IDs `IMP-001` for new syntax/types/frames/import admission, `IMP-002` for free-sphere admission and momentum/numeric updates, `IMP-003` for ordered atomic boundaries and clock sides, `IMP-004` for projections/budgets, and `IMP-005` for explicit Agent/GLB delivery inheritance. A diagnostic may include multiple applicable rules and inherited rule IDs. Do not repurpose the existing numeric rule ID `LANG-004` as this document's identifier.

## 7. Agent, catalog and delivery inheritance

Agent/0.4 explicitly inherits [OK-AGENT-003](../engineering/OK-AGENT-003-native-surface-program-workflows.md), including immutable accepted-once revisions, source-safe occurrence patches, validated run provenance, operation retry/idempotence, transaction/cancellation semantics and signed geometry cursors. Select it explicitly with `ProgramAgentService(store, protocol="ontokin.agent/0.4")` or the corresponding explicit CLI binding. Its separate database must reject explicit wrong-version stores before mutation. It may read its own previously accepted revisions; it never relabels a previous profile's store.

There is no `apply_impulse` host RPC. Create/patch `.ok`, validate, evaluate and inspect the accepted revision through existing operations. Catalog data must advertise this source event, its units/frames and free-sphere restriction while continuing to mark finite forces, continuous torques, actuators, contacts and broader body models unavailable.

Native mesh inspection remains the inherited geometry capability: nested `geometry.surface.profile` and `surface.mesh_page` result `profile` stay **`surface-0.1`**, with their existing public schemas and geometry fingerprint meaning. That field does not claim the entry program uses source `0.3`. Agent/0.4 compiles the entry under `impulse-0.1`, and its private signed cursor context additionally binds `entry_profile="impulse-0.1"` along with selected protocol, implementation, revision, occurrence and inherited geometry context. Do not add that field to the public inherited page object or reinterpret old fingerprints. Imported declaration projections retain each unit's actual declared profile.

GLB/0.4 retains the adopted native geometry, winding, flat normals, distinct PBR region identities, one local visual placement, program/source hashes, revision metadata and independently checked world animation of GLB/0.3. Match the explicit target to the explicit source profile. Identify rigid recorded animation as recorded; no destination-side live impulse simulation is implied. Physical assumption metadata must disclose authored instantaneous momentum changes and the absence of continuous external forces/torques beyond the inherited uniform gravity, rather than declaring all external torque absent.

Position and orientation remain continuous at an impulse; their derivatives may jump. Preserve every exact source impulse time as a required bake boundary, including zero, duration and same-sequence applications. Inherit existing float32 time-collapse, local-coordinate, translation, rotation and resource rejection policies. A rounded or regular sample schedule cannot erase the boundary.

Each GLB/0.4 boundary metadata record additionally contains `impulse_states_after`, a map from every canonical object path to that object's exact after-side `impulses` projection, including empty projections. Compare it against the source-driven evaluated boundary state during independent delivery verification. Existing boundary fields retain their meaning; older GLB targets do not acquire this field. Charge complete nested impulse records both in boundary sampling and in serialized metadata budgets before publication. The artifact therefore identifies the source influences behind its recorded trajectory without implying a destination-side impulse engine.

For conservative spin sampling, add `sum(norm(q) * norm(J) / I)` over **every authored impulse** to the existing whole-scene angular-speed bound. Rotation preserves the lever-arm norm; the triangle inequality covers unknown application orientation and ordered accumulation. Use the bound in both baking and independent binary animation verification, with cancellation checks in the new loop. A nonfinite bound or resulting keyframe/work demand above the existing limits is an explicit export failure. The bound may overestimate; it must not be replaced by angular speeds inferred only from regular samples, which can miss full turns. The high-spin fixture requests low FPS intentionally and requires actual additional samples and an independent analytic orientation check.

## 8. Predetermined acceptance and release rule

[acceptance.json](impulse-v0.1/acceptance.json) fixes complete source closures, analytic samples, boundary sides, diagnostic codes, generated occurrence repairs and operational checks. Its original **proposed-unexecuted** labels preserve the preimplementation authorship record; the expectations are adopted by [adoption.json](impulse-v0.1/adoption.json), and actual execution evidence must remain separate. All source hashes and program revisions refer to the exact listed bytes, including rejected candidates. Transport manifests resolve only inside this folder; the inherited surface library is included as an exact-byte fixture copy with the original hash and origin recorded.

| Gate | Required proof |
| --- | --- |
| I01 | Native source parsing, units, frames, contextual spelling, exact occurrence lowering and compatible pinned imports |
| I02 | COM linear response, zero angular response and momentum/energy expectations |
| I03 | Off-center and rotated-frame response with pose continuity and independent angular oracle |
| I04 | Gravity continuation and release at simultaneous natural completion, preserving full incoming derivatives |
| I05 | Zero, repeated and opposite impulses; cumulative counts and latest-boundary state; separate origin/anchor |
| I06 | Exact zero/duration/binary64 event boundaries and transactional written-order failures |
| I07 | Generated-part mass and radius source repair; stable siblings, library bytes and visual geometry/materials |
| I08 | Unit/frame/type/mode/domain/numerical negatives, finite cancellation and exposed intermediate overflow |
| I09 | Actual Agent/0.4 accepted-revision workflow, retries, rejected repairs, isolation and geometry-page inheritance |
| I10 | Complete nested output accounting, conservative sample planning, cancellation and rollback under lowered budgets |
| I11 | Actual source-to-GLB/0.4 delivery, dense high-spin animation, independent Khronos/Three.js decode and same-artifact browser evidence |
| I12 | All prior core, Agent, construction, native surface and destination gates, all extant regression IDs and required CI roles still pass |

A release must retain current implementation/source/artifact identities, actual executed test IDs and results, source-driven Agent repair records, independent numerical destination checks, browser captures and identified CI, following [the native release evidence discipline](../engineering/OK-ENG-004-native-surface-release-conformance.md). Historical evidence cannot certify changed runtime bytes. New-profile success alone cannot close the full programming-language goal.

**Explicitly unimplemented by this profile:** finite force intervals, continuous torques, actuators/controllers, contacts/collision detection or response, friction, restitution, moving/static contact planes, sphere-sphere interaction, nonspherical inertia, compound rigid-body aggregation, deformable matter, solver selection, engine-side live simulation and performance or authoring-benefit benchmarks. Existing static and prescribed modes remain available with their established meanings; this proposal does not redefine them.
