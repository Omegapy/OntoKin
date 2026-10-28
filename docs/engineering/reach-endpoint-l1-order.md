# Exact ordering of independent endpoint distances

This implements two bounded arithmetic identities inside the independent
supplied-byte checker. The [endpoint proof](reach-independent-endpoint-bounds.md)
and [current operand admission](reach-endpoint-operand-reuse.md) remain in force.
Neither the producer's bounds nor its expected poses supply the result. Source
motion, actual stored bytes, certificate claims, operation and operand maxima,
and the existing 256-entry request cache retain their contracts. This note is a
derivation; execution results and release acceptance require separate evidence.

## Farthest endpoint outside an admitted interval

For one actual exact component `x` and an independently admitted ordered source
cell `[lo, hi]`, the existing sufficient endpoint bound contains

```
max(abs(x - lo), abs(x - hi)).
```

Let the two existing exact subtractions be `a = x - lo` and `b = x - hi`.
Since `lo <= hi`, they satisfy `a >= b`.

- If `b >= 0`, then `a >= b >= 0`, so the maximum is `abs(a)`.
- Otherwise, if `a <= 0`, then `b <= a <= 0`, so the maximum is `abs(b)`.
- If neither condition holds, the actual component lies strictly inside the
  interval and the original guarded comparison of the absolute values runs.

For canonical native fractions, each sign follows directly from its integer
numerator. The outside-cell cases therefore need no rational comparison or
cross-product multiplication. Both original subtractions still execute and
charge their real arithmetic, including all prospective allocation guards.
The first absolute value is still computed before the second subtraction's
callback. Point cells retain their preceding exact-zero and one-subtraction
paths. The resulting rational bound is identical, including nonzero source
interval widths and values on either endpoint.

## Keep the source-order proof current

This identity is optional at the existing full native 32,768-bit operand limit
and the existing 256-bit admitted input range. After the complete original
scalar/source admission, a local receipt records each component's six native
integer numerator and denominator values. All three denominators must be
positive. There are at most four receipts, and they are discarded on return;
no new history or cache entry is retained.

The receipt and work owner are checked before the first subtraction and after
each subtraction callback. If the actual fraction, source cell, current work
owner, native cap type or full cap changes, that component permanently takes
the original absolute-value comparison. A later callback restoring the earlier
cap does not restore the proof. Receipts for all components are captured before
any component calculation, so a callback for an earlier component cannot
silently replace a later component's source-order admission.

The current operands still enter each subtraction at their original evaluation
time. In particular, the second source endpoint is read only after the first
subtraction returns. This preserves the preceding behavior even for deliberate
private mutation of frozen cells or fractions during a callback. Foreign cell
subclasses, foreign or nonpositive fraction denominators, wider inputs and narrower domains
do not use the identity. Malformed, reversed and nonfinite source or actual
values still encounter the original admission and failure order.

The selected outside-cell result retains both original comparison input-width
and prospective cross-product-width guards. No comparison charge is issued
because no rational cross product or ordering comparison occurs. All remaining
arithmetic and domain checkpoints still poll cancellation and propagate the
original callback exception. A source, cap or work-owner change detected at
those checkpoints uses the original charged comparison and its own guards.

## Exact constant two

The optional quaternion endpoint proof multiplies the independently computed
L1 distance by two. At the full native cap, a preconstructed native `Fraction(2)`
is the identical operand previously obtained by decoding the literal integer.
Its exact native numerator/denominator metadata must still be `2/1`; a detached
`Fraction` copy then retains those two immutable native integers without any
decoding or reduction. The multiplication's callback cannot mutate that local
coefficient through an alias to the shared module constant. An already altered
or foreign constant uses the original integer decoder instead.
The real multiplication, its callback, its input and prospective result guards,
and its exact result remain unchanged. An already narrowed or foreign cap uses
the original integer operand and decoder. No certificate field or source value
is replaced by this constant.

The enclosing orientation helper preserves its source/actual-value admission,
antipodal alignment, sufficient claim checks, normalized fallback and current
`before_error` position callback. Its existing bounded orientation cache already
shares equal completed orientation operands across carriers in the same key;
these identities add no second sharing mechanism.

## Verification obligations

`tests/test_reach_endpoint_l1_order.py` compares the complete preceding L1
kernel and complete key results, with exact operation differences. It covers
inside, outside, signed-zero and boundary values; all original prospective
width guards; narrowed, restored and foreign cap domains; current work-owner
changes; mutation of source and actual fractions at both subtraction callbacks;
later-component mutation; malformed or over-wide input; shared constant mutation
before and during multiplication; callback cancellation;
cold/warm position callback order; and existing same-key orientation reuse.
The sufficient endpoint, endpoint operand, sparse endpoint and hostile claim
cohorts remain relevant. Original full P09/L03 recordings and the complete
integrated recording suite are required before reporting recording progress.
