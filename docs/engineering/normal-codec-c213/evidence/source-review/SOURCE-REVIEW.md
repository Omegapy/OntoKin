# Independent C213 source-fidelity review

**Verdict: pass within the declared CPU-characterization scope. No blocking source finding remains.** Reviewed implementation commit: `36afd901c099bdfb6ac12af3994140a15a19ab4c`. The worktree was clean when the audit identities were recorded. This review does not pass the original Blender receiving gate.

## What was verified

The audit independently fetched the six retained upstream source files and two license files at Blender commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`. Every fetched file equals the corresponding retained bytes, size and SHA-256. Two additional pinned headers establish the vector unroll macros and the `numbers::pi` definition used by the scalar adapters. Complete retrieval receipts are retained in `upstream-fetch/`.

Without invoking the implementation's extractor, the audit extracted functions from each signature through its first unindented closing brace. The two short-conversion functions, approximate inverse cosine, complete selected encoder and complete selected decoder each appear byte for byte in `codec_exact.inc` and match all declared function hashes. Five small C support bodies—zero check, scalar/vector comparisons, vector multiply and multiply/add—also match the pinned source exactly.

The C++ adapters preserve the relevant operation sequence. Dot product starts with component zero and then accumulates components one and two. Normalization computes the squared dot, compares with `1e-35f`, takes the float square root, and divides each component by that length. It does not substitute the separate C helper's reciprocal-multiply route. The normalization routine's unused local length reset has no observable return-value effect in this adapter.

The selected code retains the float expression `1.0f-1e-4f` for the azimuth shortcut, the inclusive `1e-4f` per-component near-auto comparison, and `floorf(val*32767.0f+0.5f)` for asymmetric short rounding. The wrapper uses actual binary32 operations, disables fast-math and contraction, verifies round-to-nearest, and reports the observed evaluation mode and subnormal behavior. These settings describe this scalar build; they do not attest a Blender binary or every platform's math library.

## Preconditions, reporting and measurements

The harness supplies explicit normal frames. Finite basis, unit-length, orthogonality, handedness and angle-range checks are declared experiment preconditions. They are not proof that every admitted frame arises from Blender fan construction.

Required operation fields are explicit. Decoder short values must be exact non-boolean JSON integers in the full signed-short domain. Strict mode applies the pinned C++ normalization path; unit mode deliberately bypasses it. Zero-sentinel and invalid-angle-range modes are separately named diagnostics. The invalid-angle-range mode exercises the actual decoder fallback with an otherwise admissible supplied frame; no invalid-frame encoder division or native invalid-fan replay is claimed.

The final reporting correction is satisfactory. It distinguishes execution of the standalone process, encoder, decoder, input normalization and helper functions. A rejected frame can run the process without entering either codec function. A normalization-collapse refusal explicitly records that normalization occurred first. Historical implementation smoke files retain earlier reporting revisions and must not substitute for observations bound to this final source.

Round-trip component error is measured against `normalizedInput`, the actual float32 vector passed to the encoder. `normalInputFloat32` separately records the parsed original vector. For example, strict input `[2,3,4]` is intentionally normalized before encoding, so its reported small codec error does not claim preservation of the raw vector's magnitude. Angle calculations use normalized double-precision directions and the cross/dot `atan2` formula. Zero-sentinel rows have no meaningful direction angle and should not contribute to preservation-relevant error claims. Finite headline errors must retain their exact input/mode/frame conditions.

## Limits and integration condition

The code and documentation correctly distinguish this experiment from native fan construction, sharp-edge processing, corner averaging, importer execution and the C211 binary. The prior observations contain no native fan frames or encoded short pairs. This audit supplies none and cannot close the source-lineage limitation. Finite observations establish neither a universal error bound nor a replacement tolerance. The original `2e-6` receiving requirement and failed result remain unchanged.

Original notices, derived-source SPDX notices and pinned license texts are present and correctly bound. This is a record of the attribution evidence supplied with these files, not a general legal assessment.

No Blender process ran. The independent 212-case numerical cohort was not repeated by this reviewer. Integration still needs that cohort's final-source-bound results and exact byte equality between the reviewed implementation and the published source.

## Evidence

- `SOURCE-REVIEW.json`: 13 explicit review checks, verdict, exact commit/tree, limitations and principal source hashes.
- `SOURCE-AUDIT-BINDINGS.json`: every reviewed file's hash, independently verified upstream identities, five exact selected function hashes and five exact support-function hashes.
- `upstream-fetch/`: primary-source retrieval receipts for eight retained files and two additional adapter references.

Principal implementation hashes are `530362787d0112a1a227ee24460e226142a78603cafa25ab4df1d02372827f90` for `codec_probe.cpp`, `fc2b5deb6cf1272ea132671ce33c296f09ef1fa977aa44fe2737d6c56867832b` for `codec_exact.inc`, and `ddd85bf0c7b5732a99b7893746e3b1178b86888dfdb3bb0cbbf9d33b79ae4033` for `run_probe.py`.
