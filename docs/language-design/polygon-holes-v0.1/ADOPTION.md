# Source-authored holes in polygon extrusions

**Decision:** OK-LANG-009/0.1.0 and OK-AGENT-009/0.1.0, October 30, 2026.

**State:** Selected experimental C076 development contract. This decision and the independently specified examples are frozen before runtime implementation. Execution and integration require separate evidence.

## Binding and purpose

Explicit source `ontokin "0.9";` selects `polygon-holes-0.1`, Agent `ontokin.agent/0.9` and recorded destination `ontokin.glb/0.9`. The profile extends the [C075 polygon contract](../polygon-extrusion-v0.1/ADOPTION.md) with source-authored through-holes. Plates with bolt openings, slotted brackets and hollow housing cross-sections remain editable, reusable source. This advances the complete [GOAL](../../../GOAL.md); it does not redefine that goal as a mesh exporter.

Earlier source, Agent, destination and default bindings retain their meanings. Earlier declaring modules cannot import .9 modules. A .9 program can import compatible earlier pinned modules under their declared semantics. The existing `extrude` constructor remains available in .9 with its .8 simple-outline rules; it does not acquire implicit holes. `placed` accepts a single unplaced loft, simple extrusion or ring extrusion in .9. Nested placement remains invalid.

The new geometry is visual. It adds no mass, inertia, collision shape, physical attachment, following relationship or motion authority. Source physical declarations and the evaluated carrier world pose retain authority. Self-intersecting rings, bevels, curved edges, arbitrary Boolean operations, skin deformation, automatic physical properties and live destination physics are excluded.

## Types and constructors

| Constructor | Type and meaning |
| --- | --- |
| `planar_point(x, y)` | Existing two-`Length` constructor of a local XY `PlanarPoint`. |
| `polygon_vertex(order, point, side_region)` | Existing `Int`, `PlanarPoint`, `String` constructor of `PolygonVertex`. Its keyed entry provides the stable vertex key; its region owns the edge from this vertex to the next in its ring. |
| `polygon_ring(order, role, vertices)` | `Int`, `String`, `Keyed<PolygonVertex>` produce an immutable `PolygonRing`. Its enclosing keyed entry supplies the stable ring key. `role` is exactly `"outer"` or `"hole"`. |
| `extrude_rings(rings, palette, depth, bottom_region, top_region)` | `Keyed<PolygonRing>`, `Keyed<SurfaceMaterial>`, `Length`, `String`, `String` produce a `Geometry` spanning local z=0 through z=depth. |

`PolygonRing` is an immutable keyed-value element in .9 declarations. Nested keyed values here are typed constructor arguments, not generic untyped containers. Existing nominal classes, functions, parameters, pinned modules, keyed generation, source spans and exact source edits continue to apply. A vertex identity is scoped by its ring; equal vertex keys in different rings are allowed. Derived cap triangles and mesh corners are inspection data, not writable source identities.

## Finite domain and topology

A ring extrusion has exactly one outer ring and zero through eight hole rings. Every ring has at least three vertices; all rings together have at most 64 vertices. Ring keys are unique within their keyed value, and vertex keys are unique within each ring. Ring orders are unique integers in [0,65535]. Vertex orders are unique integers in the same range within each ring. Gaps are valid. Sort rings by increasing ring order and each ring's vertices by increasing vertex order. The outer ring can have any order; its role, not its position or key spelling, identifies it.

Coordinates are finite canonical binary64 values in [-100,100] meters. Depth is finite in [0.001,100] meters, using the binary64 representation of the written 0.001-meter endpoint. The palette contains 1 through 16 valid existing PBR materials. Every outgoing wall and both caps name a palette key. An unused valid palette entry contributes no primitive.

The outer ring traverses counterclockwise as seen from +Z; hole rings traverse clockwise. A ring is simple, has nonzero signed area and distinct points, and has no zero edge, adjacent collinearity/backtracking, nonadjacent crossing, touching or overlapping edge. The closing edge is implicit: repeating the first point is invalid. Different rings cannot cross, touch, overlap or share a point. Every hole is strictly inside the outer ring, and every pair of holes is mutually exterior: nested holes are rejected. A hole in the exterior notch of a concave outer ring is outside and rejected.

Topology uses exact rational values of canonical binary64 coordinates. Positive and negative zero compare equally. Clearance means strict separation: no positive numeric epsilon silently permits a touch or rejects an otherwise representable gap. A source-valid very narrow gap may fail destination delivery. Invalid input is rejected, never silently reversed, merged, clipped, repaired or converted into an island.

## Deterministic construction

Flatten vertices by the sorted ring and vertex orders. Begin with all directed ring boundary edges in their authored winding. Consider each nonboundary pair of distinct flattened vertex indices in lexicographic order. A candidate internal diagonal is admissible only if no third vertex lies on it, it meets boundary edges only at its own incident endpoints, its exact midpoint is strictly inside the material domain, and it meets an already admitted diagonal only at a shared endpoint. The material domain is the strict interior of the outer ring excluding every closed hole. Use exact segment predicates and a winding-number containment test.

Admit candidates in that order until `n + 3h - 3` internal diagonals exist, where `n` is the total authored vertex count and `h` is the hole count. Sort neighbors counterclockwise using an exact half-plane/cross-product comparator. For a directed edge u-to-v, the next edge takes the neighbor immediately clockwise from u at v. Traverse the authored boundary directions and both directions of every internal diagonal. Require complete, unique material-halfedge coverage, exactly `n + 2h - 2` positive triangular faces and an exact sum of cap areas equal to outer area minus hole areas. An inability to establish these invariants is an explicit failure, not partial geometry.

