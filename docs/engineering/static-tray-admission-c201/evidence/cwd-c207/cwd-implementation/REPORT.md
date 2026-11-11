# C207 working-directory implementation

Candidate `bd9fbf1487e557b9c21baf1d39e7b9cb818d4773`, tree `701e7ea878434c6f6d06366eaa3f08754d4c55d7`, branch `work/c207-cwd-impl-cbf19c`, is clean.

The C201 input validator now binds every stage cwd to its output directory. Transaction receipts require planned cwd/output, underlying supervisor cwd and locked output equality. The obsolete C201-NATIVE-CWD purpose rejection is removed; validated-factory/purpose checks and all false authorization/readiness flags remain. C201 Node command planning is consistent, but the absent readback/probe implementation remains the next gate.

## Changed files

- `docs/engineering/static-tray-admission-c201/WORKING-DIRECTORIES-C207.md`
- `prototypes/static_tray_admission_c201/input_lock.py`
- `prototypes/static_tray_admission_c201/transaction.py`
- `tests/test_static_tray_admission_c201_input_lock.py`
- `tests/test_static_tray_admission_c201_transaction.py`
- `tests/test_static_tray_admission_c201_working_directories.py`

## Verification

All 135 focused methods passed: 72 existing input-lock methods, 47 transaction methods and 16 new working-directory methods. The production-shaped synthetic transaction path completes all four component transactions without granting native authority. Subprocess/fork/spawn/shell entry points are blocked. Exact source and test hashes, interpreter/platform, command and log hash are in RESULT.json. The tested code/test bytes are unchanged in the candidate; the documentation was added after the test run.

The original mismatch was reproduced before editing and is retained in original-cwd-reproduction.json. Original input/transaction source and tests are retained under original/. No failed implementation test occurred in this worker. No C201 native, receiver, Node, lifecycle or timed-author process was started.

## Boundaries

The four frozen protocol documents, qualified C199/C200 source/locks/receipts/budgets and closed schedules are unchanged. The full historical regression remains FAILED (4,239 distinct passing methods; thirteen torque-read methods not run after the original 30,000 ms setup timeout). No host approval, production input closure, process provenance or admission is established. Root owns independent review, broader applicable checks, actual publication, source preservation and final handoff.
