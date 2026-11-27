# MH tooling review 001

C271-P35, gate MH, stage S3. Reviewer: W3, in a fresh context, with no earlier review in it and no
part in W2's tooling. Written on 2026-11-27 (UTC) against the worktree at `c81cf07b` (branch
`work/c271-missing-import-digest-control`, read from the Git files without a Git start). Paths use
the labels `<worktree>`, `<local>` and `<prefix>`.

## Verdict

**REJECT_WITH_MANDATORY_FINDINGS.** There are five mandatory findings, TR-01 to TR-05, and thirteen
nonmandatory ones, TR-06 to TR-18.

The mandatory findings, in one line each:
- **TR-01.** Three tools refuse to run from their committed place against the worktree.
  `collect_outcomes.py` cannot run the cohort as its README launches it.
- **TR-02.** The direct-probe runner records a row as met even when the Darwin supervisor refused
  it. Examples are a remaining descendant, a staged-output violation and a deadline after exit.
- **TR-03.** The runner's file predicates can be met by a file that existed before the start.
  W2's own test asserts exactly that. A row's fixture bytes are not bound before the start either.
- **TR-04.** A test file meant for the public repository spells out the package manager's name,
  two parts of the account name, and the volume and folder names. Each is split into two string
  literals, and each is plainly readable.
- **TR-05.** The failure-capture procedure ends a recorded process group without first
  establishing that it is still the recorded process, so a reused PID could be signalled.

**What holds:**
- The digests are correct.
- Discovery is the unit stage's discovery, and on a verified copy of the worktree it reproduces
  W2's inventory exactly.
- The outcome collector never records a non-pass as a pass.
- The start counting follows P07 section 4.
- The numerical audit is independent and follows the probe's scientific body.
- The MC11 scan of the real files finds no process-creation name.
- MC10's one stated extra substitution (T-01) is acceptable.
- The focused tests pass again, with identical IDs and start counts.

## 1. Method

### 1.1 Digests

`SHA256SUMS.txt` lists 17 files, and all 17 match. `tooling/` holds no unlisted file, no link and
no bytecode (`digests.json`). The JSON record gives the SHA-256 of every reviewed file.

### 1.2 What I read

- **MH-PLAN.md:** all of it.
- **P07 QUALIFICATION-PLAN.md:** sections 2 to 8.
- **CONTRACT.md:** sections 7, 9 and 10.
- **The P33 interfaces:** all of W1-SUPERVISOR, W3-OBSERVER, W4-DRIVER and W5-PROVIDER.
- **CONTROLS-FROZEN.json:** F-01 to F-10, the MC09, MC10, MC11, MC29 rows and `mc11_rule`.
- **INVENTORY-ADDITIONS.json.**
- **N34-M-REVIEW.md:** N-04 and N-09.
- **W2's deliverables:** every file of `tooling/`, `AUTHOR-NOTES.md`, and summaries of every
  `dev-runs/` file.
- **Source:**
  - in full: `supervisor.py`, `supervisor_darwin_v01.py`, the 0.2.0 probe and
    `tests/test_static_tray_readback_v01.py`;
  - in part: the provider (lines 1–140 and 320–1322), the observer's host boundary, module and
    static checks (lines 1460–1520 and 2125–2325), and `tools/check_local.py` (lines 30–180,
    244–295 and 430–730);
  - by search: the controls module (for fixtures and MC37), the synthetic GLB builder of
    `tests/test_static_tray_reader_v01.py`, `canonical.json_bytes` and `format_check`'s
    constants;
  - from the reader tree: `tools/three_loader.mjs`, and the preamble of the validator's
    `gltf_validator.dart.js`;
  - from the framework: `unittest/case.py`, `subprocess.py` and `multiprocessing/util.py`.

### 1.3 What I ran

| Run | Through | Result |
| --- | --- | --- |
| `verify_digests.py` | my script, `-I -S -B` | 17 of 17 match |
| `inspect_devruns.py` | my script | W2's discoveries ran under 7 environment names, with no private value; W2's two MC11 scans differ only in timing |
| W2's `scan_mc11.py` on the real probe, reader tree and MP reader install plan (`ff5a95da…`) | `env -i` with the declared PATH, LANG, LC_ALL and TZ, then `-I -S -B` | exit 1, as expected without a reviewed list. `none_found` true; 587 dynamic hits, 23 call names, 52 specifiers. Content equal to W2's `mc11-dev-scan-2.json` (content digest `71c79a80…`) |
| `extended_scan.py` and `require_contexts.py` | my scripts | cross-check of routes that `scan_mc11.py` does not name (TR-11) |
| clone of the worktree's source directories into my directory, then `verify_copy.py` | APFS clone (`cp -c`); my script | 24,974 entries, equal paths, SHA-256 and modes; no link, no bytecode |
| W2's `discover_inventory.py discover`, run from W2's directory on the copy | `env -i` with 6 names (PATH, LANG, LC_ALL, TZ, a resolved TMPDIR inside my directory, PYTHONDONTWRITEBYTECODE=1), then `-B` | exit 0, `COMPLETE`. 5,994 IDs in 388 modules, no import failure, process event, duplicate or bytecode. Order digest `32b2b861…`, the same as W2's run. All 407 additions present; 5,994 − 407 = 5,587, the declared `base_count` |
| the same tool, copied to its committed path inside the copy and run from there with `--root` the copy | the same | **exit 2, `REFUSED`**: rule `PYTHON`, "A module of the root is already loaded", modules `["__main__"]` (TR-01) |
| copy removed; temporary directory removed (it stayed empty) | `rm -rf`, `rmdir` | |
| `analyze_discovery.py`, `compare_scans.py`, `privacy_scan.py`, `stdlib_bytecode_check.py` | my scripts | see TR-04, TR-17 and section 2 |
| W2's test suite, once, as in TEST-RUN.txt | `env -i` with 7 names (PATH, LANG, LC_ALL, TZ, TMPDIR in my directory, PYTHONDONTWRITEBYTECODE=1, MH_TOOLING_ROOT=`<worktree>`), then `-B -m unittest discover -s tests -v` from W2's `tooling/` | exit 0. 48 tests, all ok, in 4.92 s. The same 48 IDs as TEST-RUN.txt. Starts reported by the suite: `python -B` 75, `/bin/sh` 4, `/usr/bin/true` 2, which are TEST-RUN.txt's counts |
| after-checks | `find -newer` my first output | 0 new entries in `<worktree>` (`.venv` included) and in the framework tree; no `__pycache__` in the worktree or in W2's `tooling/` |

