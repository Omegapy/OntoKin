# OntoKin status

Current checkpoint: **2026-10-18T17:27:58Z**. Native `surface-0.1` source-to-GLB/0.3 export and material integration is merged into `main` through [PR #7](https://github.com/Omegapy/OntoKin/pull/7), merge `1976b615935ee17ff45e7e6392cded85dc317e87`. All four jobs passed independently on the resulting main revision. The complete [GOAL](GOAL.md) remains **in progress**. This adapter milestone does not complete the native surface release or the language.

## Implemented and verified milestone

[OK-ENG-003](docs/engineering/OK-ENG-003-native-surface-glb-export.md) documents the implemented adapter. The [identified native evidence](docs/engineering/surface-native-validation/README.md), [summary](docs/engineering/surface-native-validation/validation-summary.json), and retained archive contain actual source bundles, 12 GLBs, decoded geometry/material/animation checks, browser evidence, complete test results and exact hashes.

| Component | Delivered behavior |
| --- | --- |
| Native geometry | Authored keyed loft sections, numeric station order, caps, outward flat normals, parameterized proportions and source-driven composition. |
| Material regions | Separate indexed primitives and distinct region identities; actual linear RGBA, metallic, roughness and alpha behavior. |
| Placement and animation | Local visual position/rotation applied once; evaluator-driven carrier world tracks, including noncommuting rotation and existing release regressions. |
| Source integrity | Complete pinned program revision, entry/import bytes and hashes, occurrence identities, source locations, recipe/order/region metadata and artifact identity. |
| Bounded work | Per-occurrence aggregate vertices and byte caps; cancellation through generation, encoding, full timeline validation and final return. |
| CLI and compatibility | Explicit `--target ontokin.glb/0.3`, optional `--bundle`, unchanged pinned Studio manifest example, source/output alias protection; earlier source and export profiles preserved. |

Changed runtime files: `ontokin/scene.py`, `gltf.py`, `cli.py`, narrow construction diagnostics, and the optional preflight callback in `evaluator.py`. Added `tests/test_surface_export.py`, `tests/test_surface_export_cli.py`, the native source/destination/browser tools, CI steps, adapter documentation and the source file manifest. Package version remains experimental **0.4.0**.

| Evidence | Actual result |
| --- | --- |
| Published implementation | `908032be8762dfe533fcef06356bc0d768183d73`, branch `work/glb03-native-pbr-20261018-1519-gpt6` |
| Implementation tree / runtime digest | `ae39d24ef7903a6b4c9e5bd5abe590ff2e74c686` / `14b2529edba069a5e98bf701c96988d36d5ada6469411da29623b9fc91ebb82c` |
| Full Python suite | **390 passed**, 114.035 s locally; 39 added native export/CLI regressions over the recovered 351-test baseline. |
| Original conformance | **43 source cases / 694 assertions** and **A01–A10** passed. |
| Current construction conformance | **C01–C19 passed; C20 pending** for the changed implementation identity. Historical C20 remains verified and unchanged. |
| Native external checks | 12 actual source GLBs; Khronos zero errors/warnings; **98** independent Three.js carrier pose comparisons; geometry, winding, normals, PBR, placement and provenance passed. |
| Native browser checks | Chromium 141.0.7390.37; **28** pose comparisons, **six** visually inspected captures, playback hold, zero page/console/network errors. |
| Documentation | 29 historical sources and 233 sections preserved; 548 local links passed before this added evidence record. |
| Implementation PR CI | [39148556348](https://github.com/Omegapy/OntoKin/actions/runs/39148556348): all four jobs passed. |
| Resulting main CI | [39148970424](https://github.com/Omegapy/OntoKin/actions/runs/39148970424): all four jobs passed for merge `1976b615`, including legacy and native GLB/browser paths. |

The maximum measured native local vertex conversion error was `2.727053982631844e-8 m`, within the fixed `1e-5 m` surface gate. Finite fixtures and samples do not establish continuous accuracy for arbitrary programs. The evidence preserves a reported untracked development-dependency symlink at build time; all tracked code matched the identified implementation. No dependency directory is committed.

## Next task: Agent/0.3 surface workflow

[Issue #8](https://github.com/Omegapy/OntoKin/issues/8) records the exact contract decisions and active branch scopes. Complete the explicit `ontokin.agent/0.3` binding with surface discovery, bounded summary inspection, revision-bound `surface.mesh_page`, atomic source section/material repair, evaluated state and GLB/0.3 artifact retrieval. Preserve the default Agent/0.2 service and separate stores.

Parallel work began from published `b8ae453` and depends on the final `908032be` exporter. The contract worker owns new OK-AGENT-003/schemas and profile-aware catalog; the service worker owns program service/protocol/runtime/store files; the test worker owns new service/protocol tests. Root CLI/integration uses `work/agent03-integration-20261018-1722` from `908032be`. Exact worker branches, commits, tests and handoffs are in issue #8. No branch checkpoint is an integrated acceptance claim.

Then execute the full native **M01–M12** gate: actual composed and generated sources, predetermined held-outs and boundaries, rejected-candidate preservation, scoped repair with unchanged siblings/library pins, insertion/reorder/removal, cursor/resource/cancellation failures, independently checked nonidentity rotation/release, and matching source/artifact/browser identities. Reissue current-implementation C20 evidence after the final runtime changes while retaining historical evidence. M07/M08 agent workflows and the complete M12 regression/attestation gate remain open.

## Preserved scope and history

The [previous main STATUS](docs/engineering/surface-validation/status-20261018-1442.md.txt), [earlier recovery](docs/engineering/surface-validation/recovery-2026-10-18.md), [0.4.0 construction evidence](docs/engineering/construction-validation/validation-summary.json) and original core/agent evidence remain unchanged. Native parsing/construction had already merged in PR #5; those commits were reconciled, not replayed.

Still unmet: richer algorithms/libraries and compatible part replacement; textures, mapping, smooth surfaces and deformation/skinning; contacts/collisions, general rigid dynamics, forces and dynamic or closed mechanisms; purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; fluids/deformable materials; reusable animation transitions, live engine behavior, scale/performance and measured agent-authoring benefit. Creature, vehicle, appearance and every other full-product area remain governed by GOAL. Existing physics is bounded uniform-gravity/free homogeneous spheres and prescribed connections with collisions disabled. Visual lofts add no physical matter or motion authority. GLB recorded playback is not live physics. Blender delivery and a generic delivered-level check are not established.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Integration owner | `interactive-agent03-20261018-1835Z-astra-root` |
| Task | Integrate tested Agent/0.3 and the complete native M01–M12 gate through PR #9. |
| Acquired UTC | 2026-10-18T18:36:06Z |
| Expires UTC | 2026-10-18T19:33:58Z |
| Observed main | `e0ebb9562ec03fb532355cca4c672bcc83a0f961` |
| Verified branch checkpoint | `80d59bb2b09a5a57cad8e1b477d89f23a3e5a5a1`; M01–M12 all passed, 464 tests passed, current C01–C20 passed; PR CI 39153863765 all four jobs passed. |
| Immediate action | Verified archive checkpoint d41329798c4b420c5bbc3436a307a33e751413c5 contains 1,247 hash-checked files and the complete M01–M12 pass. Publish the 6,325,076-byte archive (SHA-256 8c49bdeee3cadd5d80883b57937da3c13c815e7ea3ffe56e49efd3324bae761d), conditionally merge PR #9, verify resulting main CI and release this lease. |
| Recovery | Read actual main/PR refs and current STATUS before retrying an interrupted write. Independent nonoverlapping branch work remains permitted. |

This status/evidence publication changes no runtime bytes. Its own later CI is distinct from the verified implementation/main runs above. After a timeout or unknown write, read actual refs and files before retrying; preserve ongoing branch work. A missing uploaded-image error in chat does not block repository development and does not require retrying that attachment.

The owner intentionally disabled **Advance OntoKin** and instructed this session not to reactivate it. No automation was changed. Continue authorized development interactively; configured schedules and branch existence are not evidence of running workers.
