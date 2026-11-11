---
document_id: OK-MAP-STATIC-TRAY-001
version: 0.1.0
profile: ontokin.static-tray/0.1.0
source_language: "0.2"
source_profile: construction-0.1
implementation_status: not-implemented-or-qualified
---

# Finite static-tray mapping contract

## 1. Authority and scope

This contract defines an explicitly selected experimental delivery mapping for
exactly two reusable equipment trays. Each tray has five solid-looking box
surfaces and one payload measurement box. The mapping preserves dimensions,
identity and the distinction between owning a part and making it follow a
frame. It assigns no physical matter, contact response or motion simulation.

[ADOPTION.md](ADOPTION.md) records the technical decision. Adoption fixes the
requirements below; it does not mean that an adapter, source fixture, Blender
worker, delivered object or receiving check already exists or passes. The
[C197 feasibility result](../equipment-tray-c197/FEASIBILITY.md) remains the
reason this separate mapping is needed.

The adopted [core language](../../language-design/OK-LANG-001-core-language-specification.md)
and [construction language](../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md)
retain authority over source meaning. This is a destination restriction on
their existing features, not a new source language, parser or physics profile.
The source must pass the existing `construction-0.1` compiler. No tray-specific
parser may substitute for it, and no source annotation may substitute for the
compiler's resolved values and relationships.

Normative requirements use **must** and **must not**. JSON Schema checks only
structure and the explicit constraints it encodes. Every additional semantic,
source-binding and delivered-geometry check in this document is mandatory.

## 2. Explicit selection and unchanged defaults

The mapping selector is exactly `ontokin.static-tray/0.1.0`; the contract
identity is `OK-MAP-STATIC-TRAY-001/0.1.0`. A future adapter must require that
selector explicitly. Missing, different or unsupported selectors cannot fall
back to this mapping. The current runtime does not acquire a working selector
merely because these documents have been adopted.

An OntoKin input remains language `0.2`, source profile `construction-0.1`,
with its existing bundle and nominal identities. The normal
`ontokin.agent/0.2` to `ontokin.glb/0.2` binding remains unchanged. Neither that
destination nor C191/C193 may be renamed, widened or redirected to this worker.
No ordinary exporter, default profile, accepted store or hosted workflow changes
under this contract decision.

The direct-Python route must produce the same route-neutral record and use the
same constructor, settings, independent reader and receiving checks. Supplying
Python instead of OntoKin does not waive any geometry or relationship rule.

## 3. Exact source family and stable identities

### 3.1 Reusable definition

The OntoKin route uses exactly two source units: entry `main.ok` and one imported
definition module `tray.ok`, package `ontokin.static-tray`, version `0.1.0`,
module key `static-tray`. The entry pins the exact UTF-8 bytes of that module
through the existing package/version/SHA-256 import mechanism. The exact future
source bytes, rather than a dummy digest or this filename alone, must be frozen
before any qualification execution.

The module contains one public tray class with key `tray` and one private box
helper class with key `box`. Both roots instantiate that same nominal tray
definition. The tray class declares exactly six ordinary part occurrences of
the box helper and six fixed follows. There are no generated collections,
inheritance, additional classes, functions, methods, imported packages or
user-defined sites in this first mapping. Ordinary typed parameters, `derive`
expressions, assertions and the existing built-ins are sufficient.

The tray has exactly these seven public length parameters. Their lexical names
are listed to fix the future source fixtures; their declaration keys are stable
under an otherwise valid lexical rename.

| Lexical name | Declaration key | Meaning |
| --- | --- | --- |
| `payload_width` | `payload-width` | Payload full X side, `px` |
| `payload_height` | `payload-height` | Payload full Y side, `py` |
| `payload_depth` | `payload-depth` | Payload full Z side, `pz` |
| `clearance` | `clearance` | Equal horizontal clearance on each side, `c` |
| `wall_thickness` | `wall-thickness` | All four wall thicknesses, `t` |
| `base_thickness` | `base-thickness` | Base thickness, `b` |
| `headroom` | `headroom` | Payload top to open rim plane, `h` |

