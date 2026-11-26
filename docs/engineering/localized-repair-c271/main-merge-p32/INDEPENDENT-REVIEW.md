# Independent review: C271-P32 merge commit `5f30f26b` (gate MB)

- Candidate: merge commit `5f30f26b313946d1fdd763670b340341d2eed489`, tree
  `f0a017e2a01aaecd22340a3e7b20e5d686ea57f6`. It is local and not pushed.
- Reviewer: an independent reviewer with fresh context (Claude Opus 5.5 subagent). It did not
  write the candidate.
- Review time: 2026-11-26, about 05:58Z to 06:13Z.

**Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding. Every path
carries the expected bytes. The six overlaps match the recorded resolution and keep both
purposes. `CURRENT.json` is valid schema 2, and the schema-1 file is retained byte for byte.
All required checks pass on the exact commit, and nothing was written to main. The six
nonmandatory findings (M-01 to M-06) are:
- two corrections to record wording or evidence binding;
- one completeness note on CURRENT's history entry;
- three follow-ups for P32's outcome records and for R04.

## 1. Ancestry

| Item | Observed | Expected |
| --- | --- | --- |
| Object type of `5f30f26b` | commit | commit |
| Tree | `f0a017e2a01aaecd22340a3e7b20e5d686ea57f6` | same |
| First parent | `6fb6525f670ac619857d4830cda0a3e2bf298d93` (branch, C271-P32 declaration) | same |
| Second parent | `51223c9b94a222f29d38eb6c33808f8e55e2bff9` (main) | same |
| Merge base (`git merge-base`; `--all` gives one base) | `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d` | same |
| Commit time | 2026-11-26T05:57:17Z | — |
| `refs/heads/main`, `refs/remotes/origin/main` | `51223c9b`, unchanged before and after this review | not written |
| `refs/remotes/origin/work/c271-missing-import-digest-control` | `6fb6525f` | merge not pushed |
| Is `5f30f26b` an ancestor of main? | no (`git merge-base --is-ancestor` exit status 1); only the local C271 branch contains it | — |

## 2. Per-path comparison

Method: `git ls-tree -r -z --full-tree` of the base, both parents and the merge, compared by
(mode, type, object id) for the union of all paths. The script is `compare_paths.py`, and its
result is `path-comparison.json`.

