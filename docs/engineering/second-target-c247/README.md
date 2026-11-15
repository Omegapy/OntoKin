# C247: held final native mesh-array snapshot

**Held source only. GDScript parsing and native execution have not run.**
This component reads positions, indices and normals from the 18 final mapped
parts after the [C246 observer](../second-target-c246/README.md) completes its
replacement chain. It preserves native surface encoding and the auxiliary
tangent channel required by the inspected engine. It grants no execution
admission, native acceptance, full raw-capture completion or R07 pass.

The [source](mesh_arrays.gd), [CPU model](inert_model.py),
[controls](test_inert_model.py) and [binding checker](verify_bindings.py) are
isolated here. Existing observer, registry, product, authority and tolerances are
unchanged. The model runs on fabricated nodes and arrays; it is neither a
GDScript interpreter nor an emulation of Godot precision, lifetime or diagnostics.
[Results and limitations](RESULTS.md) distinguish those evidence levels.

## Identity and capture boundary

A future independently admitted caller must notify C246 of actual synchronous
generation return, then call `capture_after_generation_return(state, root)`
once. C247 itself calls `Registry.close_state(state)`. A caller-supplied receipt
cannot substitute for that exact-state registry result. The receipt must be
complete, in `CHAIN_COMPLETE_RAW_PENDING`, and free of fatal faults.

C247 rechecks root identity, final live membership and every observed
old-to-new identity edge without reading the stale loader map. Each node's
current `ArrayMesh` must match the resource identity in C246's final native
facts. Multiple nodes may share one resource. Names, traversal order, matching
shape and expected source positions are never identity fallbacks.

For the exact original fixture, each source mesh has one indexed triangle
primitive with position and normal attributes. The pinned parser creates
importer surfaces in primitive order, and the converter builds ArrayMesh
surfaces in that same order. Combined with the observed node replacement chain
and the required single native surface, this supplies the finite association
`source primitive 0 -> native surface 0`. It is a source-supported association
for this held implementation, conditional on the still-unresolved installed
build and frozen loader settings. The complete primary-source and authority
hashes, original fixture check and claim locations are in [BINDINGS.json](BINDINGS.json).
No multi-surface correspondence is inferred.

Each part keeps its source node/mesh/primitive, native node/resource identity,
native surface index, exact format and primitive enum, descriptor counts,
raw surface field types, raw vertex/index buffers, slot types/lengths, and
detached native API position/normal/index arrays. The native auxiliary tangent
array is retained separately. Missing or unsupported values are refused; no
source values fill gaps. No coordinates, normals or winding are changed.

One row is added before each part's reads. Refusal retains previous complete
rows and the current partial observations, including bounded supported arrays
and their actual lengths before cross-slot validation. Failed reads are not
replaced with empty successful observations. The receipt remains non-accepting.

## Native storage facts that affect this reader

The inspected [RenderingServer source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/servers/rendering/rendering_server.cpp)
adds tangent storage whenever normals are present. This is distinct from the
GLTF tangent-generation flag, which remains disabled under C241. C247 does not
generate tangents; it retains the API's auxiliary array and format bit.

The same source reconstructs normals and tangents from native octahedral
encoding even when `ARRAY_FLAG_COMPRESS_ATTRIBUTES` is clear. Here *native API
readback* means the values returned by those accessors. It does not mean exact
original source values or proof of a fidelity limit. Raw encoding buffers are
retained beside the decoded API arrays. No numerical comparison is rerun.

`ArrayMesh.surface_get_lods` exists in C++ but is not a public script binding at
the pinned revision. The component instead uses the bound
`RenderingServer.mesh_get_surface` dictionary to retain raw encoding and refuse
unexpected LOD, skin, blend-shape or attribute fields. It also refuses extra
surfaces, shadow meshes, unsupported primitives/channels/format versions,
compression/dynamic/2D flags, wrong packed types, inconsistent counts,
nonfinite values and out-of-range indices. The accepted format is exactly
position, normal, auxiliary tangent, index and current format-version bits.

A second full read of every captured surface must equal the first, followed by
another live membership and registry-fault check. This detects lasting changes
in same-sized buffers or arrays as well as descriptors. It cannot prove atomic
capture against transient concurrent changes. Future reviewed isolation is
still required.

## Bounds and deferred work

The reader caps traversal at 64 nodes, vertices at 100,000 per part, indices at
300,000 per part, and each retained raw buffer at 16,000,000 bytes. It inspects at
most the 13 defined slots, with tangent length capped at four times the vertex
cap. Counts are checked before element loops and duplication when the API
provides them. These are finite reader bounds, not a process-memory or time
limit: native APIs can allocate before returning, 18 parts can share resources,
and receipts contain detached copies. Over-limit values retain their type,
actual length, cap and explicit omission marker instead of an unbounded copy.
No hard memory/process/output enforcement
has been implemented or demonstrated.

The component returns a detached native Dictionary, not a serialized C238
member or a saved file. Later exact serialization and raw hashes must preserve
represented values. Materials, evaluated poses, raw-capture sealing, complete
diagnostics, build lineage, useful images, scene persistence, launcher,
reservation and hard limits remain separate gates. C246 fact records precede
C247's cleanup; the trusted chain's cleanup ledger remains included. The
original strict Blender-normal failure and all prior held source remain intact.

## Recheck without starting Godot

From the restored repository, with `PACKAGE` denoting the extracted handoff:

```sh
python3 -B docs/engineering/second-target-c247/test_inert_model.py
python3 -B docs/engineering/second-target-c247/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c247-bindings.json
```

The checker verifies original bytes, APIs, fixture associations and selected
lexical boundaries. It does not parse GDScript or establish runtime behavior.
There is no runnable Godot project, loader, automatic registration or launch
command here. After independent review and confirmed saved handoff, stop.
[The next component](NEXT-TASK.md) needs a separate bounded scope.
