# Reconciliation: main, C271, the R06 handoff and the local clone

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
REQ-030 to REQ-033.
**State:** The Git-visible part (TASK-005) is complete. The handoff-specific
findings are marked **awaiting TASK-007**, which needs the R06 archive and its
receipt on the local machine.

Everything below was read on 2026-11-25 between 06:49Z and 06:52Z from live
refs, Git objects and GitHub. The identities are observations made at that time,
not instructions to reset a newer ref. The C271 branch was read through Git
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
(`e43cc6c5`) and the three added skills with their `.claude/skills` links
(`6b346b1e`).

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
| `STATUS.md`, `docs/README.md`, `docs/workflow/CURRENT.json`, `docs/workflow/memory.json`, `tools/check_local.py`, `tests/test_local_checks.py`, `tests/test_static_tray_readback_v01.py` | 7 modified | Workflow records (`CURRENT.json` is blob `7bf67efb`, 192,376 bytes), driver inventory and driver tests |

The large C271 records stay exactly as they are, readable from Git at that head:

| Record | Git blob | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `docs/workflow/CURRENT.json` | `7bf67efb72b3554c9340f583b0bf2427bba69a11` | 192,376 | `46024c296602ecad251573fca0cf23b461d015f74d8743db5e80476abffc1a34` |
| `docs/workflow/tasks/C271/task.json` | `50c5bdfce6d821ab553e259432d1dd36d8834cec` | 418,591 | `06aa614e893812c89ed86065c492fa48f2193ec1511c4ee6fb23977b1c664914` |

### Not in Git

| Object | Local object store | Remote, as recorded |
| --- | --- | --- |
| Evidence blob `9facb186ec11523163520323d83dc58fd68e829c` (`VERIFICATION-EVIDENCE.zip`, 25,817,783 bytes) | Absent | Absent: the recorded remote blob read returned 404 |
| Accepted candidate tree `db30c29f24c154f378a5acac713385fc8bb44f52` | Absent | Not published |
| `docs/engineering/localized-repair-c271/required-images-p29/` | No path on either branch | Not published |
| Candidate parent commit `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` | Present, on the C271 branch | Published |

The exact evidence bytes must not be recreated from other bytes. Their identity
is held by the handoff chain (below), not by Git.

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
| `docs/README.md` | C271 navigation | Local entry point, browser workflow and setup guide links |
| `docs/workflow/CURRENT.json` | C271 pointers and embedded receipts (192,376 bytes) | Compact pointers with the retained history linked |
| `docs/workflow/memory.json` | C271 lessons | Only if the learning checkpoint records a lesson |
| `tools/check_local.py` | Adds `.agents` to the source directories and `CHATGPT-START-HERE.md` and `ROLE.md` to the root files | The same additions and the new local-mode files |
| `tests/test_local_checks.py` | Matches its driver inventory | Matches the amended driver inventory |

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

**Awaiting TASK-007.** The archive and its receipt were not on the local machine
when this part was written, so the following are not established here:

- what is unique to the R06 handoff, checked item by item against both branches;
- where each unique item belongs;
- how the handoff's older `CURRENT.json`, C271 `task.json`, `REQUIREMENTS.md` and
  `PLAN.md` snapshots relate by meaning to the current records;
- the verified identity and durable location of the R06 archive, its receipt and
  the C262 archive.
