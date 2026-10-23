# Exact source products on a shared Cartesian axis

This optimization extends the existing scalar/Z integer Hamilton product to
scalar/X and scalar/Y source rotations. It changes no coordinate law, source
or recording bound, projection, normalization allowance, recording classifier,
sampling clock or acceptance threshold. The public request limit remains
100,000 operations, the operand maximum 32,768 bits, and the shared numerical
cache maximum 256 entries. Verification results belong to their identified
execution reports; this derivation alone is not a release result.

## Identical algebra and projection

For one Cartesian quaternion basis unit `e`, `e*e = -1`. Therefore the full
Hamilton product of `a = aw + ai*e` and `b = bw + bi*e` is

```
real = aw*bw - ai*bi
imag = aw*bi + ai*bw
```

Every component on the other two axes is exactly zero. These equations have
the same signs for X, Y and Z; the axis selects only the position of `imag` in
the result tuple. This is an exact support identity, not a small-angle or
near-zero approximation. Mixed-axis products retain the complete original
Hamilton computation.

The existing integer routine admits only exact Fraction components, each on
the 96-bit dyadic grid and with magnitude at most one. It lifts each operand's
two nonzero components to that operand's common dyadic denominator. If those
denominators are `2**ea` and `2**eb`, the integer Hamilton numerator has the
common denominator `2**(ea+eb)`. The ordinary power-of-two projective rescale
cancels this common denominator. The existing integer scale, ties-to-even
quotient, canonical sign and final 96-bit grid are consequently unchanged.
Only the imaginary component's Cartesian index differs.

All resulting Fraction components, their exact signs and the resulting
binary64 projection equal the complete original product. The output error is
still exactly `a.error_rad + b.error_rad + PRODUCT_ERROR`. Existing frozen
public projections are not transferred through a product. Error allowances
remain absent from the pure component cache key and are freshly compared or
recomputed through the existing allowance path.

## Domain, callbacks and storage

Only the full operand domain selects the new X/Y path. Under its admitted
96-bit dyadic input bounds, all generic zero products and sums that are omitted
would fit that domain: no omitted intermediate can create a new resource
failure. Larger magnitudes, non-grid denominators, foreign scalar types,
uncertain zeros, mixed axes and narrowed caps retain the complete generic
calculation. The pre-existing Z path and scalar-identity paths remain intact.

The X/Y branch copies the exact component tuples already read by the ordinary
Hamilton calculation. A callback that replaces an input RotationValue cannot
make the integer helper read different operands from that ordinary branch.
The new tuple has no extra numerical result or cached projection. Integer
arithmetic keeps its existing per-operation prospective-width guards and
cancellation checkpoints; a cap change leaves the integer path before further
integer arithmetic or publication. The outer original-operand restart and
bounded cache insertion remain unchanged. An exception raised by a callback,
including one with the internal fallback exception type, propagates by identity.

The existing recording rotation cursor reaches this source product for
nonplanar ordinary paths such as P11's Y-axis head. It still seeds and reseeds
through the original source kernel, retains only the latest bounded cursor,
and uses the existing complete phase/source admission. No path becomes eligible
for the scalar/Z native sampler as a result of this change.

## Focused checks

The dedicated source-product cohort compares exact components, error bounds and
binary64 projections against the unchanged generic X/Y equations while keeping
the original Z optimization enabled. It covers signed axes, sign crossings,
ties to even, scalar and invalid zero operands, foreign/nonplanar/non-grid
fallbacks, cold and warm narrowed caps, allowance changes, eviction, interrupted
arithmetic and publication, replaced private operands, every value in complete
source cursor sequences and an actual independently validated P11 prefix GLB.
The original P11 recording must then be executed at its original settings and
unchanged 100,000-operation limit; a faster prefix is not a full recording pass.
