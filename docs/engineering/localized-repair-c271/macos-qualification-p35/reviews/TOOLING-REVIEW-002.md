# MH tooling review 002

C271-P35, gate MH, stage S3. Reviewer: W3, in a fresh context. I wrote none of the tooling and took
no part in review 001, which I read only as a document. Written on 2026-11-27 (UTC) against the
worktree at `c81cf07b` (branch `work/c271-missing-import-digest-control`, read from the Git files
without a Git start). Paths use the labels `<worktree>`, `<local>` and `<prefix>`.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** The revised tooling may become commit C. There is no
mandatory finding. The six nonmandatory findings, TR2-01 to TR2-06, may be carried to the S6
freeze.

**What holds:**
- Every mandatory finding of review 001 is met by the code itself. Each one's named tests fail on a
  copy of `rejected-001` for the defect's reason (section 2, A). Every adopted nonmandatory finding
  is met, and TR-14 is unchanged, as carried to S6.
- `capture_probe.py`'s identity rule is sound, and its `ctypes` declarations match
  `struct proc_bsdinfo` on this host. Every path that cannot establish identity sends nothing.
- `discover_inventory.py`, run from its committed place inside a verified clone of the worktree's
  sources, admits its own `__main__` and completes. It finds 5,994 IDs in 388 modules, in the same
  order as W2's and review 001's runs (`32b2b861…`). All 407 additions are present, and
  5,994 − 407 = 5,587.
- On the real files, the MC11 scan finds no process-creation name under the frozen rule or the wider
  scan, and it now lists the validator's `"url"` specifier.
- W2's suite passes again: 91 of 91, with the same IDs and start counts as `TEST-RUN.txt`.
- No file of `tooling/` holds a machine path, the account name, a personal name, an e-mail address or
  the package manager's name, whether plain, split or reversed.

**The nonmandatory findings, one line each:**
- **TR2-01.** The runner records an interruption before a row's start as `ROWS_UNMET`, not
  `UNKNOWN`.
- **TR2-02.** Two sub-checks that the record lists against `rejected-001` fail there for a renamed
  rule or a new field, not for the defect.
- **TR2-03.** Neither MC11 verdict flags two dynamic routes: `.constructor` and computed members of
  the global objects. On the real files both are inert.
- **TR2-04.** `capture_probe.py` silently omits unreadable directories, and reads no facts of an
  exited, unreaped process.
- **TR2-05.** Each tool's `-B` refusal comes after its module-level imports, so it cannot prevent a
  write. None occurs today.
- **TR2-06.** In MC29's configuration case, the accounting refusal comes from the facade's 0.1.0 code
  (F-07).

## 1. Method

### 1.1 Digests and the fixed state

- **W2's delivery.**
  - `SHA256SUMS.txt` lists the 20 files of `tooling/`, and all 20 match. `tooling/` holds no unlisted
    file, no link and no bytecode.
  - `rejected-001/SHA256SUMS.txt` matches its 17 files under `rejected-001/tooling/`.
  - Those 17 files and `rejected-001/AUTHOR-NOTES.md` equal the digests that
    `TOOLING-REVIEW-001.json` records for the reviewed first version.
- **The worktree.**
  - The 23 worktree files that review 001 recorded have the same digests now.
  - HEAD is `c81cf07b5386ea7eba7904f3ef5700709b84b366`, read from the Git files.
  - Compared with the index's 22,451 entries, no file is modified or deleted. Outside `.venv/` no file
    is untracked, and nowhere is there a `__pycache__` or a `.pyc`.
  - A snapshot of all 22,751 files (`.venv` included) has the same paths, sizes and modification
    times before my first run, after my last run and at the end.
- **The framework.** Its 414 bytecode files were unchanged throughout.
- **W2's directory.** All 55 entries are unchanged in size, digest and modification time.
- **The reader tree.** Its 24 files equal MP's reader install plan (`ff5a95da…`, purpose
  `retained-dependencies`).

The JSON record gives the SHA-256 of every reviewed file.

### 1.2 What I read

- **MH-PLAN.md:** all of it.
- **P07 QUALIFICATION-PLAN.md:** sections 2 to 8.
- **CONTRACT.md:** sections 7, 9 and 10, and section 5 for the lifecycle meanings.
- **The P33 interfaces:** all of W1-SUPERVISOR, W3-OBSERVER, W4-DRIVER and W5-PROVIDER.
- **CONTROLS-FROZEN.json:** findings F-01 to F-10, the MC10 and MC11 rows, and `mc11_rule`.
- **INVENTORY-ADDITIONS.json:** its header.
- **N34-M-REVIEW.md:** N-04 and N-09.
- **W2's records:**
  - every file of `tooling/`, in full;
  - `AUTHOR-NOTES.md`;
  - `TEST-RUN.txt`;
  - `TEST-RUN-AGAINST-REJECTED-001.txt`: its header, and the failures of the TR-01 to TR-05 tests and
    of the hygiene test.
- **Review 001 and disposition 001:** both, in full.
- **Source:**
  - in full: `supervisor.py`, `supervisor_darwin_v01.py` and `tests/test_static_tray_readback_v01.py`;
  - the probe: its constants and helpers (lines 25–74 and 118–125), `environmentAdmitted`,
    `approvedEnvelope`, the head of `verifyBootstrap`, and the scientific body and report (700–835);
  - the provider: `_check_python`, the boundary helpers, `_verify_source`'s Git reads,
    `_verify_methods` and `guarded_run_process`;
  - the observer: `loaded_module_files`, `check_loaded_modules`, `Host`, and the command's intent and
    started publication;
  - MI's `scan_javascript`;
  - `tools/check_local.py`: `UNIT_REMOVED_ENVIRONMENT`, `git_environment`, `build_plan` and
    `execute_step`.
