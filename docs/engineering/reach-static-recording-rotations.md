# Exact static rotations within one recording traversal

## Scope and status

This candidate starts from `115adf5cfb528f65b5ccf9a2640f01b39486d029`.
It extends the existing per-traversal orientation-recipe index in
`ReachSimulator._resolve_kinematics` to a narrow ordinary exact recording
case. It does not reuse a full source pose as a recorded pose, replace the
binary64 captured sampler, or add a numerical cache.

The candidate contains code, this derivation, and 18 dedicated test
methods. They have not yet been executed. P23 still needs an original-setting
recording run, the coordinator must check the integrated 28-recording suite,
and all outstanding release gates remain open.

## The repeated calculation

P23 has 32 translated copies of the same two-hinge arm. After the reach
actions complete at two seconds, their actual coordinates are fixed. The
ordinary recording traversal still obtains a complete private body rotation
for each upper arm and forearm. The existing bounded pure seed cache can
reuse identical numerical seeds, but each occurrence rebuilds its complete
ancestry key before that lookup. It also creates a separate body cursor even
though the proved body rate is exactly zero.

The traversal already contains the earlier occurrence's required actual
pose. A structural recipe can identify its complete orientation calculation
without retaining another computed rotation. Translations and identity names
are absent only where the existing `_recording_orientation_recipe` proves
that they do not enter the ordered orientation calculation. Joint axes,
constant actual/ideal coordinates, child-site rotations, root rotation,
root error, frozen projection, mode and ancestor recipes remain present.

The static case requires native `_ReachRunState` and `ReachPoseOps`, empty
native claim and dynamic tables, the full existing 32,768-bit arithmetic
domain, an opaque recorded-phase context, an admitted angular proof, native
zero rates, and unchanged native dispatch. It admits no action law, free
trajectory, approximate zero, full-source pose request or strict ordinary
recording request without a phase context.

## Exact equality argument

For an admitted zero-rate body law, the ordinary cursor either evaluates its
complete captured source seed or returns that same seed without a quaternion
increment. Empty claims and dynamics make the complete orientation operands
independent of the sampling clock. Equality of the complete structural recipe
therefore identifies the same ordered source operations and the same private
result. It preserves every quaternion component, the accumulated angular
error and any frozen projection; no projective normalization or new
approximation is introduced.

A successful earlier required body pose supplies the representative only
when its direct seed completed in this traversal. A warm cursor without a
new direct seed retains the ordinary path; it does not obtain a new source
provenance receipt merely because its final quaternion is equal. Its
exact `RotationValue` is copied into fresh Fraction wrappers. The current
occurrence still rounds its own actual parent origin and constructs its own
`RecordedTransform` through the original operations. Thus translated arms
retain distinct world origins. The optimization never substitutes one arm's
pose or position for another arm's pose.

The distinction between full source and recording composition matters.
Recording identity elision and frozen projection rules can produce a
different private quaternion from a superficially equal full-source pose.
Only a representative produced by this same ordinary recording traversal is
eligible. The existing native binary64 sampler retains its separate recipe,
enclosure and source admission path.

## Admission and mutable-wrapper boundaries

Each fixed-size source witness is type-checked against its actual current
source with bounded tuple/int/string/None traversal. This prevents Python's
boolean/integer value equality from admitting a malformed frozen scalar.
The index freezes exact zero-rate integer operands instead of retaining a
mutable Fraction in its structural key. Each record receipt retains the
actual proof record, parent, immutable witness, rate wrapper and integer
pair, axis, trig count and proof token.

The numerical receipt binds the representative's actual frame entry,
`RecordedTransform`, native arithmetic owner, exact `RotationValue` and all
five Fraction numerator/denominator pairs. Native finite frozen-projection
floats are fingerprinted by their hexadecimal strings, preserving zero
signs. These completed fields have a sufficient 512-bit optional domain;
larger values retain the ordinary path. Source clocks have the same optional
width ceiling, proving the omitted original rational comparisons fit the
unchanged full domain.
The structural index includes only the clock's captured integer pairs;
it never hashes a live mutable Fraction wrapper as part of that index.

