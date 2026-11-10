# C191 recovery: source, native authority and compatibility review

**Decision: accept the inspected C191 increment for development integration.**
The adopted finite source contract, native mapping and surviving qualification
artifacts agree with the actual implementation at
`2c140286a3b1ca0ef0d3b435f8280ccafaf03490`. No implementation repair is required
by this review. The coordinator must still record the actual main integration
and verify resulting-main input identity and applicable checks.

This is a recovery review of existing work. It adds no language decision, changes
no frozen expectation and makes no fresh Blender solve claim. All writes were
confined to the review directory. The repository and original evidence were
read without modification.

## Exact evidence

`implementation-evidence-audit.json` records a fresh, independent read-only
check of current code, source closure, saved native records and encoded X/time
tracks. Its SHA-256 is
`15c17f0ce9d27141793957d0d29b230dc95aed0e0fd116f2aa68eac24512fa12`.
The companion `audit_recovered_implementation.py` uses only the Python standard
library and does not import the adapter. Its SHA-256 is
`6f98859d1ee3e09f41a8d2973db1b54aba191d25e70c69c2885c4b5af0b9b4f8`.

The audit verified all **12,794 inherited tracked paths**, including Git blob
identity and mode, against C190 merge
`405422ba9e3de3b94258feaad742ede356d157f3`. None changed. It separately compared
the current eleven prototype Python files with the retained executed files in
each of **nine formal builds**. All 99 file comparisons matched. The recorded
implementation was `de813a652ab5380a9c96f2a72ad9bd9ce5bbb96e`; the later changes
through the reviewed head are evidence and documentation, with no runtime
change.

Every file in each formal artifact manifest was rehashed. Each saved-scene
replay's source and scene identities matched its originating build, and all
481 reopened native states were equal to the corresponding original states.
The nine original worker receipts report successful exit, no trusted test
hooks, factory startup and execution of the retained worker script. They are
actual native qualification attempts, distinct from failure-injection tests.

The adopted contract manifest remains
`bc85696002d641122322313cf5167f84eb1ae377599930112e3afd0f054b0137`.
Every listed contract file and the separately adopted C191-A1 source-admission
amendment match their published identities. Both archived evidence bundles
also match `evidence/native-qualification.json`:

| Archive | SHA-256 |
| --- | --- |
| `qualification-evidence.tar.xz` | `392cce364da6b4f589bd41c49076feac31792dbfb6c059d425488c9d56370495` |
| `author-recovery-evidence.tar.xz` | `0b071b12330601ca51cd312cac0fb7d5f8c3a7afca7c2b8f2ee3b52d924a523f` |

## Source ownership and finite boundary

The source uses explicitly selected bindings:
`c191-experimental-0.1`, `guided-box-contact-0.1`,
`blender-bullet-c190-0.1` and `glb-guided-contact-0.1`.
Its entry point is `python -m prototypes.guided_contact_v01`. It introduces
no Agent binding and does not alter the original `.22` parser or default CLI.

The source parser admits literal declarations for the fixed seven-part gauge,
two mass-owning carriage bodies, four shoe/stop collider identities and two
massless spatial follow relationships. Stable `@` keys control references and
mapping. Labels and declaration order remain outside canonical physical input.
The allowed physical edits are the left-stop X coordinate within the adopted
range and the left-shoe collider's enablement. All other dimensions, feeds,
mass values, rotations, guides and contact laws remain bounded by the sealed
source schema. This is deliberately a finite experimental language path.

Code inspection confirms that source byte and token admission is bounded,
units and literal types are checked, ownership and motion authority are
validated separately, and initial positive-volume overlap rejects before
native construction. Source spans and exact revision identities are retained.
The only pre-admission exception is the separately adopted oversized-source
rule, which correctly reports no full-source hash from a bounded prefix.

## Native construction and motion authority

`native_worker.construct` starts with an empty factory scene. It does not load
C189/C190 scenes, hidden source assets or expected trajectories. All visible
box dimensions, colors, initial placements, follow offsets, masses and feeds
come from canonical source. The pinned backend supplies the declared helper
construction and numerical settings.

The source-to-native map is `(x,y,z) -> (x,-z,y)/1000`. Mesh origins are centered
from source minimum-corner boxes. A shoe's centered local offset is derived
from its follow offset and the two box centers. Hidden carriage boxes copy the
corresponding centered source mesh at the compound parent's identity frame.
The left-stop driver derives its half-width from source. The source and native
body frames therefore have explicit, verified meanings.

The independently rechecked saved configuration has exactly thirteen native
objects: seven visible solids, two hidden carriage boxes and four constraints.
Only the two carriage roots are independent active COMPOUND bodies. Each owns
1 kg; the mapping's mass contributions sum to 2 kg. Compound child rigid-body
mass fields are not counted as independent mass owners. Case D lacks only the
left-shoe collision component while retaining the visible child and its parent.

