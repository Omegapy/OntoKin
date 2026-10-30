# Agent/0.9 polygon holes contract

The [C076 adoption](../polygon-holes-v0.1/ADOPTION.md) explicitly selects source 0.9, `polygon-holes-0.1`, Agent/0.9 and recorded GLB/0.9. Earlier bindings and defaults retain their meanings.

- [request.schema.json](request.schema.json) defines all twelve inherited operations, caller execution caps and exact source-file edits
- [response.schema.json](response.schema.json) defines envelopes, execution receipts, ordered ring summaries and bounded triangle pages
- [diagnostic.schema.json](diagnostic.schema.json) preserves the source-bound diagnostic shape

`HolesAgentService` uses `holes-program-agent.sqlite3` and store schema `ontokin.holes-program-agent-store/0.1`. Each request retains one original work counter and deadline, current trusted host authorization, revision checks, cancellation, durable retries and atomic publication. Omitted source limits remain 100,000 operations and 30,000 ms.

The new `ontokin.polygon-holes-summary/0.1` describes ordered ring keys, roles and orders, with each ring's ordered keyed vertices, local planar points and outgoing wall regions. It includes ring, hole and authored-vertex counts; cap and palette keys; `cap_triangle_count` for each cap; `palette_count` including unused palette entries; `used_region_count` for emitted regions; actual triangle/corner counts; rigid local placement; and explicit visual-only physical and motion semantics. Vertex keys are local to their ring. Derived triangle and corner indices are inspection identities; agents change exact source bytes.

Mesh pages identify the actual .9 program profile. Inherited loft and simple-extrusion summaries retain `ontokin.surface-summary/0.1` and `ontokin.polygon-extrusion-summary/0.1` respectively. The JSON schemas constrain structure; geometric containment, winding, cross-ring uniqueness, cumulative limits and workflow behavior require executed semantic checks. Schema validity alone establishes neither valid geometry nor completed delivery.
