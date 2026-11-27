# Freeze review 001: operational freeze 001 of gate MH

C271-P35, gate MH, end of stage S6. Reviewer: W3, a Claude Code subagent in a fresh context with the
session's model. I wrote none of the freeze, the tooling, the observer, the provider, the probe, the
contract or MP's preparation, and no earlier review is in my context. Written 2026-11-27 (UTC), at
commit C (`0eb9a551`, tree `ea10cd94`), in the boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`.

Paths use the labels `<worktree>`, `<local>`, `<prefix>`, `<home>` and `<package-manager>`. Below,
`<E>` is `<local>/c271-p35/evidence`, `<F>` is the freeze directory
`<local>/c271-p35/workers/W2-freeze-001` and `<OUT>` is this review's directory
`<local>/c271-p35/workers/W3-freeze-001`.

## Verdict: REJECT_WITH_MANDATORY_FINDINGS

Two findings are mandatory. FR-01: the frozen outer-bound rule cannot be carried out on this host.
FR-02: no frozen step evaluates the predicates of the `.L` and `.P` commands, and the `.P` probes
come before Node starts. Both can be fixed with small, mechanical changes, which belong in a
corrected freeze 002. Everything else I checked holds. FR-03 to FR-12 are nonmandatory.

| Document | SHA-256 (computed here) | Size and mode |
| --- | --- | --- |
| `<F>/FREEZE-001.json` | `a5d994ea2db61262bf851379b9289ec028242bb7943d63df1992b3f386b634e6` | 884,666 bytes, 19,407 lines |
| `<F>/config/cohort-config-001.json` (D0) | `83c8b1582c1ea4263d60014ca6b4cd22130e57b3fb65e06ff60a78768a5d7a3c` | 2,014 bytes, `0o644` |
| `<OUT>/MC11-REVIEWED-LIST-001.json` | `aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800` | 344,283 bytes, `0o644`, status `REVIEWED` |

The Director's values from 07:23Z to 07:30Z are confirmed:
- SHA256SUMS: 85 of 85 files verify, and none is unlisted.
- The freeze and the configuration have the digests above.
- The boot is unchanged.
- The evidence parent's mtime is `2026-11-27T05:35:19Z`. Its inode is 15728417, it has 21 entries
  and no `s7-001` path.
- The worktree holds no bytecode, `__pycache__` or `.DS_Store` outside `.venv`. No entry in it is
  newer than my first file. Git I did not start.

## 1. Method, and every start

I read the freeze in full. I used its author's notes only as a map. I also read every document the
freeze binds and the sources it relies on:
- MH-PLAN, the tooling README and FAILURE-CAPTURE;
- sections 4 and 8 of the tooling author's notes, the three tooling reviews and the five
  dispositions, and N34-M-DISPOSITION;
- the four interface documents;
- the CONTROLS files: FROZEN, its `mc11_rule`, and REFREEZE-002;
- contract sections 5, 7 and 9 to 12, and P07 sections 2 to 8;
- the probe and the 0.2.0 provider;
- the facade's dispatch, lines 1054 to 1218;
- both supervisors, the cohort test module, MC37's test, and `tools/check_local.py`'s Git reads;
- all seven tools, the wrapper, and the S7 checker and preparation script;
- the Git configuration, info directory and attributes, read as files.

My scripts are in `<OUT>/scripts/` and their records in `<OUT>/records/`:

| Script | What it does |
| --- | --- |
| `w3f_01` | Hashes the freeze directory and maps FREEZE-001.json. |
| `w3f_02` | Recomputes all 120 bindings: lstat kind, SHA-256, size, mode, link count, canonical form, and every path component found in its parent's listing (TR3-03). Also the tool digests against `TOOLING-SHA256SUMS.txt`, HOST, completion and result, the adoption record, the wrapper, the CF file and the 12 environment files. |
| `w3f_03` | Structural checks of all 71 commands. `shell` must be the single-quoted `wrapper_argv`, and `wrapper_argv` the wrapper prefix plus `argv`. Also the placeholder indices, `-B`, the `env -i` assignments against the environment file, records and outputs against the absent lists, and the predicate key sets. It writes a compact listing of every command, which I read in full. |
| `w3f_04` | My own replay of the probe's `approvedEnvelope`, `verifyBootstrap`, `verifySource`, `verifyDependencies`, `verifyHost`, `environmentAdmitted`, `verifyMethods` and the main block up to the first reader import. It reads each row's own fixtures, under both assumptions about Node's environment. |
| `w3f_05` | JSON differences: each derived document against its source. |
| `w3f_06` to `w3f_08` | The MC11 comparison, grouping, route-class count, and the reviewed list (section 4). |
| `w3f_09` | Import-time references to `.git` or `.venv` in the test modules, found by AST. Nothing is imported. |
| `w3f_10` | The S7 checker, loaded from its bound bytes, run in one process on synthetic freezes inside `<OUT>`: 48 predicate cases and 31 phase and special cases. |
| `w3f_11` | Compares the preparation script with the freeze's entries. Also checks a rewritten copy that ran in `<OUT>`. |
| `w3f_12` | The state after my work, and the digests of the 145 files I reviewed. |

**Every start**, counted from my transcript:
- **Shell calls:** 66, each one `/bin/zsh -c` of the session's shell tool. They ran only `ls`,
  `grep`, `head`, `tail`, `cut`, `sed`, `awk`, `wc`, `cat`, `find`, `paste` and the starts below.
  The last one ran `/usr/bin/jq` once, to check this review's JSON record for syntax.
- **Python:** 35 starts of `<worktree>/.venv/bin/python`, every one with `-I -S -B`.
  - my own scripts: 15;
  - inline reads with `-c`: 12. One stopped on a `TypeError` in my own expression.
  - `scan_mc11.py` at C: 2, once without a reviewed list and once with my list;
  - `w2f_s7_check.py` against the real freeze, in phase `pre`: 1. Before that, I checked from its
    source that it writes nothing but its stdout. It also ran 79 times in process, inside
    `w3f_10`, on synthetic freezes in `<OUT>`.
  - the observer's `static`: 3, once with each MC10 plan, from `env -i` with the declared
    environment and without the wrapper. My cwd was `<OUT>`, not the evidence parent.
  - W2's self-check: 1;
  - the observer's `python-inventory`: 1, as the last Python start.
- **Other starts:**
  - 9 of `/usr/bin/env`;
  - 3 of `/bin/sh`. These were `-n` on the original preparation script and two runs of a copy whose
    evidence root I rewrote into `<OUT>/prep-test/`. The first run started 25 `/bin/mkdir` and 18
    `/bin/cp`. The second refused at its first check.
  - 2 of `/usr/bin/shasum`, which is a Perl script;
  - 1 of `/bin/ps`. Its listing was context only, under FC-P1, and showed no process of mine.
- **Never started:** Node, Git of any kind, `ldd`, `codesign`, `otool`, the observer's `observe`,
  the runner, the collector, the harness, the discovery collector, the audit, `capture_probe.py`,
  the wrapper, the original preparation script and the project's test modules.
- **Writes:** only under `<OUT>`. Nothing was changed or created in the worktree, `<F>`, `<E>` or
  MP's inputs, and nothing was downloaded or installed. No Finder was used.
- **Inventory:** `python-inventory` after my work gives `c277bdd3ac6aa731…`, 776,209 bytes. That
  is plan 001's frozen inventory. No process of mine is alive.

## 2. Findings

### FR-01, mandatory: the outer-bound rule cannot be carried out as frozen

The rule is stop rule 9: "a command still running after its `limits.outer_bound_s` is interrupted
once (SIGINT to its foreground group, as Ctrl-C does) … (a tool timeout at least 600 s)". On this
host it cannot be followed. Four facts stand in the way.
- **No terminal.** Each tool command runs as its own session and process-group leader, without a
  controlling terminal. There is no foreground group, and no Ctrl-C.
- **Foreground mode.** The Director is blocked until the command ends, so nothing can be sent at
  120, 300 or 600 s. The tool's own timeout is at most 600 s, and it ends the command by a means the
  Director does not choose.
  - C17's bound is 600 s, so the tool's timeout falls at the bound itself, and "nothing else ends it
    earlier" cannot be guaranteed.
  - If the tool sends SIGKILL to the group, the wrapper dies before `.exit.txt` and `.command.json`,
    and the supervisor's cleanup never runs. Node lives in its own session (`start_new_session`) and
    would survive.
- **Background mode.** The only group the Director could signal is the command's own, whose ID is
  the PID of the tool's shell, which the wrapper keeps through `exec`. No frozen record or tool can
  establish that group's identity:
  - the wrapper writes nothing that names its PID before the command ends;
  - every `argv[0]` in that group is a launcher whose image differs: `/bin/sh`, `/usr/bin/env` and
    the venv's `python`, whose image is the framework's `Python.app` binary (HOST's
    `process_image`). FC-P3 says such an `argv[0]` never establishes identity.
  - a `ps` listing is context only (FC-P1).

  Signalling that group would therefore break FC-P6. It would also break FAILURE-CAPTURE section 6,
  step 1, which admits no command outside steps 3 to 5.
- **One SIGINT does not reliably stop C17.** In the Darwin supervisor, `run_process` turns a
  `KeyboardInterrupt` into a `Stop` (`supervisor_darwin_v01.py` lines 197–206). The provider's
  `guarded_run_process` turns any `BaseException` into `CurrentHostBindingError` (lines 1116–1140).
  `check_case` then re-raises it as an ordinary test error, and unittest goes on to the next CPU
  method, which starts Node again. In the end the collector reports
  `COMPLETED_WITH_OTHER_OUTCOMES` (exit 1), not an interruption. The runner (C16, C19) does detect
  the interruption, through the `Stop`'s reason prefix (TR-18).

**Required change.** The smallest change has two parts, and it satisfies FAILURE-CAPTURE with FC-P6
first.

(a) Freeze the launch: the shell tool's background mode, with no tool timeout, passing only the
`shell` member, with only its named placeholders replaced.

(b) Replace stop rule 9 with this:
1. At `outer_bound_s`, record the overrun with its time. The command's outcome is UNKNOWN.
2. Start one `capture_probe.py probe` on every start pair the command has recorded so far:
   - the runner's `intent.json` and `started-<n>.json`;
   - the provider's `preflight.json` and `started.json`.
3. Run FC-P6's `capture_probe.py stop` only for a target in state "present, identity established".
   That can end a stuck supervised Node group.
4. Send nothing to the wrapper or the tool.
5. Wait for the wrapper to exit, then apply section 6, steps 5 to 7.
6. If it never exits, the attempt stays UNKNOWN and the owner is told.

The freeze must also say that for C17, an FC-P6 stop of one case may be followed by the remaining
CPU starts. Every supervised start is bounded at 30 s, so a C17 still running at 600 s is stuck
outside any start.

The Director may want the overrunning tool itself interrupted. Its group's identity must then first
be made establishable by a reviewed means, for example a frozen pre-start record that the launching
shell writes with its own `$$` before `exec`, and an identity rule for that record. That is new
procedure and tooling. It is not available at C.

### FR-02, mandatory: no frozen step evaluates the `.L` and `.P` predicates

Each `.X` runs `w2f_s7_check.py expect --command Cnn`, which evaluates only `commands[Cnn].expect`
(checker lines 341–350). The checker's other phases do not cover them either: phase `prepared`
evaluates P01 to D01, and phase `post` evaluates Q01 to Q03.

That leaves these predicates with no frozen step that evaluates them:
- **The 19 `.L` commands:** exit 0, `/command`, the boot before and after, `/process_events` empty,
  and the tool's digest.
- **The three `.P` commands:** `/targets` length, and every state `absent`.

`capture_probe.py` exits 0 whatever the states it records.

**Why it matters.** C16.P and C17.P are FC-P3's independent check that no supervised Node group
remains. They run before the next Node-starting command, C17 and C19. As frozen, a target
"present, identity established", "present, identity not established" or "unknown" stops S7 only if
the Director reads the probe record and applies the prose classification. So a Node start could
follow an unmet expectation, and the outcome is left to the Director's decision.

**Required change**, by either of two routes:
- Append each `.L`'s and `.P`'s predicates to the main command's `expect`, which the `.X` already
  evaluates after the `.L` and the `.P`.
- Or freeze a checker step for each `.L` and `.P`.

### Nonmandatory findings

- **FR-03.** C17's stop-rule predicates bound only the Node events, as a `count_where` of 3. C06's
  and C07's bound none of the unit process's process events. Git's 60, 15 and 25 and C17's total of
  63 are in `audit_expect` only. So a start of any other program in those commands would not stop
  S7 before C19's two Node starts; it would appear only in S8.
  - Add to `expect`: `{"pointer": "/process_events", "each": {"pointer": "/argv/0", "one_of": [<node>, <git>]}}`,
    and the same `each` on `/event` equal to `subprocess.Popen`.
  - The checker supports both forms (tested).
- **FR-04.** C17's three CPU starts run as one unit. P07 section 6 requires the complete module, so
  a failure of Q01 does not stop Q03 and the changed reference. MH-PLAN section 8 lets remaining
  Node starts continue only if the freeze declares the rows independent. The freeze should say
  that C17's trio is one indivisible row, or declare it independent within C17.
- **FR-05.** The preparation has 25 directories and 18 files, 43 entries in all. The author's notes
  say 26 directories and 44 entries, and the Director's brief repeats it. The freeze's
  `preparation.entries` and `prepare-s7-001.sh` agree with each other one for one, in order (see
  answer 6). Records should use 25 and 43.
- **FR-06. Gaps in the classifications.** None of these changes an action; each would otherwise be
  decided after the fact.
  - **C19:** MC30-probe may refuse after the environment check with a message other than "Actual
    input identity differs". Class it PLAN unless a bound input changed; MC36 is then NOT_RUN.
  - **C17, positive case:** a refusal at another bootstrap check, for example the manifest's labels
    or bindings, is IMPLEMENTATION, since the provider wrote that manifest.
  - **C17, setup:** an `EVIDENCE` refusal at `setUpClass`, for example an existing override path,
    is PLAN.
  - **C02:** if P02 to P04 passed in the same boot just before, `state_equals_host` false points to
    the provider's `host_state` disagreeing with the observer, which is IMPLEMENTATION, not HOST.
  - **C03 to C05:** a refusal at `SOURCE` or `PYTHON` after P02 to P04 passed the same plans
    statically points to the harness, so PLAN, or to the observer, so IMPLEMENTATION. It does not
    point to an input change.
  - **C13:** a difference caused by exporting C rather than by the source would be PLAN. An export
    lacks the `.git` pointer, `.venv` and every ignored file. `w3f_09` found no module-level use of
    `.git` or `.venv`, so the risk is small.
- **FR-07.** The checker checks its own binding, which is circular. The only check of its bytes
  that does not depend on itself is the Director's SHA256SUMS verification, and that is not a
  frozen step. Repeat it, or at least `eb96aa1a…` of `s7/w2f_s7_check.py`, immediately before P01,
  and record it.
- **FR-08. The checker's semantics, for the record.** None of these is exploited by this freeze.
  - An empty `expect` list is vacuously MET, and so is an `each` over an empty list. Every `each` in
    this freeze is paired with a `length` or count predicate on the same member.
  - A rule with two predicate keys evaluates only the first: `text_includes` over `text_excludes`,
    `length` over `each`. The freeze has no such rule; its only two-key form is
    `count_where`+`equals`.
  - A malformed JSON record raises an exception: exit 1 with a traceback, not `NOT_MET`. That still
    stops S7.
  - `os.walk` skips unreadable directories silently in the bytecode check.
- **FR-09.** `STATIC_TRAY_READBACK_CPU_OUTPUT` (Q4) changes where the cohort is written. It also
  means the provider's `_OwnedTemporaryCohort` and `_preserve_temporary` are not exercised. That is
  the driver's default path: a temporary cohort, its preserved copy and its cleanup. The seven
  methods and every provider check are unchanged. The freeze's limits should say that MH does not
  cover that default path.
- **FR-10.** W2's self-check reports MC30-probe's absent branch as "Current-host binding: Actual
  input identity differs". The probe throws `Error('Actual input identity differs')` without that
  prefix (line 722). The freeze's own texts are correct, and no predicate depends on this.
- **FR-11.** C09 and C11 expect `/usr/bin/tar` (bsdtar) to write nothing on stderr while it
  extracts Git's pax archive. That was predicted, never observed on this host: the baseline figure
  comes from MI's retained export, the current one from an APFS clone. A warning would stop S7 at
  C09 or C11 as PLAN, before any Node start.
- **FR-12.** N-04's elimination assumes the same environment in every start. That includes the same
  user and an unchanged `<home>/.CFUserTextEncoding`. D02 checks the file before C17 and Q04 checks
  it after S7, but nothing checks it between C17 and C19. The risk is negligible; the assumption
  should list the file.

## 3. Answers

### 1. Completeness

The freeze decides each item the author's brief lists, in its JSON and not only in prose:
- TOOLING-AUTHOR-NOTES section 4, items 1 to 11: `decisions`;
- TR-14, TR2-01 to TR2-06, TR3-03, PR-01, PR-03 and HR-01 to HR-07: `carried_findings`;
- N-04, MC36 and the MC30-probe decision: `n04`, `controls` and R2;
- MH-PLAN section 6, every row: `mh_plan_section_6`;
- section 7's rows and totals: `totals`;
- section 8: `stop_rules` and a per-command `classification`;
- the preconditions: P01 to P05, D01 and D02, plus `preconditions.conditions`.

These items are missing, or decided only in prose:
- **FR-01:** an executable outer-bound procedure and the launch mode.
- **FR-02:** the evaluation of the `.L` and `.P` outcomes.
- **FR-04:** within-C17 independence.
- **FR-06:** the classification gaps.
- **The Director's re-verification of the checker before P01:** FR-07.

### 2. Bindings

I recomputed all 120 bindings. Each one matches its SHA-256, size and mode, has one link, is
canonical, and has every component spelled as in its parent's listing (`records/02-bindings.json`).
There are no duplicate IDs or paths.

**The nine tool bindings** equal `authoring/TOOLING-SHA256SUMS.txt` at C:
FAILURE-CAPTURE, the README, and the seven scripts from `audit_numeric` to `scan_mc11`.

**The bindings the brief names:**
- **HOST:** `34e94f29…`, 18,420 bytes, `0o600`.
- **completion.json:** `fd1a0350…`, 981 bytes, state `OBSERVED_UNAPPROVED`.
- **result.json:** `1b4cae0f…`, 2,621 bytes, state `PENDING_COMPLETION`. That is HR-04.
- **The adoption record:** `872312ed…`, 5,396 bytes, `0o644`. That is PR-01. Every configuration's
  `amendment_adoption` binds it, and the probe checks it in `verifySource`.
- **The wrapper:** `3c24f923…`, 3,601 bytes, `0o644`. That is HR-01.
- **The CF file:** `bd605d2e…`, 7 bytes, `0o400`, one link, content `0x0:0x0`. With UID 501 it gives
  HOST's `0x1F5:0x0:0x0`. It is unbound by HOST and checked by P01, D02 and Q04. That is HR-02.
- **Node:** `6f320694…`, 122,545,856 bytes, `0o755`.
- **The probe:** `bca11b2a…`, 58,452 bytes.
- **The loader:** `927190e6…`, 564 bytes.
- **The reader tree:** 24 files, each equal to `dependencies-inventory-001.json`.
- **The three inventories:**
  - source `95abd300…`, 96,238 bytes;
  - Python `c277bdd3…`, 776,209 bytes;
  - dependencies `3545d5f9…`, 4,543 bytes.

**The 12 environment files** each equal the freeze's `environments` entry exactly, with names and
values.

### 3. Every command, all 71

**Structure.** For all 71:
- `shell` is exactly the single-quoted `wrapper_argv`;
- `wrapper_argv` is `/bin/sh <wrapper> NAME CWD ENVFILE --` followed by `argv`;
- every placeholder sits at its `argv_index`, and at `wrapper_argv_index` = `argv_index` + 6;
- no other `<…>` element exists;
- every one of the 64 Python starts carries `-B`;
- every `env -i` assignment set equals its environment file;
- every record and output is in `outputs_absent_before` and in both absent lists, except P01's and
  D02's own records, which must exist while those commands run;
- no output is a prepared path.

**The tools' interfaces.** The argv matches each tool's argument parser in the source and the
README:
- `collect_outcomes` cohort and controls;
- `run_direct_probe`;
- `control_harness` `mc10`, `mc29` and `host-state`;
- `discover_inventory` `discover` and `compare`;
- `scan_mc11`, `audit_numeric`, and `capture_probe` `listing` and `probe`;
- the observer's `static`, `python-inventory` and `source-inventory`.

**Environments and cwd.** The environments are what each tool requires:
- the collector requires an exact environment and the driver's rules: no `GIT_*` names, none of
  `UNIT_REMOVED`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1` and both selection variables;
