# C271 P02 validation results

Candidate: `88bc8b51b3963b7072375edac6400b6e6a4532e4`; tree `755f366d1091beb71b5421b14fdac0b9b868cfb0`. Both original processes completed and their clean source identity remained unchanged.

Affected observer cohort: **passed**, all 12 checks and 282 test methods, with zero failures, errors or skipped obligations.

Routine driver: **failed**, exit 1; all seven planned steps have observed outcomes.

| Step | Result | Exit | Seconds |
| --- | --- | ---: | ---: |
| unit-tests | failed | -15 | 900.025 |
| source | passed | 0 | 0.769 |
| agent | passed | 0 | 0.869 |
| construction | passed | 0 | 36.597 |
| surface | passed | 0 | 21.694 |
| impulse | passed | 0 | 53.316 |
| documents | failed | 1 | 2.271 |

## Required-gate findings

- `unit-tests`: Exceeded 900 seconds. Driver-parsed footer fields: `{"tests_run": 0, "skipped": 0, "expected_failures": 0, "executed_without_skips": 0, "complete_regression_passed": false}`. Complete log: `routine-candidate/logs/unit-tests.log`.
- `documents`: failed. Driver-parsed footer fields: `null`. Complete log: `routine-candidate/logs/documents.log`.

The unit log has no final `Ran ... tests` footer. The driver therefore records `tests_run=0` because it cannot parse a completed-suite total; this does **not** mean no tests executed. `PARTIAL-UNIT-LOG-ACCOUNTING.json` records two precisely defined progress-line parsers and the retained log hash. Neither progress-line count is a completed method count. No predicted missing-dependency skips are counted as actual skips.

The driver documentation check reports 21 missing local links to five files: `CHATGPT-START-HERE.md`, `ROLE.md`, and the `ontokin-session`, `ontokin-delivery` and `ontokin-learning` skill files. All five exist in the complete candidate checkout but are absent from the driver copy; its copy lists omit the two root files and `.agents`. The same checker passed in the complete candidate during the affected cohort. `DOCUMENTS-FAILURE-INSPECTION.json` preserves the exact failures and file/copy identities. The driver is unchanged from the observed main baseline, but that static equality is not a baseline execution or a waiver.

The available environment is CPython 3.12.14 / Linux x86-64. Pillow is 13.0.0. The installed rpds-py is 2026.6.3, while the lock names 2026.5.1. Historical absolute readback dependency and host-inventory paths are absent. No packages, pins, source, contracts, fixtures, expected results or hardcoded paths were changed.

A failure in the required routine gate prevents integration acceptance. The full observer cohort passing does not waive that gate. Pending external conformance cases retain their original status; this run establishes no complete release, other-Python compatibility, native/model trial or comparative claim.

## Evidence and process closure

The original routine execution is session 40272; affected execution is session 52200. `ACTIVE-OPERATIONS.json` records positively observed completion. `execution-receipts/` contains exact commands, timing, environment, source identities, stdout, stderr and return codes. `RUN-RESULTS.json` includes individual report inspection and verified evidence hashes. The C271 control was not replayed.

`WORKSPACE-RECOVERY-DELTA.json` records 0 new or modified non-Git workspace files and 0 missing original files. Any unique bytes are preserved in `workspace-recovery/`. Copied clean source and reconstructed `.git` are excluded from the ZIP, with exact source/input manifests retained. No original outputs were deleted.

The verified archive identity and extraction audit are external in `RAW-EVIDENCE-VERIFICATION.json`; `RESULTS.json` adds that receipt to the immutable run summary. No integration, publication or final Library delivery was performed by this worker.

Next action: Director preserves the complete evidence and delivers the phase handoff. Unmet acceptance requires retained branch/issue and a separately selected next phase; this worker performs no repair or automatic retry.
