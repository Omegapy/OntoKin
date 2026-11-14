# C238/0.1.0: finite combined observation envelope admission

## Scope and result meaning

An observation envelope names one finite set of raw observation files and the
source identities they claim to describe. This C238 step admits one such set
for the original C210 18-part fixture after fresh C221 authority admission.
It implements the bounded next task in [C237 NEXT-TASK](../second-target-c237/NEXT-TASK.md).

C238 checks actual bytes, schema/identity projections, complete declared
inventories, provenance declarations, and dependencies between those members.
It does not execute any C222/C234/C235/C236/C237 numerical or semantic
comparison API. In particular, it does not establish geometric correspondence,
normal accuracy, material accuracy, matrix consistency, pose accuracy, semantic
equality, original-byte retention, actual native capture, or full R07 acceptance.
A declared corner mapping is inspected completely but is not proved by
position matching. All original component contracts, limits, source and evidence
remain unchanged. Passing admission does not import earlier PASS results.

The result is `PASS_CPU_ENVELOPE_ADMISSION` or `FAIL_CLOSED`. Every report
states that all five component validators and the geometric correspondence
proof are `NOT_RUN`. No new numerical tolerance is defined.

## Public API, invocation and authority

The only public admission API is
`check_envelope(package_root, envelope_path)`. Every invocation first executes
unchanged `tools.second_target_c221.check_bindings.check_package(package_root)`.
No caller-supplied authority, cached admission or earlier component report is
accepted. A failure includes its original authority refusal code.

C238 then reloads the pinned C220 authority documents and safely rereads the
original GLB, C214 source-normal payload and semantic sidecar through their
unchanged size/hash/mode pins. This supplies the complete original part,
primitive/material, source-corner/vertex and semantic-shape inventories.
It neither evaluates source nor regenerates those inputs.

```bash
python3 -IB tools/second_target_c238/check_envelope.py \
  --package-root /absolute/extracted-handoff \
  --envelope /absolute/observations/envelope.json
```

Standard output contains one JSON report; there is no output-file option or file
write side effect. Exit 0 means admission passed, exit 1 is a structured refusal,
and exit 2 is invalid command syntax with a JSON refusal. The API raises
`CheckError` carrying its reached report on refusal. Private helpers are test
seams, never admission APIs. Only Python's standard library and unchanged C221
authority code are runtime dependencies.

## Envelope schema

Schema ID: `ontokin.c238.observation-envelope/0.1`.
Exactly these root fields occur:

| Field | Exact meaning |
| --- | --- |
| `schema` | The schema ID above. |
| `capture` | Exactly `kind` and `label`. Kind is `synthetic` or `unattested-native`; label is a nonempty UTF-8 string of at most 256 bytes without NUL. Both are untrusted declarations. |
| `authority` | Exactly `accepted_program_revision` and `glb_sha256`, equal to freshly admitted C221 authority. |
| `parts` | Exactly 18 unique complete part records defined below; list order is immaterial. |
| `members` | Exactly six unique role descriptors from the table below; list order is immaterial. |

Each part record has exactly `gltf_node`, `gltf_mesh`, `element_id`,
`definition_id`, `source_path`, and `native_node_id`. The first five fields
must equal the pinned C220 part map by exact typed canonical JSON. Node and mesh
are nonnegative non-Boolean integers. Native labels are nonempty, NUL-free
strings of at most 4096 UTF-8 bytes and unique in this envelope; they remain
unattested.

Each member descriptor has exactly `role`, `path`, `schema`, `bytes`, and
`sha256`. Paths are distinct ASCII basenames matching
`[A-Za-z0-9][A-Za-z0-9._-]{0,127}`, not `.` or `..`, relative to the
envelope's actual directory. Nested paths, absolute paths, separators and
traversal are not admitted. The envelope filename cannot also be a member path.
Length is a positive non-Boolean integer within the role limit; the digest is
exactly 64 lowercase hexadecimal characters. The inspected byte length, digest
and parsed schema must match the declaration. Copied hash strings alone cannot
satisfy these checks.

| Role | Required schema | Maximum raw bytes |
| --- | --- | ---: |
| `geometry` | `ontokin.c222.geometry-observations/0.1` | 16 MiB |
| `materials` | `ontokin.c234.material-observations/0.1` | 256 KiB |
| `normals` | `ontokin.c235.normal-observations/0.1` | 16 MiB |
| `poses` | `ontokin.c236.pose-observations/0.1` | 1 MiB |
| `semantics` | `ontokin.second-target.c237.observations/0.1` | 4 MiB |
| `corner_map` | `ontokin.c238.declared-corner-map/0.1` | 4 MiB |