- the harness requires its selection pair to equal its arguments;
- the observer and `mc10` require exactly the declared environment;
- the runner requires `PATH` only.

The cwds are correct. The collector, discovery and the harness's root imports also `chdir` to the
root themselves.

**Starts and limits.** They are as stated. The CPU clock of 30,000, 28,000 and 2,000 ms is P07's.

**The predicates.** No failed, partial, skipped or interrupted run of a main command meets its
predicates:
- C17 requires `ALL_PASSED`. That needs a complete run: not interrupted, every test passed, no
  class-level, unplanned or loader event, and every body equal. C17 also requires seven tests, each
  `pass`, and seven required methods, each `pass`.
- C16 and C19 require `ALL_ROWS_MET`, the exact Node count, each row `COMPLETED` with
  `OBSERVED_ONE`, `interrupted` false, and `started-2.json` absent.
- A wrapper that dies leaves no `.exit.txt`.

The exceptions are FR-02 and FR-03. The expectations are the contract's and P07's, not weakened.

**Classes.** They are right, except the gaps in FR-06. No PLAN class hides an implementation fault,
because my replay shows the fixtures coherent up to each frozen refusal.

### 4. The Node-starting commands: C16, C17, C19

**The rows.** `rows-r1.json` and `rows-r2.json` pass `validate_rows` (schema `/2`), as I read it:
- **IDs and stages:** the IDs are admitted, and each row has its own stage.
- **argv:** the syntax shape is `[node, --no-addons, --max-old-space-size=256, --check, probe]`. The
  probe shape has the loader and `STAGE/job.json`.
