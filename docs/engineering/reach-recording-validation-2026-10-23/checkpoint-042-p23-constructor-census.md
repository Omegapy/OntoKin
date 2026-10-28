# C042: P23 constructor census and bounded design decision

Date: October 26, 2026, America/Denver. Owner: `interactive-reach06-p23-constructor-census-20261026-c042-b480`. Scope: source and retained-evidence review only. Parent: C041 `b0ebdc318444ca97c729c11e0b29b19646096b34`, tree `a798a4c3f52f80e123fb54b65b3ac344bd8ea42b`. Ownership is recorded in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6420137944).

**C042 establishes a historical cold/warm constructor census, rejects one concrete four-charge default-receipt design, and selects a larger distinct operation for the next source-only review. It selects no runtime implementation.** Current P23 constructor misses remain unmeasured. The latest complete original28 remains 24/28; C035 is held.

The review follows [AGENTS](../../../AGENTS.md), [GOAL](../../../GOAL.md), the adopted [reach contract](../../language-design/planar-reach-v0.1/ADOPTION.md), [release obligations](../../language-design/planar-reach-v0.1/release-contract.md) and [budget-counting section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse). C041's unconditional `upper_binary64` cache bypass and unchanged-key `RecordedTransform` substitution remain rejected. The latter cannot replace a full pose consumed by source evaluation.

## 1. What the retained evidence establishes

The C020 observer contains enough attributed charge data to distinguish several cache outcomes that its earlier summary did not extract. These are retrospective deductions from the exact old source and retained observations. They are not newly executed product measurements or explicit hit/miss fields in the old log.

| Historical C020 export scope | Outer helper calls | Outer hits | Cold noninverse | Cold inverse | Stationary-cache hits | Stationary-cache misses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `advance:0:before` | 40 | 6 | 33 | 1 | 2 | 32 |
| `advance:0:after` | 3 | 3 | 0 | 0 | 0 | 0 |
| `advance:2:before` | 3 | 3 | 0 | 0 | 0 | 0 |
| `recording_sampling` | 192 | 130 | 62 | 0 | 0 | 62 |
| Observed export total | 238 | 142 | 95 | 1 | 2 | 94 |

Here, **cold** means the outer source-constant lookup returned no value and entered the corresponding constructor. A cold call can still hit an inner cache. The export observer begins after source construction, so this table is not a whole-process inventory. Warm hits cannot be further divided into inverse and noninverse calls from these aggregates alone.

### Source identities and recovery boundary

The historical observation belongs to runtime `88473124cc058f7e2926a04d79ab38e340ab4407`, tree `02efa05c691ff31258e39c16b98044d2a47fda20`. Its exact original P23 request used end `3`, integer fps `1`, helpers false and the original tolerances/caps. It failed at 100,001 shared operations and 80,033 completed reach operations. The original failure remains unchanged.

The current retained C035 P23 observation belongs to held runtime `4ca73909f861fe4bef9694787473621c1d21c140`, tree `87c949b238055af1ce368c694e1d5683c8aeacde`. All 65 `ontokin/` file blob/mode identities in C041 match that held runtime. This binds the current runtime source; it does not establish a new execution or close all release inputs.

The old/current pose file is byte-identical. The outer helper, `make`, `constant_pose`, `inverse_pose`, native lookup and native insertion bodies are structurally identical. The enclosing resolver and `charge` method differ. Therefore the historical constructor source explains the old trace, but the old invocation sequence and cache hit rates cannot be assigned to current P23. See the [source binding](checkpoint-042-source-binding.json) and [retained census](checkpoint-042-census.json).

The retained reviewer recovered only required archive segments and selected members from C020 and C035. Selected spans were present, every recovered part matched its published identity, and selected members matched their length, SHA-256 and ZIP CRC. This is not a new whole-archive hash or all-member verification. Exact copies of the relevant records, observer source, inventories and historical runtime files are retained in [the C042 evidence directory](checkpoint-042-retained/), with their [recovery receipt](checkpoint-042-retained/recovery-receipt.json). No archived driver was executed. The C020 inventory still discloses its historical 37 omitted archives; current recovery does not rewrite that history.

### Why sampling is 62 cold plus 130 warm

The executed observer attributes each work charge to its nearest selected function. Constructor internals were not separately selected, so their charges remain attributed to `_constant_pose`. Its sampling self and inclusive totals both equal 1,934. All constructor charges in that scope completed; the historical refusal occurred later during recorded position projection.

| Sampling category | Retained count | Source reconciliation |
| --- | ---: | --- |
| `pose_stationary_check` | 62 | One per completed `make` entry |
| `pose_vector_domain` | 248 | Four per entry: position, raw quaternion, default velocity and default angular velocity |
| `exact_decode`, `binary64_decode` | 434 each | Seven raw position/quaternion scalars per entry |
| `cache_lookup` | 316 | 192 outer + 62 rotation + 62 stationary; no inverse lookup remains |
| `cache_promote` | 192 | 130 outer hits + 62 rotation hits; no stationary hit remains |
| `cache_insert`, `cache_evict` | 124 each | 62 outer publications + 62 stationary publications at capacity |

