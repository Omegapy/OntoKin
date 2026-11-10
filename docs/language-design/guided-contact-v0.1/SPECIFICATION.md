# C191 finite guided-contact contract, version 0.1

**Draft for explicit adoption. No runtime capability is claimed by this file.**
The coordinator's adoption receipt and the independent input freeze make the
identified bytes effective before implementation. Later corrections require a
separate amendment; prior inputs, failures and results remain preserved.

## Bindings and compatibility

| Surface | Exact binding |
| --- | --- |
| Experimental source | `ontokin "c191-experimental-0.1"` |
| Profile | `guided-box-contact-0.1` |
| Backend | `blender-bullet-c190-0.1` |
| Recorded output | `glb-guided-contact-0.1` |
| Invocation | `python -m prototypes.guided_contact_v01` |

This is a separately invoked, finite declarative `.ok` prototype. It reuses
OntoKin's readable unit literals and stable `@` keys but does not inherit the
existing parser, classes, functions, imports, Agent interface or physical
constructors. The original source `0.22`, `torque-0.1`, Agent/0.22, GLB/0.22,
defaults, contact rejection and pass-through fixtures remain unchanged. A new
experimental source sent to the old parser is unsupported. There is no new
Agent binding. This contract qualifies only the seven-part C190 assembly.

The normative grammar is [GRAMMAR.ebnf](GRAMMAR.ebnf). The normalized literal
model is [source.schema.json](source.schema.json). The exact backend mapping and
resource limits are [backend.json](backend.json); result fields and diagnostics
are [output.schema.json](output.schema.json) and
[diagnostics.json](diagnostics.json). The strict native worker envelope is
[native-result.schema.json](native-result.schema.json). The examples are editable source inputs,
not native `.22` programs.

## Source ownership and admitted model

An immutable UTF-8 `.ok` revision owns geometry, colors, local frames, attachment,
two masses, four contact-box dimensions and offsets, feeds, initial state,
collision enablement and left-stop placement. No external imports or assets are
allowed. Its dependency closure is the exact adopted grammar, schemas and
backend mapping; each file is SHA-256 identified. Generated Python maps these
declarations and never supplies an undeclared geometric or physical design
constant. Source SHA-256 and closure hashes accompany every attempt.

The scene contains exactly these stable visible-part keys: `base`,
`left_carriage`, `left_shoe`, `left_stop`, `right_carriage`, `right_shoe`,
`right_stop`. Names preceding `@` are labels; rename and declaration reorder
have no effect on semantic identity or mapping. Every declaration key is unique
across part/body/collider/follow namespaces. Native names and GLB node names use
stable keys. Occurrence identity is `(module_key, scene_key, declaration_key)`;
revision identity is recorded separately. A label or source-line change cannot
reattach a collider.

`part` declares `box`, `color`, `rotation`, and, for a root part, `at`. Box and
placement vectors have unit `[mm]`; color is unitless linear RGBA; quaternion is
unitless `[w,x,y,z]`. Geometry has a minimum-corner source origin. A followed
shoe has no independent `at` field. `follow` declares `parent`, `child`,
`offset[mm]` and identity `rotation`. This relationship is a massless, rigid
spatial attachment only. It supplies no force-bearing joint. Each shoe has one
follow parent, its matching carriage, and no body declaration.

`body` declares `part`, `mass[kg]`, `authority`, `guide`, `feed[mm/s]` and
`initial_velocity[mm/s]`. Only the two matching carriage bodies exist, with
stable IDs `body.left` and `body.right`, mass 1 kg each, `authority="solver"`,
`guide="world_x"`, initial velocity `[0,0,0]`, feeds 125 and 150 mm/s respectively.
At modeled t=0 the solver owns the carriage pose; the constant native motor
requests its feed from the first step. No handoff or pre-roll occurs. A motor
target is not a transform driver and is not a calibrated force promise.

`collider` declares `part`, `owner`, `shape`, `box[mm]`, `offset[mm]`, `enabled`,
`friction` and `restitution`. Four stable collider IDs identify the two shoes and
two stops: `contact.left_shoe`, `contact.left_stop`, `contact.right_shoe`,
`contact.right_stop`. Each shoe collider has exactly one owner, its carriage body
ID. Stop colliders have owner `world` and no moving mass. The box matches its
visible part, with zero local offset. The source can disable only the left shoe
collider. Its identity and visible attachment persist when its native collision
component is absent. Friction and restitution are zero. Source ownership and
spatial following are checked independently.

