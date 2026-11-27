# MH tooling review 003

C271-P35, gate MH, stage S3. Reviewer: W3, in a fresh context. I wrote none of the tooling and took
no part in reviews 001 and 002, which I read only as documents. This is a focused review of the
change from revision 2 to revision 3, the correction of the Director's IP-01. Written on 2026-11-27
(UTC) against the worktree at `c81cf07b`, read from the Git files without a Git start. Paths use the
labels `<worktree>`, `<local>` and `<prefix>`.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** Revision 3 may become commit C. There is no mandatory
finding. The three nonmandatory findings, TR3-01 to TR3-03, need no code change at C.

**What holds:**
- **Scope.** Revision 3 is exactly the IP-01 correction and the records of its reruns.
  - The nine files outside `tests/` are byte-identical to revision 2, with the same modes.
  - In the tests, only `mh_support.py` gains three names, and only one test method changes: one
    statement becomes two.
  - The run records, `SHA256SUMS.txt` and `AUTHOR-NOTES.md` change only by what the reruns and the
    correction require.
- **Correctness.** The runner test now asserts the exact admission in both places. Its rule agrees,
  on every layout I built, with the runner's and the discovery's own functions, which I ran, and with
  the collector's expression, which I read and which is the same.
  - From W2's directory, it asserts None.
  - In place, it asserts exactly `{"module": "__main__", "path": <the runner's realpath>, "admitted":
    true, "reason": <the tools' reason>}`.
- **Nothing is weakened.** The other 27 statements of the test are unchanged, all 22 of its other
  assertions among them. No other test, helper or tool changed.
- **The records match.** Each labelled record equals W2's labelled raw output, and each header's
  counts equal its body. Every traceback frame names the line it shows.
- **The suite passes in both places.**
  - My rerun from W2's directory passes 91 of 91. Its output equals `TEST-RUN.txt`'s once timing is
    removed, and so does the Director's `inplace-run-002`.
  - My in-place run in an APFS clone reproduces `TEST-RUN-IN-PLACE.txt`'s two clone-only failures,
    for the reasons W2 gives. IP-01's test passes there.
- **Privacy.** No changed or new file holds a machine path, the account name, a personal name, an
  e-mail address or the package manager's name, whether plain, split, squashed or reversed.

**The nonmandatory findings, one line each:**
- **TR3-01.** The Director's `inplace-run-002` does not record its command, working directory or
  environment, so its output alone cannot show that the suite ran at the committed place.
- **TR3-02.** AUTHOR-NOTES section 1 still gives revision 2's run times and file list. The new header
  paragraph declares that section 8 replaces them.
- **TR3-03.** The admission rule, the helper's and the tools' alike, compares realpath strings. On
  this case-insensitive volume, a `--root` spelled in another letter case passes `canonical_path` and
  reads as "outside". This limit lies outside the change.

## 1. Method

### 1.1 Digests and the fixed state

- **W2's delivery.**
  - `SHA256SUMS.txt` lists the 21 files of `tooling/`, and all 21 match.
  - `tooling/` holds no unlisted file, no link, no bytecode and no `.DS_Store`.
  - `revision-002/SHA256SUMS.txt` matches its 20 files.
  - Those 20 files equal the 20 digests that `TOOLING-REVIEW-002.json` records for W2's
    `tooling/`. So `revision-002/` is the revision that review 002 reviewed.
  - Disposition 002's digests of the revision-2 `SHA256SUMS.txt` (`c45d150e…`) and `AUTHOR-NOTES.md`
    (`2a9bb361…`) equal those files in `revision-002/`.
- **The worktree.** The state is read from its files and file times only.
  - HEAD is `c81cf07b5386ea7eba7904f3ef5700709b84b366`, through the `.git` pointer and a loose ref.
  - The index's modification time is 2026-11-26T23:53:39.925658Z. The Git directory holds no lock
    file.
  - No bytecode exists outside `.venv/`, and none inside it. There is no `.DS_Store`.
  - The tooling's committed place is absent.
  - Outside `.venv/`, the only entry newer than the index is the directory
    `docs/engineering/localized-repair-c271/macos-qualification-p35`, at 03:22:47Z. That is the
    Director's removal of the copies after `inplace-run-002`, which ended at 03:22:30Z.
  - The snapshot at 03:35:04Z, my first interpreter start, and the one at 03:50:42Z, after both of
    my suite runs, are identical, entry for entry. The trees compared were:
    - the worktree's 25,341 entries, `.venv` included;
    - the Git directory's 10 entries;
    - the 4,441 entries of the interpreter installation, including its 414 bytecode files;
    - W2's 101 entries, with SHA-256;
    - the 16 entries of the Director's checks, with SHA-256.

  The final snapshot at the end is compared again (`outputs/state-compare-after-final.json`).

