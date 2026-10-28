# C042 independent constructor cost and next-operation review

Reviewer: `/root/constructor_cost`. Date: October 26, 2026, America/Denver.

Scope: source inspection, retained-data inspection and algebraic accounting only. The inspected C041 publication is `b0ebdc318444ca97c729c11e0b29b19646096b34`, tree `a798a4c3f52f80e123fb54b65b3ac344bd8ea42b`. No production module was imported or executed. No runtime change, product request, numerical replay, test, benchmark, archive extraction, hosted job or remote mutation belongs to this review. The parent coordinator supplied the exact source subset; the independent retained-evidence reviewer recovered the historical data used below.

## Decision

**Do not select the concrete per-construction deep-default receipt design.** It keeps the full `PoseValue` result and both original cache layers, but its specified fresh default receipt already costs at least four charges for at most three removed charges. This is a narrow economic rejection of that explicit design and accounting schedule. It is not a universal lower bound on every possible constructor specialization.

The next larger, distinct operation to review is **the repeated angular-envelope arithmetic inside `recording_float_excess` during P23 sampling**. Its historical source-bound evidence contains 32 cold whole-result calculations costing 960 charges. Fourteen exact arithmetic sites in each calculation depend only on the angular signature and implementation constants. The repeated-signature opportunities, their current-source frequency and a safe complete reuse design are not established. No saving or implementation is selected.

## Inspected source identity

All these local bytes were matched to the C041 recursive Git tree as ordinary Git blobs. The local directory is a partial review workspace, not a complete execution checkout.