The absent rescale category confirms all 62 normalized-rotation lookups hit on this native historical flow. The planning row independently reconciles one computed inverse and two stationary hits. The [contract reviewer](checkpoint-042-reviews/constructor-contract.md) and [retained-evidence reviewer](checkpoint-042-reviews/retained-census.md) checked this partition separately.

For the three-charge constructor target, the historical sampling opportunity is therefore **at most 186 gross charges**, before any new checks. Neither all 192 calls nor all 1,934 attributed operations are removable construction work.

## 2. Original constructor and consumer contract

`ReachSimulator._constant_pose` uses `("reach_source_constant_pose", inverse, value.position, value.rotation)`. The key contains no recording namespace. Its graph call sites serve both full-source and recording traversals: source sites, following offsets and inverse child-joint offsets.

The result must remain a full `PoseValue`: exact position, complete rotation/error, exact linear velocity, exact angular velocity, position error, source operations owner and projections. Full composition requires that type; source snapshots, release anchors, finiteness checks, source-site receipts and bounds consume derivative/error fields. A later or reentrant full-source call can use the same outer key. A position/quaternion-only `RecordedTransform` remains invalid under that unchanged key.

All relevant entries share one bounded numerical cache; they are not separate 256-entry allowances.

| Route | Original order after reading the outer key |
| --- | --- |
| Outer hit | Lookup charge; cap synchronization; promotion callback; cap/presence recheck; return the full cached result. No constructor work follows. |
| Cold noninverse raw `Pose` | Outer lookup returns `None`; read source position/rotation again; position admission; raw-rotation admission and rotation-cache path; default velocity admission; default angular-velocity admission; stationarity charge/test; stationary-cache lookup; construct/insert a full pose only on an inner miss; outer insertion. |
| Cold inverse raw `Pose` | Complete forward `constant_pose`/`make` sequence first; then a separate inverse-result lookup; on its miss, inverse rotation, three position-negation charges, rotation of the negated position, original error arithmetic including `VECTOR_ERROR`, full inverse result and inverse insertion; finally outer insertion. |
| Direct `inverse_pose(PoseValue)` | Uses the existing full pose before inverse lookup. It does not enter `make` and offers none of the default-constructor three charges. |

Position failures precede rotation failures; both precede derivative admissions. Each original charge can invoke the external budget/cancellation callback, check limits, update the category dictionary and invoke the captured observer. Category key comparisons can also be observable Python behavior. Native lookup/remember already protect changed operand limits and reentrant publication. The review does not allege that warmed native entries survive a legitimate cap change.

An inverse result does not incur a second pair of default-vector admissions. The three-charge target belongs only to the preceding forward `make`, when reached. Even identity inverse inputs retain the existing position-error contribution; numerical identity does not authorize deleting it. The [complete contract review](checkpoint-042-reviews/constructor-contract.md) records the scalar, guard, cache and first-failure order in detail.

The untouched P23 source supplies a vocabulary of **34 possible outer keys** at these graph sites: 32 noninverse mount offsets `(0,j/4,0)` for `j=0..31`, one noninverse unit-x tip offset, and one inverse zero-position child-base offset. All use identity local quaternions. This is a source vocabulary, not a visit or miss count. Shared-cache eviction can repeat a miss, while upstream reuse, captured graphs and the existing native identity-leaf route can avoid this helper altogether.

## 3. Current P23: exact gap and refusal

The retained C035 request fails at **100,001 shared / 80,801 completed reach operations**. Its final traceback enters `_constant_pose -> work.lookup -> charge("cache_lookup") -> external_check`. The external shared-budget check refuses before key membership. **That final call is unclassified; it is not a recorded cache miss.**

The current aggregate map contains 103 `pose_stationary_check` occurrences, 1,137 vector-domain occurrences and 5,053 completed lookups across all callers and namespaces. For eligible constructor entries whose three target charges completed in the original failed prefix, `m <= 103` and `3*m <= 309` is only a conservative gross ceiling. It is not the sampling-only opportunity, an equality, a net saving or a ceiling on a whole request that an optimization might allow to advance further.

The missing datum is the current per-caller/per-namespace classification: outer hit/miss/refusal and inverse flag; entry to `make`; rotation, stationary and inverse-cache outcomes; completed/refused insertion; and original scope/phase/order. Aggregate stationarity and cache counts cannot supply it. Historical planning counts cannot be subtracted from current totals. No new diagnostic or replay was run to fill this gap.

## 4. Concrete design closed without runtime scope

