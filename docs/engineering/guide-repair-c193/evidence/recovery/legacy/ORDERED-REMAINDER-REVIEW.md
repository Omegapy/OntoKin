# Conditional review: complete the unexecuted unit-test remainder

**An ordered supplemental run is a reasonable development-verification action only after an actual stock-driver timeout is observed.** It must remain a separate invocation. The original driver stays failed or incomplete; combined coverage does not change its outcome or its `complete_regression_passed` field.

This review inspected candidate `bc8c0918045248cd3d34c64e40c135fff0eec985`, tree `631034be6fcd5249af753a9852a13f76baf44493`, from the independent clean checkout. No tests were started, and no repository file, fixture, budget or expected result was changed. The live run belongs to the legacy reviewer; this note does not predict its eventual result.

## What the stock driver does

`tools/check_local.py` executes `python -m unittest discover -s tests -v` in an isolated source copy. Its `--timeout` is a wall-clock allowance for each driver command, separate from the resource limits inside individual tests. On command timeout it terminates the process group, records that step as failed, and continues the other planned core roles. Only an interrupt stops the driver loop early.

Therefore, if the unit command times out, allow the original driver to finish its remaining source, Agent, construction, surface, impulse and documentation roles. Preserve its complete final summary and raw logs before starting supplemental work. Do not rerun already completed roles merely to obtain a green aggregate label.

Read-only inspection found no custom `load_tests`, `setUpModule` or `tearDownModule` definitions in the 354 discovered-pattern test modules. The installed Python 3.12 unittest implementation calls class setup before starting the first method in a class, per-method setup/teardown and cleanup through normal `TestCase.run`, and class teardown/cleanup when the class changes or the outer suite ends. Its loader sorts directory entries, class names and method names by the standard loader rules. Actual discovered groups and IDs, rather than a newly sorted list of string names, should be retained.

## Safest bounded selection

After the timeout and original driver completion:

1. Preserve the source commit/tree, interpreter and pinned verification environment. Use a fresh isolated workspace at the exact candidate inputs. Do not use a driver workspace whose later roles may have regenerated example products unless every relevant test input is first established identical. Keep the source and evidence outside the user's working checkout.
2. Use the original `TestLoader.discover("tests")` to import the entire suite in the standard order. Discovery is not test execution. Require no loader errors, record every discovered test ID in order, and reconcile the expected 4,252-method inventory against the unchanged historical inventory. Do not silently accept a changed inventory.
3. Parse the frozen stock log using the already corrected multiline-aware parser. Retain each started method, completed outcome and any class-fixture error. Determine the last-started method at termination. If there is no unambiguous mapping from the log to the discovered groups, stop and resolve it.
4. Find the top-level discovered module suite containing that boundary method. Select that **whole module suite and every subsequent module suite**, preserving the original group order. Rewind the boundary module even if its last printed method ended in `ok`: its class teardown or the next class setup may have been interrupted before the next method name was printed.
5. Run those preserved module-suite objects once through standard `unittest.TestSuite` / `TextTestRunner(verbosity=2)`, with ordinary failure continuation. Keep all class and method fixture mechanisms. Do not call test methods directly, bypass setup, reconstruct the tail using individually sorted names, or remove a class because its setup is known to be expensive.
6. Save the selected IDs and selection rationale before execution. Preserve commands, finite outer watchdog, raw log, exact result, source/input identities and before/after integrity. If result callbacks are additionally recorded, the recorder must delegate to the standard result methods without changing outcomes or execution.

Selecting whole groups provides a small, explicit overlap at the boundary. Count duplicate successful methods once for aggregate coverage and report their repeated executions separately. The first segment's incomplete method is an interrupted attempt, even if its later repetition succeeds.

The standard success result for a method occurs after its own teardown and cleanups. It does not alone prove completion of a following class teardown. Rewinding the complete boundary module addresses that uncertainty. Do not assume a missing method passed because another method in its class passed.

## Class fixtures and the A08 obligation

The possible remaining tail after the observed reach-recording region contains these class-level fixtures. Keep them through the ordinary suite machinery:

| Class or group | Setup and cleanup obligation |
| --- | --- |
| `ReachSourceCorpusTests` | Verify frozen hashes and all 45 mapped methods, then load the frozen independent oracle. Per-method temporary-directory setup/teardown remains active. |
| `ActualSurfaceOccurrenceReuseTests`, `IndependentStoredLiftCompleteGlbTests`, `IndependentPrimitiveOccurrenceTests` | Construct and export their own class fixtures under unchanged options and budgets. |
| `RingLoftAgentTests`, `TextureAgentTests` | Construct their schema registries/validators; preserve per-method isolated service setup and teardown. |
| `RingLoftIntegrationTests`, `TextureDeliveryTests` | Produce their own actual class-level export fixtures; do not substitute retained artifacts. |
| `SurfaceConformanceWorkflowEvidenceTests`, `SurfaceConformanceNativeEvidenceTests` | Build their own workflow/native evidence and clean their temporary directories in `tearDownClass`. |
| `SurfaceCorpusTests`, `SurfaceManifestExecutionTests`, `NativeSurfaceConstructionTests`, `NativeSurfaceExportTests` | Load declared fixture manifests or build their original class-level source/export state. |
| `TorqueArtifactReadTests` | Execute the original A08 seed construction/export, then all 13 artifact-read methods; retain method-level store/service checks and class seed cleanup. |
| `TorqueNativeParentSiteC093Tests` | Compile the frozen P28 source with its declared host policy and verify its exact program and parent-joint identities. |
| Connected-duct and duct offset/placement/selection/span audit classes | Load their original source contracts and generate their own class-level export witnesses. |

The exact timeout boundary may move beyond the observed reach-recording region. Select from the actual completed log, not the provisional module named in progress updates. Any boundary module's own setup and teardown must be reviewed before selection if it falls outside the region above.

`tests/test_torque_artifact_reads.py` defines its own `POLICY = HostPolicy(max_operations=1000000, max_elapsed_ms=30000)`. `TorqueArtifactReadTests.setUpClass` loads `workflow-agent-base.files.json`, creates a fresh `.22` project in a temporary store, then performs the frozen A08 export request from `agent/request-workflows.json`. That request retains the two-second recording, 4 fps, original geometry tolerances and actual runtime clock. The class checks the resulting artifact identity before providing the seed database to its methods.

Each method copies that seed into a new temporary store. Its existing controlled read clock is part of the unchanged test, not permission to replace the real clock in class setup. Method teardown closes peers and service handles, checks WAL cleanup and SQLite integrity, and removes its temporary directory. Successful class teardown removes the seed directory. If class setup fails, normal unittest behavior reports a fixture error and the 13 methods remain unexecuted; do not manually invoke them or supply another seed.

No specified external A08 prelude or cross-module execution dependency was found. Preserve every naturally preceding module in the selected tail, including the texture modules immediately before `test_torque_artifact_reads`. Full discovery preserves import order, but a new process cannot restore state warmed by previously executed tests. Report that difference explicitly. Do not claim the split is identical to the original single-process execution, and do not add artificial cache warming to obtain a pass.

## Acceptable disposition and stop conditions

OK-ENG-006 section 4 requires exact inputs, actual test identities/results, failures and unexecuted roles. OK-ENG-009 section 3 requires the complete applicable regression cohort and explicit failure accounting; it does not require one passing process as the only possible development evidence format. A fully reconciled successful prefix plus an ordered supplemental tail can therefore support **combined, split-process method coverage** for a bounded development decision. It cannot be submitted as a passing original full-driver invocation or silently substituted into a release schema that requires another evidence format.

The combined receipt should identify: the original timed-out command; its successful prefix; the supplemental selection and overlap; every method's observed outcomes; any fixture errors; remaining unexecuted IDs; exact inputs and environment; and the six other driver-role outcomes. Required released-behavior obligations still need actual passing execution. A new failure, an unexplained missing method, a skip, a discovery change or an uncertain effect on released behavior blocks that development decision until resolved.

If the unchanged torque A08 class setup fails again, retain its actual diagnostic and all 13 unexecuted methods. The prior C191 full run and candidate/main isolated controls already identify this separate experimental `.22` failure, and the legacy reviewer has bound the unchanged runtime/test/tool/torque input trees. A matching result may support the same specifically reasoned contained-incomplete-feature disposition under OK-ENG-009 section 3; it does not pass the full regression cohort or torque release. Any different failure needs fresh investigation rather than a preexisting label.

If the tail itself times out, preserve that failed attempt and reassess the exact remaining obligation. This plan is not authorization for repeated opportunistic splitting until a nominal green count appears. No source limit, test fixture, expected outcome, historical evidence or result status may be weakened to close the task.
