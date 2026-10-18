# Surface-0.1 research-prototype validation checkpoint

**Status:** experimentally validated geometry/GLB kernel, not a compiled language release. **Date:** 2026-10-18.

## Version identities

| Item | Verified identity |
| --- | --- |
| Merged branch source revision | [96c12d5a2bd11cc04423c497a7b134539c4e73ce](https://github.com/Omegapy/OntoKin/commit/96c12d5a2bd11cc04423c497a7b134539c4e73ce) |
| Observed successful branch CI | [39105285128](https://github.com/Omegapy/OntoKin/actions/runs/39105285128), four jobs passed |
| Preserved published package | `ontokin-reference` 0.4.0, source-code SHA-256 `2fec4df8a853fb04f05981137165b093dbe5fe72abc1e49ceee15a7747bb4a24` |
| Prospective surface contract | `ontokin "0.3"` / `surface-0.1` in [OK-LANG-003 v0.2](../../language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) |
| Prototype GLB SHA-256 | `b2034d95d2c1d856642be68b29ffee375b918654d3141197654fb6ac1dd5183b` |

## Observed checks at the merged source revision

* Python **3.11, 3.12 and 3.13**: **294 unit tests passed** in each relevant CI job. This combines the retained 276 baseline tests with 18 added geometry, material, GLB and frozen-corpus consistency tests.
* Core source conformance: **43/43** cases, **694** authored assertions. Agent conformance: **A01–A10**, **10/10**. Construction conformance: **C01–C20**, **20/20** for the unchanged 0.4.0 core package and retained independently pinned external destination evidence.
* The new prototype produced a rigid capped, offset elliptical loft with numeric-key ordered **3 sections**, **16 facets**, **96 triangles** and **3 actual PBR material primitives**, not metadata-only region tags.
* The new prototype GLB passed **Khronos format validation with zero errors and warnings**; Three.js loaded **3 material meshes** with group triangle counts **16, 32, 48**. Maximum local vertex float32 error was **2.4439790857755384e-08 m** for the identified fixture. Verified encoded color/metallic/roughness values for all groups.
* Existing GLB/agent/construction visual validation and historical documentation-preservation checks remained passing in the same branch run. The extra GLB validation is an additional prototype-only check, not a reinterpretation of an older format's meaning.

## Reproduction

From repository root, with Python 3.11+ and Node 22/npm:

```bash
python3 -m unittest discover -s tests -p 'test_surface_*.py' -v
python3 -m tools.build_surface_prototype --output-dir /tmp/ontokin-surface-prototype
npm ci --prefix tools --ignore-scripts
node tools/verify_surface_prototype.mjs /tmp/ontokin-surface-prototype/offset-taper.glb --output /tmp/ontokin-surface-validation.json
```

The output uses **hard-coded, independently inspected Python records**, NOT compiled `.ok` source. The `surface-0.1` authored example in [surface-v0.1](../../language-design/surface-v0.1/) is a *prospective* pinned input, currently unsupported in the published parser.

## Open release gates

The source contract and prospective M01–M12 fixtures are adopted, **but none is claimed to pass as an end-to-end native-language case**. Still missing: full 0.3 parser and type integration, keyed `LoftSection`/`SurfaceMaterial` values, reusable source construction/overrides, real local visual binding to animation, versioned `ontokin.glb/0.3` adapter, agent/0.3 paginated inspection and revision repair, independently decoded scene GLB/material/pose and reviewed visual capture, complete composed-source and failure fixtures. No mass, collision, skinning or new dynamics claim follows from this mesh.

The full [GOAL](../../../GOAL.md) remains unfinished.