The reviewed same-type candidate retains the full `PoseValue`, all original relevant cache layers, original position/rotation work and original fallback. At the derivative-admission point it proposes a fresh default receipt: one charged check for the common native three-element default tuple and at least one charged inspection for each of its three native Fraction fields. The purpose is to establish the actual zero numerator/unit denominator values, not merely a tuple identity containing mutable backing objects.

That explicit schedule adds **at least four charges** per completed gate and can remove only the two default-vector admissions and stationarity charge, **three charges** per eligible construction. The four-charge subtotal is optimistic; it does not claim to cover every source, work, callback, dispatch or lifetime obligation.

Let `m` be eligible constructions, `g >= m` completed gates, `A` setup/admission, `D` partial/declined-gate and fallback overhead, and `L` added storage/lifetime/cleanup. These extra costs are nonnegative:

`saving <= 3*m - 4*g - A - D - L <= -m - A - D - L`.

**NO-GO for this concrete fresh deep-default receipt schedule.** A positive current miss count cannot rescue it. No implementation needs to be reserved to establish this cost failure. This is not a universal minimum for every possible constructor theorem, an impossibility claim for origin-retained defaults, or a claim that the proposed receipt already preserves every callback/exception. The [independent cost review](checkpoint-042-reviews/constructor-cost.md) and [ledger](checkpoint-042-cost-ledger.json) preserve these qualifications.

## 5. Next distinct source-only target

Inspect repeated angular-envelope arithmetic inside `recording_float_excess`, which computes conservative additional recording error. C020 records **32 cold whole-result sampling calculations / 960 attributed charges**. Its function body is structurally identical to current source, while the surrounding implementation differs. Current P23 records 32 domain occurrences, but current costs and key repetitions remain unknown.

The whole-result key includes both angular and spatial operands. The formulas expose 14 exact arithmetic sites depending on `(t,c,sq)` and current constants: one for `source_leaves`, four each for `e`, `g` and `q`, and one for `rotation_rad`. The ten nondynamic position-expression sites depend on different spatial bounds and remain separate. Domain/width checks, range comparisons and existing whole-cache operations are not counted as removable.

For `r` genuinely eligible repeats among cold calculations, `14*r` is only a conditional gross count. Even the historical optimistic maximum `14*31 = 434` assumes all 32 calls share one admitted signature; that grouping has not been established. All 960 charges are not removable, and no net bound or P23 pass follows.

The next bounded task is a separately owned **C043 source/retained-evidence angular-envelope feasibility review**. Establish exact per-call angular/spatial operands, selector values, whole-cache classifications and order where retained evidence permits. The old observer retained no individual `recording_float_excess` calls in its thresholded call list, so scoped totals alone do not supply those tuples. If source plus retained evidence cannot establish the required facts, name the missing datum before proposing a separately scoped diagnostic.

A candidate must preserve omission points: thirteen common arithmetic sites precede position calculation, while `rotation_rad` follows both range comparisons. Moving all fourteen early can change first-failure order. Charge the actual new admission, lookups, key construction, stored/copied values, fallback, retirement and cleanup, and close shared-cache effects. Require independent review and a complete positive worst-case charged bound before selecting any runtime scope. The held whole-pose static-transfer route and its adverse timing remain separate.

## 6. Verification and continuing state

Independent reviews cover source/consumer contracts, retained evidence and cost/authority. Their exact bytes and agreement scope are indexed in [the review record](checkpoint-042-reviews.json). Metadata/count/AST checks and the unmodified documentation preservation/navigation command have their separately identified inputs, commands, logs, outcomes and limits in [the validation directory](checkpoint-042-validation/). The local review copy lacks twelve existing historical binary link targets because large-file retrieval is unavailable in this environment. Their identities exist in the authenticated parent tree, but remote existence does not establish a full local documentation pass. Actual source-preservation, local-link and supplemental tree checks remain separately reported. Documentation verification establishes no product behavior.

C042 changes only new evidence, review, validation and handoff files. It changes no runtime, source fixture, oracle, tolerance, schedule, workflow, shared status, main or other-owner branch. It runs no product request, numerical replay, runtime test, recording suite, benchmark or destination check. No hosted/paid job or merge is part of this scope.

The limits remain 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and the separate 512-category metadata bound. Latest complete original28 remains **24/28 (85.7%)**, with P11/P16/P23/L03 capped; C035 remains held, including adverse L03 timing. Accepted reach `d2f0088c4f3c1f570630334804a5a8f78e0105ac` and main `2bb4588e121fcfe99b4d42c734b15b38362f3642` are unchanged.

Even 28/28 would still require actual Agent delivery and ten retrieved artifacts, independent rates/source work, CPython 3.11/3.12/3.13 roles, Khronos/Three/browser/native visualization, hostile/inherited roles, formal input closure, all R01-R12/Q01-Q22 gates and resulting-main verification. The complete OntoKin GOAL remains open. [HANDOFF-042](HANDOFF-042.md) provides the bounded continuation.
