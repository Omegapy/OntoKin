# C077: matched-topology polygon ring lofts

This increment adds source-authored matched polygon sections for tapered housings, chamfered profiles and hollow ducts. Candidate `ece7904ffbca102e05c113049de5dfef4e9f3afe` passed the frozen source and Agent workflow, independent delivered-geometry and destination checks, actual capture review, durable evidence reconciliation and input preservation described below. Complete inherited local-driver result: `passed all 11 selected steps on candidate ece7904ffbca102e05c113049de5dfef4e9f3afe`. Evidence publication and verified main integration have separate boundaries.

The increment implements the [C076 continuation](../polygon-holes-2026-10-30-c076/NEXT-TASK.md) while preserving the complete [GOAL](../../../GOAL.md). The separately selected source/Agent/GLB `.10` capability remains experimental development under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md). Candidate evidence does not certify a completed development integration or release.

## Source and publication roles

| Role | Commit | Tree or evidence |
| --- | --- | --- |
| Verified C076 starting main | `6c28722b6a6b67e44f7e4ba1617ca6e5fad22f26` | `560adc2cce7c62c102c0932e4649771b997ec75f` |
| Published versioned adoption | `4d1b15f5859e7f08feb8041b67c112d9f1485174` | `c1ba1cb22b8c3cc6126a6688813dd7bbbced9f97` |
| Published independent input freeze | `3dd722dcacadbb51860cf8d7b768cd9d664f41f7` | `ac5dc85b631e2189ac4c535e515983ea1ff72122` |
| Executed and reviewed candidate | `ece7904ffbca102e05c113049de5dfef4e9f3afe` | `7072ddac0b0e8142ee4a4b0a8423dc291231382d` |
| Evidence publication | `pending publication; actual identity will be recorded separately` | `pending publication` |
| Main integration lease | `not yet acquired` | `not yet acquired` |
| Actual merge | `not yet merged` | `not yet merged`; PR `https://github.com/Omegapy/OntoKin/pull/75` |

The [adopted decision](../../language-design/polygon-loft-v0.1/ADOPTION.md) is OK-LANG-010/0.1.0 and OK-AGENT-010/0.1.0. It and the independent [fixture freeze](../../../examples/polygon-lofts/acceptance-freeze.json) were published before runtime implementation. The manifest identifies 83 input files, including 79 `.ok` sources. Its 74 case records comprise **23 valid cases, 47 invalid cases and four source-valid delivery refusals**. The additional source files supply the pinned reusable library, composition, generated occurrences and exact repair variants. All 74 predetermined outcomes were subsequently checked on the identified candidate; the frozen expectations were not regenerated from product results.

The bounded C077 implementation scope is recorded in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6532808985). Local worker cuts, their integrated counterparts, failed preparations and later executed candidates have distinct identities. [REVIEW.md](REVIEW.md) records those roles and the corrections. The [candidate input-preservation record](candidate-input-preservation.json) binds exact Git paths, modes, blobs and recorded source-file hashes.

## Adopted capability

Explicit `ontokin "0.10";` and `profile "polygon-loft-0.1";` select the new source semantics. `RingLoftAgentService` uses `ontokin.agent/0.10`, and recorded delivery selects `ontokin.glb/0.10`. Earlier defaults remain CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1. Earlier declaring modules cannot import `.10` modules; a `.10` entry may import compatible earlier pinned modules without changing their declared source semantics.

`polygon_section(order, station, rings)` constructs an immutable `PolygonSection` from an integer order, a length station and `Keyed<PolygonRing>`. Its enclosing keyed entry supplies the section identity. `loft_rings(sections, palette, bottom_region, top_region)` constructs visual geometry from typed keyed sections and materials. The `.9` ring and vertex constructors remain the source of outer and inner boundaries.

Each section lies in local XY at a local Z station. Explicit orders select section, ring and vertex traversal independently of declaration order. Every section must retain the first section's ring keys, roles and orders, and each matched ring must retain its vertex keys and orders. Coordinates and outgoing-edge material regions may change. A source corner is identified by `(section key, ring key, vertex key)` within its occurrence. No nearest-point matching, automatic cyclic alignment, resampling, topology change or vertex insertion is implied.

| Domain | Adopted bound |
| --- | --- |
| Sections | 2–8 |
| Rings per section | One counterclockwise outer ring and zero through eight clockwise holes |
| Vertices per section | 3–64 across all rings; at least three per ring |
| Total authored vertices | At most 256 |
| Explicit orders | Unique integers from 0 through 65,535 within their respective scopes |
| XY coordinates | Finite canonical binary64 values within ±100 meters |
| Z stations | Finite values from 0 through 100 meters, increasing in section order |
| Minimum station separation | Exact rational difference of canonical binary64 stations at least canonical binary64 0.001 meter |
| Palette | 1–16 valid named PBR materials |
| Largest simultaneous mesh | 540 triangles and 1,620 flat corners |