The JSON record gives the SHA-256 of every reviewed file.

### 1.2 What I read

- **MH-PLAN.md:** sections 4, 5 and 7 in full, and the other sections for context.
- **Review 002:** all of it, section 2, A, on TR-01 with care.
- **Disposition 002:** all of it, `director_in_place_run` (IP-01) included.
- **W2's records:**
  - `AUTHOR-NOTES.md` of both revisions, with the new header paragraph and section 8 in full;
  - both `SHA256SUMS.txt`;
  - the three run records of revision 3 and the two of revision 2;
  - W2's raw outputs in `test-runs/`, and the helpers `run_suite.py`, `label.py`, `count_starts.py`
    and the three headers in `helpers-003/`.
- **The tooling:**
  - in full: `tests/mh_support.py` and `tests/test_run_direct_probe.py`, both revisions;
  - `test_discover_inventory.py`, the first 290 lines of `test_collect_outcomes.py`, lines 30–244 of
    `test_control_harness.py`, and `test_zz_hygiene.py`;
  - the admission code in each tool: `run_direct_probe.py` lines 1–180, 355–379, 425–494 and
    880–949; `discover_inventory.py` 1–114, 218–247 and 436–490; `collect_outcomes.py` 686–709;
  - every other line of `tests/` that names a place (Q4).
- **The Director's runs:** every file of `inplace-run-001/` and `inplace-run-002/`.

### 1.3 What I ran

Every interpreter start carried `-B`. My scripts, in `scripts/`, ran as
`<worktree>/.venv/bin/python -I -S -B`, and so did my `-c` reads.

| Run | Result |
| --- | --- |
| `w3r3_state.py`: snapshots `before`, `after` and `final`, their comparisons, and `redact` of the first two | HEAD and the fixed state, read from files; unchanged (1.1). The first two snapshots listed the installation's relative paths, which name the package manager's directory; `redact` rekeyed them by the SHA-256 of each path, as `final` is written. |
| `w3r3_proc.py`: `baseline`, `after-runs`, `final`, and `last` as my very last start, through libproc, with no `ps` start | no process of mine alive (1.4) |
| `w3r3_digests.py` | the digests of 1.1, the comparison of the two revisions, the diffs in `outputs/diffs/` (Q1) |
| `w3r3_analysis.py`, three times: before my two suite runs, after them, and before the assembly | the test IDs, the records, the AST comparison, the reasons, the place scan, the frames, raw against labelled, the admission cases, review 002's digests and the comparison of bodies (Q1–Q5) |
| W2's suite, once, as `TEST-RUN.txt` shows. From W2's `tooling/`, `env -i PATH=/usr/bin:/bin LANG=C.UTF-8 TMPDIR=<local>/c271-p35/workers/W3-tooling-003/runs/tmp-suite/ MH_TOOLING_ROOT=<worktree>`, then `<worktree>/.venv/bin/python -B -m unittest discover -s tests -v`; 03:42:59Z to 03:43:14Z | exit 0. 91 of 91 ok in 14.5 s, with the 91 IDs. Starts: 135 of the interpreter with `-B` and 1 of `/usr/bin/true`. Through the tools: 4 of `/bin/sh`, 3 of `/usr/bin/true`, 7 stand-ins and 1 fork. The temporary directory was empty afterwards. |
| The APFS clone, made as `TEST-RUN-IN-PLACE.txt` describes, in `<local>/c271-p35/workers/W3-tooling-003/clone-003` | It took `cp -cR` of the worktree's 28 top-level entries other than `.git` and `.venv`, a plain copy of the one-line `.git` pointer, and W2's `tooling/` with `cp -pR` at its committed place. `w3r3_clone_check.py` then found all 24,994 entries equal in kind, size, mode, link target and SHA-256, no `.venv`, the pointer equal, and the committed place equal to W2's 21 files. |
| The suite in that clone, once, from the committed place, without `MH_TOOLING_ROOT`, under the same `env -i` with `TMPDIR` its own directory in `runs/`; 03:45:35Z to 03:45:48Z. The clone was removed at once. | exit 1. 89 of 91 ok. The MC10 test errors with "Bound path or ancestor is missing: <clone>/.venv", and 13 hygiene subtests fail (Q5). IP-01's test passes in place. Starts: 133 and 1; through the tools: 4, 3, 7 and 1. |
| `w3r3_privacy.py`: twice on the delivery, five times on my own files and three times on my raw runs. The last scan of my files came after this report's last edit. | Q6. The last version masks each context's whole line before cutting it, gives no context for a hit of a short piece, and quotes nothing from the raw runs. Earlier versions cut a window first, which could leave a piece of a machine path from the raw runs in their records, so those records were rewritten. |
| `w3r3_assemble.py`, five times | It checks every fact of this report that my outputs hold before it writes. The first run refused: this report then gave 92 frames and four unresolved ones, a count from my first analysis, before I labelled `<prefix>` as W2 does. The second run wrote `TOOLING-REVIEW-003.json`, and the third and fourth rewrote it after the scanner's change and a count correction. The fifth came after this report's last edit, so that its digests of my files are final. That edit removed example words which, quoted as false positives of the piece check, would have hinted at a component of the interpreter installation. |
| Ten `-c` reads | summaries of my JSON outputs; the masked contexts of the privacy hits; the worktree's size; the normalized comparison of the two rejected-run records; the frame counts; the masked names in my snapshots that hold a piece of an installation component |