The exact dimensions, initial placements, follow offsets and colors are in the
source examples and schema. Only the left-stop world X coordinate may vary in
the inclusive range 200–495 mm. Only the left-shoe collider enablement may vary.
Labels and declaration order may vary. This finite scope deliberately rejects
all other design edits pending a new qualification. Initial positive-volume
overlap rejects before native construction; touching faces are permitted.
Rotations must be identity and gravity must be zero.

## Canonical input and identity mapping

The canonical solver JSON is the validated normalized source model, sorted by
stable declaration key, with labels, source spans and source revision omitted.
It includes every admitted source field, the four bindings, module/scene keys
and adopted backend content hash. JSON uses sorted object keys, compact
separators, UTF-8, finite JSON numbers and a trailing newline. Equivalent label
renames/reorders therefore have identical canonical solver-input bytes.
The separate source manifest contains original source bytes/hash, labels,
spans and all dependency hashes. Neither file substitutes for the other.

Each mapping row identifies source occurrence/revision, body ID if any, collider
ID if any, visible-part key, native object, native body parent, native shape,
mass contribution, initial source frame and the explicit source-to-native
frame transform. Disabled contact shapes remain rows marked `native_absent`.
Hidden helpers have their own mapping rows and a source derivation. They never
become independent moving mass owners. Count total moving mass as 2 kg.

## Native construction and solver boundary

`backend.json` enumerates two active COMPOUND carriage parents, two source shoe
BOX children (one may be disabled), two hidden carriage BOX children, two passive
stop boxes, one passive base box, two GENERIC guides and two MOTOR constraints.
Only seven solids are visible. Native child rigid-body mass fields remain the
measured C190 value 1 kg but are ignored as separate mass owners by the compound
construction. The owning carriage's 1 kg mass is the only moving mass per lane.

Construct a fresh empty scene from source on every build. Do not open the C189 or
C190 `.blend` as a design input. The C190 build and audit remain historical
evidence for this construction. Native helper geometry is derived only from
the declared carriage or base box. Explicitly set the measured defaults; do not
invent exclusive pair filtering or a four-native-shape engine.

The source frame is right-handed, +Y up, in mm. Blender is right-handed, +Z up,
in m: `(x,y,z)_source -> (x,-z,y)_Blender / 1000`. A part's centered native mesh
origin is source minimum corner plus half its box dimensions. The carriage
body frame is this centered visible carriage frame. A shoe's centered native
local origin is `follow.offset + shoe.box/2 - carriage.box/2`, transformed by
the same axis/unit map. Stop center X is `at.x + box.x/2`; its static property
driver uses this declared half-width, never an independent 15 mm constant.

Each guide has native object1=base and object2=carriage, X unbounded, Y/Z and
all rotations locked, with collisions between the constrained objects disabled.
Each motor has the same ordering, target `-feed_mm_s/1000`, maximum impulse
100000, and an own-carriage speed-property driver. There are no carriage or
shoe transform drivers/actions. Collision groups are the measured Blender
default group 1 for all bodies, not exclusive matching-pair masks. Margins,
gravity, friction, restitution and damping are zero; deactivation is off.

The pinned world uses 240 frames/s, 10 substeps/frame, 100 iterations, time scale
one and split impulse. The nominal step is 1/2400 s. Frame 0 contains the initial
pose, followed by 480 sequential frame advances through 2 s. Record all 481
evaluated world matrices. First-interval feed must meet the frozen speed gate.
Native Bullet manifold/impulse and direct velocity telemetry are unavailable
through this interface. Report finite-difference velocities and geometric gap
flags as derived measurements, never as solver contact records.

Save the editable unbaked `.blend` before capture. A separate fresh process must
reopen that file, validate persisted settings and identities, clear native
caches, start at frame 0 and repeat capture without reconstructing or repairing
objects. Reopening is a separate attempt with the same limits.

## Raw and final recorded output

Use a finite captured-pose GLB encoder, identified by the new output binding.
It does not trigger a second native simulation or reinterpret an old GLB
profile. Geometry and colors come from source; raw animation comes from the 481
native captures. Time keys are the float32 encodings of `frame/240`. Each
carriage translation X is exactly the float32 native Blender matrix X entry,
with no retiming, interpolation, stop schedule or replacement value. All raw
matrix records retain the complete native floats. The source/Blender/glTF axis
mapping is explicit; quaternion conversion uses that basis transform.

The raw GLB uses seven stable-ID nodes, centered box geometry, one carriage
translation track per lane and native rotation tracks when nonidentity. Shoe
nodes remain children with constant local transforms. All tracks have the same
481 float32 times and LINEAR interpolation (SLERP for quaternion playback).
The final projection may remove active carriage rotation channels and replace
transverse translation values with their initial values. Nothing else changes
semantically. Retain unused rotation data and list each changed JSON field and
each changed binary float. Raw/final X bytes, input-time bytes, meshes, colors,
hierarchy, fixed transforms and shoe-local transforms must be identical.

