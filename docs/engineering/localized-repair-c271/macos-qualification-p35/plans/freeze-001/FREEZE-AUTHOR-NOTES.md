# Operational freeze 001 for gate MH: author's notes

C271-P35, gate MH, stage S6. Author: W2, a Claude Code subagent in a fresh context with the
session's model. I wrote none of the tooling, the observation plan, the observer, the provider, the
probe, the contract, its amendment or MP's preparation. Written on 2026-11-27 (UTC) against commit C
(`0eb9a551`, tree `ea10cd94`), clean, in the boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`.

Paths use the labels `<worktree>`, `<local>`, `<prefix>` (the interpreter's installation prefix),
`<home>` and `<package-manager>`. The bound documents beside these notes keep their real paths.
`<E>` below is `<local>/c271-p35/evidence` and `<OUT>` is `<local>/c271-p35/workers/W2-freeze-001`.

## 1. Result

`FREEZE-001.json` is the closed document. It holds, in this order: the contract and the fixed
state; HOST with `completion.json` and `result.json` (HR-04); the one unbound host fact (HR-02); the
boot, the umask and the evidence ancestors; the wrapper and its semantics (HR-01); 12 frozen
environments; three configurations (the approved cohort's and the two MC29 sources), the methods and
discovery documents, four direct-probe fixture sets (each a configuration, a manifest and a job) and
two HOST copies; 120 bindings; the deferred inputs and arguments; the preconditions, the preparation
and its 44 entries (26 directories, 18 files); 370 paths that must be absent; the order of 71 commands with their wrapper argv,
predicates and classifications; the post checks; the controls table; the totals; the stop rules;
the outcome classes; how FAILURE-CAPTURE applies; the carried findings; the eleven decisions of
TOOLING-AUTHOR-NOTES section 4; N-04; MH-PLAN section 6; the limits; and the open questions.

| | |
| --- | --- |
| Node starts in S7 | 8: R1 3 (syntax check, P06-H01, P06-H02), the cohort 3, R2 2 (MC30-probe, MC36) |
| Other bounded starts in S7 | 1: MC37's Python child |
| MH in all, with M0 and M1 | 9 Node, 2 other (MH-PLAN section 7 expects 8 and 2; the ninth Node start is MC30-probe) |
| Recorded, not bounded | 100 bound Git reads of the provider (cohort 60, MC29 15 and 25), 4 Director's Git reads, 2 tar runs, 64 Python launchers |
| Controls that run | MC10, MC11, MC24 to MC30 (MC29's two possible cases), MC36, MC37, F-04, the probe syntax check, the numerical audit |
| Controls NOT_RUN at MH | MC01 to MC09 as controls (MC09's real reader runs for F-04), MC12 to MC23, MC31 to MC35, MC38, MC39; MC29's source, runtime, dependency and OS-build cases |

## 2. Method

1. **Reads.** MH-PLAN; TOOLING-AUTHOR-NOTES (section 4 as my checklist; section 8 over section 1,
   TR3-02); the three tooling reviews and their dispositions; N34-M-DISPOSITION; the tooling README
   and FAILURE-CAPTURE; W5-PROVIDER sections 2 to 4, W4-DRIVER, W3-OBSERVER, W1-SUPERVISOR; the
   frozen controls, both refreezes, INVENTORY-ADDITIONS and DIRECTOR-DECISIONS; CONTRACT sections
   5, 7, 9 to 12; P07 sections 2 to 8; the S4 and S5 records and dispositions; and the source:
   the 0.2.0 provider, the facade, the probe, the observer, the two supervisors, the cohort module,
   the controls module, `tools/check_local.py` and all seven tools.
2. **Bindings.** `author/scripts/w2f_bind.py` hashed every input and checked every path component
   against its parent's listing, so each path is spelled as on disk (TR3-03):
   `author/records/bind-001.json`. Every digest equals the one the earlier records name.
3. **Figures, by the allowed tools.** One MC11 scan without a reviewed list
   (`author/records/mc11-scan-candidate-001.json`). Two discoveries, each on an APFS clone inside
   `<OUT>/author`, removed afterwards: the worktree at C (5,994 IDs, 388 modules, sorted SHA-256
   `32b2b861…`) and MI's retained export of `1c2f25ba` (5,587 IDs, 382 modules, `bcc36ee7…`, equal to
   MI's own list). The baseline plus the 407 additions equals the current set exactly. Neither run
   wrote into its clone or its temporary directory.
4. **Fixtures.** `author/scripts/w2f_fixtures.py` built the original GLB and reference bytes with the
   project's own builders (`synthetic()` of `tests/test_static_tray_reader_v01.py` and the reader's
   `audit()`), exactly as `check_case` does, in a `-I -S -B` process that refused process creation.
   Nothing was written into the worktree.
5. **Generation.** `author/scripts/w2f_generate.py` wrote every bound document, deriving the
   manifests from `_manifest` and the MC10 plans from plan 001 (checked by reproducing plan 001's
   bytes). `author/scripts/w2f_compose.py` wrote `FREEZE-001.json`.
6. **Static replay.** `author/scripts/w2f_selfcheck.py` replays, from the source, the runner's
   `validate_rows`, the probe's `approvedEnvelope` and `verifyBootstrap` (with the real source,
   reader tree, HOST and Node bytes), the provider's static selection checks, the collector's
   environment rules and every `--*-sha256` argument: 457 checks, none failed
   (`author/records/selfcheck-002.txt`). It shows each probe row refusing exactly where frozen:
   - P06-H01 at `CH-SELECTION: manifest digest is not external approval`;
   - P06-H02 at `Current-host binding: wrong configuration contract/schema`;
   - MC30-probe at `actual Node environment differs` with the variable, and at `Actual input
     identity differs` without it;
   - MC36 at `actual Node environment differs` with the variable; without it MC36 would reach the
     readers, which is why it waits for MC30-probe.
7. **The checker.** `s7/w2f_s7_check.py` is new: the Director runs it for P01, D02, every `.X` step
   and Q04. One run against this freeze in phase `pre` met every check but the reviewed MC11 list,
   which does not exist yet (`author/records/check-pre-test-001.json`). A synthetic freeze exercised
   every predicate kind in both directions, all four phases, a wrong freeze digest and an unknown
   command: 19 of 19 cases as expected (`author/records/checker-test-001.txt`). `/bin/sh -n` parsed
   `s7/prepare-s7-001.sh`.

## 3. TOOLING-AUTHOR-NOTES section 4, item by item

1. **MC10 (F-01) runs,** with T-01's exclusion, which review 001 accepted (Q7). Three cases, C03 to
   C05, each with its own plan (`mc10/observation-plan-mc10-a|b|c.json`) and absent attempt under
   `<E>`. Each plan is plan 001 with only the attempt, its output topology and the two cwds changed;
   the evidence parent and its ancestors stay plan 001's, so the plans hold no value that S7
   creates. Node stdout `v24.22.0\n` and `v24.22.1` without its newline are refused at OUTPUT; the
   baseline `v24.22.1\n` is accepted with a mocked HOST. The Git line is HOST's real line. The four
   `--bind` digests are the observer's files; `control_harness.py` is bound. The harness lists the
   loaded modules once per static pass, so the freeze requires every excluded row to be its own
   `__main__`, not a count of one.
2. **MC29 (F-03): both possible cases** (C06 configuration, C07 job input), each on its own prepared
   copy of its own configuration (its own evidence root), and its own frozen environment with that
   copy's selection pair (T-11, TR-14). The GLB and reference are `fixtures/Q01/`. Expected attempt
   codes CH-SELECTION and CH-JOB; accounting codes CH-SELECTION and CH-EVIDENCE (TR2-06, with Q1
   below). The source, runtime, dependency and OS-build cases stay simulated as MI ran them.
3. **F-04: both** the host-state harness (C02) and the cohort's own reads (C17). T-08.
4. **MC30-probe is added** (T-04). Its HOST copy records `cf_user_text_encoding: null`; its job binds
   the SHA-256 of the empty string as the GLB digest. MC36 follows it in R2, with
   `rows_independent: false`, after the cohort. That makes nine Node starts for MH.
5. **The unit process:** `<worktree>/.venv/bin/python -B`, cwd `<worktree>`. Its exact environment
   is `PATH`, `LANG`, `LC_ALL`, `TZ`, `TMPDIR` (a prepared directory of this attempt, without a final
   slash), `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, the selection pair and
   `STATIC_TRAY_READBACK_CPU_OUTPUT`.
   - **No `GIT_*` name.** The collector allows only the driver's exact set; the provider's
     `git_read` builds its own Git environment for every read anyway.
   - **No `HOME`** (TR-06).
   - **The override** keeps the cohort in place at `<E>/s7-001-cohort/run`, without a temporary
     root, a preserved copy or a removal (Q4).
   - **The module digest** is `6295e044…`, and the methods document holds `original_bodies`.
   - **MC37** runs with the same base, without the selection or the override, under its own
     `TMPDIR`, with module `3b8c91b7…`.
