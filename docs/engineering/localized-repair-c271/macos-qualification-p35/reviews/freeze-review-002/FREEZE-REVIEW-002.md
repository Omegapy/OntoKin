# Freeze review 002: operational freeze 002 of gate MH

C271-P35, gate MH, stage S6. Reviewer: W3, a Claude Code subagent in a fresh context with the session's
model. I wrote none of the freezes, the tooling, the observer, the provider, the probe, the contract or MP's
preparation, and I took no part in freeze review 001; I read its records as documents. Written 2026-11-27
(UTC), from 09:25:49Z to 09:58Z, at commit C (`0eb9a551`, tree `ea10cd94`), in the boot
`C90010BA-4DA9-475D-BBAB-CF1A9C40175A`.

Paths use the labels `<worktree>`, `<local>`, `<prefix>`, `<home>` and `<package-manager>`. Below, `<E>` is
`<local>/c271-p35/evidence`, `<F1>` is `<local>/c271-p35/workers/W2-freeze-001`, `<F2>` is
`<local>/c271-p35/workers/W2-freeze-002`, `<R1>` is `<local>/c271-p35/workers/W3-freeze-001` and `<OUT>` is
this review's directory `<local>/c271-p35/workers/W3-freeze-002`. Stop rules are numbered from 1, as the
freeze's prose numbers them; JSON pointers count from 0.

## Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS

Freeze 002 does what disposition 001 requires. Both mandatory findings of review 001 are resolved: the outer
bound is now executable with the shell tool's background mode, a frozen timer and frozen capture commands
(FR-01), and every `.L` and `.P` predicate is evaluated by its command's `.X` (FR-02). The difference record
lists every change. The main path of S7 is sound: every main command's complete `expect` is satisfiable, and
the checker, P00 and the bindings all pass now.

My six findings are all nonmandatory. Two of them, FR2-01 and FR2-02, concern the failure path: a pointer in
overrun step 3, and the class of a `.P` target whose start never happened. The Director should settle both
readings in the disposition, before S7, so that nobody has to decide during S7.

