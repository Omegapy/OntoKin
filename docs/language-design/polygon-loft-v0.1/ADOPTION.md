# Matched-topology polygon ring lofts

**Decision:** OK-LANG-010/0.1.0 and OK-AGENT-010/0.1.0, October 30, 2026.

**State:** Selected experimental C077 development contract. Publish this decision and freeze independently specified acceptance inputs before runtime implementation. Implementation, execution, integration and release acceptance are separate outcomes.

## Binding and purpose

Explicit source `ontokin "0.10";` selects `polygon-loft-0.1`, Agent `ontokin.agent/0.10` and recorded destination `ontokin.glb/0.10`. Editable matched polygon sections form tapered housings, chamfered profiles and hollow ducts. This extends the [C076 ring contract](../polygon-holes-v0.1/ADOPTION.md) and advances the complete [GOAL](../../../GOAL.md).

Earlier source, Agent, destination and default bindings retain their meanings. Earlier declaring modules cannot import .10 modules. A .10 program can import compatible earlier pinned modules under their declared semantics. Existing `loft`, `extrude` and `extrude_rings` constructors retain their own geometry rules. `placed` accepts one unplaced native geometry, including the new ring loft; nested placement remains invalid. These visual surfaces add no mass, inertia, collision shape, attachment, following relationship or motion authority.

## Types, correspondence and finite domain

| Constructor | Type and meaning |
| --- | --- |
| `polygon_section(order, station, rings)` | `Int`, `Length`, `Keyed<PolygonRing>` produce immutable `PolygonSection`. Its keyed entry supplies a stable section key. Rings retain the .9 typed ring/vertex constructors. |
| `loft_rings(sections, palette, bottom_region, top_region)` | `Keyed<PolygonSection>`, `Keyed<SurfaceMaterial>`, `String`, `String` produce `Geometry` between the first and last authored stations. |

A loft has 2 through 8 sections. Section keys and orders are unique; orders are integers in [0,65535]. Sort sections by increasing explicit order. Each section lies in local XY at its finite local Z station in [0,100] meters. Stations strictly increase in that order. The exact rational difference of their canonical binary64 values must be at least the exact rational value of canonical binary64 `0.001` meters. No rounded-subtraction or ULP allowance changes this rule. Thus 0 to 0.001 is an accepted boundary; decimal-looking differences at other stations depend on their actual represented values.

Every section has exactly one counterclockwise outer ring and zero through eight clockwise holes. It has 3 through 64 vertices across all its rings, with at least three in each ring. Across all sections there are at most 256 authored vertices. Coordinates are finite canonical binary64 values in [-100,100] meters. Every section independently satisfies all .9 simple-ring, winding, distinct-point, no-adjacent-collinearity, strict-containment and non-touching rules.

Every section must retain exactly the first section's ring keys, roles and integer orders, and each ring's vertex keys and integer orders. Ring and vertex orders remain in [0,65535]. Coordinates and outgoing-edge material regions may vary. Matching uses these explicit identities, never declaration position, nearest points, cyclic alignment or resampling. Source vertex identity is `(section key, ring key, vertex key)` within the occurrence. No ring creation/removal, automatic topology matching or point insertion is implied. Reordered declarations preserve geometry when keys, orders and values are unchanged; exact source revisions still change.

The palette contains 1 through 16 valid existing PBR materials. Both cap names and every section's outgoing-edge region must name a palette key. Terminal-section regions are validated although they emit no outgoing strip. An unused valid material emits no primitive. Existing object, source, value, sample, artifact and aggregate mesh limits remain, including 250,000 mesh vertices.

## Authoritative triangular surface

The actual deterministic triangles define the surface. The contract does **not** promise exact polygon slices obtained by linearly interpolating corresponding section vertices. For a noncoplanar edge quad those two constructions differ. No smooth surface or automatic bevel is inferred.

Flatten section vertices in sorted ring order and sorted vertex order. Between each consecutive lower/upper section pair, take every directed ring edge a-to-b and emit `(a_lower,b_lower,a_upper)` followed by `(b_lower,b_upper,a_upper)`. This fixes the diagonal from b_lower to a_upper. Both triangles use the lower section's outgoing-edge region at a. Each has its own cross-product unit normal; no averaged or horizontal wall normal substitutes for it.

Triangulate the first and last material domains independently using the exact deterministic .9 cap algorithm. The endpoints may need different diagonals. Emit the first cap with reversed winding, the last cap with positive winding, then strips in section/ring/vertex order. Intermediate sections have no caps. Each emitted triangle has three distinct flat-shaded corners. Group triangles by sorted used material key while preserving emission order within a material.

Let S be section count, N the matched vertex count per section, and H the hole count per section:

| Quantity | Required value |
| --- | ---: |
| Triangles on each endpoint cap | `N + 2H - 2` |
| Strip triangles | `2(S - 1)N` |
| Complete triangles T | `2SN + 4H - 4` |
| Flat mesh corners | `3T` |
| Unique authored positions | `SN` |

The simultaneous bounds imply at most 540 triangles and 1,620 flat corners per ring loft. Area is the sum of actual triangle areas. Volume is the positive signed sum `sum(dot(a,cross(b,c)))/6`; homothetic planar-wall frusta additionally admit independent analytic formulas. General linear-slice frustum formulas cannot redefine a noncoplanar triangular surface.

## Complete source and delivered admission

