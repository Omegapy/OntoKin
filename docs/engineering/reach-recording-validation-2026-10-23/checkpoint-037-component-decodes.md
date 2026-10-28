# Checkpoint 037: same-key quaternion component-decode feasibility

Date: October 25, 2026, America/Denver. Status: **source-only investigation complete; no-go for the evidenced one-decode optimization**.

## Decision and scope

The repeated w-component conversion identified by [C036](checkpoint-036-census.md) is mathematically reusable. A bounded, detached receipt can also be described. It does not provide a positive operation-saving design under the adopted accounting rule: the one omitted conversion would save one charge, while the new component lookup or admission requires at least one charge. Additional retention, publication, copies, unsuccessful probes and retirement cannot improve that bound.

This rejects the currently evidenced single-component opportunity and the proposed zero-added-charge argument. It does not prove that all component reuse is impossible, price an unimplemented algorithm exactly, or exclude a separately established multi-result opportunity. No runtime implementation, product request, timing cohort or candidate promotion was selected.

The investigation follows [HANDOFF-036](HANDOFF-036.md) and [its selected scope](checkpoint-036-next-scope.json). The full [GOAL](../../../GOAL.md), adopted semantics, original source fixtures, independent expectations and release gates retain their meanings.

## 1. Authority and exact source

The [adoption record](../../language-design/planar-reach-v0.1/ADOPTION.md) establishes OK-LANG-006/0.1.0. The preserved proposal labels in its frozen inputs do not remove that authority. The effective profile and language contract apply the actual rules in [budget-counting, section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse): real avoided numerical work need not be counted as executed, but new lookup, type/limit/claim checks and copied logical values remain charged. Bounded storage does not make additional logical work free.

| Identity | Value |
| --- | --- |
| Observed C036 publication parent | 96b8f05571fecaf8babb3b6c000b4a829f0a9fb3 |
| Parent tree | ee1b241fb5d5de8b3ac965f9ad0063928a393190 |
| Held candidate whose unchanged source is reviewed | 4ca73909f861fe4bef9694787473621c1d21c140 |
| Held candidate tree | 87c949b238055af1ce368c694e1d5683c8aeacde |
| Accepted reach runtime | d2f0088c4f3c1f570630334804a5a8f78e0105ac |
| Observed main | 2bb4588e121fcfe99b4d42c734b15b38362f3642 |

The [source verification](checkpoint-037-validation/source-verification.json) checks all **2,065 tracked files / 461,840,089 bytes**, including file modes and exact Git blob identities, against a fresh complete GitHub tree. The original local commit object hashes exactly. Runtime, tests, tools, workflows and the adopted reach sources/contracts are identical to the held candidate in the named scopes. History is shallow; no historical object completeness is claimed. This verification executes no product code.

Source anchors below refer to those exact bytes. The [checkpoint index](checkpoint-037.json) gives the relevant SHA-256 and Git blob bindings. The later enclosing documentation commit is a publication identity, not a new runtime execution identity.

## 2. What the original path does

The relevant file is [reach_conformance.py](../../../ontokin/reach_conformance.py).

| Source anchor | Existing behavior |
| --- | --- |
| _Bounds.value, lines 129–140 | Charges independent_bound_decode, checks supported input type/finite value, creates the exact Fraction, checks result widths, then returns. |
| _recording_vector, lines 1311–1329 | Admits each actual supplied vector, including general finite binary64 width bounds and the ordinary decoder for narrower domains. |
| _small_proof_values, lines 1367–1373 | Requires exact Fraction values with numerator and denominator widths at most 256 bits. |
| centered current/checked/l1, lines 1812–1843 | Checks source receipt, owner/callback identity and latched live domain; decodes each nonzero component, then computes current subtraction, absolute error and L1 accumulation. |
| centered reused, lines 1862–1883 | Admits an identical whole proof; a successful hit charges independent_centered_endpoint_reuse. A predicate mismatch returns before that charge. |
| quaternion comparison, lines 1906–1932 | Keeps sign selection, existing whole-proof search, current L1 calculation, radius, factor two and claim checks. |
| result publication, lines 1943–1952 | Publishes a complete comparison with two sealed seven-field proofs. No individual quaternion decode is retained. |
| _key_comparisons, lines 1957–2056 | Builds current results, copies valid stationary previous rows, tries centered comparisons, then performs ordinary interval fallback. |

