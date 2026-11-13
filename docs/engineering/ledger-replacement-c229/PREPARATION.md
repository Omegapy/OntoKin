# C229 retained diagnosis preparation

This document describes the preparation approved before C229's failed launch.
The [actual outcome](RESULTS.md) is zero executed test methods and zero observed
replacement cases. The earlier plan is consumed and must not be resumed.

## Source and contract

The planned diagnosis used immutable published main
`d578a30dab9a112895d2e3c09561a17866d9c464`. Its package initializer, ledger,
schedule, test file and frozen admission protocol exactly match C228's executed
`fc500331ce789eb6f9c1210ea4f3b394d45e507c` for those five files. The
[source bindings](evidence/STATIC-SOURCE-BINDINGS.json) record this comparison
and nine exact implementation/test/contract hashes.

The original method in
[`test_static_tray_admission_c201_ledger.py`](../../../tests/test_static_tray_admission_c201_ledger.py)
contains ten subtests: two authority files and five mutations each. Its
same-content replacement branch reads the original bytes, unlinks the selected
file and writes those bytes at the same path. The next reservation must raise
`LedgerError`. Only then does the method assert that the capability is stopped
and cannot reserve again. The expectation remains unchanged.

In [`ledger.py`](../../../prototypes/static_tray_admission_c201/ledger.py),
`_identity` returns `(st_dev, st_ino)`. Creation and later read descriptors close
after use. `_append` compares exact file bytes and those stored identity
numbers. It also checks file type, link count and byte ceilings. A rejected
append wraps its underlying integrity error as `PERSISTENCE` and marks the live
capability stopped and uncertain. The
[existing component contract](../static-tray-admission-c201/LEDGER-C204.md)
requires missing or replaced authority files to stop progression.

These facts motivate an inode-reuse hypothesis; they do not observe an
allocation event. C228 did not preserve the inode sequence needed to determine
whether reuse happened in its failed subtests.

## Planned finite observations

| Slot | Planned work | Maximum starts | Actual executions |
| --- | --- | --- | --- |
| 1 | Original unchanged test method once, containing ten subtests | 1 Python worker | 0 method executions; Python failed before opening its worker script |
| 2 | Marker/journal replacement with no retained descriptor, then explicit held-descriptor controls for both files | 1 Python worker | 0; worker never started |

Each worker had a 60-second host ceiling. The planned maxima were 14 synthetic
ledger creations and 28 reservation calls. Product limits, original
replacement semantics and rejection/poisoning expectations were unchanged.
Four bounded Git metadata commands checked source identity and cleanliness.
No aggregate, native application or historical executable admission was part
of the scope.

The observation design included exact original/recreated/post-reservation
bytes; path existence, device/inode, mode, link count and nanosecond timestamps;
open-descriptor inventories; complete error cause chains; and stopped/uncertain
snapshots. A poison check was permitted only after an initial rejection.
A pre-opened synchronized evidence file was intended to preserve exact
originals before unlink without allocating another evidence-file inode in the
unlink/recreation gap. Supplementary binary copies would follow the four cases.
None of those case observations was produced.

Fresh temporary directories were bound beneath the current session workspace.
Each worker would record its actual filesystem device and Linux mount
information. The old C228 temporary path is retained in the plan as context,
without claiming that the same allocator or timing sequence could be recreated.
Extra stats, reads and synchronization could affect timing. Holding an original
file descriptor is an explicit intervention that changes the old object's
lifetime; that control is distinct from the original no-held-descriptor case.

## Approval and uncovered limitation

The [independent approval](evidence/PLAN-APPROVAL.json) binds plan SHA-256
`4aeb4ad04f9abfbb1266910c9cfda13b921920a2f7faba1f2058a4c9bbb4a31c` and both
harness files. The detailed [plan review](evidence/PLAN-REVIEW.md),
[preparation feedback](evidence/PREPARATION-FEEDBACK.md),
[static review](evidence/STATIC-REVIEW.md) and
[historical source comparison](evidence/HISTORICAL-SOURCE-EQUIVALENCE.json)
remain alongside it. [Static pre-execution checks](evidence/PREEXECUTION-CHECKS.json)
verified the source and syntax. The approved preparation was preserved before
the root launch, as recorded in the separate recovery evidence.

Earlier static feedback corrected a platform-report call that could spawn
`uname`, required reconciliation of top-level unittest failures, and added
cleanup gates. Those corrections did not catch the remaining relative-path
interaction with the child working directory. The finite stop condition did
operate after that failure: no second worker or retry started, the attempted
process was reaped, and source identity remained unchanged.

Approval of preparation is separate from observed execution and product
acceptance. The [next scope](NEXT-TASK.md) must correct and verify the launch
path and review a new finite plan before any diagnostic case runs.
