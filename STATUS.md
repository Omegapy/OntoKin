# OntoKin status

Checkpoint: **2026-10-19T04:08:00Z**. Native surface **M01–M12** and source impulse **I01–I12** remain integrated and verified. The source `0.5` / `force-0.1` parser, compiler and analytical evaluator are published and all four normal checks on the current [PR #13](https://github.com/Omegapy/OntoKin/pull/13) head have passed. Its bounded checkpoint integration is being completed. The complete force release **F01–F12**, GLB/0.5 and the full [GOAL](GOAL.md) remain **unfinished**. Agent/0.5 implementation is being tested separately.

## Integrated releases and preserved evidence

Source `0.3` / `surface-0.1`, Agent/0.3 and GLB/0.3 provide native parameterized lofts, regional PBR materials, rigid placement, source-driven motion, triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`; [surface evidence](docs/engineering/surface-release-validation/README.md) is unchanged.

Source `0.4` / `impulse-0.1`, Agent/0.4 and GLB/0.4 provide off-center source impulses on free homogeneous spheres, ordered release/impulse boundaries, atomic rollback, bounded source-aware inspection, physical-parameter repair and conservative recorded animation. PR #11 merged at `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`; all four resulting-main checks passed in [39178143664](https://github.com/Omegapy/OntoKin/actions/runs/39178143664). [Impulse evidence](docs/engineering/impulse-release-validation/README.md) and [integration identities](docs/engineering/impulse-release-validation/integration.json) retain 40 fixed source cases, 124 mapped methods, both 588-test inventories, inherited gates, nine source-built GLBs, 192 fixed plus 7,628 dense destination poses and reviewed captures. These historical results certify their identified implementation, not later changed bytes.

[The preceding STATUS](https://github.com/Omegapy/OntoKin/blob/c5c40144f46172a7980fb45c8b5ae3a4b78a1299/STATUS.md) preserves the complete source-kernel publication record. No original evidence, accepted older-profile fixture or archived preservation hash has changed. Recorded GLB playback is not live physics; visual lofts add no matter or motion authority.

## Published force source-evaluator checkpoint

Implementation **`cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1`**, tree **`a92aac948bbb6e80e7adaa136d8a6098f0f17563`**, was published before this integration. PR #13 now points to **`8bd62b0685c4c7b42c57ac84332d5d793b0fa3ae`**, tree **`c2f0fe7cbecf565902096a019a34054b772a9b52`**. Its only changes after the tested kernel are STATUS and the additive KERNEL-CHECKPOINT record. Main integration is still pending at this exact checkpoint.

The contract was adopted at `676e5542c09b8af1cbc9e5f0b5bbb42a898b1e34` before runtime work. Constant world COM-force intervals have exact completion clocks, additive final active sets, unchanged anchors for unchanged canonical acceleration, inherited release/impulse ordering, whole-boundary rollback, bounded provenance and valid requested prefixes. The original 44-case corpus is unchanged. Twelve supplements and additive errata at `26307378dd99b298bfa230bd13660dbe36eb1c1f` preserve original sources while correcting S10/S11 initializer braces and P09 before-zero inherited derivatives; no tolerance was widened.

| Executed check | Actual result |
| --- | --- |
| Kernel local complete regression | 677/677 passed, 193.790 s |
| Kernel local force/review cohort | 89/89 passed, 2.124 s; 56 effective source cases |
| Original source conformance | 43 cases / 694 assertions passed |
| Documentation preservation | 29 historical sources / 233 sections / 663 links passed |
| Exact-tree publication | [39194062765](https://github.com/Omegapy/OntoKin/actions/runs/39194062765): 677/677 in 160.218 s; 89/89 in 1.716 s; source and preservation checks passed |
| Normal exact PR-head CI | [39195106229](https://github.com/Omegapy/OntoKin/actions/runs/39195106229): Python 3.11, 3.12, 3.13 and inherited GLB/browser validation all passed for `8bd62b0` |
| Recovered publication bytes | Artifact `12161410669`; ZIP SHA-256 `e2e374d6d1e84497b27618a85335b00b80ecd63070c21664a44f85dbd81c8fb5`; bundle and exact kernel tree independently checked again |

Kernel changes: `syntax05.py`, `force_source.py`, `force_runtime.py`, narrow dispatch/linker/construction/model/evaluator hooks and corresponding source/transaction/budget/cancellation tests. Publication helper workflows and staging payloads are not part of PR #13.

## Exact next task and independent Agent/0.5 work

Merge the checked source-evaluator checkpoint through PR #13 under this lease, verify the actual merge and resulting-main checks, and publish its integration record. Do not declare F01–F12 complete.

Agent continuation branch `work/force01-agent05-20261019-0350-astra` starts from the published kernel and has adopted [OK-AGENT-005 at `d8c2f61`](https://github.com/Omegapy/OntoKin/blob/d8c2f61403d2ffec0ca6f5c762c3c2d1ca08834a/docs/engineering/OK-AGENT-005-finite-force-program-workflows.md). Its implementation remains local and unaccepted at this STATUS checkpoint. Actual focused runs passed 15 agent workflow tests, 12 protocol/CLI tests and seven catalog/schema-shape tests. The initial two new-test field-path errors were corrected without changing production envelopes. Full regression and independent message-schema checks remain in progress. Publish actual tested code and evidence before treating this work as a recoverable implementation. Preserve the earlier Agent branch, which still points to the kernel.

The new interface must preserve all earlier defaults/protocols/stores and perform actual source-authorized mass/force/duration repair, exact world-force inspection, signed cursor isolation, retries, cancellation and final-response budget checks. It must truthfully reject unavailable GLB/0.5 delivery and create no artifact. The next separate task is the versioned acceleration-aware GLB/0.5 adapter, source workflows, independent geometry/PBR/intermediate-motion/browser checks and a strict complete force-release gate.

[Issue #12](https://github.com/Omegapy/OntoKin/issues/12) retains scopes, adoption, failures and recovery. The old unavailable draft is not substituted for current published source. No other agent is claimed active.

## Remaining full-product requirements

Still required: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful movement; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Every GOAL domain remains required. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-force-integration-20261019-0408Z-astra` |
| Task | Integrate checked PR #13 and verify resulting main; preserve separate Agent/0.5 work. |
| Acquired UTC | 2026-10-19T04:08:00Z, after prior expiry, unchanged refs and successful current-head CI were reconciled. |
| Expires UTC | 2026-10-19T04:38:00Z |
| Observed main before acquisition | `c5c40144f46172a7980fb45c8b5ae3a4b78a1299` |
| Reserved scope | Main integration, STATUS and source-kernel integration evidence. |
| Recovery | Read actual main, PR #13, issue #12 and CI before retrying. Kernel publication already succeeded; do not rerun helpers or merge an unchecked head. Preserve any completed merge and all separate branch work. |

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue interactively toward GOAL; attachment or stream errors do not change repository state.
