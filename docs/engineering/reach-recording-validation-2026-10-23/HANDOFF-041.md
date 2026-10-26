# OntoKin continuation: HANDOFF-041

Date: October 25, 2026, America/Denver. Owner: `interactive-reach06-operation-reduction-20261025-c041-35d1`. Branch: `work/reach06-operation-reduction-20261025-c041`. Coordination: [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6408443031).

**C041 result: source-only NO-GO for unconditional `upper_binary64` cache bypass.** This is a different producer-side target from C040's rejected reader-axis/aggregate-counter design. A positive local P16 ledger was found, but a concrete generic counterexample disproves positive worst-case saving for the unconditional design. No runtime implementation was selected.

Read [the exact review](checkpoint-041-operation-reduction.md), [cost ledger](checkpoint-041-cost-ledger.json), [source binding](checkpoint-041-source-binding.json) and [independent review index](checkpoint-041-reviews.json) before continuation. The publication's `checkpoint-041-validation.json` records the actual documentation-check candidate and result; it supplies no product validation. Read the final publication commit from GitHub and the C041 closure comment rather than assuming this file can name its own containing commit.

## Startup and live ownership

1. Reopen current `AGENTS.md`, `GOAL.md`, `STATUS.md`, `README.md`, `docs/README.md`, adopted reach `ADOPTION.md`, `release-contract.md`, and budget-counting section 3. Read C038 retained census, C039/C040 qualifications, and this C041 record.
2. Refresh main, relevant branches and draft PRs, Issue #26, CI and any main integration lease. A timeout or old branch is not evidence that a worker stopped. Preserve published and unpublished work.
3. C041 starts from C040 head `0fab8a2fe00047ebf3f8778721d0a77b7a1d5420`, tree `bc1ef0444d6c284d4c78ed4bd626f396a935b54c`. C040 is draft PR #37, stacked on C039 draft PR #36. At startup PRs #27-37 were open drafts, main was `2bb4588e121fcfe99b4d42c734b15b38362f3642`, and its documented lease was released.
4. Held runtime remains `4ca73909f861fe4bef9694787473621c1d21c140`, tree `87c949b238055af1ce368c694e1d5683c8aeacde`; accepted reach runtime remains `d2f0088c4f3c1f570630334804a5a8f78e0105ac`. C041 changes only new evidence/handoff files. Its local review copy is documentation-complete but not a full execution checkout.
5. C041 acquired no main lease and changed no shared status, other-owner branch, runtime, fixture, oracle, tolerance, limit or workflow. Continue on a new separately owned isolated branch; declare any implementation scope only after its required positive review.

## Exact C041 findings

### Producer bound-rounding cache

Candidate: retain the existing `upper_binary64` input decoder, negative/zero behavior and complete numeric calculation, but replace its final `_reuse` with direct `calculate()`.

C038's original failed P16 request recorded 21 certificate-group visits, 261 actual bound calculations and 136 `nextafter` charges. The original source allows at most `21*21 + 21 + 1 = 463` conversions; therefore at most 202 remaining calls could be old nonzero cache hits. Removing lookup/insertion saves at least two charges per old miss; recalculating a former hit adds at most two. The resulting **conditional local bound is at least 118 saved operations**, before every new gate and without eviction credit.

That is not an actual optimization run or whole-request bound. The cache is shared, and changes can alter enclosing `certificate_group` hits and nested call sequences. No favorable or harmful total effect was established.

The generic counterexample is closed from source: `n` repeated native `Fraction(1)` calls with an empty cache cost `3*n+3` in the current helper versus `4*n` under direct recalculation. At four calls this is **15 versus 16**, and every `n>3` regresses. A fresh outer group key does not prove unique inner values. Unconditional bypass also suppresses foreign lookup/remember callbacks and may change their original exceptions. Native cache limit synchronization remains intact; C041 does not allege stale warmed native entries survive a cap change.

**Do not implement unconditional bypass or treat the 118 local bound as a general eligibility rule.** Different restricted policies remain possible in principle, with their own full source/work/callback/cache/exception and cost proof.

### Other routes remain separate

