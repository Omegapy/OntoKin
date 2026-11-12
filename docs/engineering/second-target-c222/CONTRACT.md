# C222/0.1.0: finite CPU observation and corner correspondence

## Scope and authority

This component implements the CPU observation schema and geometry-correspondence
step in the [C221 next task](../second-target-c221/NEXT-TASK.md), under the
[C220 plan](../second-target-c220/PLAN.md). It accepts only the same 18-part
C210 after-edit fixture. It starts no native process, evaluates no `.ok` source,
and performs no export, import, render or native scene write.

Every public invocation first calls the unchanged
[C221 authority checker](../second-target-c221/CONTRACT.md). A supplied pass
report cannot replace this admission. The checker then rereads the locked GLB
and C214 payload through the same exact byte-size/hash/mode checks and parses
those inspected bytes. The C221 implementation and C220 authority documents
remain unchanged. Executable provenance comes from the externally recorded
reviewed source revision; this program is not a hostile-host attestation.

The checker decodes the source POSITION and index accessors using C221's finite
GLB reader and Python's little-endian binary32/unsigned-16 decoding. It checks
every unique C214 corner key, source vertex, winding triple and exact position
bytes against that GLB. All 3,024 source corner records must be accounted for.
Their instances supply 7,800 triangles and 23,400 corners over the 18 parts.
C214 normal values stay retained authority but are not numerically compared in
this step.

## Public invocation

```bash
python3 -IB tools/second_target_c222/check_observations.py \
  --package-root /absolute/extracted-handoff \
  --observations /absolute/observations.json
```

The command emits one JSON report to standard output and creates no output
file. Exit `0` means `PASS_CPU_CORRESPONDENCE`; exit `1` means `FAIL_CLOSED`
with a stage, reason code and message. Argument errors use argparse exit `2`.
The only public admission API is `check_observations(package_root,
observation_path)`. The internal `_load_authority`, `_source_geometry`,
`validate_observations` and `_match_surface` functions are test seams, not
alternative admission or provenance APIs.

Observation files are bounded to 16 MiB. Their root, ancestor directories and
file must be real paths; symlinks, traversal, nonregular files and changed
descriptor metadata are refused. Nonblocking open prevents a substituted FIFO
from hanging. The exact bytes read are hashed and parsed once. Strict UTF-8 JSON
parsing refuses duplicate keys, non-finite values and truncation. Python's JSON
numeric decoding is used; no subsequent binary32 rounding or position tolerance
is applied. Observation file permissions do not establish authority.

## Observation schema

Schema ID: `ontokin.c222.geometry-observations/0.1`. Every object has exactly the
fields listed below. Extra or missing fields fail. Numeric indices must be
nonnegative integers; booleans cannot substitute for them. Vectors have exactly
three finite numeric components.

| Object | Exact fields and meaning |
| --- | --- |
| Root | `schema`; `declared_origin`; `accepted_program_revision`; `glb_sha256`; `coordinate_system`; `parts`. |
| Origin | `declared_origin` is `synthetic` or `unattested-native`. Both are untrusted producer labels. Neither can enable native acceptance. |
| Source | `accepted_program_revision` must equal the C221 constant. `glb_sha256` is the bare 64-character hexadecimal digest of the fixed GLB. These claims are checked against separately admitted authority. |
| Coordinates | Exactly `position_unit: "m"`, `basis: "gltf-rh-y-up-identity"`, and `winding: "godot-clockwise-reverse-once"`. These are declarations to check against positions, not observations of Godot conventions. |
| Part | `gltf_node`, `gltf_mesh`, `element_id`, `source_path`, `native_node_id`, `display_name`, `surfaces`. All 18 node identities must occur exactly once and agree with the locked map's mesh, element ID and path. |
| Native labels | `native_node_id` must be nonempty, bounded text and unique across parts. `display_name` is bounded text, may be empty or duplicated, and has no identity role. These strings do not attest a loader's node-index mapping. |
| Surface | `gltf_primitive`, `material_index`, `positions`, `normals`, `indices`. Every planned primitive occurs exactly once; material index must agree with the fixed primitive. Material parameter fidelity is not checked. |
| Vertex arrays | `positions` and `normals` are equal-length arrays of three-component finite vectors. Every vertex must be referenced. Split or reindexed vertices are permitted within the finite corner-count ceiling. Normal length, orientation and fidelity are not acceptance conditions here. |
| Indices | A complete raw native triangle-index array with exactly the planned corner count, all indices in range. The array's raw order is preserved in the result; no missing, extra or truncated triangle is accepted. |

