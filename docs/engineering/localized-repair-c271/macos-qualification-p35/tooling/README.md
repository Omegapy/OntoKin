# Gate MH observational tooling

Phase C271-P35, gate MH of `ontokin.current-host-readback/0.2.0` at design revision 4, stage S3 of
`../MH-PLAN.md`, section 4. Author: W2, the independent author, who wrote none of the code under test.
This is revision 2, after tooling review 001 (`REJECT_WITH_MANDATORY_FINDINGS`); `../AUTHOR-NOTES.md`
maps each finding TR-01 to TR-18 to its change and its test.

The tooling observes. It changes no test, no implementation file, no contract, no amendment and no
frozen control of MI. It is not a general execution-plan runner, and it does not redesign the test
result protocol. Every plan that uses a tool binds it by path, SHA-256, size and mode.

## Shared rules

- **Placement.** This directory lies outside the source inventory's trees and outside the unit
  stage's start directory `tests/`. So it changes neither the default inventory (MC28) nor the
  provider's source set. Its `tests/` directory is not discovered by the unit stage.
- **Its own place inside the root (TR-01).** A tool that refuses preloaded modules of `--root`
  admits exactly one: its own `__main__`, identified by realpath equality with its own file. It
  records the admission as `own_main_admitted` and refuses every other preloaded root module. So
  each tool runs from `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/` with
  `--root <worktree>`.
- **Standard library only.** No tool imports another tool. Only `control_harness.py` imports
  project modules, and it says which.
- **No machine path.** Every path is an argument. The constants are the contract's own values (the
  declared environment, the schemas) and two system paths: `/usr/lib/libSystem.B.dylib`, for
  `proc_pidpath`, `proc_pidinfo`, `proc_listpgrppids` and `sysctlbyname`, and the `/usr/bin:/bin` of
  the declared `PATH`.
- **Outputs.** A tool writes only to the absent output path or directory given to it. It refuses an
  existing one and never replaces anything. Every file is created exclusively (`O_EXCL`) and fsynced
  with its directory. Every path argument must be canonical; on macOS that means `/private/var/...`,
  not `/var/...`.
- **Self-identification.** Every output records:
  - the tool's path, SHA-256, size and mode;
  - `sys.argv` and `sys.orig_argv`, the cwd and the PID;
  - the Python version, build string, executable and `sys.flags`;
  - the start and finish times (UTC) and the elapsed time;
  - the digests of the project files it loaded (`loaded_project_files`).
- **Refusals and failures.** A refusal is written to the output when the output path is valid, and
  as one JSON line on stderr. An unexpected failure is reported as `UNKNOWN`, never as a result.
- **Environments (TR-06).** `discover` and `mc29` require an exact frozen environment, given as
  `{"schema": "ontokin.c271.p35-unit-environment/1", "environment": {...}}` with its digest
  supplied outside it, as the collector does. `HOME` is never part of one. Records hold the frozen
  environment's binding and its variable names, never its values; the one value recorded is the
  `__CF_USER_TEXT_ENCODING` that macOS adds, as `admitted_cf_user_text_encoding` (D-16). A refusal
  lists names only.
- **Process creation.** No tool imports `subprocess`. Every tool that runs project code installs
  one audit hook that records each process-creation event (`subprocess.Popen`, `os.posix_spawn`,
  `os.exec`, `os.fork`, `os.forkpty`, `os.spawn`, `os.system`) and each ctypes lookup of libc's
  fork, exec, posix_spawn, system and popen functions. Where a tool must start nothing, the hook
  also refuses the event. A child's environment is recorded by its names and a SHA-256 of the
  mapping. The hook substitutes no object.
- **The audit hook's blind spots (TR-08).** `_posixsubprocess.fork_exec`, which multiprocessing's
  spawn and forkserver start methods call, raises no audit event; neither does a call made through
  ctypes, nor a lookup made before the hook was installed. A start made that way is not counted. So
  a start count is exact only for the routes the hook sees; MC11's scan is the static evidence that
  the probe and the readers use no such route (FAILURE-CAPTURE FC-P7).
