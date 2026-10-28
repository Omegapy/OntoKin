# C051 independent numerical and authority review

Reviewer: `/root/numerical_authority`. Date: October 27, 2026, America/Denver.
Parent source: C050 commit `492b0e0edb5eb71e058fc29af059992b3a7952cb`, tree `ebc9e155ee98b37e56199dde987774ff38960d81`.
The coordinator owns the C051 review branch under [Issue 26 scope 6448305659](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6448305659). This review changes no runtime source, test, fixture, prior evidence, shared status, or integration state.

## Result and scope

**The adjacent quotient identity is sound under a complete native, non-effectful domain. That conditional theorem is not an admission mechanism. Bare local carry, or a one-time screen that admits arbitrary nested callbacks, does not preserve the original cancellation behavior.** A fully screened observer-free native callback graph remains a plausible mathematical domain. It needs its actual fresh-screen costs, all rejected paths, and exact request incidence before any implementation GO. The much larger actual centered-observer graph cannot be inferred safe from the name or identity of `_Guard.original` alone.

This is source reasoning. No OntoKin module was imported; no candidate, numerical series, request, runtime test, archived driver, or benchmark was executed. Read commands and file-hash metadata are the only executed activities. The exact selected input bytes are recorded in `result.json`. The coordinator's recovered snapshot is partial; reading a module does not establish complete request input closure.

## Exact transformation under review

The positive native path in `ontokin/reach_reference.py:370–387` first forms `square = exact(value, value, "mul")`. Each iteration then performs four charged scalar operations: term division, signed sum update, power multiplication, and following-term division. The strict comparison against `1 / 2**(bits+8)` chooses the first accepted next-term bound. The selected transformation preserves the first term division and carries each already computed `following` into the next iteration's `term` position. It preserves every sum, power update, following division, comparison, final remainder update, and grid operation. It introduces no persistent cache or numerical receipt.

Let `x` be the nonnegative exact native input and let `p_k = x**(2*k+1)`. At iteration `k`, native multiplication gives `p_(k+1) = p_k*x*x`. The already computed next term is

```text
following_k = p_(k+1)/(2*k+3)
term_(k+1)  = p_(k+1)/(2*(k+1)+1).
```

The denominators are the same integer. If the power, arithmetic meaning, limits, and dispatch remain unchanged across the gap, the quotient values are exactly equal. This is equality of rational numbers, not approximate floating-point reuse.

### Partial sums, first strict stop and enclosure

By induction, replacing only later term divisions preserves each partial sum

```text
S_k = sum((-1)**j * x**(2*j+1)/(2*j+1), j=0..k).
```

For `0 < x <= 1/2`, consecutive unsigned terms decrease because their ratio is `x*x*(2*k+1)/(2*k+3)`, which is strictly below one. The alternating-series remainder therefore lies between zero and the signed next term. For even `k`, the endpoints are `S_k-following_k` and `S_k`; for odd `k`, they are `S_k` and `S_k+following_k`. The source's `min`/`max` and final `grid` retain exactly these endpoint inputs. At zero, both endpoints are zero and the original first iteration still runs.

Every `following_k` remains identical, and the candidate keeps the source's strict `<` test. Thus the first accepted iteration is identical in this conditional domain. The outward grid still floors the low endpoint and ceilings the high endpoint on the same `2**bits` scale. This preserves the actual source enclosure, not just an equal midpoint. A successful negative input still recurses through the positive path and applies the original `neg`; a rejected magnitude still rejects at the original domain check.

These statements require the original threshold evaluation, range bound, `bits`, `scale`, Fraction constructor/operators/comparisons, and grid dispatch to retain their meanings. In particular, the loop bound is evaluated once by `range(self.bits + 8)`, but the stopping threshold reads `self.bits` afresh on every iteration. A stored initial bit count cannot replace that live behavior without an independently established domain.

### Useful finite bound at the default precision

With `bits=128`, the threshold is `2**-136`. The largest admitted positive input is `x=1/2`. After 64 iterations, its next term is `1/(2**129 * 129)`, strictly below `2**-136` because `129 > 128`. After 63 iterations its next term is `1/(2**127 * 127)`, above `2**-136`. Therefore the native unmodified mathematical path for `x=1/2` stops at exactly 64 iterations, and every smaller nonnegative input stops no later, provided no earlier resource or callback refusal occurs.

This bound is symbolic. It is not a measured request count. At this precision, the largest per-call gross opportunity is 63 omitted term divisions. Calls at higher precision have different bounds and costs; the source permits additional precision owners through `_canonical_targets`, so the default-precision bound is not a global request maximum.

## A concrete cancellation counterexample to incomplete admission

Use an exact `_Arithmetic` with `bits=128`, an exact `ReachExecutionWork`, and its native bound outer callback `ConstructionBudget.tick`. Keep native methods, native dictionaries, integer limits, and both arithmetic observer slots unchanged. The constructor explicitly supports a nested `ConstructionBudget.check` callback. Let that callback count invocations belonging to this call and raise a pre-created sentinel exception on invocation 197, remaining inert before then. The callback is already installed before the call; this example requires no asynchronous change, tracing, cache mutation, or later replacement of the outer bound method.

