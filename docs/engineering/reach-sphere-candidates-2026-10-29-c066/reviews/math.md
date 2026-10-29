# C066 independent mathematics review

## Scope and source identity

This is a source-only review of a fixed eight-vertex shortlist for the cold
native 32-segment, 16-band sphere. No OntoKin module was imported. No geometry
was generated, product request executed, runtime trace collected, or runtime
test run. The radius witness below is conditional algebra, not an observed
native constructor output or an executed source program.

The reviewed files were recovered from C064 and independently compared by Git
blob hash with the complete uploaded C065 source index at commit
`b7357df3bc296cc1cd728bdf52dbeaf2697da85b`. Every comparison matched:

| Path | Git blob |
| --- | --- |
| `ontokin/geometry.py` | `c060ffb3b88023aa1521ef74777377a3ab47df7c` |
| `ontokin/reach_conformance.py` | `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea` |
| `ontokin/scene.py` | `e35942ed86fbe48be720ace7c0a5639ad4a63c59` |
| `ontokin/validator.py` | `66f1b29a56bc74479cb8bf818b86ebaf4a106a72` |
| `ontokin/values.py` | `d993e1e82cb6216eb2c1bf8b01208e0ae9e71cb6` |
| `docs/language-design/OK-LANG-001-core-language-specification.md` | `c3c8e82c8ca7f927563e5a29829bfbf287e29dbb` |

## What must remain exact

`geometry.py` 47–75 constructs 482 positions: two poles and 15 rings of 32
points. It rounds angle expressions, calls native `math.sin`/`math.cos`,
multiplies their returned floats to form normal components, and finally
multiplies each component by the radius. These positions are the source
vertices. The proof target is their exact rational L1 maximum, not the
continuous sphere's Euclidean radius or an ideal trigonometric maximum.

`reach_conformance.py` 817–839 validates each stored vertex first, screens its
actual absolute coordinate sum upward in binary64, and exactly decodes only
possible new maxima. A repeated maximum witness already avoids some exact
work. Lines 838–847 preserve componentwise conversion-error maxima and their
final exact sum. A new shortlist must not claim any of these existing omissions
as new savings.

For constructor latitude label `l` (1 through 15) and zero-based longitude
label `j` (0 through 31), the position index is
`1 + (l - 1)*32 + j`. The natural ideal-lattice shortlist is:

| Latitudes | Longitudes | Position indices |
| --- | --- | --- |
| 5 | 4, 12, 20, 28 | 133, 141, 149, 157 |
| 11 | 4, 12, 20, 28 | 325, 333, 341, 349 |

All eight must be retained: the actual angle evaluations and multiplications
need not preserve ideal sign symmetry or equal rounded sums.

## A restricted mathematical premise survives

Write the ideal unit-lattice coordinates as
`n(l,j) = (sin(theta)*cos(phi), cos(theta), sin(theta)*sin(phi))`, with
`theta=l*pi/16` and `phi=j*pi/16` interpreted as exact real expressions here.
This ideal model is used only to state a conditional enclosure theorem.

At a diagonal longitude, the L1 sum is
`f(theta)=sqrt(2)*sin(theta)+abs(cos(theta))`. The eight selected points have
ideal L1 sum greater than `1.73`. For example, exact half-angle formulas give
`sqrt(2)>1.4142`, `sin(5*pi/16)>0.8314`, and
`cos(5*pi/16)>0.5555`; their resulting lower bound is
`1.4142*0.8314+0.5555 = 1.73126588 > 1.73`.
These rational inequalities can be verified by squaring the positive radicals;
they do not require native trigonometric evaluation.

The companion `math_derivation.py` reproduced these rational bounds, the
conditional gap and the subnormal rounding cells with Python's standard
library. Its exact-rational derivation completed successfully. It states the
half-angle identities and monotonicity reductions as mathematical premises;
it does not evaluate `pi`, `sin`, `cos`, a sphere constructor, or a native
mesh. Its successful result is not product validation.

Every excluded ideal point has L1 sum less than `1.71`:

- An excluded longitude is at least `pi/16` from a diagonal. Thus its horizontal
  factor is at most `sqrt(2)*cos(pi/16)`. Maximizing over all latitudes gives
  `sqrt(1+2*cos(pi/16)^2)=sqrt(2+cos(pi/8)) < 1.71`, since
  `cos(pi/8)<0.924` and `1.71^2=2.9241`.
- At diagonal longitudes, symmetry reduces the latitude argument to the
  northern half. The continuous maximizing latitude `atan(sqrt(2))` lies
  strictly between `pi/4` and `3*pi/8`. Unimodality makes latitude 4 or 6 the
  largest excluded discrete latitude. Latitude 4 gives `1+sqrt(2)/2 < 1.71`.
  Latitude 6 gives `sqrt(2)*cos(pi/8)+sin(pi/8)`, which is less than
  `1.415*0.924+0.383=1.69046 < 1.71`.
- Each pole has L1 sum 1.

Consequently, for any positive radius `r`, **if every actual generated
coordinate satisfies**

`abs(actual_coordinate - r*ideal_unit_coordinate) <= r/1000`,