- **`-B`, rule N-09 (MH-PLAN section 10).** On the owner's host, `python3` on `PATH` is the same
  framework interpreter that HOST binds. Every start of that interpreter carries `-B`, whatever
  name starts it: the tools, these tests, the failure-capture probe, and the Director's own checks.
  The alternative is `PYTHONDONTWRITEBYTECODE=1`, set and recorded. M0, the cohort and every
  control run here put `-B` on the command line, because their environments admit no Python
  variable or freeze one exactly. **Every entry point of every tool refuses a start without `-B`
  (`sys.flags.dont_write_bytecode` must be 1; TR-17)**, with rule `PYTHON`.
- **Exit codes.** 0 is the tool's success predicate. 1 means that the run completed and something
  differs. 2 means a refusal before any work. 3 means an unknown outcome. Each section below says
  what 0 and 1 mean for that tool.

## FAILURE-CAPTURE.md and capture_probe.py

`FAILURE-CAPTURE.md` is the failure-capture procedure, version 2. It says what is kept on a refusal,
a failure or an unknown outcome, and how the absence of a process or a process group is
established: by `ESRCH` from `kill` and `killpg` on the recorded PIDs and groups, never by a list of
names. Before any signal, the identity of a present process must be established (TR-05); otherwise
nothing is sent and its outcome stays unknown. It allows no retry. The observation plan's
`failure_capture.procedure` binds it.

`capture_probe.py` is the procedure's own tool, fixed as code (TR-16):

```
capture_probe.py probe   --pair BEFORE AFTER [--pair ...] --output OUT     (FC-P3)
capture_probe.py stop    --pair BEFORE AFTER --output OUT                  (FC-P6)
capture_probe.py listing [--dir D ...] [--path P ...] --output OUT          (FC-K5)
```

- **Pairs.** `AFTER` is a started record that holds the supervisor's record under `/process`: the
  runner's `started-<n>.json`, or the observer's or the provider's `started.json`. `BEFORE` is the
  record written before that start: the runner's or the observer's `intent.json`, or the provider's
  `preflight.json`.