### 1.4 Starts

| Kind | Count |
| --- | ---: |
| Bash tool calls, one shell each, the two final ones (assembling the JSON, then checking it) included | 47 |
| Qualification interpreter, started by me with `-I -S -B` (my scripts and `-c` reads, and W2's `scan_mc11.py`) | 23 |
| Qualification interpreter with `-B` only: W2's discovery tool twice, which refuses `-I`/`-S` | 2 |
| Qualification interpreter with `-B` only: the one test rerun | 1 |
| Children of the test rerun: the interpreter with `-B` | 75 |
| Children of those children (started by the tools under test): `/bin/sh` and `/usr/bin/true` | 4 and 2 |
| Static-read and file utilities in those shells: `ls`, `head`, `grep`, `wc`, `cat`, `find`, `du`, `mount`, `stat`, `sed`, `cut`, `sort`, `uniq`, `tr`, `diff`, `tee`, `date`, `mkdir`, `cp`, `rm`, `rmdir`, `mv`, `readlink`, `dirname`, `shasum`, `env` (which `exec`s into the interpreter) | about 160 |
| **Node, Git, `ldd`, `codesign`, the observer's `observe`** | **0** |

- **What I wrote:** only my own directory. I made no Git start, no Git write and no edit in the
  worktree.
- **Interpreter starts:** each one carried `-B`, and the tests' children ran under
  `PYTHONDONTWRITEBYTECODE=1` too.
- **The worktree's identity:** I read `HEAD` and the branch ref from the Git files.

## 2. Answers

### Q1. Fitness

**Does each piece do what is required?** Each piece corresponds to its row in MH-PLAN section 4 and
to P07 sections 3 to 6, with these defects:
- the failure-capture procedure, TR-05 and TR-16;
- the discovery collector, TR-01 for the current inventory, TR-06 and TR-07;
- the outcome collector, TR-01, which blocks it, and TR-09;
- the direct-probe runner, TR-01, TR-02, TR-03 and TR-10;
- the numerical audit, TR-15;
- the MC11 scanner, TR-11 and TR-12;
- the control harness: it meets F-01, F-03 and F-04 within the limits of T-01 and T-02, and TR-06
  and TR-13 apply.

**Does any piece do more?**
- None is a general execution-plan runner:
  - the runner admits five fixed row IDs and two argv shapes;
  - the collector admits only the cohort module and the frozen controls module;
  - the harness has three fixed commands.
- None changes a test, the implementation, the contract, the amendment or a frozen control, and
  none redesigns the result protocol. The collector uses unittest's own loader, runner and result
  class.
- Two extensions go beyond the frozen definitions:
  - `scan_mc11.py`'s process-creation set is wider than MI's frozen `mc11_rule` (TR-12);
  - the optional `MC30-probe` row starts nothing unless the freeze adds it.

### Q2. `discover_inventory.py`

**The same discovery as the unit stage:**
- **The argv:** read by parsing `tools/check_local.py`, never by importing it. The tool requires
  `add("unit-tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"])`, line 449.
- **The options:** start directory `tests`, the default pattern `test*.py` and the implicit top
  level directory, so the IDs carry the prefix `test_static_tray_readback_v01.`.
- **The loader:** `unittest.TestLoader().discover`, the loader class that
  `unittest.main._do_discovery` uses.
- **The interpreter:** the root as cwd and `sys.path[0]`, the tool's own directory removed, `-B`
  required, and `-I`, `-S`, `-E` and `-P` refused.
- **The result:** 5,994 IDs, the same as W2's run (order digest `32b2b861…`).
- **Remaining differences,** none affecting the IDs on these files:
  - the environment is not frozen (TR-06);
  - `__main__` and `sys.argv` differ;
  - the root is the worktree or an export, not the driver's workspace copy, and the IDs do not
    depend on the path;
  - the `-B` that `build_plan` adds is asserted by the tool, not derived from `add` (TR-07).
- **Its own place:** run from its committed place with `--root <worktree>`, it refuses (TR-01).

**The comparison:**
- It is an exact set comparison, `expected = (baseline ∪ added) − removed`, and it reports
  `missing` and `extra`.
- It checks the additions record's internal counts.
- Duplicates are taken from each discovery document's own `duplicates` field, and are not
  recomputed. The baseline's duplicates are not checked at all (TR-07).

**Refusing process creation:**
- Sound for the audited events: `subprocess.Popen`, `os.posix_spawn`, `os.fork`, `os.forkpty`,
  `os.exec`, `os.spawn`, `os.system`.
- A refused start becomes a recorded event, usually also an import failure, and both make the
  discovery unclean, so MC28 cannot pass silently.
- It is blind to `_posixsubprocess.fork_exec`, which multiprocessing's default spawn method on
  macOS calls with no audit event (`multiprocessing/util.py` line 456), and to process creation
  through ctypes (TR-08).

### Q3. `collect_outcomes.py`

**Does it run the complete module unchanged?** Yes:
- `loadTestsFromNames(["tests.test_static_tray_readback_v01"])`, then `TextTestRunner` with
  verbosity 2 and the `"default"` warnings filter;
- a result subclass whose every method records and then calls the original;
- no patch, and a non-blocking audit hook;
- the root as cwd and `sys.path[0]`.

This is `python -B -m unittest -v tests.test_static_tray_readback_v01` from the root, so setup and
teardown see all three CPU cases.

**Does it keep every ID, outcome and class-level error?**
- It keeps every planned raw ID and its outcome, the tracebacks and subtests, and every
  class-level and module-level event under unittest's description, for example
  `setUpClass (tests.test_static_tray_readback_v01.ReadbackCPUControls)`.
- One exception: a skip raised inside a `subTest` is reported under the subtest's ID, which is
  not planned, so `outcomes.json` drops it. The journal keeps it, and the parent reads `unknown`
  (TR-09).

**Can a skip, an error or a missing method become a pass, or vanish?**
- None becomes a pass. `ALL_PASSED` needs every planned test `pass`, no class-level event, no
  loader error, no bytecode, an unchanged module, a complete run, and all seven required methods
  `pass`.
- A method that is not run reads `not_run`, and an absent one reads `missing`.

**The environment rule:**
- **The driver's qualifying unit rules (W4-DRIVER sections 2 and 4) are enforced:**
  - the 13 names of `UNIT_REMOVED_ENVIRONMENT` and every `DYLD_*` name are refused;
  - `PYTHONDONTWRITEBYTECODE=1` and `PYTHONNOUSERSITE=1` are required;
  - both selection variables are required;
  - the process environment must be exactly the frozen one, with `__CF_USER_TEXT_ENCODING`
    admitted and recorded.
- **Stricter than the driver.** The driver passes its ambient environment, minus `GIT_*`, plus its
  Git overrides. `git_read` applies `git_environment` to each Git start anyway, so the overrides
  reach every Git child either way.
- **The provider's `_check_python` (W5-PROVIDER section 3) is mirrored exactly:**
  `sys.executable == launcher == venv + "/bin/python"`, the implementation,
  `platform.python_version()`, `sys.version` and `proc_pidpath`.

**T-05** is right. I read `_check_python` (lines 534–562) and `_verify_host`: neither checks the
unit process's flags, loaded modules or own environment.

### Q4. `run_direct_probe.py`

**One start per row, through the real supervisor:** yes.
- One `run_process` call per row, with no retry.
- The four supervisor files are compiled from bytes checked against the supplied digests, and
  registered under their own names.
- `run_process` must come from the bound file, and `Clock`, `Stop` and `json_bytes` must be the
  originals.
- Any other loaded module of the root refuses. That same check refuses the tool itself in its
  committed place (TR-01).

**What it keeps:** everything asked.
- stdout and stderr: the supervisor's logs stay in the stage, and their bindings and text are in
  `outcome.json`;
- the exit status;
- the receipt, and whether `<label>.process.json` equals `json_bytes` of it;
- `started-<n>.json`.

**Counting, by P07 section 4:** it follows the rule.
- `PROVEN_ZERO` needs no audit event, no callback, no PID and no unexpected exception.
- `OBSERVED_ONE` needs one `subprocess.Popen` event, one callback, and a positive PID equal to the
  callback's and to the group.
- Anything else is `UNKNOWN`, with an observed lower bound. An unknown row stops every later row.

**Predicates:** insufficient.
- The supervisor's own refusal is ignored (TR-02).
- File predicates are not tied to the start, and fixtures are unbound (TR-03).
- Exact forms are missing (TR-10).

**T-03** is right. The environment binding (`verifyHost`, probe line 487) runs inside
`verifyBootstrap`, which the `try` block calls (line 719). The refusal therefore reaches
`probe.json` as `error.message` "Current-host binding: actual Node environment differs", with exit 1.

**Can it start Node for a row whose bindings fail?**
- Not when the Node executable, the probe or the loader differ: they are re-hashed before each
  start.
- Not when the supervisor files or the rows document differ.
- Yes when a row's own fixtures differ: the job, configuration, manifest, HOST copy, GLB and
  reference are not bound by the runner at all (TR-03).

### Q5. `audit_numeric.py`

**Independence.** It imports only the standard library, and I compared it with the probe's lines
749–821 and the test's lines 119–161 directly.

**The row inventory, by the probe's definitions:**
- for every node, 16 matrix terms;
- for a node whose reference is truthy in JavaScript's sense, per vertex and axis a world-position
  row and then a normal row (the probe's order), and then the minimum, maximum and size per axis.

That is 12 × 169 + 2 × 16 = 2,060 rows per case.

**Each row's values:**
- **The difference:** `abs(actual − expected)`.
- **The threshold:** 5e-6 for the terms `[0..2][3]` and for every position and bound row; 1e-6 for
  the other matrix terms and the normals.
- **The decision:** both values finite and `difference ≤ threshold`, as in the probe.
- The reported rows must equal the recomputation exactly, with nothing missing, extra, duplicated
  or out of order.

**The decisions:**
- **Q01 and Q03:** must pass every row, with no finding.
- **The negative:** exactly one failed row and one finding, at `equipment-tray/pair/left/base`
  `matrix_0_3`, with threshold 5e-6 and |difference − 0.001| ≤ 1e-9. Its exact comparisons must
  pass, and there must be no `error` member.
- **The negative's fixture:** a GLB byte-identical to Q01's, and a reference equal to Q01's except
  at that term, which must equal Q01's + 0.001 exactly (as check_case line 129 makes it), and in
  the fixed scope text.

**Where the order differs:**
- **Nodes.** The probe walks the imported IDs in JavaScript sort order and skips any ID without a
  reference; the audit walks the reference's IDs. For these 14 ASCII IDs, equal sets give the same
  order.
- **Vertices.** The probe counts the imported vertices, the audit the reference's. A mismatch
  shows as missing or extra rows, which fails closed.

**Not recomputed:** `world_bounds` and `world_vertices` are taken as the probe retained them
(TR-15).

**T-10's 1e-9 bound is sound for these fixtures.**
- Q01's transforms are exact JSON doubles, with identity rotations (`synthetic`, lines 163–177).
- The positive difference at that term is therefore expected at rounding level, and so is the
  negative's deviation from 0.001. This is not observed, since no Node run was made.
- 1e-9 lies about five orders of magnitude below the 5e-6 threshold and far above rounding.
- It is the harness's own bound, since P07 states none, and it fails closed.

### Q6. `scan_mc11.py`

**Coverage of the routes asked about:**

| Route | Found? |
| --- | --- |
| `node:child_process` | yes, a substring match in any letter case |
| string-built names on one line | yes, through the decoded and joined views |
| computed specifiers | yes, as `require-computed` or `import-computed` |
| `process['binding']` | in the raw text only: the pattern is excluded from the decoded and joined views |
| `module.constructor._load` | dot forms only |
| `process.mainModule` | dot form only |
| `globalThis.process` | only when `.binding` or `dlopen` follows |
| `worker_threads` | yes |
| `cluster` | yes, as a name |
| `process.dlopen` | yes, through `dlopen` |
| `createRequire` | yes |
| `process.execve` | yes |
| `wasi` | no, but WASI cannot create a process |

**Gaps:**
- the binding names `spawn_sync` and `process_wrap`;
- bracket spellings;
- receiver-qualified or parenthesized calls, such as `self.require(x)`, `(c ? a : require)(x)` and
  `require.call` (TR-11).

**On the real files:**
- My cross-check found no binding name, no bracket form, and no `Function` or `eval` call.
- It found one call shape that the scanner misses: the validator's preamble calls
  `(…?__non_webpack_require__:require)("url")`. So "url" is absent from the validator's specifier
  list, and the preamble also sets `self.require=require`. The MC11 reviewer must add and review
  both (TR-11).

**Links and the inventory:** sound.
- The tree must be exactly the inventory's 24 regular files, with no link, no special file and no
  `.DS_Store`.
- Each file is read with `O_NOFOLLOW` and stable identity, and compared with its SHA-256, size and
  mode.
- The inventory is bound by its digest, and must be `dependencies/0.2.0`, or `install/0.2.0` with
  purpose `retained-dependencies`.
- Directories and hard links are not compared, which does not matter for a scan.

**The module loader** is identified correctly as `tools/three_loader.mjs`, one of the 24 files. The
provider's manifest, the probe's roles and the frozen `mc11_rule` name it the same way. It is 10
lines, maps `three`, `three/webgpu` and `three/tsl`, and creates nothing.

### Q7. `control_harness.py`

**T-01 is acceptable as a stated substitution, labelled mocked, so MC10 need not stay NOT_RUN.**
- **Its scope.** The exclusion removes one row: `__main__`, with a realpath equal to the running
  harness file. Every other loaded module is checked by the real `check_loaded_modules`.
- **The harness's imports.** Its own imports are standard-library files of the framework
  inventory, and its project modules are loaded from bound source files without bytecode.
- **What MC10 tests is unchanged:** M1's output predicate leading to failed preparation and no HOST.
- **Narrower than MI.** MI substituted all of M0's static facts.
- **Conditions:**
  - the freeze states both substitutions in MC10's row;
  - the harness is bound by path, SHA-256, size and mode;
  - the output shows exactly that one excluded row;
  - a test exercises the exclusion (TR-13), since today's tests refuse at `SOURCE` before
    `check_loaded_modules` runs.

**T-02's coverage claim is right.**
- The configuration and job-input changes are real, and every detector of the provider runs as its
  own: 17 functions are checked as plain provider functions before and after the run.
- The source, runtime, dependency and OS-build cases stay simulated or NOT_RUN.
- One nuance: a real source change would be possible in a derived workspace copy, which the
  provider supports through `parent`, without editing the worktree. It needs the driver's Git
  workspace preparation, so its exclusion is a cost decision, not an impossibility (TR-14).

**The recorder supervisor cannot let a real start through.**
- It raises before doing anything.
- It is patched for the whole flow: setup, the attempt and the accounting.
- The provider resolves `supervisor_darwin_v01.run_process` at call time.
- A missed detection reaches the recorder and fails `zero_supervisor_calls`.
- The only real starts in `mc29` are the provider's bound Git reads.

**`host-state` is right,** and so is T-08:
- the provider's real `host_state` is compared with HOST by the provider's own `_check_state`;
- nothing is substituted, process creation is refused, and the boundary must read `real` before
  and after;
- the cohort's `setup.json` `boot` and every ledger's `boot_before` and `boot_after` are the same
  real reads, provided the cohort's `labels.boundary` is `real`.

### Q8. `FAILURE-CAPTURE.md`

- **Coverage.** It is complete for refused, failed and unknown outcomes. Unknown includes a missing
  final record, disagreeing records, a null or bounded count, a started record without a receipt,
  and a receipt without cleanup proof. It keeps every record, partial ones included.
- **No retry:** FC-R1 to FC-R5.
- **Absence** is established soundly: only `ESRCH` from `kill` or `killpg` on a recorded identity,
  never by name. `EPERM` counts as present, and the descendant limit is stated.
- **Presence is weak.** FC-P3's start-time comparison names no source of the kernel's start time
  and no comparable recorded time. FC-P6 then signals the recorded group (TR-05).
- **The probe's code** is described, not fixed (TR-16).

### Q9. Safety and privacy

**Starts:**
- **Node** starts only from the runner's frozen rows, through the supervisor, and from the cohort
  module's provider.
- **Git** starts only as the provider's HOST-bound reads: about 60 in a cohort, and about 15 or 25
  in an `mc29` run. I verified both counts in the code.
- **T-07 is right about them.** The hooks record them, and each has `git_read`'s timeout of at
  most 5 s. They are not supervised and not counted, and MH-PLAN section 7 lists them neither as
  bounded starts nor as uncounted ones (TR-14).
- **`ldd` and `codesign`** are never started.
- **Discovery, `mc10` and `host-state`** refuse process creation, within TR-08's limit.

**Writes outside the output paths:** only by design:
- the supervisor's files in the frozen stages;
- the provider's evidence under the configuration's evidence root;
- the observer's attempt for `mc10`;
- `mc29`'s stage inputs, and its one change to the configuration or the GLB.

**Bytecode:** `-B` is enforced by discovery, the collector, the runner and the harness. It is not
enforced by `scan_mc11.py`, `audit_numeric.py` or `compare`, although every module they import
already has cached bytecode (TR-17).

**Private strings in `tooling/`:** one file, `tests/test_zz_hygiene.py` (TR-04). No other file has
a machine path, the account name or the package manager's name, plain or split.

**Environment values in outputs:**
- the collector, the runner and `mc10` admit only the declared or frozen variables, plus the
  recorded `__CF_USER_TEXT_ENCODING`;
- `discover` and `mc29` record whatever environment they are given, and the audit hooks record
  every child's environment values (TR-06);
- W2's own development runs used a 7-name environment with no private value.

### Q10. Tests

**The rerun matches TEST-RUN.txt.** It ran once: 48 of 48 ok, the same IDs, and the same start
counts (75 / 4 / 2). It left no new file and no bytecode.

**The tests do not cover the risks above (TR-18):**
- the in-place layout;
- a supervisor `Stop` other than the exit-status one;
- an interrupted direct-probe row;
- MC10's exclusion;
- `mc29` with the real detectors, which needs S6's inputs.

One test asserts the stale-file behaviour as correct (TR-03).

## 3. Findings

### TR-01 (mandatory): three tools refuse to run from their committed place

- **Location.**
  - `discover_inventory.py` lines 354–358;
  - `collect_outcomes.py` lines 635–639;
  - `run_direct_probe.py` lines 374–380;
  - README lines 74–76 and 155–157, and the docstrings' launch lines.
- **Issue.** Each tool refuses when any module of `--root` is already loaded. The tool itself is
  `sys.modules["__main__"]`, and its `__file__` lies under the root once the tooling sits at
  `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/` and `--root` is the
  worktree.
- **Evidence.** I ran `discover_inventory.py` from that path inside a verified copy, with `--root`
  the copy. It returned exit 2 and `REFUSED`, with rule `PYTHON` and modules `["__main__"]`
  (`discovery-inplace-w3.json`). The collector and the runner contain the same check.
- **Effect.**
  - The collector cannot run the cohort as its README launches it. The provider's root must be the
    worktree, so `--root` must be too.
  - The runner refuses with `--root <worktree>`.
  - The discovery of the current inventory refuses with `--root <worktree>`.
  - All three fail closed, but S7 would stop. A byte-identical copy outside the worktree would
    avoid this, but that is an unstated change of the tool's path, against P07 section 3's rule
    that a tool is source-inventoried before use.
- **Required change.**
  - Admit exactly the running tool's own `__main__`, identified by realpath equality with its
    `__file__`, as `control_harness.py`'s `mc10` already does.
  - Record that it was admitted, and keep refusing every other preloaded root module.
  - Add a test that runs each tool from inside a root.

### TR-02 (mandatory): the runner ignores the supervisor's own refusal

- **Location.** `run_direct_probe.py` lines 510–519, 545–551 and 570–573;
  `supervisor_darwin_v01.py` lines 188–206.
- **Issue.** `expectation_met` checks the exit status, substrings and paths, but not
  `supervisor_failure` or the receipt's `error`.
- **What the supervisor raises after a child exits,** each with the child's real `returncode` and
  usually with a passed cleanup:
  - "Child exited while an owned descendant remained";
  - a staged-output `Stop` from `inventory`, for a link, a non-private file, the byte ceilings or
    2,048 entries;
  - a deadline `Stop` after exit;
  - "Captured output exceeded the fixed log ceiling";
  - a `KeyboardInterrupt` converted to a `Stop`.
- **Effect.** A probe row that exits 1 with the expected stderr text, or a syntax check that exits
  0, is then `COMPLETED` and met although the supervisor refused it. That is a failed run shown
  as a pass. The case most relevant to MC11 is a descendant.
- **Required change.**
  - Add the expected supervisor error to the row: exactly
    `{"code": "OTRAY-E-BACKEND", "reason": "Child exited with status N", "state": "REJECTED"}`
    for an expected status N ≠ 0, and `null` for 0.
  - Require equality, both for the raised `Stop` and for the receipt's `error`.
  - Add tests with a stand-in that leaves a descendant, and with a staged link.

### TR-03 (mandatory): file predicates are not tied to the start, and fixtures are not bound

- **Location.** `run_direct_probe.py` lines 408 and 449–452 (only the supervisor's three outputs
  must be absent), and 561–569 (`present_paths` and `file_includes` are read after the run).
  Probe lines 644–645. `tests/test_run_direct_probe.py` lines 93–107.
- **Issue.**
  - A `file_includes` or `present_paths` target that exists before the start satisfies the
    predicate.
  - If MC36's stage already holds a `probe.json`, the probe refuses at `approvedEnvelope` with
    "job paths, case, output freshness or actual stage differ" on stderr, with exit 1. The stale
    file then still contains "actual Node environment differs", and the row is met.
  - W2's test writes a `probe.json` before the run, and asserts that the row is met from it.
- **The fixtures.** The rows schema carries no input descriptors, as P07 section 3 item 7 asks. So
  a Node start can be made on job, configuration, manifest, HOST-copy, GLB or reference bytes that
  differ from the freeze.
- **Required change.**
  - Require every `file_includes` and `present_paths` target to be absent at intent, and record
    that.
  - Add to each row the frozen input descriptors (path, SHA-256, size, mode) and the exact set of
    the stage's entries.
  - Verify both immediately before the start, as Node, the probe and the loader are verified.
  - Change the test so that a pre-existing file refuses the row before any start.

### TR-04 (mandatory): private strings in a public test file

- **Location.** `tests/test_zz_hygiene.py` lines 19–21.
- **Issue.** The `FORBIDDEN` tuple holds, each split into two literals so that the test does not
  match itself:
  - the package manager's name;
  - two parts of the account name;
  - the external volume's name and the folder name.

  They are plainly readable, and everything in `tooling/` is meant for the public repository. My
  scan found no other such string anywhere in `tooling/` (`privacy-scan-w3.json`).
- **Required change.** Derive the forbidden strings at run time, for example:
  - from `os.path.expanduser("~")` and `pwd.getpwuid(os.getuid()).pw_name`;
  - from the path components of the tooling directory;
  - from `sys.base_prefix`'s ancestors.

  Commit no literal of them.

### TR-05 (mandatory): FC-P6 signals without establishing identity

- **Location.** `FAILURE-CAPTURE.md` FC-P3 (lines 97–105) and FC-P6 (lines 112–114).
- **Issue.**
  - FC-P6 has the Director end a process that is "still present" through its recorded group, with
    SIGTERM and then SIGKILL.
  - Presence is a successful or `EPERM` probe of a recorded PID or group. After the recorded child
    has exited and been reaped, its PID can be reused. If the new holder is a group leader of the
    same user, `killpg` reaches an unrelated process group.
  - FC-P3's start-time rule names no way to read the start time. The records hold the parent's
    `start_monotonic` and UTC times of the callbacks, not the kernel's start time.
- **Required change.**
  - Before any signal, establish identity: the kernel's start time (`proc_pidinfo`,
    `PROC_PIDTBSDINFO`) within the window between intent and the started record, and the image
    from `proc_pidpath` equal to the recorded `argv[0]`.
  - Otherwise send nothing. Record "present, identity not established", and keep the outcome
    unknown.
  - The procedure is bound at S4, so this must change before commit C.

### TR-06 (nonmandatory): ambient environments are recorded

- `discover` writes `dict(os.environ)` (line 359) and enforces no environment.
- `mc29` writes `dict(os.environ)` (line 602) and checks only the selection pair (line 593).
- Every tool's audit hook writes each child's full environment values. In `mc29`, each Git child
  inherits the harness's whole environment.
- Launched as the README shows for discovery, without `env -i`, the session's whole environment
  would enter the evidence.
- **Recommendation.**
  - Enforce an exact frozen environment, as the collector does, or record names only.
  - In S6, launch both under `env -i`.
  - Leave `HOME` out of frozen environments, since the collector writes the observed environment
    into `outcomes.json`.

### TR-07 (nonmandatory): the comparison trusts the discovery documents' own fields

- `compare` takes `duplicates` and the counts from each document (lines 427–438 and 472–478). It
  neither recomputes them from `ids_in_discovery_order` nor checks the baseline's duplicates or
  `state`.
- `interpreter_flags_added_by_build_plan: ["-B"]` (line 283) is asserted, not derived from
  `build_plan`'s `add` (`check_local.py` lines 441–444).
- **Recommendation.** Recompute both from the IDs, and derive the flag from the AST.

### TR-08 (nonmandatory): the audit hook's blind spots are not stated

- `_posixsubprocess.fork_exec`, which multiprocessing's spawn and forkserver start methods call,
  and calls through ctypes raise none of the seven listed events.
- **Recommendation.**
  - State this limit in the README and FAILURE-CAPTURE.
  - Optionally record `ctypes.dlsym` events for `fork`, `vfork`, `posix_spawn`, `execve` and
    `system`.

### TR-09 (nonmandatory): collector details

- **A skip inside a `subTest`** is keyed by the subtest's ID (lines 558–560, unittest `case.py`
  line 63). It is absent from `outcomes.json`, and the parent reads `unknown`. Keep unplanned
  events in `outcomes.json`, by name.
