# Independent sufficient endpoint and arc bounds

This derives optional supplied-byte checks in
[`reach_conformance.py`](../../ontokin/reach_conformance.py). It implements the
existing [GLB/0.6 quantization contract](../language-design/planar-reach-v0.1/quantization.md);
it changes no source equations, tolerances, resource limits, destination method,
or supplied certificate field. It is an implementation argument, not a release
acceptance result.

## Independent source and actual bytes

The independent reference reconstructs the source topology, coordinate laws and
event history. Its ideal pose enclosures contain the true source position and a
unit quaternion representing its ideal rigid orientation. Initial placements
are independently normalized. Hinges use independently normalized source axes
and enclosed sine/cosine; spins use the same unit-rotation definition. Quaternion
products and inverses preserve unit length. Ideal release and dynamic anchors
transfer those ideal poses, and subsequent rigid rotations preserve that
property. Interval rounding encloses those true values; it does not assert that
every point of a component interval box is unit.

The checker reads the actual finite stored quaternion components as exact
rationals. It chooses a source antipode using the existing largest-component
sign rule. Either source antipode remains unit. An ambiguous interval can make
the resulting bound insufficient; it cannot make it an underestimate. Neither
the source enclosure nor its unit property comes from a writer certificate.

## Endpoint sufficient inequality

For nonzero stored vector `x`, a unit source quaternion `q`, and Euclidean norm,
the triangle and reverse triangle inequalities give

```
||x/||x|| - q|| <= ||x/||x|| - x|| + ||x - q||
                 = |1 - ||x||| + ||x - q||
                <= 2 ||x - q||.
```

If the independently aligned source component belongs to `[lo_i, hi_i]`, let

```
D_i = max(|x_i - lo_i|, |x_i - hi_i|),
E = 2 sum_i D_i.
```

Exact rational `E` therefore bounds the distance between the mathematically
normalized stored endpoint and the true unit source quaternion. `E <= 1/2`
also proves `||x-q|| <= 1/4`, hence `||x|| >= 3/4`. Thus neither a zero stored
quaternion nor the original normalizer's near-zero failure domain can pass
this sufficient test. A nonunit stored vector remains permitted by the format:
if this inequality is too loose, the original exact normalization is performed.

For positions the same component distances yield `sum_i D_i`, an upper bound
on the required Euclidean position error, without the factor two.

An endpoint belongs to at most two adjacent interval certificates. The checker
admits both actual claims and uses their minimum as the sufficient-test limit.
A sufficient bound is used only when it is no greater than that exact supplied
limit. Otherwise the existing outward normalized-quaternion or Euclidean norm
calculation supplies the bound. Every certificate row is subsequently checked
against its own independently obtained bounds and all complete inequalities.
The supplied claim is a threshold, never an expected endpoint or source oracle.

A sufficient bound can be larger than the original norm bound. A claim below
that sufficient bound is consequently not itself a forgery: the fallback may
prove it. Hostile tests must understate the original exact comparison, rather
than assuming that every conservative upper bound is a necessary lower limit.

## Arc sufficient inequality and actual lift

Two exactly equal typed raw operands have exactly the same normalized
quaternion and zero arc. The checker may use this identity after fresh raw
admission only when both completed endpoint proofs name those same operands
and the current full operand cap. Each endpoint proof already established a
valid nonzero normalization, either directly or through the sufficient
endpoint inequality. This is an equality of actual stored operands and
requires no continuity between source anchors, so it remains valid at semantic
boundaries. A foreign raw operand or narrower live domain retains the original
calculation; the supplied zero-arc claim is still admitted and checked with
every certificate's complete inequalities.

Let the independently proved endpoint unit-chord errors be `e0,e1 <= 1/2`,
let `W` be the independently derived physical angular-speed bound of the
source phase, and let `h` be the exact authored interval width. The ideal
orientation path has quaternion-sphere length at most `W*h/2`.

For unit quaternions at chord distance `e <= 1/2`, the shorter spherical
distance is `2 asin(e/2) <= 2e`. In the antipodal orientation metric, triangle
inequality therefore gives an upper bound on the shorter stored endpoint arc:

```
c = W*h/2 + 2*e0 + 2*e1.
```

This argument allows different independently chosen source antipodes at the
two endpoints. It uses the physical orientation metric, where those antipodes
are the same orientation. The optional path is used only when the right
endpoint lies strictly inside the same retained source phase as the left
endpoint. At a semantic boundary, the right endpoint is sampled from the
outgoing state and may have a separately retained ideal anchor. Its actual
stored arc uses the original normalized-endpoint calculation, without assuming
continuity between independently retained anchors. No interval crossing an
unretained source boundary is admitted.

The checker independently establishes the exact dot-product sign of the two
actual raw stored quaternions. Normalization divides by positive norms and
preserves that sign. A negative dot is rejected, so the literal supplied lift
must agree with the short spherical lift. Zero dot is not assumed to mean zero arc: it
has spherical distance pi/2, and therefore cannot satisfy a sound `c <= 1/2`
proof. When the sufficient proof cannot establish the local range, the original
normalized endpoint calculation remains responsible for accepting or rejecting
it.

When all nonzero coordinate products have the same sign, that sign follows
from the signs of the actual operands, without forming any product or sum.
Zero coordinates, including either signed zero, contribute exactly zero; no
overlapping nonzero coordinates therefore prove an exact zero dot. Mixed
product signs retain the original exact dot calculation, including possible
exact cancellation. This sign proof changes neither the independent endpoint
nonzero proofs nor the source-path inequality. In particular, a zero dot does
not establish a zero arc.

