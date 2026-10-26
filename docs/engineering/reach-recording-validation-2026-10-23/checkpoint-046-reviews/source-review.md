# C046 independent source and authority review

Reviewer: `/root/source_review`. Date: October 26, 2026, America/Denver.

**Result: the retained current traceback establishes a direct-seed coefficient-construction refusal, but it does not establish the historical cursor locals or a profitable coefficient-retention change. Preserve the 64-update retirement rule and the original direct seed. A passive current-L03 boundary capture is an appropriate next diagnostic preparation. Tracing or profiling the current request is not neutral by construction.**

This review reads source text, Python ASTs and retained JSON. It executes no OntoKin module, archived driver, source request, pose calculation, candidate polynomial, test or benchmark. It performs no archive extraction or remote mutation. Root owns C046 under Issue #26 comment 6424530160.

## 1. Exact source comparison

Historical source was fetched independently at actual C033 execution source `a7af3ee6ad0a22869b3b26fc45ad4f42f0191c41`. Its three file payloads match their Git blob hashes. Current source is the C045 final `a5bb1e674e4ae3eb1d77e83b63f7a809eacf0bd0`; root separately binds the complete current runtime to held C035.

| Module | Historical Git blob | Current Git blob |
| --- | --- | --- |
| `ontokin/reach_reference_center.py` | `499db559592c0846ecefb24e369515dab18da1ac` | `e1017c79786066e263bdc7877e318003cb61bbc0` |
| `ontokin/reach_reference.py` | `d751b2a49d6da41f61d1a92e2d32eadf507e5c7e` | `0e98ba4c2ba0c49dbf9672ecb1c0f0fd50079dbb` |
| `ontokin/reach_reference_plan.py` | `8a797f3805d29da637a01c32359492315a9e95bc` | `8a797f3805d29da637a01c32359492315a9e95bc` |

The companion `source-comparison.json` records whole-file SHA-256 values, symbol locations, complete function-body SHA-256 values, AST comparisons and raw body equality. Center has 26 unchanged common function ASTs and seven changed common functions; reference has 157 unchanged functions and two changed functions. All 30 functions in the plan module and the whole plan file are unchanged.

The complete bodies of `_orientation`, `_seed`, `guard_cursor`, `_Guard.original`, `_Guard.lookup`, `_Guard.remember`, all `_series_*` functions, arithmetic lookup/remember, the direct root/attachment/coordinate/hinge reconstruction, `_PoseArithmetic.hinge`, pending publication and source-batch cleanup are byte-identical. This is stronger than matching the final failing line.

The enclosing execution is nevertheless different. C035 changes center preparation/evaluation, `_Guard.__init__`/`current`, `_coefficients`/`_offset` and adds the product session. In reference, `_Arithmetic.__init__` and `tick` acquire the product observer. Therefore equality of unchanged inner functions and final counters does not transfer complete current cache chronology, local values, callback ownership or timings from C033.

## 2. Retirement and direct reconstruction

Current `_orientation` in `reach_reference_center.py` lines 536–598 first obtains the actual previous cursor from the existing reader cache and admits its shape, integer seal, operands and current owners. Advancement requires the same source witness, axis and rate, a strictly increasing clock and `previous.steps < 64`. The original increment magnitude/domain and direct-fallback checks remain additional requirements.

When advancement is unavailable, line 590 calls `guard.original(body.direct, clock)` before `_seed`. A cursor with 64 updates is not a new zero-step seed; the current direct calculation must complete before a replacement zero-step cursor can exist. `_seed` lines 508–527 checks the actual independent interval cells, axis sparsity, native 128-bit lattice and summed width at most `2^-112`. It selects lower endpoints with an honest radius. The centered proof's `2^-104` accumulated radius is derived for at most 64 updates; increasing that limit is outside this task.

The direct hinge recipe in `reach_reference.py` computes its current local ideal affine coordinate, the independent hinge quaternion, the parent's context-free direct quaternion and the original ordered Hamilton/fixed-attachment composition. It does not obtain a fresh seed from a preceding approximate center or a producer pose. In a forearm seed, local hinge work precedes recursive parent work. A failure in the local series can therefore prevent that invocation from reaching the parent reconstruction.

