# Independent review: recover the inherited harness timeouts

**Approved:** run the separately recorded `inherited-full02` attempt with the original **3,600 seconds per driver command** and **7,200 seconds for the outer supervisor**, on unchanged candidate `39afec7971b9221fe58cf7c7d002505d172dd64f`. The exact reviewed plan is `evidence/recovery/PLAN.json`, SHA-256 `84ded7b8d5d59d87b7c58216b38f657e961ce39e6d9610fd4d1b4271a603ed56`. This approval covers recovery of the harness settings and makes no claim that the fresh run has passed.

## Evidence and reason

The retained C087 invocation explicitly used `--full --force-agent --timeout 3600` and an outer `timeout_seconds: 7200.0`. Its unit role passed all 3,979 tests with zero skips or expected failures. The role occupied **1,237.175 seconds of harness wall time**; unittest itself reported **1,233.161 seconds**. Both exceed the C088 preparation's narrower 900-second allowance. The historical overall attempt was **failed**, because its documents role failed; this review does not relabel that attempt. Its recorded source cut was `af585dd9a6d952a61a0ea8b45d3597ef6cc4b796`, and its before/after source identities matched. [Evidence: `evidence/historical/invocation.json`, `summary.json`, `unit-tests.log`.]

The original C088 preparation and actual `inherited-full01` invocation chose 900 seconds. The unit role was terminated with return code -15 after 900.046 seconds and the explicit reason `Exceeded 900 seconds`. Its log has no complete unittest footer. The driver's recorded zero test count reflects that missing footer; many test bodies had executed. The full attempt was still running other roles when this review copied its exact records. That as-observed snapshot is not a final full-suite result. [Evidence: `evidence/preparation/VALIDATION-COMMANDS.json`, `evidence/full01-as-observed/invocation-start.json`, `summary.json`, `unit-tests.log`.]

## Source consistency

`tools/check_local.py` is byte-identical between recovered final C087 and the fixed C088 candidate, SHA-256 `1b64398d9a5a724dcec964017d8e1d86ffdef31e6d158c2175c8ccf35fb98381`. Lines 392–414 launch and wait for a driver subprocess and record a failure when the wall-time limit expires. Lines 494–502 preserve the role plan and pass the timeout to that wrapper. Lines 537–558 define the option as a maximum per command. This is an external validation harness limit, separate from the language's product execution ledgers. The actual historical and current attempted plans retain the same ordered 34 roles. [Source: `evidence/source/check_local.py`; both summary files.]

The new supervisor, SHA-256 `96d18ba4c31a84d1d4b608b545ce081d4c1e9d9b35775a3fa2ac75596c492244`, changes only its outer `process.wait` cap from 3,600 to 7,200 seconds and adds explicit cap/self-hash recording. Its command selection, environment, raw output capture, failure reporting, and process cleanup are otherwise unchanged. [Source: `evidence/recovery/run_role.py` and `run_role_7200.py`, especially new lines 22 and 29.]

## Execution and acceptance boundary

Use the concrete command and supervisor arguments recorded in the reviewed plan after full01 closes, with fresh full02 output paths and the existing no-concurrent-workload condition. Preserve all prior attempts. No source, fixtures, expected answers, suite membership, product budgets, or historical statuses are changed. A complete actual full02 result remains necessary before reporting success; this review is not release acceptance or a performance certificate.

This review ran no tests or product workloads. It read and hashed the specified files, checked the fixed candidate's clean Git identity, and copied exact evidence bytes to this new review directory. `REVIEW.json` binds every copied byte stream, origin, mode, and observed time. All earlier evidence and the separately sealed artifact-verification closure remain unchanged.