- **Environment:** exactly the declared environment.
- **Limits:** `28000 <= 30000 - 2000`.
- **Inputs and stage entries:** every stage file is an input, and the stage entries are exact.
- **`supervisor_error`:** it is the one status 1 implies.
- **Predicate targets:** each is absent at intent.

**Replay from the source** (`w3f_04`, without Node):

| Row | Where it refuses | With the variable | Without it |
| --- | --- | --- | --- |
| P06-H01 | `approvedEnvelope`, uncaught, so on stderr with no `probe.json` | "CH-SELECTION: manifest digest is not external approval": manifest selection `16032c32…` against argv's D0 `83c8b158…` | the same |
| P06-H02 | `approvedEnvelope`, after the selection checks pass on its own comparator `48d33d34…` | "Current-host binding: wrong configuration contract/schema" (Q8) | the same |
| MC30-probe | inside the `try`, so in `probe.json` | "Current-host binding: actual Node environment differs" at `verifyHost` | "Actual input identity differs" at line 722, after every other check passes with the copies |
| MC36 | inside the `try` | "…actual Node environment differs" | none: it reaches the readers, which is why it must follow MC30-probe |

Each refusal comes before the readers are imported, at lines 728–740. The loader is a reader-set
file that Node loads first; it only defines a `resolve` hook and imports `node:url` and
`node:path`. The JSON differences confirm minimal mutations:
- **The configurations** differ from D0 only in `evidence_root`; H02 also has its `schema`, and
  MC30 and MC36 also have their `host`.
