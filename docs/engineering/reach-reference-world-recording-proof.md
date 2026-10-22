# Independent complete-carrier interval recurrence

This derivation describes the optional ideal recording path in
`ontokin/reach_reference.py`. It supplements the independent local-angle and
[fused interval product derivation](reach-reference-fused-recording-proof.md).
It is a reader proof, not a production numeric allowance or a release result.
No test result is established by this document.

## Source authority and domain

The independent reader captures constructed source records and reconstructs
their action clocks, selected targets, boundary states and ideal affine laws.
It imports no production simulator, phase planner, sampler, certifier or pose
kernel. An explicit reader-owned recording context may reuse a complete ideal
carrier orientation only when that source reconstruction proves a constant
signed body-frame angular rate on one Cartesian axis.

The optional path requires the existing 128-bit interval grid, the full
32,768-bit operand domain, and a shared work object preserving callback error
identity. Other precisions and smaller live domains retain ordinary evaluation.
Full source observations, actual canonical poses, velocities, release anchors
and event construction do not use this recurrence. In particular, the ideal
affine coordinate is evaluated without the canonical source's binary64
coordinate rounding. The separate existing source-numeric allowance continues
to cover the distinction between that mathematical ideal and canonical source
evaluation; this change neither enlarges nor removes it.

The recurrence replaces a proved prescribed root spin, or a hinge carrier
whose child-site translation is exactly zero. The root's prescribed world
translation has no orientation operand and keeps its ordinary expression.
Every other position composition remains in the ordinary independent graph.
Dynamic roots and unproved angular paths retain the previous local-angle/direct
evaluation.

## Independently proving the body rate

Write a mathematical unit world quaternion as `Q(t)` and a body-frame angular
vector as `w`. A constant body vector gives

```
Q'(t) = Q(t) * (0,w)/2,
Q(t) = Q(s) * R(w*(t-s)).
```

The reader obtains `w` from the following source rules.

* A prescribed fixed orientation, or a paused orientation action, has zero
  rate. A dynamic root has no optional rate proof.
* A running root spin qualifies only when its exact source vector has one
  nonzero Cartesian component, its independent anchor rotation error is zero,
  and its fixed initial orientation exactly preserves or reverses that axis.
  Conjugating the world spin vector into the initial body frame then gives its
  signed constant body rate. Uncertain transferred anchors are excluded.
* A fixed attachment transports the parent's body vector by its inverse
  rotation. A nonzero quaternion preserves axis `k` if both other imaginary
  components are exactly zero. It reverses that axis if its scalar and `k`
  components are exactly zero. These predicates survive normalization; the
  inverse rotation has the same sign on a preserved/reversed axis. An interval
  merely containing zero is not an exact zero.
* A hinge qualifies only for an exact source axis `+/-e_k` and a parent whose
  body rate is zero or parallel to `e_k`. Its independently computed affine
  slope adds with the source axis sign to the parent's signed rate. The fixed
  child-site inverse then transports the combined rate into the carrier body
  frame. Sliders and fixed joints add no angular contribution.

For parallel parent and local hinge rates, the local hinge rotation commutes
with the parent's angular vector. Therefore the usual composed body angular
velocity is precisely their signed sum. Nonzero contributions may cancel;
their complete world orientation is then constant even while parent offsets
move. A wholly stationary chain needs no cursor.

Unknown, oblique, noncoaxial or nonunit source-axis cases use the original
independent graph. These rules are derived again from reader source records;
production `RecordingAngularProof` records are never inputs.

## Exact quaternion interval update

Each cursor starts with the original context-free independent orientation
equations at its actual seed clock. An immutable recipe holds each admitted
root orientation/spin, fixed quaternion, hinge axis and affine coordinate law.
The direct recipe evaluates the same normalized source quaternions and ordered
Hamilton products as the ordinary graph, without computing unused seed
positions or derivatives. It bypasses complete frame maps and all ancestor
recording cursors; existing pure numeric caches remain keyed by actual
operands. Its rate and direct seed therefore describe the same captured source
curve even if a cancellation callback temporarily changes a private source
record during arithmetic.

A fixed source quaternion with positive scalar component and exactly zero
imaginary components normalizes to the exact positive identity. After a fresh
charged admission of all raw components and parent interval endpoints, its
normalization, optional conjugation and identity product can be omitted. A
negative scalar quaternion keeps the original path and representative sign.
An affine law with identical admitted initial and target values has exact zero
slope; it still checks the original subtraction preflight and nonzero-duration
domain before omitting its unnecessary numeric lookup and arithmetic. Combining
that zero rate with a guarded parent rate merely selects the nonzero operand;
two nonzero rates still require their original charged exact addition.

For a Cartesian body rate `r`, let `sine` and `cosine` enclose the sine and
cosine of the exact half-increment `r*(t-last)/2`. With quaternion order
`(w,x,y,z)`, a right Hamilton product is two independent pair updates

```
(u,v) -> (u*cosine + v*sine, v*cosine - u*sine).
```

