# OntoKin status

Current checkpoint: **2026-10-18T21:16:36Z**. Native **M01–M12** remains implemented, verified and merged through [PR #9](https://github.com/Omegapy/OntoKin/pull/9). The next source impulse milestone is implemented on [draft PR #11](https://github.com/Omegapy/OntoKin/pull/11) at `885fbc011b179422a8f6cb564219c66db09adac3`; all four jobs passed in branch [CI 39165524745](https://github.com/Omegapy/OntoKin/actions/runs/39165524745). Its complete **I01–I12 release gate is still in progress**. The complete [GOAL](GOAL.md) remains **in progress**.

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
| Documentation preservation | 29 historical sources, 233 sections and 603 local links passed |
| Reconciled PR CI | [39157391557](https://github.com/Omegapy/OntoKin/actions/runs/39157391557): all four jobs passed at `1a6dc326` |
| Resulting main CI | [39157876920](https://github.com/Omegapy/OntoKin/actions/runs/39157876920): all four jobs passed at actual merge `1a6dc326` |

Changed components: program service/protocol/runtime/store and new `program_surface.py`; profile-aware construction catalog; agent and main CLIs; narrow final-response transaction/store-startup hardening; Agent/0.3 schemas/contract; actual source workflow builder and fixed composition fixtures; independent native destination/browser tools; new surface conformance runner/mapping and tests; additive CI and guides. No installed dependency directory is committed. Package version remains experimental **0.4.0**.

The release closes the adopted finite surface requirements, including real source edits and source-to-export functionality. The analytical and rendered fixture corpus does not establish arbitrary continuous accuracy or untested destinations. Recorded GLB playback is not live physics. Visual lofts add no represented matter or motion authority.

[The integration record](docs/engineering/surface-release-validation/integration.json) retains raw PR/main run and job records, observed merge state, conditional parent/head identities and proof that all 182 eligible verification inputs match the tested implementation. Archival publication `3e7a2a61a68a7f7442cbe59e97753405ffbc7856` and merge `1a6dc326` preserve those input bytes. Later status-only CI is distinct from the identified resulting-main run above.

## Exact next development task

Finish the adopted, separately versioned source impulse release in [issue #10](https://github.com/Omegapy/OntoKin/issues/10) and [PR #11](https://github.com/Omegapy/OntoKin/pull/11). The frozen OK-LANG-004 contract was published at `342788a2b5868189c72eae0541e86860a0de43ee`; its complete predetermined acceptance corpus remains unchanged. Branch `work/impulse01-integration-20261018-1916-astra` supplies source `0.4` / `impulse-0.1`, explicit Agent/0.4 and native recorded GLB/0.4.

The implemented scope includes instantaneous world momentum at an actual target-self point on a free homogeneous sphere, off-center angular response, ordered release/impulse events, whole-boundary rollback, source-aware bounded inspection, actual mass/radius source repair, conservative high-spin export and older-profile compatibility. All 40 fixed source cases and the published branch CI pass. This is an implementation checkpoint, not full release acceptance.

The immediate work is to close independent retained-evidence audit gaps for decoded intermediate animation values, complete application-history linkage, exact scoped-edit source authorization and ordinary self-frame conversion. Freeze and publish those reviewed corrections; execute fresh complete regression, current core/Agent/C01–C20/M01–M12, actual Agent/0.4 source workflows, independent GLB/browser validation and factual visual reviews; require all I01–I12 and exact-commit CI to pass before integration. Historical evidence cannot certify changed runtime bytes. The earlier diagnostic-default regression and boundary-budget validation gap were fixed; their actual failing and passing results remain in issue #10 and branch history.

After this finite release is integrated, reread GOAL and adopt the next unmet physical-influence task. Finite center-of-mass force intervals are under technical review; they are not yet adopted or implemented. Contacts still require an explicit rule for computed impact times and event ordering. Finite forces, contacts and general dynamics remain separate requirements.

## Remaining full-product scope

Still unmet: richer algorithms/libraries and compatible part replacement; textures, mapping, smooth surfaces and deformation/skinning; contacts/collisions, general rigid dynamics, forces and dynamic or closed mechanisms; purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; fluids/deformable materials; reusable animation transitions, live engine behavior, scale/performance and measured agent-authoring benefit. Creature, vehicle, appearance and every other full-product area remain governed by GOAL. Current physics is bounded uniform-gravity/free homogeneous spheres and prescribed connections with collisions disabled. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Integration owner | `interactive-impulse04-20261018-2116Z-astra-root` |
| Task | Review, validate and integrate the separately versioned source impulse release through PR #11. |
| Acquired UTC | 2026-10-18T21:16:36Z |
| Expires UTC | 2026-10-18T21:46:36Z |
| Observed main before acquisition | `b4366ccaacc672900b9def98c0a56003aadb826b`; prior native release and historical evidence preserved. |
| Published branch checkpoint | `885fbc011b179422a8f6cb564219c66db09adac3`; PR/push CI 39165524745 and 39165521147 passed. |
| Reserved shared scope | Main integration, STATUS/GOAL release records and new impulse release evidence. Kernel, service and conformance workers retain their declared isolated scopes in issue #10. |
| Immediate action | Publish corrected independent readers/tools, freeze exact verification inputs and complete fresh I01–I12 evidence. Merge only after required checks pass. |
| Recovery | Read actual main/PR refs, this lease, issue #10 and CI before retrying any interrupted write. Preserve concurrent work and immutable historical evidence. |

[Previous main STATUS at 17:27](docs/engineering/surface-validation/status-20261018-1727.md.txt), [earlier recovery](docs/engineering/surface-validation/recovery-2026-10-18.md), historical construction/agent/native evidence and original preservation hashes remain intact. [Issue #8](https://github.com/Omegapy/OntoKin/issues/8) records branch scopes and handoffs. A missing uploaded-image error in chat is unrelated to repository work; do not retry those attachments.

The owner intentionally disabled **Advance OntoKin**. No automation was changed or reactivated. Continue development interactively toward GOAL; a branch or configured schedule does not establish that another worker is running.
