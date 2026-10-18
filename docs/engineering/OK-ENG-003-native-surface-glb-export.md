---
project: OntoKin
document_id: OK-ENG-003
title: Native surface GLB export
version: 0.1
date: 2026-10-18
status: implemented-reference-adapter-release-gate-tracked-separately
target_contract: ontokin.glb/0.3
source_profile: surface-0.1
---

# Native surface GLB export

## Purpose and authority

The `ontokin.glb/0.3` adapter turns actual `ontokin "0.3"` / `surface-0.1` source programs into embedded glTF 2.0 geometry, regional PBR materials and recorded rigid animation. The [adopted OK-LANG-003 contract](../language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) remains authoritative for surface meanings, fixed limits and M01–M12 acceptance. This engineering record documents one implemented delivery stage; [STATUS](../../STATUS.md) identifies the tested revision, independent destination results and remaining gates.

The adapter uses the existing pinned module compiler and evaluator. No asset-specific Python geometry is substituted for authored lofts. The earlier [GLB/0.1 engineering contract](OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) and GLB/0.2 program provenance retain their meanings. Package version 0.4.0 is unchanged; source version, agent protocol and delivery contract are separate identities.

## Run an authored program

From the repository root, Python 3.11 or later can export the exact pinned studio example:

```bash
python3 -m ontokin export docs/language-design/surface-v0.1/program.files.json --bundle --target ontokin.glb/0.3 --output /tmp/ontokin-studio.glb
```

The [file manifest](../language-design/surface-v0.1/program.files.json) lists the unchanged entry and library source. Import version/content pins are checked against those actual bytes. Paths resolve inside the manifest directory. There is no network package lookup or implicit source migration.

A complete source file without imports can use:

```bash
python3 -m ontokin export model.ok --target ontokin.glb/0.3 --output /tmp/model.glb
```

Successful export writes the GLB and its `.export.json` evidence sidecar. The report records the complete program revision, entry source revision, artifact SHA-256, implementation digest, options, measured numerical errors and limits. Source, manifest, imported files, GLB and report must not alias one another through paths, symbolic links or hard links. Outputs are staged before replacement. Each replacement is atomic; the report/artifact hash establishes pairing after an interrupted two-file write.

The default `export FILE.ok` command still selects GLB/0.1. GLB/0.2 can be selected explicitly for `construction-0.1` input. A mismatched source profile or target fails. Generic delivered-level checking still lacks a destination contract and remains unsupported.

Python callers use `compile_construction(bundle, level="evaluated").model`, then `export_glb(model, target_contract="ontokin.glb/0.3", options=ExportOptions(...), check=callback)`. `load_bundle` and `load_file_manifest` retain the existing exact-source bundle interfaces. The optional no-argument callback can stop work by raising an exception. Export propagates that exception and returns no partial success.

## Geometry and material delivery

`ontokin/scene.py` lowers each authoritative loft recipe with `ontokin/surface_runtime.py` and the native bounded surface generator. It applies the one authored local visual pose to positions and normals. Each carrier remains one root scene node with the evaluator's world translation and rotation tracks. Source ownership stays metadata; it does not multiply transforms. Visual geometry adds no physical mass, collision shape, joint or motion authority.

The serializer writes a single logical mesh for each surface occurrence. All its region primitives share position/normal attributes and have separate actual triangle index arrays. Numeric station order governs topology. Side intervals use the lower station's region; end caps use their endpoint regions. Disjoint intervals with the same key form one region primitive. Unused palette entries remain in source metadata and do not create empty primitives.

Each used region has a distinct source material identity, even when two regions have equal color and PBR factors. glTF materials carry the authored linear RGBA `baseColorFactor`, `metallicFactor` and `roughnessFactor`; alpha below one selects `BLEND`. A palette edit changes serialized material factors. A station-region edit changes index membership. Older sphere/box objects keep their existing material defaults.

