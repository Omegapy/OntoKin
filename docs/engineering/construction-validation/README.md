# Construction release evidence

This directory records the **0.4.0** verification of [OK-LANG-002](../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) and [OK-AGENT-002](../OK-AGENT-002-program-bundles-and-atomic-source-edits.md). The release status and exact implementation identity are recorded in [validation-summary.json](validation-summary.json). Earlier headless, visual and 0.3.0 agent reports remain historical records in their original directories.

## What the demonstration establishes

The [actual program workflow](../../../examples/construction/workflow.json) uses the new agent protocol to discover a pinned component library, create two assemblies, inspect a generated occurrence, reject an invalid units edit, repair one public occurrence parameter, evaluate the program, and retrieve the exported GLB in bounded chunks. It finishes at the exact [predefined source bundle](../../language-design/construction-v0.1/01-keyed-rack/program.bundle.json), whose independent oracle was authored before the production implementation.

The scene has two Rack roots, eight generated Finger objects and eight owned Blade objects. One assembly contains three generated parts, the other five. The generated collections add no scene objects, bodies or matter. The selected first blade is 0.75 m long; the other blades remain 0.6 m. The first Rack translates while that blade rotates about its hinge; the second Rack stays fixed. This is a construction and prescribed-motion example, with no physical body mass claimed for these visualization objects.

Independent checks read the actual GLB, validate its glTF structure, inspect decoded mesh dimensions and compare loaded world poses. The browser harness loads those same agent-retrieved bytes through the existing viewer's **Open GLB** input. It compares all 18 world poses at seven times, exercises playback controls, and captures the rendered scene. The captured image is reviewed separately. The custom-import UI sees only the GLB, so it correctly leaves numerical conformance unknown; the harness supplies and verifies the source/report sidecars outside that UI.

## Evidence roles

| File | What it measures |
| --- | --- |
| [Unit tests](unit-tests.txt) | Complete Python regression run against the recorded fixed implementation. |
| [Core conformance](core-conformance.json) | Original 43 source cases and 694 authored assertions. |
| [Agent 0.1 conformance](agent-conformance.json) | Original A01–A10 through actual requests. |
| [Construction conformance](conformance.json) | C01–C20, executed required tests, exact fixtures and verified retained external evidence. |
| [External results](external-results.json) | Khronos format validation plus independent Three.js geometry and animation comparisons for the new GLB. |
| [Viewer results](viewer-results.json) | Actual Chromium/WebGL playback, sampled world poses, controls, sidecar identity checks and capture provenance. |
| [Rendered capture](keyed-rack.png) | Actual imported 3D assembly at 1.5 seconds; visual evidence for the recorded review. |
| [External gate](external-gate.json) | Exact source/workflow/artifact/report/capture identities and the identified review required by C20. |
| [Protocol schema results](schema-results.json) | Independent Draft 2020-12 validation of five schemas and actual workflow messages, using local reference resolution. |
| [Legacy export regression](legacy-external-results.json) | Fresh export and independent playback checks for all six original GLBs. |
| [Agent 0.1 export regression](agent-external-results.json) | Fresh execution and independent decoding of the existing single-source authoring demonstration. |
| [Legacy viewer regression](legacy-viewer/viewer-results.json) | Ten control/layout checks using the retained built-in demonstration assets. |
| [Agent 0.1 browser regression](agent-viewer/viewer-results.json) | Eight browser checks and 16 decoded poses from the freshly rebuilt single-source agent artifact. |
| [Regression artifact retention](legacy-artifacts/retention.json) | Byte-identical retained copies of the fresh legacy inputs and outputs; original execution paths remain disclosed. |
| [Preservation](preservation.json) | Historical document/content and current navigation checks. |
| [CI results](ci-results.json) | Actual observed remote jobs for the identified published implementation. |

Assertions, executed test methods, source cases, object-pose comparisons and browser checks count different things. The reports label them separately. A passing retained-evidence check verifies the recorded external run and its exact files; it does not rerun a browser or a format validator.

## Reproduce the construction result

From the repository root, use Python 3.11 or later and the verification tools pinned in `tools/package-lock.json`:

```bash
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-core.json
python3 tools/run_agent_conformance.py --output /tmp/ontokin-agent.json
python3 tools/build_construction_demo.py
npm ci --prefix tools --ignore-scripts
node tools/verify_gltf.mjs examples/construction --output docs/engineering/construction-validation/external-results.json
node tools/node_modules/playwright/cli.js install chromium --only-shell --with-deps
node tools/verify_construction_viewer.mjs
```

These commands regenerate the named local demonstration/evidence files; commit a new identified result after review rather than relabeling historical runs. Open the resulting `keyed-rack.png` and inspect the scene before recording a review:

```bash
python3 tools/record_construction_evidence.py --reviewer YOUR_REVIEWER_ID --visual-review "Your factual observation after inspecting this capture"
python3 -m ontokin.construction_conformance --output docs/engineering/construction-validation/conformance.json --external-evidence docs/engineering/construction-validation/external-gate.json
```

The recorder cross-checks actual successful workflow, numerical and browser reports and their file hashes before replacing the gate manifest. Supplying text does not perform the review. Without identified external evidence, C20 remains pending and the conformance command returns exit status 2. A failed expectation or unstable implementation/test/fixture bytes returns 1. A complete passing selected gate returns 0; a partial case selection never claims the full gate.

The optional [schema-check recipe](../../../examples/construction/README.md) installs its independent validator into a temporary development directory. Neither it nor the renderer/validator tools add a Python runtime dependency to OntoKin.

## Scope and remaining work

This release adds exact offline module binding, pure bounded keyed construction, stable generated identity, atomic program/source editing, and provenance-preserving GLB delivery. It preserves the earlier profile semantics. It does not certify network package resolution, unbounded procedural algorithms, rich surfaces or textures, contacts, general dynamics, purposeful controllers, live destination physics, production/distributed agent infrastructure, or a measured authoring-efficiency benefit. Blender import remains untested. The full project remains in progress under [GOAL](../../../GOAL.md); the next surface/material design is [OK-LANG-003](../../language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md).
