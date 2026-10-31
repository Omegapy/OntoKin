# Author explicitly framed polygon lofts

The experimental [OK-LANG-011 / OK-AGENT-011 decision](ADOPTION.md) selects source `0.11` / `framed-polygon-loft-0.1`, Agent/0.11 and recorded GLB/0.11. Each section has an authored rigid pose in its consuming carrier's frame. Stable section, ring and vertex identities define the triangles between sections. Earlier source meanings, summary schemas and defaults remain unchanged.

## Start from complete editable source

The [hollow elbow](../../../examples/framed-polygon-lofts/hollow-elbow.ok) has two square annular sections, with the second turned through a right angle. Its fixed strip triangles and endpoint caps form a closed surface. The [solid handle](../../../examples/framed-polygon-lofts/solid-handle.ok) and [hollow handle](../../../examples/framed-polygon-lofts/hollow-handle.ok) use additional explicit frames. Their motion is authored on their carrier; visual geometry contributes no implicit physical body, inertia, collision shape or action authority.

```bash
python3 -m ontokin export examples/framed-polygon-lofts/hollow-elbow.ok \
  --target ontokin.glb/0.11 --output /tmp/elbow.glb
python3 -m ontokin agent --protocol ontokin.agent/0.11 \
  --store /tmp/ontokin-framed-agent
```

The [fixture guide](../../../examples/framed-polygon-lofts/README.md) links the complete source corpus. Expected geometry was independently frozen before runtime implementation. It is an acceptance input, not a claim that a later implementation or destination passed.

## Source values and ownership

The existing expression, function, class, `Keyed`, unit, frame and execution-header grammar is retained under the explicit `.11` header. The new type and callable signatures are:

```text
FramedPolygonSection
framed_polygon_section(order: Int, frame: Pose,
                       rings: Keyed<PolygonRing>) -> FramedPolygonSection
loft_framed_rings(sections: Keyed<FramedPolygonSection>,
                  palette: Keyed<SurfaceMaterial>,
                  bottom_region: String, top_region: String) -> Geometry
```

Every section pose references the consuming object's `self.frame`. A `Pose` supplies origin and orientation; it carries no scale or shear. A section's key comes from its surrounding `Keyed` entry, while `order` determines traversal. Distinct orders may have gaps. Declaration order does not determine geometry.

Reusable pure functions can receive a pose and rings, construct a section, and return geometry. The caller's carrier authority remains attached to that computation. A section or already constructed geometry cannot escape to a different carrier by borrowing a value from a sibling. Pinned definitions remain immutable source inputs, and generated occurrences retain independent nominal identities.

An unplaced framed loft accepts one existing `placed(geometry, pose)` operation. This outer visual placement is separate from section poses and is baked once into carrier-local coordinates. Nested placement remains invalid. Existing placement rules and arithmetic retain their previous meanings.

## Correspondence and admitted geometry

Each section contains one counterclockwise exterior ring and zero through eight clockwise holes, viewed from that section's local positive Z axis. Every section independently meets the earlier exact planar-ring rules. Across sections, ring keys, roles and orders, and vertex keys and orders, must match. Coordinates and outgoing strip materials may change. The lower section's outgoing vertex region owns each strip edge; endpoint cap regions are supplied explicitly.

Adjacent frames must have origins at least canonical binary64 `0.001` meter apart. The exact origin displacement must have a strictly positive dot product with both neighboring frames' exact positive Z axes. No universal angle threshold replaces these rules. A near half turn can be admitted if its actual triangles satisfy every mesh predicate.

The fixed diagonal rule defines two triangles for each corresponding ring edge between neighboring sections. There are no intermediate caps. The first and last XY domains are independently triangulated; the first cap faces backward and the last forward. A change in section orientation does not imply a smooth sweep, transported frame, interpolated planar slice, automatic topology match or branching junction.

