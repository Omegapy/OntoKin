# C239/0.1.0: finite combined CPU observation checks

## Scope and public path

C239 joins the separately versioned C222 geometry, C234 material, C235 normal,
C236 pose and C237 semantic-retention checks for the unchanged C210 fixture.
It follows [C238 admission](../second-target-c238/CONTRACT.md) and the
[C220 plan](../second-target-c220/PLAN.md). This contract is committed before
implementation controls. None of the existing contracts, checkers, authority
files, tolerances, profiles or historical outcomes changes.

The only public API is `check_combined(package_root, envelope_path)`. It accepts
actual paths, never a caller-supplied admission or component report. The CLI is:

```bash
python3 -IB tools/second_target_c239/check_combined.py \
  --package-root /absolute/extracted-handoff \
  --envelope /absolute/observations/envelope.json
```

It emits one JSON report and has no output-file option. The API returns the same
report for pass, measured loss and refusal. Exit 0 means all finite checks pass;
exit 1 means completed checks expose measured loss or a declared-corner-map
mismatch without a structural refusal; exit 2 means a structural, authority,
source, snapshot or argument refusal. All original component result strings,
error codes, reached stages and complete available reports remain explicit.
Temporary private CPU input copies are allowed and removed before return. No
native application, version probe, source evaluator, exporter/importer, renderer,
scene writer, subprocess or aggregate runner is imported or executed.

## Exact inherited executable and authority binding

The inherited implementation reference is observed main
`f53c44ed6ef660c1a1ebc17af43e66e37b06d9fa`. The following unchanged files are
pinned by exact bytes. C239 checks these bindings before loading components and
at public invocation boundaries. A changed file refuses execution even if a
previously imported module would still work. The implementation also records
its own source byte binding and refuses a change since that source was loaded.
The externally observed C239 Git revision remains part of execution evidence;
a reported base revision is not substituted for it.

| Component | File under `tools/` | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| C221 | second_target_c221/check_bindings.py | 31854 | fff5569d31b3cd900385ac4b955dc5b30c8ee440ef16d8851b5a0ffb5d03aa4b |
| C222 | second_target_c222/check_observations.py | 18786 | 1eab170204d8f02b5d281f7e67d7f649040a1c525884fcc17eadfed6c765b6b9 |
| C234 | second_target_c234/check_materials.py | 20025 | e68d212d4b5490c9e17466fb1a858a69a6d0764b0019cb4df265902bf0cabb13 |
| C235 | second_target_c235/check_normals.py | 20057 | 15acd1e95b47a9f6f6eee6c3c28875883d3722b5071ec37a14b7c720a9e8773c |
| C236 | second_target_c236/check_poses.py | 27129 | 51864445f638a36ef5a93fd4bd58c07a416d342ce6e371a894f52f3af06bf584 |
| C237 | second_target_c237/check_semantics.py | 20819 | c5127c265eb247ebeb1e7625e57179fb839ba932967c48ed071d5b60afb3a0c0 |
| C238 | second_target_c238/check_envelope.py | 40475 | 76c87096d810236b58ac47a13ad58ab9eec558500104c6c96acf89f462deea83 |

The C220 authority documents keep their existing C221 pins. Every call freshly
executes C238's public admission on the supplied authority and observation paths.
That admission includes fresh C221 inspection of all eight original files. It
is a prerequisite, not numerical acceptance. No saved PASS can replace it.

This is exact inspected-source provenance on the ordinary trusted Python host,
not hostile-host attestation. In-process function replacement by a hostile
caller, operating-system compromise and native-capture authenticity remain
outside the promise. Controls may use private seams to exercise boundary
failures; they never become public authority APIs.

## One private, verified input snapshot

After fresh admission, C239 safely rereads the envelope and six actual members
and requires their exact lengths and hashes to equal that invocation's report.
It keeps descriptor-relative no-follow/nonblocking reads, C238 path/alias rules,
per-file ceilings, the 42 MiB combined ceiling and strict parser limits. Held
file descriptors and original directory entries are checked again after all
seven byte sequences have been captured. A change between admission and capture
refuses the snapshot; no unchecked reread provides a component input.

C239 separately rereads all eight original authority files through unchanged
C221 size/hash/mode pins. It writes exact bytes into a new mode-0700 private
snapshot, preserving required authority file modes and member basenames. No
hardlink or symlink connects those copies to the supplied files. The public
C238 API freshly admits this retained copy before component execution.

All five public component APIs receive this one private authority directory and
these exact member files. Before and after every component, C239 verifies the
private snapshot's complete inventory, regular-file identities, entry/descriptor
metadata and byte bindings; an altered, removed, replaced or added file causes
a snapshot refusal. Inherited executable and authority-document bindings are
rechecked at component boundaries. No component result is accepted as a valid
combined snapshot if those checks fail. Reports retain reached component results
with their invalidated-snapshot status instead of silently discarding them.

The verified private copy defines the execution snapshot. Original caller files
may change after capture without changing that copy; the report does not claim
those external files remain unchanged at return. Temporary paths are not durable
evidence. The caller's exact raw inputs, full result and source revision must be
preserved by the external evidence workflow when a result is used for a gate.
No file modes or private path establish protection from a hostile same-user host.

## Fixed component execution and full correspondence comparison

