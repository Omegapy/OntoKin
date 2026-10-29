# C063: exact archive recovery and diagnostic integration

## Recovery result

All twelve historical archive objects that blocked C060, C061 and C062 are recovered with their original bytes: **74,915,834 bytes**. The complete C062 source tree is now materialized and verified: **3,458 tracked files, 618,214,168 bytes, zero omissions**. The unchanged documentation checker passes on exact C062 `995ab0a46131a99b12e939b43bfb25e44287f442`, tree `c0b295ff04076db2b585b6b2f78d1025910a25e6`.

The check verifies 29 preserved sources, 233 required sections and 2,096 local links across 296 documents, with zero failures. Its 3,458 input files remained stable. Earlier failed documentation runs retain their original bytes and results. Recovery changed no historical link, preserved source, archive, fixture, runtime file or workflow.

Read [the recovery record](recovery.json), [complete source identities](source-manifest.json), [native checkout receipt](native-checkout.json), [documentation result](checks/documentation.stdout) and [actual command](checks/documentation-command.json). [RECOVERY.md](RECOVERY.md) explains the successful byte route and its limits. Failed transfer records remain in [the transfer ledger](recovery/transfers.jsonl).

## Diagnostic stack review

C060, C061 and C062 cumulatively add 131 paths and modify only the preexisting `docs/README.md`; they delete no path. All 65 product runtime files and both hosted workflow files retain their original blobs and modes. The workflows remain manual-only with default-false opt-in. Standalone diagnostic tools are executable additions, with retained actual diagnostic, independent-audit and negative-control evidence; they are not wired into released product routes.

[The independent review](reviews/integration-review.md) identifies the applicable development gates and path-sensitive historical auditors. [The integrity check](diagnostic-integrity.json) verifies all 603 C060 archive members and all 609 C061 archive members, their ordered parts and whole archive hashes. These checks preserve prior executions; they do not rerun the original requests or silently rebind historical absolute paths.

The [fresh C062 calculation](checks/calculation-command.json) passes and its [stdout](checks/calculation.stdout) equals the historical ledger byte for byte. It uses the standard library and imports no OntoKin module.

## Verified development integration

All four pull requests are merged into main, in dependency order. The unchanged documentation checker passed after **each** merge, with stable complete source inputs. [The integration record](integration.json) binds every actual commit/tree, command and result.

| Increment | Pull request | Actual main merge |
| --- | --- | --- |
| C060 diagnostic tooling and evidence | #58 | `203703cc5fedac58ebe0235e474c6504f7fafe7a` |
| C061 reader-setup diagnostic evidence | #59 | `18a212d794e5aed64f9056a07dadc257cf3fcb3b` |
| C062 source-only ancestry decision | #60 | `371716fca642829595e977fde824382678d7b3d4` |
| C063 archive recovery and checks | #61 | `da69c1d16fcfdb1c257e17edb9e12961d07d204f` |

Each merged tree equals its reviewed candidate except for the separately acquired main integration lease in `STATUS.md`. All diagnostic, runtime, fixture and workflow inputs retain their exact identities. GitHub deleted the four merged work branches automatically; their heads remain parents of the recorded merges. The unchanged historical archive branch and main are the two observed remaining branch names.

This updated record and current STATUS are a final documentation receipt increment after the four merges. Its actual publication identity and final resulting-main check are recorded in the portable handoff and subsequent Issue #26 release. [HANDOFF-063.md](HANDOFF-063.md) provides continuation instructions; [NEXT-TASK.md](NEXT-TASK.md) defines the next bounded objective.

Recovery first produced a native checkout with its shallow history boundary at the exact original C062 commit. Resulting-main checks use separately verified original commit/tree objects; the portable snapshot does not include full Git history. The archive-only retention branch remains outside development and all merge paths.

## Product limits retained

C063 executes no product request, product suite, Agent/SQLite workflow or hosted job. Historical original28 remains **24/28, failed**, with **P11, P16, P23 and L03 unresolved**. M1 remains rejected, C035 held, and the full reach release obligations remain open. No resource limit, original input, numerical result, oracle, tolerance, default route or capability claim changes. Git LFS migration is still separate and unfinished. The complete [OntoKin goal](../../../GOAL.md) remains in progress.
