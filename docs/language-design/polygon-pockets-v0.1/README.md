# Author blind polygon pockets

The experimental [OK-LANG-012 / OK-AGENT-012 decision](ADOPTION.md) selects source `0.12` / `polygon-pockets-0.1`, Agent/0.12 and recorded GLB/0.12. A constant outer polygon surrounds separately keyed recesses that end at their own interior floors. Earlier geometry constructors, source meanings and defaults retain their contracts.

## Start with complete source

The [rectangular pocket](../../../examples/polygon-pockets/rectangular-pocket.ok) is a 4 by 3 by 2 meter body with a 2 by 1 meter opening and a depth of 0.5 meter. Its independently frozen control has volume 23 cubic meters and surface area 55 square meters. These quantities refer to the complete closed surface, including the pocket walls and floor. The [fixture guide](../../../examples/polygon-pockets/README.md) links concave shapes, unequal depths, a stepped tray, placement, generated instances and reusable libraries.

```bash
python3 -m ontokin export examples/polygon-pockets/rectangular-pocket.ok \
  --target ontokin.glb/0.12 --output /tmp/pocket.glb
python3 -m ontokin agent --protocol ontokin.agent/0.12 \
  --store /tmp/ontokin-pockets-agent
```

The frozen sources and analytic expectations are acceptance inputs. Actual implementation, execution, destination and integration results are identified separately in [STATUS](../../../STATUS.md).

## Values and constructors

```text
PolygonPocket
polygon_pocket(order: Int, vertices: Keyed<PolygonVertex>,
               depth: Length, floor_region: String) -> PolygonPocket
extrude_pockets(outer_vertices: Keyed<PolygonVertex>,
                pockets: Keyed<PolygonPocket>,
                palette: Keyed<SurfaceMaterial>, height: Length,
                bottom_region: String, top_region: String) -> Geometry
```

An existing `PolygonVertex` names an explicit order, a two-component length point and the material region for its outgoing wall edge. The exterior is counterclockwise when viewed from positive Z. Each pocket is clockwise. Every boundary must be simple, and every pocket must be strictly inside the exterior, strictly separated from every other pocket and nonnested. No epsilon admits touching or intersecting outlines.

Keys come from the surrounding `Keyed` entries. Explicit orders, including gaps, determine traversal independently of declaration order and key spelling. Pocket order controls emission between pockets. Each pocket has its own floor material; the entire body names separate exterior bottom and perforated top materials. Reusing a palette entry across these domains is allowed, but every referenced region must exist.

Zero pockets produces the exact local position, normal and material-index streams of the unchanged `.8` simple extrusion. Provenance headers and whole GLB bytes differ because `.12` is a distinct explicit binding. One inherited `placed(geometry, pose)` may place a native pocket body in its carrier frame. Nested placement remains invalid.

## Depth and floor arithmetic

Height and each authored depth first become canonical binary64 values under the existing unit rules. Treat those stored values as exact rationals and subtract depth from height. This exact remaining base must be at least the exact rational value of canonical binary64 `0.001` meter. Depth must also be positive and strictly less than height.

Round the complete exact remaining base once to binary64 to obtain the floor coordinate. The floor must remain strictly between bottom and top. Actual geometry uses this rounded floor. Its effective depth is the exact rational difference between stored height and stored floor, which can differ from the authored depth. The summary retains both meanings rather than silently substituting one for the other.

With exterior area A, exterior perimeter P, body height H, and each pocket's area Ai, perimeter Pi and effective depth Di, volume is `A*H - sum(Ai*Di)` and total surface area is `2*A + P*H + sum(Pi*Di)`. The floor replaces the opening's removed horizontal area; the added interior wall area depends on the effective depth.

## Complete surface and limits

The surface contains an independent exterior bottom, perforated top, exterior walls, each pocket's walls and each pocket's floor. Existing deterministic cap algorithms and fixed wall diagonals define the triangle stream. Logical identities are `(boundary_kind, boundary_key, vertex_key, level)`, with separate `outer` and `pocket` namespaces and `lower`/`top` levels. A pocket's lower level is its own floor, not the exterior bottom.