In l1, raw zero already bypasses decoding. For a nonzero component, only a decoder call that returned normally and passed checked/current and the 256-bit gate could supply the proposed operand. A failed decode, failed small-domain check or incomplete donor endpoint cannot publish a completed donor receipt.

The existing orientation payload contains the actual quaternion, selected expected center, radius, typed claim, completed total error, a magnitude placeholder and operand domain. The exact component conversion is absent. Recomputing Fraction(raw) from that payload is another conversion, not reuse of a retained result.

## 3. Numerical feasibility and its limits

For an exact native finite nonzero float, identical binary64 bits determine the same exact rational conversion. This fact is independent of the expected source center. A conservative generic rule could reuse a completed donor conversion only when both actual raw inputs are exact native floats with identical bits and the detached numerator/denominator belong to that successful conversion. It need not accept integers, bools, opposite signs, Fraction subclasses or equal values with different native types.

C036 identifies bits **3feb04bc00000000**, converted to **442671/524288**. The numerator uses 19 bits and the denominator 20 bits. The current right-forearm w decode had already completed when the following error addition reached the cap. The donor's individual decoded result was not retained by existing source.

The exact source centers differ: right_z + left_z = -97 / 2^128, and right_w - left_w = -40 / 2^128. Consequently, a scalar conversion receipt cannot transfer the current subtraction, absolute error, accumulated distance or whole quaternion proof. Matching zero components offer no omitted decoder charge because the original code already skips it.

### General binary64 width bounds

A normal binary64 number has exact form sign × (2^52 + fraction_bits) × 2^(exponent_bits - 1075). A subnormal has exact form sign × fraction_bits × 2^-1074. After reduction, a finite binary64 numerator has at most **1,024 bits** and its denominator at most **1,075 bits**. These are the existing _recording_vector bounds, not an assumption that all inputs came from binary32.

The optional centered proof has a smaller domain: both decoded value and current expected component must independently pass the existing **256-bit** Fraction gate. A value such as 2^-300 is finite binary64 but has a 301-bit exact denominator; it must retain the original charged decoder and centered-to-interval fallback. All live operand domains other than exact native integer 32,768 retain ordinary behavior. A narrowed domain stays invalid for the optional attempt even if a later callback broadens it.

Only the raw conversion could be omitted. Fresh antipodal sign selection, expected source values, subtraction, absolute error, ordered accumulation, radius addition, multiplication by two and current typed claim checks remain. Every surviving arithmetic operation retains its original prospective and result width guards.

### Detached copies

Retaining a mutable Fraction alias is insufficient. A candidate packet could store the already reduced exact native integer fields. A fresh operand would require admitted native storage construction. The accepted field helper at lines 2963–2970 uses object.__new__ plus original native numerator/denominator slot assignment, avoiding numerical reduction.

Fraction(n, d) must not be described as a free copy: the ordinary constructor performs reduction work. The reduction-free alternative still creates a copied logical value and requires its own accounting and native admission. Neither mechanism repairs the positive-cost failure below.

## 4. Bounded storage and lifetime argument

This is a structural construction used to assess feasibility, not a selected implementation.

Use one fresh authority object per _key_comparisons invocation, bound to the actual arithmetic/work owners and recording context. Require a native geometry map with at most 64 rows before enabling the optional route; larger or unsupported shapes use the unchanged path. This is a sufficient optional bound, not a new product object limit. The source-plan 64-target/object restriction is supporting context; it does not automatically bound arbitrary completed/helper records.

Each successful donor row can hold exactly four optional positional slots. A slot is absent or contains native 64-bit raw identity and detached numerator/positive denominator, each at most 256 bits. There are at most **256 published scalar slots**. A donor's at-most-four staging slots and a recipient's at-most-four detached operands are fixed local scratch, with at most 264 slots under a deliberately loose bound. Identity/owner/context references and tuple counts are fixed per row; no source graph is copied. This is a logical shape bound, not a measured Python byte allocation or permission to enlarge either existing 256-entry numerical cache.

Publish only after the complete original donor comparison succeeds. A whole-proof hit that did not decode components cannot invent fresh component provenance. A failed or insufficient donor contributes no reusable packet; any work already spent on staging remains overhead.