- **`probe`** records the errno names of `kill(P, 0)` and `killpg(G, 0)`. For a present PID it reads
  the kernel's facts: `proc_pidinfo` with `PROC_PIDTBSDINFO` (start time, group, parent, user,
  command name), `proc_pidpath` (the image) and the group's members (`proc_listpgrppids`). Identity
  is established only when the kernel start time lies between the modification times of `BEFORE`
  and `AFTER` (in microseconds), the image equals the recorded `argv[0]`, and the group equals the
  recorded group, which equals the PID. A launcher that executes another program never
  establishes it. Each target's state is `absent`, `present, identity established`, `present,
  identity not established` or `unknown`.
- **`stop`** sends SIGTERM to the recorded group only with an established identity, probes every
  50 ms, and sends SIGKILL only after 2,000 ms of continuous presence and a second established
  identity. Every send and probe is recorded.
- **`listing`** lists each attempt directory and each planned output, links never followed, with
  the SHA-256 of every regular file and the target of every link; this process computes every
  digest of the readback record.
- **Launch:** `<worktree>/.venv/bin/python -I -S -B`. Every command reads `kern.bootsessionuuid`
  before and after, refuses every process creation, imports nothing of the project, and writes one
  absent output file. **Exit:** 0 when the command completed (its record holds the states); 2 for a
  refusal; 3 for an unknown failure. **Starts:** none. **Signals:** only `stop`'s, as above.
- **Limit (FC-P5):** a descendant that moved to another process group or session is not found by
  the group probe. Every probe record states this.

## discover_inventory.py: runtime discovery (MC28)

**Purpose.** It lists the default unittest inventory as the unit stage of `tools/check_local.py`
discovers it, without running a test. Then it compares the list with the baseline plus the
approved additions.

**`discover --root ROOT --environment ENV --environment-sha256 H --output OUT`**
- It reads the unit stage's argv from `ROOT/tools/check_local.py` by parsing the file, never by
  importing it. The argv must be `-m unittest discover -s tests -v`; any other form refuses
  (`UNIT-STAGE`).
- **The interpreter flag is derived (TR-07)** from `build_plan`'s `add()`, by its AST: the
  statement `if argv[0] == python: argv = [python, FLAGS..., *argv[1:]]`. The flags must be
  exactly `-B`. The record states `derived_from: build_plan.add, by its AST`.
- **The environment** must be exactly the frozen one (TR-06).
- The discovery runs in this process, as `python -B -m unittest discover -s tests -v` runs from
  `ROOT`:
  - `ROOT` is the working directory and `sys.path[0]`, and the tool's own directory leaves
    `sys.path`;
  - `unittest.TestLoader().discover("tests", "test*.py", None)` is unittest's own loader.
- Only the import of the test modules runs. Any process creation during the import is refused and
  recorded.
- **Output:** the IDs in discovery order, with their counts and digests; duplicates; import
  failures (`_FailedTest`) and the loader's error texts; the process events; the loaded project
  files; any bytecode present; `sys.path` before, at and after discovery; `own_main_admitted`.
- **Launch:** `env -i <frozen environment> <worktree>/.venv/bin/python -B`, without `-I`, `-S`, `-E`
  or `-P`, because the unit process imports `site`. For the baseline, `--root` is an exported copy
  of commit `1c2f25ba`'s tree. The tool never starts Git.
- **Exit:** 0 for a clean discovery; 1 for import failures, duplicates, a refused process start,
  loader errors or bytecode.

**`compare --current C --current-sha256 H --baseline B --baseline-sha256 H --additions A --additions-sha256 H --output OUT`**
- The two discovery documents and `INVENTORY-ADDITIONS.json` are bound by the supplied digests.
- **Recomputed, not trusted (TR-07):** each document's count and duplicates come from its IDs; its
  recorded `count` and `duplicates` must agree with them, and its `state` must be `COMPLETE`. A
  duplicate inside the baseline is therefore found.
- `expected = (baseline ∪ added) − removed`, compared exactly with the current IDs. It reports
  `missing` and `extra`.
- It checks that the additions record agrees with itself: `added_count`, `removed_count`,
  `added_by_module` and `base_count`, the candidate count, no addition already in the baseline,
  and no removal absent from it.
- **Launch:** `-I -S -B`. **Exit:** 0 only for an exact match with clean, consistent inputs.

**Starts:** none. **Substitutes:** nothing. **Limits:**
- Discovery imports every test module, so code at module level runs.
- A `load_tests` hook that varies between runs cannot be detected.
- A refused process start turns that module into an import failure, which is a finding, not a
  silent omission.

## collect_outcomes.py: unittest outcomes

**Purpose.** It runs, as the unit process:
- `cohort`: the complete module `tests.test_static_tray_readback_v01`, both classes;
- `controls`: named methods of MI's frozen module `tests.test_current_host_readback_controls_v02`,
  in a separate run.

It records each test's raw ID and outcome: `pass`, `fail`, `error`, `skip`, `expected_failure`,
`unexpected_success`, `not_run` or `interrupted`. It also records the traceback texts, each subtest,
the timing (the start and stop of each test and unittest's own duration), and the class-level and
module-level errors under unittest's descriptions, for example
`setUpClass (tests.test_static_tray_readback_v01.ReadbackCPUControls)`.

**CLI**

```
collect_outcomes.py cohort   --root ROOT --environment ENV --environment-sha256 H --module-sha256 H --output-dir OUT
collect_outcomes.py controls --root ROOT --environment ENV --environment-sha256 H --module-sha256 H \
                             --test tests.test_current_host_readback_controls_v02.<Class>.<method> [--test ...] --output-dir OUT