| Body axis | First pair `(u,v)` | Second pair `(u,v)` |
| --- | --- | --- |
| X | `(x,w)` | `(y,z)` |
| Y | `(y,w)` | `(z,x)` |
| Z | `(z,w)` | `(x,y)` |

The existing independent sine/cosine series encloses the exact increment.
Each pair uses the existing exact interval-product extrema and outward final
grids. Exactly zero pairs stay exactly zero; an uncertain zero does not take
that shortcut. At zero combined rate, the previous complete enclosure itself
is valid. The interval box need not consist of unit quaternions: it encloses
the same mathematical unit quaternion established by the source walk, and
ordinary interval multiplication encloses that quaternion's exact update.

The cursor permits at most 64 successive interval updates and only a
half-increment of magnitude at most `1/4`. A missing or evicted entry, repeated
or reversed clock, changed source receipt, new context, changed semantic phase
or side, larger increment, or exhausted update count starts a new direct seed.
A later seed replaces the old enclosure; it does not accumulate another
seed's error. This is an exact outward interval construction, so no extra
floating discrepancy or endpoint tolerance is introduced.

## Position enclosure

For a prescribed root, a `move` action supplies a world translation independently
of a `spin` action's orientation. The ordinary translation, velocity and unused
recording derivative values are evaluated unchanged before the root cursor.
The cursor's final source receipt admission therefore occurs after translation
callbacks, and no translation callback follows orientation publication inside
that root evaluation. Original translation and direct-spin arithmetic failures
remain outside the optional increment's changed-domain retry handler.

At a hinge with zero child-site translation, both the hinge motion and the
fixed child-site inverse have zero local translation. Its exact carrier origin
is consequently the parent-site origin. The new result retains that existing
independent parent position enclosure directly. Fixed/site/follow offsets still
use the original independent quaternion-vector interval expression. If several
ancestors have different seed clocks, each independently encloses the correct
ideal orientation at the current clock. Composing these interval enclosures
therefore encloses the same ideal position without correlating or equating
their seeds. No production position or source error bound is used as an oracle.

## Fresh receipts, finite work and failure behavior

The current frame walk rebuilds a bounded immutable ancestry witness. It
includes root mode/orientation and active spin data; fixed attachment poses and
parent identities; hinge topology and exact axes; action identity, coordinate
index, duration, initial values, targets, elapsed/since clocks and running
status. Only small exact rational/integer leaves, finite binary64 values,
immutable interval cells and bounded tuples enter the receipt. Source changes
cannot inherit a preceding orientation merely because the clock or carrier
name matches. Complete recording frame maps cannot bypass this fresh walk.

Each capture's charged callback occurs before reading its operands. The direct
orientation recipe uses those immutable operands throughout, including the
independent affine-law clock, rather than rereading mutable action records.
Before cursor publication, one charged admission is made for every source
record in that ancestry. The current records are then checked atomically after
the insertion callback and before insertion, with no intervening callback. A
persistent source mismatch rejects the sample without replacing the old
cursor. A source mutation that is restored during arithmetic cannot poison the
entry, because neither its direct seed nor its rate read the temporary values.
The same current-source check covers a direct fallback result. These source
receipts are ephemeral getters/snapshots; only their immutable witness and the
completed orientation/clock enter the existing cache.

These temporary rate/witness maps belong only to that frame evaluation. Each
completed cursor occupies one entry in the existing independent arithmetic
cache, whose unchanged maximum is 256. There is no second retained numeric
cache, extra operation budget, hidden counter adjustment or fixture exception.

Every remaining exact rate sum, difference, clock difference, multiplication,
division, series operation, interval product and final grid remains charged
through the existing arithmetic. Charged source-record admissions and cache
lookups/inserts remain cancellation points. Current-domain checks follow their
callbacks. Optional rate and clock operands are at most 1,024 bits; their added
delta preflights and grid widths are below 4,096 bits, within the original full
domain. Larger inputs keep direct evaluation. Fixed binary64 zero predicates
need no new numerical product, division or normalization, and every finite
binary64 component fits the full domain.

A narrowed domain returns to the direct current-domain path only for an added
proof's own admission failure. Callback exceptions keep their exact identity.
Original direct trigonometric or interval fallback failures are outside that
retry handler and cannot be retried into a later broader domain. Fresh guards
also cover a completed ordinary pose after any added source-proof callback.
An interrupted cursor update publishes no partial clock/orientation pair.
Other already completed pure numeric cache entries remain valid; source model
and action state are never changed by this optional proof.

## Verification scope

`tests/test_reach_reference_world_recording.py` specifies finer independent
enclosures on X/Y/Z, signed source composition, full position propagation,
restart schedules, eviction, changed source receipts at the same clock,
source mutation during admission, direct arithmetic and final publication,
semantic sides, unsupported source paths, live-domain changes, cancellation
identity, source-observation separation, and complete valid/forged GLB
equivalence with measured shared work. Existing local/fused/shared recurrence,
independent endpoint, forged-claim and source-reference cohorts remain relevant.
Executed results must identify the actual code revision separately; this
derivation does not claim that the complete recording or release gates passed.
