# C207: C201 stage working-directory compatibility

C207 corrects one launch-plan mismatch in the separate C201 input-binding and
transaction components. A child's working directory is the directory from which
its process resolves relative paths. Every C201 stage now binds that directory
to its own output directory. This agrees with the unchanged qualified supervisor,
construction worker and receiver.

This is a checked component contract, not native readiness. There is no production
C201 input lock or actual current-host approval. The code starts no child and
does not implement the coordinator or Node readback. The CPU controls use
synthetic process evidence, including the control that exercises structurally
valid `production-inputs` bindings. No C201 native construction, receiver, Node,
lifecycle or timed-author process is started by this increment.

## Contract

For every A01–A04 slot and each `construction`, `receiving` and `node` stage,
the following values must be the same normalized absolute path:

- `outputs[slot][stage]`;
- `commands[slot][stage].output`;
- `commands[slot][stage].cwd`.

The exact argument vector must name that directory's absolute `job.json` path.
The existing path checks still require separate empty stage directories, distinct
filesystem identities, and separation from inputs, stores and invocation
authority. The entire launch plan remains bound to an independently retained
review digest. Consistently moving all three values and the job argument does
not bypass that digest.

Construction and receiving jobs are written by the transaction component. Their
`output_directory` value is the same stage path. Their exact job bytes are checked
before construction sealing or transaction promotion. The declared command in a
process observation must exactly match the validated command. The underlying
supervisor receipt must bind that same argument vector, environment and working
directory. There is no longer a fixture bridge that tolerates different declared
and observed working directories.

Accepted evidence is moved from a stage into its sealed store. Its job and
process receipts retain the original launch directory. Read-only inspection
validates that original binding; it does not rewrite receipts to claim that the
process ran from the later storage location.

## Separate command-path decisions

| Stage | Qualified behavior and C207 decision | Remaining boundary |
| --- | --- | --- |
| Construction | `supervisor.run_process` launches with `cwd=stage`. `worker.main` requires actual cwd to equal `job.output_directory`. The worker, settings, source record and job arguments use absolute paths. The C201 lock now records this same stage directory. | Actual native process provenance, complete dependency/alias inventory, supervision and readiness still require the future coordinator and host review. |
| Receiving | The same supervisor supplies the receiving stage directory. `receiver.main` independently requires cwd to equal its job output directory. Candidate and settings paths are absolute. The C201 job, command and process-receipt bindings now agree. | Native scene reopening, GLB import and the assigned image must later be measured in the receiving process. CPU fixtures do not prove those operations occurred. |
| Node | The C201 plan uses its own Node output directory as cwd and an absolute job path, module loader and probe path. The safe Node flags and clean environment remain exact. This provides a consistent planned directory. | The separate C201 `format_check.py` and `readback.mjs` roles are not implemented. A valid planned cwd does not prove their future job or receipt compatibility. The historical twelve-slot implementation cannot silently substitute for the four-slot roles. |

The historical Node probe reads explicitly named job, manifest, artifact, audit
and result paths. Its Python wrapper also uses the qualified supervisor's stage
directory. That source inspection informs the planned directory choice; no
historical or synthetic Node process is executed here. The later C201 readback
increment must define and check its actual job/output contract and retained
result bindings before a production input closure can be complete.

## Changed component boundary

[`input_lock.py`](../../../prototypes/static_tray_admission_c201/input_lock.py)
now rejects a repository-root cwd, another slot or stage's cwd, noncanonical
cwd spelling, and mismatched command/output/job paths. The object fields and
input-lock schema remain unchanged. This corrects a component implementation
choice: the four approved protocol documents require exact reviewed commands,
environments and distinct outputs, but do not require repository-root cwd.
Those documents and their approved hashes remain unchanged.

[`transaction.py`](../../../prototypes/static_tray_admission_c201/transaction.py)
removes the obsolete blanket `C201-NATIVE-CWD` rejection of a validated
`production-inputs` purpose. It retains the validated-factory token and matching
context/validation purpose checks. An ordinary direct constructor call still
rejects with `C201-BINDING`; unsupported or inconsistent purpose values cannot
construct a session. Process checks explicitly require the supervisor cwd,
planned cwd, planned output and locked stage output to agree.

Removing that specific mismatch does not authenticate a caller's context or
receipt, discover missing dependencies, establish a production lock, or grant
execution approval. All `ValidationResult` and `AcceptedTransaction` execution,
readiness and admission flags remain false. `PreparedTransaction` also retains
false native-start authorization. Ledger reservations, process starts and full
schedule progression remain outside the transaction component.

The C205 and C206 documents and their original test results retain their
chronological meaning. This document supersedes their descriptions of the
current working-directory mismatch and the related blanket rejection only.
Accepted-source resolution, receipt inventories, original clocks, conditional
promotion and post-commit `UNKNOWN` behavior remain unchanged.

## CPU checks

The focused [directory controls](../../../tests/test_static_tray_admission_c201_working_directories.py)
exercise the actual validator and transaction component using temporary files.
They check all twelve planned commands; repository, other-stage and other-slot
cwd rejection even after a test-only plan repin; exact path spelling; mismatched
outputs and job arguments; changed stage-directory identity; altered retained
plan bytes; matching job/process/supervisor paths; and rejection before promotion
when a job, observed command or supervisor cwd changes.

The existing input-lock and transaction cohorts also run. The transaction cohort
retains four-slot accepted-source regeneration, exact retained closures,
unchanged accepted pointers on rejection, and uncertain pointer outcomes after
replacement. A synthetic production-shaped four-slot control now demonstrates
that the resolved purpose path can use the component while every execution and
readiness flag remains false. Its host-role files and receipts are still CPU
fixtures. Subprocess, fork, spawn and shell seams are blocked by the controls.

```sh
python3 -B -m unittest tests.test_static_tray_admission_c201_input_lock tests.test_static_tray_admission_c201_transaction tests.test_static_tray_admission_c201_working_directories -v
```

Source-bound logs and the independent decision are retained by the integrating
handoff. A passing directory control establishes only this compatibility
boundary. It is not a complete process/coordinator check or native admission.

## Stopping point

The next coherent implementation boundary is the separate C201 readback/probe
compatibility component. Complete process provenance and deadline supervision,
coordinator/ledger/control sequencing, durable trusted bootstrap, current-host
and dependency/alias sealing, independent native readiness, the sole
four/four/four invocation, image reviews and final admission remain pending.

C199/C200 source, locks, receipts, budgets and closed schedules remain unchanged.
The full inherited regression remains **FAILED**: 4,239 distinct passing methods
and thirteen torque-read methods not run after the unchanged 30,000 ms setup
timeout. This increment does not rerun that suite or establish general physics,
broader destination compatibility, measured authoring advantage or completion
of the full [GOAL](../../../GOAL.md).
