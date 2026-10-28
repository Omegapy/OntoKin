# C052 independent cost and cache-lifetime review

Reviewer: `/root/c052_cost`. Date: October 27, 2026, America/Denver. Source commit: `9aeab3e1b4e05e47a0284da55925f41cccc23964`; tree: `c661e9b40d5ba8390d4ed96725e41198f67655f9`. The coordinator recovered a partial snapshot and verified its file bytes against that published tree. This review binds its own 15 selected inputs in [the input manifest](input-manifest.json). It uses source inspection and metadata hashing only.

## Decision

No positive complete-request implementation is established for the reviewed direct-parent reuse schedules.

The exact successful native 128-bit pi opportunity is **165 operations for a cold miss versus 1 for an authentic resident hit**, or **164 gross**. The first canonical precision body uses only the pi cache family. It does not offer 164 for every pi call: its original fresh child caches the first completed pi calculation and reuses it for the remainder of that precision attempt.

R1's current type, owner, precision and observer screen does not prove the origin of a preexisting parent pi value. The authority review supplies a native poisoned-value counterexample. Even an authentic value cannot justify skipping an admitted effectful cancellation callback. A policy retaining one charged checkpoint for every omitted pi operation consumes all 164 gross room before other work.

R2's specified fresh inspection of every resident parent-cache entry adds at least m charged inspections for occupancy m. Its immediate net ceiling is `164 - m - A_other` on the strongest hot-pi path. At m=256 this is at most **-92**, before its other checks. This rejects that scan schedule at the stated occupancy, not every origin mechanism. A structural scan also fails to prove numerical origin by itself.

An empty-parent-only variant avoids importing a prior cached pi payload, but has zero immediate pi saving and no eligible call on the ordinary unchanged native, fixed-domain reference-construction route. Generic direct callers and changed-domain routes require separate proof.

No collector, runtime change, original request, candidate replay, test, benchmark or release gate is selected by this review.

## 1. Exact call and ownership boundary

The [independent source](../../../../../ontokin/reach_reference.py) constructs one request arithmetic owner in `build_reference` at line 815. `ReachReference.__init__` retains it as `self.a`, performs initialization, and then builds the event ledger. At a reach start, lines 3489–3499 form the existing target key from lengths, target, branch and closed limits. A target-key hit bypasses `_canonical_targets`; repeated authored actions cannot be multiplied into fresh canonical calls.

At lines 674–708, `_canonical_targets` uses the parent for exact algebra and sign decisions. At lines 709–735 it constructs a fresh child for each fixed precision in `(128, 256, 512, 1024, 2048)`. The reviewed substitution changes only the child choice for the first 128-bit iteration after the common algebra. Rejections and later precisions retain their original fresh child.

The fresh child has its own empty dictionary, requested scale, current operand-limit record and unset arithmetic observers. It shares the existing work owner. When work is present, its constructor derives `check` from the current `work.tick`; an old parent check binding is not automatically the same current behavior. Construction performs limit checks but has **no tick**. Removing it creates no operation saving and must not suppress its possible original refusal.

The native precision body calls `point`, `mul`, `sqrt`, `atan2`, `add` and `round64`, and their scalar/interval dependencies. In that reachable arithmetic graph, the only cache family is `("pi", bits, operand_limit)`. The body does not call `sincos`, coefficient caches or pose caches. Under stable native state there is at most one cold pi construction per precision attempt; subsequent pi calls hit the same child key.

## 2. Gross operation ledger

The source `pi` route uses an initial lookup, two fixed arctangent series, scalar interval multiplications, interval subtraction, and insertion. For the successful unchanged-domain native 128-bit route with its ordinary nonpoint enclosures:

| Component | Cold miss |
| --- | ---: |
| Initial pi lookup | 1 |
| Arctangent series at 1/5, 28 iterations | 115 |
| Multiply its interval by 16 | 5 |
| Arctangent series at 1/239, 8 iterations | 35 |
| Multiply its interval by 4 | 5 |
| Interval subtraction | 3 |
| Remember completed pi | 1 |
| Total | 165 |
| Authentic existing hit | 1 |
| Gross difference | 164 |

