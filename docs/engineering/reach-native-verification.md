# Actual native checks for recorded reach

This document describes a verification component for the adopted
[planar reach release contract](../language-design/planar-reach-v0.1/release-contract.md).
It does not record a completed native run or close a release gate.

`tools/verify_reach_native.mjs` reads exact source-built or Agent-retrieved
GLB/0.6 bytes, passes those bytes to the pinned Khronos validator and actual
Three.js `GLTFLoader`, and plays the loaded scene with
`tools/reach_destination.mjs`. It compares actual loaded geometry, PBR material
factors, carrier poses, world sites, and world vertices with separately supplied
source expectations. It does not use `AnimationMixer` for reach, synthesize a
replacement scene, invoke the production source pose evaluator, or create the
answers against which the artifact is checked.

## Implementation checkpoint and execution status

The first component consists only of new files:

- `tools/verify_reach_native.mjs`: bounded input/provenance handling and actual
  Khronos/Three execution.
- `tools/reach_native_support.mjs`: independent byte parsing, sample planning,
  enclosure comparison, and bounded exact arithmetic.
- `tests/reach_native_resources.mjs`: focused parser, clock, coverage,
  orientation, world-point, and filesystem rejection tests.
- This document.

At this implementation checkpoint, the component has **not executed against a
fresh reach GLB**. All three `node --check` syntax commands below passed without
importing or executing the modules. The focused tests and documentation
preservation check are prepared for the integrator's exclusive executor window.
A fresh source/oracle bridge,
successful real-byte positive runs, and native tamper runs remain necessary.
The source/export budget failures being investigated on the integration branch
must be resolved without changing the frozen source cases or acceptance limits.
No destination success is inferred from the presence of this code.

The component does not modify the controlled player, writer, independent source
reader, source corpus, package pins, existing evidence, or shared release status.
Its new file scope is declared in repository issue #24. The integrator records
the commit and executed results separately.

## Inputs and commands

Use the pinned verification-only packages already declared and locked under
`tools/`: Three.js `0.180.0` and Khronos `gltf-validator`
`2.0.0-dev.3.10`. A release run requires Node 22. The report records the actual
Node version and whether its major version is 22. A successful check on another
Node major establishes only that execution; it does not satisfy the prescribed
release environment.

The planner needs only Node's built-in modules and the new support module:

```bash
node tools/verify_reach_native.mjs --plan /absolute/run/scene.glb --output /absolute/run/native-plan.json
```

The output path must be fresh. Planning parses actual bytes and emits a required
observation schedule; it does not execute source, import Three.js, validate the
artifact in Khronos, or produce expected poses.

After a separate source bridge has produced the manifest and reference files:

```bash
node tools/verify_reach_native.mjs --manifest /absolute/run/native-input.json --output /absolute/run/native-report.json
```

The native command writes a report for both passing and failed verification and
exits nonzero if verification fails. It refuses to replace an existing output
file. A malformed command or unavailable output path is reported to stderr;
that failure cannot manufacture a passing report.

The tool can be imported without running its CLI. The principal exported entry
points are `planArtifact(filename)`, `verifyManifest(filename)`, and
`verifyCase(item, directory, dependencies, observed)`. The last is an execution
adapter for a controlled test harness, not an alternate source oracle.

### Manifest

The manifest schema is `ontokin.reach-native-input/0.1`:

```json
{
  "schema_version": "ontokin.reach-native-input/0.1",
  "source_kind": "source_component",
  "source_commit": "<40 lowercase hexadecimal characters>",
  "source_tree": "<40 lowercase hexadecimal characters>",
  "cases": [
    {
      "case_id": "P01-prefix",
      "program_revision": "sha256:<64 lowercase hexadecimal characters>",
      "artifact": {
        "path": "P01/scene.glb",
        "sha256": "sha256:<artifact digest>",
        "bytes": 1234
      },
      "reference": {
        "path": "P01/native-reference.json",
        "sha256": "sha256:<reference digest>",
        "bytes": 5678
      },
      "sources": [
        {
          "source_id": "entry",
          "path": "P01/source.ok",
          "sha256": "sha256:<raw UTF-8 source digest>",
          "bytes": 901
        }
      ]
    }
  ]
}
```

Digest placeholders and byte sizes above illustrate the schema; they are not a
valid runnable fixture. `source_kind` is either `source_component` or
`agent_retrieved_artifact`. That label records how the producer identifies its
input. The tool does not audit protocol messages or prove that an artifact was
retrieved through Agent. The corresponding report field
`agent_transport_audited` remains `false`.