- A fallback-only reader flag does not remove hostile-capable category dictionary access from existing work charges. Full post-row authentication again reaches C040's inferred 266 categories against 205 comparisons; a new per-row witness costs at least 206. No complete cheap authority/retirement design was established.
- The producer phase-clock loop offers 404 comparison sites on the retained P16 source flow. A new 206-value copy plus 206-value admission costs at least 412. A different immutable-at-origin route remains unselected, with lifetime/domain/phase-slice authority unproved.
- **P23 unchanged-cache constructor substitution is rejected.** Storing p/q-only `RecordedTransform` under the existing full `_constant_pose` cache key can return it to full-source or reentrant callers that need `exact_velocity`, `exact_omega` and `position_error_m`.
- A P23 specialization preserving `PoseValue` and both cache layers has only three unconditional removable charges per eligible cold construction. If `m` is actual eligible outer-cache misses, it requires `A + sum(h_i) + L < 3*m` for setup, per-call and lifetime/storage/fallback costs. Neither current P23's `m` nor that complete bound is established. Historical 192 calls/1,934 inclusive operations are not cold-call or removable-work counts.
- P11 component reuse, held P23 static transfer and L03's 64-update retirement/direct reseeding remain separate. No cutoff, source schedule or independent predicate is changed.

## Next bounded task: C042, independent P23 constructor census

Use current source and already retained evidence to establish the actual cold versus warm constant-pose construction opportunities and their complete consumer contract.

1. Bind each retained observation to its exact runtime source. Do not assume historical observer counts apply to C040/C041.
2. Distinguish outer source-constant cache hits, cold noninverse constructors, cold inverse constructors, and inner stationary-cache hits. Write each original scalar/guard/cache sequence and first-failure order. Total `_constant_pose` calls are not equivalent to cold constructors.
3. Enumerate full-source and reentrant consumers of the existing key. Any private recording-only value requires distinct authority and lifetime; it cannot silently replace a full-pose cache result.
4. Derive a worst-case positive charged bound for one concrete eligible design, including actual added checks, retained entries, copies, fallback and cleanup, and its supported P23-specific opportunity. Require independent review before reserving runtime implementation. If the three-charge target cannot pay for its gate, close it promptly and select a larger distinct P23 sampling operation.
5. If current retained evidence cannot establish the needed cold/warm distinction, record the exact missing datum. This source-only checkpoint does not silently schedule a new product replay. A separately scoped diagnostic would need current source closure, untouched original request/caps, exclusive execution and preserved failures. Never resume a failed tail or reuse its allowance.

## Continuing product state

Latest complete original28 remains **24/28 (85.7%)**; P11, P16, P23 and L03 are capped. C035 remains held, including adverse L03 timing. Every historical focused/regression/local result retains its own tested source identity.

Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numeric-cache entries and the separate 512-category metadata bound. No fixture/key/schedule shortcut, relaxed tolerance, fresh allowance, discarded independent predicate or retrospective pass is permitted.

No C041 product request, recording or runtime-test run, numerical replay, benchmark, browser/native check, hosted/paid job, merge or accepted release result exists. Independent agreement is limited to the published source-only review. Documentation validation has its separate recorded scope.

Even 28/28 still requires actual Agent delivery and ten retrieved artifacts, independent rates/source work, CPython 3.11/3.12/3.13 roles, Khronos/Three/browser/native visualization, hostile/inherited roles, formal source closure, R01-R12/Q01-Q22, resulting-main verification and the larger OntoKin GOAL.

> Continue authorized Omegapy/OntoKin development from HANDOFF-041. Reconcile the live C041 branch/closure, draft PR stack, ownership, main and lease. C041 rejects unconditional upper_binary64 cache bypass: its retained P16 ledger is only a conditional local >=118 opportunity, whereas repeated native Fraction(1) calls regress at n>3, and callback/shared-cache authority remains unclosed. It also rejects placing RecordedTransform in the unchanged full constant-pose cache. Next independently establish P23 cold/warm constructor and consumer facts from current source/retained evidence, then require a complete positive charged bound before any runtime scope. Original28 remains 24/28; C035 is held; accepted reach and main are unchanged. Preserve every original cap, fixture, oracle and pending release gate.