| Quantity | Bound |
| --- | --- |
| Pockets | 0–8 |
| Vertices per boundary | At least 3 |
| Total authored vertices N | At most 64 across exterior and pockets |
| Orders | Unique integers from 0 through 65,535 in their applicable scope |
| Authored XY components | Within ±100 meters |
| Height and authored depth | 0.001–100 meters, subject to positive remaining base |
| Exact remaining base | At least canonical binary64 0.001 meter |
| Materials | 1–16 |
| Derived geometry | 2N logical vertices, 4N−4 triangles, 12N−12 flat corners |
| Maximum derived geometry | 128 logical vertices, 252 triangles, 756 flat corners |

Both the complete source mesh and supplied delivered coordinates must preserve distinct identities, nonzero exact faces, closed opposite edge incidence, only explicitly shared vertex/edge contacts, positive signed volume and outward normals. The bottom faces down; the top and pocket floors face up along the placed cap axis. Authored XY domains establish cap coverage; actual three-dimensional triangles establish delivered topology.

A source-valid shape may fail export if binary32 positions collapse an opening or floor, introduce contact, reverse a face or exceed the unchanged 0.00001-meter local position tolerance. Failure produces no artifact. The exporter does not weld, repair or silently simplify geometry.

## Inspect and repair through Agent/0.12

`ontokin.pockets_agent.PocketsAgentService` uses a separate `pockets-program-agent.sqlite3` store and the [Agent/0.12 schemas](../agent-v0.12/README.md). All twelve inherited operations remain available: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page.

The `ontokin.polygon-pockets-summary/0.1` result includes the sorted exterior and pocket boundaries, authored depths, floor material, rounded `floor_m` and `remaining_base_m`, and exact numerator/denominator objects for `exact_remaining_base_m` and `effective_depth_m`. Separate bottom, top, floor and wall counts make the full surface inspectable. Earlier geometry occurrences retain their original summary definitions.

Mesh pages contain at most 256 triangles and bind revision, query, occurrence, geometry, implementation and protocol. They expose derived geometry for inspection; exact UTF-8 source edits remain the authority. The frozen [assembly](../../../examples/polygon-pockets/assembly.ok) and [repaired assembly](../../../examples/polygon-pockets/assembly-repaired.ok) demonstrate changing one pocket depth while preserving its sibling, pinned library and stable occurrence identity.

A failed edit preserves the accepted revision. Saved programs and artifact retrieval require current host authorization. Identical retries return the same durable receipt, changed-payload reuse is refused, cancellation retains atomicity, and an incomplete export cannot publish an artifact.

## Execution and verification

Ordinary defaults remain 100,000 operations and 30,000 milliseconds. A source request for more requires independently authorized host ceilings; caller caps can only reduce a request. The largest frozen cases explicitly request 2,000,000 operations and 80,000 milliseconds. Those cases do not change earlier fixed-budget gates. Computation time remains separate from modeled animation duration, and exact arithmetic retains the 32,768-bit operand bound.

`tools/run_pockets_acceptance.py` executes the frozen source and actual Agent workflow. `tools/pockets_oracles.py` independently checks supplied geometry and motion. `tools/audit_pockets_acceptance.py` reconciles raw requests, responses, stores and artifact bytes. `tools/verify_pockets_glb.mjs` runs pinned Khronos, Three.js and browser checks. Their actual results and source identities belong in the engineering evidence rather than this authoring contract.

This finite increment is experimental visual geometry and recorded carrier motion. General Boolean operations, intersecting or nested cavities, bevel offsets, branching, implicit mass/inertia/collision, Unreal import and live destination physics remain outside its established scope. All remaining language, mechanism, simulation, animation and delivery domains in [GOAL](../../../GOAL.md) remain required.