- **The reader tree:** `tools/three_loader.mjs` in full, and the context of every construct that my
  cross-check flagged in `three.webgpu.js` and in the validator.

### 1.3 What I ran

Every interpreter start carried `-B`. Each of my own scripts ran as `<worktree>/.venv/bin/python -I -S -B`.

| Run | Result |
| --- | --- |
| `w3_inventory.py`, `w3_digests.py` | the digests of section 1.1 |
| `w3_wt_state.py`, three times (before, after, final) | HEAD and cleanliness from the Git files; snapshots unchanged |
| `w3_proc_check.py`, three times | see B; no process of mine left |
| `w3_privacy_scan.py`, on `tooling/` and on my own files | see E |
| `w3_bytecode_and_scan_checks.py`, `w3_contexts.py` | see TR2-03 and TR2-05 |
| W2's suite, once, as `TEST-RUN.txt` shows: from W2's `tooling/`, `env -i PATH LANG TMPDIR MH_TOOLING_ROOT=<worktree>`, then `-B -m unittest discover -s tests -v`; `TMPDIR` a resolved directory of mine | exit 0. 91 of 91 ok in 13.7 s, with the same 91 IDs. Starts: 135 of the interpreter with `-B` and 1 of `/usr/bin/true`; through the tools, 4 of `/bin/sh`, 3 of `/usr/bin/true`, 7 stand-ins and 1 fork. These are `TEST-RUN.txt`'s counts. |
| A copy of `rejected-001`, made with `cp -pR` and checked 17 of 17. Then one focused rerun of 22 tests from W2's `tests/` with `MH_TOOLING_UNDER_TEST` set to the copy: every TR-01 to TR-05 test, and the start report | exit 1, with 18 failures (subtests counted) and 9 errors, each for the reason in A. The copy was removed afterwards. |
| W2's `scan_mc11.py` on the real probe, the reader tree and MP's install plan. Launched under `env -i` with PATH, LANG, LC_ALL and TZ, then `-I -S -B`, with no reviewed list | exit 1, as expected without a list. The frozen rule finds no process-creation name and 587 dynamic hits awaiting review. The wider scan finds no hit, with 628 dynamic hits, 23 call names, 53 specifiers and 0 unresolved. It equals W2's `mc11-dev-scan-3-revised.json`, apart from paths, timing and invocation. |
| An APFS clone (`cp -cR`) of every top-level entry of the worktree except `.git` and `.venv`. 22,451 files equal in path, size, mode and SHA-256. Then W2's `tooling/` copied to its committed place inside the clone | |
| W2's `discover_inventory.py discover`, from that committed place, with `--root` the clone. Launched under `env -i` with a 6-name frozen environment (no HOME), then `-B` | exit 0, `COMPLETE`, `own_main_admitted` the in-place copy. 5,994 IDs in 388 modules, with no import failure, process event, duplicate, loader error or bytecode, and the same order as W2's run. The tooling's own tests were not discovered. The clone was removed. |
| `w3_discovery_helpers.py` | the environment file, the copy check, the analyses and comparisons |
| `w3_assemble_review_json.py`, twice: the second time after this report's last edit | `TOOLING-REVIEW-002.json` |

### 1.4 Starts

| Kind | Count |
| --- | ---: |
| Bash tool calls, one shell each. The last four assemble the JSON and scan this report, the JSON and my scripts, and then do both again after this report's last edit | 39 |
| Qualification interpreter, started by me with `-I -S -B`: my scripts, my `-c` reads, and W2's `scan_mc11.py` | 33 |
| Qualification interpreter, started by me with `-B` only: W2's suite, the focused rerun, and W2's `discover_inventory.py`, which refuses `-I` and `-S` | 3 |
| Children of the suite rerun: the interpreter with `-B`, and `/usr/bin/true` | 135 and 1 |
| Started by the tools under test in the suite rerun: `/bin/sh`, `/usr/bin/true`, stand-ins (the interpreter with `-B`) and forks | 4, 3, 7 and 1 |
| Children of the focused rerun: the interpreter with `-B`, and `/usr/bin/true` | 37 and 1 |
| Started by the rejected tools in the focused rerun: `/bin/sh`, `/usr/bin/true`, stand-ins and forks | 1, 6, 5 and 1 |
| Static-read and file utilities in those shells: `date`, `grep`, `head`, `tail`, `wc`, `sed`, `cut`, `sort`, `uniq`, `tr`, `awk`, `du`, `find`, `ls`, `cat`, `mount`, `mkdir`, `cp`, `rm`, `rmdir`, `tee`, `env` (which `exec`s into the interpreter) | 140 |
| Commands that failed before running: one shell did not split a command variable, so five interpreter commands never ran | 5, none ran |
| **Node, Git, `ldd`, `codesign`, the observer's `observe`** | **0** |

- **No process of mine remained.** At the end, the only processes still alive that had started after
  my first command, and had the image of the interpreter, `/bin/sh`, `/usr/bin/true`, `/usr/bin/env`,
  Node or Git, were these:
  - two Node processes of another parent, which is not one of my shells;
  - the checking command itself.
- **Where I wrote:** only in my own directory. I made no Git start, no Git write and no edit in the
  worktree, and opened nothing in Finder.
- **Each shell's profile.** The harness's shell may source the account's profile. I could not observe
  that, and so did not count it.

## 2. Answers

### A. Each finding of review 001

