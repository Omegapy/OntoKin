# OntoKin

**An AI-native semantic language for constructing, inspecting, repairing and transporting physically meaningful 3D objects.**

OntoKin (pronounced **ON-toh-kin**) gives an agent editable `.ok` source that names parts, records dimensions and units, declares physical properties and keeps source identities. Its normalized intermediate representation is the structured object description used between that source and destination tools. Accepted source remains authoritative; a delivered mesh is one checked result of it.

For example, an agent can change one finger in a reusable rack assembly while preserving its sibling, reject a value with the wrong unit, and regenerate geometry tied to the accepted source revision. Existing geometry, materials, bounded reference physics, atomic source edits and GLB/Blender work remain available under their named profiles.

Engines and specialist tools provide rendering, general simulation and gameplay. Unreal Scene Graph and Verse are intended integration targets; their runtime behavior belongs to the destination. The [Unreal boundary](docs/engineering/semantic-export-c210/UNREAL-INTEROP.md) records conceptual mappings and current documentation limits. It does not claim an implemented Unreal importer.

## Continue from the current checkpoint

Read [STATUS.md](STATUS.md) for exact publication and ownership, the [C210 scope decision](docs/engineering/semantic-export-c210/DECISION.md), and the [C219 finite receiving decision](docs/engineering/receiving-decision-c219/DECISION.md). The fixed Blender experiment retains authoritative source, checked native geometry with disclosed shading loss, useful views and observed save/reopen persistence. The strict normal gate and historical failed regressions remain failed. [C220](docs/engineering/second-target-c220/README.md) now plans a second destination using the installed, byte-pinned Godot candidate. Upstream build lineage and a rendering route remain unresolved; no Godot process or receiving proof has run. [C221](docs/engineering/second-target-c221/README.md) now supplies the CPU-only checker for the eight locked inputs and complete 18-part source map, with independent negative controls. The next bounded step is [observation-schema and corner-correspondence preparation](docs/engineering/second-target-c221/NEXT-TASK.md); target execution remains held.

The staged roadmap is: this semantic proof; one version-pinned receiving application; a second-target/source-traceability proof; then a controlled comparison with matched direct authoring. General gameplay, a replacement physics engine, broad syntax, new creature/vehicle/fluid systems, training, MCP transport and simultaneous backends are deferred. [GOAL.md](GOAL.md) defines the revised priorities and measured-benefit gate.

C209's CPU-only job/0.2 retained-result compatibility is explicitly deferred. C201 native admission has not started; its frozen instructions remain unchanged. C199/C200 schedules stay closed, with their original failures, qualification results and hashes retained. Earlier tray preparation is historical evidence, not the automatic next task. The [C200 integration record](docs/engineering/static-tray-exporter-c200/evidence/publication-c203/INTEGRATION.json) and [C209 checks](docs/engineering/static-tray-admission-c201/evidence/entries-c209/README.md) preserve that work.

The research question is whether the same agent makes more correct, localized repairs and reusable deliveries than with direct tools under comparable conditions. No general authoring advantage or Unreal support is established by this milestone. The [model research archive](docs/maintenance/model-research-archive.md) remains separate deferred work.

## Try an agent edit

From a local checkout with Python 3.11 or later, run this example from the repository root.

```sh
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-first-model
```

Open the checkout's [offline viewer](examples/visual/viewer.html), choose **Open GLB**, and select `/tmp/ontokin-first-model/repaired.glb`. Scrub to **1.5 s**. The moving assembly's blue head is wider than the stationary assembly's head. The example uses a scripted client to make the edit, reject a value with the wrong unit, and retrieve the animation through the agent interface.

To try your own edit, start with the [editable scene](examples/agent/authoring-demo.ok), the [Agent/0.1 request schema](docs/language-design/agent-v0.1/request.schema.json), and the [agent guide](examples/agent/README.md). The [first-use task](examples/agent/first-use.md) describes how to test a fresh coding agent on this workflow.

To see why a valid part can still make a bad assembly, try the [connected-duct example](examples/connected-duct/README.md). It checks the opening between two hollow parts and repairs an offset through the Agent interface.

> **Project status:** OntoKin remains in development. The reference package is **0.4.0**. Its development line supports pinned reusable assemblies, native exterior surfaces and regional PBR materials, instantaneous impulses, and finite center-of-mass force intervals. Explicit Agent/0.5 and recorded GLB/0.5 support force-program inspection, source repair and artifact retrieval. Earlier profiles retain their meanings and defaults. [STATUS.md](STATUS.md) identifies integrated implementation, complete release evidence and remaining requirements; component implementation alone does not close a release or the broader product goal.

The [project goal](GOAL.md) defines the current semantic-authoring mission and records the disposition of earlier ambitions. [STATUS.md](STATUS.md) records verified progress, the active milestone, and the next unmet gate. [AGENTS.md](AGENTS.md) defines how development resumes after interruptions and coordinates concurrent work.

### Select sparse per-key component overrides

Explicit source `0.21` / `keyed-membership-0.1` supports bounded, read-only keyed membership:

```ontokin
if has_key(overrides, key) then overrides[key] else defaults[key]
```

A pinned component library can select an optional override while preserving each occurrence's complete catalog, independently identifiable parts, appearance and recorded motion. The operation accepts an existing immutable keyed value and an exact String query, admits the complete input, and checks canonical keys under the current request's execution budget. Both results preserve actual dependencies and inherited provenance. Generated keyed views retain their existing access and taint restrictions. Invalid queries and unguarded missing lookups remain explicit errors.

```bash
python3 -m ontokin export examples/keyed-membership/agent/base.files.json --bundle --target ontokin.glb/0.21 --output /tmp/ontokin-sparse-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.21 --store /tmp/ontokin-keyed-membership-agent
```

The [adopted decision](docs/language-design/keyed-membership-v0.1/ADOPTION.md), [language guide](docs/language-design/keyed-membership-v0.1/README.md), [Agent/0.21 guide](docs/language-design/agent-v0.21/README.md) and [C088 engineering record](docs/engineering/keyed-membership-2026-11-02-c088/README.md) identify the contract, independent inputs, actual checks and integration. An existing typed reduction/conditional helper remains a valid alternative for authored keyed leaves. This experimental convenience introduces no physical authority or measured authoring-benefit claim; complete feature release and full-product acceptance remain open.

