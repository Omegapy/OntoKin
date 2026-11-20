# C268 independent verification

**Verdict: PASSED for the assigned R05 verification scope.**

Worker `/root/verify_c268_cohort` verified published commit `e6f55b73fa71953aa648bcd34711a6796a7346b6` and tree `d94436a22552db903b8016f9d035985a7d8b6752` in an authentic clean local clone with a separate index.
The earlier local commit `52af987fd5705c034bf264e2fe3fbc9fa1f146ae` has the exact same tree. Its complete passing run remains in `candidate/`; the fresh published-commit run is in `candidate-published/`.

## Execution

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -B docs/engineering/localized-repair-c268/evidence/run_checks.py --repo /workspace/scratch/ee457d84062e/verify-candidate --phase candidate-finalization --output /workspace/scratch/ee457d84062e/verification/candidate-published --c268-methods 35
```

Environment: 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]; Linux-6.18.57-x86_64-with-glibc2.41.

All 12 groups passed with 282 test methods, zero failures/errors/skips, and 14 C253 corpus bindings. Inputs and tracked/untracked checkout state remained unchanged.

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

## Evidence audit

`OUTPUT-AUDIT.json` records 25638 independent assertions across both runs and all source, log, report, snapshot and archive identities. Every one of the 30 output entries per runner manifest matches size and SHA-256; `CHECKS.json` is separately hashed, giving 31 files per run with no missing or unlisted files.
All logs and JSON results were parsed; every expected/actual call outcome and every archived or frozen byte reference was checked. Archive members were checked for unique safe names, CRC and content hashes. Sparse/selector recipe hashes were recomputed.

Published run controls: C266 34 methods/748 calls (28 bound, 720 typed refusals); C267 25 methods/123 calls (35 agreements, 88 typed refusals); C268 35 methods/131 calls (12 historical admissions, 9 raw successes, 110 typed refusals). C268 records 121 historical and 10 raw calls, no untyped exceptions, and real mode-000 permission denial at effective UID 1000.

## Preservation and workflow policy

Against immutable main `409ef18e0cb992ad1ab771c1258e989d5ef1c765`, all changes are confined to C268 engineering/task paths. Product documentation, runtime, fixtures, tests, examples, packaging, prototypes, tools, adopted language documents, all C260 files and workflow definitions have identical Git tree/blob identities. The Director supplied the main identity; this worker made no live remote-state claim.
Both workflow files allow only `workflow_dispatch`. Their boolean `enable_hosted_ci` defaults to false; all three jobs have explicit opt-in guards. No hosted run or billing change occurred. Repository-wide Actions disablement was not observed.

## Limits and remaining ownership

No full product aggregate, source conformance/export, native/visual/model trial, other interpreter compatibility or hosted workflow was run. This finite engineering observer does not qualify site/world behavior, physical validity, accepted revisions, edit atomicity, rebuild equivalence, full H groups or comparative benefit.
Separate exact-candidate review, integration/resulting-main checks, branch disposition and final saved delivery remain Director-owned gates. The worker made no source-checkout edits, commits, task/status/CURRENT changes or remote writes. No child worker was launched.

No blocker or active process remains.
