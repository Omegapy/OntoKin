# C271 P02 independent acceptance review

**Verdict: NOT ELIGIBLE for integration or parent-task closure.** The affected regression cohort passed in full, but the required routine driver failed. Its unit-test process timed out and its documentation process failed because the isolated copy omitted five tracked files. Preserve the draft branch and open parent, record R03 as unmet, and deliver the saved partial handoff. This review neither starts a repair phase nor waives a requirement.

Reviewer: `/root/intake_audit`. Review date: 2026-11-20 UTC. Scope: independent source/evidence inspection and acceptance decision. No project behavior was executed by this reviewer. Only this review directory was written.

## Reviewed identities and authority

| Role | Commit | Tree |
|---|---|---|
| Observed main | `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d` | `9345594c980f121fae2f087b40e4c78adb8f7925` |
| P01 execution | `067392f2b5f592a5c3104fa8848cc0030ba1117b` | `21ab07914931495d6bee70591a70ff2d8bcabb84` |
| Tested candidate | `88bc8b51b3963b7072375edac6400b6e6a4532e4` | `755f366d1091beb71b5421b14fdac0b9b868cfb0` |
| P02 phase checkpoint | `2a85f71489fea57dc165cde61e3f7cc67a8ae999` | `219962df4639a0c1de0fdbbe708ac3adf5a0b6b6` |
| Published affected evidence | `15b1dd985b59cf037ebbeae733c16a54ca87f83d` | `5e3e6a54a64f91a49e124bac7f11e6c73c024129` |

The user authorized one bounded phase with early recovery, preserved failures, final saved ZIP, and stop. The early recovery receipt records a confirmed save before execution at 2026-11-20T22:49:10.172349+00:00. Source and package identities were separately checked during intake. The earlier intake report remains authoritative for its 2,286 passing checks; those are not included in the review totals below.

Applicable sources are the repository's AGENTS, GOAL, ROLE, workflow PROTOCOL/HANDOFF, selected delivery/learning skills, C271 P02 session/requirements/plan, OK-ENG-006 and OK-ENG-009. Their exact read identities are in `READ-SET.json` and the referenced intake read set. At the reviewed checkpoint, `docs/workflow/tasks/C271/task.json` declares the routine driver required. `tools/chat_workflow.py` requires every required check to pass before a task can be done. Successful affected tests cannot satisfy a separate failed mandatory check.

Prepared blocked-state working records are covered by the bounded addendum below. Their later published revision and the final saved handoff still require separate exact verification. Root alone owns publishing, integration, saving, and final delivery.

## Mandatory findings

### C271-P02-RV-001 — complete unit-test outcome unavailable

The required routine driver executed from the clean candidate with `python3 -B tools/check_local.py --output-dir …/routine-candidate --timeout 900`. Its unit command was `python3 -B -m unittest discover -s tests -v`. The process exceeded the declared 900-second limit, returned `-15`, and ended after 900.025 seconds. The log has no unittest completion footer. Thus the driver reports failure and the complete unit-suite result is unknown.

The `test_execution.tests_run=0` field is a footer-parser result, not evidence that no tests executed. Independent accounting found 3,370 strict single-line method `ok` records and 60 additional unittest docstring continuation lines ending in `... ok`. These are partial log counts, not a completed-suite result. No actual assertion-failure, error, or skipped result line was observed before termination. The last unfinished logged method is `ReachSamplingScalarReuseTests.test_p16_prefix_keeps_the_complete_original_glb`; this does not establish that method as defective or identify the cause of total run time.

Evidence: `../validation/routine-candidate/logs/unit-tests.log` (655,857 bytes; SHA-256 `727232296a766d1af6edae14343966fa15e8b3389ea04e1efb44e6652cbe78d7`), final summary/receipt, and `UNIT-TIMEOUT-INSPECTION.json`. No timeout retry or behavioral diagnosis was performed.

### C271-P02-RV-002 — documentation check fails in isolated source copy

The routine documentation process returned 1. All 21 reported failures are local links to five tracked files that exist in the authentic candidate but are absent in the copied workspace:

