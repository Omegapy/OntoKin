# Reviews while the candidate was still changing

What independent readers found before the candidate was frozen, and what was done about
each finding. None of these is the review of the exact candidate (TASK-032, REQ-040); that
review has its own record.

| Review | Reviewer | Examined | Result |
| --- | --- | --- | --- |
| Lock and provenance (TASK-010) | Independent reviewer subagent, fresh context | Lock `b1e3e866…`, provenance `cbcc1b27…` | Accepted, no finding: [LOCK-REVIEW](LOCK-REVIEW.md) |
| Documents and records | Independent reviewer subagent, fresh context, read-only | Commit `c6835c4d` | 7 mandatory, 6 minor, 2 notes |
| Tools and tests | Independent reviewer subagent, fresh context, no change to the checkout | Commit `c6835c4d` | 13 mandatory, 11 minor, 3 notes; 39 of 90 hand-written mutants survived |
| Rehearsal of "Continue" | Independent subagent, fresh context, read-only | Commit `1d974e4a` | Right account and next action; 27 findings |
| Second review of the tools and tests | Independent reviewer subagent, fresh context, no change to the checkout | Commit `7d937e26` | 6 mandatory, 13 minor, 7 notes; 28 of 54 mutations survived |
| Audit of all 42 requirements | Independent auditor subagent, fresh context, read-only | Commit `7d937e26` | 111 criteria: 78 met, 21 complete with later steps, 12 wait for the owner, none not met; 1 mandatory, 10 minor findings, 9 notes |

Every reviewer was a separate agent of the same model family, inherited from the session,
and wrote none of the work. The rehearsal is no fresh-session demonstration (DEC-010), and
the early audit is not the audit of TASK-031. "Fixed" means changed on this branch and, for
code, covered by a test. The commits are `3c4694f9` and `ebcfee8c` (first tool review),
`02797bb0` (documents), `27ede8cf` and `7d937e26` (rehearsal), and the later commits whose
messages name the second tool review and the audit.

## Documents and records

| ID | Severity | Finding, in short | Disposition |
| --- | --- | --- | --- |
| F1 | Mandatory | The ledger's next action, step states and blockers were older than the work | Fixed; the ledger is updated with each step |
| F2 | Mandatory | The reach of a mode marker was undefined, so hosted-CI rules could be read as browser-only | Fixed in AGENTS and PROTOCOL; CI rules carry no marker |
| F3 | Mandatory | Browser handoff rules in HANDOFF also bound local sessions | Fixed |
| F4 | Mandatory | No outcome when the recorded mode does not fit the session; a local session could overwrite a `browser` record | Fixed: report and ask; record a mode only where none is named |
| F5 | Mandatory | The prompt sent the owner to a checkout without the branch's records; startup missed other worktrees | Fixed in LOCAL-PROMPTS and startup step 1 |
| F6 | Mandatory | A per-user temporary path was committed in ENVIRONMENT.json | Fixed; the doctor labels the temporary directory and the record was generated again |
| F7 | Mandatory | C271's driver change was described as inventory additions only | Fixed in RECONCILIATION |
| F8 | Minor | OK-ENG-006 lost "outside the checkout" for browser preparation; two local rules were unmarked | Fixed |
| F9 | Minor | knowledge.json named only the assistant workspace | Fixed |
| F10 | Minor | Effective date against the task's own mode | Fixed in DECISION |
| F11 | Minor | CLAUDE.md routed by location | Fixed |
| F12 | Minor | STATUS omitted the pending external cases | Fixed |
| F13 | Minor | SCHEMA-MAPPING named one of two new fields; `new-task` wrote no mode | Fixed; `new-task --mode` |
| F14 | Note | Number of skill links; a citation | RECONCILIATION fixed. HOST-INVENTORY is left as the observation it was |
| F15 | Note | WORKER has no mode field; session fields for both modes are unmarked; one command in neither list | LOCAL-SETUP fixed. The other two are left: unmarked fields bind both modes, and an assignment's constraints carry mode and worktree |

## Tools and tests

