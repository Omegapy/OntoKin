# C048 general series-coefficient construction feasibility

Date: October 27, 2026, America/Denver. Owner: `interactive-reach06-series-coefficient-feasibility-20261027-c048-91b3`. Base: final C047 `3ad8e84209bf0b39716dc6167ca4553dcf3aa29f`, tree `c8674859f621c953653002f457e979491f03b7e0`. [Owned scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6444541131).

**Result: no runtime implementation is selected.** The two-endpoint design with preserved checkpoints and the affine design with fresh per-interior divisibility checks have no positive net operation bound. A more substantial affine arithmetic identity and its prospective-width proof are established for genuine factorials in the unchanged native domain. A bounded factorial-origin design remains open; this is not a proof that every coefficient optimization is impossible.

This is a source and retained-data feasibility checkpoint. No OntoKin import, candidate numerical replay, original request, runtime test, benchmark, hosted job, main merge or release acceptance occurred. Original28 remains **24/28**, and C035 remains held, including its earlier adverse timing.

## What was verified

Live startup reads preserved the C047 publication, PR #44's open draft status, main `2bb4588e121fcfe99b4d42c734b15b38362f3642`, 93 existing branch heads and 23 open draft PRs. C047 had explicitly released ownership. C048 owns only new checkpoint records on `work/reach06-series-coefficient-feasibility-20261027-c048-91b3`; no main integration lease is acquired.

All seven uploaded original payloads match their published C047 Git blobs. The complete 18-part C047 archive was restored with the unchanged recovery utility in a separately declared exclusive window. All 414 members, ZIP CRCs, membership, paths, hashes and extracted bytes pass. No archived program was executed. The new independent retained-data audit passes **30 grouped metadata checks over 325 stable inputs**, including all **311 snapshots / 122,526,082 bytes**. These are evidence checks, not runtime tests. [Evidence review](checkpoint-048-reviews/evidence/review.md).

The source snapshot contains **813 exact C047 files / 59,720,305 bytes**, including all **65 runtime modules**, all original Markdown/HTML documents and the complete current capture archive. Every recovered file is bound to the untruncated 2,673-file remote tree. This is a partial source snapshot, not a complete Git checkout. Direct authenticated download links returned 404 for 2,359 missing files; three already recovered files were verified. No failed download substituted content, and temporary signed-URL manifests were deleted. The repository connection recovered the files needed for this analysis and nearly all documentation dependencies. Twelve older binary evidence archives remain unavailable locally. The unchanged full documentation checker and its actual limitations are recorded in [validation](checkpoint-048-validation.json); no full-checkout or passing full documentation gate is inferred.

## Original equations and costs