- **The HOST copies** differ only in `/environment/cf_user_text_encoding`.
- **The manifests and jobs** differ only in the fields specific to each row.

**The syntax check.** The expectation of empty stdout and stderr (Q2) is right for `node --check`
on success. Node's two flags (Q3) are admitted, and they emit no warning. The ExperimentalWarning
for `--experimental-loader` appears only in the four probe rows. Their `stderr_exact` is null, and
the warning contains neither "CH-SELECTION" nor "Current-host binding".

**The cohort, C17:**
- **The unit process:** `<worktree>/.venv/bin/python -B`, in cwd `<worktree>`, with the exact
  environment of item 5. `sys.executable` equals HOST's `python.launcher`, and `venv` is the root's
  `.venv`.
- **The module and the methods:** module `6295e044…`, bound. The methods document's nine
  `original_bodies` equal the probe's constant. The collector compares the source bodies with them.
- **Raw IDs:** seven tests, and the seven required methods joined by the alias. The module's digest
  fixes the raw IDs.
- **Node starts:** exactly three. Each case ledger has one, `cohort.json` has three, and the
  collector's events are counted where `argv[0]` is Node.
- **The quartet** patches `format_check.run_process` and starts nothing.
- **Git reads:** 60, which is 12 selection checks of 5 reads each in `_verify_source`, by
  `git_read` with a timeout of at most 5 s. This agrees with my source count.