The source validator checks distinct positions for distinct authored identities, nonzero faces, closed opposite directed edge incidence, only the explicitly shared vertex or edge contacts, positive signed volume, and endpoint cap orientation. Overlap, crossing, pinching and nonadjacent touching fail explicitly. It does not repair or weld geometry.

## Numeric meaning and bounds

| Quantity | Bound or rule |
| --- | --- |
| Sections | 2–8 |
| Rings per section | One exterior and 0–8 holes |
| Vertices | At most 64 per section and 256 over the complete loft |
| Origin and authored XY components | Within ±100 meters |
| Rounded transformed source components | Within ±256 meters |
| Order | Unique integer in 0–65535 within its applicable scope |
| Materials | 1–16 explicit keyed linear RGBA / metallic / roughness values |
| Maximum derived mesh | 540 triangles and 1,620 flat corners |
| Ordinary request defaults | 100,000 operations and 30,000 ms |

Existing rotation constructors canonicalize their quaternions under their previous rules. Section transforms use the resulting stored quaternion directly: an exact rational proper rotation divided by its exact squared norm, followed by one binary64 rounding of each complete translated coordinate. The new transform does not normalize the quaternion again or separately round the rotated point before adding the origin.

Rounded endpoint caps can be slightly nonplanar. Their coverage and holes are checked in the original authored XY domain by source identities, while their actual triangles and contacts are checked in three dimensions. The delivered binary32 mesh must independently preserve the complete topology and outward face/cap orientation after inherited outer placement. A valid source can therefore fail delivery with a geometric precision diagnostic. The ordinary local geometric error tolerance remains 0.00001 meter.

New exact arithmetic consumes the original cumulative request budget and preserves the unchanged 32,768-bit operand bound. The maximum fixtures explicitly request 2,000,000 operations and 80,000 ms and need an independently authorized `HostPolicy` with those ceilings. A larger host does not increase an omitted program limit, and caller caps only reduce requests. These higher-budget examples do not alter historical fixed-budget acceptance gates.

## Inspect, repair and retrieve through Agent/0.11

`ontokin.framed_loft_agent.FramedLoftAgentService` uses `framed-loft-program-agent.sqlite3` and the [separate .11 schemas](../agent-v0.11/README.md). It exposes all twelve operations: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page.

The framed summary schema is `ontokin.framed-polygon-loft-summary/0.1`. Ordered sections expose their keys, orders, origins, canonical wxyz quaternions, owning frame reference and ring identities. They have no station range. Mesh pages remain bounded to at most 256 triangles, with revision, query, occurrence, geometry, implementation and protocol bound to every cursor. The derived triangle array is inspection data; exact `.ok` edits remain the authority for changes.

The pinned [assembly](../../../examples/framed-polygon-lofts/assembly.ok) has two independent instances of one definition. Its frozen repair changes only the first instance's `end_x = 4[m];` to `end_x = 5[m];`. The sibling and pinned library retain their source bytes and geometry. A rejected edit retains the accepted revision. Saved work and artifact retrieval require current host authorization, while identical retries return their original durable receipts.

## Verification and remaining scope

The [adoption](ADOPTION.md), [independent freeze](../../../examples/framed-polygon-lofts/acceptance-freeze.json) and [Agent schemas](../agent-v0.11/README.md) define distinct inputs. `tools/run_framed_loft_acceptance.py` executes the frozen source cases and real Agent workflow. `tools/framed_loft_oracles.py` independently checks supplied geometry bytes, and `tools/verify_framed_loft_glb.mjs` runs pinned destination and browser checks. Actual results, source identities and integration belong in [STATUS](../../../STATUS.md) and its linked engineering records.

This increment remains experimental. It does not establish Unreal import, live destination physics, smooth path sweeps, automatic frame transport, topology changes, blind cavities, branching, general Boolean operations, collision dynamics, skin deformation, or completion of the full [GOAL](../../../GOAL.md).
