# Bounded static-tray delivery proposal

**Identity:** `OK-PROP-C197-TRAY-001/0.1.0`  
**Status:** proposed; not adopted or implemented  
**Date:** November 10, 2026, America/Denver  
**Basis:** [C197 feasibility map](FEASIBILITY.md) at verified main
`6cbcf9c8c136659def1aac94829330cb81872511`

## Unsupported requirement and intended scope

C197 requires both reusable OntoKin source and direct Python to construct the
same equipment-tray family through one pinned backend, with inspectable source,
stable identities and independent delivery measurements. No inspected existing
path provides that mapping. The ordinary language can describe the boxes; the
qualified shared Blender path supports a different, fixed carriage assembly.

Create a separately versioned, explicitly selected **static box-assembly delivery
adapter** for this one tray family. Reuse the adopted core/construction language
and its compiler. Do not add a second tray-specific source parser, broaden the
C193 namespace, change standard export defaults, or build a general importer.
An experimental destination/profile name and its exact version must be frozen
in the later contract; this proposal does not reserve or activate a selector.

The first supported family is two independently identified trays, each with a
base, four walls and a named payload measurement proxy. One shared definition
supplies derived dimensions. A later repair changes only the left payload/cavity
selection while preserving wall thickness, clearance and the complete right
instance. Later reuse adds a supported selection without overwriting earlier
accepted source/output closures. General solids, arbitrary meshes, textures,
animation, dynamic bodies, collision, joints, deformation and live physics are
outside this proposed adapter.

## Proposed mapping

1. **Compile existing source.** Resolve the exact `construction-0.1` source and
   pinned dependency closure through the existing compiler. Admit only the
   finite tray family, supported positive box dimensions, constant poses and
   permitted ownership/following relationships. Reject unsupported geometry,
   motion, body semantics or relationships before starting Blender. The source
   remains authoritative; a mesh or caller-supplied dimension annotation cannot
   replace it.
2. **Lower to one bounded construction record.** Record instance/part identity,
   separate ownership and frame relationships, full box extents, resolved rigid
   transforms, role and fixed material selection. Preserve exact source and
   dependency hashes separately from geometry. The direct-Python route supplies
   the same canonical construction record under the same schema and checks.
   Both routes must call the same constructor with identical settings. This
   newly specified mapping is the missing work; no implementation is implied.
3. **Make frame conversion explicit.** Preserve centered full side lengths and
   convert declared units once. A candidate proper rotation from OntoKin's
   right-handed Y-up coordinates into Blender's Z-up coordinates is
   `(x, y, z) -> (x, -z, y)`. Existing receiving code uses this convention, but
   the new construction/export round trip needs its own frozen proof and
   measurements. Do not rely on Blender defaults or apply the rotation twice.
4. **Use one pinned constructor/exporter.** A separate finite worker creates the
   admitted boxes with exact instance/part identifiers and no solver. Pin the
   Blender executable, worker bytes, settings, axis/unit handling, glTF exporter
   and required environment. Both routes must use that worker. Distinct stores
   and output locations prevent accidental replacement of C193 or earlier
   accepted outputs.
5. **Preserve delivery identity.** Define the exact source-to-node identity rule,
   hierarchy or flattening rule, treatment of measurement proxies and supported
   metadata. Freeze canonical numeric serialization and the regeneration rule.
   Any permitted volatile fields must be listed before exports; a later mismatch
   cannot create a new exemption. Keep accepted source, dependencies, receipts
   and output bytes together.

## Independent validation required before admission

The checker must read the actual GLB buffers, triangle/accessor geometry, node
transforms and mapped identities. It measures cavity width/depth, wall/base
thickness, payload clearances, placement, and the right sibling's complete
geometry/identity closure. It must not accept source annotations as measurements
or derive expected dimensions by calling the producer's lowering code.

Freeze positive, boundary, negative, composition and localized-edit controls.
Include unit/frame mistakes, duplicate or missing identities, unsupported
relationships and accidental overlap of corner material. At least the two
C197-required controls must alter real retained output: inadequate payload
clearance, and changed or missing right-tray geometry/identity. The same reader
must reject both for the expected reasons. Reopen the actual accepted output
through the named receiving implementation and check the static geometry there.

Bind the original editable source, complete dependency closure, constructor,
backend and checker bytes. Regenerate each baseline in a clean location and
apply the predetermined equality rule. A staged candidate must preserve the
previously accepted source/output closure on failure. Explicit operation limits,
finite outer deadlines, cancellation and process cleanup remain mandatory.
Ordinary limits stay 100,000 operations and 30,000 ms; a new workload requiring
higher limits needs an explicit, separately reviewed host allowance before it
runs. No old gate may be widened.

## Work and effort estimate

These are planning estimates based on the identified components, not measured
implementation time, promised elapsed completion, model tokens or provider cost.
One engineering day means roughly six focused engineering hours. Independent
review may overlap implementation, so the summed work is not a calendar forecast.

| Work package | Estimated focused engineering effort |
| --- | ---: |
| Freeze finite mapping, source restrictions, identity rules and controls | 1–2 days |
| Implement compiler-to-record lowering and the shared static Blender worker | 1.5–3 days |
| Build the independent delivered-geometry reader and corruption controls | 1.5–3 days |
| Qualify failure lifecycle, receiving, regeneration, evidence and integration | 1–2 days |
| **Total estimated work** | **5–10 engineering days** |

The estimate assumes the existing compiler exposes the required box/pose state,
a usable pinned Blender build is available on Linux, and no language semantics,
general mesh support, physical solver or new production backend is needed.
Dependency availability and exact backend bytes must be checked in the later
preparation. If implementation reveals additional representation or semantic
requirements, stop and revise the versioned proposal before further execution.

## Later go/no-go decision

Proceed to a separate bounded implementation only after independent review and
an explicit versioned mapping decision. Freeze the precise public geometry,
dimensions/ranges, identities, tolerances, sources, backend, checker, comparison
rules and attempt allowances before native work. Record any preparation trials
separately; they cannot count as the original C197 admission attempt, which
stopped before exports.

Return to tray admission only after both routes use the same qualified constructor
and the complete independent controls pass. The later admission must retain
the original bound of one baseline export and one clean regeneration per route,
four native exports total including failures, with no automatic retry. Its
author exercise is another separately frozen task. Provider telemetry must be
reported unavailable if it is not observed; one passing family cannot establish
comparative advantage.

Stop or narrow the proposed investment if preserving source meaning, equal
backend construction, independent measurements or bounded work requires a
general backend. The proposal preserves the entire [GOAL](../../../GOAL.md),
the inherited **FAILED** legacy driver/tail, **4,239** distinct passing methods,
**thirteen NOT RUN** torque-read methods, and every other unresolved release,
compatibility and external-role requirement.