### Give reusable part groups computed namespaces

Explicit source `0.20` / `string-concat-0.1` supports pure immutable String concatenation:

```ontokin
rekey_keyed<Length>(widths, (old_key, width) -> prefix + old_key)
```

A pinned library can receive different prefixes for independent occurrences while preserving each original payload and source dependency. Both operands evaluate once, in order. Results preserve exact Unicode text and are bounded to 65,536 UTF-8 bytes each and 4,194,304 cumulative logical result bytes per request. The existing admitted execution budget governs scanning, allocation and publication. Rekey retains its separate 1–64-character ASCII stable-key rule and collision refusal. Earlier declaring versions and ordinary defaults retain their meanings.

```bash
python3 -m ontokin export examples/string-concat/agent/panel-task.files.json --bundle --target ontokin.glb/0.20 --output /tmp/ontokin-namespaced-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.20 --store /tmp/ontokin-string-concat-agent
```

The [adopted decision](docs/language-design/string-concat-v0.1/ADOPTION.md), [frozen corpus guide](docs/language-design/string-concat-v0.1/CORPUS.md), [Agent/0.20 guide](docs/language-design/agent-v0.20/README.md) and [C087 engineering record](docs/engineering/string-concat-2026-11-01-c087/README.md) distinguish meaning, executed checks and integration. The representative workflow changes one occurrence's prefix or member set while preserving its sibling, pinned library, image and unrelated recorded motion. Complete experimental-feature release and full-product acceptance remain open.

### Pair named attributes with exact key agreement

Explicit source `0.18` / `keyed-zip-0.1` combines corresponding entries from two immutable keyed values:

```ontokin
zip_keyed<Length, Length, Area>(widths, heights,
    (key, width, height) -> width * height)
```

Both inputs must have exactly the same complete key set. The operation admits the left input once, then the right, refuses the first missing partner in canonical ASCII order, and runs the pure body once per matched key. Input and result types are exact; at most 256 entries are allowed. Inspection retains both original contributors, aggregate dependencies, and detached paired provenance through later construction.

```bash
python3 -m ontokin export examples/keyed-zip/panel-task.files.json --bundle --target ontokin.glb/0.18 --output /tmp/ontokin-paired-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.18 --store /tmp/ontokin-keyed-zip-agent
```

The [versioned decision](docs/language-design/keyed-zip-v0.1/ADOPTION.md), [independent frozen examples](examples/keyed-zip/README.md), [Agent/0.18 guide](docs/language-design/agent-v0.18/README.md), and [C085 engineering record](docs/engineering/keyed-zip-2026-11-01-c085/README.md) distinguish the contract, actual execution, and integration. Separate keyed dimension and material libraries support an atomic repair of one textured occurrence while preserving its sibling and unrelated motion. Ordinary budgets and earlier defaults remain unchanged. This selected experimental capability adds no physical or motion authority; complete feature release and full-product acceptance remain open.

### Combine named part groups with explicit collision refusal

Explicit source `0.17` / `keyed-merge-0.1` combines two immutable keyed values with the same exact element type:

```ontokin
merge_keyed<Length>(standard_widths, optional_widths)
```

The operation evaluates and fully admits the left input once, then the right input once. It refuses the lowest shared ASCII key even when its values are equal. A disjoint result keeps original keys and detached typed values in canonical order, with at most 256 entries. Both inputs' actual dependencies and source origins remain available through later construction and inspection.

```bash
python3 -m ontokin export examples/keyed-merge/panel-task.files.json --bundle --target ontokin.glb/0.17 --output /tmp/ontokin-merged-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.17 --store /tmp/ontokin-keyed-merge-agent
```

The [versioned decision](docs/language-design/keyed-merge-v0.1/ADOPTION.md), [frozen examples](examples/keyed-merge/README.md), [Agent/0.17 guide](docs/language-design/agent-v0.17/README.md) and [C084 engineering record](docs/engineering/keyed-merge-2026-11-01-c084/README.md) separate semantics, actual verification and integration. The representative repair adds and then removes an optional vent in one occurrence while preserving its standard panels, sibling, pinned image and unrelated recorded motion. This explicit experimental capability keeps ordinary 100,000-operation / 30,000-ms defaults and adds no physical or motion authority. Complete feature release and full-product acceptance remain open.

### Select optional keyed parts while preserving surviving identities

Explicit source `0.16` / `keyed-filter-0.1` adds a bounded pure selection:

```ontokin
filter_keyed<Length>(widths, (key, width) -> width >= 1.5[m])
```

The input is evaluated once. A strict Boolean predicate visits at most 256 entries in canonical ASCII key order, retaining original keys and detached values for survivors. Empty input still receives static predicate checking. Filtering composes with mapping and reduction to select optional parts while preserving exact source repair authority and every actual dependency, including when no entries survive.

```bash
python3 -m ontokin export examples/keyed-filter/panel-task.files.json --bundle --target ontokin.glb/0.16 --output /tmp/ontokin-filtered-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.16 --store /tmp/ontokin-keyed-filter-agent
```

The [versioned decision](docs/language-design/keyed-filter-v0.1/ADOPTION.md), [frozen examples](examples/keyed-filter/README.md), [Agent/0.16 guide](docs/language-design/agent-v0.16/README.md) and [C083 engineering record](docs/engineering/keyed-filter-2026-10-31-c083/README.md) identify semantics, actual repair evidence and remaining gates. The representative repair removes one occurrence's left panel while preserving its right panel, sibling, pinned image and unrelated recorded motion. This experimental construction operation preserves ordinary defaults of 100,000 operations / 30,000 ms and adds no physical or motion authority. Complete feature release and full-product acceptance remain open.

### Compute reusable construction parameters from keyed values

Explicit source `0.15` / `keyed-reduction-0.1` adds a bounded pure aggregate with an explicit typed seed:

```ontokin
reduce_keyed<Length>(dimensions, 0[m], (total, key, value) -> total + value)
```

