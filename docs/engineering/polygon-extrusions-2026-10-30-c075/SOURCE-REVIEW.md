# C075 independent geometry and contract review

Reviewer: `/root/extrusion_review`.

## Contract and freeze review

Reviewed root contract/fixture commit `bdf6b61a732de8bfbfcc55bbab13e4d1115d64db` in `/tmp/ontokin-c075` before runtime implementation was available for review.

The explicit source .8 / Agent .8 / GLB .8 binding, keyed authored vertices, separate integer traversal order, CCW-only simple outlines, exact binary64-rational predicates, deterministic ear clipping, flat outward normals, named PBR regions and no implicit physical participation form a coherent bounded increment. Existing defaults and earlier profiles are explicitly preserved.

The proposed larger coordinate/depth bounds were revised before this freeze to existing 100-meter local bounds and a 0.001-meter minimum depth. This avoids silently relaxing the inherited 0.00001-meter local float32 quantization gate. The contract still explicitly rejects destination geometry that collapses or cannot meet inherited tolerances.

Independent checks on October 30, 2026 verified all 34 entries in `examples/polygon-extrusions/acceptance-freeze.json` by exact length and SHA256. For each of the 10 valid single-source geometry cases, a separate standard-library calculation used the shoelace area, Euclidean edge-length sum, prism volume and surface-area formulas, and `4n-4` / `12n-12` counts. Every expected value matched within 1e-14 relative/absolute tolerance. A separate literal-source scan sorted points by their explicit integer order and matched every expected outline exactly. No OntoKin compiler, mesher or evaluator was imported for these checks.

The rectangle's area/volume/surface area are 2/1/7 in SI units. The concave bracket's are 5/1.25/13. Editing only its inner corner from (1,1) to (1.5,1) gives area 5.5, volume 1.375 and surface area 13.890388203202207. Declaration-reordered geometry has the same expected local mesh while source revisions and provenance may differ. The pinned library's digest matches its bytes.

The two-instance repair and generated reusable-parts sources were read. The repair changes the `first` occurrence's single coordinate; the sibling and library source stay unchanged. Generated local mount X values are 4, 8 and 12 meters, with an inherited array world offset of -8 meters; final world X origins are -4, 0 and 4 meters before any other placement. Only the first assembly occurrence moves, while the generated assembly's parent motion carries all generated parts.

No blocking contract or expected-value defect was found in this freeze. Runtime behavior, full Agent lifecycle, destination decoding and visual validation are not established by this review.

## Runtime review

### Fixture preparation correction 001

Reviewed root correction commit `677ada2` separately. The initial read-only review did not identify the reserved import alias `parts`; first execution found that parser error and the inherited wrong-unit diagnostic mismatch. Every original freeze entry remains byte-identical. The corrected assembly/generated files only rename the import alias and references to `libparts`. The corrected expected file changes only those selected paths and `wrong-point-unit`'s diagnostic from `OKL-E-TYPE` to the existing `OKL-E-UNIT`. All geometric, physical, motion, numerical tolerance and resource requirements are unchanged. The four corrected file hashes and lengths match their separate manifest. This is an explicit preparation correction, not a silently repaired original fixture or an acceptance relaxation.

### Geometry algorithm review

Reviewed the uncommitted geometry worktree in `/tmp/ontokin-c075-geometry`. At the time of the following probes, `ontokin/extrusion.py` SHA256 was `3a3ea1ea47fd27cb571cdcc0bf180574ab16efbabb3ba784662c5ef0b2f4a160`.

The kernel copies validated finite values, orders by the explicit integer field, rejects duplicate positions and adjacent collinearity, checks nonadjacent crossing/touch/overlap with exact rational predicates, and admits only CCW outlines. Ear clipping excludes points on the closed ear triangle, preventing a diagonal from passing through an unremoved vertex. Emission follows the frozen bottom/top/side sequence, with consistent outward normals, outgoing-edge region selection and sorted region groups. Required corner counts are checked against the remaining aggregate allowance before allocation. Every specified variable-length loop has cooperative checks; callback exceptions escape unchanged.

An independent 42-probe run passed: all 10 frozen valid standalone shapes were checked for volume, surface area, triangle count, opposite oriented edge pairing, outward winding and declaration/palette reorder equivalence; 24 separately generated polar outlines with 3 through 64 vertices were checked against independent area/perimeter/prism totals and edge pairing; and eight separate checkpoint-triggered exceptions retained their exact original exception identity. Three additional assertions passed for alternating outgoing-edge materials, absence of an unused palette primitive and rejection when only 35 of the rectangle's required 36 corners were available. These are reviewer probes, not additions to the product test inventory or full acceptance evidence.

