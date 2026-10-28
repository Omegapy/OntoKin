# Exact one-cell interval products

The production arctangent still evaluates the fixed `floor((p+5)/2)` terms
and adds the original remainder from the adopted numerical method. This
optimization changes neither that schedule nor any interval endpoint.

Let `S=2^p`. An outward interval is represented by integer endpoints. For
`A=[0,1]` and `0 <= B.lo <= B.hi <= S`, with `B.hi > 0`, the four integer
products have minimum zero and maximum `B.hi`. Division by `S` gives lower
endpoint zero and upper endpoint one. The complete outward product is exactly
`A`. For `A=[-1,0]`, the minimum is `-B.hi` and the maximum zero; its outward
product is again exactly `A`. Commutativity supplies the reversed operands.
These are identities of the original directed interval operation, including
its rounding. They do not claim the enclosed mathematical product is unchanged.

The branch requires native ordered interval cells with native integer endpoints.
It retains the original interval-operation charge, all four original operand
guards and the complete prospective product-width guard before and after that
charge's callback. It omits the two extremal integer products and two directed
quotients because their exact answer has already been established by the
endpoint inequalities. As in the original monotone path, endpoint pairs are
captured before callbacks. The returned cell is fresh, so changing a private
input object cannot alter those captured numeric operands. If a callback
changes the scale, the original four constituents run on those same pairs,
with complete guards after their callbacks. Cancellation and resource
exceptions propagate normally. No cache or retained table is added.

The focused checks compare all five precisions, signs, reversed operands and
boundary/fallback shapes against independent rational four-corner calculations.
They check the original operand guards, callback mutations, cancellation,
foreign cells, and complete arctangent enclosures and recurrence counts. Actual
source-recording results must be identified separately; this derivation is not
a recording or release pass.
