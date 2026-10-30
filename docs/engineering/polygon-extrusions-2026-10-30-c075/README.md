# C075: source-authored polygon extrusions

C075 implements editable polygon extrusions through explicit source **0.8 / polygon-extrusion-0.1**, **Agent/0.8** and recorded **GLB/0.8**. Plates, concave brackets and reusable housing exteriors now come from typed `.ok` outlines, including stable vertex keys, separate geometric order, regional materials and rigid visual placement. This is an experimental development increment under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md). It does not complete a feature release, reach acceptance or the full [GOAL](../../../GOAL.md).

## Decision, implementation and source identity

The [versioned contract](../../language-design/polygon-extrusion-v0.1/ADOPTION.md) and [frozen cases](../../../examples/polygon-extrusions/acceptance-freeze.json) preceded implementation at actual commit `efeda179218a6231e4ffd5042210d4d237663184`. Starting main was `9b9b0c242d8ee02ea7d75ac1805341c1d30d3223`, tree `ae0861e94c0e0c1baea3ea938532791f9b9134ca`. The full measured runtime candidate is **`d3f0d69b953550b60b5eb0a0b41bc390ba934985`**, tree **`ea880242abd9e323c1d80a46c2b01bdbd35a2aa8`**. [PR #73](https://github.com/Omegapy/OntoKin/pull/73) records publication and actual integration separately.

The finite geometry contract admits simple counterclockwise outlines of 3–64 vertices, unique explicit integer orders, coordinates within ±100 meters and positive depths from 0.001 through 100 meters. Exact rational predicates over canonical binary64 coordinates reject crossings, touching, duplicate points, adjacent collinearity and reversed winding. Deterministic ear clipping produces closed caps and outward side walls, with flat normals and named PBR regions. Binary32 collapse or unacceptable destination error is a delivery failure. No geometry repair, automatic mass/inertia, collision shape, holes or bevels are inferred.

`ExtrusionAgentService` uses a separate durable store and all twelve documented operations. It retains the inherited source-authoritative execution ledger, current trusted host authorization, exact UTF-8 file patches, revision-bound inspection pages, accepted-state rollback, cancellation identity, durable retries and atomic artifact publication. Defaults remain 100,000 operations / 30,000 ms; modeled animation time remains separate. Older source, Agent, export and CLI/Python defaults retain their meanings.

## Actual candidate verification

| Executed role | Result on the identified candidate |
| --- | --- |
| Complete inherited and new unit cohort | **3249 tests**, zero failures, errors or skips; CPython 3.12.14; 1058.193 seconds. The 62 new methods are included in this total. |
| Local driver, core plus force-agent | **11 selected steps passed**, including original source/Agent, construction, surface, impulse, documentation, fresh Agent/0.5 workflow and its independent audit. The 106-test force-agent cohort overlaps the full suite. |
| Frozen polygon/source and actual Agent workflow | **28 source cases, 212 assertions, 57 exchanges and 55 durable request identities** passed. All 57 exchanges passed schema checks. |
| Separate lifecycle schema capture | **23 tests**, 306 intermediate/repeated observations and 310 response envelopes across all twelve operations; 22 services, 150 distinct service/project/request identities, 151 payloads and zero schema errors. Ten schema-invalid hostile observations were rejected. These observations are not 306 independent requests. |
| Independent supplied-byte geometry and destination checks | **12 GLBs**, zero Khronos errors/warnings, **80 native poses and 40 browser poses** passed. Node 22.16.0, Three.js 0.180.0, Validator 2.0.0-dev.3.10, Playwright 1.56.1 and Chromium 141.0.7390.37. |
| Actual visual inspection | **Eight fresh captures** opened and reviewed: front/oblique views of the concave bracket, rigidly placed bracket, generated parts and repaired assembly. |

The frozen rectangle has area 2 m², volume 1 m³ and 12 triangles. The concave bracket has area 5 m², volume 1.25 m³ and 20 triangles. Independent checks decode actual positions, normals, material assignments, cap direction, authored side edges, opposite edge pairing, surface area, volume and recorded carrier poses. Six checker tests reject tampered geometry, normals, winding, colors and missing triangles.

The Agent workflow rejects an invalid candidate, repairs one occurrence by changing its inner corner, preserves sibling geometry and exact pinned-library bytes, rejects stale inspection cursors, evaluates motion, exports, retrieves exact chunks and checks identical/changed-payload retries. The repaired outline has area 5.5 m² and volume 1.375 m³. Its export uses **8,915 operations** under unchanged defaults. Generated parts retain three independently keyed occurrences with different depths and coherent parent motion. Saved artifacts reject insufficient current host authorization; cancellation and reset are exercised.

All 34 originally frozen files remain unchanged. Initial fixture preparation mistakes—reserved alias `parts` and an incorrect expected wrong-unit diagnostic—have a separate [correction record](../../language-design/polygon-extrusion-v0.1/FIXTURE-CORRECTION-001.md). The [development reconciliation](DEVELOPMENT-RECONCILIATION.md) preserves the new-test expectation failure and each unsuccessful checker attempt. Their later correction does not relabel those failed executions as passes.

## Independent review and evidence

[Source review](SOURCE-REVIEW.md) and its [exact binding](source-review-binding.json) found no substantive blocker. Reviewer probes checked the frozen analytic expectations, additional concave outlines, material ownership, finite allocation and cooperative exception identity. The original baseline tests, examples, workflows, .7 schemas, adoption records, legacy binding registry and original surface kernel are unchanged; no baseline file was removed. A separately reviewed navigation-only newline correction joins row 24 to its specification table.

[The compact validation summary](validation-summary.json), [actual visual review](visual-review.json) and [raw evidence descriptor](evidence-archive.json) identify the measured results and immutable archive. The separate [evidence reconciliation](c075-evidence-review.md) rehashed all candidate source files, checked the exact durable requests and receipts, reconstructed the retrieved artifact from 39 chunks and independently validated the captured response envelopes. Its 1,144 consistency checks are not added to product test totals. Later evidence-publication, merge and final-main checks must identify their actual source roles and prove complete eligible-input equality before reusing the candidate cohort. A focused check is not another full-suite execution. The packet verifier checks recorded bytes and identities; it does not execute product or browser tests.

Coordinator `interactive-polygon-extrusions-20261030-c075-22a257e3` owns the bounded scope declared in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6528011677). Main integration uses a separately acquired expected-head lease. Current [STATUS](../../../STATUS.md) and the PR provide its actual integration/ownership state; this candidate record does not assert a future merge.

## Remaining boundaries and continuation

This run covers one Python interpreter. The selected inherited reports retain **16 external cases pending**; the broader compatibility matrix and complete release roles are not established. Actual Three.js/Chromium recorded playback establishes no Unreal Engine import or live destination physics.

Original28 remains **24/28, failed**, with **P11/P16/P23/L03 unresolved**. Preserve M1 rejection, comparison accounting/passive authority, C035 including adverse timing, C057, complete reach acceptance, C059's unestablished storage cause, historical LFS migration and all other GOAL domains. The earlier held/unselected optimization dispositions remain intact. A higher-budget success cannot retroactively pass a fixed-budget gate.

The next selected task is [C076: source-authored holes in polygon extrusions](NEXT-TASK.md), beginning with a separate versioned decision and frozen independent fixtures. Naming it starts no worker or continuation schedule. C075 integration, final verification, portable delivery and explicit scope closure precede continuation.
