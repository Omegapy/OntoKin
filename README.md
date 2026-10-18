# OntoKin

**An AI-native, object-oriented language for physical 3D models and animation.**

OntoKin (pronounced **ON-toh-kin**) is a programming language under development, designed primarily for AI agents to create reusable objects, characters, and animations. An agent describes an object's form, parts, appearance, physical properties, mechanical connections, and intended actions. The language system supplies supported construction and behavior. People can inspect the definitions, review the results, and direct changes.

The current direction begins with exterior 3D models and short animations. Those objects should remain reusable in larger scenes, video games, and eventually more complex virtual worlds. Physics and mechanics are central to the design; mathematics gives those descriptions precise meaning.

> **Project status:** The published experimental reference is **0.4.0**. It supports exact-pinned source modules and keyed assembly construction through language `0.2`, `construction-0.1`, and `ontokin.agent/0.2`, with working `ontokin.glb/0.2` animation export. Its [local and CI release gate passed](docs/engineering/construction-validation/validation-summary.json): 276 tests, the original source/agent cases, C01–C20, independent geometry/playback checks, and Python 3.11–3.13 plus browser CI. The existing core language and interfaces remain supported. Broader modeling, physical interaction, controllers, live delivery, and production architecture remain unfinished; [native exterior surfaces and material regions](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) have a newly adopted source contract and experimental research prototype, but are not supported by the published compiler yet.

The [project goal](GOAL.md) preserves the full language and product mission. [STATUS.md](STATUS.md) records verified progress, the active milestone, and the next unmet gate. [AGENTS.md](AGENTS.md) defines how development resumes after interruptions and coordinates concurrent work.

## Exterior-surface research prototype (not yet source-executable)

The adopted [OK-LANG-003 surface-0.1 contract](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) specifies typed cross-sections, named material regions, bounded triangulation, and local rigid placement. The [frozen prospective M01–M12 corpus](docs/language-design/surface-v0.1/acceptance.json) and [pinned source example](docs/language-design/surface-v0.1/02-studio.ok) record intended behavior; **these new `.ok` programs cannot yet be compiled by version 0.4.0**.

An [isolated geometry and GLB prototype](prototypes/surface_v01/README.md) now constructs ordered elliptical lofts, outward flat normals, real per-region glTF triangles and PBR material factors. Its CI generates a GLB, checks it with Khronos' glTF validator and Three.js, and preserves 0.4.0's separate evidence. To reproduce the geometry-only demonstration from a repository checkout:

```bash
python3 -m unittest discover -s tests -p 'test_surface_*.py' -v
python3 -m tools.build_surface_prototype --output-dir /tmp/ontokin-surface-prototype
npm ci --prefix tools --ignore-scripts
node tools/verify_surface_prototype.mjs /tmp/ontokin-surface-prototype/offset-taper.glb
```

This demonstration builds from explicit Python data structures, **not OntoKin source or an agent operation**. It has no physical solver or recorded animation. Compiler integration, scoped source repair, source-driven scene animation, the versioned delivery adapter, and full M01–M12 evidence remain future steps.

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

The `check`, `evaluate`, and `export` file commands use the existing single-source `core-0.1` contract. Program bundles use the explicitly selected agent service or the [construction Python APIs](examples/construction/README.md#use-local-source-files-or-an-inline-bundle).

| Command | Purpose |
| --- | --- |
| `python3 -m ontokin capabilities` | Inspect implemented operations, output levels, physical assumptions, and numerical limits. |
| `python3 -m ontokin agent --store DIR` | Serve versioned JSONL agent requests with durable local source, request, run, and artifact state. |
| `python3 -m ontokin agent --store DIR --request request.json --wait` | Execute one request and return its terminal result; omit `--wait` for a retained queued receipt. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR` | Serve program-bundle JSONL requests in a separate durable store, with exact dependency and per-file source identities. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR --request request.json --wait` | Execute one versioned program request and return its terminal response. |
| `python3 -m ontokin check FILE.ok` | Validate and preflight the declared timeline. |
| `python3 -m ontokin check FILE.ok --level represented` | Check source representation while disclosing unresolved support requests. |
| `python3 -m ontokin check FILE.ok --level constructed` | Derive the initial world state before time-zero actions, without requiring later actions to be admissible. |
| `python3 -m ontokin evaluate FILE.ok --times 1 1.5 2 --side before` | Sample the incoming side of an event or natural completion. The default side is `after`. |
| `python3 -m ontokin evaluate FILE.ok --times 0.5 --object first.ball --frame first.frame` | Inspect one object in another frame. Velocity remains measured relative to world and is expressed in the requested axes. |
| `python3 -m ontokin export FILE.ok --output FILE.glb` | Bake, encode, and numerically verify a GLB under the named `ontokin.glb/0.1` contract; write a JSON sidecar. |
| `python3 -m ontokin export FILE.ok --output FILE.glb --fps 120 --end 1.5 --no-helpers` | Export a shorter interval with denser sampling and no display-only assembly/joint markers. |
| `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json` | Execute all 43 published source cases and write their measured results. |

JSON diagnostics contain the stable error code, failure phase, source revision, original UTF-8 byte span, governing rules, and repair guidance. Admission and transition failures found during preflight retain the time and phase of the authored failure. Receiving a suggested repair does not apply it.

For the core file commands, exit status is `0` for success, `1` for I/O failure, `2` for an invalid/conflicting source, unavailable sample, numerical failure, or resource limit, and `3` for an unsupported requested capability/level. Core conformance returns `1` when its run fails. Agent one-request mode returns `1` for a rejected, failed, or unknown result; JSONL clients inspect each response's status and diagnostics. Generic `check --level delivered` still returns unsupported because it names no destination contract. Use `export` for the bounded core GLB contract, or name `ontokin.glb/0.2` in a program-agent export request.

Sample times written on the command line are exact decimal seconds. Source time quantities first become canonical binary64 values, and event scheduling preserves those values exactly. A decimal sample of `0.1` is therefore slightly earlier than an event authored as `0.1[s]`. Returned `boundary_times_seconds` gives the exact event and completion times; use those strings for exact boundary inspection.

For an optional installed `ontokin` command, install the checkout in a Python environment with `python3 -m pip install -e .`. The conformance command expects this repository's fixture directory; a packaged installation can specify it with `--fixtures PATH`.

### Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-conformance.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
python3 tools/build_visual_demos.py
python3 tools/build_construction_demo.py --output-dir /tmp/ontokin-construction-demo
```

The tests check source-to-state behavior, independent numerical expectations, diagnostics, event boundaries, release from moving joint chains, parameter scope, and command-line failures. Export tests also decode the GLB independently, check triangle geometry and several complete turns of rotation, and reject precision loss or unsupported output. The [GitHub Actions workflow](.github/workflows/reference.yml) runs Python checks on 3.11, 3.12, and 3.13, with a separate format and visual verification job. [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md#6-measured-evidence) preserves the original prototype evidence; [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#8-measured-evidence) records the export milestone.

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
| How will agents describe native exterior surfaces and material regions? | [OK-LANG-003: Parameterized exterior surfaces and material regions](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) |

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
