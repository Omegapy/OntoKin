# Polygon lofts with authored rigid section frames

**Decision:** OK-LANG-011/0.1.0 and OK-AGENT-011/0.1.0, October 30, 2026.

**State:** Selected experimental C078 development contract. Publish this decision and an independently specified input freeze before runtime implementation. Adoption, implementation, execution, integration and release acceptance are separate outcomes.

## Purpose and explicit bindings

Source `ontokin "0.11";` selects `framed-polygon-loft-0.1`, explicit Agent `ontokin.agent/0.11` and recorded destination `ontokin.glb/0.11`. Each polygon section has an authored position and orientation in its owning carrier's local coordinates. Bent ducts and finite handle forms use the same stable ring and vertex correspondence as [C077](../polygon-loft-v0.1/ADOPTION.md). This advances the complete [GOAL](../../../GOAL.md).

Earlier source, Agent, destination, summary schemas and defaults retain their meanings. A .11 entry may import compatible earlier pinned definitions under their own declared semantics; an earlier declaring module cannot import .11 definitions. Existing `loft`, `extrude`, `extrude_rings`, `polygon_section` and `loft_rings` retain their contracts. An explicit .11 constructor does not reinterpret an older section or infer a frame from its station. One `placed` operation may rigidly place an unplaced framed loft. Nested placement remains invalid.

The finite triangles specified below are the surface. No continuously swept polygon, interpolated frame field, inferred tangent, automatic frame transport or smooth bending behavior is supplied. Visual geometry adds no mass, inertia, collision shape, attachment, following relation or motion authority. Recorded carrier motion remains independently evaluated.

## Types and ownership

| Constructor | Signature and meaning |
| --- | --- |
| `framed_polygon_section` | `(order: Int, frame: Pose, rings: Keyed<PolygonRing>) -> FramedPolygonSection` |
| `loft_framed_rings` | `(sections: Keyed<FramedPolygonSection>, palette: Keyed<SurfaceMaterial>, bottom_region: String, top_region: String) -> Geometry` |

The keyed entry supplies each section's stable key. `frame` is the existing typed `pose(self.frame, vec3(x[m], y[m], z[m]), rotation)` value. Its origin is a length vector in the owning carrier's local coordinates. Its `Rotation` maps the section's local XYZ axes into those carrier coordinates. Ring points `(u,v)` occupy section-local `(u,v,0)`.

The pose reference must equal the consuming carrier's own `self.frame`. Check that reference both when a framed section is constructed and when a framed loft consumes it. A section cannot escape one carrier and acquire another carrier's frame meaning. Reusable functions can receive the owning pose explicitly. World, parent, sibling and another carrier's frame references are rejected; scale, shear, matrices, implicit hierarchy and live frame following are not accepted substitutes for `Pose`.

Source `quat` and `axis_angle` retain existing admission and canonicalization. Quaternion order is **wxyz**. `quat` requires finite nonzero components whose norm is within 1e-12 of one, normalizes once, selects a positive first nonzero component and canonicalizes zero. This decision does not change that constructor or normalize a stored section rotation a second time. Native geometry input requires four finite numeric components with exact squared norm in `[(1-Fraction(binary64(1e-12)))**2, (1+Fraction(binary64(1e-12)))**2]`. Canonicalize its sign and zero leaves without another normalization; reject malformed values or a norm outside that envelope. Exact stored norm squared need not equal one. Quaternion sign-equivalent values have the same geometric action.

Snapshot the complete bounded section, pose reference, origin, rotation, ring, vertex and palette structure into immutable native leaves before later work callbacks. A frozen host record containing a mutable list is not itself an immutable snapshot. Retain callback exception and cancellation identity.

## Exact transform and finite domain

Interpret each canonical binary64 quaternion component as its exact rational value. For `q=(w,x,y,z)` and `D=w*w+x*x+y*y+z*z`, use the exact rotation matrix

```text
R = [[w*w+x*x-y*y-z*z, 2*(x*y-w*z),       2*(x*z+w*y)],
     [2*(x*y+w*z),       w*w-x*x+y*y-z*z, 2*(y*z-w*x)],
     [2*(x*z-w*y),       2*(y*z+w*x),       w*w-x*x-y*y+z*z]] / D
```

For each authored planar point, compute `origin + R * (u,v,0)` in exact rational arithmetic. Round each complete resulting component once to canonical binary64, including positive zero. No intermediate binary64 matrix, repeated quaternion normalization or separately rounded rotation/translation replaces this rule. Division by exact `D` makes the unrounded action a proper rigid rotation even when stored canonical `q` has norm squared slightly different from one. Actual rounded source positions are authoritative for the complete three-dimensional mesh predicates.

