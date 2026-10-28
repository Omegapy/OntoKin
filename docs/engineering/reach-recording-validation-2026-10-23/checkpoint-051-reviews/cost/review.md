# C051 independent cost and lifetime review

Reviewer: `c051-cost-review`. Source parent: `492b0e0edb5eb71e058fc29af059992b3a7952cb`, tree `ebc9e155ee98b37e56199dde987774ff38960d81`. This is a source review with metadata hashing. It does not report an OntoKin import, numerical replay, test, benchmark, original request, or measured candidate saving. The local repository is a partial recovered source snapshot. [Exact inspected inputs](input-manifest.json) and [structured findings](result.json) identify the review's dependency scope.

## Decision and scope

The adjacent-term identity has real arithmetic opportunity, but no positive complete implementation is established. The literal carry omits a live callback and prospective operand check at each reused term. A repair that retains one charged checkpoint for each omission consumes the entire arithmetic opportunity before admission. A stronger, concrete fresh admission screen was also considered: the four class-field maps below alone require 73 newly charged probes per call, exceeding the maximum 63 arithmetic operations available in any successful native 128-bit call. That named fresh-screen policy is NO-GO for positive charged-operation saving.

These results do not disprove every specialized, amortized, or origin-based admission mechanism. A different mechanism would need its own complete source proof, actual charge schedule, lifetime accounting, and request incidence. None is selected here. The review agrees with closing these bounded C051 designs without implementation, and moving to a distinct, separately reviewed target.

## Baseline and carried schedule

The source at `ontokin/reach_reference.py:370-387` computes a square once, then four exact operations per iteration: current term division, alternating sum, next power multiplication, and following-term division. On the first strict stopping test it performs one more exact add/subtract and one outward `grid` operation. `exact` and `grid` each call `tick` once at lines 126-145 and 177-187.

Let N be the number of completed iterations in a successful nonnegative call, with native unchanged dispatch, stable supported precision/domain, and all original arithmetic succeeding. The direct helper ledger is:

| Work | Original | Carry before any admission |
| --- | ---: | ---: |
| Initial square | 1 | 1 |
| Current-term divisions | N | 1 |
| Alternating sum updates | N | N |
| Power updates | N | N |
| Following-term divisions | N | N |
| Other enclosure endpoint | 1 | 1 |
| Final outward grid | 1 | 1 |
| Total | 4N+3 | 3N+4 |

The gross difference is N-1. These counts cover `_atan_small` itself. It has no cache lookup or insertion. The caller `pi()` performs its own `lookup` and `remember`; an existing pi-cache hit bypasses both seed calls completely. `sincos` and target caches can also bypass work. No caller count is inferred from a helper formula.

The proposed abstract schedule retains the original first term division and then uses the prior `following` as the next `term`, preserving all remaining operations and the first strict stop. The table is an arithmetic ledger, not a fully implemented control-flow or admission ledger. Any new branch/selection check, ownership inspection, copied value, output occurrence, fallback work, or cleanup must be added at its actual position. Hoisting the first division ahead of the original loop-domain evaluation is not valid for generic malformed or empty-range paths without admission and unchanged fallback.

## Finite native bounds and fixed pi seeds

For fixed native `bits=128` and 0 <= x <= 1/2, the following term after N iterations is x^(2N+1)/(2N+1). At N=64 it is at most 2^-129/129, which is strictly smaller than 2^-136 because 128 < 129. At x=1/2, N=63 does not stop: 2^-127/127 exceeds 2^-136 because 512 > 127. Thus N <= 64, with an attainable mathematical maximum of 64 when the original operations all succeed. The per-call gross ceiling is 63. This is a source-derived bound, not a measured original-request call count.

For the exact pi seeds, the strict stop is equivalent to q^(2N+1)*(2N+1) > 2^136 for x=1/q. The adjacent inequalities establish:

- q=5: 55*5^55 < 2^136 < 57*5^57, hence N=28. The original helper costs 115, the carried helper before admission costs 88, and gross room is 27.
- q=239: 15*239^15 < 2^136 < 17*239^17, hence N=8. The original helper costs 35, the carried helper before admission costs 28, and gross room is 7.

For example, the first left inequality follows from 5^3 < 2^7 and 275 < 2^9; the first right inequality follows from 5^7 > 2^16 and 285 > 2^8. The second left inequality follows from 239 < 2^8 and 15 < 2^4. For its right inequality, 239^5 > 230^5 = 643634300000 > 2^39 and 17*239^2 = 971057 > 2^19, so 17*239^17 > 2^136. No numerical driver was executed for these inequalities.

