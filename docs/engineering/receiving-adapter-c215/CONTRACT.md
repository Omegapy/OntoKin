# Proposed receiving-corner adapter and loss contract, C215/0.1.0

**Proposed experimental CPU adapter. No native receiving acceptance is established.** A surface normal is a direction used to shade a surface. This adapter links recorded Blender triangle corners to the exact source normals retained by [C214](../source-normals-c214/CONTRACT.md), then measures their differences. It does not start Blender, emit native observations, or authenticate a recorded execution.

## 1. Receiving promise and authority

The proposed promise is **exact retained source authority plus independently measured native shading and disclosed loss**. It is not an approximation policy. No new normal tolerance or pass threshold is adopted. C211's original `2e-6` normal failure, held receiver and unrun save/reopen/visual gates retain their exact meanings. A small measured error, metadata copy, successful mapping, or synthetic exact match cannot approve native shading.

C215 uses separate schemas `ontokin.receiving-input-lock/0.1`, `ontokin.blender-corner-observations/0.1` and `ontokin.blender-corner-loss-report/0.1`, with profile `c210-blender-corner-adapter-c215/0.1`. C214's synthetic-only profile and source bytes remain unchanged. Public report generation revalidates the entire exact C214 payload against its accepted C210 GLB, source bundle and semantic sidecar; an arbitrary self-consistent substitute source is refused.

This module is an isolated standard-library CPU tool. Its only local dependency is the retained C214 prototype. It imports no production OntoKin runtime and launches no process. Its report always sets `nativeFidelityEstablished`, `receivingEvidence`, `receiverExecutionVerified` and `provenanceAuthenticated` to false; `acceptanceTolerance` is null and `shadingAcceptance` is `NOT_EVALUATED`.

## 2. Independently supplied byte lock

`build_report(payload, observations, glb, bundle, semantic, *, input_lock, artifacts)` accepts the source payload, observation document, original source triple, independent lock and exact artifact bytes. The lock is a distinct input, not copied from untrusted observation claims. A future execution plan must freeze and review it before execution and retain its canonical SHA-256. Updating a lock creates a new unverified proposal, not acceptance of a previous execution.

The lock has exactly `schema_version`, `profile`, `sourcePayloadSha256`, `sourceInputs`, `receiverRevision`, `receiverDisposition` and `artifacts`. `sourceInputs` equals C214's three pinned byte descriptors. The canonical payload digest is recomputed. `receiverRevision` is a complete 40-character lowercase Git identity. These source dispositions distinguish historical execution from held source:

| Disposition | Required identity and meaning |
| --- | --- |
| `c211-executed-source` | `66f1940c4c99f52dfdea835445cdc380498815f7`, the actual source identity retained in C211's execution-input record. This label alone does not attest a new run. |
| `c211-held-unexecuted-correction` | `cdae8b582a37e37f76f142f07039ba74cedc08ad`, held draft PR #155 including its unexecuted denoising correction. A native label is refused with this disposition. |
| `future-proposed-source` | A separately identified source revision, distinct from those two historical identities. It remains unverified and needs source review and a separate execution plan. |
| `synthetic-fixture` | Explicit synthetic context, distinct from historical source. It cannot carry a native label. |

`artifacts` has exactly `receiver_source`, `importer_source`, `build_record`, `import_settings` and `scene` keys in both the lock and supplied byte dictionary. Every non-null artifact is nonempty bytes, and its descriptor is exactly `{bytes, sha256}`. Each length and SHA-256 is recomputed against the independent lock. Changing observed hashes together with artifact bytes still fails against the original lock. `scene` alone may be null, and only for synthetic observations. Exact scene bytes are mandatory for a native-unverified input.

`receiver_source` is the exact source artifact or bundle selected by the future plan, not a filesystem path or a digest string. The adapter hashes these bytes. It does not itself reconstruct a Git tree or certify that those bytes belong to the claimed revision; the future source review owns that check. The build record binds exact raw JSON with fields `application="Blender"`, `version` (three nonnegative non-bool integers), `executableSha256` (complete SHA-256), nonempty `buildHash`, and `importerSourceSha256`. `Unknown` can record genuinely unavailable build lineage; it does not establish that lineage. `importer_source` contains the separately reviewed importer source artifact bytes; `importerSourceSha256` must equal their recomputed digest and independently locked descriptor. This prevents substituting an importer under an unchanged build declaration. A build-record hash is not a fresh executable or installed-importer verification. Import settings are an exact raw JSON object. A future plan must bind executable/add-on provenance, settings and any scene to actual execution separately.

This separation provides checked content identity, not trusted provenance. The caller must preserve the independently reviewed lock. Synthetic tests deliberately use synthetic source/build/settings/scene artifacts; their correctly matching hashes do not make them native evidence.

## 3. Recorded-observation envelope

The envelope has exactly `schema_version`, `profile`, `kind`, `inputLockSha256`, `sourcePayloadSha256`, `frame`, `phase`, `producer` and `objects`. Both digests must equal the independently supplied canonical lock and validated source payload. `producer` is nonempty text. The only supported frame is `blender-object-local-right-handed-z-up`.

`kind="synthetic-cpu"` requires `phase="synthetic"`. `kind="native-unverified"` requires phase `import` or `reopen`, independently locked scene bytes, and a disposition other than held or synthetic source. This native label is only a caller claim. It does not change any fixed false evidence/acceptance field. The old C211 raw observation schema lacks this new envelope and native-loop identity boundary; it is not silently relabeled or accepted here.

