# P08 delivery reconciliation

**Verdict: P08 partial delivery is complete. C271 remains in progress.** No prior-delivery blocker was found.

The original ZIP matches **14,680,844 bytes** and SHA-256 `037d7ff2b2b64f61f1b53b5fdae93b3d16a32bdb6fd681f45f824e2652d425b5`. Fresh extraction verified 4,370 safe unique entries, 4,369 payload hashes, 281 source byte/Git-blob identities and 4,075 mapped recovery files. Both standalone prompts exactly match their ZIP members. All 179 compressed terminal-receipt evidence files decoded with matching sizes and hashes.

The terminal receipt matches **2,062,098 bytes** and SHA-256 `e5a7017a847992a25dbd9f65b19dd32ca730578d56406b44e0f4beff68592114`. Fresh Director-provided PR #274 and issue #273 current blocks confirm its saved identity and all four saved-byte comparisons. The authentic checkout's canonical receipt and corrected CURRENT bytes match the receipt's embedded evidence.

## Freeze and correction boundary

Accepted code is `cf16a0facebdce2fadf69e5c7fae6f2ca31cbd2e`; the immutable archive source is `3ed2670bf9bf4326dab126d3466699053f6b4320`. Its `save_pending` fields correctly precede the later receipt. First receipt commit `be159c31db3ef26f66adbcb641e326e2b6ebc198` failed the explicit UTC timestamp check. Correction head `2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e` changes only the existing CURRENT timestamp field and adds retained correction evidence. The failed check remains preserved; later exact-receipt checks passed. The archive and accepted production/test bytes are unchanged.

Main remains `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. Branch `work/c271-missing-import-digest-control` remains retained at the correction head; PR #274 is draft/open with no merge date, and issue #273 is open. R01/R02 are done; R03–R05 are not done. This is phase delivery, without main integration or parent completion.

## Remaining uncertainty and next action

Historical **C270 broad-driver completion remains unknown**, and **global prior-process termination remains unestablished**. No current unresolved P08 operation is reported at its terminal boundary. Earlier run001, rejected package, helper failures, receipt timestamp failure, P02 routine failures and P03/P04 runtime refusals remain evidence, not erased outcomes.

After the Director confirms new early recovery, the first technical H0 action is to authenticate the retained P05 Node and unchanged C195 dependency archives and independently freeze exact archive/member inventories and task-specific destination/absence guards. H0 may then use the existing preparer as selected, statically inspect actual source/Python/ldd/loader inputs, and obtain independent review of the exact executable inspection plan with a separate digest. **Stop before H1 Node/ldd execution or actual host observation.** Input availability and closure are not established by this startup audit.

## Audit limits and preserved audit correction

No Git command, product test, Node/ldd command, dependency installation, GitHub mutation or worker spawn occurred. Live readbacks came from the Director. Local source hashes do not independently prove historical commit/tree membership; the package retains that earlier verification. Inner fixture stores were not restored or executed.

The initial verifier's sole failed group assumed every source snapshot was below `repository/`; two intentional `observed-main/` snapshots also belong to the source manifest. `VERIFICATION.json` and its verifier remain unchanged. `AUDIT.json` records the corrected exact inventory, which passes. The connector-materialized CURRENT has one extra trailing newline; parsed content agrees, and byte checks use the authentic checkout.

Detailed evidence: `AUDIT.json`, `VERIFICATION.json`, `POSTFREEZE-INVENTORY.json`, and captured PR/issue current sections. The reviewer owns only this audit directory and stops here.
