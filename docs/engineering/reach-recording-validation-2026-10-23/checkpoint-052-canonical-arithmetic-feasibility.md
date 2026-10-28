# C052 canonical-target arithmetic reuse feasibility

Date: October 27, 2026, America/Denver. Owner: `interactive-reach06-canonical-arithmetic-20261027-c052-a64e`. Branch: `work/reach06-canonical-arithmetic-20261027-c052-a64e`. Source parent C051: `9aeab3e1b4e05e47a0284da55925f41cccc23964`, tree `c661e9b40d5ba8390d4ed96725e41198f67655f9`. [Coordination](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6451095874).

**Decision: NO-GO for R1 structural parent reuse; R2's fresh structural cache scan does not repair numerical origin and has an occupancy-dependent cost barrier; R3 empty-parent reuse has no ordinary native fixed-domain constructor eligibility. No runtime implementation is selected.** These are bounded design findings, not proof that every possible parent-reuse design is impossible.

The next source question is **C053: preserve the original fresh canonical child and review publication of its completed 128-bit pi enclosure into a genuinely absent parent slot for later residual work**. This direction keeps the original child authoritative for target calculation. It is a distinct unapproved hypothesis with explicit origin, callback, safe-key, cache-lifetime and complete-cost gates. [Next scope](checkpoint-052-next-scope.json).

## 1. Scope and evidence

This checkpoint reviews the source of `_canonical_targets` and its independent request arithmetic. A canonical target is the exact source-defined pair of shoulder/elbow coordinates after branch, rounding and closed-limit checks. A cache-origin proof establishes that a stored numerical value actually came from the independent calculation required by the claim. Native types and an expected key do not supply that proof.

The new work contains only C052 analysis, independent reviews, validation and handoff records. No OntoKin import, numerical candidate, original request, runtime test, benchmark, failed-tail continuation, archived-driver execution, hosted dispatch or main merge occurred. Original28 remains **24/28**; **P11/P16/P23/L03** remain unresolved. C035 remains held, including adverse timing.

Startup read current governance, separate main/continuation STATUS, branches, PRs, CI and explicit C051 release. The first branch-create call was interrupted without a confirmed result. Readback found the ref absent and no C052 comment; the later create was confirmed before publication. Isolated source review continued during recovery. The new branch starts at final C051. Main remains `2bb4588e121fcfe99b4d42c734b15b38362f3642`; no main integration lease was acquired. [Startup record](checkpoint-052-validation/startup.json).

The recovered **1,042-file / 132,726,817-byte partial snapshot** matches the parent Git tree by path, length and Git blob. All **65 runtime modules** match freshly fetched held C035 tree `87c949b238055af1ce368c694e1d5683c8aeacde`. It is not a full 2,827-file checkout. Historical binary bytes copied from the predecessor remain identified bytes; no new internal archive audit is claimed. C047's 18 evidence parts are absent here. [Source inventory](checkpoint-052-validation/recovered-inputs.json), [runtime binding](checkpoint-052-validation/held-runtime-binding.json).

Independent [numerical/authority](checkpoint-052-reviews/authority/review.md), [cost/lifetime](checkpoint-052-reviews/cost/review.md) and [evidence/next-source](checkpoint-052-reviews/evidence/review.md) reviews identify their own selected inputs and limits. Actual documentation/metadata execution and publication have separate records. Source reasoning is not an executed runtime result.

## 2. Exact schedule and conditional numerical identity

In [reach_reference.py](../../../ontokin/reach_reference.py), `_canonical_targets` at lines 674–735 uses the parent for common exact annulus, cosine, radical and signed-shoulder algebra. Its fixed precision loop then constructs a fresh `_Arithmetic` for each precision in `(128, 256, 512, 1024, 2048)`.

R1 changes only that first constructor selection: after the original common algebra, use the parent at the first128 attempt if current native owner/work/check, bits, scale, operand domain and absent arithmetic observers are admitted; otherwise retain the original fresh child. All later precisions, the entire body, atan, original refinement and final failures remain unchanged. The review does not invent a completed implementation of that admission or assign its cost zero.

A fresh child derives its check from current `work.tick` when work is present, initializes an empty cache and unset arithmetic observers, and checks the dyadic denominator against the live limit. Construction has **no tick**. Avoiding it saves no charged operation and cannot suppress its original refusal. Matching a bound method means the correct native function and owner, not identity of two newly allocated bound-method wrappers.