### 1.4 Starts

| Kind | Count |
| --- | ---: |
| Bash tool calls, one `/bin/zsh` each. Near the end, one call each: redact the two snapshots, assemble and scan; scan and assemble again after the scanner's change; read the snapshots' masked names; assemble, scan and take the final state and process checks. The last call, after this report's last edit, assembles and scans once more and repeats the process check. | 30 |
| The qualification interpreter, started by me with `-I -S -B`: 31 runs of my scripts and ten `-c` reads | 41 |
| The qualification interpreter, started by me with `-B` only, through `env -i`: W2's suite, once in W2's directory and once in the clone | 2 |
| Children of those two suite runs: the interpreter with `-B`, and `/usr/bin/true` | 268 and 2 |
| Started by the tools under test in those runs: `/bin/sh`, `/usr/bin/true`, stand-ins (the interpreter with `-B`) and forks of a stand-in | 8, 6, 14 and 2 |
| Static-read and file utilities in those shells: `date` 16, `ls` 6, `grep` 9, `head` 5, `cat` 3, `cut` 4, `tail` 2, `wc` 2, `sed` 1, `mkdir` 2, `find` 1, `xargs` 1, `cp` 3, `rm` 1, and `env` 2, which `exec`s into the interpreter | 58 |
| **Node, Git, `ldd`, `codesign`, `otool`, the observer's `observe`, Finder** | **0** |

- **No process of mine remained.** Each check lists every process of this account through libproc,
  as of my first command (03:26:01Z), by image kind and parentage.
  - **After my runs, five other processes had started.**
    - A `/bin/bash` and two Node processes are children of a process that is not the parent of my
      shells. They were not started by any command of mine.
    - Two processes of the framework's interpreter descend from a long-running process of the same
      interpreter, alive since 2026-11-23, which W2 describes as another project's watcher. They are
      not descendants of my shells.
  - **At my final check** (`outputs/proc-final.json`), the others also included:
    - a `/bin/zsh` of that other parent, with an interpreter child;
    - Node processes of a third parent;
    - new children of the watcher.

    None descends from my shells. `outputs/proc-last.json` repeats the check as my very last start.
- **The framework's 414 bytecode files** and the rest of the installation were unchanged between my
  snapshots. That watcher starts the same interpreter, so the installation inventory before and after
  each later stage stays the check (disposition 002, TR2-05).
- **Where I wrote:**
  - My own writes were only in my own directory.
  - The two suite runs changed nothing in the worktree, W2's directory or the framework, by the
    snapshots. Their temporary directories, `runs/tmp-suite/` and `runs/tmp-clone/`, were empty
    afterwards, and are kept empty.
  - The clone and the admission-case tree were made in my directory and removed.
  - I made no Git start of any kind, and opened nothing in Finder.