| Class | Paths | Result |
| --- | --- | --- |
| Union of the four trees (equal to the merge tree's entry count) | 22,348 | — |
| Changed on neither side | 18,577 | all identical to the base |
| Changed only on main | 104 (82 added, 22 modified) | all carry main's mode and blob, including the six `.claude/skills/*` symbolic links (mode 120000), each of which resolves to an `.agents/skills/` directory holding its `SKILL.md` |
| Changed only on the branch | 3,659 (3,658 added, 1 modified: `tests/test_static_tray_readback_v01.py`) | all carry the branch's mode and blob |
| Changed on both sides | 6 | see the table below and section 3 |
| Added only by the merge commit | 2: `main-merge-p32/MERGE-RESOLUTION.md` and `main-merge-p32/CURRENT-C271-schema1.json` | the phase's own records, required by PHASE.json A2 and A3 |
| Deleted on either side | 0 | no rename effects possible |

The counts add up: 18,606 base paths, plus 3,658 added on the branch, plus 82 added on main,
plus 2 added by the merge, give 22,348. `git diff --stat` reports 112 files from the first
parent to the merge (104 + 6 + 2) and 3,666 from the second (3,659 + 5 + 2; `STATUS.md` equals
main's).

| File | Base | Branch | Main | Merge | Recorded resolution | Match |
| --- | --- | --- | --- | --- | --- | --- |
| `STATUS.md` | `2cabb4ca` | `3fa05858` | `99ab22fb` | `99ab22fb` | main's side of the one hunk | yes, byte-equal to main and to `git merge-file --theirs` |
| `docs/README.md` | `070c4f3b` | `fb6cf522` | `9729282f` | `f8084990` | clean merge | yes, byte-equal to a clean 3-way merge |
| `docs/workflow/CURRENT.json` | `9b9b7d4b` | `e098a6fc` | `81465753` | `fa702ef8` | schema-2 rewrite | yes (section 4) |
| `docs/workflow/memory.json` | `3b9c2b83` | `d4c00ef9` | `c3a47a59` | `c69f0138` | union, branch then main | yes |
| `tools/check_local.py` | `18c56cb5` | `aab024ae` | `95cd375f` | `859d776d` | branch's readback constants plus main's lists | yes, byte-equal to the reconstruction |
| `tests/test_local_checks.py` | `938e4fde` | `e85abd96` | `45c67d5c` | `1e359887` | both new tests plus main's declared-input test | yes, byte-equal to the union |

A dry 3-way merge of the extracted blobs (`git merge-file -p --diff3`, Git 2.50.1, run in this
directory only) gives these conflict hunk counts:

| File | Conflict hunks |
| --- | --- |
| `STATUS.md` | 1 |
| `docs/README.md` | 0 |
| `docs/workflow/CURRENT.json` | 6 |
| `docs/workflow/memory.json` | 1 |
| `tools/check_local.py` | 1 |
| `tests/test_local_checks.py` | 1 |

This matches MAIN-CONFLICTS and PHASE.json: five files conflict and `docs/README.md` merges
cleanly. No file contains a leftover conflict marker. `git diff --check` from each parent to
the merge, over the six files and the two new records, reports nothing.

## 3. Each conflict, by meaning

### `STATUS.md`: main's side; dropping the P22 line is justified

The merge equals main's blob. Outside the single hunk, the branch changed nothing. So the only
branch content that is not carried forward is the two-line paragraph beginning "C271 P22
prepared the exact retained Node and 24-file readback-dependency inputs".

The drop is justified, for four reasons:

1. **The line was already stale on the branch.** The branch head had moved to P32, but this
   line still gave P22's source-time state. It contained "Finish only those delivery gates,
   then stop" and "Observed main remains 70ca7e68…". Carried forward, it would contradict the
   branch's CURRENT and task record.
2. **Main's C271 paragraph is newer.** It records P29, observed 2026-11-25. MAIN-CONFLICTS
   requires it to stay as a dated observation until R04.
3. **No evidence is lost.** The text is in `6fb6525f:STATUS.md`, which is reachable as the first
   parent. The P22 records that the line links to all remain in the tree:
   `retained-input-p22/OUTCOME.json`, `reviews/OUTCOME-REVIEW.md` and `P22-DELIVERY.json`.
   REQUIREMENTS section P22 records the outcome.
4. **Keeping the line would add a needless conflict at R04.**

The stated reason is slightly inaccurate in wording; see M-02. On the branch, STATUS now shows
main's dated view of C271; see M-05.

### `docs/README.md`: union, clean

Main's local entry block at the top and the branch's "Current C271 loader-path prerequisite"
section at the end are both present, unchanged. The documentation verifier checks their links
(section 5).

### `docs/workflow/CURRENT.json`: schema-2 rewrite

See section 4.

### `docs/workflow/memory.json`: union

The 15 base records are identical and in their original order. Neither side changed any of
them. The branch's `memory-c271-loader-source-admission-boundary` (recorded 2026-11-21) and
main's `memory-local-state-in-checkpoint` (recorded 2026-11-25) are each equal to their side's
object. They appear in that order, which is also chronological. The text equals the automatic
merge with the marker lines removed, and `schema_version` stays 1.

### `tools/check_local.py`: C271's controls intact, main's lists complete

The branch-to-merge diff touches only the `SOURCE_DIRS` and `ROOT_FILES` statements. Every
C271 addition is byte-identical to the branch:
- `import stat`;
- `READBACK_CONFIG_ENV` and `READBACK_DIGEST_ENV`;
- `readback_config_identity`, `prepare_readback_selection` and `bind_readback_workspace`;
- the removal of ambient readback variables;
- the unit-step scrubbing of injection variables and `PYTHONNOUSERSITE`;
- `process_started` and `process_pid`, and the `ValueError` handling;
- the planned-steps and selection ordering in `run`;
- the `not_executed_steps` accounting;
- `--readback-config` and `--readback-config-sha256`.

Main's two list statements appear exactly as they are on main:
- `SOURCE_DIRS` adds `.agents` and `TRDs`;
- `ROOT_FILES` adds `CHATGPT-START-HERE.md`, `ROLE.md`, `LOCAL-START-HERE.md`, `CLAUDE.md`,
  `LICENSING.md` and `NOTICE`.

Main's lists contain the branch's additions. Every top-level entry of the merged tree is copied,
except `.claude`, which main also excludes. No other code reads these lists in a way the merge
could break.

### `tests/test_local_checks.py`: all three tests intact, nothing lost or wrongly duplicated

The merge equals the automatic merge with its one hunk resolved as the branch's side followed by
main's side. Main's change to `test_declared_validation_input_roots_survive_inventory_and_copy`
and the branch's `execute` helper and `nullcontext` import come through outside the hunk.

The file has 33 test methods (30 in the base, plus 1 from the branch, plus 2 from main, counted
from the parsed class), and no name is repeated. The three tests are complete:
- `test_workflow_instruction_targets_survive_workspace_isolation` (branch);
- `test_instruction_files_and_adopted_requirements_reach_the_isolated_workspace` (main);
- `test_declared_instruction_inputs_exist_in_this_repository` (main).

The assertions the two isolation tests share appear once in each method, which is correct for
separate methods. Main's test passes an empty step list, so the branch's readback mocks are not
engaged, and the driver requires no selection without a unit step. The test still runs through
the branch's helper.

## 4. `CURRENT.json`

**Main's schema-2 rules** (`tools/chat_workflow.py` in the merged tree, which is main's bytes)
pass, both in the fresh run and in a reading of `validate_pointers` and `validate_tasks`:
- **Field sets:** closed field sets at every level.
- **Active task and mode:** active task `C271`, with `execution_mode` `local`. C271's
  `task.json`, unchanged from the branch, records `execution_mode` `local` and status
  `in_progress`.
- **Checkpoint:** the record is `docs/workflow/tasks/C271/task.json`, and the session file
  `P32-SESSION.md` is a Markdown file under the active task's folder.
- **Unfinished list:** it is empty. The checker refuses an `unfinished` entry that names the
  active task, so main's C271 entry has to go.
- **Delivery policy:** it has exactly `local` and `browser`, both identical to main's.
- **History:** each entry's digest, size and named keys are checked against the retained file.

**Parts kept from main:**
- the seven boundaries, verbatim and in their original order;
- `delivery_policy`, identical;
- `history[0]`, identical (`CURRENT-before-migration.json`: SHA-256 `fec57459…`, 5,527 bytes,
  equal to the base's CURRENT blob `9b9b7d4b`).

**Parts changed from main:**
- Two boundaries are added.
- `latest_task` and `active_task` are `C271`.
- `observed_main` is `51223c9b`, main's actual head; main's own file recorded `8e847c15`.
- `snapshot_date` is 05:55:41Z, before the commit at 05:57:17Z.

The formatting (two-space JSON with a final newline) matches main's.

**Content accuracy.** `next_action` is `ready`. It says the merge awaits independent review,
push and readback, that nothing is integrated into main, and it gives the remaining gates.
Its sources exist.

Boundary 8 agrees with the branch's records: P31 `ADOPTION.json`, `CONTRACT.md` (its opening,
section 1 and section 11), P31's open gates, and the task requirements (R01 and R02 done, R03
to R05 not done). It says:
- 0.2.0 is design only;
- the Linux 0.1.0 contract and plans /0.1.1 to /0.1.5 stay adopted;
- H0 and H1 stay unmet (P30-EXECUTOR-001);
- R03, R04 and R05 are not done.

