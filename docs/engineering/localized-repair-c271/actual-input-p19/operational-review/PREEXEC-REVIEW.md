# P19 pre-execution review — candidate 001

Reviewer: `/root/operational_review`.

**Verdict: changes required before invocation.** This is static source/plan review only. The reviewer did not execute the observation script, import production code or inspect actual host inputs.

## Exact candidate

- Script: `technical/observe_inputs.py`, 12,122 bytes, SHA-256 `9ffe5b8137bb25b05fcc122049698aa8c6506415f044c7b023d1e8e33cb01212`; all 184 lines read.
- Plan: `technical/OBSERVATION-PLAN.json`, 2,050 bytes, SHA-256 `06c79df44367500b7c3825755a9d9299b2cd6a11cc456f8eb56f715169735d09`; all 43 lines read.
- Production source: accepted P18 module, 196,305 bytes, SHA-256 `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206`.
- Selected seven-pin lock: `tools/native-reader-verification-linux-cp312.lock`, SHA-256 `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f`.

The Director confirmed early recovery before this candidate review. Its separate receipt is `state/EARLY-RECOVERY-RECEIPT.json`, SHA-256 `43ff32a126271633199f24ba2fa5a22e49cace07cbe9d83682c8aeed678534b2`.

## Mandatory findings

### PX-01 — post-read failure must block a successful result

The `finally` block records unsuccessful identity/hash rechecks in `after`, but does not change `failure`, `status` or the exit code. Therefore an otherwise successful observation can report `raw_inputs_passed_complete_h0_review_still_required` and exit zero after observed input drift or an expired deadline. This contradicts the frozen first-mismatch/refusal stopping rule and input-preservation requirement.

Preserve any earlier first blocker. Retain postflight failures separately, and if there was no prior blocker, convert the first failed recheck into the blocking outcome. Success must require all post-read identity/hash checks. Do not retry the observation.

### PX-02 — authenticate the lock actually consumed

The outer invocation will check the lock digest before launch, but `observe()` later consumes whichever seven-row lock it reads. It records that digest without comparing it to the independently frozen value. A replacement between prelaunch checking and the actual read can therefore redefine the expected package versions, with subsequent rechecks covering only the replacement.

Compare the bounded-read lock bytes directly with the frozen expected lock SHA-256 before parsing or accepting any package pin. Preserve mismatch evidence and stop. This supplements the outer check; it does not change the lock or package expectations.

### PX-03 — enforce the package-directory bound during enumeration

`sorted(packages.iterdir())` materializes the entire directory before checking the 4,096-entry limit, and has no deadline callback during enumeration. The declared finite limit must bound the actual operation.

Iterate with `check()` and stop immediately when the observed count exceeds 4,096; sort only the bounded collected list afterward. Retain the same package-name selection and lockfile order. No alternate environment search is permitted.

## Accepted aspects of the proposed scope

The candidate correctly distinguishes raw private-reader observations from operational-plan admission and keeps H0/H1 false. Exact selected Python/loader/libc pins precede product import. The source bytes are verified before the module is compiled. A process/native/network audit guard is installed before product import. The frozen direct Python launcher uses `-I -S -B` and the exact five-variable environment. The script runs no target, package import, site initialization, installer, source Git read, H1 command or complete plan validation.

The selected-process map rows are limited witnesses, with inode/device checks and no complete process-closure claim. Reader order is Python, loader, libc. Product refusals retain their category, reason, state, details and cause. Later package checks read only METADATA text, use the unchanged production name normalization, follow the seven-pin lock order and stop at a missing/ambiguous/mismatched package. Raw failed METADATA is retained. The package result is explicitly weaker than a complete dist-info inventory or later ordinary provider lookup.

The output directory and files use exclusive creation. Root's outer wrapper must still authenticate the independently approved script/plan/source/lock identities and absent output before its single exact invocation, retain timeout/launch/result evidence and reconcile any unknown outcome before any later attempt. No acceptance is given to that wrapper's implementation because its source has not yet been supplied here.

## Required next step

Apply only the three observation-harness fixes, preserve candidate 001 and this review, freeze a new script/plan identity, and return them for static re-review. This decision authorizes no execution. Product source, frozen expectations, dependency pins and all parent gates remain unchanged.