The series counts follow `4N+3`; their strict stopping inequalities and independent source derivation remain in the [C051 cost review](../../checkpoint-051-reviews/cost/review.md). A scalar-by-nonpoint-interval multiplication uses scalar `point` 1, operation tick 1, two exact endpoint products 2 and grid 1. Subtraction of the two positive grid-aligned nonpoint intervals uses one operation tick and two exact subtractions, with no additional grid tick.

Let p be the number of `pi` calls in one native stable first-precision attempt that completes the relevant arithmetic. If p=0, the cache opportunity is zero. If p>=1, the original pi contribution is `165+(p-1)=164+p`. A parent already containing the authentic eligible key contributes p. A cold parent contributes the same `164+p`. Therefore:

- Authentic hot parent: 164 immediate gross, once for that precision attempt.
- Cold parent: zero immediate gross; any advantage is deferred to later work.
- No pi call: zero immediate gross, even if the parent has a pi key.
- Later precision: no immediate substitution saving under this schedule.

Additional synchronization ticks, changed-domain paths, interrupted construction, non-native dispatch or malformed inputs are outside this completed stable-route formula. They retain their own event accounting.

### A manually derived source case

For lengths `(2,1)`, target `(1,0,0)`, positive elbow branch and permissive closed limits, the exact algebra gives cosine -1, radical 0 and shoulder signs positive/zero. No product execution was performed.

| Component | Original child | Authentic hot parent |
| --- | ---: | ---: |
| Common exact-algebra prefix | 26 | 26 |
| Pi calculation | 165 | 1 |
| Multiplication by sign +1 | 2 | 2 |
| Square root of zero | 3 | 3 |
| Nonzero-sign Cartesian coordinate | 4 | 4 |
| Zero-sign Cartesian coordinate | 1 | 1 |
| Shoulder atan2(0,positive), including the zero atan series | 8 | 8 |
| Two rounding calls | 2 | 2 |
| Total before new admission | **211** | **47** |

The authority reviewer independently confirmed these source counts. They establish the 164 opportunity without assuming an actual original-corpus occurrence. The authority counterexample uses the native poisoned parent value `Interval(25/8,25/8)`. It is ordered, positive, dyadic, lies between 3 and 4, and produces elbow 3.125 within the usual closed plus/minus-PI64 limits. The true independent pi lower bound exceeds `1184/375-4/239-20*2^-128`, which is greater than 25/8. Its unrounded margin is `11183/717000`, much larger than grid and binary64 rounding effects. Thus the original cannot produce the candidate's 3.125 elbow. The poisoned point payload has the same counted 21-tick body here; type, sign, and broad-range checks do not repair its origin.

For bare reuse with an admitted nested callback, a fixed sentinel on the 48th call-local checkpoint is observed by the original but not by the 47-tick candidate. If a fixed admitted screen adds G charged checkpoints and otherwise leaves the counted native route unchanged, candidate cost becomes `47+G`. For integer `0 <= G < 164`, a callback sentinel at `48+G` still distinguishes it from the 211-tick original. This is a schedule-qualified source counterexample, not a claim about a future gate that excludes effectful callbacks. Attempted ticks also need not increment every counter when a callback raises.

## 3. The reviewed admissions

**R1: structural direct-parent substitution.** After the common algebra, use the parent at first precision 128 if current native owner/work/check/precision/scale/domain and both arithmetic observers appear eligible. Keep original child fallback. This schedule has no proof that a preexisting native pi payload was independently computed. `_Arithmetic.cache` is an externally reachable native dictionary; native interval and Fraction types do not establish numerical provenance. Consequently its claimed hot-path equality is conditional, and no positive accepted ledger follows from the 164 arithmetic difference.

