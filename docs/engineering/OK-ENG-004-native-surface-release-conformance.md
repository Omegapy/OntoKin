# OK-ENG-004: Native surface release conformance

- Version: **0.1**, October 18, 2026.
- Scope: the adopted **M01–M12** requirements for language `0.3`, profile `surface-0.1`, `ontokin.agent/0.3` and `ontokin.glb/0.3`.
- Status: implemented reproduction and evidence contract; measured release results are recorded separately in [STATUS](../../STATUS.md).
- Governing requirements: [OK-LANG-003](../language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md), [OK-AGENT-003](OK-AGENT-003-native-surface-program-workflows.md), and [GOAL](../../GOAL.md).

## 1. What constitutes this release gate

[The frozen acceptance corpus](../language-design/surface-v0.1/acceptance.json) states the source, geometry, material, motion, boundary and repair requirements. [The executable mapping](../language-design/surface-v0.1/conformance.json) binds those requirements to actual unittest methods and mandatory external evidence. Neither file is an execution report. The additional [composition sources and expected values](../language-design/surface-v0.1/compositions/README.md) cover ordinary parts, generated counts 1/3/7, and a nonidentity placement with physical release while keeping the original reusable library bytes unchanged.

The runner executes each distinct selected unittest method once. A selected case can pass only after its mapped tests pass and its required external evidence verifies. An explicit subset can pass while `full_gate_complete` remains false. All 12 adopted cases must pass together to close this finite gate. Every report keeps `full_product_conformance_certified: false`; contacts, general dynamics, textures, skin deformation, controllers and the other GOAL domains remain separate work.

| Evidence gate | Required relationship |
| --- | --- |
| Workflow | Exact Agent/0.3 requests, responses, source snapshots, accepted history, native triangle pages, scoped edits and retrieved artifact chunks. |
| Destination | All 22 mandatory native fixtures, retained `.ok` bundles, independently expected geometry/PBR/motion, GLB binary contents, and Khronos/Three.js results for those same retrieved bytes. |
| Browser | Four fixed repaired/composed/released fixtures, fixed numerical sample times, source/artifact identities, play/pause observations and 12 identified, visually reviewed captures. |
| Regression | Every current discovered test plus the frozen 439-test inherited floor; original 43-case source and A01–A10 evidence; complete current C01–C20 including a fresh independent C20 attestation. |
| CI | An observed successful GitHub run with Python 3.11/3.12/3.13 and visual jobs, tied to the actual commit tree and current runtime/test/spec/tool/workflow inventory. |

## 2. Execute source tests and the full suite

Run these commands from the repository root in a stable checkout:

```bash
python3 tools/run_surface_conformance.py --output build/surface-release/surface-pending.json
python3 tools/run_surface_conformance.py --full-suite-only --output build/surface-release/full-suite.json
python3 -m ontokin conformance --output build/surface-release/core.json
python3 tools/run_agent_conformance.py --output build/surface-release/agent.json
```

The first command normally returns **2** before external evidence is supplied. Exit **1** records executed failure, discovery/fixture problems or changed inputs during execution. Exit **0** means all selected requirements passed. `--allow-pending` changes only the pending exit status for CI preparation; the JSON retains every pending gate and `full_gate_complete: false`. It never converts a failed test to success. The full-suite mode returns 0 only when every discovered test passes, the inherited test floor remains present, and inputs remain stable.

The full-suite report names every executed test and records its actual outcome. Counts cannot replace the required test identities. Skips, loader failures, duplicate or missing results, stale inventory and changed runtime bytes cannot close the regression gate.

## 3. Build actual source artifacts and inspect the destination

Install the pinned development-only validation tools with `npm ci --prefix tools`; the Python runtime itself uses the standard library. Install the corresponding Playwright Chromium build using the procedure in [OK-ENG-002](OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). Then run:

```bash
python3 tools/build_surface_agent_demo.py --output-dir build/surface-release/native
node tools/verify_surface_native.mjs --demo-dir build/surface-release/native --output build/surface-release/native-destination.json
node tools/verify_surface_viewer.mjs --demo-dir build/surface-release/native --fixture palette-repaired --fixture composition-ordinary --fixture composition-generated --fixture rotated-release --output-dir build/surface-release/native-browser
```

The builder sends actual service operations. It preserves every request and response, rejected and accepted source snapshots, dependency identities, complete paginated triangles, evaluation results and bounded artifact retrieval. It supplies no Python geometry to the service. The exported artifacts include the fixed held-out dimensions and largest admitted single loft, ordinary and generated part compositions, isolated material changes, and two separate nonidentity animation/release cases.