Under a fully native unchanged graph, an authentic parent pi entry with exactly the original endpoints supplies the same inputs to every subsequent operation. The body reaches only the pi cache family; its first original child pi call misses, and subsequent child calls already hit. Induction gives identical intervals, first refinement, binary64 cells, half-turn normalization and branch/limit decisions. The original fresh calculation's prospective operand domain must also be established. A merely valid enclosure of pi can change refinement, so containment alone is insufficient.

These are conditional mathematical facts. They do not prove an existing mutable cache entry's history, the complete current callback graph, or its behavior after an added admission charge.

## 3. R1 counterexample: a native pi entry can be wrong

The parent cache can contain the native key `("pi",128,32768)` with native value `Interval(F(25,8),F(25,8))`. This value is positive, ordered, dyadic, grid-aligned and between 3 and 4. A current scan of those properties passes, but it is not the original pi result.

Use native lengths `(2,1)`, target `(1,0,0)`, branch `elbow_positive`, and ordinary symmetric pi64 joint limits. The common algebra gives cosine -1, radical 0, `k=1` and shoulder Cartesian coordinates `(1,0)`. Reuse therefore returns `(0.0,3.125)`. The original common prefix does not read this parent cache; its fresh child independently constructs pi.

The unchanged alternating-series enclosure proves the original pi lower endpoint is above

```text
1184/375 - 4/239 - 20*2^-128.
```

Before the tiny grid allowance, the margin over `25/8` is exactly `11183/717000`, greater than 0.015. Binary64 rounding cannot bridge that gap. If the original returns, it cannot return elbow 3.125; a later original refinement/failure also differs from the candidate's returned false target. No unexecuted exact pi64 rounding-cell audit is claimed. The [authority review](checkpoint-052-reviews/authority/review.md) gives the series and grid derivation.

This is a symbolic counterexample to R1's admission, not a claim that any retained original request had a corrupted cache. A protected computation-to-use history or an independent exact value proof could exclude it. A present-tense structural screen cannot establish that history. Scanning every existing entry does not change this conclusion.

## 4. Gross cost and callbacks

The successful native128 pi miss costs **165**, while an authentic eligible hit costs **1**:

| Work | Cold pi cost |
| --- | ---: |
| Initial lookup | 1 |
| Atan at 1/5, 28 iterations | 115 |
| Multiply that enclosure by 16 | 5 |
| Atan at 1/239, 8 iterations | 35 |
| Multiply that enclosure by 4 | 5 |
| Interval subtraction | 3 |
| Publication | 1 |
| Total | 165 |

Thus the immediate gross is **164 once per qualifying first128 attempt**, not once per pi call. If there are p>=1 stable pi calls in an attempt, the original child contribution is `164+p`; a hot parent contributes p; a cold parent also contributes `164+p`. No-pi paths offer zero.

For the example in section 3, the common exact prefix has 26 ticks. A successful first precision has 185 ticks with fresh pi or 21 with a parent hit, giving **211 versus 47 before admission**. Both independent reviewers derived these counts from source. They are not measured request costs.

The original callback graph is arithmetic tick -> work tick/charge -> external check -> possible nested construction check, followed by the captured work/product/source observers. Empty arithmetic observer slots do not exclude a nested callback. With authentic pi and the successful native route, a fixed sentinel at callback 48 is reached by the original but missed by bare 47-tick reuse. If a fixed admitted gate adds G ticks, `0<=G<164`, the corresponding separator is callback`48+G`. This argument applies to that schedule; a gate that excludes all effectful callbacks needs its own proof and ledger.

Restoring one charged checkpoint for each omitted boundary consumes all 164 local room before other costs. A tick alone still does not preserve every prospective operand or dispatch failure. Genuine work reduction need not reproduce the original operation-budget exhaustion; the actual performed work must respect the unchanged caps. Original callback exception identity and required cancellation boundaries remain obligations.

## 5. R2 scan and R3 empty-cache boundaries

R2 freshly inspects every resident parent entry as part of a stronger current native/origin screen. Even if one combined entry inspection costs only one operation, occupancy m gives

```text
immediate net <= 164 - m - A_other.
```

Here `A_other>=0` includes all other new authority, origin, selection, copying, rejection and cleanup work. At m=256 the immediate ceiling is **-92**; at m>=164 it cannot be positive. This is a chosen-scan bound. Low occupancy, specialized or amortized admissions remain unresolved. Actual setup occupancy is unknown; a later cache snapshot is not that measurement. R2's structural scan also still admits the false native pi unless a separate numerical-origin proof is added.