Node metadata retains the bounded source recipe, ordered keys/stations, facets, caps, region counts, local placement, source locations, occurrence identity and complete pinned program revision. Material metadata also identifies its region, occurrence and program. Exact source files remain authoritative; derived triangle offsets are not editable stable identities.

## Bounds and cancellation

The existing language limits remain fixed: 2–64 sections, 1–16 palette entries, 8–64 facets divisible by four, and at most 8,192 triangles/24,576 corners in one closed loft. A closed loft has `2*S*N` triangles and `6*S*N` independent corners. An open loft has `2*(S-1)*N` triangles and `6*(S-1)*N` corners.

Surface-profile exports precompute the aggregate mesh cost per occurrence, including repeated identical geometry and optional visual helpers. They enforce the 250,000-vertex cap before constructing large output arrays. Binary buffer growth is checked before row conversion/allocation, and final JSON plus binary must fit 64 MiB. A smaller configured/testing cap does not silently reduce output.

Cooperative checks cover scene construction, surface generation/grouping, local placement, evaluator samples, float conversion, binary rows, JSON encoding, decoded validation and final return. Callback exceptions, including `ValueError`, are preserved instead of being converted into malformed geometry errors. The existing finite-work caps still apply when no callback is supplied.

## Numerical and source validation

The adapter reads its actual JSON/BIN bytes back and compares them with the supplied compiled model. Surface positions and normals must match deterministic float32 conversion of the source mesh and its single local placement. Region keys, triangle indices/winding, cap topology, PBR factors and source/bundle/occurrence metadata are checked explicitly. The bounded reader also rejects degenerate triangles, inconsistent normal directions and invalid PBR factors.

Surface local vertex error must not exceed `0.00001 m`, or the caller's stricter position tolerance. Relaxing animation tolerance cannot weaken this surface gate. The adapter reports actual quantization loss in the GLB metadata and sidecar. It does not clamp coordinates to obtain a passing result. Larger local visual offsets can fail float32 precision even when source construction succeeds.

Animation uses the existing exact boundary timestamps and bounded sample clock. Fresh evaluator samples are compared with decoded LINEAR translation and quaternion interpolation at source/stored keys, interior probes and both sides of semantic boundaries. Default playback tolerances remain `0.001 m`, `0.001 rad` and `0.000001 s`. Finite probes do not establish continuous accuracy for every possible source program.

## Independent destination evidence

The native source builder and separate verification tools extend the existing pinned development toolchain:

```bash
python3 tools/build_surface_demo.py --output-dir /tmp/ontokin-native-surfaces
npm ci --prefix tools --ignore-scripts
node tools/verify_surface_native.mjs --demo-dir /tmp/ontokin-native-surfaces --output /tmp/ontokin-native-destination.json
node tools/node_modules/playwright/cli.js install chromium --only-shell --with-deps
node tools/verify_surface_viewer.mjs --demo-dir /tmp/ontokin-native-surfaces --output-dir /tmp/ontokin-native-browser
```

The corpus contains the unchanged pinned studio, fixed analytic and regional-material cases, all four predetermined held-out section/facet variants and an independently moving carrier with nonidentity local surface rotation. JavaScript independently computes ring points, regional oriented triangles and carrier motion, then compares decoded buffers and Three.js world poses. Khronos validation checks glTF structure. Browser checks capture front, side and animated views with source/artifact identities and exercise playback controls.

Those scripts must actually run against the identified implementation. Their presence is not evidence of a passing destination gate. The exporter sidecar continues to state that destination validation is separate. GitHub Actions retains the prior core, agent, construction, prototype, GLB and browser checks and adds this native path.

## Remaining acceptance

Native GLB delivery does not complete `ontokin.agent/0.3`, revision-bound mesh pagination, the complete M01–M12 agent repair/composition corpus, or the full [GOAL](../../GOAL.md). Agent/0.3 is the next implementation gate. Texture coordinates, smooth surfaces, deformation/skinning, contacts, general rigid dynamics, controllers, live destination behavior and the remaining product domains stay open. Blender import, game-engine integration and measured authoring-efficiency claims require their own identified evidence.