`_Guard.original` installs and restores the original readmission observer around the direct call. It preserves original reference failures through `_OriginalFailure` and preserves external callback exceptions. A later broader domain cannot turn that failed original calculation into a successful retry. The cursor reaches `pending.values` only after its full seed/update and guard complete. `_PendingCursors.publish` runs after the complete plan and batch owners, current domain and cursor ledger are admitted; an incomplete forearm seed publishes neither that cursor nor the already staged new upper cursor.

## 3. Two separate caches and two different coefficient families

The Taylor coefficients at the refusal use `ReachReference.a.cache`, a native insertion-ordered `dict` with fixed `MAX_CACHE = 256`. They do not use `ReachExecutionWork._cache`, the separate production work `OrderedDict`. The retained work report's 256 entries cannot establish reader-cache occupancy. The historical boundary reader snapshots range from 112 to 165 entries.

`_Arithmetic._series_coefficients` lines 471–493 uses the exact key `("series_coefficients", operand_limit, exponent, degree)`. `_series_factorials` has its own `("series_factorials", operand_limit, last)` key. Both share the existing reader cache with other independent arithmetic and cursors. They are distinct from center `_coefficients`, which caches raw Hamilton projection coefficients for a source-centered offset.

Series lookup charges before domain synchronization and dictionary access. A non-`None` return takes the original warm return; otherwise the original construction runs. Publication occurs only after the whole immutable coefficient tuple, denominator and lane are complete. A failure during construction publishes no partial coefficient result. Lookup promotion, publication, capacity eviction and operand-cap clearing retain their original behavior. A helper that fails before dictionary access has no observed hit or miss; reaching the coefficient loop, as the retained L03 failures do, establishes that the lookup returned `None`.

The current series proof preserves the independent midpoint, interval half-width, first strict alternating-tail stopping degree, exact two-lane polynomial, final error and outward grids. The exponent comes from the actual reduced dyadic midpoint denominator; the degree comes from the actual original tail test. Repeated seeds or similar clocks do not prove equal coefficient keys. Reusing a tuple under a different key, moving seeding, changing degree, borrowing producer coefficients, or retaining a second numerical cache would each require a separate proof and complete charged bound.

For the historical native exponent 129 and degree 14, the source construction contains 59 integer-operation sites: two initial shifts, fourteen divisions, fourteen coefficient shifts, fifteen packed additions and fourteen packed multiplications. Including lookup and successful publication gives 61 charges for the helper's complete stable-domain miss route, versus one for a valid existing hit. The resulting 60-charge gross difference is a source-derived counterfactual, not measured candidate saving. The historical refusal occurs before index-7 division executes, after 29 construction operations. Neither the remainder of that helper nor the complete failed request was executed. No complete cost or candidate bound is inferred.

## 4. What the retained current result establishes

Both C035 `execution/complete-p11-l03-002/L03/request-result.json` and `execution/original28-002/L03/request-result.json` retain this current traceback chain:

`_key_comparisons` → centered `evaluate` → `_orientation` direct branch → `_Guard.original` → hinge-body local direct recipe → `_PoseArithmetic.hinge` → `sincos` → `_series_sincos` → `_series_dyadic` → `_series_coefficients` coefficient-division expression → `_series_integer.tick` → shared budget refusal.

That current chain and the identical function bodies support a narrow conclusion: the direct branch was taken, the coefficient lookup completed with `None`, and the request refused at a coefficient-construction division's charge before that integer division executed. It is not a pre-membership refusal. Both requests remain failed at 100,001 shared and 95,767 admitted reach operations.

The current reports do not retain the exact key index/time, selected frame, previous cursor steps/witness, exponent, degree, coefficient-loop index, exact key tuple or ordered reader-cache state. The C033 values 153, `244/89`, forearm, 64, 129, 14 and 7 remain historical observations until a current capture binds them. The historical and current complete count maps may agree without supplying those missing locals. Adverse C035 diagnostic timing remains held evidence.

## 5. Historical cache-lifetime bound and its scope

The raw C033 capture records cache category histograms and centered cursor snapshots, not complete coefficient keys or individual cache mutations. Histograms alone are not an eviction history. A bounded source-and-data inference is nevertheless available from **key 1 entry through key 153's pre-cleanup exit**:

1. The exact native request uses `ConstructionBudget.tick` with `check=None`; the capture preserved native dispatch, owners, original observers, trace/profile absence and limits. The source provides no request-time assignment that changes the work operand cap or reader precision. Thus the cache-domain clear is unavailable on this observed native path.
2. `_key_comparisons` invokes the centered reader at most once per key. An effectful center-domain rejection discards its tracked center entries and returns `None`. The following ordinary interval route cannot construct `_CenteredCursor` or `reference_centered_stationary_pose` values.
3. Every recorded exit from key 1 onward contains centered cursors, with the reviewed continuing history, including the pre-cleanup failed key. Consequently those keys did not take an effectful discard followed by ordinary fallback. The final enclosing source-batch failure cleanup occurs after the final key snapshot and is excluded.
4. The other historical reader-cache mutation sites are ordinary lookup promotion, replacement/insertion, inline Cartesian caching and pending cursor publication. Completed promotions/replacements preserve size; insertion increases it until capacity, where replacement preserves 256. Transient delete-and-reinsert promotion has no callback in between. With the clearing/discard routes excluded, reaching capacity would prevent a later boundary size below 256.
5. The recorded boundary sizes remain at most 165, starting at 122 on key 1 entry. Thus no capacity eviction occurs in this bounded interval. A coefficient key absent at the final completed lookup cannot have been retained at key 1 entry or successfully published earlier in this interval.

This is a source-bound inference under the recorded native provenance, not an observed mutation ledger. It does not cover source setup or key 0, whose snapshots have no centered entries, final rejection cleanup, a custom/reentrant callback domain or current C035 execution. It does not reveal the other coefficient key values or the order/count of intervening hits. It gives no evidence that pinning an allegedly evicted historical coefficient would fix this refusal.

## 6. Capture preparation and neutrality

Do not install a trace or profile hook and call it neutral. Current center `_product_native` explicitly rejects non-`None` `sys.gettrace()` or `sys.getprofile()` at line 849; the expected getter functions are identity-bound. Current conformance's term/native-field reuse gates also inspect trace/profile status. Wrapping arithmetic/guard methods can similarly violate the stored native-dispatch identities.

A later capture should preserve the C033 two-boundary approach: wrap only `gltf.validate_export` and `reach_conformance._key_comparisons`, forward the exact original argument/owner objects and call the original functions once. Extend passive snapshots to detached native reader-cache key fields in original order, exact coefficient-key/value metadata, reader caps, source-plan product-pair fields, all relevant cursors and pending values, and exact failure-frame locals. Never call a charged helper, cache lookup, source getter, native gate, equality on live foreign objects, `repr`, pose function or numerical oracle merely to observe it. Unsupported shapes must mark the observation invalid without changing the original product exception or request result.

Boundary snapshots can establish observed state differences and order at each boundary. They still do not reveal every lookup, promotion, temporary insertion or eviction inside one key. Any such event claim needs a separate mechanism and proof; it cannot be reconstructed by assuming a cache policy from final state. Record a refusal before membership distinctly from a completed lookup returning `None` and from a completed hit.

Before execution, independently review the exact driver, complete source closure, immutable input identities and diagnostic bounds. Use fresh original stock and captured L03 requests on the same source under an actually active exclusive window, original limits and fresh output paths. Compare full category maps, source/options/diagnostics, underlying trace frames after only approved wrappers, cache/owner/callback identities and actual original dispatch restoration. Capturing adds elapsed overhead; no elapsed neutrality follows from equal work counters. Preserve failed captures and stop at the original request failure, with no reset budget or tail continuation.

## 7. Recommendation and review limitations

No implementation is selected by this review. The direct-seed work is required by the existing proof. Historical cache retention does not support an eviction-repair hypothesis in the bounded reviewed interval; current exact inputs are still missing. Prepare the passive current boundary capture and use its actual results to choose a structural arithmetic or cache opportunity, with a complete charged bound and separate numerical/authority review.

The reviewer did not author root's evidence census, capture specification or final report. The raw source-comparison JSON and independently fetched historical sources accompany this review. Exploratory reads initially named two not-yet-recovered proof files and one nonexistent guessed proof filename, and one historical path was resolved against the wrong working directory; these produced read errors only. Correct files were subsequently read. No product result was obtained from those failed reads. The initial chat arithmetic count was corrected before this report: 59 construction charges, 61 full miss helper charges and a 60-charge gross counterfactual hit difference.