Existing records cross key boundaries. _key_comparisons copies stationary rows with dict(previous[carrier]) at line 1988; the caller eventually assigns previous = following at line 3442. A fresh token alone prevents stale use but does not remove stale retained state. A valid construction must strip optional packets before a successful return, invalidate the scope authority on every exit, and clear owned storage in a pinned non-raising finally path. Nested calls and replays use different authorities. No cross-clock sharing or resurrection after retirement is allowed.

An original traceback can retain aliases to failed local objects after cleanup. Such bytes cannot be promised to disappear while preserving the traceback. They must remain inert diagnostic data: the retired authority can no longer authorize reuse. Cleanup preserves the original exception and cannot spend a new fallible operation after failure; any required cleanup work must have been accounted for in advance. This constraint adds to the cost obligations rather than waiving them.

## 5. Native dispatch, ownership and fallback obligations

The centered current() function is necessary but insufficient for the new protocol. It checks current source values/seals, owners, callback identity and domain; it does not prove all decoder/storage behavior native.

A conservative hypothetical path would require exact original _Bounds and ReachExecutionWork types, original methods and storage descriptors, pinned function code/defaults/closures/globals/builtins, bit identity helpers and native Fraction allocation/field access. Pin the exact Fraction MRO and inherited Rational, Real, Complex and Number storage descriptors before reading any added operand fields. C035's inherited-descriptor regression and repair show why checking only Fraction's own dictionary is insufficient.

The patterns in _certificate_term_native and _certificate_fields_native, lines 2696–2891, provide relevant admission structure, not a complete ready-made gate. The C035 MRO/storage extension is in [reach_reference_center.py](../../../ontokin/reach_reference_center.py), lines 1291–1318. Any future implementation must bind every dependency it actually omits or introduces.

Decline the optional route for foreign callbacks, existing observers, active trace/profile hooks, replaced instance/class dispatch and narrower domains before new operand probes. The only work callback allowed by the conservative construction is absent or the exact native ConstructionBudget.tick whose check is None. Do not add an observer to make arbitrary callbacks eligible. A callback can install foreign behavior and restore it before a post-call comparison; entry and exit equality alone do not establish native execution.

Donor admission precedes the original decoder and repeats after its surviving callback and result guards. Recipient admission checks current native storage, owner, same-invocation authority, typed raw identity and live domain immediately before an omission, and after every preceding surviving callback. Original source validation still runs; no per-component source traversal is introduced. Scalar identity cannot replace source-center/radius/claim validation.

[ReachExecutionWork.charge](../../../ontokin/reach_numeric.py), lines 71–94, preserves external callback, budget/elapsed checks, count update and observer order. A callback exception remains the original exception, including its callback_error identity. A failed added admission is a real failed operation, not a harmless cache miss. Fallback uses the same remaining work allowance and preserves original errors; it cannot resume the capped request or restore its counter.

## 6. Complete accounting inventory and decisive lower bound

The [machine-readable ledger](checkpoint-037-cost-ledger.json) records the stage inventory and all fallback cases. No exact implemented total is invented for an unimplemented design. Let the added operation difference be:

**Delta = E + R + P + L + A + C + T + F - D.**

| Term | Work requiring coverage |
| --- | --- |
| E | Additional generic eligibility and native/storage/type/domain checks. |
| R | Capture and retention of completed decoded fields. |
| P | Packet publication and its bounded receipt/seal checks. |
| L | New component lookup/packet examination, including misses. |
| A | Reuse admission and post-callback re-admission. |
| C | Detached logical result copies; any reduction actually performed. |
| T | Retirement and cleanup work, preaccounted where failure must preserve an original exception. |
| F | Additional fallback/replay work after optional processing. |
| D | Original decodes actually omitted; never zero shortcuts or hypothetical tail occurrences. |

Every actual task must be assigned exactly once in a concrete ledger. The terms do not require one charge per Python field read and must not double-count a single admitted semantic operation. For this decision, grant all uncertain terms zero as a favorable lower bound, and count only the unavoidable new component lookup/admission. For hypothetical successful reuse of this one evidenced conversion, **D would be 1**. The new lookup/admission requires **L + A >= 1**, so **Delta >= 0**. Zero assigned to uncertain terms is not permission to execute them uncharged.

| Selected work | Original pair | Most favorable justified reuse lower bound |
| --- | ---: | ---: |
| Donor's original conversion | 1 | 1 |
| New recipient component lookup/admission | 0 | At least 1 |
| Recipient's original conversion | 1 | 0 |
| All other added protocol work | 0 | Optimistically 0 for the inequality only |
| Total | **2** | **At least 2** |

