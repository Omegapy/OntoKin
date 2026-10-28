# C050 independent charged-cost and cache-lifetime review

Reviewer: `c050-cost-lifetime`. Date: October 27, 2026, America/Denver. Source: C049 commit `e828ee2d54b3c2a5a82bb332327fdce982a0f7f2`, tree `574c75e870d50aed5e5e96b34b454389074350fe`. C050 owns new review records on `work/reach06-factorial-cache-origin-20261027-c050-7a91`; [scope declaration](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6447560284). The [input and result record](result.json) identifies every inspected source by path, length, Git blob and SHA-256.

**Decision: no implementation GO.** A closed native writer graph could preserve the existing raw-tuple storage rule, but no complete admission and positive whole-request ledger have been established. The specific H2 repair that performs a newly charged authority check at every affine construction callback has a negative helper bound. This rejects that policy; it does not prove that every factorial-origin mechanism or coefficient optimization is impossible.

This reviewer did not author the root report or any runtime candidate. The work is source inspection and file-identity verification. No OntoKin import, candidate arithmetic replay, original request, runtime test, benchmark, archived driver or archive extraction ran. C047 observations below are inherited from its identified review, not freshly executed or re-audited capture evidence.

## 1. Exact accounting basis

[Adopted budget counting, section 3](../../../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse), as adopted by [ADOPTION.md](../../../../language-design/planar-reach-v0.1/ADOPTION.md), permits avoided real work but charges every new lookup, type/limit/claim check, copied logical value and output occurrence. Adding authority checks to an existing observer does not make those checks free. The [release contract](../../../../language-design/planar-reach-v0.1/release-contract.md) requires actual identified execution before accepting a runtime or release claim.

The source basis is [_Arithmetic](../../../../../ontokin/reach_reference.py): initialization and callback order at lines 72–117; cache methods at 346–368; integer, factorial and coefficient helpers at 435–491; and the dyadic caller at 493–573. The independently checked predecessor equations and width conditions are recorded in [C048](../../checkpoint-048-series-coefficient-feasibility.md) and [C049](../../checkpoint-049-factorial-origin-feasibility.md).

For genuine factorials, degree `D >= 1`, exponent `e >= 0` and an unchanged native operand domain, the fixed-domain counts are:

| Path | Original charged work | Hypothetical affine work before new authority costs |
| --- | ---: | ---: |
| Factorial hit | 1 | 1 plus actual new maintenance |
| Factorial cold miss, `last >= 1` | `last + 1` | Same original construction plus new mint/authority work |
| Cold `last = 73` | 74 | 74 plus additions |
| Coefficient full-key hit | 1 | Can remain 1 if new coefficient admission follows the original lookup miss |
| Complete coefficient miss | `4D + 5` | `3D + 6` |
| Degree 14 complete miss | 61 | 48 |
| Corresponding D14 pre-division prefix, including lookup | 30 | 26 |
| Degree 1 complete miss | 9 | 9 |
| Degree 2 complete miss | 13 | 12 |

The factorial miss has `last - 1` defining multiplications, one lookup and one publication. At native `bits=128`, the caller has `limit=36` and `last=73`. Its 74 original charges are already required baseline work; only added authority or minting belongs in the optimization's incremental cost. A genuine construction does not inherently require a new audit of every defining multiplication. Such an audit would be a separate proposed design.

The complete coefficient counts assume genuine factorials. Arbitrary injected values can alter the original `coefficient != 1` branches and therefore cannot inherit this formula. Degree 0 is outside the selected affine positive-degree domain and must retain its original generic behavior. Live-domain resets and effectful callbacks can introduce further work; they are not silently absorbed by these fixed-domain counts.

The 13-operation complete D14 opportunity and the four-operation corresponding-prefix opportunity cover different intervals. The prefix stops before the corresponding index-7 division. It neither includes publication nor establishes any unexecuted tail.

## 2. What raw tuples do and do not cost

The original caller assigns `factorials` at line 518 and still uses it at line 570. That local reference already keeps the returned tuple alive during this invocation, including if an intermediate callback removes its cache entry. Its existing lifetime is not a new persistent numerical slot.

