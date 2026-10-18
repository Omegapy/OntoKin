---
project: OntoKin
document_id: OK-AGENT-003
title: Native Surface Program Workflows
version: 0.1
date: 2026-10-18
status: adopted-interface-contract-implementation-and-release-evidence-pending
language_contract: OK-LANG-003 v0.2 with OK-LANG-003-C1
agent_contract: ontokin.agent/0.3
diagnostic_contract: ontokin.diagnostic/0.2
mesh_page_contract: ontokin.surface-mesh-page/0.1
---

# Native surface program workflows

## 1. Authority, scope, and inheritance

This contract extends [OK-AGENT-002](OK-AGENT-002-program-bundles-and-atomic-source-edits.md) to the native `ontokin "0.3"` / `surface-0.1` language defined by [OK-LANG-003](../language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) and its [numeric clarification](../language-design/surface-v0.1/clarification-c1.md). The interface decisions were recorded in [issue #8](https://github.com/Omegapy/OntoKin/issues/8) before the corresponding service implementation.

**All OK-AGENT-002 rules remain mandatory unless this document explicitly replaces them for Agent/0.3.** This includes immutable source bundles, exact UTF-8 patches, nominal occurrence identity, source provenance, atomic candidate acceptance, accepted-once snapshots, run state, retries, cancellation, unknown outcomes, result expiry, worker fencing, and response-before-commit limits. This contract does not change Agent/0.1 or Agent/0.2. It does not migrate their requests, stores, programs, cursors, or artifacts.

Agent/0.3 adds native surface summaries, bounded mesh pages, and native GLB/0.3 delivery to the inherited authoring workflow. Mesh pages expose constructed visual geometry. They add no physical body, motion authority, collision surface, texture, skin, or live destination controller. The full [GOAL](../../GOAL.md) and the complete M01–M12 gate remain separately tracked in [STATUS](../../STATUS.md). Publication of these shapes and rules is not evidence that a service or release has passed them.

## 2. Explicit binding and separate durable state

Python clients select the new interface explicitly:

```python
from pathlib import Path
from ontokin.program_agent import ProgramAgentService

with ProgramAgentService(Path(".ontokin-state"), protocol="ontokin.agent/0.3") as service:
    response = service.handle(request)
```

The Python constructor's default remains `ontokin.agent/0.2`. The command-line binding is:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.3 --store .ontokin-state
python3 -m ontokin agent --protocol ontokin.agent/0.3 --store .ontokin-state --request request.json --wait
```

The CLI's default remains Agent/0.1, as specified in OK-AGENT-002. A request's `schema_version` does not choose a protocol or store. Mismatched requests reject using the explicitly selected response protocol, including malformed-JSON and startup error envelopes. The inherited queued JSONL, synchronous `--wait`, worker draining, and one-request retention behavior remain unchanged.

Agent/0.3 uses **`surface-program-agent.sqlite3`**, identified by **`ontokin.surface-program-agent-store/0.1`**. Agent/0.2 continues to use `program-agent.sqlite3`; Agent/0.1 continues to use `agent.sqlite3`. These databases remain independent when they share a directory. Equal project or request IDs across protocols do not join their accepted heads, retry records, runs, or artifacts. The stored complete source bundles continue to use `ontokin.bundle/0.1`; its hashing, exact source bytes, dependency pins, and persistence rules remain unchanged.

An Agent/0.3 program requires a `surface-0.1` entry. Compatible imported older component definitions retain their own declared profiles under OK-LANG-003. Agent/0.2 rejects a surface entry instead of labeling it construction support. No service reinterprets the profile by changing a result tag. Structurally valid unsupported or invalid source can remain an immutable diagnostic candidate; retaining that candidate does not accept it or grant ordinary evaluation, export, or mesh-page access.

## 3. Requests, envelopes, and inherited operations

The [request schema](../language-design/agent-v0.3/request.schema.json) and [response schema](../language-design/agent-v0.3/response.schema.json) publish the new wire shapes. The [diagnostic schema alias](../language-design/agent-v0.3/diagnostic.schema.json) explicitly reuses `ontokin.diagnostic/0.2`. There is no `ontokin.diagnostic/0.3` payload in this contract. Native surface diagnostics already use the containing program revision and actual source-unit locations provided by diagnostic/0.2; the new service must preserve them.

The inherited operations are `discover`, `create`, `edit`, `validate`, `inspect`, `evaluate`, `reset`, `status`, `cancel`, `export`, and `artifact`. Their required fields and meanings remain those of OK-AGENT-002, with these changes:

| Field or behavior | Agent/0.3 contract |
| --- | --- |
| Request and response `schema_version` | `ontokin.agent/0.3` |
| Supported discovery and entry profile | `surface-0.1` |
| Discovery catalog `schema_version` | `ontokin.agent-catalog/0.3` |
| Named destination | `ontokin.glb/0.3` |
| Additional operation | `surface.mesh_page` |
| Surface object inspection | Bounded summary at `result.items[i].geometry.surface` |
| Diagnostic payload | Unchanged `ontokin.diagnostic/0.2` |

The native catalog inherits compatible construction capabilities and adds the two surface leaf types, four constructors, fixed geometric limits, summary projection, and mesh-page operation. It identifies the explicit Agent/0.3 store and GLB/0.3 destination. Global capabilities describe the selected surface profile; linked module, definition, and member records retain their actual declaring source's profile and language version, including compatible `0.2` imports. Their source hashes, spans, and nominal identities keep the inherited meanings. A catalog revision fingerprints the returned content; it does not certify the listed source's construction, evaluation, or delivery. Default construction-profile discovery retains the earlier catalog's contents and identity.

Generic `requested_level: "delivered"` still requires an explicit supported destination. Delivery options require that destination and the delivered stage. Agent/0.3 does not route an export to GLB/0.1 or GLB/0.2. Artifact retrieval returns the retained native artifact's exact bytes and matching source/program/exporter identities; changing the protocol does not prove an external destination check.

Every response preserves the distinction between `program_revision`, which identifies the requested or candidate program, and `accepted_program_revision`, which identifies the current accepted head. A retained older program may have been accepted once and remain usable after the current head changes. It must retain its old revision in all results and artifacts. A never-accepted candidate remains available for inherited source inspection and diagnostic validation, but it cannot supply ordinary runs, exports, or `surface.mesh_page` output. A successful diagnostic validation alone does not turn it into an accepted program.

## 4. Surface summary inspection

An ordinary `inspect` request selecting the `geometry` field returns the existing geometry projection. For an occurrence with native `loft` or `placed(loft(...))` geometry, it also returns `geometry.surface` conforming to the response schema's `$defs.surface_summary`. Its fields are:

| Field | Meaning |
| --- | --- |
| `schema_version` | `ontokin.surface-summary/0.1` |
| `profile` | `surface-0.1` |
| `section_keys`, `stations_m` | Matching arrays in numeric station order, independent of source key spelling or entry order |
| `palette_keys` | All authored palette keys, including valid unused entries, in canonical key order |
| `facets`, `caps` | Authored angular facet count and `"flat"` or `"none"` cap policy |
| `triangle_count`, `vertex_count` | Complete occurrence counts; flat triangle corners give `vertex_count = 3 × triangle_count` |
| `regions` | Used groups as `{key, material_key, triangle_count}`, in canonical region-key order |
| `local_visual_placement` | `{frame: "carrier_self_frame", position_m, orientation_wxyz}`; positions in meters and unit quaternions in scalar-first order |
| `physical_participation` | `"none"` |
| `motion_authority` | `"carrier_evaluated_world_pose"` |

The existing `geometry.description` remains a bounded JSON-safe recipe. Neither the summary nor an ordinary geometry description contains unbounded positions, normals, or triangle-index arrays. Palette values and section values remain available through the inherited bounded value/source projections. Primitive geometry in a surface program retains its existing projection; the service does not attach a fabricated loft summary to a box, sphere, or empty object.

These are occurrence summaries. A class definition or collection does not acquire an occurrence frame, physical state, or mesh merely because its type can produce surfaces. Selecting additional source/state fields keeps the inherited source-scope and matching-run requirements. Geometry inspection does not advance a run.

## 5. Bounded `surface.mesh_page`

### 5.1 Request and selection

In addition to the four common request fields, the operation requires:

| Field | Shape and interpretation |
| --- | --- |
| `program_revision` | Exact retained SHA-256 program revision accepted at least once in this project and selected protocol |
| `element_id` | Exact occurrence identity array, not a display-path alias, class definition, collection, or derived vertex handle |
| `count` | Integer JSON token from 1 through 256; counts complete triangles |
| `region` | Optional nonempty region-key string; omission selects all triangles |
| `cursor` | Optional inherited opaque string or `null`; omission/`null` starts at filtered offset zero |
| `budgets` | Optional inherited work and response limits |

Explicit `region: null` is invalid. Unknown fields, including `frame`, `time`, `run_id`, and direct offsets, reject. A mesh page has one fixed coordinate system and ordering. It does not request evaluated world geometry. As with other protocol counts, `1.0`, `1e0`, Boolean values, and strings are not integer JSON tokens even when a JSON Schema validator's mathematical integer test treats a numeric value as integral. The transport validator must enforce this additional lexical/type rule.

Selection must resolve exactly one native surface object in the named revision. An absent or non-object identity rejects with protocol error `OKL-E-REVISION`. A known object with non-surface geometry reports `OKL-E-CAPABILITY-UNSUPPORTED`, retaining the known source/occurrence location. A request cannot silently select a sibling or substitute a primitive proxy. A nonexistent palette key reports `OKL-E-SURFACE-REGION`. A valid authored palette entry with no assigned triangles returns an empty complete page: `returned_triangles: 0`, empty mesh arrays, `filtered_triangles: 0`, `offset: 0`, `truncated: false`, and `next_cursor: null`.

### 5.2 Coordinates and deterministic order

`coordinate_system: "carrier_local_after_placement/0.1"` means finite binary64 positions in meters and dimensionless flat normals in the carrier object's local frame. The authored `placed(...)` translation and rotation are applied exactly once. Translation changes positions; rotation changes positions and normals. The carrier's world transform and animation are not baked into a page. Combining the page with an independently requested valid carrier pose produces world geometry. GLB/0.3 subsequently encodes its local vertices as float32 and reports the applicable quantization loss; a mesh page is not that binary encoding.

`ordering: "native_triangle_ordinal/0.1"` fixes zero-based triangle ordinals before material grouping. Sections are sorted by numeric station. The native generator emits each side interval in station order, each angular segment in increasing index order, and its two outward triangles in the order specified by OK-LANG-003. For flat caps it then emits all lower-cap fan triangles in angular order, followed by all upper-cap fan triangles in angular order. An open loft has no cap triangles. A triangle's source ordinal is the index of its first original flat corner divided by three.

Filtering preserves those original ordinals and their increasing order. It does not renumber them according to material groups. An authored section insertion can change derived triangle ordinals; surviving source section/occurrence keys retain their separate identity. Derived ordinals never become source-edit targets.

### 5.3 Exact result shape

A successful response has `operation: "surface.mesh_page"`, `requested_level: null`, `achieved_level: "constructed"`, and `run_id: null`. It uses the inherited complete envelope, with its result conforming to `$defs.mesh_page_result`:

| Result field | Meaning |
| --- | --- |
| `schema_version` | `ontokin.surface-mesh-page/0.1` |
| `implementation` | Inherited durable implementation record: `{name, version, source_code_sha256}` for the loaded service |
| `program_revision`, `element_id`, `path`, `profile` | Exact selected program, occurrence identity, display path, and `surface-0.1` |
| `geometry_sha256` | Fingerprint of the complete unfiltered placed mesh, topology, region mapping, and full palette, as described below |
| `coordinate_system`, `ordering` | The two versioned values fixed in section 5.2 |
| `region` | Requested region key, or `null` for an unfiltered page |
| `total_triangles` | Complete occurrence triangle count before filtering |
| `filtered_triangles` | Number of triangles selected by the region filter, or `total_triangles` when unfiltered |
| `offset` | Number of triangles already consumed in that filtered sequence |
| `returned_triangles` | Number of complete triangles on this page, from zero through requested `count` |
| `positions_m`, `normals` | Matching arrays of exactly `3 × returned_triangles` three-component vectors; at most 768 of each |
| `triangles` | Exactly `returned_triangles` page-local index triples; triangle `i` is `[3i, 3i+1, 3i+2]` |
| `source_triangle_ordinals` | One original native ordinal per returned triangle, strictly increasing and below `total_triangles` |
| `region_keys` | One actual authored region key per returned triangle, matching its native assignment |

An unfiltered page therefore contains exactly the next requested number of triangles, except at the end. A filtered page does the same within its selected subsequence. Flat corner duplication makes each page self-contained: no position, normal, or index references another page. The inherited durable commit adds the required `implementation` identity to this result just as it does to other object results. No optional result fields or additional mesh buffers are introduced by this version.

The envelope owns pagination. `truncated` is true exactly when `offset + returned_triangles < filtered_triangles`; in that case `next_cursor` is non-null. Otherwise `next_cursor` is null and `truncated` is false. A nonfinal successful page cannot contain zero triangles. Scalar counts, array lengths, index relations, ordinal order, and envelope/result consistency are semantic checks in addition to JSON Schema validation.

`geometry_sha256` is an implementation-scoped opaque SHA-256 fingerprint with domain `ontokin.surface-mesh/0.1`. It covers the complete unfiltered placed positions and normals, source triangle topology and region mapping, and all palette PBR values including unused entries. It is independent of page size and region filter. It is not a source revision, program revision, or GLB artifact hash. Clients compare the returned value; they need not reproduce an internal serialization or use the fingerprint to authorize source edits. The implementation identity is bound separately because an implementation change can change the concrete fingerprint or constructed approximation.

## 6. Cursors, resource limits, and atomic outcomes

A surface cursor binds the project, operation, program revision, exact occurrence identity, profile, region filter, complete geometry fingerprint, coordinate-system version, ordering version, implementation identity, and protocol. It also carries the next filtered-sequence offset under the inherited integrity mechanism. Invalid, tampered, or mismatched immutable-context cursors reject with `OKL-E-REVISION`; clients must not decode or edit them to select a new offset.

`count` is deliberately outside the immutable cursor context. A client can change it from one legal value to another on the next page using a new request ID. Work budgets can also be lowered for that new request. They cannot raise the profile limits or change the selected data. Reusing a request ID with a changed count or budget is still changed-payload reuse and rejects under the inherited retry rules.

An old cursor remains usable with its original explicitly named previously accepted revision while that snapshot and matching implementation context remain available. Advancing the current accepted head does not relabel the cursor. Applying the old cursor to a new revision rejects, even when the geometry happens to look the same. A geometry or region edit requires new pages and cursors for the newly accepted revision.

The existing source closure, object, operation, value-entry, elapsed-time, and JSON limits remain mandatory, together with the surface profile's aggregate mesh limit of 250,000 generated vertices and the request's 256-triangle page limit. A page size above `budgets.max_result_items` is an explicit resource failure; the service must not silently reduce it to satisfy that budget. All vector components, array entries, metadata, cursors, and envelope fields count toward JSON value-entry and encoded-byte limits. A small output page does not authorize unbounded construction or hashing of the selected program.

Construction, placement, region selection, full-mesh fingerprinting, pagination, and serialization must observe cooperative cancellation and remaining budgets. Cancellation or exhaustion cannot return a successful partial mesh. A geometry-page failure has no accepted-head or run advancement effect. The inherited final transaction and response validation protect create/edit acceptance, runs, artifacts, and cancellation effects from being committed when the required response cannot be returned. No page size promises hard real-time preemption or operating-system isolation.

## 7. Source repair and diagnostic integrity

Surface repairs use existing authorized UTF-8 source spans and exact program/source revision preconditions. An occurrence's public `rings` or `palette` initializer can be patched where the inherited inspection contract exposes that authority. The agent cannot write through a derived page-local vertex, triangle ordinal, or fingerprint. An imported shared definition does not become writable through an occurrence handle.

The required repair workflow begins with the exact [frozen library and Studio fixture](../language-design/surface-v0.1/README.md). It rejects an invalid candidate without advancing the accepted head, then changes the second occurrence's `"middle"` X radius from `0.48[m]` to `0.52[m]` in one accepted revision. Its first occurrence and imported library bytes/pin remain unchanged. A separate palette repair changes actual regional PBR factors while preserving unaffected source and geometry. Section insertion, source reordering, and removal preserve surviving authored keys while allowing the derived mesh to change under the fixed station-order rules.

All native compiler/exporter errors retain diagnostic/0.2 locations and source hashes. Unknown region queries use `OKL-E-SURFACE-REGION`; malformed wire shapes use the inherited protocol error envelope. A program-wide failure without an actual source span retains `primary: null` and `location_status: "program_condition_without_source_span"`. The service must not invent an entry-file span or emit a new diagnostic version merely because the request uses Agent/0.3.

## 8. Required execution evidence

The following obligations must be exercised through the actual versioned interface. They supplement the frozen M01–M12 cases; this document does not mark them passed.

| Obligation | Required observable result |
| --- | --- |
| Binding and storage isolation | Explicit Python/CLI selection; defaults and old envelopes preserved; separate store schema and durable request/head/run/artifact state |
| Discovery and summary | Actual surface built-ins and pinned definitions; bounded source-bound summaries with keys, stations, palette, placement, counts, and no hidden mesh arrays |
| Page geometry | Complete local triangle pages match independently checked native geometry, normals, winding, regions, counts, and GLB/0.3 float32 output within its stated tolerance |
| Pagination and cursors | Minimum/maximum/changing counts; filtered/unfiltered pages; known-unused empty region; unknown-region rejection; exact-context and tamper rejection |
| Revision isolation | Previously accepted old revisions remain readable; never-accepted candidates cannot page/evaluate/export; stale edits and old-cursor/new-revision requests fail without head changes |
| Targeted source repair | Invalid candidate rejection; radius and palette repairs; unchanged sibling/library bytes and pins; exported artifact identifies the repaired program |
| Topology edits | Section insertion/reordering/removal preserves source-key meanings and updates native triangle order/counts correctly |
| Lifecycle and failure | Identical retries, changed-payload rejection, queued/running cancellation, work/result limits, atomic rollback, durable restart, and unknown-outcome reconciliation |
| Compatibility | All earlier source, service, construction, numerical, GLB, browser, and preservation gates retain their versioned behavior |

Evidence must identify source bytes, implementation revision/digest, settings, actual requests/responses, native artifacts, independent destination results, and current CI. Schema validation proves wire shape only; it cannot prove native geometry, accepted-once access, revision integrity, or transaction behavior. The complete exterior-language gate, current construction C20 destination identity, and broader project goal remain open until their separate acceptance requirements have matching evidence.
