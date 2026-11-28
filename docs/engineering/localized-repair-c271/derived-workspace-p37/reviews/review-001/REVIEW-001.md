# Review 001 of C271-P37 candidate C (stage S7)

Reviewer: W3, the phase's independent reviewer, a subagent in a fresh context with the session's model, for
Director `c271-p37-08beec34eb0a`. I took no part in this phase: I wrote none of the plan, the decision, the
implementation or the controls. Times are UTC. The JSON record is [REVIEW-001.json](REVIEW-001.json).

Labels: `<worktree>` the C271 worktree; `<local>` the data root beside the clone; `<P37>` = `<local>/c271-p37`;
`<W3>` = `<P37>/workers/W3-review-001`; `<tmp>` the per-user temporary directory in resolved form; `.../` =
`<worktree>/docs/engineering/localized-repair-c271/`.

Inspected candidate: C = `5a3502e22d0fa4b29fbff2c867f1aab8271c4235`, tree `9249fdeb2ea3b80ac7f05c1ee3a7f0ce4d88e580`,
parent the declaration commit `2f728998456c829f3cdc13bbf72d6dd805fefa36`. Acceptance criteria: A7 of
`.../derived-workspace-p37/PHASE.json` and the six items of the S7 brief.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** No finding is mandatory. C closes the phase's correction: A2 to A6 hold
on the evidence I recomputed, this review meets A7, and A8 remains for S8. I did not check A1's and A5's pushes
and readbacks, since I start no Git and no network. C can be the basis of the next gate MR attempt, which still
needs its own observation plan, HOST and freeze at the corrected commit.

- The decision's rule is exact, stays within P05 section 3 and MC19, and needs no amendment. Every MC19 case
  still refuses.
- The implementation matches the decision, with one definition of the copied set and no other change of
  behaviour. The refresh keeps every summary field and value.
- The controls were frozen by an independent author before the Director ran them.
- S5, S6, the discovery and the additions record recompute exactly from the raw files.
- Walking R1's route at C, I find nothing else in this phase's scope that refuses it. The checks after the
  source check have never run on a real derived selection (RV-06 e).

There are six nonmandatory findings, RV-01 to RV-06, and two observations.

## Digests of the candidate's eight changed files, computed from the bytes

I read Git's object and index files directly and started no Git. The worktree's bytes equal C's blobs.

| File | SHA-256 | Bytes | Blob at C | Blob at the parent |
| --- | --- | ---: | --- | --- |
| `.../derived-workspace-p37/CONTROLS-FROZEN.json` | `7c5f86ca92d8e6452b73e89ce9c97475533f6a7bed23a1a7a8266fb26c534a8a` | 172,127 | `aafa6411` | new |
| `.../derived-workspace-p37/DECISION-001.md` | `7a1626cb7916d744c7e91f6c82f6ce84d72a9c4e84d44bfa8004fdcdd21815fe` | 27,829 | `6eee5f22` | new |
| `.../derived-workspace-p37/interfaces/W1-CORRECTION.md` | `ce434b54e4b1de5d899bfc5ff4b41398bad5e3efcf1d6d79c088bed3be13abf5` | 20,576 | `68c03e34` | new |
| `prototypes/static_tray_v01/current_host_readback_v02.py` | `bab89614c9ceeeaae56e9e264937cae482feda5bf08bda13c5972ad7412f902b` | 83,145 | `5b681575` | `b410c399` |
| `tests/test_current_host_readback_derived_controls_v02.py` | `c0eebef7796cecda2725f717aebd1f912947ee67feda690e8ac03ce9d564199a` | 85,712 | `c08bd517` | new |
| `tests/test_current_host_readback_provider_v02.py` | `95e04a46ad8a3a0691b40e7a2809154040a7a272c0a25c60e86c48540dbafc83` | 112,238 | `a24d9aaf` | `6ad8be8c` |
| `tests/test_local_checks.py` | `0ceb6b8342178322d3253e7e1c733add498564a43f521b6ec8653ee56f7e6125` | 47,088 | `f666b640` | `1e359887` |
| `tools/check_local.py` | `3136f52cef8ca4492e06f6c12898ea9f6e9f101eb5b34e4fed5c61b8b9be5ab8` | 52,020 | `705577f2` | `f39f2936` |

