# Agent/0.11 framed polygon loft contract

The [C078 decision](../framed-polygon-loft-v0.1/ADOPTION.md) explicitly selects source `0.11`, `framed-polygon-loft-0.1`, Agent/0.11 and recorded GLB/0.11. Earlier source declarations, Agent services, stores, destinations and defaults retain their meanings.

- [request.schema.json](request.schema.json) describes all twelve operations, exact source patches and caller budget reductions.
- [response.schema.json](response.schema.json) describes request envelopes, execution receipts, bounded mesh pages and five distinct native geometry summary families.
- [diagnostic.schema.json](diagnostic.schema.json) retains source-bound diagnostics, including inherited errors and `OKL-E-FRAMED-LOFT-*`.

`FramedLoftAgentService` uses `framed-loft-program-agent.sqlite3` and store schema `ontokin.framed-loft-program-agent-store/0.1`. Each request retains one cumulative work counter, its original deadline, current trusted host authorization, immutable accepted revisions, cancellation, durable identical retries and atomic publication. Omitted source requests remain 100,000 operations and 30,000 ms, including on larger hosts. Explicit larger requests need independently supplied host ceilings; caller caps only reduce those requests.

## Source inspection

`ontokin.framed-polygon-loft-summary/0.1` describes the admitted framed surface. `sections` is sorted by explicit section order. Each section supplies `key`, `order`, `frame: "carrier_self_frame"`, its authored `origin_m`, its canonical `orientation_wxyz`, and sorted rings. Each ring supplies `key`, `order`, `role` and sorted vertices. Vertices retain `key`, `order`, original section-local `point_m` and `side_region`.

| Field | Meaning |
| --- | --- |
| `section_count` | Number of sections, from 2 through 8. |
| `ring_count`, `hole_count` | Matched ring and hole counts in each section. |
| `vertices_per_section`, `authored_vertex_count` | Matched vertex count and its total across sections; at most 64 and 256. |
| `sections[].origin_m` | Three local-meter components in [-100,100], relative to the owning carrier. |
| `sections[].orientation_wxyz` | Four canonical rotation components in wxyz order; geometric interpretation follows the exact adopted matrix. |
| `surface_rule` | `fixed-diagonal-triangles`. |
| `section_transform_rule` | `exact-rational-quaternion-single-round`. |
| `cap_triangle_count`, `strip_triangle_count` | Count on each endpoint and total count between consecutive sections. |
| `triangle_count`, `vertex_count` | Complete triangles and flat mesh corners, at most 540 and 1,620. |
| `palette_count`, `used_region_count` | All authored palette entries and entries that emit triangles. |

There is no global station range in this summary. Each lower outgoing vertex region owns its two strip triangles; terminal regions are validated but emit no strip. Cap regions, sorted palette keys and emitted material regions remain explicit. `local_visual_placement` describes the separate outer placement, applied once after section transforms. Visual geometry adds no physical matter or motion authority.

The original XY material domains govern cap coverage. Actual rounded three-dimensional triangles govern geometry, contacts, area, signed volume and normals. A rounded cap need not be exactly planar. These distinct requirements remain semantic checks; the schema does not certify a surface.

Earlier elliptical-loft, simple-extrusion, hole-extrusion and station-loft summaries retain their original schemas, profiles and fields. In particular, `ontokin.polygon-loft-summary/0.1` retains its `.10` station semantics alongside the new framed summary. Agent/0.11 mesh pages identify the `.11` entry profile even when an occurrence uses an inherited geometry family. Pages contain at most 256 triangles and remain bound to revision, occurrence, filter, geometry, implementation and protocol. Derived triangles are read-only; source bytes remain the editing authority.

## Ownership and bounded operations

A section pose must name its consuming carrier's frame when constructed and when consumed. Same-carrier free functions may receive an owning pose; they do not acquire lexical `self`. A framed section copied from another occurrence remains foreign and is rejected. Invalid edits preserve accepted source, previously valid runs, stored artifacts, siblings and pinned module bytes.

Discovery publishes the current framed interface and retains the previous station-loft interface as explicitly inherited information. It lists old and new constructors with their adopted meanings. Profile compatibility permits earlier pinned definitions; it does not reinterpret old source as the new geometry contract.

Schema-valid requests still require exact source identity, current budget admission, ownership, progression and geometry validation. Source-valid geometry can fail binary32 delivery. Successful schema validation alone establishes no destination or release result, and recorded GLB/browser evidence establishes no Unreal import or live physics support.
