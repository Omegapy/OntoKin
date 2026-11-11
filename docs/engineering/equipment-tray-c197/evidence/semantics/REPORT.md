# C197 semantic feasibility review

**Finding:** the existing language has the required mechanisms for a minimal static two-tray assembly. This review identifies no required language semantic extension. It does **not** establish that an existing common Blender construction path admits trays; that separate gate must pass before qualification exports.

Reviewed source: `6cbcf9c8c136659def1aac94829330cb81872511`, tree `13eb2463217d3021c7783c6c6d8be749e8c2e145`. The fixed actual-main checkout was clean. `REPORT.json` binds 17 inspected specifications, implementation files, examples and test/evidence definitions by SHA-256 and Git blob. This was static source research: no program was authored or executed, no native output was created and no tests were rerun.

## Feature-to-implementation map

| Need | Existing mechanism and evidence | Disposition |
| --- | --- | --- |
| Typed dimensions and frames | `Length`, `Vec3<Length>`, `FrameRef`, `Pose`, dimension-checked arithmetic, millimetre/centimetre/metre literals; right-handed world with +Y up. `pose` requires a length triple; `box` requires three positive full extents. | Supported by adopted spec and current code. Actual tray dimensions/frames remain to be frozen. |
| Reusable tray definition | A `core-0.1` local class can declare the five box components and payload proxy once and be instantiated twice. `construction-0.1` additionally supports reusable package/version/SHA-256-pinned modules, ordinary parts and keyed parts. | Existing source mechanism; the actual tray source and dependency closure are not yet qualified. |
| Independent left/right instances | Occurrence keys determine identity paths. Each occurrence expands its own children and overrides. An occurrence-local public parameter override does not edit the shared class or its sibling. | Supported by spec and current registration/override code; eventual output preservation still requires measurement. |
| Derived geometry | Typed immutable parameters and `derive` expressions can calculate box sizes and frame offsets with `+`, `-`, `*`, `/`. Pure dependencies must be acyclic; derived values cannot be overwritten as instance parameters. | Existing operators support the proposed static partition below. No tray composition has been run. |
| Common delivery | The real construction binding names `ontokin.agent/0.2`, source `0.2` / `construction-0.1` and native `ontokin.glb/0.2`. | A native OntoKin exporter is observed. A common Blender constructor for both routes is **not established by this review**. |
| Independent checking | Existing construction export tests read delivered `POSITION` accessors, node poses and stable identities, then compare geometry with independent expected values. | Useful existing reader primitives; not a frozen tray clearance/sibling checker or proof of both-route qualification. |

### Dimensions, frames and physical meaning

[The adopted types and frame rules](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/OK-LANG-001-core-language-specification.md#L200-L279) define dimensioned lengths, compatible arithmetic, explicit frame identities and +Y-up coordinates. [The validator implementation](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/ontokin/validator.py#L838-L876) enforces typed poses and positive full box dimensions; [the value layer](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/ontokin/values.py#L424-L502) performs dimensional arithmetic.

Keep the static formulation explicit. An empty tray container owns its component parts, but ownership does not place them. Each component needs an explicit `follow` relation from the tray frame with its offset expressed in that exact frame. A relation-controlled child must not also have an authored `placement`; the root tray placement is world-relative. [Core geometry and following rules](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/OK-LANG-001-core-language-specification.md#L353-L395) and [resolve_follow](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/ontokin/validator.py#L969-L984) supply these distinctions.

The proposed geometry uses `no_body()` and prescribed static poses. Core box geometry has no box-body model: it does not establish cuboid mass, contact or inertia. The parent container contributes no surface or physical matter. [Mass and ownership rules](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/OK-LANG-001-core-language-specification.md#L424-L428) retain one occurrence count per represented body; no physical claim is introduced by these static visible parts.

### Reuse and preservation

[Core occurrence identity and override rules](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/OK-LANG-001-core-language-specification.md#L283-L319) already permit two independent occurrences of one reusable local class. For a separately versioned component library, [the construction contract](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md#L54-L178) adds exact offline dependency closure, pinned source bytes and distinct definition/occurrence identity. The current [compiler registration and overrides](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/ontokin/construction.py#L2860-L2942) register each part under its owner and retain its own initializer bindings.

The retained [Rack entry](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/construction-v0.1/01-keyed-rack/main.ok) and [pinned component module](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/docs/language-design/construction-v0.1/01-keyed-rack/hinges.ok) show a complete example of imported reuse, derived dimensions, explicit parent frames and a scoped override. The [existing test](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/tests/test_construction_catalog.py#L225-L241) checks that the selected first blade is 0.75 m while the corresponding second blade remains 0.6 m. This is inspected source and prior example evidence, not a fresh tray test result.

## A non-overlapping geometric partition

The following is a mathematical feasibility construction, **not a frozen task or executable trial**. Let cavity width, depth and wall height be `W`, `D`, `H`; wall thickness `t`; base thickness `b`. All are positive lengths. Set the cavity floor at local `Y=0`, with width on X and depth on Z.

| Component | Full dimensions `(X,Y,Z)` | Local center `(X,Y,Z)` |
| --- | --- | --- |
| Base | `(W+2t, b, D+2t)` | `(0, -b/2, 0)` |
| Front wall | `(W+2t, H, t)` | `(0, H/2, (D+t)/2)` |
| Back wall | `(W+2t, H, t)` | `(0, H/2, -(D+t)/2)` |
| Left wall | `(t, H, D)` | `(-(W+t)/2, H/2, 0)` |
| Right wall | `(t, H, D)` | `((W+t)/2, H/2, 0)` |

The base occupies `-b ≤ Y ≤ 0`; walls occupy `0 ≤ Y ≤ H`. Front/back walls own the corner strips because they span the full outside width. Left/right walls stop at the cavity front/back planes. Thus the solid interiors are disjoint; meeting faces have zero volume. No subtraction, Boolean solid operation, importer or new geometric primitive is required to express these five cuboids.

A named rectangular payload proxy can derive the cavity as `W = payload_width + 2 × clearance` and `D = payload_depth + 2 × clearance`. The later task must explicitly define vertical fit, proxy placement, supported size selection, exact preserved source fields and output tolerances. Those choices are not silently fixed here.

## Admission boundary

The language may express this static family, but that alone does not satisfy C197. The [existing native binding](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/ontokin/program_bindings.py#L24-L38) and [independent native export checks](https://github.com/Omegapy/OntoKin/blob/6cbcf9c8c136659def1aac94829330cb81872511/tests/test_construction_export.py#L24-L77) establish an OntoKin-to-GLB path with inspectable identities. Common GLB format or later Blender import is insufficient to establish equal construction meaning with direct Blender/Python. The backend review must identify the actual shared constructor and mappings or require a bounded versioned proposal.

A tray-specific independent reader must eventually measure actual delivered vertices/transforms, cavity clearance and unchanged sibling geometry/identities, and reject the two frozen delivered-content controls. None of those tray qualification outcomes is claimed here.

The inherited legacy driver and supplemental tail remain **FAILED**, with **4,239 distinct passing methods and thirteen torque-read methods NOT RUN**. There were zero native exports, simulations, receiving jobs or timed authors in this review. All broader product and release gates retain their prior status.