Boundary 9 tells the reader that main's STATUS and CURRENT describe C271 as observed on
2026-11-25. The file is neither invalid nor misleading.

**Retained schema-1 file.** `CURRENT-C271-schema1.json` has blob `e098a6fc40ffd5b6883a9a5dbab9a9b97c16533c`, the same
object as `6fb6525f:docs/workflow/CURRENT.json`, so it is byte-identical. It is 215,534 bytes,
with SHA-256 `b0f51618e0aa9c706f33d8de5ad8e49323f1574d7484ed100adf20c414a6c368` and
`schema_version` 1.

**History entry for it:**
- `sha256` and `bytes` are right.
- `source_commit` is `6fb6525f`, the first parent, where that blob is `docs/workflow/CURRENT.json`.
- Each of the 15 `holds` keys exists in the file.
- The list is not complete; see M-03.

## 5. Checks run on the exact commit

The checks ran in a detached worktree created with
`git -C /Volumes/P-SSD/Omegapy/OntoKin-worktrees/c271 worktree add --detach
/Volumes/P-SSD/Omegapy/OntoKin-local/c271-p32/review/wt 5f30f26b`. Its HEAD was `5f30f26b`,
with tree `f0a017e2`. It was clean before and after the checks, including ignored files.

The executor was `/Volumes/P-SSD/Omegapy/OntoKin-worktrees/c271/.venv/bin/python` (CPython
3.12.13, with no packages and no pip). `-B` was added to all three commands so that no bytecode
was written.

