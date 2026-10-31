# Agent/0.12 blind polygon pockets

The [C079 decision](../polygon-pockets-v0.1/ADOPTION.md) selects source `0.12`, `polygon-pockets-0.1`, Agent/0.12 and recorded GLB/0.12. Earlier source declarations, services, stores, destinations and defaults retain their adopted meanings.

- [request.schema.json](request.schema.json) covers all twelve operations, exact source patches and caller budget reductions.
- [response.schema.json](response.schema.json) covers execution receipts, bounded mesh pages and six distinct native geometry summaries.
- [diagnostic.schema.json](diagnostic.schema.json) retains source-bound diagnostics, including inherited errors and `OKL-E-POCKETS-*`.

`PocketsAgentService` uses `pockets-program-agent.sqlite3` and store schema `ontokin.pockets-program-agent-store/0.1`. Every operation retains one cumulative work counter, the original deadline, current trusted host authorization, immutable accepted revisions, cancellation, durable identical retries and atomic publication. Omitted source requests remain 100,000 operations and 30,000 ms, including on larger hosts. Explicit larger requests require independent host authorization; caller caps only reduce them.

## Pocket inspection

`ontokin.polygon-pockets-summary/0.1` describes one constant-outline body with zero through eight blind pockets. Its `profile` is `polygon-pockets-0.1` and `family` is `polygon_pockets`. `outer_vertices` is sorted by explicit vertex order. `pockets` is sorted by explicit pocket order, and each pocket's vertices retain their own order. Every vertex supplies `key`, `order`, `point_m` and `side_region`.

| Field | Meaning |
| --- | --- |
| `height_m` | Authored body height, from 0.001 through 100 meters. |
| `pockets[].key`, `order`, `vertices` | Stable pocket identity, traversal order and its clockwise XY boundary. |
| `pockets[].depth_m` | Authored canonical binary64 depth. |
| `pockets[].exact_remaining_base_m` | Exact rational difference between canonical height and authored depth. |
| `pockets[].floor_m` | That exact difference rounded once to binary64; actual source vertices use this floor. |
| `pockets[].remaining_base_m` | The same rounded source value as `floor_m`. |
| `pockets[].effective_depth_m` | Exact difference between canonical height and the rounded floor. |
| `pockets[].floor_region` | Material key owning that pocket's complete floor. |
| `pocket_count`, `authored_vertex_count`, `logical_vertex_count` | Pocket, authored boundary vertex and complete lower/top vertex counts; maxima 8, 64 and 128. |
| `bottom_triangle_count`, `top_triangle_count`, `floor_triangle_count`, `wall_triangle_count` | Face counts in the distinct material domains. |
| `triangle_count`, `vertex_count` | Complete triangles and flat mesh corners; maxima 252 and 756. |
| `palette_count`, `used_region_count` | All authored materials and the materials that emit triangles. |

Both exact arithmetic fields are objects containing decimal-string `numerator` and `denominator`. Values are reduced and denominators are positive. The schema requires their positive integer wire shape. Construction and independent evidence establish their reduction, arithmetic equality and geometric meaning.

`bottom_region`, `top_region`, sorted `palette_keys` and sorted emitted `regions` retain material ownership. The outgoing vertex region owns each wall edge; `floor_region` owns an interior floor. `local_visual_placement` describes the separate one-time rigid placement. `physical_participation` remains `none`, and `motion_authority` remains `carrier_evaluated_world_pose`.

The summary distinguishes authored depths from rounded floor coordinates and effective geometry. It does not infer geometry from metadata. Complete domain, incidence, contact, orientation and volume predicates still apply to the actual source and delivered positions. A source-valid body can fail binary32 delivery after placement.

## Inherited geometry and pages

Earlier elliptical-loft, simple-extrusion, through-hole extrusion, station-loft and framed-loft summaries retain their original schemas, profiles and fields. Their definitions are preserved in the .12 response schema. Discovery retains the inherited constructor records and summary contracts. `inherited_geometry_interfaces` supplies compact references to the unchanged station-loft and framed-loft bindings and their schemas; the complete current `polygon_pockets_interface` states all twelve operations, limits and current host authority once. This avoids duplicating prior transport and policy descriptions in every page while retaining their published specifications.

The .12 catalog holds immutable source-defined metadata, following the existing static construction catalog. Every request materializes and charges a fresh complete copy, supplies its current host policy and service limits, extracts any linked declarations under that request, and measures and hashes the resulting catalog. No accepted revision, run, linked program, host grant or prior response is retained in the template. Both inherited publication checks remain inside the original request allowance.

Agent/0.12 mesh pages identify the `.12` entry profile even for inherited geometry. Pages contain at most 256 triangles and bind their cursors to revision, occurrence, region filter, geometry, implementation and protocol. The pocket body itself has at most 252 triangles. A caller can request smaller pages; derived corners and triangles remain read-only inspection data.

## Editing and actual workflow

All twelve operations are explicit: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. A depth edit acts on exact UTF-8 `.ok` bytes with file revision and expected-text preconditions. An invalid candidate preserves accepted source, valid runs, stored artifacts, siblings and pinned library bytes. Nominal occurrence identity must remain continuous after an accepted repair.

An export succeeds only after actual delivered geometry and resource admission. Failed delivery does not publish a partial artifact. Retried identical requests return their durable result; changed payloads under an existing request identity are refused. Current host authorization also applies to later use of stored runs and artifacts.

Schema validity establishes a wire shape, not successful construction, a complete agent workflow or release acceptance. Recorded GLB and browser evidence do not establish Unreal import or live engine physics.