| ID | Status | What the code does now (file: lines) | Test |
| --- | --- | --- | --- |
| TR-01 | met | discovery `preloaded_root_modules` skips only a `__main__` whose realpath is its own file (233–244), and records the admission (482). Collector: 694–706. Runner: `load_supervisor`'s `others` (461–470), recorded at 922. Every other root module still refuses. | the three `test_it_runs_from_its_committed_place_inside_the_root`, and `test_every_other_preloaded_root_module_still_refuses`; also my real in-place discovery |
| TR-02 | met | `validate_expected` admits only the error that the exit status implies (491–495, 569–571). `evaluate` requires that error both as the raised `Stop` and as the receipt's `error` (730–731, 769–770). | the descendant and staged-link tests, and the refusal subtest |
| TR-03 | met | Rows carry `inputs` and `stage_entries`, and every stage file must be an input (604–629). `check_frozen_state` checks the inputs, the exact entries and the absent targets (the predicates' files and the supervisor's three outputs) when the rows are read (671). It checks them again after `intent.json`, immediately before the start (792–794), with Node, the probe and the loader re-hashed. The record lists `targets_absent_at_intent`. | the stale-target test, the before-each-start test, and three refusal subtests |
| TR-04 | met | `forbidden_strings` derives the strings at run time (53–79). The joined-literal views (82–102) cover adjacent, added and sibling literals. A failure names the file and the kind only. My own scan (E) finds no literal or fragment. | the hygiene test, and `test_the_derivation_finds_a_split_literal` |
| TR-05 | met | `capture_probe.py` and FAILURE-CAPTURE FC-P3 and FC-P6 (B) | `test_capture_probe.py`, 10 tests |
| TR-06 | met | `discover` (313–340, 472–484) and `mc29` (658–670) require the exact frozen environment and record names only. `HOME` refuses in every frozen environment. Every audit hook records a child's environment by names and a digest. The one value recorded is the `__CF_USER_TEXT_ENCODING` that macOS adds (D-16). | the tests named in AUTHOR-NOTES section 6 |
| TR-07 | met | `discovery_summary` recomputes the counts and duplicates from the IDs and requires `state` `COMPLETE` (552–574). The `-B` is derived from `add()`'s AST (347–369). | two tests |
| TR-08 | met | README "blind spots" and FC-P7. Every hook records the `ctypes.dlsym` lookups of libc's process functions. | documentation |
| TR-09 | met | A subtest skip is the parent's `subtest_skip` (610–618). Unplanned events are kept and rule out `ALL_PASSED` (778–779, 815). `--module-sha256` is required in both modes (843, 849). The bodies are compared with `original_bodies` (787–793). `GIT_*` names must be exactly the driver's set (413–418). | five tests |
| TR-10 | met | The boot is read before and after each row (783, 828), and must be unchanged for the row to be met (866, 879). Exact and negative predicates (732–768). One stage per row (650–652). `is not None` (459–460). MC36's order is S6's decision. | three tests |
| TR-11 | met | Every pattern runs on the raw text and on the decoded and joined views (549–565). The binding names, the bracket forms, the require references, `__non_webpack_require__` and the multi-line specifiers are covered. The real validator's `"url"` is listed (1.3). | `test_the_forms_of_review_001_are_found_on_every_view` |
| TR-12 | met | The frozen rule's patterns (124–134) equal those of MI's `scan_javascript` (controls module 657–666), and so does its line loop (572–591). Its verdict is reported separately. `load_reviewed` refuses a list that is not `REVIEWED` or names no reviewer (675–680). | two tests |
| TR-13 | met | A test reaches `PYTHON-MODULE` without the exclusion and passes that rule with it. `attempt_listing` opens with `O_NOFOLLOW` and records links (517–537). | two tests |
| TR-14 | carried | No change. AUTHOR-NOTES section 4, item 11 lists it for S6. | |
| TR-15 | met | The vertices are recomputed in `applyMatrix4`'s order, and the bounds from them (343–382). The retained ones must be equal (385–405, 611–614). | two tests; deviation 0 on all 12 meshes |
| TR-16 | met | FC-P3, FC-P6 and FC-K5 name `capture_probe.py`. The listing records `digests_computed_by`. | two tests |
| TR-17 | met as worded | Every entry point refuses a start without `-B`, with rule `PYTHON`. The refusal's limit is TR2-05. | in-process tests for five tools; code read for the other two |
| TR-18 | met | The missing tests are added. An interruption after a start is `UNKNOWN`. SIGTERM and SIGHUP are handled as SIGINT (993–994). The gap before a start is TR2-01. | `test_sigint_and_sigterm_after_a_start` and the rest |

**The TR-01 to TR-05 tests against `rejected-001`, from my focused rerun on my own verified copy.**
The results match `TEST-RUN-AGAINST-REJECTED-001.txt`.
- **TR-01.** Each of the three tools refuses its own `__main__`, with exit 2, rule `PYTHON` or
  `SUPERVISOR`, and modules `["__main__"]`. That is the defect. The refusal of a preloaded
  `sitecustomize` passes on both versions, as a guard should.
- **TR-02.** Both stand-ins, the one that leaves a descendant and the one that stages a link, give
  `ALL_ROWS_MET` with exit 0. The supervisor refused them, and the rejected runner ignored that. That
  is the defect.
- **TR-03.** The stale `probe.json` meets MC36's row. All three rows start after an earlier row
  changed their inputs. The `input digest`, `unbound stage file` and `stage entries` subtests run and
  are met. That is the defect, in each case.
