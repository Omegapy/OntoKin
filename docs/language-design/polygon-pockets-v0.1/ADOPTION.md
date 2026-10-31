# Source-authored blind polygon pockets

**Decision:** OK-LANG-012/0.1.0 and OK-AGENT-012/0.1.0, October 30, 2026.

**State:** Selected experimental C079 development contract. Publish this decision and the independently authored source-input freeze before runtime implementation. Adoption, implementation, execution, integration and release acceptance remain separate outcomes.

## Purpose and explicit bindings

Source `ontokin "0.12";` selects `polygon-pockets-0.1`, explicit Agent `ontokin.agent/0.12` and recorded destination `ontokin.glb/0.12`. The new geometry is a constant exterior XY outline extruded from z=0 to an authored height, with zero through eight keyed blind pockets. Every pocket opens at the common top and ends at its own interior floor. This supports editable trays, recessed panels and open housings while preserving the complete [GOAL](../../../GOAL.md).

Earlier source, Agent, destination, constructors, diagnostics and defaults retain their meanings. A .12 entry can import compatible earlier pinned definitions under their own declaring semantics. An earlier declaring module cannot import .12 definitions. Existing `extrude`, `extrude_rings`, `loft_rings` and `loft_framed_rings` do not acquire pocket semantics. One existing `placed` operation may rigidly place an unplaced pocket body in its carrier's `self.frame`; nested placement remains invalid.

Pocket geometry is visual. It adds no mass, inertia, collision body, attachment, following relationship or motion authority. Existing physical declarations and evaluated carrier world motion remain authoritative. This decision does not supply general Boolean subtraction, intersecting or nested cavities, tunnels, branching, changing cavity frames, bevels, smooth sweeps, deformation or live engine physics.

## Types, source identity and immutable input

| Constructor | Signature and meaning |
| --- | --- |
| `polygon_pocket` | `(order: Int, vertices: Keyed<PolygonVertex>, depth: Length, floor_region: String) -> PolygonPocket` |
| `extrude_pockets` | `(outer_vertices: Keyed<PolygonVertex>, pockets: Keyed<PolygonPocket>, palette: Keyed<SurfaceMaterial>, height: Length, bottom_region: String, top_region: String) -> Geometry` |

The enclosing keyed entry supplies each pocket's stable key. Its integer order determines traversal independently of declaration order and key spelling. Existing `planar_point`, `polygon_vertex`, `SurfaceMaterial`, nominal classes, functions, parameters, pinned modules, keyed generation and exact source edits keep their rules. Each vertex's `side_region` owns its outgoing wall edge. A pocket's `floor_region` owns its whole floor.

Vertex identity is scoped by its boundary. Logical mesh identity is `(boundary_kind, boundary_key, vertex_key, level)`: exterior uses `("outer","outer",vertex_key,"lower"|"top")`; a pocket uses `("pocket",pocket_key,vertex_key,"lower"|"top")`. Thus a user pocket key `outer` cannot collide with the exterior namespace. Exterior lower vertices lie on z=0; pocket lower vertices lie on the corresponding rounded floor. Derived triangles/corners are read-only inspection data, not writable source identities.

Before subsequent work callbacks, capture bounded immutable copies of the full exterior, pocket membership, keys/orders, vertex coordinates/regions, depths, floor regions and material channels. A frozen record containing a mutable list is insufficient. Preserve callback exception and cancellation identity; never translate an arbitrary callback failure into a geometry error.

The [grammar supplement](ontokin-pockets.ebnf) uses ordinary expression, keyed-value and type syntax. The [diagnostic registry](diagnostics.json) fixes new error families and inherited distinctions.

## Finite domain and planar topology

| Quantity | Bound |
| --- | --- |
| Pockets | Zero through eight |
| Vertices | At least three per boundary; at most 64 across exterior and all pockets |
| Orders | Unique pocket orders in [0,65535]; unique vertex orders in that range within each boundary |
| Coordinates | Finite canonical binary64 values within [-100,100] meters |
| Body height | Canonical binary64 [0.001,100] meters |
| Pocket depth | Canonical binary64 [0.001,100] meters, additionally subject to remaining-base admission |
| Exact remaining base | At least the exact rational value of canonical binary64 0.001 meter |
| Palette | One through sixteen valid existing PBR materials |
| Complete body | At most 252 triangles / 756 flat corners |

