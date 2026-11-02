# C089 recovery and compact-checkpoint disposition

## Observed inputs

The attached Part 1 ZIP was unavailable in this session. Parts 2, 3 and 4 and the transport README were available. The three available segment hashes and outer ZIP CRCs matched the identical transport metadata. An existing complete canonical archive was found independently and matched the exact advertised identity: 1,878,747,004 bytes, SHA-256 `579f8a4024153a540497523de616a13d5d9bedeb26834c52d45a84b0ec79f85e`.

The missing attachment was not read or reconstructed from absent bytes. The existing canonical archive supplied the original complete payload. No Library attachment access was used for this recovery.

## Original full recovery remains failed

The unchanged `c088_handoff.py verify` passed every member's bytes, hash and mode, plus the native metadata and retention pins. Its original `recover` invocation failed in inherited C086/C085 directory verification because that fresh reconstructed directory contained an unexpected extra file. The original top-level and nested failed reports are retained under `evidence/recovery/`; their statuses and helper bytes were not edited. The complete historical transient workspace was not successfully restored by that invocation. The cause of the extra file is not established.

## Separate exact source and native history recovery passed

The existing native object database was observed to match the sealed C088 inventory exactly. A separate read-only export created one non-thin native pack from precisely those object IDs. The export was imported into an independent empty object database, then used to restore a fresh checkout with no checkout filters, hooks, ambient Git configuration or network protocols. The original store, HEAD, refs and worktree remained unchanged.

The [independent receipt](evidence/recovery/independent-source-recovery-passed.json) records the actual passing scope:

- Final source commit `7b6900baa0357ab96c4639ac5c2ebe4e1791833e` and tree `1a31d387795b0b794935b81d9f77803054e82699`.
- All 10,792 tracked files, totaling 669,367,315 bytes, matched exact blob identities, SHA-256 hashes and modes.
- All 10,255 native objects matched their complete ID/type/size inventory; all 205 raw commits and their graph matched.
- The exact ref namespace and both disclosed shallow boundaries were restored. Strict full Git fsck passed.
- The native pack is 440,908,778 bytes, SHA-256 `90687723c1dae942c41d28725fc5e1fe245f130adc50fadd0e712db64a56b8e4`.

This is complete recovery of the captured development source and native history, within the inherited shallow-history limits. It does not reclassify the failed full-workspace recovery or execute product tests.

## One practical next handoff

The new handoff carries that complete base object set once, together with the C089 object delta, complete current source/native manifests, new review evidence and a fresh-destination offline restorer. The source tree, including every tracked historical evidence archive, is reconstructed from its native blobs. A duplicate source ZIP is unnecessary.

The older C088 delivery also carries two whole validation-workspace Git packs totaling 895,281,029 bytes and its 720,699,751-byte nested predecessor ZIP. The new checkpoint does not repeat those transport/workspace containers. Their existing archives and identities remain preserved; omission from the new compact transport does not delete them or change a historical failure. The compact checkpoint is a standalone continuation package for the current source and captured native history, not a byte-for-byte replacement for every earlier transient workspace.

The outer handoff's provenance index identifies the original C088 canonical archive and supplied transport identities if a later historical workspace investigation requires them. Ordinary C090 contract work requires no additional archive or network download after recovering this checkpoint.
