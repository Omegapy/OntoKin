# Finite Blender receiving acceptance — C219/0.1.0

**Decision:** ACCEPT THE PRECISE FINITE PROMISE.  
**Date:** November 12, 2026, America/Denver.  
**State:** Experimental, evidence-only acceptance decision; independent review and publication are recorded separately.  
**Scope owner:** [C219 issue #170](https://github.com/Omegapy/OntoKin/issues/170).

## 1. What is accepted

For the single accepted C210 assembly, the exact retained C214 source-normal payload, the separately identified C217 capture and C218 observer, and the pinned Blender 4.3.2 executable/importer/settings, the existing evidence satisfies this promise:

> Exact retained source authority plus independently measured native geometry and shading, disclosed loss, useful inspected views, and persistence of the observed native values through the specified save/reopen sequence.

Authoritative source means the retained source program and dependencies, source identity, semantic sidecar, accepted GLB and original float32 normal payload. A surface normal is a direction used for shading. The source directions remain exact in retained authority; Blender's actual directions differ by the measured amounts below.

This decision completes the selected one-application feasibility gate under this explicit finite promise. It permits the next task to plan one second-target/source-traceability proof. It does not claim a general receiving implementation or authorize a native start. The held prototypes remain held.

The decision is separate from [C215's proposed contract](../receiving-adapter-c215/CONTRACT.md) and its automatic report. C215 still reports `nativeFidelityEstablished=false`, `receivingEvidence=false`, `receiverExecutionVerified=false`, `provenanceAuthenticated=false`, `acceptanceTolerance=null` and `shadingAcceptance=NOT_EVALUATED`. Its report supplies measurements; the independently reviewed execution, persistence and visual evidence supply the additional conditions for this decision. Small error by itself is not the acceptance rule.

## 2. Exact evidence boundary

The starting published main is `12f9ec0d3dc582fb895799450c5f20945b4647df`, tree `7d2c2d1cd3e08dfce494fce160b6995382ff9983`. The complete [C218 source handoff](https://chatgpt.com/library?file_id=libfile_fde3_f-e0d94eb678648191b4b866ea7a6b0f8f_2ab2a24d43748191957f9bcc356b59de&account_id=personal) is 461,987,145 bytes, SHA-256 `86c89578715dc707f121edbc9519fe78908f7f9a01b9b3d733e9abdbc3114111`. C219 independently verifies its finalized directory and documented offline restore; [C218 issue #168](https://github.com/Omegapy/OntoKin/issues/168) records the completed post-seal delivery.

| Role | Exact source identity |
| --- | --- |
| C217 actually executed import/capture source, unpublished local identity | `6af212204d58fbac2a98f3cded44facd67c52528` |
| C217 published held source, draft PR #167 | `55ce9f34a14cbf3d954332244c9e9a6800ed93fb` |
| Shared C217 execution/held tree | `50cd8c97290130fc97945e74c51332bd507e91eb` |
| C218 actually executed reopen observer, unpublished local identity | `efd5002a8dd955a4fb59c96920b0263e35e01a25` |
| C218 published held source, draft PR #169 | `15c369134cf8ae42d092823aeab9348c9861adfd` |
| Shared C218 execution/held tree | `35ce5d109bb45d3a08930031fef5cbc98728854a` |

Equal trees establish equal tracked bytes, not identical commits or evidence that a held commit executed. [Exact artifact bindings](evidence/BINDINGS.json) identify the accepted GLB, source bundle, semantic sidecar, source-normal payload, motion reference, plans, source artifacts, build records, importer bytes, settings, observations, reports, audits and images. The inventory records each original C218 archive path and its retained C219 package path. Root controls, tools and source descriptors moved under `history/c218` are mapped through `history/c218/PRESERVATION.json`; preserved payload bytes, modes and hashes remain unchanged.

The native executable was `/usr/bin/blender`, 94,967,000 bytes, SHA-256 `0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4`. The reviewed importer inventory pins 117 Python files. Version 4.3.2 was actually observed; upstream build lineage remains `Unknown`. These bindings do not establish complete shared-library closure or authenticity against a hostile host.

The exact saved scene is `agent-results/namespace-repair/run-01/received.blend`, 3,864,164 bytes, SHA-256 `dd8a6f32e96e45ec92207ee3417af0b3c88a6f9d898cff6d07e4366ab79993c4`. C217 saved it once. C218 reopened those bytes with automatic scripts disabled, without import, save, source repair or normal replacement. Its bytes remained unchanged.

## 3. Requirement-to-evidence decision

Every row is required for this finite promise. A passed row retains the limits stated in its evidence; it is not a general-purpose certification. The C218 requirement identifiers refer to the preserved 32-row review, including its original pending-at-seal dispositions.

| ID and condition | Existing evidence and observed result | C219 disposition |
| --- | --- | --- |
| F01 — Exact accepted source and authority | C214 validation binds the C210 GLB/source/semantic triple and all 3,024 source-corner float32 normal entries. C217/C218 raw scene observations and source/text audits retain the four authority texts and accepted identities. C218 R14–R16. | SATISFIED for these exact bytes. Raw payload, canonical JSON and base64 GLB text hashes are distinct identities and are not substituted for each other. |
| F02 — Reviewed executed source, application and settings | C217/C218 plans, approvals, reservations, source manifests, process receipts and independent binding audits identify the executed local commits, executable, importer and actual settings. C218 R01–R13, R25, R28–R29. | SATISFIED within the observed host boundary; upstream build lineage and complete dependency/authenticity claims remain unresolved. |
| F03 — Complete independent correspondence and loss measurement | Separate GLB decoding checks 18 product instances, 7,800 triangles and 23,400 corners. All source corners have one valid native match; missing, ambiguous and invalid counts are zero. Exact local positions and cyclic winding select correspondence; normals do not select matches. C218 R16–R18. | SATISFIED for complete measured loss. The strict source-normal fidelity gate remains FAILED. |
| F04 — Geometry, identities, dimensions, units and frames | Source/corner and material/semantic/pose audits check actual mesh positions, topology, winding, source identities, mappings and units. Blender local `(X,Y,Z)` converts to source `(X,Z,-Y)` without a new matching tolerance. | SATISFIED for the accepted triangulated assembly and declared conversion. Other evaluated frames, drifted coordinates and general meshes are outside the profile. |
| F05 — Supported materials and sampled motion | Independent native-details checks cover actual material values/slots/sidedness and all 126 object poses at seven declared times. Maximum material component error is `2.384185793236071e-08`; position error `4.768371586472142e-08 m`; rotation error `1.976862424823881e-07 rad`. C218 R21–R24. | SATISFIED under unchanged existing material `2e-6`, position `0.001 m` and orientation `0.001 rad` limits. These are not replacement normal or shading limits. |
| F06 — Meaning preserved with unsupported execution separated | Original importer extras, explicit scene/object mapping and the complete source sidecar are independently checked. No rigid-body world, constraints or modifiers are introduced. C218 R14–R15, R24. | SATISFIED as retained source/mapped metadata plus observed geometry/playback. Declared joints, ownership, following, matter and action meaning are not thereby native executable physics or behavior. |
| F07 — Saved-scene authority and native persistence | C218 exact-persistence audit reports 55,197 assertions, comparing all native normal/position values, triangle/loop identities, materials, mappings, retained source and 126 poses with C217. Changed normal corners, position corners and poses are all zero; maximum numerical differences are all zero. C218 R19–R23. | SATISFIED for this one reopen. It preserves the native loss already present; it does not restore source-normal fidelity or prove stability across other builds. |
| F08 — Useful reviewed native images | C217 and C218 each produced the two planned views, independently inspected. Overview shows both assemblies; detail shows a complete sphere front/silhouette and arm/post junction. C218 R26–R27. | SATISFIED for useful visible evidence. Faceted silhouettes, low-sample grain and hidden surfaces limit what the views establish. No numerical precision or universal visual-quality claim follows. |
| F09 — Controlled actual execution and failure accounting | C217 import/save/capture exited 0 after 14.217 seconds. C218 reopen exited 0 after 9.911 seconds. Both reports record no timeout or remaining process group. Their single-start schedules are consumed and closed. Original C216/C211 failures and reviewer-harness corrections remain retained. | SATISFIED for the recorded completed operations. No retry, native run or source-program execution occurs in C219. |
| F10 — Historical integrity and durable source/evidence | C218 post-seal delivery is reconciled through the observed closed scope issue, exact downloaded ZIP hash, finalized package verification and documented offline restore. Original C218 R31/R32 are preserved as written; the later closure is recorded separately. | SATISFIED for C218 evidence availability. C219's own final archive verification/save is a separate delivery obligation recorded after sealing. |

The [independent C217 import review](../native-receiving-c217/evidence/FINAL-IMPORT-REVIEW.md) and [independent C218 reopen review](../native-reopen-c218/evidence/FINAL-REOPEN-REVIEW.json) supply the detailed scientific checks. Their full evidence in the handoff includes 93,691 source/corner/loss assertions, 2,695 material/semantic/pose assertions, and 464 corrected provenance assertions for C218. Counts identify existing observations; C219 does not rerun or relabel those historical tests.

## 4. Native values, retained meaning and failed claims

| Boundary | Accepted meaning | Limit |
| --- | --- | --- |
| Authoritative source | Exact source bundle, sidecar, original normal payload and accepted GLB remain recoverable and traceable. | Retention does not make every declaration executable in Blender. |
| Native geometry and appearance | Imported geometry, sampled poses and material values satisfy the stated existing checks; actual native shading directions and useful views are measured. | Only this fixture, build, inputs, settings and observed sequence are covered. |
| Semantic mappings | Stable identities, source mapping, explicit scene/object metadata and unsupported feature treatment remain inspectable. | Metadata for ownership, following, joints, material/mass declarations or actions is not a native simulator implementation. |
| Save/reopen | Captured native values and source records persist exactly in the observed reopen. | Numerical equality of captured values is not byte identity of rendered PNGs, cross-version compatibility or a universal persistence guarantee. |

The original normal gate is **FAILED**. Maximum native-versus-source component difference is `0.0001531541347503662`, above unchanged `2e-6`. There are 14,880 exceeding corners and 7,088 exceeding triangles across eight sphere instances. Independent maximum angular difference is `0.008947222990085959` degrees. Repeated instances share geometry; this finite observation is not a universal error bound. No normal, correspondence or shading tolerance is introduced.

The following original or broader claims remain failed, blocked, unknown or unrun:

- C211's strict normal failure, rendering failure and missing historical fan-frame/short/interrupted-driver observations retain their original dispositions. Its held denoising correction is still unexecuted as that historical source. C217's separate correction and renders do not rewrite it.
- C216's start failed before product import; actual failing module attributes were not captured. C217's observed namespace does not invent the missing C216 receipt.
- Upstream executable lineage, complete system shared-library closure and hostile-host authenticity remain unproved.
- Lossless native normals, a general or production importer, live destination physics/actions, complete compatibility and full-product release are not established. The four prototype PRs #155/#165/#167/#169 remain held.
- C210's broad regression attempt remains FAILED, and the inherited earlier regression remains FAILED with unrun obligations. Documentation-only checks in C219 do not establish a new full regression pass.
- Second-target execution/source-traceability proof, Unreal support, a matched direct-authoring comparison and an authoring advantage remain unrun or unestablished.
- The C201 admission/coordinator/host-sealing work, C209 job/0.2 follow-up and broader deferred domains remain deferred and incomplete under C210.

## 5. Decision rationale and stop

The proposed promise requires retained authority, independently verified actual native observations, complete disclosed loss, supported semantic mappings, persistence and useful inspected images. C217 supplies the import/save/capture evidence and C218 supplies the missing reopen evidence. C219 reconciles their post-seal availability and independently reviews this combined requirement table. No required native condition remains unobserved within the precise promise stated here.

Acceptance therefore applies to that promise alone. It changes the current stage disposition, while retaining the failed strict normal contract and the unchanged automatic reporter. No historical contract, evidence, expected result, source implementation or released behavior is edited to obtain this result.

After publication and a verified saved C219 handoff, the [next bounded task](NEXT-TASK.md) is a planning decision for one second target and source traceability using the same accepted semantic source. It must identify the actual available destination and exact requirements before any later implementation or native start. C219 does not perform that planning task, select a new backend or start another milestone.