Every input path is normalized, relative to the manifest directory, and
contained in that directory after resolving symlinks. Absolute paths, traversal,
backslashes, repeated source paths within a case, and symlink escapes are
rejected. Shared inputs across different cases must retain the same exact
identity. Every source unit in the artifact's complete pinned bundle manifest
must be supplied exactly once. Raw source SHA-256 values, manifest-derived
program revision, carrier identities, and source-span byte bounds are checked.

`source_commit` and `source_tree` are the source producer's Git identities. They
are retained as such; this tool does not reconstruct those Git objects or claim
that the working tree is clean. The report instead identifies the exact checker,
controlled player, derivation, package files, and oracle implementation inputs
actually read. Inputs are hashed again after the case executions; any change
fails the run. A separate evidence auditor must bind the producer's Git state
and actual invocation to the broader release record.

### Independent source reference

Each case has a reference with schema
`ontokin.reach-native-reference/0.1`. Its shape is:

```json
{
  "schema_version": "ontokin.reach-native-reference/0.1",
  "program_revision": "sha256:<bundle revision>",
  "artifact_sha256": "sha256:<actual artifact digest>",
  "tolerances": {
    "position_m": 0.001,
    "rotation_rad": 0.001,
    "time_s": 0.000001,
    "local_vertex_m": 0.00001
  },
  "oracle": {
    "method": "independent_reach_reference",
    "geometry_method": "<identify any inherited geometry constructor reuse>",
    "inputs": {
      "ontokin/reach_reference.py": "sha256:<executed implementation digest>",
      "<other repository-relative oracle input>": "sha256:<digest>"
    }
  },
  "source_boundary_times_seconds": ["0", "1"],
  "expected_nodes": [
    {
      "path": "<source occurrence path>",
      "element_id": ["<exact source element identity>"],
      "geometry": {
        "positions": [[0, 0, 0]],
        "normals": [[0, 1, 0]],
        "primitives": [
          {
            "indices": [0, 0, 0],
            "material": {
              "region_key": null,
              "base_color": [0.5, 0.5, 0.5, 1],
              "metallic": 0,
              "roughness": 0.7
            }
          }
        ]
      },
      "sites": [
        {"path": "<complete source site path>", "position_m": [0, 0, 0]}
      ]
    }
  ],
  "samples": [
    {
      "sample_id": "key:0",
      "kind": "recorded_key",
      "time_seconds": 0,
      "side": "after",
      "poses": {
        "<source occurrence path>": {
          "position_m": [["0/1", "0/1"], ["0/1", "0/1"], ["0/1", "0/1"]],
          "orientation_wxyz": [["1/1", "1/1"], ["0/1", "0/1"], ["0/1", "0/1"], ["0/1", "0/1"]]
        }
      },
      "sites": {
        "<complete source site path>": [["0/1", "0/1"], ["0/1", "0/1"], ["0/1", "0/1"]]
      }
    }
  ]
}
```

The geometry and sample arrays above show field layout only. Real references
must contain the complete nondegenerate source mesh and the complete required
schedule; a one-vertex triangle is not a passing example.

`expected_nodes` contains every source object carrier, including empty carriers.
An empty carrier uses `geometry: null`. Geometry positions and normals are the
source canonical carrier-local arrays after any one rigid local visual
placement. Primitive order, index order, winding, region membership, and all PBR
factors are explicit. For unregional box/sphere material, `region_key` is `null`;
for a native surface it is the exact source region key. Every carrier has a
`sites` array, including `[]` when it has no source sites.

The source bridge may reuse the inherited geometry constructors to emit the
canonical local mesh. It must disclose that reuse in `oracle.geometry_method`
and identify the relevant implementation files in `oracle.inputs`. This is an
actual native byte/geometry preservation check with separately supplied source
geometry; it is not a claim that this JavaScript component independently derives
the entire source loft construction algorithm.

Pose and site expectations must come from the independent `ReachReference`
enclosure path. Do not populate them with production `sampleControlled`, source
production poses, GLB key interpolation, or measurements of the artifact under
test. `oracle.inputs` must include the exact `ontokin/reach_reference.py` input
and all other source-oracle code used by the producer. The checker verifies the
listed hashes against actual repository files. A method label alone cannot prove
how an external producer generated an answer; the producer implementation and
its executed evidence remain reviewable inputs.

