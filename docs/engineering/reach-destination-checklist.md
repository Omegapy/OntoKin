# Reach native and browser execution checklist

This is an execution handoff for the adopted [release contract](../language-design/planar-reach-v0.1/release-contract.md), not an acceptance report. It adds tooling without changing the production operation allowance, frozen fixtures, tolerances, historical evidence, or the [full goal](../../GOAL.md).

## Documentation continuity

At the recovered `4292d51` source checkpoint, an exact SHA-256 comparison found all **95 narrative documents and 15 diagram assets unchanged** from the preserved [full-reading ledger](reach-release-review/documentation-review.md). That ledger retains its named reviewers, exact source cut and reading modes. The present continuity check does not claim new full-body reads of all historical material or new visual inspection of the diagrams. The current work reread the active release/native/export requirements, authority and status records, and product-scope clauses needed to implement these destination roles. The ledger and frozen historical files remain unchanged.

The documentation continues to require actual source meaning, complete geometry and materials, purposeful action outcomes, useful Agent repair, independent destination observations, and explicit limits. A successful recorded reach artifact closes no broader creature locomotion, contact, deformation, live physics, Blender, or measured authoring-benefit requirement.

## Tool roles

| Tool | Concrete role | Limits of the result |
| --- | --- | --- |
| `tools/build_reach_source_artifacts.py` | Execute the 28 required source/export requests, or an explicit finite subset, with the compiler's existing shared 100,000-operation counter; preserve actual artifact bytes, settings, diagnostics and per-request results. | A source export pass does not establish native/browser or Agent acceptance. |
| `tools/reach_delivery_inventory.py` | Name the frozen source/Agent inventories, complete or required prefix horizons, settings and bounded evidence descriptors. | Inventory membership and correct intake do not prove delivery or protocol behavior. |
| `tools/verify_reach_destinations.py` | Sequentially prepare independent references, validate actual supplied source/Agent bytes, and optionally execute the prescribed browser selection on one exact clean committed cut. | Its completeness flags describe the executed corpus only; Agent audit, actual image review and release acceptance remain separate. |
| `tools/verify_reach_native.mjs --plan` | Decode supplied actual GLB bytes and enumerate every retained key, eight distinct interiors per interval, and both source-boundary sides. | Does not generate source expectations or validate Agent transport. |
| `tools/build_reach_native_reference.py` | Compile the exact source bundle, obtain independent `ReachReference` pose/site enclosures for that actual-byte schedule, add fixed fixture observations inside the prefix and phase neighbors, and copy identified inputs into a fresh directory. | Does not export, sample production poses, or establish the exporter request budget. Geometry-constructor reuse is disclosed. |
| `tools/verify_reach_native.mjs --manifest` | Run actual Khronos validation and actual Three.js decoding/controlled playback, comparing full source geometry/PBR, every required carrier/site pose, and all world vertices. | The native component still requires independent source/certificate, Agent, browser and release audits. |
| `tools/verify_reach_viewer.mjs` and `tools/reach_viewer_harness.mjs` | Require a passed native report for the same manifest, load the supplied GLB in actual Chromium WebGL, exercise real controls, compare source enclosures with browser readbacks, and retain three identified screenshots per artifact. | Screenshots remain pending actual human/agent image inspection; a successful command does not supply visual review. |

The bridge shares one finite offline counter through source loading and dense independent expectation construction: at most 100,000,000 arithmetic callbacks and 900 seconds, with the native sample/observation/world-vertex limits also enforced. This is a separate verification role over many observations. Source compilation retains its own unchanged 100,000-operation gate. The bridge report explicitly says it does **not** test the production export request's shared 100,000-operation budget. The reference callback limit cannot be used to make a failed runtime request pass.

For recognized P/N/L IDs, the bridge requires the frozen case's exact program revision. Fixed samples beyond a requested prefix are counted as outside that prefix; they are not silently claimed executed. Each independent positive-width phase additionally receives two exact neighbor clocks with offset `min(1e-6 seconds, phase width / 16)`. Recorded binary64 clocks and exact authored rational clocks remain distinct observations. Current tooling rejects an observation outside its requested independent horizon; it never extrapolates a valid prefix to conceal a later failure.

The browser receives GLB bytes and identity labels only. Expected meshes and pose trajectories remain on the host. Native carrier translation-key bounds, enlarged by each decoded carrier's local geometry radius, fit the complete supported linear-translation and rigid-rotation extent. Every seek retains the selected camera. Local material factors, native vertex probes, complete carrier poses, and source-site positions reconstructed from actual browser matrix readbacks are checked. Arbitrary play/pause clocks establish control stability; numerical source checks use the explicit independent seek schedule.

