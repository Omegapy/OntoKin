# C076: source-authored holes in polygon extrusions

This reviewed development increment adds editable through-holes for plates, brackets and hollow cross-sections under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md). It implements the [C075 continuation](../polygon-extrusions-2026-10-30-c075/NEXT-TASK.md) while preserving the full [GOAL](../../../GOAL.md). Source/Agent/GLB .9 remains explicitly selected experimental development.

## Source and implementation roles

| Role | Actual commit | Actual tree |
| --- | --- | --- |
| C075 baseline | `84a523fb5d359f0e3f0a5104ac0856dbf5eff3a0` | `93fb9a943d1dbf424223199597f64674d6467f90` |
| Contract and fixture freeze | `2c0fe255281a9e3dde482a5845f2587728106e30` | `14b2fa7bc2e90d45d5364cc299f2828b0e3ec6a0` |
| Executed runtime candidate | `15c45f3ee3ed39883188e71bbde0e4d1482f8757` | `1eda7611fdd1294aaf7d9764e881dfdd8f41725e` |

The [versioned decision](../../language-design/polygon-holes-v0.1/ADOPTION.md) and all 63 [fixture files](../../../examples/polygon-holes/README.md) were published before implementation and remain byte-identical. [PR #74](https://github.com/Omegapy/OntoKin/pull/74) identifies publication and integration. Local author/worker cuts retain separate raw Git bodies, input identities and execution receipts; they are not substituted for the published candidate.

## Selected capability

Explicit source `0.9` / `polygon-holes-0.1`, Agent/0.9 and recorded GLB/0.9 support one counterclockwise outer ring and zero through eight clockwise holes, with at most 64 vertices across all rings. Ring and vertex orders are independent from declaration order. Vertex keys are local to their ring. Coordinates remain within ±100 meters, depth within 0.001–100 meters, and palettes contain 1–16 valid materials. Holes must remain strictly inside the outer boundary and mutually exterior. Touching, crossing, overlapping, nested and self-intersecting boundaries are rejected.

Exact predicates over canonical binary64 coordinates select a deterministic planar graph and establish complete cap coverage. Closed triangulation supplies outward flat normals, cap and outgoing-edge wall regions, rigid placement and reusable/generated occurrences. Source corner identities survive into supplied-position validation. Actual placed binary32 triangles must retain distinct identities, nonzero outward faces, closed opposite edge incidence and no intersections beyond their source-shared vertices or edges. Source-valid openings that collapse or touch during delivery fail explicitly. These visual surfaces supply no implicit mass, collision shape or new motion authority.

`HolesAgentService` provides all twelve versioned operations in a separate durable store. It preserves current host authorization, source-requested limits, one original request counter/deadline, exact source edits, revision-bound ring summaries and triangle pages, cancellation, retry identity and atomic publication. Ordinary omitted limits remain 100,000 operations / 30,000 ms. The maximum fixture explicitly requests 400,000 operations / 80,000 ms under an independently authorized host policy.

## Executed candidate validation

| Check | Measured result |
| --- | --- |
| Complete unit suite | 3,329 passed; zero failures, errors or skips; CPython 3.12.14 |
| Local driver | All 11 selected core/Agent steps passed; source and Git revision unchanged |
| New methods within that suite | 34 geometry, 26 Agent, 20 independent checker methods; 80 total |
| Separate Agent/0.5 cohort | 106 passed, zero skips; overlaps the complete unit inventory |
| Frozen source acceptance | 55 cases / 308 assertions: 17 valid, 34 invalid, four source-valid delivery refusals |
| Actual Agent workflow | 62 exchanges / 60 durable identities; all twelve operations; schemas checked |
| Independent destinations | 19 source-built GLBs; zero Khronos errors/warnings; geometry, PBR and identity checks passed |
| Recorded playback | 115 native and 55 browser pose observations; 14 actual capture reviews |
| Complete maximum request | 257,108 / 400,000 operations, about 2.78 seconds within its 80-second request |
| Repaired Agent export | 17,594 operations under unchanged ordinary defaults |

The [validation summary](validation-summary.json) binds the actual receipts. The full driver took 1,274.303 seconds, with 1,047.465 seconds in the complete unit suite. These are observed execution times on the identified host, not a cross-platform performance promise. Only one Python version ran. Sixteen external case attestations remain pending in the selected inherited reports; local execution does not supply those missing roles.

The source workflow discovers the interface, creates the pinned assembly, inspects source and bounded mesh pages, rejects a touching-hole edit, repairs one inner corner, verifies the accepted stored bytes, and preserves the sibling mesh and pinned library. It rejects stale cursors and changed-payload retries, evaluates motion, exports and retrieves exact chunks, then exercises reset, cancellation and lower current host authorization. Independent reconciliation reconstructed the same 44,836-byte GLB from all 44 chunks and the SQLite artifact BLOB. The repaired first plate has volume 6.25 m³; its unchanged sibling retains 6 m³. Generated parts retain three stable keys, different depths and coherent parent motion.

The independent supplied-byte geometry checker uses frozen authored boundaries and actual decoded vertices. It checks cap-domain coverage beyond centroids, overlapping triangle interiors, directed cap boundaries, closed edge incidence, outward inner walls, region ownership, area, volume, normals and materials. Hostile controls use hand-divided geometry without the product compiler or triangulator. Static and animated scale cannot escape the rigid destination comparisons. The [visual review](visual-review.json) binds every original front/oblique Chromium capture actually inspected by the coordinator.

## Independent review and evidence

[Source review](SOURCE-REVIEW.md) and the [coordinator's exact binding](coordinator-source-review.json) cover native geometry and supplied-position validation. Separate reviewers checked shared adapters and the acceptance/destination tools. Original findings remain preserved: the promised summary counts were added, a checker scale gap was closed, and library preservation now reads actual durable state. Their separate [adapter closure](shared-adapter-closure.md) and [acceptance review](acceptance-review-final.md) identify the repaired inputs. No remaining blocker was found in the finite reviewed scope.

The [independent evidence reconciliation](c076-evidence-review.md) and [compact record](evidence-review-summary.json) bind the complete source inventory, frozen receipts, actual protocol and store, artifact reconstruction, destination results, visual-attestation hashes and final driver receipts. Its 6,960 consistency checks are not product-test executions. Worker schema observations retain their worker source identity; all relevant runtime, contract, test and fixture bytes match the candidate.

The [raw archive descriptor](evidence-archive.json) identifies 1,512 immutable members, including original failed preparations and every corrected attempt. The complete audit JSON and executed audit script are retained there. Later evidence publication, main integration, final verification and portable-helper wrapper records have a separate publication boundary. A focused or integrity check does not imply another complete regression run. [Development reconciliation](DEVELOPMENT-RECONCILIATION.md) explains the preparation and review corrections without changing historical outcomes.

[Preservation](preservation.json) confirms all 3,990 baseline paths remain. All 975 protected old test/example/schema/workflow/language-design files and all 64 original C076 adoption/fixture paths retain their exact Git blobs and modes. Nineteen deliberate baseline changes are listed: shared runtime adapters and three navigation/goal files. Earlier behavior, defaults, acceptance limits and adoption records retain their meanings.

Coordinator `interactive-polygon-holes-20261030-c076-57d0170e` owns the bounded scope declared in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6530373184). Main integration requires a separately verified expected-head lease. Current [STATUS](../../../STATUS.md) and PR #74 identify the actual ownership/integration state; this evidence publication asserts no future merge.

## Remaining boundaries and continuation

Recorded Three.js/Chromium playback establishes no Unreal Engine import or live destination physics. Bevel offsets, Boolean operations and automatic physical properties remain outside the adopted scope. Original28 remains **24/28, failed**, with P11/P16/P23/L03 unresolved. Preserve M1 rejection, comparison accounting/passive authority, held C035 including adverse timing, C057, complete reach acceptance, missing compatibility/external roles, C059's unestablished storage cause, historical LFS migration and every broader GOAL domain. Higher-budget success cannot retroactively pass fixed-budget gates.

After actual integration, final verification, portable delivery and explicit scope closure, the [next selected task is C077: matched-topology polygon ring lofts](NEXT-TASK.md), beginning with an explicit surface/interpolation decision and frozen independent fixtures. Naming it adopts no syntax or limits and starts no worker or schedule.