The envelope itself is nonempty and at most 64 KiB. The combined envelope and
six member byte lengths must not exceed 42 MiB. No optional report or extra
member is admitted. Reformatting any member requires changing its own exact
binding and every dependency binding that refers to it.

## Shared identity and origin admission

Geometry, materials, normals, poses and corner-map roots retain their exact
declared revision and GLB-digest fields. They must equal the envelope and fresh
authority. Their `declared_origin` values must equal the capture kind.
C237 semantic `programRevision` must equal authority; its producer kind must
be `synthetic` for a synthetic envelope or `declared_destination` for an
unattested-native envelope. Its producer name is preserved as a nonempty
untrusted string. No source or member name establishes capture provenance.

Geometry, material and pose parts must use the exact node/mesh/element/path
projection of each full envelope identity. Pose also declares the exact
definition ID. Geometry/material schemas do not contain definition IDs; the
report explicitly identifies those definitions as authority-derived joins,
not raw fields observed in those members. C237 parts must agree on all five
source fields, translating their existing camel-case names without remapping
values. Its `destinationLabel` must equal the matching envelope native label.
Geometry/material/pose `native_node_id` values must equal that same label.
This equality is a new joint declaration profile, not proof of native mapping
and not a change to standalone C237's allowance for duplicate cosmetic labels.

Every part list has exactly the original 18 unique nodes; extra, absent,
duplicate, swapped, mistyped and stale identities are refused. Normals and
corner-map rows inherit complete part identities only through their checked
node/primitive/source-corner joins. Reports preserve all 18 full mappings and
record which fields were declared versus derived.

## Exact member projection checks

C238 admits the stated schemas' following structural and identity projections;
it does not claim to execute their complete existing validators.

- **Geometry:** exact C222 root/part/surface fields and coordinate declaration;
  all original part/primitive/material associations; finite three-component
  position/normal vectors; equal nonempty position/normal counts; original
  triangle-index counts; non-Boolean in-range indices using every declared
  vertex. This accounts for 18 parts, 7,800 triangles and 23,400 raw corners.
  Original triangle counts/material associations come from pinned GLB/C214
  inventories. No observed position is compared to a source position.
- **Materials:** exact C234 root/part/surface/raw fields; all original
  primitive/material associations; declared native labels equal geometry;
  complete original two-material set; finite unit-interval raw albedo, alpha,
  metallic and roughness values; existing literal color-storage/culling/
  transparency domains. One native resource label cannot claim contradictory
  material indices or raw values. No sRGB conversion, source parameter
  comparison or culling/opacity acceptance is performed.
- **Normals:** exact C235 root/binding/record fields and original normal-frame
  literal; all 23,400 unique five-integer raw corner keys; finite nonzero
  three-component vectors. Each key is present in the complete declared map;
  each copied normal exactly equals the corresponding geometry normal using
  typed canonical JSON, including signed zero. No source-normal comparison,
  normalization, angular measurement or tolerance check is performed.
- **Poses:** exact C236 root/part/sample fields and coordinate declaration;
  all 18 parts and all seven exact reference-time strings, totaling 126
  samples; finite time/translation/quaternion/scale/matrix numbers; nonzero
  quaternions and positive scales. No matrix/TRS consistency, scale profile,
  time error, position or orientation comparison is performed.
- **Semantics:** exact C237 root/part/producer/feature/retained-file/capability
  fields; complete original sidecar-shaped record with exact key sets,
  list lengths/order and primitive JSON types; all 14 unique original feature
  identities; existing C237 feature provenance/capability matrix and original
  unsupported-capability restrictions; exact no_body capability profile.
  The four retained-file kinds must contain canonical standard padded ASCII
  base64, inspected by decoding and re-encoding. Reports retain decoded
  lengths/digests. Original semantic values, feature treatment/reason values,
  decoded retained bytes and embedded source-unit content are not compared.
  Their C237 outcomes remain pending; empty/changed canonical retained bytes
  may pass envelope admission and later fail C237 retention.

Missing/unknown fields are rejected at the named projection levels. Recursive
semantic shape checking is explicit above; opaque primitive contents are still
subject to global JSON bounds. A projection pass never implies the numerical,
semantic-loss, source-unit or retained-byte outcome of its standalone checker.

## Required ancillary corner-map member

The normal schema binds a corner-map digest but does not contain the map.
Therefore an actual sixth member is mandatory. Its schema is
`ontokin.c238.declared-corner-map/0.1`. It has exactly `schema`,
`declared_origin`, `accepted_program_revision`, `glb_sha256`,
`geometry_observation`, `corner_map_fields` and `corner_map`.

The geometry binding contains exactly `bytes` and `sha256`, equal to the
actual inspected geometry member. Field names/order are exactly unchanged
C222's ten fields:

`gltf_node, gltf_primitive, raw_triangle, raw_corner, raw_vertex,
source_mesh, source_primitive, source_triangle, source_corner, source_vertex`.

The map contains exactly 23,400 rows of ten nonnegative, non-Boolean integers,
sorted by the first five fields with no duplicate raw key. Every raw key must
equal an actual geometry index occurrence. Every source corner/vertex must
exist in pinned C214 payload, use that part's admitted mesh and primitive,
and occur exactly once per part. The complete original per-part source-corner
inventory must be covered. Each raw triangle maps to three distinct corners
of one source triangle; its corner order follows C222's predeclared
reverse-once winding with an allowed cyclic rotation. No alternative winding,
missing source corner, extra vertex or many-to-one map is admitted.

The map's canonical JSON-array SHA-256 is computed from these actual rows,
using the unchanged C221 canonical encoding. The normals member's
`geometry_observation.corner_map_sha256` must equal it. Material and normal
geometry byte bindings must equal the actual geometry bytes; the corner-map
geometry binding does too. The full map is a **producer declaration** even when
internally consistent. C238 does not determine which source triangle has the
same positions, detect positional ambiguity or attest the map's correctness.
C222 must later derive and compare geometric correspondence independently.

## Secure reads and JSON bounds

Require POSIX descriptor-relative no-follow directory/file support. Open the
envelope directory through real no-follow ancestors; do not normalize away
traversal. Member names are opened relative to that retained directory handle.
Files must be regular; use no-follow/nonblocking opens so symlinks, directories,
devices and FIFOs are refused without blocking. Open/hold all admitted file
descriptors, reject device/inode aliases between the envelope or any member,
and bound each read to its declared ceiling plus one byte.

For every file compare device, inode, mode, size, mtime and ctime before/after
read and again before successful return. Recheck each directory entry without
following symlinks against the held descriptor's metadata to detect replacement.
The hashed bytes are the parsed bytes; no unchecked reopening supplies content.
This establishes the inspected snapshot only, not a hostile-host attestation
or immutability after return.

Parse strict UTF-8 JSON: reject duplicate object keys, nonfinite numbers,
unpaired surrogates, truncation and malformed input. Limit nesting to 64 levels,
each string to 1 MiB UTF-8 and each document to 1,000,000 JSON values, with the
stricter existing C237 limits of 100,000 values/1 MiB strings for semantics.
Booleans cannot stand in for numeric indices or scalar observations. Huge
integers that cannot be handled as finite numeric observations are refused.
The envelope additionally has at most 10,000 JSON values. Structural limits
are admission constraints, not numerical acceptance tolerances.

## Reports, refusal classes and required controls

Report schema: `ontokin.c238.envelope-admission/0.1`.
Reports retain reached stages, the fresh C221 admission, exact envelope/member
byte bindings, every full source identity and member projection, complete
declared corner map plus canonical digest, cross-file dependency comparisons,
all declared origin/capture labels, decoded retained-file byte bindings,
inventories and explicit limitations. Complete passing reports have no missing
member or omitted identity/map row. Component outcomes remain `NOT_RUN`
and no aggregate component PASS is invented.

Refusals have a stable stage/code/message, distinguishing authority refusal,
missing member, unsafe path/file/alias, size or changed-read failures, malformed
JSON, incompatible schema, byte-binding mismatch, incomplete/duplicate
inventory, stale/swapped identity, inconsistent dependency, and mixed or
contradictory provenance. The current failing stage is explicit; unreached
stages remain `NOT_RUN`. Every result leaves native evidence/mapping,
source/native execution, target authorization and full R07 acceptance false,
with zero source evaluations, exports, imports, target/version starts,
renders and scene writes.

Required controls include independent complete positives for both origins,
reordered outer keyed lists, byte-reserialization with correctly updated
dependencies, and semantically/numerically lossy but structurally admitted
observations demonstrating the limited boundary. Negative controls cover
missing/extra/swapped/corrupt members, wrong lengths/digests/schemas,
stale revisions, every source-identity projection, inconsistent native labels,
mixed origins/capability claims, all corner inventories and dependency hashes,
raw-normal copies, malformed JSON and safe-read limits/aliases/races.
Public API fresh-authority checks must fail after source mutation even following
a successful call. Independent review constructs its own data/oracle and
inspects every admitted map/identity/dependency row.

Run the author cohort and unchanged C221 prerequisite cohort on the exact
source. Standalone existing component results remain separately identified.
Documentation preservation/link checks apply to publication. No aggregate
replay or native operation belongs here. Coordinated publication, actual-main
checks, preserved evidence and one verified saved successor handoff close C238.

