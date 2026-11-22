# Independent final package review — C271 P11

## Disposition

**Accepted for the exact save, subject to the separate terminal-receipt supplement described below.** The final ZIP has no unresolved byte, inventory, source-identity or recovery gap. The original permissions are preserved as authenticated metadata and can be restored exactly in a fresh private evidence tree. Ordinary ZIP extraction alone does not restore those original permissions.

This is acceptance of the design-and-inert-controls handoff. It is not a completed-save claim, product-test result, host qualification, H0/H1 acceptance, parent-task completion or integration approval. Root must still save and read back the exact reviewed bytes, issue the separate receipt and stop this bounded phase.

## Exact checked identities

| Item | Bytes | SHA-256 or exact Git identity |
| --- | ---: | --- |
| Final ZIP | 5,606,509 | `4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e` |
| Continue prompt | 5,673 | `0d0b6bbf3d5e0cdbd550f8777d37b54cea3db339e9b121bfbb5461e46b966237` |
| Recover prompt | 5,899 | `9cae6e7f92ab216cbae6e917152e58a9ad4fb261ecaff70190f5d85509e3bbda` |
| Published source commit | — | `e7508fb23c64563549631a1be46a3523593e2d9f` |
| Published source tree | — | `06c7db644326a5e03bffe8ad53ea4fa0004e7065` |
| Observed main commit | — | `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d` |
| Accepted candidate004 manifest | 35,041 | `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de` |
| Required receipt restoration procedure | 3,044 | `c2ba5026577a11710891dcbb16c040b8cd4748b11a458ae85c37c53f404b52b4` |

The immutable package freeze is `2026-11-21T23:59:58.438218+00:00`. Both adjacent standalone prompts equal their corresponding ZIP members. All checks were against these frozen bytes, not evolving author outputs. Detailed records are in `CHECKS-RUN001.json`, `FP12-ADJUDICATION.json`, `RESTORATION-CHECKS.json` and `REVIEW.json`.

## Package and source checks

The complete inventory has 1,626 safe, unique ZIP entries and 1,625 hashed payloads. CRC, size and SHA-256 checks passed after fresh extraction. All 800 source snapshots match the exact declared Git objects, paths, tree and modes. Required root recovery documents, instructions, task/specification material and the complete P11 source subtree are present. The 22 protected source files retain their required byte identities. `GIT-WORKTREE.patch` is empty, consistent with the clean published source.

The recovery map contains 8,118 exact records: 813 embedded files and 7,305 aliases to authenticated prior sources. Full inventory coverage includes all 608 author-history files, 43 design-review files and 18 transport-review files present at freeze. The review explicitly checked original failed attempts, withdrawn candidate003 and its 148 payloads/12 supporting files, support scripts, source observations, phase declarations, early receipt, publication evidence, ordinary whitespace-check failure, subsequent transport review and current independent design review. Unique prefreeze session work is covered. Later review and publication observations belong in the separate receipt.

Authenticated prior intake and early-archive identities were reused. The P10 archive, terminal receipt and P11 early archive retain exact locators and identities. P09's selected Python image remains an explicit external dependency with its exact member and digest; it was not newly retrieved or executed. C262 remains an inherited external historical dependency. This is an online continuation handoff, not a complete offline repository backup. `COVERAGE-RUN001.json` records inventory scope and the observed late files.

## Permission finding and correction

The first review completed with 26 of 27 groups passing. FP12 wrongly treated original recovery permission metadata as the ZIP transport permission. All 532 reported differences were the same dimension: an original file recorded as `0600` was transported as inert regular `0644`. No byte/hash/source mismatch accompanied these differences. The other 281 embedded files are recorded as `0644`.

The package explicitly distinguishes transport from evidence metadata. `RECOVERY-STATUS.md` states that original modes are evidence and ZIP payloads are inert regular files. `README-START-HERE.md` points to the separately preserved physical modes. Candidate004 `MATERIALIZATION.md` requires new private copies with recorded modes, exact bytes and hashes before control consumption, including supporting/prior-candidate artifacts. None of these documents claims that automatic unzip restores original private modes.