The station rule deliberately rejects a difference that appears to be one millimeter in decimal source but is smaller after canonical binary64 representation. For example, stations `1[m]` and `1.001[m]` fail that exact minimum. No subtraction rounding allowance or epsilon widens the adopted domain. All inherited simple-ring, winding, containment, distinct-point, collinearity and non-touching rules apply separately to each section.

### The triangles define the surface

For each outgoing edge `a → b` of a lower section and its matching upper edge, the authoritative strip triangles are `(a_lower, b_lower, a_upper)` and `(b_lower, b_upper, a_upper)`. The diagonal from `b_lower` to `a_upper` is fixed. For a noncoplanar edge quad, this triangular surface can differ from intermediate polygons obtained by linearly interpolating all corresponding vertices. The contract promises the specified triangles.

Both triangles use the lower outgoing vertex's region. The terminal section emits no strip, although every terminal region must still name a palette material. The first and last caps are triangulated independently under the exact `.9` cap algorithm. The first cap is reversed, the last has positive local winding, and intermediate sections have no caps. Each face has its own outward unit normal and three flat corners. Used material keys determine regional PBR primitives; an unused valid material emits none.

For `S` sections, `N` vertices per section and `H` holes per section, each endpoint has `N + 2H - 2` cap triangles; strips contribute `2(S - 1)N`; the complete mesh has `2SN + 4H - 4` triangles and three flat corners per triangle. The two frozen maxima separately use eight sections with 32 vertices each and four sections with 64 vertices each. Both have eight holes, 256 authored vertices, 540 triangles and 1,620 flat corners.

The quarter-turn authority control forms a 2 × 2 × 1 box with volume 4 m³ and area 16 m² under the specified triangles. A negative quarter-turn instead pinches the triangular surface despite valid endpoint polygons. Separate fixtures exchange otherwise disjoint hole identities and pinch correspondence edges. Their endpoint validity cannot authorize a crossing or folded strip surface.

### Complete source and actual delivered admission

Source admission uses exact rational predicates over canonical binary64 positions. It establishes identity consistency and separation, nondegenerate faces, exactly one directed incidence and one opposite incidence per mesh edge, no intersection beyond a source-shared vertex or edge, and positive exact signed volume. Cap coverage retains the inherited exact domain rules. Invalid geometry is rejected without hidden welding, clipping, winding reversal or repair.

The bounded section/ring/vertex/material input is captured into immutable leaves before later callbacks can mutate host-owned data. Geometry work, cap construction, emission, inspection, encoding and supplied-byte checking remain under the same request counter and original deadline. Cancellation and host callback exceptions retain their identity.

Rigid local placement is baked once in the carrier's self frame. The **actual placed binary32 positions** are then checked again in three dimensions, including identities, nonzero outward faces, closed opposite edge incidence, shared-simplex intersections and positive volume. Rounding after rotation need not preserve an endpoint plane. Source-valid openings or clearances that collapse or touch in delivery fail export. Normals, regional material values, source-quantized attributes, recorded carrier motion and inherited tolerances remain independently checked. The local geometry tolerance remains 0.00001 meter.

These are visual surfaces. They introduce no mass, inertia, collision shape, attachment, following relation or motion authority. Existing `loft`, `extrude` and `extrude_rings` retain their own rules. Their inspection summaries retain their original schemas and profile meanings inside a `.10` program.

## Agent workflow and execution authority

The separate `ring-loft-program-agent.sqlite3` store has schema `ontokin.ring-loft-program-agent-store/0.1`. The [Agent guide and schemas](../../language-design/agent-v0.10/README.md) expose all twelve operations: **discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page**.

The implementation preserves exact UTF-8 patch preconditions, complete-file source scopes, nominal occurrence continuity, immutable accepted revisions, failed-edit rollback, current trusted host authorization, cumulative work, original deadlines, durable identical retries, changed-payload rejection and atomic artifact publication. Derived triangle indices remain inspection data. The new `ontokin.polygon-loft-summary/0.1` reports authored sections and matched identities, counts, station range, materials, strip/cap totals and local placement. Mesh pages contain at most 256 triangles and bind the actual `.10` program revision, occurrence, region, geometry, implementation and protocol.

The executed end-to-end workflow repairs one upper-hole vertex in the first of two reusable occurrences. It preserves the unchanged sibling, pinned module bytes, source identities and rollback state. Independently checked geometry gives the original first and sibling volumes as 21 m³ and the repaired first volume as 21.375 m³. Generated parts retain stable keyed identities and heights of 1, 2 and 3 meters under recorded parent motion. The [independent Agent evidence review](agent-evidence-review.json) reconciles actual accepted source, durable requests, stored artifacts and retrieved bytes.