Every enclosure coordinate is a closed `[lower, upper]` pair. Prefer exact
reduced rational strings such as `"123/1024"`. Exact decimal strings are also
accepted. A JSON number is interpreted as its exact binary64 value, not as an
unbounded-precision decimal. Position units are meters; orientation order is
`WXYZ`, representing the proper source rotation. World site enclosures are
independent source points, not carrier-local offsets.

Tolerances must be positive, must not exceed the adopted `.001 m`, `.001 rad`,
`1e-6 s`, and `1e-5 m` local-vertex caps as represented by the existing settings,
and must not exceed the artifact's requested corresponding tolerance. The local
vertex tolerance is also bounded by the overall position tolerance. The checker
does not add a comparison epsilon. Its bounds can conservatively reject a
result extremely close to the acceptance boundary; they do not widen that
boundary.

## Exact observation coverage

The `--plan` output contains `required_samples`. The bridge copies each sample's
identity and clock fields and adds complete `poses` and `sites` enclosures.

| Kind | Sample identity | Source expectation clock |
| --- | --- | --- |
| Every actual stored key | `key:<index>` | Exact binary64 value of `time_seconds`, after side. |
| Eight distinct interiors per adjacent stored-key interval | `interval:<index>:fraction:<numerator>-<denominator>` | Exact binary64 value of `time_seconds`, after side. |
| Both sides of every source boundary | `boundary:<index>:before` and `boundary:<index>:after` | Exact decimal `source_time_seconds`, on the stated side. |
| Additional frozen fixture observations | Unique `fixture:<identity>`, kind `fixture` | Source clock chosen by the fixture, with an explicit side. |

The interior fractions are exactly `1/16`, `1/8`, `1/4`, `3/8`, `1/2`, `5/8`,
`3/4`, and `7/8`. This includes the midpoint and seven other interiors. Their
actual binary64 clocks must be distinct and strictly inside the interval.
Before/after samples can have the same destination clock but different source
expectations. A source boundary's exact decimal and its rounded stored key are
different observations even when both display as the same binary64 number.
The planner preserves separate sample IDs for them.

The independent `source_boundary_times_seconds` list must agree exactly, in
source-clock order, with the artifact boundary inventory. Every boundary must
also identify an exact retained key. Thus deleting a boundary from artifact
metadata cannot silently reduce source boundary coverage. Stored clocks are
checked against a direct exact-rational-to-binary32 round-to-nearest/even
conversion; there is no binary64 intermediate that can introduce double
rounding. Exact key-clock quantization is separately checked against the time
tolerance.

The checker requires the entire carrier and site inventory at every sample.
Missing or duplicate samples, changed sample clocks/sides, omitted source
boundaries, and an incomplete pose/site dictionary fail before native playback.
It does not silently substitute the available subset. Additional observations
must have `fixture:` IDs and kind `fixture`; mandatory IDs cannot be replaced.

## What is actually compared

Before asking Three.js to allocate decoded geometry, the checker verifies GLB
headers/chunks, embedded-buffer bounds, per-accessor spans, alignment, counts,
declared decoded components, repeated component work, the complete flat carrier
inventory, and the shared animation clock. Sparse/normalized accessors, external
resources, additional scenes, skins, textures, morph targets, cameras, and visual
helper carriers are outside this adapter and are rejected. It checks one
translation and one rotation channel per source carrier, LINEAR encoding,
initial node transforms, source identities, and the current source/destination
numerical basis hashes.

Khronos must report zero errors and zero warnings without a truncated issue
list. The exact bytes are then passed to `GLTFLoader`. Actual loaded root nodes
are resolved through its parser rather than by counting copied `extras` on
primitive children. Every loaded primitive's positions, normals, indices, PBR
material and occurrence/region association is checked against the independent
byte reader and source arrays. Local child transforms must be identity so that
local visual placement is applied once. Distinct native regions cannot merge
merely because their material factors happen to be equal.

At every required or extra fixture observation, the actual controlled player
updates the loaded scene. The checker reads actual carrier `matrixWorld`, world
position and proper orientation, transforms all independent carrier-local sites
by that matrix, and transforms every loaded primitive vertex by its actual
native mesh matrix. Expected world vertices are obtained from the source local
vertex and independent source pose enclosure. This covers placed geometry,
payload carriers, held/following objects, and moving ancestry to the extent they
are present in the supplied complete source case. It does not claim that an
unlisted release case was exercised.

### Numerical comparison

Carrier positions and world sites use exact rational Euclidean error bounds.
For each component, the checker bounds the distance from the actual binary64
observation to both source enclosure endpoints, sums squared component bounds,
and compares that exact upper bound with the exact squared tolerance.

