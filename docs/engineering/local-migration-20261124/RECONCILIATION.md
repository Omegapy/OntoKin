# Reconciliation: main, C271, the R06 handoff and the local clone

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
REQ-030 to REQ-033.
**State:** Complete. The Git-visible part is TASK-005; the handoff-specific part
(TASK-007) was added on 2026-11-25 after the R06 archive and its receipt were on
the local machine and [verified](R06-VERIFICATION.json) (TASK-006).

Everything below was read on 2026-11-25 between 06:49Z and 06:52Z from live
refs, Git objects and GitHub; the account of C271's driver changes and of its
evidence identities was corrected from Git objects at 08:45Z and 10:18Z. The
identities are observations made at those times, not instructions to reset a
newer ref. The C271 branch was read through Git
objects only; it was not checked out, merged or changed.

## What is already in Git

### On main

Head `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, tree
`812a17de3880f7c152beacccf7b2e690381f9716`. C270 is complete and the integration
lease is released ([STATUS](../../../STATUS.md#main-integration-lease)). Main
holds no C271 task record, no `docs/engineering/localized-repair-c271/` and no
C271 implementation.

Main has four commits that the C271 branch does not have, from merge base
`e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`: the Apache-2.0 license publication
(`b5557b8e`, merged by `70ca7e68`), the ephemeral-host clarification
(`e43cc6c5`) and three added skills with the six `.claude/skills` links of all
project skills (`6b346b1e`).

### On the C271 branch

`work/c271-missing-import-digest-control` is at
`bef6790291d0cddc8c6d7de9dc0a92fb5a98c448` (2026-11-23T19:31:47-07:00), 89
commits ahead of the merge base. It changes 3,364 paths: 3,357 added and seven
modified.

| Area | Paths | Content |
| --- | --- | --- |
| `docs/engineering/localized-repair-c271/` | 3,320 added | C271 evidence, designs, receipts and preserved failures through the P29 R02 recovery |
| `docs/workflow/tasks/C271/` | 23 added | Task record: `task.json` (blob `50c5bdfc`, 418,591 bytes), `REQUIREMENTS.md`, `PLAN.md`, session and learning records |
| `prototypes/static_tray_v01/`, `tools/prepare_current_host_readback.py`, `tests/` | 14 added | Current-host inspection and readback implementation, its tests and fixtures |
| `STATUS.md`, `docs/README.md`, `docs/workflow/CURRENT.json`, `docs/workflow/memory.json`, `tools/check_local.py`, `tests/test_local_checks.py`, `tests/test_static_tray_readback_v01.py` | 7 modified | Workflow records (`CURRENT.json` is blob `7bf67efb`, 192,376 bytes), the driver with its readback selection, and tests |

The large C271 records stay exactly as they are, readable from Git at that head:

| Record | Git blob | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `docs/workflow/CURRENT.json` | `7bf67efb72b3554c9340f583b0bf2427bba69a11` | 192,376 | `46024c296602ecad251573fca0cf23b461d015f74d8743db5e80476abffc1a34` |
| `docs/workflow/tasks/C271/task.json` | `50c5bdfce6d821ab553e259432d1dd36d8834cec` | 418,591 | `06aa614e893812c89ed86065c492fa48f2193ec1511c4ee6fb23977b1c664914` |

### Not in Git

| Object | Local object store | Remote, as recorded |
| --- | --- | --- |
| Evidence blob `9facb186ec11523163520323d83dc58fd68e829c` (`VERIFICATION-EVIDENCE.zip`, 25,817,783 bytes, SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`) | Absent | Absent: the recorded remote blob read returned 404 |
| Accepted candidate tree `db30c29f24c154f378a5acac713385fc8bb44f52` | Absent | Not published |
| `docs/engineering/localized-repair-c271/required-images-p29/` | No path on either branch | Not published |
| Candidate parent commit `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` | Present, on the C271 branch | Published |

