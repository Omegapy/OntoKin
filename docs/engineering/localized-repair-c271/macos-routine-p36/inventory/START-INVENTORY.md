# Gate MR, stage S2: the static start-and-write inventory

Worker W1 of C271-P36 (Director `c271-p36-14f7f8b219db`), a Claude Code subagent in a fresh context.
Candidate: branch `work/c271-missing-import-digest-control` at `d3b622d61745259c3477bc94be0fb4da05c23c56`,
read in the clean worktree (the branch ref and the worktree `HEAD` were read from Git's files; no Git
command ran). Everything below was established by reading files, with helper scripts run only as
`python3 -I -S -B`. Nothing that the inventory is about was started.

Labels: `<worktree>` the C271 worktree; `<workspace>` the driver's isolated copy under its output
directory `<output>`; `<local>` the local data root beside the clone; `<tmp>` the temporary directory;
`<prefix>` the package manager's installation prefix; `<framework>` the framework interpreter's version
directory under `<prefix>`. "The bound Git" is the developer tools' Git implementation whose absolute path
HOST binds; `/usr/bin/git` is the operating system's dispatcher to it. The routine is
`.venv/bin/python -B tools/check_local.py --timeout T --output-dir D` (R2), plus
`--readback-config F --readback-config-sha256 H` for R1. The machine-readable list is
[START-INVENTORY.json](START-INVENTORY.json): 56 entries, of which 42 are real start sites or groups,
8 are reached but substituted (mocked or forbidden), 5 start nothing and 1 groups the unreached sites.

## The six verdicts

1. **Every start, in either run kind: YES, enumerated.** The driver makes `uname -p`, `file -b`, its Git
   reads and seven step starts. Three of the other steps add starts (agent, construction and impulse);
   source, surface and documents add none. The unit stage adds Python children, Git, one `os.fork`, shell
   stand-ins and, in R1 only, the three Node checkers. Limits: Git's own descendants and exact per-test
   Git counts are not enumerated, R2's counts are upper bounds, and no reading excludes every dynamic route.
2. **Foreign programs.**
   - (a) A Node other than the pinned runtime: **YES, but only through `PATH`.** Two unit tests run the
     real doctor without `--node`, and it starts the first `node` on the inherited `PATH`
     (`tools/doctor_local.py:737-741`). That is up to 6 starts per run kind (U-28 ×3, U-30 ×3). **Under
     `PATH=/usr/bin:/bin` there are none:** neither `/usr/bin/node` nor `/bin/node` exists.
   - (b) `ldd`, `codesign` or `otool`: **NO.** No reachable start names them. The `/usr/bin/ldd` start
     sites are unreached or forbidden by guards, and `/usr/bin/ldd` does not exist.
   - (c) Another program outside the allowed set: **NO under `PATH=/usr/bin:/bin`, YES through `PATH`
     otherwise.** Every bare name follows `PATH`: `git`, `uname`, `file`, `node`, `python3.12` and Git's
     `lfs` helper. Under `/usr/bin:/bin` they resolve to `/usr/bin/git`, `/usr/bin/uname`, `/usr/bin/file`
     or to nothing.
3. **Writes into bound trees.**
   - (a) The Python installation trees: **NO write is expected; a dynamic import is the residual.**
     Four kinds of start can write bytecode: U-26 ×8, U-27 ×2, U-30's environment creation ×1 and U-18's
     grandchild ×1. By reading, they import only standard-library modules whose cached bytecode already
     exists and matches its source. None imports from the `.venv`, which has no `.pth` file and no
     bytecode at all. A dynamic import cannot be excluded by reading.
   - (b) The pinned runtime and the reader tree: **NO.**
   - (c) The worktree: **NO,** provided that the driver itself runs with `-B`.
4. **Expected Node starts: CONFIRMED.** R1 makes exactly 3, the readback CPU trio through the provider
   (RB-01). R2 makes 0, because the class fails at `setUpClass` with the ordinary-run reason. Both hold
   on condition that `PATH` holds no `node`.
5. **Order: established.** `test_static_tray_readback_v01` is module 337 of 389 in discovery order. All
   389 modules are imported before any test runs. Every bytecode-writing start and every `PATH`-sensitive
   doctor start comes before it: modules 5, 32 and 105. So does the first `uname`/`file` of the unit
   process, at module 16. MC22's nested ordinary run of the readback module, at module 24, also comes
   before it.