| Domain | Bound |
| --- | --- |
| Sections | 2 through 8; unique keys and integer orders in [0,65535] |
| Ring correspondence | Identical ring keys, roles and orders in every section; identical per-ring vertex keys and orders |
| Rings per section | One counterclockwise exterior; zero through eight clockwise holes |
| Vertices | At least three per ring; at most 64 per section and 256 over all sections |
| Planar coordinates and pose origins | Each component finite canonical binary64, within [-100,100] meters |
| Transformed source positions | Each rounded component within [-256,256] meters |
| Palette | 1 through 16 valid existing PBR materials |
| Complete mesh | At most 540 triangles and 1,620 flat corners per occurrence |

Sort sections by explicit order, independently of declaration order or key spelling. For adjacent origins, form exact displacement `d=origin_next-origin_previous` and each exact section normal `n=R*(0,0,1)`. Require all three conditions:

1. `dot(d,d) >= Fraction(binary64(0.001)) ** 2` in exact rational arithmetic.
2. `dot(d,n_previous) > 0` exactly.
3. `dot(d,n_next) > 0` exactly.

These rules define separation and forward progression without a global station axis. They reject coincident, sideways and reversed progression. There is no additional angular threshold or tolerance; a near-half-turn must meet these rules and complete mesh admission. Exact opposite normals cannot meet both positive-dot requirements. A nonadjacent section may return near an earlier position only if the complete mesh remains valid. No automatic orientation reversal, cyclic alignment or nearest-point matching occurs.

Every authored XY section independently satisfies the unchanged .9 simple-ring, distinct-point, winding, no-adjacent-collinearity, strict-containment and non-touching rules. Validate both cap region names and every outgoing vertex region, including terminal regions that emit no strip. Existing aggregate object, source, value, sample, artifact and 250,000 mesh-vertex limits remain.

## Authoritative triangles and complete admission

Flatten vertices by section order, ring order and vertex order. For each lower directed ring edge `a -> b` and its matched upper edge, emit exactly `(a_lower,b_lower,a_upper)` and `(b_lower,b_upper,a_upper)`. The diagonal is `b_lower -> a_upper`. Both faces use the lower outgoing vertex's region. Triangulate the first and last original XY material domains independently with the existing exact .9 cap algorithm. Reverse the first cap's winding and retain the last cap's positive winding. Intermediate sections have no caps. Group faces by sorted used material key, preserving emission order within each region; give every triangle three flat corners and its own outward unit normal.

For S sections, N matched vertices per section and H holes, each endpoint has `N+2H-2` triangles, strips have `2(S-1)N` triangles and the whole mesh has `2SN+4H-4` triangles. Area is the sum of actual triangle areas. Signed volume is the exact determinant sum of actual positions divided by six. Neither an analytic sweep formula nor interpolated polygon slices redefine these faces.

After the exact transform and per-coordinate rounding, complete source admission requires consistent source identities `(section key,ring key,vertex key)`, distinct positions for distinct identities, three distinct identities and nonzero exact area on every face, opposite closed directed edge incidence, only explicitly shared-vertex or shared-edge triangle contacts, and strictly positive exact signed volume. Cap triangle cross products must have strictly negative dot product with the first exact frame +Z axis and strictly positive dot product with the last. Invalid crossing, touching, folded, pinched or overlapping geometry fails without clipping, welding, reversing or repair.

Rounding may make a transformed cap slightly nonplanar. Check cap coverage, hole exclusion, overlap and directed boundary in the original authored XY domain by exact source identities. Check actual transformed triangles and their contacts in three dimensions. Do not inverse-transform rounded vertices and require exact planarity or equate actual three-dimensional area with an unrounded cap area.

After the existing one-time local visual placement and binary32 delivery, independently repeat identity separation, nonzero face and cap orientation, closed incidence, shared-simplex contact and positive-volume checks on actual supplied positions. Outer placement keeps its inherited arithmetic: normalize its quaternion through the existing binary64 `math.hypot` rule, form the exact rational matrix with diagonal entries `1-2*(...)`, round each complete rotated point component to binary64, then perform the inherited binary64 translation. It does not use the new section matrix divided by D. For cap sign guards, apply that exact inherited placement matrix to the exact section +Z axis without rounding the axis; compare it against the exact cross of actual delivered positions. Preserve the existing 0.00001-meter local geometric error bound, normal orientation/source-quantized agreement, regional materials and recorded-motion tolerances. A source-valid narrow opening, near-touch or rounded cap fold that fails at delivery is an explicit geometric precision refusal, not successful export. A resource refusal cannot substitute for a frozen geometric refusal.

## Diagnostics, summaries and Agent lifecycle

