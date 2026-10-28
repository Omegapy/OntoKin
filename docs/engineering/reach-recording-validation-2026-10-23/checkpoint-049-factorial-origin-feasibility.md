# C049 factorial origin and native admission feasibility

Date: October 27, 2026, America/Denver. Owner: `interactive-reach06-factorial-origin-feasibility-20261027-c049-e7a2`. Base: final C048 `8b6df27e323797e6b93bc9b44b5cd9083d4e3859`, tree `4ff706f642beac532eb44f0ec879ec99491f873f`. [Owned scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6446434735).

**No runtime implementation is selected.** A concrete fresh four-helper screen is already too expensive for the degree-14 target, even before it becomes a complete safe admission. Revalidating the existing table through its factorial recurrence is also too expensive. A single retained tuple can carry mathematical origin only under additional ownership, construction, observer and lifetime proofs. This review defines those obligations and separates a future complete request from the captured request's existing, unreceipted table.

The independent [numerical and authority review](checkpoint-049-reviews/numerical/review.md) and [cost review](checkpoint-049-reviews/cost/review.md) bound the conclusions. The [ledger](checkpoint-049-cost-ledger.json) explicitly records incomplete candidate costs as unknown nonnegative additions. It is not a complete positive implementation ledger. [Validation](checkpoint-049-validation.json) records the actual documentation gate, source identity and recovery results. No product import, numerical candidate replay, original request, runtime test or benchmark is part of this checkpoint.

## Preserved arithmetic and current target

C048's affine identity remains valid for genuine factorials. For degree `D >= 1`, exponent `e >= 0`, `F=(2D+1)!`, `Q=F*2^(2eD)` and `L=2^bit_length(Q)`, form `N_0=F*(L+1)` and advance `N_i=N_(i-1)+2F`. Interior coefficients are `(N_i/(2i+1)!)*2^(2e(D-i))`; the last coefficient is `L+2D+1`.

This preserves the exact polynomial, the first strict stopping degree, packed Horner evaluation, remainder and outward rounding in the proved domain. C048's bound `2q+2`, where `q=bit_length(Q)`, fits the unchanged caller admission. It does not cover a later mutation of the admitted limit.

The original complete miss costs `4D+5`, including lookup and publication. The affine schedule costs `3D+6` before new admission. Thus the complete gross opportunity is `D-1`, or **13 at degree 14**. At the captured corresponding index-7 division, the original has completed 29 construction operations and the hypothetical affine schedule has completed 25: **four gross prefix operations**. The unexecuted tail and complete request saving remain unknown.

The current evidence is the published C047 source-and-data result, checked again in C048. C049 reads those identified records; it does not rerun the pair or restore and re-audit all 311 snapshots. The five completed new keys have degrees 7, 8, 13, 17 and 16, with combined gross opportunity 56. The seven initially resident keys are not seven newly observed misses. The degree-14 coefficient key was absent in the proved interval, while the factorial table used by that call already existed. [C047 lifetime review](checkpoint-047-lifetime-review/review.md) and [C048 review](checkpoint-048-series-coefficient-feasibility.md).

## A concrete one-slot origin protocol

The smallest retained-object proposal examined here keeps one strong reference to a completed immutable factorial tuple per arithmetic owner. A conceptual receipt binds that exact tuple, its highest factorial index, the arithmetic owner, the cache owner, the admitted operand domain and the authority that performed the construction. These are required relationships, not a selected Python representation or a claim that a private attribute is unforgeable.

| State or event | Required behavior |
| --- | --- |
| New arithmetic owner | No table has origin authority. `_Arithmetic.__init__` currently creates an empty cache. |
| Genuine factorial miss | Build the original values through the unchanged guarded multiplication path. Mint authority only after a complete authenticated construction and admitted publication. |
| Existing unreceipted hit | Return through the original helper behavior; do not infer origin from the key, shape, present native method or object ID. The affine optimization remains ineligible. |
| Receipted factorial hit | The exact returned tuple must match the retained origin object, with current owners/domain and valid authority. Equality of contents is not an identity proof. |
| Coefficient-key hit | Keep the original lookup/return before any new coefficient admission. Factory-side maintenance, if introduced earlier in the caller, is still additional request work. |
| Table replacement | A different tuple cannot inherit authority. Restoring the original exact tuple would require the receipt's still-valid owner/domain/lifetime proof. |
| Clear, eviction, owner/domain replacement or unsupported observer | Invalidate or follow a separately proved lifetime rule before reuse. No stale authority or hidden retained numerical allowance is permitted. |
| Interrupted construction/publication | Do not mint a receipt for an incomplete table. Preserve the original exception and every already completed cache effect. |