6. **Other risks to R1 (section 8).**
   - `PATH` must be fixed.
   - A driver started without `-B` would make R1 refuse.
   - The provider's refusal of any added file in the four source trees of the workspace. No test writes
     there, by reading.
   - Shared process state that earlier tests leave behind. It is restored, or harmless.
   - The two-volume premise of MC16.
   - Git children of the doctor read the user's global Git configuration.

## 1. Method

- Read: the governing files, the MR plan, `PHASE.json`, contract sections 4 and 7 to 9, MI's
  `for_later_gates.MR` and D-18 to D-21, MH's portable HOST and Python inventory, `tools/check_local.py`
  in full, and every start site listed below, with its callers.
- `scripts/scan_starts.py`, an AST scan of all 851 `.py` files under `tests/`, `tools/`, `ontokin/`,
  `prototypes/` and the documents verifier, recorded:
  - every call of `subprocess.*`, `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `os.system`, `os.popen`,
    `os.fork`/`forkpty`, `pty`, `multiprocessing`, `concurrent.futures.ProcessPoolExecutor`, the `asyncio`
    subprocess APIs, `ctypes`, `shutil.which`, the `platform` helpers and the dynamic loaders;
  - every reference to a start function;
  - every `mock.patch` target, and every mutation of the environment or of `sys.dont_write_bytecode`.

  A second scan covered `examples/`, `docs/language-design/` and `fixtures/`, which tests load by path.
  No `multiprocessing`, `pty`, `asyncio` subprocess, `os.exec*`, `os.spawn*`, `os.posix_spawn*`,
  `os.system` or `os.popen` call is reachable. These names occur only as patch targets that forbid them.
  `ctypes` is used for `sysctlbyname`, `renamex_np`, `renameat2` and `prctl`, never for `fork` or `exec`.
- `scripts/import_graph.py` built the static import closure of each of the 389 test modules and of each
  step's entry point. `scripts/module_level_calls.py` listed the code that runs at import time. No test
  module, and no module that tests import, starts anything at import time.
- `scripts/pyc_presence.py` and `scripts/stdlib_closure_toplevel.py` read the cached bytecode of the
  framework's standard library, and the import closures of the bytecode-writing starts.
- The CPython 3.12.13 `platform` module was read in the framework, to establish when it starts `uname`
  and `file`.

## 2. The driver's own starts (both run kinds)

| Entry | Site | Program and argv | Count R1 / R2 |
| --- | --- | --- | ---: |
| DRV-01 | `tools/check_local.py:729`, `platform.platform()` → `platform.py:819-835` | `uname -p` by name through `PATH`, in the driver's environment | 1 / 1 |
| DRV-02 | the same → `platform.py:648-676` | `file -b <interpreter file>`, by name, environment plus `LC_ALL=C`. The file is `sys.executable` with its final-component links followed: `…/Python.framework/Versions/3.12/bin/python3.12`, possibly through the `<prefix>` link | 1 / 1 |
| DRV-03 | `tools/check_local.py:272` `git_read` | `<git> -c core.fsmonitor=false -C <root> …`. R1: the bound Git, from the selection, hashed again before each start. R2: `git` resolved once on `PATH` | 41 / 21 |
| DRV-04 | `tools/storage_identity.py:53` | the same Git, `-c core.hooksPath=/dev/null -c core.attributesFile=/dev/null`, 4 `StorageContext` reads and 4 attribute reads, one of them `init` in a new `<tmp>` directory | 8 / 8 |
| DRV-05 | Git internals of `git fetch --depth=1 -- <worktree> <head>` | `/bin/sh -c "git-upload-pack …"`, `index-pack`, `rev-list`, `maintenance run --auto` from Git's exec path | not counted |
| DRV-06 | `tools/check_local.py:666` | `<worktree>/.venv/bin/python -B <step>`, cwd `<workspace>`, `start_new_session` | 7 / 7 |

- **DRV-01 and DRV-02 (D-19).** `platform` computes `uname().processor` once per process and caches the
  result of `platform()`. So each Python process that calls it unpatched starts each program once. The
  baseline summary's `macOS-26.6.2-arm64-arm-64bit` is that output.
- **DRV-03.** The 41 Git reads of R1 are:
  - `git_metadata(<worktree>)`, before and after: 5 + 5;
  - `prepare_workspace_git`: 6, namely `init`, `fetch`, `update-ref`, `read-tree` and `rev-parse` twice;
  - `git_metadata(<workspace>)`: 5;
  - the provider's `_verify_source`, which runs through `git_read` three times: in `validate_selection`
    on `<worktree>`, and in `derive_workspace_binding` on `<worktree>` and on `<workspace>`: 15;
  - `derive_workspace_binding`'s own `git_metadata(<workspace>)`: 5.

  Every one runs with the environment of `check_local.git_environment`, which has
  `GIT_OPTIONAL_LOCKS=0`. So `git status` refreshes no index, and nothing is written in `<worktree>`.
- **DRV-04.** It is reached because `.gitattributes` is committed. `configure_offline_filters`, with
  `shutil.which("git-lfs")` and `[git-lfs, version]`, is not reached: no file lies under
  `docs/engineering/lfs-archives/`. Adding one at B would add a `PATH` lookup and a start of `git-lfs`.
- **DRV-06: each step's environment.** It is the driver's own, with these changes:
  - every `GIT_*` name removed;
  - `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_TERMINAL_PROMPT=0`,
    `GIT_ATTR_NOSYSTEM=1`, `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_REPLACE_OBJECTS=1`, `GIT_NO_LAZY_FETCH=1` and
    `GIT_CEILING_DIRECTORIES=<output>` added;
  - `PYTHONDONTWRITEBYTECODE=1`;
  - both selection variables removed.

  R1's unit step also gets the derived selection pair and `PYTHONNOUSERSITE=1`, and loses the
  `UNIT_REMOVED_ENVIRONMENT` names. Every step's argv carries `-B`.
- **What starts nothing.** `build_plan`'s `shutil.which("node")` (line 440) is a lookup only, since the
  core plan never uses it. `stop_process` (line 518) only signals, on a timeout (O-01).

## 3. The other six steps

| Step | Starts beyond its own process |
| --- | --- |
| `source` (`-m ontokin conformance`) | none: `ontokin/conformance.py` uses `platform.system` and similar only |
| `agent` (`tools/run_agent_conformance.py`) | `uname -p` and `file -b` once each (line 79). Its A01 to A10 cases start no child |
| `construction` (`-m tools.verify_construction_ci`) | `uname`/`file` once each (`ontokin/construction_conformance.py:681`), and 128 required tests in process, among them U-08 (3 Python CLI starts) and U-09 (2 Python starts) |
| `surface` (`tools/run_surface_conformance.py --allow-pending`) | none: its 61 required tests have no start site, and `_verify_ci`'s `git ls-tree` needs external evidence |
| `impulse` (`tools/run_impulse_conformance.py --allow-pending`) | U-07 (2 Python starts), U-15 (`git rev-parse HEAD`, `git status --porcelain` in `<workspace>`) and U-14 (at most 5 Git starts in a `<tmp>` repository, `ls-tree` with cwd `<workspace>`) |
| `documents` (`verify_reorganization.py`) | none |

These children inherit the step's environment, which holds `PYTHONDONTWRITEBYTECODE=1`, and none uses
`-I` or `-E`. No step receives a selection, so none runs the readback module.

## 4. The unit stage

The unit stage is `python -B -m unittest discover -s tests -v`, started in `<workspace>`.
- There is no `tests/__init__.py`, and `tests/fixtures` is not a package. Discovery therefore imports the
  389 files `tests/test*.py`, in `sorted(os.listdir)` order, as top-level modules, before any test runs.
- Classes and methods run in name order. In the readback module, `ReadbackCPUControls` runs before
  `ReadbackCoordinatorSeams`, and its methods run in the order Q01-positive, Q03-positive,
  Q01-changed-reference.

The real start sites follow. JSON entries U-00 to U-30 hold the exact argv, cwd, environment, guard and
conditions of each.
- **Metadata leaf (U-00).** The first unpatched `platform.platform()` of the unit process is in
  `test_construction_conformance`, module 16, through `run_conformance`. It starts `uname -p` and
  `file -b` once each; later calls are cached. Those later calls are MC22, `RTLDPathControls.setUpClass`
  and `test_local_checks`.
- **Python children with the inherited environment** (U-01 to U-10). They are `.venv/bin/python -c …` or
  `-m ontokin …`, with cwd `<workspace>`. The guard is `PYTHONDONTWRITEBYTECODE=1`, without `-I` or `-E`.
  They come from:
  - `test_agent`: 3;
  - `test_agent_cli`: 4 sites;
  - `test_cli`: 1;
  - `test_budget_agent_lifecycle`: 1;
  - the five export-and-agent modules: 10;
  - `test_force_agent_cli` and `test_reach_agent_cli`;
  - `test_impulse_cli`: 2;
  - `test_program_protocol`: 3;
  - `test_program_transactions`: 2;
  - `test_surface_agent_cli`: 6 sites.

  The prepared workers are killed in `finally` blocks.
- **Python children with `-B`** (U-11, U-12, U-13, U-19 to U-21, U-23). They come from:
  - the reader's `-IB` command-line tests: 8;
  - the observer's command-line tests, under `-I -S -B` in the declared environment: 5;
  - the Darwin supervisor's children and the MI supervisor children, under `-I -S -B -c`, which fork
    descendants by design and are killed by their teardowns;
  - the driver tests' unit children, `-B -c` and `-B -m unittest discover` in `<tmp>` workspaces;
  - the MI driver controls, under `-I -S -B -c`.

  MC22's child loads `tests.test_static_tray_readback_v01` from `<workspace>` in an ordinary run. It
  fails at setup and starts no Node.
- **Git by name through `PATH`** (U-14, U-15, U-17, U-25). These cover:
  - the temporary repositories of `test_chat_workflow`, `test_force_conformance`,
    `test_impulse_conformance`, `test_surface_conformance` and `test_local_checks`, and the
    `LocalProject` of the doctor and setup tests, 3 starts per fixture, plus the fake runner's
    pass-through of `git`;
  - `git rev-parse HEAD` and `git status --porcelain` in `<workspace>`, from the impulse and surface demo
    builders;
  - `git ls-tree` with cwd `<workspace>`, from `_verify_commit_inventory`.
- **Shell stand-ins for Git** (U-20, U-22, U-24): `#!/bin/sh` scripts in `<tmp>` that log, then exit or
  `exec` the Git on `PATH`. They are bound through `check_local.bind_git`. Every such test isolates
  `check_local._GIT_STATE`.