For `x=1/2`, the original successful mathematical schedule has `4*64+3 = 259` charged ticks; the bare carry schedule has `3*64+4 = 196`. On the original route, invocation 197 occurs during iteration `k=48`'s following-term division, after 48 complete iterations and that iteration's term, sum, and power operations. `ConstructionBudget.tick` calls the nested callback before incrementing its counter. The sentinel is recorded in `ConstructionBudget.callback_error`, propagates through `ReachExecutionWork.charge` with its identical object recorded in `work.callback_error`, and escapes `_Arithmetic.tick`, `exact`, and `_atan_small` unchanged. A non-`ReferenceError` sentinel also passes unchanged through the centered guard's `original` wrapper.

The bare carry schedule returns after invocation 196 and never calls the nested callback a 197th time. This difference is cancellation behavior, not a claim that a smaller honest work count is itself invalid. All rational operand widths in the finite example are comfortably below the fixed 32,768-bit cap; a simple unreduced-denominator upper bound for the 64-term sum is below 5,000 bits. As with any source-only control-flow example, an unrelated earlier elapsed-time refusal is excluded from the stated scenario; no elapsed measurement is claimed.

An added admission schedule changes callback ordinals and must be analyzed separately. The 197/196 numbers apply to bare carry. They are not silently reused for an unspecified future gate. The general defect remains that a screen of only owner types, outer bound-method identities, current map shapes, or an initial empty hook does not establish the behavior of a permitted nested callback at an omitted event.

This counterexample rejects that incomplete admission family. It does not reject a future rule that verifies `budget.check is None` and proves the rest of the transitive native graph non-effectful. It does not allege that any original P11/P16/P23/L03 run contained this hostile callback.

## Stronger native admission considered

### Observer-free native graph

A serious candidate can first retain the original input conversion and domain checks, then admit only a fully native positive call with plain stored state. The graph must include all dynamically invoked arithmetic helpers, live limit access, native Fraction construction and operators, the bound `work.tick` and `charge` methods, the actual external callback, any construction-budget callback beneath it, all numeric counters/maps and limit mappings, and the clock functions used by resource checks. Foreign observers, descriptors, non-native dictionary entries, mutable numeric aliases and changed code/default/closure/global/builtin state must either be excluded before reuse or independently admitted.

If this complete graph is native, no user callback is installed, no concurrent mutation mechanism is admitted, and the native counter/clock checks have their stated behavior, there is a sound route to a fixed-domain proof. This reviewer does **not** conclude that every such gate is impossible. The missing engineering mechanism is a fully specified, correctly charged gate that closes these dependencies without relying on an unverified cached Boolean or on callbacks that can change its premises.

`_certificate_term_native` in `reach_conformance.py:2762–2829` shows the scale of a related existing native screen. It checks class fields, function code/default/closure/global/builtin state, Fraction and numeric ABC machinery, trace/profile hooks, plain work state, the complete diagnostic-count map, and a native construction budget with `check is None` and native limit entries. It cannot simply be called for `_Arithmetic`: it requires a different `_Bounds` and `_CertificateWork` representation and excludes preexisting observers. Adapting it adds actual work; treating the whole new graph scan as one check would hide its new lookups and comparisons.

A concrete conservative screen considered with the cost reviewer contains 73 class-field identity probes before its other obligations: 18 arithmetic fields, 16 work fields, 12 construction-budget fields, and 27 Fraction fields. Every group includes the five chosen storage probes `__getattribute__`, `__getattr__`, `__setattr__`, `__delattr__`, and `__dict__`. Its remaining fields are:

| Class | Additional probed names | Total including storage |
| --- | --- | ---: |
| `_Arithmetic` | `exact`, `tick`, `guard`, `operand_limit`, `_dyadic_denominator`, `grid`, `_grid_domain`, `work`, `check`, `bits`, `scale`, `_recording_after_tick`, `_recording_product_after_tick` | 18 |
| `ReachExecutionWork` | `tick`, `charge`, `resource`, `external_check`, `_source_after_charge`, `counts`, `operations`, `max_operations`, `max_operand_bits`, `max_elapsed_ms`, `started` | 16 |
| `ConstructionBudget` | `tick`, `exceeded`, `check`, `operations`, `limits`, `started`, `profile` | 12 |
| `Fraction` | `__new__`, `__init__`, `__mul__`, `__truediv__`, `_mul`, `_div`, `_from_coprime_ints`, `__add__`, `_add`, `__sub__`, `_sub`, `__bool__`, `__eq__`, `__lt__`, `__gt__`, `__le__`, `__ge__`, `_richcmp`, `numerator`, `denominator`, `_numerator`, `_denominator` | 27 |

