# C223 R01 author report

The bounded validation-driver repair is implemented at unpublished commit `7a72d489235a6bc880ffd6c9732591a94a0ae383` (tree `a5967bda226def86cd7e0aef79caa7d7a5ec976e`), based on published C222 main `3891869bb0c58a04d38b02bdfded226f924c21c2`. Only `tools/check_local.py` and `tests/test_local_checks.py` changed.

## Behavior

The shared source-directory list now contains top-level `fixtures/`, so copying, file inventory, source-stability checks and untracked-source accounting agree. The current repository has 42 tracked fixture files, all present in the actual 15628-file inventory. Every tracked top-level repository entry is covered by the declared roots/root files.

Every directly planned Python command receives `-B`. Each executed step also receives `PYTHONDONTWRITEBYTECODE=1`, recorded in its evidence, so ordinary Python descendants inherit the same policy. This does not weaken or alter the frozen independent-reader guard. Existing source caches are still excluded from the isolated copy by the unchanged exclusion policy; no original cache or historical failed evidence was deleted.

## Focused evidence

`baseline-with-regressions.log` preserves the run against the unchanged driver with new regressions: 30 test methods, 11 failed assertions/subtests. Seven methods are affected; the parent-only `-B` counterexample succeeds by observing actual child-created bytecode. `baseline-with-regressions.json` binds the original driver and test bytes, exact command and environment.

`corrected-focused.log` and `.json` bind the same focused invocation after the repair: 30 methods passed, zero errors, failures or skips. Controls exercise every declared root/root file, an actual child read of a top-level fixture, source and workspace fixture mutation, fixture symlink rejection, planned flags for all four role combinations, direct execution with `-E`, and an ordinary Python grandchild. The existing 22 methods continue to check source/Git isolation, failure/blocking, timeout, skipped-test and report handling.

`actual-source-input-inventory.json` contains complete current source identities; `AUTHOR-RESULT.json` records the commit, counts and exact changed-file hashes. `git diff --check` passed. The tested file hashes match the committed files; committing adds no code change.

## Limits and next action

This is focused R01 evidence. It is not the full aggregate R02 regression, compatibility matrix, native acceptance or a release claim. No native target, `.ok` source evaluation, export or render ran. Historical failures, fixtures, frozen-reader checks, default budgets, timeout values, generated exclusions and expected outcomes remain unchanged. A descendant intentionally ignoring its environment must supply its own `-B`; all currently planned direct Python commands already do.

Independent review, integration, actual-main checks and final saved handoff remain root-owned.
