# Exact point and integer-divisor cells

This implementation note covers only `DyadicContext.point` and `DyadicContext.div`
in [the production arithmetic module](../../ontokin/reach_numeric.py). It changes
the integer calculations used to obtain an existing directed cell. The precision
schedule, number of series terms, remainder bounds, rounding criteria, residual
limit, maximum work, maximum operand width and request cache remain unchanged.

The preceding kernels are retained as differential test helpers in
[the dedicated tests](../../tests/test_reach_dyadic_identities.py). This note is
a derivation and validation plan; executed results must identify their own source
revision and evidence. It does not establish release acceptance.

## Exact point conversion

Let the context precision be `p` and its fixed-point scale be `S = 2**p`. The
preceding point conversion for a reduced fraction `n/d` returns

```
lo = floor((n << p) / d)
hi = ceil((n << p) / d)
```

When `d = 2**k` and `0 <= k <= p`, both endpoints equal the integer
`n << (p-k)`. This includes zero and negative numerators. A left shift of a
negative Python integer is exact multiplication by the positive power of two;
no rounding or sign convention changes. The new kernel therefore performs one
shift instead of one shift and two quotients. It retains one logical interval
operation and charges one arithmetic constituent instead of three.

Admission is restricted to native `int`, `float` and `Fraction` inputs, a native
context and one of the five adopted native integer precisions. The original
`Fraction` conversion still occurs first. Other accepted input types, denominators
that are not powers of two, and dyadics finer than the current grid keep the
preceding calculation and all three constituent charges.

The original guard remains `n.bit_length() + p + 1`, even when the smaller final
shift would fit a narrower domain. Both the complete fraction and that original
prospective width must pass before denominator classification and again after
the retained constituent callbacks.

## Exact integer interval divisors

The preceding canonical division selects the same two extremal corners as before.
For one corner numerator `x`, an exact point divisor `b = m*S`, and nonzero integer
`m`, cancellation of the common positive factor `S` gives

```
floor((x*S) / (m*S)) = floor(x/m)
ceil((x*S) / (m*S))  = -floor(-x/m)
```

This is true for either sign of `m`. The existing sign-based corner selection
therefore remains valid without modification. Recovering `m` requires one exact
right shift. The two directed quotients remain. Three arithmetic constituents
replace the preceding two products and two quotients; one logical interval
operation remains.

The identity is admitted only for canonical native ordered interval cells, an
exact point denominator, native context precision/scale, the adopted `2**p` scale,
and a denominator exactly divisible by that scale. Every original operand and
the full prospective width `max(abs(a.lo).bit_length(), abs(a.hi).bit_length()) +
p + 1` remain guarded before classification and after the retained callbacks.
The denominator is known nonzero from the preceding canonical path.

Nonintegral divisors, denominator intervals, malformed or foreign cells and the
ordinary zero-containing-denominator failure keep their preceding calculations,
charge counts and ordering. Existing zero-numerator and positive-unit-divisor
identities remain in their existing earlier positions.

## One-cell intervals adjacent to zero

Within the same admitted exact-integer divisor domain, positive `m` gives

```
[0, 1] / m  -> [floor(0/m), ceil(1/m)]  = [0, 1]
[-1, 0] / m -> [floor(-1/m), ceil(0/m)] = [-1, 0]
```

These are integer fixed-point cells, not real endpoints of magnitude one. For
every finite positive integer `m`, `0 < 1/m <= 1`; its upper directed integer is
one and the lower directed integer of `-1/m` is minus one. No quotient or
denominator shift is necessary after admission. The interval checkpoint and
complete original guards remain; no arithmetic constituent is charged because
none is performed.

A fresh `Interval` is built from the endpoints captured before the interval
callback. This matches the preceding corner kernel, which selects its immutable
integer pairs before that callback. Returning the original object could expose
a private callback mutation of its fields and would not preserve that behavior.
Negative integer divisors retain the general three-constituent reduction.

## Live domains and callback ordering

These optional identities require the original maximum native operand domain.
An initially narrowed or foreign domain takes the preceding path. Every logical
interval checkpoint remains before the complete original operand and width
guards. No new cache entry or cross-request state is introduced.

After the interval callback and guards, admission is checked against the current
context, work owner, and operand cap. The reduced arithmetic constituents retain
their own callbacks. Before returning a reduced result, the kernel checks that
the context precision, relevant scale, domain and work owner still match. Point
conversion also checks the native fraction numerator and denominator again.

If a retained callback changes this optional proof, the kernel charges the
remaining preceding constituents before taking the preceding arithmetic path.
The final complete operand and original-width guards therefore run at the same
point in that ordinary path. Exceptions from retained callbacks propagate by
identity. Work limits still count each actually requested arithmetic operation.

An `AdmissionWork` constituent batch increments its admission exact counter only
after the whole batch succeeds. When callbacks require restoring the ordinary
batch, both parts use the parent charge method bound before the first
constituent. The admission exact counter is incremented once after that complete
batch succeeds. Thus cancellation during a restored constituent or replacement
of the admission parent cannot turn a partial charge into a completed admission
batch or redirect the remainder to another owner. Parent operation counters
continue to count each individually completed callback/charge.

## Focused verification

The dedicated tests compare preceding and new directed cells across all five
precisions, positive and negative inputs, representable and finer dyadics,
positive and negative integer divisors, zero-adjacent cells, and ordinary
fallback domains. They compare complete error details and counts for narrowed
caps, the original wider prospective checks, retained cancellation callbacks,
callback changes to context/value/cell inputs, interrupted restored batches,
and admission-parent replacement.

Integration checks compare actual P16 and P23 admissions, including target bits,
coordinate enclosures, precision and residual bounds. Only actually performed
constituent work may differ. A complete short P16 GLB is also compared byte for
byte against the preceding point/division kernels. The complete original-settings
recordings remain a separate measured gate after the focused cohort.
