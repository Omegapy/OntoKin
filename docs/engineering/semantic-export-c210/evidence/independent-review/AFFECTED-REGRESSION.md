# C210 affected regression inventory

The complete finite affected cohort contains **262 preexisting test IDs in 18 complete modules**, plus **13 new semantic-export tests**. [AFFECTED-REGRESSION.json](AFFECTED-REGRESSION.json) lists every module, method ID, source hash and inclusion rationale. It includes all **128 unique test IDs required by the unchanged C01–C20 construction manifest**, with no omissions. This inventory was derived by parsing Python syntax trees; no tests were imported or executed.

The new sidecar calls the existing bundle loader, construction compiler, source provenance, JSON bounds and GLB validator. The new driver exercises existing Agent discovery, revision-safe editing, acceptance, artifact retrieval and recovery. Complete modules covering those calls and their shared parser/validator/evaluator/Agent foundations form the cohort. No result-based selection was made.

All 192 preexisting OntoKin Python files remain unchanged. The new opt-in module and proof driver do not change an existing parser, compiler, evaluator, Agent protocol, GLB exporter or source-language profile. Other profile suites therefore need no extra rerun merely because they exist; their mandatory-driver results and historical failures remain separately visible.

The inventory binds the mandatory-check candidate `7feb0dc501d3a6995732637f38c3c3b651914f4b`. Root HEAD advanced during preparation, so the JSON separately records the observed later revision and verifies that `ontokin/`, `tests/`, the semantic proof driver and local driver match the verification candidate. This is input equivalence, not a claim that the later complete repository tree was tested.

Reconcile these IDs against completed method outcomes in the actual local-driver log and separately bound focused runs. Preserve failures, errors, skips and missing/unrun methods. Execute only required missing affected methods or concrete failure-resolution controls. The original 43-case source role, documentation role and independent GLB/browser checks remain separate requirements.

This inventory **does not replace the mandatory local driver or convert its full-regression failure into a pass**. Unchanged source hashes help establish scope; they do not excuse a newly introduced or worsened failure. The inherited failed/unrun regression remains explicit, and any new global-driver failure requires its own honest accounting.
