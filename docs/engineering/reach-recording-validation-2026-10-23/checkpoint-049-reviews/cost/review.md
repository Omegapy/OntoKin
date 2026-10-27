# C049 independent factorial-origin cost review

Reviewer: `/root/c049_cost_review`. Base: final C048 `8b6df27e323797e6b93bc9b44b5cd9083d4e3859`, tree `4ff706f642beac532eb44f0ec879ec99491f873f`. This review inspects source text and identified C047/C048 records. It does not import OntoKin, execute a numerical candidate, replay a request, execute a runtime test or run the documentation checker. The reviewer and numerical reviewer exchanged the authority-screen and callback issues; these are separate review roles, not blind reviews. [Exact reviewed inputs and result](result.json).

## Decision and scope

Accept the corrected [C049 feasibility review](../../checkpoint-049-factorial-origin-feasibility.md), [cost ledger](../../checkpoint-049-cost-ledger.json) and [next scope](../../checkpoint-049-next-scope.json) as bounded source-design findings. The specified fresh 14-check screen and the two defining-recurrence migration routes cannot yield a positive net operation saving for the degree-14 target. The separate one-slot receipt remains unresolved. No complete safe admission, positive implementation ledger, runtime candidate or complete-request saving is established.

The 14 checks are an explicit partial screen for one design. They are neither a universal minimum for all possible designs nor a complete authority proof. Missing costs remain unknown nonnegative additions, not assumed zero. A request-local origin proof that shares authority across calls is a different design.

## Correct costs and the resolved notation issue

Under the unchanged fixed native domain, the original coefficient construction costs `4D+3`; a complete miss including lookup/publication costs `4D+5`; and a full-key hit costs one. The affine complete miss costs `3D+6` before new admission, giving `D-1` gross operations. The original separate factorial helper costs one on a hit and `last+1` on a miss for `last>=1`.

The specified miss-side screen checks four helpers for class-slot identity, function-code identity and absence of an instance override. Those twelve checks are followed by exact factorial-tuple identity and current operand-domain checks. These fourteen checks detect different changes. They omit further field acquisition, descriptor, global/default/closure, owner, work, observer, receipt and lifetime costs.

The corrected notation distinguishes `A_complete`, additional charges within a completed coefficient miss, from `A_prefix`, additional charges before the corresponding captured division. Both are nonnegative. One-time factory startup and earlier caller upkeep remain separate request costs and must not be repeatedly allocated to each miss.

| Bound for the specified screen | Result |
| --- | ---: |
| Complete hypothetical coefficient miss | At least `3D+20+A_complete` |
| Complete net saving | At most `D-15-A_complete` |
| Degree-14 complete net saving | At most `-1-A_complete` |
| Corresponding degree-14 partial-prefix saving | At most `-10-A_prefix` |
| Smallest degree with positive complete room before further costs | 16 |

The first reviewed draft used one `A` for both completed and prefix costs. This review requested separate variables because post-prefix publication or cleanup cannot be subtracted from a prefix saving. The corrected report and ledger resolve that issue. The numeric upper bounds of -1 and -10 did not change.

If exactly this screen is applied to all five identified completed misses, their 56 gross operations minus 70 screening charges gives an upper bound of -14 before other costs. Applying it also to the incomplete target gives `(56+4)-84=-24`. Both are conditional schedule bounds. A low-degree filter changes which calls pay the screen and adds its own charge; it cannot retain the same aggregate formula without a new ledger. A threshold of `D>=16` excludes the observed degree-14 target.

## Existing-table migration

At native precision 128, the source chooses `limit=36` and `last=73`. A defining-recurrence rebuild through `73!` requires 72 guarded multiplications. A narrower rebuild through the degree-14 endpoint `29!` requires 28. These counts exclude comparisons, type/authority checks, copies and storage.

The degree-14 complete opportunity is thirteen operations, so the multiplication-only upper bounds are `13-28=-15` and `13-72=-59`. If a fresh full-table audit is paid inside the identified captured interval, its 72 multiplication charges exceed the 56 completed plus four partial gross operations by twelve. That interval placement is a condition of the bound. It does not establish the cost of an unknown successful tail or of amortization over unobserved events.

