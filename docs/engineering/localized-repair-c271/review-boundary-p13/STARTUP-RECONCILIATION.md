# C271 P13 independent startup reconciliation

Reviewer: `/root/intake_review` in the current P13 session. Scope: independently reconcile the prior P12 handoff and delivery boundary before the Director selects and releases one design clarification phase. This is startup verification, not acceptance of any new design.

## Verdict

**Accepted for startup reconciliation.** The exact P12 final ZIP, separate terminal receipt, supplied continuation prompt, live repository core delivery record, authenticated commit objects and retained GitHub terminal confirmations agree. Source-time pending fields are historical. They do not leave a P12 delivery-only gate open for these exact bytes.

The audit passed 56 check groups with no failed group. One explicitly external historical byte check was not run: 70 aliases requiring the older P12 early archive. The archive and receipt declare that dependency; full historical restoration is outside this assignment. No new P13 early recovery or design has been accepted by this review.

## Exact identities

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| P12 final handoff ZIP | 2,075,115 | `337f8fd00f91987c6a70ba91a9439a5da29bc91a81507d4a92d2d9bc17cbb323` |
| P12 separate terminal receipt | 3,949,967 | `577f58d70355c7658e6b70bec9b175a87e633dfa4756db4f9bbce121b071c512` |
| Supplied Continue prompt | 5,223 | `18a638004be6cb4a935e4e3049e517ea7832d5e32d32fb6ad83777ebd916e3e8` |
| Archived Recover prompt | 5,757 | `048b145380663743d6d81ab755b6cd3eb833d2ef80495039640e928ef8ea8467` |

Frozen ZIP source: `09e04b394194b7a21dc203dd7bba2e548ca1c168`, tree `ae7a01657b6f545640eba2b7e30e5800dacda37f`.

Terminal repository checkpoint and inspected checkout: `ef127e60e461dd24d73a40d5fd5b7bfe1cde79fb`, tree `0727d39bf37c6c951478affac3a5506104d8eea7`. Its raw commit object directly names the frozen ZIP source as its parent. The source and terminal commits are distinct as required: the immutable ZIP cannot contain its future save receipt.

Observed main: `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`, tree `9345594c980f121fae2f087b40e4c78adb8f7925`. The inspected working tree was clean. Retained PR 274 data names the same branch/head and main/base; the PR is draft, open and unmerged. Issue 273 is open.

The saved terminal receipt identity is `libfile_fde3_f-c9d08c730a5c8191aade52c0aac641a9_2ab2a24d43748191957f9bcc356b59de`, backing file `file_00000000855c81f5a93671eda54c70ae`, version 0. The final ZIP identity is `libfile_fde3_f-09b2accb4c888191905fc46853b65d7a_2ab2a24d43748191957f9bcc356b59de`, backing file `file_00000000897c81f58cad16de814d541f`, version 0.

## Delivery reconciliation

The terminal receipt's `core_delivery` object equals the parsed live `loader-path-p12/P12-DELIVERY.json` exactly. Its archive and prompt records match the actual downloaded ZIP and supplied prompt. Both archived prompts match their receipt sizes and hashes. The supplied Continue prompt is byte-for-byte identical to `PROMPT-1-CONTINUE.md`.

The retained PR and issue each contain exactly one P12 terminal-confirmation marker. Their terminal text is identical and records confirmation at `2026-11-22T01:08:20.667802+00:00`. It binds the exact final archive, both prompts, terminal receipt, frozen source commit/tree and terminal checkpoint/tree. The relevant Library response includes all four files with matching identities, names, paths, byte counts and version 0. Its pagination cursor is nonempty; this review claims only the four observed relevant records, not a complete Library inventory.

Consequently, `delivery_confirmation_pending`, `not_yet_saved_at_this_source_snapshot`, and the terminal receipt's own `status_at_freeze: not_yet_saved` are reconciled by the later exact confirmation. They do not authorize a duplicate save or package rebuild. P12's correct disposition is `complete_partial_delivery`; technical completion and parent completion remain false.

## Archive, source and recovery checks

The ZIP has 399 unique safe relative regular-file members, all with inert `0644` transport modes. CRC checks passed. Its manifest lists exactly the other 398 payloads, and every listed size and SHA-256 matches. Required root documents are present.

All 316 source snapshots match their recorded sizes, SHA-256, Git blob identities, source path, Git mode, source commit and tree. The source commit and P11 baseline were initially absent from the shallow checkout. The Director fetched those exact objects; the final audit compares the snapshots to the authenticated source tree.

