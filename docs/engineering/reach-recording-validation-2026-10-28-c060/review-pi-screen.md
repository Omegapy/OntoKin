# C060 independent producer-pi screen and diagnostic implementation review

## Decision and scope

The saved P11 and L03 captures support a finite **NO-GO for isolated shortening of the producer's `atan(1/239)` recurrence as the sole way to complete these two original requests**. P11 performed no cold producer pi calculation. L03 performed exactly one cold producer pi calculation at precision 96. Removing even all 27 iterations of its 239-denominator loop could save at most 108 recurrence charges; the 24 wholly unvisited L03 keys alone require at least 144 `independent_key_pose` charges under the existing reader.

This screen holds the original returned dyadic pi endpoints, planned keys, geometry, other charged paths, cache behavior, callbacks, and independent validation algorithm fixed. It is not a rejection of broader pi algorithms, changes to other computations, or a combination of optimizations. It does not prove that any shorter series preserves the original dyadic endpoints. Eliminating every term is deliberately an overgenerous accounting bound, not a proposed numerically valid implementation.

The screen justifies selecting a larger structural target. It does not identify or approve a replacement implementation, weaken a cap, or establish release acceptance.

## Reviewed identity and evidence

The captures identify diagnostic commit `5170bb99bfb045c651e1aabb1ac5f24c9d2259dc`, tree `ed848bced2c9f8cf4027ffd278b6bf9e0be606e6`. Local Git identity matched those values during review. The input manifests disclose a shallow, partial checkout: 488 materialized tracked files out of 3,329, with 2,841 explicit omissions and `complete_checkout=false`. The capture manifests before and after each request are equal. This is not evidence of the stock whole-checkout harness or complete delivery corpus.

All evidence paths below are relative to `/workspace/scratch/3f450eca9f36/`. Source paths in the proof are relative to its `ontokin/` repository. This review read the actual saved JSON and GLB files, not a prior checkpoint's reported counts.

| Observation | P11 | L03 |
| --- | ---: | ---: |
| Shared operations after construction | 7,391 | 4,499 |
| Reach operations after construction | 668 | 266 |
| Both relevant source categories after construction | 0 | 0 |
| Shared operations at reader entry | 61,415 | 54,988 |
| Reach operations at reader entry | 54,692 | 50,755 |
| `source_series_recurrence` at reader entry | 144 | 198 |
| `source_horner_integer_product` at reader entry | 144 | 144 |
| Difference of those categories | 0 | 54 |
| `source_series_grid_guard` / `source_horner_argument_square` / `source_horner_unpack` | 12 / 12 / 12 | 12 / 12 / 12 |
| Retained keys in GLB and captured tracks | 52 | 178 |
| Geometry carriers | 20 | 6 |
| Completed key calls | 36 | 153 |
| Failed key index, zero based | 36 | 153 |
| Failed authored time | 36/25 | 244/89 |
| Final attempted shared count | 100,001 | 100,001 |
| Final Reach count | 93,277 | 95,767 |

Sources are `.evidence/c060-attempt001/{P11,L03}/capture/capture.json`, `capture/key-ledger.json`, and `control/{P11,L03}/request-result.json`. Both captures have one reader call, no observation errors, and all recorded identity checks true. The construction callback is the native `ConstructionBudget.tick`, its optional `construction_check` is null, and the source observer is null at reader entry and after the request. The recorded work limits remain 100,000 operations, 30,000 ms, 32,768 operand bits, and 256 cache entries.

Both requests reached `gltf.validate_export` after `_export_glb` completed scene construction and encoding. The producer stage marker calls all returned. A returned encoding marker alone would not establish completed encoding; the subsequent reader entry and retained complete GLB bytes establish that boundary here. The failures occur later in the independent reader. The bytes remain unvalidated failed-request input, not accepted export artifacts.

## Counter attribution proof

The complete runtime-source search finds exactly three charging sites for `source_series_recurrence`, all in `ontokin/reach_pose.py`:

1. `ReachPoseOps._pi`, line 658: one charge for each alternating-series iteration, in each of the 5 and 239 denominator calculations.
2. `_fraction_horner_sincos`, line 710: twelve charges per completed fallback evaluation because `_HORNER_TERMS` is 13.
3. `_packed_horner_sincos`, line 773: one recurrence charge paired with one `source_horner_integer_product` charge at line 776, twelve pairs per completed packed evaluation.

There is no other runtime charging site for `source_horner_integer_product`. The producer completed under the native unchanged limits, so the reader-entry snapshot is not a snapshot midway through one of these recurrences. No counter reset occurs on these paths. `ReachExecutionWork.charge` increments its category only after its external callback and resource checks return.

