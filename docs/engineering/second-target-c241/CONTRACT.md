# C241/0.1.0: zero-start native capture and preflight boundary

## Selected scope and completion

This increment specifies how one future Godot observation is to be captured and
bound to the existing C238 envelope and C239 CPU comparison. It also records a
fresh read-only inspection of the installed candidate and rendering prerequisites.
The deliverable is this finite contract, exact evidence and independent review.
It implements no observer, envelope emitter, launcher or native admission.

The original C210 after-edit fixture, C220 plan and all C221–C239 contracts remain
authoritative. C241 preserves their exact inputs, numerical limits, failure
classes and absence of native attestation. A completed documentation step does
not pass R07. This step consumes zero native/version, source-evaluation, export,
import, render, scene-save, reopen or aggregate starts.

Full observer and execution preparation is larger than this contract increment.
It remains a separately bounded task. All unimplemented items below are entry
blockers for execution, not permission to complete missing settings during a run.

## 1. Observed candidate and prerequisite disposition

[STATIC-PREFLIGHT.json](evidence/STATIC-PREFLIGHT.json) was produced by the
retained [read-only script](evidence/observe_static.py), without a child process.
It binds the script, original contracts and the inspected file metadata.

| Prerequisite | Current disposition | Meaning and required next evidence |
| --- | --- | --- |
| Installed candidate bytes | MATCH_C220 | `/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64`; 138,981,968 bytes; SHA-256 `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`; mode 0755. Metadata was unchanged during the static reads. This is an inspected file, not executable approval. |
| Build lineage | UNRESOLVED | Embedded commit identifier `7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3` still differs from pinned upstream `35e80b3a8822a9df9be390814b62f44c0a9c69e8`. A later reviewed decision must resolve or explicitly retain the limitation for exact bytes. No silent replacement is permitted. |
| Dynamic libraries and precision | NOT_VERIFIED | ELF headers name direct dependencies. Located files and embedded version strings do not establish actual loaded libraries, runtime precision or API behavior. Runtime information belongs in an admitted phase, before fixture import, and does not permit an extra probe. |
| Rendering route | NOT_ESTABLISHED | This shell has no DISPLAY/WAYLAND_DISPLAY, X11 socket, Xvfb/xvfb-run, inspected Vulkan ICD file or `/dev/dri` entry. OpenGL libraries exist. No connection or render was attempted. A complete useful-image route remains required. |
| Node-map lifetime | UNRESOLVED_SOURCE_RISK | The inspected upstream runtime converter can replace/delete imported mesh nodes while the inspected lookup implementation reads a stored node map. [Source analysis](evidence/MAPPING-LIFETIME-REVIEW.md) records the inference and its limits. A post-generation lookup cannot be assumed safe or authentic. |
| Observer/emitter and frozen settings | NOT_IMPLEMENTED | Exact source, negative controls and independent review are required before any admission decision. This contract supplies no executable command. |
| Reservation and resource enforcement | NOT_IMPLEMENTED | No native reservation exists. Local cgroup limit files were unavailable in this shell. No memory, process or output enforcement has been demonstrated. |

Missing prerequisites cannot be converted to PASS by copying a status string,
using a different binary, adding a display variable, or substituting a headless
numerical result for the full C220 useful-image proof.

## 2. Authority and immutable input set

Use unchanged C221 `check_package(package_root)` to admit all eight original
files and the two pinned C220 authority documents. The accepted program revision
is `sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082`.
The original 185,236-byte GLB has SHA-256
`05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`.
Original relative paths, lengths, modes and hashes come from
[C220 INPUT-BINDINGS](../second-target-c220/evidence/INPUT-BINDINGS.json), not a
replacement manifest. Both source units and the exact C214/C218 evidence remain.

The future wrapper must retain a private copy of those admitted bytes, verify
the copy, bind every actual input path and keep independent before/after hashes.
The native observer must hash the actual bytes it consumes and include those
bindings in its phase receipt. Agreement with a prior manifest without an
actual consumed-input record is insufficient. No source evaluation, fixture
regeneration, new export, tolerance change or prior native replay is scheduled.

