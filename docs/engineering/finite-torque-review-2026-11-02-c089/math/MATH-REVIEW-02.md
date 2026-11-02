# C089 independent mathematical review — revision 02

Review scope: the proposed fixed-axis finite-torque design on the final C088 baseline `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`. This record supplies mathematical witnesses for a design decision. It does not adopt torque syntax, implement torque, freeze release inputs, or establish a passing product gate.

## Review correction and current evidence

The parent review identified that the original translation diagnostic used exact clocks 3/10 and 2/5. Those are valid mathematical samples, but current authored source-event clocks are the rational values of canonical binary64 numbers. The original script, report, and review remain unchanged. This revision uses a new diagnostic with exact dyadic clocks and canonical binary64 inputs. `analyse_canonical_rounding.py` and `canonical-witnesses-02.json` record sixteen separate passing assertions. They reproduce the arithmetic formula without importing or executing production code. The earlier 663 arithmetic assertions remain ideal-model design evidence only.

## Decision supported by these witnesses

An exact named Cartesian world axis with signed scalar angular speed and torque is a coherent first scope. The axis remains fixed when speed reaches zero or reverses. It avoids a real failure of exact collinearity under component-wise binary64 rounding. A future arbitrary-axis scope needs a different explicit state and admission contract; an unspecified tolerance cannot resolve that contract.

Torque-only events must preserve the existing translational anchors. Inserting an otherwise irrelevant rounded anchor can change later position even with zero force and constant velocity. Recorded rotation needs both an acceleration interpolation bound and an angular-travel bound. Endpoint orientations alone cannot reveal a braking-and-reversal excursion.

## Executed independent calculations

`analyse_torque_math.py` uses only Python's standard library and imports no OntoKin production module. `analytic-witnesses.json` records 663 passing arithmetic assertions. These are repeated exact checks over eight named physical examples, five segmentation comparisons, fifteen interpolation grids, and two rounding witnesses. The assertion count is not a count of independent product requirements or release scenarios.

Each physical example has a literal expected table authored from the scalar equations. Work-energy checks provide a second identity. The following selected values use radians, seconds, kilograms, metres, and newton-metres under the physical SI-radian convention; they do not claim that the current language's distinct `Angle` dimension is interchangeable with a dimensionless value.

| Example | Inertia | Input | Selected expected state |
| --- | --- | --- | --- |
| Spin-up and coast | 1 | Initial speed 0; torque 2 during [0, 2] | At 2: angle 4, speed 4, work 8. At 3: angle 8, speed 4. |
| Brake through zero | 1 | Initial speed 2; torque -2 during [0, 2] | At 1: angle 1, speed 0. At 2: angle 0, speed -2. |
| Overlap | 1 | Torque 2 during [0, 3] and -1 during [1, 2] | At 1: angle 1, speed 2. At 2: angle 7/2, speed 3. At 3: angle 15/2, speed 5. |
| Cancelling overlap | 1 | Initial speed 1/2; torques +3 and -3 during [0, 2] | At 2: angle 1, speed 1/2, net work 0. |
| Different mass and radius | 1/2 | Mass 5, radius 1/2; torque 1 during [0, 2] | At 2: angle 4, speed 4, work 4. |
| Negative torque | 1 | Initial speed 0; torque -3 during [0, 1] | At 1: angle -3/2, speed -3, work 9/2. |
| Zero torque and speed | 1 | Initial angle 1/4; torque 0 during [0, 2] | Angle remains 1/4 and speed remains 0. |
| Adjacent acceleration and braking | 1 | Torque +2 during [0, 1], then -2 during [1, 2] | At 1: angle 1, speed 2. At 2: angle 2, speed 0. |