| Command (cwd: the worktree) | Exit | Result | Evidence |
| --- | --- | --- | --- |
| `.venv/bin/python -B tools/chat_workflow.py check` (also `--json`) | 0 | "Workflow structure passed (13 tasks)." `passed: true`, `errors: []`, `tasks_checked: 13` | `checks/workflow.out`, `checks/workflow.json` |
| `.venv/bin/python -B docs/maintenance/reorganization-2026-10-17/verify_reorganization.py` | 0 | `status: passed`, `failures: []`, 29 of 29 sources verified, 233 sections, 1,705 documents, 6,779 local links, 165 anchors, 1,102 external links skipped, baseline tree `72aa56f6…` reconstructed | `checks/docs.out` |
| `TMPDIR=/Volumes/P-SSD/Omegapy/OntoKin-local/c271-p32/review/tmp .venv/bin/python -B -m unittest tests.test_local_checks -v` (the temporary directory resolves to itself) | 0 | `Ran 33 tests in 5.466s`, `OK`, no skip and no expected failure; the three tests above and the inventory test passed; the temporary directory was empty afterwards | `checks/focused-tests.out` |
| `git diff --check` from `6fb6525f` and from `51223c9b` to `5f30f26b`, over the six files and the two new records | 0 | no whitespace error | this report |

SHA-256 of the output files:

| File | SHA-256 |
| --- | --- |
| `checks/workflow.out` | `93548ae0…e293` |
| `checks/workflow.json` | `99f168ae…aca2` |
| `checks/docs.out` | `05539741…7c03` |
| `checks/focused-tests.out` | `af7e402f…d290` |

## 6. The account in MERGE-RESOLUTION.md

| Statement | Finding |
| --- | --- |
| 104 paths changed only on main take main's bytes; the instruction files, the workflow tool, the environment specification, doctor and setup tools, and the macOS lock with its provenance are among them | accurate |
| 3,659 paths changed only on this branch keep the branch's bytes | accurate |
| `docs/README.md` merged cleanly | accurate |
| `STATUS.md`: main's side of the one hunk, with the three paragraphs as described | accurate |
| `STATUS.md`: the P22 line's "text stays … in C271's REQUIREMENTS, section P22" | imprecise (M-02) |
| `CURRENT.json`: schema 2, active C271 in local mode, checkpoint, main's boundaries, policy and history kept, two boundaries added, `unfinished` entry removed, retained file of 215,534 bytes with the stated SHA-256 | accurate |
| `memory.json`: union, 15 base records unchanged, order | accurate |
| `check_local.py`: hunk contents, main's lists contain the branch's additions, other C271 changes unchanged | accurate |
| `test_local_checks.py`: both tests kept with their shared assertions, main's declared-input test kept, the helper applies | accurate. The branch's mocks are not engaged by main's empty-step test, and they need not be |
| Checks: workflow check passed (13 tasks), documentation verifier passed, whitespace check passed, 33 tests passed with no skip | results reproduced on the exact commit; the recorded runs were not on the committed tree (M-01) |
| Raw outputs in `../OntoKin-local/c271-p32/checks/merge/` | present |
| Environment readiness: `core` ready, `python-verification` missing (the `.venv` holds none of the seven pins), no Node started | consistent with `doctor.out`, which shows Node not found and npm's version read from its manifest by the doctor's code; not rerun, because that was outside this review's scope |

The account does not mention two things:
- the two paths added by the merge commit itself (the CURRENT row names one of them);
- the note in MAIN-CONFLICTS about regenerating `TRDs/INDEX.md` (M-06).

## 7. Findings

There is no mandatory finding. All six findings are nonmandatory.

