# C229 outcome: worker script did not start

## Actual result

The one-use launcher attempted its first diagnostic Python process. That process
exited with code **2** because Python could not open the worker script. No test
method, replacement case, `Ledger.begin` call or reservation ran. The second
planned worker never started. The run is blocked and its schedule is consumed;
there was no retry. The [raw receipt](evidence/RUN-RESULT.json) reports
`completed=false` and `source_unchanged=true`.

| Item | Observed result |
| --- | --- |
| Immutable source | `d578a30dab9a112895d2e3c09561a17866d9c464` |
| Source tree | `080b9d00bc340dfd9728601147d11816fab4375d` |
| Environment | Linux x86-64 / CPython 3.12.14, checked by the launcher before its worker attempt |
| Approved plan SHA-256 | `4aeb4ad04f9abfbb1266910c9cfda13b921920a2f7faba1f2058a4c9bbb4a31c` |
| Worker processes attempted / started | 1 / 1 |
| Worker script executions | 0 |
| Original test methods / subtests executed | 0 / 0 |
| Observed replacement cases | 0 |
| Ledger creation / reservation calls | 0 / 0 |
| Second worker | Not started |
| Native starts / aggregate attempts / retries | 0 / 0 / 0 |
| Timeout | Not reached |
| Worker cleanup | Reaped; no remaining process-group members observed |
| Source checks | Same commit, tree, clean status and nine bound file hashes before and after |
| Launcher elapsed time | 0.07998351000060211 seconds |

The elapsed time is launcher overhead through the failure and cleanup. It is not
a ledger test or diagnostic performance measurement. The worker could not
produce its planned environment or filesystem observations.

## Why the launch failed

The [exact root invocation](evidence/ROOT-INVOCATION.json) ran the launcher
from the current session workspace using the relative argument `--plan diagnosis-author/prepared/RUN-PLAN.json`. The launcher
used `args.plan.parent` directly to construct
`diagnosis-author/prepared/diagnose_replacement.py`, then passed that still
relative script argument to a child with `cwd` set to the immutable source
checkout. Python consequently looked beneath that checkout for a harness
located in the session workspace. The [worker stderr](evidence/original-method.stderr.log)
records the missing file, and the [run receipt](evidence/RUN-RESULT.json)
retains the actual command and process result.

This combines a caller invocation using a relative plan path with a launcher
that failed to resolve its script path before changing working directory. The
pre-execution review checked the frozen files, source bindings and finite
execution plan but did not catch this invocation/path interaction. C229 leaves
that failed preparation unchanged for review. It does not correct the path or
relaunch with an absolute argument.

After the worker exited, the launcher found no complete worker result, raised
`Missing complete worker result; no further start`, and stopped. The
[launcher output](evidence/diagnosis-launcher.log) and
[author accounting](evidence/AUTHOR-OUTCOME.json) preserve that boundary.

[Independent outcome review](evidence/OUTCOME-REVIEW.md) reconciles fifteen
checks across the launcher command, raw error, exit/cleanup receipts, unchanged
source and zero-execution accounting. It records the caller invocation, launcher
path weakness and the preparation review's failure to catch that interaction.
The reviewer ran no replacement diagnostic or test replay.

## What remains unknown

C229 produced no inode, descriptor-lifetime, replacement, reservation or
poisoning observations. Static inspection found that the ledger stores file
identity as device/inode numbers and closes its creation descriptors. Reusing
those numbers after unlink/recreation could satisfy its identity comparison,
but this run did not test that hypothesis. There is no supported new causal
conclusion about C228's two failures.

The original test checks poisoning only after its first `assertRaises` succeeds.
C228's two failed assertions therefore establish missing rejection, not the
subsequent poisoning state. An unrelated stage-order rejection on a second
reservation must not be presented as replacement poisoning.

[C228's complete aggregate](../aggregate-regression-c228/RESULTS.md) remains
**4,661 passing methods and one failed method containing two replacement
subtest failures**. All earlier failed aggregates remain historical evidence.
R02 remains blocked. Sixteen external conformance cases, other interpreter and
optional validation roles, R07 preparation and broader release acceptance
retain their existing status.

## Source and execution boundary

C229 changes only diagnostic preparation, documentation and retained evidence.
The ledger, test expectations, protocol, fixtures and product limits remain
unchanged. The nine recommendation records and 41 acceptance criteria remain,
as do all held native drafts and consumed schedules. Synthetic ledger fixtures
would grant no native execution authority even if the diagnosis had run.

The exact [frozen plan](harness/RUN-PLAN.json),
[launcher](harness/launch_diagnosis.py),
[worker](harness/diagnose_replacement.py) and
[independent plan approval](evidence/PLAN-APPROVAL.json) remain inspectable. Their
presence and approval do not establish execution. The next action is the
separately reviewed [launcher-path repair and fresh finite diagnosis](NEXT-TASK.md).
