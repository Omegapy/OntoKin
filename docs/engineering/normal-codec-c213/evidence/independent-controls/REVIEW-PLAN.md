# C213 independent boundary controls

The 212-case corpus and its expectations were sealed in `PREDECLARATION.json` before the reviewer read the new C213 implementation or executed its harness. The corpus comes from the pinned upstream codec and its scalar/vector helpers, rather than the retained C211 sphere measurements. `CHECKER-DECLARATION.json` separately binds the first independent checker before implementation inspection; any output-schema adaptations must be recorded without rewriting the sealed expectations.

## Independent expectations

The canonical frame is exact: automatic normal `(0,0,1)`, reference `(1,0,0)` and orthogonal direction `(0,1,0)`. The other two bases test rotation and oblique coordinates. Every accepted frame is supplied explicitly; these cases do not establish that Blender's mesh fan constructor reaches each frame or range.

The codec's near-auto comparison uses `<= 1e-4` independently on all three components. The corpus includes both signs at the adjacent float32 values below, at and above the threshold, and a two-component input. The expected NOP is a reported upstream shortcut. A strict input rejection is a separate harness action.

The azimuth branch compares a projected cosine with float32 `1 - 1e-4`. Independent cases cover adjacent float32 cosines and both azimuth signs. For a canonical polar angle of pi/2 and azimuth 0.01 radians, the source condition predicts zero encoded azimuth: the output loses a component close to 0.01, despite the small input angle. This predicted counterexample is conditional on its supplied frame. It is neither a reconstruction of C211 nor a proposed receiving tolerance.

Signed short cases cover both signs around six mathematical half-step locations, with the input and each arithmetic operation explicitly rounded to float32. The test expectation follows `floor(float32(float32(value * 32767) + 0.5))`, which does not implement ties away from zero for negative values. The decoded signed grid is compared to an independent double-precision spherical calculation using the supplied float32 frame constants.

Normalization includes ordinary scaled vectors, zero, sub-threshold length and finite values whose squared float32 length overflows. Strict roundtrip refusal is distinguished from the raw normalization diagnostic and explicit zero sentinel. Invalid frames cover range, unit length, orthogonality, handedness, degeneracy and nonfinite values. The decoder's upstream zero-range fallback is exercised only through its explicit diagnostic mode; unsafe invalid-frame encoding is not attempted.

The sharp-boundary cases are distinct per-corner directions, processed separately. They check that this harness does not silently average them together. They do not test Blender's topology-dependent sharp-edge detection, shared-fan averaging or fan assignment.

## Review boundary

Acceptance requires exact source bindings and inspection of the selected arithmetic route, complete case identity accounting, frozen expectation preservation, meaningful refusal reasons and independently recomputed numerical observations. The decoder-reference allowance and approximate-acos comparison are checks on this local experiment; neither changes C211's `2e-6` receiving promise. A successful investigation can report cases that fail that original promise.

No Blender process, import, render, save/reopen or product-regression run belongs to this review. The unknown C211 binary lineage and absent native fan frames/short pairs remain unresolved.