### M-01: nonmandatory (low). The recorded pre-commit checks did not run on the committed tree

- **Location:** MERGE-RESOLUTION.md, "Checks of the merged tree, before the commit"; the merge
  commit message ("pass on the merged tree"); raw outputs in
  `/Volumes/P-SSD/Omegapy/OntoKin-local/c271-p32/checks/merge/`.
- **Evidence:**
  - The Director's verifier output counts 1,704 documents and 6,776 local links. The committed
    tree gives 1,705 and 6,779. The verifier counts every Markdown and HTML file it finds on
    disk. The difference is exactly MERGE-RESOLUTION.md: one document with three local links.
  - The Director's `doctor.out` reports "111 tracked modifications, 0 untracked files" at
    `6fb6525f`. 112 paths differ between `6fb6525f` and `5f30f26b`.
  - So the checks ran on the staged resolution before MERGE-RESOLUTION.md existed, not on tree
    `f0a017e2`.
- **Impact:** None on results. Section 5's fresh runs on the exact commit pass, and they cover
  MERGE-RESOLUTION.md in the verifier and in `git diff --check`.
- **Correction:** In P32's outcome record, state which tree the pre-commit checks ran on. Bind
  acceptance A4 to checks of `5f30f26b` and `f0a017e2`: this review's runs, or a recorded rerun.

### M-02: nonmandatory (low). The reason for dropping the P22 line is imprecise

- **Location:** MERGE-RESOLUTION.md, the `STATUS.md` row.
- **Evidence:**
  - `docs/workflow/tasks/C271/REQUIREMENTS.md`, section "P22 retained-input prerequisite scope",
    holds the line's substance:
    - the INSTALLED_EXACT preparer reports and their independent acceptance;
    - the P21 gap resolved;
    - 626 unchanged source files;
    - R01 and R02 done, R03 to R05 not_done, P02 in_progress;
    - the link to the outcome.
  - It does not hold the line's text. It also lacks the line's review link, delivery receipt, and
    observations of the pull request, issue and main. Those remain in the retained P22 records.
- **Correction:** Reword the row, for example: "its text stays in Git history
  (`6fb6525f:STATUS.md`); its substance stays in REQUIREMENTS section P22 and in the retained P22
  records (OUTCOME.json, OUTCOME-REVIEW.md, P22-DELIVERY.json)."

### M-03: nonmandatory (low). The history entry's `holds` lists 15 of the retained file's 40 keys

- **Location:** `docs/workflow/CURRENT.json`, `history[1].holds`.
- **Evidence:**
  - The list omits 25 of the 40 top-level keys of the retained file that are not identity
    scalars. Among them:
    - `next_action`, `checkpoint` and `execution_mode`;
    - `previous_recovery` and `older_recoveries`, although their sibling `latest_recovery` is
      listed;
    - `pending_phase_delivery`, `concurrent_main_observation`, `p28_r02_recovery`,
      `p29_publication_recovery_r02` and `p29_reconstruction`;
    - the `prior_p2x` and `p2x` source-time records;
    - the `p29_r07`, `p30`, `p31` and `p32` prior-current-field records.
  - Main's own entry lists every non-identity key of its retained file.
  - The checker requires only that each named key exists, and it passes.
  - The listed `p29_r07_superseded_fields_index` names most of the omitted keys, and `purpose`
    describes the content. So the list does not misdirect a reader.
- **Correction:** At the next change of CURRENT, either list all 40 keys, or say in `purpose`
  that `holds` names the principal records and that `p29_r07_superseded_fields_index` indexes
  the rest.

### M-04: nonmandatory (follow-up). The task record still names schema-1 CURRENT fields as current state

- **Location:** `docs/workflow/tasks/C271/task.json`, which the merge does not change:
  - `p31_fields_index.current_state_fields["CURRENT.json"]`;
  - `p29_r07_superseded_fields_index.current_state_fields["CURRENT.json"]`.
- **Evidence:**
  - These indexes name the following as CURRENT.json fields that hold current state:
    `execution_mode_record`, `historical_handoff`, `p31_macos_contract_design` and
    `p29_local_publication_r07`.
  - The schema-2 CURRENT.json has none of them. They are now history in
    `CURRENT-C271-schema1.json`. The task record keeps its own `execution_mode_record` and
    `p31_macos_contract_design`.