Independently compare all native-record vertices with final vertices and all
raw/final sample vertices. For each playback interval, use the C190 conservative
rotation/translation bound: maximum endpoint transverse displacement plus
`2*r*sin(theta/2)`, where theta is the smaller endpoint orientation distance to
identity plus the endpoint quaternion arc, capped at pi. The maximum native
sample and continuous raw-playback deviation must be <=0.2 mm. This bound does
not claim unrecorded native substep accuracy. A projection cannot create the X
stopping response.

Positive cases require <=0.5 mm near-face penetration throughout all 480 final
interpolation intervals. All cases require continuous nonoverlap of the twenty
unrelated visible-solid pairs; the left shoe/left stop is the separate intended
pair and is allowed to pass through in the disabled control. Independent
expectations retain 25 ms settling, <=0.5 mm/s residual speed, <=0.1 mm rebound,
the other C190 proposal tolerances, and exact unaltered historical tests.

## Budgets, failure and atomic state

Absent an execution block, ordinary limits are 100000 operations and 30000 ms.
Qualification sources explicitly request 1000000 operations and 80 s. The host
must separately authorize ceilings at least as high; never silently clamp a
larger source request into a success. The attempt clock covers source checking,
native worker, encoding, validation and publication. Each loop over source
tokens, model fields, pair checks, native scheduled substeps, recorded matrix
scalars and encoded/accessed scalar values charges the operation counter; log
component totals. Check the deadline and cancellation at these boundaries.

Hard caps are 65536 source bytes, 8192 tokens, 15 declarations, 13 native objects,
9 native rigid-body components (8 when disabled), 481 native capture states and
4800 scheduled native substeps per worker. Native trace/result bytes <=16 MiB,
captured stdout/stderr <=4 MiB total and total staged output <=64 MiB. Fail on
excess; report actual measurements. The supervisor polls <=50 ms, terminates the
entire process group on cancellation/deadline/resource breach, waits <=500 ms
then kills it. Qualification requires observed cancellation completion <=2 s.
Do not claim direct visibility into Bullet's internal substeps; 4800 bounds the
configured and commanded advances. No uncapped exporter replay is permitted.

The CLI offers `validate` (read-only) and `run` (one atomic source/build/output
transaction). `run` stages into a fresh directory on the store's filesystem.
It validates all native result fields, finite numbers, exact 481 frame/time
sequence, known seven IDs, affine matrices, persisted configuration, source
hash and artifact sizes before publication. Unknown/duplicate JSON fields,
nonfinite numbers, malformed records and native failures reject. No late worker
result may be accepted after timeout/cancellation. Join/reap the worker first.

The store has one atomic state file pointing to the accepted source revision
and its immutable artifact directory. Compare the optional expected revision
before work and immediately before commit. A write lock serializes local
publishers. Stage the full artifact directory, fsync files where supported,
rename it to a new immutable location, then atomically replace the state file.
The pointer change is the sole commit point. An invalid edit, failed solve,
cancelled/exhausted run, stale revision or injected publication failure leaves
the accepted pointer and every previous artifact byte unchanged. An unreferenced
new directory may remain as failed-attempt evidence; it is not successful state.

Successful adapter output establishes represented, constructed, evaluated and
exported levels. Destination validation remains false until independent
receiving-application evidence is attached. Every failure has `successful=false`,
`committed=false`, exact diagnostics, source hash, reached/blocked levels and
attempt costs. Previously committed artifacts retain their original revision
and are never relabeled as the failed candidate. Native logs and failed stages
are preserved under separate attempt identifiers, subject to caps.

## Qualification boundary

Freeze independent A/B/C/D source fixtures, analytic expectations, negative
diagnostics, rename/reorder control and failure tests before any adapter output.
Build every case twice in fresh native processes and empty scenes. Canonical
inputs and final GLBs must be byte-identical on this pinned environment; `.blend`
byte identity is not required. Reopen every saved scene and reproduce native
response. Independently inspect raw/final geometry, matrices, identities, native
settings, collider removal, all interpolation intervals and actual destination
playback. Preserve exact commands, hashes, run times and failures.

C191 establishes neither general collision dynamics, arbitrary inertia,
dynamic/dynamic contact, a production backend nor comparative authoring value.
The next step after a complete pass is a separately frozen same-backend task
comparison with adapter preparation cost disclosed.
