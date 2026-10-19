# OntoKin status

Checkpoint: **2026-10-19T03:29:00Z**. Native surface **M01–M12** and source impulse **I01–I12** remain integrated and verified. The adopted source `0.5` / `force-0.1` parser, compiler and analytical evaluator are implemented and published in [PR #13](https://github.com/Omegapy/OntoKin/pull/13). Integration of that bounded implementation checkpoint is in progress. The complete force release **F01–F12**, Agent/0.5, GLB/0.5 and the full [GOAL](GOAL.md) are **not complete**.

## Integrated finite releases

Source `0.3` / `surface-0.1`, Agent/0.3 and GLB/0.3 provide actual parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`; [original surface evidence](docs/engineering/surface-release-validation/README.md) remains unchanged.

Source `0.4` / `impulse-0.1`, Agent/0.4 and GLB/0.4 add authored world impulses at target-self points on free homogeneous spheres, off-center angular response, ordered release/impulse semantics, whole-boundary rollback, bounded source-aware inspection, physical-parameter source repair and conservative recorded animation. PR #11 merged at `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`. All four resulting-main jobs passed in [39178143664](https://github.com/Omegapy/OntoKin/actions/runs/39178143664). [Release evidence](docs/engineering/impulse-release-validation/README.md) and [integration identity records](docs/engineering/impulse-release-validation/integration.json) preserve the 40 fixed source cases, 124 mapped methods, both 588-test inventories, current inherited gates, nine source-built impulse GLBs, 192 fixed and 7,628 dense destination poses and reviewed captures. These records are historical proof for their identified implementation, not evidence for changed force code.

[The preceding complete STATUS](https://github.com/Omegapy/OntoKin/blob/3b962fede4d44fb26ad152029a1fd9b1414159dc/STATUS.md) retains all original archive, commit and measurement details. No original evidence or accepted older-profile fixture has been altered. Recorded GLB playback is not live physics; visual lofts add no matter or motion authority.

## Published force source-evaluator checkpoint

Implementation **`cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1`**, tree **`a92aac948bbb6e80e7adaa136d8a6098f0f17563`**, on `work/force01-recovery-20261019-0144-astra`. It is not yet integrated at this STATUS checkpoint.

The source contract was adopted at `676e5542c09b8af1cbc9e5f0b5bbb42a898b1e34` before runtime work. It defines constant world forces at the center of mass of a free homogeneous sphere, exact rational completion clocks, additive final active sets, unchanged trajectory anchors when canonical acceleration is unchanged, inherited release/impulse order, whole-boundary rollback, bounded provenance and valid requested prefixes. The original 44-case corpus remains byte-identical; twelve supplemental cases and ten independent contract-review tests were added. Additive errata `26307378dd99b298bfa230bd13660dbe36eb1c1f` preserve the original fixtures while correcting S10/S11 initializer braces and P09 before-zero derivatives against independently executed inherited semantics. No tolerance was widened.

| Executed check | Actual result |
| --- | --- |
| Local complete regression | **677/677 passed**, 193.790 s |
| Local focused force and review checks | **89/89 passed**, 2.124 s; all 56 effective source cases exercised |
| Original source conformance | **43 cases / 694 assertions passed** |
| Documentation preservation | **29 historical sources / 233 sections / 663 links passed** |
| Independent publication execution | [39194062765](https://github.com/Omegapy/OntoKin/actions/runs/39194062765): exact tree required; **677/677**, 160.218 s; **89/89**, 1.716 s; source conformance and preservation passed |
| Publication source and logs | Artifact `12161410669`, ZIP SHA-256 `e2e374d6d1e84497b27618a85335b00b80ecd63070c21664a44f85dbd81c8fb5`; bundle and actual source tree checked again after retrieval |

Changed components: new `syntax05.py`, `force_source.py`, `force_runtime.py`; narrow hooks in source dispatch, linker, construction, immutable event payload and evaluator; actual source and transaction/cancellation/budget tests. Original source units, dependencies, geometry and material recipes remain authoritative. Force code adds neither a host-only force operation nor a new physical body. Temporary publication helper workflows and staging payloads are excluded from PR #13.

## Exact next task

Verify the exact PR #13 head's normal Python 3.11/3.12/3.13 and inherited GLB/browser jobs, integrate the checked source-evaluator checkpoint safely, and record resulting-main verification. This does not close F01–F12. Then implement explicit Agent/0.5 and GLB/0.5 with versioned operation/delivery contracts, actual source-authorized force/mass/duration repair, complete bounded world-force inspection and artifact retrieval, conservative acceleration-aware recording, independent format/geometry/PBR/intermediate-pose/browser checks, and a strict current-identity force-release gate. Keep older profile defaults, protocols, stores, snapshots and output contracts unchanged.

[Issue #12](https://github.com/Omegapy/OntoKin/issues/12) and PR #13 retain scopes, recovery, adoption and actual failures/fixes. The unavailable earlier local draft remains separately identified; do not replace current published sources with an assumed reconstruction. The next agent/export work may proceed on a separately declared branch from the published kernel without modifying shared integration records.

Still unmet: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful movement; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Every GOAL domain remains required. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-force-kernel-integration-20261019-0329Z-astra` |
| Task | Integrate verified PR #13 source-evaluator checkpoint, not declare the full force release complete. |
| Acquired UTC | 2026-10-19T03:29:00Z |
| Expires UTC | 2026-10-19T03:59:00Z |
| Observed main before acquisition | `3b962fede4d44fb26ad152029a1fd9b1414159dc` |
| Reserved scope | Main integration, STATUS and source-kernel integration evidence. |
| Recovery | Read actual main, PR #13, issue handoffs and CI before retrying. Kernel publication already succeeded at `cd5a6f2`; do not rerun publication or merge an unchecked head. |

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue interactively toward GOAL; attachment or stream errors do not change repository state.