| Document | SHA-256 (computed here) | Size and mode |
| --- | --- | --- |
| `<F2>/FREEZE-002.json` | `bc35d6347608f7e04d9968957fa9888bee983c51ff12f2a3799e02733a82a621` | 1,329,283 bytes, 27,142 lines |
| `<F1>/config/cohort-config-001.json` (the cohort configuration) | `83c8b1582c1ea4263d60014ca6b4cd22130e57b3fb65e06ff60a78768a5d7a3c` | 2,014 bytes, `0o644` |
| `<R1>/MC11-REVIEWED-LIST-001.json` | `aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800` | 344,283 bytes, `0o644`, one link |
| `<F2>/SHA256SUMS.txt` (P00's first list) | `0f441f5f9c4246c4422d5d67fb9365e476958d5f51ac7b7eabf8be587409ca4b` | 82 lines |
| `<F2>/s7/p00-freeze-001-rebound.sha256sums.txt` (P00's second list) | `6912e1768e0d760a37e7c76d948f0b3839b4c525f3650f2d18345d7d341d4ef4` | 7,369 bytes, `0o644` |
| `<F2>/FREEZE-002-DIFFERENCES.json` | `df7ae291bed508ef14c9367cf6f46827be1b2ef0378a99a30660558e9803bb83` | |

**The Director's values from 09:13Z, recomputed** (`records/01-state.json`, and again at the end in
`records/11-final-state.json`):
- Freeze 002's SHA256SUMS: 82 of 82 verify, none unlisted, none missing.
- Freeze 001: 85 of 85 verify, none unlisted, nothing newer than its SHA256SUMS.txt (07:22:09Z).
- Review 001's records: the MD `af2ea72c…`, the JSON `282188cc…` and the list `aade03ac…`, as the disposition
  records them. Nothing in `<R1>` is newer than 08:26:52Z.
- The disposition: `6eedbff5…`, 11,599 bytes.
- The evidence parent: inode 15728417, 21 entries, modified 05:35:19Z, nothing newer, and no `s7-` path.
- The worktree: no bytecode, `__pycache__` or `.DS_Store` outside `.venv`. Its newest entry is from 04:16:54Z.
  I started no Git.
- The boot is unchanged.

## 1. Method, and every start

I read FREEZE-002.json in full, partly through compact listings that my scripts printed and I read whole. I
also read:
- the difference record;
- the author's notes, as a map only;
- FREEZE-001.json's changed parts, review 001's MD and its findings in JSON, and the disposition;
- MH-PLAN sections 5 to 8, FAILURE-CAPTURE in full, and the README's `capture_probe.py` section;
- `capture_probe.py` in full, the checker in full and the wrapper in full;
- the parts of the collector, the harness, the runner, the provider, both supervisors, `tools/check_local.py`
  and the cohort module that the new predicates rely on;
- `/usr/bin/shasum` (a Perl script, version 6.02), and the conditions of the framework's `subprocess.py`
  under `<prefix>`.

My scripts are in `<OUT>/scripts/` and their records in `<OUT>/records/`:

| Script | What it does |
| --- | --- |
| `w3f2_01_state` | The state at the start: both freezes' sums, review 001's records, the disposition, the wrapper, the evidence parent, the worktree and the boot. |
| `w3f2_02_bindings` | Recomputes all 122 bindings: lstat kind, SHA-256, size, mode, link count, canonical form, and each component in its parent's listing. Compares them with freeze 001's 120, and the reader tree with the dependencies inventory. |
| `w3f2_03_commands` | Checks all 97 commands: records, `wrapper_argv`, `shell`, `timer_shell` against the template, the `env -i` sets, `-B`, placeholders, absent paths and multi-key rules. Also each command against freeze 001, the `expect` composition, the rebuilt wrapper predicates, and the difference record's `changed_fields`. It writes a listing of every command. |
| `w3f2_04_overrun` | Checks the candidates against each `.P`, and each `select_shell` against a text generated from the candidates. Simulates every subset of recorded pairs through an exact interpreter of that text. Checks every probe and stop command against `capture_probe.py`'s interface, and step 3's pointer against each probe's target order. |
| `w3f2_05_diff` | My own comparison of the two freezes, leaf by leaf. |
| `w3f2_06_absent` | Recomputes both absent lists from the commands and the preparation. |
| `w3f2_07_texts` | Shows the `jq -r` extractions equal to the freeze's strings, and token-scans the timer and selection texts. Builds the synthetic timers. |
| `w3f2_08_late_exit` | A synthetic command for timer test t3. |
| `w3f2_09_checker_tests` | Loads the checker from its bound bytes, after checking `eb96aa1a…`. For each of C01 to C19 it builds a synthetic world in `<OUT>` where the whole frozen `expect` holds, then mutates the FR-02, FR-03 and FR-12 parts. It also runs the checker's `main()` in phases `expect` and `prepared`. |
| `w3f2_10_p00_lists` | Checks P00's two lists against freeze 001's lines and the bindings, the preparation's counts, and every absolute path that a command names. |
| `w3f2_11_final_state` | The state after my work, and the SHA-256 of every file I reviewed. |

**Every start**, counted from my transcript:
- **Shell-tool calls:** 101, each a `/bin/zsh -c` of the session's tool. Four ran in background mode: the three
  synthetic timers and my synthetic command.
- **Python:** 17 starts of `<worktree>/.venv/bin/python`, every one with `-I -S -B`.
  - **My scripts: 14.** `w3f2_04` and `w3f2_09` each stopped once on a fault in my own code, a `ValueError` and
    a `FileNotFoundError`. Run 2 of `w3f2_09` could not build C14's world, whose `equals_from` sources are
    other commands' files. Run 3 built them; its record is `09-checker-tests-run3.json`.
  - **The checker, `w2f_s7_check.py`: 1.** Phase `pre` against FREEZE-002.json, run directly through
    `/usr/bin/env -i` with the declared environment, after I checked its bytes. It gave `MET`, exit 0. In
    process, inside `w3f2_09` run 3, it ran 111 cases, 26 of them through its own `main()`.
  - **W2's self-check: 1.**
  - **The observer's `python-inventory`: 1**, the last Python start.
- **Other starts:**
  - **The texts:** `/bin/sh -n` 100 times and `/bin/zsh -n` 100 times, on the 97 timer texts and the 3
    selection texts as `jq -r` printed them; `/bin/zsh --version` once.
  - **The selection texts:** each of the three real ones once, in the tool's foreground. Each printed
    `overrun-select: none`. I confirmed byte for byte that what I passed is the frozen text.
  - **The timer template:** three synthetic runs, t1, t3 and t4, in `<OUT>/timer-test/`. They made about 13
    `/bin/date` and 7 `/bin/sleep` starts. My own three time stamps added 3 `/bin/date`.
  - **`/usr/bin/shasum`, which is Perl: 5.** P00's exact argv once, cwd `<F2>`, no wrapper, its streams into
    `<OUT>`; the other four hashed files.
  - **`/usr/bin/env`: 3.** The checker, P00 and `python-inventory`.
  - **`/usr/bin/jq`: about 176 reads.** 101 of them extracted the texts.
  - **Read-only utilities:** `ls`, `cat`, `grep`, `sed`, `awk`, `head`, `wc`, `cut`, `tr`, `cmp` (4), `find`
    (1), `file` (1) and `mkdir` (my `<OUT>` subdirectories).
- **Never started:**
  - Node, and Git of any kind;
  - `ldd`, `codesign` and `otool`;
  - the observer's `observe`;
  - the runner, the collector, the harness, the discovery collector and the audit;
  - `capture_probe.py` and the wrapper;
  - the original preparation script and the project's test modules;
  - `ps`.
- **Writes:** only under `<OUT>`. Nothing was changed or created in the worktree, `<F1>`, `<F2>`, `<R1>`, `<E>`
  or MP's inputs. Nothing was downloaded or installed, and no Finder was used.
- **Inventory:** `python-inventory` after my work gives `c277bdd3ac6aa731…`, 776,209 bytes. That is HOST's and
  plan 001's frozen inventory, so no bytecode was written.
- **No process of mine is alive.** All four background tasks reported their exit, and every foreground call
  returned.

My scripts and records hold raw paths. Any portable copy of them needs the labels.

## 2. Findings

All six are **nonmandatory**.

### FR2-01, nonmandatory: overrun step 3's pointer `/targets/<k-1>` is wrong for 9 of the 17 probe commands

**What step 3 says.** "For each target … in state 'present, identity established' (its `/targets/<k-1>/state`
…), it starts that candidate pair's frozen stop command `<ID>.S<k>`."