6. **The direct-probe rows** use schema `/2`, in two documents.
   - **R1** holds the syntax check (with Node's two flags), P06-H01 and P06-H02. **R2** holds
     MC30-probe and MC36.
   - **Stages.** Each probe row has its own evidence root, holding
     `cohort/supplemental-cpu.json` and the stage `cohort/Q01-positive` with exactly `job.json`,
     `synthetic.glb` and `synthetic-audit.json`, all inputs.
   - **Inputs.** Each row also lists by descriptor every document the probe reads: the
     configuration, HOST or its copy, the methods and discovery documents, both inventories, the
     contract and the adoption record.
   - **Limits** are 30,000 and 28,000 ms.
   - **Predicates.** The supervisor error of status 1. For H01 and H02: stdout exactly empty, stderr
     including the frozen text and excluding the other row's text, and no `probe.json`. For
     MC30-probe and MC36: the exact stdout line, and sixteen `json_members` of `probe.json` (T-03).
   - **Refusal texts** are read from stderr, the exit status and the receipt, or from `probe.json`.
     No predicate reads a refused result's labels.
7. **MC11.** `mc11/MC11-CANDIDATE-LIST-001.json` has schema `/2` and status `CANDIDATE, NOT REVIEWED`,
   and covers 25 keys: the probe, the loader and the 23 other reader files.
   - **Its counts:** 23 call names, 628 dynamic hits, 53 specifiers, the frozen rule's 587 dynamic
     entries and 30 one-line specifiers.
   - **Per file, its notes** hold the specifiers that only the wider scan lists, which include the
     multi-line ones, and an advisory count of TR2-03's route classes.
   - **My count agrees with review 002** on 61 `.constructor(` calls, all `new` expressions, and on
     the validator's five `window[` lookups. It also finds two `Reflect.set` beside the six
     `Reflect.get` in `three.webgpu.js`, which is no construction route.
   - **TR-11's "url"** is listed.
   - **The reviewer** writes the REVIEWED list at
     `<local>/c271-p35/workers/W3-freeze-001/MC11-REVIEWED-LIST-001.json`, which C01 binds.
   - **The configuration's `dependencies/0.2.0`** is plan 001's (`3545d5f9…`).
8. **MC28.** C08 and C10 are two read-only Director's exports with the bound Git (`git archive`,
   whose output includes `docs/`, T-06). C09 and C11 extract them into prepared empty directories.
   C12 and C13 are the two discoveries, each under its own exact environment (TR-06), and C14 is
   the comparison.
   - **Why an export of C, not the worktree.** No discovery imports the worktree (Q5).
   - **Why `git archive` is safe.** The repository's local configuration defines no filter driver,
     `$GIT_DIR/info/attributes` does not exist, and `.gitattributes` names LFS filters only under
     `docs/engineering/lfs-archives/`, which `1c2f25ba` does not hold.