The physical example tables use ideal exact rational inputs. They are not expected bit patterns for a future canonical runtime. In particular, a production rule may round mass, radius, inertia, net torque, acceleration, speed, or angle at specified stages. Exact work-energy equality is not asserted for those rounded outputs; the future contract must define any discrepancy allowance before implementation. The inertia-1 examples use mass 5/2 and radius 1. Exact arithmetic gives `I = 2 m r^2 / 5 = 1`. A single torque-1 interval [0, 2] and adjacent torque-1 intervals [0, 1] and [1, 2], both starting at speed 1/3, produce identical exact angle, speed, work, and energy change at all five checked times. Their source histories still differ. This equivalence does not permit a runtime to erase source provenance.

## Scalar derivation and interpolation limit

For a free homogeneous sphere, use the scalar inertia required by the existing proposal:

`I = 2 m r^2 / 5`, `alpha = tau / I`.

Within one interval of constant net torque, with elapsed time `s`:

`omega(s) = omega0 + alpha s`

`theta(s) = theta0 + omega0 s + alpha s^2 / 2`.

For an interval of width `h`, the straight angle chord between endpoint values is

`L(s) = theta0 + (omega0 + alpha h / 2) s`.

Subtracting gives

`theta(s) - L(s) = alpha s (s - h) / 2`.

Since `s(h-s)` is maximized at `s=h/2`, its maximum is `h^2/4`. Therefore the largest absolute angle error is exactly `abs(alpha) h^2 / 8`. The checker verifies this identity at 17 rational positions for each of fifteen acceleration-duration combinations, including both signs and zero. Equality at the midpoint is checked separately. The algebra establishes the continuous-interval result; the finite grid is a reproducible arithmetic check of the derivation.

For ideal fixed-axis short-arc quaternion SLERP, orientation follows this linear angle chord when the endpoint arc is selected without wrapping. The bound is thus an analytic contribution to a delivered rotation-error budget. It is not the whole error budget. Canonical state rounding, quaternion construction and normalization, quaternion sign equivalence, stored time and quaternion quantization, and the actual destination interpolation behavior require their own allowances and checks.

An affine angular speed has maximum absolute value at one of the interval endpoints. A conservative travel bound is therefore

`travel <= max(abs(omega_start), abs(omega_end)) h`.

Combine a bound of this kind with the acceleration error test and the existing angular-step limit. Net endpoint displacement alone is insufficient. In the braking example, `theta(0)=theta(2)=0`, while `theta(1)=1`. An endpoint-only recorder can display a motionless body despite a one-radian excursion in each direction. Total absolute angular travel is 2 radians; the conservative maximum-speed bound is 4 radians. The exact interpolation error is 1 radian, matching `abs(-2) * 2^2 / 8`.

A zero crossing need not be serialized as an additional source event. Its exact time `-omega0/alpha` may have a non-terminating decimal expansion, whereas the current `time_text` publication contract requires finite decimal clocks. An internal rational extremum calculation and a conservative gap bound can detect the excursion without inventing a publishable source clock. If the future implementation chooses to add an actual recording key there, its clock representation and quantization policy must be specified first.

The work-energy identity follows directly:

`W = tau (omega0 h + alpha h^2 / 2)`

`Delta K = I ((omega0 + alpha h)^2 - omega0^2) / 2 = W`.

It holds on each constant-torque interval and therefore sums over overlaps and adjacent intervals. The braking example removes kinetic energy before the zero crossing and adds it again after reversal; its net work over the full interval is zero.

## Witness 1: exact collinearity is not closed under vector rounding

Start with the common binary64 direction `(0.6, 0.8, 0)`. Binary64 `hypot` reports its length as 1.0. As with ordinary non-Cartesian normalized binary64 vectors, its exact rational squared norm is not exactly one; the witness concerns an admission rule that has already accepted this stored direction.

Let initial angular velocity equal that stored vector and let angular acceleration be exactly twice it. Both are exactly collinear with the stored axis when their binary64 components are interpreted as rational values. At exact elapsed time 1/8, an exactly representable binary64 source clock, the unrounded result is exactly 5/4 times the original vector and is still collinear.