- **`--module-sha256`** is optional (line 630). Make it required in both modes.
- **The body digests** are computed but not compared with `ORIGINAL_BODIES`. Compare them, or
  state that the audit does.
- **Ambient `GIT_*` names** in a frozen environment are not refused, although the driver strips
  them.

### TR-10 (nonmandatory): runner details

- No `kern.bootsessionuuid` is read before and after each row. The plan binds one boot, so record
  it.
- No exact or negative predicate exists, such as stdout empty, `probe.json` `passed: false`, or no
  `khronos` member. They would let P06-H01, P06-H02 and MC36 be stated exactly.
- Two rows may share a stage.
- `json_bytes_is_the_original` lacks `is not None` (line 373).
- MC36's dependence on MC30-probe can be expressed only by order with `rows_independent: false`.
  S6 must use that.

### TR-11 (nonmandatory): MC11 scan coverage, with one concrete miss on the real files

- **The gaps:**
  - `process.binding` is excluded from the decoded and joined views (line 70);
  - no search for `spawn_sync` or `process_wrap`;
  - module-loading patterns match dot forms only;
  - `CALLS` skips receiver-qualified and parenthesized calls (lines 79–82).
- **On the real files:** the validator preamble's `(…:require)("url")` is not listed among its
  specifiers (the list is empty), and `self.require=require` exposes `require` to the Dart code.
  `require-contexts-w3.json` lists every `require` and `import(` occurrence.