| ID | Severity | Finding, in short | Disposition |
| --- | --- | --- | --- |
| F1 | Mandatory | A checkout path with a space was taken for a copied environment | Fixed |
| F2 | Mandatory | A foreign `.pth`, symlinked site-packages or a missing creation record still counted as isolated | Fixed |
| F3 | Mandatory | Duplicate package metadata and pip remnants were read differently from pip | Fixed; duplicates are a mismatch |
| F4 | Mandatory | An empty or foreign `ontokin` counted as the source package | Fixed |
| F5 | Mandatory | In a partial clone the offline doctor fetched objects | Fixed with `GIT_NO_LAZY_FETCH` |
| F6 | Mandatory | A failed Git observation was reported as clean | Fixed; unread values are reported as unread |
| F7 | Mandatory | Commits on a detached head were not counted | Fixed |
| F8 | Mandatory | Only direct npm packages were compared; a linked directory counted as ready | Fixed; the whole lock for the platform |
| F9 | Mandatory | Some users of an environment or of Node dependencies were not seen | Fixed; a use that cannot be excluded refuses. A real run then showed false positives, fixed in `ebcfee8c` |
| F10 | Mandatory | `--repair-node` followed a linked dependency directory | Fixed; refused |
| F11 | Mandatory | Setup looped when pip was missing or an import was broken | Fixed; explicit rebuild |
| F12 | Mandatory | A failed removal, an interruption or an unwritable place lost the report | Fixed; set aside first, report always |
| F13 | Mandatory | CURRENT schema 2 accepted embedded receipts | Fixed; closed list of fields |
| F14 | Minor | `new-task` obeyed another repository named in the environment | Fixed; the branch is recorded |
| F15 | Minor | Registry and CURRENT could have different schemas | Fixed |
| F16 | Minor | A mode without an active task passed | Fixed |
| F17 | Minor | Malformed modes ended in tracebacks | Fixed |
| F18 | Minor | `holds` and `unfinished` were not cross-checked | Fixed |
| F19 | Minor | Errors of lsof or ps counted as unused | Fixed |
| F20 | Minor | The setup lock could be lost or not held by children | Fixed; in the Git directory, passed to children |
| F21 | Minor | Packages were replaced in a used environment | Fixed |
| F22 | Minor | A healthy environment without a record stayed unrecorded | Fixed |
| F23 | Minor | Two workflow tests could pass for the wrong reason | Fixed |
| F24 | Minor | Untested states and branches | Fixed; 70 further mutations, the five that survived are answered |
| F25 | Note | `.claude/.gitignore` is absent from the driver's isolated workspace | Left: no driver step reads it |
| F26 | Note | Caller settings reached `npm ci` | Fixed |
| F27 | Note | A visual run changed `.venv` before refusing used Node dependencies | Fixed |

## Rehearsal of "Continue"

| ID | Finding, in short | Disposition |
| --- | --- | --- |
| 1 | A session could not recognise itself as the demonstrating one | Fixed in the session checkpoint: an observable test, and a rule for every other session |
| 2 | No method for "as read from the application itself" | Fixed: named in the checkpoint |
| 3 | One session without parallel editing cannot show the Worktree criterion | Fixed: a separate owner step with its own prompt |
| 4 | The Worktree setting was stated for the main checkout only | Fixed in LOCAL-PROMPTS |
| 5 | "Commit only that file" against the closing rules | Fixed: the checkpoint says who updates the records |
| 6 | Push was not stated | Fixed |
| 7 | A second "Continue" would repeat the step | Fixed |
| 8 | "This session" meant two sessions; the branch's owner was unclear | Fixed: implementing and demonstrating session |
| 9 | TASK-030 depended on a step still in progress | Fixed: TASK-029 closes with the corrected checkpoint |
| 10 | "First unmet step" is TASK-006 by plan order | Fixed: the next unmet step is the one that CURRENT's next action names; a blocked step is reported |
| 11 | A ready next action was also listed as a blocker | Fixed: it waits for the owner's session and blocks nothing else |
| 12 | Where the recorded mode is, and what shows the persistent clone | Fixed in AGENTS, CLAUDE and LOCAL-START-HERE |
| 13 | "Folder" invited a machine path | Fixed: relative to the clone |
| 14 | The next action named no checks | Fixed in the checkpoint |
| 15, 16 | Startup lacked the issue, the pull request and commands | Fixed in LOCAL-START-HERE |
| 17 | Whether to read the whole TRD | Fixed in REQUIREMENTS and LOCAL-START-HERE |
| 18, 20 | Which specifications apply, and that these rules already bind this branch | Fixed in the checkpoint |
| 19 | The resolved TMPDIR was missing from two commands | Fixed in AGENTS (link) and in the ledger |
| 21 | "Skills are not automatically installed" had no mode | Fixed in AGENTS. "Live GitHub" in the template is left; it binds both modes when online |
| 22 | Tracker mismatch although the tracker is not committed | Fixed in PLAN |
| 23, 25–27 | Length of the required read-set and of the pointer chain | Left: the read-set is shared and the pointers are short; CURRENT and the checkpoint give the next action |
| 24 | Requirement stubs in the task record; `brief` counts requirements, not steps | Left: the record schema requires them, and no requirement is done before the audit |