The mathematical origin statement is stronger than an exact-division test. It covers the initial values `0!=1`, `1!=1`, every required native integer and every multiplication in the defining recurrence. Checking the factory at entry does not certify subsequent construction if an admitted callback can replace a helper, alter a limit or change dispatch. A marker stored beside an externally replaceable payload cannot authenticate itself.

Keeping the strong tuple reference avoids copying its integers and prevents object-ID reuse from confusing two objects. It also retains numerical data if the ordinary cache entry is evicted. Therefore a separate slot is not automatically free under the existing 256-entry bound. Reserving capacity for that slot can displace another entry; clearing it on eviction requires recognizing and charging that event. A second dictionary adds lookup/publication/occupancy work. A same-cache-entry record would be a different representation with its own compatibility and authority proof. No extra numerical slot is authorized here.

This protocol is bounded in object count, but its trustworthy implementation is unresolved. In particular, no protected minting mechanism, complete descriptor/global/default/closure admission, or callback-stable lifetime mechanism is selected.

## Design A: fresh four-helper admission

For a specific conservative route, place a fresh screen after the existing coefficient lookup misses. Check `_series_factorials`, `_series_coefficients`, `_series_integer` and `_series_dyadic` separately for (1) current class-slot identity, (2) unchanged function code identity, and (3) absence of an instance override. Then check the passed tuple's identity against an authenticated retained tuple and the current operand domain against the admitted domain.

| New work in this specified screen | Minimum charges |
| --- | ---: |
| Four current class-slot identity checks | 4 |
| Four function-code identity checks | 4 |
| Four instance-shadow checks | 4 |
| Exact passed-tuple identity check | 1 |
| Current operand-domain check | 1 |
| **Subtotal** | **14** |

These checks detect different changes. A class identity check does not detect in-place replacement of the same function's `__code__`; class and code checks do not detect a shadowing instance method. The counting contract charges each new lookup, type/limit/claim check, output occurrence and copied logical value. The subtotal does not exempt the inspections needed to obtain those values or any additional checks. [Adopted budget counting, section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse).

Let `A_complete >= 0` be further authority, receipt, observer, copying, lifetime and publication charges actually incurred within the completed coefficient-miss path. Let `A_prefix >= 0` include only further added charges before the corresponding division. Factory startup and earlier caller upkeep remain separate request costs; they are not charged repeatedly in these per-miss bounds. The complete miss would cost at least `3D+20+A_complete`, so its net saving is at most `D-15-A_complete`. At degree 14:

```text
complete-helper net saving <= 13 - 14 - A_complete = -1 - A_complete
corresponding prefix saving <= 4 - 14 - A_prefix = -10 - A_prefix
```

This is enough to reject the specified route for the target. The 14-check subtotal is a partial screen, not a complete safe admission and not a universal lower bound on all designs. Sharing authority across calls, a different invocation structure or not rechecking an already executing helper would be different designs requiring their own proof and full accounting.

If exactly this screen is paid on all five newly completed misses, the conditional combined bound is `56-5*14=-14` before other costs. If it is also paid on the incomplete degree-14 call, the combined observed-progress bound is `(56+4)-6*14=-24`. These are hypothetical schedule bounds against identified source events, not measured request costs or estimates of the failed tail.

A low-degree filter changes the ledger. A separately charged filter can avoid the full screen for small degrees, but it adds work to every miss it inspects. Even with every other new cost set to zero, this screen needs `D >= 16` to have positive complete-helper arithmetic room. Such a filter excludes the degree-14 target. Degree 1 has zero gross arithmetic room and degree 2 has one; neither can silently pay startup or admission elsewhere.

## Design B: authenticate the existing table by recomputation

At the observed native precision `bits=128`, `_series_dyadic` computes `limit=36` and `last=73`. Rebuilding the defining recurrence through `73!` requires **72 guarded multiplications** for factors 2 through 73. Comparing that rebuild to the stored table, validating types and current authority, and any copies add work.

Even a restricted recurrence through `29!`, the endpoint factorial for degree 14, requires **28 multiplications**. This restricted audit is not a proof of the whole 73-index table; it only bounds the cost of that narrower migration approach.