The two complete seed helpers therefore offer 34 gross operations in a cold native 128-bit `pi()` construction. A pi-cache hit offers none of this opportunity. Refinement uses the separate precision schedule `(128, 256, 512, 1024, 2048)` in `_canonical_targets`; the 63 ceiling and seed counts above must not be applied to other precisions.

## Stronger one-time admission hypothesis

An observer-free native path is a real source possibility. `_canonical_targets` creates a fresh `_Arithmetic` per attempted precision at line 710, and `_Arithmetic.__init__` starts both arithmetic hooks at `None`. The current work still has its actual callback graph, counter map, live limits, and optional work observer. This fact is not proof that a particular retained request takes an eligible path.

The stronger policy considered here performs one fresh native admission for each 128-bit call. It follows the field/function/state inspection style of `_certificate_term_native` in `ontokin/reach_conformance.py:2686-2828`, adapted to the arctangent helpers and to `ReachExecutionWork`. It would reject custom callbacks and non-native owners; an accepted construction callback must have native dispatch and nested `check is None`. It does not replace or clear callbacks.

The following four class-field maps are a concrete part of that policy. Every field includes a fresh class-namespace lookup compared with its pinned identity. The five storage fields are `__getattribute__`, `__getattr__`, `__setattr__`, `__delattr__`, and `__dict__`.

| Class | Additional fields beyond the five storage fields | Probe count |
| --- | --- | ---: |
| `_Arithmetic` | `exact`, `tick`, `guard`, `operand_limit`, `_dyadic_denominator`, `grid`, `_grid_domain`, `work`, `check`, `bits`, `scale`, `_recording_after_tick`, `_recording_product_after_tick` | 18 |
| `ReachExecutionWork` | `tick`, `charge`, `resource`, `external_check`, `_source_after_charge`, `counts`, `operations`, `max_operations`, `max_operand_bits`, `max_elapsed_ms`, `started` | 16 |
| `ConstructionBudget` | `tick`, `exceeded`, `check`, `operations`, `limits`, `started`, `profile` | 12 |
| `Fraction` | `__new__`, `__init__`, `__mul__`, `__truediv__`, `_mul`, `_div`, `_from_coprime_ints`, `__add__`, `_add`, `__sub__`, `_sub`, `__bool__`, `__eq__`, `__lt__`, `__gt__`, `__le__`, `__ge__`, `_richcmp`, `numerator`, `denominator`, `_numerator`, `_denominator` | 27 |
| Total | Four maps | 73 |

The adopted budget-counting section 3 charges each new lookup/check. Even assigning only one operation to each listed field probe gives A_call >= 73 for a fully accepted call. This deliberately ignores further nonnegative work: class type/MRO checks; code/default/keyword-default/closure/global/builtin identities; Fraction numeric ancestors and `Interval` construction; plain instance dictionaries and instance shadow checks; native rational numerator/denominator checks; hook checks; authentic work/construction scalar and map fields; live counts and all construction-limit entries; callback binding; trace/profile conditions; the gate's own safe charging; fallback and cleanup.

Consequently, for this named fresh-screen policy, net <= N-1-73 <= -10 on a successful native 128-bit call. The fixed pi seed calls have ceilings -46 and -66 respectively; if independently screened per call, their combined ceiling is -112. All further necessary costs make these ceilings no larger. Rejected paths may stop screening early, so 73 is an accepted-path floor, not an asserted cost for every rejection.

The 73 probes are not claimed to be a universal minimal admission. This policy admits only the fixed 128-bit domain; other precisions use the original fallback and incur whatever screening was actually reached. Their rejection overhead has no assigned zero cost. Hoisting a different proof to owner construction, sharing a completed authority check across multiple calls, or relying on some separately protected origin would be another design. Its complete lookup/check/lifetime schedule, live state, safety through every callback, and number of uses would need fresh proof. This review has not priced or accepted such a design. The existing `_product_native` and `_Guard.current` mechanisms do not automatically provide all atan-specific dispatch or nested-callback authority. An actual `_Guard.original` observer path needs its own transitive closure and must preserve its current-limit and failure behavior.

## Checkpoint-preserving repair

An omitted `exact` call normally invokes `tick`, the current check, captured arithmetic observers, and prospective operand checks before arithmetic. `ReachExecutionWork.charge` also executes the actual external check before its resource/counter checks and later source observer. `ConstructionBudget.tick` can execute an already-installed nested callback. A type check of the outer budget does not prove that nested callback inert.

Define a repair which adds at least one newly charged checkpoint at each of the N-1 omitted divisions. Its successful helper cost is at least `(3N+4)+(N-1)+A_other = 4N+3+A_other`. Its net saving is at most `-A_other`, with no positive charged-operation room. A bare `tick` is still not a complete correctness repair: it does not itself duplicate the original conversion, operand, prospective allocation, or dispatch behavior. Preserving those checks costs additional actual work. This bound rejects the specified per-omission repair, not every possible safe admission.