- **Q4** changes only the location and the temporary-copy path (FR-09).
- **Writes:** no test writes into the worktree. The seams write in TMPDIR, the CPU cases under
  `run/`, Node only `probe.json`, and Git reads run with `GIT_OPTIONAL_LOCKS=0`.

**N-04.** The elimination is valid:
- The positive starts pass `environmentAdmitted` with HOST's value, so Node's environment is the
  declared one, or the declared one plus the variable with HOST's value.
- MC30-probe's refusal under null shows that it is not the declared one alone.
- So, under the stated same-environment assumption, the variable is present with HOST's value. The
  assumption holds: the same executable, supervisor and declared environment, and the same user and
  CF file (FR-12).

MC36's order is right: it is in R2, after C17 and after MC30-probe, with `rows_independent` false.

**The stop rules.** Between commands, Node starts follow only after every `.X` is MET, except as
FR-02 and FR-03 say. Within R1 and R2, an unmet row stops the later rows. Within C17, see FR-04.

### 5. The other controls

- **C01 (MC11).** With my reviewed list, `scan_mc11.py` exits 0. `frozen_rule.passed` and
  `process_creation_none` are true, with 587 dynamic hits and 0 unreviewed. `none_found` and
  `reviewed_list_matches` are true. There are no unresolved specifiers, process creation is 0 and
  the status is `REVIEWED`. The totals are 628 dynamic hits, 23 call names and 53 specifiers. So
  every C01 predicate would hold.