The destination tool validates the exact GLB with Khronos and loads it through Three.js. It compares decoded triangles, winding, normals, material regions and linear PBR values against the predetermined source oracle. It checks local placement and source-driven world poses independently of exporter-reported pass flags. Regional edit pairs must preserve every unaffected geometry/material region. The browser tool checks seven fixed times per selected fixture and records front/side views at time zero plus the animated front view at 1.5 seconds.

Inspect all 12 produced PNGs. Record one factual observation and a reviewer identity for each exact capture hash. A script producing a PNG cannot supply the visual review itself. Keep the complete browser report with the captures so rendered frames, numerical poses, source revisions and artifact identities remain connected.

## 4. Reissue current legacy construction evidence

Changing native runtime modules also changes the implementation identity used by earlier profiles. Preserve historical construction evidence and run a fresh C20 in a new output directory:

```bash
python3 tools/build_construction_demo.py --output-dir build/surface-release/legacy-c20
node tools/verify_gltf.mjs build/surface-release/legacy-c20 --output build/surface-release/legacy-c20/external-results.json
node tools/verify_construction_viewer.mjs --demo-dir build/surface-release/legacy-c20 --output-dir build/surface-release/legacy-c20
python3 tools/record_construction_evidence.py --help
```

After visually inspecting `keyed-rack.png`, use `--demo-dir build/surface-release/legacy-c20 --evidence-dir build/surface-release/legacy-c20 --reviewer "REVIEWER" --visual-review "ACTUAL OBSERVATION"` with the recorder to bind its actual source bundle, workflow, GLB, reference, external results, browser results, capture and visual observation. Replace both placeholder values with the actual review. Keep these files under the repository root because the construction evidence contract uses repository-relative paths. Run the full construction conformance command with that newly recorded `external-gate.json`; the historical CI compatibility check intentionally keeps a changed implementation's C20 pending and cannot substitute for this step.

```bash
python3 -m ontokin.construction_conformance --external-evidence build/surface-release/legacy-c20/external-gate.json --output build/surface-release/construction.json
```

## 5. Supply identified evidence and observed CI

The versioned record shapes are fixed in `conformance.json` under `evidence_contract`. Each referenced file uses `{path, sha256}`, with a relative POSIX path beneath `--evidence-root` and an exact `sha256:` identity. Nested workflow/source paths resolve beneath their report's output directory. The top-level `ontokin.surface-release-evidence/0.1` manifest contains:

- `implementation`: the current `{name, version, source_code_sha256}` identity.
- `workflow`: the native workflow report's file identity.
- `native`: identities of `build.json`, the destination and browser reports, and `visual_reviews` with `capture_sha256`, `status: "reviewed"`, `reviewer` and `observation`.
- `legacy`: identities of the core, agent, full-suite, current construction and construction external-gate reports.
- `ci`: the identified `ontokin.surface-ci/0.1` record.

Read the actual GitHub Actions run and every required job after they complete. Retain the raw API responses alongside a CI record with the exact implementation commit, run ID/head SHA/status/conclusion/URL, and job IDs/run IDs/names/status/conclusion/roles/Python versions. Do not infer a pass from a configured workflow or a previous commit. The named commit must be available locally so the reader can compare its actual Git tree with the current verification inventory. Evidence output and archival documentation are excluded from that inventory to avoid making a new report invalidate its own execution.

```bash
python3 tools/run_surface_conformance.py --external-evidence build/surface-release/release-evidence.json --evidence-root . --output build/surface-release/surface-conformance.json
```

The release audit reads retained files; it does **not** rerun Khronos, a browser or GitHub. It explicitly reports `executed_external_tools: false` for this phase. The earlier commands and the integrator's observed CI/visual review establish those external executions. Missing, stale, contradictory or incomplete evidence leaves the relevant gate pending. The final report identifies both the implementation and the complete verification-input inventory before and after its actual test execution.

## 6. Publish and integrate

Follow [AGENTS](../../AGENTS.md) for branch ownership, the bounded integration lease, observed-head updates and current-main checks. Retain the generated reports, sources, artifact bytes, capture observations and hash manifest in a new evidence record or identified archive. Do not rewrite historical evidence to match a new digest.

Only after the full named gate and required checks pass should STATUS mark this finite surface release complete, identify its implementation/merge/CI commits and exact test results, and choose the next unmet GOAL requirement. A successful surface release does not establish live destination physics or the complete programming language.