## Exact tools and preparation

The committed `tools/package-lock.json` pins Three.js **0.180.0**, Khronos validator **2.0.0-dev.3.10**, Playwright **1.56.1**, and esbuild **0.25.10**. The release requires **Node 22**; its patch version is recorded, not silently assumed. Matching Playwright Chromium is **141.0.7390.37 / build 1194**. Use a separate browser cache and never substitute a globally installed newer Playwright or Three package.

```bash
cd tools
npm ci --ignore-scripts --no-audit --no-fund
PLAYWRIGHT_BROWSERS_PATH=/absolute/verification-browser-cache node node_modules/playwright/cli.js install chromium --only-shell
```

The source/reference bridge itself uses the Python standard library. The complete release still requires separately identified CPython 3.11, 3.12 and 3.13 runs and the existing pinned verification-only packages. Dependency installation is not runtime or browser validation. Never commit `node_modules`, browser caches, or installed interpreters.

## First actual-artifact execution

Use one clean committed source cut containing the exporter, independent reference, bridge and browser tools. The artifact's source and destination numerical-basis hashes and the reference oracle's source hashes must agree with that cut. Preserve failed attempts and use fresh output paths outside the checkout. Execute under the repository's exclusive runtime/workflow/browser window.

For an already exported P01 quarter-second prefix, with `$REACH_NODE` naming the actual Node 22 executable and `$REACH_RUN` an existing fresh evidence parent:

```bash
"$REACH_NODE" tools/verify_reach_native.mjs --plan "$REACH_ARTIFACT" --output "$REACH_RUN/native-plan.json"
python3 tools/build_reach_native_reference.py --source-manifest docs/language-design/planar-reach-v0.1/p01.files.json --artifact "$REACH_ARTIFACT" --plan "$REACH_RUN/native-plan.json" --case-id P01 --end 0.25 --output-dir "$REACH_RUN/P01"
"$REACH_NODE" tools/verify_reach_native.mjs --manifest "$REACH_RUN/P01/native-input.json" --output "$REACH_RUN/P01/native-validation.json"
PLAYWRIGHT_BROWSERS_PATH=/absolute/verification-browser-cache "$REACH_NODE" tools/verify_reach_viewer.mjs --manifest "$REACH_RUN/P01/native-input.json" --native-report "$REACH_RUN/P01/native-validation.json" --case P01 --output-dir "$REACH_RUN/P01-browser"
```

The selected single-prefix browser run is a component probe, not the complete prescribed browser corpus. The bridge's `--source-kind agent_retrieved_artifact` label also does not audit transport; it must be linked to actual requests/retrieval and an independent Agent provenance audit.

Run the bridge clock/fixture tests, direct native resource probes, and direct browser selection probes in the granted execution window. Preserve the actual named probe output rather than interpreting a file-level wrapper as all checks executing:

```bash
python3 -m unittest discover -s tests -p test_reach_native_reference_bridge.py -v
"$REACH_NODE" tests/reach_native_resources.mjs
"$REACH_NODE" tests/reach_viewer_resources.mjs
```

## Required release inventory

| Role | Required inventory |
| --- | --- |
| Source-built actual GLBs | **28**: P01–P23, P25, P26 and L01–L03. P17 is its valid `t=2` prefix. P24 remains a source/Agent positive budget case without an oversized-history GLB promise. |
| Agent-retrieved actual GLBs | **Nine**: P01, P11, P13, P20, P16, P17 valid prefix and L01–L03; plus a **separate tenth** L04 `t=0.25` recovery artifact after LP01 reset/new run with unchanged program revision. |
| Source browser artifacts | **Nine**: P01, P11, P20, P16, P18, P19 and L01–L03. |
| Agent browser artifacts | The nine ordinary retrieved artifacts above. The additional L04 recovery remains separately native-validated. |
| Browser captures | At least **54 fresh images**: complete front, complete side and action-specific intermediate for each of 18 artifacts. |
| Native samples | All retained keys; both semantic-boundary sides; midpoint plus seven further distinct interiors for each adjacent key interval; fixed fixture samples and phase neighbors; complete carriers, sites, geometry and payload trajectories. |

L01's intermediate image is paused between `.5` and `1.5` seconds, with a separate resumed moving check after `1.5`. L02 must be observed after `.5`, L03 after `2`, P16 after release at `2`, and P17 inside its successful prefix. All numerical observation times remain in the report even when no additional screenshot is retained.

Predetermined caps remain `.001 m` position, `.001 rad` rotation, `1e-6 s` stored-clock error and `1e-5 m` local vertices; any tighter requested cap remains binding. Dense comparisons do not replace the independent continuous certificate. Khronos defaults to zero errors and zero warnings. Every material/geometry/motion corruption probe must start from an otherwise valid identified artifact and retain unrelated expected source content, with transport identities recomputed so that the intended numerical/geometric comparison actually rejects it.

