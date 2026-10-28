# Exact zero terms in the stored certificate quarter

This candidate extends the independent supplied-byte certificate reader in
`ontokin/reach_conformance.py`. It starts from the accepted checkpoint 026
runtime, carried by checkpoint 027 commit
`103a9cc8f87ac68af597e39557857c100bdee7ec`. The equal-operand candidate held at
checkpoint 027 remains outside integration. This is a separate identity with
its own proof and measurements; it does not relax that candidate's condition.

The adopted [complete inequalities](../language-design/planar-reach-v0.1/quantization.md#5-nonzero-endpoint-slerp-proof-and-complete-inequalities)
and both mandatory quarter plans remain unchanged. The existing
[authored-term proof](reach-certificate-term-reuse.md) supplies the bounded native
receipt and ownership model. Actual execution results and the adoption decision
belong in the [continuation evidence](reach-recording-validation-2026-10-23/README.md).

## Identity and original execution order

Let `W,A` be the authored angular-speed and acceleration bounds, `WE,AE` their
enclosing counterparts, and `hs` the actual stored width. Admission requires all
four original local coefficient objects to have native integer fields exactly
`(0,1)`. Noncanonical zero objects, nonzero counterparts and partial zero pairs
retain the ordinary calculation. No width equality is required or inferred.

The authored quarter has already completed and retained its exact angle,
angle squared, rotation, acceleration product and chord. Each result must still
have fields `(0,1)`, and each receipt must still match its actual operands and
result. The five stored terms are therefore equal to those completed zero
results even when authored and stored widths differ:

| Stored calculation | Exact result | Action |
| --- | --- | --- |
| `WE * hs` | `0/1` | Guard current operands and copy the completed zero angle. |
| `hs * hs` | Actual stored-width square | Execute the original operation, charge and all guards. |
| `angle * angle` | `0/1` | Guard current angle objects and copy the completed zero angle square. |
| `angle_squared / four` | `0/1` | Guard the current angle square and actual nonzero divisor. |
| `AE * actual_stored_width_squared` | `0/1` | Guard the actual stored square, never the authored square. |
| `product / eight` | `0/1` | Guard the current zero product and actual nonzero divisor. |

The stored square remains between the stored angle and angle square, exactly
as in the original expression order. Both quarters retain their angle and
rotation comparisons, radius multiplication, chord addition and position
comparison. All later reported claims, stored-arc checks, endpoint/time-shift
terms and final tolerance comparisons remain in their original places. A
fresh claim is never replaced by a saved claim or a previously successful check.

## Finite guard proof

Existing receipt admission bounds native input fields to 2,048 bits and requires
the original full 32,768-bit request domain. Its scalar dispatch, owner, native
construction callback, field access and function bindings must remain current.
The actual stored square has prospective and resulting fields of at most
4,096 bits. Its multiplication by a canonical zero has at most a 4,097-bit
prospective denominator. All optional proofs fit within the unchanged domain.

For a canonical zero `z=(0,1)` and current other operand `b=(bn,bd)`, the helper
retains the actual operand, prospective-product and result field guards of
`_Bounds.op`. Write `B(x)` for the bit length of integer `x`:

| Omitted operation | Prospective numerator guard | Prospective denominator guard |
| --- | --- | --- |
| `z * hs` | `B(hs.numerator)` | `1 + B(hs.denominator)` |
| `z * z` | `0` | `2` |
| `z / four` | `B(four.denominator)` | `1 + B(four.numerator)` |
| `z * actual_stored_width_squared` | `B(square.numerator)` | `1 + B(square.denominator)` |
| `z / eight` | `B(eight.denominator)` | `1 + B(eight.numerator)` |

Each check also includes all four operand-field sizes and the zero result's
field sizes `(0,1)`. Divisor nonzero checks use the actual operand. Guarding
only the small result would lose a required failure and is not permitted.
The unchanged actual square can still refuse a width or prospective product.
Wider initial fields or narrower live domains decline the optional identity.

## Ownership, callbacks and fallback

The new helper captures the four original local coefficient objects after the
authored quarter has completed. The existing receipt's input tuple did not
include the two enclosing coefficients, so the new helper explicitly rechecks
their current fields at each omission. It does not reread the quantity mapping
and thereby change the earlier local binding order.

Each omission validates the original authored result receipt, its operands and
the current stored-operation operands. It returns a new Fraction object copied
from the already admitted integer fields. The returned object does not alias
the authored result or any other returned zero. The actual stored square is
never copied from an authored receipt. All state lasts only for this invocation;
no numerical cache is added and the 256-entry numerical-cache cap is unchanged.

Original native method/function/descriptor bindings, work ownership and callback
identity remain mandatory. Foreign callbacks, nested construction checks,
observers, active tracing/profiling or changed dispatch retain the ordinary
calculation. A newly invalid receipt or operand declines the individual omission
before returning a value. Original arithmetic, callback and resource exceptions
escape unchanged. Existing callbacks and observers are not replaced or cleared.

Saved primitive nonzero authored fields reject ineligible groups before a new
heavy native-dispatch scan. This limits overhead where the identity cannot apply.
Metadata inspection retains its separate 512-category bound; that bound does
not enlarge numerical storage.

## Real accounting and validation

The first actual stored-zero omission charges the existing
`independent_certificate_term_admission` operation. Later authored-term reuse
shares that one admission. The mandatory first-quarter checks already ran;
the admission now precedes the stored angle instead of following both quarters.
An eligible native budget refusal can therefore occur at a different instruction.
The same budget mechanisms and maxima still apply. No identical callback schedule
is claimed for an optimized native calculation.

The identity structurally removes five additional scalar operations compared
with checkpoint 026: three multiplications and two divisions. The stored square,
all comparisons and radius arithmetic remain performed and charged. This count
is a proof prediction until measured complete requests confirm the saving.

Dedicated tests use the exact frozen checkpoint 026 algebra, with its original
global resolution and existing helper methods. New helper methods are additive;
the prior `create`, `current`, `calculate` and `borrow` behavior remains unchanged.
Tests cover unequal widths, each nonzero counterpart, noncanonical zero, ownership,
current stored-square guards, original claims, dispatch changes, interruption,
limits and complete work accounting.

Before adoption, original P09/P11/L03 prefixes at end `1/4`, 4 fps and helpers
disabled must each show positive complete shared-request savings across five
alternating control/candidate pairs. Complete GLB bytes and entire export reports
must match. The development timing screen is a candidate median no more than
10% above control in each case. This predeclared screen does not change the
30,000 ms request cap and does not establish an elapsed speedup. All attempts,
individual times and ranges remain evidence, including failures.

After an accepted candidate, execute the related cohort and every unchanged
original recording. The public limits remain 100,000 operations, 30,000 ms,
32,768 operand bits and 256 numerical-cache entries. Full regression,
compatibility, actual Agent delivery, destination/browser/visual roles, formal
input closure and R01-R12/Q01-Q22 remain separately required release gates.