The entry has module key `equipment-tray`, scene key `pair` and exactly two
ordinary root objects with keys `left` and `right`. It has no local class,
function, site, joint, follow, action or event declarations. Roots may override
their seven public inputs and their own world placement; an admitted input may
not override a descendant or change the shared module. Both source files use
the existing construction profile. The scene authors `duration = 1[s]` and
zero world-expressed gravity. Duration is required by the existing language;
this mapping exports the constant scene and does not advance a simulation.

The private box helper has one public `Vec3<Length>` extent parameter, key
`extent`, and `box(extent)` geometry. All source surfaces, offsets and colors
must resolve to the values in sections 4–5. Exact helper names, formatting and
source bytes are frozen with the executable fixtures; a later implementation
cannot accept a different structural family merely because its screenshot looks
similar.

### 3.2 Occurrence, definition and relationship identities

There are exactly **14 object occurrences**: two empty roots and twelve boxes.
The source identity tuple, rather than a display label or array index, identifies
each object. Definition identity remains separate from occurrence identity.

| Element | Stable identity |
| --- | --- |
| Entry scene | `["equipment-tray", "pair"]` |
| Left/right root | `["equipment-tray", "pair", side]`, with `side` equal to `left` or `right` |
| Tray part | Root identity followed by its part key |
| Part keys | `back`, `base`, `front`, `left-wall`, `payload`, `right-wall` |
| Fixed follow | Root identity followed by `follow-` plus its part key |
| Tray definition | `["package", "ontokin.static-tray", "static-tray", "definitions", "tray"]` |
| Box definition | `["package", "ontokin.static-tray", "static-tray", "definitions", "box"]` |

The fixed follow for a part is declared in the reusable tray class. Its parent
is that root's implicit object frame and its child is that occurrence's part.
Its offset is expressed in that same parent frame. Each part is also owned by
that root. The two facts must be checked and recorded separately. Ownership
does not itself place a child. A child has exactly one incoming follow, no
authored placement, and no second pose authority. The roots have no incoming
relation and use their explicitly authored world poses.

The compiler's ordinary implicit `frame` and `origin` references remain intact;
they do not become extra delivered objects. Cross-tray follows, shared children,
extra descendants, missing or duplicate identities and ownership changes are
outside this profile. Renaming a display identifier while retaining its keys
must not change the canonical record. Replacing a definition is not an
instance-local parameter edit.

## 4. Units, finite inputs and six-box geometry

### 4.1 Numeric domain

All source inputs are typed lengths. Source unit conversion and arithmetic use
the existing nearest-even binary64 rules. The canonical record contains metres
only. Each boundary below is the canonical binary64 value of the written decimal
quantity in metres; comparisons are inclusive and contain no hidden tolerance.

| Input | Minimum, m | Maximum, m |
| --- | ---: | ---: |
| `px`, `pz` | 0.01 | 1.0 |
| `py` | 0.01 | 0.5 |
| `c` | 0.001 | 0.05 |
| `t`, `b` | 0.001 | 0.025 |
| `h` | 0.001 | 0.1 |
| Each world root translation component | -10.0 | 10.0 |

All box full sides must remain finite and strictly positive after resolution.
No negative-size convention, scale, reflection, shear, unit inference, geometry
clamping or tolerance-based correction is permitted. Each source unit is at
most 32,768 UTF-8 bytes; their combined bytes are at most 65,536. The serialized
canonical record is at most 32,768 bytes. These are new mapping restrictions,
not increases to any inherited source or execution cap.

### 4.2 Derivation and placement

Use X for width, Y for height and Z for depth. The cavity floor is Y = 0.
Resolve the following expression trees in order, with the ordinary source
rounding at each scalar operation:

- `W = px + (2 * c)`
- `D = pz + (2 * c)`
- `H = py + h`
- `OX = W + (2 * t)`
- `OZ = D + (2 * t)`

The producer must read the actual compiled values and verify these identities.
It must not discard compiled boxes and silently reconstruct compliant ones from
reported parameters. The direct route uses the same operation order and exact
binary64 inputs. Reassociation that changes a bit is not canonical equality.