- **Recommendation.**
  - Apply every pattern to every view.
  - Add the binding names and the bracket forms.
  - Flag any `require` that is neither a plain call nor a declaration.
  - The reviewer adds "url" and reviews the preamble.

### TR-12 (nonmandatory): the scanner's verdict is not the frozen rule's, and an unreviewed list passes

- **A wider verdict.** `none_found` counts five more process-creation patterns than MI's
  `mc11_rule` (CONTROLS-FROZEN lines 5248–5256), with case-insensitive matching and transformed
  views. Report the frozen rule's verdict separately, so that MC11 is decided as frozen.
- **The reviewed list's status.** `load_reviewed` (lines 546–551) ignores the list's `status`.
  W2's candidate list, whose status reads "CANDIDATE, NOT REVIEWED", would make MC11 exit 0.
  Require a reviewed status and a reviewer identity.

### TR-13 (nonmandatory): the mc10 exclusion is untested, and the attempt listing follows links

- The synthetic plans of `test_control_harness.py` (lines 158–170) refuse at `check_source`. That
  is before `_python_static` calls `check_loaded_modules` (observer lines 2248–2249 and 2228). Add
  a test that reaches `PYTHON-MODULE` both with and without the exclusion.
- `attempt_listing` opens files without `O_NOFOLLOW` (lines 462–472).

