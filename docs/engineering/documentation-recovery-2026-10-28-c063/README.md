# C063: exact archive recovery and diagnostic integration

## Recovery result

All twelve historical archive objects that blocked C060, C061 and C062 are recovered with their original bytes: **74,915,834 bytes**. The complete C062 source tree is now materialized and verified: **3,458 tracked files, 618,214,168 bytes, zero omissions**. The unchanged documentation checker passes on exact C062 `995ab0a46131a99b12e939b43bfb25e44287f442`, tree `c0b295ff04076db2b585b6b2f78d1025910a25e6`.

The check verifies 29 preserved sources, 233 required sections and 2,096 local links across 296 documents, with zero failures. Its 3,458 input files remained stable. Earlier failed documentation runs retain their original bytes and results. Recovery changed no historical link, preserved source, archive, fixture, runtime file or workflow.

Read [the recovery record](recovery.json), [complete source identities](source-manifest.json), [native checkout receipt](native-checkout.json), [documentation result](checks/documentation.stdout) and [actual command](checks/documentation-command.json). [RECOVERY.md](RECOVERY.md) explains the successful byte route and its limits. Failed transfer records remain in [the transfer ledger](recovery/transfers.jsonl).

## Diagnostic stack review

C060, C061 and C062 cumulatively add 131 paths and modify only the preexisting `docs/README.md`; they delete no path. All 65 product runtime files and both hosted workflow files retain their original blobs and modes. The workflows remain manual-only with default-false opt-in. Standalone diagnostic tools are executable additions, with retained actual diagnostic, independent-audit and negative-control evidence; they are not wired into released product routes.

[The independent review](reviews/integration-review.md) identifies the applicable development gates and path-sensitive historical auditors. [The integrity check](diagnostic-integrity.json) verifies all 603 C060 archive members and all 609 C061 archive members, their ordered parts and whole archive hashes. These checks preserve prior executions; they do not rerun the original requests or silently rebind historical absolute paths.

The [fresh C062 calculation](checks/calculation-command.json) passes and its [stdout](checks/calculation.stdout) equals the historical ledger byte for byte. It uses the standard library and imports no OntoKin module.

## Integration boundary

This first C063 publication records the completed recovery and review prerequisites. Main integration remains pending until a fresh expected-head lease is acquired. The sequence is C060 PR #58, C061 PR #59, C062 PR #60, then this recovery record, with live dependency reconciliation and resulting-main checks. Actual resulting commits and final status will be recorded separately; this paragraph is not a merge claim.

The complete source checkout has shallow Git history at the exact original C062 commit. It is not a full history clone. The archive-only retention branch remains outside development and all merge paths.

## Product limits retained

C063 executes no product request, product suite, Agent/SQLite workflow or hosted job. Historical original28 remains **24/28, failed**, with **P11, P16, P23 and L03 unresolved**. M1 remains rejected, C035 held, and the full reach release obligations remain open. No resource limit, original input, numerical result, oracle, tolerance, default route or capability claim changes. Git LFS migration is still separate and unfinished. The complete [OntoKin goal](../../../GOAL.md) remains in progress.
