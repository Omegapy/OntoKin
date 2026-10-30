# Source-authored polygon extrusions

**Decision:** OK-LANG-008/0.1.0 and OK-AGENT-008/0.1.0, October 30, 2026.

**State:** Selected experimental C075 development contract. This decision and its frozen examples precede implementation. Actual implementation, checks and integration are recorded separately.

## Binding and scope

Explicit source `ontokin "0.8";` selects `polygon-extrusion-0.1`, Agent `ontokin.agent/0.8` and recorded destination `ontokin.glb/0.8`. This profile adds rigid visual polygon extrusions to the features of the [source-budget contract](../execution-budgets-v0.1/ADOPTION-C073.md) and [Agent budget lifecycle](../agent-v0.7/ADOPTION.md). Earlier source, Agent, destination and default selections retain their meanings. Earlier declaring modules cannot import a newer source contract. The new profile can reuse compatible earlier pinned modules through their existing declared semantics.

An extrusion describes a closed plate, bracket or housing exterior from editable source. It adds no mass, inertia, collision shape, attachment or motion authority. An object's explicit `physical` declaration and evaluated carrier pose retain authority. Holes, intersecting outlines, bevels, curved edges, general Boolean operations, skin deformation and live destination physics are outside this increment. This advances the [full product goal](../../../GOAL.md); it does not complete the product or any pending reach gate.

## Types and constructors

| Constructor | Type and meaning |
| --- | --- |
| `planar_point(x, y)` | Two `Length` arguments produce `PlanarPoint` in the carrier's local XY plane. Coordinates are canonical SI meters. |
| `polygon_vertex(order, point, side_region)` | `Int`, `PlanarPoint`, `String` produce `PolygonVertex`. The enclosing keyed value supplies its stable authored key. `order` determines geometric traversal; `side_region` names the material for the edge from this vertex to the next. |
| `extrude(vertices, palette, depth, bottom_region, top_region)` | `Keyed<PolygonVertex>`, `Keyed<SurfaceMaterial>`, `Length`, `String`, `String` produce `Geometry`. It spans local z=0 through z=depth, with closed caps. |
| `placed(geometry, pose)` | The existing rigid visual-placement constructor accepts one unplaced extrusion in source .8. The pose references its own `self.frame`. Nested placement is rejected. |

`SurfaceMaterial`, `surface_material`, exact source spans, nominal types, functions, class parameters, inheritance, pinned modules and keyed generation retain their existing rules. Derived triangle/corner indices are inspection identities, not writable source keys. An agent edits actual source bytes; one vertex coordinate can change without renaming that vertex, its object or siblings.

## Finite geometry and deterministic topology

An outline has 3 through 64 vertices. Vertex keys use the existing stable keyed-value syntax. Orders are unique integers from 0 through 65,535; gaps are allowed. Sort by increasing order, independently of declaration order and key spelling. The closing edge is implicit; do not repeat the first point.

Each coordinate is finite binary64 and lies within [-100,100] meters. Depth is finite in [0.001,100] meters, using the canonical binary64 representation of the written 0.001-meter lower bound. The palette has 1 through 16 valid existing PBR materials; every side and cap region must resolve to a palette key. Unused valid palette entries are permitted and emit no triangle primitive.

The ordered outline must be simple and counterclockwise as viewed from +Z. Reject duplicate positions, zero-length edges, adjacent collinearity or backtracking, nonadjacent intersections, touching vertices or edges, overlapping edges, and zero signed area. Positive and negative zero are equal for these predicates. Orientation, intersection and ear-admission decisions use exact rational values of the canonical binary64 coordinates, without an epsilon that could admit crossings. Invalid geometry is rejected; it is never silently repaired or reversed.