| Omitted target | Why it is excluded |
|---|---|
| `CHATGPT-START-HERE.md` | Not in driver `ROOT_FILES` |
| `ROLE.md` | Not in driver `ROOT_FILES` |
| `.agents/skills/ontokin-session/SKILL.md` | `.agents` not in driver `SOURCE_DIRS` |
| `.agents/skills/ontokin-delivery/SKILL.md` | `.agents` not in driver `SOURCE_DIRS` |
| `.agents/skills/ontokin-learning/SKILL.md` | `.agents` not in driver `SOURCE_DIRS` |

Independent parsing resolved all 21 link destinations to this exact set. The initial `summary.workspace_git.tracked_worktree_status` already lists these five deletions. Therefore the omissions preceded test execution; they are not evidence of later timeout damage. AST inspection confirms the two copy inventories exclude the targets. The copied referring documents and documentation verifier exactly match the authentic candidate. Their bytes, the five target files, and the driver are identical at main, tested candidate, and published affected-evidence checkpoint. The driver Git blob is `18c56cb58824474f848044ff859c36004364f6fd`.

The direct documentation check passed on the authentic candidate in the affected cohort and on both clean metadata checkpoints. These observations establish why direct and isolated documentation outcomes differ. Static main equality is not a baseline behavioral run and does not waive the failed driver gate. No files were added to the failed copy and no check was rerun.

Evidence: `ROUTINE-EVIDENCE-REVIEW.json` includes every failure, target, copy constant, initial deletion, and exact source identity. The original log is `../validation/routine-candidate/logs/documents.log` (SHA-256 `1534a47da2777a4797d4039f650764eb2e82e193bdb7ee12a6d74ee9c3e683e8`).

## Completed validation and source preservation

The two original authorized processes positively completed. No active or unknown current validation operation remains. The routine outer receipt reports exit 1 after 1,039.836432 seconds; the driver records 1,039.574 seconds for its own interval. Both duration definitions are preserved.

| Routine step | Process result | Meaning and limits |
|---|---|---|
| Unit tests | Failed, `-15` | 900-second timeout; no completion footer |
| Source | Passed, 0 | 43 cases, 694 assertions |
| Agent | Passed, 0 | 10 cases |
| Construction | Passed, 0 | 19 passed; C20 independent visual-delivery gate pending |
| Surface | Passed, 0 | 1 passed; 11 external-evidence cases pending; `--allow-pending` |
| Impulse | Passed, 0 | 8 passed; 4 external-evidence cases pending; `--allow-pending` |
| Documents | Failed, 1 | 21 links to five omitted files |

A process pass does not complete its pending external or release roles. All seven planned processes have final results; none were silently omitted. All referenced logs/reports and outer stdout/stderr identities were independently verified. The authentic checkout remained clean at the exact candidate commit/tree. The driver's 18,659-file declared source inventory is byte-identical before and after. Its inventory excludes the same five files by construction; separate full Git identities and initial copy status preserve that limitation.

### Affected regression cohort passed in full

The retained C268 runner was executed once from the candidate with phase `C271-P02-integration` and `--c268-methods 35`. It returned 0 after 67.468424 seconds. All 12 checks passed: nine suites containing 282 methods, the 14-file/three-task corpus binding check, workflow structure, and documentation. There were zero test failures, errors, or skips.

| Suite | Methods |
|---|---:|
| C255 oracle | 31 |
| C256 reader | 29 |
| C257 ownership | 23 |
| C258 follows | 28 |
| C261 hinge GLB | 28 |
| C265 source hinges | 49 |
| C266 binding | 34 |
| C267 comparison | 25 |
| C268 endpoint | 35 |

The reviewer independently derived the method inventory from source AST and matched every method exactly once to its successful verbose-log record. All 161 input identities and 30 output-file identities were checked. Retained call accounting is C266: 748 calls (28 bound, 720 typed refusals); C267: 123 (35 agreements, 88 typed refusals); C268: 131 (12 admitted, nine raw successes, 110 typed refusals), with zero untyped exceptions.

