---
project: OntoKin
document_id: OK-LANG-003
title: Parameterized Exterior Surfaces and Material Regions
version: 0.2
date: 2026-10-18
status: adopted-language-contract
document_type: normative-language-contract
language_version: "0.3"
profile: surface-0.1
implementation_status: not-implemented
---

# OK-LANG-003: Native exterior surfaces and material regions

## 1. Authority, boundary and history

This is the **adopted source-language and acceptance contract**, not a claim that the compiler or GLB exporter implements it. The original 2026-10-18 design proposal is preserved unchanged at [the proposal archive](../maintenance/contract-proposals/OK-LANG-003-original-proposal.txt). Previous `ontokin "0.1"` / `core-0.1` and `ontokin "0.2"` / `construction-0.1` programs retain their exact original meanings. This contract introduces `ontokin "0.3"` with mandatory `profile "surface-0.1"`. Profile selection is explicit; there is no implicit migration.

The purpose is native, agent-authored, rigid exterior modeling with geometric sections, named PBR material regions, a local visual placement and exact source provenance. It extends the pinned offline module and keyed-construction model of [OK-LANG-002](OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md); its new types are unavailable to old profiles. The broader [GOAL](../../GOAL.md) remains in progress. No collision, mass, inertia, skinning, texture, procedural noise, force or controller support is inferred from a visible surface.

## 2. Source grammar and typed values

All pre-existing `0.2` grammar is available, except that an importer cannot reinterpret an older module under a newer profile. Source units in this gate use version `0.3` and `surface-0.1`. Imported definitions must be part of the exact, hash-pinned offline closure; both `0.3`-profile imports and explicitly compatible `0.2`-profile component imports are permitted. Imported source is compiled under its own declared version and profile. New surface types cannot leak into an older-profile import.

Add exactly two immutable, flat keyed leaf types: `LoftSection` and `SurfaceMaterial`. `Keyed<LoftSection>` and `Keyed<SurfaceMaterial>` are permitted in `0.3` fields, parameters, `let` values and pure function signatures. Their type constructors and surface constructors are:

```ontokin
loft_section(station: Length, center: Vec3<Length>,
             radius_x: Length, radius_y: Length, region: String) -> LoftSection
surface_material(base_color: Color, metallic: Real,
                 roughness: Real) -> SurfaceMaterial
loft(sections: Keyed<LoftSection>,
     materials: Keyed<SurfaceMaterial>,
     facets: Int, caps: String) -> Geometry
placed(surface: Geometry, placement: Pose) -> Geometry
```

These are closed, positional function forms, not host-code hooks or arbitrary user-defined mesh instructions. `caps` is the string literal `"flat"` or `"none"`; other strings and dynamic cap-mode expressions fail explicitly. `loft` accepts only the authored `LoftSection` family, not a pre-baked triangle buffer. `placed` permits at most one explicit local pose for this family; nesting `placed(placed(...))` fails until composition semantics are adopted. The pose frame must be the carrier object's own `self.frame`, including a generated part's frame; `world` or a sibling frame is not silently converted. A nonidentity local translation/rotation affects vertices, not a second simulation node or action authority.

A complete representative class-member source fragment (within a `0.3` module) is:

```ontokin
public class Shell @ "shell" {
    public param rings @ "rings": Keyed<LoftSection> = keyed<LoftSection> {
        "base": loft_section(0[m], vec3(0[m], 0[m], 0[m]), 0.5[m], 0.35[m], "clay"),
        "rim": loft_section(1[m], vec3(0.2[m], 0[m], 0[m]), 0.3[m], 0.25[m], "paint")
    };
    public param palette @ "palette": Keyed<SurfaceMaterial> = keyed<SurfaceMaterial> {
        "clay": surface_material(rgba(0.6, 0.3, 0.2, 1), 0.0, 0.8),
        "paint": surface_material(rgba(0.1, 0.4, 0.8, 1), 0.2, 0.4)
    };
    geometry = placed(loft(self.rings, self.palette, 16, "flat"),
                      pose(self.frame, vec3(0[m], 0[m], 0.1[m]), quat(1, 0, 0, 0)));
    physical = no_body();
}
```

Immutable keyed values preserve the `0.2` key domain, duplicate-key rejection, canonical ASCII iteration, stable identity, ordinary read lookup and public occurrence-override rules. No `Keyed` mutation, indexing assignment or new dynamic loop is introduced. A repair may patch one literal entry in an occurrence-specific parameter override, or replace that complete immutable parameter value as one atomic accepted revision. Repairing an imported shared definition through an occurrence handle is forbidden; the imported library's bytes and sibling occurrences are unchanged.

## 3. Geometry definition and topological invariants

The local coordinate system is right-handed, meters, with **+Z as the loft axis**. A section with station `z`, center `vec3(cx, cy, 0[m])`, and positive `rx, ry` defines the ellipse
`p(z, θ) = (cx + rx cos θ, cy + ry sin θ, z)`, for `0 ≤ θ < 2π`. All five input values are immutable dimensional/typed source values. Exact +0 and -0 compare equal for station ordering. Only the X/Y center components are allowed to differ from zero; a nonzero Z component is a frame/geometry error. There is no implicit auto-rotation to a different long axis.

