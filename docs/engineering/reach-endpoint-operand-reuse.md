# Current independent endpoint operands

This note describes a work-avoidance change inside the independent supplied-byte
checker, `reach_conformance.py`. It changes neither the source reference nor the
producer, certificate quantities, complete inequalities, tolerances, operation
limit, operand limit or numeric-cache capacity. The existing
[sufficient endpoint proof](reach-independent-endpoint-bounds.md) remains the
mathematical argument. Execution evidence and acceptance are separate records.

## One exact coordinate conversion

The existing endpoint check computes the current position error inside the
orientation check's `before_error` callback. It then computes the stored
position's L1 magnitude after the orientation comparison returns. Both
calculations use the same three actual stored coordinates. Converting a fixed
native finite integer or binary64 value to its exact rational is a pure
operation; a second conversion cannot change that rational.

A short-lived `_PositionOperands` view accompanies only these two helpers for
one endpoint. Its immutable native-coordinate tuple and three optional exact
ratios retain completed conversions. Each ratio is recorded only after the
original decoder, including its cancellation callback and width guard, returns
successfully. The view delegates arithmetic, source-interval admission,
comparison and numeric-cache operations to the original reader.

A ratio can be reused only for an equal native value of the same concrete type,
with the same work owner and the unchanged full 32,768-bit domain. The retained exact numerator and
denominator must each fit the existing 256-bit sufficient-proof range. Every
reused ratio is guarded again against the live domain. Foreign values, changed
values, wider ratios and narrowed domains perform the ordinary decoder.
Reusing a ratio for an equal coordinate at another component position is safe:
conversion has no component-order dependence, while the actual ordered sum
and every source comparison are still calculated normally.

Both receiving helpers retain their existing initial cancellation checkpoint
and complete current stored-value admission. Their real additions, subtractions
and comparisons retain the original scalar charges and prospective allocation
guards. In particular, a narrower cap at the later magnitude checkpoint takes
the original decoder and sum preflights. No earlier position error, source
enclosure or endpoint result is inherited from the conversion tuple.

The view is not placed in the preceding-endpoint map, source state, a request
cache or an exported result. It is discarded with the current endpoint's
comparison. The original position-callback and later magnitude order is
unchanged, including the existing independently normalized fallback hooks.

## Reusing exact source-cell representation

The orientation helper already converts and admits all four source enclosures
as frozen `_Cell` records before cache lookup. Its sign-selection helper guards
the complete current cells after its own callback. The subsequent optional L1
helper can therefore use those same exact cell records instead of converting
and allocating another identical tuple.

This does not retain their admission across an unchecked callback. The L1
helper keeps its original checkpoint and any required native scalar decoders.
After all those callbacks, it rechecks every current numerator and denominator,
both comparison cross-product widths, and the ordered low/high relation before
performing a source comparison. Noncanonical or foreign cells keep the original
general interval decoder. Reversed, malformed and over-wide current cells
cannot borrow the earlier admission.

The resulting exact L1 bound is identical, including nonzero enclosure widths.
An insufficient bound still takes the original norm proof. Antipodal alignment,
zero and near-zero normalization rejection, source-cell validation and the
current position callback retain their existing responsibilities.

## One sufficient inequality for a small native claim

The existing quaternion shortcut requires both `E <= 1/2` and `E <= claim`,
where `E` is independently computed as twice the current endpoint L1 distance.
For a finite native binary64 claim in `[0, 1/2]`, or the exact native integer
zero, the second inequality implies the first. The checker can therefore omit
that redundant first rational comparison.

The range classification performs no large rational arithmetic. The actual
claim is still admitted by the original scalar decoder and compared with `E`
using the original guarded exact comparison. The full operand domain is checked
before and after that comparison. Exact `Fraction` claims, larger integers or
floats, negative values, nonfinite values and foreign objects retain the
original two-comparison order and rejection path. A tighter claim can still
require the independently normalized fallback; the claim remains a threshold
and never supplies an expected source value or a numerical error bound.

## Verification obligations

`tests/test_reach_endpoint_operands.py` compares complete endpoint results with
the repeated-conversion path, verifies actual removed decodes and unchanged
cache limits, checks changed stored/source values and malformed cells, and
exercises live cap narrowing, original cancellation identity, exact fallback
ordering and native-versus-foreign claim domains. The existing sufficient-bound,
orientation-claim, position-receipt, sparse-endpoint and independent-reader
cohorts remain relevant. Actual source recordings and their byte-level reader
checks must be executed on the integrated revision before recording progress.
