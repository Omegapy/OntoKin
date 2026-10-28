# C043 independent review: angular-envelope cache cost

Reviewer: `/root/angular_cost`. Date: October 26, 2026, America/Denver. Scope: static source and retained-evidence review only. No product import, product request, numerical replay, runtime test or benchmark was executed for this review.

## Decision

**NO-GO for an unconditional positive worst-case saving claim for the concrete U-Angular design below.** Even under ideal free eligibility and free copies, its native all-cold function-domain case adds work and removes none. The retained P23 evidence does not establish the conditional repeat count or shared-cache effect needed to select a narrower design. This is not an impossibility theorem for angular reuse or a claim that the counterexample is P23's actual trace.

The decision follows the adopted accounting rule: each new lookup, type/limit/claim check and copied logical value is charged, and storage is bounded. Existing source authority, cancellation and independent reader obligations remain. See [budget-counting section 3](https://github.com/Omegapy/OntoKin/blob/00606a16be62631179b50255d4de8daa34f8f196/docs/language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse).

## Exact source inspected

All paths below are at C042 commit `00606a16be62631179b50255d4de8daa34f8f196`, tree `9d9dd9f77b976c4b8b2076b8f5a0c4f87aa82342`.

| File | Git blob | Relevant source |
| --- | --- | --- |
| `ontokin/reach_recording_fast.py` | `c58d76692a79c1a1507a1185d1dfd15959de11cc` | `recording_float_excess` lines 527–586; `_checked_compare` 245–250; caller 2312–2341 |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` | `ReachExecutionWork` lines 38–265; `exact` 321–341 |
| `ontokin/reach_phase.py` | `9bae69ea6bda16fbbd841480139443cdbfe63d6f` | `PhaseBound` lines 38–57; source `finish` 790–796 |
| `docs/language-design/planar-reach-v0.1/budget-counting.md` | `d2113ebd1f44bbf78ba484a5f971d62741dab715` | Section 3 |
| `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-040-private-axis-design.md` | `64c68b42a59d5f74354323fe27c6dcccf28ea846` | Native mutable work/counter authority and complete charged accounting qualifications |
| `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-041-operation-reduction.md` | `f776cf7bd4963c3381adbbd84fa2416b1df18098` | Distinction between a local bound and complete shared-cache/request saving |

I read current AGENTS, GOAL, STATUS and HANDOFF-042. This review changes no source or repository coordination state. The finite release goal remains all original recordings and the remaining adopted reach release obligations; a source-only rejection closes none of those product gates.

## One concrete candidate: U-Angular

The candidate preserves the existing whole-result lookup first. Its existing key contains the method, operand cap, `(t,c,l,m,sp,sq)` and both selectors. Only after that lookup returns a miss and its existing cap check succeeds does the candidate perform an extra lookup in the **same** bounded numerical LRU cache.

The extra key distinguishes the method and angular proof kind, current cap, exact integer snapshots for `(t,c,sq)`, and every applicable arithmetic constant. The value contains immutable integer pairs for the five completed rational values `source_leaves`, `e`, `g`, `q` and `rotation_rad`. A lookup hit can substitute the first four values for the thirteen prefix arithmetic sites only after a fresh current native authority and intermediate-guard proof. `rotation_rad` can be substituted only at its original later point, after the original position expression, optional dynamic extension and original short-circuit range comparisons. Failed late admission executes the original multiplication at that point.

On an angular miss, the candidate executes the original arithmetic. It publishes its extra angular entry **only after the original whole-result publication, final guards and final cap check have succeeded**. That extra publication needs its own callback-safe source/key/work admission and final checks. It does not change the existing whole-result key or returned `RecordingFloatExcess` type. A failed or declined candidate gate retains its actually incurred added charges and the literal original fallback. It does not receive a second cache capacity or request allowance.

This is a precise design schedule for review, not an implemented or approved algorithm. Its complete authority/guard/copy proof remains open. The negative cost witness below grants that missing proof for free; charging it can only make that witness less favorable.

## Original work that can actually disappear

The function's angular sites are:

| Expression | Original exact sites | Omission position |
| --- | ---: | --- |
| `source_leaves = c + 1` | 1 | Before all position work |
| `e` | 4 | Before all position work |
| `g` | 4 | Before all position work |
| `q` | 4 | Before all position work |
| `rotation_rad = 16*q` | 1 | After position work and both successful range comparisons |

The ordinary position expression has ten exact sites. Its optional dynamic extension has four additional sites. Domain/selector admissions, the whole-result lookup, both range predicates when reached, cell-radius work when selected, whole-result publication and final guards remain. The comparisons are short-circuiting: if the first comparison fails the range, the second comparison and late rotation site are not reached. A replacement cannot move that late multiplication ahead of a position or range failure.

The actual gross amount is `13*r13 + r1`, where `r13` counts completed eligible prefix reuses and `r1` counts completed eligible late rotation reuses. `r1 <= r13` for this candidate. Calling the gross amount `14*r` requires proving both parts of every reuse. The number of domains, source arms or whole-cache misses alone proves neither value.

## Static counterexample to unconditional positive saving

Take full stable native limits, ordinary native dispatch, no external callback or observer, no trace/profile interference, an initially empty native cache, and adequate operation/time allowance. Use `include_cell_radii=False` and `dynamic=False`. Consider one call with the exact native default `PhaseBound()`.

The dataclass defaults give `t=c=0` and `l=m=sp=sq=0`. The literal expressions therefore give:

- `source_leaves = 1`;
- `e = 2^-46`;
- `g = 0`;
- `q = 2^-42`;
- `p = 2^-46`;
- `rotation_rad = 2^-38`.

Both original range comparisons pass. All original operands and prospective arithmetic widths fit the fixed 32,768-bit cap, including the final 1,075-bit guard. This is an algebraic function-domain witness. It was **not** executed, and it is not offered as a source-produced P23 bound.

The exact original charge count for this successful non-dynamic, no-cell-radius call with an empty cache is:

| Original operation | Charges |
| --- | ---: |
| Domain admission | 1 |
| Whole-result miss lookup | 1 |
| Angular arithmetic | 14 |
| Position arithmetic | 10 |
| Two range comparisons | 2 |
| Whole-result insertion without eviction | 1 |
| **Total** | **29** |

U-Angular adds an angular miss lookup and an angular insertion, and skips none of the fourteen sites. Even with all new authority, key, copy and lifetime work assigned zero for this lower-bound argument, it costs **at least 31**. The saving is at most **-2**. With an already full cache of unrelated native keys, the same singleton has an original cost of 30 and a candidate cost of at least 33: the added angular entry also incurs an additional eviction.

The witness extends without cache pressure to the 32-call sequence `PhaseBound(product_count=k)` for `k=0..31`, with all other dataclass fields at their native defaults. Every angular key is distinct. The maximum `e` is `2^-41` and maximum `q` is `2^-37`, so both comparisons still pass. No cell-radius or dynamic work runs. The candidate stores 64 distinct keys, within the existing 256-entry capacity, and no earlier result is reused by either algorithm. Original cost is exactly **928**; the candidate cost is **at least 992**, before all admission/copy/key/lifetime work. This is a static function-domain sequence, not a claim about source reachability or the original P23 request.

A restricted design could exclude this sequence, defer publication, or demand a source-proven repetition group. Those are different eligibility/scheduling decisions whose checks and actual repeat evidence need a separate proof. This counterexample therefore rejects an unconditional positive worst-case claim for U-Angular; it does not prove that every conditional angular cache loses.

## Complete accounting terms that a positive conditional claim would need

For a matched complete accounting comparison, let `A` be all added source/work/dispatch/selector/current-cap admissions; `K` be new key/snapshot checks and construction; `C` be copied or reconstructed logical values; and `L` be added lifetime, retirement and cleanup work. Let `D` include all partial/declined-gate and fallback overhead actually incurred. None may be silently set to zero in a positive implementation proof.

Let `B` be the actual added cache charges: each lookup, promotion, insertion, eviction and operand-domain reset. A normally completed angular hit alone pays one lookup and one promotion. A new angular miss pays one lookup plus its later insertion, and normally an eviction if the shared cache is full. Reentrant lookup/reset/publication outcomes must be counted by their actual route; the label “hit” cannot stand in for those charges.

Finally let `Delta_other = other_candidate_work - other_original_work`. It contains changed nested and enclosing work caused by the new shared-cache access sequence and any corresponding changes to invocation paths. **Its sign is not established.** Some extra entries can evict expensive existing proofs; some changed histories can suppress other work. A local cache-bookkeeping calculation must not assign either effect a favorable sign without proof. For a complete request, previously unvisited work after the old failure also needs its own bound; a failed prefix is not a complete-request ledger.

The conditional saving equation is:

`saving = 13*r13 + r1 - A - K - C - B - D - L - Delta_other`.

This is an accounting decomposition, not a closed positive bound. Establishing a positive worst-case bound requires valid upper bounds on all added terms and a valid lower bound on actual eligible reuse. Historical `14*31=434` supplies neither. It assumes a single reusable angular signature across all 32 historical cold calculations, no lost reuse, successful late reuse, and no consequential shared-cache change.

For the singleton/32-call counterexamples above, no extra-key displacement changes any later useful access. Thus `Delta_other=0`, gross reuse is zero and the negative lower-bound calculation is closed. No uncertain shared-cache term is needed to establish that specific regression.

## Authority and guard obligations are substantive

1. `PhaseBound` is frozen at the dataclass interface, but its `Fraction` fields and global `Fraction` constants have backing numerator/denominator state. Object identity or a tuple containing them does not establish immutable scalar values. The new key must bind actual integer fields, and copied output values count as real work.
2. A completed result under a former cap does not prove every omitted prospective guard at its current original point. `exact` charges first, admits current operands, checks prospective numerator/denominator widths, computes and checks the result. The prefix proof must cover all thirteen sites in order; the late multiplication has its own later proof. The ordinary whole-result cache remains separate and is not authority for this new partial result.
3. Constants include the current `MAX_RECORDING_ROTATION_STEPS`, `AXIS_ERROR`, `PRODUCT_ERROR`, method and exact/Fraction bindings. Callbacks between their original read points can alter them. Capturing an early tuple is not sufficient unless native dispatch and intervening lifetime are established.
4. `ReachExecutionWork.lookup` and `remember` invoke callbacks, synchronize the operand domain and perform generation/presence rechecks. New cache accesses are observable operations. Publishing after the original final cap check avoids earlier radius/guard precedence changes, but introduces a new final callback boundary; it still requires fresh post-callback domain and publication authority.
5. Exact native work type is not a proof of its mutable instance dispatch, external construction callback, observer, category map or shared cache. As C040/C041 explain, native dictionaries can contain hostile colliding keys. Added reads and normal charge bookkeeping can run those comparisons. Any gate relying on a counter or private cache witness must authenticate the actual relevant state or use a separately proved provenance mechanism, with each inspection charged.
6. False eligibility, callbacks that mutate source/caps/cache state, reentrant insertion, reduced limits, foreign dispatch and original exception identity need literal fallback at the relevant original boundary. Cleanup must not replace the original error with a new callback error. No proof survives a failed request by being reused under a fresh allowance.

These are unclosed implementation obligations, not an accusation that the current native cache omits its existing operand-limit resets. The source already checks those resets during lookup and insertion.

## Evidence needed before selecting a different conditional design

The exact missing observation is a current, source-bound ordered record of the original function's angular and spatial operands, both selectors, whole-result lookup classification including refusal, and completed arithmetic/publication points. A shared-cache design additionally needs the relevant complete native cache operation sequence or an independently established bound on induced cache effects. A dictionary of aggregate domain counts cannot recover the temporal sequence or the copies/authority costs.

This review does not schedule a new diagnostic. Any later diagnostic remains separately scoped, must start a fresh untouched original P23 request from closed current inputs, and must preserve control/capture failures and every original cap. It must not resume the failed request's tail. No runtime implementation is selected here.
