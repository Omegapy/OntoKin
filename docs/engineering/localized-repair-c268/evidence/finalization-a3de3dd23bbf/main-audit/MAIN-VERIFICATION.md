# C268 fresh resulting-main verification

**Passed: all 12 required groups, 282 methods and 14 corpus bindings.** Zero failures, errors or skips occurred. Worker `/root/remote_audit` ran the unchanged existing cohort once and then audited its receipts without repeating product checks.

## Source and execution

Actual integrated source: `5084dd69312e8da5a49aadd33cf83ba56db7c058`, tree `07971fcdbc6d912febc6adbec7ebf576eccab43f`. Tracked and untracked checkout state stayed clean; all 159 explicitly recorded input identities stayed unchanged.

Execution began `2026-11-20T00:29:52.171662+00:00` and ended `2026-11-20T00:30:54.505503+00:00`. Runtime: CPython 3.12.14 / Linux 6.18.57 x86-64 with glibc 2.41, Clang 22.1.3, bundle 26.1117.11355. The interpreter binary and checked implementation/dependency/fixture/runner hashes match the accepted candidate evidence.

The exact invocation was:

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -B docs/engineering/localized-repair-c268/evidence/run_checks.py --repo /workspace/scratch/a3de3dd23bbf/OntoKin --phase main-integration --output /workspace/scratch/a3de3dd23bbf/evidence/main-integration --c268-methods 35
```

| Group | Methods | Result |
| --- | ---: | --- |
| c253-corpus | — | passed |
| c255-oracle | 31 | passed |
| c256-reader | 29 | passed |
| c257-ownership | 23 | passed |
| c258-follows | 28 | passed |
| c261-hinge_glb | 28 | passed |
| c265-source_hinges | 49 | passed |
| c266-binding | 34 | passed |
| c267-comparison | 25 | passed |
| c268-endpoint | 35 | passed |
| workflow | — | passed |
| documentation | — | passed |

## Receipt audit

All 284 audit assertions passed. This audit checked all 159 source identities against main Git blobs, all 30 output files against their size/SHA-256 receipts, exact output inventory, all group logs and method totals, the accepted code/test/dependency/fixture identities, and every control ledger's expected/actual outcome. Preserved input ZIPs have safe unique names and valid CRCs.

C266 recorded 748 calls: 28 bindings and 720 typed refusals. C267 recorded 123 calls: 35 agreements and 88 typed refusals. C268 recorded 131 calls: 121 historical and ten raw, comprising twelve historical admissions, nine raw successes and 110 typed refusals, with no untyped exception. C253 verified fourteen bindings across three tasks.

The fresh `CHECKS.json` is 93,825 bytes, SHA-256 `b2af5b4c93f39f297f6711ee74a210ca48e44e01becb6454f7b5c8fc10ad6492`. Preserve it and every receipt-listed file from `../main-integration/`, including ignored logs and ZIPs. `MAIN-AUDIT.json` contains the detailed audit and this directory's `ARTIFACTS.json` identifies the audit files.

The first audit attempt assumed C266 exposed the input-stability flag used by C267/C268. That schema assumption caused a `KeyError`; the audit source and failure record are retained as `audit_main.attempt01.py.txt` and `ATTEMPT01.json`. The corrected audit uses C266 exact input identities and the surrounding before/after source inventory, while still requiring the explicit flags for C267/C268. This was an auditor error, not a cohort failure. The cohort was not rerun.

## Remaining gates and limits

The Director still owns publication of exact evidence, final integration/branch records, verified saved handoff, separate receipt and closure. No process remains active. No repository/index mutation, installation or remote write occurred in this worker subtask.

This proves only the specified affected observer cohort in the recorded interpreter/environment. Full product aggregate, source conformance/export, other interpreters, native/visual/model trials, complete C260 H groups, site/world behavior, accepted revisions, edit atomicity, rebuild equivalence and comparative benefit remain unrun or unqualified as previously recorded.