Ordinary omitted limits remain **100,000 operations / 30,000 ms**, including on a larger host. The two maximum fixtures explicitly request **2,000,000 operations / 80,000 ms**, with matching independent host authorization. Caller limits only reduce the source request. No stage resets the request ledger or deadline. Modeled animation duration remains separate from computation time, and higher-budget outcomes cannot retroactively pass an earlier fixed-budget gate.

## Executed candidate evidence

The [validation summary](validation-summary.json) binds the exact receipts and execution environments. There are **119 new test methods** in the candidate: 35 geometry, 31 Agent, 45 independent-oracle and eight integration methods. A preceding 118-method focused run passed on preparation `50d65d3a89f152ee8afcc0f672825cab1d925088`; the later station-type correction added one integration method. Candidate unit execution is reported with the complete driver below. Focused, full-suite and separate Agent cohorts overlap and are not added together as independent test totals.

| Check | Observed result |
| --- | --- |
| Complete unit suite | `3448` methods; failures `0`, errors `0`, skips `0`; CPython 3.12.14 |
| Selected complete local driver | `11 / 11`; source and Git identity `unchanged`; result `passed all 11 selected steps on candidate ece7904ffbca102e05c113049de5dfef4e9f3afe` |
| Frozen source acceptance | All 74 cases / 418 assertions passed: 23 valid, 47 invalid and four source-valid delivery refusals |
| Actual Agent workflow | 68 exchanges / 66 durable request identities; all twelve operations exercised, including a successful constructed-level validation and queued cancellation |
| Wire schemas | All 68 actual request/response exchanges validated, including rejection and failure envelopes |
| Artifact reconstruction | All 49 chunks reconstruct the exact 49,868-byte stored GLB; file, returned digest and SQLite BLOB agree |
| Independent geometry and destinations | All 25 source-built GLBs passed geometry, PBR and identity checks; zero Khronos errors and zero warnings |
| Recorded playback | 145 native and 60 browser occurrence/time observations; the separate evidence audit independently decoded all 145 recorded samples |
| Actual image review | 16 captures across eight artifacts: 14 retain byte-identical previously inspected images, and two changed final captures were opened and inspected directly |
| Maximum section workload | 946,268 operations / 5.765 seconds within the frozen 2,000,000 operations / 80,000-ms request |
| Maximum per-section vertex workload | 1,246,457 operations / 10.589 seconds within the same request |
| Repaired Agent export | 37,603 operations under unchanged 100,000 operations / 30,000-ms defaults |
| Independent Agent evidence reconciliation | 2,132 consistency checks passed, zero failed; these are evidence-audit checks, not product-test executions |
| Candidate input preservation | All 4,098 baseline paths retained; all 1,046 old protected paths and 85 frozen inputs retain exact modes and blobs |

The acceptance wrapper took 36.599 seconds and the separate destination wrapper took 5.599 seconds. These timings and the workload figures are observations on the identified host, not cross-platform performance guarantees. Candidate acceptance and destination command receipts both retain unchanged complete before/after source inventories. Only CPython 3.12.14 has been executed in these candidate roles; other required Python versions and pending external release attestations are not supplied by these results.

The failed preparation at `50d65d3a89f152ee8afcc0f672825cab1d925088` remains separately recorded. It reached the maximum workloads but failed the frozen `wrong-station-type` diagnostic before any Agent exchanges. The constructor correction in `fb6c99a7219f3486b709aa2bd34972aba088b537` distinguishes a non-Quantity type error from a wrong-dimension unit error. The corrected preparation and the published candidate each have their own acceptance/destination receipts; the candidate figures above come from its own executions.

The independent supplied-byte oracle checks actual decoded corners against frozen source identities, exact prescribed strip triangles, complete endpoint cap domains, cap overlap and boundaries, full edge incidence, three-dimensional contacts, outward normals, PBR ownership, area, volume and recorded motion. Its exact edge/triangle witnesses and closed coplanar segment clipping are separate from the production intersection algorithm, and it imports no product triangulator or intersection predicate. Hand-built hostile controls test the checker independently of product exports. The actual artifact path also checks the active scene, single animation clip and geometry-free generated parent.

Independent destination execution used Node 22.14.0, Three.js 0.180.0, gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1, esbuild 0.25.10 and Chromium 141.0.7390.37. The [visual review](visual-review.json) records every final PNG hash and how it was inspected. Fourteen final images exactly match the individually reviewed preparation captures; their findings are reused by complete byte equality. The two changed repaired-assembly captures were separately opened and inspected. No claim is made about the cause of their raster-byte difference. No visible defect requiring correction was found. Image review does not rerun geometry validation or establish complete motion, watertightness, positive volume or freedom from intersections.

