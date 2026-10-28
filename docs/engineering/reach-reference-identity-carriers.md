# Independent identity carrier reuse

This note derives the optional identity-hinge step in
`ontokin/reach_reference.py`. It supplements
[the independent complete-carrier recurrence](reach-reference-world-recording-proof.md).
It is a reader derivation, not a production allowance or an executed acceptance
result.

## Exact source condition

The independent reader has already captured the hinge, its child-site pose,
the complete parent ancestry, and its own ideal coordinate law. A relative
transform is the exact positive identity when all of the following hold:

- The admitted source hinge axis is an exact signed Cartesian unit vector.
- Its unclaimed ideal coordinate is exactly zero, or both its admitted ideal
  initial and target coordinates are exactly zero. In the latter case the
  original affine subtraction preflight and nonzero-duration admission still
  run. A zero current derivative by itself does not prove this condition.
- The child-site translation has three exact zero components.
- The child-site raw quaternion has a finite positive scalar component and
  three exact zero imaginary components.

The ideal hinge angle is then zero at every clock in the captured law, including
when paused. Its quaternion is exactly `+1`. The child's raw quaternion
normalizes to `+1`, and its inverse is also `+1`. Both local translations vanish.
Consequently the complete child pose is the parent's pose: its position,
orientation, velocity and angular velocity enclosures can be reused directly.
The proof does not assume that every point in an orientation interval box is a
unit quaternion. Multiplication by the positive identity is exact for every
quaternion represented by that box.

The positive representative matters. A negative scalar quaternion keeps its
ordinary path and source representative. Nonzero coordinates, paused nonzero
angles, nonzero child offsets and nonidentity child rotations do not qualify.

## Recording scope and finite domain

Reuse is restricted to the existing optional ideal recording walk, its
128-bit interval grid, and the full 32,768-bit live operand cap. The parent must
be an exact immutable `PoseEnclosure` containing all four correctly sized
tuples of exact `Interval`/`Fraction` components. Every returned endpoint is
guarded in the current domain.

This removes a duplicate complete-world rotation trajectory when an identity
hinge is carried by a moving ancestor. It does not create another numeric
cache. The ordinary immutable source recipe remains unchanged, so narrower
domains and unsupported shapes use the original body seed or local equations.
Their original arithmetic failures remain outside any added retry handler.

## Fresh source admission and cancellation

An earlier parent pose, a zero rate, or equal sampled quaternions is not source
authority. The new path retains the complete current ancestry receipt check.
Each receipt is precharged, and a changed live cap immediately declines reuse.
After the last callback, every captured source receipt is compared with its
current immutable source operands, and every returned parent field is admitted.
No callback follows those checks before the parent pose is selected.

A changed receipt raises the existing identity error. A callback exception
propagates unchanged. The identity helper neither reads nor publishes a numeric
cache entry, so cancellation in its admission cannot advance a child cursor or
reorder the cache. The existing parent cursor and all nonidentity descendants
retain their own ordinary source-bound proofs.

This is a local orientation/relative-transform proof. It does not claim that
the entire surrounding source position walk is an atomic snapshot against
arbitrary mutation of private interpreter state.
