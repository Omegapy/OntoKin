# C213 independent review

**Verdict: approve the finite CPU characterization at `36afd901c099bdfb6ac12af3994140a15a19ab4c`.** This verdict approves the isolated investigation and its stated limitations. C211's strict normal-preservation gate remains failed; the review approves no receiving retry or replacement tolerance.

## Evidence and checks

The [212-case corpus](cases.json) was [sealed](PREDECLARATION.json) before this reviewer read or executed the new implementation. It covers 21 families: cardinal/oblique directions, signed rounding midpoints, near-auto and azimuth shortcut thresholds, signed decoder inputs, normalization, finite and nonfinite invalid inputs, explicit invalid-range fallback and separate sharp-boundary corner directions. Final execution accepted 182 rows and refused 30 under the documented harness policy. All 934 [independent numerical assertions](checks-final.json) pass after the explicit oracle correction below.

Source inspection found that the first implementation silently supplied omitted normal, encoded-short and scalar inputs. The corrected candidate refuses them. Eleven separately declared [post-inspection controls](supplemental-cases.json) all refuse with accurate execution indicators. The [source and execution review](source-review.json) passes another 731 assertions, including exact pinned-source comparisons, selected function-body equality, numeric stability across the corrections and distinct encoder/decoder/normalization/process evidence. The implementation's selected codec arithmetic is unchanged by the corrections.

The initial independent run is preserved in [its observations](observed-initial.json) and [failed assertion report](checks-initial.json): 933 of 934 assertions passed. Its sole mismatch was this reviewer's mistaken expectation that decoding `-32768` should be refused. The pinned decoder takes the full signed-short domain; it divides by `32767` without imposing the encoder's smaller output range. [The explicit oracle correction](ORACLE-CORRECTION.json) therefore accepts that defined decoder diagnostic and requires the independent spherical comparison. The original cases, expectations and failed report remain unchanged. No product tolerance or measured failure was altered to obtain a pass.

## What the measurements establish

| Independently supplied case | Maximum component difference | Interpretation |
| --- | ---: | --- |
| Canonical frame, polar angle pi/2, azimuth 0.01 radians | `0.009999833069741726` | The azimuth shortcut stores zero azimuth and loses the small transverse component. |
| Canonical frame, projected cosine at the float32 shortcut threshold | `0.014142955653369427` | The shortcut boundary produces a larger finite discrepancy. This is an observed case, not a global maximum. |
| Near-auto input with two components of about `0.00009` | `0.00009000000136438757` | The componentwise comparison treats the supplied direction as the automatic normal. |

These cases use explicit finite, unit, orthonormal, right-handed frame inputs and valid angular ranges. They independently contradict a universal `2e-6` component-preservation promise for the selected codec on those supplied frames. They do not reconstruct the C211 sphere's missing native fan frame, encoded shorts or exact cause. The retained C211 maximum must remain a separate measured result.

The separate mathematical decoder, rounding and metric checks agree with the selected source. Actual scalar float32 evaluation uses the pinned approximation and helper operation order; compiler contraction and fast math are disabled. Round-to-nearest is verified, and subnormal parsing and arithmetic observations are reported separately. The executed environment is Linux x86-64, CPython 3.12.14, g++ 14.2 and glibc 2.41. [Final observations and source bindings](observed-final.json)

## Limits and next decision

The result supplies conditional finite counterexamples and a reproducible characterization. It does not establish a useful universal error bound, demonstrate visual acceptability or justify increasing the receiving tolerance. Before another native attempt, select and separately review a precise revised contract or a source-preserving alternative. Exact normals retained merely as metadata would not prove the fidelity of native shading normals.

Native fan construction, shared-fan averaging, mesh-based sharp-edge handling and the installed executable's source lineage remain outside the experiment. The sharp-boundary controls only establish that this isolated harness processes distinct supplied corner directions separately. No Blender process, import, render, save/reopen or full OntoKin regression ran. All detailed bindings and limitations are recorded in [the machine-readable review](FINAL-REVIEW.json).
