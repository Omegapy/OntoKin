# C049 independent numerical and authority review

Reviewer: `/root/c049_math_review`. Date: October 27, 2026, America/Denver. Source base: final C048 `8b6df27e323797e6b93bc9b44b5cd9083d4e3859`, tree `4ff706f642beac532eb44f0ec879ec99491f873f`.

**Disposition: accept the stated source-feasibility conclusions and the distinct next scope. No runtime implementation is approved.** The fresh fourteen-check route is too expensive for the degree-14 target; the two defining-recurrence migration routes are also too expensive at that target. These are scoped negative bounds. They do not establish a universal lower bound for admission or rule out every coefficient optimization.

This review inspected source, the identified C047/C048 records, and the exact corrected [C049 feasibility report](../../checkpoint-049-factorial-origin-feasibility.md), [cost ledger](../../checkpoint-049-cost-ledger.json), and [next scope](../../checkpoint-049-next-scope.json). The [result manifest](result.json) binds the reviewed files by byte length, SHA-256 and computed Git blob identity. Runtime modules were read as text for the call-site inventory. No OntoKin module, archived program, candidate, request, test, benchmark or documentation checker was executed by this reviewer. Historical numerical evidence was read, not rerun.

## Preserved mathematical result

For genuine factorials, `F=(2D+1)!`, `Q=F*2^(2eD)`, `q=bit_length(Q)` and `L=2^q`, the affine numerators satisfy `N_i=F*(L+2i+1)` exactly. Starting with `N_0=F*(L+1)` and adding `2F` preserves that identity. Exact division by `(2i+1)!`, followed by the original power-of-two shift, therefore preserves the original coefficient. The direct last coefficient is `L+2D+1`.

The C048 prospective-width argument remains valid in its genuine-factorial, fixed-native-domain premises. If `b=bit_length(F)`, then `q=b+2eD`. New numerator multiplication needs at most `b+q+1` prospective bits, its update at most `b+q+2`, and a coefficient shift at most `2q+1`. Thus `2q+2` bounds the new operations and fits the unchanged caller admission. This does not authorize using an earlier domain proof after a callback changes the live cap.

The original stopping degree, exact packed polynomial, Horner evaluation, alternating-tail remainder, final midpoint factor and outward rounding remain unchanged. The source-derived gross difference is `D-1`; the degree-14 complete ceiling is thirteen, while the corresponding captured index-7 division has only four gross prefix operations. Neither is a measured saving or a known complete-request tail.

## Origin and authority

`_series_factorials` returns a cached object directly on a hit. `_series_coefficients` receives that object as an argument and first performs its independent coefficient-key lookup. A cached key, native tuple shape, present native factory method, object ID, or C035 product receipt does not prove the tuple's mathematical origin.

A strong reference to the exact immutable tuple avoids copying its integers and avoids recycled-object-ID ambiguity. It does not by itself prove authenticated minting, current owners, domain compatibility or lifetime. A separate slot can retain numerical values after ordinary eviction; its storage and invalidation therefore require explicit accounting. A marker next to an externally replaceable payload cannot authenticate itself. The proposed one-slot protocol correctly leaves these matters unresolved.

Factory entry admission alone is also insufficient when a permitted callback can change methods, function code, limits or dispatch during the multiplication loop. Origin must cover the actual completed construction and publication. An interrupted factory must preserve its original failure and completed cache effects without minting authority for an incomplete object.

## The specific negative bounds

The report deliberately specifies four separate class-slot checks, four function-code checks, four instance-shadow checks, a passed-tuple identity check and a current-domain check. These fourteen checks are distinct in this concrete design. A class slot can retain the same function while its `__code__` changes; an instance can shadow an unchanged class method.

The adopted counting rule makes these new checks charged work. Other lookups, descriptor-safe reads, native work/observer admission, origin minting, storage and lifetime costs remain additional. This is a partial screen, not a complete safe admission. At degree 14 it already gives a complete-helper saving at most `13-14=-1`, and a corresponding-prefix saving at most `4-14=-10`.

