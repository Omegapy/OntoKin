# C210 global-run error diagnosis

**Finding:** The observed error groups reproduce on published pre-C210 commit `94dee707c148b7a545e43d4de0d601642c5fa3e8` under the same original local-driver copy policy. They do not require the new semantic sidecar. No old runtime, test, validation limit or frozen reader guard was changed.

The global run remains **FAILED**. Its unit-test step stopped at the unchanged 900-second outer limit. The final coverage reconciliation identifies 4,342 passing actual test IDs and 91 errored actual IDs. Of 4,654 actual IDs found by separate intact discovery, 221 lack terminal outcomes: 216 belong to failed imports and five were unreached at timeout. Seven failed-import placeholders are recorded separately from actual test IDs. These observations do not constitute a full-suite pass.

The frozen coverage source is `evidence/c210/local-checks/UNIT-LOG-TALLY.json` (SHA-256 `753ec7ce256a8bf6cd4f148a918fe65c5595eaf119b8b2c6b63d29e0263e574d`). Its final parser accounts for 60 existing passing outcomes with multiline descriptions, including 56 dynamically generated force-source tests. The diagnosis independently checked the final count arithmetic and all 275 affected IDs against that report. These are corrections to the count, not new test runs.

## Reproduced causes

| Global group | Recorded errors | Reproduced cause |
| --- | ---: | --- |
| C201 input-lock tests | 72 methods | The driver omits the tracked `fixtures/` directory. Common setup cannot copy the required Q01 `main.ok`. |
| Static-tray finalization | 7 methods | Common transaction setup cannot read the omitted Q01 source manifest. |
| Static-tray transaction | 9 methods | The same missing source-manifest precondition fails before the controlled transaction. |
| Static-tray source | 1 method | Both Q01 source routes lack their manifests; the method then also indexes an empty result list. |
| Force and surface discovery guards | 2 methods | Repository discovery reports seven failed imports and correctly rejects that incomplete inventory. |
| Failed imports | 7 placeholders | Default Python bytecode writes create a local cache rejected by the frozen independent-reader guard. |

The missing-fixture groups account for **89 actual method errors**. The reader-cache/discovery group accounts for **two method errors plus seven failed-import placeholders**. Together they explain the 98 recorded error entries. This grouping combines representative tracebacks with the exact common setup/import paths; every individual global error was not rerun.

Both original-driver copies omit **42 tracked static-tray fixture files**. The baseline copy starts with no reader cache, then ordinary discovery creates four `.pyc` files and encounters the existing cache rejection. The guard is intentional: independent-reader execution must not use an unbound bytecode closure. The diagnostic work did not delete the original failed cache or bypass that guard.

## Executed controls and exact inputs

The current isolated candidate is `7feb0dc501d3a6995732637f38c3c3b651914f4b`. One targeted force test reproduced its traceback. Five further targeted methods covered the remaining groups. A new detached baseline checkout was then copied with its own original `tools.check_local.prepare_workspace` function, preserving the same omitted-fixture policy. The same six representative methods reproduced all groups on that baseline.

[Current force command and result](current-isolated-test.json), [other current controls](current-representative.json), [baseline copy preparation](baseline-copy.json) and [baseline controls](baseline-representative.json) retain the actual commands, environments, source commits, durations, cache observations and log hashes. Corresponding `.log` files retain complete tracebacks. Only these selected methods executed; no full suite was retried.

[Exact input bindings](exact-input-bindings.json) compare 598 preexisting Python and contract files between candidate and baseline copies. All match. The record also identifies every omitted tracked fixture by hash. The 192 existing OntoKin runtime modules remain unchanged; only the explicitly selected sidecar module is additive.

## Review disposition

The finite C210 component remains eligible for **experimental integration**, subject to the root's exact-input checks and actual-main affected, core and documentation checks. The separately reconciled 275-test affected cohort passed, and this diagnosis identifies no newly introduced functional legacy failure in the observed error groups.

This is not a waiver of the failed global run, proof that the 221 unrun cases would pass, or a full release certification. The short controls do not establish the cause of the 900-second whole-suite timeout. Preserve the inherited torque failures and prior timing observations separately.

A later, separately bounded validation-maintenance task can review fixture copying and documented source-only Python execution. No broad driver repair belongs to this semantic-export milestone, and no frozen guard or historical outcome should be weakened to obtain a green result.

## Retention

Keep this directory's `.json`, `.md` and `.log` records in the handoff. Exclude `baseline-source` and `baseline-copy/workspace`, which are temporary reconstructions of source already retained by Git history. No C201 native admission, C199/C200 schedule, receiver or timed author trial ran during these diagnostic controls.
