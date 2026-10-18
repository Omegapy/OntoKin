# OntoKin status

Current checkpoint: **2026-10-18T19:02:44Z**. The complete native **M01–M12** release gate passed on implementation `80d59bb2b09a5a57cad8e1b477d89f23a3e5a5a1`, branch `work/agent03-integration-20261018-1722`, [PR #9](https://github.com/Omegapy/OntoKin/pull/9). Evidence publication and main integration are in progress under the lease below. The complete [GOAL](GOAL.md) remains **in progress**.

## Completed implementation and acceptance

Language `0.3` / `surface-0.1` now supplies actual parameterized exterior geometry, regional PBR materials, rigid placement and source-driven animation through the native source/compiler pipeline. [OK-AGENT-003](docs/engineering/OK-AGENT-003-native-surface-program-workflows.md) implements explicit `ontokin.agent/0.3`: source discovery, bounded summaries and revision-bound `surface.mesh_page`, atomic section/material edits, evaluation and exact `ontokin.glb/0.3` artifact retrieval. Pages contain at most 256 complete carrier-local triangles; signed cursors bind accepted revision, occurrence, complete geometry/material identity and ordering. Failed candidates, budgets and cancellation preserve accepted state. Earlier protocols, source profiles, catalog defaults and separate stores remain compatible.

[The durable release evidence](docs/engineering/surface-release-validation/README.md), [summary](docs/engineering/surface-release-validation/validation-summary.json), archive and per-file hash manifest identify exact sources, operations, artifacts, numerical results, captures, visual observations and CI. [OK-ENG-004](docs/engineering/OK-ENG-004-native-surface-release-conformance.md) documents reproduction and the strict evidence audit. Historical GLB adapter evidence and [PR #7](https://github.com/Omegapy/OntoKin/pull/7), merged at `1976b615935ee17ff45e7e6392cded85dc317e87`, remain unchanged.

| Evidence | Actual result at implementation `80d59bb` |
| --- | --- |
| Runtime identity | `ontokin-reference` 0.4.0; SHA-256 `abebb2fe7f5af46862db0c24a83c244113a2cfabea1b8a69a22260e4aef2d4d6` |
| Implementation tree | `a2d9d8f6cc897fb6b5781ed06f2a89e9b256b60c`; tracked checkout clean |
| Verification inventory | SHA-256 `9cd60ecfc1e52f714adaa410f0928dc1f20bc48680c9ef596a4c54bbff93c012` |
| Full regression suite | **464/464 passed**, 167.052457 s; every current method plus all 439 inherited identities retained; stable inputs |
| Core / original agent | **43 source cases / 694 assertions** and **A01–A10** passed |
| Current construction | **C01–C20: 20 passed, zero failed/pending**; 128 required methods passed; fresh matching source, GLB, browser and reviewed capture |
| Native acceptance | **M01–M12: 12 passed, zero failed/pending**; 61 mapped methods passed in 35.252839 s; `full_gate_complete: true` |
| Actual native agent workflow | 22 fixtures; **492 exchanges**, 22 immutable snapshots, 150 mesh pages, 308 source poses; rejected edits, scoped repairs, insertion/reorder/removal, ordinary and generated counts 1/3/7 |
| Native destination | **22 GLBs / 1,636,624 bytes**; Khronos zero errors/warnings/infos/hints; geometry, winding, normals, PBR, placement, identity and **308 independent Three.js poses** passed |
| Native browser | Four fixtures, **84 pose comparisons**, **12 visually inspected captures**; Chromium 141.0.7390.37; no page, console or network failures |
| Current legacy destination | 18 objects; 126 Three.js and 126 browser pose comparisons; Khronos zero errors/warnings; inspected keyed-rack capture |
| Identified implementation CI | [39153863765](https://github.com/Omegapy/OntoKin/actions/runs/39153863765): Python 3.11, 3.12, 3.13 and GLB/visual jobs all passed for `80d59bb` |
| Documentation preservation | 29 historical sources, 233 sections and 602 local links passed |
| Main integration | Pending verification of actual merge and its own four CI jobs; implementation CI is not a claim about a later changed revision |

Changed components: program service/protocol/runtime/store and new `program_surface.py`; profile-aware construction catalog; agent and main CLIs; narrow final-response transaction/store-startup hardening; Agent/0.3 schemas/contract; actual source workflow builder and fixed composition fixtures; independent native destination/browser tools; new surface conformance runner/mapping and tests; additive CI and guides. No installed dependency directory is committed. Package version remains experimental **0.4.0**.

The release closes the adopted finite surface requirements, including real source edits and source-to-export functionality. The analytical and rendered fixture corpus does not establish arbitrary continuous accuracy or untested destinations. Recorded GLB playback is not live physics. Visual lofts add no represented matter or motion authority.

## Exact next development task

Freeze a new explicit source/profile contract for an **instantaneous world-expressed impulse applied at a target-local point on a free homogeneous sphere**, then implement it through source parsing/type checking, ordered atomic events, evaluation, bounded source-aware inspection, agent repair and native recorded export. Include off-center angular momentum, rotated application frames, complete release state, zero/repeated impulses, invalid mode/unit/frame/overflow cases and high-spin export sampling. Existing profiles must retain their current meanings. This advances the off-center impulse portion of PHY-008; finite forces, contacts and general dynamics remain separate requirements. No new impulse operation is implemented or adopted by this status statement alone.

The rationale is to reuse the exact authored-event clock and current sphere inertia before adding endogenous contact times. Sphere/static-plane contact remains a following candidate and requires an explicit rule for irrational impact times and event ordering. The implementation starts only after the versioned contract and predetermined fixtures are frozen.

## Remaining full-product scope

Still unmet: richer algorithms/libraries and compatible part replacement; textures, mapping, smooth surfaces and deformation/skinning; contacts/collisions, general rigid dynamics, forces and dynamic or closed mechanisms; purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; fluids/deformable materials; reusable animation transitions, live engine behavior, scale/performance and measured agent-authoring benefit. Creature, vehicle, appearance and every other full-product area remain governed by GOAL. Current physics is bounded uniform-gravity/free homogeneous spheres and prescribed connections with collisions disabled. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Integration owner | `interactive-agent03-20261018-1835Z-astra-root` |
| Task | Preserve complete native release evidence, integrate PR #9 and verify resulting main CI. |
| Acquired UTC | 2026-10-18T18:36:06Z |
| Expires UTC | 2026-10-18T19:33:58Z |
| Observed main | `3dffe428710f2abae8a929c25ac56487ef927093`, renewed after hash verification of the complete evidence archive; original lease `385dd7ec` |
| Verified branch checkpoint | `80d59bb2b09a5a57cad8e1b477d89f23a3e5a5a1`; complete tests, M01–M12, current C20 and CI passed. |
| Immediate action | Publish excluded documentation/evidence only, conditionally merge against observed main, inspect actual merge/CI and record result; then release or renew after a meaningful checkpoint. |
| Recovery | Inspect actual refs, current STATUS, intended commit and outstanding operations before retrying an interrupted write. Independent nonoverlapping branches remain permitted. |

[Previous main STATUS at 17:27](docs/engineering/surface-validation/status-20261018-1727.md.txt), [earlier recovery](docs/engineering/surface-validation/recovery-2026-10-18.md), historical construction/agent/native evidence and original preservation hashes remain intact. [Issue #8](https://github.com/Omegapy/OntoKin/issues/8) records branch scopes and handoffs. A missing uploaded-image error in chat is unrelated to repository work; do not retry those attachments.

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue development interactively toward GOAL; a branch or configured schedule does not establish that another worker is running.
