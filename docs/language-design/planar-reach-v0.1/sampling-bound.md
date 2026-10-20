# Proposed conservative sampling bound

This derivation is part of the **unadopted** OK-LANG-006 draft. It establishes proposed planning inequalities for the supported two-hinge chain. The implementing GLB engineering contract must also fix the endpoint/time quantization allocation and independently verify supplied output bytes. Nothing here is a measured exporter result.

## 1. Semantic intervals and supported paths

Partition only the requested source prefix at every exact event, natural action completion, pause/resume/stop, force change and release. Within an open interval, each admitted joint coordinate is affine in exact time, a held coordinate is constant, the prescribed root translates at constant world velocity, and its world spin vector is constant. Every other root-to-base offset/rotation is fixed. The base cannot depend on an unmodeled dynamic or articulated ancestor in this first reach profile.

For a link/constant follower carrier, write its ideal world origin as a constant-velocity root plus a finite sum of rotated constant vectors. In the longest supported path, those vectors are: the complete root-to-base offset, the shoulder-to-elbow vector and the elbow-to-carrier vector. Constant mount rotations and following offsets are included in the actual vectors. The child-site zero/identity conditions remove additional animated pivots.

Let `w0` be the norm of root spin and `w1,w2` the absolute joint rates on this interval. For vector `j`, let `rj` bound its length and let `Sj` be the sum of angular-rate norms on the actual path that rotates it. A root-only offset has `Sj=w0`; an upper-link vector has `Sj<=w0+w1`; a forearm vector has `Sj<=w0+w1+w2`. Other inherited objects must have their own justified bounds; these two-joint formulas do not silently admit a general articulated/dynamic ancestor.

Scalar coordinate and exposed pose rounding remain separate from this ideal real-valued trajectory. Treat their errors as an explicit numerical/quantization budget, not as evidence that a rounded function is everywhere differentiable.

## 2. Translation and landmark curvature

For a constant-axis rotation `R(t)` with angular norm `w`, the induced operator derivatives satisfy `||R'||<=w` and `||R''||<=w²`. The second derivative of a product of rotating matrices applied to a fixed vector is bounded, by the product rule and triangle inequality, by `r*(sum w)²`. This includes cross terms from a rotating root and a nonparallel local hinge axis.

Therefore a conservative carrier acceleration bound is:

```text
A_carrier = sum_j rj * Sj²
          <= (sum_j rj) * (w0+w1+w2)².
```

Constant world root translation contributes zero acceleration. Actual source distances determine every `rj`; a display radius or just the longest authored link is insufficient when a root mount offset exists. Radius computation itself must be bounded by the mesh/object limits before key allocation. A freed sphere uses the inherited canonical net world acceleration for its free translation interval.

For any twice differentiable vector curve with `||p''||<=A`, linear interpolation between two exact endpoint positions at gap `h` has maximum Euclidean deviation at most `A*h²/8`. This follows from the scalar interpolation-error kernel, applied to every unit-vector projection; it is not three independent coordinate bounds multiplied by an assumed factor.

The same construction bounds a specific source landmark trajectory when its full local offset is included among the rotated vectors. A GLB rotates local geometry about an interpolated carrier, however, so source landmark chord error alone is not the complete GLB landmark error. The rotation contribution below must also be included.

## 3. Noncommuting orientation and quaternion LINEAR interpolation

Use a continuous unit-quaternion lift `q(t)` on one interval. A constant-axis rotation with angular norm `w` contributes quaternion derivative norm `w/2`. For the product of root and joint quaternions, set `W=w0+w1+w2`. Product differentiation gives:

```text
||q'|| <= W/2
||q''|| <= W²/4.
```

Let `L(t)` be the ordinary linear chord between exact lifted endpoint quaternions. Then `||q-L|| <= e = W²*h²/32`. Require `W*h <= pi/4`, so endpoint quaternion arc length is at most `pi/8`; the endpoint dot product is positive and the chord never crosses zero. Choose the same endpoint sign and normalize the chord, as the required decoded LINEAR rotation semantics do.