Run public APIs in this order: C222, C234, C235, C236, C237. Material and normal
APIs retain their own fresh authority/correspondence calls. Never inject a cached
C222 report or bypass those prerequisite paths. After ordinary component
refusals, continue the remaining components on the verified snapshot so an
independent pose or retention loss remains visible. Unsafe snapshot/source
conditions or an unexpected implementation exception stop further execution;
unreached components remain `NOT_RUN`.

When C222 succeeds, compare its exact `corner_map_fields` and every one of its
23,400 derived rows with C238's complete declared map, in the original canonical
order. Compute and report both canonical digests, complete declared and derived
maps, row counts, equality and every mismatching row. A matching digest alone
is insufficient. The map remains a producer declaration until this independent
position/winding derivation agrees. If C222 refuses, map comparison is `NOT_RUN`
with the geometry refusal identified. Normal values cannot select a match.

All available component reports are embedded without modifying their meanings.
Validate their observed file bindings against the retained snapshot. Material
and normal geometry/map bindings must also equal the actual C222 result when
that result exists. Admission-only reports remain unchanged as admission
reports, including their own historical `NOT_RUN` component fields; the C239
component section records actual execution separately.

| Check | Preserved condition and report content |
| --- | --- |
| C222 geometry | Exact position matching, reverse-once winding, complete 18-part/7,800-triangle/23,400-corner correspondence and ambiguity refusal. |
| C234 materials | Fixed inverse sRGB transfer; unchanged inclusive 0.000002 represented-number limit; exact culling and transparency; all 108 numerical and 36 mode checks. Its numerical failure remains the original `FAIL_CLOSED`/`MATERIAL_COMPARISON` report and is classified separately as measured loss by C239. |
| C235 normals | Every raw/source value and all 23,400 corner rows; unchanged inclusive 0.000002 component gate; complete `FAIL_STRICT_NORMAL_LIMIT` measurements. |
| C236 poses | All 126 slots; original 0.001 m position, 0.001 rad orientation and 0.000001 s time limits; separately declared matrix consistency and exact-unit-scale profile; original result and errors. |
| C237 semantics | Complete 18 identities, 14 features, four retained-file inspections, both source units and complete semantic values/losses; original pass, measured-loss or refusal class. |

Imported, independently derived, observer-copied, externally retained and
unsupported provenance remain untrusted declarations under C237's existing
matrix. Source retention, numeric equality and a shared set of byte bindings do
not attest a shared native capture session or executable/build lineage.

## Combined report and refusal precedence

Report schema: `ontokin.c239.combined-comparison/0.1`. Include fresh original
and retained C238 admission, exact inherited and C239 source bindings, the
retained envelope/six member/eight authority bindings, 18 complete identity
mappings, snapshot verification boundaries, complete component outcomes and
reports, full declared-versus-derived map comparison and explicit limitations.

The overall result is `PASS_CPU_COMBINED` only when every component passes,
all 23,400 map rows agree and every snapshot/source boundary passes. Otherwise:

- `FAIL_CLOSED` records admission/source/snapshot failures or unexpected errors;
  remaining components are `NOT_RUN` and any reached reports remain available.
- `FAIL_COMPONENT_REFUSAL` records an ordinary structural component refusal.
- `FAIL_DECLARED_CORRESPONDENCE` records a derived/declaration mismatch when no
  structural refusal has higher precedence.
- `FAIL_COMPONENT_LOSS` records measured numerical, additional-profile or
  semantic/retention loss when no higher-precedence condition applies.

Every report also retains independent lists of component losses, component
refusals and map mismatches, so precedence never hides concurrent outcomes.
The CLI exit classification above follows that precedence. No finite pass
claims native receiving evidence, attested mapping, native/source execution,
shared capture provenance, target permission, full R07, a release or repair of
the original strict Blender normal failure. Every native/version/source/export/
import/render/scene-write and aggregate count remains zero.

## Controls and stopping condition

Construct complete independent positive sets for both C238 origins and inspect
all maps, identities and component inventories. Exercise outer-order changes,
correctly rebound reserialization, raw-normal and dependency consistency,
stale/mixed/swapped/corrupt envelopes, full internally valid but positionally
wrong declared maps, geometry refusal, individual and simultaneous material/
normal/pose/semantic/retention losses, matrix/scale distinctions, and C237 source
unit inspection. Verify no component API is called before successful fresh
admission, original mutation before capture refuses, external mutation after
capture cannot mix observations, and private copy/source mutation stops later
execution while retaining reached reports. Include unsafe paths/aliases/files,
JSON/size failures, wrong-source pins, unexpected checker exceptions, clean
scratch removal and API/CLI exit behavior. Inspect complete reports, not only
summary Booleans. No source fixture is regenerated.

Run C239's explicit package-dependent author cohort and unchanged C221, C222,
C234, C235, C236, C237 and C238 cohorts on the exact candidate. Preserve failures,
commands, interpreter/platform, input hashes and exact code identity. Independent
review uses its own constructed data and oracle. Documentation checks apply to
publication; broad product/aggregate and native schedules are outside this step.
After reviewed integration, run the applicable C239 and prerequisite checks on
actual main, preserve a restorable verified successor handoff, confirm its save,
and stop. Native observer/provenance, cross-target comparison, process/resource
protocol, persistence and useful rendering remain separately bounded work.
