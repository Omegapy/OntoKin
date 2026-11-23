# C271 P28 recovery state review

**Verdict: a narrowly scoped documentary recovery checkpoint is justified, subject to the publication preconditions below. P28 implementation acceptance remains unverified.** The first unmet recovery gate is to obtain and authenticate the exact later P28 candidate, frozen inputs, execution/review evidence and publication intent. The supplied early archive cannot satisfy that gate. If those durable inputs cannot be recovered, record that concrete blocker and deliver an honest partial recovery handoff within P28.

## Observed state and ownership

The supplied live ref observations and current-host Git checkout agree on branch `work/c271-missing-import-digest-control` at `360c80062e769230199602326fa8de25660df714`. Main remains `e43cc6c5777874101a40559e4058ad6826b07e51`. PR274 is open, draft and unmerged; issue273 is open. Its five supplied comments equal its reported comment count.

P27's terminal declarations on PR274/issue273 are identical: comments `7110046284` and `7110052122`. The supplied P27 ZIP is exactly 7,397,736 bytes with SHA-256 `d9fdae71a39f343b1fa14a6eb358f780428a1d05af66e85bd9e4c191abe82a77`. The external receipt recovered inside P28's early archive is exactly 2,872,533 bytes with SHA-256 `614a765b48e90efd1de9b3f5ae102bdf838c834fa8ebcdbc0581baef676c8783`. Both match the terminal declarations. P27's design/delivery completion and ownership release can therefore be reconciled; this resolves only its matching source-time pending fields.

The later identical P28 start comments (`7111339840`, `7111340439`) record owner `c271-p28-4b91a1fab6b4`. No P28 terminal release is present in the supplied live comments. The current Director must record an explicit recovery ownership transition under the current user instruction. Do not represent P27's stale owner field as current ownership or infer the P28 owner's release from elapsed time. Governing STATUS records the main integration lease as released; P28 claims no main lease.

## Requirements and first unmet gate

The branch task and CURRENT files remain at P27's receipt-time snapshot. Their existing pending text is history, not evidence that P27 must be repeated. C271 remains blocked, with R01/R02 done and R03/R04/R05 not_done. Parent P01 is done and P02 in_progress. Preserve these acceptance states, PR/issue disposition and historical failures.

P28's early ZIP is exactly 8,480,098 bytes, SHA-256 `520b24277f2f4a28b5ed96122a477b2438a60905c1a1ae80de39d448426cb15e`, matching its start markers. Its checkpoint explicitly precedes product edits and control execution; the packaged inspector exactly matches the observed P27 branch source. Its `early_save_confirmed: false` is a pre-save snapshot, resolved by the later matching save evidence. It contains neither proof of later implementation completion nor its final publication tree.

The reported 597 passing tests and documentation counts 29/1652/6361 remain an unverified prior-chat report. Do not copy them into verified check rows. P27's 116 obligations were declarative, NOT_RUN, with executable fixture bytes not yet frozen at that predecessor boundary. Reconstructing a new candidate from the design cannot be represented as recovery of the original missing bytes or original results.

## Conditions for a documentary checkpoint

1. Continue P28 on the existing branch with a distinct recovery owner; add the recovery record and preserve all source-time snapshots. No new milestone, implementation, runtime execution or main integration follows.
2. Record the interrupted operation's known target/parent and all missing identities. Keep immutable Git-object upload outcome unknown. An unchanged branch proves only that the observed ref did not advance; it does not prove that uploaded unreferenced objects do not exist or that the old request terminated.
3. Before publication, reconcile fresh ref/ownership observations and use an observed-head, conditional, nonforce descendant update. Review the exact documentation-only delta and read back the actual resulting commit/tree. If the original uncertain operation may include a mutable ref write, reconcile that possibility before publication; this review's allowance assumes the Director's stated boundary of immutable tree uploading before ref update.
4. Run applicable workflow/documentation checks on the exact recovery candidate, preserve any failures, then independently verify and save the handoff and matching prompts. Publish the external receipt and terminal recovery disposition. Delivering recovery documentation completes neither the missing P28 implementation acceptance nor R03-R05.

## Evidence and limits

`AUDIT.json` records 22 passing static state checks and hashes of 34 inspected inputs. All task/CURRENT JSON bytes were parsed; current states and historical reconciliation indexes were inspected. The complete requirements text and all plan differences were reviewed. Historical test claims were not rerun or independently recertified.

The exact branch Git tree contains only root `AGENTS.md`; no nested AGENTS applies to a new documentation path. The saved source manifests are partial inventories and would not establish that absence alone. Governing-main instructions and the three selected skills were read. The failed supplied branch-tree API response is a transport error, not absence evidence. One initial local glob pathspec query failed and was replaced by a successful complete-tree filename inspection.

No source files, existing evidence, Git refs, GitHub records or Library files were changed by this worker. No product tests, host reconstruction or previous-host inspection occurred. This review approves recovery scope and prerequisites; it does not approve a documentary candidate or final archive that has not yet been presented.
