# Supplemental Khronos and Three.js readback

AGENTS.md and OK-ENG-002 require independent Khronos format validation and Three.js readback for exporter changes. The finite C198 geometry reader and Blender receiver remain required. This supplemental checker adds the two missing destinations without changing source meaning, canonical arithmetic, native slot order, native start counts or native transaction limits.

## Separate finite allowance

After an individual native transaction has accepted and sealed its actual candidate, one read-only Node process runs both checks on that candidate's `final.glb`. There are at most **twelve** such checks, one per assigned N01–N12 result. Each uses one 30,000 ms host clock, including at most 28,000 ms child work and 2,000 ms cleanup. There is no retry after an unexpected result. The 65,000 ms native transaction allowance remains unchanged.

The qualification coordinator runs this checker before starting the next native slot. The individual native `run` interface also requires passed supplemental results for preceding slots. A supplemental failure stops qualification; it does not relabel or rebuild a candidate. Passed candidate transactions alone do not establish overall qualification.

The checker cannot export, simulate or render. It starts no Blender receiver, browser or graphical renderer. Three.js is used as a CPU importer. Actual visual review remains a separate required gate against the retained Blender review images.

## Exact selected versions

| Role | Selected version |
| --- | --- |
| Node runtime | `v24.22.1` |
| Khronos glTF Validator | `2.0.0-dev.3.10` |
| Three.js package | `0.186.1`, runtime revision `186` |

These are the retained bytes available in the restored handoff environment. They are not described as the latest available releases. The old carriage-specific readback program is not invoked.

`seal-readback` writes a supplemental executable manifest. It binds the Node executable, its resolved shared libraries and loader configuration, library aliases, both complete retained package trees, the retained module resolver, the new static-tray probe, the Python coordinator, every process argument, the finite environment, all twelve output locations, and the check settings. The main native input lock binds this manifest's actual path, SHA-256 and byte count. Independent approval of that main lock must include these supplemental inputs.

The manifest records all retained files, including dependencies that the selected finite import path does not need. The reachable Three.js path is the retained resolver, `three.webgpu.js`, `three.core.js`, `GLTFLoader.js`, `BufferGeometryUtils.js` and `SkeletonUtils.js`. The validator's CommonJS entry loads its retained `gltf_validator.dart.js`. Node built-in modules belong to the pinned executable. Package metadata controlling module resolution is included in the file inventory.

## What the checks establish

Khronos receives the exact hashed GLB bytes. External resources are rejected. Its report must contain zero errors, zero warnings and no truncated issue list; the checker ignores no issue classes and applies no severity overrides. The raw bounded report is retained.

Three.js loads the same GLB and measures its actual imported graph. The checker compares fourteen semantic identities, two empty roots, twelve meshes, original object names, semantic roles and relationships, hierarchy, world matrices, actual vertex positions, normals, triangle indices, bounds and materials with the already passed independent audit of those exact GLB bytes. Position differences use the unchanged 0.000005 m allowance; matrix and normal components use 0.000001 where applicable. No animations, cameras, lights, skinning, morphs or external textures are admitted.

Three.js sanitizes `Object3D.name` for its own binding syntax. The probe records that importer name and separately requires the preserved original `userData.name` and semantic identity to match exactly. It does not normalize semantic IDs or geometric values to conceal a difference.

## Preparatory evidence is separate

The dedicated CPU test cohort uses independent synthetic actual-box GLBs for Q01 and Q03. A third case deliberately changes one reference transform and must be rejected. These tests exercise the actual selected validator and importer, but use no native Blender artifact and satisfy none of the twelve later checks of accepted native outputs.

The preparatory cohort starts three read-only Node checker processes. Manifest construction separately inspects Node's version and shared libraries using `node --version` and `ldd`; those are two dependency-inspection commands. All raw checker results and process receipts are retained when the test output directory is specified. Native starts, exports, receiving Blender starts, lifecycle-stub starts and timed authors remain zero for this preparation.

## Frozen native Python startup clarification

Independent review found that Blender's default isolated Python startup ignores `PYTHONDONTWRITEBYTECODE` and `PYTHONHASHSEED`. The frozen native arguments therefore include `--python-use-system-env` before the `--python` script argument. This makes the explicitly supplied `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0` and `PYTHONSAFEPATH=1` effective from startup, before worker or receiver imports can run. The safe-path setting preserves the path protection of the earlier isolated startup; Blender's explicit bundled add-on path insertions remain available. The pinned Blender distribution supplies its own bundled Python home.

The native process receives the exact environment dictionary in the main input lock. It includes those four Python values, fixed locale/timezone and thread settings, the frozen software-rendering values, and fresh private home/configuration/cache/temporary/script directories. It receives no ambient values, `PYTHONPATH` or `PYTHONHOME`. This explicit startup selection does not weaken the exact distribution inventory or permit post-result cache exceptions. Host Python continues to use `-IBS`; its separately documented isolated behavior remains unchanged.