- **Each shell's profile.** The harness's shell may source the account's profile. I could not observe
  that, and so did not count it.

## 2. Answers

### Q1. Scope: revision 3 is exactly the IP-01 correction

The nine files outside `tests/` are byte-identical to revision 2, with the same modes:
`FAILURE-CAPTURE.md`, `README.md`, `audit_numeric.py`, `capture_probe.py`, `collect_outcomes.py`,
`control_harness.py`, `discover_inventory.py`, `run_direct_probe.py` and `scan_mc11.py`. So are seven
of the twelve files in `tests/`: all eight test modules except `test_run_direct_probe.py`.

| File | Change from revision 2 (line numbers: revision 2 → revision 3) |
| --- | --- |
| `tests/mh_support.py` | Lines 134–155 inserted (22 lines): a comment, `ADMISSION_REASON`, `admission_place` and `expected_admission`. By AST, these are the only added units, and nothing else changed or went. |
| `tests/test_run_direct_probe.py` | Line 172 → lines 172–177. `assertIsNone(record["own_main_admitted"], …)` becomes three comment lines, `place = S.admission_place("run_direct_probe.py", world.root)`, and `assertEqual(record["own_main_admitted"], S.expected_admission("run_direct_probe.py", world.root), "the runner lies " + place)`. By AST, this method is the only unit of the file that changed. |
| `tests/TEST-RUN.txt` | Header lines 1–2 (revision and date) and 7, which adds `otool` to the starts that did not occur. Line 125 gives the new run's time. The 91 test lines and the start line are unchanged. |
| `tests/TEST-RUN-AGAINST-REJECTED-001.txt` | Header lines 1–2 and 8 (`otool`). Lines 24–25 are inserted: IP-01's row, the rejected runner's `KeyError`. The other 37 changed ranges (39 lines each way) are in the body. With temporary names, times, PIDs and frame line numbers normalized, the two bodies differ only in the IP-01 test's two traceback lines. The frame numbers move by +5 after line 172 of the runner test and by +22 after line 133 of `mh_support.py`, as the insertions predict. |
| `tests/TEST-RUN-IN-PLACE.txt` | New, 293 lines: the in-place run in W2's clone. |
| `SHA256SUMS.txt` (beside `tooling/`) | The digests of the four changed files, and one added line for the new record. |
| `AUTHOR-NOTES.md` | 86 lines added, none removed or changed: the "Revision 3" paragraph (lines 14–19) and section 8 (lines 379–458). |

- **AUTHOR-NOTES changes only by section 8 and the facts that the change requires.**
  - The header paragraph states the revision, keeps revision 2 in `revision-002/`, and says that
    section 8 replaces section 1's record of the runs.
  - Section 8's statements check out against the files: the line 172 premise, the three helpers, the
    one changed assertion, the unchanged lines 217 and 100, the nine identical files, the run table
    (times, results and counts) and the clone's procedure.
  - Section 1 was left as it was; see TR3-02.

### Q2. Correctness

