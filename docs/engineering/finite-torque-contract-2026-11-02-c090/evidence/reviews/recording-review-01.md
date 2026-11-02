# Independent recording review 01

Reviewer: root coordinator, independent of the recording author. Scope: the
proposed fixed-axis torque recorder, supplied-byte proof and controlled
destination contract. This is a design review, not execution of a torque source,
artifact, destination, or runtime implementation.

## Outcome

Changes required for one exact binding inconsistency. The closed
`recording-profile.schema.json` freezes `axis_domain` to `world.x`, `world.y`,
`world.z`, while the grammar, catalog and torque-state schema use `world_x`,
`world_y`, `world_z`. No separate translation is defined. Align the profile's
literal identifiers to the source/state identifiers before adoption, retain the
old schema as a preparation input, and identify the amendment by exact hashes.

## Continuous proof review

The source quaternion second-derivative estimate follows from differentiating
`q' = omega*q/2`: its norm is at most `Alpha/2 + Omega^2/4`.
The vector chord kernel contributes `h^2/8`, giving
`Alpha*h^2/16 + Omega^2*h^2/32`. The stored endpoint SLERP chord adds
`theta^2/8`; endpoint error adds `eq`. For `D <= 1/2`, the SO(3) discrepancy
is bounded by `4D`. The short-lift/travel guard is essential and is explicitly
retained; equal endpoint orientations do not establish a stationary interval.

The quarter-allocation integer counts correctly solve the stated inequalities.
In particular the positional count uses
`H^2*(A/2 + r*(Alpha+Omega^2))/position_tolerance`. Fixed-path marker origins
use `rho*(Alpha+Omega^2)` and `rho*Omega`, while local geometry/site landmarks
separately use radius `r` and native vertex error. Nested fixed offsets may use
their L1-radius sum. Treating `rho` and `r` as the same quantity would be unsound;
the contract correctly distinguishes them.

The authored smooth-phase chord proof and expanded stored-clock bounds have
different roles. The former stays inside one phase. Clock displacement is
bounded with enclosing speed over the adjacent phases, retaining after-state
transfer errors. The stored-width screen does not assume differentiability
across impulses. Upward publication and dependent recomputation retain every
source, endpoint, clock and destination term; conservative overlap is disclosed.

The canonical/reference acceleration difference and inherited full-vector
transfer uncertainty are retained. An underflowed canonical acceleration cannot
erase the reference angular error. The legacy-to-split source rule and direct
axis evaluation prohibit reusing an unproved constant-rate cursor.

## Actual implementation boundary

The pinned baseline identifies the actual reach exporter, independent reader,
phase/reference types, numerical helpers and destination. It correctly observes
that the existing controlled attachment admits only GLB/0.6. The separately
specified .22 wrapper imports its controlled sampler without rewriting artifact
metadata, retains old behavior, and requires an actual implementation hash once
that wrapper exists. No future hash or playback success is fabricated.

The independent reader's source/stream/clock/primitive order, complete
node-and-gap certificate coverage, current authority and final atomic
publication requirements are suitable implementation obligations. Historical
inactive grips do not create a false post-release composition refusal; a joint
remaining on an affected path is expressly outside this first proof domain.

## Reproduction and limits

Root separately ran the unchanged author's mathematical script: 3,485 exact
assertions passed. The source/schema derivation script passed 46 checks,
including all 18 pinned native files and modes, exact inherited certificate
fields and the two additive acceleration fields. These checks reproduce finite
design witnesses; the reasoning above is the review of the continuous proof.
The resulting JSON reports and exact reviewed input hashes accompany this
record. No production code was imported or executed by these checks.

Full JSON Schema validation, independently authored corpus coverage, actual
torque implementation, hostile supplied-byte execution, Agent stores, controlled
playback and complete release acceptance remain separately required.
