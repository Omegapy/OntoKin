# C056 independent cost review

Reviewer: `/root/cost_review`. Scope: source reasoning about the frozen `R56-first-term-read-compare-repay` schedule. Source commit: `8000959ad25e89d1794d1401c0f8c2960bcd18fc`; source tree: `5282f90bc12c321c67829ce6d7ce62c891b32424`. The exact inspected inputs and their hashes are in [result.json](result.json).

**The specified schedule fails its first-stage charge and continuation proof.** W1, W2 and W3 are supported as conditional source counterexamples. The rejection does not require a numerical endpoint, completed factory, measured request, complete admission-cost bound, or a universal lower bound on every possible design. No accepted numerical specialization follows from this review.

## 1. What the source establishes

In the pinned `reach_reference.py`, `_Arithmetic.exact` invokes its original `self.tick()` at line 127. Only after that invocation returns does line 128 evaluate `F(a)` and then `F(b)`. The first positive atan term dispatch is at line 380. Its square, `F(0)` initialization and loop setup have already occurred at lines 377–379. Consequently, this seam preserves the prefix that defeated C055's earlier eager schedules, but still has original events capable of raising before the next original charge.

`_Arithmetic.tick` captures both arithmetic observers, calls its check, then invokes the captured product observer and ordinary observer in that order. `ReachExecutionWork.charge` captures its work observer, invokes the external check, checks operation and elapsed limits, increments its operation/category counters, then invokes the captured work observer. A callback exception is stored and reraised without substitution. A failed callback or resource check need not increment the reach operation counter. `ConstructionBudget.tick`, when used by the external route, has its own nested callback and accounting order; a reach counter is not a complete shared-budget trace.

The adopted contract expressly preserves lower request limits, charges new lookups and checks, and requires bounded arithmetic to be precharged. The draft label inside `budget-counting.md` remains historical: `ADOPTION.md` separately establishes the adopted authority.

## 2. The three units are distinct

| Unit | R56 use | Consequence |
| --- | --- | --- |
| U | Original first-term checkpoint reassigned to the new raw `G['F']` lookup | U cannot also fund the displaced original exact operation. |
| V | New charge before the identity comparison | Its callback and resource checks precede the comparison and the original pending `F(a)` call. |
| W | New charge after the comparison rejects, before original arithmetic resumes | A saved frame does not prevent this repayment from introducing an earlier callback or resource failure. |

Separating the lookup and identity comparison avoids pretending that two new inspections consume one paid unit. Separating W avoids double funding the rejected arithmetic. Those accounting corrections do not establish correct event order.

## 3. Independent assessment of the witnesses

**W1 is valid for the specified schedule.** At the original first-term checkpoint, a bounded external callback may replace `reach_reference.F` with an existing callable R and return normally. Grant all stated passive-storage and charging assumptions. Original execution next invokes R through `F(a)` and raises existing E. R56 first reads R, then attempts V. If the next callback raises distinct existing B, R56 raises B before its comparison. There is no need to assume that the original factory completes. The failed V attempt is an actual reached callback event; it must not be reported as a successfully incremented reach operation.

**W2 is valid and reaches an explicit rejection.** Let V's callback return and let W's callback raise B. The stored R reference differs from F0, so I2 rejects. Original execution would already have raised E from `F(a)`. R56 instead raises B while attempting to fund the displaced arithmetic. Retaining the original exact/atan/pi frames does not repair this divergence. V succeeds and contributes one extra reach increment in this witness; W's raising external callback occurs before W's reach increment. Any external/shared counter changes require their own actual trace.

**W3 is valid without a later raising callback.** The constructor permits a positive reduced operation maximum. Choose the limit L so that the unchanged prefix reaches U with `operations=L-1`; U succeeds and leaves `operations=L`. With subsequent external callbacks passive and other limits adequate, original execution raises E from R(a) before another operation check. R56 attempts V, whose `operations >= max_operations` branch raises its actual resource exception first. No count beyond the allowed prefix or completed tail is needed. A possible external inherited charge before that reach refusal is not permission to treat the paths as equivalent.

These are source constructions, not executed hostile requests or observed recording outcomes. They reject R56's named event order. They establish no impossibility theorem for all optimizations.

## 4. The 114-versus-113 distinction

The inherited native positive atan count is conditional on the stop candidate N: `4*N+3`. One operation is the square; four are performed for each term; the final enclosure operation and grid add two. C055 supplies inherited candidates N5=28 and N239=8. This review performs no strict-stop or endpoint proof.

After the completed square, 114 or 34 units of original numerical work remain. At R56's actual seam, however, U has already returned. That unit has been charged even though its original arithmetic is still pending. Only **113 or 33 original future charge units** remain after this seam.

For a hypothetical matched completed execution, either accounting convention can be consistent:

- Use the post-square opportunity 114/34 and include the new I1 lookup, funded by reassigned U, in all new-work deductions.
- Use only the future-charge opportunity 113/33 and deduct additional successful units after U. Do not deduct I1's same U a second time.

Using 114 while omitting I1 overstates the saving by one; using 113 and charging I1 again understates it by one. Neither convention supplies an accepted budget. The complete admission, provenance, continuation-storage, certificate, construction and stability costs remain unknown.

On a fully resumed rejected prefix, V and W are two additional successful units relative to the original U-funded first term. That is a local accounting observation, not a claim that W1/W2/W3 reach that complete prefix, and not a whole-request bound. Interrupted paths must retain the actual attempted events and successful increments separately.

## 5. Assumptions that remain grants

The schedule grants charged provenance for the native globals dictionary G and expected Fraction F0, passive lookup behavior, an authentic charging route, and harmless retention/lifetime behavior. No construction or authentication procedure establishes those grants here. In particular, an ordinary dictionary type alone would not authenticate every potentially consulted object or rule out mutation. The expected-reference identity is not proof of immutable function code, globals, descriptors, closure cells or future binding stability.

The true branch leaves remaining authentication unselected. A comparison of the retained reference also needs a stability argument before any future use after V's callback. No costs for that unselected work may be invented as zero, and no artificial 164- or 180-operation floor is justified. Granting the favorable assumptions is legitimate for these negative witnesses: the specified candidate already fails even when those separate obstacles are set aside.

## 6. Review finding and scope limits

One nonblocking metadata correction was requested and resolved. The initial schedule's `seam.source_lines` was `[126,128,368,388]`; line 368 is the lookup return and line 388 is blank. The corrected schedule explicitly identifies exact lines 126–145, atan lines 370–387 with the first-term dispatch at 380, and pi lines 389–395. I reread the full corrected schedule at SHA-256 `27c60db4c9993bc6afa96540ea0e18dfbde98de0fd71d3270bada8d7c65c68b1`. Its scoped NO-GO status agrees with this review. The correction changes no witness or accounting conclusion; no finding remains unresolved.

No product module was imported or executed. No endpoints, numerical replays, requests, collectors, runtime tests, benchmarks, archived drivers or hosted jobs ran. The exact input hashes identify source inspection, not execution or release acceptance. Original recording outcomes, C035's held status and all remaining release gates are outside this review and are unchanged. Final core documents, actual metadata/documentation validation and publication need separate review records.
