# C268 surviving-work recovery audit

Investigator: `/root/recover_c268`. Director: `c268-final-ee457d84062e`.
Scope: read-only recovery investigation of the two prior workspaces. This worker
made no repository, index, ref, lease, commit, remote or Library changes. All output
is beneath `/workspace/scratch/ee457d84062e/recovery-audit/`. No child workers or
product tests were launched. Governing reads are identified in `READ-SET.json`.

## Decision

**Resume published candidate `b799b7462bdc6a04464a2f903cec8dcabd659fa1`.
No implementation or test recovery patch is needed.** All 79 staged files in the
second workspace match that commit at the same path, byte for byte. Of 71 changed
or untracked files in the first workspace, 69 match the candidate; the other two
are earlier coordination/task records already recoverable from a saved binary
patch. Preserve those historical records without applying them over newer state.

The first unmet acceptance gate remains P03/R05: a complete affected cohort on the
corrected immutable candidate and a final independent review. The recovered
281-method cohort belongs to the earlier reader. The fixed reader has a recovered
35-method C268 run, but no completed fixed-candidate full cohort or final review
verdict survived. A complete fresh runner requires `--c268-methods 35` and should
report **282 methods**. The Director owns the current scope and any integration or
delivery decisions.

## Exact Git identities and worktree state

| Observation | Identity or result |
| --- | --- |
| Director-supplied current main | `409ef18e0cb992ad1ab771c1258e989d5ef1c765` |
| Director-supplied published C268 head | `b799b7462bdc6a04464a2f903cec8dcabd659fa1` |
| Published candidate tree | `466d9711a2560c49f6fd0ef00189ebc67eb1d316` |
| Candidate parent; both prior local HEADs | `734789521f82248d39b623c33aae9d3284ab4bce` |
| Parent tree | `23aa5e900cede54b9ff2ff7b14cbfb2e440547d0` |
| Main/candidate shared ancestor | `4595bade65291f36900be3e648c733aea74d5c40` |
| Divergence from shared ancestor | Main: 8 commits / 74 changed paths; candidate: 3 commits / 113 changed paths |
| Overlapping changed paths | None; this path comparison is not merge verification |
| First prior workspace | `/workspace/scratch/c7dae94da130/OntoKin`: 53 staged files, 18 untracked files, no unstaged or ignored files |
| Second prior workspace | `/workspace/scratch/8bd47a4cbab7/OntoKin`: 79 staged files, no untracked, unstaged or ignored files |
| Original validation checkout | `/workspace/scratch/c7dae94da130/validate-candidate`: clean, including ignored files, at the parent commit/tree above |

`HEAD-COMPARISON.json` retains the exact path sets. Remote heads were supplied by
the Director; this audit read their immutable local Git objects and did not make
a fresh remote request.

The first workspace's two different records are:

| Path below its OntoKin root | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/engineering/localized-repair-c268/COORDINATION.json` | 2,088 | `d1b882aa39f5e9158b3cc15b83ef21ad41da88deb55f19e62180133932333021` |
| `docs/workflow/tasks/C268/task.json` | 8,430 | `445b54381bbf7255e15fbfdf295d86cae52e537b5f447863a0e32e26d4bf2338` |

Both are listed in the saved unpublished-work inventory. Its `STAGED.patch`
exactly equals a fresh read-only `git diff --cached --binary --full-index HEAD`
from the untouched first workspace. Saved patch SHA-256:
`f96a8894d840055402e720aea6795753bd57ee24abd9d36aa9fb1230757a2be6`.

## Evidence and findings recovered

The separate original reviewer recorded a mandatory R02 resource-bound defect:
an oversized endpoint string reached dictionary membership before length
validation. The published candidate contains the one-condition correction and an
independent regression test that forbids lookup and filesystem access for the
oversized selector. The old failure, old reader snapshot and old probe remain in
the published evidence.

| Evidence | Exact coverage and limit |
| --- | --- |
| Published `evidence/candidate/CHECKS.json` | Original 12 groups / 281 methods / 14 C253 bindings passed on `73478952…`; it does not qualify the corrected reader |
| Published `evidence/control-author/run-04/results.json` | Corrected working bytes: 35 C268 methods / 131 calls, zero failures/errors/skips; 12 historical admissions, 9 raw successes, 110 typed refusals |
| Earlier external `review-evidence/REVIEW-PROGRESS.md` | Substantive R01–R04 inspection; explicitly an unfinished checkpoint with no final acceptance verdict |
| Earlier external `review-evidence/review_fixed_candidate.py` | Prepared eight focused checks; no execution result survived |
| Earlier external `cohort-evidence/recovered-candidate-audit/VERIFICATION.md` | Integrity audit of the original evidence; explicitly no new cohort execution |
| Earlier external `cohort-evidence/recovered-candidate-audit/INITIAL-AUDIT.json` | Preserved failed equality audit caused by later reconstructed source changes; not a product-test failure |
| Earlier external `cohort-evidence/candidate-01.START.json` | Preparation receipt only; planned fresh cohort did not start |

The fixed reader is 14,914 bytes, SHA-256
`a7bb1f67398a54922e647d6d43062f89acb32c6e05a2fc653f5c30160f888157`.
The fixed test is 52,981 bytes, SHA-256
`d7c426870348ab9e0976d46ee64b8624eb39c3e0b2f84a2159d2a91f66bf46c9`.
The 12-error first control-author run, initial workflow failures and immutable
whitespace-bearing failed log remain preserved under their original identities.

This recovery audit checks byte availability and provenance. It does not replace
the independent implementation review or claim product, physics, native,
compatibility, full H-group, source-validity or comparative qualification.

## Uncertain operations and current process observation

The prior publication receipt identifies intended parent `73478952…`, tree
`466d9711…` and created commit `b799b746…`. They exactly match the candidate supplied
by the Director. The receipt contains the pre-update ref observation but no
post-update ref receipt; the Director's live branch observation resolves that
publication outcome. There is no reason to replay its commit/ref operation.

Current `/proc` inspection found no process whose working directory or explicit
path arguments referred to either prior workspace; there were no read errors.
This establishes only the local observation. It cannot prove historical worker,
hosted-job or remote-operation termination. No unknown local operation was found;
no process was interrupted or killed. Historical worker labels such as “active”
are stale evidence, not evidence of present liveness.

The published task and recovery phase still describe the prior P03-only stopping
point. The current Director must reconcile that historical plan with current user
authorization before changing task state. P04 integration, actual-main checks,
branch disposition, P05 delivery and parent closure are not established here.

## Exact inventory and minimal carry-forward

`INVENTORY.json` records 870 source files with absolute path, size, SHA-256,
Git blob identity, base/candidate identities and byte-equality results. The initial
preservation pass found 96 distinct byte blobs absent from the two current trees.
`CLASSIFICATION.json` then checked retained history and five saved archives:

| Classification | Unique blobs | Bytes | Final treatment |
| --- | ---: | ---: | --- |
| Retained Git history | 10 | 52,778 | Use the exact historical commit/path mappings |
| Already in saved archives | 47 | 13,219,434 | Use exact archive IDs, hashes and member/patch mappings |
| No retained/saved exact copy found | 39 | 1,169,267 | Include `FINAL-CARRY-FORWARD.zip` |

The 39 remaining files are historical workflow scripts, raw audit/API responses,
publication payload/receipts, original audit text variants and save-verification
receipts. No missing implementation/test bytes remain. The final payload preserves
each original path in its manifest and deduplicates content by SHA-256. Historical
scripts are evidence; they are not instructions to execute or replay operations.

`FINAL-CARRY-FORWARD.zip`: **256,639 bytes**, SHA-256
`ee5322fc8c32780f525b37f503b13200c6d1492ba9c50d2a74ddeff1ed680352`.
All member CRCs, sizes and SHA-256 values were verified. The two external review
and cohort directories, including the failed audit, already match members of the
Director's newly saved 3,373,522-byte recovery ZIP, SHA-256
`222ae9b2c63c80ca6bcb25e097cb2039c614ea0ff132fbfe209a7d65b169fed6`,
Library ID `libfile_fde3_f-376bce2516408191b9e55b3e7ce0b701_2ab2a24d43748191957f9bcc356b59de`.

For the final handoff, include this report, `INVENTORY.json`, `CLASSIFICATION.json`,
`HEAD-COMPARISON.json`, `READ-SET.json`, `CARRY-FORWARD-VERIFICATION.json` and
`FINAL-CARRY-FORWARD.zip`. The two small audit scripts may be included as procedure
evidence. The raw `unpublished-bytes/`, redundant `patches/`, and
`HISTORICAL-OBJECTS.txt` need not be copied again.

The first strict historical-object traversal failed because the current clone
lacks historical blob `ed8323336dff3a18abe4d47b58aa535182367632`. The subsequent
`--missing=print` traversal completed and reported 2,106 locally missing objects.
Every blob classified as retained history also has an explicit known
commit/path mapping. This audit does not claim a full offline Git restoration;
the online repository and saved archives remain its recovery sources.

## Next action

The Director can continue from `b799b746…` without replaying recovered patches.
Run the corrected complete affected cohort and obtain an exact-candidate final
independent review, preserve all old outcomes, then handle the authorized
integration and saved-delivery gates. No second milestone is selected by this
worker.
