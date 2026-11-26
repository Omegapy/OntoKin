# Preservation and boundary audit of C271-P29-R07

Plan step TASK-020. Run on 2026-11-26 from 01:57:00Z to 01:57:02Z (UTC) against the pushed records
commit `12d7e55472f8b1d2b67414857ec310b288025244`. It was run again against each pushed
correction commit:
- `bb75b1c5f83da34e8cc653b536e635d2e89a62d2`, at 02:12:54Z;
- `5c74f49e04da9977f7c8da80515414dbe8e89549`, the last correction, from 02:23:52Z to 02:23:55Z.

The corrections changed only records of this phase after the resumability check. Every run gave
the same result for every item. The table shows the last run, where the runs differ only in
counts. Every item rests on a command
or a comparison, not on a restated intention. Raw results are kept in the working evidence beside
the clone.

| Item | Observed | Method |
| --- | --- | --- |
| PR274 open, draft and unmerged; issue273 open; branch at the pushed head | PR274 `OPEN`, draft, not merged, head `5c74f49e`, base `main`, mergeable `CONFLICTING`; issue273 `OPEN`; the remote branch at `5c74f49e` | `gh pr view 274`, `gh issue view 273`, `git ls-remote --heads origin` |
| No pre-existing path deleted; only the four records and `prototypes/static_tray_v01/current_host_inspection_v01.py` modified | From `bef67902` to `5c74f49e`: 0 deleted, 0 renamed, 5 modified (those named), 256 added (240 accepted files and 16 records of this phase) | `git diff --name-status bef6790291d0cddc8c6d7de9dc0a92fb5a98c448 5c74f49e` |
| The R06 archive and its receipt keep their identities at the location used | 41,730,084 bytes, SHA-256 `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9`; 149,563 bytes, SHA-256 `24aa014cb430d9b7269ee2e39ff08e7005d3630e8dd41c109f824e80039909d8` | size and SHA-256 of the copy beside the clone |
| R01 to R05 unchanged; nothing marked complete | The R01 to R05 sections of `REQUIREMENTS.md` and the `task.json` acceptance texts are equal at both revisions; R01/R02 `done`, R03–R05 `not_done`, P01 `done`, P02 `in_progress`; task `in_progress`, not `done` | `git show` of both revisions |
| No record of this phase marks R03, R04, R05, C271, H22, C260 or the product complete | 15 records searched, no claim found. The one pattern match is the negated sentence in `REVIEW.md` ("none says R03, R04, R05, C271, H22, C260 or the product is complete") | regular-expression search, with each match read in its whole sentence |
| No excluded activity ran and no hosted run started | The command log has no routine driver, unit suite or behavioural test, Node or `ldd`, merge of main or write to main; GitHub lists no workflow run for this branch at all | search of the phase command log; `gh run list --branch work/c271-missing-import-digest-control` |
| No ceiling, budget, fixture, tolerance or expected outcome changed | No limit-like path outside the accepted payload changed; current main's GOAL still states 100,000 operations and 30,000 ms | `git diff --name-only` with a path filter; `GOAL.md` at `51223c9b` |
| Main untouched, and the main checkout's starting items intact | Main's remote head is `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, as at the start; every file listed in the starting state has its recorded SHA-256 (this plan's own tracker excepted, which the plan operates); no stash | `git ls-remote`, SHA-256 of each listed file, `git stash list` |
| Operations of unknown outcome stay unknown | The R02 phase record is byte-identical at both revisions and still lists four historical unknown operations; none was replayed | byte comparison of `p29-publication-recovery-r02-20261123/PHASE.json` |

## Limits of this audit

- The command log records the commands this phase ran through its logging wrapper: every
  state-changing command and every check. Some read-only inspection commands ran outside it,
  among them the dry `git merge-tree --write-tree` computation behind `MAIN-CONFLICTS.md`. That
  computation changed no ref and no working file, and the record discloses it.
- The first run of this audit reported a false positive: a wrapped line hid the negation in the
  sentence of `REVIEW.md` quoted above. The search was corrected to read whole sentences and run
  again. The first result is kept beside the clone.
- The audit covers the state through the last correction commit. The push of the closing record that
  carries this file is observed in the final report.
