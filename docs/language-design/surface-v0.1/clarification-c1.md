# OK-LANG-003-C1: Numeric boundaries and immutable mesh inputs

Version: 0.1. Adopted: 2026-10-18. Applies only to the prospective `surface-0.1` profile and its experimental kernel. This supplement clarifies [OK-LANG-003](../OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md); it does not register a working source language, agent protocol or GLB target.

## C1.1 Station representation at the minimum separation

The required ideal station separation remains exactly 1/1000 meter. Stations supplied to the kernel have already been rounded to binary64. A fixed absolute tolerance such as `1e-12 m` is not permitted: it admits below-limit gaps near zero by substantially more than coordinate representation requires.

For each finite canonical station `x`, let `u(x)` be its binary64 unit in the last place, as returned by `math.ulp(x)`. For two ordered stations `a < b`, define the representation allowance as `(u(a) + u(b)) / 2`. Compare the exact rational difference of the two binary64 values, without an additional rounded subtraction. Accept the boundary exactly when:

`exact(b) - exact(a) + (exact(u(a)) + exact(u(b))) / 2 >= 1/1000`.

Always reject equal stations, including opposite signed zero. The allowance accounts only for coordinate representation. It does not promise that the stored geometric gap itself is at least one millimeter, or that an original higher-precision input exceeded that threshold. It must not be enlarged by the caller or used as a geometric approximation allowance. Below-limit diagnostics expose the measured separation and representation allowance.

Predetermined examples: `(0, 0.001)` and `(1, 1.001)` pass; `(0, nextafter(0.001, 0))`, `(0, 0.001 - 5e-13)` and `(1, nextafter(1.001, 0))` fail. The boundary at translated coordinates is therefore explicit rather than controlled by an arbitrary epsilon. These cases were written before applying the correction to the experimental kernel. The original acceptance manifest is not changed.

## C1.2 Snapshot ownership

Validation must produce fresh, canonical, immutable section and material records. Do not retain a caller-owned mutable color or center list in accepted mesh results. Read and validate each numeric component into binary64 once; use that validated value during generation. A cooperative cancellation callback that changes its own input lists must not change values already validated by the generator.

The kernel is not an operating-system sandbox or a concurrent shared-memory API. Arbitrary unsynchronized mutation while inputs are being read is not supported. It must nevertheless isolate its validated snapshot before invoking generation callbacks, and returned arrays and material records must not alias caller-owned lists.

## C1.3 Work and reporting

Observe cooperative cancellation during the existing bounded generation loops and final material grouping. A raised cancellation exception propagates without returning a mesh. Counts are checked before allocating mesh arrays; each invocation receives an explicit remaining vertex budget. A caller assembling several lofts must reduce that budget for every occurrence, including repeated geometry. A single successful kernel call does not prove request-wide budgeting in a source compiler that is not yet implemented.

The tests in `tests/test_surface_regressions.py` exercise this supplement. `tests/test_surface_manifest.py` reads the unchanged published acceptance values directly. Both test kernel properties, not completed M01-M12 source/agent/destination gates.