The new constructor/type gates are scoped to declaring .8 modules. New profile membership explicitly inherits execution budgeting and earlier capability sets. Existing geometry-result optimizations do not accept new types and therefore use their ordinary fallback; the existing loft cache is not broadened. GLB dispatch requires matching .8 source/destination selection and the admitted shared work context. The existing supplied-byte reader rejects collapsed or reversed decoded triangles. No blocking algorithm or dispatch defect was identified in the inspected source.

### Exact candidate review closure

Source review is complete for actual published candidate **`d3f0d69b953550b60b5eb0a0b41bc390ba934985`**, tree **`ea880242abd9e323c1d80a46c2b01bdbd35a2aa8`**, against C074 main **`9b9b0c242d8ee02ea7d75ac1805341c1d30d3223`**. The candidate worktree was clean when inspected. The complete changed-input binding is in `c075-review-binding.json`; its canonical 80-input dictionary SHA256 is `4aa2a2a8d4b6eae0afad613488661f1382f079723c729c3abf32d14a2afa54fb`.

The final kernel additionally freezes host-owned native list membership to bounded tuples before later cooperative callbacks. This prevents a callback from appending vertices or materials after their count checks. Source-produced immutable tuples retain their ordinary behavior. A dedicated hostile mutation test exercises the correction. The profile-aware `placed()` error retains prior wording for old profiles and correctly names extrusion in .8.

Reviewed all changed runtime routes: `syntax08` and shared version dispatch; entry-header admission; import-version barriers and declaring-module builtin/type gates; compiler native construction; shared source/profile capability sets; evaluator/recording/independent-reader work context; source-built native scene/GLB dispatch; source-authoritative direct and CLI exports; Agent protocol/service/runtime factories; separate .8 store and context identity; exact file patches; identity-map cache guards; summaries and cursor binding; and discovery/schema selectors. No generic capability widening to earlier declaring modules, automatic version migration, new source authority, ledger replenishment, shared request counter, changed old default, or new implicit physical matter was found in those changes.

The .8 service inherits the established source, accepted-revision, cancellation, retry and publication transactions through explicit class bindings. Its protocol and database identity remain separate from .7, and old binding registries are untouched. New tests cover co-located store isolation, caller cancellation raised during actual polygon construction with the original exception preserved, source-budget reduction under changed host authority, stale/nominal edits, current-policy saved-artifact/run requests, late-publication rollback and binary32 delivery rejection. The corrected destination-failure test appropriately permits retention of an independently valid evaluated prefix while preserving accepted source/artifacts and exposing no delivered artifact. Its earlier failed expectation must remain recorded as development evidence.

The final independent oracle now requires decoded normals to match normalized face cross products, checks bottom and top cap directions explicitly, and verifies that every side triangle follows an authored outline edge. This addresses the review observation that positive dot product alone could accept a tilted unit normal. Hostile oracle tests cover tilted normals, reversed caps, missing triangles, wrong regional appearance and non-authored corners. The independent decoder continues to import no OntoKin runtime. Its quaternion interpolation helper is used only for the frozen identity-carrier rotations; this review makes no new claim about arbitrary quaternion interpolation.

Reviewed the separate destination script's pinned dependency checks, supplied artifact hashes and source revisions, actual Three.js mesh corners/regions/PBR, actual AnimationMixer poses, browser rendering and clipping observations. The script explicitly leaves actual capture review pending; screenshots alone or a script result do not establish a completed human-visible image inspection.

The preservation comparison found **zero removed baseline paths and zero modified original tests, examples, workflows, .7 schemas, execution-budget adoption records, legacy binding registry or original surface kernel**. All 34 original C075 freeze entries remain intact. Newly added tests and fixtures are separately identified; no failed historical gate is relabeled.

**Disposition:** No remaining substantive source-code, authority, geometry, or frozen-expectation blocker was identified. A nonblocking documentation issue was reported to the coordinator: remove the blank line separating row 24 from the existing table in `docs/README.md`, so the new specification link renders as a table row. This can be corrected in evidence publication without changing runtime inputs.

This is source review with the specifically recorded independent probes. It does not assert completion of the full inherited driver, final Agent acceptance, destination executions, visual review, integration, or full feature/product release; the coordinator must bind those separate executed results to this candidate or prove exact relevant input equality.