The input is admitted once, then the seed is evaluated once. A pure body processes at most 256 entries sequentially in canonical ASCII key order, preserving every intermediate type, unit, frame, domain and resource check. Empty input returns a detached seed after static body checking. This composes with `map_keyed` to derive reusable dimensions, offsets and other admitted construction values.

```bash
python3 -m ontokin export examples/keyed-reduction/panel-task.files.json --bundle --target ontokin.glb/0.15 --output /tmp/ontokin-keyed-panels.glb
python3 -m ontokin agent --protocol ontokin.agent/0.15 --store /tmp/ontokin-keyed-reduction-agent
```

The [versioned decision](docs/language-design/keyed-reduction-v0.1/ADOPTION.md), [frozen examples](examples/keyed-reduction/README.md) and [Agent/0.15 guide](docs/language-design/agent-v0.15/README.md) define the contract. Inspection preserves detached reduction provenance for exact source repair. The [C082 engineering record](docs/engineering/keyed-reduction-2026-10-31-c082/README.md) separates actual source, Agent, delivered-stream and native-view evidence from complete release acceptance. Ordinary defaults remain 100,000 operations / 30,000 ms; larger requests require current host authority. Older bindings and defaults retain their meanings. This experimental construction operation adds no physical or motion authority.

### Add opaque image labels to native surfaces

Explicit source `0.13` / `textured-surfaces-0.1` attaches content-pinned offline PNG images to keyed material regions on existing native surfaces. Author an affine planar mapping in recipe-local coordinates, bind an image by stable asset ID and exact digest, and retain the underlying geometry, rigid placement and recorded motion. The [authoring guide](docs/language-design/textured-surfaces-v0.1/README.md) and [versioned decision](docs/language-design/textured-surfaces-v0.1/ADOPTION.md) define image orientation, color multiplication, immutable bundle/files `0.2`, and bounded decoding.

```bash
python3 -m ontokin export examples/textured-surfaces/rgb-panel.files.json --bundle --target ontokin.glb/0.13 --output /tmp/ontokin-textured-panel.glb
python3 -m ontokin agent --protocol ontokin.agent/0.13 --store /tmp/ontokin-textures-agent
```

The [Agent/0.13 interface](docs/language-design/agent-v0.13/README.md) supports atomic source-and-image repair, exact image byte retrieval, and texture-aware surface inspection through a separate durable store. Bundles admit at most four opaque RGB/RGBA PNGs, each at most 256 by 256 pixels and 300,000 encoded bytes. Sampling is nearest with clamp-to-edge addressing. Ordinary limits remain 100,000 operations / 30,000 ms; larger requests require independent current host authorization. This experimental appearance scope adds no mass, collision, deformation or motion authority. [STATUS](STATUS.md) distinguishes actual verification and integration from the remaining release gates.

### Author recessed trays, panels and housings

Explicit source `0.12` / `polygon-pockets-0.1` creates a constant polygon exterior with up to eight independently keyed blind pockets. Each pocket names its clockwise boundary, depth and floor material. The [versioned decision](docs/language-design/polygon-pockets-v0.1/ADOPTION.md) defines the exact remaining-base arithmetic, rounded floor, complete bottom/top/wall/floor surface, and actual delivered-coordinate checks.

```bash
python3 -m ontokin export examples/polygon-pockets/rectangular-pocket.ok --target ontokin.glb/0.12 --output /tmp/ontokin-pocket.glb
python3 -m ontokin agent --protocol ontokin.agent/0.12 --store /tmp/ontokin-pockets-agent
```

The [authoring guide](docs/language-design/polygon-pockets-v0.1/README.md), [independent frozen inputs](examples/polygon-pockets/README.md) and [Agent/0.12 interface](docs/language-design/agent-v0.12/README.md) cover reusable definitions, one-instance depth repair, bounded inspection and recorded delivery. There are at most 64 authored vertices overall and 16 materials. Every pocket leaves at least canonical binary64 0.001 meter of base. Ordinary execution defaults remain 100,000 operations / 30,000 ms. Visual geometry adds no physical body or collision authority; measured checks and remaining gates are identified in [STATUS](STATUS.md).

### Author bent ducts and handles with explicit section frames

Explicit source `0.11` / `framed-polygon-loft-0.1` places each keyed polygon section in its own rigid `Pose` within the consuming object's frame. Matching ring and vertex identities can form bent solid bodies, hollow elbows and finite handles. The [versioned decision](docs/language-design/framed-polygon-loft-v0.1/ADOPTION.md) defines exact section transforms, fixed strip triangles, endpoint caps and complete source and delivered-mesh checks. Each frame is authored; the language does not infer a path or transport its orientation.

```bash
python3 -m ontokin export examples/framed-polygon-lofts/hollow-elbow.ok --target ontokin.glb/0.11 --output /tmp/ontokin-elbow.glb
python3 -m ontokin agent --protocol ontokin.agent/0.11 --store /tmp/ontokin-framed-loft-agent
```

The [authoring guide](docs/language-design/framed-polygon-loft-v0.1/README.md), [frozen inputs](examples/framed-polygon-lofts/README.md) and [Agent/0.11 interface](docs/language-design/agent-v0.11/README.md) describe source repair, bounded inspection and recorded delivery. Limits remain 2–8 sections, up to eight holes, 64 vertices per section and 256 total. Origins and authored XY components stay within ±100 meters; adjacent origins must advance along both neighboring frames' positive Z axes. `FramedLoftAgentService` uses a separate durable store. Ordinary defaults remain 100,000 operations / 30,000 ms. This is experimental visual geometry and recorded carrier motion; the full product and release gates remain in [STATUS](STATUS.md).

### Author tapered polygon forms and hollow ducts

Explicit source `0.10` / `polygon-loft-0.1` connects 2–8 keyed polygon sections at increasing Z stations. Matching ring and vertex identities support changing cross-sections, concave forms and up to eight through-holes, with separate cap and strip materials. The [versioned decision](docs/language-design/polygon-loft-v0.1/ADOPTION.md) defines the actual fixed diagonal triangles; it does not promise linear interpolation of planar cross-sections.