More precisely, let `RN` round an exact real result to nearest binary64, ties
to even, then normalize zero. A decimal length literal is converted with
`RN(exact_decimal * exact_unit_factor)` once. Each subsequent `a + b`, `a * b`
or `a / b` uses the exact values of its already rounded operands, performs that
one operation, and applies `RN` again. Unary minus changes the sign and then
normalizes zero. The dimensionless divisor/multiplier `2` is exactly
representable. This matches inspected
[`values.literal`, `values.binary` and `values.rounded`](../../../ontokin/values.py).
Using exact fractions internally for **each separate operation** is a permitted
independent way to reproduce this rule. Keeping a whole expression rational
and rounding only its final box extent is not permitted. Algebraically
equivalent source trees are admitted only if their actual compiled results
match the specified trees bit for bit.

| Part key | Full box sides `(X,Y,Z)` | Follow offset translation `(X,Y,Z)` | Role |
| --- | --- | --- | --- |
| `base` | `(OX,b,OZ)` | `(0,-(b/2),0)` | `base` |
| `front` | `(OX,H,t)` | `(0,H/2,(D+t)/2)` | `front` |
| `back` | `(OX,H,t)` | `(0,H/2,-((D+t)/2))` | `back` |
| `left-wall` | `(t,H,D)` | `(-((W+t)/2),H/2,0)` | `left-wall` |
| `right-wall` | `(t,H,D)` | `((W+t)/2,H/2,0)` | `right-wall` |
| `payload` | `(px,py,pz)` | `(0,py/2,0)` | `payload-proxy` |

Every follow has identity rotation. The base is below the floor, while the
walls begin at the floor. Front/back walls include the corner strips; left/right
walls end at the inner front/back planes. These formulas partition the intended
tray material without overlapping corner volumes. Binary64 and delivered-mesh
rounding are measured under the frozen delivery tolerances, not represented as
an exact-arithmetic or physical guarantee.

The payload rests at the cavity floor, is centered horizontally, and has
clearance `c` from each interior wall. Its bottom clearance is **zero**.
Headroom `h` measures its top below the open rim plane; there is no lid and no
claimed top contact surface. A measurement must not rename bottom clearance as
`h`, or infer an unseen lid from the proxy.

Root placements may translate and rotate whole trays within section 5. Their
relative layout is a task input. The two trays' independent geometry is checked
by identity in each tray frame; this contract does not infer collision avoidance
between trays. Qualification fixtures must place them separately so the native
receiving inspection remains unambiguous.

## 5. Rigid frames and the supported orientation subset

### 5.1 Twelve exact proper orientations

The source world remains right-handed and Y-up. Root placement is a world
translation plus one of the following **twelve** proper rotations. Quaternions
use `(w,x,y,z)` order. The first nonzero component is positive.

| Name | Canonical quaternion |
| --- | --- |
| `I` | `(1,0,0,0)` |
| `X180` | `(0,1,0,0)` |
| `Y180` | `(0,0,1,0)` |
| `Z180` | `(0,0,0,1)` |
| `D+++` | `(0.5,0.5,0.5,0.5)` |
| `D++-` | `(0.5,0.5,0.5,-0.5)` |
| `D+-+` | `(0.5,0.5,-0.5,0.5)` |
| `D+--` | `(0.5,0.5,-0.5,-0.5)` |
| `D-++` | `(0.5,-0.5,0.5,0.5)` |
| `D-+-` | `(0.5,-0.5,0.5,-0.5)` |
| `D--+` | `(0.5,-0.5,-0.5,0.5)` |
| `D---` | `(0.5,-0.5,-0.5,-0.5)` |

Roots must author a direct existing `quat` constructor whose dimensionless
numeric literals are one listed tuple or its sign-reversed equivalent. The
root's `placement` uses the existing `pose(world, ..., quat(...))` constructor.
No alternative rotation expression, including `axis_angle`, is admitted in
this first mapping even if an approximate projection looks close to a listed
tuple. Follow offsets use `quat(1,0,0,0)`. Source lexical validation uses the
existing compiler AST and source spans; it does not reparse source text with a
second grammar.

The restriction is supported by inspected implementation, not by a claim that
all source rotations have exact binary64 coordinates. The current
[`Validator.unit_axis`](../../../ontokin/validator.py) sums exact `Fraction`
squares, checks the existing norm domain, computes `sqrt(float(norm2))`, divides
each component, and canonicalizes its sign. Every catalog tuple has exactly
`norm2 = 1`; its literal components, square root and divisions are exact.
The existing `quat` and `pose` built-ins preserve those values. This source-code
argument establishes authorability; actual compiled fixture verification is a
later qualification requirement.