It also reported statements that did not match. The ledger and the checkpoint now state the
focused tests with their temporary directory. LOCAL-START-HERE, STATUS and this missing record
are corrected. The driver run on the frozen candidate uses the candidate worktree's own
environment. Two older passages, in the workflow guide's account of C262 and in the
documentation guide's C073 entry, are history and are left.

## Second review of the tools and tests

The reviewer reproduced the earlier findings for real in scratch clones. F1, F4, F6, F7, F10,
F14 to F21, F23, F26 and F27 were found fixed, F25 left as stated, and F2, F3, F5, F8, F9, F11
to F13, F22 and F24 partly fixed; the findings below complete them.

| ID | Severity | Finding, in short | Disposition |
| --- | --- | --- | --- |
| T1 | Mandatory | Showing a failed run without a set-aside environment ended in an error instead of the report | Fixed; the command line is now tested through the real setup |
| T2 | Mandatory | A package recorded twice, or pip that does not run beside a missing package, looped; `--rebuild` was ignored | Fixed; `--rebuild` acts on any environment that is not ready |
| T3 | Mandatory | An interruption after the last action lost the run report; an unusable `build` was noticed after changes | Fixed |
| T4 | Mandatory | An editable install of another checkout counted as isolated | Fixed, for recorded installs and import hooks |
| T5 | Mandatory | Any Node process in the checkout blocked changes of `.venv` | Fixed |
| T6 | Mandatory | Renamed npm processes, Node below a path with a space, an empty environment and a plain locale hid users | Fixed |
| T7 | Minor | A process that had just ended counted as a user | Fixed |
| T8 | Minor | A stale environment record was never refreshed | Fixed |
| T9 | Minor | Next actions omitted `--root` and `--node` or named an action that refuses | Fixed |
| T10 | Minor | A second concurrent run was told to rebuild | Fixed; the lock comes first |
| T11 | Minor | Portable reports could keep places passed as options, cut paths or a local origin | Fixed |
| T12 | Minor | Operating-system errors became tracebacks | Fixed |
| T13 | Minor | Refusals hid the cause | Fixed |
| T14 | Minor | `new-task` and `brief` could fetch in a partial clone | Fixed |
| T15 | Minor | Nested receipts and any session file were accepted in CURRENT | Fixed |
| T16 | Minor | Tests could commit into a repository named by the caller | Fixed |
| T17 | Minor | Linked or manifest-only npm packages counted as ready | Fixed |
| T18 | Minor | No test ran the command line through the real setup | Fixed; one test also runs the unmodified tool for real |
| T19 | Minor | `--node` does not reach the driver's `--full` | Documented |
| N1 to N7 | Note | Letter case of the root, Rosetta, the set-aside place, paths inside the checkout, record-only runs, Playwright's setting 0, an all-zero base | Fixed |

After the corrections 118 mutations, its own and new ones, were tried; every one that changes
behaviour is detected.

## Audit of all 42 requirements

| ID | Severity | Finding, in short | Disposition |
| --- | --- | --- | --- |
| F-1 | Mandatory | RECONCILIATION said that Git does not hold the identity of the unpublished evidence | Fixed; the separately saved copy is named |
| F-2 | Minor | The checkpoint named recorded deviations, and none was recorded | Fixed in PLAN |
| F-3 | Minor | Count and cause of the remaining failure | Fixed; two of 92 regenerated files, cause inferred |
| F-4 | Minor | The candidate record cited baseline limits that did not exist | Fixed |
| F-5 | Minor | A check "passed" beside a driver that reports failed | Fixed; the driver is its own check, recorded as failed |
| F-6 | Minor | An earlier record without a mode could become `local` | Fixed in LOCAL-START-HERE |
| F-7 | Minor | "Ready on the owner's machine" although only the worktree is | Fixed in STATUS |
| F-8 | Minor | A test that skips for root | Fixed |
| F-9 | Minor | No committed record that the identifiers were unused | Fixed in REQUIREMENTS |
| F-10 | Minor | Path forms in LOCAL-SETUP that fail in a worktree or after a change of directory | Fixed |
| F-11 | Minor | Rehearsal fixes attributed to one commit | Fixed above |
| N-1, N-2, N-4, N-7, N-8 | Note | Read window, outer timeout for browser hosts, pointer to local command forms, fresh persistent clones, the lock file | Fixed |
| N-3 | Note | The browser startup read-set grew from 64,217 to 78,191 bytes | Left; it states both modes, and no limit is set for it |
| N-5 | Note | HOST-INVENTORY publishes backup, encryption and permission facts | Left as observed; reported to the owner |
| N-6 | Note | OK-ENG-009 gate 2 and the untracked TRDs copy at integration | Belongs to TASK-031 and TASK-033 |
| N-9 | Note | The candidate run used another worktree's interpreter | Later runs use the candidate worktree's own environment |
