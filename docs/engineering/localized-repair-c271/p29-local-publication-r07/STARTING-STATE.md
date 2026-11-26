# C271-P29-R07 starting state

Observed by the Director session of this phase before any change to the repository, the
remote or GitHub. Local mode, started from current main's `LOCAL-START-HERE.md`. Inspection
commands ran between 2026-11-26T00:40:26Z and 00:46:16Z; the record was written at
00:47Z. Places beside the clone are named relative to it; no machine path, account name or
credential is recorded.

## Checkout and refs

| Item | Observed |
| --- | --- |
| Repository | `Omegapy/OntoKin`; `origin` is the owner's configured SSH remote (a host alias), the same for fetch and push |
| Checkout | The owner's persistent clone, main checkout, branch `main` |
| Local head | `main` at `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, equal to `origin/main` (ahead 0, behind 0) |
| Remote-tracking refs (last fetch) | `origin/main` `51223c9b94a222f29d38eb6c33808f8e55e2bff9`; `origin/work/c271-missing-import-digest-control` `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; `origin/HEAD` points to `origin/main` |
| Independently observed remote heads | `git ls-remote --heads origin` at 2026-11-26T00:46:14Z: exactly two, `main` `51223c9b94a222f29d38eb6c33808f8e55e2bff9` and `work/c271-missing-import-digest-control` `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; no tags; the other advertised refs are `refs/pull/*` |
| Local branches | `main` only |
| Unpublished commits | None: `git log origin/main..main` is empty and no other local branch exists |
| Stashes | None |
| Worktrees | One: the main checkout. `../OntoKin-worktrees/` beside the clone exists and is empty |
| Git lock files | Only `ontokin-bootstrap.lock`, the setup tool's permanent empty lock file (2026-11-25T14:10 local time); no `index.lock` |

## Tracked modifications and untracked files in the main checkout

All of them are preserved unchanged by this phase, except the tracker of this plan, which
the plan itself operates from the main checkout (its files change with every tracker
update; at the start of execution `plan.json` was revision 3, SHA-256
`56c315989f6041897e74ba5634964b8ddd84dc0ee3a1a2c5c091106f8de7b5da`).

| State | Path | Bytes | SHA-256 at 00:46Z |
| --- | --- | ---: | --- |
| Modified (index and HEAD blob `22c2f218`) | `TRDs/INDEX.md` | 1,195 | `5504962a9d4bb45cc49734ba5233262fdc5819437bbaab21a798f3cb0d69492a` |
| Untracked | `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md` | 73,898 | `063e8e1a88ef7224420c34dbdb92d2a25b4365a96962ad0e834951b652ff516b` |
| Untracked, completed migration tracker | `Implementation_Plans/Plan_ontokin-local-development-migration_2026-11-25_CB551B16/plan.json` | 630,302 | `49394dbfcdec4d18671367127083240aa289fe4c59778179d3bd73abb8bfd4bb` |
| Untracked, completed migration tracker | `Implementation_Plans/Plan_ontokin-local-development-migration_2026-11-25_CB551B16/PLAN.md` | 167,941 | `d096ead007986393f4c192cb04b5bcc7f426b50d2dda4919665b9f6b87d4423b` |
| Untracked, completed migration tracker | `.../CB551B16/TRACEABILITY.md` | 27,903 | `6527d7959dedb47104c8933b8e8025bd49dca900695b8511e0742e1682188fa6` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-001_baseline-scope-and-authority.md` | 21,828 | `312aa4a86c72722090b0af81b86263ef094480450a552fd4e0cf22303d7b3285` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-002_legacy-reconciliation-and-durable-storage.md` | 20,832 | `ec2ff5275cc353d7609bfa3c7e9f6a93953cc74733c6e625223f7714e9e9ef1f` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-003_repeatable-environment-and-tooling.md` | 62,201 | `ad37d72ee65dcf19fef3d8934b1a8a9cc25c29c8952bf8d69430b0880e220ae9` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-004_local-mode-instructions-and-continuity-records.md` | 56,915 | `6fcf14e908daecc07636f602984b9b78e7991d8db40e54e308099fda72ae16ba` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-005_validation-and-demonstrations.md` | 29,648 | `6e6336562ec9cd27873b4d395ec8886493f1050d9d8845fe5dbe6a54206a9c4c` |
| Untracked, completed migration tracker | `.../CB551B16/phases/PHASE-006_review-integration-and-closure.md` | 23,762 | `27c17fc3c577ee5f82bd53a0616ebe35cfc0519eee55fd4bb5227f29092b0fb4` |
| Untracked, this plan's tracker (changes by tracking) | `Implementation_Plans/INDEX.md` and the nine files of `Implementation_Plans/Plan_c271-p29-exact-publication-in-local-mode_2026-11-26_F3122BB2/` | | not preserved byte for byte by design |

Tracked files that the plan protects, unchanged on main (`HEAD` blobs): `STATUS.md`
`99ab22fb`, `docs/workflow/CURRENT.json` `81465753`, `tools/check_local.py` `95cd375f`,
`tests/test_local_checks.py` `45c67d5c`, `.gitattributes` `4e51ada2`,
`TRDs/trd_ontokin-local-development-migration_2026-11-24.md` `b7da5fd4`; each working-tree
copy equals its `HEAD` blob.

## Workers, lease and phase ownership

| Item | Observed |
| --- | --- |
| This phase's owner | The Director session of C271-P29-R07, a Claude Code session in the main checkout; no subagent active |
| Other processes | Four idle Claude Code sessions whose working directory is the removed migration worktree `../OntoKin-worktrees/local-migration-20261124`; the ChatGPT desktop application. No process has a file of the clone's Git directory open. No writer to the C271 branch is observed: its remote head is unchanged since 2026-11-23T19:31:47-07:00 |
| Main integration lease | Released at 2026-11-25T21:33:52Z, previous owner `local-migration-f58a0f3c1d5a`, no unknown write (`STATUS.md` on main). This phase does not use it |
| Last recorded C271 phase owner | `c271-p29-r06-ed94fcf35220` (R06). Its terminal record sets the release condition "this identical terminal body is observed on both #273 and #274". Observed: pull request comment 7136207682 and issue comment 7136203591 have identical bodies (4,557 characters). Released |
| Owner named in the task record | `c271-p29-r02-18d6675d4cbb` (R02), released by its terminal comment 7120290539 ("releases this recovery ownership and stops"), with a matching issue comment. The later R03, R05 and R06 owners are recorded only in comments |

## Pull request and issue

| Item | Observed with `gh` at 2026-11-26T00:40Z |
| --- | --- |
| Pull request 274 | Open, draft, unmerged; head `work/c271-missing-import-digest-control` at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; base `main`; mergeable `CONFLICTING`, merge state `DIRTY`; 18 comments, the last the R06 terminal record of 2026-11-24T15:32:44Z |
| Issue 273 | Open; 12 comments, the last of 2026-11-24T15:32:35Z with the R06 terminal body |

## Availability observed in this session

| Item | Observed |
| --- | --- |
| GitHub CLI | Authenticated, token scopes include `repo` and `workflow` |
| Git read over the SSH remote | `git ls-remote` succeeded |
| Git write over the SSH remote | Not yet observed; the declaration push is its first observation |
| Main checkout environment | `.venv/bin/python` is CPython 3.12.13 |
| R06 archive and receipt | Observed in TASK-007 |

Unique work found: none beyond the files listed above, all of which stay in place. The brief
and the TRD's S observations are not used in place of this record.
