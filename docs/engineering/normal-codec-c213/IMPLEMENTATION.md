# C213 isolated normal-codec implementation

This harness characterizes selected Blender `v4.3.2` source at commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`. It supplies explicit normal frames to the encoder and decoder. A frame contains the automatic normal (`lnor`), one perpendicular reference direction (`ref`), its right-handed perpendicular direction (`ortho`), and angular ranges (`alpha`, `beta`). It does not construct a frame from a mesh.

The complete selected encoder/decoder bodies and scalar quantization functions are extracted byte for byte from the retained upstream files. The inverse-cosine approximation is extracted the same way. [Source bindings](SOURCE-BINDINGS.json) record exact file hashes, source URLs and the upstream commit. [Extraction helper](extract_codec.py) reproduces [the generated include](codec_exact.inc); [the runner](run_probe.py) checks it against the source on every invocation. Minimal scalar vector adapters in [the executable wrapper](codec_probe.cpp) preserve the selected support operations and order.

## Run

Python 3.11+ and a C++17 compiler are required for this verification-only experiment. There is no new OntoKin runtime dependency. From the repository root:

```bash
python3 -IB docs/engineering/normal-codec-c213/run_probe.py \
  --cases /absolute/independent-cases.json \
  --output /absolute/observations.json \
  --build-dir /absolute/cpu-build
```

The case file is either a JSON list or an object with a `cases` list. Each case has a distinct string `id`. Results are observations, not a pass certificate. Independent assertions must judge expected rejection, branches and numerical outcomes. No case invokes Blender. `probeProcessExecuted` records the standalone process; separate encoder, decoder, input-normalization and standalone-helper fields record which selected functions actually executed. A frame refusal can run the probe process while executing neither codec function. A strict normalization-collapse refusal records normalization execution separately.

| Operation | Required fields | Observation |
| --- | --- | --- |
| `roundtrip` (default) | Explicit `frame`; `normal` with three components | Encoded short pair, decoded direction, branch trace and numerical differences |
| `decode` | Explicit `frame`; integer `shorts` with two components | Decoded direction and automatic-normal fallback indicator |
| `quantize` | `value` | Float32 input, intermediate multiply/add, rounded short and decoded fraction |
| `acos` | `value` | Pinned approximate result and separate double-precision `acos` reference |
| `normalize` | `normal` | Pinned float32 squared length, normalized output and zero-collapse indicator |

`frame` has `lnor`, `ref`, `ortho` arrays, and numeric `alpha`, `beta`. Operation-specific required fields must be supplied; omitted normals, encoded shorts or scalar values are refused rather than replaced with a case. Decoder shorts must be exact JSON integers, with booleans and floating-point values refused before float32 conversion. Explicit strings `NaN`, `Infinity`, `-Infinity` are available for refusal controls. They do not authorize nonfinite codec execution.

## Preconditions and diagnostic modes

All numeric inputs are converted to IEEE-754 binary32 before the selected kernel. The harness requires finite frame components; squared length within `2e-6` of one for each basis vector; pairwise dot products within `2e-6` of zero; and each component of `cross(lnor,ref)-ortho` within `2e-6`. It requires `0 < alpha <= float32(pi)` and `0 < beta <= float32(2*pi)`. These are explicit experiment preconditions, not claims that every such frame occurs in Blender. The frame-check tolerance describes input admissibility and is unrelated to changing C211's output requirement.

The default `strict` round trip rejects zero/nonfinite normals and applies the C++ `math::normalize` route used by `BKE_mesh_set_custom_normals_from_verts` before encoding. A normal that collapses to zero or becomes nonfinite during normalization is refused. The resulting squared length must be within `2e-6` of one. `unit` mode feeds an already unit float32 direction directly and applies the same squared-length precondition; this mode isolates encoder thresholds from input normalization.

`zero-sentinel` accepts only an exact zero normal and records the encoder's zero/NOP behavior. This is a raw codec diagnostic: the full mesh setter can substitute automatic vertex/corner normals before encoding, and that substitution is not replayed here. `invalid-range-fallback` is decode-only and requires an otherwise valid frame with `alpha==0` or `beta==0`. It records the upstream decoder's return of `lnor`. Invalid-frame encoder division is never executed. Degenerate/nonfinite bases and other invalid inputs are harness refusals, not measured upstream exceptions.

The decoder accepts the full signed-short domain, including `-32768`; the encoder and quantizer normally produce only `[-32767,32767]`. Quantization inputs must be finite and lie within `[-1,1]`. Finite `acos` values outside `[-1,1]` expose the upstream clamping behavior. `normalize` permits finite zero, tiny and overflowing-length inputs as explicit support-function diagnostics; nonfinite source vectors are refused.

## Floating-point boundary

The wrapper uses actual scalar binary32 arithmetic, 16-bit signed shorts and the pinned polynomial coefficients. The compiler flags are `-std=c++17 -O0 -fno-fast-math -ffp-contract=off -Wall -Wextra -Werror`; the process selects round-to-nearest and verifies both the setter result and the resulting mode. The report records compiler version/path/hash, command, probe hash, platform, libc, Python version, `FLT_EVAL_METHOD` and separate subnormal parsing/arithmetic observations.

The dot product accumulates component products in order. C++ normalization computes the float32 squared length, compares it with `1e-35f`, takes the float square root, then divides each component by that length. It does not use the separate C helper's reciprocal-multiply route. `compare_ff` is `fabsf(a-b) <= max_diff`, so equality belongs to the near-auto shortcut. Azimuth uses the float32 expression `1.0f-1e-4f`, not an abstract decimal threshold. Quantization uses `floorf(value*32767.0f+0.5f)`, including its asymmetric behavior for negative half steps. Fused multiply/add and fast-math reassociation are disabled.

The output metrics use Python double precision. They measure maximum component error against the actual float32 direction fed to the encoder, unit-length drift and the angle between normalized directions using `atan2(length(cross),dot)`. They are diagnostic calculations, distinct from the upstream float32 codec. Zero-sentinel component metrics compare against zero and have no meaningful direction angle; they are not preservation evidence.

## Limits and attribution

This is a selected scalar source characterization, not a build of Blender and not a bitwise attestation of its executable. Native fan construction, topology/sharp-edge processing, corner averaging, threading, compiler choices and other library implementations remain outside this harness. The original C211 observations do not contain native fan frames or encoded short pairs. The retained binary's exact source lineage remains unresolved. No supplied frame is labeled as a replay of that import.

Finite case maxima are observations, not universal bounds. The experiment cannot adopt a replacement loss budget or establish an acceptable visual/physical result. C211's `2e-6` requirement and failed result remain unchanged.

The retained Blender source, extracted bodies and derived C++ support carry `GPL-2.0-or-later` SPDX attribution. Their original notices are preserved in `upstream/`, with the pinned upstream [license text](upstream/GPL-license.txt) and [license provenance](LICENSE-PROVENANCE.json). The source URLs and exact commit in SOURCE-BINDINGS identify each upstream origin. This analysis directory is separate from OntoKin runtime code.