Evidence: `REGRESSION-INVENTORY-REVIEW.json`, `AFFECTED-EVIDENCE-REVIEW.json`, and `../validation/affected-candidate/CHECKS.json` (SHA-256 `100fbe9a686f51e0b281d313a15cf786f372924db4b37562b8c21de111150c35`). The metadata changes to CURRENT require fresh record checks; those were separately verified at both 2a85f714 and 15b1dd98. Behavioral input identity remains unchanged through those checkpoints.

## Historical P01 evidence reuse

Historical finite P01 control evidence is reusable at the reviewed candidate/checkpoints. This is reuse of the identified original execution, not a new execution claim. All 22 recorded runtime-opened repository inputs, 11 frozen control/runner files, five dynamic observer/utility modules, contracts/grammar, and fixture source/GLB bytes remain exact from P01 execution through candidate and phase checkpoint. All 1,124 recorded preparation reuse entries also match the phase checkpoint. The later four-file checkpoint only adds evidence.

The original six requests match the independent oracle. Its 18 responses contain six successful positive outcomes and 12 `MALFORMED` refusals. The original 1,042 assertion records pass. The four negative source mutations delete only the specified contiguous digest material; companion inputs remain exact. Neither runtime behavior nor the control definition was changed. The cumulative main-to-candidate delta contains 59 C271 evidence/control/task/CURRENT files; preexisting runtime, observer, contract, grammar, test, dependency, and hosted-workflow bytes are unchanged.

The exact original `-B` command is retained in its execution receipt. Recorded interpreter version/build/path and platform match the present environment: CPython 3.12.14, Clang 22.1.3, Linux 6.18.57 x86_64/glibc 2.41. The original P01 record has no executable-binary digest, so exact Python binary equivalence is not asserted. Static inspection of recorded executed modules found standard-library dependencies only. Scope remains the finite C271 controls, not all imports or full H22/C260 acceptance.

Evidence: `P01-REUSE-IDENTITIES.json`, `STATIC-REVIEW.json`, `CHANGED-FILES-REVIEW.json`, and the original control `EXECUTION-RECEIPT.json`/raw evidence archive.

## Preparation limits remain unresolved

- Installed `rpds-py` is 2026.6.3, while the unchanged lock requires 2026.5.1. The other six recorded packages match. The available-environment execution is not an exact-lock certification.
- The historical dependency directory and host-inventory file required by three C199 `ReadbackCPUControls` methods are absent. These methods were not reached before timeout. Their anticipated skips must not be recorded as observed skips or removed from future accounting. They are synthetic controls for an unqualified prototype, not native qualification.
- Git LFS is 3.6.1; the conditional minimum is 3.8.1 where LFS paths are selected. No LFS archive path was selected in this phase, so this is a conditional preparation limit rather than the cause of either executed failure.

Exact paths, package pins, executable digest, runtime and fixture predicates remain in `../validation/preparation/ENVIRONMENT.json` and the retained preparation records. No dependency, test, source, fixture, or gate was altered to work around them.

## Evidence preservation and review accounting

The final validation archive is `../validation/RAW-EVIDENCE.zip`: **4,965,080 bytes**, SHA-256 **`c4c973d40c4f6571def93b257877de69568bcd5fdca43bcfed92ff6acfc61e20`**. Independent verification passed for all **73 payload files plus one manifest**, totaling 20,322,760 payload bytes. Every payload equals the manifest and retained original. Paths are safe, names unique, CRC valid, and inventory exact. The external verification and final RESULTS remain outside the self-excluding manifest. Copied source/Git metadata are excluded with exact source identities; the worker's 18,659-file recovery comparison records zero unique changes. Originals remain available.

The separately published affected-evidence ZIP has 33 payloads plus manifest, 1,868,775 bytes, SHA-256 `196278f75b4bc268c45517d455ba42d0c6c4b78353199296b07f0ba7712f9d75`. All payloads and the published Git tree were verified. Its summary receipt is intentionally distinct from the original execution receipt, which remains exact inside the archive.