Sections are **sorted by numeric station**, never source order or section key. Stations must be strictly increasing with adjacent separation at least `0.001[m]`. Equal stations are rejected even when keys differ. Surviving authored section keys and material keys remain stable across insertion, removal and input reordering. Their triangle/vertex offsets are derived output and are not stable identifiers.

At station `i`, circumference vertices are `θ_j = 2πj/N` for `j=0..N-1`, with `N=facets`. Between consecutive rings, construct exactly two triangles per angular segment with outward winding `(lower_j, lower_{j+1}, upper_j)` and `(lower_{j+1}, upper_{j+1}, upper_j)` (angular indices modulo `N`). A `"flat"` loft closes the lower end with outward -Z normal and the upper end with outward +Z normal using fan triangles and no degenerate central vertex triangles. `"none"` exports open ends and makes **no volume/solid** claim. The surfaces are geometrically edge-matched by position. Because flat shading duplicates triangle corners, the index buffer is not welded and no index-manifold guarantee is made. The flat variant has two geometric end caps; the none variant stays open.

This first gate deliberately chooses **flat-shaded triangle normals**: each triangle has three independent corner vertices and the normalized outward face cross product. The cap normals are exactly `(0,0,-1)` and `(0,0,1)` before local placement; the placement rotation transforms them. Material changes are allowed at station boundaries without smoothing ambiguities. A nonfinite or zero-area triangle is an explicit numerical failure. No unstated watertight-volume estimate is introduced for open profiles.

For `S` sections and `N` facets, side triangle count is `2(S-1)N`; flat end caps add `2N` triangles, so a closed loft has `2SN` triangles and `6SN` independent triangle-corner vertices. An open loft has `2(S-1)N` triangles and `6(S-1)N` vertices. Positions and normals are authored geometry, not automatically physical matter.

## 4. Material regions and rigid visual binding

A `SurfaceMaterial` stores a linear RGBA `Color`, a metallic factor and roughness factor, each a finite number in `[0,1]`. A region is identified by its keyed palette name; every section's `region` string must resolve exactly to one palette key. Extra unused palette entries are permitted and appear only as source/inspection values, not empty glTF primitives.

The material assigned to each side interval is the **lower station's region**; the lower cap uses the first section's region and the upper cap uses the last section's region. A region that covers disjoint intervals remains one stable source region and one material identity for this mesh. Output groups contain real triangle indices and serialized PBR factors. A palette edit changes material factors in the affected output primitive(s), not mere metadata. A station-region edit changes the prescribed triangle group membership without changing positions, unless another section value also changes.

`loft` returns a rigid visual Geometry recipe. A single `placed` call defines local placement relative to its carrier object's `self.frame`. The carrier's evaluated world transform drives its mesh in animation. Neither the loft nor its visual offset adds an object, follows another frame, installs a joint, contributes physical mass, starts an action or changes the object motion mode. Existing prescribed actions, supported connections and sphere gravity/release retain their versioned mechanical limits.

## 5. Numeric limits and deterministic errors

These restrictions are fixed **before implementation** and apply alongside existing construction work, source, time, object, GLB, mesh and result-envelope caps. They are not performance guarantees.

| Property | Adopted `surface-0.1` bound |
| --- | --- |
| Section count per loft | `2..64` |
| Distinct palette keys per loft | `1..16` |
| Angular facets | `8..64`, divisible by 4 |
| Station `z` / center X,Y | Each finite and within `[-100, 100] m` |
| Adjacent station separation | At least `0.001 m` |
| Radii X,Y | Each finite within `[0.001, 100] m` |
| Center Z | Exactly `0[m]` |
| Material RGBA, metallic, roughness | All finite in `[0,1]` |
| Triangles / vertices per closed loft | At most `8192` / `24576` |
| Aggregate generated mesh vertices | Existing `250000` cap, charged before large allocation |
| Binary delivery | Existing `64 MiB` GLB limit, with no silent output truncation |

Resource use includes repeated instances, even if their source values share memory. Precompute the predicted triangle and vertex counts before materializing the arrays. Enforce aggregate budgets and cooperative cancellation during generation, grouping and serialization. Cancellation or an over-limit input never returns a successful partially generated mesh. The accepted program revision is preserved if generation/evaluation/export fails.

Use stable typed diagnostics, with source-unit identity, span, occurrence identity and details where available. Baseline syntax/type/unit/identity/access errors remain unchanged. Add `OKL-E-SURFACE-SECTION` (section count or invalid definition), `OKL-E-SURFACE-STATION` (non-finite/out-of-range/duplicate/insufficient separation), `OKL-E-SURFACE-RADIUS`, `OKL-E-SURFACE-CENTER`, `OKL-E-SURFACE-REGION` (missing palette entry), `OKL-E-SURFACE-MATERIAL`, `OKL-E-SURFACE-FACETS`, `OKL-E-SURFACE-CAPS`, `OKL-E-SURFACE-PLACEMENT` and `OKL-E-SURFACE-NUMERIC`. Existing `OKL-E-RESOURCE` applies to aggregate work/mesh limits. Each error names the actual invalid value/key, except when sensitive output budgets require bounded truncation.