**Why it fails.** A probe `<ID>.O<digits>` passes only the selected pairs, in candidate order. Candidate k
therefore sits at `/targets/<j-1>`, where j is k's place among the digits. The pointer is right only when the
digits form a prefix (1, 12 and 123). It is wrong for C16.O2, O3, O13 and O23, for C17.O2, O3, O13 and O23,
and for C19.O2 (`records/04-overrun.json`).

**When it matters.** The runner records only prefix sets, so this is reachable only in C17: a case fails
before its start, and C17 later overruns.

**What a literal reading does.** Take C17.O13. Candidate 3 sits at `/targets/1`, and `/targets/2` is `null`.
- Read by candidate, step 3 sends no stop to an established candidate 3.
- Read by position, it starts C17.S2, the stop of a pair the probe did not select. If that case started
  meanwhile and is established, the stop ends one of the remaining CPU starts, which `overrun.c17` says must
  be left alone.

The right reading is already frozen. Each O command's classification says "that pair's stop command", and
each target records its pair's paths.

**Before S7**, the disposition should state: for `<ID>.O<d1…dm>`, `/targets/<j-1>` is candidate `d_j`, and its
stop is `<ID>.S<d_j>`. A check that the target's `pair.started.path` equals that candidate's `after` path
confirms it. No tool changes.

### FR2-02, nonmandatory: a `.P` target whose start never happened is `unknown`, and two classes then apply

**How the state arises.** `capture_probe.py` gives the state `unknown` when a pair's records cannot be read.
That happens for:
- a row the runner did not run (`NOT_RUN` after a missed row: no directory, no `intent.json`);
- a row refused before its start (`intent.json` but no `started-1.json`);
- a cohort case that failed before its start (no `started.json`).

**What freeze 002 does with it.** The `.X` is then NOT_MET, which is right: S7 stops. But the new FR-02
classification row says "the command's evidence or start is UNKNOWN", and the `.P`'s own row says
`'unknown' => UNKNOWN`. These collide with designed classes:
- **`n04.if_absent`.** MC30-probe refuses with "Actual input identity differs", R2 stops and MC36 is
  `NOT_RUN`. C19.P's second target is then `unknown`, yet C19's own row classes the outcome CONTRACT, "not a
  plan error".
- **C16's row classes**, and **C17's "first unmet case's class decides"**, in the same way.

**Why it matters.** UNKNOWN is never relabelled, and it blocks every retry. FAILURE-CAPTURE section 2, which
the freeze's `classes.UNKNOWN` cites, gives UNKNOWN for a started record without a final receipt, among other
cases. A pair without records shows no start. As frozen, the Director must choose a class when writing the
capture record.

**Before S7**, the disposition should state this rule. A target that is `unknown` only because its pair's
records do not exist does not by itself make the outcome UNKNOWN, provided the main command's own records
show that the start never happened:
- the runner's `NOT_RUN`, or `REFUSED_BEFORE_START` with `PROVEN_ZERO`;
- a case with no `started.json` and zero starts in its ledger.

The main command's own class then applies. A target that is `unknown` for any other reason stays UNKNOWN.
This reading existed in freeze 001's prose; FR-02 now makes it part of every `.X`.

### FR2-03, nonmandatory: the launch's corner cases are not stated

**(a) Order and approval.** The timer counts from its own start, so the bound holds only if both calls start
together. In my session, the two calls of one message started within the same second, as test t3 showed.
- If either call waits for a permission prompt, the timer runs ahead of the command or behind it. Running
  ahead gives a false overrun. That makes the command UNKNOWN and stops S7: before any Node start for C08 or
  C10, but after them for C16, C17 or C19.
- If either call is refused, as the tool refused W2's call with a Git start in this phase, the freeze does not
  say what follows.

Before S7, the Director should confirm that no command or timer call will wait for approval. It should place
the command's call first in each message, and treat a refused or failed call as an outcome that stops S7
under stop rule 4. With that, `overrun.limits`' "never the reverse" holds within the launch skew.