Against the degree-14 complete opportunity, these multiplication-only bounds are `13-28=-15` and `13-72=-59`. If the full-table audit is newly paid inside the captured interval, its 72 multiplications also exceed that interval's `56+4=60` gross arithmetic room by 12 before other work. The placement is explicit. No claim is made about amortizing an audit over unknown future events or a complete successful request.

This rejects those defining-recurrence migration routes. It does not reject attaching origin during factorial construction already required by a new complete request.

## Active observer and original failure identity

The actual forearm reseeding route enters `_Guard.original`, which installs a non-null `_recording_after_tick` observer. A hooks-None screen therefore excludes the target. Recognizing that closure's identity is also insufficient: it calls `current()`, checks live owners, can raise identity or precision failures, and deliberately leaves a narrowed operand limit for the original operation's prospective guard.

The operation order supplies a source-only counterexample to unconditional rewriting. After denominator and lane construction, the original next operation is the duplicate shift, with prospective width `q`. The affine next operation is the lane addition `L+1`, with prospective width `q+2`. A supported callback that temporarily narrows the cap to `q` distinguishes their refusals. Early optional fallback can suppress an original refusal; proceeding with the affine operation can introduce a refusal at a different operation. C048's fixed-domain width theorem does not resolve that mutation case.

The native request described by C047 used ordinary `ConstructionBudget.tick` without a custom check. Current source for `ReachExecutionWork.charge` invokes that external callback, checks its own counters/time, updates its counts and then invokes `_source_after_charge`. `_Arithmetic.tick` subsequently runs the captured product and source observers. These native paths do not themselves change the factorial tuple or operand cap. That is useful source evidence, but a current receipt must also admit the actual work objects, maps, scalar fields, callback/observer owners and mutable dispatch. Foreign map/scalar behavior can make apparently ordinary lookup or accounting effectful. Every new admission tick also invokes the callback chain and can exhaust the remaining budget before original work.

No shortcut may convert an original failure to optional retry, replace the caller's failure object, remove cancellation checkpoints or treat restored outer observer state as absence of the internal observer. Existing C035 product receipts do not pin the four series helpers or prove the factorial table's origin.

## Prospective complete-request eligibility

All 65 current runtime modules were recovered and Git-hash verified. A text/AST inventory finds `_series_dyadic` as the sole explicit runtime call site of `_series_factorials` and `_series_coefficients`. This inventory does not authorize arbitrary external or dynamically replaced callers. With fixed native `bits=128`, each of those factorial calls asks for `last=73`.

For a **future complete request starting with a fresh native arithmetic owner**, the first genuine factorial miss is therefore an opportunity to mint origin while performing the original required construction. A previously constructed table can then be a receipted hit later in that same new request. This is a conditional eligibility route, not retroactive authority for C047's table and not a promise that a proposed receipt survives every cache event. Other callers, generic precisions, replacements and unsupported callbacks still need original behavior.

Before claiming target eligibility, prove admission from the actual first construction, continued current native authority, precise tuple identity at the degree-14 call, and receipt survival or correct reminting through every eviction, clear, owner change and interruption. Charge factory startup and maintenance even for later coefficient hits or dyadic fallback. The current capture does not record these proposed receipt events, and no new request ran in C049.

## Decision and next scope

Record scoped **NO-GO** for Design A's fresh 14-check screen and Design B's full or degree-14-prefix recurrence migration. Record the separate one-slot protocol as **unresolved**, because its authenticated authority, exact storage treatment and complete net cost remain unproved. The result does not establish that every coefficient optimization is impossible.

The next distinct source-design task is **C050: request-local factorial-cache origin closure with the existing raw tuple representation**. Start with a fresh arithmetic owner and empty cache; prove the native factory is the only admitted writer of factorial keys, every permitted cache mutation preserves their origin, and the native caller passes the exact returned tuple. Determine whether this authority can remain valid across the actual callback graph without a fresh four-helper audit on every miss or uncharged per-tick work. This avoids adding a persistent numerical slot or a wrapper/unwrap operation to every factorial hit. A same-entry receipt is a separate fallback design only if this closure cannot be proved; its hit-path and representation costs must then be explicit. Neither approach is approved. [Structured next scope](checkpoint-049-next-scope.json).

Require a complete cold/hit/miss/rejected ledger, target eligibility, preserved error identity, bounded storage and independent review before implementation. Any numerical execution requires its own reviewed bounded plan and active exclusive window. Original28 remains **24/28**, P11/P16/P23/L03 remain unresolved, C035 remains held including adverse timing, and all complete release obligations remain open.
