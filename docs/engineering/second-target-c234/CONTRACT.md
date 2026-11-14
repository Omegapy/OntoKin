# C234/0.1.0: finite CPU material observations and comparison

## Purpose and admission

This R07 component checks material parameters for the unchanged C210 after-edit
fixture: 18 parts and two source materials. It implements one remaining CPU
step of the [C220 plan](../second-target-c220/PLAN.md). It changes neither
[C221 authority admission](../second-target-c221/CONTRACT.md) nor
[C222 geometry observations](../second-target-c222/CONTRACT.md).

The public API is `check_materials(package_root, geometry_observation_path,
material_observation_path)`. Every call first executes C221 admission, then
calls C222's public checker, which performs its own fresh C221 admission and
complete 23,400-corner correspondence. No caller-supplied pass report can
replace either prerequisite. The geometry file is safely reread and must have
the exact byte length and SHA-256 returned by that C222 invocation. Its parsed
part/node/mesh/primitive/material associations are used only after this equality
check. The material file must explicitly bind that same byte length and hash.

The checker rereads the GLB against the original pinned size, hash and mode,
then independently decodes its material parameters and primitive assignments.
It uses C221's finite GLB container decoder, not an exporter, receiver, runtime
material helper or previous numerical report. The two source PBR records supply
linear base-color RGBA, metallic and roughness. The admitted fixture omits
`doubleSided` and `alphaMode`; their glTF meanings are false and `OPAQUE`.
The checker records these resolved defaults explicitly. The finite decoder
rejects unsupported material fields or a nonopaque source mode; it is not a
general glTF material validator or a new supported destination profile.

Inputs and reviewed executable provenance remain separate. External evidence
must identify the exact checked source revision and hashes. Neither a producer
label nor this program can attest a native capture or a hostile host.

## Invocation

```bash
python3 -IB tools/second_target_c234/check_materials.py \
  --package-root /absolute/extracted-handoff \
  --geometry-observations /absolute/geometry.json \
  --material-observations /absolute/materials.json
```

The command writes one JSON report to standard output and creates no output
file. Exit 0 means `PASS_CPU_MATERIALS`. Exit 1 means `FAIL_CLOSED`, with a stage,
reason and the prerequisite/comparison outcomes actually reached. Argument
errors use argparse exit 2. The API raises `CheckError` on failure; its `report`
attribute contains the same fail-closed report. Private underscore-prefixed
functions are internal test seams and cannot admit replacement authority.

Material observations are nonempty regular files bounded to 256 KiB. Reads
use no-follow directory handles, nonblocking file opening and descriptor
metadata checks before and after the bounded read. Symlink ancestors/files,
traversal, FIFOs and changed reads fail. The exact read bytes are hashed and
strictly decoded as UTF-8 JSON. Duplicate keys, non-finite values, truncation,
extra fields and missing fields fail. Geometry retains C222's separate 16 MiB
limit and safe-read rules. These are inspected-byte checks, not a guarantee
against later modification by another process.

## Material observation schema

Schema ID: `ontokin.c234.material-observations/0.1`. This is a separate document;
the frozen C222 schema has no new fields.

| Object | Exact fields and meaning |
| --- | --- |
| Root | `schema`, `declared_origin`, `accepted_program_revision`, `glb_sha256`, `geometry_observation`, `parts`. |
| Origin | `synthetic` or `unattested-native`. Both remain untrusted labels and cannot enable native acceptance. |
| Source | The accepted revision and GLB hash must match the freshly admitted C221 authority. |
| Geometry binding | Exactly `sha256` and `bytes`, equal to the exact geometry file freshly checked by C222. `bytes` is an integer, not a boolean or floating-point number. |
| Part | `gltf_node`, `gltf_mesh`, `element_id`, `source_path`, `native_node_id`, `surfaces`. All 18 parts occur once. Source identity, mesh and node must agree with the frozen authority; the node label must equal the bound geometry label. |
| Surface | `gltf_primitive`, `material_index`, `native_material_id`, `raw`. Every admitted primitive occurs once, and its material index agrees with both the GLB and bound geometry. |
| Raw material | `albedo_storage`, `albedo_rgb`, `alpha`, `metallic`, `roughness`, `cull_mode`, `transparency_mode`. |
| Raw color | `albedo_storage` must be `srgb-rgb-linear-alpha`; RGB is exactly three finite numbers in [0, 1]. Alpha is a separate finite number in [0, 1]. |
| Raw scalar parameters | Metallic and roughness are finite numbers in [0, 1]. Boolean values cannot substitute for numbers. |
| Raw modes | Culling is `back`, `front` or `disabled`. Transparency is `disabled`, `alpha` or `alpha-scissor`. Known but incorrect modes fail comparison; unknown modes fail structure. |

