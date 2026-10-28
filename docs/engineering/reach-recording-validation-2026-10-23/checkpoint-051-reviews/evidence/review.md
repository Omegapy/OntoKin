# C051 independent evidence review and next-source nomination

Date: October 27, 2026, America/Denver. Reviewer: `/root/evidence_and_next_target`. Coordination scope: [Issue #26, comment 6448305659](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6448305659).

**The inspected retained records do not establish current `_atan_small` call counts, completed iteration counts, eligible observer routes or complete-request saving.** If C051's bounded proposal is rejected, nominate a source feasibility review of reusing the request's existing arithmetic during matching-precision canonical-target construction. This investigates repeated independent pi construction across temporary arithmetic owners. It leaves `_atan_small` unchanged and does not select an implementation.

The reviewer authored this nomination and the evidence applicability assessment. It did not author C051's adjacent-term proposal, numerical/authority review or cost ledger. Any later final root-draft audit must disclose this nomination role.

## Source identity and inspection scope

The parent is C050 commit `492b0e0edb5eb71e058fc29af059992b3a7952cb`, tree `ebc9e155ee98b37e56199dde987774ff38960d81`. All 23 named inputs in [result.json](result.json) match that exact remote tree's byte lengths and Git blobs. Their total length is 1,079,572 bytes. The working source snapshot is partial; this selected-source binding is not a complete checkout claim.

The principal source, `ontokin/reach_reference.py`, has 259,809 bytes, Git blob `0e98ba4c2ba0c49dbf9672ecb1c0f0fd50079dbb` and SHA-256 `db2fa3853e231e399ca2d48e5dea04455aeb0f80f11b4f42a478c34e0c717dc6`. The controlling exact hash is also recorded in the input table. Relevant source routes and evidence schemas were inspected; every line of every named large runtime file was not reviewed.

This work used text inspection, exact source acquisition and metadata hashing. No OntoKin import, numerical replay, product request, runtime test, benchmark, archived driver or existing census script was executed. The C044/C047 binary archives and their internal members were not restored or newly audited by this reviewer. Their prior measured results below remain attributed historical records.

## What the retained observations can establish

| Inspected record | Actual observation scope | C051 inference it does not support |
| --- | --- | --- |
| [C047 L03 capture](../../checkpoint-047-l03-capture.md) | Original failed L03 pair; external wrappers at `gltf.validate_export` and `_key_comparisons`; 154 consecutive key calls and 311 ordered reader-cache snapshots. | Per-call `_atan_small` entry, local loop index, completed or interrupted series count, or canonical-target setup incidence. |
| [C047 census implementation](../../checkpoint-047-lifetime-review/census.py) and [boundary census](../../checkpoint-047-lifetime-review/census-001/boundary-census.json) | Reader-cache occupancy, coefficient keys, source domain and centered cursor boundary state. The source-led lifetime proof excludes capacity eviction only from key 0 entry to key 153's exception snapshot before cleanup. | An internal execution trace; exact lookup/hit counts; setup before key 0; a modified candidate's cache order; counts for temporary canonical arithmetic owners. |
| [C047 coefficient census](../../checkpoint-047-lifetime-review/census-001/coefficient-census.json) | Seven coefficient keys at the initial boundary and five later newly completed coefficient keys. | Arctangent calls or iterations. A coefficient key is a different calculation and is not a proxy for a pi or arctangent miss. |
| [C044 P23 angular census](../../checkpoint-044-angular-census.md) | Producer-side envelope and work-cache trace, stopped before independent reader entry. The observed request failed in the producer. | Calls in the independent reference's `_Arithmetic`, including `_atan_small` or `_canonical_targets`. |

The [C047 archive manifest](../../checkpoint-047-evidence-manifest.json) identifies retained files by hash and length. It is an inventory, not a substitute for reading the archived members. The inspected capture specification and census fields do not provide the missing per-call data. No assertion is made that every older repository archive lacks any useful arctangent evidence; those archives were not all searched.

Source routes alone also do not establish incidence. `pi()` calls the two arctangent series only on a cache miss; `_atan_point` reaches `_atan_small` after its branch-specific reductions; fresh arithmetic can be constructed at several precisions. Method appearance in a call graph does not tell us how many calls completed in a particular failed request or whether an admission rule accepts them.

Thus the correct current fields remain `eligible_calls = null`, `completed_iteration_counts = null` and `whole_request_net = null`. The `N-1` arithmetic opportunity remains conditional, without an observed whole-request multiplier.

## A distinct, larger source question

The proposed C052 question is:

> Can the first matching-precision `_canonical_targets` pass use the existing request-owned `_Arithmetic`, under a fully priced native admission, so that an independently completed pi enclosure is reused across distinct target constructions without changing the original precision schedule, numerical proof, errors, callbacks or cache limits?

This differs from carrying an adjacent arctangent term. It changes the lifetime of the existing independent arithmetic owner at a specific call boundary. The original pi and arctangent implementations remain intact. It also differs from the rejected factorial-origin hypothesis: there is no affine coefficient construction or raw factorial tuple receipt. The remaining origin problem must still be solved for the actual pi payload; changing the target does not remove it.

### Existing owners and exact call route

In [supplied-byte validation](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/ontokin/reach_conformance.py#L3507-L3555), `validate_reach_export` calls `build_reference(model, end=end, work=work)` before key comparisons. The original shared work remains the existing request work; a new allowance is not created.

[`build_reference`](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/ontokin/reach_reference.py#L807-L815) creates one `_Arithmetic` at its default precision. [`ReachReference.__init__`](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/ontokin/reach_reference.py#L2253-L2286) retains it as `self.a` and then builds the independent event ledger. Its cache is the existing native dictionary bounded by `MAX_CACHE = 256`; it is distinct from `ReachExecutionWork._cache`.

At a new reach start, [`_event`](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/ontokin/reach_reference.py#L3489-L3503) already caches completed target pairs by `(lengths, target, branch, limits)`. Only a key absent from `_targets` calls `_canonical_targets`. Consequently, repeated actions with the same key must not be counted as fresh canonical construction opportunities.

[`_canonical_targets`](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/ontokin/reach_reference.py#L674-L735) first uses the parent exact arithmetic for its algebra. It then creates a new `_Arithmetic(arithmetic.work, arithmetic.check, bits=precision)` for each precision attempted. Each child starts with an empty cache, no two recording observers, its requested scale and the same underlying request work. Its pi calculation can therefore be repeated in another child even though the parent's ordinary source pose calculations have already completed the same independent pi enclosure.

The bounded initial design to review is **parent reuse only for the first scheduled precision, 128, when the parent has exactly that admitted current precision, scale, operand domain, native work/check dispatch and no active recording observer**. Every other precision and rejected call retains fresh child construction. This is a proposal to prove, not a determination that a simple type/field screen suffices. An existing callback can still change those facts, and a previously cached payload does not authenticate itself.

The first source review should compare direct use of the existing parent against any alternative that copies a completed enclosure into a fresh child. Select one schedule before pricing it. Copying would create additional logical values and possibly a new retained numerical occurrence; it cannot be treated as free or mixed into the direct-use ledger.

### Why the opportunity is larger

For the conditional native 128-bit `pi()` miss, C050's mathematical inequalities identify 28 completed `_atan_small(1/5)` iterations and eight completed `_atan_small(1/239)` iterations. The original helper totals are respectively `4*28+3 = 115` and `4*8+3 = 35` operations. These 150 series operations are the largest part of the repeated construction.

Under ordinary nonpoint output enclosures, unchanged domain and successful completion, the complete pi miss has this source ledger:

| Component | Original charged work |
| --- | ---: |
| Initial pi lookup | 1 |
| `atan(1/5)` series | 115 |
| Scalar-by-interval multiplication by 16 | 5 |
| `atan(1/239)` series | 35 |
| Scalar-by-interval multiplication by 4 | 5 |
| Final interval subtraction | 3 |
| Remember completed pi enclosure | 1 |
| **Complete miss** | **165** |
| Existing eligible pi hit | **1** |
| **Conditional gross difference** | **164** |

The separate C051 cost reviewer independently confirmed this source count with the stated nonpoint/domain/success conditions. It is not a measured saving, a universal cold-path count, or an assertion of an eligible cache hit in L03/P11. Native endpoint collapse, interruption, additional cache synchronization, fallback and new admission must be handled separately. Even the conservative duplicated-series subtotal of 150 offers more room for a finite admission than the adjacent-term pair's 34 gross divisions at this precision.

The [L03 authored source](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/docs/language-design/planar-reach-v0.1/draft2-supplements/sources/l03-completed-action-new-owner.ok) names two different targets and opposite branches. The [P11 source](https://github.com/Omegapy/OntoKin/blob/492b0e0edb5eb71e058fc29af059992b3a7952cb/docs/language-design/planar-reach-v0.1/sources/p11-complete-segmented-character.ok) also names two different reach targets and branches. These source facts make the target worth examining. They are not a fresh build, constructor count, precision census or proof that a valid parent pi value is present at either call. P23's producer failure cannot benefit from a reader-only change before it reaches that reader.

## Required proof and accounting before selection

1. **Numerical and owner equivalence.** Bind the exact source equations and the parent/child precision, scale, work, current cap and callback relationships. Preserve `_canonical_targets`' original precision order, first successful rounding, closed joint limits and all `_Uncertain` refinement behavior. Preserve the original inner arctangent first strict stop and outward pi enclosure; do not substitute production pi values or library transcendental answers.

2. **Current independent origin.** Prove that every reused pi endpoint comes from the admitted independent calculation at the exact key and domain, with no unsupported writers or aliases. The existing `Interval` is a frozen dataclass around Python Fractions, not a hard immutable security boundary. Exact class, shape and numeric type alone cannot prove origin. Price any new value/copy/identity checks and close all callbacks, helpers, globals, descriptors, defaults and closures actually traversed.

3. **Original refusal and cancellation behavior.** Parent reuse must not hide callbacks or live operand refusals that child construction would execute. The H1-style nested callback from C051 still defeats a shallow native admission. A charged replacement checkpoint for every skipped operation would consume the numerical saving. The review must instead establish a concrete eligible native domain or reject this design; no unchecked native Boolean or free monitoring is available.

4. **Original observers and ownership.** Source setup precedes key comparison in the current reader route, but that ordering is not proof of hooks being absent for every caller. Prove the actual eligible setup route and retain original fresh construction for active observer or custom-work calls unless their current behavior is fully admitted. Preserve parent cache/work ownership, nested state and original error object identity.

5. **Bounded storage and changed cache work.** Direct parent reuse creates no extra cache container, but it can insert/promote pi earlier, keep it longer, change eviction order and affect later hits. Charge all actual new lookups, checks, values and publications. The existing 256-entry cap stays shared by that reader cache. C047's original no-eviction interval starts after setup and cannot establish candidate cache neutrality or complete-request saving.

6. **All-path costs.** Price one-target requests, already cached target hits, a cold parent pi, an already present pi, multiple distinct targets, precision mismatch, refined precision passes, changed cap, malformed/custom owners, active hooks, rejection, exceptions and cancellation. Construction of `_Arithmetic` itself has no charged tick; do not count eliminating a constructor as an operation saving. Startup must be charged once where it occurs and included even when no benefit follows.

7. **Actual request relevance.** Establish eligible canonical calls, completed precision passes, parent pi availability and the effects on the remaining request from sufficient exact evidence. Keep counts unknown until that happens. Require independent numerical/authority and cost review of a positive complete bound before an implementation plan.

This proposed source review is finite. If it cannot close safe admission or its complete bound, reject the particular design and record why. It must not become an unbounded search through cached receipts or change the adopted contract, limits, fixtures or expected records.

## If observation is still needed

Prepare a separate, independently reviewed passive setup-capture plan only after a viable source design identifies the required facts. The necessary record is an ordered ledger of actual canonical calls and precision owners, not another coefficient census. It must distinguish the parent owner from each fresh child; record native bits/scale/cap, exact input and target-cache key, pi entry/exit state, each completed/interrupted pi construction, original callback/observer route and complete shared-work/category differences.

Do not assume an outer `_canonical_targets` wrapper alone reveals child precision or pi calls: those are internal locals. Likewise, the prior C047 boundary wrappers do not supply this information. A proposed internal observation technique must first show that it cannot change native eligibility; trace/profile installation or arithmetic monkeypatching is not automatically neutral. If an observer cannot safely collect those fields, retain the insufficiency instead of inventing a call count.

The concrete planning stages are:

| Stage | Required output and stop condition |
| --- | --- |
| O1: source-only collector design | Pin one fresh original L03 request with end 4, fps 1, helpers false and original tolerances. Identify the exact call boundaries and all native gates active from `build_reference` entry through canonical setup completion. Propose one mechanism that collects the internal fields without replacing numeric methods, callbacks or observer hooks and without trace/profile changes that alter those gates. Stop with a bounded design rejection if no such mechanism is established. No mechanism is selected by this review. |
| O2: bounded schema and authority review | Define finite event/member/byte limits before allocation; retain copied native primitives instead of live frames or numerical-result owners. Separate per-process raw identities from stable source/call ordinals. Bind parent/child work identity and complete callback nesting, exact target key, precision ordinal, start/return/refusal, original work counters, pi-key availability and cache order. Every claimed absent event requires complete bounded coverage. Independent review must find no missing gate or unbounded retention before a driver is approved. |
| O3: separately authorized execution plan | Define exactly one fresh stock request and one fresh observed request from identical complete source/input closure. Both start from the beginning with their own original request allowance. Do not continue C047's failed tail or reuse its cache. Declare the actual exclusive window after other executors pause. This stage is a future plan, not current execution authorization. |
| O4: independent pair audit | Compare full counts/category maps, ordered cache state, options, program/source identities, callback identity assertions, native dispatch, underlying traceback and original error object assertions. Compare successful bytes/reports only if both requests actually succeed; otherwise retain failed product exits and any unvalidated bytes. Any observer failure, unapproved route, changed dispatch, unexplained mismatch or diagnostic overflow invalidates the census. Keep elapsed effects separate from numerical neutrality. |

For an arctangent incidence study, O2 must additionally expose completed loop indices and the exact zero/negative/range/refusal classification. Canonical call and pi-cache records alone cannot certify every `_atan_small` iteration. An earlier failed prefix constrains only what happened before its refusal; it never supplies the unexecuted complete-request tail or guarantees that a candidate will finish below the cap.

Any later capture requires a fresh original request pair, exact source/input closure, active exclusive executor window and unchanged caps. Compare complete work dictionaries, cache state, source/options, callbacks and error identity. Preserve both failed exits and disclose diagnostic overhead; no elapsed neutrality or completed tail may be assumed. The present C051 review prepares none of those executions.

## Status

Evidence applicability and distinct next-source nomination complete. C051 root-draft source/claim audit remains separate. No new runtime behavior, complete-request saving, recording pass or release acceptance is claimed. Original28 remains 24/28 and C035 remains held, including its adverse timing.