The exact cost G of a completed R1 admission is not established. A check cannot be assigned zero cost merely because it rejects or because the callback graph appears native. All actual type/field/limit/claim lookups and safe gate-charging work belong to G. Rejected paths add their executed partial G to the original behavior.

**R2: fresh full cache inspection.** This stronger schedule inspects every resident key/value entry on every admission, together with a current native-graph screen and an origin proof if one can be supplied. Define m as occupancy at that actual admission. Even giving a combined entry inspection only one charged operation yields `A_scan >= m`. Distinct type/value checks or copies may cost more.

For an authentic hot pi call, `net_immediate <= 164-m-A_other`, where `A_other >= 0` contains all other current-authority, origin, branching, rejection and cleanup costs. Thus m>=164 offers no positive immediate saving under this scan, and m=256 gives at most -92 before other work. At smaller m the bound leaves an unresolved margin; it is not a positive proof. The scanned metadata still cannot certify that a numerically false native pi interval has a valid origin.

A historical 256-entry snapshot at a later key-comparison boundary does not establish m at canonical setup. This review assigns no actual request occupancy to the source inequality.

**Checkpoint repair.** Restoring each of the 164 omitted charged boundaries costs at least 164, so `net_immediate <= -A_other`. A tick alone does not also reconstruct prospective operand checks, exact dispatch or original failure effects. This rejects the particular repair policy.

## 4. Cache state and later work

Parent substitution does not introduce a second cache container, but changes the lifetime and order of existing numerical values. The parent's dictionary uses `MAX_CACHE=256`; it is separate from `ReachExecutionWork._cache`, whose public cache operations have different charges. Counting those two caches as one mechanism would give the wrong ledger.

A native pi hit promotes the parent key through deletion/reinsertion. A cold pi miss inserts into the parent and, when full, evicts its oldest key. The original temporary child could hold at most the pi key in this precision body, then loses that cache with the child. It never promotes or evicts any parent entry. One added retained key can therefore alter future pi, pose, coefficient or cursor hits.

The usual parent lookup/insertion ticks already cover their existing bounded order/eviction bookkeeping; do not invent an extra baseline eviction charge by borrowing the work-cache API's charging scheme. New inspection, rollback, copied order or publication checks would be additional. A raw dict snapshot or restoration is not a free neutrality device.

At a domain mismatch, `_sync_cache_operand_limit` adds a tick and clears the parent's whole dictionary. A fresh child's domain record starts current. Synchronization on the parent may therefore discard unrelated values that the original child would not touch. Any design admitting that route needs its complete cost and current callback proof. A stale entry cannot be priced as an eligible hit.

The parent is also used by centered and planned recording computations. Their cursor receipts, pending publication and retirement depend on cache contents and identity. Normal canonical setup occurs before those consumer phases, but that does not prove that a generic external call has no active or pending state. The [plan module](../../../../../ontokin/reach_reference_plan.py) and [center module](../../../../../ontokin/reach_reference_center.py) contain direct cache writers/deletions. A candidate cannot assume that changed eviction order has no later cost, or that C047's original post-setup no-eviction argument applies unchanged.

For a matched completed request, let H count first-precision cold-child pi constructions actually replaced by authentic parent hits; let `Delta_later` be candidate minus original charged work outside those matched local omissions, after including every changed later cache hit, eviction, reset and recomputation. Let `A_total` be all new startup, admission, rejection, copy, publication and cleanup work. Then the conditional accounting identity is:

`saving = 164*H - A_total - Delta_later`.

Do not double count a later pi difference both in H and in `Delta_later`. A negative `Delta_later` is an additional benefit; a positive value consumes the local margin. H, actual occupancies, request-specific rejection costs and `Delta_later` are unknown here. Interrupted requests require matched event-prefix accounting, not this completed-request identity. Subtracting 164 from a historical 100001 failure count does not establish a successful request.

## 5. Empty-parent-only variant