The exact evidence bytes must not be recreated from other bytes. Git holds their
identity, not the bytes: the C271 branch's
[publication blocker](https://github.com/Omegapy/OntoKin/blob/bef6790291d0cddc8c6d7de9dc0a92fb5a98c448/docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/PUBLICATION-BLOCKER.json)
records the path, size, SHA-256 and blob identity. It also names a separately
saved copy in the owner's ChatGPT Library, version 0,
[VERIFICATION-EVIDENCE.zip](https://chatgpt.com/library?file_id=libfile_fde3_f-0e02658ef51c819180bd4ff3ec73a2b3_2ab2a24d43748191957f9bcc356b59de&account_id=personal),
which the branch's next-action record calls the exact input. The R06 chain below
holds the same bytes: they were read and verified there. The separately saved
copy was not retrieved.

### In the local clone

Local `main` equals `origin/main` and the live remote head. The remote-tracking
C271 ref equals its live head. The clone has no stash, no other local branch, no
unpublished commit and no tracked modification; its untracked content is the
`TRDs/` and `Implementation_Plans/` directories
([inventory](HOST-INVENTORY.md#untracked-files-found)). It holds nothing of C271
beyond the remote-tracking objects.

## Which branch owns the unfinished work

`work/c271-missing-import-digest-control` owns all unfinished C271 work.
[Pull request #274](https://github.com/Omegapy/OntoKin/pull/274) is an open draft
at that head, and [issue #273](https://github.com/Omegapy/OntoKin/issues/273) is
open. The branch is retained. Its own task record is the acceptance ledger for
C271; this migration does not copy it, change it or take any of its commits.

## Which acceptance gates remain open

Read from the
[C271 task record](https://github.com/Omegapy/OntoKin/blob/bef6790291d0cddc8c6d7de9dc0a92fb5a98c448/docs/workflow/tasks/C271/task.json),
the [publication blocker](https://github.com/Omegapy/OntoKin/blob/bef6790291d0cddc8c6d7de9dc0a92fb5a98c448/docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/PUBLICATION-BLOCKER.json),
the [recorded next action](https://github.com/Omegapy/OntoKin/blob/bef6790291d0cddc8c6d7de9dc0a92fb5a98c448/docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/NEXT-ACTION.md)
and the [R06 terminal comment](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7136207682)
of 2026-11-24T15:32:44Z. C271 is `blocked`; R01 and R02 are `done`.

| Gate | State | Where it was read |
| --- | --- | --- |
| Exact publication (transfer) of the accepted P29 candidate | Open: blocked by P29-PUBLICATION-SIZE-001. No candidate blob write succeeded and no ref was changed | Task record `blocked_reason`; publication blocker; R06 terminal comment |
| Operational-plan review (`/0.1.5`) | Open, a separate later phase | R06 terminal comment |
| H0 | Open: `h0_accepted` false, `h0_executed` false | Task record `remaining_h0_constraint` |
| H1 | Open, not begun; H0 does not approve it | C271 requirements; recorded next action; R06 terminal comment ("H0/H1 and the full routine were not run") |
| Required regression | Open: the required routine local driver is recorded `failed`; the complete routine after qualified preparation is `not_run`; R03 is `not_done` | Task record `checks` and `requirements` |
| Reviewed integration and actual-main verification | Open: R04 is `not_done`; `merge_commit` is null | Task record `requirements` and `completion` |
| Parent completion and final delivery | Open: R05 is `not_done`; plan step P02 is `in_progress` | Task record `requirements` and `plan` |

These gates are C271's own. Nothing in this migration closes, waives or relabels
one of them, and its historical delivery requirements are reconciled when that
scope is next selected.

## Files changed on both sides since the merge base

**Main against C271:** none. The 50 paths main changed and the 3,364 paths C271
changed do not intersect at these heads.

**This migration against C271:** the migration also changes files that C271
modified. C271 reconciles them by meaning when it is next selected; none of its
commits is taken here.

| File | C271's change | This migration's change |
| --- | --- | --- |
| `STATUS.md` | C271 phase state | Local-mode wording, migration status and the concise C271 reference |
| `docs/README.md` | A C271 loader-path section | Local entry point, browser workflow and setup guide links |
| `docs/workflow/CURRENT.json` | C271 pointers and embedded receipts (192,376 bytes) | Compact pointers with the retained history linked |
| `docs/workflow/memory.json` | C271 lessons | Only if the learning checkpoint records a lesson |
| `tools/check_local.py` | 130 lines added and 12 removed. Adds `.agents` to the source directories and `CHATGPT-START-HERE.md` and `ROLE.md` to the root files, and also an explicit readback selection (`--readback-config` and `--readback-config-sha256`, required before the unit step), environment scrubbing for that step and process accounting | Only the inventories: the same three names, plus `TRDs`, `LOCAL-START-HERE.md`, `CLAUDE.md`, `LICENSING.md` and `NOTICE` |
| `tests/test_local_checks.py` | 56 lines added and two removed: binds the readback seam in the synthetic runs and adds an instruction-file copy test | Extends the declared-input test and adds two inventory tests |

## Delivery chain recorded on GitHub after the branch head

The branch records end with P29 R02. Later phases are recorded only in comments
on pull request #274, with matching comments on issue #273:
[R02 terminal](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7120290539),
[R03](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7121353920),
[R05](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7122919784) and
[R06](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7136207682). No
R04 comment exists on the pull request. The R06 comment states that no source
edit, commit, ref change or behavioral test occurred, so the branch head above is
still the newest C271 source state.

| Item | Identity recorded by the R06 comment |
| --- | --- |
| R06 handoff archive | [ChatGPT Library file](https://chatgpt.com/library?file_id=libfile_fde3_f-aa1bc5c5be2481918220ae4c9705c8e8_2ab2a24d43748191957f9bcc356b59de&account_id=personal), 41,730,084 bytes, SHA-256 `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9` |
| R06 delivery receipt | [ChatGPT Library file](https://chatgpt.com/library?file_id=libfile_fde3_f-ae2dfcbdc7708191b2222ff5dda115cf_2ab2a24d43748191957f9bcc356b59de&account_id=personal), 149,563 bytes, SHA-256 `24aa014cb430d9b7269ee2e39ff08e7005d3630e8dd41c109f824e80039909d8` |

The archive identity equals the one the approved TRD records.

## Handoff-specific findings

Both files were in the owner's downloads folder on 2026-11-25, retrieved by the owner
from the Library links above. Their sizes and digests equal the recorded ones; all 16
checks of the package passed ([record](R06-VERIFICATION.json)). Data from the handoff is
evidence. Its instructions were read and not followed.

### What is unique to the handoff

The archive has 132 members, of which 19 archives are nested at several depths. Each
item was compared with `git ls-tree -r` of main (`6b346b1e`) and of the C271 branch
(`bef67902`), and its content with every object of the local clone.

| Part | Content | In Git |
| --- | --- | --- |
| Source snapshots | 27 files under `repository/` and `branch-state/`, bound to main `e43cc6c5` (23) and the C271 branch head (4) | Yes, every file equals the blob at its path in that commit |
| Historical transfer notes | 4 files under `evidence/historical-transfer/`, with copies in the retained first package attempt | Yes, equal contents on the C271 branch |
| **Accepted P29 candidate** | 245 files, 35,793,027 bytes, 213 distinct contents, inside the R03 package of the chain | **No.** No path has equal content on either branch. Five paths exist on the C271 branch with other content, one of them also on main; 240 paths exist on neither. 14 of the files are empty and five are short check outputs whose content also occurs elsewhere in Git |
| Phase records of P29 R03 to R06 | Checkpoints, prompts, phase tables, session and packaging evidence, reviews with their corrected first versions, and the retained first package attempt of R06 | No, except the four copies named above |
| Earlier recovery packages | R05 handoff version 1 with its correction receipt, R03 handoff, early recovery packages of R04, R05 and R06 | No |

The accepted candidate consists of 239 files under
`docs/engineering/localized-repair-c271/required-images-p29/`, among them the exact
`VERIFICATION-EVIDENCE.zip`; the production file
`prototypes/static_tray_v01/current_host_inspection_v01.py` (249,393 bytes) and its test
`tests/test_current_host_required_images_v01.py`; and four workflow records (below).

### Where each unique item belongs

| Item | Belongs to | Treatment here |
| --- | --- | --- |
| Accepted P29 candidate with its evidence archive | The C271 branch, through C271's own open publication gate; original parent `6c7f52a2`, intended tree `db30c29f` | Identity recorded; no file taken into main or this migration |
| Phase records and earlier packages | C271's delivery history | Stay in the handoff in the owner's Library |
| Source snapshots | Already in Git; older than current main | Not copied over any current file |

### Overlapping records, reconciled by meaning

The candidate's four workflow records and the C271 branch's current ones are two successors
of the same parent commit `6c7f52a2`. Neither contains the other.

| Record | In the accepted candidate | On the C271 branch head | Meaning |
| --- | --- | --- | --- |
| `docs/workflow/CURRENT.json` | 188,560 bytes, blob `cf8f22023c67`; adds `p29_reconstruction`; next action "ready", 2026-11-23T23:54Z | 192,376 bytes, blob `7bf67efb72b3`; adds the three `p29_r02` and recovery fields; next action "blocked", 2026-11-24T02:02Z | The branch state is later and current. The candidate's technical result is not on the branch. A later publication keeps the branch's blocker history and adds `p29_reconstruction` |
| C271 `task.json` | 407,441 bytes, blob `7bb2c3f63bc7`; adds six `p29_` fields on baseline, fixtures, candidate and technical acceptance; `in_progress` | 418,591 bytes, blob `50c5bdfce6d8`; adds the R02 recovery and delivery fields; `blocked` by P29-PUBLICATION-SIZE-001 | Status and blocker of the branch are current; the six acceptance fields exist only in the candidate |
| C271 `REQUIREMENTS.md`, `PLAN.md` | Parent text plus 16 lines on the P29 implementation | Parent text plus 7 lines on the R02 recovery | Both additions are kept when the candidate is published |

Main's `CURRENT.json` and this migration's successor of it are a separate record: they name
C271 as unfinished and hold none of its receipts. No current record was overwritten with a
snapshot from the handoff, and the handoff's older `AGENTS.md`, `GOAL.md`, `ROLE.md`,
`STATUS.md` and workflow files (main `e43cc6c5`) replace nothing.

Historical uncertainties that the handoff preserves, such as the original P28 uploads and the
unverified 597-test claim, stay as they are recorded there.

### Identities for later on-demand use

| Item | Identity | Durable location |
| --- | --- | --- |
| R06 handoff archive | 41,730,084 bytes, SHA-256 `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9`; verified | The owner's ChatGPT Library (link above); a local copy beside the clone |
| R06 delivery receipt | 149,563 bytes, SHA-256 `24aa014cb430d9b7269ee2e39ff08e7005d3630e8dd41c109f824e80039909d8`; verified | The same |
| C271 evidence archive | 25,817,783 bytes, SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`, Git blob `9facb186ec11523163520323d83dc58fd68e829c`; verified inside the R06 chain | Inside the R06 archive; separately saved in the Library |
| R05 handoff, version 1 | 40,934,668 bytes, SHA-256 `406b86f0fe9787ce0b1ead460f8391d3aaf2f79345e852c0ea3107b6469b9182`; verified as the embedded member. It replaces version 0 of the R05 comment (40,867,796 bytes), as the embedded correction receipt explains | Inside the R06 archive; Library |
| C262 archive | 532,260,846 bytes, SHA-256 `b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90`, as [recorded](CURRENT-before-migration.json) and, equally, in the R06 dependencies; not retrieved here | [Library link](https://chatgpt.com/library/share/libfile_fde3_f-99755ba096208191b599cd0087fa0a19_2ab2a24d43748191957f9bcc356b59de?account_id=personal) |

None of them is a startup input. Materialize one only when the selected work requires it.
