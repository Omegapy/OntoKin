# Draft control correction

The first independent run executed 29 methods: 28 passed, and one reviewer-written control failed. No implementation defect was shown.

`test_failed_precommit_preserves_absent_pointer` incorrectly expected `C201-PROMOTION` for an `OSError` before a pointer was committed. The existing component deliberately preserves the absent pointer and reports a rejected `C201-BINDING`; `C201-PROMOTION` with state `UNKNOWN` is reserved for an observed or uncertain replacement. Inspection of `_promote`, `_boundary` and the original C206 control confirmed the expectation error.

The reviewer also narrowed fault injection to the actual `state.json` replacement instead of all `os.replace` calls. This avoids intercepting preceding object sealing and verifies that the intended pointer operation was reached exactly once. The corrected control additionally checks that the transaction cannot be retried.

Original results, log, exact input bindings and the original control script remain in `draft/`. No product file was edited to repair the review harness. All 28 other independent methods passed on the observed implementation draft, including twelve stage plans, wrong-directory rejection, actual supervised launch-argument interception, worker/receiver prefixes and accepted-source behavior. Final approval requires a committed candidate and a new exact binding.
