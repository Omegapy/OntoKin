# Normal fidelity decision C212/0.1.0

**Date:** November 12, 2026, America/Denver.  
**Disposition:** retain the strict C211 contract; reject an unsupported tolerance increase and hold the current receiving path.  
**Authority:** the bounded continuation in [issue #156](https://github.com/Omegapy/OntoKin/issues/156), governed by [GOAL](../../../GOAL.md), [AGENTS](../../../AGENTS.md) and [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md). Independent review and publication are recorded separately from this decision.

## 1. What is decided

The observed stock Blender import does not satisfy C211's normal-component promise. C212 does not adopt a revised receiving contract, approve a new native attempt, or merge the held prototype. The original absolute component limit remains `0.000002` and the original failed result remains failed.

The decision rejects using `0.0002`, `0.0003`, a rounded observed maximum, or an angular number as an undocumented substitute for that limit. No new approximation budget is adopted. A future deliberately lossy profile is possible, but it needs an explicit purpose, rationale, supported boundary, independent controls and measured native results. It must not be described as a repair that preserves C211's original promise.

The present stock path is rejected **for the strict promise on this observed fixture/build**. This is not a claim that Blender cannot be useful, that every Blender normal has this error, or that a particular Blender defect has been proved. OntoKin's semantic-authoring direction remains current. The finding makes the required information-loss boundary concrete.

## 2. Exact evidence and compatibility boundary

| Item | Bound identity |
| --- | --- |
| Starting published OntoKin main | `12655f101f704050fb178ed1c7bb67e551f53eba` |
| C211 actually executed local candidate | `66f1940c4c99f52dfdea835445cdc380498815f7` |
| Separately held published receiver | `cdae8b582a37e37f76f142f07039ba74cedc08ad`, [draft PR #155](https://github.com/Omegapy/OntoKin/pull/155) |
| Authoritative accepted program revision | `sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082` |
| Accepted GLB SHA-256 | `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8` |
| Semantic sidecar SHA-256 | `1077eff813807c0b2058d35e2007c234b4d8c157f6dc0177f5a548924edd2c34` |
| Raw C211 observations SHA-256 | `f566b0f274b8b0e226639d4f10555acb31739f895f61f4e198bbe37a1adbc8bd` |
| Observed Blender version and platform | 4.3.2, Linux x86-64 |
| Executable SHA-256 | `0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4` |
| Recorded import settings | `import_shading="NORMALS"`, `merge_vertices=false` |
| Installed importer boundary | All 117 Python files rechecked against the held manifest; executable plus importer total 118 matching file bindings |

These bindings identify the retained experiment; they do not confer support for another mesh, build, platform or importer. The binary reports upstream build hash `Unknown`. No installed package-manager record established its source provenance. Exact binary equality is established; equivalence to the upstream source release is not. See [binding check](evidence/installed-binding-check.json), [source identities](evidence/upstream-sources.json) and the [original execution bindings](../semantic-receiving-c211/evidence/native/execution-inputs.json).

## 3. What the investigation establishes

The independent decoder matches all 7,800 oriented triangle position triples exactly. It reproduces 7,088 failing triangle instances and 14,880 failing corner occurrences at the unchanged limit. Maximum component error is `0.0001531541347503662`; maximum direction error is `0.00015615850038545062` radians. Normalizing both vectors leaves essentially the same discrepancy. The eight failing instances reuse one source sphere mesh and identical local observations. These are measured facts from one finite geometry case, not a general error bound. [Remeasurement](evidence/analysis/normal-remeasurement.json)

The matching installed importer supplies the normals to `normals_split_custom_set_from_vertices`. With recorded `merge_vertices=false`, its separate vertex-merging normal rounding does not run. The source-to-Blender basis change is the permutation/sign change `(x,y,z) -> (x,-z,y)` and is already accounted for by the comparison.

Official Blender tag `v4.3.2`, commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`, routes that setter into a native custom-normal layer of two signed-short angular values. The codec uses approximate inverse cosine, short rounding, a near-auto-normal shortcut and an azimuth-zero shortcut. It reconstructs a shading direction from a local fan frame; it does not store the three input float components verbatim. A normal fan is the set of connected smooth corners that share a local reference frame. [Native implementation](https://github.com/blender/blender/blob/32f5fdce0a0a571a39198edf8d7b5d719bf59f2c/source/blender/blenkernel/intern/mesh_normals.cc), [Python API route](https://github.com/blender/blender/blob/32f5fdce0a0a571a39198edf8d7b5d719bf59f2c/source/blender/makesrna/intern/rna_mesh_api.cc), [math implementation](https://github.com/blender/blender/blob/32f5fdce0a0a571a39198edf8d7b5d719bf59f2c/source/blender/blenlib/BLI_math_base.hh).

**Inference:** native encoding/calculation is the strongest supported mechanism. The exact causal decomposition remains unproved because the retained observations contain neither encoded short pairs nor native fan frames, and the executable's source lineage is unknown. The recorded importer settings do not identify an available switch that demonstrably fixes the original promise. This does not establish that no such alternative exists.

## 4. Why a larger number is not adopted

A half-step of a `2*pi` angular range at `SHRT_MAX=32767` is approximately `9.58767e-5` radians. That calculation only describes one quantization term. The upstream scalar inverse-cosine approximation documents an error up to `4.51803e-5` radians. A separate azimuth shortcut applies at cosine `0.9999`, whose angular scale is approximately `0.01414225` radians before polar-angle attenuation. Other frame, averaging, fallback and floating-point effects remain. Adding two short half-steps cannot establish a complete codec guarantee. [Reproducible scale calculations](evidence/codec-scale-calculation.json)

Choosing a new threshold just above the observed maximum would measure this known sphere, then use that same sphere to validate the threshold. It would provide no independent boundary evidence. The current task also establishes no visual or downstream requirement that makes a particular larger loss acceptable. Therefore retaining the strict promise and exposing the blocker is the supported decision.

## 5. Meaning and information loss

Accepted `.ok` source and its bound GLB remain authoritative. Exact geometry positions, winding, object identities, dimensions/frames, materials, sampled motion and semantic metadata have separate requirements. Their historical passes do not imply that shading normals passed, and a shading-normal discrepancy does not erase their observed passes.

The C211 native shading normals are **observed approximate values that fail the strict contract**. They are not approved substitute source normals. Saving the original normals in metadata could preserve an archival payload, but would not prove the fidelity of normals Blender actually shades with. Changing to calculated smooth normals, clearing custom normals, regenerating geometry or changing topology would change the mapping and requires a new explicit contract.

Any future approximate profile must report the original and resulting native directions per source-mapped corner, component difference, normalized angular difference, unit-length drift, failed/missing observations and exact build/input/settings identities. It must declare which source meaning is preserved and which native representation is approximate. Retained exact normals must not mask native loss. No such profile is adopted here.

## 6. Conditions before another receiving attempt

The [next CPU task](NEXT-CPU-PROBE.md) must first characterize the pinned upstream codec with independently specified frame/control inputs. That task is not permission for Blender execution or a complete source-to-binary attestation. It must state where its results apply and where they do not.

Before a later native attempt, separately review a strict-preserving correction or an explicit versioned approximation contract, bind all source/build/settings inputs, and execute its boundary/negative controls. Require nonfinite/zero-vector refusal; missing, duplicate or ambiguous corner rejection; preserved winding and sharp boundaries; direction-sign and basis-conversion negatives; and checks just below, at and above each adopted numeric limit. Keep original material, pose, identity, topology and metadata gates. A failed gate must not be averaged away.

A complete receiving proof still requires a newly counted bounded import, native save, separate reopen, the same independent readback checks, and inspected useful render images. The held denoising correction remains unexecuted and unrelated to the normal decision. Unknown or failed starts must be reconciled before a retry. C212 starts none of these processes.

## 7. Closure and preserved limitations

This decision completes C212's investigation scope once independently reviewed, published and delivered in a verified handoff. It does not complete the receiving proof. [Issue #154](https://github.com/Omegapy/OntoKin/issues/154) remains blocked; PR #155 remains held. The second destination and matched authoring comparison remain later stages. C199/C200 schedules stay closed and C201 admission remains deferred.

The original C211 failed contract, raw observations, render failure, interrupted broad regression and unrun save/reopen/visual gates retain their bytes and results. C210 and earlier broad regression failures remain unchanged. A successful C212 documentation or analysis check is not a full product-regression pass.