### TR-14 (nonmandatory): obligations for S6 from T-02, T-07 and T-11

- **Start accounting.** List the provider's Git reads as recorded, unbounded starts: about 60 in
  the cohort, and about 15 or 25 per `mc29` case.
- **MC29's scope.** State it: configuration and job-input real. The source case is possible only
  through a derived workspace, and the others stay simulated or NOT_RUN.
- **`mc29` configurations.** Give each `mc29` case its own configuration copy at its own path. The
  harness cannot tell a copy from the cohort's configuration, and it appends to the file it is
  given.

### TR-15 (nonmandatory): retained bounds and vertices are not recomputed

- `actual_value` (lines 332–347) takes `world_bounds` and `world_vertices` as retained.
- **Recommendation.** Recompute the bounds from the retained vertices, and optionally the vertices
  from `positions` and `world_matrix` with Three.js's `applyMatrix4` order. The audit would then
  not depend on the probe's bounds code.
- Keep T-10's bound, or derive it from Q01's own difference at the same row.

### TR-16 (nonmandatory): parts of the procedure are not fixed

- FC-P3's probe is described but its code is not fixed. Bind its exact text, or a file.
- FC-K5 does not say which process computes the listing's digests.

### TR-17 (nonmandatory): three entry points do not require `-B`

