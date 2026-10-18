# OntoKin status

Checkpoint: **2026-10-18T23:56:40Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12 and source impulse I01–I12 are implemented and verified. The impulse release is now **merged through PR #11**; resulting-main CI and the final integration record are being completed. [AGENTS.md](AGENTS.md) governs coordination and recovery.

## Integrated finite releases

Native source `0.3` / `surface-0.1`, Agent/0.3 and GLB/0.3 provide parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic scoped edits. [PR #9](https://github.com/Omegapy/OntoKin/pull/9) merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`. The original [native evidence](docs/engineering/surface-release-validation/README.md), [summary](docs/engineering/surface-release-validation/validation-summary.json) and [integration record](docs/engineering/surface-release-validation/integration.json) remain unchanged, together with all earlier agent, construction, adapter and document-preservation evidence.

Source `0.4` / `impulse-0.1`, Agent/0.4 and GLB/0.4 now add authored world impulses at target-self points on free homogeneous spheres, off-center angular response, ordered release/impulse semantics, whole-boundary rollback, bounded source-aware inspection, actual mass/radius source repair and conservatively sampled recorded animation. Frozen OK-LANG-004 expectations were adopted before implementation at `342788a2b5868189c72eae0541e86860a0de43ee` and remain unchanged.

[PR #11](https://github.com/Omegapy/OntoKin/pull/11) was confirmed merged at **2026-10-18T23:50:00Z** into actual main **`d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`**, tree `01678d2686f801aa46d29b1434539c46c805bd4a`. Its parents are observed main `9ab53fdc6ab56b4770132d53f59228f05f029926` and checked PR head `1b0510cccf2987d6d622e748b7ed2f26cdb46cb3`. All four exact-head PR jobs passed in [39177404131](https://github.com/Omegapy/OntoKin/actions/runs/39177404131). The resulting-main [run 39178143664](https://github.com/Omegapy/OntoKin/actions/runs/39178143664) is in progress; do not substitute its configured jobs for observed passing results.

## Complete durable impulse acceptance evidence

[The release evidence](docs/engineering/impulse-release-validation/README.md), [summary](docs/engineering/impulse-release-validation/validation-summary.json), [full gate result](docs/engineering/impulse-release-validation/impulse-conformance.json) and [per-file manifest](docs/engineering/impulse-release-validation/evidence-manifest.json) were published at `83148880f0f08308c3b7e99bd4b0cdf858c146da`. The 6,485,500-byte archive contains **2,188 regular files**, SHA-256 `0b3d464854dfdee3b4565f2324446fe02d3cb731f7ffab272ba5bd1109dd6131`. Every member hash/length and all five Git blob identities were verified after download. The temporary recovery workflow and installed dependency directories were not integrated.

Tested implementation is **`da0eb32c789a6f631a0d39eb219cbb3a912c9dfa`**, tree `b4da2ea696f93287e198475ef26b3cfe348e75e4`. Runtime is `ontokin-reference` 0.4.0, SHA-256 `868b64f0f4644ae7e139f9cc5925e872953b71618172b52fab4a782dd532b784`. Both the 200-file surface inventory and the complete 292-file impulse inventory were independently compared to the actual resulting-main Git objects; all eligible bytes match the tested implementation. The impulse inventory SHA-256 is `3c06c1dbb83489f5bea1f0f9907567fc4483cd679dca015f78af63e236b4f2bb`.

| Published evidence on `da0eb32` | Actual result |
| --- | --- |
| Full regression, surface inventory | 588/588 passed, 385.983845 s, stable inputs |
| Full regression, impulse inventory | 588/588 passed, 387.065488 s, stable inputs |
| Core and original Agent | 43 source cases / 694 assertions; A01–A10 passed |
| Current inherited gates | C01–C20 and M01–M12 passed; zero failed/pending |
| Impulse gate | I01–I12 passed; 40 frozen source cases, 124 mapped methods; `full_gate_complete: true` |
| Independent destination checks | 22 surface GLBs / 308 poses; nine impulse GLBs / 192 fixed and 7,628 dense poses passed |
| Actual visual review | 24 hash-identified native captures plus the newly generated construction capture |
| Implementation CI | [39169599694](https://github.com/Omegapy/OntoKin/actions/runs/39169599694): Python 3.11, 3.12, 3.13 and GLB/visual jobs passed |
| Independent downloaded-archive audit | I01–I12 passed again in 43.907899 s |

[Publication run 39176062099](https://github.com/Omegapy/OntoKin/actions/runs/39176062099) re-executed the complete gates on an exact implementation checkout before publishing the archive. Separate earlier local full-suite runs passed in 195.795694 s and 192.285004 s; their 2,204-file preparatory archive is not the published archive above. Recovery regenerated omitted construction browser inputs in [39174507443](https://github.com/Omegapy/OntoKin/actions/runs/39174507443), rather than weakening readers or inventing missing provenance.

Changes span typed source construction and syntax04; evaluator/model; program service/protocol/store/catalog; both CLIs; native scene/GLB delivery; actual source workflows; independent validators; conformance mappings/tests; and additive CI. Original source, profile meanings, frozen acceptance and historical evidence remain preserved. Recorded GLB playback is not live physics; visual lofts add no physical matter or pose authority.

## Exact next task and remaining goal

Observe all required resulting-main checks at `d25ab70`, preserve the actual merge/run/job and input-identity proof, update the completed impulse gate in GOAL and release this integration lease. [Issue #10](https://github.com/Omegapy/OntoKin/issues/10) retains defects, fixes, scopes and recovery actions. [The earlier detailed STATUS](https://github.com/Omegapy/OntoKin/blob/b59c074505292bb579b31dfa4caaf4fe19f4e76d/STATUS.md) preserves all previous identities and results.

Then review and adopt the finite center-of-mass force-interval contract tracked in [issue #12](https://github.com/Omegapy/OntoKin/issues/12). It is not adopted or implemented. The earlier named draft branch is absent from the current remote list; preserve and reconcile any prior work if it appears. Freeze exact source syntax, force identities, activation/completion semantics, additive forces, numerical/temporal limits, failure/repair fixtures and recorded delivery requirements before runtime implementation.

Still unmet: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; finite forces, continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engine behavior, measured scale/performance and a documented direct-tool authoring comparison. Every full-product GOAL domain remains required. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-impulse04-final-20261018-2328Z-astra` |
| Task | Finish resulting-main verification and publish the impulse integration record. |
| Acquired UTC | 2026-10-18T23:28:32Z |
| Renewed UTC | 2026-10-18T23:56:40Z after confirmed PR merge, passing exact-head PR CI and matching resulting-main verification inventories. |
| Expires UTC | 2026-10-19T00:26:40Z |
| Observed main for renewal | `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e` |
| Reserved scope | Main integration, STATUS/GOAL impulse completion records and new integration evidence. No force runtime work is authorized by this lease. |
| Recovery | Read actual main/PR refs, issue #10 and CI before retrying writes. Source acceptance evidence is durable in the repository; publication run 39176062099 retains the separate publishing outcome. |

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue interactively toward GOAL. Unrelated chat attachment/stream errors do not change the repository or justify replaying completed writes.
