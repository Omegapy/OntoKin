# Agent interface validation evidence

This directory records execution evidence for [OK-AGENT-001](../OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md), the local `ontokin.agent/0.1` service. The adopted expectations come from [LANG-025–028 and A01–A10](../../language-design/OK-LANG-001-core-language-specification.md). Evidence records describe actual runs; schemas, case definitions, and scripted demonstrations are not by themselves pass results.

## Current evidence status

**The finite release gate passed locally and on GitHub CI.** The [validation summary](validation-summary.json) identifies `ontokin-reference` **0.3.0**, the October 18, 2026 runs, source/artifact identities, evidence-file hashes, and remaining limits. Python tests used CPython 3.12.14 on Linux. The measured package-source SHA-256 is `8a2eae260e2adfb28d6e1fd254cfefdb5fe47841509122ec1ad01e515a311142`.

Historical ENG-001/ENG-002 source/export evidence remains unchanged. The fresh regression reports here describe the new implementation; earlier success is not relabeled as agent-interface execution or new remote CI.

## Retained measured evidence

| Record | Observed result |
| --- | --- |
| [Complete suite](unit-tests.txt) | **150 tests passed in 26.878 s**, including 47 new agent, transaction, catalog, and CLI tests. |
| [Agent conformance](conformance.json) | **10/10 A01–A10** executed and passed, with actual requests/results, fixture identities, revision integrity, retry/cursor/cancellation/tombstone checks, and velocity meaning. |
| [Source conformance](core-conformance.json) | **43/43 cases, 694 assertions, 0 failures**. This source-only command does not execute A01–A10; their results are in the separate agent report. |
| [Authoring workflow](../../../examples/agent/workflow.json) | **41 real operations and 18 checks passed**: discovery, creation, inspection, rejected candidate, instance-only repair, unchanged sibling, prefix evaluation, named export, and bounded retrieval. |
| [Agent artifact validation](external-results.json) | One **125,892-byte GLB**; **0 Khronos errors/warnings** and **200 Three.js world-pose comparisons** passed. |
| [Legacy artifact regression](legacy-external-results.json) | **Six GLBs**, **0 Khronos errors/warnings**, and **347 Three.js world-pose comparisons** passed. |
| [Browser report](viewer-results.json) and [rendered capture](agent-authoring.png) | **8 checks and 16 world-pose comparisons passed**; capture visually reviewed; no page errors or HTTP(S) requests. |
| [Publication and CI](ci-results.json) | Implementation [commit c415250](https://github.com/Omegapy/OntoKin/commit/c4152509533f77ba54fac78268ba425df9b1a177); [run 39092228352](https://github.com/Omegapy/OntoKin/actions/runs/39092228352) passed Python 3.11–3.13 and all original/agent GLB and browser checks. |

The [service tests](../../../tests/test_agent.py), [transaction tests](../../../tests/test_agent_transactions.py), and [CLI tests](../../../tests/test_agent_cli.py) exercise real SQLite stores and semantic work. Their checks cover independent-process retry, competing prepared candidates and runs, cancellation before commit, controlled worker termination and recovery, live-worker non-stealing, and implementation-identity fencing. Passing those cases does not certify arbitrary power-loss recovery or distributed transactions. [Catalog tests](../../../tests/test_agent_catalog.py) verify registry coverage and execute the displayed callable examples in valid binding contexts.

The accepted [repaired source](../../../examples/agent/repaired.ok) has SHA-256 `d9b63c16c2efc92e947b0a39564234d9e14693cc9afb32bcffeabd08350cc324`; its retrieved [GLB](../../../examples/agent/repaired.glb) has SHA-256 `2cf4c92768ed6b5b07446f6b8e9d53ca13415a2596d8305f9401c2082bf92f3f`. The workflow, reference samples, export report, format/importer report, and browser report bind their observations to those identities. The head-radius parameter drives box dimensions in this example; the repaired occurrence is larger and the sibling retains its original default.

Independent verification uses Khronos glTF Validator **2.0.0-dev.3.10** and Three.js **r180**. The agent artifact's maximum sampled Three.js position/rotation errors are **7.152557390810443 × 10⁻⁸ m** and **3.422854299336317 × 10⁻⁸ rad**. Browser evidence uses Playwright **1.56.1**, Chromium **141.0.7390.37**, and Linux SwiftShader/WebGL2. The full conversion settings and numerical limits appear in the [export report](../../../examples/agent/repaired.export.json) and [OK-AGENT-001 section 12](../OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md#12-measured-results-and-remaining-work).

## Reproduce the executable checks

From the repository root, with Python 3.11 or later:

```bash
python3 -m unittest discover -s tests -p 'test_agent*.py' -v
python3 tools/run_agent_conformance.py --output /tmp/ontokin-agent-conformance.json
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-core-conformance.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The first command runs the actual protocol/runtime tests present in the implementation. The [conformance runner](../../../tools/run_agent_conformance.py) separately executes A01–A10 and writes `ontokin.agent-conformance/0.1` evidence with case outcomes, actual operation observations, implementation identity, and fixture hashes. These checks do not require an LLM provider.

## Reproduce the authoring demonstration

The [demonstration guide](../../../examples/agent/README.md), [workflow transcript](../../../examples/agent/workflow.json), and retrieved [repaired GLB](../../../examples/agent/repaired.glb) connect the source/edit/inspection/export steps. Generate fresh results in a temporary directory:

```bash
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-agent-demo
npm ci --prefix tools
node tools/verify_gltf.mjs /tmp/ontokin-agent-demo --output /tmp/ontokin-agent-external.json
node tools/node_modules/playwright/cli.js install chromium --only-shell
node tools/verify_agent_viewer.mjs --demo-dir /tmp/ontokin-agent-demo --output-dir /tmp/ontokin-agent-browser
```

The [driver](../../../tools/build_agent_demo.py) obtains validation, accepted source, run state, and binary output through `AgentService`. It checks an invalid unit candidate, a localized head-radius override, an unchanged sibling, prefix evaluation, and the source/GLB hashes. The independent Node verifier imports the retrieved bytes and compares Three.js playback with samples from agent inspection. It reports the actual Khronos validator findings separately. The [browser verifier](../../../tools/verify_agent_viewer.mjs) imports the same artifact into the offline viewer, checks selected poses and controls, and writes a fresh capture/report. A clean CI image additionally installs Chromium with `--with-deps`. The Node/browser packages are development verification tools; the Python service/exporter has no added runtime dependency.

The transport can be exercised with a separate local store:

```bash
python3 -m ontokin agent --store /tmp/ontokin-agent-experiment --request request.json --wait
```

Use request JSON conforming to the [versioned schema](../../language-design/agent-v0.1/request.schema.json). To test restart behavior, retain the same store and deliberate request identities. For an independent experiment, choose a new store/project; repeating an existing request is intentionally idempotent. Keep the editable `.ok` bytes together with the resulting revision, conversion report, and GLB identity.

After a package update, restart the Python process. Reopening the service within the old process does not reload cached modules and is not the documented upgrade procedure. The new implementation must preserve existing terminal retry outcomes and reject replay of old runs/queued work under a mismatched implementation identity.

For independent GLB/importer/browser verification, use the pinned tooling and commands in [OK-ENG-002](../OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) and [the visual demonstration guide](../../../examples/visual/README.md). Record which artifact was actually loaded; a prior screenshot of another revision does not validate a newly edited candidate.

## Interpretation limits

Passing a finite protocol corpus establishes the named local service behavior on those cases. It does not establish distributed exactly-once execution, multi-user permissions, production durability on every filesystem, hard real-time budgets, a tested Blender import, or broad language/product completion. A scripted authoring cycle is an interface demonstration, not a measured LLM authoring-benefit benchmark. The broader acceptance gates remain in [GOAL.md](../../../GOAL.md).

The viewer marks a custom GLB's numerical status as unknown when no validation report was imported. The checked-in independent reports validate this particular artifact; they do not make the viewer's file chooser a universal numerical certification tool. Numerical checks cover the recorded sample/probe sets and tolerances, not an all-time proof. Publishing the files is also separate from observing CI for their exact commit.