```

`--module-sha256` is required in both modes (TR-09).

**What the run does, and what it leaves alone**
- It uses unittest's own `TestLoader.loadTestsFromNames` and `TextTestRunner`, with verbosity 2 and
  the `default` warnings filter that `unittest.main` sets. The result class subclasses
  `TextTestResult`: each method records, then calls the original. So the console output is the unit
  stage's format, and the driver's footer parser could read it.
- `ROOT` is the working directory and `sys.path[0]`, as for `python -m unittest` from `ROOT`.
- Nothing is monkeypatched, and no ID is normalized. The only alias is P07 section 6's prefix:
  `tests.test_static_tray_readback_v01.` to `test_static_tray_readback_v01.`. It joins only when the
  loaded method's class, module, code file and first line equal its parsed source, and the method
  has no decorator.
- **Body digests (TR-09)** are computed as `ORIGINAL_BODIES` is, and compared with the
  `original_bodies` of the configuration's methods document: `original_bodies` records, per name,
  the frozen digest, the source digest and whether they are equal. A difference rules out
  `ALL_PASSED`.
- **A skip inside a `subTest` (TR-09)** is recorded under its parent as `subtest_skip`, and the
  parent's outcome is `skip`. Events of any test that was not planned are kept by name in
  `unplanned_events`, and rule out `ALL_PASSED`.
- `required_methods` gives the outcome of each of P07 section 6's seven methods, or `missing`.

**Checks before any test runs (exit 2)**
- **Flags:** `-B`, and no `-I`, `-S`, `-E` or `-P`.
- **Environment:** exactly the frozen environment. `__CF_USER_TEXT_ENCODING`, which macOS adds to this
  interpreter, is admitted when the frozen environment does not name it, and its value is recorded
  as `environment.admitted_cf_user_text_encoding`. A refusal lists names only. `HOME` is never part
  of a frozen environment.
- **Cohort only:**
  - **driver rules on the frozen environment** (W4-DRIVER section 2): no name of
    `UNIT_REMOVED_ENVIRONMENT` and no `DYLD_*` name; `PYTHONDONTWRITEBYTECODE=1` and
    `PYTHONNOUSERSITE=1`; both selection variables; and `GIT_*` names either absent or exactly the
    driver's own `git_environment` set with its values (TR-09);
  - **the configuration:** its bytes must match the selection digest, which is the driver's
    `readback_config_identity` check; its methods document must hold `original_bodies`;
  - **the provider's `_check_python` rules,** applied to HOST through the configuration's
    descriptor: `sys.executable` equals HOST's `python.launcher`, which equals `python.venv +
    "/bin/python"`; the implementation, `platform.python_version()` and `sys.version` equal HOST's
    interpreter record; `proc_pidpath` equals its `process_image`. A failure is
    `PROVIDER-PRECONDITION`, because the provider would refuse this process.
- **Controls only:** no selection variable, and each `--test` names a method of the frozen control
  module.
- **Module digest:** the target module's SHA-256 must equal `--module-sha256`.

**Outputs:** `OUT/journal.jsonl`, one fsynced line per event, written as the run goes; and
`OUT/outcomes.json`, written at the end. The process events, the loaded project files with any
bytecode, and the module's digest before and after are recorded.

**Launch:** from `ROOT`, with `env -i` and the frozen environment:
`<worktree>/.venv/bin/python -B collect_outcomes.py cohort ...`. The tool cannot set its own
startup environment. The Director captures stdout and stderr, which carry unittest's verbose
output.

**Exit:** 0 when every planned test passes, with no class-level event, no unplanned event, no loader
error, no bytecode, every body equal and all seven methods passing (cohort); 1 for any other
completed outcome; 2 for a refusal; 3 for an interruption or an incomplete run.

**Starts:** the collector starts nothing. The tests start what they start: the provider's Node and
Git starts, and MC37's Python child. The audit hook records each of them. The provider's bound Git
reads are recorded starts that no supervisor bounds (TR-14, for the S6 freeze).

**Substitutes:** nothing.

**Limits**
- Timing has no hook for `setUpClass` itself. The journal's timestamps show it.
- A `SIGKILL` leaves only the journal, and the outcome is then unknown (FAILURE-CAPTURE.md).
- The collector observes the unit process's `__CF_USER_TEXT_ENCODING`, not Node's.

## run_direct_probe.py: direct-probe runner

**Purpose.** One start per frozen row through `supervisor_darwin_v01.run_process`, under the row's
argv, stage (the cwd), label, declared environment and limits. It does not pass through the
provider's parent guard (P07 section 5).

**CLI**

```
run_direct_probe.py --root ROOT --bind REL=SHA256 (x4) --rows R --rows-sha256 H --node N --node-sha256 H \
                    --probe P --probe-sha256 H --loader L --loader-sha256 H --output-dir OUT
