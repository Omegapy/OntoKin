# OntoKin status

Checkpoint: **2026-10-19T05:05:00Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12 and source impulse I01–I12 remain integrated and verified. The source `0.5` / `force-0.1` kernel is now **merged through PR #13 and verified on resulting main**. Actual Agent/0.5 implementation is published in [draft PR #14](https://github.com/Omegapy/OntoKin/pull/14); its schemas and complete checkpoint acceptance are being finished. **GLB/0.5 and F01–F12 are not complete.**

## Integrated releases

Native source 0.3, Agent/0.3 and GLB/0.3 provide parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`; original [surface evidence](docs/engineering/surface-release-validation/README.md) is unchanged.

Source 0.4, Agent/0.4 and GLB/0.4 provide off-center source impulses on free homogeneous spheres, ordered release/impulse boundaries, rollback, bounded source-aware inspection, physical-parameter repair and conservative recorded animation. PR #11 merged at `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`. Original [impulse evidence](docs/engineering/impulse-release-validation/README.md) and [integration record](docs/engineering/impulse-release-validation/integration.json) retain their exact 40 cases, 124 mapped methods, both 588-test inventories, independent destination/browser results and historical implementation identity. These records do not certify later changed runtime bytes.

The force source parser/compiler/evaluator was adopted before implementation at `676e5542c09b8af1cbc9e5f0b5bbb42a898b1e34` and implemented at **`cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1`**, tree `a92aac948bbb6e80e7adaa136d8a6098f0f17563`. Its constant world COM-force intervals have exact completion clocks, additive final active sets, unchanged anchors when acceleration is unchanged, inherited release/impulse order, whole-boundary rollback, bounded histories and valid short prefixes. The original 44 fixtures remain unchanged; twelve supplements and explicit additive errata supply 56 effective source cases without widened tolerances.

[PR #13](https://github.com/Omegapy/OntoKin/pull/13) **merged at 2026-10-19T04:10:09Z** into **`74089239eb81b3c5a335b63145b3444eccfab148`**, tree `204ec69db6261e1a89f08327df0ee21f300f3072`. Checked PR head was `8bd62b0685c4c7b42c57ac84332d5d793b0fa3ae`; its four jobs passed in [39195106229](https://github.com/Omegapy/OntoKin/actions/runs/39195106229). All four actual resulting-main jobs passed in [39198117569](https://github.com/Omegapy/OntoKin/actions/runs/39198117569), completed 04:18:01Z. The preceding pre-merge STATUS was stale; do not merge PR #13 again.

[The kernel checkpoint](docs/language-design/force-v0.1/KERNEL-CHECKPOINT.md) preserves the full source/test record: 677/677 locally and again in exact-tree publication [39194062765](https://github.com/Omegapy/OntoKin/actions/runs/39194062765), focused 89/89, original 43 source cases / 694 assertions, and preservation checks. A fresh Git comparison confirms the merge differs from the tested kernel only in STATUS and the additive KERNEL-CHECKPOINT record; all other 593 tracked paths and blobs are identical. The final normalized integration record is being added under the lease below.

## Published Agent/0.5 checkpoint and exact next task

**`f2785fff2c6655af88f596233400bf9182d3d269`**, tree **`812e5a871fc31e5448deb1dc3be1e59c56b9f49f`**, is published in PR #14 on `work/force01-agent05-20261019-0435-astra`, parent actual main `7408923`. It reuses the exact adopted [OK-AGENT-005](https://github.com/Omegapy/OntoKin/blob/d8c2f61403d2ffec0ca6f5c762c3c2d1ca08834a/docs/engineering/OK-AGENT-005-finite-force-program-workflows.md), not the unavailable earlier local implementation.

The binding implements explicit force source discovery, separate store/schema and cursor context, complete revision-bound force state, atomic source-authorized mass/force/duration repair, cancellation and final-envelope budget handling. Earlier protocol defaults, catalogs and stores remain unchanged. Requests for the unavailable GLB/0.5 adapter explicitly fail without an artifact. Both inherited unknown-version test identities are retained; only their newly supported 0.5 sentinel moves to unsupported 0.6.

[Publication run 39201671020](https://github.com/Omegapy/OntoKin/actions/runs/39201671020) checked every reviewed after-file hash and passed **695/695 tests in 161.273 s**, focused tests, original source conformance and documentation preservation (29 historical sources, 666 local links). Artifact `12163493891` contains exact source.bundle and logs; ZIP SHA-256 `ea89395fb211dc162fdcbee992e0c25830732d2118030b773410c1b4fe2b4627` and all member hashes were independently verified after retrieval. Publication helpers are excluded from the PR.

Finish the Agent/0.5 schemas, actual retained source-workflow recorder, independent message/source-provenance and mutation checks, remaining cancellation/CLI coverage, complete current regression and exact-head CI. Publish tested work, safely integrate the completed agent checkpoint, then implement the separately specified acceleration-aware GLB/0.5 adapter and independent geometry/PBR/intermediate-motion/browser checks. The complete retained F01–F12 gate must pass before declaring the finite force release complete.

Earlier agent branches `work/force01-agent05-20261019-0334-astra` and `work/force01-agent05-20261019-0350-astra` are preserved. Their unpublished local-tree handoff is not claimed as recovered or executed. [Issue #12](https://github.com/Omegapy/OntoKin/issues/12) records scopes, actual defects, corrections and recovery. No other agent is claimed active.

## Remaining full-product scope

Still required: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful movement; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Every GOAL domain remains required. Blender delivery and a generic delivered-level check are not established. Recorded GLB playback is not live physics, and visual lofts add no matter or motion authority.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-force-agent05-20261019-0505Z-astra` |
| Task | Reconcile the completed kernel integration record, then integrate PR #14 only after its remaining agent checks pass. |
| Acquired UTC | 2026-10-19T05:05:00Z, after prior expiry and remote merge/ref/CI reconciliation. |
| Expires UTC | 2026-10-19T05:35:00Z |
| Observed main before acquisition | `74089239eb81b3c5a335b63145b3444eccfab148` |
| Reserved scope | Main integration, STATUS and new kernel/agent checkpoint evidence. |
| Recovery | Read actual main, PR #14, issue #12 and CI before retrying. Preserve completed writes. PR #13 is already merged. Agent code is recoverable from f2785fff and its identified bundle; do not replay old helper workflows. |

[Previous checkpoint](https://github.com/Omegapy/OntoKin/blob/74089239eb81b3c5a335b63145b3444eccfab148/STATUS.md) and all historical source/acceptance/evidence records remain intact. The owner intentionally disabled **Advance OntoKin**; no automation was changed or reactivated. Continue interactively toward GOAL. Attachment or stream errors do not change repository state.