- **TR-04.** Four subtests flag the rejected `tests/test_zz_hygiene.py`: two account-name parts, a
  worktree-parent component and an interpreter-prefix component, without printing any of them. That
  is the defect. The derivation self-test passes on both versions, as it tests the test.
- **TR-05.** The nine behavioural tests error, because the rejected procedure has no tool to run.
  That absence is the defect: the probe was described, not fixed. The text test fails on FC-P3,
  which names no code for the probe.
- **Not the defect's reason (TR2-02):**
  - the runner test's `ROW-TARGET` part: `('ROWS')` against `('ROW-TARGET')`;
  - the `supervisor error not implied by the status` subtest.

### B. `capture_probe.py` and FAILURE-CAPTURE version 2

**The identity rule is sound.** Identity is established only when all three hold:
- the kernel's start time lies inside the window from the record before the start to the started
  record;
- `proc_pidpath` equals the recorded `argv[0]`;
- the group equals the recorded group, which equals the PID.

The window holds because of the order of events:
- every writer publishes its before-record before `run_process`;
- the supervisor calls `on_started` after `Popen` returns and before its first `poll`, so the child
  is forked inside the window and cannot be reaped, or its PID reused, before the started record
  exists;
- this holds for the runner (`intent.json`, then `started-1.json`), the observer (`intent.json`,
  then `started.json`) and the provider (`preflight.json`, then `started.json`), as I read in each
  writer.

**Timestamps on the evidence volume.** In 2,000 writes, every modification time lay between the
write's start and its end, 30 to 275 µs after the start. So the file times are precise wall-clock
times, the same clock as the kernel's `p_start`.

**The declarations.** These were checked on this host, in my own process:
- **My own reading of the layout.** It is 12 `uint32` fields, `comm[16]`, `name[32]`, five `uint32`
  fields, `nice` (`int32`), then `start_tvsec` at 120 and `start_tvusec` at 128: 136 bytes.
- **The kernel's answers.** It returned 136 bytes for a 512-byte buffer and refused 135 (`ENOMEM`).
  The fields matched `getpid`, `getppid`, `getpgrp` and `getuid`, and the start lay 18.6 ms before
  the script's first wall-clock read.
- **W2's own `Kernel` class,** loaded from its file:
  - it gives the same PID, parent, group, user and start;
  - its image equals mine;
  - its `proc_listpgrppids` lists my PID in my group;
  - a PID that does not exist reads `ESRCH`.
- **The constants and signatures:**
  - `PROC_PIDTBSDINFO` is 3;
  - `proc_pidpath` has a 4,096-byte buffer, which is `PROC_PIDPATHINFO_MAXSIZE`;
  - the signatures and return conventions of `proc_pidinfo`, `proc_pidpath`, `proc_listpgrppids`
    (which counts PIDs) and `sysctlbyname` are right.

**The cases:**
- **Wall-clock changes.** A step backwards inside the window can only exclude the true start, which
  fails closed. A false identity would need a reused PID whose start falls inside a window of
  milliseconds after a backward step, with the same image path, and leading its own group. That is
  not a practical risk.
- **PID reuse.** A reused PID starts after the started record, so it fails the window.
  - **A reused PID that is not a group leader:** `killpg` reads `ESRCH`, and the target is reported
    absent, with "the PID itself is held by another process". That is sound, because the recorded
    child led its own session and cannot leave its group.
  - **Shown on a live process of this account that leads no group:** `kill` success and `killpg`
    `ESRCH` gave `absent`.
- **An exited process.** `kill` and `killpg` read `ESRCH`, and it is `absent`. If its group survives,
  the state is "present, identity not established", and nothing is sent.
- **A zombie.** By XNU's source and W1's observation of `killpg`, and not observed here, since no
  start of mine may fork:
  - it reads as present: success from `kill` and `EPERM` from `killpg`;
  - `proc_pidinfo` with argument 0 does not find it, so its identity is not established and nothing
    is sent;
  - that fails closed, but the record does not show that the process exited (TR2-04).
- **Permission.** `proc_pidinfo` on another user's process (PID 1) reads `EPERM`, so its identity is
  not established and nothing is sent.

**Every path without an identity sends nothing:**
- a malformed or self-referring record: `unknown`;
- a probe answer other than `ESRCH`, `EPERM` or success: `unknown`;
- an absent group: `absent`;
- an absent PID with a present group: "present, identity not established";
- a failed identity, at the first check or before SIGKILL: no send, with "SIGKILL not sent: …".

None of these sends a signal, and none changes the attempt's outcome, which FAILURE-CAPTURE
section 2 decides; a present process without an identity keeps it unknown. Ending a process never
changes an outcome either.
- The only remaining race is the moment between the last identity check and a send. It is
  microseconds long, and inherent without process descriptors.

**No retry.** `stop` sends SIGTERM once, and SIGKILL at most once, after 2,000 ms of continuous
presence and a second identity. No command is repeated, and FC-R1 to FC-R5 are unchanged.

**Absence** is established only by `ESRCH` from `killpg` on the recorded group (FC-P4). That is
sound given session leadership. FC-P5 states the descendant limit in every record.

### C. New behaviour of revision 2

- **An interrupted run is `UNKNOWN`.** This is right after a start, as the test shows. It is not done
  before a start or inside `run_process` before `Popen` (TR2-01). Even then the run never passes, and
  its zero count is right.
- **SIGTERM and SIGHUP are handled as SIGINT.** They go to `default_int_handler` in `main`. The child
  sits in its own session, so the supervisor's cleanup ends its group. This is in scope: it brings the
  runner into P07 section 4.