The two runtime callers of producer `_pi` are `sincos` and `spin_plan`; both draw precision from `reach_numeric.PRECISIONS = (96, 192, 384, 768, 1536)`. These are the producer precisions, not the different independent-reference precision sequence. A cold producer pi evaluation contributes twice `floor((precision + 15) / 4)` recurrence charges:

| Producer precision | Terms per denominator | Pi recurrence charges |
| ---: | ---: | ---: |
| 96 | 27 | 54 |
| 192 | 51 | 102 |
| 384 | 99 | 198 |
| 768 | 195 | 390 |
| 1536 | 387 | 774 |

Let `D` be `source_series_recurrence - source_horner_integer_product` at reader entry, `F` the number of completed fraction-Horner fallbacks, and `N_p` the number of cold pi evaluations at precision `p`. Then, for these completed native producer paths,

`D = 12 F + sum_p [2 floor((p + 15) / 4) N_p]`.

Every term is nonnegative. P11 has `D = 0`, so it has neither a cold pi evaluation nor a fraction-Horner fallback. L03 has `D = 54`: higher precision pi passes cost at least 102, two precision-96 passes cost 108, and 54 is not a multiple of 12. Consequently, L03 has exactly one precision-96 cold pi evaluation and no fraction-Horner fallback. The zero construction counts place these contributions after construction and before independent-reader entry.

The other observed Horner categories corroborate the result: each case has twelve grid admissions, twelve accepted packed arguments, twelve unpack operations, and 144 packed products. The category `series_recurrence` without the `source_` prefix is not part of this attribution and must not be substituted for it.

## Saving bound for the isolated 239-denominator lever

Each existing `_pi` loop iteration performs exactly four charged operations: one `source_series_recurrence`, one exact division, one exact addition or subtraction, and one exact multiplication. `ReachPoseOps._op` delegates to `reach_numeric.exact`, which charges exactly once; its operand guards do not add work charges. For the one L03 precision-96 cold pass, replacing 27 iterations by `m` iterations therefore removes `4(27 - m)` loop charges, at most 108 for `m >= 0`.

The 5-denominator series and the 239-denominator setup, tail enclosure, endpoint comparison, final combination, projection, lookup, and insertion are outside that removed-loop allowance. A replacement proof or admission mechanism can add charges and reduce the net saving. This review does not assign it free work.

For a term-count-only edit using the same alternating-tail construction, the final `DyadicContext.point` calls also retain their nondyadic charging branch. At 27 terms, the two 5-denominator enclosure endpoints have reduced denominators divisible by powers of 5 with exponents 53 and 56. Any 239-denominator partial sum and tail with at most 27 terms has a denominator whose power of 5 is at most 2. Combining them with coefficients 16 and 4 cannot cancel the larger power of 5, so neither combined endpoint becomes a dyadic input. Thus the projection does not supply an overlooked direct-grid saving in this isolated edit.

Keeping the returned dyadic endpoints and the surrounding cache operations fixed also keeps the later numerical inputs and planned key/carrier sequence fixed. The 108 bound is a recurrence accounting screen. Changes to source-basis file/read accounting, metadata processing, other charged algorithms, validation, or cache behavior would need their own explicit analysis and are outside this isolated candidate.

P11 offers zero saving from this cold-pi recurrence lever because its producer never executes that work.

## L03 remaining-work lower bound

The L03 GLB JSON contains one animation with 12 channels and 12 samplers, six target carrier nodes, one common time accessor of count 178, and output accessor counts of 178. The capture ledger independently contains six translation/rotation tracks of length 178. Its key calls are the exact contiguous prefix with indices 0 through 153: 153 calls returned and index 153 raised. Thus indices 154 through 177 are wholly unvisited: `178 - 154 = 24` keys.

`reach_conformance._verify_certificates` calls `_key_comparisons` for the first key and every following retained key. `_key_comparisons`, line 1961, charges `independent_key_pose` once for each geometry carrier at the beginning of its first loop, before stationary comparisons or source-pose reuse can skip later work. With six carriers, the unvisited keys therefore require at least `24 * 6 = 144` additional charges. The observed count of 924 at the failing key's exit equals `154 * 6`, consistent with all six initial carrier admissions having run at index 153 before its later failure.

The original shared budget already admitted 100,000 operations before its next attempted tick raised. Even ignoring the rest of the interrupted key, the rejected operation, all between-key work, and final validation, the generous saving bound gives:

`100000 - 108 + 144 = 100036 > 100000`.