## Complete corpus orchestration

The source producer makes one actual request per case. Its default settings are explicit **1 fps**, **helpers=false**, and the adopted default position, rotation and time caps. The requested frame rate is the initial recording schedule; adaptive keys still have to satisfy the unchanged continuous and supplied-byte numerical requirements. This choice changes neither the required horizons nor the source programs. It does not claim that every other supported request setting has passed.

| Cases | Required export end |
| --- | --- |
| P01–P13, P15, P18–P23 and P25 | Full `3` seconds. |
| P14 and P16 | Full `4` seconds. |
| P17 | Successful `2`-second prefix; the separate full request must fail as specified. |
| P26 | Full `60` seconds. |
| L01 and L03 | Full `4` seconds. |
| L02 | Full `2` seconds. |
| Additional Agent L04 | Separate `0.25`-second recovery after the required reset and fresh run. |

Use the same clean committed source cut for production, independent reference construction, native decoding and browser playback. The orchestration records all tracked repository file hashes and Git identities before and after execution, including failed runs. It rejects a producer from a different commit or tree; an explicit eligible-input equivalence audit is a separate route and is not inferred by this runner. All output paths below must be fresh directories outside the checkout; `$REACH_AGENT_REPORT` names the actual separately executed Agent producer report.

```bash
python3 tools/build_reach_source_artifacts.py --output-dir "$REACH_SOURCE_OUTPUT" --fps 1
PLAYWRIGHT_BROWSERS_PATH=/absolute/verification-browser-cache python3 tools/verify_reach_destinations.py --producer-report "$REACH_SOURCE_OUTPUT/report.json" --output-dir "$REACH_SOURCE_DESTINATION" --node "$REACH_NODE" --browser
PLAYWRIGHT_BROWSERS_PATH=/absolute/verification-browser-cache python3 tools/verify_reach_destinations.py --producer-report "$REACH_AGENT_REPORT" --output-dir "$REACH_AGENT_DESTINATION" --node "$REACH_NODE" --browser
```

The Agent input schema is `ontokin.reach-agent-delivery-workflow/0.1`. It supplies the exact `source_commit` and `source_tree`, and an ordered `deliveries` array. Each successful delivery identifies `case_id`, unchanged frozen repository-relative `source_files`, `program_revision`, explicit `options.end`, `options.fps`, `options.helpers=false`, actual `project_id`, `run_id` and `artifact_id`, and an `artifact` descriptor with normalized relative `path`, exact `sha256:` hash and byte count. The complete Agent producer must retain the linked requests, responses and retrieval records, including L04's reset and fresh-run identity. The destination wrapper checks the supplied bytes and source identity; the independent Agent audit checks the transport and transaction claims.

The wrapper copies a producer report for provenance and records its original identity. Retain the complete original source or Agent producer directory as well: its artifact and exchange references are relative to that original directory. A copied report alone is not a self-contained Agent transport record. Native case directories separately contain the exact supplied artifact bytes, source units, independent references and plans used by the destination checks.

Repeated `--case` options on either wrapper select a finite development probe. A subset does not set the corresponding complete-corpus flag. For example, selecting P01 still requires its complete `3`-second delivery; the earlier quarter-second component probe uses the lower-level commands above and cannot enter this mandatory corpus as full P01. The wrappers reject duplicate cases, unpromised P24/L04 source artifacts, changed program revisions, missing explicit frame rates, weaker tolerances and substituted artifact bytes. Their focused intake checks are:

```bash
python3 -m unittest discover -s tests -p test_reach_destination_inventory.py -v
```

These wrappers and intake checks are prepared for a subsequent granted execution window. Their addition does not claim an executed full-corpus pass. The separately published [first destination evidence](reach-first-destination-validation/README.md) remains a single old-basis P01 quarter-second component result; its artifact is not relabeled as current or full-duration evidence.

## Gates after component success

Actual complete source cases, independent reference and rate acceptance, R01–R12/Q01–Q22 mapping, all 42 unchanged LP steps, required failed delivery/rollback/cancellation requests, all mandated artifacts, actual visual review, Python compatibility, inherited workflows, independent release audit and resulting-main checks remain required. Preserve exact Git/input identities before and after every execution and retain raw failures. The final audit must distinguish failed and pending rows; the full product goal remains open after any finite reach release.

At initial tooling publication, only static syntax checks had run for these new bridge/browser files. No fresh native or browser success is asserted by this checklist. Execution receipts and image-review observations must be published separately after actual runs.