Pocket keys are unique within their keyed value, and vertex keys are unique within each boundary. Order gaps are allowed. Sort pockets and vertices by their explicit orders. The exterior is counterclockwise as seen from +Z; pockets are clockwise. The closing edge is implicit, so repeating the first point is invalid.

Apply the unchanged .9 exact simple-boundary rules: distinct points, nonzero signed area, no zero edge, adjacent collinearity/backtracking, nonadjacent crossing, touching or overlap. Different boundaries cannot cross, touch, overlap or share a point. Every pocket lies strictly inside the exterior; every pair of pockets is mutually exterior. Nested pockets and pockets in an exterior notch are rejected. Exact predicates use rational values of canonical binary64 coordinates; positive and negative zero compare equally. There is no clearance epsilon and no silent reversal, clipping, welding or repair.

Every outgoing wall region and all bottom, top and floor regions must name a palette key. Unused valid palette entries emit no primitive. These material checks apply before construction, including paths with zero pockets. Existing aggregate source/object/value/result/sample/artifact limits and the 250,000 mesh-vertex limit remain.

## Exact floor arithmetic

Let H and d be the exact rational values of the canonical binary64 body height and pocket depth. Compute b=H-d exactly and require `b >= Fraction(binary64(0.001))`. A nonpositive, out-of-range or penetrating depth is rejected; a positive depth leaving less than the minimum base is also rejected. Comparing a rounded subtraction with the minimum is not a substitute for this exact comparison.

Round the complete b once to canonical binary64 floor coordinate f, and require `0 < f < height`. The actual source vertices use f. Their effective geometric depth is the exact rational `D = H-Fraction(f)`. The authored depth, exact pre-rounding base, rounded floor/remaining base and effective depth are distinct quantities. No independently rounded intermediate subtraction or later recomputation may silently change the floor.

The source summary exposes `height_m`, each pocket's `depth_m` (authored), `floor_m`, `remaining_base_m` (the same rounded source value as floor_m), `exact_remaining_base_m` and `effective_depth_m`. The latter two exact quantities use objects with decimal-string `numerator` and `denominator`, reduced with a positive denominator. This avoids rounding the arithmetic explanation back into an ambiguous JSON number.

Within the stated height and minimum-depth bounds a source floor cannot round onto the top. The separately required floor-collapse negative therefore uses actual placement/binary32 delivery. A source-valid delivery-refusal case must reach its geometric predicate under sufficient independently authorized resources; exhaustion is not that geometric result.

## Deterministic complete exterior

Flatten boundary vertices as exterior first, then increasing pocket order, with increasing vertex order inside each boundary. Each boundary contributes lower and top logical positions; there are exactly 2N positions for N authored boundary vertices.

With zero pockets, use the unchanged .8 extrusion triangulation and native face emission on the same exterior/material/height inputs. Local geometry, normal and material index streams must match that .8 path exactly. Source revision and profile provenance differ, so whole-GLB byte equality is not required. The new summary and delivery checks still describe the .12 request; identical operation counts are not promised.

For one or more pockets:

1. Triangulate the exterior with the unchanged .8 deterministic ear algorithm. Emit its complete bottom with reversed winding and -Z normals.
2. Triangulate the exterior-minus-pockets domain with the unchanged .9 deterministic exact cap algorithm, using exterior first and sorted pockets thereafter. Emit its top with positive winding and +Z normals. It must cover exactly that material domain, without filling or overlapping a pocket opening.
3. Emit exterior walls in vertex order, then pocket walls in pocket/vertex order. For each authored directed edge a-to-b, emit `(a_lower,b_lower,a_top)` and `(b_lower,b_top,a_top)`. Both use the outgoing vertex's region and normal `(dy/length,-dx/length,0)`. Clockwise pocket boundaries make these normals point into the cavities.
4. In pocket order, independently triangulate each pocket floor. Reverse the valid clockwise traversal while keeping its first ordered vertex first, then apply the unchanged .8 deterministic ear algorithm. Map the resulting faces back to the original vertex identities. Emit at that pocket's f with positive winding, +Z normals and its `floor_region`. This prescribed face construction does not repair an invalid source winding.