The native shared callback increments to 100,001 before raising, while the corresponding Reach category is not incremented. That rejected operation must not be fabricated as an extra recorded Reach charge. The lower bound above deliberately uses only the preceding 100,000 admitted operations and wholly unvisited-key admissions, so it does not rely on that bookkeeping difference.

Therefore the isolated recurrence shortening cannot close L03 under the existing cap and the stated unchanged-output/unchanged-path conditions. The actual missing work is larger than this lower bound.

## Resolved diagnostic implementation review

The final reviewed driver hashes are:

| File | SHA-256 |
| --- | --- |
| `tools/probe_reach_recording_work.py` | `38bcfd5ba46f658b7b5686c93f91a732fec9d4b19e76a6004acf7a7d499f6634` |
| `tools/capture_reach_recording_work.py` | `916718f2056b076b94ae9c1423a3bc19718f2425bccd6196537044b4657c996a` |

The actual revised probe resolved all four prior findings:

- One `read_bounded` result supplies each materialized file's byte count, SHA-256, and Git blob SHA-1.
- Failed-reader byte recovery requires the exact `gltf._export_glb` frame and an actual `gltf.validate_export` frame in the traceback.
- Initial and final input-audit failures write a durable diagnostic-failure report with `inputs_stable=false`; final-audit failures preserve completed request rows.
- Loaded module descriptors must match the frozen input manifest by path, byte count, and SHA-256.

The structured exception graph is collected after product execution through the shared probe and therefore applies to control and capture. The reviewed original request sequence and arguments remain intact. The three capture wrappers forward the original calls and restore the original functions in cleanup. Passive boundary snapshots do not call charged native arithmetic. The implementation review found no remaining blocker to the four bounded requests; it did not prospectively certify neutrality or a successful product result.

For this subsequent evidence review, control and capture agree in both cases on full work records, operation counts, work and construction limits, after-construction records, source-unit descriptors, and request options. Their retained reader-input bytes are identical. Their complete structured exception graphs agree after removing precisely the two expected capture wrapper frames, `capture_validate_export` and `capture_key_comparisons`; no product frame was removed. Both product arms failed on the original operation cap.

## Evidence checksums and review limits

| Evidence path under `.evidence/c060-attempt001/` | SHA-256 |
| --- | --- |
| `P11/capture/capture.json` | `54bb2edb4f24cbb167581d1b4014158462ad52db00ad02817f67490de079138a` |
| `P11/capture/key-ledger.json` | `4a5db4373798d8258ebfb49760974e5cf4f2bf9043682c75620478f53da146b6` |
| `P11/control/P11/request-result.json` | `0a8a4788479e09f1895fea90484aa5c09be90027b91f3cb793f2b4dbfb3a85cc` |
| `L03/capture/capture.json` | `8c120493b2b6a500928cf9f213e5f11e60bb49c7e174efbc48db4288e3fe22b7` |
| `L03/capture/key-ledger.json` | `41f48beba743c118fcaa4cd9ed5a3d223749f52d2065e375473243d299c4d50a` |
| `L03/control/L03/request-result.json` | `87965310b3e975c787a328d5d9c01615bf20d84540a3f52228704bc9b5e0d331` |
| `P11/capture/unvalidated-reader-input.glb` | `4ea1d4d90fd1942aa8a793892dfe1a72f7ae047b5725f9750ab5c7b330477c3d` |
| `L03/capture/unvalidated-reader-input.glb` | `12f78939fd6fb5e8a6dace1ed4469c4da90ae3e56a8f0e21dd2e73947ae567e5` |

The current source bytes and lengths for `reach_pose.py`, `reach_numeric.py`, `reach_conformance.py`, `construction.py`, `gltf.py`, and both diagnostic tools match the captured manifests. The relevant source SHA-256 values are `e1ec6bd98184900a5637b05fce1c0066820fa9b9f159c89f57ea7c1364167013` for `reach_pose.py`, `1bd7da1d6721369d8662ba314e08c8704abfd24a4d9707113da4ac296d92ea0a` for `reach_numeric.py`, and `b4c657eac72186203960b18738f65f08e700f52dffa11c1364c6b4609c59a81a` for `reach_conformance.py`.

This reviewer performed source inspection and standard-library analysis of existing artifacts only. No OntoKin module was imported or executed, and no product request, test, Agent, SQLite operation, archive extraction, or background process was started. The only file written was this review, as requested. The GLB checks here covered header/declared length, JSON accessor and channel counts, and equality of the three retained copies per case. They are not a substitute for the separate complete independent byte/clock/certificate census. No new runtime pi candidate was implemented or evaluated, and no broader release, full-corpus, or performance claim is made.