What I verified with [s1-candidate-identity](outputs/s1-candidate-identity.json):
- **The commit.** The branch ref is C; C names tree `9249fdeb` and the one parent `2f728998`.
- **The changes.** The tree comparison finds exactly these eight paths.
- **The provided diff.** It has the expected SHA-256 `862baca6…`. Applied to the parent's blobs, each of its
  eight sections gives C's blob, and every `index` line matches.
- **The worktree.** Its index (version 2, 23,156 entries) equals C's tree, and every file's stat data matches
  its entry. Every file outside `.git` and `.venv` is in the index, and there is no bytecode.

The same check after my test runs gave an identical record, and the `.venv` holds no `.pyc`.
Neighbouring files that stay unchanged:
- the 0.1.0 provider, `cb3f0c7f…`;
- MI's frozen control module, `3b8c91b7…`;
- the observer, `471a9547…`;
- `tools/storage_identity.py`, `c8a88e9e…`.

## Findings (all nonmandatory)

### RV-01. The F-01 correction gives one refusal reason where there are two

- **Evidence.** DECISION-001 section 2, "Not missing source", says that a missing file of the source set always
  refuses through the binding, with `CH-SOURCE`, `Complete CPU source inventory differs`. That holds for a
  missing or added file of a source tree or an optional file. A missing source role, a `SOURCE_FILES` path such
  as `pyproject.toml`, refuses earlier, in the observer's path check, with `CH-SOURCE`, `Bound path or ancestor
  is missing: <path>`. W2 froze that reason in P37-C21, and my run of the control module confirms it.
  - The rule and its fail-closed conclusion are right.
  - F-01's own case is stated exactly: a source-tree file outside the copied set, such as `ontokin/.env`.
  - At C no source role lies outside the copied set ([s2-tree-scope](outputs/s2-tree-scope.json)).
- **Change.** In the phase's S8 records, which leave C's reviewed text unchanged, state both reasons:
  - a missing tree or optional file gives `Complete CPU source inventory differs`;
  - a missing role gives `Bound path or ancestor is missing: <path>`.

  No code change.

### RV-02. Scripts that made cited evidence live only in the session's scratchpad

- **Evidence.**
  - The Director's `measure_fz02.py` (`93f0cac7…`, the digest that WORKERS.md records), `s5_run.py` and
    `s5_compare.py` exist only in the session's scratchpad.
  - So do W1's `index_scope.py`, `parent_proof_timing.py`, `compare.py`, `mutate.py` and `run_module.sh`, and W1
    recorded no digest for them. `MUTATIONS.json` names the ten mutations but not their texts.
  - The storage module's run on the unchanged tree (`<P37>/checks/s5-storage-baseline/`) has no command or
    environment record. Its tracebacks show that it ran the declaration commit's code in `<P37>/measure/prep-001`.
  - A reboot or cleanup can clear the scratchpad (PROTOCOL section 5: durable command evidence).
- **Change.** S8 does three things before the scratchpad is cleared:
  - copies these scripts beside the clone under `<P37>/` (the Director's under `director/`, W1's under
    `workers/W1-correction/scripts/`);
  - lists their SHA-256 in a sums file;
  - records the storage baseline run's command, working directory, environment names and times.

### RV-03. W2 started Git outside a test fixture, and did not record it as a deviation

- **Evidence.** W2's brief allowed Git starts only in fixtures. W2's exploration scripts `explore_git.py` and
  `explore_path_wrapper.py` started Git in fresh temporary directories, and no Git start touched `<worktree>`.
  The commands were `version`, `init`, `add`, `commit`, `fetch`, `update-ref`, `read-tree`, `update-index`,
  `status`, `ls-files`, `rm --cached`, `reset`, `ls-tree` and `rev-parse`. W2's `STARTS.md` lists these starts
  but not among its deviations D-1 to D-3. They had no effect on any bound input.
- **Change.** S8's process record lists them as W2's deviation D-4.

### RV-04. P37-C34 is an MC19 case, not MC21 coverage

- **Evidence.** P37-C34 is a qualifying run with a valid selection whose original checkout lacks
  `.claude/.gitignore`. Its docstring calls the outcome "MC21's outcome", and WORKERS.md summarises it as "(C34:
  MC21)". MC21 covers missing, partial, malformed or mismatched selections. This case is dirty original source,
  MC19, refused at a qualifying run's preparation, which is the form of outcome that MC21 has. The JSON's
  `sources` list both MC21 and MC19. The control itself is right.
- **Change.** In S8's records and in the next freeze's map of controls to obligations, count C34 under MC19
  (original route, qualifying-run preparation), not as MC21 coverage. No change to the frozen control.

### RV-05. Files that S8 must not copy as they are

- **Evidence.** These raw files beside the clone hold account values or machine paths:

  | File | What it holds |
  | --- | --- |
  | `<P37>/checks/s5-001/tests.test_current_host_readback_driver.txt` and `<P37>/routine/ordinary-001/logs/unit-tests.log` | the account's home, logname and user values, in the 0.1.0 driver tests' mocked call list |
  | `routine/ordinary-001.command.json` and `director/run/ordinary-001.environment.json` | account values and machine paths |
  | the other `routine/*.command.json` and `*.stdout.txt` files, `director/run/discovery-c.environment.json` and both Python inventories | machine paths |
  | every `*.collect.json`, both comparisons, `discovery-c.json` and its two comparisons | machine paths in the input, tool and invocation records |
  | `ordinary-001/summary.json` | the source root, the interpreter, and each step's working directory and argv |
  | `MEASURE-001.json` | the workspace path, in `copy.workspace` |
  | W1's 30 mutation logs | machine paths in their tracebacks |

  These are clean as they stand:
  - the eight files of C;
  - `S5-RUN.json`, `S5-COMPARE.json` and `INVENTORY-ADDITIONS.json`;
  - `WORKERS.md`;
  - W2's evidence, and W1's files other than the mutation logs;
  - every file of this review.
- **Change.** S8 applies FZ-09's carried rule to the files in the table: raw logs only by digest, every argv and
  environment value replaced by its label, and each portable file searched before publication.

### RV-06. To carry into the next MR attempt

- **(a) The start inventory.**
  - Every run gains one start, `update-index -q --refresh`. In R1 it goes through the bound Git.
  - The 67 new tests start real Git, through the `PATH` dispatcher in W1's and W2's fixtures and wrappers. They
    also start `/bin/sh` wrappers and stand-ins, and `cat`.
  - W1's two `run()` tests start `uname` and `file` through `platform.platform()` when they are the first such
    call in the process.
  - With LFS files, the clean filter process moves from the first status read to the refresh.
- **(b) MC28.** The freeze approves the 474 additions (`INVENTORY-ADDITIONS.json`, `7eccdc02…`).
- **(c) FZ-06 now covers P37's 67 tests too.** S5 and my runs ran each module alone without selection variables.
  R1 runs them with the derived pair set. None of them reads a selection variable.
- **(d) FZ-02.** The margin after the refresh rests on one measurement on this host. It was taken after a
  manual refresh at the declaration commit, not inside a run. The new HOST's freeze states it again.
- **(e) The derived checks after the source check.** HOST, the cross bindings, the dependencies and the methods
  have never run on a real derived selection. P37-C05 to P37-C07 substitute them, so R1 is their first exercise.
  By reading, they handle the parent explicitly: the original root for HOST's source binding, and the parent's
  map root for the methods.

## The six items

### 1. The decision: MET (RV-01)

- **The rule is exact and complete.**
  - Rule A, the generated examples, is unchanged.
  - Rule B admits a line only when all six of its conditions hold. The code applies exactly these: ` D `,
    unquoted, no ` -> `, no empty, `.` or `..` component, outside `copied_source_path`, a record held, and no
    case-folded match in the record.
  - Every other line refuses with `CH-SOURCE`, `Dirty source: <line>`.
  - Untracked names refuse as before.
  - A malformed record refuses with `CH-WORKSPACE` before any Git read.
  - The original route refuses every line, whatever record is passed.
- **The basis holds.**
  - The deletions follow from P05 section 3's own derivation: a copy of the copied set, and a repository that
    keeps the whole commit.
  - Each admitted path is outside the copied immutable-source inventory and absent from the workspace. The
    original route's check, which refuses every line, found the original checkout clean before the copy.
  - The 0.2.0 source set is bound file by file before any Git read, so no missing execution source can pass.
  - Contract section 7's untracked-file refusal is unchanged.
  - The conclusion that no amendment is needed is right.
- **Every MC19 case still refuses:**
  - another checkout (C22);
  - dirty source (C10 to C17, C51 to C55);
  - untracked source (C19, C20, C59);
  - a changed provider or probe (C21);
  - an unbound Git (C22).

  MI's MC19 rows use `derived=False` and are unchanged (S5: 151 passed).
- **F-01's correction** states F-01's case exactly. RV-01 covers its one imprecise reason.
- **Nothing the contract refuses is admitted.**
  - A case variant of a copied file refuses (condition 6).
  - Non-ASCII names are quoted by default, and refuse. `core.quotePath` keeps its default: the driver's Git
    environment drops every `GIT_*` override and sets `GIT_CONFIG_NOSYSTEM` and `GIT_CONFIG_GLOBAL=/dev/null`, and
    the workspace's repository is created fresh with `init --template=`.
  - MC29's moments and refusals are unchanged.

### 2. The implementation: MET

- **One definition of the copied set.**
  - `copied_source_path` is the former `git_metadata` expression with `name.split("/")` named once, the same
    predicate.
  - The provider imports it from the driver; in the unit process that is the workspace's copy, which the
    source set binds.
  - The copy and the inventory walk the same constants with `ignored()`. A path the walk does not reach, such
    as a tracked file named `tests`, is inside the predicate's set, so its deletion refuses: it fails closed.
- **No other change of behaviour.** The diff holds only these changes:
  - in the driver, the predicate and the refresh;
  - in the provider, `_copied_names`, the new keyword `copied`, rule B, `_verify_parent`'s return value (`None`
    as before for an original), `_selection` passing it on, a docstring paragraph and the comment;
  - in the tests, additions only. No existing class, method or assignment changed in either test module
    ([s5-inventory](outputs/s5-inventory.json)).

  `_verify_source` has one call site, `_selection`.
- **The case-folding guard** uses `str.casefold` against the recorded regular files. For the names that rule B
  can admit (unquoted ASCII), that matches the volume's case-insensitivity.
- **The refresh.**
  - **Placement.** It runs once, after the storage step and before the first status read (C60).
  - **What it changes.** Stat data only for copied entries whose bytes match (C61). A change stays visible,
    same-size changes with an old modification time included (C12, C62, C65).
  - **The summary.** It keeps every field and value (C63). The S6 summary has the declaration commit's 28
    keys. Its `workspace_git` equals main's baseline record apart from head and tree, with the same seven ` D`
    lines, and its `workspace_storage` equals main's.
  - **A failure** raises `ValueError` and fails the run before any step (C64, and W1's test).
  - **Its start** is one more Git start per run with Git.
- **LFS, by reading.**
  - `prepare_offline_workspace` configures `filter.lfs.*`, with `required=true`, only when LFS paths exist,
    and before the refresh.
  - The refresh then runs the same clean filter that the first status read ran before. A failing filter makes
    `update-index` exit non-zero, and the preparation fails visibly. Before, the first status failure turned
    into `workspace_git.available: false` in an ordinary run, so this is the fail-closed instance of the
    decision's "a failed refresh".
  - The storage test that drives `run()` on an LFS fixture still expects an empty status and an untouched
    source index, and the refresh preserves both.
  - At C there is no LFS file, and R1's `PATH` holds no `git-lfs`.
- **R1's route at C, walked again.** Nothing else in this phase's scope refuses it:
  - **The original checkout.** It is clean at C: its index equals C's tree, all stat data matches, and there is
    no untracked file or bytecode, so the original-route checks pass.
  - **The S6 preparation.** The copy, the workspace Git and storage (no LFS) succeed. The refresh ran at
    01:10:51Z, before the unit stage started at 01:10:53Z.
  - **The inventories.** `workspace_git` shows C's head and tree, and the workspace inventory equals
    `source_before` (23,149 files). C tracks 23,156 entries, and exactly seven lie outside the copied set.
  - **The derived source check.** Rule B admits all seven lines at C. No tracked name needs quoting, has an
    ignored component, or collides up to case. All 645 files of the 0.2.0 source set lie inside the copied set
    ([s2-tree-scope](outputs/s2-tree-scope.json)).
  - **The unit stage.** At the end of the whole routine the workspace showed exactly those seven deletions
    ([s3-workspace-end-state](outputs/s3-workspace-end-state.json)):
    - its index was last written by the refresh;
    - every copied entry still matches its stat data (modification time, size and inode);
    - every file is in the index, and there is no bytecode or `.DS_Store`.

    The readback class runs inside the unit stage, so its twelve checks would see the same lines, unless a test
    made and undid a change between them. Nothing in the evidence suggests one.
  - **What remains** is RV-06 (e).

### 3. The controls: MET (RV-04)

- **Independence and freeze.** W2 is a fresh-context author who wrote none of the implementation, the
  decision or the contracts. It froze the 46 controls at 01:02:35Z, and the Director's S5 started at 01:05:51Z
  on the same module bytes (`c0eebef7…`). W2 ran its own module before freezing, which its brief allowed and
  its record states.
- **Sources.** The expectations come from P05 section 3, the contract's MC19, MC21 and section 8, and the
  decision's rule. The refusal reasons that the contract leaves to the code come from the unchanged code at the
  declaration commit. Each control cites its sources.
- **Coverage.** A4 is covered: acceptance with real Git and the driver's own preparation, including a link;
  each refusal inside the copied set; the original route; the generated examples; and FZ-02's mechanism.
- **Labels.** 31 real, 11 simulated and 4 mocked, each with its boundary named.
- **Strength.** No control is weak or wrong. C18, C24, C56 and C63 are strong.
- **Cross-checks.** The module's 46 methods equal the frozen IDs, and my run passed all 46.

### 4. The evidence: MET

- **S5.** I recomputed it with MR's collector functions ([s4-recheck-s5-s6](outputs/s4-recheck-s5-s6.json)).
  Every log digest matches its record.
  - Against MI's final-003, the existing members are unchanged: `test_local_checks` +6 and provider_v02 +15,
    all passed; the 0.2.0 driver, MI's controls and prepare_v02 equal MI's; the 0.1.0 driver (2) and provider (3)
    give the same not-passing records; the readback module has the same setUpClass error.
  - The storage module differs from MI's in 6 outcomes and 2 reasons. It equals its own run on the unchanged
    tree exactly (8 unchanged not passing). The difference is `PATH` (no `git-lfs`), not the correction.
- **S6.**
  - **The run.** Exit 1. Unit tests failed; source, agent, construction, surface, impulse and documents passed;
    `source_unchanged` true; ordinary run kind.
  - **Against main's resolved-directory run** (recomputed: the Director's counts, lists and steps agree):
    4,985 passed and main's one failure are unchanged; 3 were removed, the trio that main skips, which section 8
    turns into MC22's setUpClass error; 1,073 were added.
  - **The 93 new not-passing records:** inspection 47, rtld-paths 39, the 0.1.0 provider 3, the 0.1.0 driver 2,
    required-images 1 (RI_L08), and the MC22 fixture.
  - **No difference** of outcome, reason, subtests or occurrences for any common test. Steps, reports, pending
    cases and the unexecuted steps are all equal.
  - **Each difference is explained.** All 67 P37 tests ran and passed. Freeze 001's attributions match all 92
    of their rows. RI_L08 was predicted (Q-3), and MC22's error is the contract's expected ordinary-run
    outcome. None is new because of P37, and R03 still classifies them (FZ-04).
  - **The started tests** equal the discovery minus exactly the trio, in discovery order
    ([s7-log-discovery-join](outputs/s7-log-discovery-join.json)).
  - **Node.** No Node start: `PATH=/usr/bin:/bin` reaches no `node`, no core step starts Node, the readback
    class fails at setup, and MR's reviewed start inventory agrees.
  - **The Python inventory** is byte-equal before and after (`c277bdd3…`). The framework holds 414 `.pyc`.
- **The discovery and MC28.** COMPLETE, 6,061 unique IDs, with no failed import or bytecode. That is exactly
  MH's 5,587 plus MI's 407 plus P37's 67. The 67 are W2's 46 frozen IDs and W1's 21: the interface note's IDs
  equal the methods added by syntax tree. The additions record is MI's 407 in their order, then the 67 in
  discovery order. Its counts recompute.
- **FZ-02.** The measurement script uses the driver's own copy, the bound Git and the provider's exact reads.
  The judgment is sound: each read took about 2.5 s of its 5 s allowance, 13 such reads happen per run, none may
  be retried, and the times were taken right after the copy, with its bytes in the page cache. So is the
  correction (RV-06 d).

### 5. The process and the records: MET (RV-02, RV-03, RV-05)

- **Deviations.**
  - W1: D-1 (the system launcher), D-2 (four Git reads in `<worktree>`; the index time shows no write).
  - W2: D-1 to D-3, all harmless and recorded, and RV-03.
- **The briefs.** Each worker wrote only its exclusive files: the diff holds W1's six and W2's two. W1 changed
  no existing test, and W2 changed no file of W1's. All 66 lines of W1's sums file verify, and so do W2's 14
  local lines; W2's two lines for worktree files carry a label, and their digests equal C's.
- **Two orderings** (O-02):
  - S5 ran before commit C, on the same bytes, as the plan's stage order has it.
  - W1's text correction of F-01 (01:07:38Z) fell within S5's last minute. No test reads that file, and C binds
    the corrected text.
- **Privacy:** RV-05. The files of C hold no machine path or personal name.

### 6. Amendments and blockers: none

Nothing needs an amendment, and nothing blocks the next MR attempt. RV-06 lists what it carries.

### Observations

- **O-01, outside scope, by reading.** In a `--full` run the driver links `tools/node_modules` after the
  refresh. `tools/.gitignore` ignores `node_modules/`, a pattern for directories only, which does not match a
  link. A `--full` qualifying run would therefore list the link as an untracked name, and the derived check
  would refuse it. This predates P37, and MR's routine is the core profile.
- **O-02.** The two orderings in item 5.

## My test runs

Each ran once, from `<worktree>` at C, with `/usr/bin/env -i HOME=<home> LOGNAME=<logname> USER=<user>
PATH=/usr/bin:/bin TMPDIR=<tmp>/ .venv/bin/python -B -m unittest <module> -v`
([s6-reviewer-runs](outputs/s6-reviewer-runs.json)):

| Module | Times | Result |
| --- | --- | --- |
| `tests.test_current_host_readback_derived_controls_v02` | 01:57:16Z to 01:58:13Z | 46 tests, OK |
| `tests.test_local_checks` | 01:58:19Z to 01:58:27Z | 39 tests, OK |
| `tests.test_current_host_readback_provider_v02` | 01:58:33Z to 01:58:49Z | 64 tests, OK |

Each equals S5's run of the same module, ID for ID. The logs hold no machine path.

## What I started

- **The three test runs above.** Their fixtures started real Git through the `PATH` dispatcher, `/bin/sh`
  wrappers and `cat`.
- **`python3 -I -S -B`, the framework interpreter**, for my seven scripts and their library `gitstore.py` (s1
  twice: before and after my test runs) and for short readers of JSON records, the routine summary and the
  control module's syntax tree.
  - The scripts read Git's object, pack and index files directly.
  - Two of them, s4 and s6, loaded MR's collector from its reviewed path (`0b526940…`) and called only its
    reading functions.
  - I edited `gitstore.py`, s1 and s2 before their first start. s4 failed at its first start, before it wrote
    anything; it ran again after a one-line fix.
- **Shell utilities:** `ls`, `cat`, `sed`, `grep`, `find`, `stat`, `shasum`, `cmp`, `diff`, `wc`, `date`,
  `head`, `tail`, `cut`, `sort`, `uniq`, `tr`, `mkdir`, `mktemp`, `rmdir`. `sed -i` touched my own scripts only.
  One `mktemp -d` and `rmdir` in `<tmp>` checked that it was writable. One `/usr/bin/env -i PATH=/usr/bin:/bin sh
  -c 'command -v …'` checked what that `PATH` reaches. I read, and did not run, the Director's and W1's scripts in
  the session's scratchpad.
- **Never started:** a Git command, the routine driver, the complete suite or any other module, Node, `ldd`,
  `codesign`, `otool`, a download or install, or a child agent. I wrote only in `<W3>`.

[SHA256SUMS.txt](SHA256SUMS.txt) covers every file I wrote.