- **Correction:** When P32's outcome updates the task record (A6), add a P32 fields index. It
  should say that CURRENT.json is schema 2 from `5f30f26b` on, and that its former current-state
  fields are retained in `CURRENT-C271-schema1.json`.

### M-05: nonmandatory (observation). On the branch, STATUS.md gives main's dated view of C271

- **Location:** `STATUS.md`, which is main's bytes.
- **Evidence:**
  - STATUS.md says "No scope is selected; CURRENT awaits owner direction". It describes C271 at
    `bef67902` as "blocked at P29-PUBLICATION-SIZE-001".
  - The branch's CURRENT has C271 active at P32. The branch's records mark
    P29-PUBLICATION-SIZE-001 resolved as a transfer gate (schema-1 boundary 37, R07).
  - CURRENT's boundary 9 discloses that main's STATUS describes C271 as observed on 2026-11-25.
    MAIN-CONFLICTS keeps main's dated entries unchanged until R04. LOCAL-START-HERE's read set
    reaches CURRENT two documents after STATUS.
- **Correction:** None in this merge. R04 must replace main's dated C271 paragraph with C271's
  state at that time.

### M-06: nonmandatory (follow-up). `TRDs/INDEX.md` does not list the branch's TRD

- **Location:** `TRDs/INDEX.md`, a path changed only on main, which correctly keeps main's
  generated bytes.
- **Evidence:**
  - The index lists only `TRD-20261124-E65C6113`.
  - The branch's `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md` now sits
    beside it.
  - MAIN-CONFLICTS ("Further notes") asked for regeneration with the TRD tool when the TRD
    reaches main. MERGE-RESOLUTION does not carry that note forward.
- **Correction:** Carry the note into P32's outcome record. Regenerate the index with the TRD
  tool in a later commit. Do not regenerate it in the merge, which must keep main's bytes for
  paths changed only on main.

## 8. Conduct and policy

- **Git use:** comparisons used Git object reads only: `cat-file`, `ls-tree`, `show`, `diff`,
  `merge-base`, `log`, `rev-parse` and `for-each-ref`. Dry merges ran with `git merge-file -p` on
  extracted copies in `blobs/`, which writes no repository object.
- **`git status` reads:** one read-only `git status` ran in each existing checkout at the start,
  before `GIT_OPTIONAL_LOCKS=0` was set. The index modification times stayed at their earlier
  values: the main checkout's at 2026-11-25T14:35:13-07:00, and the C271 worktree's at
  22:57:17-07:00, the commit time. So no index was written. Later status reads used
  `GIT_OPTIONAL_LOCKS=0`.
- **Worktree:** the only write outside this directory was the authorized detached worktree's
  metadata. It was removed with `git -C /Volumes/P-SSD/Omegapy/OntoKin-worktrees/c271 worktree
  remove --force /Volumes/P-SSD/Omegapy/OntoKin-local/c271-p32/review/wt`. Afterwards:
  - `git worktree list` shows only the main checkout and `c271`;
  - `.git/worktrees/` holds only `c271`;
  - all 8 refs are identical before and after (`refs-before.txt`, `refs-after.txt`);
  - the main checkout's status is unchanged;
  - the C271 worktree is clean at `5f30f26b`;
  - there is no stash.
  The checkout invoked no LFS filter (no `filter.*` configuration) and no hook.
- **Not done:** no commit, push, fetch, reset, branch checkout, stash, index change or network
  access. No Node, npm, `ldd`, routine driver, readback test, or test beyond
  `tests.test_local_checks` ran.
- **Scope:** everything was written in this directory, and no other agent was launched.

## 9. Files in this directory

| File | Content |
| --- | --- |
| `REVIEW.md`, `REVIEW.json` | this review |
| `compare_paths.py`, `path-comparison.json` | per-path classification |
| `blobs/` | the six files at the base, branch, main and merge; dry-merge outputs (`*.auto`, `STATUS.md.theirs`) |
| `checks/` | outputs of the fresh checks, their exit codes and the start time |
| `refs-before.txt`, `refs-after.txt`, `main-checkout-status-before.txt` | state before and after the review |
| `tmp/` | the test temporary directory, empty |