- **The boot session** is read before the intent and after the start, and an unchanged boot is
  required for a met row. This satisfies MH-PLAN section 5's one boot.
- **The exact and negative predicates** are enough to state P06-H01, P06-H02 and MC36 exactly (D, Q4).
- **One stage per row** is enforced at read time.
- **The inputs and stage entries are checked again just before the start.** This meets P07
  section 3, item 7. A difference refuses with `PROVEN_ZERO`, as the test shows.
- **The targets that must be absent at intent** are refused with `ROW-TARGET` if present, and
  recorded.
- **The `-B` refusal** is at every entry point, with TR2-05's limit.
- **MI's frozen rule in `scan_mc11.py`** is applied pattern for pattern and reported as the verdict
  that decides MC11. The wider scan is reported beside it, for review. A list must be `REVIEWED` and
  name its reviewer. W2's candidate list (`CANDIDATE, NOT REVIEWED`) therefore refuses.
- **The recomputation in `audit_numeric.py`** has the same operations, order and doubles as Three.js
  r186 `Vector3.applyMatrix4` on the probe's `matrixRows`: `w` from `e[3]`, `e[7]`, `e[11]` and
  `e[15]`, left-to-right sums, and no fused operations in either language. Equality is required
  exactly, which fails closed if Node ever differs.
- **No change of scope.**
  - None of this makes a general execution-plan runner. The runner still admits five fixed row IDs
    and two argv shapes, the collector two modules, and the harness three commands.
  - `capture_probe.py` adds only what FC-P3, FC-P6 and FC-K5 already called for.
  - No tool changes a test, the implementation, the contract, the amendment or a frozen control, and
    none redesigns the test result protocol.

### D. The ten questions of review 001, for the whole revised tooling

**Q1. Fitness.** Each piece matches its row in MH-PLAN section 4 and P07 sections 3 to 6, within the
findings below. Nothing does more than its row:
- the `MC30-probe` row starts nothing unless the freeze adds it;
- the wider MC11 scan is advisory beside the frozen verdict.

**Q2. `discover_inventory.py`.**
- **The same discovery as the unit stage.**
  - The argv and the `-B` are parsed from `tools/check_local.py`, line 449 and `add()`.
  - unittest's own `TestLoader().discover("tests", "test*.py", None)` runs from the root.
  - The root is the working directory and `sys.path[0]`, and the tool's own directory is removed.
    `-B` is required, and `-I`, `-S`, `-E` and `-P` refuse.
  - My run in place reproduces W2's and review 001's order digest.
  - Its `sys.path` held only the clone, the framework's library directories and the venv's
    site-packages. All 671 loaded project files lay under the clone.
- **The comparison** is exact by sets: `(baseline ∪ added) − removed` against the current IDs. Counts
  and duplicates are recomputed for both documents, and both must be `COMPLETE` and consistent.
- **The refusal of process creation** is sound for every audited event, and for ctypes lookups made
  after the hook is installed. A refusal is a recorded event and an import failure, and both make the
  discovery unclean. FC-P7 states the limits.

**Q3. `collect_outcomes.py`.**
- **It runs the complete module unchanged:** `loadTestsFromNames`, then `TextTestRunner` at verbosity
  2 with the `default` warnings, and a result class that records and then calls the original. It
  substitutes nothing, and the module's digest is checked before and after.
- **It keeps everything:** every planned ID and outcome, the subtests, the class-level and
  module-level events under unittest's descriptions, and the unplanned events by name.
- **No skip, error or missing method can become a pass.**
  - `ALL_PASSED` needs every planned test to pass, with no class-level or unplanned event, no loader
    error and no bytecode.
  - It also needs equal bodies, all seven required methods passing, an unchanged module and a
    complete run.
  - The provider's `_verify_methods` separately requires `original_bodies` to equal its nine
    `ORIGINAL_BODIES`.
- **The environment rule is right.**
  - It enforces the driver's removal list, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, the
    selection pair and the driver's exact `GIT_*` set, with the ceiling at the root's parent.
  - It also requires an exact frozen environment without `HOME`, which is stricter than the driver.
  - The provider's `_check_python` is mirrored: `sys.executable == launcher == venv + "/bin/python"`,
    the implementation, `platform.python_version()`, `sys.version` and `proc_pidpath`.

**Q4. `run_direct_probe.py`.**
- **One start per row.** It is one `run_process` call of the real Darwin supervisor, with no retry.
  - The four supervisor files are compiled from verified bytes.
  - `run_process` must come from the bound file, and `Clock`, `Stop` and `json_bytes` must be the
    originals and not `None`.
  - No other root module may be loaded, except the tool's own `__main__`.
- **It keeps everything the run produces:**
  - in the stage: the supervisor's three files and `probe.json`;
  - `intent.json`, `started-<n>.json`, `outcome.json` (bindings, text and receipt) and `run.json`.
- **Counting follows P07 section 4:**
  - `PROVEN_ZERO` needs no event, no callback, no PID and no unexpected exception;
  - `OBSERVED_ONE` needs one `subprocess.Popen` event, one callback, and a positive PID equal to the
    group;
  - anything else is `UNKNOWN`, with a lower bound, and stops the later rows.
- **The predicates are sufficient, with the expectations of AUTHOR-NOTES section 4, item 6.** I read
  them against the probe:
  - **P06-H01 and P06-H02** fail in `approvedEnvelope`, outside the `try`. The `requireSelection`
    and `requireValue` prefixes give "CH-SELECTION: manifest digest is not external approval" and
    "Current-host binding: wrong configuration contract/schema" on stderr. The exit is 1, stdout is
    empty, and `probe.json` is absent.
  - **MC36's refusal** in `verifyHost` lies inside the `try`, so it shows in `probe.json`'s
    `/error/message`, with `/passed` false and no `/khronos`. Its stdout is the summary line, so it
    must not be frozen as empty.