Source authority, native raw observations, copied metadata, derived mappings and
checker reports are distinct artifacts. They must never overwrite one another.

## 3. Fixed prospective loader boundary

Use `GLTFDocument` and a new `GLTFState` with the original binary GLB through
`append_from_file(exact_private_glb_path, state, 64, exact_private_input_directory)`.
The selected flag is only upstream `GLTF_IMPORT_FORCE_DISABLE_MESH_COMPRESSION`;
the bits for tangent generation, named skin binds and discarding meshes/materials
remain clear. Require successful error return before scene generation.

Set `state.create_animations = true`, `state.import_as_skeleton_bones = false`,
`state.use_named_skin_binds = false`, `state.bake_fps = 60.0`, and
`state.handle_binary_image_mode = 3` (embedded uncompressed mode). This fixture
must still have no external image/buffer dependency. Call
`generate_scene(state, 60.0, false, false)`: no trimming and no removal of
immutable tracks. These choices are prospective source/API settings; they have
not been observed on the installed candidate. [Primary sources](evidence/PRIMARY-SOURCES.json)
bind the inspected API documentation and exact upstream files.

No editor import, source import plugin, custom GLTFDocumentExtension, geometry
repair, LOD generation, shadow-mesh generation, tangent generation, normal
replacement, axis conversion or scale adjustment belongs to this route. Any
required correction needs a separately reviewed versioned change before a start.
Do not remove built-in extensions merely to work around the map-lifetime risk.

The future frozen project must enumerate its settings, source files, autoloads,
plugins, loaded-extension expectations and renderer choice. The supported glTF
extension-name list is useful metadata, but is not an inventory of all extension
objects or proof that no custom callback ran. Bind isolation and extension
assumptions through exact project/observer/build evidence. Record raw mesh array
formats, indices, surface flags and animation tracks; selected flag values alone
do not prove compression or unwanted transformations were absent.

## 4. Native identity and capture order

Before writing observer metadata, the observer must establish a live one-to-one
association for the exact 18 source nodes through the loader's glTF node-index
map. `GLTFState.get_scene_node(index)` and the inverse
`get_node_index(native_node)` are the intended API boundary. Null, invalid,
deleted, duplicated, mismatched or ambiguous nodes stop capture. A node name,
scene traversal order, matching geometry or source label is not a fallback for
that association. The unresolved converter/lifetime prerequisite must be
settled before an observer can be approved; this contract does not prescribe
calling a potentially stale pointer and then testing it.

Once a reviewed safe mapping route exists, preserve a complete initial mapping
record containing the glTF index/mesh, native class, instance identity, root-relative
node path, source element/definition/path and exact source span/occurrence joins.
Declare one stable capture label per mapped node. Geometry, materials and poses
use it as `native_node_id`; semantics uses it as `destinationLabel`. Normals and
the corner map retain their unchanged node/primitive/corner keys, through which
C238 joins them to the full identities. Do not add label fields to those schemas.
Process-local instance IDs remain additional evidence, not identities expected
to survive reopening. Native names remain descriptive.

Capture in this order:

1. Record the original native tree, parent/owner relations, native classes,
   metadata keys, typed metadata values, script attachments, resources and source
   map. Preserve unsupported metadata types as an explicit capture refusal;
   do not silently omit or stringify them into apparent equality.
2. Read the original native mesh positions, normals, indices and material
   parameters. For this finite fixture each part has one planned primitive and
   one corresponding surface. A missing/extra surface or unproved primitive
   association stops the projection; no post hoc surface guess is permitted.
3. Evaluate the imported native animation at all seven declared times and record
   all 126 raw world poses. Bind the selected animation and complete track
   inventory. The prospective sampling call is `seek(time, true, true)` with
   automatic advancement disabled and the actual time recorded. Missing tracks,
   unsupported update behavior or unexpected executable tracks stop capture.
   No source pose values can fill a missing native observation.