Use deterministic ear clipping: repeatedly scan the retained order from its first vertex and remove the first strictly convex ear that contains no other retained vertex on or inside the closed triangle. Preserve the traversal order of each cap triangle. Bottom cap triangles reverse that winding; top cap triangles retain it. After the bottom and top cap triangles, emit side triangles in ordered-edge sequence as `(a0,b0,a1)` and `(b0,b1,a1)`, where 0 and 1 name bottom and top. A cap has n-2 triangles, sides have 2n, and the full extrusion has 4n-4 triangles. Flat shading duplicates all triangle corners, totaling 12n-12 vertices. Region index groups use sorted material keys and preserve each region's native triangle order.

Triangle normals must be finite outward unit vectors. Failure to represent a nonzero triangle or a valid unit normal is an explicit numeric failure. Aggregate limits remain the existing 250,000 mesh vertices, object/source/value/result/sample/artifact caps and inherited numerical bounds. Validation, exact predicates, triangulation, mesh inspection, encoding and supplied-byte readback consume the same authorized request budget; each bounded vertex, edge-pair, ear-candidate, retained-vertex and emitted-triangle loop has a cooperative work checkpoint. No stage resets the original deadline or counter.

Declaration reordering preserves local positions, normals and region membership. It changes exact source revisions and provenance, so byte-identical whole GLBs are not promised across different source text. Renaming a key or changing an order is an explicit source change; derived topology can change after a geometry edit.

## Diagnostics and delivery

The new diagnostic family is `OKL-E-EXTRUSION-POINT`, `-VERTEX`, `-ORDER`, `-DEPTH`, `-TOPOLOGY`, `-WINDING`, `-REGION` and `-NUMERIC`. Existing type, keyed-value, material, placement and resource diagnostics retain their meanings. Failures identify the authored occurrence and source span when available; key/order/region details make the failing outline repairable.

The .8 exporter uses actual source-generated positions, flat normals, regional PBR primitives and rigid placement. Recorded animation follows the evaluated world carrier exactly once. Existing local geometry tolerance of 0.00001 meters and recorded motion tolerances remain unchanged. Binary32 conversion must retain nonzero triangles, outward winding, valid normals and the existing geometric error bound. A binary64-valid outline that collapses in the destination is rejected at delivery; metadata cannot establish successful geometry or authorize a later request.

The explicit Agent service uses a separate .8 database and all twelve C074 operations. It retains exact file-level source-edit scopes, immutable revision checks, failed-candidate rollback, nominal occurrence continuity, bounded cursor pages, current-policy reauthorization, cancellation, identical durable retries and transactional artifact publication. Polygon summaries expose the actual profile/family, ordered vertex keys/orders/points, depth, cap regions, used region counts, rigid placement and no physical participation. Mesh pages identify the actual program profile; loft summaries keep their original meanings. A source request cannot supply host policy.

Source omissions retain 100,000 operations and 30,000 ms, including on a larger host. The source may explicitly request more within host ceilings, and caller caps can only reduce the request. Animation duration is a separate value. CLI and Python defaults remain earlier bindings; .8 is explicitly selected.

## Predetermined evidence

The [frozen examples and expected results](../../../examples/polygon-extrusions/acceptance-freeze.json) identify positive, boundary, invalid, reorder, edit and reuse cases before implementation. Independent checks use analytic area, volume, surface area, triangle counts, oriented edge incidence and decoded PBR values rather than reproducing the production triangulator. A rectangular plate has area 2 m2, depth 0.5 m, volume 1 m3 and 12 triangles. The concave L bracket has area 5 m2, depth 0.25 m, volume 1.25 m3 and 20 triangles. Its single inner-corner edit yields area 5.5 m2 and volume 1.375 m3. The sibling and pinned library stay unchanged.

Required execution includes actual source compilation and Agent discovery/create/inspect/mesh-page/edit rejection/edit repair/evaluate/export/chunk retrieval/retry, schema validation, independent decoded geometry and recorded poses, browser playback and actual image review. The applicable complete inherited cohort, fixed original expectations, local validation roles, independent code review and resulting-main checks are required for development integration. All failed attempts are retained. Original28 remains 24/28 failed; complete reach, other external/compatibility roles, historical LFS migration and all remaining product domains stay open.