## 6. Accuracy and inspectable delivery contracts

The generator computes in binary64, then the named **`ontokin.glb/0.3`** adapter serializes float32 positions/normals and true glTF 2.0 PBR material groups. The generator's analytic station-ring coordinate difference must be at most `1e-10 m` in local binary64 for fixtures with all coordinates at most `10 m`. Each flat face normal has length within `1e-12` of 1 in local binary64. Per-axis float32 *local vertex* quantization error must be at most `1e-5 m` for generated local vertices with coordinates in `[-100,100] m`; failures are reported, not silently clamped. These are **per-fixture prescribed tolerances**, not guaranteed visual accuracy in arbitrary unbounded world coordinates.

Angular meshing approximates ideal ellipses; the specification does not claim exact curved geometry. A constant-radius round section of radius `R` has ideal-to-polygon radial sagitta `R(1-cos(π/N))`. Any more general loft error must be independently compared against the ideal piecewise-affine elliptical surface at declared samples and tolerances, rather than inferred from this circle formula. No unconditional volume-error or smooth-surface normal promise is made.

Extend the existing `ontokin.agent/0.2` program revision semantics under the separately versioned `ontokin.agent/0.3` contract. Ordinary object inspection returns section keys, ordered stations, profile, palette names, placement and geometric count summaries, without unbounded vertex arrays. A read-only `surface.mesh_page` request selects accepted program revision, occurrence identity, optional region filter, and an integer count (1..256), then returns stable-revision pages of positions, normals and triangle indices plus the next cursor or end. Cursors bind revision, occurrence, profile and ordering; stale revision or changed geometry invalidates the cursor rather than mixing pages. Agent edits still target authorized source spans, not derived vertex indices.

GLB/0.3 metadata identifies the program bundle revision, source declaration/occurrence identities, section ordering, regional material mapping, caps/facets, local visual transform, target profile, limitations and any quantization loss. Decoding must prove exported triangle count, winding, material assignment, color/metallic/roughness, physical/nonphysical semantics and world-space animation at fixed independently sampled times. Multiple primitives within one logical mesh are required; one material per node does not satisfy this contract. Asset-specific Python mesh generation outside the language is not valid source-conformance evidence.

## 7. Frozen acceptance matrix, release rule and omissions

The adopted **M01–M12** suite is frozen in [surface-v0.1/acceptance.json](surface-v0.1/acceptance.json) with fixed oracle values, boundary inputs, expected errors, composition and held-out variants. A sample source in that folder is an authored fixture, **not** a currently executable supported `0.2` program. Tests must compare independently derived geometry and animation expectations to actual `.ok` compilation and decoded glTF destination, and must run alongside all prior core/agent/construction regression suites.

| Case | Required implementation gate |
| --- | --- |
| M01 | Exact constant circular and elliptic ring geometry; finite normals, winding, count and closed prism volume. |
| M02 | Taper plus offset, explicit geometric sorting independent of source keys; caps and nondegenerate faces. |
| M03 | Independently measured circular angular approximation, binary64 ring coordinates and float32 export error. |
| M04 | Real regional triangle indices and decoded PBR material values; isolated palette change. |
| M05 | One hash-pinned library reused in two structurally different complete exterior compositions. |
| M06 | Held-out station counts, facets, proportions and generated-part numbers fixed prior to evaluation. |
| M07 | Revision-safe single-occurrence section/material repair; unchanged siblings and imported library bytes. |
| M08 | Section insertion/removal preserves surviving authored keys but changes derived geometry as expected. |
| M09 | Local visual placement, inherited rigid animation and existing mechanical release numerically agree. |
| M10 | Duplicate/near stations, invalid dimensions/frames/regions, cap/facet and aggregate budget failures; cancellation. |
| M11 | Independent GLB/0.3 geometry/material/pose decode and browser capture on identical program/artifact identities. |
| M12 | All original `0.1`, `0.2`, GLB/0.1, GLB/0.2, agent and construction gates still pass. |

**Adoption status:** The contract and case IDs are adopted here. **No M-case is marked passed by adopting text or fixtures.** A release gate can close only after compiled language source (including unseen variants), tests, independent destination and visual validation, actual agent repairs, and identified GitHub CI demonstrate the cases. Rejected and repaired candidates must retain exact byte hashes, no silent source migrations, and correct target contract labels.

**Still excluded:** Subdivision/freeform NURBS, smooth normals and UV textures; automatic mesh mass/collision; deformation, skinning, contact and dynamics; branching inside one loft; arbitrary external engines or engine-side live simulation; performance or authoring-benefit benchmarks; worlds/terrain/fluids/creatures at full-product scale. Each remains a future versioned goal rather than being quietly dropped.