The new diagnostic family is `OKL-E-FRAMED-LOFT-SECTION`, `-ORDER`, `-FRAME`, `-PROGRESSION`, `-CORRESPONDENCE`, `-TOPOLOGY`, `-REGION` and `-NUMERIC`. Inherited type, unit, rotation, planar-ring, material, placement and resource diagnostics keep their names and meanings. Report relevant section/ring/vertex identity and source span when available. Wrong constructor types or dimensions do not become topology errors.

The new summary is `ontokin.framed-polygon-loft-summary/0.1`, profile `framed-polygon-loft-0.1`, family `framed_polygon_loft`, with `surface_rule: "fixed-diagonal-triangles"` and `section_transform_rule: "exact-rational-quaternion-single-round"`. Expose sorted sections with key, order, authored local origin, canonical wxyz orientation, owning frame designation, rings and vertices; counts, palette, used regions, cap/strip/total triangle counts, flat corner count and the separate rigid visual placement. There is no invented station range. Physical participation remains `none`, and motion authority remains `carrier_evaluated_world_pose`. Earlier geometry families retain their own summary schemas in .11 programs.

`FramedLoftAgentService` uses separate `framed-loft-program-agent.sqlite3` state with schema `ontokin.framed-loft-program-agent-store/0.1`. Explicit Agent/0.11 supplies discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. Preserve exact UTF-8 patch preconditions, accepted-revision immutability, failed-edit rollback, nominal occurrence continuity, unchanged sibling/library bytes, current host authorization, revision/query/geometry/implementation/protocol-bound pages, the existing 256-triangle page maximum, durable identical retries, changed-payload rejection, cancellation and atomic artifact publication. Derived mesh data is read-only; editable .ok source remains the mutation authority.

## Work and evidence requirements

Omitted requests remain **100,000 operations / 30,000 ms**, including on larger hosts. Explicit entry requests can increase only within separately supplied trusted host ceilings; caller caps only reduce them. All constructor, frame validation, rational transform, progression, topology, inspection, encoding and delivered-byte work shares one cumulative counter and the original deadline. Charge each bounded iteration and explicit rational arithmetic operation in the new transform; enforce the unchanged 32,768-bit operand bound. Do not add a numerical cache or change the inherited 256-entry cache or 64-step reference-cursor bound. Computation time remains separate from modeled animation duration. Maximum-count frozen requests use 2,000,000 operations / 80,000 ms with independent matching host authority; their actual completion remains a required measurement.

Freeze independent positive, boundary, invalid, composition, exact-repair and source-valid delivery-refusal inputs before implementation. Include identity-frame equivalence to .10, a known rigid rotation, bent solid, hollow elbow, finite solid/hollow handle, concavity, multiple holes, material transitions, declaration reordering, generated/reusable occurrences and count maxima. Include malformed/nonrigid/foreign-owner frames, wrong types/units, numeric and separation boundaries, reversed and near-reversed progression, matching failures, crossing/pinching/cap and nonadjacent collisions, and actual binary32 failures. An exact one-occurrence frame or vertex repair must leave its sibling and pinned library unchanged.

Useful independently calculated controls use outer square coordinates ±1, hole square ±0.5, identity at `(0,0,0)`, Y90 at `(4,0,4)` and optionally Y180 at `(8,0,0)`. The exact Y90 control uses equal stored w and y quaternion components; an `axis_angle` expression whose canonical leaves differ is a separately rounded case. Exact rational rotation gives solid elbow volume 16 m³ and area `24+16*sqrt(2)` m²; hollow elbow volume 12 and area `30+24*sqrt(2)`; solid handle volume 32 and area `40+32*sqrt(2)`; hollow handle volume 24 and area `54+48*sqrt(2)`. These are prescribed polyhedral-face calculations, not general sweep formulas.

Require actual twelve-operation Agent use, independent supplied-byte cap/strip/identity/3D contact/normal/material/volume/motion checks without product triangulation or intersection imports, native and pinned Three.js/Chromium playback, actual capture review, applicable complete inherited checks, independent review and verified resulting-main inputs under [OK-ENG-009](../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md). Every result identifies its actual source, environment and omissions. Input equality permits attribution, not a claim of fresh re-execution.

## Retained boundaries

Automatic path transport/alignment, inferred tangents, resampling, ring creation/removal, topology changes, branching, blind cavities, Booleans, bevel offsets, implicit physical properties, skin deformation and live destination physics require separate decisions. Unreal Engine support still requires named import and playback evidence.

Original28 remains 24/28 failed with P11/P16/P23/L03 unresolved. Preserve M1 rejection, comparison accounting/passive authority, held C035 including adverse timing, C057, complete reach and all R/Q gates, missing interpreter/external roles, C068/C069/C070/C071 dispositions, C059's unestablished storage cause, unfinished historical LFS migration and all GOAL domains. Higher-budget work cannot retroactively satisfy fixed-budget gates. This decision is experimental development; `release_acceptance` remains false.
