# C244/0.1.0: observer-only capture hook decision

**Status: CONDITIONAL DESIGN EXCEPTION; NO NATIVE EXECUTION ADMISSION.**

Observed baseline: `6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01`, tree `bf6ede10c8b41efd90f67698ec4de23c88c742eb`.

## Versioned exceptions and limits

C220/0.1.0's no-custom-loader-extension policy is amended **only for an inert, observer-only `GLTFDocumentExtension._import_node` design** with direct `replacing_by` notification and an external glTF-index registry. A future separately reviewed implementation may be proposed. The built-in converter remains mandatory. No callbacks may replace nodes, alter product metadata/resources, attach source labels or scripts, or change default import configuration.

C241/0.1.0's requirement for postconversion `GLTFState.get_scene_node` and `get_node_index` consistency **remains unsatisfied**. This decision permits review of an *alternative evidence requirement*, not a false claim of unchanged contract acceptance: while the original importer is alive verify both forward and inverse map; then track every direct replacement by native identity, and after generation check 18 distinct live nodes under the returned root. An execution-admission decision must independently authorize this replacement of the C241 acceptance gate against the actual installed build, or first require engine-side GLTFState map repair.

## Pinned source evidence

Pin Godot `35e80b3a8822a9df9be390814b62f44c0a9c69e8`:
- [Initial map and callback order](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L7038-L7086)
- [Converter replaces and deletes importer nodes](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension_convert_importer_mesh.cpp#L37-L95)
- [Native replacing_by signal timing](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/main/node.cpp#L3222-L3287)
- [Stored-pointer forward/inverse state lookups](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_state.cpp#L375-L389)

The installed candidate's embedded revision differs from this upstream commit. Source inspection is not installed-runtime proof.

## Required predicates for a later inert implementation

1. Pin installed build and complete extension inventory, callback ordering, script binding, and converter selection, with unexpected overrides fatal.
2. Resolve exact original node index and mesh association through *live* bidirectional GLTFState checks in the preconversion callback. Names, traversal, geometry, labels and shared mesh IDs cannot establish identity.
3. Capture untouched preconversion native metadata, script/signal/resource properties and native instance identity **before** observer signal installation. Keep source authority separate.
4. Subscribe nondeferred, nonpersistent, directly. Record each old-to-new native instance transition once with one original source index, no callback-return-code success assumption.
5. For frozen 18-mesh fixture demand synthetic nonmesh root, zero mesh-root replacements, 18 descendant replacements. Reject duplicates, missing transitions, cross-index reuse, unexpected roots and retired handles.
6. At signal time capture only the transition; final arrays and resources are not yet complete. After return use only the external **live** registry and native-scene membership, never stale GLTFState pointers.
7. Keep pre/post native captures distinct from source/sidecar retention and observer-derived identity. Persistent fatal latch vetoes output, save, acceptance or retry on *any* callback or accounting error, regardless of ERR_CONTINUE.
8. Exact negative controls and independent review are prerequisites, not a native observation claim.

## Gate and next scope

This is a **zero-start decision**. No Godot, version probe, import, rendering, save, reopen, source re-export, schema/tolerance change, or aggregate was run. All R07 and strict original Blender-normal gates remain pending/failed as previously recorded.

**Next:** independently review this decision and build a bounded inert observer/registry prototype, then decide whether actual installed extension bindings can support the revised C241 map requirement. If not, select a pinned engine-side repair separately. No native start is authorized.

The full C244 decision, 12 inert test cases, outputs, source and preservation evidence are carried in the C244 Library handoff; this in-repository copy is the reviewable scope record.