9. **The audit:** the cohort root `<E>/s7-001-cohort/run` (the cohort in place, not a preserved
   copy), and the 1e-9 bound (T-10). C18 records one run of `audit_numeric.py`, and S8 recomputes.
10. **Every tool's binding:** the nine files that S7 starts or reads, each equal to
    `authoring/TOOLING-SHA256SUMS.txt` at C, `capture_probe.py` among them. Section 8 of the tooling
    notes supersedes section 1 (TR3-02).
11. **TR-14:** see section 4.

## 4. The carried findings

- **TR-14.** The provider's bound Git reads are recorded, not bounded: 60 in the cohort, 15 and 25
  in the MC29 cases, which is 12 selection checks of 5 reads, and 3 or 5 checks. MC29's scope is
  stated, and each case has its own copy at its own path. Sources: T-07, review 001's verification,
  and the provider's `_verify_source`.
- **TR2-01.** The stop rules make any interrupted runner command UNKNOWN, whatever `run.json`
  says, and keep each row's `outcome.json`.
- **TR2-02.** The evidence against `rejected-001` is cited with its limit: two sub-checks fail
  there for a renamed rule or a missing field, not for the defect (`tools` in the freeze).
- **TR2-03.** Both route classes are in the candidate's notes, with review 002's cross-check and my
  own count, under the scan's limit.
