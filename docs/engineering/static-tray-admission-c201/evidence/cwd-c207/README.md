# C207 working-directory component evidence

The [working-directory contract](../../WORKING-DIRECTORIES-C207.md) resolves the C205/C206 launch-plan mismatch. Every planned command cwd equals its stage output; construction/receiving job and supervisor receipts bind that same path. This component grants no native readiness or process authorization.

## Review and checks

- [Independent decision](cwd-review/REVIEW.md): APPROVE_CWD_COMPONENT_ONLY for exact local candidate `bd9fbf1487e557b9c21baf1d39e7b9cb818d4773`. All 29 independent CPU controls passed; 36 exact reviewed bindings match the integrator candidate.
- [Implementation report](cwd-implementation/REPORT.md) and [source-bound result](cwd-implementation/RESULT.json): 135 methods (72 input-lock, 47 transaction, 16 working-directory controls). Original mismatch reproduction and source snapshots remain in that directory.
- [Integration checks](CHECKS.json): all 171 current C201 methods, 78 source/compiler methods and 43 core cases / 694 assertions passed. All 301 historical inputs and four frozen protocol documents remain exact.
- [C201 log](validation/candidate-components/tests.log), [source/compiler log](validation/candidate-source-compiler/tests.log), [core report](validation/candidate-core.json), [preservation](validation/candidate-protected-inputs.json) and [validation scope](validation/PLAN.md) identify actual inputs and limits.
- The original reviewer expectation failure remains in [draft findings](cwd-review/DRAFT-FINDINGS.md), with original script/log/bindings. It required no implementation change.

All agents used the available Linux x86-64 CPython 3.12.14 environment. Three qualified-supervisor launch calls were intercepted by independent CPU controls before any child existed. Actual C201 native, receiving, Node, lifecycle and timed-author starts remain zero. Synthetic production-shaped inputs and receipts are fixtures, not current-host evidence or native approval.

Publication and actual-main results are recorded separately after remote verification. The next bounded gate is C201 readback/probe compatibility. Full coordinator/process provenance/deadlines, trusted bootstrap and complete host/dependency/alias sealing, independent native readiness and the sole four/four/four invocation remain pending. The inherited full regression remains FAILED: 4,239 distinct passing methods; thirteen torque-read methods not run after the unchanged 30,000 ms setup timeout.