Every catalog matrix has entries in `{0,1,-1}`, determinant `+1`, and exactly
one nonzero entry per row and column. It preserves handedness and full side
lengths. There is no approximate nearest-rotation classification, snapping,
normalization repair or arbitrary quaternion export in this profile. In
particular, a 90-degree yaw or roll is unsupported. Broader rotation support
requires a later version and its own numerical qualification.

### 5.2 Transform meaning and coordinate conversion

For a local point `v` on a box, the source-world point is
`Rroot * (v + part_offset) + root_translation`. Ownership adds no transform.
There is one root pose and one follow offset; neither is applied twice.
The canonical record stores them separately instead of storing an ambiguous
flattened world pose or independently rounded duplicate world coordinates.

The native Blender coordinate conversion is the proper rotation
`C(x,y,z) = (x,-z,y)`. It is a change of basis, not a scene edit or reflection.
Positions convert with `C`; orientations convert with `C * R * inverse(C)`.
Local vertices and offsets must use the same declared basis convention. The
delivered GLB returns to source Y-up coordinates. The pinned native worker and
export settings must demonstrate that `C` and its inverse are applied exactly
once on the complete source/native/delivery round trip. A good endpoint or
matching dimension label does not prove this conversion.

## 6. Appearance, matter and unsupported behavior

All fourteen source objects use `no_body()`, `prescribed`, and disabled
collision. Empty roots have the role `tray-root`; boxes use the roles in
section 4. No mass, inertia, density, force, joint, collider or solver is
introduced by a visible mesh. Own and owned aggregate mass remain exactly zero.
The payload is a visible **measurement proxy**, never a simulated load.

The fixed material set is `static-tray-materials/0.1.0`. Five tray surfaces per
root use source linear RGBA `(0.25,0.5,0.75,1)`, material token `tray`. Payload
proxies use `(0.75,0.5,0.25,1)`, material token `payload`. Both are opaque;
textures, transparency, face-dependent regions, modifiers and additional
appearance inputs are unsupported. Empty-root appearance has no delivered
surface. Metallic/roughness, normal, triangulation and exporter settings must be
fixed in the common worker contract before qualification; they are not route
choices.

Explicit zero velocity/omega may not be used to imply a dynamic body. This
finite source family omits those authored fields. The compiler's existing zero
defaults remain unchanged. Nonzero state, action descriptions, events,
simulation, animation, constraints, imported meshes, general solids and live
physics must fail explicitly before native work.

## 7. Canonical route-neutral construction record

The structural contract is
[`canonical-record.schema.json`](canonical-record.schema.json), JSON Schema
2020-12. The geometry record contains **no route name, source hash, source path,
program revision, timestamp, host path or backend receipt**. Those belong to the
separate provenance envelope in section 8. Equivalent admitted constructions
can therefore have identical canonical bytes even when their source languages
or exact source revisions differ.

The record fixes these identities:

| Field | Exact value |
| --- | --- |
| `schema_version` | `ontokin.static-tray.record/0.1.0` |
| `profile` | `ontokin.static-tray/0.1.0` |
| `contract` | `OK-MAP-STATIC-TRAY-001/0.1.0` |
| `template_id` | `static-tray-six-box/0.1.0` |
| `length_unit` | `m` |
| `frame` | `ontokin-world-rh-y-up` |
| `numeric_encoding` | `binary64-be-hex/1` |
| `material_set` | `static-tray-materials/0.1.0` |

`trays` has two entries in order `left`, `right`. Each contains its scene owner,
role, empty geometry, physical/motion/collision modes, world root pose, seven
resolved input values, and six parts. The payload's three inputs are collected
as `payload_size_m` in X/Y/Z order; the other fields are
`horizontal_clearance_m`, `wall_thickness_m`, `base_thickness_m`, and `headroom_m`.
The parts are ordered `back`, `base`, `front`, `left-wall`, `payload`,
`right-wall`. Each contains its complete identity, owner, role, full box sizes,
material token and explicit follow identity/parent/offset. Array order never
substitutes for the identity fields.

The semantic validator must independently enforce the bounds, source equality,
geometry equations, allowed rotations, materials and relationship rules. It
must reject extra, omitted or contradictory information rather than ignoring it.
Exactly matching source bytes and schema-valid JSON are necessary but do not
establish correct lowering or delivery.

