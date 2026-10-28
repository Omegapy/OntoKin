# C056 authority and rejected-continuation review

Reviewer: `/root/authority_review`. Review date: October 27, 2026, America/Denver. Source commit: `8000959ad25e89d1794d1401c0f8c2960bcd18fc`; source tree: `5282f90bc12c321c67829ce6d7ce62c891b32424`.

## Decision

The three conditional source counterexamples reject the frozen `R56-first-term-read-compare-repay` bootstrap. The candidate can preserve the original active frames and still change the first exception: funding its additional inspection or repaying its displaced arithmetic invokes another checkpoint before the original pending `F(a)` conversion.

This is a scoped source rejection. It does not establish an executed failure, a complete gate cost, a numerical result, or impossibility of every specialization. The one source-line citation finding was corrected and reread. There are no unresolved findings for this frozen first-stage schedule.

## Inputs and role

The initial schedule SHA-256 is `09bbc186ef5c09d547913c56bcb1568a086c7f6198f86804d0c737c5b3186d5c`. The corrected reviewed schedule SHA-256 is `27c60db4c9993bc6afa96540ea0e18dfbde98de0fd71d3270bada8d7c65c68b1`. Exact input byte lengths and SHA-256 values are recorded in `result.json`.

The reviewer first read the supplied C055 README, handoff, authoritative next scope, feasibility argument, schedule, cost ledger and source bindings. The reviewer independently fetched immutable C055 `reach_reference.py` lines 1–405, `reach_numeric.py` lines 1–250, and the complete budget-counting document through GitHub, then checked their local full-file hashes. The current review reread local `reach_reference.py` lines 108–145 and 370–395, `reach_numeric.py` lines 38–103, and budget-counting lines 89–110. `AGENTS.md` was read completely. These are source reads; the complete-file hashes do not mean every line of the runtime files was reviewed.

Before the schedule was frozen, this reviewer identified the repayment exception-order witness and asked for separate funding of a binding read and identity check. The reviewer also requested that any passive storage or authority assumptions be disclosed as favorable counterexample grants. The parent authored the frozen schedule. This review is independent scrutiny of the frozen result, with those earlier contributions disclosed; it is not an independent invention of the same witness.

## Source findings

1. **The seam is reached after the relevant original prefix.** `_atan_small` converts the incoming value, compares it, completes the initial square, evaluates `F(0)`, establishes the range iterator, obtains `k = 0`, and enters the first `exact(power, 1, "div")` call. The original `exact` then completes its tick at line 127. Thus this schedule preserves the original events that defeated C055's G0–G2 schedules.

2. **The pending operation remains observable.** The next statement, `a, b = F(a), F(b)`, is at line 128. The first global `F` lookup and its call occur before the second conversion, guards, prospective operand checks and arithmetic dispatch. A completed tick does not establish that this pending call will return normally. The suspended exact frame retains its original `a`, `b`, `kind` and return path.

3. **Original captured observers must finish before admission.** The arithmetic tick captures ordinary and product observers before `check`, then invokes product followed by ordinary after normal return. Native work charging captures its observer before the external callback, checks operation and elapsed limits, increments counters, and invokes that captured observer. The schedule places the seam after all these events and propagates any prefix failure without starting admission. The counterexamples legitimately choose all observer slots absent.

4. **The units are separated.** U pays only the added raw global-binding lookup; V pays only the identity check; W pays the displaced first-term arithmetic if rejection reaches resumption. No completed square charge is reused. Successful retention of the active frames does not remove the need to obtain V or W before their associated work.

5. **W1 changes the first exception before any rejection decision.** At the reached original callback, replace the `F` global used by `reach_reference` with preexisting callable R and return normally. R raises existing E when invoked. Let the next callback raise distinct B. The original calls R(a) immediately after its completed tick and raises E. The candidate performs its granted passive binding read, then Q2 reaches that next callback and raises B. The separate Fraction binding used by `reach_numeric` is unchanged, so the mutation does not prevent the stated native work-charge prefix from reaching the seam.

6. **W2 changes the first exception on an actual rejected path.** Let Q2's added callback return normally, keep R current, and let the following callback raise B. The identity comparison is false because R is not F0. The candidate rejects but QR invokes the later callback before R(a). The original still raises E without either additional callback. This remains a failure even when the original frames and captured call targets are perfectly preserved.

7. **W3 is a permitted lower-limit case.** Native work construction permits positive limits below the maximum. A reached original U may increment operations from L−1 to its permitted maximum L; elapsed and other limits can remain adequate. The original next raises E in R(a). Q2 instead checks the already exhausted operation count and raises the native resource error first. No raising future callback is required. This case does not claim any historical recording used that allowance.

8. **The grants strengthen the rejection only.** Passive dictionary access, preauthenticated provenance and an authentic charging route are explicitly granted. They are not evidence that the complete admission program has funded or proved those properties. The failure survives these favorable assumptions, before an accepted path or endpoint proof is selected.

## Funding and continuation limits

Budget-counting section 3 requires new lookups and checks to be charged, while allowing genuinely avoided numerical work to remain uncharged. The frozen schedule correctly treats the first exact operation as displaced, not already performed. It cannot both use U for the lookup and count U again for retained exact arithmetic. Buying V or W introduces the demonstrated earlier checkpoint; running the displaced operation before its replacement unit lacks the schedule's required precharge. A projected later saving cannot pay an interrupted prefix. Suppressing B, replacing it with E, or replaying the outer expression does not preserve the original callback and continuation contract.

The first failure requires only the active exact continuation, its `F` global, native charge/callback order and original operation-limit checks. The complete future atan/interval dependency authentication is unnecessary to refute this bootstrap and remains unproved. No complete cost bound or endpoint analysis should be inferred from this review.

## Citation correction

Finding A56-01, **resolved**: `seam.source_lines` in the initial schedule listed `[126, 128, 368, 388]`. Line 368 is the end of `lookup`; line 388 is blank. The corrected schedule explicitly identifies `exact` at 126–145, `_atan_small` at 370–387, and `pi` at 389–395. The reviewer reread the updated states and witnesses and compared the complete parsed original/revised documents. Only the source-line metadata and the status wording changed. The status now states the scoped conditional NO-GO. This was a source-location issue, not a flaw in W1–W3.

## Execution boundary

This review ran only file reads, hashes and review-file generation. It did not import or execute product modules, construct a request or work object, run a hostile witness, generate endpoint constants, execute a numerical replay or collector, run runtime tests, change a runtime/fixture/limit, or mutate GitHub. The final core documents and publication will require their own subsequent readback.
