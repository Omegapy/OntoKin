# C076 shared-adapter review

## Source and independence

Reviewed commit `e114f9bf3a99d27f5655c43cd2240a09d198cbe9` against the frozen contract/fixture commit `2c0fe255281a9e3dde482a5845f2587728106e30`. The root-owned adapter implementation is commit `6f9af2ec9eccf7f384f8fd8a5b56501583565536`.

This is an independent source review of the shared adapters. The reviewer authored `ontokin/holes.py`, `ontokin/holes_delivery.py` and `tests/test_holes_geometry.py`; no independent-review claim covers those files. Agent service internals, schemas, independent oracle implementation and untracked acceptance/browser runners are also outside this review's ownership scope. Their relevant interfaces were read only as context.

No product runtime test was executed during this review. The accompanying JSON records the exact Git blob identities, byte sizes and SHA256 hashes of reviewed files and contextual inputs. Working-tree activity does not change the immutable reviewed source identity.

## Required repair

**C076-SHARED-001 — The new summary omits three promised numeric counts.**

The frozen adoption's inspection contract promises cap, palette and used-region counts. `holes_inspection.holes_summary` returns cap region names, `palette_keys`, and nonempty `regions`, but does not expose those numeric counts. Add `cap_triangle_count` for the number on each cap, `palette_count` including valid unused materials, and `used_region_count` counting emitted regions. Keep earlier loft/simple-extrusion summaries unchanged. Synchronize the .9 response schema/documentation and add a summary assertion, including a valid unused palette entry.

Root acknowledged this finding and assigned the targeted repair. At this review's source identity, it remains unresolved. A later identified readback can close it without relabeling this original review.

## Findings supporting the adapter design

- Source `0.9` dispatches to `Parser09`, which retains `Parser07`'s entry-only execution declaration and initializes the exact `polygon-holes-0.1` profile. Earlier parser branches retain their selections.
- Profile membership adds the new profile explicitly. Hole type/constructor lookup uses the declaring module's profile. Existing extrusion constructors remain available in .9, while older declaring modules cannot acquire ring constructors.
- The linker rejects an earlier declaring module importing a .9 dependency. The .9 profile can reuse .8 and earlier modules through the existing version-specific rules; the check applies on every import edge, including transitive edges.
- `polygon_ring` receives typed `Int`, `String`, and `Keyed<PolygonVertex>` values. `extrude_rings` receives typed rings, palette, depth and region names. Source locations remain attached to the geometry recipe, and the normal construction path attaches topology failures to the authored occurrence.
- `placed` accepts ring geometry only in .9 and retains the existing self-frame and nonnested-placement rules. `HolesSurfaceMesh` carries source corner identities through the existing rigid placement calculation; the legacy `SurfaceMesh` fields and `.8` return path are unchanged.
- Writer and supplied-byte reader both reject holes under an older destination. The matching `.9` source/target is also enforced by `checked_contract`. Geometry metadata, PBR identities, region indices, exact quantized positions/normals and source provenance retain their existing checks.
- The hole delivery checker receives the decoded shared position accessor after the exact source/placement comparison. It runs once per logical surface's shared attribute pair. The existing guards wrap arbitrary caller exceptions before geometry translation, and the execution path restores an active callback exception through the existing callback marker/exception chain.
- `.9` uses the same admitted `SharedExecutionBudget`, compiler work, evaluation work and original deadline. Omitted requests retain existing defaults. Explicit `execute_holes_export` selects the new binding; CLI export/Agent defaults remain their original values. A caller cannot override the alias's profile through a second keyword argument.
- Ring inspection uses sorted authored rings/vertices. Native pages keep revision/query bindings and use the .9 program profile even for inherited geometry. Existing loft and simple-extrusion summary schemas remain distinct.
- Polygon geometry uses the uncached constructor fallback in the inherited loft cache; no incomplete ring cache key was introduced. This is correct but means complete-request work must include each actual construction and supplied-byte check.

No additional source-level integration blocker was identified in the reviewed adapter changes. This does not substitute for executed acceptance, inherited regression, compatibility, browser or resulting-main evidence.

## Targeted verification obligations

1. Validate the repaired summary counts and .9 schema, including an unused material and zero-hole geometry.
2. Execute the complete maximum fixture under its frozen 400,000-operation/80,000-ms source request. Record cumulative work, rather than relying on the worker's component counts. Preserve a lower-cap refusal with no artifact publication.
3. Exercise `.8 -> .9` import rejection, `.9 -> .8` reuse, mismatched source/target bindings, and .9 inherited loft/simple-extrusion inspection.
4. Inject a caller `SurfaceError`, an `OntoKinError`, and an ordinary exception during both ring construction and delivered-geometry checking. Assert original exception identity through the public direct export boundary.
5. Run the actual frozen source/Agent acceptance and applicable inherited cohort on an identified complete candidate. Retain earlier default/profile results and all failed attempts.

Root separately reported an acceptance run after the reviewed cut. This source review does not independently assert its results; the acceptance receipts and their actual source identities remain authoritative.
