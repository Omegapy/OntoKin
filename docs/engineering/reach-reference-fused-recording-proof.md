# Independent recording interval rotation with final outward grids

This note derives `_PoseArithmetic._recording_rotate_sincos` in
`ontokin/reach_reference.py`. The change is confined to an explicit independent
recording cursor. Source observations, direct trigonometric seeds, phase and
context isolation, rewinds, and the 64-step reseed rule retain their existing
calculations. Recording tolerances and all public budgets are unchanged.

## Exact enclosure

Let `S`, `C` enclose the previous sine and cosine, and let `s`, `c` enclose
the independently calculated increment. The exact angle-addition identities
give

```
new_sine   = S*c + C*s
new_cosine = C*c - S*s.
```

For two closed real intervals the extrema of a product occur at endpoint
pairs. Sign monotonicity identifies two endpoint pairs when at least one
operand has a fixed sign. When both straddle zero, all four corner products
are retained. Point-by-point products are evaluated once. All selected
products are exact rational operations using the independent reference's
existing charged arithmetic.

The lower/upper bounds of a sum are the sums of its lower/upper bounds. A
difference uses the first lower minus the second upper, and the first upper
minus the second lower. These exact endpoints are rounded outward to the
128-bit grid once for each final output. No intermediate product needs its
own grid: the exact product interval is contained in that rounded product
interval. Interval addition, subtraction, and outward rounding are monotone
with respect to containment. Consequently the new result contains every
mathematical update and is contained in the original result evaluated on
the same inputs.

The omitted intermediate rounding introduces no new approximation, slack,
producer error allowance, native trigonometry, or independent precision
change. Repeated updates remain enclosing by induction. Every actual stored
endpoint is still compared against the independent source enclosure, and
every supplied certificate still satisfies the same complete inequalities.

## Complete finite domain

The path admits only immutable reference cells with exact `Fraction`
endpoints on the existing 128-bit dyadic lattice, in the original 32,768-bit
live operand domain. Each reduced numerator must have at most 131 bits and
each denominator at most 129 bits. These width checks precede even the
denominator-minus-one lattice test, as well as ordering or product selection.
Reversed cells, other types or precisions, off-grid
values, larger operands, and narrower domains retain the original operation
sequence. Exact zero/unit inputs also retain its cheaper existing shortcuts.

For an admitted pair, exact product numerators have at most 262 bits and
denominators at most 258. Product comparison cross-products need at most
520 bits. A prospective addition or subtraction of two unrounded product
endpoints needs at most 521 numerator bits and 516 denominator bits. Its
final grid shift needs at most 649 bits. The original path's intermediate
grids and subsequent endpoint additions have smaller extents. Thus a
conservative 1,024-bit domain contains every performed and omitted original
preflight, well inside the unchanged live limit. No resource refusal can be
bypassed merely by removing an intermediate grid.

## Callbacks, fallback and cursor ownership

The fused calculation first polls the existing callback and guards all
actual endpoints. Every performed product, sum and final grid retains its
ordinary operation charge, callback, and prospective allocation guard. The
live cap is checked after each operation before further endpoint selection
or return. A changed domain re-enters the complete original operation
sequence. Only the added calculation's own resource error after a real cap
change can trigger this fallback; the caller's exact exception propagates.

The original interval fallback is outside that handler. The enclosing
cursor's retry is also limited to its extra exact delta construction. An
original trigonometric or interval fallback failure therefore retains its
identity; a subsequent callback cannot broaden the cap and turn the first
refusal into success. The default helper stores no cache or cursor state.
The optional [shared completed-update proof](reach-reference-shared-recording-proof.md)
uses the existing bounded arithmetic cache for identical input cells, with
separate per-path cursors. Only a fully completed update reaches the existing
cursor publication, with its live-domain checks and bounded cache.
Cancellation cannot advance the last completed cursor.

## Verification scope

The focused tests compare all product-sign domains against separately
evaluated exact corner extrema, verify containment in the previous outward
calculation, and exercise point/identity behavior, domain fallback, large
operand failure order, cancellation identity, and full-cursor fallback
failure propagation. Actual source-built GLBs and complete supplied-byte
validation are compared with the original interval update under the same
100,000-operation allowance. Existing finer-reference cursor, phase,
rewind, reseed and operand-domain cohorts remain applicable. Execution
reports record observed results separately; this derivation makes no claim
about an unexecuted release gate.