**(b) Timing races.**
- **An outer-bound line near the task's end.** Whether that line came "while the task is still running" must
  be decided from records, for example the timer's `now=` against the wrapper's `end_epoch_s`. A line printed
  after the task ended has "no effect", but the Director "goes on" only after an exit-file line, which that
  timer will never print.
- **The wrapper's tail.** Once a timer has printed `exit-file`, nothing bounds the rest of the wrapper's run,
  which builds the record. No frozen step tells the owner if that task does not end. The same holds in step 6
  if the second timer prints `exit-file`.

**(c) The tool's label.** The tool reports a timer's status 1 as "failed", as test t4 showed. That is the
frozen `outer-bound` result, not a timer failure under `launch.after`. The printed line decides.

**Why nonmandatory.** None of these changes a passing S7. They arise only when a command takes about its
bound, which is 2 to 10 times its expected time, or when an approval intervenes.

### FR2-04, nonmandatory: stale or inaccurate texts

- **(a) The `.P` classifications.** C16.P's, C17.P's and C19.P's rows, unchanged from freeze 001, still
  describe an unfrozen stop, "`capture_probe.py stop --pair BEFORE AFTER --output <name>.stop.json`". Freeze
  002 froze the stops as `<ID>.S<k>`, with outputs `<name>.stop-<k>.json`, in stop rule 4 and overrun step 3.
  The stale output path is in no absent list. The stop rules govern, and the Director must not build that
  argv. The revision should have updated these rows; the difference record omits them because only their
  timers changed.
- **(b) The wrapper's exit file.** `launch.after` and the notes say a wrapper exit of 90, 91 or 92 leaves no
  exit file. Exits 91 and 92 come after `run_once_v2.sh` writes `NAME.exit.txt` at line 31, before lines 34
  and 51. The timer therefore prints `exit-file` for them. This is harmless, because stop rule 11 governs 91
  and 92.
- **(c) The group.** `launch.command` gives the reason for passing the string alone: "so that zsh -c runs one
  simple command and the wrapper leads its group". In my background test, the program the call started was
  not its group's leader: pid 24998, process group and session 24996. The tool's zsh leads the group, and the
  command runs beneath it. No step of freeze 002 signals that group, so nothing depends on this.
- **(d) The difference record.** Its `where` lists miss `/trees` (A-4) and `/limits/this_freeze/7`, the
  overrun limits. Its mechanical section and its stated additions cover both.

### FR2-05, nonmandatory: what P00 itself trusts

**What runs before any check.** The Director reads P00's `shell` and `timer_shell` from FREEZE-002.json before
anything checks that file.

**What P00 does not check.** P00 checks freeze 002's files against SHA256SUMS.txt, which nothing checks. The
wrapper runs P00 before P01 checks the wrapper's binding.

**What is still caught.**
- An accidental change is caught by P00, and then at P01 by the checker's freeze digest and the bindings.
- A changed wrapper is caught at P01, before anything else runs.
- A change of SHA256SUMS.txt made consistently with a file it lists is not caught by P00 alone.

**Recommended.** Immediately before P00, the Director should compare the SHA-256 of FREEZE-002.json and of
SHA256SUMS.txt with this record (`bc35d634…` and `0f441f5f…`), as one read, and record it. These are limits
within FR-07's disposition; this review does not add to that disposition.

### FR2-06, nonmandatory: recorded, unbounded starts of the capture path

- `totals.capture_commands_only_on_failure` counts each capture command as "one Python launcher start". Each
  one also starts:
  - the wrapper's `/bin/sh` and `/usr/bin/env`;
  - the wrapper's `jq`, `shasum` (Perl), `date`, `sysctl`, `cut` and `stat`;
  - its own timer: a zsh, `date` and `sleep`.
- Step 1's second timer adds the same.
- `shell_and_env_launchers` counts only the 72 ordered commands.

None of these starts Node, and none is bounded. S8 should count them as recorded starts if they occur.

## 3. Answers

### 1. The disposition, finding by finding