- `scan_mc11.py`, `audit_numeric.py` and `discover_inventory.py compare` accept a start without
  `-B`.
- Observed: all 45 framework modules that they import have cached bytecode or are frozen, so no
  write would occur today (`stdlib-bytecode-check.json`).
- **Recommendation.** Refuse, as N-09 asks of every start.

### TR-18 (nonmandatory): test coverage

**Missing:**
- the in-place layout;
- a non-exit-status supervisor `Stop`;
- an interruption after a start in the runner;
- MC10's exclusion;
- the subtest skip;
- a duplicate inside a baseline.

**To change.** `test_a_nonzero_exit_is_kept_raw_and_an_unmet_row_stops_the_later_rows` asserts the
TR-03 behaviour, so change it with the fix. Each mandatory fix should come with a test that fails
on today's code.

## 4. W2's findings T-01 to T-11

| ID | View |
| --- | --- |
| T-01 | Agreed, and acceptable under the conditions of Q7. MC10 can run, labelled mocked; it need not stay NOT_RUN. Add the missing test (TR-13). |
| T-02 | Agreed, with one nuance: a derived workspace would make a real source change possible without an edit in the worktree (TR-14). The runtime, dependency and OS-build reasons hold. |
| T-03 | Agreed: verified in the probe, lines 487, 713–719 and 830–834. |
| T-04 | Agreed: the positive starts cannot tell absence from HOST's value. The MC30-probe design discriminates presence, and both refusals come before any reader import (lines 487 and 720–722). The value then follows by elimination, assuming the same environment in every start. It adds a ninth Node start, and MC36 must be ordered after it, with `rows_independent: false`. |
| T-05 | Agreed: verified (Q3). |
| T-06 | Consistent with my run. With `docs/`, the copy gave no import failure. |
| T-07 | Agreed. The counts are verified: 5 reads per selection check; 12 checks per cohort; 15 or 25 in `mc29`. Recorded, with at most 5 s each, not supervised. S6 must list them (TR-14). |
| T-08 | Agreed (Q7). |
| T-09 | The deviations are recorded properly. The possible refresh of the index by `git status` cannot be checked now, because the index was rewritten at 23:53:39Z by the Director's commit. Since my first output, the framework tree, the venv and the worktree show no new entry. |
| T-10 | Sound for these fixtures, and fail-closed. It is a declared bound, not P07's (Q5 and TR-15). |
| T-11 | Agreed. Note also that the harness cannot detect being given the cohort's own configuration (TR-14). |

