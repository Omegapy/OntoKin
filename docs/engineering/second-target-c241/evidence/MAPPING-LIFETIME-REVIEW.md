# Pinned upstream node-map lifetime review

## Finding and confidence

The intended native source identity comes from GLTFState's glTF-index/native-node
association. The inspected official upstream source contains a mesh conversion
path that makes its lifetime a concrete prerequisite for observer design.
This is a source-derived risk, not an executed reproduction and not a claim that
the installed binary has a demonstrated defect. Its build lineage still differs
from this upstream commit. No native process was started for the review.

All four source files were fetched from `godotengine/godot` at commit
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`. [PRIMARY-SOURCES.json](PRIMARY-SOURCES.json)
records canonical URLs, Git blob identities and SHA-256 bindings; the original
source texts preserve their license notices.

## Evidence chain

1. `modules/gltf/register_types.cpp` registers
   `GLTFDocumentExtensionConvertImporterMesh` when the engine is not in editor
   mode. This is a built-in extension, distinct from an observer-supplied custom
   extension.
2. `modules/gltf/gltf_document.cpp` builds the scene and its `scene_nodes` map,
   then runs each selected extension's `import_post` before returning the scene.
3. The converter's `import_post` walks imported mesh nodes. It replaces each
   `ImporterMeshInstance3D` with a new `MeshInstance3D`, copies metadata and
   transforms, then deletes the old node. The inspected converter does not write
   the `GLTFState.scene_nodes` mapping.
4. `modules/gltf/gltf_state.cpp` implements `get_scene_node` as a lookup in that
   map and `get_node_index` as a scan of its stored pointers.

Taken together, these definitions make a post-conversion lookup unsafe to assume
valid without an identified preservation/update mechanism. The limited review
does not prove the absence of every other engine-side mechanism or establish
what the mismatched installed build executes. It is sufficient to withhold a
claim that the documented lookup alone completes native provenance.

## Required disposition

Keep the mapping route unresolved in C241. Before implementing an observer,
review the complete applicable source path and choose a safe, explicit route
that preserves the original association and raw metadata. No caller may merely
dereference a possibly stale node, switch to matching names, fabricate metadata,
disable a built-in conversion, add a custom extension or use editor import to
claim the existing C220 contract was met. Any necessary contract change must be
versioned and independently reviewed before execution.

The follow-up remains zero-start. It may produce a concrete source design and
inert controls, or a precise blocker. A native/version probe would consume one
of C220's two later starts and is outside this review.