Under a genuinely closed native writer graph, the storage argument is straightforward. A fresh owner starts with an empty dictionary. The authentic factory creates the original seeds and guarded recurrence, then publishes the exact immutable tuple. Hit promotion preserves the payload object. Other native key families do not manufacture a factorial tuple. Clear and eviction remove cache ownership without inventing values; a later genuine miss reconstructs normally. The active caller passes its already returned tuple without copying it.

That argument is conditional on the native writer, callback and dispatch closure. It does not authenticate arbitrary calls to the generic `remember` method, external dictionary writes, foreign map behavior or a replaced factory. A retained key, tuple shape, native integer elements, current method identity or recycled object ID is insufficient origin evidence.

The relevant lifetime operations are in [_Arithmetic cache methods](../../../../../ontokin/reach_reference.py), [_Guard lookup/remember and product replacement](../../../../../ontokin/reach_reference_center.py), and [_PendingCursors.publish and _SourceBatch discard](../../../../../ontokin/reach_reference_plan.py). Their existing mutation behavior must be preserved, including current order, capacity, domain clearing and pending publication. The ordinary reader dictionary and `ReachExecutionWork._cache` are separate caches.

A new cross-call strong reference would change the conclusion: it could preserve numerical data after ordinary eviction. It would require explicit capacity treatment or charged invalidation. Reserving a slot can displace another entry; adding a wrapper can add work to every consumer and hit. None of these costs is free merely because the number of new Python objects is bounded.

Affine numerator and delta values are temporary arithmetic state. Their widths are covered only by C048's genuine-factorial, fixed-domain proof. Old and new numerator objects can coexist during reassignment. The arithmetic identity by itself adds no persistent cache entry and retains the same `D+1` coefficient outputs, denominator and lane. A future implementation must still account for any additional copies or output occurrences it actually introduces.

## 3. All-path ledger obligations

The factorial lookup occurs before charged degree search, threshold testing, power construction and refinement. The coefficient call occurs only at line 560. Factory-side maintenance therefore applies even to calls that later reject, hit a coefficient key or fail before coefficient construction.

| Path or event | Required cost treatment |
| --- | --- |
| Fresh owner and first factorial miss | Retain original construction; add actual native-graph admission, minting, bookkeeping and publication charges once at their real positions. |
| Factorial hit | Retain one original lookup; add every actual provenance, owner, domain or lifetime check, including if the later dyadic route rejects or coefficient lookup hits. |
| Coefficient full-key hit | Preserve its original lookup/return. New admission after a miss can avoid helper-local hit cost; earlier caller maintenance remains charged. |
| Eligible coefficient miss | Add the complete admission and lifetime costs to `3D+6`; do not report `D-1` as net saving. |
| Degree 0/1/2 | Preserve original generic behavior for degree 0; degree 1 has zero gross room and degree 2 has one. Charge any degree filter where it actually runs. |
| Foreign or replaced tuple, mapping or method | Charge actual rejection work and preserve the original fallback, side effects and failure identity. Rejection does not refund earlier admission. |
| Changed cap, owner or observer | Charge actual readmission/invalidation; retain original prospective refusal policy and callback timing. A fixed-domain width proof is insufficient. |
| Cancellation or incomplete factory | Retain all completed original work and the original exception object. Do not publish trust for incomplete construction; charge actual cleanup/restoration. |
| Eviction, clear, replacement or remint | Preserve the 256-entry rule and original order. Charge added recognition, invalidation, retained references and any resulting recomputation. |
| Added copies, output or publication | Count each actual occurrence. Reusing immutable storage does not exempt newly materialized logical values. |

An added charge itself calls the real callback chain. [_Arithmetic.tick](../../../../../ontokin/reach_reference.py) runs the captured caller check, product observer and original observer in that order. [ReachExecutionWork.charge](../../../../../ontokin/reach_numeric.py), lines 71–94, runs external checking and counter/time work before its captured source observer. [ConstructionBudget.tick](../../../../../ontokin/construction.py), lines 75–87, reads its mutable check, operations and limits fields. These events can refuse or be effectful. A safe policy must account for them rather than assuming a new check is behaviorally invisible.

## 4. H2: one additional charged check at every affine construction callback

Consider this explicit repair to an unproved request-start authority marker:

> On each affine construction-operation callback, perform at least one newly charged origin/authority check before allowing optimized arithmetic to proceed.

There are `3D+4` affine construction operations. Ignoring every other additional cost gives the favorable complete-helper upper bound:

```text
net saving <= (D-1) - (3D+4) = -2D-5
D14 complete-helper net <= -33
```

At the corresponding pre-index-7-division point, the hypothetical affine schedule has completed 25 construction operations. Under this same monitor policy:

```text
corresponding prefix saving <= 4 - 25 = -21
```

These are bounds on the defined monitor schedule, conditional on reaching the compared arithmetic progress. They omit, favorably to the proposal, checks at lookup/publication, startup, other caller operations, rejected paths and monitor-management costs. The monitor's own charged callbacks also require a correct recursion/invalidation design. No such implementation was selected; this favorable bound is already negative before resolving those further obligations.

H2 is therefore **NO-GO for positive operation reduction**. This is not a universal minimum cost for all callback admission designs. It does not repeat C049's fresh 14-check helper screen or existing-table recurrence migration.

## 5. Whole-request result remains unknown

For a hypothetical successfully completed, behavior-preserving matched event sequence, the incremental saving would be:

```text
S = sum(D_i - 1 over eligible completed coefficient misses)
    - A_startup - A_factory - A_hits - A_misses
    - A_rejections - A_callbacks - A_lifetime - A_output
```

Each `A` counts genuinely added charged work at its actual occurrence. Startup is included once, not repeatedly allocated per miss. If altered cache handling changes later recomputation, that difference also needs explicit accounting. The expression is an accounting obligation, not a measured request total or a complete safe implementation ledger.

[C047's lifetime review](../../checkpoint-047-lifetime-review/review.md) establishes five new completed coefficient keys only in the interval from key 0 entry through key 153's exception snapshot before outer cleanup:

| Degree | Original complete miss | Affine complete miss before admission | Gross difference |
| --- | ---: | ---: | ---: |
| 7 | 33 | 27 | 6 |
| 8 | 37 | 30 | 7 |
| 13 | 57 | 45 | 12 |
| 17 | 73 | 57 | 16 |
| 16 | 69 | 54 | 15 |
| **Total** | **269** | **213** | **56** |

The seven keys resident at key 0 are not seven observed new misses in that interval. C047's snapshots do not establish their setup chronology, internal factorial-hit counts, proposed mint events or the unexecuted tail. They establish no candidate runtime event at all.

The four gross operations at the corresponding D14 prefix can be stated alongside the 56 completed opportunities. Their sum 60 is an interval ceiling before new costs, not a whole-request saving. Added factory startup occurring earlier must not be deducted from that interval as if it occurred inside it, and neither may it be omitted from a complete request.

Actual L03 has no successful complete baseline: it refuses inside the D14 helper. The complete candidate tail remains unknown. `100001 - 60` is not a justified optimized-request cost. No complete-request positive bound, successful target eligibility or release outcome is established here.

## 6. Distinct C051 source-study nomination

I independently checked the alternative reviewer's proposal in [_Arithmetic._atan_small](../../../../../ontokin/reach_reference.py), lines 370–387. Its prior iteration's `following` division uses the numerator left in `power` and the divisor required by the next iteration's `term`. A carry-forward design could retain the first term division and use that existing local thereafter.

For `N >= 1` completed iterations on the ordinary nonnegative small-input path, the original has one initial square, four operations per iteration, one final `other` operation and one grid charge: `4N+3`. The hypothetical carry-forward path has the first term division once and three operations per iteration: `3N+4`. Gross room is `N-1`, before all new admission costs.

This is a separate local redundant-division target; it does not use factorial provenance or a persistent cache. It remains a **source-study nomination**, not an approved implementation. Its current call counts, complete-request relevance, exact stopping behavior, live limits, callbacks and mutable dispatch need their own bounded review. Retaining one new charged checkpoint per skipped division would consume all of its gross operation room.

## 7. Review boundary

The selected raw-tuple proposal has no closed positive all-path ledger. H2 has a concrete negative bound. The appropriate outcome is to publish the bounded C050 result and move to the distinct source target, while preserving other unproved designs as unproved.

This review does not change original28's inherited **24/28**, unresolved P11/P16/P23/L03, held C035 status, the 100,000-operation/30,000-ms/32,768-bit/256-entry limits or 64-update cursor retirement. It supplies no runtime acceptance, original-request execution, benchmark, hosted CI, merge or complete release evidence.