- **TR2-04.** The readback can leave out an unreadable directory's entries, and the probe cannot
  tell an exited, unreaped process from a live one without established identity. Either way the
  outcome stays UNKNOWN and nothing is sent.
- **TR2-05.** `-B` is on every frozen Python command line; the self-check verified each of the 64.
  The tools' refusal relies on the frozen bytecode set, and P02 to P04, the provider and Q01 detect
  any write.
- **TR2-06.** C06 expects accounting CH-SELECTION and C07 CH-EVIDENCE. The attribution differs from
  the disposition's wording (Q1).
- **TR3-03.** Every `--root` and bound path is in its on-disk spelling, checked component by
  component here and again by the checker for every binding.
- **PR-01.** Every configuration's `amendment_adoption` binds `872312ed…`, 5,396 bytes, `0o644`
  (blob `0431fab5` at C, per plan review 001). The provider and the probe each check it.
- **PR-03 and HR-03.** The owner's launchd job (PID 1304) runs the framework interpreter with
  `PYTHONDONTWRITEBYTECODE=1`. It stays as it is unless the owner pauses it. The inventory is
  rechecked immediately before S7 (P02 to P04: the observer's static compares the installation
  with `c277bdd3…`), by every provider check during S7, and by Q01 after it.
- **HR-01.** The wrapper `run_once_v2.sh` is bound (`3c24f923…`, 3,601 bytes, `0o644`), and its
  epoch fields are authoritative. S5's static record is `observe-001.static.command-record.json`;
  the empty first record stays as it is.
- **HR-02.** `<home>/.CFUserTextEncoding` (`bd605d2e…`, 7 bytes, `0o400`) is an unbound host fact.
  P01, D02 and Q04 check it. The owner keeps the language and region settings unchanged until MH
  ends.
- **HR-04.** HOST (`34e94f29…`) is bound with `completion.json` (`fd1a0350…`, state
  `OBSERVED_UNAPPROVED`) and `result.json` (`1b4cae0f…`, which says `PENDING_COMPLETION` by design).
- **HR-05 and HR-06.** The freeze cites contract section 10's full list and does not read HOST's
  claims as complete. It cites HOST review 001 for commit C's tree, the index, the shared cache
  (`7a024959…`, UUID `F2E86C53-…`) and dyld (`373fce2b…`).
- **HR-07.** M1's 1,109.748 ms of 3,000 ms is the timing evidence for `bin/node`. The rows keep
  P07's 30,000, 28,000 and 2,000 ms.
- **N-04.**
  - **The positive start.** C17's Q01-positive and Q03-positive starts end with `probe.json`
    passed true. So the probe's `environmentAdmitted` accepted Node's `process.env` against HOST's
    value: Node held either the declared environment alone, or it plus the variable with
    `0x1F5:0x0:0x0`.
  - **Presence.** MC30-probe, under a HOST copy that records null, refuses with "actual Node
    environment differs". So Node's environment was not the declared one alone.
  - **The value.** By elimination, Node held HOST's value. This assumes the same environment in
    every start: the same bound executable, supervisor and declared environment.
  - **The order.** MC36 runs only after both.
  - **Absence.** If MC30-probe instead refuses with "Actual input identity differs", the variable is
    absent. MC36 then stays NOT_RUN pending an amendment of D-16, which is the CONTRACT class, not a
    plan error.

## 5. MH-PLAN sections 6 to 8

- **Section 6, every row,** is in `mh_plan_section_6`. Three rows are worth naming here.
  - **A refused probe result's labels.** They are not read: P06-H01 and P06-H02 are read from
    stderr, the exit status and the receipt; MC30-probe and MC36 from `probe.json`, the exit status
    and the receipt. The audit reports a refused result's labels as found and unverified (W5 Q5).
  - **The adoption record:** PR-01.
  - **`-B`:** TR2-05.
- **Section 7.** The rows and totals are in `totals`, counted as P07 section 4 counts. The ninth
  Node start is MC30-probe, for T-04's reason. "Recorded, not bounded" is listed exactly; the
  launchers come to 64 Python starts and one `/usr/bin/env` and one `/bin/sh` per command.
