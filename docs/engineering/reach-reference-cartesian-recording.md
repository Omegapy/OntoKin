# Independent Cartesian recording rotation

## Scope and baseline

This bounded candidate extends the recording-only independent arithmetic from
`cbb2582141862a1d2e7e76b55690ff0e24fa6c89`. It admits a quaternion with at most one
nonzero Cartesian vector component and a general small native dyadic offset.
The existing scalar/Z, single perpendicular offset calculation remains a
separate branch with its original cells, order, and operation counts. Ordinary
source inspection and generic `rotate` retain their preceding expressions.

The motivation is the original P11 head. Its hinge axis is Y; its child origin
is `(0,-0.25,0)` with identity rotation; and its three eye/brow offsets contain
both axial and perpendicular components. A permutation restricted to one
perpendicular offset cannot cover these source operands. The separate source
plan change must still compose the original inverse child translation after
the independently computed complete body orientation. This arithmetic change
does not alter the source plan or any source coordinates.

The candidate is unexecuted at this document's first commit. The dedicated
tests and their identified execution must establish correctness and actual
cost. No original recording, integration, or release pass follows from this
derivation alone.

## Hamilton expansion and coordinate orientation

Let the active Cartesian axis be `a`, numbered X=0, Y=1, Z=2, and choose the
ordered basis

`(u,v,a) = ((a+1) mod 3, (a+2) mod 3, a)`.

Each choice is a cyclic permutation of `(X,Y,Z)` with positive determinant.
The multiplication signs in the right-handed Hamilton algebra therefore stay
unchanged. In that basis, write `q=(w,0,0,s)` and the vector as `(x,y,z)`.
Expanding `q*(0,x,y,z)*conjugate(q)` gives

`((w²-s²)x - 2wsy, 2wsx + (w²-s²)y, (w²+s²)z)`.

The implementation derives three interval factors independently:

| Factor | Exact expression | Use |
| --- | --- | --- |
| A | `w²-s²` | Perpendicular diagonal terms |
| B | `2ws` | Perpendicular signed cross terms |
| C | `w²+s²` | Axial scale |

It maps the result back through the inverse cyclic permutation. Signed source
axes are represented by the sign of `s`; no reflection is substituted for a
proper coordinate permutation. For example, positive Y rotation sends a
positive X vector toward negative Z.

The input need not be a point quaternion or exactly unit length. In particular,
C is calculated whenever the axial vector component is nonzero. It is never
replaced by one using an inferred unit property. The test quaternion `(1,e_a)`
has axial scale two and makes this distinction explicit.

## Enclosure construction

Each square uses both endpoint squares and includes zero when its input
interval straddles zero. These are the exact square extrema. A product uses
the ordinary sign-monotone extrema and retains the complete four-corner
finite-domain preflight. If both operands straddle zero, all four products
remain. Exact extrema for A, B, and C are combined before each factor's final
outward 128-bit grid.

Multiplying these factor intervals by the admitted offset components and
adding/subtracting the results supplies an enclosure of every point Hamilton
rotation in the entire input box. Discarding correlations among A, B, and C
can widen a bound; it cannot exclude a realizable point. The general branch
may have different conservative cells from the preceding two-Hamilton-product
expression. Equality to that older over-enclosure is not the correctness
criterion. Exact rational point Hamilton products and a finer independent
Taylor/Hamilton calculation provide separate containment controls.

An exactly zero coordinate omits its corresponding products, and an exactly
unit perpendicular offset can reuse A/B directly. A purely axial offset
calculates C alone. These are exact zero/identity facts admitted by the full
operand receipt. No uncertain zero is treated as exact. The ordinary scalar
product, sum, difference, negation and outward-grid kernels still perform
every required nonzero calculation and charge their original work.

## Bounded numeric admission

