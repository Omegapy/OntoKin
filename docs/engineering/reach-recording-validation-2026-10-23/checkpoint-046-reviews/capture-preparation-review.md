# C046 independent review of the prepared boundary capture

Reviewer: `/root/source_review`. Date: October 26, 2026 UTC.

**Disposition: source preparation reviewed, with the identified serialization and identity omissions corrected. The driver remains unexecuted and unvalidated for current-request neutrality. No product execution or implementation is authorized by this review.**

This review covers the complete prepared driver, its changes from the exact retained C033 driver, and the correction diff against the preserved C046 v001 preparation. It uses only source text, AST parsing and file hashes. It does not import either driver or any OntoKin module, execute extracted code, perform a numerical request, or extract an archive.

## 1. Exact reviewed inputs

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-046-capture.py` | 36,992 | `d5803f0249aae67047d4780a1a1f0d19c67663a5a1cc24b00c160d54d7e61276` |
| `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-046-audit.py` | 13,596 | `6990766b8cce52132d1bc8c729a61229fc28ed08adbf11bae39876cd07014b91` |

The product-source comparison is separately bound in `source-comparison.json` and `source-review.md`: the current 65 runtime modules match the held C035 inventory. Historical C033 differs only in `reach_reference.py` and `reach_reference_center.py`; the plan module and all coefficient-series, direct-seed, cursor-retirement and ordinary cache helpers relevant to the refusal retain their reviewed bodies. The capture adds no runtime-source edit.

## 2. Observation boundary and authority

The driver installs only the existing C033 wrapper pair, `gltf.validate_export` and `reach_conformance._key_comparisons`. Each wrapper forwards the original positional and keyword objects to its saved original function exactly once. The native arithmetic, plan, guard, polynomial and cursor helpers remain unwrapped. The outer `finally` restores both installed wrappers. Dispatch receipts compare the saved selected method/function identities after the request, and per-key receipts compare arguments, work/source owners, callback identities, observers and the reader-cache owner.

This choice matters for current C035 source. `_product_native` and other native gates inspect trace/profile absence and captured dispatch/function identities. Installing trace/profile hooks or wrapping arithmetic could change the native branch being diagnosed. The reviewed driver has no such hook installer. Source preparation cannot prove that a later execution remains equivalent: it creates additional objects, reads fields and consumes elapsed time inside the original capped request. A future result must establish the applicable receipts and be compared with an independent fresh stock request.

The current product observer, `_recording_product_after_tick`, is now saved strongly at key entry and compared with `is` at exit, in addition to `_recording_after_tick` and the work observer. The reader dictionary is saved strongly within the wrapper and checked with `source.cache is saved["source_cache"]`. These are valid same-call owner receipts. Ordinary integer `id()` labels remain explicitly limited to instantaneous diagnostic labels; they cannot prove cross-boundary retention, cross-run equality, or the lifetime of a retired value.

The observer does not invoke a charged arithmetic helper, cache lookup/promotion, source getter, pose calculation, native admission gate or `repr` to obtain its new cache data. It iterates the native dictionary in its existing insertion order and copies whitelisted exact native fields. Scalar arithmetic used to describe native integer widths belongs to the observer and is not passed back into the product calculation.

## 3. Complete-key codec corrections

The initial full-cache extension could not encode keys that the retained historical request actually contains. The final version corrects the following omissions:

| Native key shape | Source factory | Final encoding |
| --- | --- | --- |
| `PoseEnclosure` | `compose`, `inverse`, `world_target` in `reach_reference.py` | Four fixed fields: position, orientation, velocity, omega; recursively copied native interval leaves |
| `RecordingPoseEnclosure` | Recording composition paths | Two fixed fields: position and orientation |
| `_SourceBound` | `_source_basis.compose`, key `source_bound_compose` | All 18 declared fields, including the three integer operation counters |
| `frozenset[str]` | `_incoming`, key `incoming_graph` | Explicit `frozenset_strings` wrapper after exact native string and length checks; deterministic sorted string order |

Other reviewed reader-key factories use native primitive tuples, Fractions, Intervals, strings, integers, booleans, optional `None` and opaque `object` tokens already handled by the codec. The fixed whitelist avoids generic dataclass traversal and arbitrary property/getter execution. No full numerical cache value is recursively copied merely because it resides in the dictionary.

The prepared source-plan observation also matches current schema. `_Plan.centered` is initially `None`, can be the disabled sentinel `False`, or is a tuple of `_CenteredNode` recipes. The final codec handles all three. It copies all seven current recipe fields: `vector`, `position_radius`, `identity_offset`, `coefficient_source`, `product_pair`, `product_owner` and `seal`. The body and node fields selected for failure diagnostics use the already supported native `_RecordingBodyRate` and `_Node` shapes; callable source getters and receipt readers are deliberately not executed or serialized.

This is a review of the relevant source factory closure, not a claim that the unexecuted current L03 request has met every diagnostic bound. If it encounters an unsupported type or excess depth, size or integer width, `observe` records the defect and returns no successful observation. The stock original call still runs or its original exception is re-raised. Such a result must remain an invalid capture.

## 4. What the observations establish

The ordered cache rows record exact serialized native key fields and dictionary order at key entry, key exit and selected failure-frame inspection. A `series_coefficients` value contributes its native immutable tuple shape, coefficient count and integer widths; the complete coefficient integer payload is not recorded. Width equality therefore cannot establish value equality, and object IDs cannot fill that gap.

Selected failure frames include the current coefficient key, whether a `cached` local exists and its value when supported, exponent, degree, loop index, factorials, construction values and integer operation operands. A later actual traceback can discriminate a refusal before lookup, during lookup, during coefficient construction or during publication. For example, the retained current C035 trace already reaches the coefficient-construction division after lookup returned `None`; it does not supply the missing actual current key/index/time or previous cursor state. These historical local values must not be inserted into a new result by assumption.

The driver explicitly reports `boundary_only: true` and leaves intra-key lookup/publication/eviction events `null`. Comparing boundary order or occupancy does not recover a complete mutation chronology. The separately reviewed C033 no-capacity-eviction inference needs its full source/native-callback/cursor-continuity argument and applies only from historical key 1 entry to key 153's pre-cleanup wrapper exit. The new boundary format does not broaden that theorem automatically.

## 5. Bounds and post-request publication

The final preparation separates ordered snapshots into bounded files after the original product request. The inherited ledger holds hashed file receipts instead of all expanded ordered-cache bodies. This removes the initial design's avoidable multiplication of full cache payloads inside the one 64 MiB ledger limit. Each snapshot, ledger and failure-locals JSON publication reports success with byte count and SHA-256, or records a post-request serialization error. Observation errors prevent `captured_failed_request` status and preserve the stock request's actual failed result.

The driver still has deliberate diagnostic limits, including 256 reader entries, 16,384 recursively visited nodes across all keys of one ordered snapshot, depth 24, 32,768 integer bits and 64 MiB per JSON file. Their sufficiency for a current capture has not been measured or established by this review. Excess is a capture failure, never truncation or permission to increase product budgets. The later run must retain an adverse result rather than silently repeat with altered limits.

Likewise, the separate-file design does not prove an elapsed or memory-cost bound for all in-memory observations. Expanded key copying can materially affect the original 30-second request limit. No equality of charged operations can alone prove elapsed neutrality. Filesystem failure can still prevent final diagnostic delivery; the earlier stock outputs must remain available and unmodified in that case.

## 6. Source identity and refusal handling

Before importing OntoKin, the driver requires exact expected Git commit, tree and a clean tracked/untracked status, plus a fresh output path outside the repository. It narrows the case selection to original L03 and calls the unchanged stock builder with the original `fps=1.0`. It does not alter work, operand, cache, sample or construction limits. The observed original error object is re-raised through the key and reader wrappers; no tail continuation or replacement numerical attempt appears in the preparation.

The output distinguishes diagnostic capture status from stock product-request status. A successful diagnostic of the expected failed request remains `captured_failed_request`, with `accepted_artifact` and `release_acceptance` false, and the wrapper preserves the failed builder exit convention. The copied unvalidated GLB is labelled as unvalidated reader input. No output converts partial keys or pending cursors into accepted release evidence.

## 7. Static audit review and later execution gate

The companion audit uses standard-library JSON, source/AST, file-size and hash reads over the already restored evidence. It has no OntoKin imports, numerical replay or archive extraction. Its historical category/cursor checks are boundary checks; the output correctly says that a no-eviction theorem needs a separate source proof. Its AST check for absent trace/profile/monitor installers is a useful narrow assertion, not a comprehensive proof of runtime neutrality. Its retained-trace normalization is appropriate only with the independently reviewed exact known trace bodies; a future comparison should explicitly allow only the two approved wrapper differences.

The next separately scoped execution gate should bind the final committed driver and complete immutable source/input closure, use fresh original stock and captured L03 requests under an active exclusive window, and compare actual full options, source metadata, failures/diagnostics, whole count maps, approved normalized traces, unvalidated reader payloads and owner/callback receipts. Retain the existing budgets and all adverse results. The observed key/time/cursor and coefficient-local facts become current evidence only if that capture is complete and the required comparison passes.

No product request, candidate polynomial, modified cursor rule, cache extension, benchmark or test was executed for this independent review. No optimization is selected by it.
