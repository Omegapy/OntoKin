# C256 finite GLB reader boundary

C256 reads the existing C210 before/after GLB files. It measures local triangle
geometry and seven sampled world transforms. It does not create a complete
C255 observation, a semantic graph, a revision transaction or a trial score.
The C253 corpus and C255 formulas and tolerances remain unchanged.

## Three distinct results

`measure_glb(raw)` traverses supplied bytes and reports measurements with
untrusted artifact identity labels. It does not authorize a source association.
`associate_glb(raw, source_files)` additionally checks the exact frozen source
closure and independently joins its authored keys and declaration spans to the
GLB identities. It still does not certify the supplied artifact as a historical
proof. `read_bound_endpoint(repo, endpoint)` admits only the exact original
`before` or `after` GLB and source bytes, then performs the same traversal and
source joins. A raw measurement can change when valid artifact bytes change;
the historical entry point must refuse the same changed bytes.

## Finite supported profile

The input is GLB 2 with one JSON chunk and one embedded binary buffer, one
scene, eighteen object nodes that are all scene roots, one triangle primitive
per mesh, and one animation with translation and rotation channels for each
node. Mesh reuse is allowed. POSITION is binary32 VEC3; triangle indices are
unsigned 16- or 32-bit scalars. Animation times and outputs are binary32,
tightly packed, with LINEAR interpolation. Sparse accessors, external buffers,
extensions, hierarchy, skinning, morph targets, matrix nodes, animated scale,
nonunit scale and other interpolation modes are outside this boundary and
refuse explicitly. This component is not a general glTF validator.

Raw GLBs are limited to 4 MiB, including at most 2 MiB of JSON. Arrays contain
at most 256 accessors/views, eighteen nodes, eighteen meshes and 36 channels.
Each vertex accessor has at most 2,048 elements, each index accessor 12,288,
and each animation/time accessor 4,096. A cumulative 200,000 decoded scalar
components bounds alias amplification, including repeated reads in distinct
roles. The exact endpoint route checks file size before a bounded read of at
most the pinned size plus one byte. Source association checks the exact
1,708-byte entry and 1,911-byte dependency lengths before hashing.

The reader follows the [consulted Khronos glTF 2 specification](https://github.com/KhronosGroup/glTF/blob/70129abe2ba5c8f0b50da8328874780b85a621ae/specification/2.0/Specification.adoc)
for little-endian accessor interpretation, XYZW stored rotations, animation
replacement of node properties, strictly increasing time and shortest-path
spherical interpolation. Stored rotations must first meet the unchanged
C255 delivery structural norm residual of 1e-6. Interpolation normalizes only
those admitted rotations; invalid rotations are never repaired. Raw endpoint
values and norms remain in provenance. The output matrix is calculated from
the traversed TRS values and identified as such, not claimed to exist as a
stored matrix. No pose or geometry answer comes from sidecar dimensions,
declared primitive parameters, C255 expected-state functions or source formulas.

## Identity and semantic limits

The association entry point admits only the two exact entry sources and exact
`hinges.ok`. Its finite source-key recipe reads the authored module, scene,
object, part, class and keyed-collection tokens and their byte spans. Complete
occurrence keys remain separate from reused definition keys. Source manifest,
program revision, node labels, source mappings and occurrence inventory must
agree. A display name alone is insufficient. The raw entry point labels these
same artifact metadata fields as untrusted.

The source join establishes the identity association for this fixed family.
It does not independently qualify ownership, follow constraints, hinges,
actions, physical declarations or semantic parameter values. Those fields are
not supplied to C255. Native source decoding, accepted revision authority,
clean rebuild evidence, invalid-edit atomicity, model settings and statistical
comparison remain unqualified. The seven times do not prove all-time motion.

## Review and stopping conditions

Independent controls must check byte traversal and full identity joins, reject
malformed structures and unsupported features, and show changed geometry,
transforms or valid animation times changing actual measurements. Exact-bound
controls must reject changed proof bytes. The unchanged C255 geometry/pose
predicates may be called by tests as independent consumers; the reader must
not import them. Preserve all failed attempts. After reviewed integration,
create and verify one successor handoff, confirm its save, and stop.
