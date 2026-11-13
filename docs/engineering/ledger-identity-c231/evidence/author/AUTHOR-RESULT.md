# C231 author result

## Outcome and exact source

The bounded ledger identity repair is implemented and checked on local author commit `e9f811dbd0d32d16aea55ce90ca3615a138a3416`, tree `e21381900f793a5fd30f9ef8fe2124d848e928c8`, branch `work/c231-ledger-author`. The worktree is clean. This is a local author checkpoint, not a claim of remote publication or integration. Root owns those operations.

The change retains the exact invocation-marker and journal file objects until the live capability stops, completes or is disposed. Both retained objects must remain regular files with one link and their original identity before persistence. Existing pathname, exact-content, append, nonblocking, no-follow, corruption and directory protections remain. Same-content replacement cannot acquire authority through numeric inode reuse while the original object is pinned.

Cleanup covers partial construction, initial/later append failures, negative observations, invalid mutations, completion, interruptions, explicit close, context exit and abandoned-object finalization. A fork coordination lock protects descriptor acquisition/registration and release against concurrent fork. Child capabilities are stopped and child pin copies closed without touching the parent; process identity is checked before the per-object mutex.

An interrupted pre-close lock acquisition retains pins and finalizer for a later first close attempt. An actual uncertain close is never retried. Cleanup clears completion and marks uncertainty; it preserves an already active body/mutation failure and otherwise propagates an interruption or reports PERSISTENCE. Automatic collection/shutdown finalization is explicitly best effort under asynchronous interruption; explicit close/context management is the normal lifecycle.

## Changed paths

- `prototypes/static_tray_admission_c201/ledger.py`
- `tests/test_static_tray_admission_c231_ledger_identity.py`
- `docs/engineering/ledger-identity-c231/CONTRACT.md`

The complete original ledger test file remains at SHA-256 `ea363ae96a8e8ed441da0992fca870047f81f4deabb528786bca9306d85c7b1f`. The original failing method and its ten subtests were not edited. No historical digest, consumed schedule, protocol, fixture, product budget, shared runtime, workflow or dependency lock changed. Independent contract review separately verifies the 42 frozen bindings.

## Checks and evidence

All **307** discovered affected methods executed and passed: 284 original C201 methods plus 23 additive C231 methods. There were zero method failures, errors, skips, expected failures, unexpected successes or unrun methods, and no setup/import failures. The complete run took 46.792631 seconds on Linux x86-64 / CPython 3.12.14. Full tracked-file hashes, commit, tree and clean status were equal before and after.

The new controls deterministically force the recreated file's numeric identity to match the original while preserving real link-state observations. They check the initial rejection and subsequent STOPPED state separately. Lifecycle controls cover each creation-sync boundary, partial writes, lost replies, terminal state paths, both context-body and cleanup errors, interrupted lock acquisition and descriptor disposal. One bounded actual CPU fork simultaneously observes a parent mutex held by another thread and a second capability paused between descriptor creation and registration. It exited 0, was reaped and did not reach its timeout; the parent capability remained usable. No native product was started.

`affected-run-03/RESULT.json` contains all method outcomes; `inventory.json`, `unittest.log`, source-before/source-after manifests and the separate stderr CPU-process receipt accompany it. `run_affected.py` is the exact reusable external runner. Root can run it against resulting main with a fresh output directory. `final-documentation.stdout.log` and `.stderr.log` record documentation preservation/link checking, exit 0.

## Earlier findings retained

Initial source checkpoint `4d3466e` was untested and independently identified two lifecycle gaps: fork between descriptor open/registration or pop/close, and interrupted cleanup reporting completion. Checkpoints `2a343b4` and `71e5e17` corrected those with finite fork/lifecycle controls; its 21 additive methods passed.

The first external affected-cohort runner then failed before any product method because it set an importable repository top level for a tests directory without `__init__.py`. `run_affected-initial.py.txt`, the original stderr and `affected-run-01/PREEXECUTION-FAILURE.json` preserve that failure. Standard unittest discovery semantics corrected the external runner only.

Independent review next measured context-body errors being masked by secondary cleanup failure. `8e7e4fc` corrected that path, and all 306 then-selected methods passed. Root's separate cleanup-lock concern was subsequently reproduced: consuming a one-shot finalizer before an interrupted lock acquisition could lose cleanup ownership and mask an existing error. Final `e9f811d` corrects that defect and adds the 307th method. Previous successful cohorts remain attributed to their own source and do not override these later observed failures. Independent probe artifacts remain under the root review directory.

## Remaining work

Independent final review, root integration, actual-main checks and the verified saved handoff remain root responsibilities. The full default aggregate is a separate next step; R02 remains blocked until it actually passes. Other interpreter/platform roles, historical failures, native receiving limits, held drafts and deferred target work retain their meanings. No additional feature or optional test expansion is selected.
