# Gate MH audit 001 (stage S8, acceptance A8)

Phase C271-P35, gate MH of `ontokin.current-host-readback/0.2.0` at design revision 4
(P33-AMENDMENT-001), local mode on the owner's macOS 26.6.2 arm64 host.

- **Auditor:** W4, a Claude Code subagent in a fresh context with the session's model (Claude Opus
  5.5). It wrote none of the freezes, the tooling, the observer, the provider, the probe, the
  contract, MP's preparation or any review, and took no part in any earlier stage.
- **Subject:** S7's run of operational freeze 002 (`FREEZE-002.json`
  `bc35d6347608f7e04d9968957fa9888bee983c51ff12f2a3799e02733a82a621`, 1,329,283 bytes), from
  2026-11-27T10:05:55Z to 10:32:45Z, at commit C `0eb9a5517f4e19705178a2c59b8d8d33fb87867a`
  (tree `ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b`), boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`.
- **Places:** `<worktree>`, `<local>`, `<home>`, `<prefix>`. OUT is
  `<local>/c271-p35/workers/W4-audit-001/`.

## Verdict

**PASS_WITH_NONBLOCKING_FINDINGS.** No blocking finding. Every item of P07 section 6 and every MH
obligation of the contract that S7 exercised was recomputed from the records and bytes with this
auditor's own code, and each holds. MH can be reported as passed, with the labels and limits of
item 12 and the eight nonblocking findings AU-01 to AU-08 stated.

## Method

- **Own code decides.** Every conclusion rests on this audit's scripts in `scripts/`. Each runs as
  `<worktree>/.venv/bin/python -I -S -B`, installs an audit hook that refuses every process
  creation, and writes one output by exclusive creation into `outputs/`.
  - a01 bindings; a02 starts; a03 direct probe; a04 seven methods; a05 numerical audit.
  - a06 N-04, controls, limits and labels; a07 FC-K1; a09 commit, index and exports from the Git
    files; a10 audit_expect and records; a11 checker summary.
  - z02 listing comparison; z03 process check; z04 builds `AUDIT-001.json`; z05 and z06 privacy
    scan and digest list. x01 to x06 are exploration aids.
- **Cross-checks only,** by the Director's decision for this audit:
  - the bound checker `w2f_s7_check.py`, run directly with `--freeze` and `--freeze-sha256`, 78
    times: `expect --command ID --audit` for the six commands with an `audit_expect`, and `expect`
    for all 72 ordered commands;
  - `audit_numeric.py` from the tooling at C, once;
  - the observer's `python-inventory`, once, at the end.
  Their stdout went only to `outputs/`.
- **Nothing changed.** A no-follow listing with SHA-256 was taken of the evidence parent,
  `director/`, both freezes, the three review directories read and MP's trees before the audit's
  checks and again at its end. They are identical: 0 entries added, removed or changed, mtimes
  included (z02). The Python inventory at the end is `c277bdd3…`, unchanged, so no bytecode was
  written. No process of this audit remains (z03).

### This audit's starts

| What | Count |
| --- | ---: |
| Shell-tool calls (one `zsh` each; whatever the harness's shell does at its own start is not observable here) | 56 |
| Interpreter starts, every one `-I -S -B` | 138 |
| — own scripts (44) and inline `-c` reads (14) | 58 |
| — bound checker, `expect --audit` | 6 |
| — bound checker, `expect` | 72 |
| — `audit_numeric.py`, cross-check | 1 |
| — observer `python-inventory` | 1 |
| `/usr/bin/env -i` launchers (each exec'ing the interpreter, same process) | 80 |
| Static-read utilities: `grep` 11, `head` 16, `cat` 15, `tail` 4, `wc` 3, `ls` 3, `mkdir` 2 | 54 |
| Node, Git of any kind, `ldd`, `codesign`, `otool`, `observe`, runner, collector, harness, discovery, `capture_probe.py`, wrapper, preparation script, test module | 0 |

The counts include this audit's last five calls: z04, z05 twice, z06 and the final z03.
- z05's first run stopped on a false positive, the prefix's three-letter first component inside the
  word "adoption", and wrote nothing. Its second run used the corrected term list.
- z06 corrected these start counts in `AUDIT-001.json`, repeated the privacy scan and rewrote the
  digest list.
- One call's pipeline failed on a shell glob before its first `grep` started. Its second `grep` and
  its `head` are counted as an upper bound.

## 1. The bindings

- **The freeze.** `FREEZE-002.json` hashes to `bc35d634…`, the value of the disposition of freeze
  review 002.
- **The 122 bindings, all hold:** kind, SHA-256, size, mode, one link, canonical path and on-disk
  spelling. So do the host fact `<home>/.CFUserTextEncoding` (`bd605d2e…`, 7 bytes, `0o400`, one
  link) and the seven evidence ancestors (device, inode, mode, no link).
- **Digest lists, line by line:**
  - freeze 002's `SHA256SUMS.txt`: 82 of 82;
  - P00's second list: 44 of 44 digest lines, besides two comment lines;
  - freeze 001's `SHA256SUMS.txt`: 85 of 85;
  - the tooling's `TOOLING-SHA256SUMS.txt`: 21 of 21. The nine `tool:` bindings equal it.
  No file in either freeze directory is unlisted, and none is newer than its list.
- **The cohort configuration** `83c8b158…`, 2,014 bytes:
  - schema `config/0.2.0`, `parent` null, source root the worktree, commit and tree equal to C;
  - its six descriptors verify: the contract source `42db98dc…`, the adoption record `872312ed…`,
    the source inventory `95abd300…`, HOST `34e94f29…`, the dependency inventory `3545d5f9…` and the
    methods document `ae687f2f…`;
  - the methods and discovery documents' own descriptors verify;
  - `original_bodies` equals the probe's constant and both providers' constants.
- **HOST's 20 descriptors.** 19 verify. One is relative to the runtime directory and equals the
  bound Node (AU-08).
- **The probe, the loader and Node:** `bca11b2a…` (58,452 bytes), `927190e6…` (564 bytes),
  `6f320694…` (122,545,856 bytes, `0o755`).
- **The reader tree:**
  - its 24 files equal the dependency inventory and the historical C199 binding, which names the
    same 24;
  - directories and modes are equal;
  - no link, special file or `.DS_Store`;
  - the C195 archive `b1e54a6c…` verifies.
- **The inventories, entry by entry:**
  - **Source inventory:** each of its 644 files matches the worktree (SHA-256, size, mode, one
    link). The file set equals the probe's own source rules (SOURCE_TREES, SOURCE_REQUIRED,
    SOURCE_OPTIONAL), with no bytecode. Q02's output is byte-identical to the frozen inventory.
  - **Python inventory:** the framework's 3,788 entries and the venv's 345 entries, recomputed,
    give 0 mismatches and 0 extra entries, so no bytecode was added. The five external closure files
    verify. Q01's output is byte-identical, and the observer's rerun at the end of this audit gives
    `c277bdd3…`.
- **What each Node start used, from its own records:**

| Start | argv digest | job | manifest (its selection) | configuration bytes |
| --- | --- | --- | --- | --- |
| syntax check | — | — | — | — (argv: Node, `--no-addons`, `--max-old-space-size=256`, `--check`, probe) |
| P06-H01 | D0 `83c8b158…` | `74d90fdb…` | `dc79f726…` (D1 `16032c32…`) | D1, by design ≠ D0 |
| P06-H02 | `48d33d34…` | `3dc6fd07…` | `4aa599df…` (`48d33d34…`) | `48d33d34…` |
| MC30-probe | `f86d32c7…` | `4d25e839…` | `c301fa28…` (`f86d32c7…`) | `f86d32c7…`; the job binds the empty string's digest for the GLB, by design |
| MC36 | `8f46961e…` | `6151ea76…` | `c62fc516…` (`8f46961e…`) | `8f46961e…` |
| C17 Q01 / Q03 / changed | `83c8b158…` | `a62f4b83…` / `093cbe5d…` / `dd4b1910…`, equal to the ledgers' job bindings | `6f1a3633…` (`83c8b158…`) | `83c8b158…`; every ledger's preflight equals its postflight |

  Every job's manifest digest equals the manifest's bytes. Every start's probe, loader and Node
  hash to the bound values. The manifests of C16 and C17 bind HOST `34e94f29…`, and those of
  MC30-probe and MC36 bind their HOST copies.
- **The worktree,** read from the Git files with this audit's own reader:
  - HEAD resolves to C. C's commit object hashes correctly, and its tree is `ea10cd94…`.
  - Each of the index's 22,490 entries equals its worktree file's blob hash and mode, with no stage
    or skip flags.
  - The tree computed from the index is `ea10cd94…`.
  - There is no untracked file outside `.venv`, no bytecode and no `.DS_Store`.

## 2. Starts, by P07 section 4's rules

| Row | Where | PID | Start established by |
| --- | --- | ---: | --- |
| M0 Git `--version` | S5 | 7994 | receipt with positive PID, plus started record |
| M1 Node `--version` | S5 | 7995 | receipt, plus started record |
| probe syntax check | C16 R1 | 33371 | audit event, started record, receipt |
| P06-H01 | C16 R1 | 33379 | audit event, started record, receipt |
| P06-H02 | C16 R1 | 33380 | audit event, started record, receipt |
| Q01-positive | C17 | 33806 | audit event, provider started record, receipt |
| Q03-positive | C17 | 33835 | audit event, provider started record, receipt |
| Q01-changed-reference | C17 | 33862 | audit event, provider started record, receipt |
| MC30-probe | C19 R2 | 34541 | audit event, started record, receipt |
| MC36 | C19 R2 | 34550 | audit event, started record, receipt |
| MC37's Python child | C15 | — | one audit event, plus the test's own EPERM and ESRCH evidence (AU-02) |

**MH: 9 Node starts and 2 other starts.** That is S5's 1 and 1, then C16 3, C17 3, C19 2 and C15 1:
exactly the frozen totals.

- **Audit events in S7: 109.** C06 15, C07 25, C15 1, C16 3, C17 63 (3 Node and 60 Git), C19 2.
  Every one is `subprocess.Popen`, none blocked. Every other S7 record (C01 to C05, C08 to C14,
  C18, every `.L` and `.P`) holds zero process events.
- **Programs.** The 109 are the bound Node 8 times, the bound Git 100 times and the bound interpreter
  once (MC37). The provider's Git reads are 15, 25 and 60, as frozen. In C17, 15 fall in the class
  setup and teardown and 15 in each CPU test: 12 selection checks of 5 reads each.
- **Receipts with a positive PID:**
  - the eight S7 Node PIDs. Each has one audit event, a started record, a receipt file equal to the
    record, and a group equal to the PID;
  - S5's 7994 and 7995;
  - the simulated MC10 receipts 999990001 and 999990002 (AU-03).
  The other positive PIDs are the tools' own self-records: 37 in S7 and 2 in S5. They belong to the
  freeze's 64 Python launchers, which are recorded and not bounded.
- **Cleanup.** Every receipt shows `cleanup.passed`, `process_group_absent`, `reaped` and
  `handles_closed` true. C16.P (3 targets), C17.P (3) and C19.P (2), and S5's probe (2), show every
  target absent, with `kill` and `killpg` both ESRCH. MC37's child was reaped by the test, and its
  group then answered ESRCH.
- **No start is UNKNOWN or interrupted:**
  - every runner row is `OBSERVED_ONE`, `COMPLETED` and not interrupted;
  - both collectors are `ALL_PASSED`, with complete journals (31 and 7 lines, ending `stop_run`);
  - the three ledgers are `COMPLETED`, `COMPLETED` and `SUPERVISOR_REFUSAL` (the expected exit 1),
    each with one start; `cohort.json` passed with 3;
  - the only `UNKNOWN` strings are the observer's pre-start intent records.
- **No other program** started in any S7 command, as far as the audit hooks see (AU-05). Nothing
  records `ldd`, `codesign`, `otool`, `observe`, or Node outside C16, C17 and C19.

## 3. The direct negatives and the syntax check (C16)

| Row | Starts | Exit | Receipt error | stdout | stderr | `probe.json` |
| --- | ---: | ---: | --- | ---: | --- | --- |
| probe syntax check | 1 | 0 | none | 0 B | 0 B | none (empty stage) |
| P06-H01 | 1 | 1 | `OTRAY-E-BACKEND` "Child exited with status 1" | 0 B | 1,434 B: `CH-SELECTION: manifest digest is not external approval`; not H02's text | absent |
| P06-H02 | 1 | 1 | the same | 0 B | 1,400 B: `Current-host binding: wrong configuration contract/schema`; not H01's text | absent |

The recorded stdout and stderr equal the log files byte for byte. Each receipt file equals the
runner's record, and the boot before and after each row is `C90010BA…`.

**The mutations,** compared with the approved configuration:
- H01 differs only in `evidence_root`. Its digest D1 is the manifest's selection, while argv keeps
  D0.
- H02 differs in `evidence_root` and in schema `config/0.1.0`, and argv carries its own digest.
- MC30 and MC36 differ in `evidence_root` and `host`. Each HOST copy differs from HOST only in
  `environment.cf_user_text_encoding`: null in MC30's, `0x1F5:0x8000100:0x0` in MC36's.

**The source-backed inference of P07 section 5 holds for the bound bytes.**
- **The probe** (`bca11b2a…`):
  - its static imports are `node:` builtins only (fs, path, crypto, module, url, os);
  - `approvedEnvelope(args)` runs at line 704, outside the `try` that begins at 713;
  - H01's selector is at line 626 and H02's at 632, both inside `approvedEnvelope`;
  - the readers are reached only through `require(manifest.validator_entry)` (729) and two dynamic
    `import()` calls (739, 740). These follow `verifyBootstrap` (719) and the input-identity check
    (722), and the file holds no other `require(` or `import(`.
- **The stack traces on stderr** name exactly those lines: 123, 626 and 704 for H01, and 119, 632
  and 704 for H02.
- **The loader** (`927190e6…`) imports only `node:url` and `node:path`. It exports one `resolve`
  hook and makes no `import()` or `require()` call, so it preloads nothing.

This is an inference from the source and the refusals, not an OS-wide module trace.

## 4. The seven methods (C17) against P07 section 6

- **IDs.** The seven raw IDs `tests.test_static_tray_readback_v01.<Class>.<method>` are the same in
  `outcomes.json` and in unittest's own stderr lines: all `pass` and `ok`, "Ran 7 tests in
  7.827s", "OK". Joined through the declared prefix alias alone, they equal discovery-001's seven
  IDs and P07's table exactly. There are no class-level events, unplanned events, loader errors or
  bytecode.
- **Source, class, method and body identity.** Module `6295e044…` is the same before and after.
  This audit's own AST digests of the nine bodies equal `methods-001.json`'s `original_bodies`:
  `check_case`, `run_seam` and the seven methods, each found at its own class and line, with no
  decorator.
- **The CPU starts.** There are three Node events, one per case, each inside its own test's
  journal window. Each case has one provider ledger with one start.
- **The coordinator quartet.** No process event falls in the four seams' windows. The seams patch
  `format_check.run_process` with a stand-in, and the label mocked comes from the freeze (AU-06).
- **Imported reader versions,** recorded at run time in every case: validator `2.0.0-dev.3.10`, from
  `validator.version()` and the report; Three.js `0.186.1`, revision `186`; Node `v24.22.1`. The
  bound `package.json` files agree.
- **Raw counts.**
  - stdout: 174, 174 and 184 bytes, one JSON line each;
  - stderr: 417 bytes each, Node's loader ExperimentalWarning only (AU-07);
  - receipts: observed equals retained, 591, 591 and 601;
  - C17's own stdout is 0 bytes and its stderr 1,433.
- **Preserved inputs.** Each GLB and reference equals its job's digests, the ledger's
  `artifacts_after` and the freeze's independently built fixtures: Q01 `d00a7362…` and `7f10f355…`,
  Q03 `02a495d5…` and `ae24b5ee…`, changed `d00a7362…` and `26d78f8d…`. `input_preserved` is true in
  each.
- **Scientific predicates.** These come from the reports' retained values and from this audit's own
  reading of each GLB:

| Predicate | Q01 | Q03 | changed reference |
| --- | --- | --- | --- |
| nodes, meshes, scenes, animations, cameras | 14, 12, 1, 0, 0 | 14, 12, 1, 0, 0 | 14, 12, 1, 0, 0 |
| semantic identities equal to the reference's 14 | yes | yes | yes |
| names, extras (roles and relationships), children, parents | equal | equal | equal |
| materials; indices (36 per mesh) | equal | equal | equal |
| layout: POSITION and NORMAL VEC3 float (24 per mesh), indices SCALAR uint16, triangles | yes | yes | yes |
| every retained value and measurement finite | yes | yes | yes |
| bounds equal to min/max of the world vertices | yes | yes | yes |
| external resources: no `uri` in the GLB; one buffer stored in the GLB; the probe forbids fetch, external resources and URL resolution | yes | yes | yes |
| validator: errors, warnings, infos, hints; truncated | 0, 0, 0, 0; no | 0, 0, 0, 0; no | 0, 0, 0, 0; no |
| exact-comparison findings | none | none | none (only the matrix row) |

## 5. The numerical audit, recomputed

The row inventory was built from the retained reference alone, in the probe's order. For each node
identity, in sorted order, there are 16 world-matrix terms. Each mesh node adds one world-position
row and one normal row per vertex and axis, then the minimum, maximum and size of its world bounds
per axis.

- **Actual values.** Matrix terms are the retained importer matrices. World positions are
  recomputed from the retained local positions and matrix, in Three.js r186's `applyMatrix4`
  operation order. Normals are the retained importer normals.
- **Rows.** Difference is `|actual - expected|`. The threshold is 5×10⁻⁶ for positions, bounds and
  the terms `[0..2][3]`, and 10⁻⁶ otherwise. A row passes when both values are finite and the
  difference is within the threshold.

| Case | Rows | Unique | Same order and values as the report | Failed rows | Findings |
| --- | ---: | --- | --- | ---: | ---: |
| Q01-positive | 2,060 | yes | yes, 0 mismatches | 0 | 0 |
| Q03-positive | 2,060 | yes | yes, 0 mismatches | 0 | 0 |
| Q01-changed-reference | 2,060 | yes | yes, 0 mismatches | 1 | 1 |

- **Each case's 2,060 rows:** 224 matrix terms, 864 world positions, 864 normals, and 36 each of
  minimum, maximum and size.
- **The negative's one row,** `equipment-tray/pair/left/base` `matrix_0_3`:
  - actual −0.3, expected −0.299;
  - difference 0.0010000000000000009, within 8.7×10⁻¹⁹ of 0.001, so within the 1e-9 bound (T-10);
  - threshold 0.000005;
  - its report has no `error` member, so it is a scientific rejection.
  Every other row passes. The changed reference differs from Q01's only in that term and in the
  scope text, and the two GLBs are byte-identical.
- **Against the GLB's own bytes:**
  - each mesh's float32 positions, normals and uint16 indices, read by this audit, equal the
    importer's retained values exactly;
  - world matrices composed from the node transforms equal the retained matrices exactly;
  - recomputed world vertices and bounds equal the retained ones exactly;
  - the largest passing difference is 5.6×10⁻¹² of its threshold (Q03); all others are 0.
- **C18.** C18's record lists the same 6,180 rows, equal to this audit's row by row. The single
  cross-check run of `audit_numeric.py` passed, and its rows equal C18's.

## 6. N-04, MC30 and MC36

**The elimination, as `n04` states it, holds on the records.** Call the declared environment D and
HOST's recorded value V (`0x1F5:0x0:0x0`).
1. Q01-positive and Q03-positive ended with `probe.json` passed true under HOST `34e94f29…`, which
   records V. `verifyBootstrap`'s environment check therefore admitted Node's `process.env` as D, or
   as D with `__CF_USER_TEXT_ENCODING=V`. The changed reference also reached the scientific body.
2. MC30-probe ran under a HOST copy that records null. It refused with "Current-host binding:
   actual Node environment differs", not "Actual input identity differs", so `process.env` was not
   D.
3. Hence `process.env` was D plus the variable with V. The value is not read directly (T-04).
4. MC36's copy records `0x1F5:0x8000100:0x0`. It refused at the same selector, where frozen, with
   `passed` false and no `khronos` or `three` member. The environment check, at line 487 in
   `verifyHost`, precedes every reader import, so MC36 never reached the readers. Its result labels
   are as found and unverified (W5 Q5).

**The assumption's conditions:**
- **One executable.** All nine Node receipts name the same `argv[0]`. Its digest was verified
  before each start and again now.
- **One supervisor.** `supervisor_darwin_v01.py` `bd4a5e3f…`, compiled from verified bytes by both
  runners; the same file is listed in C17's loaded project files.
- **One declared environment.** All nine receipts record the same map, equal to the declared file
  and to HOST's `declared`.
- **One user.** UID 501 (`0x1F5`) owns the CF file and every `probe.json` the Node starts wrote,
  and is the prefix of the value admitted by the C15 and C17 collectors.
- **The CF file unchanged.** The checks of P01, D02, C17.X and Q04 all record `bd605d2e…`, and this
  audit's own read now gives `bd605d2e…`, 7 bytes, `0o400`, one link.
- **The order.** MC30-probe ran before MC36, with `rows_independent` false, and C19 started after
  C17 ended.

## 7. The MH controls and their labels

| Control | Label | Commands | Outcome, from the records |
| --- | --- | --- | --- |
| MC10 | mocked (command boundary), real static bindings | C03–C05 | `v24.22.0\n` and `v24.22.1` without newline refused `CHO-OUTPUT`, with no HOST or completion; `v24.22.1\n` accepted, HOST labelled mocked, runtime `v24.22.1`, `OBSERVED_UNAPPROVED`; zero audit events |
| MC11 | real (static; a name scan cannot exclude every dynamic route) | C01 | frozen rule passed, 587 dynamic hits reviewed and 0 unreviewed; wider scan finds no process creation; reviewed list `aade03ac…` matches; 0 unresolved specifiers; 25 files; totals 628, 23 and 53 |
| MC24 | real | C17, C18 | Q01 and Q03: exit 0, every row passes, result written |
| MC25 | real | C17, C18 | exit 1, exactly the intended `matrix_0_3` finding |
| MC26 | mocked (the original seams) | C17 | the four seams pass, with no process event |
| MC27 | real | C16 | item 3 |
| probe syntax check | real | C16 | exit 0, empty streams |
| MC28 | real | C08–C14 | recomputed: baseline 5,587 IDs in 382 modules and current 5,994 in 388, equal to baseline plus exactly the 407 additions of `f710dbb5…` (per module 109, 151, 22, 49, 59, 17), none missing or extra; sorted digests `bcc36ee7…` and `32b2b861…` recomputed; no failed import, loader error, process event, duplicate or bytecode; each extracted export's tree hash equals its commit's tree (`fb012dfe…` for 1c2f25ba, `ea10cd94…` for C) |
| MC29 | mocked (supervisor recorder) with the real detectors | C06, C07 | configuration: attempt and accounting `CH-SELECTION`; job input: attempt `CH-JOB`, accounting `CH-EVIDENCE`; zero supervisor and `on_started` calls and zero Node events; Git reads 15 and 25; the consumed copy is the source plus one space, and the job-input GLB is the fixture plus one zero byte, as frozen |
| MC30 | real (positive direction and MC30-probe; the value by elimination only) | C17, C19 | item 6 |
| MC36 | real, after MC30-probe | C19 | item 6 |
| MC37 | real | C15 | `raw_unreaped` EPERM, `raw_reaped` ESRCH; module `3b8c91b7…` equals CONTROLS-REFREEZE-002's; one other start |
| F-04 | real | C02, C17 | `host_state` equals HOST's platform and OS, with nothing substituted and the boundary real before and after; `setup.json` and every ledger carry boot `C90010BA…` and `boundary` real |
| MC09 | real, positive direction only | C02, C17 | the change cases stay MI's (simulated) |

**NOT_RUN at MH, and never reported as passed:**
- MC01 to MC08, MC12 to MC17, MC20 to MC22, MC23 (MR's), MC31, MC33 to MC35, MC38 and MC39;
- MC18, MC19 and MC32 as controls. Only their positive direction runs, in every selection check and
  in P02 to P04 and Q01;
- MC29's source, runtime, dependency and OS-build cases, which are MI's simulated cases;
- MC30's case without the variable, MI's mocked case.

## 8. Limits

- **The clocks.**
  - Every direct row: `total_ms` 30,000, `stage_ms` 28,000, a reserve of 2,000. Rows took 36 to 128
    ms.
  - `check_case`: `Clock(total_ms=30000)` and `stage_end = clock.started + 28`. Each CPU child ran
    0.24 s.
  - The manifest's limits equal the probe's constant: 30,000 / 28,000 / 2,000 ms, 8 MiB GLB, 4 MiB
    result and log, 12 checks.
  No long outer timeout extends them, and the largest command took 7.98 s.
- **The file-size caps:**
  - GLB 21,152 and 21,176 bytes, against 8 MiB;
  - results 643 KB and references 567 KB, against 4 MiB;
  - logs 545 to 1,434 bytes, against 4 MiB;
  - manifests 21 KB, against 1 MiB;
  - jobs 803 to 839 bytes, against 32 KiB.
  The probe's own bounds are 8 MiB, 4 MiB, 1 MiB and 32 KiB.
- **The supervisor's caps** are unchanged in bound `supervisor.py` `c47b84ab…`: 64 MiB of output and
  2,048 entries. Each stage holds 7 entries and about 1.23 MB.
- **GOAL's ceilings** of 100,000 operations and 30,000 ms are the runtime's source-execution
  ceilings, for example `ontokin/construction.py` `LIMITS`. The cohort runs no `.ok` source, so no
  S7 record shows them. Their source is unchanged: the worktree is clean at C, and the inventory is
  equal.
- **The unused native-schedule directory** is absent in the cohort root, in all four probe-row
  cohort roots and in both MC29 roots.

## 9. FAILURE-CAPTURE and FC-K1

- **No capture record exists.** There is no `*.failure-capture.json`, and none of the 125 overrun-
  and stop-command paths exists.
- **S5 is unchanged.**
  - All 39 files of `observe-001/` and its beside-files equal HOST review 001's reviewed digests.
  - Its 45 readback entries are unchanged.
  - The Director's logged digests hold: HOST `34e94f29…`, readback `058aee0b…`, probes `9030422f…`,
    completion `fd1a0350…` and result `1b4cae0f…`.
  - Nothing in it is newer than 05:35:19Z, and the empty static `command.json` is retained.
- **MP's inputs, the freezes and the worktree are unchanged** (item 1). The 43 prepared entries
  match the freeze, except the one copy C06 consumes by design.
- **The evidence parent** holds 370 entries: 21 of S5 and 349 of S7. Every S7 entry is in the
  495-path list, apart from P00's and P01's own eight records, which that list leaves out by
  construction.
- **The absent-path lists:**
  - of the 495, 370 now exist and 125 do not; of the 428, 303 exist and 125 do not;
  - every path that exists was created by the frozen command or preparation step that names it;
  - every path that is still absent is a capture-command path, as frozen.
- **The six temporary directories are empty.** No temporary cohort was made.

## 10. The audit_expect sets

C01 has 3 rules, C06 2, C07 2, C12 3, C13 3 and C17 9: 22 rules in all. This audit's own evaluator
finds all 22 met.

- MC11 totals: 628, 23 and 53.
- Git reads: 15 and 25.
- Discovery: 382 and 388 modules, sorted digests `bcc36ee7…` and `32b2b861…`, and `-B` derived from
  `build_plan`.
- C17: 60 Git events and 63 events in all, 9 `original_bodies`, and the six cohort input digests
  equal to the fixtures.

The bound checker's six `expect --audit` runs are all `MET`.

## 11. The records' own consistency

- **All 72 command records** were checked in the frozen order:
  - schema and name;
  - argv equal to the frozen argv after the named substitutions: the freeze digest, and the
    discovery digests `8d53b1c9…` and `48db9799…`, which equal the files now;
  - cwd, the environment file and its digest;
  - boot before and after, `C90010BA…`;
  - wall time equal to end minus start;
  - the exit file equal to the status (0 everywhere, as frozen);
  - stream digests and sizes, retries 0, and the writer `run_once_v2.sh`.
- **The order.** The commands are strictly ordered, without overlap, with gaps of 15 to 39 s between
  them. Every wall time lies far below its outer bound.
- **The checks:**
  - every `.X` is `MET`, with a predicate count equal to the frozen count (705 in all);
  - P00 has 126 OK lines;
  - P01, D02 and Q04 are `MET`: 122 bindings; 495 and 428 absent paths; 43 prepared entries; 17
    prepared inputs; 66 and 24 earlier predicates.
- **The cross-check.** The bound checker's 72 `expect` runs are all `MET` now, with 1,248
  predicates. No stray command record exists.
- **The Director's log** agrees with the records: C16 0.396 s; C17 7 tests in 7.827 s with 63
  events; `.X` counts 67, 87 and 59; Q01 `c277bdd3…`; Q02 `95abd300…`; Q03 empty; Q04 with 24
  predicates.
- **The timer lines** are not on disk (AU-04).

## 12. What MH may and may not claim

**If reported as passed,** MH qualifies the seven original methods of
`tests/test_static_tray_readback_v01.py` and the direct negatives P06-H01 and P06-H02 on this
executor only. It is not MR, R03, R04, R05 or a release (MH-PLAN section 1).

**The results carry contract section 10's labels.** Every cohort result, ledger, setup and cohort
record checked carries exactly these:
- executor `macos-arm64-local`;
- contract `ontokin.current-host-readback/0.2.0`, design revision 4, P33-AMENDMENT-001, profile
  `darwin-arm64-v1`;
- OS 26.6.2 (25G83), with the cryptex present at 26.6.2 (25G83);
- Node archive `node-v24.22.1-darwin-arm64.tar.gz` `89c68259…`, and the executable `6f320694…`
  (122,545,856 bytes, `0o755`);
- Python inventory `c277bdd3…`;
- the bound Git `be4afb2b…`;
- run kind `qualifying`, boundary `real`.

The outcome must also label MC10, MC26 and MC29 mocked, and report the NOT_RUN controls of item 7 as
NOT_RUN. The two refused results' labels (MC30-probe, MC36) are reported as found and unverified.

**Never claimed:**
- contract section 10's nine items: a Linux x86-64 qualification; the C199/C225 replay; P05's Gate
  H for the Codex build; the ELF policies; N34 or N57; descendant reaping or any enforcement
  against descendants; a per-file closure of the macOS system libraries; durability beyond `fsync`;
  a binding of run-time loads;
- HOST's four claims as complete (HR-06);
- a verified signature for the Node archive (`signature_check` `not_performed`);
- Node behaviour beyond these cases (contract section 12).

**Limits the outcome must state:**
- a name scan cannot exclude every dynamic route;
- the audit hooks do not see `_posixsubprocess.fork_exec`, ctypes calls or earlier lookups
  (FC-P7, AU-05);
- the no-reader-import conclusion is a source-backed inference;
- the CF value follows only by elimination;
- the driver's default temporary-cohort path is not exercised;
- the CF file's mode, link and user are only partly checked;
- the overrun procedure's limits;
- the 1e-9 tolerance is the harness's own (T-10).

## 13. Anything else

- **The recorded launch deviation** is AU-01.
- **Simulated PIDs** are AU-03, and the missing MC37 receipt is AU-02.
- **Records as frozen.** C06 consumed its copy, the source plus one space. The job-input stage's
  GLB is the fixture plus one zero byte, while the prepared job-input copy is unchanged. Both are
  as frozen.
- **Reviews and dispositions.** Freeze review 002 accepted with six nonmandatory findings.
  FREEZE-REVIEW-DISPOSITION-002's readings were applied: two calls per launch, with the one
  exception of AU-01; no overrun; FR2-05's pre-P00 read recorded with `bc35d634…`, `0f441f5f…` and
  `3c24f923…`.

## Findings

All eight are nonblocking.

| ID | Blocking | Finding |
| --- | --- | --- |
| AU-01 | no | C01's launch message held a third call, a foreground log append, before the launch pair, against FR2-03 (a). It ended before C01's call began. C01 ran once (exit 0, retries 0, wall 2.0 s), its timer was the pair's second call, and later launches held two calls. There was no effect on the bound, the order or any record. Keep it in the outcome as a recorded launch deviation. |
| AU-02 | no | MC37's other start (C15) has no receipt or PID on record, so FC-P3 could not probe it (as frozen in `no_pair`). The start and its cleanup rest on one audit event and the passing test's own evidence: EPERM while unreaped, ESRCH after `Popen.wait`. The outcome should say this rather than cite a receipt. |
| AU-03 | no | The MC10 harness (C03 to C05) wrote supervisor-shaped receipts with positive PIDs 999990001 and 999990002. These lie above Darwin's PID_MAX (99999), are labelled mocked, have no audit event, and pass `zero_process_starts`. They are simulated, not starts, and a literal reading of P07 section 4 over every record would count them. Name them as simulated in the outcome and its portable copies. |
| AU-04 | no | The bound timer writes nothing, so its 72 lines are not on disk; the Director's log summarizes them. The audit decided the bound from the records instead (FR2-03 (b)): strict order, no overlap, and a largest wall of 7.98 s against bounds of 120 to 600 s. If S9 cites the lines, keep them from the session transcript. |
| AU-05 | no | "No other program started" holds only for the routes the audit hooks see. The provider's 100 Git reads have events but no receipt or probe, and their own children are not observed. P00, P05, Q03, C08 to C11 and D01 run without any hook. That is the frozen design (FC-P7). The exports were confirmed independently to equal their commits' trees. |
| AU-06 | no | `outcomes.json` records the four coordinator seams as passing, without a label. The label mocked comes from the freeze (MC26) and the test source. P07 section 6 keeps the four results labelled mocks, so the MH outcome must carry the label. |
| AU-07 | no | Every Node start through the module loader writes Node's 417-byte ExperimentalWarning that `--experimental-loader` may be removed. It is not an error, and no predicate depends on it. The contract's argv keeps the flag, which a later Node may drop: a note for MR and R04. |
| AU-08 | no | HOST's `runtime.node_source.content.extracted` is the only relative descriptor (`bin/node`, copied from `NODE-SOURCE.json`). A generic recomputation reads it as absent. Its digest equals the bound Node. Documentation only. |

## Files in OUT

| File | Content |
| --- | --- |
| `AUDIT-001.md` | this record |
| `AUDIT-001.json` | the same content, structured: start counts, per-case rows and failed rows, controls with labels and outcomes, every item's evidence, and the SHA-256 of 993 audited files (the exported source trees by their tree hashes) |
| `scripts/` | x01 to x06, a00 to a11, z02 to z06 |
| `outputs/` | every script's output and stdout, the checker's 78 outputs and exit codes, the `audit_numeric.py` cross-check, and the observer's Python inventory |
| `SHA256SUMS.txt` | the digest of every other file in OUT, except the last process check's output (`outputs/z03-process-check-3.json`), which is written after it |

Portable-copy note: the scripts and the raw outputs carry machine paths taken from the records.
This record and `AUDIT-001.json` use the labels only.
