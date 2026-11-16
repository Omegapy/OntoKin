# Geometry and appearance workflows

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Add opaque image labels to native surfaces

Explicit source `0.13` / `textured-surfaces-0.1` attaches content-pinned offline PNG images to keyed material regions on existing native surfaces. Author an affine planar mapping in recipe-local coordinates, bind an image by stable asset ID and exact digest, and retain the underlying geometry, rigid placement and recorded motion. The [authoring guide](../../docs/language-design/textured-surfaces-v0.1/README.md) and [versioned decision](../../docs/language-design/textured-surfaces-v0.1/ADOPTION.md) define image orientation, color multiplication, immutable bundle/files `0.2`, and bounded decoding.

```bash
python3 -m ontokin export examples/textured-surfaces/rgb-panel.files.json --bundle --target ontokin.glb/0.13 --output /tmp/ontokin-textured-panel.glb
python3 -m ontokin agent --protocol ontokin.agent/0.13 --store /tmp/ontokin-textures-agent
```

The [Agent/0.13 interface](../../docs/language-design/agent-v0.13/README.md) supports atomic source-and-image repair, exact image byte retrieval, and texture-aware surface inspection through a separate durable store. Bundles admit at most four opaque RGB/RGBA PNGs, each at most 256 by 256 pixels and 300,000 encoded bytes. Sampling is nearest with clamp-to-edge addressing. Ordinary limits remain 100,000 operations / 30,000 ms; larger requests require independent current host authorization. This experimental appearance scope adds no mass, collision, deformation or motion authority. [STATUS](../../STATUS.md) distinguishes actual verification and integration from the remaining release gates.

## Author recessed trays, panels and housings

Explicit source `0.12` / `polygon-pockets-0.1` creates a constant polygon exterior with up to eight independently keyed blind pockets. Each pocket names its clockwise boundary, depth and floor material. The [versioned decision](../../docs/language-design/polygon-pockets-v0.1/ADOPTION.md) defines the exact remaining-base arithmetic, rounded floor, complete bottom/top/wall/floor surface, and actual delivered-coordinate checks.

```bash
python3 -m ontokin export examples/polygon-pockets/rectangular-pocket.ok --target ontokin.glb/0.12 --output /tmp/ontokin-pocket.glb
python3 -m ontokin agent --protocol ontokin.agent/0.12 --store /tmp/ontokin-pockets-agent
```

The [authoring guide](../../docs/language-design/polygon-pockets-v0.1/README.md), [independent frozen inputs](../../examples/polygon-pockets/README.md) and [Agent/0.12 interface](../../docs/language-design/agent-v0.12/README.md) cover reusable definitions, one-instance depth repair, bounded inspection and recorded delivery. There are at most 64 authored vertices overall and 16 materials. Every pocket leaves at least canonical binary64 0.001 meter of base. Ordinary execution defaults remain 100,000 operations / 30,000 ms. Visual geometry adds no physical body or collision authority; measured checks and remaining gates are identified in [STATUS](../../STATUS.md).

## Author bent ducts and handles with explicit section frames

Explicit source `0.11` / `framed-polygon-loft-0.1` places each keyed polygon section in its own rigid `Pose` within the consuming object's frame. Matching ring and vertex identities can form bent solid bodies, hollow elbows and finite handles. The [versioned decision](../../docs/language-design/framed-polygon-loft-v0.1/ADOPTION.md) defines exact section transforms, fixed strip triangles, endpoint caps and complete source and delivered-mesh checks. Each frame is authored; the language does not infer a path or transport its orientation.

```bash
python3 -m ontokin export examples/framed-polygon-lofts/hollow-elbow.ok --target ontokin.glb/0.11 --output /tmp/ontokin-elbow.glb
python3 -m ontokin agent --protocol ontokin.agent/0.11 --store /tmp/ontokin-framed-loft-agent
```

The [authoring guide](../../docs/language-design/framed-polygon-loft-v0.1/README.md), [frozen inputs](../../examples/framed-polygon-lofts/README.md) and [Agent/0.11 interface](../../docs/language-design/agent-v0.11/README.md) describe source repair, bounded inspection and recorded delivery. Limits remain 2–8 sections, up to eight holes, 64 vertices per section and 256 total. Origins and authored XY components stay within ±100 meters; adjacent origins must advance along both neighboring frames' positive Z axes. `FramedLoftAgentService` uses a separate durable store. Ordinary defaults remain 100,000 operations / 30,000 ms. This is experimental visual geometry and recorded carrier motion; the full product and release gates remain in [STATUS](../../STATUS.md).

## Author tapered polygon forms and hollow ducts

Explicit source `0.10` / `polygon-loft-0.1` connects 2–8 keyed polygon sections at increasing Z stations. Matching ring and vertex identities support changing cross-sections, concave forms and up to eight through-holes, with separate cap and strip materials. The [versioned decision](../../docs/language-design/polygon-loft-v0.1/ADOPTION.md) defines the actual fixed diagonal triangles; it does not promise linear interpolation of planar cross-sections.

```bash
python3 -m ontokin export examples/polygon-lofts/hollow-frustum.ok --target ontokin.glb/0.10 --output /tmp/ontokin-duct.glb
python3 -m ontokin agent --protocol ontokin.agent/0.10 --store /tmp/ontokin-loft-agent
```

