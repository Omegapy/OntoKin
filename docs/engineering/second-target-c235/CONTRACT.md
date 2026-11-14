# C235/0.1.0: finite CPU normal observations and strict loss comparison

## Scope and authority

A surface normal is a direction used for shading. This separately versioned
R07 checker compares all 23,400 instance corners of the unchanged C210 fixture
with the exact C214 source directions. It implements the normal comparison
selected by [C234's next task](../second-target-c234/NEXT-TASK.md), under the
[C220 plan](../second-target-c220/PLAN.md). C214, C221, C222 and C234 retain their
existing contracts and behavior. No source evaluation, export, native process,
import, render or native scene write occurs.

The only public admission API is `check_normals(package_root,
geometry_observation_path, normal_observation_path)`. Every call executes fresh
[C221 admission](../second-target-c221/CONTRACT.md), then the public
[C222 checker](../second-target-c222/CONTRACT.md), including its own fresh
admission and complete geometry correspondence. A caller cannot supply a pass
report or replacement source. Geometry is safely reread and must match the exact
byte length and SHA-256 just checked by C222. The normal document binds both
those bytes and the canonical digest of the complete C222 corner map.

C222 chooses correspondence using admitted part identity, exact positions and
the predeclared winding reversal/cyclic order only. No observed or source
normal, angle, magnitude or desired result selects a geometric match. C235
uses that finished map to join each raw corner to its source mesh, primitive,
triangle, corner and vertex. It rereads the C214 payload and GLB through the
original byte-size/hash/mode pins. Every retained `normal_f32le` is decoded
directly as three little-endian binary32 values and checked against the GLB's
NORMAL accessor at its source vertex. The original twelve bytes remain in
each reported row. No direction is regenerated, repaired or averaged.

Executable identity is recorded externally with the exact checked revision and
file hashes. These byte checks are not hostile-host or native-capture attestation.

## Invocation and file handling

```bash
python3 -IB tools/second_target_c235/check_normals.py \
  --package-root /absolute/extracted-handoff \
  --geometry-observations /absolute/geometry.json \
  --normal-observations /absolute/normals.json
```

The command emits one JSON report on standard output and creates no file.
Exit 0 means `PASS_CPU_NORMALS`; exit 1 means either structural `FAIL_CLOSED`
or admissible measured `FAIL_STRICT_NORMAL_LIMIT`. Argument errors use exit 2.
The API raises `CheckError` for either failure; its `report` retains the complete
outcomes reached, including all measured rows on a strict-limit failure.
Underscore-prefixed helpers are internal test seams, never admission APIs.

Each normal-observation file is nonempty and bounded to 16 MiB. No-follow
directory handles, nonblocking file opening and before/after descriptor metadata
checks reject symlinks, traversal, nonregular files and changed reads. The exact
read bytes are hashed and decoded as strict UTF-8 JSON. Duplicate object keys,
nonfinite tokens, truncation, unknown fields and missing fields are refused.
Geometry retains C222's independent safe-read and 16 MiB limit. Neither file's
permissions establish authority, nor do these checks prevent later mutations.

## Normal observation schema

Schema ID: `ontokin.c235.normal-observations/0.1`. The frozen C222 document is
unchanged. C235 adds an explicit complete corner-normal view of its exact bytes.

| Object | Exact fields and meaning |
| --- | --- |
| Root | `schema`, `declared_origin`, `accepted_program_revision`, `glb_sha256`, `normal_frame`, `geometry_observation`, `records`. |
| Origin | `synthetic` or `unattested-native`, equal to the bound C222 origin; both are untrusted labels. |
| Source | Revision and GLB digest equal the freshly admitted C221 authority. |
| Frame | Literal `gltf-object-local-right-handed-y-up`; the C220 identity basis, with no conversion or axis selection. |
| Geometry binding | Exactly `bytes`, `sha256`, `corner_map_sha256`; all equal the current C222 result. |
| Record | Exactly `key` and `normal`. All 23,400 raw corners occur once; record order is immaterial. |
| Key | Five nonnegative, non-bool integers: `[gltf_node, gltf_primitive, raw_triangle, raw_corner, raw_vertex]`, exactly matching a C222 map row. |
| Normal | Exactly three finite non-bool numeric values, with at least one nonzero component. No unit-length requirement is imposed. |

Each normal must equal the bound geometry array entry at its raw vertex using
canonical JSON equality, including represented type and signed zero. This
redundant corner view cannot contradict or silently replace the raw geometry
normal. Missing, extra, duplicate, swapped, unknown or mistyped keys, zero
vectors, malformed vectors and inconsistent copies cause structural rejection;
the numerical comparison then remains `NOT_RUN`. Changing a normal requires
changing the raw geometry bytes and their binding too, while the geometry-only
corner map can remain unchanged. Source keys are derived, never producer claims.

The report preserves the raw normal exactly as decoded, including signed zero.
Signed zero has zero component error. The accepted source fixture contains no
negative-zero normal components; an internal numeric control does not claim
otherwise. C235's refusal of incomplete/invalid observations is its own finite
contract and does not modify C214's separately versioned partial-loss reporter.

## Numerical rule declared before controls

Compare each raw component with its mapped source binary32 component in the
same object-local identity basis, **before any normalization**. Python JSON
decoding supplies represented integers or binary64 values; source binary32
values are exactly representable in binary64. The strict, inclusive absolute
component limit is unchanged: **0.000002**, exactly `1/500000`.

For each component, compare `abs(Fraction(raw) - Fraction(source)) <=
Fraction(1, 500000)`. Do not round the observed value to binary32, add an epsilon,
use relative error or let rounded subtraction decide the boundary. Exact
rational boundary controls may exercise the private comparison seam; they do
not add Fraction-valued JSON input. Public controls use the closest binary64
values on each side of the exact decimal limit. A JSON token `0.000002` follows
its represented binary64 value; token spelling does not create decimal arithmetic.

For reporting, signed deltas and absolute errors are binary64 displays of the
exact rational differences. Pass flags and the maximum-error corner selection
use exact rational differences, so displayed rounding cannot change a result.
Any unrepresentable display is null with an explicit overflow flag; exact
maximum-error fractions remain available in the overall and per-part summaries.
Every exceeded component and corner is retained. Neither magnitude nor angular
agreement can excuse a component error.

Angular error is diagnostic only, with no angular acceptance tolerance. Scale
each nonzero vector by its largest absolute component, normalize the scaled
vector with `hypot`, then compute degrees of `atan2(hypot(cross), dot)`. This
avoids overflow/underflow for finite huge or subnormal vectors. Equal directions
have zero angle; opposite directions have 180 degrees. Angle-only normalization
never overwrites raw/source values or changes the component gate. Reports also
retain the raw and source vector magnitudes using `hypot`; if a finite vector's
magnitude exceeds binary64 range, its magnitude display is null with an explicit
overflow flag, not a nonfinite JSON number or structural rejection.

## Report, accounting and limits

Report ID: `ontokin.c235.normal-comparison/0.1`. Stages are `admission`,
`geometry`, `structure` and `comparison`. Unreached stages remain `NOT_RUN`.
The report identifies both observation files by exact length and SHA-256, the
complete corner-map digest and field declaration, and the pinned C214 payload.
All 18 parts, 23,400 corners and 70,200 component comparisons are accounted for.

Comparison contains one row per C222 map row, in its deterministic order: raw
key, complete source key and vertex, exact source-normal bytes, raw/source
vectors, signed/absolute errors, three pass flags, failed component names,
angular error and magnitudes. Per-part summaries contain full corner/component
denominators, passing/exceeding counts and numerical maxima. An explicit list
of every exceeding corner references those keys and failed components. A
nonempty list gives `FAIL_STRICT_NORMAL_LIMIT`; no row is dropped to improve it.

Native evidence, native mapping attestation and target-execution authorization
remain false even for a pass or an `unattested-native` label. Material and pose
comparisons are not repeated. The original strict Blender normal failure remains
failed. This is one CPU preparation component, not Godot behavior, receiving
acceptance, R07 completion, a release or a new shading tolerance.

## Affected controls and next boundary

Standalone controls live under `tools/second_target_c235/tests/`, outside broad
product-test discovery because they need the pinned historical package. They
cover an independently decoded exact fixture, complete keys/accounting, fresh
authority and observation binding, normal-only changes with unchanged mapping,
swapped/missing/malformed values, zero/nonfinite vectors, exact and adjacent
boundaries, signed zero, magnitude loss, opposite directions and numeric extremes.
Run the unchanged C221, C222 and C234 cohorts as the affected prerequisites.
Independent review constructs a separate oracle and identifies its exact source.

The 126-pose comparison, semantic/cross-target treatment, observer/capture and
persistence protocols, exact settings/cameras, resource/process enforcement,
build lineage and rendering capability remain later R07 scopes. No aggregate
replay, fixture regeneration, native attempt or broader feature belongs here.