```bash
python3 -m ontokin export examples/polygon-lofts/hollow-frustum.ok --target ontokin.glb/0.10 --output /tmp/ontokin-duct.glb
python3 -m ontokin agent --protocol ontokin.agent/0.10 --store /tmp/ontokin-loft-agent
```

The [authoring guide](docs/language-design/polygon-loft-v0.1/README.md), [frozen examples](examples/polygon-lofts/README.md) and [Agent/0.10 interface](docs/language-design/agent-v0.10/README.md) describe the contract. `RingLoftAgentService` supports exact source edits, bounded section and triangle inspection and recorded GLB retrieval. Limits are 64 vertices per section and 256 across all sections. Each source mesh and its delivered binary32 coordinates must retain a closed, nonintersecting surface and outward normals. Defaults remain 100,000 operations / 30,000 ms; the largest examples explicitly request separately authorized higher budgets. This is experimental visual geometry, with no implicit mass, collision shape or live destination physics.

### Author plates, slots and through-holes

Explicit source `0.9` / `polygon-holes-0.1` adds one keyed outer ring and up to eight keyed inner rings. Use it for slotted plates, bolt holes and hollow cross-sections, with separate cap and wall materials, reusable parts and rigid local placement. The [versioned decision](docs/language-design/polygon-holes-v0.1/ADOPTION.md) requires counterclockwise outer boundaries, clockwise holes, strict separation and at most 64 vertices across all rings. Coordinates remain within ±100 meters and depth within 0.001–100 meters.

```bash
python3 -m ontokin export examples/polygon-holes/slotted-bracket.ok --target ontokin.glb/0.9 --output /tmp/ontokin-slot.glb
python3 -m ontokin agent --protocol ontokin.agent/0.9 --store /tmp/ontokin-holes-agent
```

The [source examples](examples/polygon-holes/README.md), [Agent/0.9 schemas](docs/language-design/agent-v0.9/README.md) and [C076 engineering record](docs/engineering/polygon-holes-2026-10-30-c076/README.md) identify the contract and measured verification separately. `ontokin.holes_agent.HolesAgentService` supports source repair, bounded ring/triangle inspection and exact GLB retrieval. Source-valid geometry whose openings cannot survive delivered 32-bit coordinates fails export explicitly. The ordinary 100,000-operation / 30,000-ms defaults remain unchanged; the largest fixture requests a separately authorized higher budget. This is experimental visual geometry and recorded animation, with no implicit mass or collision shape.

### Author polygon plates and concave brackets

Explicit source `0.8` / `polygon-extrusion-0.1` adds closed extrusions from typed, keyed XY outlines. An agent can author a rectangular plate or concave bracket, reuse a class with different dimensions, edit one instance, inspect its triangles and retrieve recorded GLB/0.8 output. Separate cap and side materials and rigid local placement are supported. The [versioned decision](docs/language-design/polygon-extrusion-v0.1/ADOPTION.md) fixes 3–64 vertices, coordinates within 100 meters and depth from 0.001 to 100 meters. Self-intersections, holes, bevels and implicit mass/inertia are excluded.

```bash
python3 -m ontokin export examples/polygon-extrusions/concave-bracket.ok --target ontokin.glb/0.8 --output /tmp/ontokin-bracket.glb
python3 -m ontokin agent --protocol ontokin.agent/0.8 --store /tmp/ontokin-extrusion-agent
```

The [examples](examples/polygon-extrusions/README.md), [Agent/0.8 schemas](docs/language-design/agent-v0.8/README.md) and [C075 engineering record](docs/engineering/polygon-extrusions-2026-10-30-c075/README.md) distinguish the selected contract from actual verification and integration. The Python service is `ontokin.extrusion_agent.ExtrusionAgentService`. It inherits source-requested execution budgets, host authorization, exact source edits and atomic publication. The ordinary 100,000-operation / 30,000-ms defaults stay unchanged. This is experimental development; recorded playback does not establish live engine physics.

### Configurable execution budgets: source, CLI and Agent workflows

Explicit source `0.7` / `planar-reach-budget-0.1` can request more computation time and operations within ceilings independently authorized by its execution environment. Ordinary defaults remain **100,000 operations and 30,000 ms**; existing acceptance tests retain their original limits. A larger host ceiling does not silently increase an omitted program budget. Computation time and the animation's modeled duration are separate values.

[The C073 adoption](docs/language-design/execution-budgets-v0.1/ADOPTION-C073.md) defines the implemented grammar, trusted host API, bounded admission and explicit GLB/0.7 output. One counter and original deadline cover admission, compilation, simulation, export and independent output validation. [The example guide](examples/execution-budgets/README.md) provides an operator-controlled launcher and a frozen six-vessel force/impulse workload. Command-line caps can reduce a request; they cannot authorize a larger host ceiling.