4. Seal the raw capture and its hashes. Only then attach exact retained source
   bytes, explicit source bindings and observer provenance. Record every
   metadata and Godot scene-save ownership change in a separate mutation ledger.
   These operations must not reparent or alter product transforms/resources.
5. When separately admitted, save and capture useful images under the fully
   frozen execution settings. Before/after raw observations must show that
   metadata/ownership preparation did not change the product values being
   claimed. An observer-added value is never reclassified as originally imported.

The full source sidecar may be retained as copied descriptive data. It does not
become native following, hinge physics, action execution or reconstructed source.
Godot scene-save `owner` is distinct from OntoKin semantic ownership.

## 5. Raw-to-envelope projection and provenance

The observer emits raw native data. A separately reviewed CPU emitter creates
the exact C238 schemas and preserves complete raw inputs beside them. Numeric
values are serialized with enough precision to round-trip their represented
value, without normalization, tolerance repair or new binary32 rounding. Matrix
layout conversion to C236 row-major form and quaternion reordering to `wxyz`
are explicit representation changes, not coordinate transformations.

The emitter reads retained sidecar/program bytes with the unchanged strict
Python JSON semantics required by C237. Preserve integer/float/Boolean types,
list order and exact raw retention separately. Do not assume a native JSON
round-trip preserves those requirements. For a reopened scene, retained-file
bytes must come from that scene's captured retention fields; copying originals
again would conceal a persistence failure.

Use the existing C237 provenance vocabulary without adding a capability:

| Feature group | Prospective provenance | Required interpretation |
| --- | --- | --- |
| Source closure | `retained_external` | Exact original source is available; reconstruction is unproved. |
| Stable identities | `independently_derived` | Derived from the proved loader mapping and original source joins. |
| Dimensions, units and frames | `retained_external` | Source declarations remain available; numerical observations are checked separately. |
| Ownership, following, hinges and physical declarations | `observer_copied` or `retained_external`, according to actual storage | Descriptive source facts; no live destination constraint or physics claim. |
| Materials and primitive geometry | `imported_native` only when the original raw capture establishes it | Actual parameters/arrays, independently checked. |
| Numeric precision | `independently_derived` | CPU measurements from preserved raw arrays, retaining every failure. |
| World motion | `imported_native` only for actual evaluated imported tracks | Baked playback, not OntoKin action execution. |
| Action execution, live physics and source reconstruction | `unsupported` | All corresponding capability flags remain false. |

These are predeclared interpretations. The emitter must record what actually
happened; failure does not permit switching a missing native result to copied
source data. C237's exact allowed feature/capability matrix still decides
structural admission. Its no-body counts, zero mass and motion-authority text
remain unchanged.

The envelope has exactly `schema`, `capture`, `authority`, `parts` and `members`.
Use `capture.kind = "unattested-native"`, even after a genuine native process:
this existing CPU schema deliberately makes no native-attestation claim.
The label and accompanying external phase receipt bind the claimed capture.
All 18 complete identities and unique native labels agree across the members.
The geometry, material, normal, pose and corner-map `declared_origin` fields
are `unattested-native`. C237 instead uses `producer.kind =
"declared_destination"` and preserves its nonempty producer name. Session,
build, process and capture-order provenance remains in a separate sidecar;
no extra root field or member is added to the C238 envelope.

| Role and basename | Existing schema | Raw ceiling |
| --- | --- | ---: |
| `geometry`, `geometry.json` | `ontokin.c222.geometry-observations/0.1` | 16 MiB |
| `materials`, `materials.json` | `ontokin.c234.material-observations/0.1` | 256 KiB |
| `normals`, `normals.json` | `ontokin.c235.normal-observations/0.1` | 16 MiB |
| `poses`, `poses.json` | `ontokin.c236.pose-observations/0.1` | 1 MiB |
| `semantics`, `semantics.json` | `ontokin.second-target.c237.observations/0.1` | 4 MiB |
| `corner_map`, `corner-map.json` | `ontokin.c238.declared-corner-map/0.1` | 4 MiB |

