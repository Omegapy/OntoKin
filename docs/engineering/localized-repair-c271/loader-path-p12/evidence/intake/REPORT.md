# Independent P12 intake review

**Verdict: accepted for the new early recovery gate, followed by the bounded P12 implementation.** There are no unresolved intake findings. P11 is complete as a design/control phase with verified partial delivery. Parent C271 remains blocked and incomplete.

Reviewer: `/root/intake_review`. Review scope: exact P11 archive, supplied terminal receipt, preserved live service observations, authentic Git objects, task state, recovery boundary and selected next phase. This review does not accept implementation or actual host behavior.

## Exact inputs and source identities

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `input/OntoKin_C271_P11_Loader_Path_Handoff_2026-11-21.zip` | 5,606,509 | `4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e` |
| `receipts-input/OntoKin/OntoKin_C271_P11_Delivery_Receipt_2026-11-21.json` | 8,723,877 | `55d46239b1950b032a7fa9496b37e49a638b0d8162497b74be9aa29b9c208fd8` |
| Accepted candidate004 manifest | 35,041 | `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de` |
| P11 payload manifest | 380,166 | `20a782c8d571d1cf87e2718cf07a9cf282d3a4eee5425dda2718ac01a59e99c5` |

The frozen archive source is `e7508fb23c64563549631a1be46a3523593e2d9f`, tree `06c7db644326a5e03bffe8ad53ea4fa0004e7065`. The terminal receipt binds `79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae`, tree `c3aed39729812e3c2abf2a4a4332d75052c4f19d`. The authentic checkout initially had that terminal head and a clean working tree. Observed main is `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`, tree `9345594c980f121fae2f087b40e4c78adb8f7925`.

The frozen source is an ancestor of the terminal commit. Every one of the receipt's 55 repository delta paths matches the actual Git transition, including before/after contents, modes, blob identities and sizes. Both embedded Git commit objects match their actual object bytes and Git object identities.

## What was verified

The executable audit completed **32 passing check groups**, with no failures. `AUDIT.json` records commands, environment, input hashes, exact findings and limits. `SOURCE-CHECKS.json` records each snapshot's source identity and result.

The ZIP has 1,626 unique safe ordinary-file entries, including the manifest. All 1,625 listed payload byte counts and SHA-256 hashes match; inventory is exact; required root files are present; ZIP integrity passes. The supplied extraction matches every archive entry and contains no extra file. All transport modes are inert `0644`.

All 800 frozen source snapshots match actual Git blobs, recorded paths, modes, revisions and trees. The terminal receipt's 83 compressed blobs decode to their declared sizes and SHA-256 identities. Every one of its 11,422 postfreeze recovery rows resolves to an exact embedded blob, frozen payload member, frozen recovery identity or the exact archive identity. These reference checks preserve external dependencies as external; they do not assert that every historical byte was materialized locally.

The accepted corpus has 97 expected records. All 93 original records remain identical. All 942 entries in the protected-source baseline still have their recorded Git blob identities at the terminal source. The accepted decision retains the existing 16 MiB document reader and records withdrawal of the separate 4 MiB proposal.

## Why P11 delivery is complete

`CHECKPOINT.json`, branch `P11-DELIVERY.json`, task state and `CURRENT.json` are earlier source-time records. They correctly say that terminal delivery confirmation is pending. The terminal receipt itself was frozen before its own save and correctly makes no self-save claim.

The later matching P11 section in both current PR274 and issue273 explicitly confirms all four saved artifacts and terminal readback at `2026-11-22T00:21:11.290292+00:00`. The two P11 sections are identical. They bind the exact receipt hash, archive hash, source and terminal revisions. Their service responses are preserved in `session_p12/startup/pr274.json` and `issue273.json`; the exact P11 section is retained here as `PUBLIC-P11-CONFIRMATION.md`.

The current saved-file listing identifies the terminal receipt as file `file_00000000905c81f7aa094310513be026`, Library file `libfile_fde3_f-6c84b3949d548191ab5c978242124e7d_2ab2a24d43748191957f9bcc356b59de`, version `0`, 8,723,877 bytes. The freshly supplied readback hashes to the exact identity in that public confirmation. The listing response and downloaded bytes were obtained by the Director; this reviewer independently verified their preserved responses and exact bytes.

This evidence supersedes only the matching P11 delivery-pending fields. It does not rewrite frozen evidence, close parent acceptance, or imply that P11 executed product tests. PR274 remains draft, open and unmerged; issue273 remains open.

## Preservation and recovery limits

The P11 recovery map has 8,118 rows: 813 embedded and 7,305 externally recoverable aliases. All embedded rows bind verified archive bytes. All external rows have valid exact dependency locators. Their distribution is 6,990 P10-archive aliases, 204 P11-early-recovery aliases and 111 P10-terminal-receipt aliases.

Of the 813 embedded rows, 532 record original mode `0600` and 281 record `0644`. Their ZIP transport mode remains `0644`. The receipt's authenticated supplemental procedure requires private copying and recorded-mode restoration before consuming recovered fixtures. Its text hash matches `c2ba5026577a11710891dcbb16c040b8cd4748b11a458ae85c37c53f404b52b4`. This intake did not restore modes or execute recovered files. The subsequent candidate materialization must follow both `GIT-TRANSPORT.md` and candidate004 `MATERIALIZATION.md`.

P10, its terminal receipt, P09, the selected inert Python image, and historical C262 remain explicit external dependencies. Their existence as locators is not a fresh full-archive download or complete offline-restoration proof. Ordinary online continuation does not require reconstructing the whole historical collection.

Known failed and withdrawn attempts remain represented by frozen payloads, Git history, receipt blobs or explicit external references. The supplemental mode procedure preserves the original failed package audit instead of changing its claim. The intake's own truncated preliminary displays and corrected read-only `KeyError: body` are recorded in `AUDIT.json`; the cause was the issue response nesting its body under `structuredContent.issue`, with no repository write or product execution.

The current receipt and new phase record list no known pending operation. Historical C270 broad-driver completion and global prior-process termination remain unestablished. An empty current-operation list does not prove all historical processes stopped.

## Remaining gates and next action

R01 and R02 remain done. R03, R04 and R05 remain `not_done`; P02 remains `in_progress`. H0 is unaccepted, H1 is unapproved, actual loader variant completeness and real sibling-library inventory remain unestablished, and the full routine remains required. This audit grants no main lease or integration acceptance.

`session_p12/PHASE.json` selects exactly one phase: `C271-P12-loader-path-implementation`. Its owned production surface is `prototypes/static_tray_v01/current_host_inspection_v01.py`; its new test surface is `tests/test_current_host_loader_path_v01.py`. It requires all 97 immutable controls, all 175 existing inspection/mapping methods, independent exact-source review, branch publication verification and verified partial delivery. It preserves the stated no-runtime/no-integration exclusions and stops before H0 re-establishment or any second phase.

**First required action:** independently verify, save and exactly read back the new P12 early recovery ZIP. Only after that gate passes may implementation start on the selected surface. If that surface cannot express the accepted decision, preserve the concrete blocker and stop with a verified partial handoff.

No OntoKin import, product behavior, host preparation, H0/H1, Node/ldd, runtime installation, original-seven/full-routine run, main lease, integration or parent closure was performed by this reviewer. Repository files, index, refs, canonical records, Library and PRs were not changed.
