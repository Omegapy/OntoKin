# Independent C247 held-source review

## Disposition

**Approved for held-source publication only** at commit
`58ac8c83880cb5dccd4f8d4a0d75098209dd593b`, tree
`6ffa45877e5e171764fc10b5c405cee0883ad890`.
There is no remaining blocking finding within the selected mesh-array source
component. This does not authorize or certify Godot parsing, native execution,
receiving acceptance, main integration or R07 completion.

The exact source is a clean eight-file addition under
`docs/engineering/second-target-c247/` to the held C246 baseline
`bf64092e65a2cdfdef8c7202728589aaaeeae9c8`. All inherited dependencies, original
fixture and source authority remain unchanged. `EXACT-REVIEW-SOURCE.json` and
`APPROVAL.json` bind every reviewed file and the independently checked source.

## Evidence and behavior

Independent CPU controls pass **261 cases / 2,776 assertions** against a frozen
snapshot. The reviewer constructs a separate four-vertex synthetic fixture;
no author fixture or product output is substituted for native evidence.
Checks include all 63 candidate format-bit changes, all 18 source/resource
association failures, shuffled scene traversal, exactly bounded membership,
shared resources, source-value independence, non-unit normals, negative zero,
copy isolation, malformed/missing arrays, type/length/feature refusals, all
numeric nonfinite classes, explicit omission markers, retained current/prior
observations, and same-length raw-buffer/array drift.

The independent primary-source and original-fixture suite passes **117 checks**.
The ten author upstream files match their retrieval bytes and Git blob hashes.
The unchanged original GLB independently decodes as 18 nodes, five meshes and
one indexed triangle primitive per mesh. Source/primitive/native-surface
association is supported by the exact one-primitive fixture and ordered parser,
ImporterMesh and replacement-converter code. This remains conditional on
installed-build lineage and the future frozen loader route.

The C247 GDScript is manually reviewed against the model and pinned APIs.
It obtains the exact-state C246 receipt internally, rejects a failed/incomplete
chain, rechecks live root/final membership and mesh-resource identities, then
reads bounded supported arrays from each actual final ArrayMesh. No stale
loader-map access, source-position/normal/index fill, coordinate/winding repair,
metadata write, file serializer, process launcher or native admission occurs.
Shared native resources retain separate part records.

## Source findings and corrections

**F02, corrected:** The initial source recorded array slot types but discarded
actual lengths and bounded valid arrays before a cross-slot type/length refusal.
The final source records those partial observations first. Excessive arrays or
raw buffers remain omitted with explicit field, type, count, reason and cap.
The controls verify both normal partial refusals and over-limit omissions.
Unsupported native types retain their observed type inventory; no arbitrary
object serializer is introduced.

**F01, reviewer correction:** The reviewer initially suspected that returning a
Mesh-typed value from an ArrayMesh-typed function would be a static error.
The exact upstream analyzer permits reverse-compatible returns as unsafe, so
that parser-failure claim was not established. The author added an explicit
validated cast for clarity. No version was parsed or executed by Godot.
The initial concern and correction remain in `INITIAL-FINDINGS.json`.

One additional review-tool correction is preserved: applying downloaded primary
source with a text patch appended a trailing newline. Exact-byte assertions
caught this; the reviewer rewrote those local copies from their unchanged
retrieval records and verified the original upstream Git blob identities.
`SOURCE-MATERIALIZATION-CORRECTION.json` records both local hashes. No project
source or upstream content changed, and no failed native result was concealed.

## Native API facts that constrain interpretation

The pinned RenderingServer source binds the full format-version constants and
`mesh_get_surface` for scripts. Public ArrayMesh `surface_get_lods` is absent,
so the implemented raw surface dictionary route avoids that unavailable API.
Optional LOD/skin/blend/attribute keys are emitted only when their data is
nonempty in the inspected implementation, making presence-based refusal
consistent with the selected finite route.

RenderingServer adds auxiliary tangent storage when normals exist and decodes
native normals/tangents from octahedral storage even with the attribute
compression flag off. The source correctly retains both API arrays and raw
buffers without asserting source-normal fidelity. The explicit glTF tangent
import flag stays off; this observer does not generate tangents.

The pinned Dictionary deep-copy implementation recursively duplicates values,
and Variant explicitly duplicates packed byte, int32, float32 and Vector3 arrays.
Together with the reader's explicit packed-array duplicates, this supports the
claimed detached receipt by inspected source semantics. The actual installed
implementation and runtime behavior have not been established.

Primary URLs, exact hashes and full licensed sources are retained in the author
bindings and `INDEPENDENT-PRIMARY-SOURCES.json`. The new independent sources are
`core/variant/dictionary.cpp`, `core/variant/variant_setget.cpp`,
`core/variant/variant.cpp`, and `modules/gdscript/gdscript_analyzer.cpp`, all at
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`.

## Limits and handoff

The CPU model does not emulate GDScript parsing, engine allocation, native object
lifetime, codec behavior, diagnostic continuation or installed precision. Raw
buffer bytes are observed, not independently decoded by this component. No
numeric source/native comparison ran. Two equal reads detect retained changes
but do not prove atomicity against transient concurrent mutation. Native APIs
can allocate before returning; no hard resource limit is claimed.

Materials, evaluated animation, full raw sealing/serialization, complete
diagnostics, installed lineage, useful images, scene persistence, reservation
and execution admission remain later gates. R07 is pending. The original strict
Blender-normal failure remains unchanged.

The next separate material component must preserve the already-consumed C246
session boundary and C247 part associations; this review starts no such work.
Root owns publication reconciliation, recovery, complete archive verification,
restoration and confirmed saved delivery. Review workers are finished.

Scratch dependency snapshots need not be duplicated in the package. Their exact
restoration identities are in `SNAPSHOT-RESTORE-MAP.json`; all are retained Git
commits. The initial C247 source itself is also kept in `initial-c247-source/`.