Write those six distinct regular basenames beside `envelope.json`. The envelope
is at most 64 KiB; the seven files total at most 42 MiB. Every member descriptor
binds the actual schema, bytes and SHA-256. Geometry-dependent bindings must
refer to the actual final geometry bytes. Normals copy the actual raw geometry
normal values, including signed zero; they do not copy source normals.

The declared map contains all 23,400 rows in C238's exact ten-field order and
canonical raw-key order. Its producer derivation must use source-node identity,
exact local positions and the single predeclared winding reversal. Normals
cannot select a correspondence. The producer implementation/oracle must remain
separate from the C222 result against which C239 compares it. A digest alone
does not replace full rows. If a complete valid projection cannot be produced,
preserve the incomplete raw output and report the blocker rather than inventing
members, filling missing values, or weakening a schema.

Run unchanged C239 `check_combined(package_root, envelope_path)` through its
public API only after all raw inputs and the actual source revision are retained.
Its fresh C238/C221 admission, private byte copy, complete component reports and
declared-versus-derived map comparison remain unchanged. Full reports and raw
inputs are durable evidence. CPU pass, measured loss, refusal, native provenance,
useful-image review and persistence remain separate conclusions.

## 6. Later execution admission and limits

C241 creates no reservation. C220's later ceiling stays at two Godot process
starts total: import/observe/save/capture, then separately admitted
reopen/observe/capture. A failed launch or a version probe consumes a start.
Runtime metadata must be recorded inside an admitted phase before fixture
processing. No automatic retry, extra capability probe or headless substitute
is permitted by this contract.

Each future phase retains 120 s wall time, 8 GiB process memory and 256 MiB
total output; combined ceilings are 240 s and 512 MiB. The future wrapper must
demonstrate enforcement for the complete child process group, with a monotonic
deadline, bounded diagnostic capture and output counting that includes scene,
images, raw capture, observation files, logs and unexpected files. A per-file
limit alone does not enforce the total output budget. Sampling memory alone
does not demonstrate an 8 GiB hard bound. Unavailable enforcement blocks launch.

Before any start, an independently reviewed, durable reservation must name exact
observer/emitter/wrapper/checker source, candidate and dependency identities,
input hashes, command argument vector, filtered environment, working directory,
private user/cache directories, extension/settings expectations, complete output
inventory and all limits. No unresolved placeholder is an executable admission.
The wrapper records reservation transition, actual start/PID/group identity,
exit status, output hashes and cleanup. Interrupted or unknown starts remain
consumed/unknown until reconciled; they are not silently retried.

On timeout, identity mismatch, missing capability, incomplete capture, output
overrun or cancellation, stop progression and terminate the complete owned
process group, escalate as reviewed, reap children and verify no member remains.
Unproved cleanup is a blocker and must remain visible. Preserve reached evidence
and failed attempts. No network access or dependency installation occurs inside
the run.

Rendering still requires the exact C220 two 1280×960 images per phase: whole
assembly overview and the sphere/arm/post junction detail. Numeric camera
transforms/projection, lighting, background, animation time, renderer/driver,
sampling and capture timing must be frozen and reviewed before admission.
They are deliberately not invented in this documentation step. Missing values
block execution. The second phase requires independent review of the first
phase's complete outcome and exact saved scene; it reopens that file without
GLB reimport and inspects the same retained bytes, mapping, raw values and poses.

## 7. Review, checks and stopping point

For C241, independent review checks source/API citations, candidate identity,
zero-start evidence, complete C238 projections, provenance distinctions,
preserved C220 limits and explicit unmet prerequisites. Run the repository's
documentation preservation/link check on the actual publication candidate and
resulting main. No product runtime code changed; re-running the broad aggregate
or the C239 scientific cohort is not justified by this documentation increment.

Root records exact published and unpublished revisions, source/evidence hashes,
review outcomes and remaining blockers in the handoff. Once the contract is
reviewed and the saved handoff is verified, stop. The next separate step resolves
one bounded observer mapping-lifetime/source-design question with zero native
starts, then predeclares and checks an emitter/observer implementation only when
that route is concrete. Build lineage, rendering, enforced reservations, images,
persistence and full R07 acceptance remain later gates.
