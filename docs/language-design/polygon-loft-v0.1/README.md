# Author matched polygon ring lofts

The explicit experimental `polygon-loft-0.1` profile connects polygon cross-sections into a closed visual mesh. Use it for tapered housings, hollow ducts, changing polygon outlines and stepped or chamfer-like forms. The [adopted decision](ADOPTION.md) defines its finite semantics; [frozen source examples](../../../examples/polygon-lofts/README.md) state independent expectations and [STATUS](../../../STATUS.md) identifies measured implementation evidence.

## Select the contract

An entry selects `ontokin "0.10";` and `profile "polygon-loft-0.1";`. Export selects `ontokin.glb/0.10`; the separate Agent service selects `ontokin.agent/0.10`. Earlier default selections retain their original meanings.

```bash
python3 -m ontokin export examples/polygon-lofts/hollow-frustum.ok --target ontokin.glb/0.10 --output /tmp/hollow-frustum.glb
python3 -m ontokin agent --protocol ontokin.agent/0.10 --store /tmp/ring-loft-agent
```

The Python interface is `ontokin.ring_loft_agent.RingLoftAgentService`. Its [protocol guide and schemas](../agent-v0.10/README.md) describe all twelve operations and separate durable state. Source remains authoritative. A mesh page is a bounded derived view of an identified revision, not a second editable model.

## Define sections and correspondence

`polygon_section(order, station, rings)` produces a `PolygonSection`. Supply a `Keyed<PolygonSection>` to `loft_rings(sections, palette, bottom_region, top_region)`. Rings and vertices use the [polygon-holes constructors](../polygon-holes-v0.1/ADOPTION.md):

```text
polygon_section(Int, Length, Keyed<PolygonRing>) -> PolygonSection
loft_rings(Keyed<PolygonSection>, Keyed<SurfaceMaterial>, String, String) -> Geometry
```

Each section contains one counterclockwise outer ring and zero through eight clockwise holes, viewed from positive Z. A section's XY coordinates and Z station define its vertices. Section keys and explicit integer orders are unique. Orders select traversal; declaration order does not. Stations must strictly increase in that order. All sections have the same ring keys, roles and orders, and every matched ring has the same vertex keys and orders. Coordinates and material regions may vary. The constructor does not rotate, resample or align mismatched rings automatically.

The complete source identity of a corner is `(section_key, ring_key, vertex_key)`. A targeted edit can therefore change one vertex of one section in one instance while preserving an unchanged sibling and pinned source library. See [the two-instance source](../../../examples/polygon-lofts/assembly.ok), [its exact repaired variant](../../../examples/polygon-lofts/assembly-repaired.ok), and [the generated duct assembly](../../../examples/polygon-lofts/generated.ok).

## Understand the actual surface

For every lower outgoing ring edge `a → b` and its matching upper edge, the strip consists of `(a_lower, b_lower, a_upper)` and `(b_lower, b_upper, a_upper)`. This fixes the diagonal from `b_lower` to `a_upper`. Those triangles define the surface even when the quadrilateral is not planar. Interpolating all corresponding polygon vertices at an intermediate station can describe a different cross-section.

The lower outgoing vertex's region owns both strip triangles. The terminal section emits no further strip, but every terminal region must still name an available material. The first and last sections receive independently triangulated caps; intermediate sections receive none. Concave end sections can require different diagonals. The cap-region arguments select the bottom and top materials independently.

Every section must be locally valid. The complete triangle surface must also remain closed, consistently oriented and free of unintended intersections. Valid endpoints alone are insufficient: twisting correspondence or crossing holes may collide between stations. No hidden repair, vertex merging or fallback triangulation changes the authored surface. Local placement through `placed()` is applied once, in the carrier's self frame, before delivery.

## Limits and computation

| Item | Explicit limit |
| --- | --- |
| Sections | 2–8 |
| Vertices in each section, across all rings | 3–64, with at least three in each ring |
| Authored vertices across all sections | At most 256 |
| Holes in each section | 0–8, with matched topology throughout |
| Section, ring and vertex orders | Unique integers from 0 through 65,535 in their own scopes |
| XY coordinates | Each within ±100 meters |
| Stations | 0–100 meters; consecutive exact binary64 differences at least canonical binary64 0.001 meter |
| Palette | 1–16 named materials |
| Largest admitted mesh | 540 triangles, 1,620 flat corners |

The station comparison uses the exact difference between the canonical binary64 values. For example, `1.001[m] - 1[m]` is slightly less than canonical binary64 `0.001[m]` and fails the adopted minimum. No epsilon silently widens the limit.

Computation defaults remain 100,000 operations and 30,000 milliseconds. The maximum fixtures explicitly request 2,000,000 operations and 80,000 milliseconds; the host must authorize those ceilings separately. A caller can reduce a request, but cannot grant host authority. Modeled animation duration remains independent of computation time. Earlier fixed-budget gates retain their original limits.

## Delivery and scope

Recorded GLB/0.10 contains actual regional PBR materials, flat outward normals and the carrier's evaluated rigid motion. Validation checks the delivered binary32 positions after local placement. A source-valid opening that collapses or touches another boundary during conversion causes export to fail. Source acceptance and successful delivery are distinct outcomes.

This profile inherits earlier compatible geometry and behavior without redefining their constructors or summary schemas. An earlier declaring source profile cannot import a 0.10 dependency. Polygon lofts add no mass, inertia, collision shape or independent motion authority. Blind cavities, changing topology, branching, bevel offsets, Boolean operations, skin deformation and live destination physics remain outside this increment. The full product goal and outstanding release gates remain in [GOAL](../../../GOAL.md) and [STATUS](../../../STATUS.md).