The actual loaded quaternion is normalized with a rational square-root
enclosure. The source quaternion enclosure must contain unit squared norm. The
checker considers both signs and obtains a conservative upper bound `D²` on
squared chord distance between unit quaternions. For `D² < 4`, physical angular
error satisfies

\[
\theta^2 \leq \frac{4D^2}{1-D^2/4}.
\]

This follows from `theta = 4 asin(D/2)` and the upper bound
`asin(x) <= x / sqrt(1-x²)`. Acceptance compares the rational upper bound to the
squared rotation tolerance. Host `acos`, `atan2`, a nearly-one dot product, and
an unexplained angular epsilon do not determine acceptance.

For repeated world-vertex work, the checker derives a rational interval rotation
matrix from the independent source quaternion enclosure. It converts each
endpoint outward to binary64 and performs interval multiplication/addition with
explicit next-representable outward rounding. It compares an outward squared
Euclidean error upper bound with an inward squared-tolerance lower bound. This
avoids costly repeated rational matrix products at each vertex while retaining
a conservative comparison. Numeric output roots are also outward enclosed for
reporting. These checks concern actual CPU transforms; GPU shader evaluation and
rendered pixels are separate obligations.

## Resource limits and rejected work

All limits apply before the corresponding decoded allocation or observation
loop. A resource rejection means the requested native check is unestablished;
it does not mean the source program is semantically invalid or that a release
gate passed with fewer observations.

| Resource | Component limit |
| --- | --- |
| GLB, JSON reference, manifest, or identified implementation file | 64 MiB each |
| Raw source unit | 2 MiB |
| Cases per invocation | 256 |
| Keys per artifact | 10,000 |
| Baked carrier poses | 250,000 |
| Aggregate occurrence vertices | 250,000 |
| Declared accessor components | 4,760,000 |
| Repeated animation or primitive decoded components | 16,777,216 per respective account |
| Reference observations | 100,000 sample records and 1,000,000 aggregate carrier/site observations per case |
| Repeated native world vertices | 16,000,000 per case |
| Exact arithmetic operand | 32,768 bits, with prospective product guards |
| JSON nesting / values | 128 / 5,000,000 |

Input files must be regular files with bounded actual lengths. Reads allocate
only the checked length, detect growth/truncation, verify exact SHA-256, and
check for changes after execution. JSON parsing rejects duplicate keys, invalid
UTF-8, unpaired surrogates, nonfinite numeric literals, and excessive nesting.
The support tests include these rejection paths.

## Verification procedure and remaining gates

Run static syntax checks and the focused regressions in an exclusive executor
window under the repository coordination procedure:

```bash
node --check tools/reach_native_support.mjs
node --check tools/verify_reach_native.mjs
node --check tests/reach_native_resources.mjs
node tests/reach_native_resources.mjs
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

Retain output for all nine named tests, including the total and failure count.
The [destination verification record](reach-destination-validation/README.md)
documents a local `node --test` invocation that reported only a file-level
wrapper. If that invocation is also used, preserve its receipt separately;
a wrapper result alone does not establish that these nine probes executed.

Those focused tests construct a small structural GLB only to exercise bounded
decoding and schedule rules. They test exact rational conversion near a
binary32 tie, strict Euclidean rejection, quaternion sign/normalization,
outward world-point error, file-size limits, and path escapes. They do not
replace a real `.ok` source-to-GLB positive execution.

Next, the integrator must run a real source case through the independent
source/reference bridge and the native command. Preserve both successes and
failures with exact input/implementation identities. For meaningful native
rejection evidence, alter native vertex bytes, triangle membership, a PBR
factor, a recorded position/orientation, and a required observation in separate
copies. Recompute transport hashes and the reference's artifact identity for
the altered artifact while keeping the independent expected source answer
unchanged; otherwise a hash mismatch alone does not demonstrate the intended
geometric or motion comparison. Record the observed rejection code for each
probe. Malformed accessor counts/spans must fail before a native loader request.

A passing report always retains `release_acceptance: false`. It establishes
only its actual listed inputs and executed native observations. The following
remain separately required: complete independent source histories and
continuous certificates; all mandated source and ordinary Agent artifacts and
failure/recovery cases; transport and R/Q mapping audits; actual browser
rendering and reviewed screenshots; required Node/Python environments;
compatibility and inherited gates; and resulting-main integration checks.
Completing this native component does not complete the finite reach release or
the full [OntoKin goal](../../GOAL.md).
