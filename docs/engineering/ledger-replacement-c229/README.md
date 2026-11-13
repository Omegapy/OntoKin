# C229: ledger replacement diagnosis blocked at launch

C229 prepared and independently reviewed a finite CPU diagnosis of the two
same-content authority-file replacement failures retained by
[C228](../aggregate-regression-c228/RESULTS.md). Its sole launch reached a
concrete path-resolution blocker before the diagnostic worker script opened.
**Zero test methods and zero replacement cases executed. R02 remains blocked.**

The caller supplied a relative plan path. The launcher retained a relative
worker-script path while changing the child working directory to the immutable
source checkout. Python could not find that script and exited with code 2. The
launcher reaped the process, observed no remaining process-group members,
verified unchanged source and stopped before the second planned worker. No
repair or retry occurred.

Read [RESULTS.md](RESULTS.md) for the actual outcome,
[PREPARATION.md](PREPARATION.md) for the reviewed but unexecuted diagnosis, and
[NEXT-TASK.md](NEXT-TASK.md) for the next separately selected scope. The
[raw run result](evidence/RUN-RESULT.json),
[worker error](evidence/original-method.stderr.log),
[author accounting](evidence/AUTHOR-OUTCOME.json) and
[artifact bindings](evidence/ARTIFACTS.json) retain the evidence.

The files in `harness/` are the frozen, consumed preparation. They are retained
for review and recovery, not as a current executable instruction. Their approval
does not establish that the diagnosis ran or explain C228's failure.
