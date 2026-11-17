# C256 measurement origins

Each geometry and pose record keeps the four C255 origin fields: artifact
basename, whole-file SHA-256, concrete location and bound program identity.
The separate `measurementOrigins` collection carries structured decoding
details. It is not a substitute for the actual artifact bytes.

| Output | Actual origin and operation |
| --- | --- |
| Artifact identity | SHA-256 and length of every supplied GLB byte, including both chunks. |
| Geometry identity | Node `extras.ontokin.element_id`; source association independently checks the complete list against authored module, scene, object, collection key and part tokens. |
| Reused definition identity | Node source mapping checked against authored class keys and exact class declaration spans, separately from occurrence keys. |
| `vertices_m` | Mesh primitive POSITION accessor; little-endian binary32 elements at buffer-view offset plus accessor offset and stride. Declared box size, radius, accessor min/max and sidecar values do not supply measurements. |
| `triangles` | Actual unsigned 16/32-bit index elements grouped in threes, with vertex-index bounds. |
| Requested `time_s` | One of seven frozen sampling requests; it is not relabeled as a stored timestamp. |
| Stored time brackets | Actual input-accessor elements selected by ordered search. Exact keys use one element; intermediate requests record both endpoints and interpolation fraction. |
| Position | Actual translation output elements, with component interpolation between the stored time brackets. Animation replaces the node's default translation. |
| Orientation | Actual XYZW rotation elements. Raw norms first satisfy 1e-6 structural admission. Shortest-path spherical interpolation yields a normalized rotation, reordered to WXYZ. Raw samples and norms remain recorded. |
| Scale | Actual node scale or glTF's default; only exact `[1,1,1]` is supported. Scale animation refuses. |
| Matrix | Row-major `T*R` calculated from measured sampled channels, with that derivation stated. Every node is an actual scene root, so the supported local pose is also world pose. |
| Source association | Actual entry/dependency bytes, fixed historical program identity, GLB source manifest and source-map joins. Key-token, declaration and definition byte spans identify authored origins. |

An accessor origin records accessor and buffer-view indices, component type,
shape, count, embedded-buffer offset, absolute GLB offset, element size,
stride and SHA-256 of used element bytes. Animation origins add channel and
sampler indices, input/output accessor origins, stored indices and times,
raw output samples and interpolation operation. Independent review resolves
these observations back to the same bytes.

The source association checks the eighteen-path inventory, full stable keys,
separate definition keys, program revision, complete two-file source manifest,
node/source-map equality, declaration and definition spans, path steps and
generated-key associations. The remaining semantic metadata is not promoted
into verified facts. Ownership/follow/hinge meaning, semantic dimensions,
actions, matter, accepted history and clean rebuilds remain separate gates.
The C210 semantic sidecar is not a measurement input.

Interpreted GLB rules came from the pinned Khronos source in
[specification provenance](evidence/specification-provenance.json). Consulted
sections include Nodes, GLB-stored Buffer, Buffer Views, Accessors, Animation
Samplers, Linear Interpolation, Spherical Linear Interpolation and Binary glTF
Chunks. The full specification text is not duplicated here.