- **The real doctor and setup tool.**
  - U-26: `RealEnvironmentTests.setUp`, 8 times, runs
    `.venv/bin/python -I -m venv --without-pip <tmp>/…`, with neither `-B` nor an honoured variable. The
    real `doctor.collect` then runs with `which=lambda name: None`, so its probes are `-I -B` and `-B`.
  - U-27: `test_real_child_keeps_a_passed_descriptor_open`, 2 times, runs `.venv/bin/python -I -c "import
    os, sys; …"`, with no `-B`.
  - U-28: `ReportTests.test_command_line_runs_without_site_packages_and_writes_only_a_new_report` runs
    the doctor's command line three times, as `-I -S -B tools/doctor_local.py --root <tmp>/checkout`
    without `--node`. Each run makes about 17 Git starts, `git lfs version` among them, and starts
    `node --version` if `which("node")` finds one. It also tries to execute an empty, non-executable `python3.12` fixture;
    the exec fails, and no program starts.
  - U-29: four `-I -B` runs of a one-line `chat_workflow.py` stand-in.
  - U-30: `RealSetupTests.test_real_core_environment_from_the_command_line` runs the setup tool's command
    line twice, as `-I -B tools/bootstrap_local.py … --profile core`. Inside, it starts:
    - three `doctor.collect` calls with the real `which`, so `node --version` and `git lfs version`
      again;
    - a probe of the base interpreter, `sys._base_executable`, which is the framework interpreter, possibly
      through its `<prefix>` link (`-I -B`);
    - one `<base> -I -m venv <tmp>/check out/.venv`, without `-B`;
    - that process's `ensurepip` child and pip child, which inherit `PYTHONDONTWRITEBYTECODE=1` from
      `doctor.clean_environment()`;
    - `-I -B` probes, `-I -B -m pip check`, a `-B` source import, a `-I -B` preflight, and four `-B`
      smoke checks.

    The core profile neither installs packages nor reaches `lsof` or `ps`.