| Finding | Disposition | In freeze 002 |
| --- | --- | --- |
| FR-01 (a) | Launch the `shell` member alone: `jq -r`, the named placeholders only, background mode, no timeout, one call per command, never retried | Carried out (`launch.read`, `launch.command`, stop rule 2) |
| FR-01 (b) | A frozen bound timer, started in the same message | Carried out. `launch.timer_template` is inline, so the freeze's digest binds it, and all 97 `timer_shell` are that template with the command's own exit file and bound (script 03) |
| FR-01 (c) | The six steps | Carried out: `overrun.steps`, with candidates, selection rule, 17 probes and 8 stops, and stop rule 10. Two stated additions, A-1 and A-3. Defect FR2-01 in step 3's pointer |
| FR-01 (d) | For C17, an FC-P6 stop may be followed by the remaining CPU starts | Carried out (`overrun.c17`, stop rule 6) |
| FR-01, the option not taken | Not interrupting the tool | Recorded (`overrun.not_taken`) |
| FR-02 | Append every `.L` and `.P` predicate; a `.P` in any state but absent stops S7 | Carried out for all 19 main commands, in full, and the checker is unchanged. Class question: FR2-02 |
| FR-03 | Bound every process event in C06, C07 and C17 | Carried out: each event is `subprocess.Popen`; `argv[0]` is one of the bound Node and the bound Git for C17, and the bound Git for C06 and C07. Classification rows added |
| FR-04 | C17's trio is one indivisible row | Carried out (stop rule 6, C17's row) |
| FR-05 | 25 directories, 18 files, 43 entries | Carried out in the notes. The preparation is unchanged, and I counted 43 = 25 + 18 |
| FR-06 | Each row as review 001 states it | Carried out. C02 splits the row by boot: in the same boot, IMPLEMENTATION; in another boot, HOST. C03 to C05, C13 (with C12's shared list), C17's positive case and setup, and C19 |
| FR-07 | P00 before P01: `/usr/bin/shasum -a 256 -c` on freeze 002's SHA256SUMS.txt and on freeze 001's for every rebound document | Carried out. P00 is first, runs through the wrapper, and is read from its exit file alone (stop rule 1, `launch.p00`). The second list is freeze 001's own lines for exactly the 44 rebound documents, with absolute paths, verified line for line. That is a faithful form: one call has one cwd, and freeze 001's list has relative paths and 41 other files. Plus `--strict` (A-2) |
| FR-08, FR-10, FR-11 | No change | None made. C09's and C11's stderr predicates are unchanged |
| FR-09 | A limit | Carried out (`limits.this_freeze`) |
| FR-12 | Name the CF file; check it after C17 and before C19 with existing predicate kinds, or record the gap | Carried out. `n04.assumption`; C17's `expect` holds `{file: <home>/.CFUserTextEncoding, sha256: bd605d2e…}`; the gap is stated |
| MC11 list | Bind it directly; keep FREEZE-002.json's digest deferred | Carried out. `review001:MC11-REVIEWED-LIST-001.json`; `deferred_inputs` is empty; C01's `argv[25]` is `aade03ac…`; C01.X's argv rule now compares index 25 literally, and the binding check and the scanner's own DIGEST check replace its `equals_sha256_of` rule |

**The difference record is complete.** My comparison (`records/05-diff.txt`) found changes in 25 top-level
members besides the commands, the absent lists and the bindings. Each falls under D-01 to D-14 or A-1 to A-7.
The record's per-command `changed_fields` equal mine for all 71 shared commands. Nothing changed that the
dispositions and stated additions do not cover. Two places are missing from the `where` lists (FR2-04 d), and
the `.P` classifications should have changed but did not (FR2-04 a).

**The stated additions:**
- **A-1, needed and correct.** Section 6, step 4 asks for a probe of every recorded start, and C17 may record
  starts after the overrun probe. The `.P` is frozen, reviewed and starts no Node.
- **A-2, needed and correct.** This shasum (6.02) counts a malformed line and only warns at the end, exiting 0
  when the remaining lines verify. With `--strict` it exits 1. `#` lines are skipped before the format check,
  so the second list's two comment lines pass.
- **A-3, needed.** It makes "never exits" executable, using the same frozen text. See FR2-03 (b) on an
  exit-file line from the second timer.
- **A-4, correct.** It is a `.DS_Store` check of a directory that holds bound inputs. Its bytecode flag is
  off, which is harmless.
- **A-5, correct and conservative.** A broken timer stops S7 after the command's own checks.
- **A-6, needed.** Q01 to Q04 must not observe a running command.
- **A-7, correct.** Phase `prepared` evaluates P00's 12 predicates (tested), and a `FAILED` line, a missing OK
  line or a shasum warning on stderr makes D02 NOT_MET.

All seven lie within the disposition's intent.

### 2. What did not change

- **48 of freeze 001's 71 commands** have byte-identical `argv`, `wrapper_argv` and `shell`.
- **The other 23** are the 19 `.X`, P01, D02, Q04 and C01. They differ only where stated:
  - at `argv` 13, the freeze's path, `<F1>/FREEZE-001.json` becoming `<F2>/FREEZE-002.json`;
  - at 15, the placeholder `<FREEZE-001.json SHA-256>` becoming `<FREEZE-002.json SHA-256>`;
  - for C01 only, at 25, `<MC11 reviewed list SHA-256>` becoming `aade03ac…`.

  Their `wrapper_argv` differs at the same positions plus 6, and their `shell` is the quoted `wrapper_argv`.
  Their rebuilt wrapper predicates equal freeze 001's after that substitution, in order.
- **The 30 commands listed as "only timer_shell added"** differ in `timer_shell` alone.
- **Bindings.** All 122 verify: lstat kind file, SHA-256, size, mode, one link, canonical, and every component
  as spelled in its parent's listing. The first 120 are identical, in order, to freeze 001's. The two new ones
  are correct:
  - the MC11 list: `aade03ac…`, 344,283 bytes, `0o644`;
  - P00's second list: `6912e176…`, 7,369 bytes, `0o644`.
- **The MC11 list's dependencies are unchanged:** the probe (`bca11b2a…`, 58,452 bytes), the dependencies
  inventory (`3545d5f9…`, 4,543 bytes) and the reader tree (24 files, each binding identical to freeze 001's
  and to the inventory's entry). The list's binding therefore holds. Its schema is `/2`, status `REVIEWED`,
  with 25 entries. I did not re-review the entries.

### 3. FR-01: the launch, the timer and the overrun procedure

**The launch** is executable as frozen:
- The Director reads each member with `launch.read`'s `jq -r`. The output equals the frozen string byte for
  byte, plus `jq`'s newline (100 of 100).
- The only placeholders are `<FREEZE-002.json SHA-256>` and C14's two digests. Each sits inside single quotes,
  no `argv` element holds a quote, and every `deferred_arguments` index is right, with the wrapper index at +6.
- Background mode has no timeout and notifies on exit. There is one call per command, and one per timer.

**The timer:**
- **Its exit file and bound.** For all 97 commands, `f` is exactly the command's `records.exit`, the wrapper's
  `<E>/NAME.exit.txt` with the same `<E>` and NAME, and `b` is its `limits.outer_bound_s` (120, 300 or 600).
- **It never fires early, measured from its own start.** It prints `outer-bound` only when
  `floor(now) > floor(start) + b`, that is, more than b seconds after its first `date`. Against the command's
  start, the skew of the two calls applies (FR2-03 a). It polls about once a second, so it reports an overrun
  at most about two seconds late.
- **Its lines and statuses, in synthetic worlds in the tool's background mode:**
  - t1, exit file present: `bound-timer: exit-file …`, status 0.
  - t3, exit file written by my synthetic command 3 s after it started in the same message:
    `exit-file … now=…257`, status 0.
  - t4, bound 3 and no exit file: `bound-timer: outer-bound began=1795772243 now=1795772247 bound_s=3`,
    status 1.
  - The `no-clock` branch, status 2, I read statically: an empty or non-numeric `date` matches
    `''|*[!0-9]*`.
- **Syntax.** `/bin/sh -n` and `zsh -n` pass for all 97 instances.
- **What it starts.** A token scan finds only `/bin/date` and `/bin/sleep` as programs, the builtins `[`,
  `printf`, `:` and `exit`, no redirection, pipe, `eval`, `exec`, `trap` or `kill`, and `$(…)` only around
  `/bin/date +%s`. It writes nothing; its stdout goes to the tool's task file.

**The `select_shell` texts:**
- **Exact.** Each equals, byte for byte, a text generated from its command's candidates.
- **Correct for every subset.** My interpreter of that exact grammar maps every subset of recorded started
  records (8, 8 and 4) to `overrun-select: <ID>.O<digits>`, with the digits ascending, or to `none`.
- **Builtins only.** They use builtins only, write nothing and pass both `-n` checks.
- **Run once each.** Each printed `overrun-select: none`; no `s7-` path exists.
- **Matching the probes.** The candidates equal each `.P`'s pairs in order.

**The 25 capture commands** match `capture_probe.py`'s parser:
- `probe --pair B A [--pair …] --output O`, and `stop --pair B A --output O`, each with one pair, since its
  `--pair` is not `action=append`.
- The prefix is the declared environment, then the venv's Python with `-I -S -B`.
- Each probe passes exactly its digits' candidates in order, and each stop exactly its candidate.
- Each output is `<E>/<main name>.overrun-probes-<digits>.json` or `.stop-<k>.json`: absent now, in both
  absent lists, in a canonical existing directory.
- Each has a bound of 120 s and cwd `<E>`.

**FC-P6's identity rule** is the tool's own:
- `stop` re-establishes identity before SIGTERM and again before SIGKILL: the start time in the window between
  the two records' modification times, the image equal to `argv[0]`, and the group equal to the PID.
- It refuses a recorded process that is itself, its parent or its group.

So a stop started for the wrong pair sends nothing unless that pair's own process is established. That keeps
FR2-01 from ever signalling an unrecorded process, though it can still end a remaining CPU start.

**The six steps:**
- **Nothing is sent to the wrapper, the tool's task or its group.** The probes send signal 0 to the recorded
  PIDs and groups only. The stops signal only a recorded supervised group, which leads its own session
  (`start_new_session`) and is never the tool's zsh group, and only with identity established. No step uses a
  task stop.
- **Against FAILURE-CAPTURE section 6:**
  - Only probes, stops, the `.L` and the `.P` are started, which are steps 3 to 5.
  - Every start reads the boot.
  - The probe comes before FC-P6 (step 4).
  - The readback (step 5) follows the wrapper's exit.
  - The capture record (6) follows; then the stage stops (7).
  - A-1's `.P` repeats step 4 for later starts, in the normal path's `.L`-then-`.P` order.
- **Against section 8.** The capture record will hold two probe records, the overrun probe and the `.P`. Its
  `probes` member can list both.

**The Director can carry it out with the shell tool's facts.** Every step uses background calls,
notifications, foreground reads (`jq`, the selection text) and frozen commands. No step needs a signal, a
task stop, a foreground wait or a sleep. FR2-01 needs a stated reading; FR2-03 needs the order and
no-approval preconditions.

### 4. FR-02

Every main command's `expect` is freeze 001's `expect` (C01 after the stated substitution), then the FR-03 and
FR-12 predicates, then its `.L`'s 12 predicates in full. For C16, C17 and C19 the `.P`'s 12 follow. The `.L` and
`.P` lists are unchanged from freeze 001.

**The `.P` predicates** are a `length` of 3 (C19: 2) on `/targets`, and a separate
`each {pointer: /state, equals: absent}`. There is no two-key rule anywhere in the freeze, and every `each` on
`/targets` is paired with a `length`.

**Against the unchanged checker** (eb96aa1a, its bytes loaded in process), every one of these gives NOT_MET:
- a target `present, identity established`;
- a target `present, identity not established`;
- a target `unknown`;
- a target without a state;
- one target fewer;
- a refusal document in place of the record;
- a missing probe record, exit file or listing record;
- a probe exit of 2;
- a process event in the probe;
- another `boot_after`;
- another tool digest in the `.L`.

That holds for C16, C17 and C19, through `check_predicate` and through `main()`. A process event in a `.L` is
NOT_MET too. The base worlds are MET for all 19 main commands, so the appended predicates contradict nothing
(`records/09-checker-tests-run3.json`, 111 of 111 cases as expected). On what a non-absent target means for
the class, see FR2-02.

### 5. The other changes

- **FR-03.** C17: each `/process_events` item has `/event` equal to `subprocess.Popen`, and `/argv/0` one of
  the bound Node and the bound Git. C06 and C07: the same, with the bound Git alone.
  - **What the predicates rely on.** The collector and the harness describe a Popen as
    `{event, executable, argv, …}`. `git_read` passes `git_executable()`, the selection's canonical path, as
    `argv[0]`. The supervisor's Popen is `start_new_session=True`. On this Python (3.12) `posix_spawn` is used
    only without `close_fds`, so no `os.posix_spawn` event appears.
  - **Tested NOT_MET:**
    - `os.posix_spawn`, `os.exec` and `ctypes.dlsym` events;
    - a Popen of `/bin/sh`, of `git` by name, or of `/usr/bin/true`;
    - a fourth Node start, or a Node start in C06;
    - an event without `argv`.
  - **Vacuous on an empty list.** An empty list is MET for C06 and C07; their Git counts of 15 and 25 stay in
    `audit_expect`.
- **FR-04.** Stop rule 6, and C17's row: the remaining CPU starts run, C17.X is NOT_MET, C18 and C19 do not
  run, and the first unmet case's class decides.
- **FR-05.** 25 directories and 18 files, 43 entries.
- **FR-06.** The rows are as listed in answer 1. They change no action.
- **FR-07.**
  - **`--strict`** in this shasum: see A-2.
  - **P00's run.** P00's exact argv, run once in `<F2>` without the wrapper, gave exit 0, 126 `OK` lines (82
    plus 44), empty stderr and no `FAILED`. Its three required lines are present.
  - **The two lists.** The first covers every file of freeze 002, the second list among them. The second
    covers the 44 rebound documents, the checker and the preparation script among them.
  - **Coverage of what S7 runs or reads.** Every absolute path that a command names falls in one of these
    classes:
    - in P00's lists, or bound and checked by the checker at P01, D02 and Q04;
    - a prepared copy, checked by D02;
    - an S7 output;
    - the venv or the framework, through the Python inventory at P02 to P04 and Q01;
    - the worktree at C, through P05 and the source inventory;
    - an OS file, which no freeze binds (contract section 10);
    - the main clone's Git directory, which `git archive` reads by object ID.

    The exceptions are the wrapper and FREEZE-002.json at P00 itself (FR2-05). The MC11 list is outside P00
    but bound, and `scan_mc11` checks its digest.
- **FR-09.** The limit is present.
- **FR-12.**
  - **The predicate.** `{file: <home>/.CFUserTextEncoding, sha256: bd605d2e…}` in C17's `expect`, evaluated
    by C17.X after C17, C17.L and C17.P, and before C18 and C19. A file of content `0x0:0x0` hashes to
    `bd605d2e…`.
  - **Tested NOT_MET:** another content, a trailing newline, an absent file.
  - **Tested MET:** mode `0o600` with the same content. That is the stated gap: the checker's `expect` has no
    mode, link-count or user predicate. P01, D02 and Q04's `host_facts` check mode and link, and each admitted
    value's `0x1F5` carries the user.

### 6. Totals and paths

- **The absent lists.**
  - **495 before the preparation.** That is every record and output that any of the 97 commands names, plus
    the 43 prepared entries, minus P00's and P01's own 8 records.
  - **428 after.** That is the named paths minus the 32 records of P00 to D02.
  - **Against freeze 001.** Exactly freeze 001's 370 and 303, plus the 125 capture paths: 25 commands with 5
    paths each. P00's 4 records are in neither list. The wrapper's own refusal (exit 90) and P00's absence now
    cover them.
  - **Their properties.** Each list is unique and sorted, lies under `<E>`, and is absent now.
- **The starts:**
  - **S7, bounded.** Node 8 (C16 3, C17 3, C19 2) and other 1 (C15), from the commands' `starts` members.
  - **MH.** Adding S5's 1 and 1 gives 9 and 2. MH-PLAN expects 8 and 2; MC30-probe is the ninth, as review
    001 accepted.
  - **Python launchers.** 64 among the 72 ordered commands. The 8 others are P00, P05, D01, C08 to C11 and
    Q03.
  - **Recorded and unbounded.** Provider Git reads 100 (15, 25, 60), the Director's Git reads 4, and tar 2.
- **The capture commands.** 25 Python launchers, run only on failure. None starts Node. See FR2-06 for their
  wrapper and timer starts.

### 7. Q2-1 to Q2-8

- **Q2-1.** Yes. A-1 stays within the disposition's step 5, as the answer on A-1 says. It is needed for C17's
  later starts.
- **Q2-2.** Yes, verified in the source and in P00's run.
- **Q2-3.** Acceptable, with FR2-03 (b): if the second timer prints `exit-file` and the task still does not
  end, nothing tells the owner.
- **Q2-4.** Correct. The freeze's digest binds the timer, and P00's own timer runs before any file is
  verified. It never fires before b whole seconds after its own start. Its skew against the command is FR2-03
  (a).
- **Q2-5.** Harmless, and it keeps the selection total. But 9 of the 17 probes meet FR2-01's pointer.
- **Q2-6.** Correct. The lines equal freeze 001's, verified. The environment is PATH only, and the output is
  ASCII.
- **Q2-7.** Correct and acceptable. Content is what HOST's value depends on; mode and link are checked at P01,
  D02 and Q04.
- **Q2-8.** Acceptable. The MC11 list's own binding covers its bytes. No tool reads `<R1>` as a directory.

### 8. Anything else

**For the Director, before S7:**
- Take FREEZE-002.json's digest from this record with `jq` (`freeze_sha256`), and compare the file and
  SHA256SUMS.txt with it before reading P00 (FR2-05).
- Record in the disposition the readings of FR2-01 and FR2-02.
- Confirm the launch preconditions of FR2-03 (a).
- Treat the `.P` rows' stop text as superseded by `<ID>.S<k>` (FR2-04 a).
- Keep the MC11 list, the probe, the dependencies inventory and the reader tree unchanged until C01, as
  before.

**For the auditor:**
- The `.X` commands' own predicates and the capture commands' `expect` are evaluated by no step during S7, as
  in freeze 001. They are for S8.
- FR-03's `each` is vacuous on an empty list for C06 and C07.
- FR-12's gap, as stated.
- FR2-02's class reading.
- A capture record after an overrun may hold two probe records.

## 4. Files in `<OUT>`

- `FREEZE-REVIEW-002.md` and `FREEZE-REVIEW-002.json`: this review.
- `scripts/`: `w3f2_01_state.py` to `w3f2_11_final_state.py`.
- `records/`:
  - `01-state.json`, `02-bindings.json`, `03-commands.json` and `03-commands-listing.txt`;
  - `04-overrun.json`, `05-diff.json` and `05-diff.txt`, `06-absent.json`;
  - `07-texts.json`, `07-syntax.txt`, `07-select-real-runs.txt` and the `texts-pasted-*.select.txt` checks;
  - `texts/`, the 100 extracted texts;
  - `09-checker-tests-run3.json`, the complete run; `09-checker-tests.json` is run 2;
  - `10-checker-pre-real.*`, the checker against FREEZE-002.json;
  - `10-p00-lists.json`;
  - `11-p00-run.*`, P00's argv;
  - `11-final-state.json`, which holds the SHA-256, size and mode of the 36 files I reviewed and of the 122
    bound files;
  - `12-w2-selfcheck-crosscheck.*`: 2,483 checks, 0 failed, byte-identical to W2's record;
  - `python-inventory-after-W3F2.*`.
- `timer-test/`, `checker-test/` (run 1, partial), `checker-test-run2/` and `checker-test-run3/`: the synthetic
  worlds.