- **Section 8.**
  - **The stop rules.** S7 stops at the first unmet `.X`, and every Node-starting command needs
    every earlier expectation met. No row or command is declared independent, because a defect
    should not cost further Node starts.
  - **Classification before the run.** Every command carries the class of each anticipated outcome:
    PLAN, IMPLEMENTATION, CONTRACT, INPUT/HOST or UNKNOWN, each defined in `classes`, as plan review
    001 did for M0.
  - **Two cases to name.** A refusal of a probe row before its frozen check names one of this
    freeze's fixtures, so it is PLAN. Passing the frozen check would be the probe's fault, so it is
    IMPLEMENTATION.

## 6. Preconditions immediately before S7

- **P01:** the checker in phase `pre`.
  - It checks every binding (120, digest, size, mode, one link, canonical, spelled as on disk), the
    CF file, the boot, the evidence ancestors and the umask `0022`.
  - It checks that the worktree outside `.venv` holds no bytecode, and that no `.DS_Store` is in the
    worktree, the reader tree, the runtime or `<OUT>`.
  - It checks that every S7 path is absent, and that the reviewed MC11 list exists with status
    REVIEWED and a named reviewer, reporting its digest.
- **P02 to P04:** the observer's `static` with each MC10 plan, zero starts.
  - Each covers the inventory recheck of HR-03, the source with HEAD from the Git files, the
    packages, the runtime and its Mach-O rules, the reader tree, the Git binding and the ancestors.
  - Each also proves its plan valid and its attempt absent.
- **P05:** the Director's read-only `git status --porcelain=v1 --untracked-files=all`, with
  `GIT_OPTIONAL_LOCKS=0`. Its output must be empty.
- **D01:** `s7/prepare-s7-001.sh`, run once through the wrapper.
  - It creates 26 directories with `0o700`: six `TMPDIR`s, the cohort's and the two MC29 evidence
    roots, the MC29 inputs, two empty export directories, the syntax stage, and three directories
    per probe row.
  - It copies 18 files: the two MC29 configuration copies, and per probe row the manifest, the job,
    the GLB and the reference.
  - It refuses an existing path, and replaces or removes nothing.
- **D02:** the checker in phase `prepared`.
  - It checks every prepared entry exactly (mode, directory entries, digests) and the bindings
    again.
  - It checks that every later output is still absent, and evaluates P01 to D01's predicates.
- **Conditions outside the commands:**
  - freeze review 001 accepted (A6), its record giving this file's digest and the reviewed list;
  - the same boot, the volume mounted, the host awake;
  - no Finder, no other MH command running, and the Director's umask `0022`.

## 7. Every start I made

These are counted from my transcript. None was Node, Git of any kind, `ldd`, `codesign`, `otool`,
the observer's `observe`, the runner, the collector, the harness or `capture_probe.py`.

