# Storage classes, durable locations and the restore check

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
REQ-038 (TASK-008, DEC-009). Every location below was observed read-only on
2026-11-25, or is marked as not observed. No backup service was set up and nothing
was uploaded for this record; the repository is public, so machine paths stay out.

## By kind

| Kind of material | Treatment | Durable location |
| --- | --- | --- |
| Source, instructions, manifests, locks, small task records | Committed; pushed with ordinary Git | GitHub `Omegapy/OntoKin`: main, the migration branch and the C271 branch, read with `git ls-remote` |
| Environments, `node_modules`, caches, setup reports, temporary builds | Ignored, recreated from the committed specification, never archived | None needed. A copy of an environment is no specification |
| Test working output | A new directory for each run beside the clone (`OntoKin-local/checks/`), with source and environment identities | Local disk only. Digests of the logs and summaries that records cite are committed; the runs can be repeated from the named revisions |
| Durable evidence of this migration | Exact bytes committed in this directory | GitHub |
| Durable evidence of C271 that Git does not hold | Kept as it is, never recreated, recompressed, split or converted to an LFS pointer | The owner's ChatGPT Library: the R06 handoff and the separately saved copy named in [RECONCILIATION](RECONCILIATION.md#not-in-git) |
| Legacy handoffs and receipts | Kept unchanged; identities and links recorded where they were created | The owner's ChatGPT Library, folder `OntoKin`; [the retained earlier CURRENT](CURRENT-before-migration.json) holds the C262 archive and the browser handoffs and receipts through C270 |
| Machine paths, credentials, sign-ins | Local configuration, SSH agent and system keyring; never committed | Not backed up by this project |

Handoffs are not moved into the repository, and no chain of nested handoffs was added. Small
pointers and referenced evidence replace them for local sessions.

## Existing durable mechanisms

| Mechanism | Observed |
| --- | --- |
| GitHub | Holds every commit of this clone: no unpublished commit and no stash |
| ChatGPT Library | Not readable by a local agent. The owner retrieved the R06 files from it on 2026-11-25 (below) |
| Personal backup of the machine | Known to the owner; kept off this public record |
| Git LFS | No tracked file is selected for LFS |

An ignored directory on this disk is not a backup, and a Git bundle would cover neither
untracked files nor LFS payloads.

## Restore check

The R06 handoff archive is the representative unique artifact: it holds the chain with the
accepted C271 candidate, which Git does not hold. The owner retrieved it from the ChatGPT
Library on 2026-11-25; its size and SHA-256 equal the recorded ones, and its manifests, its
nested archives, the 245 accepted files and the exact evidence archive passed every check
([record](R06-VERIFICATION.json)).

## Material that exists only on the local disk

Neither GitHub nor the Library holds the following, as far as it was observed. Whether a
personal backup covers it is kept off this record.

| Material | Content | Consequence of losing it |
| --- | --- | --- |
| `Implementation_Plans/` in the main checkout | The plan tracker of PLAN-20261125-CB551B16 (764 KiB), kept untracked by decision (DEC-012) | The committed [plan](../../workflow/tasks/LOCAL-MIGRATION-20261124/PLAN.md) and [ledger](../../workflow/tasks/LOCAL-MIGRATION-20261124/task.json) keep the steps and their state; the tracker's evidence texts would be lost |
| `OntoKin-local/` beside the clone | Raw logs, workspaces, staged wheels, package-smoke directories, inventories (about 25 GiB), and local copies of the two R06 files | Records keep the digests and results; the wheels can be downloaded again and compared with the lock |
| The approved brief of the migration | 72,126 bytes, SHA-256 `1f05310df589ed3a303290712eaaad460d2e451371693ebc85347a5c6450d2cb`, in the owner's downloads folder | The TRD restates its material content. Whether the Library also holds it was not observed |
| Other legacy handoffs in the owner's downloads folder | Listed below | Copies, as far as their identities are recorded; whether the Library still holds each one was not observed |

No project mechanism protects this material. Setting one up is the owner's separate decision.

### Legacy handoffs found in the downloads folder