Valid sections alone are insufficient. Before accepting geometry, establish over exact rational canonical binary64 coordinates that every identity has one position, distinct identities have distinct positions, each triangle has three distinct identities and nonzero area, every directed mesh edge occurs exactly once with exactly one opposite edge, and any two triangles meet only at their explicitly shared source vertex or edge. Duplicate faces, nonadjacent touches, crossings, pinches and folded overlap are rejected. The closed oriented mesh must have positive exact signed volume. Endpoint cap coverage and winding retain the .9 exact rules. Invalid input is rejected without clipping, reversing, welding or repair.

Copy the complete bounded section/ring/vertex/material structure into immutable leaves before later work-check callbacks can mutate host-owned input. Every bounded geometric loop, exact intersection schedule, cap construction, emission, inspection, encoding and supplied-byte check consumes the same authorized request counter and original deadline. Cancellation and callback exceptions retain their identities.

After rigid local placement and binary32 conversion, validate the **actual delivered positions** again: identity consistency and separation, nonzero oriented faces, closed opposite edge incidence, exact shared-simplex intersections, positive volume and the existing geometric error bound. Source-valid narrow openings, close stations or nonadjacent surfaces that collapse or touch in delivery fail export explicitly. Recheck all positions in three dimensions; rounding after rotation need not preserve a cap plane. Supplied normals must agree with outward face winding and source-quantized values. Regional materials and recorded carrier pose must agree with source. Local geometry tolerance remains 0.00001 meters and recorded-motion tolerances remain unchanged.

## Diagnostics and inspection

The new family is `OKL-E-RING-LOFT-SECTION`, `-ORDER`, `-STATION`, `-CORRESPONDENCE`, `-TOPOLOGY`, `-REGION` and `-NUMERIC`. Inherited ring, point, winding, containment, type, unit, material, placement and resource diagnostics retain their original names and meanings. Include relevant section/ring/vertex identity and source span when available. A wrong field type remains a type error; semantic count, matching and surface errors do not become generic internal errors.

The summary schema is `ontokin.polygon-loft-summary/0.1`, profile `polygon-loft-0.1`, family `polygon_loft`, with `surface_rule: "fixed-diagonal-triangles"`. It exposes sorted sections (`key`, `order`, `station_m`, sorted rings and keyed vertices), section/ring/hole counts, vertices per section and total authored vertices, station range, palette and used regions, cap/strip/total triangle counts, flat corner count, and rigid local placement. Physical participation is `none`; motion authority is `carrier_evaluated_world_pose`. Derived triangles are bounded inspection data, never editable source identities.

Existing elliptical-loft, simple-extrusion and hole-extrusion summaries retain their own schemas and profile meanings inside .10 programs. Bounded mesh pages identify the actual .10 program profile and remain bound to revision, query, geometry, implementation and protocol. A page contains at most the existing 256-triangle maximum.

## Agent lifecycle and execution limits

`RingLoftAgentService` selects a separate `ring-loft-program-agent.sqlite3` store with schema `ontokin.ring-loft-program-agent-store/0.1`. Explicit Agent/0.10 provides all twelve existing budgeted operations: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. Preserve exact UTF-8 patch preconditions, nominal occurrence continuity, immutable accepted revisions, failed-edit rollback, revision-bound cursors, current trusted host authorization, cumulative work, original deadlines, cancellation, durable identical retries, changed-payload rejection and atomic artifact publication. Source edits remain the only mutation path.

Omitted source requests remain **100,000 operations / 30,000 ms**, even on a larger host. Explicit entry requests may increase those limits within current trusted host ceilings; caller caps only reduce source requests. No stage resets the ledger or deadline. Modeled animation duration is separate from computation time. The maximum-count acceptance examples explicitly request **2,000,000 operations / 80,000 ms**, with matching separately supplied host ceilings. This is the frozen authorized request; complete execution of the larger triangle-pair schedule must still be demonstrated without weakening its accounting. Larger authorized settings never retroactively pass an older fixed-budget gate.

## Predetermined evidence and exclusions

Freeze independent positive, boundary, invalid, composition and exact-repair inputs before runtime. Include extrusion-equivalent constant sections; solid and hollow analytic frusta; a three-section chamfer; concavity and multiple holes; material transitions; declaration reordering; count/numeric/matching boundaries; valid endpoints with crossing, pinching or folded strips; binary32 delivery failures; and scoped repair preserving an unchanged sibling and pinned library.

A specific authority control uses lower square keys at `(-1,-1),(1,-1),(1,1),(-1,1)` and upper coordinates rotated +90 degrees at station 1. The adopted triangles form a volume-4, area-16 rectangular box although linearly interpolated corresponding vertices would bound a different intermediate slice. A -90-degree correspondence instead produces an invalid pinched triangular surface despite valid endpoint rings. Swapped disjoint hole identities between endpoints must also be rejected.

Require independent supplied-byte checks of complete cap coverage, strip triangles, shared edges, surface intersections, normals, materials, volume and recorded motion. The acceptance oracle must not import the product triangulator or intersection predicate. Execute the actual Agent repair/evaluate/export/retrieval and failure/retry cases against its published schemas. Fresh native and pinned Three.js/Chromium playback, actual capture review, applicable complete inherited tests, independent review and verified resulting-main checks are required for development integration under [OK-ENG-009](../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md).

Blind cavities, branching ducts, arbitrary bevel offsets, Boolean operations, automatic mass/inertia/collision, skin deformation and live destination physics are excluded. Recorded GLB and browser success does not establish Unreal import. Original28 remains 24/28 failed with P11/P16/P23/L03 unresolved until separately resolved under its original settings. Preserve complete reach, M1 rejection, held C035 including adverse timing, C057, comparison/passive authority, missing compatibility/external roles, C059's unestablished storage cause, historical LFS migration and all remaining GOAL domains. This decision is experimental development, not release acceptance or full-product completion.
