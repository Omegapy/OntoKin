# C061 handoff

## Start here

Read [README](README.md), then [the measured decision](CHECKPOINT-061.md). C061 is complete as a finite diagnostic NO-GO. The independent-reader axial-reuse hypothesis was measured and rejected within its stated scope. No product runtime bytes changed, and no recording became valid.

The executed tooling commit is `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`, tree `037157a58442ba1956597d32e1e540802f9ed896`. It depends on C060 `00533b953ed345cbf5fa13eaa56aafa3a2f052a8` / draft PR #58. C061's branch is `work/reach-reader-setup-20261028-c061`. Publication commits are later evidence/receipt commits; consult [publication.json](publication.json) and the latest Issue #26 release comment before using a branch name as an immutable source identity.

## Actual work and unchanged product state

Exactly four original requests ran: P11 control/capture and L03 control/capture. All exit 1 at the 100,001st attempted shared tick. Both pair audits pass. Two offline negative audits reject deliberately damaged setup evidence for their intended reasons, and both originals are restored exactly. There is no active product process, failed-tail continuation, automatic loop or started C062 worker at this checkpoint.

P11 setup costs 23,171 operations, with zero axial calls. L03 setup costs 17,185, with four axial calls totaling 376. The isolated L03 target cannot fit the unchanged downstream request: the source-derived selected lower bound is 100,218 even after ideal removal of all 376 charges. This bound is conditional on unchanged downstream behavior and does not measure complete request cost or reject other algorithms.

Main remains the independently observed development baseline `b37b39102aea67eb81bd9e38518352403a844e99`. No main integration lease was held or merge attempted. The archive-only branch `archive/pre-consolidation-20261028` remains `e6917dae0be3a786c22e76be3de62e3c97784cf5` and must never be merged. Reconcile live heads before any continuation; these observations are time-bounded evidence, not permanent assertions about the remote.

The historical corpus result is still 24/28, with P11/P16/P23/L03 unresolved; no C061 full-corpus run updates that result. C059 unit/selected-role/visual records remain historical evidence. M1 stays rejected and C035 stays held. Do not relabel retained `unvalidated-reader-input.glb` files as successful exports or use them to pass destination/release gates.

## Recovery and documentation gate

Direct Git transport failed because this executor could not connect to its configured proxy. The repository was recovered using immutable authenticated file/tree/commit reads. Files were written only after exact size and Git-blob verification. The full Git tree was reconstructed against the commit's authoritative tree SHA. The local checkout has explicit omitted index entries and shallow commit history; a clean status is not proof that every tracked file is present.

An initial commit bootstrap used the wrong UTC offset assumption. Recovery reproduced the original `-0600` commit headers and verified the actual commit hash before any execution. An exploratory nonexistent source-path lookup and all unavailable historical archive lookups remain preparation limitations. The scope comment's initial approximate start-time wording was corrected to use the comment's actual creation timestamp; measurement timing comes from actual command receipts.

The immutable execution checkout contains 491 files / 9,527,653 bytes and omits 2,890 entries. Its exact input inventory and every materialized byte are in the archive. The separately recovered documentation checkout initially had 1,271 materialized files at the executed tooling revision. Its first actual documentation check failed with 17 links. All 108 files / 8,842,039 bytes in four omitted historical validation directories were then recovered with exact hashes, resolving the five directory-link failures without placeholders. The twelve missing archive payloads total 74,915,834 bytes and remain unavailable. The final gate receipt records the actual materialized input inventory, command, exit and failures.

Preserve `documentation-before` with its original 17 failures. Do not overwrite it with the later result or describe either failed gate as passed. Do not edit old documentation links, preservation hashes or old archive identities to hide the unavailable bytes. A complete authenticated checkout or another authorized byte-transfer route must recover those same immutable archive objects before the unchanged gate can pass.

LFS future-path configuration does not migrate historical evidence. The old 357-archive / 459,206,837-byte inventory predates C060 and C061 additions and must be regenerated before any migration. No pointer was substituted for an absent payload, no history was rewritten, and no migration or paid/hosted Actions job was run.

## Evidence verification and portability

Run the included standard-library `verify_evidence.py` with this checkpoint directory as its argument. It checks every archive part, reassembles the ZIP in memory, verifies its byte hash and validates every member against the manifest. It does not execute product requests, certify recordings or import OntoKin.

The archive preserves the 491 materialized source files with modes and Git identities; full tracked tree/omission lists; exact raw commit metadata; original commands and absolute execution paths; product outputs including failures; audit outputs; negative probes; command runners and source-recovery helpers; preparation receipts; and independent reviews. Historical paths in the raw receipts intentionally remain unchanged. Replaying the CLI auditor elsewhere requires recreating the named execution paths and exact Git/input identity or a separately reviewed relocation mechanism. The standalone archive verifier needs neither those old absolute paths nor the product runtime.

`publication.json` records the remote payload commit and exact byte readback of every newly published file. A later receipt commit records that result; its own final head/readback is recorded in Issue #26 and the portable handoff. This avoids pretending that a file can contain the hash of the commit that first contains itself.

## Continuation order

1. Reconcile current main, both dependent PR heads, Issue #26 scope/lease comments and queued/in-progress workflows. Verify no previous worker remains active after a timeout. Acquire only the authority required for the next bounded task.
2. Recover the twelve immutable historical archives through a working authorized byte route and rerun the unchanged documentation checker in a complete identified checkout. Keep the prior failures and exact recovery receipts. Do not use empty files or LFS pointers as substitutes.
3. Review C060 before integrating its dependent C061 increment, or explicitly restack and verify the dependency if remote history has changed. A passing evidence audit is not a waived documentation gate or automatic main integration.
4. If continuing performance work, use the separate [C062 proposal](NEXT-TASK.md). Declare its scope and exclusive execution window before any product request. Do not reopen the rejected C061 target without materially new evidence and a new explicit task decision.

The current user requested continuation, so no extra permission prompt was needed for this bounded branch work, evidence publication or draft PR. Any future substantive change must still preserve the repository's semantics, budgets, callback/error order and independent source authority.
