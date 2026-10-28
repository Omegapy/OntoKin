# C055 independent cost and continuation review

Reviewer: `/root/c055_cost`. Runtime source: final C054 commit `2aca5afb05a0320971ccaf9d9ce30904d120e249`, tree `7082ceb840e0ce4c2f30baccbdb527913e9fa2ca`. All findings below are source reasoning. No OntoKin import, numerical execution, endpoint generation, collector, test, benchmark or repository mutation was performed.

## Result

The native128 pi factory has the inherited 163-operation opportunity. Original lookup and final remember remain; there is no 164-operation credit. **Complete admission cost is unknown. No positive complete bound is established, and no numeric cost-based rejection is claimed.**

An eager first precharge immediately after the original lookup can change exception priority and call-capture behavior. The authority reviewer supplies a separate normal-return/rejected-fallback witness. Moving admission after the first small-atan square also does not automatically make it safe: the original next operation is an unticked `F(0)` call.

The dependency analysis does support useful reductions from C054: unused defaults and unused Fraction fallback cells can be omitted, shared globals can be authenticated once per proven stable shared dictionary, and function identity and code/globals authentication are alternative strategies. A complete concrete schedule still needs safe bootstrap, continuation-preserving rejection and every new charge priced before numerical work.

## 1. Conditional native operation ledger

`reach_reference.py` lines370–395 show that a positive `_atan_small` call with first strict stop N has one initial exact square, four exact operations per term, one final exact enclosure operation and one grid: `4*N+3` charges.

| Component | Charges under inherited native stop/branch assumptions |
| --- | ---: |
| atan(1/5), N=28 | 115 |
| atan(1/239), N=8 | 35 |
| Multiplication by16 | 5 |
| Multiplication by4 | 5 |
| Final subtraction | 3 |
| Factory | 163 |

Each nonpoint multiplication uses one scalar point, its own tick, two selected exact products and one grid. The final subtraction uses its tick and two exact subtractions; the native dyadic sum-enclosure return adds no grid tick. Original lookup and final remember add one each, explaining the inherited165 cold-call count.

These are structural counts conditional on native stop/branch assumptions. They are not a new strict-stop, endpoint, operand-domain or completed-request proof. No endpoint calculation was performed.

For completed matched candidate/original executions, use `saving = 163*J - A_new - Delta_remaining`. J counts actual completed cold factories replaced; A_new includes all new admission, precharge, certificate read, copy and retention work; Delta_remaining is the disjoint remaining candidate-minus-original work. Complete convergence is required before setting Delta_remaining to zero.

| Path | Accounting obligation |
| --- | --- |
| Original warm hit or lookup failure | No new gate cost; preserve original return or failure prefix. |
| Admitted replacement | Local saving is `163-A`, with complete new cost A currently unknown. |
| Rejected gate | Every reached new charge remains; there is no omitted-factory credit. Do not assume callbacks leave the fallback state unchanged. |
| Precharge, callback or resource failure | Preserve reached prefix and exception identity. Never append unexecuted suffix costs or use a completion formula. |
| Other precision/domain | Charge reached discrimination/rejection; claim no native128 credit. |
| Several calls | Count actual admitted cold calls and all rejected prefixes; no target-count multiplier or assumed setup incidence. |

## 2. Actual used dependencies and meaningful omissions

This inventory describes reached behavior, not a mandatory number of runtime checks. The native-work/no-external-callback variant reaches14 arithmetic callables, two Interval callables,18 Fraction callables and two work callables. The count36 is **not an operation lower bound**.

The arithmetic entries are `operand_limit.fget`, `_dyadic_denominator`, `tick`, `guard`, `exact`, `point`, `grid`, `_grid_domain`, `_sum_enclosure`, `interval`, `sub`, `_corner_domain`, `mul` and `_atan_small`. Fresh Interval construction reaches its generated initializer and post-initializer.

Fraction behavior includes `__new__`, numerator/denominator getters, four forward arithmetic wrappers and their four captured monomorphic delegates, `_from_coprime_ints`, `__bool__`, `__eq__`, `_richcmp`, `__lt__`, `__gt__` and `__ge__`. The currently used delegate is the forward-wrapper closure cell. A similarly named class attribute can change without changing that captured delegate; checking the class slot would test the wrong dependency. Native shared charging reaches `ReachExecutionWork.tick` and `charge`.

The following reductions are valid obligations for a candidate design:

- Authenticate behavior with either a retained expected function identity plus its mutable used state, or exact expected code plus the actual used globals/defaults/closure cells. Do not require original function identity merely because C054's blanket screen did so. Conversely, code identity alone does not authenticate globals or mutable cells.
- Group a module's globals after proving each accepted callable uses that dictionary. Check each used binding once during a proven stable callback-free interval. The readonly function `__globals__` reference can be known from a retained authentic function; its dictionary contents remain mutable. Repeated per-function scans are unnecessary when stability and sharing are proved.
- For exact Fraction operands, forward wrappers select the monomorphic delegate. Their unused fallback-operator closure cells can be omitted after the operand/branch proof. The selected delegate cells remain relevant.
- Arithmetic calls supply their required arguments; unrelated defaults need no blanket checks. Fraction's numerator default is unused, while denominator=None is consumed by one-argument `F(value)` calls. `work.tick` calls `charge()` with both default arguments; these defaults matter. A ConstructionBudget route additionally consumes its tick defaults and adds nested-check, counter, limit, clock and failure dependencies.
- The native tick/charge route does not read work-cache contents, cache generation or cache-entry limits. Finished-child metadata, caller target maps, active targets, sincos and early-publication tag/corridor checks are absent from the direct cold-factory replacement. Original lookup/remember still retain their own capture and observable behavior.

Current arithmetic bits, scale, work/check owners and both observer fields matter. Shared work's external check, observer, counters, operation/elapsed limits, started clock, counts map and operand limit matter. A native outer method does not imply a passive nested callback. Class/MRO/metaclass and descriptor authority, actual used globals/builtins/ABC checks, raw storage, observer capture, runtime trace/profile effects, concurrent mutation, lifetimes and fresh construction remain explicit unresolved requirements. Failure-only helpers can be omitted only when an admitted domain/headroom/elapsed proof makes their branches unreachable or an original-prefix-preserving fallback covers them.

No complete safe inspection/precharge schedule has been proved for this inventory. It would be misleading to turn its size into a universal numeric rejection bound.

## 3. Exception-priority witness for immediate precharge

Original `pi` evaluates the outer remember target, sub target, first mul and small-atan target, then `F(1,5)` before the first factory `exact.tick`.

Choose an empty native cache, passive key/domain methods, no observer hooks and a check callback whose lookup invocation returns normally. Its next invocation raises existing exception object B. Let current module binding F be a callable whose `F(1,5)` invocation raises distinct existing exception object A.

The original raises A before the post-lookup callback is reached. An immediate new `self.tick()` precharge raises B before it can inspect and reject the changed F binding. Catching/translating B to continue would alter callback behavior. This conditional source witness rejects that precharge-first placement. No hostile request was executed. It does not prove all conceivable placements impossible or authorize free preliminary checks.

## 4. Post-square opportunity and its unresolved bootstrap

For a future question, retaining `_atan_small`'s initial square means one original charge is already spent. The remaining native suffix costs `4*N+2`: **114** for the conditional N=28 call and **34** for N=8. These are omitted-suffix opportunities, not established net savings.

Immediately after square returns, the original executes `power,total = value,F(0)`, constructs `range(self.bits+8)`, obtains its first exact-operation call target and evaluates its arguments before the next original exact tick. An eager post-square precharge can again change exception priority: a current F proxy can allow the nonzero conversions needed by the completed square but raise A on F(0); a newly inserted callback can raise B first. Thus the seam itself does not close bootstrap or original failure order.

A substantive future source task would identify an **already reached original checkpoint**, preserve every original pre-tick call target/argument/local and captured observer, and specify exactly how rejection resumes the existing continuation. It must not restart a completed prefix or rerun callbacks. A proposed continuation object is itself retained/copied work that needs pricing and authority. No such plan is proved here.

If an admitted repair retains original prefix cost P, require `P+A_new<163` for the whole pi factory, or price the individual remaining suffix against its own114/34 opportunity. Original prefix charges cannot simultaneously pay for new checks and be claimed as saved work. Rejected/interrupted paths keep their actual prefix and new costs; the completed identities do not project beyond a refusal.

## 5. Review history and evidence limits

A provisional direct-read screen imposed four actions on each36 callable and ten state read/check pairs, producing164. The parent correctly challenged the necessity of that representation. It is withdrawn: no164 floor or numerical cost rejection is part of this review. Its exact earlier text is retained under `drafts/superseded-direct-read-screen.md` for review history only; it must not be presented as a selected candidate or final proof input.

`source-binding.json` lists named source/attachment hashes and actual inspected scopes. Runtime source bytes were fetched at the pinned final C054 commit and verified against provider Git blobs. Fraction analysis uses CPython v3.12.14 `Lib/fractions.py`, blob `e3a8bbcfb3ea5e016b218a69487983b97250433d`; it establishes no runtime observation or3.11/3.13 compatibility result.

Original28 remains24/28 historical; P11/P16/P23/L03 remain unresolved. C035 remains held including adverse timing. This reader question cannot repair the observed P23 producer refusal before reader entry. Actual setup incidence, full request saving and release acceptance remain unknown or pending.