The normalized chord `N=L/||L||` obeys `||N-q|| <= 2*||L-q|| <= 2e`: the norm deficit of `L` is no larger than its distance from a unit `q`. Unit-quaternion distance gives rotation-angle error at most `4*asin(e)`. Since `e<=pi²/512<1/2` and `asin(e)<=2e` on this range, the simpler conservative bound is:

```text
B_rotation = W²*h²/4  radians.
```

This deliberately loose bound remains valid when root and local axes are nonparallel. An angular-step cap by itself does not show that the source orientation curve equals quaternion interpolation. A tighter bound may replace it only with an independent derivation and a reviewed change to the implementation plan, without changing predetermined acceptance tolerances.

## 4. Combined planning inequalities

For local landmark radius `r`, rotation-angle error `B` displaces that landmark by at most `2*r*sin(B/2) <= r*B`. Using carrier translation and quaternion interpolation bounds, require each planned interval to satisfy all of:

```text
W*h <= pi/4
B_rotation <= rotation_tolerance/4
A_carrier*h²/8 <= position_tolerance/4
A_carrier*h²/8 + r*B_rotation <= position_tolerance/4
```

The last inequality dominates the carrier-only position check for visible local points. `r` must bound every native occurrence vertex and retained site/landmark whose position is promised. It may be computed as a conservative AABB-corner radius; an independently validated exact maximum radius is also acceptable. Radius is about the delivered carrier origin after native local visual placement, not the geometric primitive's unplaced origin.

The quarter-tolerance allocations reserve error for source numerical representation, endpoint binary32 storage and time shifts. They are sufficient planning conditions, not permission to spend the remainder without checking. The final engineering contract must allocate and enforce the remaining terms, reject an impossible float32 representation, and check actual decoded carrier/landmark poses. Default delivered position and rotation tolerances remain `0.001 m` and `0.001 rad`, separate from the `1e-9 m` source goal residual; no draft fixture silently loosens them.

## 5. Exact time and stored time

Keep source semantic endpoints as exact rational clocks over canonical input numbers. Subdivide source intervals within bounded work. After conversion to binary32, require finite strictly increasing stored clocks equal to the specified conversion of the retained authored clocks. Two distinct semantic boundaries that collapse to the same stored value fail.

Recheck interval inequalities against the **actual stored gap** as well as the exact authored gap. Select rate/acceleration bounds by the semantic interval that produced the pair. A stored pair around a rounded semantic boundary must conservatively include every source phase it can cover; do not classify it only by a rounded midpoint. If a stored endpoint crosses the neighboring semantic boundary, use an enclosing bound and separately charge the shifted-time pose error, or reject/refine when representation cannot meet the tolerance.

At a true boundary, before/after action claims, derivatives, force/impulse histories and goal outcomes are separately preserved. Position/orientation continuity does not authorize dropping a pause, a stopped action or a force completion. Incoming release velocity is computed from the before-side full chain and then becomes the initial velocity of the independent free trajectory.

## 6. Bounded independent verification

Before geometry/sample/accessor expansion, charge distinct source chains, named actions, semantic histories, planned keys, materialized poses and output bytes against profile and request caps. Shared input accessors do not exempt repeated decoded output components or per-object poses. Cancellation checkpoints belong in planning, sampling, geometry, decoding and serialization, as well as action admission.

A supplied-byte checker reconstructs the requested prefix and its phase bounds from immutable source independently of the writer, verifies authored/stored clocks and every required metadata projection, and bounds aggregate accessor expansion before reading values. It then checks actual GLB source/Agent identity, carrier transforms, geometry radii, sampled source poses and expected goal outcomes. The fixed source corpus alone does not prove this checker; its corrupt-byte and budget probes are separately predetermined in [requirements.json](requirements.json).