This bound is enough to reject a positive-saving design for the evidenced occurrence. A separately charged publication or copied logical result makes it worse. It does not assert a complete-request cost or infer the unvisited tail.

### Why the original sign checkpoint does not cover the new query

The sign charge still pays for the original representative selection. The existing whole-proof predicate keys actual quaternion, exact expected center, radius, typed claim and domain. C036's two available proofs first reject on actual-quaternion equality, before the successful whole-proof reuse charge.

The new scalar query has a different canonical key and proof method. Putting it inside that old loop does not turn it into already charged work. Nor does uncharged existing proof publication or _PositionOperands supply authority to expand the original sign unit. The closest accepted native-field decode transformation explicitly adds an admission charge and deducts it from gross savings; see [native-field derivation](../reach-certificate-native-fields.md) and source lines 2953–2970.

C034/C035 had a different proposed fusion: an already executed charged coefficient lookup could retrieve the same expanded record, with an additional publication charge. No equivalent paid scalar lookup exists on this whole-quaternion miss. The no-go finding follows from the adopted accounting rule and this control flow, not a fabricated cost per low-level instruction.

### Failed and unused routes

| Route | Required outcome and cost treatment |
| --- | --- |
| Unsupported shape/native storage/domain | Ordinary dynamic decoder; no foreign field probes for optional reuse. Any permitted added checks already performed remain spent. |
| Original donor decode fails | Preserve failed charge and exception; publish no receipt. |
| Donor later fails or centered proof declines | No completed packet; staging is unused overhead. |
| Packet publication/admission fails | Preserve the real request failure and original exception; do not refund work. |
| Missing, unequal, stale, replaced or foreign packet | Keep spent lookup/check costs and run ordinary decoding/fallback on the same allowance. |
| Surviving callback narrows domain | Re-admit afterward; latched centered fallback remains. No fresh allowance or later broadening can validate a stale optional receipt. |
| Successful scalar hit | Omit only its completed duplicate conversion; all source/sign/error/radius/claim work remains fresh. |
| Existing whole-proof hit | Preserve original path; there is no additional component decode saving to count. |
| Later arithmetic or claim fails | Preserve that failure; a local gross omission is not a completed request. |
| Success, fallback, replay or exceptional exit | Retire packet authority and owned storage; no cross-clock propagation or diagnostic-alias resurrection. |

## 7. Independent review and correction record

Three read-only reviewers independently inspected numerical equality/widths, storage/lifecycle/native dispatch, and costs. Initial suggestions that fixed metadata could automatically fit under the sign tick were withdrawn after direct review of the adopted counting rule. A mathematically valid Fraction(n, d) copy suggestion was also corrected to distinguish reduction from native detached slot construction. These were review hypotheses, not executed implementations or measurements.

All three final reviews agree: numerical identity and bounded lifetime are possible in principle; lawful positive savings for the one evidenced conversion are not established. The [review record](checkpoint-037-reviews.json) preserves the correction, final dispositions and source anchors. The final draft also receives an independent wording/scope check before publication.

## 8. Verification, disposition and next scope

Only source/tree verification and the required documentation preservation/link check belong to this checkpoint. Their exact inputs, commands, streams and results are retained in [checkpoint-037-validation](checkpoint-037-validation). No new runtime tests, timing pairs, P11 requests, original28 run or numerical analyzer were needed to decide this no-go. C036's existing archive remains unchanged and was not replayed as new evidence.

The accepted runtime remains d2f0088c, C035 candidate 4ca73909 remains held, and the latest complete original suite remains C035's **24/28**, with P11/P16/P23/L03 capped. C035's 29 focused methods, 3,093 regression methods and seven local checks retain their original candidate identity. They are not newly executed C037 validation. Main and all other-owner refs remain unchanged; no integration lease or merge belongs to this scope.

The [next bounded task](checkpoint-037-next-scope.json) moves to a **neutral complete-P16 retained-clock failure census**, subject to fresh ownership reconciliation. It uses a new evidence branch and the exact unchanged held candidate for paired control/capture, preserving P16's original four-second horizon, integer fps 1, helpers false and all limits. First establish its actual current failure and complete clock/input costs; do not preselect an optimization or infer a full deficit from the 100,001 refusal. This is a newly selected future diagnostic, not executed C037 work.
