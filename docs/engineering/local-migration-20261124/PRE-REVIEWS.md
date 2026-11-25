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

Every reviewer was a separate agent of the same model family, inherited from the session,
and wrote none of the work. The rehearsal is no fresh-session demonstration (DEC-010).
"Fixed" means changed on this branch and, for code, covered by a test; the commits are
`3c4694f9` and `ebcfee8c` (tools), `02797bb0` (documents) and the commit that adds this file
(rehearsal).

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
