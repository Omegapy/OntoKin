# C271-P37 records: the portable copies

These are the path-portable copies of C271-P37's records, made at stage S8. The exact files stay beside
the clone under `../OntoKin-local/c271-p37/`, unchanged. [EXACT-RECORDS.json](EXACT-RECORDS.json) lists
each exact file with its SHA-256 and size, and with either its portable copy or the reason it is not
copied.

The phase's own records at candidate C are in this directory as committed:
- [PHASE.json](PHASE.json) and [CORRECTION-PLAN.md](CORRECTION-PLAN.md);
- [DECISION-001.md](DECISION-001.md) and its [interface note](interfaces/W1-CORRECTION.md);
- [CONTROLS-FROZEN.json](CONTROLS-FROZEN.json);
- [INVENTORY-ADDITIONS.json](INVENTORY-ADDITIONS.json), the cumulative additions for the next MR
  attempt's MC28.

[OUTCOME.json](OUTCOME.json) gives the result.

## Labels

A portable copy differs from its exact file only in labels that replace machine paths, as in P36's
[records](../macos-routine-p36/README-PORTABLE.md#labels): `<worktree>`, `<worktrees>`, `<local>`,
`<clone>`, `<parent>`, `<volume>`, `<volume-name>`, `<home>`, `<user>`, `<prefix>`, `<tmp>`, `<tmpdir>`,
`<tmpdir-link>`, `<tmpdir-truncated>` and `<tmpdir-link-truncated>`.

One more label is used here, MH's: `<package-manager>` stands for the package manager's name in one
phrase of W1's notes. JSON pointers that held a machine path hold the label in its place. The JSON
copies still parse. The copied scripts are records, not runnable tools, because their paths are labelled.

## What is here

| Directory | Content | Source beside the clone |
| --- | --- | --- |
| `measure/` | stage S2: FZ-02's measurement | `<local>/c271-p37/measure/` |
| `checks/s5-001/` | stage S5: the run and comparison records of the eleven modules, and each module's collected outcomes beside MI's final-003 collection | `<local>/c271-p37/checks/s5-001/` |
| `checks/s5-storage-baseline/` | the storage module on the unchanged tree, with its command record (RV-02) | `<local>/c271-p37/checks/s5-storage-baseline/` |
| `routine/` | stage S6: the wrapper's command records and streams, the driver's summary and storage record, MR's comparisons with main's resolved-directory run, and the discovery's two comparisons | `<local>/c271-p37/routine/` |
| `workers/W1-correction/` | the author's evidence: test runs, mutation records, its scripts (copied from the session's scratchpad by the Director, RV-02) | `<local>/c271-p37/workers/W1-correction/` |
| `workers/W2-controls/` | the control author's evidence | `<local>/c271-p37/workers/W2-controls/` |
| `reviews/` | review 001 (`review-001/`) and the Director's disposition | `<local>/c271-p37/workers/W3-review-001/` and `<local>/c271-p37/director/reviews/` |
| `director/` | the worker log, the briefs of S3, S4 and S7, the wrapper and environment records, and the Director's scripts (RV-02) | `<local>/c271-p37/workers/WORKERS.md` and `<local>/c271-p37/director/` |
| `checks/closing/` | the records checks of this commit | written here |

## What is not copied

- **Content already here.** A file whose exact bytes equal a file copied earlier is listed once, under
  `same_bytes`.
- **Raw logs** of the S5 modules, of the routine's stages and of W1's mutation runs, listed by digest.
  They may hold the account's values or machine paths (FZ-09, RV-05). The workers' own focused-test logs
  are copied, because review 001 found them clean and the copy builder found no private term left in
  them.
- **Large outputs that can be recomputed from retained bytes,** listed by digest:
  - MR's collection of the routine's unit log;
  - the discovery of C;
  - the stage reports;
  - the two source inventories of the run.
- **The two Python inventories** of S6, which are byte-equal to HOST's (`c277bdd3…`), whose labelled
  copy is in [P36's records](../macos-routine-p36/plans/observation-plan-001/python-inventory-001.json).
- **The two workspace copies:** FZ-02's copy of the declaration commit's tree, and the routine's isolated
  workspace. Each is summarized by its file count, its bytes and the SHA-256 of its sorted digest
  listing.
- **The copy builder itself.** Its label table hard-codes the values that it replaces, so it stays beside
  the clone, recorded by digest. This is P35's `memory-c271-privacy-scan-scripts-stay-local`.
- **The reviewer's copy of the candidate's diff,** which Git reproduces.
