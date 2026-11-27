# Gate MH records: the portable copies

These are the path-portable copies of gate MH's records (C271-P35, stage S9). The exact files stay
beside the clone, unchanged, and [EXACT-RECORDS.json](EXACT-RECORDS.json) lists each exact file with
its SHA-256 and size, and with either its portable copy or the reason it is not copied.

## Labels

A portable copy differs from its exact file only in these labels, which replace machine paths:

| Label | Stands for |
| --- | --- |
| `<worktree>` | the C271 worktree, `../OntoKin-worktrees/c271` from the clone |
| `<worktrees>` | the directory that holds the worktrees, `../OntoKin-worktrees` |
| `<local>` | the local data root beside the clone, `../OntoKin-local` |
| `<clone>` | the owner's main checkout, whose Git directory `git archive` read in MC28 |
| `<parent>` | the directory that holds the clone and its neighbours |
| `<volume>`, `<volume-name>` | the external volume that holds them, and its name |
| `<home>` | the owner's home directory |
| `<user>` | the owner's account name |
| `<prefix>` | the package manager's installation prefix, as in P33's and P34's records |
| `<tmp>` | the session's temporary directory |

Some workers' own reports use `<prefix>` for the interpreter's installation prefix and
`<package-manager>` for a directory under it. JSON pointers that held a machine path hold the label
in its place. The JSON copies still parse. The copied scripts are records, not runnable tools: their
paths are labelled.

## What is here

| Directory | Content | Source beside the clone |
| --- | --- | --- |
| `plans/observation-plan-001/` | stage S4: the observation plan, M0-LAUNCH, the source, Python and dependencies inventories, the author's notes and scripts | `<local>/c271-p35/workers/W2-plan-001/` |
| `plans/freeze-001/` | stage S6: operational freeze 001, rejected and never run, with every document it binds (configurations, environments, probe rows and fixtures, MC10 plans, MC11 candidate list, the S7 checker and preparation script) | `<local>/c271-p35/workers/W2-freeze-001/` |
| `plans/freeze-002/` | stage S6: operational freeze 002, accepted and run; it rebinds freeze 001's unchanged documents at their paths | `<local>/c271-p35/workers/W2-freeze-002/` |
| `host/` | stage S5: M0 and M1's attempt `observe-001/`, with HOST, and its command, readback and probe records | `<local>/c271-p35/evidence/observe-001*` |
| `cohort/` | stage S7: every command's records and outputs, `s7-001-*` | `<local>/c271-p35/evidence/s7-001-*` |
| `reviews/` | the plan, HOST and two freeze reviews (Markdown, JSON and scripts), the MC11 reviewed list, and the Director's dispositions; the tooling reviews were committed at commit C | `<local>/c271-p35/workers/W3-*/` and `<local>/c271-p35/director/reviews/` |
| `audit/` | stage S8: the independent audit, with its scripts and its digest list | `<local>/c271-p35/workers/W4-audit-001/` |
| `director/` | the Director's worker log, the wrappers, the FR2-05 pre-P00 read and the 72 launch lines of S7 | `<local>/c271-p35/workers/WORKERS.md` and `<local>/c271-p35/director/` |

## What is not copied

- **Content that is already here.** A file whose exact bytes equal a file copied earlier is listed
  once, under `same_bytes`, with the copy it equals. Examples are the fixture copies in the probe
  stages and the two inventories that Q01 and Q02 wrote again.
- **Large outputs that can be recomputed,** each listed with its digest:
  - the two `git archive` exports, and their extracted trees;
  - the listings of those trees;
  - the two discovery lists.

  The audit compared each extracted tree's hash with its commit's tree, and recomputed the
  discoveries.
- **Raw outputs of workers, which hold machine paths or the owner's processes,** listed file by file
  with their digests. This follows plan review 001's PR-06.
- **Privacy-scan scripts whose search terms exist to find private items:**
  - the audit's `z05` and `z06`;
  - the HOST review's `h05`.

  They are listed with their digests.
- **Synthetic test worlds of the reviewers and the author,** summarized by directory: the number of
  files and the SHA-256 of their sorted digest listing.