Positions are object-local. There are no transforms, poses, materials, semantic
treatments or persistence claims hidden in this geometry-only schema. Those
remain later C220 preparation. A later richer observation schema must version
its changed fields and responsibilities separately.

## Exact correspondence

For each already mapped glTF node and primitive:

1. Build the source triangle table from admitted GLB positions and indices,
   joined to C214 corner keys. Canonicalize signed zero only.
2. Read each raw observed triangle `(a, b, c)` and use `(a, c, b)` for comparison.
   This is C220's predeclared reversal, applied exactly once. The checker never
   chooses a winding convention after observing a desired result.
3. Match the three positions to the source's ordered position triple, permitting
   only cyclic corner order. Source vertex indices are outputs of this match,
   not matching criteria. No nearest-neighbour search, normal, display name,
   float32 conversion or position tolerance selects a match.
4. Require one source triangle and one corner rotation. Duplicate positional
   source candidates or degenerate ambiguous corner rotations fail. Matching a
   source triangle twice fails; every source triangle must be matched once.
5. Retain the raw triangle/corner/vertex reference together with the exact
   source mesh/primitive/triangle/corner/vertex. All 23,400 corners are required.

Changing finite normal values cannot change any selected corner correspondence.
Identical geometry in distinct instances is separated by the admitted part
identity, while duplicate geometry within one part/primitive remains ambiguous.
Consistently forged self-reported labels or arrays cannot be distinguished from
an authentic native capture by this CPU check. A future observer must establish
the actual GLTFState association, consumed inputs and capture provenance under
its own reviewed protocol.

## Report and limits

Report ID: `ontokin.c222.corner-correspondence/0.1`.

- `admission` contains the freshly executed C221 byte/source-binding result.
- `structure` reports its separate observation-structure pass and complete
  part/surface/vertex/triangle/corner inventory.
- `correspondence` reports the exact matching result, a deterministic complete
  `corner_map`, the field-order declaration and the map's canonical JSON digest.
- `observation_bytes` and `observation_sha256` identify the exact read file.
- `untrusted_observation_labels` retain the supplied native ID and display
  strings without promoting them to provenance evidence.
- `limits` keeps every native/source/export/import/render/scene-write count at
  zero and every native evidence, mapping-attestation, normal/material/pose
  comparison and target-execution authorization flag false.

Each corner-map row follows `corner_map_fields`: glTF node, glTF primitive, raw
triangle, raw corner, raw vertex, source mesh, source primitive, source triangle,
source corner, source vertex. The four source fields from mesh through corner
are the C214 key. The report is correspondence evidence only, not a native
receiving pass or a normal-fidelity result.

## Verification boundary

Run the package-dependent author controls explicitly:

```bash
python3 -IB tools/second_target_c222/tests/run_controls.py \
  --package-root /absolute/extracted-handoff
```

They remain outside broad product-test discovery because this finite checker
requires externally retained historical inputs. Independent controls should
decode their own source fixture and compare the complete corner map. Internal
source-ambiguity controls do not authorize modified public input artifacts.

The full product regression, source/CLI/export workflows, all target starts,
the Godot observer, material/pose and cross-target comparisons, process budget,
settings, rendering capability, build lineage, save/reopen and semantic/loss
reports remain outside C222. C211's original strict normal failure and every
historical failed/unrun gate remain unchanged. The owner's R01–R08 follow-up
tracker is carried by the root integrator; completing this CPU step does not
complete those maintenance, usability, proof or benefit tasks.