The source is `_Arithmetic._series_coefficients`, `_series_factorials`, `_series_integer` and `_series_dyadic` in [the exact independent reference](https://github.com/Omegapy/OntoKin/blob/3ad8e84209bf0b39716dc6167ca4553dcf3aa29f/ontokin/reach_reference.py). These Taylor-series coefficients are separate from centered Hamilton coefficients and C035 product receipts.

For selected degree `D >= 1`, dyadic exponent `e >= 0`, and genuine factorials, define:

```text
F = (2D+1)!
Q = F * 2^(2eD)
q = bit_length(Q)
L = 2^q
f_i = (2i+1)!
C_i = (F/f_i) * 2^(2e(D-i)) * (L+2i+1)
```

The source uses floor division, which is exact on this factorial domain. The unchanged packed Horner loop extracts the sine-without-midpoint and cosine numerators. The unchanged return path supplies the additional midpoint factor for sine. The selected first strict stopping degree, exact polynomial values, alternating-tail remainder, Fraction conversions and outward grid guards remain fixed.

Under a fixed native operand domain, each `_series_integer` call charges once before checking its prospective allocation. The original helper costs `4D+3` construction operations and `4D+5` for a complete miss including lookup/publication. A full-key hit costs one. At degree 14, these are **59 / 61 / 1**. Cache-domain changes and arbitrary callbacks can add other work; they are not included in this fixed-domain formula. [Complete cost review](checkpoint-048-reviews/cost/review.md).

The unchanged factorial helper costs one lookup on a hit. For `last >= 1`, a fixed-domain miss costs `last-1` multiplications plus lookup and publication, or `last+1`. The caller's `last=2*limit+1` remains at most 129. None of that startup work is silently removed or priced as a hit.

## Design A: reuse the two endpoint identities

At index 0, the coefficient's shift recomputes the already available `Q`. At index D, the division is `F/F=1`, so the packed coefficient is `L+2D+1`. These identities offer two gross arithmetic operations per completed positive-degree miss.

The helper also supports live callbacks and mutable operand limits. Removing its original charge/checkpoint can change which operation receives a callback. The numerical review gives an unexecuted symbolic example: a temporary limit of `q` admits the original repeated shift, but rejects the lane addition moved into that callback position, whose prospective width is `q+2`. The final division has an analogous counterexample. This is a control-flow argument, not a measured hostile probe.

For the literal variant that retains both original callback and prospective-guard checkpoints, the ledger is two removed arithmetic charges and two retained checkpoint charges. Net saving is **zero before any new screening**. Extra native, domain, type or ownership checks only lower that bound. Omitting those checkpoints unconditionally is not approved. The rejection concerns this concrete operation-budget design, not a claim about elapsed-time improvement or every possible native admission.

## Design B: advance an affine numerator

A larger general arithmetic opportunity uses:

```text
N_i = F * (L+2i+1)
N_0 = F * (L+1)
delta = 2F
N_i = N_(i-1) + delta
C_i = (N_i/f_i) * 2^(2e(D-i))
```

Build through `N_(D-1)` and form `C_D=L+2D+1` directly. This schedule replaces repeated packed multiplications with numerator additions.

| Construction work | Charges |
| --- | ---: |
| Original denominator and lane shifts | 2 |
| Add `L+1`, multiply by F | 2 |
| Shift F to form delta | 1 |
| Shift N_0 to form C_0 | 1 |
| Each interior: numerator add, divide, coefficient shift | 3(D-1) |
| Direct last coefficient add | 1 |
| **Construction** | **3D+4** |
| **Complete miss, with original lookup/publication** | **3D+6** |
| **Gross arithmetic difference from original** | **D-1** |

At degree 14, the complete-helper arithmetic ceiling is **13 operations**. It is not a candidate's net saving. Degree 1 offers zero under this schedule; degree 2 offers only one. An entry screen, low-degree fallback and every actual miss-side check must be costed. Moving admission after the existing coefficient lookup can preserve the one-charge hit path, but does not make miss or rejected-path checks free.

### The original operand cap is sufficient

Let `b=bit_length(F)` and `q=b+2eD`. Since `2i+1 <= 2D+1 <= F < L`, `bit_length(L+2i+1)=q+1`. Each affine numerator is at most `b+q+1` bits. Its multiplication preflight needs that bound; its update needs at most `b+q+2`. Division needs at most `b+q+1`, and the subsequent coefficient shift needs at most `2q+1`. The final add needs `q+2`. Thus `2q+2` bounds all new prospective widths.

The unchanged caller defines `H=2*limit+1` and `W=H*e+H*bit_length(H)+1`. Genuine factorials and `D<=limit` imply `q<=W`. Its existing sufficient admission, `max(2W+2e+5, W+bits+11) <= operand_limit`, dominates the new bound. The numerical and cost reviewers derived compatible bounds separately. No cap, source equation, stopping rule or remainder change is needed in this fixed native domain. Every actual new operation must still run its original-style leading charge and prospective guard. A later domain mutation invalidates reliance on an old width admission. [Numerical and authority review](checkpoint-048-reviews/numerical/review.md).

The output retains the same `D+1` coefficient integers, Q, L, key and publication. The affine numerator and delta are bounded local integers. Old and new numerator objects can coexist during reassignment; the implementation's peak temporaries must be counted. This arithmetic schedule adds no persistent cache. A proposed origin receipt would add separate storage and lifetime obligations.

### Exact divisibility needs authority

For arbitrary cached integers, `floor(F/f_i)*(L+2i+1)` and `floor(F*(L+2i+1)/f_i)` can differ. A native tuple and native integer types do not prove `f_i` divides F. The existing cache is externally mutable, and `_series_factorials` returns cached payloads without an origin receipt. No actual C047 corruption is alleged.

The concrete conservative variant considered here checks divisibility for every interior coefficient using one guarded integer operation. The `D-1` added operations alone consume the entire `D-1` gross saving:

```text
maximum net saving
  = (D-1) saved arithmetic - (D-1) divisibility operations
    - additional admission/remainder/owner/copy/storage/fallback costs
  <= 0
```

The bound explicitly leaves the remaining added costs nonnegative; it does not price unspecified checks at zero or pretend to be a fully implemented positive candidate. This suffices to reject that fresh per-interior audit design. It does not reject a separately proved bounded factorial-factory origin mechanism that could avoid those repeated audits.

## Why the existing native path is insufficient

`_series_coefficients` has no reusable native-owner receipt. `_series_dyadic` proves a dyadic/width domain, not all mutable dispatch, cache-origin and callback conditions. `_Guard.current` binds centered owners and cells; C035's `_product_native` covers another route and does not pin the four series helper methods or prove factorial provenance.

The observed forearm reseeding calls `_Guard.original(body.direct, clock)`. That method installs a non-null `_recording_after_tick` observer for the direct call and restores it while unwinding. A gate requiring this observer to be `None` therefore excludes the actual target. The capture's outer work-observer value and boundary restoration checks do not imply an absent internal source observer. The original failure object and the original live-cap refusal policy must remain intact; an optimization cannot turn an original refusal into optional fallback.

## Current census and bounded opportunity

The verified twelve resident keys span degrees `{2,7,8,13,16,17}` and exponents `{50,52,53,127,128,129}`. Degree 16 occurs at four exponents, degree 13 at three and degree 17 at two. This supports investigating common factorial work across exponents; it does not provide internal hit counts or publication order.

Within C047's proved interval, five new completed keys have degrees **7, 8, 13, 17 and 16**. Their affine complete-helper arithmetic ceilings total **56** before added costs. The seven initially resident keys belong to prior setup and cannot be counted as seven observed construction events.

At the failed degree-14 helper's corresponding index-7 division, the original completed **29** construction operations. The proposed arithmetic schedule reaches that point after **25**, a **four-operation gross prefix difference**. The complete-helper 13-operation ceiling concerns an unexecuted tail. Neither 4 nor 56 nor 13 is a measured request saving. The missing `(129,14)` key cannot be treated as an existing full-key hit, and a new degree-only cache cannot assume a warm degree-14 entry.

## Decision and next bounded task

Record scoped **NO-GO** for the checkpoint-preserving endpoint design and the fresh divisibility-audited affine design. Retain the affine equation and its fixed-domain width proof as useful completed work. No implementation is selected and no runtime replay is authorized by this review.

The next bounded task is **C049 factorial-origin and native-admission feasibility**. Define a bounded origin proof for genuine `_series_factorials` output, covering the already resident table used by the target, exact methods and owners, cache replacement and domain changes, active source observers, cold starts, hits and rejected paths. Price every new charge and value against `D-1`, including current degree 14. A factory-fresh-only route cannot automatically claim eligibility for that existing table. Reject a design whose complete bound is nonpositive, and preserve other possibilities as unresolved. Resolve the documented full-checkout/checker limitation before claiming that gate. [Structured next scope](checkpoint-048-next-scope.json).

Any later implementation or numerical replay needs its own reviewed bounded plan and active exclusive window. Completing L03 still requires a fresh complete original request under all original limits, not continuation of the failed tail. P11/P16/P23 and every complete release requirement remain separate and open.
