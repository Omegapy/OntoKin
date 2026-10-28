# C041 P16 rounding-cache review

Reviewer: `/root/p16_hotspot_review`.

Decision: **NO-GO for unconditional bypass of `upper_binary64` memoization.** This is a narrow source-only decision. It does not exclude a different, positively bounded eligibility rule.

## Source binding

Reviewed C040 publication `0fab8a2fe00047ebf3f8778721d0a77b7a1d5420`, with runtime source equal to the held C038/C035 execution candidate. The inspected local files matched these exact Git blobs:

- `ontokin/reach_export.py`: `f8a240dd033ebf5e4f2ce83bf46e3ae379b9b27a`.
- `ontokin/reach_numeric.py`: `c552b085106a02b612a24a4884d8096f9733ee40`.

Line references below refer to those blobs. The historical counts come from `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-038-analysis.json`, at `neutrality.post_state.reach_work.counts`. They are retained C038 observations, not fresh measurements.

## Concrete rejected candidate

Replace the final `_reuse(...)` call in `upper_binary64` with its existing `calculate()` function. Preserve the original input decode, negative/zero checks, float conversion, exact comparison, outward `nextafter`, and finite-result rejection. Source: `reach_export.py:290-313`; ordinary reuse: `reach_export.py:59-74`; native lookup and insertion: `reach_numeric.py:120-175`.

The numerical calculation is retained, but an unconditional change has an unfavorable generic workload. Consider `n` successful calls with native `Fraction(1)`, an initially empty native LRU, stable full operand limit, sufficient work/time, and no callbacks or observers. This is a source-level witness, not an executed test or source-fixture modification.

The first old call costs six charges: initial decode, lookup, conversion-return, converted-result decode, comparison, and insertion. Each later hit costs three: initial decode, lookup, and promotion. The direct candidate costs four per call: initial decode, conversion-return, converted-result decode, and comparison. No `nextafter` or eviction occurs.

```text
old(n)    = 6 + 3(n - 1) = 3n + 3
direct(n) = 4n
direct(n) - old(n) = n - 3
```

At `n=4`, the old route uses 15 charges and direct recalculation uses 16. The unconditional candidate therefore has no universally positive charged bound even on simple native inputs.

## P16 local arithmetic remains conditional

C038 records 261 `recording_bound_float_return` operations. Under the retained native flow these are completed nonzero misses in this helper. The source permits at most 463 helper calls for its 21 certificate groups:

```text
21 groups * (13 primitive + 2 destination + 4 derived + 2 total calls)
+ 21 group time-shift calls + 1 report time-shift call = 463
```

The call sites are `reach_export.py:1070-1119`, `1312`, and `1715`. Therefore, on the same original invocation and cache-hit trace, former hits number at most `463 - 261 = 202`; zero fast paths can reduce that count. Every removed miss saves at least lookup plus insertion, or two charges. Recalculating an old hit costs at most two more charges than its lookup/promotion pair. The resulting conditional local ledger is:

```text
removed bookkeeping >= 2 * 261 = 522
additional arithmetic <= 2 * 202 = 404
conditional local saving >= 118
```

This is **not** a complete P16 saving bound. It assumes the compared invocations and cache decisions remain those of the retained flow, omits new admission costs, and does not establish the effect of a changed shared cache on enclosing or downstream calculations. It predicts no P16 pass, timing improvement, completed tail, or release result.

## A fresh enclosing group does not prove unique inner values

The outer cache key at `reach_export.py:1307-1311` includes the complete `bound` object. Its `speed` field participates in that key. The inner `_certificate_quantities` calculation consumes `bound.angular_speed` and `bound.acceleration`; passing `bound.speed` into `rounded_bound` does not make it a consumed quantity, because `complete_interval_bounds` reads only that bound's angular speed and acceleration (`reach_export.py:1371-1402`). Consequently, different outer keys do not imply different rounded values. A "new certificate group" flag cannot establish that inner rounding results will be used only once.

## Remaining authority and cache obligations

1. Native lookup, promotion, insertion, and eviction contain charged callbacks, live operand-scope synchronization, generation checks, and exception behavior. Suppressing them requires an eligible route that preserves required custom-work, observer, reentrancy, domain, and original-error behavior. Such a route and its complete charged admission have not been established.
2. Removing upper-bound cache accesses changes shared LRU occupancy. An enclosing `certificate_group` hit suppresses the whole nested calculation; a miss executes it. The reference sequence is therefore adaptive. Fixed-reference-string LRU reasoning alone does not prove that all other request costs are nonincreasing.
3. Keeping the same cache occupancy through dummy entries, shadow bookkeeping, or another storage representation would still require charging the actual lookups, stores, promotions, copied values, and retirement. It cannot be credited as free preservation of the old cache state.
4. No high-volume source-private uniqueness or cache-disjoint eligibility class was proved. A last-use miss might avoid a single unused insertion, but that is not the proposed broad reduction and does not establish the required P16 bound.

## Scope and next action

No product request, recording, unit/regression test, runtime edit, fixture edit, cap change, failed-tail replay, GitHub write, or merge was performed by this reviewer. Original28 remains the historically reported 24/28. C035 remains held.

Do not implement the unconditional bypass from the 118-charge local estimate. Reserve an implementation only after a genuinely different eligibility rule has both a generic positive bound and a complete P16-specific ledger, including shared-cache and callback effects. Otherwise proceed to the separately authorized bottleneck investigation.

Signed: `/root/p16_hotspot_review`.