Every triangle has three flat corners and finite outward unit normals. Group faces by sorted used material key, preserving the stated native emission order within each group. Failure to represent a nonzero outward face or valid unit normal is explicit.

For p pockets, exterior vertex count n0 and total boundary vertex count N: bottom triangles are n0-2; top triangles N+2p-2; floor triangles N-n0-2p; wall triangles 2N. Thus the complete body has exactly **4N-4 triangles and 12N-12 flat corners**, independent of pocket count. There are no interior caps or hidden partitions below a pocket floor.

Let A0 and P0 be exterior area/perimeter, and Ai and Pi each pocket's positive area/perimeter. Source volume is `A0*H-sum(Ai*Di)`. Source surface area is `2*A0+P0*H+sum(Pi*Di)`. Use the actual effective depths Di after floor rounding. These formulas describe this prismatic geometry; independent triangle determinants and area sums must agree within their declared numeric comparison rules.

## Complete source and actual delivery admission

Complete source construction retains the full logical identity set, distinct positions for distinct identities, three distinct identities and nonzero exact area per face, exactly opposite closed directed edge incidence, only shared-vertex/shared-edge triangle contacts and positive exact signed volume. Bottom faces point -Z; top and floor faces point +Z. Independent domain checks establish complete exterior bottom and pocket floors and the perforated top, including directed boundaries, no filled openings and no overlapping cap coverage.

After the existing one-time rigid visual placement and actual binary32 conversion, repeat identity separation, nondegeneracy, closed incidence, shared-simplex contact and positive-volume checks on supplied positions. Check actual normal orientation, exact source-quantized position/normal correspondence, materials and bottom/top/floor signs. For signs, use the inherited exact placement matrix applied to local +Z. Preserve the existing 0.00001-meter local geometric error bound and recorded-motion tolerances. Narrow openings, walls or floors that collapse, touch or invert are explicit geometric precision refusals.

A placed and rounded cap need not remain exactly planar. Establish its intended domain in original authored XY identities, and establish actual triangle contacts in 3D. Do not inverse-transform rounded positions and demand exact planarity. Metadata alone cannot prove a pocket, floor, material, volume or recorded motion. A through-hole with the same top opening is not an acceptable pocket.

## Inspection, Agent lifecycle and budgets

The summary is `ontokin.polygon-pockets-summary/0.1`, profile `polygon-pockets-0.1`, family `polygon_pockets`. Its arrays are `outer_vertices` and `pockets`; each pocket has `key`, `order`, `vertices`, `depth_m`, `floor_region`, `floor_m`, `remaining_base_m`, `exact_remaining_base_m` and `effective_depth_m`. Every vertex exposes `key`, `order`, `point_m` and `side_region`. Count fields are `pocket_count`, `authored_vertex_count`, `logical_vertex_count`, `bottom_triangle_count`, `top_triangle_count`, `floor_triangle_count`, `wall_triangle_count`, `triangle_count` and `vertex_count` (flat corners). It also exposes `height_m`, `bottom_region`, `top_region`, `palette_keys`, `palette_count`, `used_region_count`, sorted `regions` with material keys and triangle counts, and the standard `local_visual_placement`. Physical participation remains `none`, and motion authority remains `carrier_evaluated_world_pose`. Earlier geometry families retain their own summaries inside .12 programs.

`PocketsAgentService` uses separate `pockets-program-agent.sqlite3` state with schema `ontokin.pockets-program-agent-store/0.1`. Explicit Agent/0.12 supplies all twelve actual operations: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. Preserve exact UTF-8 patch preconditions, immutable accepted revisions, invalid-edit rollback, nominal occurrence continuity, unchanged sibling and pinned-library bytes, current host reauthorization, revision/query/geometry/implementation/protocol-bound pages, the inherited 256-triangle page maximum, durable identical retries, changed-payload refusal, cancellation and atomic artifact publication. Editable `.ok` source remains the only mutation authority.