then a selected actual point has L1 sum greater than `1.727*r`, while every
excluded actual point has L1 sum less than `1.713*r`. All actual maximizers
therefore occur among the eight indices. Evaluating the eight actual points
exactly would recover the exact maximum; substituting the ideal value would
still be wrong.

This theorem is useful but conditional. The current source contains no
certificate establishing its premise for the rounded angle expressions,
native transcendental calls, component products and final radius products.
Restricting `r` to normal binary64 values removes the specific extreme-underflow
witness below, but does not itself establish that certificate. A restricted
normal-radius route remains mathematically plausible; it has no complete
authority, exception-order or funded cost proof in this review.

## The unrestricted eight-index premise fails under underflow

Let `mu = 2^-1074` and use the positive native radius `r = 2*mu`. Consider
ordinary native binary64 round-to-nearest multiplication and actual generated
normal components with these strict magnitude intervals:

1. At all eight shortlisted points, every normal magnitude is in `(1/4,3/4)`.
2. At latitude 3, longitude 4, the x and z magnitudes are in `(1/4,3/4)` and the
   y magnitude is in `(3/4,1)`.

These are conditions on the **actual normal floats**, not a claim that an
unexecuted platform produced particular bits. The ideal normal factors satisfy
the intervals with wide margins. For latitude 5, the angle lies between
`pi/4` and `pi/3`; both `sin(theta)/sqrt(2)` and `cos(theta)` lie in
`(1/4,3/4)`. Southern latitude 11 has the same ideal magnitudes. For latitude
3, `pi/6 < theta < pi/5`, so `sin(theta)/sqrt(2)` lies in `(1/4,3/4)` and
`cos(theta) > cos(pi/5) = (1+sqrt(5))/4 > 3/4`.

For any actual factor `a` in `(1/4,3/4)`, the exact product `r*a` lies between
`mu/2` and `3*mu/2`; rounding gives `mu`. For an actual factor `b` in
`(3/4,1)`, the exact product lies between `3*mu/2` and `2*mu`; rounding gives
`2*mu`. The strict intervals avoid midpoint ties entirely.

The eight shortlisted actual vertices therefore each have exact L1 sum
`3*mu`. The excluded latitude-3/longitude-4 vertex, index 69, has magnitudes
`(mu,2*mu,mu)` and exact L1 sum `4*mu`. The full maximum is at least `4*mu`,
so the shortlist's `3*mu` answer is wrong. Determining the full maximum is
unnecessary for this counterexample.

This is a conditional arithmetic counterexample. It becomes an actual
constructor witness whenever the generated normal floats meet the stated
intervals. It must not be labeled an executed request, a measured failure, or
a proof of any exact platform's transcendental results. It also shows why a
proof based solely on accurate ideal trigonometry cannot cover all positive
native radii: ordinary final-coordinate underflow can reverse the ordering.

## The source radius domain does not exclude the witness

The witness is not dismissed by the actual authoring rules:

- Core language section 5.2, lines 227–235, explicitly allows finite positive
  subnormals down to `2^-1074`, with an underflow warning.
- `values.py` 243–258 converts to finite binary64 and warns for subnormal
  results; it does not reject them. Lines 329–347 permit exact decimal
  quantity literals within a 4,096-character/exponent budget. The exact
  finite decimal expansion of `2^-1073` fits those limits.
- `validator.py` 850–866 requires only a positive visible `sphere` radius.
  The additional positive-inertia check applies to `sphere_body`. A visible
  sphere can use `no_body`, so inertia underflow is not a lower bound on its
  visible radius.
- `geometry.py` 50 rejects nonfinite or nonpositive radius, neither of which
  applies. `scene.py` 95–103 accepts finite binary32 conversion, including
  conversion to zero. The cold reader compares those exact stored zeros and
  retains the tiny source-coordinate error (`reach_conformance.py` 819, 838–847).

These observations establish that the selected radius is authorable and is
not excluded by the inspected radius/conversion gates. No complete source
program or end-to-end export was executed, and no claim that every later
request gate passes is made.

## Evaluation order and possible alternative

For a proved shortlist, computing its entries only at their original traversal
positions would retain the order of supplied-vertex validation. Computing a
future shortlisted exact value at entry would move its arithmetic before
earlier vertex checks. Native-domain checks, callback behavior and first-error
preservation remain separate obligations; mathematical equality is not enough.

A different source-only possibility is an actual-vertex lower witness:
derive a conservative lower bound from one immutable future source vertex,
then use it to screen earlier candidates while still validating every vertex
in order and exactly evaluating that witness at its original position. Its
mathematical safety would depend on an actual retained vertex, not an ideal
trigonometric maximizer, so the underflow counterexample would not apply in the
same way. This is a new hypothesis only. Selecting, binding, funding and
preserving first exceptions around that future witness are unresolved, and
no performance claim or authorization to execute it follows from this review.

## Finite finding

The unrestricted eight-point ideal-lattice shortlist has an unclosed
underflow case and no current source-bound rounding certificate. It is not
ready for implementation. A normal-radius restriction with an adequately
certified coordinate enclosure could support the eight-point mathematical
claim, but is not yet a complete optimization. Other finite sets, dynamic
source-bound witnesses and other restricted schemes are not disproved.

No new product success, runtime improvement, operation saving, benchmark result
or release acceptance is established by this source review.
