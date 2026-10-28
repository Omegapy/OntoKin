# Fixed exact materialization of deferred phase locations

## Scope and observed cost

This development change is limited to the final materialization of the
phase-local `_PhaseLocation` representation in `ontokin/reach_phase.py`.
It changes no source traversal, current-state projection, angular witness,
release transfer, recorded key, certificate formula, tolerance, work limit or
cache capacity. The complete eighteen-field `PhaseBound` remains the result.

The neutral original-P23 planning observation in
`p23-planning-observer-001` used implementation
`0cd8400e2b31b14203a45497f934f90b8a3a28fe` and reproduced the complete unobserved
work record, diagnostic, failed status and 100,001 request operations from the
tested runtime at `52548f3adfc01f4ea1424f2262a7976308e4f4e9`. The only intervening
input change was the earlier claimed-seed execution documentation. Both input
manifests were stable; selected-function self costs reconciled to all request
and reach work. The observer changes no callbacks or source behavior.

That observation measured 46,906 operations for `reach_prefix_plan`:

| Component | Original measured operations |
| --- | ---: |
| Complete phase bound for `[0, 2]` | 5,814 |
| Complete phase bound for `[2, 3]` | 4,750 |
| Final location materialization within each phase | 1,943 |
| Final location materialization across both phases | 3,886 |
| All seven maximal reach-map forecasts | 1,120 |

Each phase materialized 155 actual deferred locations. The additional calls
on already ordinary bounds did no numerical work. The six repeated maximal
reach-map forecasts account for only 960 operations before any new receipt
cost; that separate optimization was deferred.

The existing generic arithmetic discovers zero/one identities for variable
length lists. This is useful for general recurrences. Final materialization has
a fixed seven-operation expression. Under the existing small spatial domain,
executing those seven exact operations directly avoids the additional
variadic identity-discovery work. The entry charge remains, predicting eight
operations per eligible location and 703 fewer operations per original P23
phase. These are predictions until the new committed candidate is executed.

## Identical exact equation

The deferred location invariant is established by
[the existing derivation](reach-deferred-phase-locations.md). Let the relative
bound have spatial extent `M`, path offset `L`, position allowance `P` and
rotation allowance `R`; let the deferred additions be `e` and `l`. Its complete
materialized fields are exactly:

```text
extent         = M + e
path_offset    = L + l
rotation       = R - EXPOSED_ROTATION_ERROR
extent_error   = e * 2^-53
offset_error   = l * rotation
position_error = (P + extent_error) + offset_error
```

All seven binary operations continue to call the unchanged `exact()` helper.
They retain its operation charges, callback, operand guards, prospective
numerator/denominator width checks and exact `Fraction` result guards. There is
no approximate arithmetic or changed allowance. The final `replace()` retains
every other original field, including ideal and actual derivatives, source
counts and inherited errors. The original complete operand guard before the
calculation and complete result guard after it remain in place.

The optional path does not eliminate an operation by declaring it free.
It replaces the generic variadic zero/one discovery with a fixed expression
whose operations are known in advance. The ordinary generic expression remains
verbatim as the fallback, including its order of exact error additions.

## Native and finite-width admission

The optional expression requires the native `PhaseArithmetic` instance and
its original `add`, `sub`, `mul` and `exact` dispatch, the same native
`ReachExecutionWork` owner, and the full 32,768-bit operand cap. Instance-level
method replacements, subclasses, changed class dispatch, changed `exact`
dispatch and narrower domains retain the generic expression.

The four relative spatial fields and both deferred terms must be exact native
`Fraction` values with exact integer backing components and positive
denominators, within the existing 2,048-bit small-location domain. A private
boolean replacement cannot compare equal to an admitted integer receipt. For a
constituent width `m <= 2048`, the two extent/offset sums need at most `2m+1`
prospective numerator bits. `EXPOSED_ROTATION_ERROR = 2^-50` has a 51-bit
denominator, and `2^-53` has a 54-bit denominator. Even without cancellation,
the final error sum needs at most `4m+107 = 8299` numerator bits and
`4m+105 = 8297` denominator bits. These bounds are below the unchanged full
operand cap. Each operation still checks its actual prospective widths.

Zero operands are allowed within this full domain; explicitly performing their
addition or product cannot introduce a width rejection there. Narrow domains
keep the generic identity elisions because, for example, an already admitted
wide fraction plus exact zero may fit even when the unreduced addition's
prospective width does not. The optional path does not narrow that original
behavior.

## Callback, dispatch and input changes

The optional calculation checks its live cap and native dispatch immediately
after every exact operation, before another optional operation or publication.
A changed cap or dispatch immediately abandons that attempt. The caller runs
the generic expression afresh under the current context. It does not reenter
the optional calculation, so a later callback restoring the full cap or native
method cannot revive a partial optional result.

Private mutation can alter even native `Fraction` objects and frozen bounds.
Six immutable numerator/denominator pairs bind the optional attempt to its
actual spatial inputs. A changed pair, type or spatial width also abandons
the attempt before another optional operation. This is a constant-size local
admission receipt, discarded on return; it is not a numerical cache and stores
no derived coefficient, pose, history or sampled result.

If a changed cap causes an exact prospective-width error before the post-call
check, the attempt can fall back only for that `numeric_operand_bits` error and
only after detecting that its original context or input receipt has changed.
Other arithmetic/resource errors remain errors. An exception identical to the
original work callback's recorded exception always propagates unchanged,
including a callback exception that itself has the numerical-limit type.

Moving the arithmetic object to a different work owner during an admitted
attempt raises the existing `reach_domain` admission error. No partial work
may continue on a fresh request budget. All intermediate values remain local;
there is no cache publication or retained state to roll back.

## Review and verification plan

`tests/test_reach_phase_fixed_materialization.py` compares the complete
original P23 phase maps and angular proof records with the retained generic
formula for both intervals. It also covers exact zeros, signs, nondyadic values,
the 2,048-bit boundary, wider/native-type fallbacks, an admitted narrow-domain
zero identity, changes at each of the seven arithmetic callbacks, restored
dispatch, mutable input pairs, changed work ownership, cancellation identity,
the shared operation budget and preservation of existing numeric cache entries.

The source and focused tests are prepared for independent review. No execution
of this candidate is claimed here. After the focused cohort passes, the
existing phase-location, phase-node, mount, coaxial, angular-proof and planning
cohorts and the unchanged full original P23 recording remain required. The
release still requires all 28 original recordings and its remaining mandatory
acceptance gates; this local optimization establishes none of those gates by
itself.