### 7.1 Exact scalar and JSON serialization

Every real scalar is a JSON **string** containing exactly sixteen lowercase
hexadecimal digits: the eight big-endian bytes of its IEEE-754 binary64 value.
Examples are zero `0000000000000000`, one `3ff0000000000000`, one half
`3fe0000000000000`, and minus one half `bfe0000000000000`. The schema uses this
encoding for lengths, translations and quaternion components. It does not accept
decimal JSON numbers, booleans, hex prefixes or alternate spellings.

Before encoding, negative zero is normalized to positive zero. A received
negative-zero bit pattern is rejected as noncanonical. NaN and either infinity
are rejected; they are never geometry. No decimal rounding, lossy quantization,
orientation repair or platform-dependent float formatting is allowed. A finite
value outside its field's range still fails even when its encoding is valid.

Canonical JSON recursively sorts object keys by ASCII, emits no insignificant
whitespace, uses unescaped ASCII strings, and has no BOM or trailing newline.
All schema keys, fixed identities and scalar strings are ASCII. Array orders
are those fixed above. The canonical record file consists of those exact UTF-8
bytes. Duplicate JSON object members must be rejected before a JSON parser can
silently discard one.

The record identity is `sha256:` followed by the lowercase SHA-256 of
`b"ontokin.static-tray.record/0.1.0\0" + canonical_record_bytes`. It is distinct
from a plain file-byte hash, the source program revision and every GLB hash.
Readers must compare the named identity they actually mean. A successful clean
regeneration must reproduce the exact canonical record bytes; numeric closeness
does not satisfy that equality.

## 8. Exact source, dependency and delivery binding

A separate immutable provenance envelope accompanies every attempt. Its schema
identity is `ontokin.static-tray.provenance/0.1.0`. It includes the profile and
contract identities, route, candidate identity, canonical record identity and
plain record-file SHA-256. It is never injected into route-neutral mesh or node
data. Unknown or missing required bindings block qualification.

For the OntoKin route, retain the actual `ontokin.bundle/0.1` manifest and exact
UTF-8 bytes of both units, with their `source_id`, diagnostic filename,
`source_revision`, package ID/version and byte count. Preserve the existing
`program_revision` algorithm exactly: it hashes the canonical bundle manifest
under the existing domain separator, before source parse/link. The supplied
module set must equal the import closure. Retain the tray and box nominal
definition identities and the defining unit's exact revision; an alias or
unchanged class key does not authenticate changed dependency bytes.

For direct Python, retain exactly two editable local source files, `main.py`
and its reusable `tray.py` helper. Apply the same 32,768-byte per-file and
65,536-byte combined source caps as the OntoKin route. The reusable tray helper
must be called twice with the two instance input sets. No additional local or
external source/input file, ambient module search, fetched code or remembered
output may replace those bytes. The Python interpreter and standard-library
distribution belong to the execution dependency pin, not to an invented
OntoKin program revision.

Its source manifest has exactly `schema_version`, equal to
`ontokin.static-tray.python-sources/0.1.0`; `entry_filename`, equal to `main.py`;
and `files`, an array sorted by ASCII filename. Each file entry has exactly
`filename`, `source_revision` (the `sha256:`-prefixed lowercase SHA-256 of its
exact bytes), and integer `size_bytes`. Canonicalize that manifest with sorted
ASCII object keys, no whitespace/BOM/trailing newline, and ordinary unsigned
decimal integer sizes without leading zeros. The direct source identity is
`sha256:` followed by SHA-256 of
`b"ontokin.static-tray.python-sources/0.1.0\0" + canonical_manifest_bytes`.
It is a Python source-closure identity, not an OntoKin bundle revision.

Both routes additionally bind:

- The implementation Git commit and relevant exact file manifest, compiler or
  direct lowerer bytes, schema and contract bytes, and the command/options used.
- The complete native worker, Blender build/executable and glTF exporter pins,
  receiving implementation, independent checker and every required dependency.
- Effective budgets, launch environment, attempt ID and ledger slot, return
  state, retained stdout/stderr, and produced file identities.
- The unchanged candidate source closure used to construct the record; accepted
  predecessor identity and requested transition precondition, where applicable.
