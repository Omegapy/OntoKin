# Exact coaxial source-phase derivative bounds

This engineering derivation accompanies `ontokin/reach_phase.py`. It tightens
the ideal continuous derivative bounds used by the existing recorded GLB/0.6
planner. It does not change source coordinates, the source numerical kernel,
the recording tolerances, the fixed quarter allocation, the 100,000-operation
limit, or the required geometry and interval coverage. The general numerical
allowance derivation remains in [reach-numeric-kernel.md](reach-numeric-kernel.md).
The adopted recording argument remains in
[sampling-bound.md](../language-design/planar-reach-v0.1/sampling-bound.md) and
[quantization.md](../language-design/planar-reach-v0.1/quantization.md).

## Narrow topology proof

For each resolved source frame, an optional phase-local descriptor states that
its ideal angular velocity in its own body coordinates is the constant vector
`c e_k`, where `c` is an exact rational and `e_k` is a Cartesian unit vector.
The separate zero descriptor has no preferred axis. An absent descriptor means
the ordinary conservative recurrence is used. The descriptor is rebuilt from
current phase operands and source topology; it is not inferred from samples,
measured residuals, or a previous phase's numerical cache.

The proof admits only these transitions:

1. A root with no running orientation claim has zero angular velocity. A
   running root spin qualifies only when its canonical world vector has one
   nonzero component, its initial ideal rotation allowance is exactly zero,
   it has no transferred private rotation anchor, and its initial quaternion
   preserves or reverses that Cartesian axis. The inverse initial rotation
   supplies the body-coordinate sign.
2. A constant site, follow offset, or inverse child-site rotation transports a
   nonzero descriptor only if its canonical quaternion preserves or reverses
   the same axis. Zero angular velocity remains zero under any constant valid
   rotation.
3. A hinge must have an exact canonical positive or negative Cartesian unit
   axis. A stationary parent admits that axis; a moving parent must have the
   same body axis. Add the signed exact ideal affine hinge slope to the parent
   coefficient. Exact cancellation produces the zero descriptor. A stationary
   parent and stationary hinge remain stationary even when the axis is outside
   this optional narrow proof.
4. Fixed joints, active rigid grips, and sliders have identity relative
   orientation and preserve the descriptor before the child-site transform.
   Dynamic roots, noncoaxial moving hinges, general fixed-axis changes, and
   transferred root-spin anchors use the ordinary recurrence.

Canonical quaternions have order `(w, x, y, z)`. For axis `k`, a finite nonzero
quaternion preserves `e_k` when its other two imaginary components are exactly
zero. It reverses `e_k` when `w` and its `k` imaginary component are exactly
zero. These statements follow directly from the homogeneous quaternion
rotation formula, and hold without assuming that the quaternion's binary64
norm is exactly one. The inverse rotation has the same sign on this invariant
one-dimensional subspace. No near-zero threshold or approximate angle test is
used. More general axis permutations are deliberately outside this proof.

## Constant signed rates

Let `R(t)` map a frame's body coordinates to world coordinates, and let its
body angular velocity be the proved constant vector `u = c e_k`. Then

\[
\omega(t)=R(t)u,\qquad
\dot\omega(t)=R(t)(u\mathbin{\times}u)=0.
\]

Thus a valid angular-speed bound is exactly `abs(c)` and a valid angular
acceleration bound is zero. For a coaxial parent and hinge, the hinge rotation
fixes the common axis, so the child body rate is

\[
c_{\mathrm{child}}=c_{\mathrm{parent}}+s\,\dot q_{\mathrm{ideal}},
\qquad s\in\{-1,1\}.
\]

The ideal hinge slope is the existing exact canonical operand ratio, including
any continuous ideal start carried through a nonbinary event boundary. It is
never substituted with a rounded inspection rate. This signed sum can be much
smaller than the sum of absolute rates. For example, opposing shoulder and
elbow motion in P09 has a single constant combined angular rate, although the
general norm recurrence treats their contributions separately.

The existing ideal carrier-speed and carrier-acceleration formulas remain in
place. They consume the tighter parent angular bounds, so a downstream rigid
offset uses the proved `abs(c)` and zero angular acceleration. The standard
triangle and cross-product inequalities still bound every carrier point.
No position or translation contribution is dropped merely because the final
angular rate cancels: ancestor translations and their accelerations remain.

## Source numerical allowances and bounded work

Only these four ideal fields can decrease: carrier speed, carrier
acceleration, angular speed, and angular acceleration. Actual speed and angular
speed, position and rotation allowances, velocity and angular-velocity errors,
anchor errors, coordinate errors, path extents, and operation counts in the
source numerical derivation retain their original recurrences. Those error
recurrences use actual rates and numeric error fields, not the ideal angular
fields tightened here. Generic composition cache entries remain unmodified;
the current topology descriptor is applied only when returning a checked
result. A tightened parent participates in the complete existing cache key.

The source traversal stores one optional immutable descriptor per already
resolved frame. It introduces no reusable numeric-result cache and does not
increase the existing 256-entry cache limit. Canonical shape, type, finiteness,
axis, and quaternion tests are freshly charged fixed-size operations. Exact
rate addition uses the existing operand and intermediate-width guards. If the
live operand cap is below the full 1,075-bit binary64 domain, the optional
structural recognition falls back; the ordinary per-operand arithmetic still
enforces that lower cap. Returned bounds recheck their complete operands after
callbacks, including cancellation and live limit changes. A failed calculation
does not publish source state.

## Verification obligations

`tests/test_reach_phase_coaxial.py` checks signed rates and exact cancellation,
all Cartesian axes, reversing mounts and inverse child transforms, generic
fallback, changed source operands with warm caches, eviction, live limit
changes, and cancellation. It compares every non-derivative bound field exactly
against the unchanged generic recurrence, including P09, moving-root/release
P16, and a lifecycle handoff. These tests require execution evidence at the
actual candidate revision; this derivation alone is not an executed result.

An independent source-topology derivation must establish the reader's required
derivative minima without importing this production helper or trusting its
cache. Tighter valid bounds may change the recording timeline and GLB bytes;
the new output must satisfy the same complete point, interval, and reference
checks. An earlier artifact or a passing sampled comparison cannot establish
acceptance for the changed timeline.
