# P19 pre-execution review — candidate 003

Reviewer: `/root/operational_review`.

**Accepted for one bounded raw actual-input observation under the frozen plan.** All three mandatory candidate001 findings are resolved. This acceptance covers the planned observation only. It does not accept a complete operational plan, policy dispatch, H0, H1 or parent completion.

## Exact accepted files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `technical/observe_inputs.py` | 12,873 | `c14b171df87d47dbd78d6a73946c72c32add8891d6d52b0a7e1da697cdd1e287` |
| `technical/OBSERVATION-PLAN.json` | 2,707 | `946fd14dc1022ddb1e9cc4d8f22a0c0a2746efb3b0b9c08db62cd70c17945aab` |
| Accepted production inspection source | 196,305 | `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206` |
| Seven-pin lock | 779 | `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f` |

The reviewer fully read candidate001, independently read every candidate002/003 source delta and the full updated plans, and rechecked the actual accepted production-source/lock bytes. The exact output pathname `technical/attempt001` was absent, with no symlink, at review. No observation or product execution occurred in this review.

## Finding disposition

- **PX-01 resolved:** final identity/hash/deadline failures remain in `postflight_failures`. They block previously successful observations and the exit code while preserving an earlier first blocker.
- **PX-02 resolved:** the actual bounded-read lock digest is compared with the independent frozen SHA-256 before any pin is parsed.
- **PX-03 resolved:** a context-managed `os.scandir` stream enforces deadline and 4,096-entry checks while collecting names. Sorting happens only on the bounded list. Candidate002's remaining `Path.iterdir` issue is retained in `PREEXEC-REVIEW-002.json`.

The reviewed script retains pin-first input checks, source verification before product import, the process/native/network audit guard, strict raw-reader order, actual mapped-role witnesses, METADATA-only package inspection in unchanged lockfile order, exclusive output paths and stop-at-first-blocker behavior. It neither imports `site`/packages nor launches targets, helpers, Git, installation or H1 commands.

The updated plan correctly discloses uncommitted documentary work. The inspected production module and lock are exact bytes from revision `2f791017c6559bfd47937b32b1862cfe98a81551`; this observation does not claim clean whole-tree H0 admission.

## Invocation and outcome limits

The Director must recheck the exact accepted script/plan/source/lock digests and absent output immediately before the one invocation, using the frozen absolute interpreter, argv, five-variable environment and cwd, without a shell. The outer capture must retain command, start/exit/timeout, stdout/stderr and any uncertainty; its implementation is Director-owned and was not supplied for this static review.

An actual metadata refusal or missing/mismatched package is the first blocker and ends technical work. The script may perform final identity rechecks and evidence finalization after a blocker; those are preservation work, not permission to examine later input prerequisites. No automatic retry, package installation, alternate environment search, input substitution or source change is approved.

Raw metadata success establishes only the named primitive's result on the exact observed bytes. Package METADATA agreement establishes only name/version readiness in the selected standard site-packages location. Full dist-info inventories, ordinary-provider lookup compatibility, complete closure, origin nonselection and operational plan review remain unmet. N57 remains external and untested.

Candidate001, candidate002, the reviewer copy-race record and every correction remain preserved. The reviewer is ready to inspect the retained single-run outcome independently.