- **Node cannot start for a row whose bindings fail.** The bindings are checked at read time, and
  again after the intent, immediately before the start: Node, the probe and the loader are re-hashed,
  the inputs re-read, and the entries and the absent targets checked. A difference refuses with zero
  starts. Two limits remain:
  - the gap of microseconds before `Popen`;
  - a file outside the stage is bound only when the freeze lists it among the row's inputs; the probe
    then re-checks its own digests of the job, manifest, configuration, GLB and reference.

**Q5. `audit_numeric.py`.**
- **Independence.** It imports only the standard library and uses none of the probe's or the
  provider's code. Only the matrix terms and the normals are the importer's retained values.
- **The row inventory and thresholds** equal the probe's:
  - 16 terms per node, at 5e-6 for `[0..2][3]` and 1e-6 otherwise;
  - per vertex and axis, a position row at 5e-6, then a normal row at 1e-6;
  - then the minimum, maximum and size per axis, at 5e-6.

  That makes 14 × 16 + 12 × (144 + 9) = 2,060 rows per case, in the probe's order.
- **The decision** is `isFinite`, with `difference <= threshold`.
- **The single negative** is at `equipment-tray/pair/left/base` `matrix_0_3`. It has exactly one
  failed row and one finding, threshold 5e-6, and no `error` member. Its fixture is checked too: the
  same GLB, and a reference equal to Q01's except for that term (+0.001, as `check_case` line 129
  adds it) and the scope.
- **The 1e-9 bound of T-10 is sound.** Both references come from the same exact JSON doubles, so the
  difference is 0.001 to within a few ULP. It is a declared bound, it fails closed, and it lies far
  below the 5e-6 threshold.
- **The exact comparisons** follow the probe's `exact()` calls. `empty_root` and the order of the
  findings are stated limits.

**Q6. `scan_mc11.py`.**
- **The patterns cover every named route:**
  - `child_process`, `cluster`, `worker_threads` and `Worker`;
  - `process.binding`, `_linkedBinding`, `internalBinding` and the binding names;
  - `dlopen` and `execve`;
  - the call names;
  - the constructs that could hide them: `eval`, `Function`, `createRequire`, computed `require` and
    `import()`, require references, module internals, bracket forms and `vm`.

  A computed name stays the stated limit. TR2-03 names two more dynamic routes, inert in the real
  files.
- **Links and the inventory are handled soundly.**
  - The tree must be exactly the 24 regular files, with no link, no special file and no `.DS_Store`.
  - Each file is read with `O_NOFOLLOW`, with stable identity, and compared with its binding.
  - The inventory is bound by its digest.
- **The loader is identified correctly.** It is `tools/three_loader.mjs`, one of the 24 files. It
  imports only `node:url` and `node:path`, maps `three`, `three/webgpu` and `three/tsl`, and passes
  every other specifier to `nextResolve`.

**Q7. `control_harness.py`.**
- **T-01 holds for MC10.**
  - The real `Host` is kept, except `supervisor()` and `loaded_modules()`.
  - Exactly the harness's own `__main__` row is excluded (lines 571–577), and the record lists it.
  - A test reaches `RUNTIME` with the exclusion and `PYTHON-MODULE` without it.
- **MC29's coverage.**
  - The configuration and job-input changes are real, and the attempt is refused by v02's own
    `_job`.
  - The 17 detectors are proved to be the provider's own functions.
  - In the configuration case, the accounting refusal comes through the facade's 0.1.0 code
    (TR2-06).
  - The other cases stay simulated or `NOT_RUN` (T-02, TR-14).
- **The recorder cannot let a real start through.**
  - The provider calls `supervisor_darwin_v01.run_process` by attribute at call time (provider line
    1111). The recorder raises before doing anything.
  - The facade's 0.1.0 `guarded_run_process` is never reached, because the dispatch for the attempt
    happens before the change.
  - A Node event would fail `zero_node_process_events`.
  - The only real starts are the provider's bound Git reads (TR-14).
- **`host-state`** runs the provider's real `host_state` and `_check_state`, with nothing substituted
  and process creation refused. The boundary must read `real` before and after. It passed on this
  boot in my rerun.

**Q8. FAILURE-CAPTURE.md.**
- **It is complete for refused, failed and unknown outcomes**, and it keeps every record.
- **No retry:** FC-R1 to FC-R5.
- **Absence is never established by name.** Only `ESRCH` establishes it.
- **Identity comes before any signal,** and its code is fixed: FC-P3 and FC-P6 name
  `capture_probe.py`, and FC-K5 names the listing process.
- **Its limits are stated:** FC-P5 and FC-P7.

**Q9. Safety and privacy.**
- **Node** starts only from the runner's frozen rows and from the cohort module's provider.
- **Git** starts only as the provider's bound reads (TR-14).
- **Nothing starts `ldd` or `codesign`.**
- **Discovery, `mc10`, `host-state` and `capture_probe.py`** refuse process creation.
- **The writes** go to the absent output paths, plus the by-design evidence that review 001 listed.
- **`-B`** is required everywhere (TR2-05).
- **No environment values** are written, except the admitted `__CF_USER_TEXT_ENCODING`.
- **Privacy:** see E.

**Q10. Tests.**
- **The suite passes again:** 91 of 91, with the same IDs and counts. It writes nothing outside the
  temporary directories, and no bytecode.
