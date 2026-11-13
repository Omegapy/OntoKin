# C216 native receiving experiment, version 0.1.0

## 1. Selected promise and preserved failures

For the single accepted C210 assembly and the exact installed Blender 4.3.2 executable/importer identified in [build_bindings.json](build_bindings.json), the experimental promise is **exact retained source authority plus independently measured native shading and disclosed loss**. The source bundle, semantic sidecar, source-normal float32 payload and accepted GLB remain authoritative. Blender’s actual normal values are observed without changing product normals, topology or materials to improve a comparison.

This is an explicit finite receiving decision, not a new normal-fidelity tolerance. C211’s original strict `2e-6` normal failure remains failed. C214 stays synthetic-only and C215 remains a non-accepting CPU loss reporter. The held C211 revision `cdae8b582a37e37f76f142f07039ba74cedc08ad`, including its denoising correction, is not run or merged. C216 independently implements and observes scene/view-layer denoising disabled under a new capture revision. A C216 render cannot establish that the old held correction executed.

Acceptance requires all of the following actual evidence: exact source/build/settings/capture bindings; complete loss measurement from native corners; source-aligned geometry, identity, dimensions, poses and material values; retained semantic mapping with unsupported execution explicitly separated; saved-scene source authority and reopen persistence; and useful reviewed native images. Any unmet item is a failed, blocked or unrun gate. Small measured normal loss or a metadata copy alone grants no acceptance.

## 2. Scope and inputs

The fixed source is C214’s accepted C210 triple: `after.glb`, `after.program.bundle.json` and `after.semantic.json`. The C214 prototype independently validates it and constructs the exact source-normal payload. The retained `after.reference.json` has SHA-256 `b8df15b2645caaa523a79116912ddbfb9db1eb293c2f1f6d3e190b212bcd8a55`; it supplies the unchanged seven-time motion reference. No OntoKin source program or exporter runs.

There are 18 product mesh instances, 7,800 triangle instances and 23,400 observed corners. The C215 schema retains native object/mesh names, actual triangle indices and loop IDs, object-local positions and `mesh.corner_normals` values. Object correspondence uses the importer’s preserved `ontokin.path`, `element_id` and source-mapping extras, checked against exact source instances. It never depends on incidental object iteration order. C215 then matches exact local POSITION triples with cyclic winding; normals never choose correspondence. Missing, ambiguous, invalid or drifted geometry stops continuation; no rounding or new matching tolerance is introduced.

The executable is `/usr/bin/blender`, 94,967,000 bytes, SHA-256 `0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4`. The 117 separately installed `io_scene_gltf2` Python files are individually pinned and retained as deterministic tar bytes. The runtime verifies the loaded importer module path. Historical version `[4,3,2]` and build hash `Unknown` are checked in the first approved native start, without a separate exploratory launch. Unknown upstream source/build lineage and unpinned system shared-library closure remain limits; exact input hashing does not claim a hermetic machine.

The host and capture require zero `.pyc`/`.pyo` files under the pinned importer. Initial native cache prefix and any already-loaded importer modules are recorded before further importer loading. An initial external cache prefix is refused. Capture sets `sys.dont_write_bytecode=True` and a newly created empty per-phase `sys.pycache_prefix`, retaining already-loaded modules rather than unregistering/reloading them. Every observed `io_scene_gltf2` module must resolve to a pinned source file with matching bytes and no existing cache; receipts retain `__file__`, `__cached__`, loader/origin, source hashes and actual Python flags before/after import and at closure. The private cache must remain empty. This closes the finite stale-bytecode ambiguity; it does not authenticate a hostile host or all native dependencies.

## 3. Reviewed plan and scene-hash timing

`prepare` requires a clean committed capture checkout. It verifies exact current source against that Git revision, binds the six C216 source/contract files plus unchanged C214/C215 helpers, copies source inputs, and writes an immutable `plan.json`. The plan pins source/receiver/importer/build/settings artifacts, exact commands, per-phase output location, render recipe, deadline, start ceiling and failure rules. Preparation, checking, report generation and independent review start no native process.

A saved scene’s bytes cannot be known before it exists. Before launch, independent review freezes all known input identities and this explicit two-stage binding rule. Start 1 saves the native scene once. The capture then hashes the actual scene and completes the external C215 `input-lock.json`, preserving every prelaunch binding unchanged. Both actual observation envelopes bind this final lock and source payload. Independent review checks that the final lock is exactly the reviewed inputs plus the observed output scene; it is not described as a preknown scene hash. The scene itself retains the prelaunch plan hash, avoiding a self-referential scene hash.

The saved scene contains exact source bundle, sidecar and source-normal payload texts, plus base64 accepted GLB bytes. It also contains canonical scene/object semantic JSON in explicitly named C216 properties. Those properties are an adapter mapping, not importer-native executable physics. Original importer extras are captured before this mapping; current actual extras are captured again on each phase. No rigid-body world, modifier or constraint is introduced.