The archive records 825 recovery rows. All 755 aliases to included bytes match; the remaining 70 explicitly reference the historical P12 early archive. The terminal receipt records 1,271 post-freeze rows: all 45 inline gzip/base64 blobs and all 1,201 rows available from the receipt/current ZIP pass their size and SHA-256 checks. Seventy other rows require the same external early archive and were not downloaded or restored. The rejected first ZIP is present as a verified inline blob, 1,840,636 bytes, SHA-256 `cb7fdb60de7e116c9d89ccb0aead793fef1bdfc38cdb927f8c8477a123040ea7`.

No recovery payload was executed or restored. This is an online continuation check with explicit dependencies, not proof of full offline restoration.

## Protected source and frozen controls

All 942 tracked files under `ontokin`, `prototypes`, `tests`, `tools`, and `.github` match the retained protected-source blob map, authenticated P11 baseline tree and terminal tree. Every corresponding current working file hashes to the same Git blob. The new focused loader-path product test is absent.

Candidate004's manifest remains SHA-256 `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. All 146 declared candidate payloads and 29 supporting artifacts retain exact bytes. One candidate payload, `REVISION-004.diff`, is not a Git-checkout file; its exact 38,093 bytes are retained in the final ZIP recovery map and pass the manifest hash. This is an explicit transport location, not missing evidence. Original private fixture modes were not materialized; the review makes no claim that Git's ordinary checkout permissions equal their authored `0600` modes.

The fixture and expectation inventories contain the same 97 case IDs, covering 131 fixture files. These are static artifact checks. The 97 product controls and 175 inherited inspection/mapping methods were not executed.

## Scope established by the blocker

P12's blocker is `P12-N57-POLICY-BINDING-001`. Independently comparing the frozen P01 and N57 JSON confirms exactly one difference: `/variant_review/completeness` is `synthetic_declared_complete` in P01 and `unsupported` in N57. Removing only that field makes the logical contexts identical. N57's frozen expected refusal remains `CHI-UNSUPPORTED`, stage `variant_review`, rule `LP-VARIANT-SEMANTICS`.

Candidate004's operational variant object has exactly `schema`, `loader`, `source_review`, and `suffixes`. Its decision assigns completeness to independent source review and says that no field constitutes approval. The existing private-rule control contract explicitly distinguishes synthetic contexts from operational plans. The P12 adjudication therefore identifies a missing adopted binding from a source-review result to production admission, not a failed product execution.

The authorized next phase is one separately versioned design clarification: define a genuine source-bound admission predicate with faithful controls, or explicitly classify completeness as an independent-review-only gate. The original 97 expected outcomes and historical candidates/failures must remain unchanged. This startup review chooses neither design option and accepts no P13 candidate.

The Director must confirm a new early recovery before substantial clarification work, then obtain independent design/control review and verified partial delivery. The phase stops there or at its first concrete blocker. Production/test implementation, product imports, H0/H1, runtime preparation/installations, Node/ldd, the original seven/full routine, native/model/hosted execution, main lease, integration and parent closure remain outside scope.

## Current state and known unknowns

C271 remains blocked and open. R01/R02 remain done; R03/R04/R05 remain `not_done`. The work branch is retained. The current worker has no active process, unknown write, publication or child worker. No canonical repository, index, reference or shared record was changed by this reviewer.

Historical C270 broad-driver completion remains unknown. Global prior-process termination remains unestablished. Empty returned hosted-status observations do not establish CI acceptance. These limitations remain explicit in the prior receipt and are not closed by this review.

## Review procedure and retained corrections

The full applicable `AGENTS.md`, `ROLE.md`, `docs/workflow/PROTOCOL.md`, `docs/workflow/HANDOFF.md`, `docs/workflow/templates/WORKER.md`, and `.agents/skills/ontokin-delivery/SKILL.md` were read. No nested AGENTS file was found in the relevant repository directories. Global startup, external operations and delivery remain Director-owned.

The verifier uses only Python standard-library parsing, hashing and archive inspection plus read-only Git commands. It imports no project module. Its exact command, interpreter/platform, input hashes, per-payload and per-snapshot checks, protected-file rows and read-only Git results are in `AUDIT.json`.

Early broad discovery/JSON display returned truncated tool text. Required governing prose was re-read fully, and verification consumes the complete files rather than truncated tool output. Three verifier attempts are retained. Attempt001 stopped on shallow `merge-base` behavior; the final check inspects the direct parent in the authenticated commit object. Attempt002 stopped because it assumed `REVISION-004.diff` was a checkout file; the final check verifies the exact preserved ZIP bytes. Attempt003 incorrectly treated explicitly external recovery aliases as required local bytes; its audit is retained and the final audit marks that historical byte check not run. These were review-tool scope/transport mistakes, not changed package bytes or product failures.

The Director can inspect `AUDIT.json`, this report and `verify_intake.py`. The next action for this worker is to wait for the separately assigned P13 early-package or final-package review.