[The C073 engineering record](docs/engineering/source-execution-budgets-2026-10-29-c073/README.md) identifies the source/CLI checks and integration. [C074](docs/engineering/agent-execution-budgets-2026-10-30-c074/README.md) adds the separately selected **Agent/0.7** service for discovery, exact source edits, saved-program authorization, evaluation, export, retrieval, cancellation and retries. Its [versioned contract and schemas](docs/language-design/agent-v0.7/README.md) preserve earlier Agent defaults and stores. [C072](docs/engineering/language-execution-budgets-2026-10-29-c072/README.md) retains the original proposal and source evaluation.

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.7 --store /tmp/ontokin-budget-agent
python3 tools/run_budget_agent_acceptance.py --output-dir /tmp/ontokin-budget-agent-evidence
```

The ordinary CLI host permits the default ceilings. An embedding host can use `BudgetAgentService(store, host_policy=HostPolicy(400000, 80000))` from `ontokin.budget_agent` and `ontokin.execution_budget`, or pass that policy to `cli.main`. Request JSON never grants host authority. Agent/0.7 patches use exact UTF-8 spans within an identified source file; earlier finer edit scopes keep their own contracts. Successful artifact production and later retrieval have separate current-policy requests and receipts. C074 remains an experimental development increment; its complete verification and integration are recorded separately.

### Current development: experimental planar reach

The C059 reconciliation selects the reviewed C032 development runtime, preserves the later C058 evidence, and excludes the held C035 runtime experiment. Source `0.6` / `planar-reach-0.1`, Agent/0.6 and recorded GLB/0.6 require explicit selection and are marked experimental in capabilities and discovery. Earlier bindings and defaults retain their meanings. [Current integration status](STATUS.md) and the [reconciliation record](docs/engineering/repository-reconciliation-2026-10-28/README.md) distinguish the actual candidate, checks and resulting main from release acceptance.

Historical original recording evidence is **24/28, a failed gate**. P11/P16/P23/L03 remain unresolved under the original limits; C035 remains held, including adverse timing. The comparison accounting/passive-authority concern remains open. [The M1 decision](docs/engineering/OK-DEC-COMPARE-M1-0.1.0.md) rejects the exact proposed model for comparison-only operation saving and adopts no replacement.

Main is the current development baseline under [OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md). New checkpoints normally become commits on the same active scope branch. Historical branches are preserved through a separately verified archival history before removal. This consolidation does not complete the reach release: all 28 source recordings, ten Agent artifacts, compatibility, rates, native/browser/visual checks, formal input closure and every R01–R12/Q01–Q22 obligation remain required.

This profile delivers recorded animation. Demonstrating live behavior would require a separate import and behavior test in the named engine version.

## Git LFS for engineering archives

Git LFS tracking is configured for future ZIP, numeric ZIP-part, TAR.XZ and TAR.GZ payloads under `docs/engineering/lfs-archives/`. Existing archives remain ordinary Git files with their original bytes and history. [The storage guide](docs/engineering/OK-ENG-010-git-lfs-archive-storage.md) defines the exact profile, local Git LFS setup, storage verification and no-history-rewrite migration procedure. [The focused validation record](docs/engineering/lfs-storage-validation-2026-10-28/README.md) identifies the actual checks.

Authenticated object upload and independent retrieval are required before publishing new LFS pointers. Existing-archive migration is prepared but remains pending that authenticated transfer. Ordinary checkouts with no LFS payloads retain their existing local-validation requirements; checkouts containing tracked LFS payloads need Git LFS 3.8.1 or newer and hydrated files.

## Export native exterior surfaces

The [OK-LANG-003 surface contract](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) defines typed keyed sections, material regions and rigid local placement. Its pinned studio source now compiles through the native language and produces two actual animated, multi-material meshes:

```bash
python3 -m ontokin export docs/language-design/surface-v0.1/program.files.json --bundle --target ontokin.glb/0.3 --output /tmp/ontokin-studio.glb
```

For a complete source without imports, use `python3 -m ontokin export model.ok --target ontokin.glb/0.3 --output /tmp/model.glb`. The [native export guide](docs/engineering/OK-ENG-003-native-surface-glb-export.md) explains pinned bundles, local transforms, PBR properties, source identities, resource limits, cancellation and independent validation.

The [M01–M12 fixtures](docs/language-design/surface-v0.1/acceptance.json) remain the full surface-release acceptance contract. The [release procedure](docs/engineering/OK-ENG-004-native-surface-release-conformance.md) connects actual agent edits, composed source programs, delivered GLBs and current regression evidence. The [earlier Python-input workbench](prototypes/surface_v01/README.md) remains preserved as historical prototype evidence.

### Inspect and repair a native surface program

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.3 --store /tmp/ontokin-surface-state
python3 tools/build_surface_agent_demo.py --output-dir /tmp/ontokin-surface-agent
```

The first command serves an agent's own versioned JSONL requests. [OK-AGENT-003](docs/engineering/OK-AGENT-003-native-surface-program-workflows.md) defines the operations and schemas. A `surface.mesh_page` request returns at most 256 complete triangles from an identified accepted program and object occurrence. It exposes carrier-local positions, normals and material-region keys, and binds continuation cursors to that exact geometry and implementation. Section and material edits remain edits to authoritative `.ok` bytes.

The second command runs the fixed acceptance workflow: reject an invalid radius, repair one occurrence, change one palette region, insert/reorder/remove a keyed section, evaluate motion, and retrieve actual GLB bytes through the service. It also exports the predetermined dimensional variants, ordinary and generated compositions, and a rotated release. Its output retains source snapshots and every request/response for independent verification. It generates geometry through native source operations; the driver supplies no prepared mesh.

## Apply source impulses and export their motion

The explicit language `0.4` / `impulse-0.1` profile adds instantaneous world-expressed momentum changes at a free sphere's own local point. An off-center application changes both linear velocity and angular velocity. For a declared free sphere named `ball`, the source event is:

```ontokin
at 1[s] sequence {
    impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s])
        at point(ball.frame, 0.5[m], 0[m], 0[m]);
}
```

Export the complete pinned source fixture, run the actual agent repair workflow, or start the explicit JSONL service:

```bash
python3 -m ontokin export docs/language-design/impulse-v0.1/p02-off-center-mixed-imports.files.json --bundle --target ontokin.glb/0.4 --output /tmp/ontokin-impulse.glb
python3 tools/build_impulse_agent_demo.py --output-dir /tmp/ontokin-impulse-agent
python3 -m ontokin agent --protocol ontokin.agent/0.4 --store /tmp/ontokin-impulse-state
```

[OK-LANG-004](docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) fixes units, frames, own sphere inertia, ordered release and impulse events, exact source identities, and atomic failure. [OK-AGENT-004](docs/engineering/OK-AGENT-004-source-impulse-program-workflows.md) defines complete bounded influence inspection, source-based mass/radius repair, and exact artifact retrieval. GLB/0.4 retains native lofts and regional PBR materials and records the resulting rigid motion, including sufficient samples for authored high-spin cases.

The [I01–I12 release procedure](docs/engineering/OK-ENG-005-source-impulse-release-conformance.md) separately requires all 40 frozen source cases, actual agent workflows, independent destination/browser evidence and current inherited execution roles. Implementation and finite release acceptance have separate identities in [STATUS](STATUS.md). Contacts, continuous torque, general rigid dynamics and live destination physics remain open requirements; earlier source, agent and export profiles retain their existing meanings and defaults.

## Apply finite force intervals and retrieve recorded motion

