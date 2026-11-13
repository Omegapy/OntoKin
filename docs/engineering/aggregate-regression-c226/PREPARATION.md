# C226: one immutable R02 aggregate attempt

This checkpoint continues the aggregate regression task after [C225's exact prerequisite recovery](../readback-prerequisites-c225/README.md). R02 asks whether the complete selected test inventory can finish on one identified, unchanged source revision. A focused passing subset cannot establish that result.

## Frozen source and environment

The selected source is published main `3f17a523b5d5c435f71525a499d2f071ca6e4e96`, tree `324d7a23d67d0c23f5dfba968a63a5c12cb7bcff`. It has a separate clean execution checkout. Pre-run discovery recorded all 4,662 methods, with no duplicate identities, declared skips, expected failures or failed-import placeholders. The complete source inventory contains 15,690 files; every one of the 371 discovered test source files is hashed.

Execution uses Linux x86-64 and CPython 3.12.14 in a separate verification environment. All seven packages were installed with the unchanged hashed [native-reader lock](../../../tools/native-reader-verification-linux-cp312.lock). The Pillow decoder preflight passed. C225's unchanged helper first checked, then restored, the exact 24 retained readback dependency files and historical HOST record. All ten required current runtime bindings and their aliases matched. The historical HOST remains historical evidence.

The input C225 ZIP has SHA-256 `82ca063c10a8f1a2045a28f347c34dc3f30e6c208c2a6007f80f34be3cc689e9`. Its finalized directory and documented offline restore passed. Exact main/tree, clean source, retained published and unpublished histories, and all 303 original historical evidence files were verified without a network dependency. The current six remote branch heads and four held draft PRs were reconciled separately. [Scope #184](https://github.com/Omegapy/OntoKin/issues/184) identifies current ownership.

## Declared execution

The exact interpreter, absolute paths, environment, source hashes and argv are recorded in the raw prelaunch plan. The selected command is:

```bash
PYTHONDONTWRITEBYTECODE=1 <prepared-python> -B tools/check_local.py --timeout 3600 --output-dir <fresh-external-output>
```

The 3,600-second limit applies to each validation command. C224 reached its earlier 900-second limit with 3,451 passing methods, one interrupted method and 1,210 unrun methods. The longer ceiling is declared before execution and is consistent with the example in [OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md). Original product execution budgets, fixtures, numerical tolerances and test expectations remain unchanged.

Only the seven default steps are selected: unit tests, source conformance, Agent conformance, construction conformance, surface conformance, impulse conformance and documentation checks. The unchanged driver continues its default plan after an ordinary failing step. No optional visual or dedicated force-agent role is added. The prepared interpreter's directory prefixes PATH, a private temporary directory is declared, and the existing `STATIC_TRAY_READBACK_CPU_OUTPUT` option retains readback artifacts externally. No separate focused readback test is rerun during preparation.

An external launcher reserves this one attempt before starting the process and records its PID, command and outcome. A preexisting reservation or evidence directory prevents replay. The execution source remains unchanged throughout the run. A failure or timeout is retained for the next bounded diagnosis; it does not authorize a retry or repair in this checkpoint.

## Review and recovery

Independent prelaunch review passed 19 checks, including actual interpreter/packages, full input inventories, restored dependencies, exact source, command and launcher bindings, bytecode policy and fresh output paths. The documented restore and reviewed recovery-save conditions were separately verified before launch.

The [C226 recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-418b5d9dd9408191abc0f5cd33b4c69d_2ab2a24d43748191957f9bcc356b59de&account_id=personal) preserves the source-handoff identity, raw preparation evidence, independent reviews, frozen method inventory, process receipt and subsequent progress. Complete new evidence will also be included in the final self-contained handoff. The raw preparation lives under `evidence/run-preparation/`; independent reports live under `evidence/preflight-review/`, `evidence/input-audit/` and `evidence/state-outcome-review/`.

This preparation record does not claim a completed aggregate, another interpreter, a native receiving result or release acceptance. C224's timeout, the original Blender normal failure, Godot capability limits and all nine recommendation records / 41 criteria remain preserved.
