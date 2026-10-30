# C076: source-authored holes in polygon extrusions

This bounded development increment implements the [C075 continuation](../polygon-extrusions-2026-10-30-c075/NEXT-TASK.md) under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md). It adds editable through-holes for plates, brackets and hollow cross-sections. It does not complete a feature release or the full [GOAL](../../../GOAL.md).

The [versioned decision](../../language-design/polygon-holes-v0.1/ADOPTION.md) and [independent fixtures](../../../examples/polygon-holes/README.md) were published before runtime implementation in commit `2c0fe255281a9e3dde482a5845f2587728106e30`, tree `14b2fa7bc2e90d45d5364cc299f2828b0e3ec6a0`. The baseline is actual C075 main `84a523fb5d359f0e3f0a5104ac0856dbf5eff3a0`, tree `93fb9a943d1dbf424223199597f64674d6467f90`. [PR #74](https://github.com/Omegapy/OntoKin/pull/74) identifies the active branch and its current publication.

## Selected capability

Explicit source `0.9` / `polygon-holes-0.1`, Agent/0.9 and recorded GLB/0.9 support one counterclockwise outer ring and zero through eight clockwise holes, with at most 64 vertices in total. Ring and vertex orders are explicit and independent from declaration order. Keys are stable; vertex keys are local to their ring. Holes must lie strictly inside the outer ring and remain mutually exterior. Touching, crossing, overlapping, nested or self-intersecting boundaries are rejected.

Exact predicates over canonical binary64 coordinates select a deterministic planar graph and verify complete cap coverage. Closed triangulation supplies outward flat normals, separate cap and outgoing-edge wall materials, rigid local placement and reusable/generated occurrences. A separate check operates on actual placed binary32 positions, rejecting collapsed identities, degenerate faces and intersections beyond source-shared vertices or edges. Source geometry supplies no implicit mass, collision shape or new motion authority.

`HolesAgentService` provides all twelve versioned operations in its separate durable store. It inherits current host authorization, source-requested limits, the original request counter/deadline, revision checks, exact edits, bounded mesh pages, cancellation, retry identity and atomic publication. Omitted budgets retain 100,000 operations / 30,000 ms. The maximum fixture explicitly requests 400,000 operations / 80,000 ms within an independently authorized host policy.

## Acceptance and evidence roles

The frozen standalone corpus has 17 valid cases, 34 invalid cases and four source-valid delivery refusals. Additional pinned-module, generated-part and one-instance repair cases exercise composition and unchanged siblings. Expected volume, area, boundary incidence, coverage, materials and motion precede implementation. The independent decoded oracle uses actual delivered vertices and faces; hostile controls use hand-divided geometry rather than the product triangulator.

`tools/run_holes_acceptance.py` executes the frozen source cases and an actual discovery → create → inspect → reject edit → repair → evaluate → export → retrieve workflow, with retries, reset, cancellation and current-policy failure. `tools/verify_holes_glb.mjs` checks the resulting files with pinned Khronos and Three.js tools and captures actual Chromium playback. Visual review must inspect the captured images. The inherited full regression and local driver remain separate required gates.

This initial implementation record claims no completed candidate cohort, destination validation, integration or full-suite execution. Later measured summaries and exact source bindings record those outcomes separately. Every failed preparation or execution remains preserved; a corrected attempt does not relabel a prior failure.

## Coordination and remaining boundaries

Coordinator `interactive-polygon-holes-20261030-c076-57d0170e` owns this scope on `work/polygon-holes-20261030-c076`, declared in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6530373184). Geometry, Agent binding and independent oracle work have separately identified local branches and file ownership. The temporary fourth branch is justified by independent oracle development in the issue. Main integration requires its own verified expected-head lease; this record asserts no active main lease or future merge.

Earlier source, Agent and destination profiles, defaults, fixtures and adoption records retain their meanings. Original28 remains **24/28, failed**, with P11/P16/P23/L03 unresolved. Preserve M1 rejection, comparison accounting/passive authority, held C035 including adverse timing, C057, complete reach acceptance, compatibility and external roles, C059's unestablished storage cause, historical LFS migration and every broader GOAL domain. Recorded Three.js playback establishes neither Unreal Engine import nor live destination physics.