**The runner test asserts the exact expected admission in both places.**
- **Outside the root** (W2's directory, with `MH_TOOLING_ROOT=<worktree>`): `expected_admission`
  returns None. `assertEqual(record["own_main_admitted"], None)` is as strict as the old
  `assertIsNone` for any JSON value. My rerun passes it.
- **Inside the root** (the committed place, the root found from the tooling's own path): it returns
  exactly four keys.
  - `module` is `"__main__"`.
  - `path` is `os.path.realpath` of the running tool.
  - `admitted` is `True`.
  - `reason` is `ADMISSION_REASON`.

  Dict equality refuses a missing, extra or different key. My clone run passes it, and so does the
  Director's `inplace-run-002` (TR3-01). In the clone the helper returns that dict, so the runner
  recorded exactly it.
- **The reason** is byte-equal, by AST, to the literal that each of the three tools records:
  `run_direct_probe.py` line 370, `discover_inventory.py` line 228, and `collect_outcomes.py`
  lines 702–704, which split it into two adjacent literals. The four keys are the same in all three.

**`admission_place`'s rule is right.** It decides "inside" when
`realpath(tool).startswith(realpath(root) + "/")`. The tools decide with the same string rule, on a
root that `canonical_path` has already proved to be its own realpath in normal form. I ran the
helper's two functions and the tools' own `canonical_path` and `own_main_admission`, loaded from W2's
files, on nine layouts that I built and then removed.

| Case | Helper | Runner and discovery |
| --- | --- | --- |
| tool at the committed place inside the root | inside: the dict | the same dict |
| root given with a trailing slash | inside (realpath drops the slash) | refused, `ROOT`: "not in normal form", so no admission is recorded |
| root given through a symbolic link | inside (realpath resolves it) | refused, `ROOT`: a component is a symbolic link |
| tool under `root2`, whose name has the root's as a prefix | outside: None | None |
| tool outside the root | None | None |
| tool path a link outside the root to a file inside it | inside, path the target's realpath | the same dict |
| tool path a link inside the root to a file outside it | outside: None | None |
| root spelled in another letter case (it exists on this volume) | outside: None | None (TR3-03) |
| `/` as the root | outside (`"//"`) | None |

- **Symbolic links.** Realpath on both sides resolves them, as the tools do with `own`.
- **The trailing slash, and a root through a link.** The helper normalizes both. The tools refuse
  such a root before any record, so there is nothing to compare. In the test the root is always
  `project_root()`, which is a realpath.
- **A prefix of another directory name.** The added `"/"` keeps `root2` outside.
- **Agreement.** Where a tool records an admission, the helper's answer equals it in all nine cases.

**The helper is independent of the tool.**
- It imports no tool and reads no record.
- Its inputs are `TOOLING`, the script's name, the test's root and an optional path.
- It uses only `os.path.realpath`, `startswith` and its own constant. The reason is the specified
  constant, not a value read back.
- The place comes from the test's own root and the tooling's path, so a tool that admitted itself
  outside the root, or failed to admit itself inside it, fails the test.

### Q3. Nothing weakened

By AST, the method has 28 statements in revision 2 and 29 in revision 3. One replace turns
`assertIsNone(…)` into `place = …` and `assertEqual(…)`. The other 27 statements are identical, in
order. They hold the test's other 22 assertions: the return code, `ALL_ROWS_MET`, the exact
`node_starts`, the four verified supervisor files, `darwin_precondition_before_rows`,
`json_bytes_is_the_original`, the row's state and count, the receipt, the cleanup, the environment,
the cwd, the started record, the stage's process file, the argv, the boot (three assertions), both
supervisor-error predicates, the exact streams, the stage entries and the targets absent at intent.
In revision 2 those assertions never ran in place, because line 172 failed first. In revision 3 they
pass in both places.

### Q4. No other location-dependent expectation

I read every line of `tests/` that names a place: `project_root`, `TOOLING`, `__file__`,
`MH_TOOLING_ROOT`, `MH_TOOLING_UNDER_TEST`, `parents[`, `COMMITTED_PLACE`, `in_place`, `.venv`,
`.git`, `getcwd`, `relative_to`, `realpath`, `resolve()`, `docs/` and the admissions
(`outputs/analysis.json`, F).

- **W2's reasons are right.**
  - `test_collect_outcomes.py:217`: the collector runs with `--root` set to `CollectorWorld`'s fresh
    `<temporary>/root` (lines 108 and 142). `test_discover_inventory.py:100`: the discovery runs with
    `--root` from `make_root` in the test's own temporary directory (lines 65, 70 and 53).
  - The tool under test lies in `S.TOOLING`, which can never be inside a directory that `mkdtemp`
    has just made. So None is right wherever the tooling sits.
  - The three `test_it_runs_from_its_committed_place_inside_the_root` tests copy the tool to
    `<synthetic root>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/` with
    `in_place`. They compare `own_main_admitted["path"]` with that copy's path, which is a realpath
    because the temporary base is resolved. Their expectation is independent of the tooling's place.
    They passed in every run of revision 3 against its own tools: W2's two, the Director's, and my
    two.
- **The other expectations that name a place hold in both the author's directory and the worktree.**
  - `test_discover_inventory.py:91–92` and `test_control_harness.py:229–230` compare with `S.TOOLING`
    itself.
  - The runner's place test copies the supervisor's bytes from `project_root()`.
  - `test_audit_numeric.py:114` and `test_control_harness.py:39–41` and `297–299` read project files
    under the root, which exist in every root.
- **Two tests depend on what the root holds, or where it lies, not on where the tooling sits:**
  - **The MC10 real-static test** (`mc10_plan`, lines 135–142) reads the root's HEAD through its
    `.git` and binds `<root>/.venv`. It passes wherever the root is the prepared worktree.
  - **The hygiene test** takes the components of the root's parent as private. In the worktree they
    are the worktrees folder's, none of which occurs in the tooling. It also adds the local root's
    strings when the tooling lies outside the root, which is stricter there.

  Both are documented in `TEST-RUN-IN-PLACE.txt`, and both pass in W2's directory and in the
  worktree. They fail only in a clone placed under `workers/`, as Q5 shows.

### Q5. The records

- **`TEST-RUN.txt`, `TEST-RUN-AGAINST-REJECTED-001.txt` and `TEST-RUN-IN-PLACE.txt` match the tests
  and the starts they claim.**
  - Each body is W2's raw output (`test-runs/TEST-RUN-revised-4`, `-against-rejected-001-4` and
    `-in-place-clone-1`), labelled. My relabelling of each raw file equals it exactly, and each
    header equals W2's header file in `helpers-003/`.
  - Each raw file records the argv `<worktree>/.venv/bin/python -B -m unittest discover -s tests -v`,
    its cwd, its environment names, its times and its exit:
    - `TEST-RUN.txt`: W2's `tooling/`; `LANG`, `MH_TOOLING_ROOT`, `PATH` and `TMPDIR`; 03:14:36Z to
      03:14:50Z, exit 0.
    - `TEST-RUN-AGAINST-REJECTED-001.txt`: the same names and `MH_TOOLING_UNDER_TEST`; 03:15:10Z to
      03:15:41Z, exit 1.
    - `TEST-RUN-IN-PLACE.txt`: the clone's committed place; `LANG`, `PATH` and `TMPDIR`, with no
      `MH_TOOLING_ROOT`; 03:17:02Z to 03:17:15Z, exit 1.

    These are the headers' dates and exits. The records write the launch as `env -i …`. W2's
    recorder gave the child exactly these variables, which is the same environment.
  - Each lists the 91 IDs that I enumerated from the test modules' ASTs: 10, 10, 17, 14, 16, 12, 7
    and 5 by module.
  - Each header's claims equal its body.
    - `TEST-RUN.txt`: 91 ok. Children 135 and 1; through the tools 4, 3, 7 and 1.
    - The run against the rejected tooling: 42 failures and 27 errors, both in the summary blocks
      and in the final line. Children 125 and 1; through the tools 5, 8, 9 and 1.
    - The in-place run: 89 ok, 14 failures and 1 error. Children 133 and 1; through the tools 4, 3,
      7 and 1.
  - **Every traceback frame** names a line whose source equals the line shown: 96 frames in the
    rejected-run record and 20 in the in-place record, checked against revision 3's files, the
    rejected files, the worktree's and the framework's, with none left unresolved
    (`outputs/analysis.json`, G).
  - **The two fewer interpreter starts in place** are the MC10 test's two `run_mc10` calls. Its setup
    stops before them.
- **The two tests that cannot run in a clone.** W2's explanations are right.
  - **The MC10 test.** `mc10_plan(real_static=True)` reads HEAD through `<root>/.git`, then calls
    `OBSERVER.python_inventory(<root>/.venv, …)`. A clone without `.venv` stops there, with "Bound
    path or ancestor is missing", before any start.
  - **The hygiene test.** `forbidden_strings` takes `os.path.dirname(project_root())` as "worktree
    parent" and treats its non-generic components as private words.
    - In W2's clone the parent was `workers/W2`. Components 12 to 14 are `c271-p35`, `workers` and
      `W2`, all public names in the tooling: 14 subtests failed.
    - My clone's parent is my own directory. `c271-p35` and `workers` occur, and `W3-tooling-003`
      does not. So 13 subtests failed: 11 files for component 12, and the two run records for
      component 13. The new `TEST-RUN-IN-PLACE.txt` holds both, and did not yet exist when W2's clone
      ran.

    This difference confirms the cause.
  - **The wording.** "could not run" is loose for the hygiene test, which ran and found its premise
    false in a clone.
  - **Both passed in the Director's `inplace-run-002`, in the worktree itself, and that is right.**
    There `<root>/.venv` is the qualification venv, and the root's parent is the worktrees folder,
    none of whose components occurs in the tooling.
- **The Director's `inplace-run-002` is a complete pass of the 21 files' suite.**
  - It lists the 91 enumerated IDs, in unittest's order, and all are ok, with no skip.
  - It ends with `Ran 91 tests` and `OK`, and `exit.txt` says 0.
  - Its start line equals `TEST-RUN.txt`'s, and once timing is removed the whole output equals
    `TEST-RUN.txt`'s body.
  - `digest-mismatches.txt` is 0, and `status-before.txt` and `status-after.txt` show the copied
    `tooling/` untracked in the worktree during the run.
  - The output cannot show where it ran. A run from W2's directory gives the same output (TR3-01).

### Q6. Privacy

**How I derived the strings.** I derived them at run time and wrote none of them, nor a fragment of
one, into my files.
- the home directory;
- the account name and its parts, and the password database's full-name field;
- the Git user name, its parts and the e-mail address, from the account's global configuration and
  the worktree's common configuration;
- the host name and its distinctive part;
- the worktree's path and its ancestors, with their distinctive components;
- the interpreter installation that `<worktree>/.venv/pyvenv.cfg` names (home, executable and
  command), with the base prefix, their realpaths, ancestors and distinctive components, and the
  leading and trailing pieces of four or more letters of each alphabetic component.
- the temporary directories.

That makes 56 strings.

**How I searched.**
- **Views:** the raw text, names as words and, from four characters, as substrings; the text
  squashed to lowercase letters and digits, and that text reversed; and, for each Python file, every
  string literal joined in source order, raw and squashed.
- **Also:** e-mail-like strings, and absolute paths under the home, volume, optional-software and
  temporary roots.
- **What a hit records:** its file, view, kind and line. A context is the whole line, masked before it
  is cut, and the raw runs get none.

**The result for the changed and new files.**
- `mh_support.py`, `test_run_direct_probe.py`, `SHA256SUMS.txt` and `AUTHOR-NOTES.md` have no hit in
  any view.
- The three run records have only false positives.
  - In the squashed view, "CPython" and its version, and the generic `lib/python3.x` directory of
    the frames, squash into the alphanumeric form of the installation's versioned component. The
    component itself does not occur.
  - In the rejected-run record, line 651 holds unittest's elided repr of a temporary path. Only the
    system's generic temporary root and the suffix `txt` remain. That line is unchanged since
    revision 2.
- No file holds an e-mail-like string.

**The unchanged files.** The same scan of the other files finds only:
- the joined-literal false positive that disposition 002 noted: the adjacent constants `actual` and
  `expected` in `audit_numeric.py` and `test_audit_numeric.py`;
- README line 30's generic mention of macOS's temporary root.

W2's own hygiene test passed on all 21 files in my rerun.

**My own files.** My scripts, outputs, state records and these two reports hold labels only. They were
scanned after this report's last edit (`outputs/privacy-own.json`).
- **The first scan of my files** found the installation's own relative paths in my first two state
  snapshots: its directory named after the package manager. I rekeyed those entries by the SHA-256 of
  each path (`redact`), as the final snapshot is written.
- **What remains** are false positives and generic roots:
  - the same squashed version forms, in my diffs and digests of W2's records and in the listing of
    `.venv`;
  - in my snapshots' listing of the worktree, 32 repository file names, ordinary words that happen
    to contain one of the short pieces;
  - a repository file name under `TRDs/` that squashes to the local root's name;
  - the adjacent constants ending in `final` and `exit` in my analysis script;
  - the generic roots named in my scanner's, analysis's and assembly's code, and in the masked
    contexts of my delivery scan.

`runs/` keeps my raw suite outputs, with machine paths, as local evidence. It is not a public copy,
and `outputs/suite-*.labelled.txt` are its labelled copies.

## 3. Findings

### TR3-01 (nonmandatory): `inplace-run-002` does not record its command

- **Location.** `<local>/c271-p35/director/checks/inplace-run-002/`, which holds `start.txt`,
  `end.txt`, `exit.txt`, `status-before-copy.txt`, `status-before.txt`, `status-after.txt`,
  `digest-mismatches.txt` and `suite.raw.txt`.
- **Issue.** No file gives the run's argv, working directory, environment or interpreter flags.
  - The output is a complete pass (Q5), and the status files show the copy in the worktree during
    the run.
  - But the output equals `TEST-RUN.txt`'s, which comes from W2's directory, apart from timing. So
    it cannot show that the suite ran at the committed place without `MH_TOOLING_ROOT`, and asserted
    the in-place admission there.
  - Disposition 002 recorded the command of `inplace-run-001`. Nothing yet records the command of
    run 002.
- **Effect.** A3 requires a passing run from the committed place. That rests, for now, on the
  Director's statement and the status files. My clone run shows the in-place behaviour
  independently.
- **Recommendation.** Before commit C, the disposition of this review, or a file beside the output,
  records run 002's exact command line, cwd, environment names and flags (PROTOCOL section 5), as
  W2's raw headers do.

### TR3-02 (nonmandatory): AUTHOR-NOTES section 1 keeps revision 2's record of the runs

- **Location.** `AUTHOR-NOTES.md` section 1:
  - "The run is recorded in `tests/TEST-RUN.txt` (2026-11-27T02:07:54Z, exit 0)";
  - "`tests/TEST-RUN-AGAINST-REJECTED-001.txt`, 2026-11-27T02:08:08Z";
  - the `tests/` row of the delivered files, which does not list `TEST-RUN-IN-PLACE.txt`.
- **Issue.** The records in `tests/` now carry 03:14:36Z and 03:15:10Z, and `tests/` holds the new
  record. The header paragraph says that section 8 replaces section 1's record of the runs, so the
  notes are consistent as a whole. Read alone, section 1 disagrees with the files it names.
- **Effect.** None on the code or the evidence.
- **Recommendation.** Keep the reviewed bytes at C. Where the disposition or the S6 freeze cites the
  notes, it says that section 8 supersedes section 1's times and file list. W2 can correct section 1
  in a later revision.

### TR3-03 (nonmandatory): letter case, a shared limit of the admission rule, outside the change

- **Location.**
  - `tests/mh_support.py` line 141, which mirrors the tools;
  - `run_direct_probe.py`, `own_main_admission` (lines 364–372) and the `others` check (461–467),
    after `canonical_path` (140–157);
  - `discover_inventory.py`, lines 222–244 and 95–112;
  - `collect_outcomes.py`, lines 694–706.
- **Issue.** Every one of them compares realpath strings by prefix. `os.path.realpath` does not
  establish the letter case on disk, and this volume is case-insensitive: my case 8 found the
  differently spelled root present.
  - So `canonical_path` accepts a `--root` spelled in another case.
  - The tool and the helper then both say "outside the root", although the tool lies inside it.
  - The same string rule decides which other preloaded root modules a tool refuses. Such a root would
    not see a module whose path is spelled as on disk.
- **Effect.** None at C. The helper mirrors the tools, so the test is right in both places, and both
  runs passed.
- **Recommendation.** Carry to S6: the freeze gives every `--root` in its on-disk spelling, as the
  observation plan binds the worktree, and the freeze's review checks it. A code change, if one is
  wanted, belongs to a later phase.

## 4. Files in `<local>/c271-p35/workers/W3-tooling-003/`

**The reports:**
- `TOOLING-REVIEW-003.md` and `TOOLING-REVIEW-003.json`.

**My scripts** (`scripts/`):
- `w3r3_common.py`, `w3r3_digests.py`, `w3r3_state.py`, `w3r3_proc.py`;
- `w3r3_analysis.py`, `w3r3_clone_check.py`, `w3r3_privacy.py`, `w3r3_assemble.py`.

**Their outputs** (`outputs/`):
- `digests.json`, and `diffs/`, which holds the unified diff of each changed file, of
  `AUTHOR-NOTES.md` and of `SHA256SUMS.txt`;
- `analysis.json` and `analysis-summary.txt`;
- `clone-check.json`;
- `privacy-delivery.json`, `privacy-own.json` and `privacy-runs.json`;
- `proc-baseline.json`, `proc-after-runs.json`, `proc-final.json` and `proc-last.json`;
- `state-compare-before-after.json` and `state-compare-after-final.json`;
- `suite-rerun.labelled.txt` and `suite-in-place-clone.labelled.txt`.

**The state snapshots** (`state/`):
- `before.json`, `after.json` and `final.json`.

**The runs** (`runs/`, local only, with machine paths):
- my rerun: `suite-rerun.raw.txt`, with its start, end and exit files;
- the clone run: `suite-in-place-clone.raw.txt`, with its start, end and exit files;
- the two temporary directories of those runs, `tmp-suite/` and `tmp-clone/`, both empty.
