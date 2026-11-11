# C201 public Q01 admission protocol

**Revision:** `OK-ADMIT-STATIC-TRAY-C201/0.1.0`  
**State:** preparation only, pending independent review of exact documents  
**Status:** C201 admission protocol prepared; coordinator and execution gates pending.

## 1. Authority and precedence

This separate admission retains mapping `OK-MAP-STATIC-TRAY-001/0.1.0` and
experimental profile `ontokin.static-tray/0.1.0`. The
[C198 adoption](../static-tray-mapping-c198/ADOPTION.md),
[specification](../static-tray-mapping-c198/SPECIFICATION.md),
[validation plan](../static-tray-mapping-c198/VALIDATION-PLAN.md) and
[controls](../static-tray-mapping-c198/CONTROLS.json) govern inherited geometry
and meaning. [C200's adoption](../static-tray-exporter-c200/ADOPTION.md) and
[qualification](../static-tray-exporter-c200/QUALIFICATION.md) preserve its
qualified constructor and closed schedule. C201 defines only this new public
task, process schedule and admission decision. A conflict among normative
records, or between this document and [ADMISSION.json](ADMISSION.json), blocks
readiness until an identified amendment receives review. Do not silently choose
an easier expectation.

C200 merged through [PR #137](https://github.com/Omegapy/OntoKin/pull/137) at
`2b2f3e7de7595099ad5f9e0176c5596220c0c2dc`, tree
`7e1ab341160cf5b86807e8ffec2cc3bb7b47db92`. Its historical executed source is
`62b2316cc3f88db187f69fbd7fdb2cf0997a97de`, tree
`87779ee65fb31dbd6de0f4372697a91f1bf4744a`, with input-lock SHA-256
`e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0`.
C199 consumed one failed construction; C200 consumed twelve accepted
constructions. Neither invocation or ledger may be reset, resumed or reused.

This protocol does not approve native execution now. A separately committed
implementation, meaningful CPU controls, current-host verification, complete
executable lock and independent exact-input approval must precede the single
C201 invocation. The producer cannot issue its own approval.

## 2. Exact public task and source

Use the qualified Q01 two-tray task in metres, right-handed Y-up coordinates:
X is width, Y is height and Z is depth. Each empty root has exactly six box
children in canonical order: back, base, front, left-wall, payload, right-wall.
The output contains fourteen nodes and twelve meshes, with roots
`equipment-tray/pair/left` and `equipment-tray/pair/right`. Preserve all stable
IDs, semantic roles and explicit owner/follow relationships.

| Quantity | Left | Right |
| --- | --- | --- |
| Payload X, Y, Z, m | 0.200, 0.060, 0.120 | 0.160, 0.040, 0.100 |
| Horizontal gap on each side, m | 0.005 | 0.005 |
| Wall / base / headroom, m | 0.004 / 0.006 / 0.020 | 0.004 / 0.006 / 0.020 |
| Root X, Y, Z, m | -0.300, 0, 0 | 0.300, 0, 0 |
| Root quaternion w, x, y, z | 1, 0, 0, 0 | 1, 0, 0, 0 |
| Cavity width, height, depth, m | 0.210, 0.080, 0.130 | 0.170, 0.060, 0.110 |
| Outside width, depth, m | 0.218, 0.138 | 0.178, 0.118 |

The inherited Q01 equations and binary64 rounding govern derived values; the
table introduces no rounded-value comparison exemption. Tray surfaces use
linear RGBA `(0.25, 0.5, 0.75, 1)` and payload proxies use
`(0.75, 0.5, 0.25, 1)`, both opaque under `static-tray-materials/0.1.0`.
All other appearance/export/import settings retain their qualified bytes.
Every object remains `no_body`, prescribed and collision-disabled. A payload
is a visible measurement proxy with zero represented mass, not a physical load.
No wrapper, camera, light, animation, skin or additional geometry belongs in the
GLB. Unsupported resources or physics claims must fail explicitly.

Both routes receive the same public dimensions, expected measurements, identity
and material rules, inspection information, common constructor, output
requirements and resource limits. No model or timed author takes part. OntoKin
uses its editable `main.ok`, pinned `tray.ok` and source manifest. Direct Python
uses `main.py`, `tray.py` and its manifest. These existing files remain unchanged.
All paths in this table and ADMISSION.json are relative to the repository root.

| Source file | Bytes | SHA-256 |
| --- | ---: | --- |
| `fixtures/static_tray_v01/native/Q01/ontokin/main.ok` | 930 | `458b996c4bb1564c1bf2ad32541099ddcbc30cf2570129cd9ffb130fe9f9e2be` |
| `fixtures/static_tray_v01/native/Q01/ontokin/source.json` | 191 | `a170cd8622cfcae2f2979a5c56c7fcd38e0bdd16e11b81fde8e2bc8b8836a01a` |
| `fixtures/static_tray_v01/native/Q01/ontokin/tray.ok` | 3298 | `849f784ee51a84908f1921e92d8136fefad409627199f6df17f4c0cdf8cdfb34` |
| `fixtures/static_tray_v01/native/Q01/direct-python/main.py` | 789 | `67e318628e4f8f1997cf9516aca47ef0fbedce10f2c825d467689ec951c52d17` |
| `fixtures/static_tray_v01/native/Q01/direct-python/source.json` | 363 | `dee8a9f153bbf8220751059f508dcfdfa0501731cda5061dc45921a2248e4d4d` |
| `fixtures/static_tray_v01/native/Q01/direct-python/tray.py` | 2657 | `562de2b1d558f421315fe8f0350cb01830ba0ce7726d2263e020808025413b03` |

## 3. Four-slot schedule and process accounting

| Slot | Route | Required source / purpose | Predecessor and equality references |
| --- | --- | --- | --- |
| A01 | OntoKin | Frozen editable Q01 source; baseline | No predecessor |
| A02 | Direct Python | Frozen editable Q01 source; baseline | A01 complete; D01 and D03 passed; compare A01 |
| A03 | OntoKin | Resolve A01 accepted source; clean regeneration in a new empty store | A02 complete; compare A01 |
| A04 | Direct Python | Resolve A02 accepted source; clean regeneration in a new empty store | A03 complete; compare A02 and A03 |

Each slot permits at most one native construction, one receiving process and
one actual-delivery Node checker. The independent maxima are four, four and
four. Every attempted start consumes its slot, including failure, timeout,
cancellation and unknown outcome. No fifth native slot, automatic retry,
receiving retry, extra render, simulation, timed author, lifecycle cohort,
synthetic Node preparation cohort or deliberate Blender cancellation experiment
is permitted. Each receiver may render its one assigned image only.

Complete receiving measurements and required cleanup before conditional
transaction promotion. Then complete the actual-delivery Node check before
advancing. A later Node failure stops the schedule; prior technical acceptance
is not family admission. A01 must also pass both controls below before A02.
Slot and comparison references must be explicit fields. Historical N01/N02
numbering is not an admission implementation.

## 4. Actual output, receiving and regeneration

Decode the actual raw and final GLB buffers, indices, transforms and hierarchy.
Check closed box corners, outward triangles, signed volume, identities, roles,
materials, wall/base/cavity dimensions, all four horizontal gaps, floor contact,
headroom and material overlap in independently expected tray frames. Preserve
0.000005 m dimension/corner/clearance allowances and 0.000001 rigid-transform
element allowances. Do not round a failed comparison into a pass.

Each successful slot's clean receiver reopens its actual saved `.blend`, measures
native geometry, then imports and measures that slot's actual final GLB. Both
sets of observations must agree with the independent reader before promotion.
Retain the existing fixed isometric 1024 by 768 Workbench view, with one image
per receiver. Review all four actual images for omissions, axes, intersections,
role/material distinctions and visible contradictions. Record any occlusion or
resolution limit. A fixed view does not certify hidden surfaces.

Require exact `canonical-input.json`, `raw.glb` and `final.glb` bytes for all
four comparisons: A01/A02, A03/A04, A01/A03 and A02/A04. Keep route provenance
detached. Add no timestamp, path, generator, key-order or metadata exemptions
after a mismatch. Hash and retain every native scene; native `.blend` container
byte equality is not required by the inherited mapping.

For A03/A04, resolve the baseline's durable accepted pointer and sealed editable
source/dependency closure, then regenerate in a new empty store. A mutable
fixture path, prepared canonical record or copied output cannot substitute for
accepted source. Verify that the baseline source, reusable module, complete
output/receipt closure and accepted pointer remain unchanged before and after.
Require exact stable-ID keyed right-sibling geometry, transforms, topology,
materials and relationship values across paired/regenerated results. Only the
inherited exclusion for unrelated GLB index renumbering applies. This admission
contains no new left-edit or reuse performance task.

## 5. Two controls on A01's actual delivery

After A01's actual-delivery check, use separate fresh copies of its final GLB.
The unmodified positive audit is the baseline control. Apply the qualified
independent corruption writer in process, without a new native, receiving or
Node start. Retain mutation offsets, input/output hashes, observed findings and
accepted-closure preservation before and after each operation.

1. **D01:** increase only the actual left payload full X extent by 0.004 m,
   without changing source or metadata. Nominal 0.005 m side gaps become
   0.003 m. Require rejection with `CLEARANCE`; a parse error or `GEOMETRY`
   alone does not satisfy it.
2. **D03:** move the actual right/front node transform by +0.002 m along its
   tray-local Z, keeping names and expected metadata. Require `SIBLING` against
   A01's independently decoded right-sibling closure. Preserve valid structure
   so a structural failure cannot substitute for the assigned finding.

Run D01 then D03 and stop before A02 if either fails. Other findings retain
their inherited meaning; the named required finding is mandatory. D03 supplies
the changed-sibling alternative; no extra missing-node control is added. Label
these as C201 observations rather than additional C200 qualification coverage.

## 6. Exact closure, dependencies and bounds

ADMISSION.json binds the existing source/expected files and qualified shared
roles by SHA-256. Those bindings are not a complete future executable lock.
Retain constructor geometry, source lowering, canonical arithmetic, independent
reader/expectations, receiver, store, supervisor and settings by exact identity.
Separately implement and review the required four-slot lock, transaction,
readback/probe compatibility and coordinator roles. Do not monkeypatch global
verification or disable old guards.

The intended dependency target is Linux x86-64 CPython 3.12.14, Blender
4.5.3/build `67807e1800cc`, exporter 4.5.48, Node v24.22.1, Khronos Validator
2.0.0-dev.3.10 and Three.js 0.186.1/revision 186. C200's pinned inventories
identify intended bytes; they do not verify a new host. Recheck the actual
interpreter/standard library, complete Blender distribution, executable,
loader/shared libraries, Node dependencies, aliases and clean environment.
Missing dependencies block sealing and native readiness.

The future lock must bind committed C201 source and every transitive imported
role; fixture and independent expectation hashes; expanded commands and exact
environments; distinct stores/output paths; explicit slot/control/reference
fields; host/dependency inventories; protocol and input-lock digests; and
independent approval. That approval must identify this revision and its
four/four/four ceilings. Preparation cannot manufacture it.

| Bound | Value |
| --- | ---: |
| Ordinary source operations / elapsed time | 100,000 / 30,000 ms |
| One monotonic transaction total | 65,000 ms |
| Construction plus independent reading | 30,000 ms |
| Receiving stage | 30,000 ms |
| Promotion / cleanup | 3,000 / 2,000 ms |
| Poll / termination grace | 50 / 500 ms |
| Native output | 67,108,864 bytes |
| Each GLB | 8,388,608 bytes |
| Each bounded log / result | 4,194,304 / 4,194,304 bytes |
| Separate Node checker outer / child-work time | 30,000 / 28,000 ms |

These retain the inherited stage allowances for the separate future admission;
they do not authorize execution now or increase source defaults. A stage may
start only when the remaining original transaction clock permits its full
allowance. Mandatory cleanup/reaping precedes promotion. The separate Node
check retains its own bounded deadline.

## 7. One-use invocation, stops and final decision

Before any child starts, the future coordinator must exclusively create its
own one-use invocation receipt and append-only durable ledger, reserving each
slot/stage once. An existing invocation blocks another even after timeout or
unknown outcome. A changed directory, cleared ledger or copied store cannot
reset that identity or make a stopped schedule resumable.

The first unexpected transaction, receiver, readback, control, cleanup,
identity or persistence result stops all later work. Retain partial outputs,
raw logs, attempts and accepted-state observations. Failed promotion preserves
the previous pointer. Reconcile unknown durable state without launching a
replacement child or continuing a later stage. A later repair requires an
identified, independently reviewed revised schedule; failed receipts remain.

Admission requires exactly four successful accepted transactions, four receiving
comparisons, four actual-delivery Node checks, both assigned control rejections,
all exact equality/preservation checks, four image reviews and independent
final result review. Preserve measured coordinator status, visual completion
and independent final admission as separate chronological records. A technical
`ACCEPTED` receipt alone does not admit the family.

## 8. Preparation boundary and open requirements

No C201 executable coordinator, full input lock, native-readiness approval,
invocation, delivery or admission result is supplied here. The concrete next
gate is [implementation and its independent controls](IMPLEMENTATION-NEXT.md).
Document review can approve only these exact preparation rules and bounded
implementation, not execution readiness or admission completion.

The inherited full regression remains FAILED: 4,239 distinct passing methods
and thirteen torque-read methods NOT RUN after the unchanged 30,000 ms setup
timeout. Preserve C200's N05/N06 resolution and N07/N08 occlusion limitations;
review C201's own images when they exist. Actual-Blender cancellation, general
contact, live destination physics, broad compatibility and sixteen external
roles, unseen-task reliability, comparative benefit, full release and the
complete [GOAL](../../../GOAL.md) remain open. This public Q01 task does not
resolve those broader requirements.