Language `0.5` / `force-0.1` adds a constant world force at the center of mass of a supported free homogeneous sphere. Authored intervals have exact activation and completion times; overlapping forces add to the existing gravity and impulse behavior. Source inspections expose the complete revision-bound force history, current acceleration and motion authority.

```bash
python3 -m ontokin export docs/language-design/force-v0.1/p01-single-interval.files.json --bundle --target ontokin.glb/0.5 --end 2.5 --output /tmp/ontokin-force.glb
python3 -m ontokin agent --protocol ontokin.agent/0.5 --store /tmp/ontokin-force-state
python3 tools/build_force_delivery_demo.py --output-dir /tmp/ontokin-force-delivery
```

The explicit export records the requested prefix, including its exact completion boundaries, and checks decoded binary32 motion against the chosen tolerances. A valid short prefix can succeed when a later authored activation would fail. Acceleration and angular bounds add samples within fixed resource limits; a representation that cannot meet its contract fails explicitly. GLB playback uses recorded transforms.

The [force delivery guide](examples/force/README.md) explains source-authoritative mass/force/duration repairs, actual chunk retrieval, independent native decoding, and real browser inspection. [OK-LANG-005](docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), [OK-AGENT-005](docs/engineering/OK-AGENT-005-finite-force-program-workflows.md) and [OK-ENG-007](docs/engineering/OK-ENG-007-native-force-glb-export.md) fix the source, interface and export contracts. [OK-ENG-008](docs/engineering/OK-ENG-008-force-release-conformance.md) defines complete F01–F12 acceptance under the current local execution policy, including all required source, regression, compatibility, destination and visual evidence. The complete finite release result is recorded separately in [STATUS](STATUS.md).

## Build an assembly from a pinned component library

From the repository root, with Python 3.11 or later:

```bash
python3 tools/build_construction_demo.py --help
python3 tools/build_construction_demo.py --output-dir /tmp/ontokin-construction-demo
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store /tmp/ontokin-program-state
```

The demonstration uses a real imported component module and a `Keyed` input to construct two assemblies with three and five articulated parts. It discovers the pinned library, inspects a generated occurrence, rejects an invalid units edit, repairs that occurrence's public length parameter, evaluates the motion, and retrieves `keyed-rack.glb` through the agent interface. The final assembly contains 18 objects; the generated collection itself adds no object or mass. Its expected dimensions and 126 world poses are specified independently in the [Rack fixture](docs/language-design/construction-v0.1/01-keyed-rack/expected.json).

Open [the offline viewer](examples/visual/viewer.html), choose **Open GLB**, and select `/tmp/ontokin-construction-demo/keyed-rack.glb`. The [construction example guide](examples/construction/README.md) explains the motion, exact source files, reports, and Python APIs for loading either a local file manifest or an inline bundle. The demo driver reproduces its fixed fixture; the program-bundle APIs support an agent's own authored sources.

[OK-LANG-002](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) defines the versioned language extension. [OK-AGENT-002](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) defines program revisions, atomic edits across files, source provenance, and the separate agent service. `.ok` files remain the editable authority; the complete pinned source closure identifies an accepted program. The new animation target is `ontokin.glb/0.2`.

## Author and repair through the agent interface

```bash
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-agent-demo
python3 -m ontokin agent --store /tmp/ontokin-agent-state
```

The first command runs a complete, inspectable workflow: create a two-assembly scene, reject an invalid units edit, repair only one head, confirm the sibling remains unchanged, evaluate the motion, and retrieve a verified GLB. The second starts the local JSONL interface for an agent's own requests. Python clients can use `from ontokin.agent import AgentService` directly.

The [agent example guide](examples/agent/README.md) includes the editable sources, actual [repaired animation](examples/agent/repaired.glb), complete [request/response evidence](examples/agent/workflow.json), and instructions for opening the result in the offline viewer. [OK-AGENT-001](docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) defines immutable source revisions, scoped UTF-8 patches, idempotent requests, cancellation, exact-time inspection, engine-bound runs, and recovery. The local interface requires no language-model call or external runtime dependency.

## See the animations

Open [the offline animation viewer](examples/visual/viewer.html) from a local checkout. It includes two actual OntoKin exports: an assembly whose head and hand move independently, and a sphere that continues under gravity after its carrier releases it and stops. Play, pause, scrub the timeline, orbit the view, or inspect an object's world position. The viewer loads the exported GLB bytes through Three.js; it does not calculate another physical trajectory.

On macOS, from the repository root:

```bash
open examples/visual/viewer.html
```

The bundled viewer and demonstrations work offline. The [visual example guide](examples/visual/README.md) explains the controls, editable sources, generated files, and optional verification tools. To open the exports in another application, use [independent parts](examples/visual/01-independent-parts.glb) or [gravity and release](examples/visual/02-gravity-and-release.glb). Blender import instructions are included in the guide; the measured target for this milestone is Three.js, with separate Khronos format validation.

### Export an OntoKin program

```bash
python3 -m ontokin export examples/visual/01-independent-parts.ok --output /tmp/independent-parts.glb
python3 -m ontokin export examples/visual/02-gravity-and-release.ok --output /tmp/gravity-and-release.glb
```

Each successful command writes a self-contained GLB and a JSON report beside it, such as `/tmp/gravity-and-release.export.json`. The report identifies the source revision, artifact hash, sampling settings, measured errors, and information retained only as metadata. The `.ok` source remains unchanged.

The default export samples at least 60 times per second and includes exact semantic event/completion boundaries. Its numerical checks read the encoded GLB and compare positions, orientations, and key timing with the reference evaluator. The adapter's default tolerances are `0.001 m`, `0.001 rad`, and `0.000001 s`. These concern exported playback and do not relax the evaluator's stricter language conformance checks. [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) defines the contract, evidence, and limits.

## Run the core prototype

Use **Python 3.11 or later** from this repository's root. No external runtime dependency or installation is required.

```bash
python3 -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
python3 -m ontokin evaluate docs/language-design/core-v0.1/01-independent-parts.ok --times 0 1 2 3
python3 -m ontokin evaluate docs/language-design/core-v0.1/02-gravity-and-release.ok --times 1 1.5 2
```

