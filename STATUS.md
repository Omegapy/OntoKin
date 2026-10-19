# OntoKin status

Checkpoint: **2026-10-19T00:29:00Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12 and source impulse I01–I12 are implemented, verified and integrated. All four checks on the actual impulse merge into main have now passed. The final integration record and GOAL milestone update are being published. [AGENTS.md](AGENTS.md) governs coordination and recovery.

## Integrated finite releases

Native source `0.3` / `surface-0.1`, Agent/0.3 and GLB/0.3 supply parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic scoped edits. [PR #9](https://github.com/Omegapy/OntoKin/pull/9) merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`. Original [surface evidence](docs/engineering/surface-release-validation/README.md) and all earlier agent, construction, adapter and document-preservation records remain unchanged.

Source `0.4` / `impulse-0.1`, Agent/0.4 and GLB/0.4 add authored world impulses at target-self points on free homogeneous spheres, off-center angular response, ordered release/impulse semantics, whole-boundary rollback, bounded source-aware inspection, actual mass/radius source repair and conservatively sampled recorded animation. The frozen OK-LANG-004 corpus was adopted before implementation at `342788a2b5868189c72eae0541e86860a0de43ee` and remains unchanged.

[PR #11](https://github.com/Omegapy/OntoKin/pull/11) merged at 2026-10-18T23:50:00Z into **`d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`**, tree `01678d2686f801aa46d29b1434539c46c805bd4a`. Its parents preserve observed main `9ab53fdc6ab56b4770132d53f59228f05f029926` and checked PR head `1b0510cccf2987d6d622e748b7ed2f26cdb46cb3`. All four exact-head PR jobs passed in [39177404131](https://github.com/Omegapy/OntoKin/actions/runs/39177404131). All four resulting-main jobs passed in [39178143664](https://github.com/Omegapy/OntoKin/actions/runs/39178143664), completed 2026-10-18T23:57:52Z: Python 3.11, 3.12, 3.13 and GLB format/visual validation.

## Durable impulse evidence

[Release guide](docs/engineering/impulse-release-validation/README.md), [summary](docs/engineering/impulse-release-validation/validation-summary.json), [complete gate](docs/engineering/impulse-release-validation/impulse-conformance.json) and [member manifest](docs/engineering/impulse-release-validation/evidence-manifest.json) were published at `83148880f0f08308c3b7e99bd4b0cdf858c146da`. The 6,485,500-byte archive contains 2,188 regular files, SHA-256 `0b3d464854dfdee3b4565f2324446fe02d3cb731f7ffab272ba5bd1109dd6131`.

Tested implementation: **`da0eb32c789a6f631a0d39eb219cbb3a912c9dfa`**, tree `b4da2ea696f93287e198475ef26b3cfe348e75e4`. Runtime remains `ontokin-reference` 0.4.0, SHA-256 `868b64f0f4644ae7e139f9cc5925e872953b71618172b52fab4a782dd532b784`.

| Published evidence | Actual result |
| --- | --- |
| Both full regression inventories | 588/588 each; 385.983845 s and 387.065488 s; stable inputs |
| Core and original Agent | 43 source cases / 694 assertions; A01–A10 passed |
| Current inherited gates | C01–C20 and M01–M12 passed, zero failed/pending |
| Impulse gate | I01–I12 passed; 40 frozen source cases and 124 mapped methods |
| Native destination | 22 surface GLBs / 308 poses; nine impulse GLBs / 192 fixed and 7,628 dense poses passed |
| Actual visual review | 24 hash-identified native captures and a fresh construction capture |
| Implementation CI | [39169599694](https://github.com/Omegapy/OntoKin/actions/runs/39169599694): all four required jobs passed |
| Continuation archive audit | Every member hash/length verified; I01–I12 passed again, 124 mapped methods in 58.366934 s |
| Continuation Git identity proof | All 200 surface and 292 impulse eligible paths/blobs match implementation, PR head, merge and status-only main `4c7b014` |

The complete 292-file inventory SHA-256 is `3c06c1dbb83489f5bea1f0f9907567fc4483cd679dca015f78af63e236b4f2bb`. [Publication run 39176062099](https://github.com/Omegapy/OntoKin/actions/runs/39176062099) re-executed the complete gates on an exact implementation checkout. The temporary recovery workflows and installed dependencies are not integrated. [The preceding detailed STATUS](https://github.com/Omegapy/OntoKin/blob/4c7b014c4d4470c7605e71c0676295b80462252a/STATUS.md) preserves earlier recovery and audit results.

Changes cover typed construction/syntax04, evaluator/model, program service/protocol/store/catalog, both CLIs, scene/GLB delivery, real source workflows, independent validators, conformance tests and additive CI. Recorded GLB playback is not live physics. Visual lofts add no matter or motion authority.

## Exact next task

Publish the final impulse integration record, update its completed gate in GOAL and release this lease. [Issue #10](https://github.com/Omegapy/OntoKin/issues/10) retains scopes, defects, fixes and recovery actions. No implementation or acceptance bytes need changing for this record.

Then review, freeze and adopt the finite center-of-mass force-interval contract in [issue #12](https://github.com/Omegapy/OntoKin/issues/12). Independent draft scope `work/force01-contract-20261019-0020-astra` starts from `4c7b014`; no earlier force draft exists in the recovered source or current remote branch list. It remains **not adopted and not implemented**. Define exact source keys, world-force intervals, rational endpoints, final active-set aggregation, numeric/temporal limits, prefix validity, source repair and recorded delivery before implementation. Reconcile earlier work if it appears.

Still unmet: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; finite forces, continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engine behavior, measured scale/performance and a documented direct-tool authoring comparison. Every full-product GOAL domain remains required. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-impulse-close-20261019-0029Z-astra` |
| Task | Publish the verified impulse integration record and GOAL update. |
| Acquired UTC | 2026-10-19T00:29:00Z, after prior expiry and reconciliation of completed writes/CI. |
| Expires UTC | 2026-10-19T00:59:00Z |
| Observed main before acquisition | `4c7b014c4d4470c7605e71c0676295b80462252a` |
| Reserved scope | Main integration, STATUS/GOAL impulse completion and new integration evidence. |
| Recovery | Read actual refs, issue #10 and CI before retrying writes. The impulse release itself is already merged; do not merge it again. |

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue interactively toward GOAL; unrelated attachment/stream errors do not change repository state.
