# Operational freeze 002 of gate MH: the author's notes

Gate MH (C271-P35), stage S6, for S7. Author: W2, the author of freeze 001, revising it under disposition 001 of
freeze review 001. Labels: `<local>` is the local data root, `<worktree>` the C271 worktree, `<home>` the owner's
home, `<prefix>` the package manager's prefix. `<E>` is `<local>/c271-p35/evidence`, `<F1>` is
`<local>/c271-p35/workers/W2-freeze-001`, `<F2>` is `<local>/c271-p35/workers/W2-freeze-002` (this directory), and
`<W3>` is `<local>/c271-p35/workers/W3-freeze-001`. The JSON documents keep their real paths.

## Identity and status

- `FREEZE-002.json`: SHA-256 `bc35d6347608f7e04d9968957fa9888bee983c51ff12f2a3799e02733a82a621`, 1,329,283 bytes,
  as the author computed it. Its digest stays deferred: the Director takes it from the record of freeze review 002
  (placeholder `<FREEZE-002.json SHA-256>`).
- Status `FROZEN_NOT_RUN`. Nothing of freeze 001 or 002 has run, and no S7 path exists.
- `revision_of` binds freeze 001 (`a5d994ea…`, 884,666 bytes), its `SHA256SUMS.txt`, both review records and the
  disposition by SHA-256. Freeze 001 stays unchanged in `<F1>`.
- Attempt `s7-001`'s paths are kept (revision rule 4). Freeze 002 adds only P00's four records and the capture
  commands' 125 records and outputs.

## 1. The changes, finding by finding

`FREEZE-002-DIFFERENCES.json` lists every change (D-01 to D-14), each with its finding or rule. It also holds a
mechanical comparison with freeze 001.