- **The deliberate bytecode test** (U-18). `test_parent_only_no_bytecode_flag_does_not_protect_child_imports`
  starts `-B -c` in an environment without the variable. Its grandchild,
  `.venv/bin/python -c "import ontokin"`, writes `<tmp>/source/ontokin/__pycache__/…` by design.
- **`os.fork`** (U-16). `test_static_tray_admission_c231_ledger_identity` forks once, with no exec. The
  child always calls `os._exit`.
- **The readback cohort, R1 only** (RB-01 and RB-02).
  - Three starts of the pinned runtime through `supervisor_darwin_v01.py:155`, with this argv:
    `<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node --no-addons --max-old-space-size=256
    --experimental-loader <local>/c271-macos/reader-c195/tools/three_loader.mjs
    <workspace>/prototypes/static_tray_v01/current_host_readback_v02.mjs --expected-config-sha256 <digest>
    --job <cohort>/<case>/job.json`.
  - Their cwd is the case stage, and their environment is exactly `format_check.ENVIRONMENT`.
  - The provider makes 60 Git reads with the bound Git in `<workspace>`, 5 per `_selection`: 2 at setup,
    3 per attempt and 1 at finish.

**Reached but substituted** (M-01 to M-08; no real start):
- `format_check.run_process` in the readback seams;
- `transaction.run_process`;
- the 0.1.0 Linux inspection's helpers, which include `ldd`. The `subprocess` and `os` start functions
  are patched to raise there;
