# Gate MR records: the portable copies

These are the path-portable copies of gate MR's records (C271-P36), made when MR stopped at stage S6.
The exact files stay beside the clone, unchanged. [EXACT-RECORDS.json](EXACT-RECORDS.json) lists
each exact file with its SHA-256 and size, and with one of these:
- its portable copy;
- its copy committed at commit B;
- the reason it is not copied.

MR stopped before any routine run. Freeze review 001 found that R1 would refuse in the driver's
preparation at B ([FZ-01](reviews/freeze-review-001/FREEZE-REVIEW-001.md)), and the Director
confirmed it ([disposition](reviews/FREEZE-REVIEW-DISPOSITION-001.json)). So there is no `routine/`
directory and no audit. [OUTCOME.json](OUTCOME.json) gives the result.

## Labels

A portable copy differs from its exact file only in these labels, which replace machine paths:

| Label | Stands for |
| --- | --- |
| `<worktree>` | the C271 worktree, `../OntoKin-worktrees/c271` from the clone |
| `<worktrees>` | the directory that holds the worktrees, `../OntoKin-worktrees` |
| `<local>` | the local data root beside the clone, `../OntoKin-local` |
| `<clone>` | the owner's main checkout |
| `<parent>` | the directory that holds the clone and its neighbours |
| `<volume>`, `<volume-name>` | the external volume that holds them, and its name |
| `<home>` | the owner's home directory |
| `<user>` | the owner's account name |
| `<prefix>` | the package manager's installation prefix, as in P33's to P35's records |
| `<tmp>` | the session's temporary directory |
| `<tmpdir>`, `<tmpdir-link>` | the per-user temporary directory, in its resolved form and in macOS's default form through the `/var` link |
| `<tmpdir-truncated>`, `<tmpdir-link-truncated>` | the same directory where unittest shortened the value before a `[N chars]` marker |

JSON pointers that held a machine path hold the label in its place. The JSON copies still parse.
The copied scripts are records, not runnable tools, because their paths are labelled. Some workers'
own reports already used labels of their own, such as `<F>`, `<E>` or `<framework>`, which they
define at their top.

## What is here

| Directory | Content | Source beside the clone |
| --- | --- | --- |
| `plans/observation-plan-001/` | stage S4: the observation plan, M0-LAUNCH, M0's environment, the source, Python and dependencies inventories, the author's notes and scripts | `<local>/c271-p36/workers/W2-plan-001/` |
| `plans/freeze-001/` | stage S6: operational freeze 001, rejected and never run, with the configuration, the methods and discovery documents, the environments, the attributions, the discovery comparison and the author's scripts | `<local>/c271-p36/workers/W2-freeze-001/` |
| `host/` | stage S5: M0 and M1's attempt `observe-001/`, with HOST, and its static and observe command records | `<local>/c271-p36/evidence/observe-001*` |
| `reviews/` | the plan, HOST and freeze reviews (Markdown, JSON and scripts), and the Director's dispositions. The tooling reviews and their dispositions were committed at commit B. | `<local>/c271-p36/workers/W3-*/` and `<local>/c271-p36/director/reviews/` |
| `director/` | the Director's worker log, the wrapper, the briefs of S4 and S6, main's change list for the freeze author, and the status files of commit B's in-place tooling run | `<local>/c271-p36/workers/WORKERS.md` and `<local>/c271-p36/director/` |

The inventory and the tooling, with their authoring records and reviews, were committed at commit B
in `inventory/`, `tooling/`, `authoring/`, `reviews/` and `checks/commit-b/`.

## What is not copied

- **Content that is already here.** A file whose exact bytes equal a file copied earlier is listed
  once, under `same_bytes`, with the copy it equals. Examples are the two inventories that the
  freeze author wrote again, which are byte-equal to the observation plan's.
- **Raw outputs of workers.** They hold machine paths, the account's values or the owner's processes,
  and are listed file by file with their digests (plan review 001's PR-06, freeze review 001's
  FZ-09). The exception is the twelve outputs that the freeze review's report links to: they are
  copied with labels, so that its evidence for FZ-01 can be read here, and EXACT-RECORDS.json lists
  them under `copied_because_linked`. The ones left out include:
  - the freeze author's self-tests;
  - the checker's dry runs;
  - the collections of MI's and main's retained logs;
  - the configuration's validation;
  - the reviewers' outputs.
- **MH's collector's raw discovery of B,** listed with its digest. Its comparison with the baseline
  and the additions is copied.
- **Synthetic test worlds of the freeze author,** summarized by directory: the number of files and the
  SHA-256 of their sorted digest listing.
- **Earlier drafts of two briefs and a timing marker,** listed with their digests.