| Finding | Change |
| --- | --- |
| FR-01 (a), (b) | `launch` (new). Every command, whatever its phase, runs as its `shell` member alone, in background mode with no tool timeout. Each command gains `timer_shell`, the bound timer (section 2). |
| FR-01 (c), (d) | `overrun` (new) replaces stop rule 9 with the six steps (section 3). There are 25 capture commands: 17 probes `<ID>.O<digits>` and 8 stops `<ID>.S<k>`, each with its argv and absent outputs. C16, C17 and C19 each gain an `overrun` member: candidates, `select_shell`, and the IDs of their probes and stops. |
| FR-02 | Each main command C01 to C19 appends its `.L`'s expect to its own, in full. C16, C17 and C19 also append their `.P`'s. Its `.X` evaluates them all. A `.P` target in any state but `absent` stops S7 (stop rule 4). The checker is unchanged. |
| FR-03 | C17's process events: every one is `subprocess.Popen`, with `argv[0]` the bound Node or the bound Git. C06 and C07: `subprocess.Popen` of the bound Git only. |
| FR-04 | C17's three CPU starts are one indivisible row: stop rule 6 (MH-PLAN section 8), C17's classification and `overrun.c17`. |
| FR-05 | The preparation has 25 directories and 18 files: 43 entries. My notes for freeze 001 said 26 and 44; that was wrong. Nothing in the preparation changes. |
| FR-06 | New classification rows, each as the review states it: C02, C03 to C05, C13 (also C12's shared list), C17's positive case and setup, and C19. |
| FR-07 | P00 runs first (section 4). |
| FR-09 | `limits.this_freeze`: the driver's default temporary-cohort path is not exercised. |
| FR-12 | `n04.assumption` names the user and `<home>/.CFUserTextEncoding`. C17's expect checks the file's SHA-256 after C17 and before C19. Its mode, single link and user cannot be expressed in an expect predicate. P01, D02 and Q04 check the mode and the link. |
| FR-08, FR-10, FR-11 | No change, as disposed. |
| MC11 list | Bound directly: binding `review001:MC11-REVIEWED-LIST-001.json`, `aade03ac…`, 344,283 bytes, `0o644`. `deferred_inputs` is now empty. C01's argv carries the digest at index 25, so C01's wrapper predicates are rebuilt. |
| Freeze digest | P01, D02, Q04 and every `.X` name `<F2>/FREEZE-002.json` and `<FREEZE-002.json SHA-256>`. C14's two discovery digests stay deferred as frozen. |

Every other argv, wrapper argv and `shell` string is byte-identical to freeze 001's: 48 of its 71 commands (the 23
changed are the 19 `.X`, P01, D02, Q04 and C01). Every
unchanged document is rebound at its `<F1>` path. Freeze 001's 120 bindings are kept unchanged, and two are new
(the MC11 list and P00's second list).

**Stated additions, for freeze review 002** (`stated_additions`, A-1 to A-7):
- **A-1.** After an overrun, once the wrapper exits, the command's `.P` runs as well as its `.L`. FR-04 (d) allows
  starts after the overrun probe, and section 8's capture record needs a probe of each recorded start.
- **A-2.** P00 passes `--strict`. Without it, this shasum (Perl, 6.02) silently skips a malformed line.
- **A-3.** A second run of the command's own timer makes "never exits" executable.
- **A-4.** `<F2>` is a tree root.
- **A-5.** The launch states what every timer output means.
- **A-6.** Q01 to Q04 wait until every wrapper has exited.
- **A-7.** D02 re-checks P00's streams.

## 2. The launch and the bound timer

- **Read and pass.** The Director reads each member raw with
  `jq -r --arg id ID '.commands[] | select(.id == $id) | .shell'` (or `.timer_shell`). It replaces only the named
  placeholders and passes the string alone.
- **Background calls.** The command and its timer start in the same message, both in background mode. There is one
  call per command, never retried.
- **What the timer is.** The timer is inline text in the freeze, not a file. It is bound with the freeze, so no
  unverified file runs before P00. Its template is `launch.timer_template`, with the exit file and `outer_bound_s`
  substituted.
- **When it exits.** The timer exits at the first of two events:
  - the exit file exists: it prints `bound-timer: exit-file …` and exits with status 0;
  - more than `outer_bound_s` whole epoch seconds have passed since it began: it prints `bound-timer: outer-bound …`
    and exits with status 1. It compares with `-gt`, so it never fires early.
- **No clock.** If `date` gives no number, it prints `no-clock` and exits with status 2. That is a PLAN deviation
  (`launch.after`).
- **What it starts.** It starts only shell builtins, `/bin/date` and `/bin/sleep 1`, and writes nothing.
- **Going on.** The Director goes on only when the command's task has ended and its timer printed `exit-file`. A
  timer line printed after the task ended has no effect. A wrapper exit of 90, 91 or 92 leaves no exit file.

## 3. The overrun procedure (`overrun`)

**The six steps**, as disposed:
1. Record the overrun with its time. The outcome is UNKNOWN. Start the second timer (A-3).
2. Run the command's frozen `select_shell`. It uses builtins only and writes nothing. It prints
   `overrun-select: <ID>` or `none`. Start that one probe.
3. Run `<ID>.S<k>` once for each target in state `present, identity established`. Send nothing for any other
   state.
4. Send nothing to the wrapper, the tool's task or its group.
5. Wait for the wrapper to exit. Then run the command's `.L` and `.P` (A-1), write the capture record, and stop the
   stage. The `.X` is not run.
6. If the second timer ends first, tell the owner, keep waiting and start nothing.

**Candidates and selection:**
- The candidates are the `.P` pairs:
  - C16 and C19: each row's `intent.json` and `started-1.json`;
  - C17: each case's `preflight.json` and `started.json`.
- A candidate is recorded when its started record exists (`-e` or `-L`). The recorded candidates' 1-based numbers,
  in order, name the probe: `C17.O13`, for example.
- All non-empty sets are frozen: 7 each for C16 and C17, 3 for C19. The runner itself can record only the sets 1,
  12 and 123.

**C17.** An FC-P6 stop of one case may be followed by the remaining CPU starts.

**Limits** (`overrun.limits`):
- a start recorded after the selection is probed only after the wrapper exits;
- a start between its two records cannot be named;
- a command that ends at its bound may be reported as an overrun, never the reverse.

## 4. P00

- **The call.** One wrapper call in `<F2>`, with the PATH-only environment file (rebound `env/runner…`):
  `/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/shasum -a 256 --strict -c SHA256SUMS.txt s7/p00-freeze-001-rebound.sha256sums.txt`.
- **The second list.** It holds freeze 001's own lines for the 44 rebound documents, the checker and the
  preparation script among them, with absolute paths. The first list covers it, and the freeze binds it.
- **Which files.** The two lists cover every file of freeze 002 and every document it rebinds.
- **The decision.** The Director reads P00's outcome from its exit file alone.
- **D02's re-check.** D02 checks P00's exit, empty stderr, the three `OK` lines and the absence of `FAILED`.
- **Absent paths.** P00's records, like P01's, are left out of `before_preparation`, so the absent lists hold 495
  paths before the preparation and 428 after it. Freeze 001's were 370 and 303.

## 5. Totals: unchanged

| | Node | Other |
| --- | --- | --- |
| S7, bounded | 8 (C16 3, C17 3, C19 2) | 1 (C15) |
| MH | 9 | 2 |

The MH-PLAN table gives 8 and 2; MC30-probe is the ninth Node start.

Recorded but not bounded:
- **Unchanged:** provider Git reads 100, Director Git reads 4, tar 2.
- **Python launchers:** 64 for the 72 commands in order.
- **P00:** 1 shasum.
- **The capture commands:** up to 25 Python launchers, run only on failure. They start no Node.
- **The Director's side:** a zsh for each tool call, the timer's `date` and `sleep`, and `jq` reads.

## 6. Checks the author ran

| Check | Result | Record |
| --- | --- | --- |
| `w2f2_selfcheck.py` | 2,483 checks, 0 failed: structure, argv identity with freeze 001, appended predicates, P00 lists, bindings, absent paths, capture commands, selection texts | `author/records/selfcheck-002-001.txt` |
| `w2f2_checker_test.py`: the unchanged checker, in process, on a synthetic freeze in `author/checker-test-002/` | 22 of 22 cases as expected. FR-02's appended `.L`/`.P` predicates with each probe state and missing records; FR-03 with other programs, `os.posix_spawn`, missing keys, empty and null lists; FR-12 with the same, a changed and an absent file; C17's real expect without records | `author/records/checker-test-002.txt` |
| The timer and selection texts, read from FREEZE-002.json with `jq -r` | `zsh -n` and `sh -n` pass. The exit-file branch ran with status 0. The outer-bound branch ran with status 1, after 2 s at bound 1. A synthetic selection gave `C17.O13`. The three real selections give `none` | `author/timer-test/` |
| The checker, once, phase `pre`, on FREEZE-002.json | MET, exit 0: 122 bindings, 495 absent paths, trees, ancestors, CF file, boot, umask `0o022` | `author/records/check-pre-002.json` |
| The observer's `python-inventory` | `c277bdd3…`, equal to HOST's. One earlier run was refused at CHO-PATH (relative output path) before any write; its streams are kept | `author/records/python-inventory-*` |

After `SHA256SUMS.txt` was written, the author ran P00's argv once in `<F2>`, without the wrapper. Its result is in
the hand-back report only, so that `SHA256SUMS.txt` stays complete.

## 7. Open questions for freeze review 002

Q2-1 to Q2-8 in `open_questions`: A-1, A-2, A-3, the inline timer, the complete subset sets, P00's lists, FR-12's
gap, and A-4. Freeze 001's Q1 to Q11 moved to `answered_questions_001`, with review 001's answers.

## 8. Files

New or changed, in `<F2>`:
- `FREEZE-002.json`;
- `FREEZE-002-DIFFERENCES.json`;
- this file;
- `SHA256SUMS.txt`;
- `s7/p00-freeze-001-rebound.sha256sums.txt`, bound;
- `author/scripts/w2f2_build.py`, `w2f2_selfcheck.py` and `w2f2_checker_test.py`;
- `author/records/`;
- `author/checker-test-002/` and `author/timer-test/`: the synthetic worlds.

Everything else is rebound unchanged from `<F1>`: `config/`, `env/`, `probe/`, `fixtures/`, `mc10/`, `mc11/`,
`s7/w2f_s7_check.py` and `s7/prepare-s7-001.sh`.