- `supervisor_darwin_v01.run_process` in the MI provider world and in the provider tests;
- the observer's `observe`, which runs with a mocked supervisor;
- the doctor and setup tests' fake runner, which answers `venv`, `pip`, `node --version`, `lsof`, `ps`
  and the probes;
- the driver tests that patch `Popen`;
- the Linux `supervisor.run_process`. On macOS its `prctl` lookup raises before `Popen`.

**Unreached** (X-01):
- `format_check.build_manifest`, with `node --version` and `/usr/bin/ldd`, behind the command-line
  subcommand `seal-readback`;
- `force_conformance.record_external`;
- `verify_reach_destinations.run`, and the `main` functions of the `verify_torque_native_dense*` tools;
- the tools' acceptance and audit Git helpers. Their tests import pure functions only;
- `tools/second_target_*/tests/run_controls.py` and `tools/storage_tests/`, which lie outside `tests/`;
- the guided-contact and semantic-receiving prototypes, `lifecycle*.py` and `lock.build_lock`.

`tests/test_static_tray_readback_v01.py` line 29 holds a module-level constant that names a Node path of
another software installation. Nothing uses it, and it starts nothing.

## 5. Foreign programs and `PATH`

Every start by bare name inherits `PATH` from the driver: `git`, `uname`, `file`, `node` and `python3.12`,
and Git's `lfs` helper. The pinned runtime and the bound Git are started by absolute path.

| Name | Under `PATH=/usr/bin:/bin` (checked with `stat` only) | Starts if another directory comes first |
| --- | --- | --- |
| `node` | absent from `/usr/bin` and `/bin` | U-28 ×3 and U-30 ×3: `<that node> --version` |
| Git's `lfs` helper | absent from `/usr/bin`, `/bin` and the bound Git's exec path | the same 6 `git lfs version` starts would run it |
| `python3.12` | absent | the same 6 doctor collects would probe it, with `-I -B` |
| `git`, `uname`, `file` | `/usr/bin/git`, the dispatcher to the developer tools' Git, `/usr/bin/uname` and `/usr/bin/file` | every bare-name start of section 4, and DRV-01 and DRV-02 |
| `ldd`, `codesign`, `otool` | no reachable start names them | none |

The other programs started are:
- the framework interpreter, through `<worktree>/.venv/bin/python`, through `sys._base_executable`, and
  through the `<tmp>` environments created from it;
- `/bin/sh`, for the stand-ins and inside Git.

All of them lie within the allowed set. **The freeze should give R1 and R2 exactly the declared `PATH`**,
which MH's environment and the probe's environment already use.

## 6. Writes into the bound trees