The [Agent evidence audit](agent-evidence-review.json) reconstructs the supplied GLB from raw returned chunks and compares it with the stored BLOB and file. It independently reconciles all 66 request identities, exact accepted and rejected source revisions, the unchanged pinned library and sibling, retries, current policy failure, run records and artifact ownership. It decodes actual binary32 motion accessors for all 25 artifacts. Its geometry role reconciles the already executed independent oracle reports with frozen facts; it does not claim another geometry execution.

## Review, preservation and integration

[REVIEW.md](REVIEW.md) and the [source-review summary](source-review.json) preserve the three independent worker review scopes, acceptance-checker findings, isolated Agent-test setup correction, station-type diagnostic correction and original failed preparations. The reviewed finite implementation and corrected evidence tooling had no remaining identified blocker in those scopes. The candidate acceptance, destination, audit and visual results provide the separately identified executed evidence. Complete inherited validation and external release roles have their own requirements and records. No reviewer consistency-check count is a product-test count.

The [archive descriptor](evidence-archive.json) is `saved and byte-verified: 1599 members, 14870666 bytes, SHA256 ea13615e6cf9bd5c606fc28cc619986b4d9bc672aeefb806499206c1b935fee4`. The archive retains original and corrected preparations, commands, logs, source inventories, Git identities, protocol exchanges, durable store, supplied GLBs, destination observations and image attestations. Members keep their names relative to `validation_c077`, such as `candidate-acceptance/summary.json`, with no extra `validation_c077/` prefix. `C077_Validation_Evidence.manifest.json` records every member's size and SHA256; the receipt binds the manifest and ZIP identities. Evidence publication, merge, final-main verification and portable handoff occur at separate boundaries and require their own records.

The [preservation comparison](candidate-input-preservation.json) accounts for all 4,203 candidate paths: 4,080 unchanged baseline files, 18 deliberate modified baseline files, 105 additions and zero removals. The 18 changes are the two navigation files and 16 shared adapters, all listed in the record. All 1,046 baseline files under tests, examples, schemas, workflows and language-design prefixes retain exact bytes and modes. All 85 adoption/freeze paths are unchanged, including each of the 83 manifest-bound inputs. Both candidate command inventories bind all 4,203 paths to verified Git blobs, modes, byte sizes and SHA256 contents.

The evidence publication leaves STATUS unchanged. A main integration lease is appended separately. Actual parent order, independently calculated merge tree, eligible-input equality and fresh resulting-main checks belong in the later plain record path `integration.json`: `pending actual merge and focused checks`. Only after those checks may the final STATUS publication replace the current checkpoint and release the lease. Final-main verification, portable delivery and explicit scope closure remain `pending separate final-main, packet, delivery and closure receipts`. These pending roles are not implied by the candidate checks, and focused merge checks will not be labeled as a second full regression or browser execution. Hosted workflows retain their manual-only, default-false policy; no hosted execution is claimed here.

## Remaining gates and continuation

Recorded GLB and Three.js/Chromium playback do not establish Unreal Engine import or live destination physics. Blind cavities, branching ducts, arbitrary bevel offsets, Boolean operations, automatic mass/inertia/collision, textures/mapping and skin deformation remain outside this increment unless independently adopted elsewhere. The full GOAL remains unchanged.

Historical original28 remains **24/28, failed**, with **P11/P16/P23/L03 unresolved**. M1 remains rejected; comparison accounting and passive authority remain open. C035 remains held, including adverse timing. C057 and complete reach acceptance remain open. Preserve original fixtures, horizons, rates, helpers, equations, independent oracles and tolerances, the 32,768-bit operand limit, 256-entry numerical cache and 64-step reference-cursor bound. Complete reach still needs all 28 source recordings and ten Agent artifacts, CPython 3.11/3.12/3.13, independent rates/native/browser/visual and hostile/inherited roles, formal input closure and all R01–R12/Q01–Q22 obligations. The earlier selected reports' 16 pending external case attestations remain pending unless separately completed by actual role-specific evidence.

C068 remains unadopted, C069 rejected, C070 unselected and C071 rejected. C059's storage cause remains unestablished. Historical Git LFS migration remains unfinished; future tracking and archive inclusion did not migrate old payloads. Preserve the history-only archive branch and explicit shallow-history boundaries. Nothing in C077 closes the remaining language/library, richer appearance, continuous forces/torques, general dynamics, mechanisms, creatures, locomotion, flight/swimming, vegetation, terrain/buildings, liquids/deformable solids, transitions/live engines, measured scale or direct-tool comparison goals.

After actual C077 integration, final verification, portable delivery and explicit scope closure, the [recommended next bounded task is C078: explicitly framed polygon ring lofts](NEXT-TASK.md). It begins with a separately versioned decision and independent freeze. Naming that continuation adopts no syntax or limits, starts no worker or schedule and authorizes no C078 implementation in this session.