R3 requires an empty parent so the native first pi factory can establish local origin. Even for an admitted direct helper call, both parent and fresh child compute cold pi; immediate gross is zero. Its only possible benefit is retained pi for later work.

R3 has **no eligible call on the ordinary unchanged native fixed-domain `build_reference` constructor path**. `_initialize` runs before `_build` and caches each object's normalized quaternion. A valid reach chain needs three distinct object owners. Successful native quaternion lookup/publication leaves a nonempty parent cache. Fixed-domain lookup, replacement and bounded insertion/eviction preserve nonemptiness; the domain-reset clear is excluded by the premise. Later consumer cursor retirement is not a constructor clear. Generic direct callers, changed domains and custom mutation are different unproved scopes.

## 6. Complete request accounting and evidence gaps

Parent reuse promotes pi on a hit, inserts it and may evict an unrelated entry on a miss, and may clear the entire parent cache on an operand-domain synchronization. The original temporary child has none of those parent effects. A first128 refinement can retain pi in the parent even when that attempt fails and a later fresh child supplies the result. Later pose/coefficient/cursor work and pending publication/retirement must therefore be accounted for.

The reader's `a.cache` and `ReachExecutionWork._cache` are different mechanisms. Existing reader lookup/publication ticks already cover their ordinary bounded bookkeeping. Do not borrow the production work cache's extra promotion/eviction charges or call new scans and snapshots free.

For matched completed native requests, a conditional accounting identity is

```text
saving = 164*H - A_total - Delta_later.
```

H counts actual matched local omissions; `A_total` includes every new startup, admitted/rejected gate, copied/output occurrence, publication and cleanup cost; `Delta_later` is candidate minus original remaining work. It is signed: changed later cache work can help or hurt. Do not count a later difference twice. H, setup occupancies, admission costs and `Delta_later` remain unknown. Interrupted calls need exact event-prefix accounting. Subtracting 164 from a failed 100001 count proves no complete request result.

The [all-path ledger](checkpoint-052-cost-ledger.json) includes target-key hits, common-prefix failures, cold/hot/no-pi calls, zero-related paths, refinement, later precisions, rejection, malformed/custom state and interruption. `_targets` already deduplicates equal `(lengths,target,branch,limits)` keys. C047's retained cache census begins after reference setup; C044's P23 failure occurs before independent-reader entry. Neither supplies the required setup chronology. A reader-only change cannot resolve that observed P23 producer failure.

## 7. Next bounded source task

Keep the original fresh canonical child and all its original target checks. Only after a first128 success, review publishing that child's already completed pi to a genuinely absent matching parent key, using the existing bounded parent cache. Never use a parent payload to choose or certify the target; do not compute a missing child pi for this purpose; do not overwrite a present parent entry.

The source consumer is concrete: `_event` -> `_base_tip` -> `sincos` -> parent `pi`. Under successful native128 fixed-domain L03 setup, the first target `(0,1,0)` with unit lengths needs child pi, then its nonzero shoulder's residual calculation needs parent pi. Initial vectors/quaternions have populated the parent without constructing pi. Thus one later cold parent miss can conditionally become a hit: **164 gross before every new cost**. This is normally one first-parent-miss opportunity, not 164 per target. Actual first128 success and full-request saving are unmeasured.

Under proved unchanged native child lifetime, the canonical child's cache contains zero or one completed pi entry. This narrows the origin object. It does not prove the lifetime: current type tests alone are insufficient. Parent key lookup can invoke hostile equality even if values are not consumed; ordinary parent.lookup promotes present keys and is not an order-neutral rejection probe.

C053 must freeze one schedule and close child origin, safe nonpromoting parent absence, current native callback/limit/error authority, copied/retained occurrences, insertion/capacity/order/eviction and all later work. Stop if any proof or complete positive charged bound fails. Only a surviving design justifies selecting and reviewing a precise collector for remaining incidence. The [next scope](checkpoint-052-next-scope.json) states those gates; the existing passive plan is not permission to execute.

No new recording pass follows from this review. The immediate product gate remains 28/28, followed by all original Agent, regression/compatibility, independent numerical/native/browser/visual, hostile/inherited and resulting-main requirements. The full OntoKin goal remains incomplete.