- **Every mandatory fix's test fails on `rejected-001`**, as described in A.
- **Not covered by a test:**
  - an interruption before a start (TR2-01);
  - SIGHUP, which takes the same handler as SIGTERM;
  - a zombie or another user's process in `capture_probe.py`;
  - real Node, which W2 may not start.

### E. Privacy

**How I derived the strings.** I derived them at run time and wrote none of them, nor a fragment of
one, into any of my files:
- the home directory, from the environment and the password database;
- the account name and its parts;
- the Git user name, its parts and the e-mail address, from the worktree's common configuration and
  the account's global configuration;
- the host name;
- the paths of the worktree and of the local root, with their ancestors and non-generic components;
- the interpreter prefix that `<worktree>/.venv/pyvenv.cfg` names, with its realpaths, ancestors and
  non-generic components;
- the temporary directory.

**How I searched.** I searched every file of `tooling/` in five views: the raw text, the text without
non-alphanumeric characters, the reversed text, every string literal of each Python file joined in
source order, and each run or sum of literals. I also looked for e-mail-like strings, and for absolute
paths under the macOS home, volume, optional-software and temporary roots.

**The result for `tooling/`.** There is no hit, except two false positives in the squashed view of
`TEST-RUN.txt` and `TEST-RUN-AGAINST-REJECTED-001.txt`. There "CPython 3.12.13" squashes into the
alphanumeric form of a versioned prefix component, and the component itself does not occur.
- There is no e-mail-like string, and no absolute path under those roots.
- W2's own hygiene test, rerun, passed on the same files.

**My own files.**
- My scripts and the `outputs/` and `state/` records hold only labels or relative paths. The only
  hits are the same kind of squashed false positives.
- `runs/` holds the raw outputs of W2's tools, which contain machine paths. These are local
  evidence, not public copies.
- This report, its JSON and my scripts were scanned twice, the second time after this report's last
  edit, as the last start of section 1.4 (`outputs/privacy-scan-deliverables.json` and
  `outputs/privacy-scan-deliverables-2.json`). Each scan finds only the same squashed false positive,
  from "CPython 3.12.13" in the text; there is no hit in the raw, reversed or literal views.

## 3. Findings

### TR2-01 (nonmandatory): an interruption before a row's start is not recorded as `UNKNOWN`

- **Location.** `run_direct_probe.py`:
  - lines 937–952, the per-row `except` in `run`;
  - line 973, the `interrupted` flag;
  - lines 825–835 and 884–885;
  - the docstring, lines 46–49.
- **Issue.** A `KeyboardInterrupt` can come from SIGINT, or from SIGTERM or SIGHUP through the
  handler.
  - **Raised in `run_row` before `run_process`,** for example during the re-hash just before the
    start, it leaves `intent.json` without `outcome.json`. `run` then records the row as
    `FAILED_BEFORE_START` and `PROVEN_ZERO`, without `interrupted`. The run is `ROWS_UNMET`, with
    exit 1.
  - **Raised inside `run_process` before `Popen`,** it gives an `outcome.json` that says `UNKNOWN`
    and interrupted, which the run record then contradicts as `FAILED_BEFORE_START`.
- **Effect.** The run never passes, and the zero count is right: no `Popen` event was seen. But the
  docstring's "an interrupted run's state is UNKNOWN" fails, and so does FAILURE-CAPTURE section 2's
  rule. The handler also turns the signal into a normal exit 1, so the command record does not show
  that an interruption happened.
- **Recommendation.**
  - In `run`'s per-row handler, mark a `KeyboardInterrupt` or `SystemExit` as interrupted, so that
    the run is `UNKNOWN`.
  - Keep the row's own `outcome.json` state when it was written.
  - Add a test that interrupts before a start.
  - Until then, S6 notes that the Director treats any interrupted runner command as unknown, by
    FAILURE-CAPTURE section 2.

### TR2-02 (nonmandatory): two sub-checks listed against `rejected-001` do not fail for the defect

- **Location.**
  - `tests/TEST-RUN-AGAINST-REJECTED-001.txt`, header lines 16 and 19;
  - AUTHOR-NOTES section 6, rows TR-02 and TR-03.
- **Issue.**
  - **`test_bound_inputs_and_row_shapes_refuse_before_any_start`'s `ROW-TARGET` part** fails on
    `rejected-001` with `(2, 'ROWS')` instead of `(2, 'ROW-TARGET')`. The rejected runner already
    refused a pre-existing supervisor output, under the rule `ROWS`, so the failure is a renamed
    rule.
  - **The `supervisor error not implied by the status` subtest** fails there because rows schema
    `/1` has no such field: the row simply ran.
- **Effect.** None on the code. The other tests named for TR-02 and TR-03 do fail for the defects, and
  my rerun confirms them. The record overstates two of its sub-checks.
- **Recommendation.** Say so where the S6 freeze cites this evidence, or correct the header. No code
  change.

### TR2-03 (nonmandatory): neither MC11 verdict flags two dynamic routes

- **Location.** `scan_mc11.py`, `DYNAMIC`, `PROCESS_CREATION` and the frozen patterns
  (lines 84–134).
- **Issue.** Neither the wider scan nor the frozen rule lists either of these:
  - the Function constructor reached through a function's `.constructor`, or through
    `Reflect.construct`;
  - computed members of the global objects (`globalThis[x]`, `self[x]`, `window[x]`).

  Each can reach `process` or code from a string without any of the scanned names.