Rotate each cap triangle cyclically to its smallest flattened index and sort the resulting index triples lexicographically. Emit all bottom cap triangles with reversed winding, all top cap triangles with positive winding, then the two wall triangles for each boundary edge in sorted ring/vertex order. For edge a-to-b, wall triangles are `(a0,b0,a1)` and `(b0,b1,a1)`, with normal `(dy/length,-dx/length,0)`. This points away from the material on both outer walls and hole walls. Each emitted triangle has three distinct flat-shaded corners. Group indices by sorted material key, preserving native triangle order within each group.

| Quantity | Required value |
| --- | --- |
| Triangles on each cap | `n + 2h - 2` |
| Wall triangles | `2n` |
| Complete triangles | `4n + 4h - 4` |
| Flat mesh corners | `12n + 12h - 12` |
| Material area A | outer area minus sum of hole areas |
| Volume | `A * depth` |
| Surface area | `2*A + depth*(outer perimeter + all hole perimeters)` |

All triangles must retain representable nonzero outward faces and finite unit normals. Existing aggregate limits, including 250,000 mesh vertices and the source/object/value/result/sample/artifact caps, remain. Validation, containment, candidate tests, neighbor ordering, face traversal, emission, inspection, encoding and supplied-byte readback consume the original authorized request counter and deadline. Every bounded geometric loop has cooperative work checks. Host inputs are copied into bounded immutable leaves before later callbacks can change their membership or coordinates. A failing or cancelling callback retains its exception identity.

Declaration reordering preserves geometry and material membership when keys, orders and values are unchanged. Exact source revisions and provenance change, so whole-GLB byte equality is not promised across changed source text. Coordinate or order edits may change derived triangulation without renaming surviving ring/vertex/object identities.

## Diagnostics, inspection and delivery

The new diagnostic family is `OKL-E-HOLES-RING`, `-VERTEX`, `-ORDER`, `-POINT`, `-DEPTH`, `-TOPOLOGY`, `-WINDING`, `-CONTAINMENT`, `-REGION` and `-NUMERIC`. Earlier type, unit, keyed-value, material, placement and resource errors retain their meanings. Diagnostics include source occurrence/span and relevant ring, vertex, order or region details when available.

The summary schema is `ontokin.polygon-holes-summary/0.1`, profile `polygon-holes-0.1`, family `polygon_holes`. It exposes sorted ring entries with `key`, `order`, `role` and sorted `vertices` (`key`, `order`, `point_m`, `side_region`); authored ring/hole/vertex counts; depth, cap/palette/used-region counts; actual triangle/corner counts; local visual placement; no physical participation; and carrier motion authority. Existing loft and simple-extrusion summaries retain their own schema meanings. Bounded triangle pages identify the actual .9 program profile and remain bound to the accepted revision and query. Full source edits remain the only mutation path.

The .9 exporter emits actual source-built caps, outside walls and hole walls, regional PBR primitives and one rigid local visual placement. Recorded motion uses the evaluated carrier world pose exactly once. The existing local geometric tolerance of 0.00001 meters and recorded motion tolerances remain unchanged. After placement and binary32 conversion, the delivered geometry must retain its distinct authored boundary vertices, nonzero outward faces, intended opening boundaries, nonoverlapping cap coverage and the existing error bounds. Collapsed or touching openings are delivery failures even when the source geometry is valid. Metadata cannot prove geometry or authorize a later request. No Unreal Engine import or live physics claim follows from GLB validation or browser playback.

## Agent lifecycle and execution limits

`HolesAgentService` selects a separate `holes-program-agent.sqlite3` durable store with schema `ontokin.holes-program-agent-store/0.1`. All twelve inherited operations preserve exact UTF-8 edit preconditions, immutable accepted revisions, failed-candidate rollback, nominal occurrence continuity, revision-bound cursors, current trusted host authorization, cumulative budgets, cancellation, identical durable retries, changed-payload refusal and atomic artifact publication. Schema validity alone is not workflow evidence.

Omitted execution requests remain **100,000 operations / 30,000 ms**, even when the host authorizes more. Explicit source requests may increase those limits within current trusted host ceilings; caller caps can only reduce the source request. No stage resets the ledger or deadline. Modeled animation duration remains a separate source value. Earlier Python and CLI defaults remain unchanged. Larger frozen geometry cases may explicitly request 400,000 operations and 80,000 ms without changing old fixed-budget gates.

## Predetermined evidence and integration

The [frozen examples](../../../examples/polygon-holes/acceptance-freeze.json) bind source and analytic expectations before implementation. They cover square and multiple openings, concave outer/inner rings, slots, cross-ring collinearity, ring/vertex declaration reordering, zero and maximum hole/vertex counts, finite numeric boundaries, invalid topology/containment/winding/roles/orders/materials/units, precision-related delivery rejection, reusable/generated composition and an exact one-instance repair with unchanged sibling and pinned library.

Independent supplied-byte checks establish volume, surface area, cap coverage without filled holes or overlapping triangles, directed boundary and closed-mesh edge incidence, outward inner walls, materials and recorded poses. Area or triangle centroids alone are insufficient. Checker adversaries must reject removed/miswound/overlapping/filling triangles and altered materials. Actual Agent discovery/create/inspect/page/edit rejection/repair/evaluate/export/retrieve/retry/reset/cancel and lower-current-policy cases are required, with schema validation. Fresh Three.js/native/browser playback and actual capture review, complete applicable inherited local tests, independent review, verified integration lease and resulting-main checks precede development integration under [OK-ENG-009](../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md).

Every failed preparation and execution remains evidence. Original28 stays 24/28 failed until independently resolved under its original settings; P11/P16/P23/L03, complete reach, compatibility/external roles, C059's unestablished storage cause, historical LFS migration and every remaining GOAL domain remain open. This contract is a development decision, not release acceptance or a promise that future execution will pass.