- **C02 and C17 (F-04).** Both are real. C02 runs the provider's `host_state` and `_check_state`,
  with an audit hook that refuses processes.
- **C03 to C05 (MC10).** The command boundary is a pure stub (`CommandBoundary.run_process`): it
  writes three files and returns a synthetic PID. The audit hook blocks any process creation, so the
  mocked boundary cannot start anything. The plans differ from plan 001 only in `evidence` and in
  the two commands' cwds. The observer's `static` gave `STATIC_READY` with each plan.
- **C06 and C07 (MC29), with Q1.** The facade binds the version at setup (D-20, lines 1161–1217).
  `finish_cpu_cohort` then takes `vars(cls)[readback_dispatch_version]`, which is 0.2.0.
  - The configuration case is refused by the 0.2.0 provider's `_selection`, with "Configuration
    differs from the independently supplied expected digest", in both the attempt and the
    accounting. `cohort.json` is `cohort/0.2.0`. REFREEZE-002's added MC29 case says the same.
  - The job-input case's codes are CH-JOB, with "Actual CPU input digest differs", and CH-EVIDENCE,
    with "Completed cohort is missing or has extra checker attempts".
  - `str(CurrentHostBindingError)` is its reason, so the predicates on `/…/reason` match.
- **C08 to C14 (MC28), with Q5 and Q7.** I read these files:
  - The repository's local `config` defines no `filter.*`, `core.hooksPath` or worktree
    configuration. Its `[lfs]` section holds only `repositoryformatversion`.
  - There is no `config.worktree` and no `info/attributes`.
  - The `.gitattributes` at C, and in MI's export of `1c2f25ba`, names `filter=lfs` only under
    `docs/engineering/lfs-archives/`, which does not exist at C.

  With `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM`, `GIT_ATTR_NOSYSTEM`, `HOME` unset and no
  configured driver, `git archive` passes the bytes through, so no filter driver or other process
  runs. `GIT_NO_LAZY_FETCH` blocks promisor fetches. The tar format needs no compressor, and archive
  runs no hooks. The same holds for P05's and Q03's `status`, with no index write under
  `GIT_OPTIONAL_LOCKS=0`. The ignore rules hide `__pycache__/`, `.venv/` and `.DS_Store` from
  `status`; P01's tree check covers them. Discovery `chdir`s to its root, so cwd `<E>` is fine. On
  FR-11, see above.
- **C15 (MC37).** The test's child is `sys.executable -I -S -B -c …` in a new session. The
  `CONTROL-EVIDENCE` line is written as frozen. It is one other start, exact, with
  `process_events` of length 1.
- **C18.** `audit_numeric.py` uses `NEGATIVE_DIFFERENCE_TOLERANCE` = 1e-9 (T-10). Its record keys
  are `passed` and `all_three_cases`.

### 6. The two new tools

**The checker** (`eb96aa1a…`).
- **What it does.** It refuses a start without `-I -S -B` and refuses a wrong freeze digest, which
  it hashes itself (exit 2). It refuses an unknown command (exit 2). It installs an audit hook that
  refuses process creation. It imports nothing of the project and writes no file. Its `umask` probe
  sets the mask and restores it.
- **Phases.** `pre`, `prepared`, `expect` and `post` cover what the freeze says.
- **Predicate kinds.** Every kind behaves as specified in both directions, in 48 cases. It is
  type-strict: `true` is not `1`, and a missing key differs from `null`.
- **The phases' failure checks.** The 31 phase cases detect a changed digest or mode, two links,
  the wrong letter case, a symlink component, `.DS_Store`, bytecode, a present path, an ancestor, a
  deferred input, the umask, the boot, directory entries, earlier predicates and a changed input. A
  consumed input is excused.
