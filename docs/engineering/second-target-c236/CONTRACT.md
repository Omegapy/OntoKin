# C236/0.1.0: finite CPU world-pose observations and loss comparison

## Scope and source authority

A world pose is an object's position and orientation in the common world
coordinate frame. This separately versioned CPU component compares the original
18-part C210 fixture at its seven declared times, giving 126 object/time pairs.
It implements the pose step selected by [C235](../second-target-c235/NEXT-TASK.md)
under the unchanged [C220 plan](../second-target-c220/PLAN.md). Original C214,
C221, C222, C234 and C235 contracts and evidence remain unchanged.

The only public admission API is `check_poses(package_root, observation_path)`.
Each invocation executes fresh [C221 admission](../second-target-c221/CONTRACT.md).
A caller cannot substitute an old pass, replacement authority or chosen
reference. The checker rereads the original C210 reference and GLB through
their exact C220 size/hash/mode pins, then parses those inspected bytes. Source
position and orientation values come directly from the original reference
samples, without evaluator, exporter, animation interpolation or regeneration.
The original 18-part map supplies source identities independently of labels.

The original GLB has absent/unit node scales, no node matrices or transform
parents, and no scale animation channels. These facts are checked before the
profile derives unit world scale. The original reference supplies positions and
wxyz quaternions; it does not supply world matrices or scales. Derived matrices
are consistency calculations, never new source authority.

This finite schema does not bind geometry, materials or normals to the same
capture. Their existing separate checkers remain intact. A later combined
capture/provenance protocol must bind those observations and actual loader
identities. A producer can relabel a fabricated dataset consistently; a CPU
comparison cannot attest native capture or prove a loader mapping.

## Invocation and strict file handling

```bash
python3 -IB tools/second_target_c236/check_poses.py \
  --package-root /absolute/extracted-handoff \
  --pose-observations /absolute/poses.json
```

The command emits one JSON report and creates no file. Exit 0 means
`PASS_CPU_POSES`; exit 1 means structural `FAIL_CLOSED`, measured
`FAIL_POSE_LIMIT`, or additional-profile `FAIL_SCALE_PROFILE`; argument errors use exit 2. The API raises `CheckError`
with its complete report for either failure. Internal underscore-prefixed
helpers are test seams and cannot admit authority.

The input is nonempty and at most 1 MiB. Directory-relative no-follow reads,
nonblocking file opening, and before/after descriptor checks refuse symlinks,
traversal, nonregular files and changed reads. Exact read bytes are retained by
size/SHA-256 and decoded as strict UTF-8 JSON. Duplicate object keys, nonfinite
tokens, malformed JSON, missing fields and unknown fields are refused. File
permissions and a producer origin label do not establish observation authority.

## Finite observation schema

Schema ID: `ontokin.c236.pose-observations/0.1`. All objects have exactly the
fields below. Order of parts and samples is immaterial; identities are not.

| Object | Exact fields and meaning |
| --- | --- |
| Root | `schema`, `declared_origin`, `accepted_program_revision`, `glb_sha256`, `coordinate_system`, `parts`. |
| Origin | Literal `synthetic` or `unattested-native`; either remains untrusted. |
| Source claims | Exact freshly admitted C221 revision and bare GLB SHA-256. |
| Coordinate system | Exactly `position_unit: "m"`, `time_unit: "s"`, `basis: "gltf-rh-y-up-identity"`, `quaternion_order: "wxyz"`, `matrix_layout: "row-major-4x4"`. No frame conversion or axis selection. |
| Part | `gltf_node`, `gltf_mesh`, `element_id`, `definition_id`, `source_path`, `native_node_id`, `samples`. Exactly 18 unique complete admitted source identities. |
| Native label | Nonempty text, at most 4096 characters, without NUL; unique across parts. It is descriptive and unverified. |
| Sample | `reference_time_seconds`, `observed_time_seconds`, `translation_m`, `rotation_wxyz`, `scale`, `world_matrix`. Exactly seven unique samples for each part. |
| Reference time | One exact string from `"0"`, `"0.25"`, `"0.5"`, `"0.75"`, `"1"`, `"1.5"`, `"2"`. It selects the matching frozen source row; no nearest-time matching occurs. |
| Observed time | One finite non-bool number. Its difference from the selected reference time is measured, not used to select another row. |
| Translation, quaternion, scale | Arrays of 3, 4 and 3 finite non-bool numbers. Quaternion is nonzero. Every scale component is strictly positive. |
| World matrix | Exactly 16 finite non-bool numbers representing a row-major affine matrix applied to column vectors. Translation occupies entries 3, 7 and 11; the last row is exactly [0, 0, 0, 1]. |

