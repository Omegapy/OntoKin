# P19 scope and canonical-preservation review

Reviewer: `/root/ledger_review`  
Verdict: **No mandatory scope conflict found. Scope is accepted; operational invocation is not approved by this review.**

## Basis and limits

This review reuses the complete 14-file readset in `READSET.json` and the conclusions in `REPORT.md`. It adds complete reads of `state/PHASE.json`, `state/EARLY-RECOVERY-RECEIPT.json`, and `technical/OBSERVATION-PLAN.json`. The Director reports confirmed P18 terminal delivery/live PR and issue reconciliation and a 37-group accepted P19 early package with actual saved-byte readback. I inspected only the first 100 lines of `recovery_audit/P18-RECONCILIATION.json`; I did not repeat its full archive/receipt audit.

The following hashes identify the snapshots reviewed here:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `state/PHASE.json` | 6985 | `910afa3a22add102b9978693e64c761b2e52de7816176471bc65940ccefe8a44` |
| `state/EARLY-RECOVERY-RECEIPT.json` | 1135 | `43ff32a126271633199f24ba2fa5a22e49cace07cbe9d83682c8aeed678534b2` |
| `technical/OBSERVATION-PLAN.json` | 2050 | `3de3cfc09ebac9d34df0115b472427bdfc14af75906f4a521dc568498213bdd2` |
| `recovery_audit/P18-RECONCILIATION.json` | 224348 | `b62d954b0f1d7ea554755c59e52d3a4903018639ce5ce89088a899991b51ba12` |

The observation script is assigned to `/root/operational_review` for separate pre-execution review. This worker did not inspect or invoke it. The observation plan's selected production-file hash matches the P18 implementation hash in the fully read ledger; that comparison does not itself prove the file on disk matches its declaration.

## Scope decision

The P19 declaration matches P18's recorded next action: review exact current inputs and the adopted profile for H0, then stop at the first new blocker or the H0 boundary. It correctly excludes H1, target launches, Node/ldd/direct-loader commands, probes/checkers, installation, full routine, production/test changes, substitutions, main integration and parent closure. N57 remains an independent external review obligation.

The observation plan is narrower than H0 acceptance. It is explicitly a raw actual-input review, with no child processes, a first-refusal/mismatch stop and no retry. It requires an independent exact script/source/lock review before the single invocation. These constraints fit the selected phase. A successful metadata observation would still require the complete applicable H0 input/closure/plan review. Package name/version readiness alone is not complete distribution inventory or proof of later provider lookup.

The source-time P18 ban on H0 applied to P18. A fresh authorized P19 review can select H0 inputs. Conversely, broader historical P09 preparer allowances are not inherited: the current P19 declaration expressly excludes installation.

### Documentary correction before publication

`state/PHASE.json` has one stale capability description: `capabilities.library_save` says the early phase save is still required, while `early_save_confirmed`, P19-A01 and the embedded receipt confirm it. Replace that capability description with the observed early-save/readback result before publishing the canonical phase record. This is a record-consistency finding, not a scope or technical-execution blocker.

## Canonical preservation checklist

1. **Keep the parent acceptance unchanged.** C271 remains `blocked`; R01/R02 `done`; R03–R05 `not_done`; parent P01 `done` and P02 `in_progress`. PR274 remains draft/open/unmerged, issue273 open, branch retained, merge null and no main lease. A completed P19 partial phase is not parent completion.

2. **Preserve P18 through an exact immutable reference.** Referencing its prior `session_phase` at `2f791017c6559bfd47937b32b1862cfe98a81551` is acceptable; the task already uses an exact-revision reference for P13. Identify the exact file/object and source revision. Add P19's P18 reconciliation reference beside it. Do not rewrite the frozen P18 record or copy hundreds of kilobytes solely to restate history. Only matching pending delivery/publication fields are superseded by later terminal evidence.

3. **Separate old observations from new observations.** Retain P15's actual tag refusal and the fact that its later flags predicate was unreached. Retain P18's synthetic/inert implementation acceptance and absence of actual-host reassessment. Attribute any P19 result to its exact source, profile, inputs, command and environment. Append a newly identified blocker or admission result; do not rewrite earlier failed or unrun evidence.

4. **Do not overstate H0 or N57.** One passing reader call, successful raw observation, package readiness check or loader-source review cannot qualify all H0 inputs. H0 acceptance needs the complete applicable independently reviewed operational plan and externally bound digest. N57 is never included in runtime pass/skip totals. H1 and full routine remain unrun by this phase.

5. **Update current pointers without altering historical ledgers.** Replace current owner/phase/next action with P19 and preserve the former P18 object by exact reference. Keep the active/latest task C271 on the branch; main's completed C270 pointer remains unchanged. Use real UTC observation timestamps and the validator's allowed CURRENT next-action status. Keep the existing licensing/packaging integration caveat.

6. **Keep scope and execution evidence exact.** Record whether a refusal occurred before subsequent checks, which calls actually ran, and which remained unrun. A first concrete blocker is a valid bounded phase outcome; it does not permit a repair or a second technical phase. Preserve the approved procedure, later exact outcome, all failures and unique reviewer files. Production/test/pin/default/budget changes would require stopping this declared scope.

7. **Keep delivery stages distinct.** P19 early recovery is confirmed as 1,165,706 bytes, SHA-256 `b28206da5005d6e794fb1f2fb6c7f252bc9ea8ae22e677f8d61eee66ff79a904`, version 0, before technical work. P18 remains the latest saved final handoff until a P19 final handoff is actually saved. The final P19 ZIP and matching prompts require verification, exact saved-byte confirmation and a separate actual receipt. Source-time `save_pending` is legitimate; inventing future receipt/commit identities is not.

8. **Preserve actual worker/operation status.** Record the new workers and their real dispositions. Keep current unknown operations separate from historical C270 driver completion, global prior-process termination and P13 difflib uncertainty. Do not claim global termination from the absence of a current job, or retry the diagnosed unsupported publication method.

## Next review

When the Director supplies the final five changed records and exact outcome, review only those changed bytes and their required evidence. Reuse unchanged governing/ledger read hashes. Confirm field agreement, first-refusal meaning, preservation of parent gates, valid evidence paths and truthful next action. Workflow/documentation check execution and operational script acceptance remain separately attributed to their actual owners.

No canonical file, product source or test was changed. No test, host inspection, product invocation, Git operation, publication or nested worker was performed for this review.
