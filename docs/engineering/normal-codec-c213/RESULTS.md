# C213 finite codec results

## Outcome

The selected CPU characterization establishes concrete counterexamples to strict component preservation under explicit valid normal-frame inputs. It explains why short-rounding scale alone cannot justify a replacement error budget. The finite results do not establish a universal error bound, acceptable visual loss, or the exact cause of C211's observed native error.

The original C211 absolute component requirement remains `2e-6`, and its receiving result remains **FAILED/PARTIAL**. [C212's decision](../normal-fidelity-c212/DECISION.md) is unchanged. No receiver code, runtime, exporter, original contract or historical evidence changed; no native import, render, save or reopen ran. This analysis does not adopt an approximate receiving profile.

## Source and experimental domain

The final implementation worker candidate is `36afd901c099bdfb6ac12af3994140a15a19ab4c`, following preserved initial and reporting checkpoints. Publication and final-main identities are recorded separately in the integration evidence and handoff; this exact worker commit is not described as a published commit unless independently observed in remote ancestry.

Five selected functions are extracted byte for byte from Blender commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`: short encoding, short decoding, normal encoding, normal decoding and approximate inverse cosine. The wrapper specializes their scalar support operations, including sequential float32 dot products, square-root-then-division normalization with the upstream `1e-35f` threshold, component comparison and multiply/add. [Implementation and precision](IMPLEMENTATION.md), [source identities](SOURCE-BINDINGS.json).

Inputs declare a finite, unit, orthonormal, right-handed basis and positive angular ranges. The normal is either normalized by the selected upstream support path or supplied as a unit float32 direction in an explicit diagnostic mode. Distinct modes test the zero sentinel and invalid-range decoder fallback. Invalid bases, missing fields, nonfinite values and unsupported inputs are refused by the harness. Such refusal is not a claim that Blender itself raises the same error.

The build uses scalar binary32 with contraction and fast-math disabled. Output component and angular metrics use separate Python double calculations. Independent checks compare the decoder with a mathematical spherical reconstruction, rather than importing the implementation. [Final observations](evidence/independent-controls/observed-final.json) bind the compiler, environment, executable, inputs and source hashes.

The experiment supplies frames; it does not construct native mesh fans, assign topology, average connected corners or replay sharp-edge processing. A valid supplied frame is not proof that C211 used it. The retained C211 observations contain neither native frame values nor encoded short pairs, and the installed binary's source lineage remains unresolved.

## Conditional losses

The following measurements compare nonzero direction inputs with decoded directions. They exclude zero-sentinel and support-function diagnostics, which are not preservation examples.

| Explicit-frame case | Observed maximum component difference | Interpretation |
| --- | ---: | --- |
| Azimuth of `0.01` radians in the canonical frame | `0.009999833069741726` | The azimuth shortcut replaces the small in-plane angle with zero. |
| Float32 azimuth-threshold equality | `0.014142955653369427` | Equality takes the same shortcut. This is the largest direction-component loss in the selected finite corpus, not a bound. |
| Two near-auto components of approximately `0.00009` | `0.00009000000136438757` | The component comparison accepts the automatic normal and discards the supplied perturbation. |

The threshold case's angular difference is `0.014143427182338051` radians. The selected direction round trips contain 69 accepted nonzero cases; 62 exceed the unchanged `2e-6` component criterion. That fraction describes an intentionally boundary-heavy corpus and is not a failure rate for ordinary assets. [Independent component and angle checks](evidence/independent-controls/checks-final.json).

The azimuth branch uses float32 `1.0f - 1e-4f`. The near-auto comparison accepts component deltas **less than or equal to** `1e-4f`. Short encoding uses `floorf(value * 32767.0f + 0.5f)`, including asymmetric negative half-step behavior. Approximate inverse cosine and normalization also contribute numerical differences. Complete selected-path observations retain these effects; no sum of isolated half-steps is presented as a complete bound.

These counterexamples do not revise C211's measured maximum of `0.0001531541347503662`. C211 measured one imported geometry/build case. C213 measures deliberately supplied independent frames and directions. The two results answer different questions.

## Independent validation and retained failures

The 212 cases span 21 families and were sealed before the implementation was executed. They cover cardinal and oblique directions, rotated frames, signed rounding boundaries, both shortcut thresholds, normalization, invalid inputs, raw decoder boundaries and distinct directions on opposite sides of a sharp boundary. The case file SHA-256 is `fa2241d38866224fdbe4ea9f9a02a4f667c06df973ea59c67c02cb81adb00f1e`.

The initial run passed 933 of 934 assertions. Its sole mismatch was an independent expectation error: a test expected the decoder to refuse `-32768`, but the pinned decoder accepts the full signed-short domain. The encoder/quantizer's usual `[-32767,32767]` output domain does not narrow the decoder's raw input domain. The [specific correction](evidence/independent-controls/ORACLE-CORRECTION.json) changes only the adjudication of that test, requires a finite independently reconstructed result, and leaves the sealed case and expectation files untouched. [Initial failure](evidence/independent-controls/checks-initial.json).

The final implementation run passes all 934 assertions with that explicit correction. It contains 182 accepted diagnostic/codec rows and 30 expected refusals. Acceptance of a row means the operation was within the experiment's declared domain; it does not mean its normal met C211's strict criterion. The unchanged original failed assertion remains inspectable.

Review also tightened input-field requirements, exact integer-short validation and execution/environment reporting. All 11 supplemental omission/type cases are correctly refused; a separate source/execution review passes 731 assertions. These checks cover the concrete corrections separately from the original sealed corpus. A separate [13-check source-fidelity review](evidence/source-review/SOURCE-REVIEW.json) verifies pinned file identities, extracted bodies and scalar support operations. Publication evidence records the exact reviewed inputs and applicable documentation checks.

Historical C210/C211 and earlier failed or interrupted broad regressions remain unchanged. This analysis-only increment adds no product runtime, compiler, exporter, receiver or hosted-workflow behavior. The applicable checks are the new finite experiment, independent review, exact unchanged legacy-input comparison and documentation preservation. No full product-regression pass is inferred.

## Consequence and next boundary

This evidence does not support choosing a new tolerance from either the C211 sphere maximum or the C213 finite maximum. A deliberately approximate profile would need a defined downstream purpose, independently justified acceptance criteria and actual receiving evidence. The characterization alone supplies none of those.

The next bounded implementation should make exact source-direction preservation and observed native-shading loss separate, machine-readable claims. A CPU-only source-normal payload can bind exact per-corner source identities, float32 directions and winding to the accepted GLB, and a loss-report contract can distinguish native observations from source authority. That is a proposed separately versioned profile, not a repair of C211's original strict promise. [Next task and acceptance conditions](NEXT-TASK.md).

The held receiver, unexecuted denoising correction, native save/reopen and visual gates remain pending. The second destination and direct-authoring comparison remain later stages. Stop C213 after its verified handoff is saved.