**What HOST binds** (MH's portable HOST and `python-inventory-001.json`):
- every entry of `<framework>`: 3,788, of which 414 are `.pyc`. Its `lib/python3.12/site-packages` is a
  link that is recorded, not followed;
- every entry of `<worktree>/.venv`: 345, with no `.pyc`;
- the five external dylibs.

MC32 refuses an added, changed or missing file.

**The framework's cached bytecode, read with `stat` and the 16-byte headers.**
- There are 1,804 standard-library sources, outside `site-packages`. 414 have an opt-level-0 `.pyc`, all
  of whose headers match the source's modification time and size. There are no opt-1 or opt-2 files.
- 1,390 sources have no `.pyc`. Most of them lie in `test/` (1,052), `idlelib/`, `lib2to3/`,
  `turtledemo/` and `tkinter/`, but they also include, for example, `doctest`, `graphlib`, `zipapp`, some
  `email.mime`, `multiprocessing`, `asyncio` and `encodings` modules, and `unittest/_log.py`.
- So a Python process that writes bytecode and imports any of them adds a file to a bound tree.

**The `.venv`** has 297 files, no `__pycache__` and no `.pth` file. Any import of a third-party package by
a bytecode-writing process would add files there.

**Which starts can write bytecode.** A start can write bytecode when it has neither `-B` nor an honoured
`PYTHONDONTWRITEBYTECODE`; `-I` and `-E` make Python ignore the variable. There are four kinds, all in
the unit stage of both run kinds, and all before the readback module:

| Kind | Site | Starts | What it imports, by the module-level closure plus the executed function-level imports | Writes |
| --- | --- | ---: | --- | --- |
| U-26 | `tests/test_doctor_local.py:656`, `-I -m venv --without-pip` | 8 | `venv`, `venv.__main__`, `argparse` and their closure: 58 modules. The function-level imports on its path are `_osx_support` and `argparse` | `<tmp>` only |
| U-30 | `tools/bootstrap_local.py:392`, `<base> -I -m venv` (with pip), where `<base>` is `sys._base_executable` | 1 | the same, plus the framework's `sitecustomize`. `ensurepip` runs in a child that honours the variable | `<tmp>` only |
| U-27 | `tests/test_doctor_local.py:1066`, `-I -c "import os, sys; …"` | 2 | start-up only: `encodings`, `encodings.aliases`, `encodings.utf_8` and `sitecustomize`. `site`, `os` and the other start-up modules are frozen | nothing |
| U-18 | `tests/test_local_checks.py:366`, grandchild `-c "import ontokin"` without the variable | 1 | start-up, plus the temporary `ontokin` package | `<tmp>/source/ontokin/__pycache__` by design |

- Every module in these closures has a fresh cached `.pyc`. The two exceptions are `_py_abc` and
  `_threading_local`, which `abc` and `threading` import only when `_abc` and `_thread._local` are
  missing.
- The function-level imports of the closure's modules are cached too. The two exceptions are
  `_aix_support`, which only AIX imports, and `ensurepip/_uninstall`.
- These starts import nothing from the `.venv`, and nothing from `<prefix>/lib/python3.12/site-packages`,
  which holds no `.pth` file. **By reading, no file is added to a bound tree.**
- **Corroboration.** The newest `.pyc` in `<framework>` dates from 2026-11-11, and the count of 414
  equals MH's inventory. Main's complete baseline runs of 2026-11-25 ran these tests: the
  resolved-directory unit log shows U-18, U-26, U-27, U-28 and U-30's tests as `ok`. Those runs added no
  `.pyc`.
- **Limit.** The closure is static. An import that a module makes by computed name on the executed path
  is not excluded.

**The pinned runtime and the reader tree.** No test names them. The paths reach only R1's provider, which
reads them, and Node, which executes them. No Node, compile-cache or package-manager variable reaches the
checker, whose environment is fixed.

**The worktree.** These facts establish that nothing writes there:
- the driver writes only under `<output>`;
- every test uses `ROOT = <workspace>`, `<tmp>` or `<output>`;
- the driver's and the provider's Git reads on `<worktree>` run with `GIT_OPTIONAL_LOCKS=0`;
- every Python process whose cwd is `<workspace>` carries `-B` or the variable.

The worktree holds no `__pycache__`, `.pyc` or `.DS_Store` now.

## 7. Expected Node starts

| Run | Pinned runtime, through the provider | Other Node |
| --- | ---: | --- |
| R1 | 3 (RB-01: Q01-positive, Q03-positive, Q01-changed-reference) | 0 under `PATH=/usr/bin:/bin`; otherwise up to 6 (U-28, U-30) |
| R2 | 0: `ReadbackCPUControls.setUpClass` raises "No approved current-host readback selection: ordinary run, not a qualification" | the same |

**Other tests that read the selection variables** start no Node:
- MI's provider world and MC29 set synthetic selections inside `patch.dict` and mock `darwin.run_process`;
- the provider tests patch the supervisor or refuse before it;
- the driver tests' synthetic unit children receive a synthetic pair but never load the readback module;
- MC22's nested readback run has no pair.

## 8. Other risks for R1, by reading

- **`PATH`** (section 5).
- **The driver must run with `-B`.** In R1, the driver imports `prototypes/static_tray_v01/*`
  (`current_host_readback_v01`/`v02`, the observer, both supervisors, `format_check`, `lock`,
  `canonical`) and `tools/storage_identity` from `<worktree>`.
  - Without `-B`, it would write `__pycache__` into `<worktree>/prototypes/static_tray_v01`.
  - `validate_selection`'s `source_paths` would then refuse with `SOURCE-BYTECODE`, and the worktree
    would change.
- **The provider's source check of `<workspace>`, 12 times in the unit process.** It refuses any
  `__pycache__`, `.pyc`, `.pyo`, `.DS_Store` or added file in `ontokin/`, `tests/`,
  `prototypes/static_tray_v01/` and `tools/static_tray_reader_v01/`. It also refuses a changed
  `SOURCE_FILES` entry, a dirty tracked file, or an untracked file that is not a generated example.
  - No test writes there by reading.
  - Main's two baseline workspaces hold no `__pycache__` or `.pyc`, and both runs recorded
    `source_unchanged: true`.
  - The one path that could break this only after a regression is
    `tests/test_prepare_current_host_readback_v02.py:1087`. It names files at the workspace root that the
    preparer must refuse before writing.
- **Shared process state before module 337.**
  - Earlier tests leave `check_local._GIT_STATE` as an unbound `PATH` resolution. The provider's
    `bind_git` accepts that. No test leaves a bound state: every binding test patches `_GIT_STATE`.
  - Every mutation of `os.environ`, `sys.modules`, `facade._COHORT_BINDING` and `provider._VERIFIED` is
    restored by `patch.dict` or `patch.object`. The one `chdir` is restored in `finally`.
  - `sys.path` is the exception: two additions made at import time stay, `tools/static_tray_reader_v01`
    and the workspace root. The duct tests remove `examples/connected-duct` again at import. None of
    these shadows a standard-library name.
- **MC16** (`test_current_host_readback_controls_v02`, module 24). It aims a cross-volume `renamex_np` at
  `<output>/.ontokin-w6-mc16-<random>`, and it asserts that `<output>` and `<tmp>` lie on different
  volumes. EXDEV means that nothing is created. On one volume the test fails (I-05).
- **Doctor Git children** run with `clean_environment()`, which strips `GIT_CONFIG_GLOBAL`. So they read
  the user's global Git configuration, which is host state that the freeze does not bind. The doctor's
  `git()` helper passes `-c core.fsmonitor=false`.
- **Processes left running.** None, by reading:
  - the supervisor and MI controls kill every tracked group, escaped descendants included;
  - the prepared workers are killed in `finally`;
  - `git fetch`'s automatic maintenance has nothing to collect in a new shallow repository (Git's
    behaviour, not this repository's code).
- **Writes outside the bound trees** that the freeze may want to know about:
  - the `/usr/bin/git` dispatcher may keep a cache under `<tmp>`;
  - pip may write `.pyc` into U-30's `<tmp>` environment, as it installs itself there.
- **O-01.** On a step timeout, `stop_process` lets a Darwin `EPERM` escape.
  `test_local_checks.test_timeout_stops_child_and_retains_failure` exercises `stop_process` on a child.
- **R2.** The same starts are possible, but tests that fail early under the `/var` path make fewer
  starts. R2's counts are upper bounds.

## 9. Limits

- **Static reading.** No process was run, and no import was traced at run time. A computed import, an
  `exec` or `eval`, or Git's own process behaviour (DRV-05, U-28's Git reads) cannot be excluded or
  counted exactly by reading.
- **The closure model.** The import closures follow module-level statements and class bodies, and resolve
  Windows branches as on macOS. Function bodies are reviewed only on the executed paths named above.
- **Counts.** Exact Git counts per test are not given. Starts by name assume the freeze's `PATH`.
- **The framework's stdlib census** describes its state at this reading (2026-11-27). M0 observes it
  again.
