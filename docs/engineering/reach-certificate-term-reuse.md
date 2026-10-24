# Exact term reuse inside one independent certificate

This development change is confined to the independent supplied-byte reader in
`ontokin/reach_conformance.py`. It retains completed exact arithmetic inside one
`_complete_inequality_values` invocation. The original source fixtures, reported
certificate obligations, numerical limits and release acceptance remain binding.
Execution results and the integration decision are recorded separately in the
[October 23 continuation record](reach-recording-validation-2026-10-23/README.md).

## Arithmetic identity

The adopted [complete inequalities](../language-design/planar-reach-v0.1/quantization.md#5-nonzero-endpoint-slerp-proof-and-complete-inequalities)
require separate authored and stored quarter-allocation plans. For authored
width `h`, angular bound `W` and acceleration bound `A`, the first plan already
computes the following exact values:

| Term | Calculation | Later use |
| --- | --- | --- |
| Angle | `W * h` | Authored angle squared |
| Width squared | `h * h` | Authored chord |
| Angle squared | `(W * h) * (W * h)` | Quaternion difference and ideal rotation |
| Ideal rotation | `angle_squared / 4` | Independently required ideal rotation |
| Acceleration product | `A * width_squared` | Authored chord |
| Chord | `acceleration_product / 8` | Independently required ideal position and carrier sum |

The later authored calculation repeats four multiplications and two divisions.
When the exact original operands, results and arithmetic context remain admitted,
those six operations can use the already completed results. Both quarter plans,
their comparisons, all reported-field reads, the stored arc, quaternion difference,
time-shift terms, final sums and tolerance checks still execute. Equal authored
and stored quarter inputs do not currently share their quarter calculations.

The reader derives these terms itself. No producer result supplies an independent
minimum, and no rounding, precision or tolerance changes. The complete ordinary
function remains the control in the dedicated tests.

## Finite scope and guards

Admission requires an exact native quantity dictionary with the original complete
key set and native Fraction operands with positive denominators and integer fields
of at most 2,048 bits. Authored and stored widths, tolerances, quarter outputs and
bound coefficients are admitted. Wider or unsupported values retain the complete
original calculation.

For this domain, an authored angle or width square has fields at most 4,096 bits.
Squaring the angle requires at most 8,192 bits; division by four adds at most three
bits. The acceleration-width product and its division by eight are smaller. These
conservative bounds fit the unchanged 32,768-bit operand maximum. Each actual
reuse also checks the original operand, prospective-product and result widths at
that omission point. A lower live operand limit declines reuse.

Six fixed named receipts retain only this invocation's already completed scalar
results and exact integer fields. Every receipt identifies its actual operands,
arithmetic object, request-work owner and callback. Before using a result, the
reader checks both its inputs and its result fields again, then copies the admitted
integer fields into a separate Fraction object without another rational operation.
No receipt survives the invocation. There is no new persistent numerical cache;
the existing cache maximum remains 256 entries.

The optional admission bounds the native work-category dictionary at 512 entries.
This is a finite inspection bound for counter metadata, separate from the numerical
cache maximum. A larger inventory takes the ordinary path. The original P09 request
already has more than 256 work categories, so confusing these limits would disable
the intended optimization.

## Native dispatch and ordinary fallback

The shortcut admits the original Bounds and work methods, Fraction arithmetic,
properties and construction helpers, their used function code/defaults/closures,
relevant module and builtin bindings, the native clock, and primitive counter
containers. Native class/module dictionary access precedes potentially changed
instance descriptors. Keyword-default entries are captured by key and value,
because the keyword-default dictionary can change in place.

Direct work without an external callback is supported. An exact native
`ConstructionBudget.tick` callback is also supported when its nested check is
absent and its methods, primitive counters, limits and clock remain native. It
continues to charge the inherited shared request budget for every performed
operation. A custom callback, nested construction check, preexisting observer,
foreign scalar dispatch or unsupported owner retains the original calculation
without an added admission charge. Existing callbacks and observers are never
replaced or cleared by this optimization.

This deliberate scope keeps cancellation, reentrancy, callback mutation and foreign
exception identity on the original path. Tracing and profiling hooks also decline
admission. Consequently the previously accepted v7 profiling observer describes
the original control; it cannot establish a neutral measurement of enabled reuse.
Ordinary unprofiled collectors and paired complete requests measure this candidate.

The first quarter's already charged calculations produce the local receipts.
Both mandatory quarters and the stored-arc rejection execute before the first
attempt to omit arithmetic. At that point a named admission operation is charged
before the reuse proof, guards and copies. Later receipt checks precede each later
omission. Original nested arithmetic expressions and bound-method order remain on
fallback. Failed requests publish no result and leave no term cache to reuse.

## Accounting and validation

An eligible complete invocation removes six actual scalar operations and adds one
admission operation: a predicted net saving of five. This is a structural count;
complete request measurements determine the realized benefit. Every arithmetic
operation still performed keeps its original charge. No request limit is increased.

The dedicated tests compare the untouched original function and the candidate on
equal and unequal quarters, changed operands, zero coefficients, exact boundaries,
underreported claims, malformed widths, narrow domains, callbacks, reentrancy,
mutable defaults and foreign dispatch. Actual P09/P11/L03 prefixes compare complete
GLB bytes and complete reports, with construction and validation included in their
operation costs. The original 28-recording collector remains the release gate.

Selected test cohorts, ordinary timing controls and the full recording rerun retain
their own exact source identities and input inventories. Neither a prefix pass nor
a lower operation count establishes compatibility, native/browser/visual acceptance,
the complete reach release or the full OntoKin product goal.