There is a documentation limit: the root instructions do not spell out the generic restoration procedure for every recovery-map row. The separate receipt must therefore carry the concrete supplemental procedure identified above. This clarifies application of existing authenticated metadata; it does not change the fixture oracle, operational runtime pin, artifact hashes or any guard. Acceptance does not waive the permission requirement.

The independent follow-up created a fresh owned private tree and restored all 813 embedded rows with exclusive creation, no link following, exact byte count/hash, ordinary single-link file type and authenticated original mode. **All 834 follow-up checks passed.** The result is 532 files at `0600` and 281 at `0644`; all original files and the initial raw extraction remain unchanged. Nine externally deduplicated zero-byte supporting logs were separately recovered through their exact authenticated P10 archive alias. The full candidate004 manifest, 146 payloads and 29 supports then passed size/hash/mode checks. All 110 terminal-receipt aliases were also decoded through the actual `encoding`, `bytes`, `payload` schema and verified.

One failed follow-up is retained. RUN002 restored all 813 embedded files, then the helper attempted to read an external zero-byte support alias from the embedded-only tree. RUN003 resolved the declared alias and passed. `ATTEMPTS.json` records both failed helper assumptions and all script/log identities. `mode_restored/`, `mode_restored_run003/` and `fresh_extract/` remain available as distinct evidence; original results were not rewritten to appear successful.

## Design, transport and continuation consistency

The package preserves the accepted candidate004, its 97 inert controls, 131 fixture files and 26 inert ELF images. It retains the established 16 MiB document-reader policy; the unneeded separate 4 MiB proposal and its two controls are withdrawn. All 93 original expected records remain unchanged. Author checks (1,149), independent artifact checks (1,675) and transport checks (52) are correctly described as static artifact/review evidence, not product tests.

The three Git-transport mappings decode from two closed base64 envelopes to exact original raw bytes. Both intentional-whitespace diff files and the failed whitespace-check output remain recoverable from original embedded evidence as well as the lossless envelopes. No whitespace guard is disabled, no control expectation is changed, and the original ordinary check failure is preserved.

The checkpoint, phase, required roots and prompts agree on the clean published source and completed technical work. The recorded next unmet action is final package review, exact save/readback, separate receipt and stop. Both prompts require a matching terminal receipt before treating delivery as complete. They do not authorize implementation in this phase. A subsequent bounded implementation phase remains conditional on a new declaration and early recovery.

The roster and task state do not conceal active implementation work. Draft PR274 and issue273 remain open, the branch remains unfinished and retained, main is not integrated, and the parent requirements remain blocked. There are no claims of Node/ldd execution, H0/H1 acceptance, the original seven/full routine, product behavior or integration. Historical uncertain observations are retained separately from current worker dispositions.

## Mandatory terminal receipt

Root may save the exact accepted ZIP and prompts now. Before declaring delivery complete, the separate receipt must include the saved destination/version/byte-readback identities; this final review with every failed attempt; builder diagnostics and late evidence; and the complete `RECOVERY-MODE-RESTORATION.md` procedure at the listed digest.

That procedure must remain explicit: authenticate the archive and map; create a fresh private `0700` destination outside source/runtime paths; recover each embedded or authenticated external row; exclusively create an ordinary file without links or overwriting; apply its recorded `source_mode`; and verify size/hash/type/single-link/mode before consumption. Treat `original_path` only as historical evidence. Do not chmod originals, repository files, operational Python pins or runtime paths. Do not execute restored artifacts. Mark external rows that have not been materialized as external rather than claiming their restoration.

The receipt must distinguish the 813 restored embedded rows from the nine additionally restored external support aliases and the wider set of 7,305 externally recoverable aliases. It must include final worker dispositions and any postfreeze source/publication/readback observations. Nothing in this review permits a new implementation phase in this chat.

## Limits and completion state

No Library write or saved-byte readback was performed by this reviewer. No live GitHub API reread, product import, author-validator execution, runtime/host probe, target execution, Git/index mutation or Library mutation occurred. Read-only local Git identity checks and independent artifact scripts were used. No reviewer process remains running and there is no uncertain reviewer operation.

The immutable ZIP is accepted for exact delivery with the mandatory receipt clarification. Root's save/readback and receipt are still pending at this review's completion.