The [authoring guide](../../docs/language-design/polygon-loft-v0.1/README.md), [frozen examples](../../examples/polygon-lofts/README.md) and [Agent/0.10 interface](../../docs/language-design/agent-v0.10/README.md) describe the contract. `RingLoftAgentService` supports exact source edits, bounded section and triangle inspection and recorded GLB retrieval. Limits are 64 vertices per section and 256 across all sections. Each source mesh and its delivered binary32 coordinates must retain a closed, nonintersecting surface and outward normals. Defaults remain 100,000 operations / 30,000 ms; the largest examples explicitly request separately authorized higher budgets. This is experimental visual geometry, with no implicit mass, collision shape or live destination physics.

## Author plates, slots and through-holes

Explicit source `0.9` / `polygon-holes-0.1` adds one keyed outer ring and up to eight keyed inner rings. Use it for slotted plates, bolt holes and hollow cross-sections, with separate cap and wall materials, reusable parts and rigid local placement. The [versioned decision](../../docs/language-design/polygon-holes-v0.1/ADOPTION.md) requires counterclockwise outer boundaries, clockwise holes, strict separation and at most 64 vertices across all rings. Coordinates remain within ±100 meters and depth within 0.001–100 meters.

```bash
python3 -m ontokin export examples/polygon-holes/slotted-bracket.ok --target ontokin.glb/0.9 --output /tmp/ontokin-slot.glb
python3 -m ontokin agent --protocol ontokin.agent/0.9 --store /tmp/ontokin-holes-agent
```

The [source examples](../../examples/polygon-holes/README.md), [Agent/0.9 schemas](../../docs/language-design/agent-v0.9/README.md) and [C076 engineering record](../../docs/engineering/polygon-holes-2026-10-30-c076/README.md) identify the contract and measured verification separately. `ontokin.holes_agent.HolesAgentService` supports source repair, bounded ring/triangle inspection and exact GLB retrieval. Source-valid geometry whose openings cannot survive delivered 32-bit coordinates fails export explicitly. The ordinary 100,000-operation / 30,000-ms defaults remain unchanged; the largest fixture requests a separately authorized higher budget. This is experimental visual geometry and recorded animation, with no implicit mass or collision shape.

## Author polygon plates and concave brackets

Explicit source `0.8` / `polygon-extrusion-0.1` adds closed extrusions from typed, keyed XY outlines. An agent can author a rectangular plate or concave bracket, reuse a class with different dimensions, edit one instance, inspect its triangles and retrieve recorded GLB/0.8 output. Separate cap and side materials and rigid local placement are supported. The [versioned decision](../../docs/language-design/polygon-extrusion-v0.1/ADOPTION.md) fixes 3–64 vertices, coordinates within 100 meters and depth from 0.001 to 100 meters. Self-intersections, holes, bevels and implicit mass/inertia are excluded.

```bash
python3 -m ontokin export examples/polygon-extrusions/concave-bracket.ok --target ontokin.glb/0.8 --output /tmp/ontokin-bracket.glb
python3 -m ontokin agent --protocol ontokin.agent/0.8 --store /tmp/ontokin-extrusion-agent
```

The [examples](../../examples/polygon-extrusions/README.md), [Agent/0.8 schemas](../../docs/language-design/agent-v0.8/README.md) and [C075 engineering record](../../docs/engineering/polygon-extrusions-2026-10-30-c075/README.md) distinguish the selected contract from actual verification and integration. The Python service is `ontokin.extrusion_agent.ExtrusionAgentService`. It inherits source-requested execution budgets, host authorization, exact source edits and atomic publication. The ordinary 100,000-operation / 30,000-ms defaults stay unchanged. This is experimental development; recorded playback does not establish live engine physics.

## Export native exterior surfaces

The [OK-LANG-003 surface contract](../../docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) defines typed keyed sections, material regions and rigid local placement. Its pinned studio source now compiles through the native language and produces two actual animated, multi-material meshes:

```bash
python3 -m ontokin export docs/language-design/surface-v0.1/program.files.json --bundle --target ontokin.glb/0.3 --output /tmp/ontokin-studio.glb
```

For a complete source without imports, use `python3 -m ontokin export model.ok --target ontokin.glb/0.3 --output /tmp/model.glb`. The [native export guide](../../docs/engineering/OK-ENG-003-native-surface-glb-export.md) explains pinned bundles, local transforms, PBR properties, source identities, resource limits, cancellation and independent validation.

The [M01–M12 fixtures](../../docs/language-design/surface-v0.1/acceptance.json) remain the full surface-release acceptance contract. The [release procedure](../../docs/engineering/OK-ENG-004-native-surface-release-conformance.md) connects actual agent edits, composed source programs, delivered GLBs and current regression evidence. The [earlier Python-input workbench](../../prototypes/surface_v01/README.md) remains preserved as historical prototype evidence.

## Inspect and repair a native surface program

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.3 --store /tmp/ontokin-surface-state
python3 tools/build_surface_agent_demo.py --output-dir /tmp/ontokin-surface-agent
```

The first command serves an agent's own versioned JSONL requests. [OK-AGENT-003](../../docs/engineering/OK-AGENT-003-native-surface-program-workflows.md) defines the operations and schemas. A `surface.mesh_page` request returns at most 256 complete triangles from an identified accepted program and object occurrence. It exposes carrier-local positions, normals and material-region keys, and binds continuation cursors to that exact geometry and implementation. Section and material edits remain edits to authoritative `.ok` bytes.

The second command runs the fixed acceptance workflow: reject an invalid radius, repair one occurrence, change one palette region, insert/reorder/remove a keyed section, evaluate motion, and retrieve actual GLB bytes through the service. It also exports the predetermined dimensional variants, ordinary and generated compositions, and a rotated release. Its output retains source snapshots and every request/response for independent verification. It generates geometry through native source operations; the driver supplies no prepared mesh.
