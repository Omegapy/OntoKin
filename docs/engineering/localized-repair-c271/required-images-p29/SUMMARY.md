# C271 P29: accepted required-image reconstruction

P29 implements the finite P27 design for inspection-plan schema `/0.1.5`. The operational policy binds the five catalog images (libdl, libm, libpthread, librt and libutil) and their common loader after fresh Python/libc proof, then permits their private metadata parsing route. Full validation and rechecks reconstruct that proof. The final launch retains its existing identity guards. The private reader enforces the adopted finite dynamic-tag rules; parsing a synthetic image alone does not authenticate operational pins. Existing profiles, public parsers, pinned inputs and launch sequencing remain unchanged.

This is new P29 work. The original interrupted P28 implementation and its reported 597-test result remain unavailable and unverified. No unknown P28 upload was replayed.

## Accepted evidence

| Check | Actual result |
| --- | --- |
| Corrected baseline on original production | 481 inherited tests passed |
| Final focused candidate004 | 116 obligations passed; no failures, errors or skips |
| Final inherited candidate004 | 481 exact inherited tests passed; no exclusions, failures, errors or skips |
| Independent implementation review | Accepted exact production, adapter, frozen inputs and runtime evidence; 2,513 data-only checks |
| Protected source review | 943 protected source identities and 11 pins unchanged |
| Evidence archive review | Every regular payload and all metadata verified across all six attempts |

The held production is 249,393 bytes, SHA256 `71e837c31df06df7ce10262683c5d28a72bdb3c039f09b97eec58839f4121758`. The final fixture freeze is `69065e25738c81ab88cd502edc7069b3b005ba6ae4a67181c30c83f950aa54d5`; the adapter is `92ed832d2f78509cc60185b5bbfd9da0ff563f595561f5a2cc46e5ff515581a7`. Detailed identities and exact commands are linked from [verification](VERIFICATION.json) and the [independent acceptance](independent-review/FINAL-IMPLEMENTATION-ACCEPTANCE.json). The focused suite nests selected inherited tests; those executions are not counted again as distinct tests.

## Failures and recovery

All attempts are preserved in [attempt reconciliation](VERIFICATION-ATTEMPTS.json) and [complete evidence](evidence/ARCHIVE-VERIFICATION.json). The first discovery check refused a declared 372-versus-observed481 inventory before running tests. The first complete baseline passed441/481, with40 setup failures because the inherited mapping suite required an existing retention directory. After correcting the orchestration, the baseline passed481/481. The first focused implementation attempt passed115/116; RI-L08's platform metadata collection hit the process guard before launch. Candidate004 supplies an explicit synthetic recording-only metadata value and checks one call and restoration; production and all116 original oracles stayed unchanged. Both final cohorts then passed.

Early recovery and each applicable frozen candidate were saved and read back before subsequent substantive work or final execution. The evidence archive retains 33,403 regular files, 14,436 directory records, 45 symlink records and three special-fixture records. Nonregular fixtures are metadata, not followed during collection. The archive is 25,817,783 bytes, SHA256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`.

## Boundary and remaining work

Technical acceptance ends this development phase. Source publication and saved delivery remain pending at this source snapshot and are resolved by a later separate receipt. No operational host qualification, H0/H1 execution, original-seven/full routine, Node/ldd/direct-loader/CPU-checker target launch, main integration or parent closure occurred. One inherited driver test uses its bounded inline Python environment-transport child; no global process-count or prior-process termination claim is made. N34 and historical N57 remain external review obligations. Historical C270, P13 and original P28 uncertainties remain explicit.

C271 stays in_progress; R01/R02 are done, R03-R05 not_done, P01 done and P02 in_progress. Issue273 remains open and PR274 draft/open/unmerged. No main integration lease is held.

After confirmed delivery, stop this chat. The first remaining technical action belongs to a fresh phase: prepare and independently review the executable /0.1.5 inspection plan against the adopted finite P27 policy and existing H0 prerequisites, stopping at any new blocker before H0/H1 execution.