The optional path requires native tuples, `Interval` and `Fraction` records,
128-bit arithmetic, scale exactly `2^128`, and the unchanged full 32,768-bit
operand domain. Each quaternion/offset endpoint has at most 131 numerator bits
and 129 denominator bits and is aligned to the 128-bit grid. Reversed cells,
mixed quaternion axes, foreign records, non-dyadic operands, other precisions,
larger operands and narrower domains keep the ordinary calculation.

Before omitted operations or ordering, the caller checks the complete input
domain. Input magnitudes are below `2^131`; the factor magnitudes, including
outward rounding, are below `2^264`. Their stored grid numerators therefore
fit within 392 bits. A factor-times-offset result fits below `2^396`, and its
grid numerator within 524 bits. Prospective fraction products, endpoint sums,
and grid shifts remain below 1,024 bits, including the original generic
Hamilton expression's omitted zero terms and intermediate grids. This is a
sufficient optional proof; it does not enlarge the public operand limit.

When used by native sequential composition, both complete poses retain their
existing domain: eight native vectors, 26 cells, zero derivatives, a positive
identity local quaternion and a grid-aligned parent translation. The broader
Cartesian rotation is followed by the original parent-position sum, including
its nonzero endpoints and `_sum_enclosure`. Its orientation is the admitted
parent quaternion because the local quaternion is exactly identity.

## Callback, owner, and cache receipts

A standalone general rotation retains only seven local input-cell receipts.
They bind the interval and Fraction wrappers and their exact integer operands,
the arithmetic/work/check/external-callback owners, the native record classes,
precision and scale. The composition path additionally invokes its existing
complete 26-cell/pose receipt. Receipt comparison happens after every individual
remaining callback, including scalar products inside interval multiplication,
the two endpoint sums, and cache-domain synchronization.

The general path spells the existing multiplication/addition and LRU callback
boundaries explicitly to prevent a callback from changing an operand and
restoring it at the following callback before admission. Replacing a pose,
cell, Fraction operand, owner or native record class rejects the attempted
calculation. Native class checks precede potentially foreign attribute access.
Cancellation and original arithmetic exceptions retain their identities.

A cap or precision/scale change permanently invalidates the optional proof
for that call. Only that private invalidation returns to the original rotation
on the same work context. A later callback cannot restore and publish the
discarded optional result. An original fallback failure escapes immediately;
it is not retried after possible later broadening.

Standalone rotations use a distinct operation key containing the full original
quaternion and vector, so projected axes and offsets cannot alias. They retain
the original admission, lookup, synchronization, insertion, promotion and
eviction charges/semantics. Warm hits cost the same two checkpoints. Native
sequential composition retains its already approved omission of the one-use
rotated-value entry. No new numeric cache, pose table, history or cursor is
introduced. The 256-entry LRU, 64-step direct reseeding, 128-bit precision and
100,000-operation public budget are unchanged.

## Required evidence and limitations

`tests/test_reach_reference_cartesian_recording.py` contains 20 methods covering
signed boxes and point Hamilton products, proper cyclic signs, nonunit axial
scaling, finer independent Taylor cells, the unchanged old Z branch, full cache
keys and eviction, unsupported domains, every remaining callback's cancellation
and narrowing, restored caps, persistent/transient operand mutation, owner and
record-class replacement, reentry, translated compositions, original source
prefix bytes, and a measured four-offset P11 pattern.

The two older fallback tests remove only shapes now deliberately admitted:
scalar/Z axial or general offsets and their native composition. Those shapes
receive the new containment, nonunit and callback coverage; all previous
mixed-axis, foreign, non-dyadic, nonidentity and narrow-domain fallback cases
remain.

The analytic native composition counts for the head-origin/eye/brow shapes are
approximately 14, 44, 44 and 30 operations at a normal positive sine/cosine
cell, before actual execution confirms the pattern. They are not a full P11
projection: cold seeds, ancestry, queried carriers, phase changes, source
bounds, endpoint validation and certificate work remain. The separate source
plan activation and an actual original P11 run are necessary to assess the
combined effect. Every integration still requires the complete original
28-recording suite and all remaining mandatory release gates.