| File | Git blob |
| --- | --- |
| `ontokin/reach_runtime.py` | `e7ccbb35c4f5aab7ff6431692bed80089fbf0cf0` |
| `ontokin/reach_pose.py` | `d58dd633c052c53a201eb6bdb16dac68625b3961` |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` |
| `ontokin/reach_export.py` | `f8a240dd033ebf5e4f2ce83bf46e3ae379b9b27a` |
| `ontokin/reach_recording_fast.py` | `c58d76692a79c1a1507a1185d1dfd15959de11cc` |
| `docs/language-design/planar-reach-v0.1/budget-counting.md` | `d2113ebd1f44bbf78ba484a5f971d62741dab715` |
| `docs/language-design/planar-reach-v0.1/sources/p23-maximum-chain-count.ok` | `3300ab61b9ce901f517dab18ee57f3079baaaaa5` |

The governing budget rule charges each new lookup, type/limit/claim check, copied logical value and storage action. Avoiding a real calculation can save work, but additional authority is not free. Current accepted semantics, 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and the separate 512-category metadata limit remain unchanged.

## 1. Exact removable constructor work

`ReachSimulator._constant_pose` in `reach_runtime.py`, lines 534-540, first looks up `("reach_source_constant_pose", inverse, value.position, value.rotation)`. Only a miss calls the constructor and then remembers its result. An outer hit provides no default-vector work to remove.

`ReachPoseOps.constant_pose` calls `make(pose.position, pose.rotation)` in `reach_pose.py`, lines 1202-1203. At lines 1189-1200, `make` performs, in order:

1. Position `_vector` admission.
2. Orientation `_rotation` admission and its own constant-rotation cache/calculation.
3. Velocity `_vector` admission.
4. Angular-velocity `_vector` admission.
5. One `pose_stationary_check` charge and the two zero tests.
6. The stationary-pose cache lookup; a hit returns its full cached value.
7. Full `PoseValue` construction and stationary-pose insertion on an inner miss.

The two default rates are the same module-default `ZERO` tuple. Each `_vector` call has one `pose_vector_domain` charge, validates its shape and exact native Fraction elements, and applies the original live operand guards. No per-component `rational` decoding runs for those default exact tuples. Thus omitting both default admissions and the stationarity check removes **three charges per eligible construction**, regardless of whether the later stationary cache hits. It removes neither position/orientation decoding nor any original cache lookup, promotion, insertion or eviction.

Inverse calls require their own classification. `inverse_pose` at lines 1442-1456 can first call `constant_pose` when the input is not already `PoseValue`; it then has an independent inverse-pose key, lookup, arithmetic and insertion. A valid full `PoseValue` input can bypass that forward constructor. Neither all inverse calls nor all `_constant_pose` calls can be counted as three-charge opportunities.

Both original cache layers and full results are retained in the reviewed candidate. `RecordedTransform` remains inadmissible under the full outer key: it lacks derivative and position-error fields used by full-source consumers. No result-contract shortcut or inverse arithmetic saving is credited.

## 2. One concrete fresh-default receipt

The inspected alternative is a per-construction receipt at the original derivative-admission point, after the unchanged position and orientation work. Its intended native branch uses the actual bound default objects, retains the two original cache keys and cache call sequences, and constructs the same full `PoseValue`. Ineligible or changed contexts take the original constructor using the same work object and remaining allowance.

The specific proposed receipt has the following charged schedule:

| Added action for an eligible constructor | Charged lower bound |
| --- | ---: |
| Authenticate that both bound derivative arguments refer to the same expected native three-element default tuple, with current default authority | 1 |
| Inspect the first retained native Fraction and its actual zero numerator/unit denominator | 1 |
| Inspect the second retained native Fraction and its actual zero numerator/unit denominator | 1 |
| Inspect the third retained native Fraction and its actual zero numerator/unit denominator | 1 |
| **Known fresh-default receipt subtotal** | **4** |

The record uses direct checks of the existing objects; it proposes no extra numeric vector copy or new numerical-cache entry. The listed four charges are the chosen candidate's optimistic subtotal. They do not claim to pay for every subcheck in a complete implementation. The scalar checks cannot simply be replaced by tuple identity while retaining this design's claim to deep default integrity: the tuple retains Fraction objects whose backing fields are part of the adversarial source model. The repository already preserves a historical mutation of a shared Fraction backing object in C020. The current default function objects, defaults and globals also require their own authority.

No cross-call receipt is retained by this design. Replacing this fresh receipt with an origin-retained witness or a different bundled theorem would define a different design with separate storage, lifetime, retirement and accounting obligations.

### Cost inequality and closure

Let `m` be the actual eligible calls reaching this derivative point and let `g` be the number of complete fresh-default gates attempted. Then `g >= m`. Let `A` cover setup and source/work/dispatch admission, `D` cover partial or declined gates and fallback overhead beyond the original path, and `L` cover any required lifetime, cleanup or extra storage/copy work. These uncredited added costs are nonnegative.

The saving for the inspected design is bounded above by:

`saving <= 3*m - 4*g - A - D - L <= -m - A - D - L`.

For any positive `m`, even the optimistic subtotal loses at least one charge per eligible construction. With `m=0`, there is no positive saving to establish. No exact current miss count is needed to reject this schedule. The original caches, unchanged result storage and original fallback arithmetic cancel between routes; their unchanged work is not counted as a saving. The design earns no favorable eviction credit.

This cost failure permits closing the design before attempting its unresolved authority machinery. It does **not** establish that its intended fallback is semantically complete, that the four checks alone are sufficient, or that every alternative needs four checks. It establishes that adding any further required work cannot make this particular schedule positive.

### Remaining semantic obligations, not free assumptions

The native-type label alone cannot authenticate instance-shadowed methods, class/function code or globals/defaults. The gate must also preserve the original `_vector`, `_rotation`, `make`, `constant_pose`, work/guard/cache dispatch and result factory contracts. Native `ReachExecutionWork.charge` invokes `external_check`, updates the externally reachable category dictionary, and may invoke `_source_after_charge`. A foreign colliding category key can execute a callback during dictionary access. Tracing/profiling and reentrant callbacks create additional lifetime boundaries.

The two original default-vector charge callbacks and the stationarity callback can observe or change live state or raise original exceptions. A startup snapshot cannot prove that all later states remain eligible. Every surviving cache callback can change caps, dispatch, source objects or cache generation. Native lookup/remember already synchronize operand caps and guard reentrant cache publication; this review does not allege a stale warmed native cache survives a legitimate cap change.

An implementation must retain original first-failure precedence: position/orientation failures occur before derivative work, and the stationary/inverse cache callbacks retain their own ordering and exception identity. Additional checks may not suppress an original callback exception or turn a refused native/foreign path into success. A fallback cannot restart with a fresh allowance. These obligations add work or force the original route; no complete cheap solution is established here.

## 3. Larger distinct target: repeated angular-envelope arithmetic

`recording_float_excess` in `reach_recording_fast.py`, lines 527-586, calculates conservative extra error for a recorded pose. Its output is a `RecordingFloatExcess`, not a full pose and not a substitute for independent supplied-byte checking. The whole-result key includes the operand cap, counts `t` and `c`, spatial bounds `l`, `m`, `sp`, angular bound `sq`, and the `include_cell_radii` and `dynamic` selectors.

The C020 retained observer at source `88473124cc058f7e2926a04d79ab38e340ab4407` identifies 32 sampling calls and 960 charges attributed to this function. The independent retained reviewer verified its exact JSON and driver against their manifest and source inventory. The function's AST is unchanged between the historical source (lines 362-421) and current source (lines 527-586), though the surrounding module and request implementation differ. The current function's `ast.dump(..., include_attributes=False)` SHA-256 is `1f8ad241fb956be654207b233d93c2e2f32e89fce793ec308f3ae0c373d27474`.

Historical scoped charges are:

| Category | Count |
| --- | ---: |
| `recording_float_excess_domain` | 32 |
| `cache_lookup` | 32 |
| `exact_add` | 320 |
| `exact_mul` | 448 |
| `exact_compare` | 64 |
| `cache_insert` | 32 |
| `cache_evict` | 32 |
| **Total** | **960** |

There are no attributed cache promotions. Under that identified native source flow, all 32 observed whole-result lookups missed and completed their calculation/insertion. This is historical evidence, not a new run or a current total. Current C035 P23 has 32 completed `recording_float_excess_domain` categories, but the whole-request aggregate alone does not establish current hit/miss classification or angular-signature multiplicity.

The source formulas identify a narrower candidate opportunity than all 960 charges:

| Computed quantity | Dependencies relevant to possible reuse | Exact arithmetic sites |
| --- | --- | ---: |
| `source_leaves` | `c` | 1 |
| `e` | `t`, `source_leaves`, fixed constants | 4 |
| `g` | `t`, fixed constants/cursor limit | 4 |
| `q` | `sq`, `g`, `e` | 4 |
| `rotation_rad` | `q` | 1 |
| **Potential common portion** | **`(t, c, sq)` plus current implementation/domain authority** | **14** |

The position expression `p` has ten further exact sites on the ordinary nondynamic path and depends on `l`, `m` and `sp`. Those sites are not part of the proposed common-portion target. Neither fresh type/width admission, either range comparison, nor whole-result lookup/insertion/eviction is classified as removable.

The retained P23 source has 32 mounts at different translations. This motivates inspecting whether different spatial-bound keys share the same complete angular operands; it does not prove the number of equal signatures. Let `r` be actually eligible repeated angular signatures among original cold whole-result calculations. Then `14*r` is only a conditional gross site count. With 32 historical cold calls, an absolute optimistic ceiling is `14*31=434` if all belong to one eligible group. The repeated groups and therefore that eligibility premise are unproved. No net saving, current bound, timing claim or complete-request deficit follows.

### Next bounded review requirements

Recover, without executing a new product request in C042, the exact per-call angular and spatial operands, selector values, whole-cache miss/hit classification and original order if retained evidence supplies them. If it does not, record those missing data explicitly. A new diagnostic would need a separately declared source-closed, exclusively executed scope with the untouched original P23 request and caps and preserved failures; no failed tail or allowance may be reused.

Then review a concrete common-portion design before runtime selection. It must keep the original phase/source/work authority, operand-limit and prospective-width failures, result fields, selectors, range comparisons, exception identity and all independent predicates. Thirteen potential common sites precede the position expression, but the final `rotation_rad` multiplication follows both range comparisons. Computing or caching all fourteen early would change first-failure order unless separately proved safe. Reuse must occur at its proper omission point, with new lookup/key construction, storage, per-bound admission, fallback, retirement and cleanup fully charged. The shared numerical cache's adaptive hit/eviction effects require a complete bound as well.

This target concerns repeated error-bound arithmetic within sampling. It is separate from the held P23 static-transfer design that tried to reuse an already evaluated final pose graph, and from C041's rejected full-key `RecordedTransform` substitution. It does not reopen either held route or alter the original sampling schedule.

## Scope of agreement

The constructor decision is source-only and limited to the explicitly charged per-construction receipt. The angular-envelope operation is a selected investigation target, not an approved implementation. Historical data retains its actual implementation identity. Original28 remains 24/28; P11, P16, P23 and L03 remain capped; C035 remains held. Runtime, shared status, main, all fixtures/oracles and the outstanding release and full-product gates are unchanged by this review.