## All-path accounting

| Path | Original direct helper behavior | Candidate accounting requirement |
| --- | --- | --- |
| Native x=0 with a valid nonempty loop domain | N=1 and 7 successful ticks | 7 before admission; no arithmetic saving pays for a gate. |
| Native small positive first-stop call | N=1 and 7 ticks | Same zero gross room. |
| Successful nonnegative N>=2 | 4N+3 | 3N+4+A_call before any caller changes; strongest reviewed screen and per-omission repair are nonpositive. |
| Accepted negative x | Positive recursive helper followed by exactly one native `neg` tick; 4N+4 | 3N+5 plus all outer/inner admission costs. The wrapper is not free to move ahead of the inner result. |
| abs(x)>1/2 | `_Uncertain` before square or loop; negative recursion also fails before outer `neg` | No generic arithmetic room; added rejection screening is overhead and original exception/phase must remain. |
| F conversion or comparison error/custom behavior | May occur before any native tick | Preserve generic dispatch/error/callback behavior; no successful-native formula applies. |
| Empty or malformed loop range after successful square | Original square precedes `range(self.bits+8)`; a noniterating range proceeds to nonconvergence | Do not hoist an extra first division across the original range evaluation; account admission and untouched fallback. |
| M>=1 completed iterations then nonconvergence | 4M+1 ticks, no remainder endpoint or grid | Abstract carried schedule 3M+2 before additions. Generic malformed/custom states retain fallback. Under fixed valid native x/precision with all operations succeeding, the proved bound makes native nonconvergence unreachable. |
| Narrowed operand cap or changed precision/grid | Original live prospective checks can refuse at the current arithmetic operation | Previous following success is not a receipt for the current cap or operation. Add all actual new checks; reject or preserve original fallback and error identity. |
| Interruption in square, loop, endpoint, grid, or a new gate | Completed work, attempted charge and callback effects depend on the failure position | Record actual prefix costs; never assign full N costs or assume all attempted ticks increment both counters. |
| Native admission rejected | Original helper remains the required path | Original work plus actual partial-screen/fallback cost; no assumed zero rejection cost. |
| Custom work maps, scalar descriptors, replaced functions/defaults/globals/closures | May act during original lookup, callback, guard, or arithmetic | No uncharged state audit; an earlier native class identity is not complete authority. |
| Pi/target/sincos caller hit | May bypass helper entirely | Per-owner/request admission or maintained receipts still cost wherever installed; do not count bypassed atan opportunities. |

After M>=1 complete nonstopping iterations, the matched abstract helper prefixes contain `1+4M` original ticks and `2+3M` carried ticks, a gross difference M-1 before additions. If the next original term division succeeds and is the next omitted operation, the corresponding prefix difference becomes M. Actual errors can occur before a charge increments either counter: a nested callback exception is re-raised unchanged; construction exhaustion increments its own operations before refusing, while reach work has not yet incremented. Therefore operation-attempt counts are not automatic error-prefix measurements.

## Lifetime and whole-request limits

The original already holds `power`, `total`, `term`, and `following` as invocation locals. Rebinding an existing term local to the existing following value does not by itself establish an additional persistent cache entry or create a new rational payload. Both schedules already hold `following` between iterations. It does change alias identity: ordinary Fraction immutability and no-effect native dispatch must be proved before treating that existing reference as stable. A newly copied Fraction, a persistent receipt, added cache storage, or an extra retained numerical value must be priced separately. This review selects no such additional storage and no wrapper.

For a hypothetical separately proven design, complete matched-request saving would be the sum of eligible completed call opportunities, plus separately established matched interrupted-prefix opportunities, minus every new startup, per-call, rejection, callback, copied-value, output, cleanup, and changed later-work cost. Actual call counts, N values, target-cache misses, pi misses/hits, retries at other precisions, hook incidence, accepted/rejected gate paths, and the unexecuted failed-request tail remain unknown here. The C047 factorial/coefficient census does not establish any of them.

There is no positive complete-request ledger, completed candidate, or elapsed claim. In particular, no subtraction from the observed 100001 failure count supplies a complete request cost. Original28 remains 24/28; P11/P16/P23/L03 remain unresolved; C035 remains held including adverse timing. Caps, fixtures, current observers, exception identities, publication/retirement obligations and all release gates remain unchanged.

## Execution disclosure

Inspection used textual source reads/searches and standard-library file hashing/JSON construction only. Source-derived equations and exact integer inequalities were reasoned from the inspected source. No runtime module was imported, no archived driver was run, and no candidate or original request was executed. The coordinator owns publication and any documentation/metadata check; this independent review alone certifies no release gate.