| Independent inspection | Passing checks |
|---|---:|
| Static candidate/control/reuse | 1,343 |
| Actual affected evidence | 259 |
| Clean phase records | 6 |
| Clean affected checkpoint records | 6 |
| Published affected evidence | 73 |
| Final routine evidence and copy diagnosis | 93 |
| Final raw validation archive | 157 |
| Prepared blocked working records | 46 |
| **Total final evidence-verification checks** | **1,983** |

These inspection checks verify evidence; they do not turn the failed routine driver into a pass. The final inspection reports have zero failed predicates. Three earlier reviewer checker assumptions and their first outputs are preserved in `REVIEW-ATTEMPTS.json` and `ATTEMPT-01-*`; corrected checks did not change reviewed bytes or rerun behavior. The failed quoted-glob read, root's invalid CURRENT enum attempt, validator's prelaunch identity assertion mistake, failed credentialless CLI push, and unpublished equivalent local commit also remain in their respective original records. The earlier incomplete historical run is not reclassified by this phase.

## First remaining action and stopping boundary

At the next authorized bounded validation-recovery phase, start from this preserved failed evidence and the unchanged tested candidate. Prepare the exact pinned dependencies and exact historical readback inputs. Correct the routine driver's copy/inventory coverage for the current root startup files and skill directory, with focused validation-tool coverage proving that the isolated workspace is complete. Investigate the preserved timeout boundary and use an evidence-based adequate execution budget for a complete routine run; the current log does not justify blaming a particular product test. Preserve the existing 100,000-operation/30,000-ms per-source limits. Do not delete the old failure, silently skip required tests, or change a required gate.

Then execute the complete required routine driver with truthful completion and skip accounting, inspect every result, and obtain independent acceptance review before R04 integration. Reuse completed P01 and affected-cohort evidence only after checking the exact implementation, test, dependency, input, command and relevant runtime identities; rerun only the evidence invalidated by an actual change. Any validation-tool change needs its own applicable validation and a new phase record.

The current phase stops at the concrete blocker. This review approves preserving and delivering the partial state; it does **not** approve integration, parent closure, repair work, H22/C260 acceptance, release certification, compatibility certification, hosted CI, native qualification, or a new model trial. Root's final saved handoff and later metadata require their own exact verification.

Proposed learning for root to triage: isolated validation inventories must evolve with adopted startup/navigation files; a clean source checkout does not imply that a separately copied validation workspace is complete. The review makes no canonical learning-file edit.

## Addendum: prepared blocked working records

Root requested a bounded review before publication. At parent `15b1dd985b59cf037ebbeae733c16a54ca87f83d`, the prepared task/CURRENT/plan/requirements/session, PHASE-OUTCOME, scoped learning note, copied validation files, and preflight records passed **46 inspection predicates**. Exact reviewed working-file byte counts and SHA-256 values are in `BLOCKED-WORKING-RECORD-REVIEW.json`.

The task and CURRENT correctly mark C271 blocked/open. R01/R02 remain done; R03–R05 remain not_done; P01 is done and P02 remains in_progress. Required-check declarations and requirement acceptance text remain unchanged. The failed routine gate stays required/failed; the affected cohort is passed with the observed counts. The historical independent check is explicitly limited to P01, and neither parent closure nor integration is asserted. The original prior-phase/delivery records are retained exactly. The draft PR, issue, branch, absence of a main lease, and pending partial save are recorded consistently. All eight newly copied validator evidence files equal their originals. The appendices retain prior text and add the actual two-failure boundary. The learning note is confined to the observed omission and absence of a completed unit result.

The working workflow/documentation preflight logs match their recorded hashes and both exit 0. Their receipt explicitly defers exact clean-published candidate checks. It identifies the parent and logs, but does not independently bind every working source byte; this is not a substitute for those later checks.

Root has declared three pending finalization edits: materialize this review directory with its original filenames, correct PHASE-OUTCOME's provisional `FINAL-REPORT.md` link to `independent-review/REPORT.md`, and add a separate required P02 integration-review check with result failed/eligibility false. These intentions are consistent with the verdict; their final bytes have not yet been observed. Root should retain explicit pinned-package and missing historical readback-input preparation in the next-phase instructions. No repair or test rerun is authorized by this addendum. Published-source and final saved-archive verification remain separate next review assignments.