- **One run against the real freeze** in phase `pre` gave `MET`, exit 0:
  - all 120 bindings;
  - the trees and the 370 absent paths;
  - the ancestors and the CF file;
  - boot `C90010BA-…` and umask `0o022`;
  - the deferred list `aade03ac…`, 344,283 bytes, `0o644`.

  For the checker's semantics, see FR-07 and FR-08.

**The preparation script** (`6621518b…`).
- `/bin/sh -n` passes.
- Its 25 `mkdir -m 0700` and 18 `cp -n` lines match `preparation.entries` one for one, in order.
  Each is preceded by its own absence check. Parents come before children.
- The script has `set -eu` and `umask 022`. It has no `rm`, `mv`, `ln`, `chmod`, `touch` or `tee`.
- **The rewritten copy in `<OUT>`:**
  - the first run printed "prepare-s7-001: done" with empty stderr. It created exactly 43 entries,
    with directories `0o700` and files `0o644` with one link, and their digests equal to the
    entries'.
  - the second run refused at the first existing path, with exit 1, and created nothing.

**W2's self-check**, run once, gave the same 457 checks and 0 failures. Its output is byte-identical
to `selfcheck-002.txt`.

### 7. The deferred values (D3, Q6)

Each value has a single source, and a check that catches a wrong value:

| Value | Its source | The check |
| --- | --- | --- |
| The freeze's digest | this record | The checker refuses any other value, with exit 2. |
| The reviewed list's digest | this record and the disposition | P01 reports the file's digest; `scan_mc11` refuses a mismatch with `DIGEST`; and C01.X checks `/argv/25` equals the file's digest. |
| C14's two discovery digests | C12.L's and C13.L's readbacks, at `/paths/<path>/sha256` | `compare` refuses a mismatch with `DIGEST`, and C14.X checks `equals_from`. |

A wrong copy stops S7 before any Node start. The design is acceptable. The Director should extract
the values mechanically, with the frozen JSON pointer, never by hand.

### 8. The outer bound, and the launch method

The rule is not executable as frozen, for the reasons in FR-01. The minimal procedure is in FR-01
too. The change is mandatory.

**The launch method** is sound under five conditions:
1. Read the `shell` member raw from the bound freeze, for example with `jq -r` on the frozen file.
2. Replace only the named placeholders, each by its 64-hex value. The placeholders sit inside
   single quotes, and the values hold no quote.
3. Pass the string alone, with nothing prepended or appended, so that `zsh -c` runs one simple
   command and the wrapper leads the group.
4. Use background mode, with no tool timeout.
5. Make one call per command, never retried.

Each `.X` then checks the recorded `argv` against the frozen one, and each placeholder against its
source. C16, C17 and C19 carry no placeholder. Foreground mode is unsound for any command whose
bound the Director must enforce, and for C17's bound of 600 s, which equals the maximum timeout.

### 9. FAILURE-CAPTURE

- **FC-K2, FC-K3.** The wrapper writes `stdout`, `stderr`, `exit` and `command.json` by exclusive
  creation, beside the attempt.
- **FC-K5.** All 19 C commands have a `.L` that lists their outputs, stages and TMPDIRs.
- **FC-P3.** C16, C17 and C19 have a `.P`, whose pairs are exactly their started records.
- **The unevaluated predicates:** FR-02.
- **FC-K1.**
  - No S7 command can change an existing evidence path, MP's inputs, `<F>` or the worktree.
  - Every output is new and every tool writes exclusively. C06's appended space goes to its own
    prepared copy, and C07's zero byte to its harness-written stage copy.
  - Git runs with optional locks off, and Python with `-B`.
- **The absent paths.** All 370 lie under `<E>`, each one named by some command's records or
  outputs, or by the preparation. None exists now. The 303 that `after_preparation` lists are the
  370 minus the 43 prepared entries and the 24 records of P02 to D02.

### 10. The totals

MH has 9 Node starts and 2 other starts: S5's 1 and 1, plus C16's 3, C17's 3, C19's 2 and C15's
1. MH-PLAN section 7 expects 8 and 2. The ninth Node start is MC30-probe. Its reason is valid:
- **Why the positive starts cannot settle it.** `environmentAdmitted` accepts both the declared
  environment alone and the declared environment plus the variable with HOST's value.
- **Why MC36 needs it.** Without MC30-probe, MC36 could not be interpreted, and with the variable
  absent it would read the readers.

Tooling review 001's T-04 row and its disposition accepted this.

The recorded but unbounded counts are right:
- **The provider's Git reads:** 15, 25 and 60, consistent with `_job` and `_verify_source`.
- **The Director's Git reads:** 4.
- **tar:** 2.
- **Python launchers:** 64, which is the 71 commands minus P05, D01, C08, C09, C10, C11 and Q03.

### 11. Q1 to Q11, D1 to D3

- **Q1.** Confirmed (item 5). TR2-06's disposition text, which says "the facade's unchanged 0.1.0
  code", is out of date at C. Under it, C06's `cohort/0.2.0` predicate would fail.