Each native GENERIC constraint leaves X unbounded and locks Y/Z and rotation.
Each MOTOR reads only its own carriage's source feed, requests `-feed/1000`,
and retains maximum impulse 100000. There are no carriage, shoe or proxy
transform actions or transform drivers. Both lanes meet their source feed in
the first recorded interval. The worker's capture loop only advances frames
and reads evaluated poses; it contains no stopping time, distance clamp or
expected-outcome table.

The saved configuration retains 240 Hz recording, ten substeps per frame,
100 solver iterations, zero gravity/friction/restitution/damping/margin, the
measured collision group and base/carriage suppression. It does not claim an
exclusive four-native-shape scheme. The finite motor impulse is not a
calibrated force model.

## Encoded motion and evidence limits

An independent binary decoder compared every active raw/final animation input
time with the binary32 encoding of the corresponding native recorded time.
It compared every carriage X entry with the binary32 encoding of the native
matrix X entry. All nine builds matched exactly. Final channels retain only
translations, with the same visible identities, hierarchy and source geometry
metadata. Code inspection confines final projection to removing rotation
channels and fixing transverse translation to its initial values; it cannot
create the stopping response on X.

The A/D native control preserves every recorded base, left-stop and right-lane
matrix and bound while left travel changes from approximately 200 mm to
250 mm. This supports the stated collision mechanism independently of final
playback. Physical tolerance and continuous interval certification remain the
independent fixture review's domain. The recovered qualification record gives
a maximum raw/final continuous mapping bound of 0.085188226 mm, below 0.2 mm,
and positive playback penetration at most 0.011957251 mm, below 0.5 mm.

The runtime checks native configuration and recorded matrices before export,
validates the complete saved-scene file envelope, and enforces the declared
source, step, object, sample, output, deadline and cancellation limits. State
publication has one atomic pointer replacement. The recovered source,
lifecycle, native-artifact and output-alias audits retain the failures observed
before the already-published corrections. Their successful reruns apply to the
same runtime bytes inspected here.

Native direct velocity, Bullet manifolds/impulses and unrecorded substep poses
remain unobserved. Saved-scene semantic reopening is separate from the
adapter's bounded file-envelope check. GLB is recorded playback. No general
contact, live destination physics, production backend, comparative authoring
benefit or full-project completion follows from this finite qualification.

## Integration classification of the inherited torque failure

OK-ENG-009 section 3 requires actual regression evidence and explicitly
distinguishes an unchanged failure in a correctly contained incomplete feature
from a newly introduced regression. C191 changes no legacy runtime, tests,
shared validation driver, package metadata or hosted workflow. The cumulative
inherited-path check above proves that isolation at the reviewed head. The
coordinator additionally compared actual main
`ec5c1fd3299dd915e6ef5d68944b3955978f3eb1` with the candidate across those paths;
the diff is empty.

The recovered complete discovery run remains **FAILED**: 4,239 test methods
passed with zero skips, while `TorqueArtifactReadTests.setUpClass` failed before
its thirteen `.22` artifact-read methods ran. Its unchanged A08 seed export
reached the original 30,000 ms limit. The thirteen methods are **NOT RUN** and
are not counted as passing or as covered by C191's new tests. The full driver
and finite-torque release are not declared passed.

The coordinator reproduced the exact setup failure on both reviewed candidate
and actual-main baseline using the unchanged test, same CPython 3.12.14 and
original budgets. Both receipts retain `OKL-E-RESOURCE`,
`execution_deadline_exceeded`, stage `recording_export_readback`, implementation
identity `3e6ef2df6a7e8837050abb949075bff9b65f6a4aa4a9f1587850d7ddd59bce56`,
program revision `b54065f44f34220abef40fa4615a12deb6ad11b7f0e613e4903b35bd7a68b8d7`
and entry revision
`435c772d86ae9d43779d4a924daa9e4a287e55163a5c08cc655ed5c4e72d9a54`.

| Actual rerun | Retained log SHA-256 |
| --- | --- |
| Candidate `2c140286` | `a4fbbf80dbc3c63cebeaab2d2d8c3fe4de038814f9aaf8776432cebd27e3246a` |
| Main baseline `ec5c1fd3` | `f2c43877eefdf0bc810f226d2b2b83b9ff5c9bf8673716511b90bd2c0fe3ef35` |

This evidence supports classifying the failure as unchanged and contained in
the already incomplete `.22` torque path. It does not establish performance
equality from two elapsed-time observations. No budget, fixture, assertion or
release gate was changed. Under the adopted policy, that accurately retained
failure does not block this unrelated, explicitly invoked C191 increment once
the coordinator completes the remaining integration checks. It remains an
open `.22` obligation.

The existing local conformance run also retains sixteen pending external roles
and its single-interpreter limit. These are not silently promoted to completed
release evidence. C191 can be integrated development while those independent
release obligations remain visible.