Every numeric index must be a nonnegative integer; boolean and floating-point
substitutes fail. Element identities use canonical JSON equality. Native node
and material labels are bounded nonempty strings of at most 4,096 characters,
without NULs. Names do not establish source or capture provenance.

Material values are observed per surface. The checker permits separately
labeled native resource copies for the same source material, without assuming
the destination shares one resource. A repeated native material label must
always refer to the same source material index and identical canonical raw
values. Contradictory sharing, missing/duplicate parts or primitives, swapped
source associations, and mismatched geometry labels fail. Both source material
indices must be represented. The admitted fixture has 18 surface associations.
Changing all untrusted labels and observations consistently does not establish
or disprove an actual loader mapping; that requires the later native protocol.

## Fixed normalization and numerical comparison

C220 predeclares that the prospective destination stores linear source RGB
through the sRGB transfer. C234 accepts only the inverse of that declared
storage mapping. For each raw RGB component `c`, compute:

- `c / 12.92` when `c <= 0.04045`.
- `((c + 0.055) / 1.055) ** 2.4` otherwise.

Copy alpha unchanged. Metallic and roughness also receive no color transfer.
Raw values remain in the report beside independently recorded normalized
values; normalization never overwrites observations. Unknown or different
storage semantics fail. The checker does not select a transfer by testing
which alternative would pass.

Each normalized RGBA, metallic and roughness component has the unchanged
inclusive **0.000002** absolute-error limit. Python JSON decoding and the fixed
inverse transfer produce the represented numeric values. Compare the exact
rational values of those represented numbers against `1/500000`, without an
extra epsilon, relative allowance, float32 rounding or subtraction-rounding
slack. Reported decimal error magnitudes are descriptive binary64 subtraction
results; the individual pass flags use the exact comparison. This makes the
boundary rule explicit without enlarging the original limit.

Culling is exact: source `doubleSided: false` means back-face culling; true
would mean disabled culling. Front-face culling is never a substitute. Source
`OPAQUE` means disabled transparency, independently of its alpha component.
Both source materials currently have alpha 1. Values near 1 exercise the
linear-alpha tolerance without replacing the frozen source. Internal controls
may also isolate the alpha transfer rule; such controls are not admission of
a new source material.

## Report and limits

Report ID: `ontokin.c234.material-comparison/0.1`. Its stages remain distinct:

- `admission`: the fresh C221 report. On success this is the admission from the
  actual C222 invocation, after the initial admission check.
- `geometry`: exact C222 observation size/hash, complete inventory and corner
  map digest. A failure records its original upstream stage when available.
- `structure`: complete material associations and declared resource count.
- `comparison`: all 108 component checks and 36 exact mode checks, raw and
  normalized values, decoded source values, errors, per-channel outcomes and
  every failed association. A numerical failure retains this full comparison.

Not-run stages remain `NOT_RUN`. The report also identifies the exact material
observation bytes/hash and retains its declared origin separately. Geometry's
full corner map remains available from C222; C234 binds its canonical digest
without copying that large array into every material report.

All native/version, source-evaluation, export, import, render and scene-write
counts remain zero. Native receiving evidence, native mapping attestation,
target-execution authorization, normal comparison and pose comparison stay
false. A CPU pass establishes only these finite checks on untrusted observations.

The Godot observer, build lineage, rendering route, exact settings/cameras,
normal-loss and 126-pose comparisons, semantic/cross-target reporting, retained
source persistence and process/resource protocol remain later R07 work.
Original C210/C214 authority, held prototypes, consumed schedules and the
original strict Blender normal failure remain unchanged. R03–R06 and R08 retain
their separate scopes; this component does not complete R07 or a release.

## Affected verification

Run the explicit package-dependent controls:

```bash
python3 -IB tools/second_target_c234/tests/run_controls.py \
  --package-root /absolute/extracted-handoff
```

They remain outside broad product-test discovery, like C221/C222, because the
finite locked inputs reside in the restorable historical handoff. Execute the
unchanged C221/C222 controls as the inherited affected cohort. An independent
reviewer must construct a separate source/observation oracle and check identity,
malformed values, transfer errors, alpha, exact modes and numerical boundaries.
Current source revisions, exact commands, outcomes and preserved failures belong
in the external evidence record. No aggregate or native execution belongs to
this selected CPU step.
