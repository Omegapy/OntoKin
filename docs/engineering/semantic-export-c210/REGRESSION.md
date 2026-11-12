# C210 regression disposition

The broad local-driver run is **FAILED**, and it remains failed in its original [summary](evidence/regression/summary.json). Its exact raw unittest log is retained losslessly in [unit-tests.log.gz](evidence/regression/unit-tests.log.gz). The complete handoff additionally includes the uncompressed logs, all procedural reports, before/after inventories and commands at `evidence/c210/local-checks/`. The [saved recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-0afce4bfc674819196c1bd42bff2eea0_2ab2a24d43748191957f9bcc356b59de&account_id=personal) preserves progress snapshots; its actual stage is authoritative. The final delivery receipt is written only after archive verification and a confirmed save.

[Canonical counts](evidence/regression/COUNTS.json), [affected coverage](evidence/regression/AFFECTED-COVERAGE.json), [input reconciliation](evidence/regression/INPUT-RECONCILIATION.json) and [baseline diagnosis](evidence/regression/force-error/DIAGNOSIS.md) bind the observations. The complete collected IDs and parsed outcomes are retained as lossless JSON gzip files beside them.

## Affected development gate

The new module is explicitly invoked and does not alter any existing runtime entry point. The [predefined inventory](evidence/independent-review/AFFECTED-REGRESSION.json) covers all 18 affected existing modules (262 methods), all 128 literal C01–C20 required IDs, and all 13 new methods. Every one of these 275 methods completed successfully in the original isolated candidate run. None was selected after seeing its result. New code, every invoked shared module, source bindings, actual Agent failures/retries, exact GLB references and independent output checks are covered separately.

This is the required affected-cohort gate under OK-ENG-009 for an isolated additive component. It is not permission to weaken a shared-runtime gate. All 192 preexisting runtime Python files remain byte-identical, and the larger 1,125-file preserved inventory remains exact. The mandatory driver was actually attempted; its failures are not omitted from the decision.

## Global attempt

| Observation | Count or outcome |
| --- | --- |
| Distinct actual IDs collected from intact source with bytecode writes disabled | 4,654 |
| Distinct completed passing methods | 4,342 |
| Distinct errored methods | 91 |
| Failed-import placeholders, separate from actual method IDs | 7 |
| Actual methods with no completed outcome | 221: 216 inside failed-import modules and 5 unreached at timeout |
| Unit-test process | Terminated at 900.024 seconds; no final unittest summary |
| Driver integrity guard | Failed because the original checkout changed during its isolated run |
| Complete regression or release | Not passed or certified |

Sixty passing methods print multiline docstring outcomes: four ordinary methods and 56 generated force-source cases. The initial single-line tally missed them; complete collection exposed them, and the corrected accounting retains both parser corrections. The original log is unchanged. The local driver's own zero summary count reflects the missing terminal unittest summary; the reconciled method observations do not overwrite it.

## Error causes and baseline comparison

One representative from each error group was rerun against the preserved candidate copy and an exact 94dee707c148b7a545e43d4de0d601642c5fa3e8 baseline copied using the same unchanged local-driver closure. Both revisions reproduce the same causes:

- The driver omits `fixtures/`. Required frozen static-tray data is absent: 72 input-lock, seven finalization, nine transaction and one source-test errors.
- Default Python bytecode creation conflicts with the frozen independent-reader cache prohibition. It produces seven module-import failures and the force/surface test-discovery errors.

The comparison changes no prior source, frozen reader guard, budget or expected outcome. Baseline reproduction does not establish a full baseline regression result or a runtime-performance comparison. The 900-second termination remains incompletely attributed.

The original checkout changed only STATUS.md (lease reconciliation) and 62 added evidence files. The isolated immutable verification inputs match the initial candidate under the existing driver's declared exclusions. That explains why the individual method observations are usable while the wrapper's source-stability result remains failed.

Detailed baseline commands, traces, source bindings and review are retained in `evidence/regression/force-error/`; complete accounting and inventories are in the handoff. A future maintenance task must repair the driver's fixture-copy closure and bytecode invocation before it can provide a clean full-suite result. That repair is outside this semantic milestone.

## Integration and historical limits

The exact affected methods, unchanged shared inputs and independent error diagnosis support only this experimental additive integration. Run the affected cohort and core/documentation checks on actual merged main, with bytecode writes disabled and the complete source checkout, and bind reusable artifact evidence to unchanged inputs. A new or worsened released-behavior failure still blocks integration.

The inherited full-regression FAILED result (4,239 distinct passing methods, thirteen torque-read methods unrun after the 30,000 ms setup timeout) is unchanged. C208's original three-second promotion timeout and separate successful observation remain separate, with original cause unproven. Frozen C201 files and closed C199/C200 schedules remain unchanged.