## 4. Exactly bounded native schedule

Root alone launches after the independent reviewer and root approve the exact source revision and prepared plan. Each start consumes an exclusive durable reservation before process creation. An exception, timeout or uncertain process consumes the attempt and blocks continuation; no automatic retry, relaunch, engine fallback or camera adjustment is allowed.

| Start | Required actions | Continuation |
| --- | --- | --- |
| 1, import | Validate exact runtime/source/build/importer/settings; import the unchanged GLB once; map source authority; configure review cameras/lights/render settings; save `received.blend`; capture actual native corners/poses/materials/semantics; render overview and sphere detail | Independent complete numeric/provenance/visual review and root approval of exact observed import artifacts |
| 2, reopen | Verify exact original saved-scene bytes; reopen with scripts disabled and no import; verify authority texts and metadata; recapture the same measurements; render the same views; verify saved-scene bytes unchanged | Independent final review, handoff closure, stop |

Maximum native starts: two, including attempted or unknown outcomes. Maximum wall time: 240 seconds per start. Blender threads: two. The driver launches with factory startup and automatic scripts disabled and an isolated per-phase Blender user configuration/scripts/data directory. It requests Python user-site disabled through the environment; actual `no_user_site`, `ignore_environment`, `isolated` and cache flags are recorded because Blender may ignore environment settings. On deadline it sends SIGKILL to its own process group and observes return code/group existence. A remaining or unknown group is never relabeled successful. Unknown outcomes require reconciliation before any separately reviewed future attempt.

Capture outputs are written before rendering. Any native failure, changed source/input/build, unknown outcome, missing file, failed exact geometry, incomplete denominator, incorrect metadata or unreviewable image stops this task. Unexpected API incompatibility is retained as a concrete blocker. No second target, direct-authoring comparison, general importer or production runtime change belongs to this experiment.

## 5. Measurements and visuals

Product geometry stays in its imported object-local frame. The fixed Blender-to-source conversion is `(X,Y,Z) -> (X,Z,-Y)`. C215 reports every source corner, original float32 source normal, raw native direction, component and angular differences, plus all unmatched/ambiguous/invalid outcomes. The independent reviewer parses raw accepted GLB bytes separately and checks the complete denominator. Report distributions and maxima describe this fixture/build, never a universal error bound.

Capture samples world poses at `0, 0.25, 0.5, 0.75, 1, 1.5, 2` seconds, 60 fps: 126 object poses per phase. Independent comparison retains C210/C211 position and orientation limits of `0.001 m` and `0.001 rad`, and existing PBR comparison limit `2e-6`. These are geometry/playback/material checks; they do not replace or relax the failed C211 normal limit. Current materials retain actual Principled inputs, sidedness and triangle material indices. Semantic review covers original native extras, explicit mapped scene/object JSON, the full source sidecar, and unsupported live physics/action execution.

Cycles CPU renders two PNGs per phase at 960×720 and 16 samples, fixed seed 216, no adaptive sampling, scene denoising false, all view-layer denoising false, opaque background, Standard view transform, exposure 0, gamma 1. The world has linear background `(0.12,0.12,0.12,1)` at strength 0.7 and one area light at source `(3,5,6)`, energy 1400, disk size 6. Cameras and light are explicit review-only objects, separate from the 18 product meshes, and are configured before scene save.

| View | Source-space eye | Source-space target | Orthographic scale | Time |
| --- | --- | --- | ---: | ---: |
| Overview | `(4,3,7)` | `(0,0,0)` | 5.3 | 0 s |
| Sphere detail | `(-0.73,0.18,0.45)` | `(-1,0,0)` | 0.32 | 0 s |

Review the whole assembly for missing objects and the curved detail for meaningful visible shading. Images cannot resolve a numeric precision claim by themselves. The same planned views are repeated after reopen; useful visibility and persistence must be observed, not inferred from file existence. There is no image rerender allowance if a view is unusable.

## 6. Evidence, acceptance and stopping point

Keep actual source commit/tree, prepared plan and every input byte, independent reviews/approvals, reservations, exact process receipts and logs, all native measurements, final lock, saved scene and four planned images if reached. Failed and unknown operations remain visible. Root may invoke the unchanged C215 reporter, but its fidelity/receiving/provenance flags remain false and `shadingAcceptance` remains `NOT_EVALUATED`. A separate independent C216 review decides the finite promise from captured evidence and explains any qualified acceptance or blocker.

Source authority preservation does not recover native quantized normals, prove executable joints/actions, establish full-product release or demonstrate comparative authoring benefit. If the finite gate passes or a concrete blocker appears, preserve source/evidence durably, freeze workers, verify offline restoration and the next handoff ZIP, confirm its save, and stop.