- **Q2.** Accepted: exactness is right.
- **Q3.** Accepted.
- **Q4.** Accepted, with FR-09's limit.
- **Q5.** Accepted. The export equals C's tracked files. No module-level code uses `.git` or `.venv`
  (`w3f_09`).
- **Q6.** Accepted (item 7).
- **Q7.** Accepted: PLAN is the right class for a baseline difference.
- **Q8.** Accepted: it reaches the schema guard (replay).
- **Q9.** Accepted. The probe reads many more files than its rows' `inputs` list. Each is bound by
  the inventories or by HOST, and a mismatch refuses; it can never pass falsely.
- **Q10.** Accepted.
- **Q11 and D1.** Accepted. The fixtures come from the project's builders. Only MC29 and the probe
  rows use them as inputs, and only C17's `audit_expect` compares them with the cohort's bytes.
- **D2.** Reviewed in item 6.
- **D3.** Reviewed in item 7.

### 12. Anything else

- **For the Director.** My reviewed list must stay unchanged in `<OUT>` until C01. A freeze 002 can
  rebind the same list only if the probe, the dependencies inventory and the reader tree are
  unchanged.
- **For the auditor.**
  - The predicates of C17 and of C16 and C19 never read a refused probe result's labels.
  - The `audit_expect` sets, of C17 and of C06 and C07, carry the counts that the stop rules do not:
    FR-03.
- **The repository's local Git configuration** holds the owner's personal data. I did not copy any
  of it.

## 4. The MC11 reviewed list

The list is `<OUT>/MC11-REVIEWED-LIST-001.json`: SHA-256
`aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800`, 344,283 bytes, `0o644`.
- **Format.** Schema `ontokin.c271.p35-mc11-reviewed/2`, status `REVIEWED`, and its reviewer named.
  Its 25 entries are keyed exactly as the candidate list keys them: `<probe>` and the 24 reader
  paths. Each entry uses only `process_call_names`, `dynamic`, `specifiers`, `frozen_rule` and
  `notes`.
- **Source of the lists.** They come from my own scan, which equals the candidate list exactly for
  every file: the `[pattern, line, column]` lists, the specifier multisets, and the frozen rule's
  `[kind, stripped line]` multisets and one-line specifiers.
- **My decisions**, in each entry's `notes`, grouped by pattern, enclosing token and lexical
  context, with every line and column:
  - **The 23 process call names** are all `RegExp.prototype.exec`, on regex literals or on variables
    that hold a RegExp. I checked `RePathPart`, `propertiesRegexp`, `_trackRe`, the charset `re`,
    and the dart2js `A.iK` field `b`.
  - **The 628 dynamic hits** fall into these classes:
    - identifier substrings of `Function` and `eval`;
    - the word `Function` in comments and strings;
    - dart2js's `Function.prototype.$N` call adapters;
    - the probe's `createRequire` and its three bound loads;
    - `require` as an English word or a GLSL or WGSL string;
    - three's `package.json` exports key, never loaded;
    - the validator preamble's `self.require=require` and `require("url")`.
  - **The 53 specifiers** are `node:` builtins, relative imports that resolve to reader files, and
    bare `three` specifiers that the loader maps into the tree. The rest are comment, string or
    README text. The wider-scan-only specifiers are recorded as the rule's implementation note asks.
- **TR2-03's route classes, my own count:**
  - **`.constructor(`:** 61 calls, all `new …constructor(…)`, three of them spanning lines.
  - **`Reflect`:** 6 `get` and 2 `set`, all in Proxy handlers.
  - **Computed members of global objects:** only the validator's five `window[…]` lookups, which
    return null without `window`, as in Node.
  - **None of these occurs:** `process[`, `getBuiltinModule`, `new Function`, `Function(`, a timer
    called with a string, WebAssembly, or a `worker` outside comments and strings.
- **Conclusion.** No route to process creation was found, within the stated limit of a name scan.
- **Check.** `scan_mc11.py` at C, with this list, exits 0 (`records/mc11-scan-reviewed-001.json`).

## 5. Files in `<OUT>`

- `FREEZE-REVIEW-001.md` and `FREEZE-REVIEW-001.json`: this review;
- `MC11-REVIEWED-LIST-001.json`: the bound input;
- `scripts/w3f_01_inventory.py` to `w3f_12_final_state.py`;
- `records/`, among them:
  - `02-bindings.json`, `03-commands.txt` and `03-commands-checks.json`;
  - `04-probe-replay.json` and `05-diffs.json`;
  - `06-mc11-hits.json`, `06-mc11-groups.txt`, `07-mc11-routes.json` and `07-mc11-routes.txt`;
  - `10-checker-tests.json`, `11-prep-make.json` and `11-prep-verify.json`;
  - `12-final-state.json`, which holds SHA-256, size and mode of all 145 reviewed files;
  - `checker-pre-real-001.json`, `mc11-scan-noreview-001.json` and `mc11-scan-reviewed-001.json`;
  - `observer-static-mc10-{a,b,c}.*` and `w2-selfcheck-crosscheck-001.txt`;
  - `python-inventory-after-W3F.json`;
- `prep-test/` and `checker-test/`: the synthetic worlds.
