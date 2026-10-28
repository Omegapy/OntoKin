# C048 independent coefficient cost and storage review

Reviewer: `/root/cost_review`. Source: exact C047 publication `3ad8e84209bf0b39716dc6167ca4553dcf3aa29f`. This review uses source text and retained C047 JSON only. It does not import or execute OntoKin, replay a numerical candidate, execute an archived script, rerun an original request, or measure timing. Root handles acquisition and publication. The numerical reviewer and this reviewer exchanged the affine equation, endpoint accounting, and generic callback counterexample; their review roles are separate, not blind.

## Result

Two concrete conservative designs have no positive operation bound. Preserving both old endpoint callback/guard sites consumes the two operations saved by the endpoint identities. Auditing every interior factorial divisibility with a guarded integer operation consumes the entire `D-1` arithmetic saving of the endpoint-aware affine construction before other new checks.

The affine equation remains a distinct structural opportunity. This review does not establish a general impossibility or reject a future authenticated factorial-origin design. No runtime candidate has a complete positive net ledger here.

## Baseline and unchanged costs

Let `D >= 1` be the chosen degree and `e >= 0` the dyadic exponent. In the current admitted mathematical domain, let `F = (2D+1)!`, `Q = F * 2^(2eD)`, `q = bit_length(Q)`, and `L = 2^q`. The original table entry at index `i` is

`C_i = (F / (2i+1)!) * 2^(2e(D-i)) * (L + 2i+1)`.

This is an exact integer equation for genuine factorials. The source implements the quotient with floor division. Extending the equation to arbitrary values fetched from the public mutable cache requires a separate authority argument.

Under a fixed operand domain, every `_series_integer` call contributes one tick before its prospective guard. The baseline ledger is:

| Work | Charges |
| --- | ---: |
| Full coefficient-key lookup | 1 |
| `Q` shift and `L` shift | 2 |
| Index 0: shift, add, multiply | 3 |
| Each interior index 1 through D-1: divide, shift, add, multiply | 4(D-1) |
| Final index D: divide and add | 2 |
| Publication through `remember` | 1 |
| **Construction** | **4D+3** |
| **Complete miss** | **4D+5** |
| **Existing full-key hit** | **1** |

The source performs the shifts even when `e=0`, so this ledger still applies. Degree zero is outside `_series_dyadic`'s selected positive-degree domain and must retain its original route unless separately admitted. Domain-change cache reset ticks are additional actual work; the formulas do not cover arbitrary changing callbacks.

The separate factorial helper is unchanged by either local construction design. For `last >= 1`, it costs one lookup on a hit, or `last-1` multiplications plus lookup/publication, totaling `last+1` on a fixed-domain miss. `_series_dyadic` chooses `last = 2*limit+1`, with `limit <= 64`. Degree selection, power construction, first strict stop recovery, Horner evaluation, division into lanes, tail formation, Fraction conversion and all outward interval work remain unchanged.

## Endpoint identities

The first coefficient's shift repeats the already completed `Q` calculation. The final quotient is `F/F = 1`. Using those identities removes at most two integer operations per completed positive-degree miss. It adds no persistent numerical cache, no coefficient-table element, and no new publication. It removes a redundant temporary integer calculation; it does not justify a claim about Python object allocation identities.

The original helper accepts generic callback-bearing arithmetic. It has no existing admission proving immutable native factorial inputs, stable operator dispatch and a callback domain that makes checkpoint omission safe. In particular, after the lane calculation has succeeded, a callback can temporarily lower the cap to `q` at the old index-0 shift checkpoint and restore the cap at the following checkpoint. The original repeated shift has extent `q` and can pass. Moving the lane add into that checkpoint requires extent `q+2` and refuses. This is a symbolic source counterexample; no callback or product request was executed.

For the literal checkpoint-preserving variant, retain each removed operation's original tick and prospective check, but substitute its known result afterward:

| Added or removed work | Charge change |
| --- | ---: |
| Omit duplicate index-0 shift operation | -1 |
| Retain that callback and guarded checkpoint | +1 |
| Omit final `F/F` division operation | -1 |
| Retain that callback and guarded checkpoint | +1 |
| Original lookup, publication, tuple/list occurrences and remaining arithmetic | 0 |
| Any newly introduced native/type/domain/claim check | Nonnegative additional cost |
| **Net saving before any new screening** | **0** |

This is a rejection of that literal checkpoint-preserving design as an operation-budget reduction, not a claim that arithmetic elimination can never improve elapsed time. The unconditioned two-checkpoint elision does not preserve the generic callback behavior. A separately admitted native design would need its own full ledger; the two gross ticks cannot be relabeled as net saving.

## Affine common numerator

The numerical review proposes the independent algebraic identity

`N_i = F * (L + 2i+1)`, `N_0 = F * (L+1)`, `delta = 2F`, and `N_i = N_(i-1) + delta`.

Then `C_i = (N_i // (2i+1)!) << (2e(D-i))` whenever the factorial divisor divides `F` exactly. The straight schedule costs `3D+5` construction operations, saving `D-2` gross operations. Building only `N_0` through `N_(D-1)` and forming the last coefficient as `L + 2D+1` yields the endpoint-aware schedule:

| Work | Charges |
| --- | ---: |
| Original full-key lookup | 1 |
| Original `Q` shift and lane shift | 2 |
| `L+1`, then multiply by `F` to form `N_0` | 2 |
| Shift `F` once to form `delta=2F` | 1 |
| Shift `N_0` to form `C_0` | 1 |
| Each interior: numerator add, exact integer divide, coefficient shift | 3(D-1) |
| Final coefficient `L+2D+1` | 1 |
| Original publication | 1 |
| **Construction** | **3D+4** |
| **Complete miss before new admission** | **3D+6** |
| **Gross saving** | **D-1** |

Each new shift/add/multiply/divide must use the original leading charge and prospective allocation guard. A proof of actual result width alone does not discharge these guards. Moving a shift after a division changes intermediate operands. The original conservative `_series_dyadic` width gate must remain; this schedule supplies no permission to weaken it.

The fixed-domain prospective bounds can be established from that unchanged gate. Put `b=bit_length(F)`, `h=2*limit+1`, and `W=h*e+h*bit_length(h)+1`. Then `b <= W-h*e-1` and `q=b+2eD <= W-e-1`. Since `L > 2D+1`, `bit_length(L+odd)=q+1`. The new `N_0` multiply has prospective width at most `b+q+1 <= 2W-1`; a numerator recurrence add has width at most `b+q+2 <= 2W`; and the shifted quotient has width at most `b+q+1+2eD=2q+1`. Lane/final adds need `q+2`, and `delta` needs `b+1`. Each fits the existing `2W+2e+5` sufficient bound. This independent derivation confirms that an increased operand cap is unnecessary in the stable native domain. It does not establish that callbacks leave that domain stable.

The result table still has `D+1` integers, the denominator and lane are unchanged, and the cache key/publication/capacity policy can remain unchanged. The new numerator and `delta` are bounded temporary integers, not a retained cache. Their construction and arithmetic are included above. Any detached copies, retained origin records, additional tuples, factories, lifetime bookkeeping, cache lookups or extra publications introduced to establish authority are not included and must be added explicitly. None is free because the mathematical output is unchanged.

### Exact divisibility is an authority condition

For arbitrary positive integers `F` and `f`, `floor(F/f)*(L+odd)` need not equal `floor(F*(L+odd)/f)`. Native tuple and integer types do not establish `f | F`. `_Arithmetic.cache` is an externally mutable native dictionary, and `_series_factorials` directly returns a cached value. The source's expected factory result cannot be treated as an authenticated runtime receipt after arbitrary cache replacement.

A concrete conservative design verifies `F % factorials[2i+1] == 0` for every interior index with a guarded integer `divmod`. There are `D-1` such checks. Their integer-operation charges alone consume all `D-1` gross savings:

| Added or removed work relative to original | Charge change |
| --- | ---: |
| Endpoint-aware affine arithmetic | -(D-1) |
| One guarded divisibility operation per interior | +(D-1) |
| Additional remainder/domain/type/owner checks | Nonnegative additional cost |
| Audit storage, copies, lookup, publication or fallback work, if introduced | Nonnegative additional cost |
| **Maximum net saving even before those additional costs** | **0** |

This upper-bound rejection does not require inventing a complete runtime implementation or assigning zero cost to unimplemented checks. An authenticated factory-origin design could avoid this audit, but it has not been specified or costed here. Such a design would need an exact tuple origin and lifetime, current operand limit, method and owner authority, malformed-cache fallback and all screening costs, without extending the 256-entry cache or moving numerical values into unbounded side storage.

### Existing centered observers do not supply the missing receipt

The captured target follows `_orientation`'s nonadvance branch in `reach_reference_center.py`, which calls `guard.original(body.direct, clock)`. `_Guard.original` installs a non-null `observed` closure in `_recording_after_tick` throughout that direct call. The degree-14 coefficient failure occurs inside it. A screen requiring that hook to be `None` is therefore ineligible at the target, regardless of the separate product hook.

The retained capture's outer work-observer `None` and observer-restoration checks are boundary observations; they do not show that the arithmetic hook is absent inside the call. `_Guard.current` retains and checks generic callback identities while allowing domain invalidation; it is not a proof that callbacks cannot mutate the domain. C035's `_product_native` admits a different centered-product route. Its `_PRODUCT_ARITHMETIC_METHODS` does not bind `_series_integer`, `_series_factorials`, `_series_coefficients`, `_series_dyadic`, or factorial payload provenance. Neither mechanism can be silently reused as the missing series receipt.

## Structural opportunity and limits of the census

The twelve resident coefficient keys have degrees `{2,7,8,13,16,17}` and exponents `{50,52,53,127,128,129}`. Degree 16 appears at four exponents, degree 13 at three, and degree 17 at two. This is structural evidence for considering exponent-independent factorial work, not a count of cache hits or permission to infer internal publication chronology.

C047's source-bound lifetime proof establishes five completed new constructions within its captured interval. Their endpoint-aware affine arithmetic ceilings are:

| Degree | Gross arithmetic saving per complete miss |
| ---: | ---: |
| 7 | 6 |
| 8 | 7 |
| 13 | 12 |
| 17 | 16 |
| 16 | 15 |
| **Five completed constructions** | **56** |

At the failed degree-14 invocation, the original completed 29 construction operations before its index-7 division refused. The affine schedule has 25 operations before its corresponding division: five setup operations, the initial shift, six three-operation interiors, and the index-7 numerator add. Thus only four gross arithmetic operations precede that corresponding failure point. The full helper's thirteen-operation ceiling concerns an unexecuted completion. Neither number is a measured request saving or proof that the failed tail would finish.

The seven keys resident at key-0 entry belong to prior setup. Their presence is not an exact construction-event count. The failed `(129,14)` key is new within the proved interval and supplies no existing full-key hit. A new degree-only cache has cold-start, extra lookup/publication, bounded occupancy, retained-value and eligibility costs; its genuine degree-14 miss cannot be priced as a warm hit without a new lifetime proof.

Degree 1 offers zero arithmetic saving and degree 2 offers only one. Placing new admission after the existing full-key lookup can preserve the original one-tick hit path, but every actual miss-side screen and ineligible fallback must be charged. A threshold or native test is not free merely because it rejects the optimized route. Any future positive bound must include those low-degree and fallback cases, startup and all affected requests.

## Scope of conclusion

The endpoint checkpoint-preserving variant and the per-interior divisibility-audited affine variant have no positive net operation bound. Unguarded endpoint or affine replacement does not preserve the generic authority/callback contract. A future source-origin receipt remains a separate design question with a potentially positive arithmetic allowance, not a selected implementation.

Original28 remains 24/28. This review establishes no repaired export, timing result, regression pass, candidate numerical replay, release acceptance or main integration.