- Actual raw GLB, final GLB, saved scene and validation/receiving receipts when
  those files exist. Failure receipts cannot name nonexistent successful output.

Every dependency pin must identify real retained bytes or an exact reproducible
distribution and the actual observed tool version. A URL, version label,
placeholder SHA or source filename alone is insufficient. Executable source,
worker and dependency bytes that do not yet exist are explicit prerequisites
for the later implementation gate; C198 does not fabricate them or count that
gate as passed. Implementation must freeze its completed inputs before its
first qualification run, within that same bounded implementation task.

Moving an unchanged source tree must not alter its source identity merely
because its absolute host path changed. Existing OntoKin diagnostic filenames
remain part of the adopted program identity. Changing bytes, a pin, filename
or dependency binding must invalidate the corresponding result; an old result
may stay retained only under its original identity.

## 9. Delivery identities and honest output claims

The eventual GLB contains exactly fourteen nodes: two empty root nodes, each
with six box-mesh children. It has no wrapper, camera, light, animation or extra
object nodes. Node names are the slash-joined stable identity tuples, for
example `equipment-tray/pair/left/base`. The known key alphabet contains no
slash, so this spelling is unambiguous. Semantic identity and role must also be
retained in fixed extras; a name alone is insufficient.

The hierarchy represents the explicit fixed follows for this family. The
separate owner/follow fields remain in the canonical record and receipt; this
hierarchy does not redefine the language's ownership semantics. Whole-record
identity and hashes belong exclusively in detached provenance. They must not
appear in GLB node, mesh, material, asset or other metadata. Route-specific
source/dependency information is also excluded from the GLB. Fixed semantic
ID, role and relationship metadata remains permitted. A left-only edit must
not change the right sibling's metadata through a whole-record hash, and the
reader must not normalize such a change away. Exact delivered extras, node
order, mesh/accessor layout and worker settings must be fixed before native
qualification and checked rather than inferred from exporter defaults.

The independent reader must decode actual buffer bytes, indices, vertices,
triangle faces and node transforms. It verifies complete boxes, cavity and
payload clearances, wall/base thicknesses, proper placement, exact identity
inventory and the right sibling's complete geometry/identity closure. Producer
dimension labels, extras and a successful compiler are not measurements.
Source annotations provide binding and expected intent only.

The two routes' canonical records, raw GLBs and final GLBs must be byte-identical
for the same frozen construction and settings. Independent clean regeneration
must also reproduce each of those byte sets exactly. No volatile-field
exemptions are authorized. Saved `.blend` bytes are retained and hash-bound;
they are not a byte-equality target, and actual reopening must independently
verify their geometry. A structural/native serialization change requires a
recorded decision before observing qualification outcomes.

## 10. Diagnostics and atomic failure

Mapping diagnostics use the `OTRAY-` namespace; they do not rename existing
`OKL-` compiler diagnostics. Every diagnostic records stage, candidate identity,
profile/contract, implicated semantic ID or JSON pointer, and a useful reason.
Source-origin errors retain actual source unit, revision and byte span when
available; cross-unit errors retain their related locations. No source span is
fabricated for a direct JSON/native error.

| Code | Required distinction |
| --- | --- |
| `OTRAY-E-PROFILE` | Missing, wrong or unsupported explicit mapping selector |
| `OTRAY-E-CLOSURE` | Absent/mismatched source or dependency bytes/pins |
| `OTRAY-E-SHAPE` | Wrong source family, object count, helper, geometry type or declarations |
| `OTRAY-E-IDENTITY` | Duplicate, missing, extra, replaced or inconsistent semantic identity |
| `OTRAY-E-UNITS` | A record is not in declared metres, or a supported source dimension cannot be established |
| `OTRAY-E-RANGE` | A resolved input or extent is outside its finite domain |
| `OTRAY-E-ROTATION` | Root orientation/expression is outside the exact catalog, or non-rigid transform requested |
| `OTRAY-E-RELATIONSHIP` | Wrong owner/follow parent, multiple pose authorities, omitted or extra follows |
| `OTRAY-E-PHYSICS` | Matter, contact, joint, collider, solver or other physical participation requested |
| `OTRAY-E-MOTION` | Action, event, nonzero motion state, animation or simulation requested |
| `OTRAY-E-MATERIAL` | Unadmitted color, material or appearance feature |
| `OTRAY-E-RECORD` | Malformed/noncanonical schema, member, order or numeric encoding |
| `OTRAY-E-NUMERIC` | Non-finite calculation or unavailable required exact numeric result |
| `OTRAY-E-BINDING` | Candidate, record, backend or result bytes do not match their binding |
| `OTRAY-E-STALE` | Accepted-predecessor precondition no longer holds |
| `OTRAY-E-RESOURCE` | Operation, byte, time, process or attempt limit exhausted |
| `OTRAY-E-CANCELLED` | Cancellation observed; no successful candidate promotion |
| `OTRAY-E-BACKEND` | Native worker, export or required cleanup failed |
| `OTRAY-E-DELIVERY` | Actual output geometry, identities or receiving checks failed |
| `OTRAY-E-REGENERATION` | An obligated exact reconstruction differs |

