# C230 launcher qualification and finite diagnosis preparation

C229 did not open its diagnostic worker because a relative worker path was
interpreted after the child changed working directory. The new launcher
resolves the plan and approval at the caller, resolves the two reviewed script
paths, verifies that the invoked launcher is the reviewed launcher, and passes
absolute interpreter, worker, source, output and temporary-directory paths to
each child. Relative paths inside a plan have one stated base: the resolved
plan directory.

The exact two-script hash inventory, Python/platform guards, clean source
commit/tree and input-hash checks remain. The launcher checks the declared
two-worker maximum, one start per slot and a maximum 60-second ceiling per
worker. Its new output must be outside the source checkout. An existing output
is refused. Once the fresh directory is claimed, errors consume the attempt;
missing or malformed results, forbidden child-attempt reports, unexpected
method outcomes and failed process cleanup stop before the second worker.

## Evidence from harmless qualification

[QUALIFICATION.json](QUALIFICATION.json) records 24 passing controls from the
actual launcher with harmless subprocesses and a tiny Git fixture. The old
launcher reproduces its relative-path failure in the same inert setup: its
first child exits 2 before opening the stand-in. The new launcher completes
relative and absolute caller-path controls, including an unrelated caller
directory, a different worker directory and relative source/output plan
values. The controls also check missing/mismatched files and approval,
launcher-path identity, source identity/hashes, output reuse, finite limits,
missing/malformed results, reported forbidden child attempts, unexpected
outcomes and timeout kill/reap. These are launcher controls, not product
methods or real replacement cases.

Detailed control invocations, stdout/stderr, source fixture, stand-in bytes
and results are retained in the C230 handoff's author qualification evidence.
The control runner is [qualify_launcher.py](prepared/qualify_launcher.py).

## Exact worker reuse and execution boundary

[diagnose_replacement.py](prepared/diagnose_replacement.py) is copied
byte-for-byte from the reviewed C229 observation worker. Its C229 schema names
and diagnostic messages remain intentionally unchanged. The separately
versioned [C230 plan](prepared/RUN-PLAN.json) and
[launcher](prepared/launch_diagnosis.py) identify the new execution. Reuse does
not reopen C229's consumed schedule.

The new plan identifies immutable source
`e19acb44784ba5654f24bd3d87fb7310249f6d05`, its tree, nine unchanged source and
contract hashes, the two retained C228 failure records, the actual CPython
3.12.14 executable, one absolute outer invocation and a new output directory.
Exactly two workers are permitted: one unchanged original test method with
ten subtests, then four fixed replacement observations. Held-descriptor
controls are explicit interventions. A second reservation is observed only
after the first actually rejected; an order error following success would not
prove replacement poisoning.

Root must verify the source restore, independent exact-byte approval and
confirmed durable preexecution save before launch. Author qualification has
executed no product methods, real replacement cases, ledger calls, native
starts or aggregates. Actual diagnosis, outcome interpretation, publication
and final delivery remain root-owned. No ledger repair or full regression
retry belongs to this scope. C228's failures and R02's blocked status remain.