Rounding the components separately gives `(0.75, 1.0, 0)`. The exact cross product with the stored original direction has nonzero z component

`-1 / 18014398509481984`.

Thus a later exact-cross-product admission rule would reject a state generated from its own initially accepted collinear inputs. Repeated normalization does not provide a specified state-preservation rule. The recommended Cartesian-axis scalar representation preserves exact off-axis zeros under its own rounding operations. A signed scalar also avoids redefining the axis at zero speed or reversal.

This witness is about a proposed rule, not a report that C088 currently implements or fails a torque collinearity test.

## Witness 2: a torque-only shared anchor can change translation

The current `ForceSimulator._dynamic_kinematics` computes position from the saved anchor using exact rational arithmetic followed by one binary64 rounding. `_aggregate` deliberately reanchors only when translational acceleration changes.

Use an initial position of 1 metre, canonical binary64 velocity `0.1` metre per second, and acceleration of 0. Evaluate at exact time 1 second. Add a gratuitous boundary at exact time 1/8 second. Both clocks are exactly representable as binary64; every chosen numerical input is in the canonical finite domain.

| Route | Position as binary64 hexadecimal | Decimal display |
| --- | --- | --- |
| Original anchor | `0x1.199999999999ap+0` | 1.1 |
| Gratuitous rounded anchor at exact time 1/8, then another exact 7/8 | `0x1.1999999999999p+0` | 1.0999999999999999 |

The difference is exactly `-1/4503599627370496` metre, one unit in the last place at this magnitude. The utility reviewer also independently supplied a tie-rounding case: position 1, velocity `2^-52`, split time 1/2, and end time 1. Direct evaluation gives `0x1.0000000000001p+0`; reanchoring gives `0x1.0000000000000p+0`. This script independently verifies that corroborating case with attribution.

These are formula-level reproductions of the baseline's canonical arithmetic with source-representable scalar inputs and clocks. The script does not construct or execute a complete `.ok` program and does not test a candidate torque runtime. Its claim is the numerical reason that preserving the translational anchor matters.
A future torque implementation that reuses the full `_DynamicInitial` state at every torque activation/completion can therefore change otherwise unrelated translation. Independent rotational anchors, or an equally explicit representation that preserves the original translational anchor exactly, are necessary for a no-change promise. Freeze this small constant-velocity case, zero torque, cancelling overlaps, and same-net interval replacement before runtime work.

## Exact source grounding and limits

The inspected sources are commit-pinned to C088:

- [Proposed C089 task](https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/docs/engineering/keyed-membership-2026-11-02-c088/NEXT-TASK.md): proposed physical equations and review obligations.
- [Evaluator](https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/evaluator.py): `_f`, `_round`, `_advance_orientation`, `_DynamicInitial`, and exact-time publication rules.
- [Force runtime](https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/force_runtime.py): `_dynamic_kinematics`, `_aggregate`, and whole-boundary staging.
- [Force recorder](https://github.com/Omegapy/OntoKin/blob/7b6900baa0357ab96c4639ac5c2ebe4e1791833e/ontokin/force_export.py): constant angular-contribution assumption, translational chord error, and angular-travel bound.

No production file, old fixture, expected result, or acceptance limit was changed. These witnesses do not test source grammar, diagnostic precedence, operational charging, cancellation, durable-store authority, edit rollback, hostile artifacts, recorded-byte acceptance, browser playback, or main integration. Those remain separate obligations for a complete adopted torque contract and its subsequent implementation.

To reproduce, choose a fresh output path and run:

```sh
python3 -B analyse_torque_math.py NEW-analytic-witnesses.json
python3 -B analyse_canonical_rounding.py NEW-canonical-witnesses.json
```

Both scripts refuse an existing output. Each report records the exact script hash, baseline, Python/platform, inputs, expected values, actual values, and every assertion.
