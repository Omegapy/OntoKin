# Independent binary32 clock cells on an integer grid

This derives an optional implementation of `clock_cell_contains` in
[`reach_conformance.py`](../../ontokin/reach_conformance.py). It checks the
existing exact-rational, round-to-nearest/ties-to-even clock contract in
[GLB/0.6 quantization](../language-design/planar-reach-v0.1/quantization.md).
It changes no source clock, stored byte, rounding cell, acceptance limit or
writer algorithm. The independent checker retains its original rational
midpoint calculation as the fallback. This derivation is not an executed
recording result or a release acceptance claim.

## Exact binary32 grid

For a nonnegative finite binary32 bit pattern `b`, write `E = b >> 23` and
`T = b & 0x7fffff`. Its exact value is `N(b) * 2^-149`, where

```
N(b) = T                              if E = 0,
N(b) = (2^23 + T) * 2^(E-1)           if E > 0.
```

The first expression is the subnormal definition. The second follows by
rewriting `(1 + T/2^23) * 2^(E-127)` at the same fixed scale. Both describe
the same values as exact native binary32 decoding, including the transition
from subnormals to normals and all later exponent transitions.

For nonzero `b`, the lower adjacent-cell midpoint is

```
L / 2^150,   L = N(b-1) + N(b).
```

For zero, retain the original nonnegative domain boundary `L = 0`. The
upper midpoint is `U / 2^150`, with `U = N(b) + N(b+1)`. At the maximum
finite pattern `0x7f7fffff`, the original conceptual upper neighbor is
`2^128`; its grid integer is `2^277`. This gives exactly the original
finite/overflow midpoint, without interpreting an infinity as a rational.

For an admitted source clock `n/d`, with `n >= 0` and `d > 0`, positivity
of the common denominator gives the exact comparisons

```
n/d ? L/2^150    iff    (n << 150) ? d*L,
n/d ? U/2^150    iff    (n << 150) ? d*U.
```

The source numerator shift is shared between the two comparisons. No source
clock or midpoint is rounded through binary64. Equality at either midpoint
belongs to the cell exactly when the low bit of `b` is even. Zero therefore
keeps its upper half-subnormal tie, odd subnormals lose either tie to their
even neighbor, and the odd maximum finite pattern excludes its overflow tie.
Negative source clocks and invalid bit patterns retain their original
rejection before the optional calculation.

## Bounded allocation and original fallback

The optional calculation runs only at the original full 32,768-bit operand
limit and with source numerator and denominator widths at most 1,024 bits.
All bit patterns have already passed the original exact type and range
checks. Their decoded grid integers and midpoint sums need at most 278 bits.
The source shift has at most 1,174 actual bits; its preflight conservatively
guards 1,175. Each denominator/midpoint product needs at most 1,302 bits.
The implementation guards all these prospective widths before allocation.
The restricted calculation therefore remains below 1,303 bits and cannot
enlarge any request's operand domain.

The original rational calculation also fits the full cap throughout this
restricted domain. Each decoded finite neighbor has numerator width at most
129 and denominator width at most 150, including the conceptual overflow
neighbor. Conservative unreduced midpoint-addition preflights need at most
300 bits. Division by two adds at most two bits to those estimates, and the
final comparisons against a 1,024-bit source remain below 1,400 bits. Thus
the shortcut does not accept a small operand whose original full-domain
midpoint arithmetic would have failed.

Larger source operands and any initially narrower live cap execute the
literal original rational path. The full cap is checked again immediately
after each charged arithmetic callback. If it changed, the optional result
is discarded before the next allocation and the original path runs in the
current domain. An actual error from that original arithmetic is never
caught or retried; a later callback cannot widen the domain and replace its
first failure. This preserves callback-owned exception identity as well as
the original numeric failure when the narrowed cap is insufficient.

## Accounting and cancellation

Every invocation keeps the original `independent_clock_cell` admission and
`independent_bound_decode` source admission. The fixed binary32 bitfield
decoding replaces the original uncharged native unpack/Fraction neighbor
conversion; it uses only a statically bounded pattern after admission.

Every actually executed midpoint integer addition retains an
`independent_exact_add` charge. Each exact comparison retains its
`independent_exact_compare` charge and includes its bounded cross products,
as in the original rational comparator. The second comparison reuses the
already computed source shift. The two midpoint rational divisions and
their integer-divisor decodes are no longer performed and are not charged.
For zero, the original lower-midpoint addition and division were already
absent.

| Cell | Original operations | Integer-grid operations |
| --- | ---: | ---: |
| Nonzero finite pattern | 10 | 6 |
| Zero | 7 | 5 |

These are counts of the specified helper operations, not a measured claim
about a full recording. Every remaining charge continues to use the caller's
shared operation budget and cancellation callback. A callback exception
propagates as the same exception object. No work counter is reset, no charge
is discounted, and no cache, source state or certificate record is created
or mutated by the optional calculation.

## Focused verification obligations

The focused module
[`test_reach_independent_clock_cells.py`](../../tests/test_reach_independent_clock_cells.py)
compares exact midpoint membership with the retained rational calculation
around every exponent transition. It additionally covers subnormal and
overflow ties, source rational distinctions below binary64 resolution,
invalid inputs, the 1,024-bit eligibility boundary, narrower initial and
callback-changed caps, exact cancellation identity, unchanged cache entries,
the first original failure during a narrow-then-widen callback sequence, and
the unchanged shared operation limit. Actual execution and recording evidence
must identify the tested source revision separately.
