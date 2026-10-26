# C041: higher-volume operation reduction review

Date: October 25, 2026, America/Denver. Decision: **source-only NO-GO for unconditional `upper_binary64` cache bypass; no runtime implementation selected.** A separate P23 constructor replacement also fails its existing result contract. These decisions apply to the specified designs, not every possible optimization.

## Source and ownership

This continues [HANDOFF-040](HANDOFF-040.md) on `work/reach06-operation-reduction-20261025-c041`. Owner: `interactive-reach06-operation-reduction-20261025-c041-35d1`. [Issue #26 scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6408443031) reserves only new C041 analysis and handoff records. No main integration lease was acquired and no shared status file was edited.

The observed C040 head is `0fab8a2fe00047ebf3f8778721d0a77b7a1d5420`, tree `bc1ef0444d6c284d4c78ed4bd626f396a935b54c`. Draft PR #37 holds C040, stacked on draft PR #36. PRs #27-37 were open drafts at startup. Main remains `2bb4588e121fcfe99b4d42c734b15b38362f3642`; its recorded documentation lease is released. The held runtime is `4ca73909f861fe4bef9694787473621c1d21c140`, and accepted reach runtime is `d2f0088c4f3c1f570630334804a5a8f78e0105ac`.

[Source binding](checkpoint-041-source-binding.json) identifies the inspected blobs. Root and reviewers matched current source against C040 rather than trusting a stale directory name. The local review copy contains all parent narrative documents and their documentation-check dependencies, but is not a complete execution checkout. An older scratch execution directory became unavailable during inspection; exact-commit reads supplied the additional needed source. No product ran from this partial copy.

The governing constraints remain the adopted [reach contract](../../language-design/planar-reach-v0.1/ADOPTION.md), [release contract](../../language-design/planar-reach-v0.1/release-contract.md), and [budget-counting section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse). Each new lookup, type/limit/claim check, copied logical value and storage action must be charged. An avoided calculation may save actual work; it cannot gain a fresh allowance or discard an independent predicate.

## 1. A different P16 target

The selected source review targets [upper_binary64](../../../ontokin/reach_export.py), which rounds a nonnegative rational certificate bound outward to binary64. This is producer certificate work, separate from C040's reader-axis ordering proof.

The current helper decodes and admits its input, rejects negative bounds, and handles exact zero directly under the full operand domain. For a remaining value, `_reuse` looks up a completed conversion in the existing bounded cache. A miss executes the original calculation, then inserts its result. That calculation converts to float, charges its return checkpoint, decodes the float, compares it exactly with the rational, applies `nextafter` if necessary, and rejects nonfinite output.

The concrete candidate replaces only the final `_reuse` call with `calculate()`. Its mathematical appeal is that recalculation keeps the original numeric predicate while avoiding cache bookkeeping. It does not use the rejected aggregate division counter or reader-axis receipt.

### Retained P16 local ledger

The unchanged [C038 analysis](checkpoint-038-analysis.json), at `neutrality.post_state.reach_work.counts`, contains:

| Completed category | Count |
| --- | ---: |
| `recording_certificate_group` | 21 |
| `recording_bound_float_return` | 261 |
| `recording_bound_nextafter` | 136 |

These are historical counts from the failed original P16 request. C041 did not reproduce or continue that request.

Each `_certificate_quantities` calculation has 21 conversion calls: 13 primitive quantities, two destination bounds, four derived bounds and two totals. At most one such calculation occurs per outer group visit. There is also one time-shift conversion per group and one report-wide conversion. Thus the original native source schedule has at most:

`T <= 21 * 21 + 21 + 1 = 463` conversion calls.

The 261 completed float-return charges identify calculations, which are native cache misses on that retained full-domain flow. If `M=261` and `h` is the number of old nonzero hits, then `h <= 463 - 261 = 202`. Exact-zero returns only lower this possible hit count.

On each old miss, bypass removes lookup and insertion, at least two charges. On each old hit, the old lookup and promotion cost two charges, whereas recalculation costs three or four; its increase is at most two. If `E` counts original evictions attributable to these conversions, a fixed successful invocation sequence therefore has:

`local saving >= 2*M - 2*h + E >= 118`, before any new eligibility or lifetime work.

No eviction saving is credited in the 118 bound. The number is a **conditional local source-flow bound**, not measured optimization performance or a whole-request saving. Changing the shared cache can change enclosing `certificate_group` hits and their nested invocation sequence. That effect was not proved neutral or adverse. It remains unclosed, so the bound cannot predict a complete P16 pass or the cost of its unvisited reader tail.

## 2. The unconditional candidate fails the generic bound

Consider `n` repeated calls with the exact positive value `Fraction(1)`, ordinary native work, full stable operand limits, an empty cache, no external callback or observer, and adequate remaining budgets. The value rounds exactly and needs no `nextafter`.

The first original call costs six charges: input decode, cache lookup, float-return checkpoint, result decode, exact comparison and insertion. Each later original call costs three: input decode, lookup and promotion. Direct recalculation costs four on every call.

| Route | Source-derived charge count |
| --- | ---: |
| Current cached helper | `3*n + 3` |
| Unconditional direct calculation | `4*n` |
| Saving | `3 - n` |

At four calls, the candidate increases work from **15 to 16**. It regresses for every `n > 3`, before any new admission overhead. One cache entry suffices, so this counterexample fits the existing cache limit. It is an algebraic source counterexample, not an executed benchmark or test.

Therefore unconditional bypass cannot meet HANDOFF-040's requirement for a positive worst-case bound on its admitted inputs. The positive P16 local ledger does not justify implementation.

Restricting the route to fresh outer certificate-group keys would not establish unique inner conversion inputs. The outer key includes `bound.speed`, while `_certificate_quantities` uses its angular-speed and acceleration fields rather than that speed field. Distinct group keys can still yield repeated bound values. An actual profitable subset needs a separate source proof and complete admission cost; a fixture name or historical miss ratio is not an eligibility rule.

## 3. Callback, domain and first-failure boundaries

The current helper accepts work protocols exposing `lookup` and `remember`; `_reuse` deliberately invokes them. A source counterexample is a foreign work object whose input guards succeed but whose `lookup` raises a particular sentinel exception. The current helper raises that same object before calculation. Unconditional bypass suppresses that call and can return normally or fail elsewhere. This changes original first-failure and exception identity. The example was not executed in C041.

Exact native work type alone would not authenticate instance-shadowed methods, function code/globals/defaults, the nested construction callback, current observers, mutable category/cache keys or reentrant mutations. Any selective native route needs a charged current-work/source/lifetime proof and literal fallback elsewhere. No such proof was completed for this candidate.

Native `lookup` already synchronizes operand limits and rechecks after promotion. This review does **not** allege that a legitimately warmed native cache entry survives a changed cap. Recalculation performs the original 1,075-bit result-decode guard on every former hit; its equivalence must be established under the actual native synchronization rules. Foreign lookup results or altered cache/work state do not automatically have that proof and must retain their original route.

The shared cache also stores enclosing and nested computations. A theorem about removing one key family from a fixed least-recently-used reference sequence does not by itself settle this adaptive calculation graph. The review neither proves a harmful total cache effect nor grants a beneficial one. It leaves complete request accounting unproved.

**Decision:** reject the specified unconditional bypass. A distinct restricted policy or conversion algorithm is not ruled out, but none is selected.

## 4. Other independently reviewed routes

### Fallback-only reader witness

The [witness review](checkpoint-041-reviews/reader-witness.md) considered a private flag set only on rational midpoint fallback. Such a flag avoids reading the aggregate division counter, but ordinary `ReachExecutionWork.charge` still performs `counts.get` and assignment. Foreign colliding keys can run equality callbacks there. A flag confined to the original helper cannot witness temporarily bypassed helper dispatch.

For the concrete repairs reviewed, full post-row key authentication returns to C040's inferred 266-entry cost against 205 removable comparisons. A new copied/checked row witness adds at least 206 occurrences. No complete cheap retirement mechanism was established. These are specific missing-authority/cost findings, not an impossibility theorem for every private witness.

### Producer phase-clock comparisons

The retained category `recording_captured_phase_clock=202` and the unchanged `begin_captured_phase` loop identify 404 producer comparison sites, separate from C040's reader comparisons. This offers a larger gross target. A new 206-value copy plus separate 206-value admission would already add at least 412 charges. An immutable-at-origin route could avoid that particular copy, but current phase-slice authority, operand guards and the total charged lifetime remain unproved. No implementation was selected from this lead.

### Independent P23 constant-pose route

The [P23/L03 review](checkpoint-041-reviews/p23-l03.md) examined constructing recording leaves with `make_recording`, which returns position and rotation without unused derivative fields. The ordinary `_constant_pose` cache key is `("reach_source_constant_pose", inverse, value.position, value.rotation)`. It has no recording namespace and is shared with full-source consumers.

Replacing only its constructor would store `RecordedTransform` where a later or reentrant full-source consumer expects `PoseValue`, including `exact_velocity`, `exact_omega` and `position_error_m`. **That unchanged-cache replacement is rejected for violating its result contract.** A separate private leaf or namespace would be a different design, with lost-hit, storage, callback and lifetime costs to establish.

Keeping `PoseValue` and both cache layers narrows the unconditional target to two default-zero vector admissions plus one stationarity check: three charges for each eligible call that actually misses the outer cache and reaches the constructor. If `m` is that count, setup is `A`, per-call checks are `h_i`, and added lifetime/storage/fallback work is `L`, positive saving requires:

`A + sum(h_i) + L < 3*m`.

Current P23's `m` is not established. Its 32-arm source topology is not a cache-miss count. C020's historical 192 calls and 1,934 inclusive operations retain their older source identity and cannot be treated as 192 cold constructors or 1,934 removable operations. The same-type candidate remains unselected. The held P23 static-transfer route and its adverse timing remain separate.

L03's 64-update retirement and direct reseed remain unchanged. Its captured coefficient refusal does not establish the complete reseed cost or remaining-request deficit. P11 component reuse remains separate.

## 5. Verification and next task

Three separately scoped agents reviewed producer arithmetic, adversarial authority and independent P23/L03 alternatives. Their actual conclusions are preserved in [the review index](checkpoint-041-reviews.json); agreement concerns the stated source-only findings, not implementation correctness, measured performance or release acceptance. The [machine-readable ledger](checkpoint-041-cost-ledger.json) separates retained counts, algebraic bounds, counterexamples and unproved terms.

The publication's validation record identifies the exact documentation candidate, parent-preservation check, local source identities, documentation command and observed result. No C041 product request, recording suite, runtime unit/regression test, numerical replay, timing cohort, browser/native destination check, paid/hosted job or merge is claimed. The documentation check is not a product test.

**Next bounded task: an independently owned P23 constant-pose call and consumer census from current source and retained evidence.** Establish cold versus warm calls only where the evidence supports them; write the noninverse and inverse scalar/guard/cache sequences separately. Enumerate full-source and reentrant consumers before proposing a private recording-only value. If retained evidence lacks current miss counts, record that exact gap rather than substituting historical totals or silently replaying a failed request. A runtime scope may be selected only after a complete positive charged bound and independent review. If the three-charge target is too small, close it promptly and select a larger distinct P23 sampler operation.

The [handoff](HANDOFF-041.md) supplies startup and ownership instructions. Latest complete original28 remains **24/28 (85.7%)**, with P11, P16, P23 and L03 capped. C035 remains held, including adverse L03 timing. All original caps, fixtures, oracles, tolerances, accepted runtime/main identities and outstanding Agent/destination/compatibility/hostile/inherited/release gates remain. Even 28/28 would not complete the reach release or the broader [GOAL](../../../GOAL.md).