```

**Loading the supervisor**
- The four files are bound: `prototypes/__init__.py`, `prototypes/static_tray_v01/__init__.py`,
  `supervisor.py` and `supervisor_darwin_v01.py`.
- They are compiled from their verified bytes and registered under their own module names. So no
  bytecode file and no other copy can stand in for them.
- The tool checks that `run_process` comes from the bound file, and that `Clock`, `Stop` and
  `json_bytes` are the original objects and not `None` (TR-10). No other root module may be loaded
  but its own `__main__` (TR-01).

**The rows document,** `ontokin.c271.p35-direct-probe-rows/2`, is `{rows_independent, rows}`.
- **Row IDs:** `probe-syntax-check`, `P06-H01`, `P06-H02`, `MC36`, and optionally `MC30-probe`
  (below), each at most once, **each in its own stage (TR-10)**.
- **Each row:** `{id, argv, stage, label, environment, total_ms, stage_ms, inputs, stage_entries,
  expected}`.
- **argv shapes:**
  - `[NODE, (--no-addons, --max-old-space-size=256,)? --check, PROBE]` for the syntax check;
  - the probe's argv `[NODE, --no-addons, --max-old-space-size=256, --experimental-loader, LOADER,
    PROBE, --expected-config-sha256, DIGEST, --job, STAGE/job.json]` for the others.
- **Environment:** exactly the declared environment.
- **Limits:** `stage_ms + 2000 <= total_ms <= 30000`.
- **`inputs` (TR-03):** the frozen descriptors `{path, sha256, size_bytes, mode}` of the row's
  inputs: the job, the configuration, the manifest, the HOST copy, the GLB, the reference and any
  other file it reads. Every file of the stage must be one of them.
- **`stage_entries` (TR-03):** the exact set of the stage's entries, `{path, kind}` with kind `file`
  or `directory`, paths relative to the stage.
- **`expected`:** `{returncode, supervisor_error, stdout_exact, stderr_exact, stdout_includes,
  stdout_excludes, stderr_includes, stderr_excludes, absent_paths, present_paths, file_includes,
  json_members}`.
  - **`supervisor_error` (TR-02)** is the one error the exit status implies: for an expected status
    N other than 0, exactly `{"code": "OTRAY-E-BACKEND", "reason": "Child exited with status N",
    "state": "REJECTED"}`; `null` for 0. The raised `Stop` and the receipt's `error` must both equal
    it. So a remaining descendant, a staged link or other staged-output violation, a deadline, the
    log ceiling or an interruption misses the row, whatever the exit status.
  - **Exact and negative predicates (TR-10):** `stdout_exact` and `stderr_exact` (for example `""`),
    `*_excludes`, and `json_members`: `{path: [{"pointer": "/passed", "equals": false},
    {"pointer": "/khronos", "absent": true}, ...]}`, with RFC 6901 pointers.
  - `file_includes` maps a file to literal texts. The probe reports a refusal raised inside its
    `try`, MC36's among them, in `probe.json` and not on stderr.
  - **Every file that `present_paths`, `file_includes` or `json_members` reads must be absent at
    intent (TR-03),** as must the supervisor's three outputs; the record lists them as
    `targets_absent_at_intent`.

**Per row**
- `intent.json` with `kern.bootsessionuuid`; then, immediately before the start, the frozen inputs,
  the stage's exact entries, the absent targets, and the Node executable, the probe and the loader
  are verified again (`verified_before_start`). A difference refuses the row before any start.
- `started-<n>.json` from the supervisor's `on_started`. A failed write is raised, and the
  supervisor then ends the child.
- `outcome.json` holds:
  - the receipt, whether `<label>.process.json` equals `json_bytes` of it, and its `error`;
  - the supervisor's raised `Stop`, if any;
  - stdout and stderr, as bindings and text;
  - the start count: `PROVEN_ZERO`, `OBSERVED_ONE` or `UNKNOWN`, from the audit event, the callback
    and the receipt's PID together;
  - the cleanup proof (`passed`, `process_group_absent`, `reaped`, `handles_closed`);
  - `kern.bootsessionuuid` before and after the start (TR-10), which must be equal for the row to
    be met;
  - the predicates.

`run.json` holds the summary with the exact Node count, or `null` and a lower bound.

**Stops and interruptions:** an unknown row stops every later row. A row that misses its predicates
stops the later rows unless `rows_independent` is true. **An interruption (SIGINT, or SIGTERM or
SIGHUP, which the runner handles as SIGINT) during a start is ended by the supervisor's own
cleanup; the row is not met, every later row is `NOT_RUN`, and the run's state is `UNKNOWN` (TR-18,
FAILURE-CAPTURE section 2).** There is no retry. MC36's dependence on `MC30-probe` is expressed by
their order with `rows_independent: false` (decided in S6).

**Launch:** `env -i PATH=/usr/bin:/bin <worktree>/.venv/bin/python -I -S -B`. The children get the
row's environment, not this one.

**Exit:** 0 when every row completed and met its predicates; 1 for an unmet row; 2 for a refusal
before any start; 3 when an outcome is unknown or the run was interrupted.

**Starts:** one Node start per row that runs. **Substitutes:** nothing.

**Limits**
- It interprets no scientific output.
- The labels of a refused probe result are reported as found, and are unverified (W5's Q5).
- **`MC30-probe`** is for the operational freeze to add, or not. It would be a probe start whose
  HOST input records `__CF_USER_TEXT_ENCODING` as `null`, so that the probe's own environment
  binding refuses exactly when the variable reached Node's `process.env`. That shows presence. It
  cannot show the value: no tool can read Node's environment, because the probe does not report
  it, and the supervisor passes and records only the declared environment. The value follows only
  by elimination (`../AUTHOR-NOTES.md`, T-04).

## audit_numeric.py: numerical audit

**Purpose.** An independent recomputation of P07 section 6's numerical rows. It imports nothing of
the project, the probe or the provider.

**CLI:** `audit_numeric.py --cohort-root DIR [--case LABEL ...] --output OUT`. For each stage
`Q01-positive`, `Q03-positive` and `Q01-changed-reference`, it reads `synthetic-audit.json` (the
retained reference), `probe.json` (the report), `synthetic.glb` and `job.json`.

**What it recomputes from the reference and the report's retained values (`three.nodes`)**
- **The world positions and bounds (TR-15).** Each mesh node's world vertices are recomputed from
  its retained local `positions` and `world_matrix`, in the order of Three.js r186's
  `Vector3.applyMatrix4` (`w = 1 / (m30 x + m31 y + m32 z + m33)`, `x' = (m00 x + m01 y + m02 z +
  m03) w`, and so on), and the bounds from those vertices. The rows use these values, so the audit
  does not depend on the probe's vertex or bounds code. The retained `world_vertices` and
  `world_bounds` must equal the recomputation exactly (`geometry_recomputation`). The matrix terms
  and the normals are the retained importer values.
- **The row inventory,** in the probe's order:
  - 16 world-matrix terms per node;
  - one world-position row and one normal row per vertex and axis;
  - the minimum, maximum and size of the world bounds per axis.
- **For each row:**
  - the difference;
  - the threshold: 5e-6 m for positions, bounds and the terms `[0..2][3]`, 1e-6 otherwise;
  - the decision: finite values, and a difference within the threshold.
- **The comparison with the report:** the reported rows must be that inventory exactly (no row
  missing, extra or duplicated), and equal in actual, expected, difference, threshold and decision.
- **The exact comparisons** that the retained values allow (names, extras, children, parent,
  indices, material, vertex count), and the report's findings as a multiset.

**Further checks**
- **Positives:** every row passes, and there is no finding.
- **The negative:**
  - exactly one failed row and one finding, at `equipment-tray/pair/left/base` `matrix_0_3`;
  - the threshold is 5e-6, and the difference is 0.001 within 1e-9;
  - no `error` member, so it is a scientific rejection.
- **The negative fixture:** the GLB equals Q01's byte for byte, and the reference differs from Q01's
  only in that term (+0.001) and in the fixed scope text.
- **The structure:** 14 nodes, 12 meshes of 24 vertices, and 2,060 rows. The report's schema,
  bindings, versions, validator counts, tolerances and `input_preserved` are checked too.

**Launch:** `-I -S -B`. **Exit:** 0 when all three cases pass every check; 1 otherwise; 2 when an
input is missing or malformed. **Starts:** none. **Substitutes:** nothing.

**Limits**
- Whether Three.js made a root node a mesh (`empty_root`) is not retained, so it is not recomputed.
- The retained local positions and world matrices are the importer's; the audit recomputes from
  them, not from the GLB's node transforms.
- The order of the findings, which the probe sorts with `localeCompare`, is not compared.
- The 1e-9 tolerance for "about 0.001" is this harness's own declared bound (T-10).

## scan_mc11.py: MC11 static scan

**Purpose.** A static scan of the probe, the module loader `tools/three_loader.mjs` and the 24 reader
files, for process-creation calls.

**CLI**

```
scan_mc11.py --probe P --probe-sha256 H --dependencies-root D --dependencies-inventory I \
             --dependencies-inventory-sha256 H [--reviewed R --reviewed-sha256 H] --output OUT