All numeric values use Python's JSON represented integers/binary64 values.
Numbers that cannot be represented as finite binary64 are refused. Signed zero
is retained in raw report values but equals zero in arithmetic. Indices require
actual nonnegative integers, not boolean or floating-point substitutes. Element
and definition IDs use canonical JSON equality.

Missing, duplicate, swapped or extra part identities/reference-time slots,
malformed vectors, zero quaternions, nonpositive scales, projective matrices or
inconsistent matrix/quaternion decompositions cause structural rejection.
Swapping pose values between otherwise complete declared slots remains an
admissible observation and is compared against those declared slots; it is not
silently rematched.

## Matrix and scale rules fixed before controls

Let q=(w,x,y,z) be the raw quaternion and N=w²+x²+y²+z², evaluated as exact
fractions of its represented components. The normalized rotation matrix is:

```text
[(w²+x²-y²-z²)/N, 2(xy-wz)/N,       2(xz+wy)/N]
[2(xy+wz)/N,       (w²-x²+y²-z²)/N, 2(yz-wx)/N]
[2(xz-wy)/N,       2(yz+wx)/N,       (w²-x²-y²+z²)/N]
```

For each matrix column j, divide its three linear entries by the raw positive
scale component j, using exact fractions. Each normalized entry must differ
from the corresponding exact homogeneous quaternion rotation entry by at most
**2^-20**, exactly 1/1048576. This is a new, dimensionless C236 structural
self-consistency envelope, fixed before controls. It is not a source pose
fidelity tolerance and does not alter any C220 limit. Preserve all nine exact
signed/absolute residuals, their maximum and the bound in the report.

The matrix translation entries must equal the corresponding raw translation
components arithmetically because both fields report the same world origin.
The affine final row is exactly [0, 0, 0, 1]. The raw linear-block determinant
must be strictly positive. Larger inconsistent rotation, shear, reflection,
projective transforms and stale translation are structurally refused. Small
nonorthogonal residuals within the declared envelope remain visible; a pass
does not establish an exactly rigid matrix.

The envelope permits independent rounding of matrix and quaternion/scale
representations. For binary32 rounding alone, with unit roundoff u=2^-24,
a normalized quaternion perturbation and independently rounded matrix/scale
ratios motivate a finite margin below 16u=2^-20. This is a predeclared policy,
not a theorem covering every native decomposition, accumulation or algorithm.
No current result proves that Godot observations satisfy it. An observation
outside it is refused under this profile without claiming its source-relative
pose error was measured. Do not replace the raw matrix with a recomposition.
Derived unit-source matrices are displayed by converting exact rational
rotation entries once to binary64; they never decide observed admission.

Positive nonunit scales are structurally valid and retained. The original GLB
supports an exact unit reference [1, 1, 1]. C236 adds a **separate exact-unit-scale
profile condition**, with no tolerance: differing components are scale loss.
This is not an original C220 position/orientation/time gate. Report the
original pose-gate outcome and added scale-profile outcome independently.
If original pose gates pass but scale differs, overall result is
`FAIL_SCALE_PROFILE`; any original pose failure gives `FAIL_POSE_LIMIT` while
also retaining scale outcomes. Only both passing gives `PASS_CPU_POSES`.
A separately rounded near-unit native scale can fail this additional profile;
no claim of an original C220 failure follows from that scale result alone.

