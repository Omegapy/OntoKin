# C243/0.1.0: preserve source identity across native node replacement

## Decision and scope

**Disposition: BLOCKED_NO_SAFE_CALLER_CAPTURE_WINDOW_ESTABLISHED.** The unchanged
[C220 plan](../second-target-c220/PLAN.md) and
[C241 contract](../second-target-c241/CONTRACT.md) select one complete
`GLTFDocument.generate_scene` call, with the built-in runtime mesh converter and
no observer-supplied loader extension. The inspected upstream path does not give
the ordinary caller a proven live node-index association after that call.

A glTF node index identifies an object in the original scene. Godot's loader map
associates that index with a native node pointer. Replacing the native node does
not itself change an independent variable holding the old pointer. C243 checks
where that replacement occurs and what evidence a future capture would need.

This finding closes the bounded design investigation. It does not establish
universal impossibility, an executed memory fault, or the behavior of the
installed binary. Its build lineage still differs from the inspected upstream
revision. No native start is permitted by this result. Original schemas,
tolerances, retained evidence and the strict Blender normal failure are unchanged.

## 1. Exact source and fixture evidence

All upstream references below are pinned to Godot commit
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`. The
[source inventory](evidence/PRIMARY-SOURCES.json) binds complete source bytes,
Git blob identities, SHA-256 hashes and their paths in the handoff. Four sources
are reused from the preserved C241 evidence; five supporting files were fetched
at the exact revision for C243. License notices remain in the retained sources.

| Source fact | Exact inspected definition and implication |
| --- | --- |
| Mesh creation | [`_generate_mesh_instance`, lines 4052–4071](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L4052-L4071) creates an `ImporterMeshInstance3D` for a mesh-bearing source node. |
| Initial source map | [`_generate_scene_node`, lines 4510–4593](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L4510-L4593) applies native imported metadata and stores the current node in `scene_nodes` under the original glTF index. |
| Synthetic root | [`_generate_scene_node_tree`, lines 6857–6905](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L6857-L6905) creates a `Node3D` parent when `GODOT_single_root` is absent. |
| Capture window | [`generate_scene`, lines 7038–7086](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L7038-L7086) builds the map and animation, calls extension `import_node`, replaces/deletes a mesh root if present, calls extension `import_post`, and only then returns. |
| Descendant conversion | [Converter, lines 37–95](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension_convert_importer_mesh.cpp#L37-L95) replaces importer nodes, copies their metadata, converts mesh resources, and deletes old nodes. The complete inspected file contains no `scene_nodes` update. |
| Runtime selection | [Registration, lines 129–140](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/register_types.cpp#L129-L140) selects this built-in converter outside editor mode. |
| Pointer lifetime | [State storage](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_state.h#L108-L116) is `HashMap<GLTFNodeIndex, Node *>`; [forward/inverse lookup, lines 375–389](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_state.cpp#L375-L389) returns or compares the stored pointers. |
| Replacement notification | [`Node::replace_by`, lines 3222–3287](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/main/node.cpp#L3222-L3287) emits `replacing_by(new_node)` before moving children. It does not know or update `GLTFState.scene_nodes`. |
| Hook boundary | [Extension dispatch, lines 134–149](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension.cpp#L134-L149) exposes `_import_node` and `_import_post` through an extension. Callback errors in `generate_scene` use `ERR_CONTINUE`, so returning an error is not a reliable whole-call abort. |

The original GLB remains 185,236 bytes with SHA-256
`05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`.
Fresh read-only decoding finds 18 source nodes, all mesh-bearing scene roots,
five shared meshes, no skins, and no `GODOT_single_root` extension. All 18
node-to-mesh pairs match the unchanged C220 part map. The ordinary/default mesh
branch places these nodes under a synthetic nonmesh root and enters descendant
conversion. The loader first permits selected built-in extensions to supply a
node; the nine-file review does not prove every extension override is inactive.
Exact installed extension selection remains a prerequisite. This is the
applicable default-path risk, not an exhaustive engine behavior prediction.
Mesh sharing also means a mesh-resource association alone cannot
identify each source-node occurrence. [Measured static evidence](evidence/STATIC-MAPPING-REVIEW.json)

## 2. Why the unchanged route remains blocked

The ordinary caller cannot connect a replacement observer between map creation
and conversion: both happen inside its single `generate_scene` call. Calling
`get_scene_node` afterwards and then testing validity is not an established safe
route. The binding would first receive a value from a map whose entry can name
the deleted importer node. C243 does not execute that operation to test it.

Walking the returned live scene and calling `get_node_index` avoids deliberately
starting with a deleted node, but still compares those live nodes with the old
stored pointers. It does not provide a proven original-index association for the
replacement nodes. A nonnegative result is not sufficient evidence of lifetime
correctness when the underlying map has not been rebound.

`Node::replace_by` cannot repair a separate raw-pointer map automatically.
Its signal is useful only if a subscriber is installed before replacement.
Subscribing after `generate_scene` returns misses both the conversion and old
node deletion. The source has internal C++ generation helpers declared under
`public:`; those helpers are not the reviewed script bindings. Splitting the
loader around them would change C241's prescribed sequencing and requires its
own reviewed implementation. [Header](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.h#L218-L237)

This is a bounded source argument about the inspected definitions and chosen
caller route. It does not prove the absence of every mechanism in every engine
build. No such mechanism has been identified and bound to this installed
candidate, so native capture approval remains withheld.

## 3. Route dispositions

| Route | Disposition in C243 |
| --- | --- |
| Post-return forward/inverse lookup alone | Blocked: no reviewed lifetime-preserving map update connects old and replacement nodes. |
| Names, traversal order, geometry matches, or copied source labels | Rejected as identity substitutes. They do not meet the unchanged source-map requirement. Traversal may inventory native content only. |
| Per-mesh resource association | Insufficient for this fixture's 18 occurrences sharing five meshes; it also bypasses the required original node association. |
| Insert source indices into metadata before generation | Not adopted. Observer-authored labels cannot substitute for observed loader identity, and their provenance cannot be called originally imported. |
| Rebuild/rebind the map after generation | Requires an already proven old-to-new association; it cannot manufacture the missing evidence. |
| Disable the built-in converter, use editor import, or manually split internal generation | Outside the selected C220/C241 route; no such switch occurs. |
| Engine-side map repair | Possible separate engineering direction, but requires exact new source/build identity and an independently reviewed candidate change. Not selected here. |
| Preconversion callback plus replacement signal | Concrete proposed route below; **unadopted** because it requires a narrowly permitted custom observer extension. |

## 4. Concrete candidate for a later versioned decision

The smallest identified interception point is an observer-only
`GLTFDocumentExtension._import_node` callback, followed by the native
`replacing_by` signal. A later decision would need to amend **both** the C220
no-custom-extension boundary and C241's reliance on post-conversion lookup.
It would retain the built-in converter and permit only an external observation
registry. The following is a design candidate, not executable observer source,
an adopted exception, or approval to start a process.

An external replacement registry does not repair Godot's state map and does not
establish `GLTFState.get_node_index(new_node)`. The later decision must explicitly
version C241's forward/inverse API-boundary requirement to permit the independently
observed replacement chain, or require a separately reviewed safe map repair.
It cannot claim that the old inverse-map condition passed unchanged.

1. **Establish identity while the node is live.** In the prescribed callback
   phase before root or descendant conversion, obtain the original index from
   the loader's map and verify `get_scene_node(index) == callback_node` and
   `get_node_index(callback_node) == index` while the node is live, together with
   its `GLTFNode` association. Require the exact locked 18-node set and each source
   node/mesh binding. Validate the applicable build and extension ordering
   before relying on this source-derived lifetime assumption. Do not infer an
   index from the callback's arrival order, a name, geometry, or copied text.
2. **Capture native originals before observer mutation.** Save typed original
   node metadata, scripts, signal connections, native class/instance identity,
   parent/owner relationships, resource identities and raw imported values.
   Keep source-sidecar bytes in a separate authority record. Bind each snapshot
   to its exact preconversion callback phase; do not present snapshots from
   different phases as one simultaneous observation. Unsupported types cause
   a persistent capture failure. Only after that node's original state is
   recorded may the observer install its signal connection; record that
   connection as an observer action, with no product metadata/resource write.
3. **Subscribe before replacement.** Connect a direct, nondeferred,
   nonpersistent `replacing_by` callback for each mapped importer node. Keep the
   callback owner and per-node state alive outside the imported scene. Record
   one original index and old native identity in an external registry. Do not
   attach an identity tag or observer script to product nodes. Full extension
   inventory, registration order, callback source and signal flags must be
   frozen and independently checked before a later execution.
4. **Transfer only observed identity at the signal.** The callback receives the
   replacement node while the old node still exists. Record the exact old-to-new
   event and update that index's external live-node reference. Preserve the old
   instance ID as a value only; never dereference the old node after deletion.
   Reject unknown,
   duplicated, cross-index, missing, out-of-order or repeated replacements.
   The signal fires inside `replace_by`, before converter metadata and mesh
   assignments complete. Do not capture the replacement's final resources or
   claim its metadata is complete at this signal.
5. **Treat both conversion paths explicitly.** A mapped mesh root is replaced
   and deleted directly inside `generate_scene`, before extension `import_post`;
   descendant importer nodes are converted in the built-in post callback and
   deleted from its queue. The proposed preconversion callback/signal pair must
   retain identity across either path. For the current locked fixture, the
   expected root is a synthetic nonmesh node and there must be zero product-root
   replacement events and exactly 18 descendant replacements. An unexpected
   root shape or event set is a refusal, not permission to generalize the run.
6. **Capture completed native values after generation.** After `generate_scene`
   returns, use only the independently retained live replacement registry for
   identity; do not dereference or repair the stale loader map. Require exact
   event accounting, 18 distinct live replacement nodes, membership under the
   returned scene root, expected classes and unambiguous surface associations.
   Scene traversal checks membership only. Capture complete native metadata,
   mesh arrays, materials and animation poses from these live resources before
   adding any retained source data. Preserve preconversion and postconversion
   captures separately, including native changes introduced by the converter.
7. **Fail independently of callback return codes.** `ERR_CONTINUE` means an
   extension's error can be logged while generation proceeds. A future observer
   needs an external fatal-error latch and complete callback/event counts.
   Any failure forbids emission, metadata attachment, saving and a receiving
   claim, even if a root is returned. The reviewed process must still clean up
   and retain failure evidence without a retry. A successful return value alone
   is not admission.
8. **Seal observation before retained metadata.** Only after raw native capture
   and its hashes are sealed may the separately reviewed later phase attach
   exact retained source bytes and capture labels. Record every metadata and
   scene-save ownership change. Keep originally imported values, converter
   changes, observer-added values, retained authority and derived projections
   distinct. No missing native value may be filled from source data.

These requirements address the identified source lifetime risk. They do not
implement the complete observer, prove installed callback behavior, or settle
build lineage, rendering, output ownership, resource limits or start admission.
Those remain separate gates. An alternative engine-side repair can be evaluated
later if this narrowly permitted observation route cannot satisfy the same
identity and original-metadata requirements.

## 5. Installed-build provenance and remaining gates

Fresh static reads confirm the C220 candidate's exact 138,981,968 bytes,
SHA-256 `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`
and mode 0755. File metadata was stable throughout the read. Its embedded
commit-like value remains `7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3`, distinct
from the inspected upstream revision. Embedded strings are evidence of file
contents, not authenticated build lineage or runtime behavior.
[Static receipt](evidence/STATIC-MAPPING-REVIEW.json)

The next step is the [versioned capture-hook decision](NEXT-TASK.md). Build
lineage, rendering, observer/emitter implementation, full runtime/camera
settings, hard resource enforcement, durable reservation and the two later
native starts remain pending. C243 changes no source or observation schema and
makes no new destination-acceptance claim.