`check` reads the source, validates its static definitions, and checks the complete authored timeline. `evaluate` returns JSON samples containing object positions, orientations, velocities, ownership, physical assumptions, joint coordinates, and action status. The source file is unchanged. A SHA-256 source revision ties the results and diagnostic byte spans to the exact input.

The independently moving parts example produces these world positions:

| Time | Head position, m | Hand position, m |
| --- | --- | --- |
| 1 s | (1, 1, 0) | (1.5, 0.5, 0) |
| 2 s | (2, 1, 0) | (2.75, 0.5, 0) |
| 3 s | (2, 1, 0) | (2.75, 0.5, 0) |

The head retains its 90-degree local yaw when that action completes. The hand continues its independent slider motion while the root moves. The [executed conformance report](docs/engineering/conformance-results.json) checks these values and the other published expectations.

### Commands and failure results

The `check` and `evaluate` file commands, and default `export`, retain the existing single-source `core-0.1` contract. Export can explicitly select GLB/0.2 or GLB/0.3 with `--target`; `--bundle` reads a pinned offline file manifest. Program-agent operations retain their separately selected protocol.

| Command | Purpose |
| --- | --- |
| `python3 -m ontokin capabilities` | Inspect implemented operations, output levels, physical assumptions, and numerical limits. |
| `python3 -m ontokin agent --store DIR` | Serve versioned JSONL agent requests with durable local source, request, run, and artifact state. |
| `python3 -m ontokin agent --store DIR --request request.json --wait` | Execute one request and return its terminal result; omit `--wait` for a retained queued receipt. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR` | Serve program-bundle JSONL requests in a separate durable store, with exact dependency and per-file source identities. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR --request request.json --wait` | Execute one versioned program request and return its terminal response. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.3 --store DIR` | Serve native surface source workflows and bounded triangle inspection in a separate durable store. |
| `python3 -m ontokin check FILE.ok` | Validate and preflight the declared timeline. |
| `python3 -m ontokin check FILE.ok --level represented` | Check source representation while disclosing unresolved support requests. |
| `python3 -m ontokin check FILE.ok --level constructed` | Derive the initial world state before time-zero actions, without requiring later actions to be admissible. |
| `python3 -m ontokin evaluate FILE.ok --times 1 1.5 2 --side before` | Sample the incoming side of an event or natural completion. The default side is `after`. |
| `python3 -m ontokin evaluate FILE.ok --times 0.5 --object first.ball --frame first.frame` | Inspect one object in another frame. Velocity remains measured relative to world and is expressed in the requested axes. |
| `python3 -m ontokin export FILE.ok --output FILE.glb` | Bake, encode, and numerically verify a GLB under the named `ontokin.glb/0.1` contract; write a JSON sidecar. |
| `python3 -m ontokin export FILE.ok --output FILE.glb --fps 120 --end 1.5 --no-helpers` | Export a shorter interval with denser sampling and no display-only assembly/joint markers. |
| `python3 -m ontokin export PROGRAM.files.json --bundle --target ontokin.glb/0.3 --output MODEL.glb` | Compile pinned native surface source and export regional PBR geometry plus rigid animation. |
| `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json` | Execute all 43 published source cases and write their measured results. |
| `python3 tools/run_surface_conformance.py --output /tmp/ontokin-surface-conformance.json` | Execute the fixed M01–M12 tests and report any pending identified external gates. |

JSON diagnostics contain the stable error code, failure phase, source revision, original UTF-8 byte span, governing rules, and repair guidance. Admission and transition failures found during preflight retain the time and phase of the authored failure. Receiving a suggested repair does not apply it.

For the core file commands, exit status is `0` for success, `1` for I/O failure, `2` for an invalid/conflicting source, unavailable sample, numerical failure, or resource limit, and `3` for an unsupported requested capability/level. Core conformance returns `1` when its run fails. Agent one-request mode returns `1` for a rejected, failed, or unknown result; JSONL clients inspect each response's status and diagnostics. Generic `check --level delivered` still returns unsupported because it names no destination contract. Use `export` for the selected GLB contract, or name the compatible `ontokin.glb/0.2` or `ontokin.glb/0.3` destination in a program-agent export request. The separate surface conformance runner uses `1` for executed failures or an unstable run and `2` for pending selected requirements.

Sample times written on the command line are exact decimal seconds. Source time quantities first become canonical binary64 values, and event scheduling preserves those values exactly. A decimal sample of `0.1` is therefore slightly earlier than an event authored as `0.1[s]`. Returned `boundary_times_seconds` gives the exact event and completion times; use those strings for exact boundary inspection.

For an optional installed `ontokin` command, install the checkout in a Python environment with `python3 -m pip install -e .`. The conformance command expects this repository's fixture directory; a packaged installation can specify it with `--fixtures PATH`.

### Verification

Run the existing Python test and conformance checks locally:

```bash
python3 tools/check_local.py
```

Each run saves a source inventory, environment, per-step logs and JSON results in a new `build/local-checks/` directory. Use `python3 tools/check_local.py --list` to inspect the commands. After the one-time setup in [the local validation guide](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md), `python3 tools/check_local.py --full` also rebuilds the 3D examples and runs the independent format and browser checks in an isolated copy. The original source and recorded historical evidence stay intact.

The tests check source-to-state behavior, independent numerical expectations, diagnostics, event boundaries, release from moving joint chains, parameter scope, and command-line failures. Export tests also decode the GLB independently, check triangle geometry and several complete turns of rotation, and reject precision loss or unsupported output. The [GitHub Actions workflow](.github/workflows/reference.yml) is now manual-only with an explicit hosted-job input that defaults to false. Pushes and pull requests no longer start this workflow. Manually opting in still consumes the applicable GitHub allowance or paid budget; it is not needed for local checks. Existing older branches keep their previous workflow definitions until synchronized.

A local run reports only the Python version and platform actually executed. Full compatibility still needs identified Python 3.11, 3.12 and 3.13 runs; complete release gates retain separate external-evidence and visual-review requirements. [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md#6-measured-evidence) preserves the original prototype evidence; [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#8-measured-evidence) records the export milestone.

The [C01–C20 construction manifest](docs/language-design/construction-v0.1/validation-cases.json) fixes the new module, construction, scoped-edit, lifecycle, and delivery requirements. Its [runner](ontokin/construction_conformance.py) executes the selected tests and separately verifies identified external evidence. A run without the required external delivery evidence leaves that gate pending. [STATUS.md](STATUS.md) records when the complete local and CI release gate has closed; the fixture expectations and demo driver alone do not establish that result.

## Start reading

Use the [documentation guide](docs/README.md) for the full reading order, document status, diagrams, and earlier design records.

| Question | Document |
| --- | --- |
| What should OntoKin create, and what is the initial focus? | [OK-CAP-001: Modeling, motion, and object structure](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| What must the intended product support? | [OK-PRD-001: Product requirements](docs/product/OK-PRD-001-product-requirements.md) |
| What do objects, movement, mechanics, and physics mean? | [OK-SEM-001: Core object, motion, and physics semantics](docs/language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |
| How does an agent express those meanings in valid code? | [OK-LANG-001: Core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) |
| What does the first prototype implement, and how is it checked? | [OK-ENG-001: Core reference implementation and conformance plan](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) |
| How do calculated objects and motion become a visible animation? | [OK-ENG-002: 3D scene representation, animation export, and visual validation](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) |
| How does an agent discover, inspect, edit, evaluate, and retrieve an animation? | [OK-AGENT-001: AI agent authoring and inspection interface](docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) |
| How do exact-pinned modules and immutable inputs generate reusable assemblies? | [OK-LANG-002: Pinned modules and keyed assembly construction](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) |
| How does an agent inspect and atomically edit a complete source bundle? | [OK-AGENT-002: Program bundles and atomic source edits](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) |
| How do native exterior surfaces and material regions reach GLB? | [OK-ENG-003: Native surface GLB export](docs/engineering/OK-ENG-003-native-surface-glb-export.md) |
| How do agents describe native exterior surfaces and material regions? | [OK-LANG-003: Parameterized exterior surfaces and material regions](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) |
| How does source apply an off-center impulse and retain its physical meaning? | [OK-LANG-004: Source impulses and free-sphere dynamics](docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) |
| How do agents inspect impulse state, repair physical parameters and retrieve recorded motion? | [OK-AGENT-004: Source impulse program workflows](docs/engineering/OK-AGENT-004-source-impulse-program-workflows.md) |
| What establishes the complete finite impulse release gate? | [OK-ENG-005: Source impulse release conformance](docs/engineering/OK-ENG-005-source-impulse-release-conformance.md) |
| How are finite forces authored, inspected and repaired? | [OK-LANG-005: Finite center-of-mass force intervals](docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md) and [OK-AGENT-005: Finite-force program workflows](docs/engineering/OK-AGENT-005-finite-force-program-workflows.md) |
| How is force motion recorded and independently validated? | [OK-ENG-007: Native force GLB export](docs/engineering/OK-ENG-007-native-force-glb-export.md) and [the delivery guide](examples/force/README.md) |
| What establishes F01–F12 with actual local execution? | [OK-ENG-008: Provider-neutral finite force release conformance](docs/engineering/OK-ENG-008-force-release-conformance.md) |

The documents are organized into **Product**, **Language design**, and **Engineering**. The [founding records](docs/README.md#founding-design-records) retain the original vision, language exploration, and architecture options. Their dates and proposal status remain visible. The guide explains how that earlier work relates to the current modeling direction.

## Language and implementation scope

The [core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) reviews all 28 proposed semantic rules and defines `core-0.1`: typed classes and pure methods, independently instantiated parts, explicit frames and units, prescribed joints, concurrent action channels, exact event ordering, and a limited gravity/release contract.

The `construction-0.1` extension adds side-effect-free source modules with exact version/content pins, qualified nominal types and pure functions, flat immutable `Keyed<T>` inputs, and bounded generated parts with stable per-key identities. Public per-key overrides apply before nested construction. This profile uses the same motion and physical subset. Imports are resolved from explicitly supplied bytes; supported limits include 16 dependency modules, 256 entries per keyed value, 1,000 objects, and 2,000,000 total source bytes. Nested authored keyed values, runtime topology changes, host-language execution, and network package resolution are outside this profile. The [language contract](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) supplies the complete limits and version rules.

Start with [independently moving parts](docs/language-design/core-v0.1/01-independent-parts.ok), then [gravity and release](docs/language-design/core-v0.1/02-gravity-and-release.ok). Two further programs check rotational velocity transfer and the distinction between ownership and following. The [validation manifest](docs/language-design/core-v0.1/validation-cases.json) preserves the original 43 source cases and ten agent-operation cases with their expected outcomes and historical design status. The separate [source conformance report](docs/engineering/agent-validation/core-conformance.json) records execution under 0.3.0. The [agent conformance report](docs/engineering/agent-validation/conformance.json) executes A01–A10 against the durable service; both are finite test-corpus evidence, not full-product certification.

The reference uses Python's standard library and analytic motion equations. Its GLB adapter exports sphere/box meshes, linear RGBA appearance, optional display markers, and sampled world transforms. Source ownership, physical properties, joints, and release events remain inspectable metadata; a destination plays baked motion without executing those rules. Production compiler, runtime, physics-engine, and renderer choices remain open. Contact, dynamic articulated mechanisms, general body dynamics, deformation, and broader delivery contracts remain future requirements.

The physical subset is explicit: uniform gravity, free homogeneous solid spheres, and externally prescribed connections without a load solution. Collision response is disabled and there is no ground plane. A sphere can pass below zero height without a collision. Passing the bounded fixtures does not certify correctly rounded transcendental functions for every input, exact internal rotations, rigorous interval bounds for all rotating mechanisms, long-duration accuracy, or the broader product. [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records these limits and the production decisions that still need evidence.

## About the name

**OntoKin** combines **onto-**, referring to ontology, or what exists and how entities relate, with **kin-**, referring to kinematics, or motion. Earlier drafts used the working name *OntoKine*; **OntoKin** is the current project name.

The [documentation reorganization record](docs/maintenance/reorganization-2026-10-17/reorganization-record.md) contains the requirements, implementation plan, source mapping, and preservation checks for the October 17, 2026 organization change.
