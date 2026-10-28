# C048 independent numerical and authority review

Reviewer: `/root/numerical_review`. Date: October 27, 2026. This is a source and retained-data review, with no OntoKin import, runtime test, numerical candidate replay, original-request rerun, or failed-tail continuation.

## Source and evidence

The reviewed runtime is the unchanged C047 source at `3ad8e84209bf0b39716dc6167ca4553dcf3aa29f`. The main mathematical source is `ontokin/reach_reference.py`, SHA-256 `db2fa3853e231e399ca2d48e5dea04455aeb0f80f11b4f42a478c34e0c717dc6`. Relevant methods are `_series_integer` (435–459), `_series_factorials` (461–469), `_series_coefficients` (471–491), `_series_dyadic` (493–573), and `_series_sincos` (575 onward). Cache and callback behavior comes from `_Arithmetic.tick`, `lookup`, `remember`, and `operand_limit`; centered original-call behavior comes from `_Guard.current` and `_Guard.original` in `reach_reference_center.py`.

The adopted `ADOPTION.md` establishes authority despite the historical draft label on `budget-counting.md`. Section 3 requires charging new lookups and type/domain/claim checks, bounded storage, independent numerical authority, and preserved cancellation behavior. The current C047 coefficient census has SHA-256 `2bd996e0ac9afb23cf6025ae3584c8c80ba8967ff0009b2daaaf32ac1febf779`.

After root closed the exclusive archive-restoration window, I read the restored `c047-execution/capture-001/capture.json`, `failure-locals.json`, and the current lifetime source checklist. The retained failure fields are degree 14, exponent 129, search limit 36, last factorial index 73, and sufficient width 9,929. They identify the original failed helper, not a candidate execution.

## Exact equations

Let `d >= 1` be the selected degree and `e >= 0` the dyadic exponent. Write:

- `F = (2d + 1)!`;
- `Q = F * 2^(2ed)`;
- `q = bit_length(Q)`;
- `B = 2^q`, the packed-lane base;
- `f_i = (2i + 1)!` for `0 <= i <= d`.

The existing helper constructs

`a_i = (F / f_i) * 2^(2e(d-i))`

and

`c_i = a_i * (B + 2i + 1)`.

The divisions are exact for the standard factorial sequence. For midpoint `m = n/2^e` and `p = n^2`, unchanged Horner evaluation computes the packed sum `sum((-p)^i * c_i)`. Its upper lane yields the sine polynomial divided by `Q`, and its lower lane yields the cosine polynomial divided by `Q`. The final multiplication by `n` and denominator shift by `e` supply the additional midpoint factor for sine. The two lanes retain the original exact polynomial values.

The original `_series_dyadic` selects the first strict stopping degree using its existing binary search and exact descending comparisons. Its tail is `p^d / ((2d)! * 2^(2ed))`. None of the proposed construction identities requires changing that degree, tail, midpoint, Horner loop, or error/grid handling.

These are Taylor-series coefficients. They are separate from the centered Hamilton coefficients and the C035 product receipts.

## Endpoint-only identities

The first coefficient's shifted factor is already `Q`, so its repeated `F << (2ed)` can be replaced algebraically by the local denominator value. At the other endpoint, `F/f_d = 1`, so `c_d = B + 2d + 1`.

These avoid two integer operations per completed genuine miss in a fixed native domain. The current failed helper reached only index 7, so only the first endpoint was before the original failure boundary. The full two-operation saving must not be assigned to that incomplete construction.

The last-division identity alone does not require checking every factorial entry. An immutable native tuple, an unchanged native degree, and the same nonzero native integer at its final slot suffice: the local `F` came from that same slot. Those premises still need authority; a cached tuple's mere existence supplies none.

### Symbolic callback counterexample

The following is source reasoning, not an executed probe. Set `w = bit_length(F)`, `s = 2ed`, and `q = w+s`. At the callback immediately preceding the original duplicate first shift, a supported mutable work context temporarily lowers its operand cap to `q`, then restores it at the next callback. The original shift passes, because its prospective width is `q`. Its later packed addition occurs after restoration.

If the duplicate shift and its tick are removed, the packed addition instead receives the narrowing callback. Since `B` has `q+1` bits, the addition's prospective extent is `q+2`, and it fails. The old and substituted routes therefore differ under an allowed live-cap change even with ordinary native integer coefficients.

The final division has the same issue: a temporary cap of `w` allows the original `F//F`, whereas substituting the following packed addition at that callback can fail. Retaining both original tick-and-guard boundaries avoids these particular differences but consumes the entire two-operation gross saving. It may avoid CPU arithmetic; it does not provide a positive shared-operation saving.

Disposition: the unconditional endpoint-only substitution is not approved. A separately admitted stable native domain is a distinct design requiring its own complete costs.

## General affine-numerator construction

A broader arithmetic identity has greater structural opportunity. Define

`N_i = F * (B + 2i + 1)`.

Then

`N_0 = F * (B + 1)` and `N_i = N_(i-1) + 2F`.

For the exact standard factorial sequence,

`c_i = (N_i / f_i) * 2^(2e(d-i))`.

This replaces the repeated packed multiplication with one update of an affine integer numerator. The final coefficient can still be formed directly as `B + 2d + 1`.

A concrete arithmetic schedule for `d >= 1` is:

1. Construct `Q` and `B` using the two existing guarded shifts.
2. Construct `N_0` using one guarded addition and one guarded multiplication.
3. Construct `delta = 2F` using one guarded shift.
4. Form `c_0` by shifting `N_0` by `2ed`.
5. For `i = 1, ..., d-1`, update `N` by `delta`, divide by `f_i`, and shift by `2e(d-i)`.
6. Form `c_d` using one guarded addition, then publish the same completed tuple/denominator/lane result.

The arithmetic construction count is `3d+4`, compared with the original `4d+3`. The gross arithmetic difference is `d-1`; at degree 14 it is 13 operations. This count does not include any new eligibility, authority, divisibility, callback, copy, storage, or fallback cost. The less specialized schedule that also constructs the last numerator uses `3d+5`, giving `d-2` gross operations. Neither is a candidate net-saving result.

### Prospective-width proof

Let `f = bit_length(F)` and `s = 2ed`, so `q = f+s`. For `d >= 1`, each odd factor satisfies `2i+1 <= 2d+1 <= F < B`. Hence `bit_length(B+2i+1) = q+1`.

Every affine numerator has at most `f+q+1` bits. `delta` has `f+1` bits. The initial numerator multiplication needs at most `f+q+1` prospective bits. A numerator addition needs at most `f+q+2`; its exact division needs at most `f+q+1`. A subsequent coefficient shift needs at most `f+q+1+s = 2q+1`. The direct last addition needs `q+2`. Thus `2q+2` bounds every added prospective integer width, including its operands.

The existing caller defines `H = 2*limit+1` and `W = H*e + H*bit_length(H) + 1`. Because `d <= limit`, the standard factorial bound gives `q <= W`. Its existing admission requires `max(2W+2e+5, W+bits+11) <= operand_limit`. That bound already dominates `2q+2` for `e >= 0`.

Therefore the affine construction needs no raised operand cap in that unchanged admitted native domain. Every actual new integer operation must still run its own prospective guard. The proof does not authorize skipping those guards, ignoring a later cap change, or using the caller's old bound as authority after mutation.

The output tuple has the same `d+1` integers and the same `Q` and `B`; the arithmetic identity needs no new persistent cache entry. It adds an affine numerator and a doubled-common-factor temporary. During a replacement assignment, old and new numerator objects can coexist. These temporaries have bounded widths as above, but their references, any added containers, and the peak lifetime must be included in an implementation ledger. A future origin-receipt cache is a separate storage proposal.

### Divisibility and origin are unresolved requirements

The original helper computes `floor(F/f_i) * (B+2i+1)`. The affine form computes `floor(F*(B+2i+1)/f_i)`. These are equal on the proved factorial domain, but not on an arbitrary tuple of native integers.

For a symbolic example, let degree be 2, exponent be 0, and keep the final factorial slot `F=120` while replacing the interior `3!` slot with 7. Then `B=128`; the old interior coefficient is `floor(120/7)*131`, whereas the affine expression is `floor(120*131/7)`. They differ. This is a native immutable tuple with the wrong mathematical provenance; type checks alone cannot establish divisibility. No such corruption is claimed in C047.

An audit of each interior divisor, or a trusted bounded receipt from the exact factorial factory, can establish the necessary premise. A check charged for each of the `d-1` interior divisions can consume the entire `d-1` arithmetic opportunity before any other admission cost. Replacing an arithmetic division by `divmod` is not automatically a proof of `f_i|F` if it divides `N_i`; the numerator's extra factor could hide nondivisibility of `F`.

## Callback and native-authority boundary

`_series_coefficients` itself has no native receipt. `_series_dyadic` supplies a dyadic and width admission but does not bind all mutable arithmetic methods, cache origin, work/check dispatch, or observers. The cache dictionary is exposed mutable state, and `_series_factorials` returns an existing entry on a hit without an origin receipt.

The current `_Guard.current` checks centered arithmetic owners and source cells. It is not an independent factorial-origin proof. The `_product_native` pinned arithmetic-method list also omits `_series_integer`, `_series_factorials`, `_series_coefficients`, and `_series_dyadic`. C035's product receipt must not be repurposed as unproved authority for these series tables.

The target reseeding runs through `_Guard.original`. That method installs a non-null `observed` closure in `a._recording_after_tick` around `body.direct`, then restores it in `finally`. Consequently a shortcut requiring that hook to be `None` excludes the actual target. Post-exception cleanup values cannot establish that the hook was absent during the failed arithmetic. The ordinary construction callback's `check=None` does not remove this native observer.

`_Guard.original` intentionally lets original arithmetic perform its live prospective checks after cap narrowing and preserves the original error object through `_OriginalFailure`. A construction rewrite must not convert such an original refusal into optional fallback or replace its callback exception. General external callbacks and instrumented/custom arithmetic must retain an explicitly reviewed ineligible path.

## Current disposition

The affine identity and its fixed-domain integer-growth bound are sound as source proofs. The unconditional endpoint-only route is rejected within its stated scope. The affine route has greater gross arithmetic opportunity, but no positive complete net bound or authoritative implementation has been established by this review.

Before selecting it, define the exact native factory/origin and callback admission, include startup and failed/ineligible paths, account for every added charge and retained value, and show that the current target is eligible. A positive arithmetic subtotal alone is insufficient. A source-bound negative result for a particular admission design would not prove that all possible coefficient-construction designs are impossible.

No runtime candidate, L03 success, original28 improvement, benchmark, full release gate, or main integration is asserted. The latest complete original suite remains 24/28 and C035 remains held.