The optional sign proof is restricted to exact finite binary64 components,
each zero or with magnitude in `[2^-200, 2^128]`. A nonzero binary64 in this
range has at most 53 significand bits. Below one, its reduced denominator is
at most `2^252`, because the smallest admitted exponent is -200; above one,
its reduced numerator is at most `2^128`. Thus every exact reduced numerator
has at most 129 bits and every denominator at most 253 bits. This proves the
same 256-bit input domain required by the existing sufficient arc, without
allocating and decoding eight exact ratios. Larger and smaller finite values,
integer components and other types retain the existing admission and exact
fallback behavior.

Both raw vectors still pass fresh `_recording_vector` admission before any
sign proof or complete-arc cache reuse. The fixed-size sign proof has its own
charged cancellation checkpoint and immediately checks the live full operand
cap afterward. A narrowed cap retains the original arithmetic and lazy
normalization checks. Callback exceptions propagate unchanged. The sign
classification retains no additional cache entry; complete arc reuse and all
subsequent source/error scalar guards remain unchanged.

The actual chord is no greater than its arc and hence no greater than `c`.
For `0 <= c <= 1/2`, the increasing rational chord-to-arc envelope gives

```
actual stored arc <= c / (1 - c*c/4).
```

The checker uses that exact rational result only if it fits the actual supplied
`stored_quaternion_arc_upper_rad`. Otherwise it lazily normalizes either
endpoint that does not already have a current-domain normalization proof, and
runs the original exact stored-arc calculation. The separately checked arc cap,
destination numeric bound and complete continuous inequalities are unchanged.

## Operand domains, accounting and reuse

The optional path is restricted to the original full 32,768-bit operand cap.
Each admitted input rational to its small arithmetic proof has numerator and
denominator bit lengths at most 256. The ordinary finite/type/shape and ordered
interval checks still precede cache access. The cap is checked again after
charged callbacks and before using a sufficient result. A narrower live cap
uses the original path, including its prospective root-shift and cross-product
checks; a cache hit cannot widen it.

The small domain is also safely inside the original full-cap calculation:
squaring four 256-bit rationals and adding them has numerator/denominator
width below 2,060 bits; the 96-bit root grid adds 192 bits. A successful
endpoint shortcut proves raw norm at least 3/4, so the root lower bound is
positive. The component divisions, interval differences, four-component
squared norm and its root stay below 16,384 bits even with unreduced
cross-product estimates. Three-component position differences need less.
The optional arc uses the same bounded raw values and source/error scalars;
its old normalized endpoint proof lies in the same full-cap domain. Larger
operands retain the original calculation without attempting this shortcut.

Every executed exact add, subtract, multiply, divide and comparison uses the
existing charged, prospective-allocation-guarded arithmetic. No operation is
discounted, counter reset, tolerance enlarged or additional numeric cache
created. Complete immutable orientation and arc bounds use the existing
256-entry LRU with their exact operands and current cap in the key. The claim
threshold is checked afresh and is not part of the cached mathematical proof.
Every raw endpoint is admitted on every use, including a warm cache hit.

The existing preceding-endpoint map records the cap under which its complete
proof was made. Stationary-source reuse requires the current cap to match,
fresh admission of the actual stored values, and bounds sufficient for the
current adjacent claims. A tighter claim or changed domain recomputes the
proof. Lazy normalized cells carry their own cap. Callback exceptions propagate
unchanged; no partially completed sufficient proof is returned or published.

After a stationary endpoint has successfully compared both errors with its
actual adjacent-row limits, the same preceding-endpoint entry may retain those
two typed limits as a completed comparison receipt. A later endpoint still
admits every adjacent row, checks the actual stored operands and independently
establishes source stationarity. When the proof cap and both typed limits are
unchanged, the receipt proves the same two inequalities without repeating
their rational cross products. Changed or tighter limits perform both ordinary
comparisons again; a changed cap requires a new endpoint proof. No receipt is
created before both comparisons succeed, no caller-owned previous entry is
mutated, and no additional cache or retained history is introduced.

Focused tests are in
[`test_reach_independent_sufficient_bounds.py`](../../tests/test_reach_independent_sufficient_bounds.py)
and [`test_reach_stored_lift_signs.py`](../../tests/test_reach_stored_lift_signs.py).
Full source, hostile-byte, cancellation, rollback, destination and release
acceptance still require their separately executed evidence.

## Attaining-point witness for independent geometry

The independent source-geometry walk computes the exact maximum of each
vertex's L1 radius. Its existing outward binary64 screening never excludes a
possible new maximum. A repeated vertex with the same ordered absolute
binary64 coordinates as a point attaining the current maximum has exactly
that same rational sum. The walk may therefore retain the three immutable
coordinates of one attaining point alongside its already retained maximum,
and omit only the repeated rational decodes and additions for an equal tuple.
This also applies when the maximum is zero or two distinct ordered tuples
attain the same maximum; the most recently proved attaining tuple can replace
the previous witness without changing the maximum.

Every vertex still consumes its original `independent_geometry_point`
checkpoint and undergoes the complete source-to-stored binary32 comparison.
Every component still participates in the vertex-error maxima. Changed source
coordinates, component order, or stored values cannot use this equality to
omit those checks. The witness applies only after that checkpoint, at the
original full operand cap; narrowing keeps the original exact scalar sum and
its guards. Finite binary64 ratios and the three-term original rational sum
fit that full domain. No cache, numeric allowance, certificate quantity,
vertex limit, output byte or source occurrence is added or changed.

The dedicated tests in
[`test_reach_geometry_maximum_witness.py`](../../tests/test_reach_geometry_maximum_witness.py)
compare the exact original extrema and actual charged arithmetic, including
new maxima, supplied-byte mutations, current-domain narrowing and original
cancellation identity. Execution results are recorded separately.