The final draft correctly distinguishes `A_complete` from `A_prefix`. Publication or other work after the captured division cannot be subtracted as if it occurred in the prefix. Factory startup and earlier caller upkeep are separate request costs and must not be allocated repeatedly to every miss. The corrected bounds `-1-A_complete` and `-10-A_prefix` preserve those distinctions.

The hypothetical five-miss aggregate `56-5*14=-14`, and the aggregate including the partial target `(56+4)-6*14=-24`, are valid under their stated condition that precisely this screen is paid on each identified event. They are not executed request results. A low-degree filter changes the ledger and, for this screen, any threshold with positive arithmetic room excludes degree 14.

For the specified recurrence migration, multiplying successively from `2!` through `29!` requires twenty-eight multiplications; through `73!` requires seventy-two. Comparisons, type/authority checks, copies and storage add work. The narrower route is not a proof of the entire table. Both multiplication-only bounds already exceed the degree-14 thirteen-operation opportunity. The full-table interval comparison is conditional on paying that new audit within the identified interval, and does not price unknown future amortization.

## Active observers and failure identity

`_Guard.original` installs an active source observer. A hooks-None condition excludes the actual target. That observer calls `current()`, can raise identity or precision errors, and intentionally lets the original arithmetic operation perform its live prospective check after cap narrowing. Recognition of its identity alone is not a complete admission.

The source counterexample in the report is valid: after the denominator and lane shifts, the old next operation has prospective width `q`, whereas the affine next addition needs `q+2`. A callback that temporarily narrows the cap to `q` distinguishes those operations. Early optional retry can suppress an inherited refusal; proceeding without an adequate stable-domain proof can introduce a different refusal. `_OriginalFailure` and the caller's original error identity must remain intact.

The reviewed native work and construction methods account for work/time and invoke their admitted observers; their native instructions do not rewrite the factorial tuple or operand cap. A future runtime authority mechanism must still establish the actual callbacks, work/maps/scalars, observer owners and mutable function dependencies. Historical C047 closure does not become a reusable runtime capability merely because the source is currently native. Newly charged admission work also invokes the same callback chain and can itself exhaust the remaining allowance.

## Target eligibility and next scope

The runtime text/AST inventory identifies `_series_dyadic` as the sole explicit call site of both series helpers. This claim excludes arbitrary external or dynamically replaced callers. With native `bits=128`, its factorial request is consistently `last=73`. A future complete request starts with a fresh arithmetic owner's empty cache, so a genuine required factory miss is an opportunity to establish origin before a later degree-14 call uses the table.

That is a conditional route for a new complete request. It does not attest the captured unreceipted table retroactively or authorize resuming the failed tail. It still needs exact tuple identity, continued native authority, cache mutation/lifetime closure, correct reminting after invalidation, and complete startup and maintenance costs.

The next raw-tuple request-local origin-closure scope is a distinct and appropriate hypothesis. It could avoid both a separate retained numerical slot and wrapper/type/unwrap work on every factorial hit. It must prove that the native factory is the only admitted writer of factorial keys from a fresh empty cache, that every allowed mutation preserves origin, and that the actual caller passes the returned tuple. A cached Boolean saying that a request was once native is not that proof.

The next ledger must include all factory hits and caller-side upkeep, even when the later coefficient key hits or the dyadic caller rejects. Source-bound eligible event counts are needed before claiming amortization. A same-entry wrapper is a separate representation alternative with explicit compatibility and hit-path costs. If the specific native authority cannot be established or the complete bound remains nonpositive, select a different source target rather than repeating the same unresolved receipt question.

## Scope of acceptance

This review accepts the corrected source claims, scoped negative bounds and next-task framing only. It does not independently certify remote publication, historical archive recovery, the full documentation gate or release acceptance. Those require their separately retained evidence. Original28 remains 24/28; C035 remains held, and no new complete request or implementation is claimed.