- **On the real files** (`w3_bytecode_and_scan_checks.py`, `w3_contexts.py`), both routes are inert:
  - every one of the 61 `.constructor(` calls is a `new` expression: 42 in `three.core.js`, 1 in
    `three.module.js`, 12 in `three.webgpu.js` and 6 in `BufferGeometryUtils.js`;
  - `Reflect` occurs only as `Reflect.get` in `three.webgpu.js`'s proxies;
  - the validator's five computed globals are dart2js's `window[tag]` lookups, which return `null`
    under Node.

  The `new Function…` texts are `FunctionNode` and `FunctionCallNode`, and the `inspector` texts are
  Three.js's renderer inspector.
- **Recommendation.**
  - The S6 reviewed list's notes record both route classes and this cross-check, under the stated
    limit.
  - Optionally, the wider scan lists `.constructor(` without `new`, `Reflect.construct` and computed
    global members as dynamic hits for review.

### TR2-04 (nonmandatory): two details of `capture_probe.py`, both fail-closed

- **Location.** `capture_probe.py`, `directory_listing` (lines 494–503) and `Kernel.bsdinfo`
  (lines 303–312).
- **Issue.**
  - **Unreadable directories.** `os.walk` runs without `onerror`, so an unreadable directory's
    entries are left out of the FC-K5 listing without any record. The directory's own row stays.
  - **Zombies.** `proc_pidinfo` is called with argument 0. By XNU's source, this flavor looks up an
    exited, unreaped process only for a non-zero argument. This was not observed here, since no start
    of mine may fork.
    - Such a process reads success from `kill`, `EPERM` from `killpg` and `ESRCH` from
      `proc_pidinfo`.
    - It is recorded only as "present, identity not established", not as exited.
- **Effect.** Nothing is sent that should not be. The readback can be incomplete without saying so,
  and a zombie cannot be told from an unidentifiable live process.
- **Recommendation.**
  - Record walk errors in the listing.
  - Optionally, read the facts of an unreaped process with a non-zero argument, and record its
    status. It would still be sent nothing.

### TR2-05 (nonmandatory): the `-B` refusal cannot prevent a write

- **Location.** Every tool: its module-level imports come before the check. For example,
  `capture_probe.py` imports at lines 48–58 and checks at line 533. For `discover` and the collector,
  `site`'s start-up also comes first.
- **Issue.** A start without `-B` has already imported those modules when the tool refuses, so the
  refusal can only detect the mistake.
- **Measured.** In a `-I -S -B` process, every module that the seven tools' module-level imports load
  is one of these:
  - frozen or built in: 36;
  - an extension: 8;
  - a source whose cached bytecode exists: 34.

  Only my script's `__main__` is left over. So no write would occur today.
- **Recommendation.**
  - S6 records that this refusal relies on the frozen framework's bytecode set.
  - Optionally, each tool checks `sys.flags.dont_write_bytecode` in its first statement, before any
    other import.

### TR2-06 (nonmandatory): in MC29's configuration case, the accounting refusal is the 0.1.0 code's

- **Location.**
  - `control_harness.py` `mc29`, lines 751–753 and 780;
  - the facade's dispatch (W5-PROVIDER section 4);
  - CONTROLS-FROZEN F-07.
- **Issue.** After the real configuration change, the configuration's bytes no longer match the
  selected digest. `facade.finish_cpu_cohort` is therefore dispatched to the unchanged 0.1.0 code,
  which refuses with `CH-SELECTION` and a 0.1.0 refusal without the 0.2.0 labels. The attempt's
  refusal is v02's own `_job`, because the dispatch happened before the change.
- **Effect.** `accounting_refused` holds, through the real code path. But the record's accounting
  refusal is not the 0.2.0 provider's accounting.
- **Recommendation.** The S6 freeze states it in MC29's expected outcome:
  - the configuration case: `finish_error` `CH-SELECTION`, from the 0.1.0 code, as F-07;
  - the job-input case: `CH-EVIDENCE`, from v02.

## 4. Files in `<local>/c271-p35/workers/W3-tooling-002/`

**The reports:**
- `TOOLING-REVIEW-002.md` and `TOOLING-REVIEW-002.json`.

**My scripts** (`scripts/`):
- `w3_inventory.py`, `w3_wt_state.py`, `w3_digests.py`, `w3_proc_check.py`;
- `w3_privacy_scan.py`, `w3_bytecode_and_scan_checks.py`, `w3_contexts.py`;
- `w3_discovery_helpers.py`, `w3_assemble_review_json.py`.

**Their outputs:**
- `outputs-inventory.json`;
- in `outputs/`:
  - `digests.json`, `final-w2-inventory.json`;
  - `proc-check-baseline.json`, `proc-check-after.json`, `proc-check-final.json`;
  - `privacy-scan-tooling.json`, `privacy-scan-own-scripts-and-outputs.json`,
    `privacy-scan-deliverables.json`, `privacy-scan-deliverables-2.json`;
  - `bytecode-and-scan-checks.json`, `mc11-scan-comparison.json`, `discovery-analysis.json`;
- in `state/`: `wt-state-{before,after,final}.json` and `wt-snapshot-{before,after,final}.json`.

**The outputs of W2's tools that I ran** (`runs/`, local only, with machine paths):
- the suite: `suite-rerun.raw.txt`, `suite-rerun.exit.txt` and its two time files;
- the focused rerun: `focused-rejected.raw.txt` and `focused-rejected.exit.txt`;
- the scan: `mc11-scan-w3.json` with its stderr and exit files;
- the discovery: `discovery-environment.json`, and `discovery-inplace-w3.json` with its stdout,
  stderr and exit files.
