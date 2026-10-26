# C043 independent angular-envelope contract review

Reviewer: `/root/angular_contract`. Date: October 26, 2026, America/Denver. Scope: read-only source and static AST analysis. No product module was imported or executed, and no request, test, benchmark or numerical replay was run.

## Source binding and scope

The reviewed current cut is `00606a16be62631179b50255d4de8daa34f8f196`, tree `9d9dd9f77b976c4b8b2076b8f5a0c4f87aa82342`. Files were fetched at that exact ref and verified locally by Git blob hash. The initially created review copies had one extra terminal LF; that hydration error was detected, removed only after matching the expected blob identity without that LF, and all source files below then matched. It changes neither repository bytes nor historical evidence.

| Source | Git blob | Relevant current lines |
| --- | --- | --- |
| `ontokin/reach_recording_fast.py` | `c58d76692a79c1a1507a1185d1dfd15959de11cc` | 49–56; 245–250; 527–586; 2270–2376 |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` | 40–176; 248–261; 321–349 |
| `ontokin/reach_phase.py` | `9bae69ea6bda16fbbd841480139443cdbfe63d6f` | 38–57 |
| `ontokin/reach_pose.py` | `d58dd633c052c53a201eb6bdb16dac68625b3961` | 26–32 |
| `ontokin/reach_export.py` | `f8a240dd033ebf5e4f2ce83bf46e3ae379b9b27a` | 740–764 |
| `docs/language-design/planar-reach-v0.1/budget-counting.md` | `d2113ebd1f44bbf78ba484a5f971d62741dab715` | section 3 |
| `docs/language-design/planar-reach-v0.1/ADOPTION.md` | `53df12590687983a239e7c1d29b86488ab95c0d6` | adoption and implementation obligations |

The historical `recording_float_excess` at runtime `88473124cc058f7e2926a04d79ab38e340ab4407` occupies lines 362–421 of `reach_recording_fast.py`, blob `078d6292dca80c45cfefad64108e1e0844591c2a`. Its complete AST is identical to current lines 527–586: AST SHA-256 `1f8ad241fb956be654207b233d93c2e2f32e89fce793ec308f3ae0c373d27474`. Historical/current `exact`, `compare`, `lookup` and `remember` ASTs also match. `ReachExecutionWork.charge` differs; current code captures and invokes a source observer. Function equality therefore supports interpretation of historical arithmetic sites, not transfer of the historical call/cache sequence to the current runtime.

**Decision:** splitting repeated angular arithmetic is a mathematically coherent candidate, but source inspection alone supplies neither the current repeated-signature census nor a complete authority/guard/cost proof. No runtime implementation is selected by this review. The fourteen sites are a conditional gross opportunity, not fourteen guaranteed saved charges.

## Exact original control and failure order

The original function performs these steps, in this order:

1. Charge `recording_float_excess_domain`; read `t,c,l,m,sp,sq` from the supplied bound.
2. Require native nonnegative integers `t,c` and native nonnegative Fraction-valued `l,m,sp,sq`; guard all six operands. Require both selectors to be exact booleans.
3. Form the existing whole-result key
   `(METHOD, "excess", cap, t, c, l, m, sp, sq, include_cell_radii, dynamic)`.
   Perform the original whole-cache lookup; reject a changed cap relative to the captured key.
4. On a whole-result hit, guard the cached position, quaternion-component and rotation fields, then return that original whole result. This branch does **not** execute cold-path `guard_bits(1075)`, late cap comparison, range comparisons or new arithmetic.
5. On a whole-result miss, calculate `source_leaves,e,g,q` in the original expression order: thirteen exact operations.
6. Calculate the ordinary position expression: ten exact operations. If `dynamic` is true, perform its additional four exact operations.
7. Compare `e` against `1/64`. Only if that comparison is not greater does the short-circuit expression compare `q` against `1/64`. Each `_checked_compare` first performs the original rational comparison and then checks the native full operand domain. Reject an excessive envelope at this point.
8. Calculate `rotation_rad=16*q`: the fourteenth common operation.
9. If `include_cell_radii` is true, calculate the position radius and then quaternion radius, each through the original noncached `_upper_float` route.
10. Construct the full `RecordingFloatExcess`, perform the original whole-cache insertion, guard its three rational fields, guard 1,075 bits, compare the current cap with the captured cap, then return.

This ordering has two important consequences. First, an excessive cached `e` or `q` cannot be rejected before the position expression: a position admission/arithmetic/callback failure would originally occur first. Second, a cached late rotation value cannot be admitted or exposed as if all fourteen arithmetic sites were one prefix. Surviving position and comparison callbacks occur between the two omission regions.

The existing whole-cache lookup belongs before a new angular-cache gate. Putting a new charged gate first would affect warm whole-result calls that presently require no constructor arithmetic. A complete cost ledger must separately account for those warm routes if a concrete design nevertheless chooses to touch them.

## The fourteen common sites

Write `C=c+1`, `A=AXIS_ERROR`, `P=PRODUCT_ERROR` and `N=MAX_RECORDING_ROTATION_STEPS-1`. Under the reviewed constants, `A=2^-74`, `P=2^-91`, and `N=9999`. The source's exact evaluation order is:

| Site | Operation | Original source location |
| --- | --- | --- |
| 1 | `C=c+1` | 560 |
| 2 | `t*2^-41` | 561 |
| 3 | `C*2^-47` | 562 |
| 4 | Add sites 2 and 3 | 561–562 |
| 5 | Multiply site 4 by 2, producing `e` | 561–562 |
| 6 | `N*t` | 563 |
| 7 | `2*P` | 564 |
| 8 | `A + site7` | 564 |
| 9 | Multiply sites 6 and 8, producing `g` | 563–564 |
| 10 | `2*sq` | 565 |
| 11 | Add site 10 and `g` | 565 |
| 12 | `16*e` | 565 |
| 13 | Add sites 11 and 12, producing `q` | 565 |
| 14 | `16*q`, producing `rotation_rad` | 577, after position work and comparisons |

All ten ordinary position sites remain in the reviewed scope, including the position expression's `3*e`, `g+3*e` and `2^-46*C` subexpressions. Their angular dependence does not silently expand the selected fourteen-site target. The optional dynamic position work, both original conditional range comparisons, per-bound admissions, radii and whole-result cache operations remain.

An arithmetic value key can omit spatial fields only because the selected completed values depend on `t,c,sq` and the actual current constants/method. It cannot omit those constants from its authority argument merely because their names look constant. The selectors do not enter the selected angular formulas, but still govern their surrounding work and remain part of the unchanged whole key and original admissions.

## Review of the selected U-Angular candidate

The root selected **U-Angular** for this checkpoint: after unchanged per-bound admissions and an original whole-result miss, attempt a new angular lookup in the same bounded numerical cache. Its key includes method/cap, exact integer snapshots of `t,c,sq`, and the needed constants. Its record stores copied canonical integer pairs for `C,e,g,q,rotation_rad`. On a hit it restores the prefix only after current native owner/dispatch/callback authority and intermediate guard proofs; it keeps the position expression, optional dynamic expression and short-circuit comparisons unchanged. It consumes cached rotation only at line 577 after fresh late authority/prospective guards, otherwise retaining the ordinary late multiplication. On a miss it completes the original whole calculation, then attempts angular publication only after the original whole-result return guards succeeded and only if current key/source/cap still match. This schedule reserves no implementation. Its concrete native admission and complete charged lifetime remain proof obligations.

### Arithmetic guards

`exact` in `reach_numeric.py:321–341` precharges the specific operation, guards both current operands, computes their native numerator/denominator widths, guards the **unreduced prospective** numerator/denominator size, performs the rational operation, and guards its result.

A retained final value cannot alone prove every omitted intermediate guard. Equal reduced results can have different prospective widths. Each omitted site therefore needs either its original guards at the original point or a proved native-domain theorem that makes those guards succeed for the complete present operand/constant state. A broad gate that fails its optional theorem should decline and follow the ordinary sequence, not raise a new source failure before the original position/range boundary.

A cap included in a cache key identifies a domain; it is not a proof that the actual cap stayed unchanged through lookup/promotion or the later surviving callbacks. The existing cache primitives handle cap synchronization and some reentrant state, but a new record still needs the correct proof at each use.

### Native values and dispatch

`PhaseBound` and `RecordingFloatExcess` are frozen dataclasses, but the Fraction objects inside are shallow references. Exact type `Fraction` by itself does not establish that its backing numerator and denominator are unchanged. Native class/storage descriptors, arithmetic functions, work methods, constants, and current bound fields can be externally replaced or mutated in the hostile-call model used by the surrounding code.

A canonical immutable key made from native integer numerator/denominator snapshots avoids a mutable Fraction key. Likewise an integer-pair record with fresh Fraction reconstruction avoids creating a new alias from an earlier returned whole result's `q`/rotation fields into a later calculation. These copies and checks are real charged work. A tuple holding the old Fraction objects does not supply this protection.

Original expression argument capture also matters. For example, the `AXIS_ERROR` reference is evaluated before the nested `2*PRODUCT_ERROR` operation's callback, while later global reads occur at their own source points. A candidate cannot replace these observations with one stale tuple unless it proves an eligible native interval or preserves ordinary fallback.

### Work, callbacks and exceptions

Current `charge` captures `_source_after_charge`, invokes `external_check`, checks operation/elapsed limits, updates `counts`, then invokes the captured observer. It retains the original external callback exception object in `callback_error` and reraises it. A hostile key already inside an otherwise native category dictionary can make a new dictionary lookup invoke foreign equality code; native dictionary type alone does not prove the charge boundary inert.

A reuse gate must close the whole relevant work/dispatch/callback/storage authority, rather than proving only the nominal external callback absent. It must retain cancellation and exception identity under the chosen supported route, and ordinary fallback under unsupported routes. The caller catches `_UnsupportedPlanar` and translates it to `RecordingRoundingAmbiguity` only when it is not the work object's recorded callback exception (`reach_recording_fast.py:2373–2376`). Broadening this catch or translating a callback-origin exception would change behavior.

For site 14, fresh late authority is necessary because surviving position work and range comparisons can invalidate an earlier prefix receipt. Retaining the ordinary single rotation multiplication is a smaller possible target, but then the gross opportunity is thirteen, not fourteen. This review does not choose that alternative or assert it profitable.

### Shared cache and lifetime

Every new angular entry must share the existing 256-entry numerical allowance, including lower user caps. A second private retained numerical cache is not a free additional allowance. `lookup` charges lookup and potential promotion; `remember` charges insertion and potential promotion/eviction and checks operand-domain/generation changes after callbacks. A candidate must charge any extra key construction, stored/copied values, unsuccessful lookup, declined gate, fallback, retirement and cleanup.

Extra angular entries can evict whole-result or unrelated entries and change subsequent hits. Consequently, subtracting thirteen or fourteen from each presumed repeat does not bound complete-request work. Preserve the original whole cache behavior semantically and include the changed retention/eviction consequences in the charged comparison.

U-Angular postpones new angular publication until the original whole-result return guards have succeeded. This avoids treating an incompletely computed prefix as a completed angular result. However, its new publication still adds lookup/insert/promote/evict failure routes and shared-cache consequences; those are not free because they occur at the end.

In particular, publication **after** the original result guards and cap check introduces new callbacks after the original last validation point. Native `remember` protects its own pending insertion against changed cap/generation; it does not revalidate the already constructed result's Fraction contents or all return authority. If one of these new callbacks changes the result or cap, declining the optional angular publication alone does not establish that returning the previous result is valid. The design needs a proved native nonmutating interval across publication, or the necessary fresh final result/domain/authority checks after it, with every added check charged. The original callback exception identity must survive. This is an unresolved schedule-specific obligation, not a claim that the existing whole-result insertion is defective.

## Required evidence and final disposition

The source provides a family of angular signatures; it does not establish which signatures occur in current P23, which calls miss the whole cache, or which proposed angular entries would survive the shared eviction order. The retained-evidence reviewer must establish those facts or record the exact gap. The historical/current body match cannot replace that census because the surrounding caller, charge/observer behavior and shared-cache traffic differ.

I independently confirm the 13+1 arithmetic split, ten ordinary position sites, optional four dynamic sites, unchanged whole-key fields, exact guard layers, original comparison short circuit, whole-hit branch distinction and late-site authority problem.

**No implementation approval is given for U-Angular.** Its independent cost review must include the unconditional new lookup/publication overhead even on an all-unique cold sequence with no reusable angular hit; a positive saving cannot be inferred merely from the existence of fourteen sites. The current schedule also leaves the native authority/guard and final-publication obligations above unresolved. These are schedule-specific findings; nothing here proves that every future angular specialization is impossible. The original 24/28 state and all current caps/fixtures/oracles/release obligations remain unchanged.