Omitted requests remain **100,000 operations / 30,000 ms**, including on larger hosts. Explicit entry requests can increase them only within independently supplied trusted host ceilings; caller caps only reduce requests. Modeled animation duration remains separate. All source construction, floor arithmetic, topology, triangulation, inspection, encoding and supplied-byte validation share one cumulative ledger and original deadline. Charge bounded geometric loops and the new exact subtraction/admission/rounding operations. Keep the 32,768-bit operand, 256-entry numerical-cache and 64-step reference-cursor bounds; no new numeric cache is introduced. Frozen maximum cases may request 2,000,000 operations / 80,000 ms with matching independent host authority; actual completion remains measured, not assumed.

## Frozen independent evidence and integration

Before runtime work, freeze independently authored positive, boundary, refusal, composition and exact-repair sources and their expected outcomes. Include zero-pocket .8 stream equivalence; the rectangular recess; concave exterior and pocket shapes; multiple unequal depths; count/material maxima; exact minimum-base and clearance boundaries; declaration reordering; rigid placement; reusable/generated instances; and one-occurrence repair preserving its sibling and pinned library.

Invalid cases include touching, nested, intersecting and outside pockets; reversed winding; malformed keys/orders/points/material ownership/types/units; nonpositive, penetrating and insufficient-base depths; actual floor/opening collapse and other source-valid delivery precision failures. Include exact-arithmetic boundaries that distinguish authored depth from actual rounded geometry. Independent expected calculations must not import product triangulation or intersection functions.

The control exterior 4 by 3 by 2 meters with a 2 by 1 meter pocket of depth 0.5 meter has volume **23 cubic meters**, surface area **55 square meters**, 16 logical vertices, 28 triangles and 84 flat corners. These are predetermined analytic expectations, not execution claims.

Independent supplied-byte checks must inspect domain coverage, identities, closed incidence, allowed contacts, normals, material ownership, volume, actual floor depths and fixed/dense recorded poses. Their hostile controls must reject removed/reversed floors, filled openings, duplicate/overlapping caps, altered material faces, swapped pocket depths and substitution of a through-hole. Include mutation/cancellation callbacks, current-policy reduction, insufficient caller budgets, retry payload changes, partial artifact writes and stale page/revision cases. Schema validity alone is not workflow evidence.

Require the complete applicable inherited local run, fresh immediate-predecessor .11 workflow and preservation of its geometry/motion inputs, actual twelve-operation .12 exchanges with independent raw audit, pinned native/Three.js/Chromium destination execution, and real per-capture visual dispositions with stated visibility limits. Identify exact source, environment, settings, commands, artifacts, logs, failures and omissions. Preserve original frozen inputs and every failed preparation. No new or worsened legacy failure may be hidden by changing an expectation.

Development integration follows [OK-ENG-009](../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md): independent review, fresh observed-head bounded main lease, conditional/nonforce publication, actual merge verification, relevant resulting-main checks and complete candidate-input preservation. Record complete input exclusions explicitly; equality permits correctly attributed evidence reuse, not a claim of fresh execution. The complete portable handoff preserves predecessor evidence, actual Git/source identities and all historical boundaries. Packing, extraction, native restoration, durable delivery and explicit scope closure require their own actual receipts. No hosted paid execution is launched by this decision.

## Retained project boundaries

Original28 remains 24/28 failed with P11/P16/P23/L03 unresolved. Preserve M1 rejection, comparison/passive authority, held C035 including adverse timing, C057 and complete reach, all R01-R12/Q01-Q22 and original fixtures/horizons/equations/helpers/tolerances, missing Python/external roles, C068/C069/C070/C071 dispositions, C059's unestablished storage cause and unfinished historical LFS migration. Higher-budget requests cannot retroactively pass fixed-budget gates.

Unreal import and live destination physics remain unverified. Richer language/algorithm libraries, textures/UVs, skin deformation, contacts/general dynamics, mechanisms/vehicles, articulated creatures and purposeful movement, flight/swimming, vegetation/wind, terrain/buildings, liquids/deformables, transitions/live engines, measured scale and a direct-tool authoring comparison remain part of GOAL. This finite increment is experimental development; `release_acceptance` remains false.
