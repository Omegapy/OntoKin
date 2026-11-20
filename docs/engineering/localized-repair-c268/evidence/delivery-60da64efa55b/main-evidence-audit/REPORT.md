# C268 independent post-merge evidence recovery audit

**Verdict: eligible for recovery. No mandatory finding.** The recovered `ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1` commit accurately records the already completed integration and main verification. Its evidence supports R01–R06. R07 remains pending: verify and save the final handoff, publish the separate receipt, close the task and issue, release ownership, and stop. This audit grants no new implementation or milestone scope.

Reviewer: `/root/main_evidence_audit`, separate from the implementation and preceding review workers. I read the assigned governing files, C268 requirements/plan, integration policies, and C260 contract, input pins and control plan. This subtask made no repository/index/ref changes, network calls, dependency installations, cohort executions, or nested worker assignments. The audit command was `python3 -B /workspace/scratch/60da64efa55b/evidence/main-evidence-audit/audit_evidence.py`.

## Inspected identities

| Role | Commit or tree |
| --- | --- |
| Actual merge, supplied by the Director's live readback and independently matched to preserved API readbacks | `5084dd69312e8da5a49aadd33cf83ba56db7c058` |
| Merge tree and final integration-candidate tree | `07971fcdbc6d912febc6adbec7ebf576eccab43f` |
| Final merged branch head | `43115fb864c6f475fb2a56da43566fc1c8b3af50` |
| Corrected implementation and executed candidate | `e6f55b73fa71953aa648bcd34711a6796a7346b6` |
| Accepted evidence publication | `b49a930292752e80abe47cc0526e76413089d64d` |
| Original recovered acceptance commit | `ffb912cce59ccfe7d0d82ab4349de9b12271cc03` |
| Exact shared accepted evidence tree | `10bcebf566d001a850f8e5c5c77eb96857de7e3b` |
| Unpublished recovery child under review | `ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1` |
| Recovery tree | `5fa6a2a2be560255413a692704ec175f4901d4c5` |

`ecce5f18` is a direct child of the actual merge. Its 52 changed paths contain 45 additions and seven current-record modifications. No implementation, test, dependency, fixture, contract, runner or hosted workflow changes occur in that delta. Previously committed evidence is preserved; the only modified existing evidence-path file is the current worker-disposition record. The source checkout remained clean at the same commit throughout this audit.

## Main verification evidence

**All 673 audit assertions passed.** The recorded fresh main run occurred from `2026-11-20T00:29:52.171662+00:00` to `2026-11-20T00:30:54.505503+00:00` on the exact merge. Its receipt records clean before/after source state and stable identities for all 159 explicitly listed input files. I matched every input against that merge's Git blob, and matched all 30 output files—including otherwise ignored logs and ZIPs—against their committed recovery blobs and size/SHA-256 receipts. Both main and candidate output inventories are exact.

| Required group | Methods | Recorded outcome |
| --- | ---: | --- |
| C253 corpus | — | 14 bindings across three tasks passed |
| C255 oracle | 31 | Passed |
| C256 reader | 29 | Passed |
| C257 ownership | 23 | Passed |
| C258 follows | 28 | Passed |
| C261 GLB hinges | 28 | Passed |
| C265 source hinges | 49 | Passed |
| C266 binding | 34 | Passed |
| C267 comparison | 25 | Passed |
| C268 historical endpoint | 35 | Passed |
| Workflow records | — | Passed |
| Documentation preservation/navigation | — | Passed |
| **Total** | **282** | **12 groups; zero failures, errors or skips** |

For each test group, I compared authored test method names obtained by parsing the exact source with every successful method line in the preserved log. The counts do not merely repeat a receipt summary. C266's ledger contains 748 calls: 28 bindings and 720 typed refusals. C267 contains 123 calls: 35 agreements and 88 typed refusals. C268 contains 131 calls: 121 historical and ten raw, with twelve historical admissions, nine raw successes and 110 typed refusals; no untyped exceptions occurred. Every recorded expected/outcome pair agrees.

The original-endpoint controls include both `before` and `after`, each with string and Path repository roots. Their recorded results contain eight hinges and sixteen sites. The executed assertion helper additionally requires one shared joint definition. Admission flags and all retained nonclaims agree with the contract. Successful raw controls retain `historicalInputsBound: false`.

All three input ZIPs have safe, unique paths and valid CRCs. Their 741, 210 and 31 entries total 982. Every entry's bytes are identical between candidate and main runs despite different ZIP container hashes. All 2,697 recorded snapshot references resolve to bytes with the claimed size/hash; frozen source references also match the merge.

The main `CHECKS.json` is **93,825 bytes**, SHA-256 **`b2af5b4c93f39f297f6711ee74a210ca48e44e01becb6454f7b5c8fc10ad6492`**.

## Continuity and acceptance

I verified 48 distinct implementation, test, dependency, fixture, contract and runner paths across the corrected candidate, merge and recovery child. Every accepted-review identity remains equal. The separate accepted reviewer was `/root/review_c268_final`; its R01–R05 disposition is eligible with no unresolved required finding. The complete reviewed artifact manifest, including prior failed attempts, is preserved and matches its hashes.

Candidate and main recorded environments match exactly: CPython 3.12.14, Linux 6.18.57 x86-64/glibc 2.41, runtime bundle `26.1117.11355`, and the same interpreter binary SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`. The present applicable environment also matches. The runner SHA-256 is `9c6c67a2bb1ce9e7a238b53e185f34d25f794ce7a1bb6e17753d7a9c187b3a3a`. Commands and test settings are identical apart from the three explicit output-directory arguments. The eight changed/added receipt input records between candidate and main are task/status/review documentation; main freshly checked that state.

I inspected preserved conditional lease and branch update intents/results, expected-head merge intent/result, premerge head readbacks, and postmerge main/commit/PR/branch readbacks. They support R06. The final branch head is the second merge parent, and the reviewed implementation/evidence are ancestors of main. The observed branch inventory contains only main. This audit does not claim a new live GitHub request; the Director supplied current live observations, while the checked receipts establish the earlier operation history.

## Metadata and remaining work

The full changes to STATUS, README, RESULTS, CURRENT, knowledge, task and worker state are preserved in `METADATA-DELTA.patch`. Their integration counts, bounded capability description, R06 completion, pending delivery, and stop instruction are supported. The C262 historical-handoff record is unchanged. November 19 in the integration heading is consistent with the merge commit's `-07:00` timestamp; execution receipts use November 20 UTC.

The previously uncommitted `post-integration-records` receipt identifies exact clean `ecce5f18` and passing documentation/workflow checks. Its two log hashes match; all three files are copied here unchanged. New owner/phase/delivery-record edits require the applicable fresh documentation/workflow checks. The unchanged observer cohort need not run again. Preserve attribution of its execution to the original merge, even if a later publication uses another commit identity.

My first audit attempt incorrectly normalized only output paths containing `/evidence/`, while the candidate used `/verification/`. The sole failed assertion is preserved in `ATTEMPT-01.json`, with its source and explanation. I corrected only comparison of the explicit `--evidence-dir` values. This was an auditor assumption error, not a cohort failure, and no cohort was rerun. The prior main auditor's separate schema-assumption failure also remains preserved in the recovered evidence.

Full product regression, source conformance/export, other interpreters, native/visual/model trials, hosted execution, complete C260 H groups, site/world behavior, accepted revisions, edit atomicity, rebuild equivalence and comparative benefit remain outside the demonstrated scope. No mandatory blocker prevents recovering the reviewed evidence and completing the existing delivery phase.