**On W2's list of S6 decisions:**
- **Item 5:** do not put `HOME` in the frozen environment, for the reason in TR-06.
- **Item 6:** add the supervisor-error and input-descriptor fields of TR-02 and TR-03.
- **Item 7:** use a reviewed list with a reviewer identity, and add the validator's "url"
  specifier (TR-11 and TR-12).

## 5. Files in `<local>/c271-p35/workers/W3-tooling-001/`

**The reports:**
- `TOOLING-REVIEW-001.md` and `TOOLING-REVIEW-001.json`.

**My scripts:**
- `verify_digests.py`, `inspect_devruns.py`, `extended_scan.py`, `require_contexts.py`;
- `verify_copy.py`, `analyze_discovery.py`, `compare_scans.py`, `privacy_scan.py`;
- `stdlib_bytecode_check.py`, `assemble_review_json.py`.

**Their outputs:**
- `digests.json`, `devruns-summary.json`, `extended-scan-w3.json`, `require-contexts-w3.json`;
- `copy-verification.json`, `discovery-analysis.json`, `mc11-scan-comparison.json`;
- `privacy-scan-w3.json`, `privacy-scan-w3-coarse.json` (a first, over-broad pass), and
  `stdlib-bytecode-check.json`.

**The outputs of W2's tools that I ran:**
- `mc11-scan-w3.json`;
- `discovery-copy-w3.json`;
- `discovery-inplace-w3.json` and `discovery-inplace-w3.stderr.txt`;
- `test-rerun-output.txt`, `test-rerun-exit.txt` and `test-rerun-start-utc.txt`.

**Local only.** These raw tool outputs contain machine paths. They are local evidence, not public
copies.