The screen retains an explicit absent-field comparison where a named member does not exist on a supported interpreter. Even this initial portion exceeds the default-precision maximum gross room of 63. It rejects this named fresh full-scan design for a positive default-precision call; it is not a universal lower bound on all future admission algorithms. The storage probes are chosen by this concrete conservative schedule, not asserted necessary in every conceivable design. Its unpriced code/global/default/closure and live-state obligations are not treated as discharged merely because the field list is comprehensive. The native positive domain itself remains mathematically meaningful.

### Actual centered observer graph

The source has real observer routes. `_Guard.original` installs its `observed` closure in `_recording_after_tick`, then executes an original multi-operation helper. `_Arithmetic.tick` captures both observer slots before calling the main check, invokes the captured product observer after a normal return, and then invokes the captured original observer. Removing a division removes that entire existing event. Checking only that the outer `check` object is unchanged does not replace the omitted calls.

The original observer calls `_Guard.current`. That method invokes `plan.admit_owners(reference)` and `batch.admit_owners()`, checks arithmetic/work/callback ownership, watched rational fields, watched records and interval cells, and optional product-session state. The plan path further calls `owned_by` and `_owners`; the batch path reads model maps, history lists, header values, lengths and owner identities. Native-looking guard identity is therefore not the full transitive admission.

The existing `_product_native` screen does not authenticate `_atan_small`, `_dyadic_denominator`, or the complete work-to-construction callback chain. Its arithmetic helper list is exact, guard, tick, cache synchronization, grid-domain and operand-limit; it is designed for a different product receipt. In particular, admitting a native work class and a native outer `ConstructionBudget.tick` is not equivalent to proving the nested `check` absent. Reusing that product screen as an atan authority receipt would need new proof and charging.

An admission requiring both arithmetic hooks to be `None` excludes any atan call that occurs while `_Guard.original` is active. It may still admit other calls, but source reachability alone gives no eligible request count. A scheme admitting the actual observer needs its own source graph, frozen state argument, and complete price. It cannot discard the observer or change its narrow-cap behavior to obtain eligibility.

### Limits and original error identity

`exact` ticks before converting/guarding its operands and before the prospective intermediate-width check. A former repeated division therefore re-read the live limit and re-admitted both operands at that event. Carrying the numerical answer does not by itself justify omitting those authority checks. The threshold also calls `_dyadic_denominator` and checks its current denominator width.

`_Guard.original` intentionally allows a narrowed cap to be latched while letting the original arithmetic execute its own prospective guard. It wraps actual `ReferenceError` objects as `_OriginalFailure`; the outer evaluation raises the stored original object. An early optional fallback, a different arithmetic operation at the same callback ordinal, or a new rejection cannot be assumed to preserve that original failure. Product-session observation likewise latches invalidation after the original callback and avoids preempting an original prospective refusal. These are explicit source behaviors, not incidental implementation details.

Adding one charged checkpoint for every omitted division restores at least `N-1` events. It consumes all `N-1` gross saved operations before additional admission, fallback, map audit or cleanup. That specific repair cannot produce positive operation savings. A cheaper complete policy has not been selected by this authority review.

## Request relevance and all-path limits

`pi` performs a bounded lookup before its two atan seeds; a hit performs neither seed. `sincos` calls `pi`, while `_atan_point` and `atan2` may also reach it or a separate `_atan_small`. `_canonical_targets` creates new `_Arithmetic` objects for the fixed precision schedule, with distinct caches, and can invoke `atan2` for shoulder and elbow values. Thus one retained pi key, one source action, or a coefficient-cache miss does not identify the request's number of atan calls.

The C047 coefficient census is not an atan call/iteration census. No exact original-request eligibility count was established in this review. It is particularly unsafe to assign a 63-operation opportunity to every original action or every coefficient miss. A separately reviewed passive observation would need actual call entries, exits/refusals, input rational fields, precision/limit state, observer/callback identities and cache relationships, plus neutrality against the unchanged original command.

Any future ledger must retain the original paths: zero and first-iteration calls have no gross room; negative calls preserve recursion and negation; over-range and malformed inputs retain their original pre-arithmetic failures; narrowed limits and interruptions keep original callback/error identities; nonconvergence and alternate precisions keep their finite loop bounds. Every new rejection check is still real request work. No failed-request tail or whole-request completed saving follows from these source equations.

## Recommendation

Accept the conditional rational identity and exact enclosure proof. Reject bare carry and the incomplete outer-owner admission that still permits arbitrary nested callbacks. Reject a charged checkpoint at every omitted division for positive operation savings. Record the concrete fresh native-screen cost rejection at default precision if the independent ledger verifies its field list. Keep narrower or amortized fully closed admission mechanisms explicitly unresolved; do not label all adjacent-term reuse impossible.

No implementation is approved by this review. A subsequent source target or passive observation plan must preserve the original 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 cache entries and 64 cursor updates. Original28 remains 24/28, with P11/P16/P23/L03 unresolved and C035 held. Those are inherited statuses, not newly executed results.