Process validation in this order: selector and candidate/source binding;
existing source compilation or direct-record structural validation; finite
mapping admission; exact record/source binding; native preflight; staged native
construction; independent output/receiving checks; accepted-state transition.
An earlier-stage failure stops later stages. Within one stage, report all
bounded discovered violations sorted by semantic ID and code; do not invent a
priority race between several applicable errors. Original compiler failures
remain original compiler failures, with their candidate bindings intact.

The adapter uses a distinct candidate/accepted artifact store. Each attempt
has a fresh staging directory. It must not overwrite an earlier accepted source,
dependency, record, delivery or receipt. Native work starts only after all
preflight gates and its preassigned attempt slot pass. A failure, timeout,
cancellation, cleanup failure or rejected delivered result retains the previous
accepted pointer and complete accepted closure. A failure receipt may be added
without claiming output acceptance.

The native stage can finish as `BUILT_PENDING_RECEIVING` before a separately
bounded receiving process runs. That state is not acceptance or qualification.
Promotion occurs only after complete required validation and an atomic
expected-predecessor check. Before the accepted-pointer compare-and-swap, all
required child processes must be reaped, their output handles closed, and
mandatory cleanup verified successful. A cleanup or reaping failure prevents
promotion; cleanup is not postponed until after acceptance. A stale request fails before native launch where
detectable; a race found at promotion also refuses promotion and retains the
candidate under its own identity. Unknown outcomes require accepted-state
readback before retry. No automatic native retry is permitted. No existing
program-service acceptance rule is changed by creating this separate artifact
transaction, and this finite requirement does not itself establish a qualified
concurrent-writer implementation.

## 11. Qualification boundary and preserved limitations

Ordinary source defaults remain **100,000 operations and 30,000 ms**. This new
qualification pipeline has an explicitly selected finite host allowance: its
construction plus independent-reader command has a 30-second deadline, its
separate receiving command has a 30-second deadline, and the whole transaction
has a 65-second outer deadline including cleanup and promotion. The commands
must enforce their own limits as well as the outer limit. These deadlines govern
different work; they do not raise the source budget or alter a historical gate.
Later execution must use the frozen command/deadline/cleanup/attempt ledger and
preserve cancellation. Any further allowance requires a recorded decision
before execution and cannot retroactively pass an older failed gate.

The accompanying validation plan fixes positive, boundary, negative, composition
and scoped-edit cases before outcomes are observed. At least two retained-output
controls must change real delivered bytes: insufficient payload clearance, and a
changed or missing right sibling. The same independent reader must reject them
for their expected reasons. There are **zero C198 source fixture executions,
native exports, simulations, receiving jobs or timed authors**.

Future qualification is separate from the original C197 admission attempt.
Return to the later public tray admission only after both routes and all
required controls qualify. That later admission retains at most four native
exports total, including failures: baseline plus clean regeneration per route,
without automatic retry. A subsequent author comparison is another separately
frozen task. A successful mapping is not evidence of comparative authoring
advantage.

The inherited legacy driver and supplemental tail remain **FAILED**, with
**4,239 distinct passing methods and thirteen torque-read methods NOT RUN**
after the unchanged 30,000 ms setup failure. General geometry, arbitrary
rotations, contacts, live destination physics, complete regression, broader
compatibility, external roles, full release and every other outstanding
[GOAL](../../../GOAL.md) requirement remain open.