At a direct helper call, requiring an empty native parent cache removes reliance on a preexisting numerical payload. It yields no immediate saving: the first pi calculation is cold in both parent and child. If no pi is needed, there is not even a newly retained pi. A later benefit requires that the candidate's completed pi survives until a baseline parent miss, with identical native value/domain behavior and all new costs charged.

There is a stronger incidence limitation on the ordinary source route. `ReachReference.__init__` calls `_initialize` before `_build`. Initialization calls `self.p.quaternion` for each model object. Native quaternion either hits or remembers its result, including identity quaternions. A successful validated planar chain has three distinct object owners, hence at least one initialized object. With fixed operand domain and no effectful callback or unsupported writer, native lookup, insertion and capacity eviction preserve a nonempty cache. The only ordinary clear in this arithmetic is domain synchronization. Later centered/plan cursor deletion belongs to consumer work after constructor setup.

Thus an empty-parent gate is **ineligible on the unchanged native fixed-domain constructor route**. This is a source conclusion with stated premises, not an empirical count for every hostile or changed-domain request. Clearing the parent to create eligibility would be a different design, adding resets, lost values and later work. No such action is proposed.

A more relevant distinct source question could retain the original fresh child and conditionally publish its freshly completed matching-domain pi value into an absent parent key. That moves the origin question to a local child rather than a preexisting parent value. It still requires a concrete current native/callback proof, extra logical-copy or reference accounting, safe publication, preserved errors and a complete later-cache ledger. This review does not approve that design or assign it a positive complete bound.

## 6. All-path ledger and limits

| Path | Gross opportunity before new work | Required accounting |
| --- | ---: | --- |
| Existing target-key hit | 0 in this helper | No new canonical call; any request-wide gate cost still counts. |
| Pre-loop invalid annulus, zero radius, branch error or other early failure | 0 | A selection gate after common algebra does not run; any earlier startup costs remain. Preserve the original failing operation. |
| First128 succeeds, authentic resident pi used | 164 | Subtract complete admission and signed later-cache changes. |
| First128 succeeds, parent pi cold | 0 immediately | Same cold pi work; parent insertion/eviction and future hits must be reconciled. |
| First128 reaches no pi | 0 | Admission overhead is not funded by this call. |
| Exact-zero angle or radical path | Depends on actual pi use | A zero shoulder can coexist with a nonzero elbow requiring pi, as in the counted case; do not label all zero-related inputs free of pi. |
| First128 raises _Uncertain | 0 or one conditional 164 pi difference in the completed common prefix | Preserve first-refinement timing; later precision stays fresh. A retained parent pi may change later work even though no target was returned. |
| Later precision or parent mismatch | 0 from substitution | Original child plus actual selection/rejection costs reached. |
| Changed operand limit/cache domain | Unknown | Include synchronization, whole-cache clear, original constructor checks and later recomputation. |
| Rejected native/callback/cache gate | 0 | Original route plus actual partial-gate costs, not zero overhead. |
| Malformed/custom owner, cache, keys, values or helpers | No native formula | Preserve original dispatch, errors and callback effects; a new probe can itself invoke custom behavior. |
| Cancellation/resource refusal/new-gate exception | No completed-call formula | Retain exact successful and attempted boundaries and original exception identity. |
| Empty-parent admission | 0 immediately | Ordinary native stable-domain setup incidence is zero; other callers need a separate source and later-work proof. |

Original28 remains 24/28 historically, with P11/P16/P23/L03 open. C035 remains held, including adverse timing. This review changes no runtime, source fixtures, expected values, horizons, fps/helpers, tolerances, callbacks or limits. It establishes no elapsed saving, completed tail, new recording pass or full-product acceptance.

## Execution disclosure

Only text reads/searches and standard-library file/hash/JSON operations were used. No OntoKin module was imported or executed. Exact arithmetic counts and counterexamples were reasoned from source, not measured with a candidate. The coordinator owns actual documentation validation, publication and remote readback; this source review does not certify those later actions.

