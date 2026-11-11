# C208 actual-main timeout disposition

## Decision

**Retain the component-only approval and close this bounded step with an explicit timing limitation.** A deterministic fixture change is not warranted by the current evidence. No source, assertion, production allowance or test expectation should be changed to remove this recorded timeout.

## What actually happened

At actual main `f8e397405b432d7a63464b136431d15a009c38df`, the first C201 component run executed 223 methods: **222 passed and one errored**. That run remains **FAILED**.

The failing method was `ReadbackBindingControls.test_actual_four_slot_bindings_and_measurements_without_authority`. Its stack stopped in unchanged C206 `transaction._promote`, at the deadline check immediately after flushing the temporary accepted-pointer file and before `os.replace`. The original promotion allowance is 3,000 ms. This occurred while synthesizing an accepted transaction for a later slot, before that slot's call to the new readback preparation API. The trace does not identify which slot or measure how each operation consumed the deadline.

The same complete method then **passed alone in 6.416 seconds**, on the exact same main revision and test-file bytes, with no changed limit or expectation and no child-start attempt. Other root validation and archive jobs were stopped for that diagnosis. Concurrent work was reported during the first run, but the evidence does **not** prove CPU contention, disk contention or any particular cause.

## Why this is sufficient for the selected boundary

All **66 independently reviewed component/dependency/test/contract hashes** still match actual main. The original candidate C201 cohort passed all 223 methods, and the independent component review passed 63 adversarial controls. The other 222 methods also passed in the actual-main run. The one isolated rerun exercised the entire affected four-slot method with its real unchanged timing checks; it was not an assertion-only substitute or a run with a larger allowance.

Together, the two actual-main observations establish successful execution of every required method for this bounded consistency component. They do not establish a single clean 223-method actual-main run or reliable promotion timing under every workload. The failure remains a known CPU-fixture timing limitation. The approval still grants no native execution, authenticated process provenance, readiness, admission, complete regression or production performance claim.

Changing the fixture now would alter reviewed test inputs and require new review to distinguish deterministic fixture setup from changes that hide the production deadline. The isolated unchanged-input result resolves the immediate functional question without that change. A recurring inability to pass the unchanged method in isolation would require separate concrete diagnosis; that condition was not observed here.

## Required reporting and closure

Report the first actual-main run as **222 passes / 1 promotion timeout**, and the separate same-source affected-method run as **1 pass**. It is accurate to say all 223 methods have successful actual-main observations across those two runs. Do not label the original run passed or claim 223/223 in one actual-main run.

Freeze logs only after their producing processes have finished. The archive builder's refusal to snapshot an actively changing log correctly prevented an inconsistent recovery snapshot; it is separate from the product test result. Preserve that first packaging outcome and rebuild only from frozen inputs.

No code or test was modified or executed by this assessment. Root should finish the handoff verification, save C208, and stop. The next product task remains the separately reviewed named-package resolution and versioned executable job contract.

## Evidence

`ASSESSMENT.json` binds the original and isolated results/logs, the earlier candidate result, the independent approval and all 66 actual-main input comparisons. Original evidence is at:

- `/workspace/scratch/4c105edcd17c/validation/main-components/RESULT.json` and `tests.log`.
- `/workspace/scratch/4c105edcd17c/validation/main-affected-method/RESULT.json` and `tests.log`.
- `/workspace/scratch/4c105edcd17c/validation/candidate-components/RESULT.json`.
- `/workspace/scratch/4c105edcd17c/workers/independent-review/REVIEW.json`.
