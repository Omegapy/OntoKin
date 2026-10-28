# C050 independent alternative-target nomination

Date: October 27, 2026, America/Denver. Reviewer: `/root/alternative_target`. Parent owner: `/root`. Owned scope: [Issue #26, comment 6447560284](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6447560284).

**Nominate C051 source feasibility of adjacent-term reuse in `_Arithmetic._atan_small`.** This is a new call-local arithmetic target. It is not another factorial-cache receipt design and does not select a runtime implementation. Positive whole-request net saving and current-request eligibility remain unknown.

This reviewer authored the alternative-target nomination, not the C050 factorial-origin proposal, root report, cost ledger or numerical/authority review. A later root-draft completeness audit must disclose this earlier nomination role. That audit is pending at this version.

## Inspected source and scope

The source is bound to C049 commit `e828ee2d54b3c2a5a82bb332327fdce982a0f7f2`, tree `574c75e870d50aed5e5e96b34b454389074350fe`. The 28 named source/governance/history inputs in [result.json](result.json) all match the freshly retrieved remote-tree Git blobs. They also match between the original C049 snapshot and the root's verified C050 copy. This is selected source and metadata inspection, not a complete checkout or review of every line of those files.

The target file, `ontokin/reach_reference.py`, has 259,809 bytes, Git blob `0e98ba4c2ba0c49dbf9672ecb1c0f0fd50079dbb`, and SHA-256 `db2fa3853e231e399ca2d48e5dea04455aeb0f80f11b4f42a478c34e0c717dc6`.

The review read relevant C037–C049 handoffs to distinguish this target from quaternion component reuse, clock ordering, bound-rounding cache bypass, constructor default receipts, angular reuse, cursor retirement and factorial-coefficient origin. No OntoKin import, product request, candidate numerical replay, runtime test, archived driver or archive execution occurred. Integer powers below are written mathematical inequalities, not a report of executing a numerical probe.

## Exact duplicated operation

The [original function](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference.py#L370-L387) computes:

| Source location | Work |
| --- | --- |
| 377 | Initial exact square of the argument. |
| 380 | `term = exact(power, 2*k+1, "div")`. |
| 381 | Add or subtract the current term from the partial sum. |
| 382 | Advance `power = exact(power, square, "mul")`. |
| 383 | `following = exact(power, 2*k+3, "div")`. |
| 384–386 | Test the first strict stop and form the final alternating-tail enclosure. |

If iteration `k` continues, the power left at line 382 becomes the next iteration's line-380 numerator. Its next divisor is `2*(k+1)+1 = 2*k+3`. Under unchanged native arithmetic and numerical values, the prior `following` is therefore exactly the next `term`.

The bounded proposal retains the original first term division, including its original guard, then carries the already computed `following` to the next `term`. The original local names already exist. No persistent numerical slot, cache insertion, wrapper, origin receipt or factorial-table dependency is proposed.

This equality is conditional on the native call domain. Python `Fraction` aliases, dispatch, callbacks and global bindings cannot be declared immutable merely because their ordinary values look native.

## Source-derived gross ledger

For a completed positive native call with `N >= 1` iterations and ordinary unchanged helper behavior:

| Component | Original | Proposed local carry before added admission |
| --- | ---: | ---: |
| Initial square | 1 | 1 |
| First term division | Included in loop total | 1 |
| Loop arithmetic | `4*N` | `3*N` |
| Final alternate endpoint and grid | 2 | 2 |
| Total | `4*N+3` | `3*N+4` |
| Gross difference | | `N-1` |

The separate `/root/cost_lifetime` reviewer independently confirmed these counts from source. Its agreement does not establish native admission, target incidence or execution.

Let `A_call` include every new lookup, type/limit/claim check, admission, local-value validation and changed observer/lifetime cost of an admitted completed call. Its net would be `N-1-A_call`. Rejected calls incur a separately counted `A_reject`; shared startup is charged once where actually incurred. The whole-request total must include all calls, rejected routes and side effects on later work. These costs and call counts remain unknown.

Adding a charged checkpoint at every omitted division consumes all `N-1` gross operations before other admission. Such a design cannot be reported as a positive operation optimization.

## Relevance to a new complete request

The [ordinary callers](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference.py#L389-L432) include `pi()`, which invokes `_atan_small(1/5)` and `_atan_small(1/239)` on a cache miss, and `_atan_point` after its original range reduction. `sincos` reaches `pi()` at line 621. [Canonical target construction](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference.py#L709-L735) creates fresh arithmetic at successive precisions and calls `atan2` or `pi`.

These are source routes, not an observed current-request census. In particular, this proposal can investigate complete-request setup independently of the later L03 factorial table and centered-cursor retirement. The C047 coefficient-cache census does not establish `_atan_small` call counts or iteration counts.

As a conditional mathematical illustration only, fixed native precision 128 gives the strict threshold `2^-136`. For successful ordinary `pi()` series, the stop follows from:

- `55 * 5^55 < 2^136 < 57 * 5^57`, giving 28 iterations for `1/5`.
- `15 * 239^15 < 2^136 < 17 * 239^17`, giving 8 iterations for `1/239`.

Those two hypothetical eligible completed calls offer `27+7=34` gross duplicate divisions. This is neither an executed measurement nor an assertion that a particular request has those eligible calls. The primary feasibility bound remains symbolic `N-1`.

## Finite C051 proof obligations

1. **Numerical equivalence and limits.** Prove equality of the carried value and the removed native division. Preserve the first strict stop, all partial sums, alternating-tail enclosure, sign handling and outward grid. Show that original operand and prospective-width refusal behavior remains valid throughout the admitted call.

2. **Current authority and post-following effects.** Cover `_atan_small`, `exact`, `tick`, `guard`, `_dyadic_denominator`, `grid`, `Fraction`, relevant class/code/instance bindings, globals/defaults/closures, work objects, maps and scalar fields. The original next-iteration division has a callback after `following` was computed; it can change the cap, mutate a retained rational, replace a helper or raise cancellation. Even the intervening threshold construction/comparison must remain native or follow the original path. A method-name lookup or unchecked Boolean is insufficient.

3. **Actual observer routes.** Trace `_Arithmetic.tick`, `ReachExecutionWork.charge` and `ConstructionBudget.tick`. If `_Guard.original` or a product/source observer is active on an intended eligible route, prove its current authority or explicitly exclude that route while preserving generic behavior. Do not assume that an observer-free screen admits the desired complete-request calls.

4. **All paths and errors.** Price positive arguments, zero, negative recursion and its final negation, out-of-range input, one-iteration stop, multiple iterations, finite nonconvergence, narrowed limits, malformed operands, replaced helpers, interrupted operations and fallback. Zero has no duplicate-division opportunity. Preserve original error/cancellation object identity and already completed effects; do not wrap or replace failures to make the candidate appear equivalent.

5. **Lifetime and whole-request cost.** Keep the reuse within the existing call-local variables. Account for any extra copy/reference/validation work and normal cleanup on interruption. Bound all newly executed screening on calls that receive no benefit. Do not allocate repeated misses or startup to the wrong path.

6. **Eligibility and bounded decision.** Establish eligible current-request calls from sufficient retained evidence, or prepare a separately reviewed passive observation plan if needed. Require a positive complete bound and independent numerical/authority and cost review before choosing code. A failed obligation ends this bounded hypothesis; it is not a universal impossibility proof.

The scope is source feasibility only. It does not authorize numerical replay, product tests, failed-tail continuation, changes to fixtures/caps/tolerances, or main integration.

## Secondary finding, unselected

[The quadrant result expression](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference.py#L634-L635) eagerly constructs all four choices. Native evaluation calls `neg(sine)` twice and `neg(cosine)` twice before selecting one. The selected quadrant needs 0, 1, 2 or 1 negations, respectively. A lazy branch therefore has a source-only gross opportunity of 4, 3, 2 or 3 charges per completed nonzero miss before every new check and callback obligation. This smaller opportunity is not the nominated C051 task.

## Status

Alternative-target nomination complete. C050 root-draft completeness audit pending. No runtime implementation, observed saving, recording improvement or release acceptance is claimed. All invoked commands have completed.