Quaternion magnitude is not scale: nonzero q, -q and nonzero finite rescalings
represent the same rotation, subject to their actual represented ratios.
Raw quaternions and scales are never replaced.

## Source-relative numerical rules fixed before controls

All original inclusive limits remain: position 0.001 m, orientation 0.001 rad,
and time 0.000001 s. They are the exact fractions 1/1000, 1/1000 and 1/1000000.
The position metric remains the original C210 maximum absolute XYZ component
error, not Euclidean distance.

Position/time gates use exact differences of represented numbers. Each
position component passes when `abs(Fraction(raw)-Fraction(source)) <= 1/1000`.
Observed time passes when its exact difference from the selected decimal
reference-time string is at most 1/1000000. No subtraction rounding, epsilon,
time interpolation or relative tolerance can alter those decisions.

Orientation is sign-invariant and uses the same homogeneous normalization for
raw and original source q. Set `r = dot(raw,source)^2 / (norm²(raw)*norm²(source))`
with exact rational arithmetic. The principal angle is at most 1/1000 rad
exactly when `r >= cos(1/2000)^2`. The checker encloses cosine by alternating
exact-rational Taylor partial sums, with at most 256 terms. If r is at least
the squared upper bound, the angle gate passes; if it is at most the squared
lower bound, it fails. Otherwise it refines the bounds. Failure to decide in
that fixed finite budget is explicit `NUMERIC_RESOLUTION` structural refusal,
never an approximate pass. This avoids cancellation near equal orientations
and adds no angular allowance.

The displayed angle is diagnostic binary64: normalize each quaternion using
its largest absolute component, form the relative quaternion, and calculate
`2*atan2(norm(relative.xyz), abs(relative.w))`. It cannot decide the gate.
Exact q ratios and maximum component/time errors remain reportable as rational
strings. Display overflow becomes null with an explicit flag, never NaN or
infinity. Raw/source values remain alongside all derived results.

## Complete reports and limits

Report ID: `ontokin.c236.pose-comparison/0.1`. Stages are `admission`,
`source`, `structure` and `comparison`; unreached stages stay `NOT_RUN`.
The report identifies exact observation bytes, source-reference bytes, GLB
bytes and the complete canonical 126-row source-identity/time map digest.

Every admissible sample contributes one report row with source node/mesh/path,
element and definition IDs, native label, both times, raw matrix/T/q/scale,
original reference T/q, derived unit source scale/matrix, exact per-component
and time errors, angular error/ratio, all nine matrix-consistency residuals, the three original pose
gate outcomes and separate scale-profile outcome and every failed component. Per-part and per-time summaries
account for all 126 pairs, 378 translation components and 378 scale components.
An explicit loss list identifies every failed pair and gate; measured failure
retains the complete rows and denominators. No failing sample is dropped.

All native/version, source-evaluation, export, import, render, native scene-write
and aggregate-start counts remain zero. Native evidence, mapping attestation,
target execution authorization, R07 completion and release acceptance remain
false. The original strict Blender normal failure stays failed. C234 material
and C235 normal behavior/results are not rerun by this checker.

Standalone author controls under `tools/second_target_c236/tests/` cover exact
authority/byte bindings, complete identity/time accounting, matrix consistency,
sign-equivalent quaternions, changed/renamed/swapped/missing samples, scale loss,
malformed/zero/nonfinite values, signed zero, numeric extremes and adjacent
boundaries. Unchanged C221/C222/C234/C235 cohorts are the affected prerequisites.
Independent review constructs a separate oracle on exact source. Later capture,
cross-target/semantic treatment, persistence, build lineage, rendering, settings,
cameras and process protocols remain separate R07 tasks. No native attempt or
second feature belongs to C236.