| File | Bytes | SHA-256 | Identity found recorded on |
| --- | --- | --- | --- |
| `OntoKin_C191_Guided_Contact_Results_Handoff_2026-11-10.zip` | 496,320,576 | `3d35bd16869f78c94a780985aa95c31bba60bcff782eb7ca570c614a2f871343` | not found in the searched records |
| `OntoKin_C192_Paired_Contact_Results_Handoff_2026-11-10.zip` | 498,014,409 | `4b6735c49f3c27a7b2708dab4eebbc61bbda6931e9b84cca03ff51a21c49d990` | main |
| `OntoKin_C208_Recovery_Handoff_2026-11-11.zip` | 427,796,120 | `0f8aa41fbccce9ac4896b61ceea3ab2972523fccefd73b670a3ab111a6f136bb` | not found in the searched records |
| `OntoKin_C216_Native_Capture_Blocker_Handoff_2026-11-12.zip` | 451,450,082 | `759108451998e64d8664406f87b32aa8d2b02526b35ff25322c97a225ebcda3d` | not found in the searched records |
| `OntoKin_C217_Recovery_2026-11-12.zip` | 4,145,967 | `684a351c6a5e77bc31e51697b59a67cf41506ed3251767a7398508e74742c527` | not found in the searched records |
| `OntoKin_C250_Held_Playback_Preparation_Handoff_2026-11-15.zip` | 534,426,268 | `660a96af1bfa8b5cca6eaf930f8fd20fb8dac38e4473f3d070b6245e2cb58991` | main |
| `OntoKin_C251_Held_Controlled_Attachment_Handoff_2026-11-15.zip` | 536,366,296 | `c66d9e5f86ba907c5dd1096d09ab0854be144a092cef8a73c50ca0cbbdaf4cb0` | main |
| `OntoKin_C253_Localized_Repair_Protocol_Handoff_2026-11-16_Final.zip` | 536,870,906 | `778d6fbf8062faf27b6d5e5b571bedebd303f9c7ed61b6ffe8d60cbc4de4f7f4` | not found in the searched records |
| `OntoKin_C254_Handoff_Capacity_Repair_2026-11-16.zip` | 528,428,381 | `af10ffbe3bf6957a43e20448079b5119ce1c0ae764f7efb842ba6def705993da` | not found in the searched records |
| `OntoKin_C255_Reconciled_Handoff_2026-11-16.zip` | 530,170,762 | `b357292196afd7eb03cb95c1422f86afc6b9c04a53f0fb04da3399e16dfdb2c7` | not found in the searched records |
| `OntoKin_C258_Recovery_Handoff_2026-11-17.zip` | 535,001,160 | `145203ba58c0b5996ce11b9691bbbe9f81c1c302ecfed62b1c303f40f8768211` | not found in the searched records |
| `OntoKin_C260_Reconciled_Review_Handoff_2026-11-17.zip` | 536,701,100 | `587ca7c93719485c38de92e27b2d6b3da7153e4b492b3839d92a6618aa8bc76e` | not found in the searched records |
| `OntoKin_C267_Development_Handoff_2026-11-18.zip` | 250,000 | `5d00ae5d44624f37806bff301c647f8d4486309252f575c7b762a6724f4aaaae` | main |
| `OntoKin_C270_Development_Handoff_2026-11-20.zip` | 2,573,742 | `2c8d08e8cbdeec4ada3e65d692dc47d813169c3268fe33d014b89e6281a32940` | main |
| `OntoKin_C271_P22_Ephemeral_Host_Amended_Handoff_2026-11-22.zip` | 1,957,765 | `54b79e4b6e2e31546bb0bfe7392b333c8fe340fa510b0e8d1773a97a88c72d49` | C271 branch |
| `OntoKin_C271_P28_Recovery_Handoff_2026-11-23.zip` | 9,054,965 | `00432c32fc71530cf060ba901330ef38018301363bb2ef378591af540b04ee85` | C271 branch |
| `OntoKin_Startup_Compression_Handoff_2026-11-18.zip` | 186,129 | `446b3b58e9d913af85014982ec741928b5833d490a0c7d9cb33695062639ac3d` | main |
| `OntoKin_Startup_Compression_Handoff_2026-11-19.zip` | 290,419 | `9ddf215d854c40712de986c1ffbaeccffc1e389fc50a3598a5985a685d1514af` | main |

The digests were computed on 2026-11-25. The archives were not opened for this record, except
that the listing and manifests of the C271 P28 recovery handoff were read in memory to prepare
the R06 check. "Recorded" means that the digest occurs in the documents of main, or in the
workflow and C271 documents of the C271 branch; every other file is named here as found.
