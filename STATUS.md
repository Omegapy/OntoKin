# OntoKin status

Checkpoint: **2026-10-19T00:36:00Z**. Native surface **M01–M12** and source impulse **I01–I12** are implemented, verified and integrated. All required resulting-main impulse checks passed. The complete [GOAL](GOAL.md) remains **in progress**. [AGENTS.md](AGENTS.md) governs development, integration and recovery.

## Integrated capabilities and evidence

Source `0.3` / `surface-0.1`, Agent/0.3 and GLB/0.3 supply actual parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`; [original surface evidence](docs/engineering/surface-release-validation/README.md) remains unchanged.

Source `0.4` / `impulse-0.1`, Agent/0.4 and GLB/0.4 add authored world impulses at target-self points on free homogeneous spheres, off-center angular response, ordered release/impulse semantics, whole-boundary rollback, bounded source-aware inspection, actual mass/radius source repair and conservative recorded animation. Frozen OK-LANG-004 expectations were adopted before implementation at `342788a2b5868189c72eae0541e86860a0de43ee` and remain unchanged.

[PR #11](https://github.com/Omegapy/OntoKin/pull/11) merged at 2026-10-18T23:50:00Z into **`d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`**, tree `01678d2686f801aa46d29b1434539c46c805bd4a`. Parents preserve observed main `9ab53fdc6ab56b4770132d53f59228f05f029926` and checked PR head `1b0510cccf2987d6d622e748b7ed2f26cdb46cb3`. All four exact-head PR jobs passed in [39177404131](https://github.com/Omegapy/OntoKin/actions/runs/39177404131). All four resulting-main jobs passed in [39178143664](https://github.com/Omegapy/OntoKin/actions/runs/39178143664), completed 2026-10-18T23:57:52Z: Python 3.11, 3.12, 3.13 and GLB/visual validation.

The [integration record](docs/engineering/impulse-release-validation/integration.json) preserves these observations, exact parent/merge identities, actual Git input comparisons and an additional independent archive audit. Original [release evidence](docs/engineering/impulse-release-validation/README.md), [summary](docs/engineering/impulse-release-validation/validation-summary.json), [complete gate](docs/engineering/impulse-release-validation/impulse-conformance.json) and [member manifest](docs/engineering/impulse-release-validation/evidence-manifest.json) remain unchanged at publication `83148880f0f08308c3b7e99bd4b0cdf858c146da`.

| Identified impulse evidence | Actual result |
| --- | --- |
| Implementation | `da0eb32c789a6f631a0d39eb219cbb3a912c9dfa`, tree `b4da2ea696f93287e198475ef26b3cfe348e75e4` |
| Runtime | `ontokin-reference` 0.4.0; SHA-256 `868b64f0f4644ae7e139f9cc5925e872953b71618172b52fab4a782dd532b784` |
| Full regressions | Both inventories: 588/588; 385.983845 s and 387.065488 s; stable inputs |
| Core / original Agent | 43 source cases / 694 assertions; A01–A10 passed |
| Inherited release gates | Current C01–C20 and M01–M12 passed; zero failed/pending |
| Impulse release | I01–I12 passed; 40 frozen source cases and 124 mapped methods |
| Destination | 22 surface GLBs / 308 poses; nine impulse GLBs / 192 fixed and 7,628 dense poses |
| Recorded visual review | 24 hash-identified native captures and fresh construction capture |
| Durable archive | 6,485,500 bytes; 2,188 regular files; SHA-256 `0b3d464854dfdee3b4565f2324446fe02d3cb731f7ffab272ba5bd1109dd6131` |
| Continuation audit | Every member hash/length verified; I01–I12 passed again, 124 mapped methods in 58.366934 s |
| Git input identity | All 200 surface and 292 impulse eligible paths/blobs match implementation, PR head, merge and status-only main `4c7b014` |

The 292-file inventory SHA-256 is `3c06c1dbb83489f5bea1f0f9907567fc4483cd679dca015f78af63e236b4f2bb`. Implementation CI [39169599694](https://github.com/Omegapy/OntoKin/actions/runs/39169599694) and publication run [39176062099](https://github.com/Omegapy/OntoKin/actions/runs/39176062099) retain separate identified executions. The continuation audit reads retained browser evidence; it does not claim new browser captures or visual observations.

Changes cover source construction/syntax04, evaluator/model, program service/protocol/store/catalog, both CLIs, scene/GLB delivery, actual source workflows, independent validators, conformance tests and additive CI. Recorded GLB playback is not live physics. Visual lofts add no physical matter or motion authority. Historical agent, construction, surface, adapter and preservation evidence remain unchanged. Temporary recovery workflows and installed dependencies are not integrated.

## Exact next development task

Complete and review the new finite center-of-mass force-interval contract and frozen source fixtures in [issue #12](https://github.com/Omegapy/OntoKin/issues/12), then publish explicit adoption before runtime implementation. Draft scope **`work/force01-contract-20261019-0020-astra`** starts at `4c7b014c4d4470c7605e71c0676295b80462252a` and owns only new OK-LANG-005 and `force-v0.1/` files. Force intervals remain **not adopted and not implemented** at this checkpoint. The earlier named draft is absent from the recovered source and current remote branch list; reconcile any prior work if it appears.

Freeze exact source keys, world-force intervals, rational endpoints, final active-set aggregation at atomic boundaries, numerical and temporal limits, unchanged acceleration/anchor behavior, valid short prefixes, failure and repair fixtures, bounded agent operations and recorded delivery requirements. Do not weaken earlier accepted profiles or replace source workflows with Python-prepared geometry.

Still unmet: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; finite forces, continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engine behavior, measured scale/performance and a documented direct-tool authoring comparison. Every full-product GOAL domain remains required. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

No main integration lease remains held after this record is published. The closing owner was `interactive-impulse-close-20261019-0029Z-astra`, acquired by expected-head nonforce update at `eca84ce004d5478c6903fd04c2a7924551750198`. The completion record must publish against that exact observed head. Read actual main, issue handoffs, branches and CI before a new integration lease or retry. PR #11 is already merged; do not merge it again.

[Issue #10](https://github.com/Omegapy/OntoKin/issues/10) retains impulse defects, fixes and recovery. [Earlier detailed STATUS](https://github.com/Omegapy/OntoKin/blob/4c7b014c4d4470c7605e71c0676295b80462252a/STATUS.md) preserves prior measurements and checkpoint history. Source restoration used an isolated read-only Git bundle workflow on `work/source-recovery-20261019-0016-astra`; it must not be merged.

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue interactively toward GOAL; unrelated attachment/stream errors do not change repository state.