- **Python: 33 starts of `<worktree>/.venv/bin/python`.**
  - **31 under `-I -S -B`.** Of these, 29 were my own scripts or inline reads:
    - inspection of the frozen controls, refreezes and additions, and the scan summary: 12;
    - the binding check, the candidate list, the environment file and the fixtures: 4;
    - the generator twice and the composer once: 3;
    - the self-check three times: 3;
    - the checker once against this freeze, and its synthetic test in one process: 2;
    - reading results (the two discoveries, the checker's report, the composed commands): 4;
    - writing and verifying `SHA256SUMS.txt`: 1.

    The other two were the allowed `scan_mc11.py` once and the observer's `python-inventory` once
    (section 9).
  - **2 under `-B` only,** the allowed `discover_inventory.py discover` twice. Each was inside
    `env -i` with `PYTHONDONTWRITEBYTECODE=1`, as the tool requires.
- **Other starts.** I made 68 shell calls, all `zsh` from the session's shell tool. One of them
  stopped at a glob error before running any command.
  - **The utilities they ran:** `ls`, `find`, `grep`, `sed`, `awk`, `head`, `tail`, `wc`, `cat`,
    `tr`, `sort`, `mkdir`, `cp` (APFS clones, 58 entries), `rm` (the two clones and my own regenerated
    drafts), `touch`, `date`, `tee`, `env` and `umask`.
  - **One `shasum`,** a Perl script, early on. I used my own hashing afterwards.
  - **One `/bin/sh -n`,** which parses the preparation script without running it.
- **Writes.** Only under `<OUT>`, and the tests' own temporary directory inside it. Nothing in the
  worktree, the evidence parent or MP's inputs. The clones were removed.
- **At the end,** no process of mine was alive (section 9).

## 8. Deviations and open questions

**Deviations**
- **D1. The fixture bytes.** I built them by importing the project's builders in my own process.
  That is project code, run read-only with `-B` and process creation refused. The brief allows my
  own scripts; this is how `check_case` itself builds them.
- **D2. Two new tools for S7,** the checker and the preparation script. They are bound and need the
  review's attention like any tool. Without them, S7's preconditions, preparation and stop rule
  would be decisions left to the Director.
- **D3. Deferred values.** Four values in the argv cannot exist at freeze time:
  - the freeze's own SHA-256, which comes from the review record;
  - the reviewed MC11 list's SHA-256, which comes from the disposition, and which C01.X checks
    against the file;
  - the two discovery digests for C14, which come from the readbacks C12.L and C13.L, and which
    C14.X checks.

  Each has one stated source and a checked placeholder.

**Open questions** (also in the freeze)
- **Q1, TR2-06 and D-20.** The disposition says the configuration case's accounting refusal comes
  from the 0.1.0 code (F-07). At C the facade keeps the version that setup bound until the
  accounting has run (D-20; facade lines 1161 to 1217; REFREEZE-002's added MC29 case). So the
  refusal is the 0.2.0 provider's CH-SELECTION, and `cohort.json` is `cohort/0.2.0`. C06 expects
  that; the code is CH-SELECTION either way.
- **Q2.** The syntax check expects empty stdout and stderr exactly. Node has never parsed the probe
  (W5 section 7). A warning would stop MH as IMPLEMENTATION.
- **Q3.** Node's ExperimentalWarning for `--experimental-loader` is expected on stderr, but not
  observed. No predicate depends on stderr being otherwise empty.
- **Q4.** `STATIC_TRAY_READBACK_CPU_OUTPUT` is set, which departs from the driver's default path.
  The audit's root is therefore the cohort itself, not a preserved copy.
- **Q5.** The current discovery runs on an export of C, not on the worktree or a clone of it.
- **Q6.** The deferred values, as D3 lists them.
- **Q7.** The baseline prediction comes from MI's retained export. C12 classifies a difference as
  PLAN.
- **Q8.** H02's schema is the other version's, `ontokin.current-host-readback-config/0.1.0`, with
  the 0.2.0 key set.
- **Q9.** Each row's inputs are the documents and the stage files. The probe itself verifies the
  source and reader files against the bound inventories.
- **Q10.** host-state runs as the unit process runs (`-B`, site, `PYTHONNOUSERSITE=1`), as the
  tooling's tests ran it.
- **Q11.** The fixture bytes come from the project's builders (D1). C17's audit predicates compare
  them with the cohort's own bytes.

## 9. Final checks

- **The inventory.** The observer's `python-inventory` after all my work wrote
  `author/records/python-inventory-after-W2F.json`: SHA-256 `c277bdd3…`, 776,209 bytes, equal to
  plan 001's frozen inventory. My starts wrote no bytecode.
- **The worktree.** No entry of the worktree outside `.venv` is newer than my first file, and none
  is bytecode or `__pycache__`.
- **No process of mine** remained at the end. A process listing filtered for my scripts and tools,
  kept as context only (FC-P1), showed none.

## 10. Files

- **The freeze:** `FREEZE-001.json`, these notes, and `SHA256SUMS.txt`, which covers every file
  below.
- **The documents its commands bind:**
  - `config/`: the approved cohort configuration (D0), the two MC29 sources, and the methods and
    discovery documents;
  - `env/`: 12 frozen environments;
  - `probe/`: the four probe rows' configurations, manifests and jobs, two HOST copies, and the rows
    documents `rows-r1.json` and `rows-r2.json`;
  - `fixtures/`: the original GLB and reference bytes;
  - `mc10/`: three observation plans;
  - `mc11/`: the candidate list;
  - `s7/`: the checker and the preparation script.
- **My work:** `author/scripts/` (the scripts) and `author/records/` (their records). These are not
  used in S7.