Each object contains exactly `nativeObject`, `nativeMesh`, `sourceNode`, `sourceMesh`, `sourcePath`, `elementId` and `triangles`. Native identifiers are nonempty strings; `nativeObject` and source node each appear at most once. The source node, mesh, path and stable element identity must equal one C214 instance. Missing objects are allowed and produce missing source rows. Metadata alone does not establish geometric or native provenance; triangle positions independently determine corner correspondence within that source instance.

Each triangle contains exactly `nativeTriangle`, `loops`, `positions` and `normals`. Triangle IDs are nonnegative non-bool integers unique within an object. There are three distinct loop IDs, and each loop ID occurs once per object in this already-triangulated finite boundary. Native triangulation of larger polygons can reuse polygon loops and is unsupported by this profile. Distinct objects may share a native mesh or loop numbers; object identity remains part of each observation identity. Positions are three numeric triples. Normals are three values, each independently validated as a direction. Unknown fields, duplicate IDs, booleans in indices, ambiguous object bindings and contradictory source metadata refuse the envelope.

## 4. Correspondence and coordinate conversion

Source positions and normals stay in C214's `gltf-object-local-right-handed-y-up` frame. The fixed inverse proper rotation is `(X,Y,Z) -> (X,Z,-Y)` from Blender local coordinates to the source local frame. It is a signed axis permutation with determinant +1; it preserves winding and applies equally to local position and normal direction. No world transform, translation, scale, shear, normal matrix or renormalization is inferred. Observations in a world frame, a modified local frame, or a differently transformed evaluated mesh require a new reviewed boundary.

For each source mesh, the adapter indexes every original triangle's three POSITION triples with the three cyclic rotations. A recorded triangle can be reordered globally, and its corners can rotate cyclically. The exact original node/mesh/primitive/triangle/corner and original indexed winding remain in report rows. Reversed winding is detected separately and cannot become a valid match. Native triangle and loop numbers need not equal source indices.

Matching uses source instance identity and exact numerical equality of converted POSITION triples only. Normals are never a correspondence key, so measured shading loss cannot influence which source direction is selected. Coincident positions are not welded and sharp boundaries remain separate. Numeric signed zeros compare as equal for position correspondence; original normal float32 signed-zero bytes remain authoritative in the payload/report. This finite exact-position policy is not a change to C211's separate geometry or shading tolerances. Any coordinate drift outside it produces unmatched invalid native diagnostics and missing source rows; it is not rounded or assigned a new tolerance.

If more than one source triangle/corner rotation matches, all candidate source corners become ambiguous. If more than one native triangle claims the same source corner, that source row becomes ambiguous even if the observations agree. The pure `position_candidates(source_triangles, native_positions, reverse=False)` helper permits independent synthetic geometric-ambiguity controls; it returns candidate index/permutation pairs only and cannot create an accepted payload or report.

## 5. Complete outcomes and loss measurements

Every expected C214 instance corner produces one row with `key`, `sourceVertex`, `sourceWinding`, `sourceNormalF32le` and one of four states:

| State | Meaning |
| --- | --- |
| `observed` | One orientation-preserving geometric match with one valid finite nonzero direction. |
| `missing` | No matched native corner; includes absent objects/triangles and unmatched position drift. |
| `ambiguous` | Multiple geometric correspondences or multiple native claims. No direction is chosen to minimize error. |
| `invalid` | A uniquely identified reversed-winding mapping, or an invalid direction at an otherwise unique match. |

Invalid native positions and wholly unmatched triangles additionally retain native diagnostics with no invented source identity. Ambiguous/reversed candidate triangles identify all affected source triangles. Multiple native claims also mark each implicated native triangle ambiguous; any earlier mapping diagnostic is retained in its `priorReasons`. The four source counts add to the full expected denominator. Unique mappings preserve native object, mesh, triangle, loop and corner identifiers, allowing a reviewer to trace the observation back to the captured scene/record.

Valid rows report the original source direction, raw native direction, converted observed direction, component deltas and maximum component difference. Angular difference uses scale-first normalization and `atan2(cross length, dot)` in degrees; magnitudes are not discarded from the component comparison. Opposite directions measure 180 degrees. The report has no pass threshold or universal error bound. With no valid direction, both maxima are null.

Raw observation bytes are parsed with C214's strict JSON reader: duplicate members, NaN and infinity tokens are refused. The Python API can retain nonfinite in-memory directions as invalid. Such an observation document has no canonical JSON digest; `observationsSha256` is null and `observationsCanonicalJson` false. Valid JSON observations receive a recomputable canonical hash. All reports bind the independent lock and artifact descriptors, exact source triple, source payload, build record, settings and scene presence separately from native evidence claims.

## 6. Required next gate and stopping condition

This step ends after independent synthetic mapping/binding/loss controls, source review, applicable documentation checks, reviewed publication and the verified saved handoff. It makes no C211 receiver edit and does not resolve the unexecuted correction. It is not a native import, save, reopen, visual review, complete product regression, second-target proof or authoring comparison.

Before any future native start, separately review a finite execution plan and the exact capture source for this schema. Reconcile held versus executed source, pin executable/build/add-on/settings/input/scene identities, predeclare maximum starts and failure-stop rules, count attempted and unknown outcomes, and require native save/reopen plus useful visual evidence. A proposed new receiving promise becomes an accepted gate only after its exact requirements are executed and independently reviewed. Preserve all historical failures and hashes.