These bounds reject the stated recurrence migration mechanisms. They do not charge a future origin mint for original factorial multiplications that a fresh request must already perform. New minting and maintenance still have to be priced separately.

## Path coverage and storage

The ledger correctly separates these paths:

- A coefficient hit can remain one charge only when new coefficient admission follows the existing lookup. Earlier factory upkeep can still increase the caller's cost.
- A cold factorial construction retains every original multiplication and publication. Authenticated minting, validation and retention are additional work.
- Every factorial hit that performs receipt or owner maintenance pays it even when the later coefficient lookup hits, the selected degree is too small, or the dyadic route later rejects.
- An unreceipted or replaced table must not acquire authority from its native tuple shape, key, current factory method or object ID. Any checks executed before fallback still cost work.
- Degrees one and two have zero and one gross operations respectively. A rejection filter, startup cost or extra lookup cannot be hidden on those paths.
- Domain changes, cache pressure, interruption and unsupported callbacks retain their original behavior and completed effects. Added invalidation, cleanup or later recomputation must be counted.

A strong tuple reference avoids copying the immutable integers and prevents recycled-ID confusion. It can also retain numerical values after ordinary eviction. A separate slot therefore requires an explicit capacity and lifetime rule; bounded object count alone does not preserve the 256-entry numerical-cache contract. Reserving a slot can cause different eviction and recomputation. A same-entry wrapper avoids neither authentic-origin obligations nor the cost of wrapper/type/unwrapping work on every affected hit. No extra numerical slot is approved.

## Native callbacks and observers

The reviewed call chain begins at `_Arithmetic.tick`, enters `ReachExecutionWork.tick` and `charge`, and calls the native external `ConstructionBudget.tick`. After that callback returns, reach accounting and the captured work observer run; `_Arithmetic.tick` then runs its product and source observers. The original external callback runs before the reach work counter increments; failures preserve their original object through `callback_error`. The arithmetic observer installed by `_Guard.original` is active at the target.

The native source does not itself change the factorial tuple or operand cap on this path. Admission must nevertheless bind the actual work owner, stored maps/scalars, method dispatch and observers. A native dictionary containing foreign keys or values, or a replaced counter/limit scalar, can make apparently ordinary accounting execute different behavior. Checking only the callback object is insufficient. Every added admission tick also executes the original callback chain and may exhaust the remaining allowance before the original arithmetic.

The source observer deliberately allows a narrowed cap to reach the original prospective arithmetic guard. After the denominator and lane shifts, the original duplicate shift requires prospective width `q`, while the affine lane addition requires `q+2`. A temporary cap of `q` distinguishes their refusals. The fixed-domain width proof cannot authorize that generic callback case. Early optional fallback must not suppress an original refusal, and a new affine refusal must not be mislabeled as the original operation's failure. Current C035 product receipts do not authenticate the four series helpers or the factorial tuple.

## Next bounded task

The proposed C050 question is materially different from the rejected screen: begin with a fresh native arithmetic owner and empty cache, preserve the original raw tuple representation, and prove factorial-key origin through the whole admitted native writer/mutation/callback graph. The decisive cost question is whether a bounded request-lifetime authority proof can replace repeated helper audits without uncharged per-tick work or new upkeep on every factorial hit.

Require actual startup and refresh costs, all hit/rejected-path costs, precise invalidation and preserved failure behavior, and prospective eligibility through the last-73 factory to the degree-14 call. The seven initially resident coefficient keys are not seven observed construction events. Any new whole-request event or amortization claim needs its own source/evidence proof. A same-entry receipt remains a separately costed alternative. If the specific closure cannot be proved or its full net bound is nonpositive, close that hypothesis and choose another source target.

This review does not establish the documentation check, archive recovery or publication result; root records those separately. It changes no Original28 result, C035 hold, release acceptance or main-integration status.