The current source ancestry is checked completely before using the copy.
The representative's direct seed consumes a private native copy of that
ancestry and the exact clocks. Its typed immutable witness tuples are copied
from the admitted node receipts, and its Fraction wrappers are detached.
The view delegates no model/state reads to live inputs. Consequently a
callback cannot temporarily replace a live proof record during decoding and
restore it before the final receipt while contaminating the representative.
The numerical fingerprint is captured immediately when that detached seed
returns and must still match when its original body construction completes.

Every original per-occurrence ancestry guard charge remains, one callback
at a time. After each such callback, the candidate rechecks the work,
callback, model, state, arithmetic dispatcher, proof map, phase clocks,
operand cap, cache capacity and numerical representative. An observed change
permanently invalidates sharing for the rest of this traversal. A later
callback cannot restore a previously declined receipt.

The borrowed numerical operands are detached before its first callback.
The original origin/grid/transform callbacks then execute. A final receipt
checks the representative and current complete source chain before the
occurrence enters the actual graph. If those callbacks invalidate the
receipt, that occurrence executes the original body orientation and origin
construction instead. Cancellation propagates through the same work context
with the caller's original exception identity.

Changing a live proof record to an equal replacement also declines the
structural index. Equality of final numbers does not authorize a changed
proof owner. Full source admission and the ordinary seed decoder remain
responsible for malformed or unsupported source inputs on fallback.

## Space and work bounds

The index is local to the already-required graph traversal. Each entry
points to an existing required pose and stores only structural/result
fingerprints; it retains no extra computed numerical result. It admits at
most the current existing cache capacity, never more than 256 distinct
representatives. Witnesses retain the original 512-node, eight-level,
32-item-per-tuple bound. The optional proof has at most 4,096 frame records,
and final source-chain receipt walks stop at 64 ancestors. All original
source graph, numerical cache and keyframe limits remain in force.

The optimization removes actual cursor construction, repeated frozen-source
decoding/key construction, numerical cache lookup/publication and any
duplicate seed arithmetic. It continues charging actual structural witness
blocks, recipe construction, each attempted shared result and every original
source record guard. Source arithmetic performed on ordinary fallback is
charged normally. No completed arithmetic is relabeled or refunded.

Native arithmetic dispatch is compared through the raw class dictionary,
including its original storage descriptors and true absence of custom work
descriptors. This handles native staticmethod wrappers without invoking an
untrusted descriptor during admission. An instance override also declines.

In the original P23 shape, at most 62 of 64 complete body seed paths can share
the two representative recipes. Static inspection suggests about 2,000
avoided operations at the first static key, before approximately 550 new
once-per-node recipe/witness admissions. This is an estimate, not measured
evidence; cache hits, evictions and source wrappers affect the actual result.
The dedicated complete-graph test prints matched ordinary/shared operation
counts and direct-seed counts. Any full recording benefit must be measured
at the unchanged 100,000-operation cap, including later certificate and
independent validation costs.

## Focused verification

`tests/test_reach_static_recording_rotations.py` compares against the unchanged
ordinary algorithm by disabling only the new structural admission predicate.
The cohort covers the full original P23 static graph, repeated clocks, exact
private/public/frozen values, fresh numerical wrappers, independent translated
origins, changed coordinates and child rotations, moving/dynamic exclusion,
strict/full-source exclusion, custom dispatch, narrowed/restored caps,
representative mutation at early and late callbacks, proof record replacement,
boolean-aliased source scalars, cancellation and nested same-request sampling.
It also includes a transient proof replacement with the original live decoder
as an explicit negative control for the private detached source view.

Broader recording-sampler, captured-chain, body-cursor and proof tests must
also remain green before integration. A saved original P23 recording attempt
must report its actual completed stage and counters even if the cap still
blocks completion. This candidate does not close any acceptance gate by
itself.
