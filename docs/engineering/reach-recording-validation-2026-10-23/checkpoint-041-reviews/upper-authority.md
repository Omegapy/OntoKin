# C041 independent review: upper_binary64 cache bypass

Reviewer: `/root/witness_review`. Verdict: **NO-GO for unconditional cache bypass under the required positive worst-case bound.** The retained P16 counts support a positive local conditional opportunity, but not a complete eligible-design or whole-request bound.

This was source inspection only. No product request, unit test, benchmark, hostile execution, runtime edit or GitHub write was performed. The algebraic examples below were not executed.

## Exact source and historical premises

The live C040 source tree was retrieved at `0fab8a2fe00047ebf3f8778721d0a77b7a1d5420`. Local read-only copies were hash-matched to these Git blobs:

| File | Git blob |
| --- | --- |
| `ontokin/reach_export.py` | `f8a240dd033ebf5e4f2ce83bf46e3ae379b9b27a` |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` |

Relevant source is `reach_export.py`: `_reuse` beginning at line 59, `_rational` at line 94, `_compare` at line 134, `upper_binary64` at lines 290–315, `_certificate_quantities` beginning at line 1049, and the enclosing `certificate_group` reuse at lines 1306–1312. Native shared-cache behavior is in `reach_numeric.py`: `charge` at lines 71–94, `lookup` beginning at line 120, `remember` at line 139, and `_sync_cache_operand_limit` at lines 248–260.

C038's retained `checkpoint-038-analysis.json` reports 21 `recording_certificate_group`, 261 `recording_bound_float_return`, and 136 `recording_bound_nextafter` charges. These are historical completed-source counts from the original failed request; C041 did not rerun that request. The 266-category inference from C040 concerns a later reader point and must not be reused as a measured category count at this earlier producer-conversion stage.

## Local opportunity is real but conditional

The concrete change considered is to replace `return _reuse(work, ("upper_binary64", value), calculate)` with direct `calculate()` after the unchanged input decoder, nonnegative check and existing exact-zero route.

For an unchanged sequence of successful nonzero native calls with stable arithmetic, a miss originally pays lookup and insertion, plus possible eviction. Direct calculation avoids at least two bookkeeping charges on that miss. A former hit originally pays lookup and promotion; recomputation adds three charges, or four if `nextafter` is needed. Its increase is therefore at most two charges.

Let M be original misses, h original hits and E the original evictions attributable to this family. Before any new admission or lifetime costs, a fixed-call-sequence bound is:

`saving >= 2 M - 2 h + E`.

Each executed `_certificate_quantities` makes 21 conversion calls. There are at most 21 such executions from the 21 outer group visits, plus one time-shift conversion per group and one report conversion. Thus the historical source schedule has at most `22 * 21 + 1 = 463` conversion calls. The 261 completed float-return charges identify actual calculations under native cache behavior; at most 202 remaining calls can be nonzero cache hits. The favorable local conditional bound is consequently `2*261 - 2*202 = 118`, before gate costs and without taking credit for unassigned evictions.

This is not measured optimization saving, an actual completed P16 cost, or evidence that later reader stages would finish. It also does not establish that all subsequent call sequences remain identical after changing the shared cache.

## Closed generic counterexample

Consider n repeated calls with `Fraction(1)`, a fresh native request work object, full stable 32,768-bit operand domain, ordinary empty bounded cache, no external callback or observer, and sufficient remaining operation/time budgets. All conversions are exact, so no `nextafter` runs. The existing exact-zero shortcut does not apply.

The first original call costs six charges: input decode, lookup, float return, result decode, comparison and insertion. Every later original call costs three: input decode, lookup and promotion. The total is therefore `3n + 3`.

Direct calculation costs four per call: input decode, float return, result decode and comparison. Its total is `4n`.

The saving is `3 - n`. Four calls already regress from 15 to 16 operations; every n greater than three regresses. Only one cache entry is needed, so this example fits the unchanged numerical-cache limit. These counts are algebraic consequences of the source, not results from a test run.

Therefore an unconditional bypass has no positive worst-case bound over its admitted native inputs. A restriction to distinct outer certificate-group keys does not establish distinct inner conversion inputs: the outer key includes `bound.speed`, while `_certificate_quantities` consumes `bound.angular_speed` and `bound.acceleration` rather than that speed field. Different group keys can still repeat rounding values. A profitable eligible subset would need its own genuine source proof and complete admission cost.

## Custom callback and exception behavior

The existing public helper accepts work protocols with `lookup` and `remember`; `_reuse` deliberately calls them. As a source counterexample, let a foreign work implementation have ordinary successful `charge`/guard methods but make `lookup` raise a particular sentinel exception object. For a positive value, the original helper raises that same object after input decoding and before `calculate`. Unconditional bypass never calls `lookup`, so it can instead finish or raise a different exception from float conversion/charging. That changes an actual original first-failure and exception identity. No such probe was executed for this review.

The same concern applies to `remember`, instance-shadowed methods and cache callbacks that mutate the current domain or reenter other work. An exact `ReachExecutionWork` type check alone cannot authenticate its methods, mutable state, nested construction callback, observer, cache keys or values. The original `hasattr` dispatch can itself be observable for a foreign work protocol; that protocol must retain the literal fallback.

The cache is an externally mutable `OrderedDict`. Exact container type does not establish that its keys and their equality behavior are native or that its values are authentic computed results. Omitting its lookup removes those possible callbacks; that cannot be asserted equivalent for arbitrary foreign/modified cache state.

### Lowered operand domains: precise scope

Native `lookup` calls `_sync_cache_operand_limit`. A changed native cap invalidates the previous-domain cache, including a defensive recheck after the promotion callback. This review does **not** claim that a legitimately warmed native entry survives a later cap change.

Direct calculation introduces the original calculation's fresh 1,075-bit binary64 result-decode guard on every former hit. Under authentic stable native caching, the same successful value calculation can justify that guard; a current lowered cap must be analyzed with the existing synchronization semantics. A foreign `lookup` returning a supplied value, or an altered cache/work implementation, need not have that proof and can behave differently. Such cases require the ordinary helper route. They are not a reason to assume a native stale-hit defect.

## Shared-cache scope remains unclosed

The native cache is shared by this conversion and other calculation families. Removing one family from a fixed independent LRU reference sequence reduces competition for the other families. That fixed-sequence fact alone does not close this producer's behavior: `upper_binary64` calls occur inside the calculation callback of the enclosing cached `certificate_group`. Altering retention can change whether that enclosing calculation runs, which also changes its nested references and charges.

This review has not proved that the adaptive trace produces an adverse total effect. It has also not proved that every non-conversion family is unchanged or cheaper. A whole-request ledger must establish that property or account for the changed trace. The local 118-operation lower bound must retain its fixed-call-sequence qualification.

A per-conversion eligibility gate consumes work that is currently absent. A one-time native admission would instead require a bounded lifetime and source/work/cache provenance mechanism covering every intervening callback and mutation. Neither schedule was specified or closed in this candidate. All new type, claim, limit, storage, lookup and retirement work must be included; no broad gate can be called free because it resembles an existing checker elsewhere.

## Decision

Reject unconditional `upper_binary64` cache bypass as an implementation choice under the current requirement to establish positive worst-case and P16-specific charged bounds first. Preserve the P16 `>=118` figure only as a local conditional opportunity, with no whole-request performance or pass claim.

The rejection is specific. A different call-site restriction, cache policy or conversion algorithm may be worth evaluating if its eligible domain, callbacks, first-failure guards, shared-cache effect and total added work are proved before implementation. None is selected by this review. No cap, fixture, independent predicate, expected artifact or release gate changes.
