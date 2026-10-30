# Agent/0.10 polygon ring loft contract

The [C077 decision](../polygon-loft-v0.1/ADOPTION.md) explicitly selects source `0.10`, `polygon-loft-0.1`, Agent/0.10 and recorded GLB/0.10. Earlier bindings, stores and defaults retain their meanings.

- [request.schema.json](request.schema.json) describes all twelve inherited operations, caller caps and exact source edits.
- [response.schema.json](response.schema.json) describes envelopes, execution receipts, section/ring summaries and bounded triangle pages.
- [diagnostic.schema.json](diagnostic.schema.json) retains source-bound diagnostics, including inherited ring diagnostics and the new `OKL-E-RING-LOFT-*` family.

`RingLoftAgentService` uses `ring-loft-program-agent.sqlite3` and store schema `ontokin.ring-loft-program-agent-store/0.1`. Each request retains one work counter and its original deadline, current host authorization, revision checks, cancellation, durable identical retries and atomic publication. Omitted source limits remain 100,000 operations and 30,000 ms. A source request for larger limits requires independent current host authorization; caller caps only reduce the request.

## Source inspection

`ontokin.polygon-loft-summary/0.1` describes the authored source and admitted geometry. `sections` is sorted by explicit section order. Each section has `key`, `order`, `station_m` and sorted `rings`. Each ring has `key`, `order`, `role` and sorted `vertices`; vertices retain `key`, `order`, `point_m` and `side_region`. A vertex key is scoped by section and ring within its occurrence.

| Field | Meaning |
| --- | --- |
| `section_count` | Number of authored sections, from 2 through 8. |
| `ring_count`, `hole_count` | Matched ring and hole counts in each section. |
| `vertices_per_section` | Matched authored vertex count in each section, at most 64. |
| `authored_vertex_count` | Total across sections, at most 256. |
| `station_range_m` | First and last station in local meters. |
| `cap_triangle_count` | Triangle count on each endpoint cap. |
| `strip_triangle_count` | Total triangles between consecutive sections. |
| `triangle_count`, `vertex_count` | Complete triangles and flat mesh corners, at most 540 and 1,620. |
| `palette_count`, `used_region_count` | All authored palette entries and entries that emit geometry. |
| `surface_rule` | Always `fixed-diagonal-triangles`; interpolated polygon slices are not the surface contract. |

Every lower section's outgoing vertex region owns its two strip triangles. Terminal-section regions are validated but emit no strip. `bottom_region`, `top_region`, `palette_keys` and `regions` expose cap and material assignments. Local placement, visual-only physical participation and carrier motion authority retain their established meanings.

Earlier elliptical-loft, simple-extrusion and hole-extrusion occurrences retain their original summary schemas and profiles. Triangle pages identify the actual `.10` program profile, including for inherited geometry. Pages contain at most 256 triangles and remain bound to revision, occurrence, region, geometry, implementation and protocol. Derived triangle indices are read-only; agents edit source bytes.

The JSON schemas describe structure. Matched correspondence, exact station gaps, winding, section topology, strip intersections, current budget admission and lifecycle behavior require semantic execution. Source-valid geometry can still fail binary32 delivery, and schema validity establishes no destination result.