```

**Inputs**
- **The inventory** is `dependencies/0.2.0`, or the MP install plan `install/0.2.0` with purpose
  `retained-dependencies`. It must list exactly 24 files, the loader among them.
- **The tree** must be exactly those regular files, with no link, no special file and no
  `.DS_Store`, each equal to its binding.
- **The reviewed list** (`ontokin.c271.p35-mc11-reviewed/2`) must have `status: "REVIEWED"` and a
  non-empty `reviewer`; any other list refuses (TR-12). Per file it holds the reviewed
  `process_call_names` and `dynamic` hits (`[pattern, line, column]`), the `specifiers`, and the
  frozen rule's `frozen_rule: {dynamic: [[kind, stripped line], ...], static_specifiers: [...]}`.

**Two verdicts (TR-12)**
- **The frozen rule's, which decides MC11:** MI's `mc11_rule` (CONTROLS-FROZEN.json), applied as
  MI's line-based `scan_javascript` applies it, pattern for pattern: no `child_process`, `cluster`
  (identifier), `worker_threads` or `dlopen`; each dynamic hit (`eval`, `Function`,
  `createRequire`, a non-literal `require(` or `import(`) in the file's reviewed list; the one-line
  static specifiers equal to the reviewed list as a multiset. The reviewer records multi-line
  specifiers separately, as the rule's implementation note asks.
- **The wider scan's, for review (TR-11).** Every pattern runs on the raw text and on two views of
  each line with an escape or a `+`: JavaScript escapes decoded, and adjacent string literals
  joined. Each hit has its line, column, an advisory lexical context and a snippet:
  - **process creation:** `child_process` and `worker_threads` in any letter case, `cluster` and
    `Worker` as names, `dlopen`, `process.binding`, `_linkedBinding`, `internalBinding`, `execve`,
    and the internal binding names `spawn_sync` and `process_wrap`;
  - **process call names:** `spawn`, `spawnSync`, `exec`, `execSync`, `execFile`, `execFileSync` and
    `fork`, called directly, through a receiver or parenthesized (`(0, cp.execFile)(...)`), with
    the receiver;
  - **dynamic constructs:** every `eval` and `Function` substring, classified; `createRequire`; a
    computed `require(` or `import(`; **every `require` that is neither a plain call nor a
    declaration** (`require-reference`: a member, a reference such as `self.require = require`, or a
    parenthesized callee, whose literal argument is listed as a `require-parenthesized`
    specifier, as in the validator preamble's `(...: require)("url")`); `__non_webpack_require__`;
    `Module._load`, `module.constructor`, `process.mainModule`, `module.require`; the bracket forms
    `['name']` of the process and module names; a `vm` specifier;
  - **static specifiers:** of `import`, `export`, `require` and `import()`, including statements that
    span lines, each resolved to a reader file, to a `node:` builtin, or marked bare.

**Exit:** 0 when the frozen rule passes, the wider scan finds no process creation, the reviewed
list matches it, and every relative specifier resolves; 1 otherwise; 2 for an input refusal.
**Starts:** none. **Substitutes:** nothing. **Limit:** a scan of names cannot exclude every dynamic
route (contract section 5). The lexical context is advisory, and the hit list does not depend on it.

## control_harness.py: reruns for MI's F-01, F-03 and F-04

Each command writes one output file with its `checks`, its `substituted` list and its
`process_events`. **Exit:** 0 when every check of the frozen expectation holds; 1 otherwise; 2 for a
refusal; 3 for an unknown outcome. Every command refuses a start without `-B`.

### `mc10` (F-01)

**CLI**

```
mc10 --root ROOT --plan P --plan-sha256 H --bind REL=SHA256 (x4) \
     --git-stdout-hex HEX --node-stdout-hex HEX --expect refused-output|accepted --output OUT
```

**What runs.** The observer's real `observe_host` on a frozen plan, with M0's real static bindings:
the plan, environment, platform, OS identity, source, Python installation, packages, runtime with
its Mach-O rules, reader tree, Git binding, failure-capture binding and evidence ancestors.

**Loaded from verified bytes:** the observer, `supervisor.py` and the two package files. The four
`--bind` values bind them.

**Substituted, so the host boundary is labelled `mocked`**
- **The command boundary.** It answers the frozen stdout of Git and Node `--version` (in hex), and
  writes the supervisor's three files with a receipt that names no possible PID. Nothing starts,
  and the audit hook refuses any process creation.
- **One row of the observer's loaded-module listing:** this harness's own `__main__` file. The plan
  binds that file by SHA-256 instead. A test reaches the observer's `PYTHON-MODULE` rule with and
  without this exclusion (TR-13).

**The attempt listing** opens files with `O_NOFOLLOW` and records a link as a link (TR-13).

**Launch:** exactly as M0 is launched: `env -i <declared environment> <venv>/bin/python -I -S -B`.

**Expectations**
- `refused-output`: an `OUTPUT` refusal, no HOST, no completion, not finalized, labelled `mocked`.
- `accepted`: `OBSERVED_UNAPPROVED`, and a HOST labelled `mocked` with runtime `v24.22.1`.

Each plan needs its own absent attempt directory.

### `mc29` (F-03)

**CLI**

```
mc29 --root ROOT --config C --config-sha256 H --glb G --glb-sha256 H --audit A --audit-sha256 H \
     --environment ENV --environment-sha256 H --change configuration|job-input [--expect-code CH-...] --output OUT
```

**What runs.** The 0.2.0 provider with its real detectors:
- `setup_cpu_cohort` through the facade, on a fresh class object;
- one attempt on `Q01-positive`, whose stage the harness builds as `check_case` does: the frozen GLB
  and reference, and `job.json` as `json_bytes`;
- `finish_cpu_cohort`.

**The environment (TR-06)** must be exactly the frozen one given with `--environment`, and its
selection pair must equal `--config` and `--config-sha256`. `HOME` is never part of it. The record
holds the names only.

**The change.** Immediately after the provider writes the attempt's `preflight.json`, one real
change: the configuration gains one space, or `synthetic.glb` gains one zero byte.

**Substituted, so the provider labels its records `mocked`**
- `supervisor_darwin_v01.run_process`, by a recorder that refuses to start anything;
- the provider's `_write_new`, by a wrapper that calls the original and then makes the change once.

**Checks**
- 17 named provider functions are checked before and after the run as the provider's own plain
  functions;
- zero recorder calls, zero `on_started` calls and zero Node process events;
- a refused attempt and a refused cohort accounting;
- the ledger: zero starts and not `COMPLETED`.

The provider's bound Git reads are recorded, not counted as bounded starts (TR-14, for S6).

**Launch:** as the unit process: `env -i <frozen environment> <venv>/bin/python -B`. The
configuration must be a dedicated copy at its own path for each case, because the `configuration`
case changes it.

### `host-state` (F-04)

**CLI:** `host-state --root ROOT --host HOST --host-sha256 H --output OUT`

**What runs.** The provider's real `host_state()`, compared with HOST's `platform` and `os` by the
provider's own `_check_state`. Nothing is substituted. The audit hook refuses any process
creation, and the provider's boundary label must read `real` before and after.

## Tests

`tests/` holds focused tests on synthetic inputs, with the standard library only. Run them from this
directory with the qualification interpreter:

```
MH_TOOLING_ROOT=<worktree> <worktree>/.venv/bin/python -B -m unittest discover -s tests -v
```

`MH_TOOLING_ROOT` can be left out once this directory sits at its place in the worktree.
`MH_TOOLING_UNDER_TEST=<directory>` runs the same tests against another copy of the tools; against
an earlier runner, discovery collector or rows schema, the tests write the inputs in that version's
form, so that each test of a fix fails on what the fix changes.

**What they read and what they start**
- They read the project's own files: the Darwin supervisor, the observer, the provider, and the
  synthetic GLB and reference builders of `tests/test_static_tray_reader_v01.py`. One harness test
  reads this checkout's source inventory, HEAD and Python installation, as M0 does. They write only
  in resolved temporary directories.
- **Children:** the interpreter, always with `-B`; `/usr/bin/true` and `/bin/sh`; and, through the
  runner under test, stand-in scripts that this interpreter runs with `-B` (some fork once).
- **Never started:** Node, Git, `ldd`, `codesign` or the observer's `observe`.
- **The hygiene test (TR-04)** derives the forbidden strings at run time (the home directory, the
  account name, the worktree's parent, the local root, the interpreter's base prefix and the
  temporary directory, with their ancestors and components) and also searches joined string
  literals. No file holds a literal of them, and a failure names only the file and the kind.

`tests/TEST-RUN.txt` is the output of the recorded run, with its start counts.
`tests/TEST-RUN-AGAINST-REJECTED-001.txt` is the same suite run against the rejected tooling of
review 001, which shows each fix's test failing there. Machine paths in both are replaced by the
labels `<worktree>`, `<local>`, `<prefix>`, `<home>` and `<tmp>`.
