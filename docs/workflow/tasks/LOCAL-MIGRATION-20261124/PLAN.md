# LOCAL-MIGRATION-20261124 implementation plan

Base: `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`. Branch:
`work/local-migration-20261124`. Director and integration owner token:
`local-migration-0e9ea0a483b1`. Scope issue: [277](https://github.com/Omegapy/OntoKin/issues/277).

The steps, dependencies and acceptance criteria below are those of
PLAN-20261125-CB551B16, revision 3, which the owner approved and authorized for
execution on 2026-11-24. That plan's tracker stays untracked in the owner's main
checkout because it is bound to that project root. [task.json](task.json) is the
acceptance ledger; a session that can read both reports a mismatch and does not
synchronize them.
Requirements: [REQUIREMENTS.md](REQUIREMENTS.md).

## Order and dependencies

| Step | Title | Requirements | Depends on |
| --- | --- | --- | --- |
| TASK-001 | Record the host and clone inventory | REQ-001, REQ-034 | None |
| TASK-002 | Create the migration task record, branch and worktree | REQ-002 | TASK-001 |
| TASK-003 | Record the dated owner-direction decision | REQ-016 | TASK-002 |
| TASK-004 | Capture the identities that must be preserved | REQ-006, REQ-008, REQ-020, REQ-032, REQ-033, REQ-039 | TASK-002 |
| TASK-005 | Reconcile the Git-visible state of main, C271 and the local clone | REQ-030, REQ-033 | TASK-002 |
| TASK-006 | Verify the R06 handoff and its receipt before any import | REQ-031, REQ-032, REQ-038 | TASK-001 |
| TASK-007 | Complete the reconciliation record from the verified handoff | REQ-030, REQ-031, REQ-032 | TASK-005, TASK-006 |
| TASK-008 | Record storage classes, durable locations and the restore check | REQ-038 | TASK-006 |
| TASK-009 | Define the tracked environment specification, profiles and ignore rules | REQ-003, REQ-005, REQ-009, REQ-013 | TASK-002 |
| TASK-010 | Produce and review the macOS arm64 verification lock | REQ-006 | TASK-009 |
| TASK-011 | Implement the bootstrap tool and its tests | REQ-004, REQ-008, REQ-011 | TASK-009, TASK-010 |
| TASK-012 | Implement the doctor tool and its tests | REQ-008, REQ-012, REQ-042 | TASK-009 |
| TASK-013 | Create the default environment and reach python-verification readiness | REQ-003, REQ-004, REQ-007, REQ-011, REQ-013 | TASK-011, TASK-012 |
| TASK-014 | Prove installed-package behaviour outside the checkout | REQ-013, REQ-015 | TASK-013 |
| TASK-015 | Record the routine-driver baseline on the unmodified base revision | REQ-036 | TASK-013 |
| TASK-016 | Write the local setup guide | REQ-005, REQ-008, REQ-009, REQ-010, REQ-014 | TASK-011, TASK-012, TASK-013 |
| TASK-017 | Amend AGENTS.md and OK-ENG-006 for execution modes and local validation | REQ-014, REQ-016, REQ-017, REQ-018, REQ-037 | TASK-003 |
| TASK-018 | Amend the workflow protocol, handoff contract and workflow guide for local mode | REQ-016, REQ-017, REQ-018, REQ-025, REQ-035 | TASK-017 |
| TASK-019 | Add the local entry document and the local prompts | REQ-019, REQ-023, REQ-024, REQ-029 | TASK-012, TASK-018 |
| TASK-020 | Add the Claude adapter | REQ-019 | TASK-017, TASK-019 |
| TASK-021 | Route both modes in the registry, the root README and the documentation guide | REQ-016, REQ-018 | TASK-019 |
| TASK-022 | Amend the OntoKin session and delivery skills for local mode | REQ-018, REQ-020 | TASK-018, TASK-019 |
| TASK-023 | Extend the session checkpoint template | REQ-026 | TASK-018 |
| TASK-024 | Reconcile STATUS.md and compact CURRENT.json with provenance | REQ-018, REQ-022, REQ-027, REQ-030, REQ-033 | TASK-005, TASK-018 |
| TASK-025 | Amend the workflow tool and its tests | REQ-022, REQ-027, REQ-028 | TASK-021, TASK-024 |
| TASK-026 | Amend the local driver's inventories and its tests | REQ-028, REQ-036 | TASK-015, TASK-019, TASK-020 |
| TASK-027 | Run the changed-scope checks on the candidate and compare with the baseline | REQ-007, REQ-011, REQ-018, REQ-028, REQ-036, REQ-037 | TASK-015, TASK-025, TASK-026 |
| TASK-028 | Test a second worktree for recreation from specifications and for isolation | REQ-004, REQ-014, REQ-035 | TASK-013, TASK-016 |
| TASK-029 | Close a session with a checkpoint under the extended template | REQ-025, REQ-026 | TASK-023, TASK-027 |
| TASK-030 | Demonstrate fresh-session resumption in the owner's graphical workflow | REQ-019, REQ-020, REQ-021, REQ-023, REQ-024, REQ-029 | TASK-020, TASK-022, TASK-029 |
| TASK-031 | Audit the candidate against every requirement and freeze it | REQ-009, REQ-010, REQ-018, REQ-022, REQ-042 | TASK-007, TASK-008, TASK-027, TASK-028, TASK-030 |
| TASK-032 | Obtain independent review of the exact candidate | REQ-040 | TASK-031 |
| TASK-033 | Integrate into main and verify the resulting main | REQ-034, REQ-041 | TASK-032 |
| TASK-034 | Verify preservation and clean up the migration branch and worktrees | REQ-006, REQ-008, REQ-020, REQ-032, REQ-033, REQ-039, REQ-041 | TASK-033 |
| TASK-035 | Prepare the main checkout's environment from the integrated specifications | REQ-003, REQ-014 | TASK-033 |
| TASK-036 | Publish the closing report and close the task record | REQ-022, REQ-027, REQ-042 | TASK-034, TASK-035 |

Phase gates: PHASE-002, PHASE-003 and PHASE-004 follow PHASE-001; PHASE-005
follows PHASE-003 and PHASE-004; PHASE-006 follows all of them. Integration
waits for the reconciliation record (TASK-007) and stops if the R06 archive or
its receipt is still unavailable when all other work is ready.

## Ownership

The Director owns the task record, `AGENTS.md`, `STATUS.md`, `CURRENT.json`,
the registry, the index and commits of this branch, and all publication.
Workers own only the paths assigned to them and return results to the Director.
Reviewers inspect and do not edit the candidate.

## Deviations from the approved plan

| Step | Plan | What was done | Reason |
| --- | --- | --- | --- |
| TASK-009 | Ignore rules in the root `.gitignore` | A nested `.claude/.gitignore` covers the worktrees and settings that the Claude application creates | The documentation verifier binds the bytes of the root file (SRC-01) |
| TASK-027 | One candidate record | Driver runs were repeated at later commits; the last one, from the candidate worktree's own environment, is the candidate record | Independent pre-reviews led to changes of the tools and documents |
| TASK-030 | One owner session provides every observation (DEC-010) | The owner is also asked for a second, read-only session with Worktree mode on | One session without parallel editing cannot show the Worktree criterion |

## Acceptance by step

### PHASE-001 — Baseline, scope and authority

Establish the observed starting state, the migration's own task record, branch and worktree, the dated owner-direction record, and the identities that must be preserved.

**TASK-001 — Record the host and clone inventory**

- Each listed item has its observed value or an explicit 'not observed' entry.
- Local Git authentication to origin is shown by a successful read-only observation of the remote.
- Every local modification, untracked file and unpublished commit found is listed with its path or identity, so that later tasks can show it is still present.
- The record contains no credential, account name or home-directory path.

**TASK-002 — Create the migration task record, branch and worktree**

- The identifiers are shown unused on main, on the C271 branch and among open pull requests and issues before they are used.
- The task record exists with requirements, plan, status, the exact starting revision and a scope issue, and `tools/chat_workflow.py check` passes in the migration worktree.
- The migration branch starts at the observed main head, and its worktree is a separate directory outside the main checkout.
- The TRD file on the migration branch is byte-identical to the approved revision, and the task record cites it by path and ID.
- The C271 branch is neither the working branch nor modified.

**TASK-003 — Record the dated owner-direction decision**

- The record is dated, cites TRD-20261124-E65C6113 and the owner's execution instruction as its authority, and states that the change is prospective.
- The record names the retained browser entry point and ephemeral-host rule and states that no historical record is reinterpreted.

**TASK-004 — Capture the identities that must be preserved**

- The record gives a SHA-256 and a Git blob identity for each listed file and the target of each skill link.
- The record gives the observed C271 branch head and the state of pull request #274 and issue #273.
- Each identity was read from the base revision of the migration branch.

### PHASE-002 — Legacy reconciliation and durable storage

Reconcile main, the C271 branch, the R06 handoff and the local clone, and record where each kind of unique material durably lives.

**TASK-005 — Reconcile the Git-visible state of main, C271 and the local clone**

- The record states what is already in Git on main and on the C271 branch, which branch owns the unfinished C271 work, and which C271 acceptance gates remain open, each with the commit or record it was read from.
- The record lists the files changed on both sides since the merge base and marks the handoff-specific findings as awaiting TASK-007.
- The C271 branch head, pull request #274 and issue #273 are unchanged by the task.

**TASK-006 — Verify the R06 handoff and its receipt before any import**

- The outer archive's size and SHA-256 equal 41,730,084 bytes and the R06 SHA-256 recorded in the TRD, or the mismatch is recorded and nothing is imported.
- The manifest entries, nested recovery identities and accepted payload inventory are checked, and each result is recorded as passed, failed or not checked.
- The evidence archive's size, SHA-256 and Git blob identity equal 25,817,783 bytes and the values recorded in the TRD.
- The retrieval of the archive from its durable location and this identity check are recorded as the restore check of one representative unique artifact.

**TASK-007 — Complete the reconciliation record from the verified handoff**

- The record states the four findings: what is already in Git, what is unique to the handoff, which branch owns it, and which acceptance gates remain open.
- Only needed data was extracted, into a staging location outside the clone, and the clone's working tree received no archive extraction.
- Overlapping `CURRENT.json`, C271 `task.json`, `REQUIREMENTS.md` and `PLAN.md` content is reconciled by meaning, and no current record is overwritten with an old snapshot.
- The identity and durable location of the R06 archive, its receipt and the C262 archive are recorded for later on-demand use.

**TASK-008 — Record storage classes, durable locations and the restore check**

- Each kind of material named in REQ-038 has its treatment and durable location recorded.
- The restore of one representative unique artifact from its durable backup is recorded together with the identity check that verified it.
- Material found to exist only on the local disk is listed explicitly.
- No chain of nested handoffs was added to the repository.

### PHASE-003 — Repeatable environment and tooling

Deliver the tracked environment specification, the macOS lock, the bootstrap and doctor tools, a ready python-verification environment, the installed-package check, the validation baseline and the setup guide.

**TASK-009 — Define the tracked environment specification, profiles and ignore rules**

- The specification names the exact interpreter patch, each profile's contents and readiness checks, and the lock file for each supported platform.
- The specification adds no package beyond the adopted pins and no dependency on uv, Conda or another manager.
- Worktree, local-configuration and output locations are ignored, and the specification itself is tracked.
- `pyproject.toml` still declares `requires-python >=3.11`.

**TASK-010 — Produce and review the macOS arm64 verification lock**

- The lock lists exactly the seven adopted versions, each with the SHA-256 of the downloaded wheel bytes.
- The provenance record gives each wheel's filename, platform tag, source location, byte size and SHA-256.
- The hashes of the platform-independent wheels equal the corresponding entries of the Linux lock, and the Linux lock is byte-identical to its recorded identity.
- A recorded review by a separate reviewer confirms each entry before the lock is used to install anything.

**TASK-011 — Implement the bootstrap tool and its tests**

- The tool resolves the repository or worktree and the interpreter, selects the committed profile, refuses an incompatible lock before installing anything, creates the environment only when absent, and installs only missing or mismatched packages with hash enforcement.
- A preview run changes nothing, and a repeat run on a healthy environment replaces no dependency, upgrades no package and regenerates no lock.
- An incompatible existing environment is reported and not rebuilt without an explicit request, and a missing interpreter is distinguished from missing packages.
- Node and Chromium preparation is reachable only through the visual profile, compares installed identities first and never runs `npm ci` on a healthy or in-use dependency directory.
- Concurrent runs cannot mutate the same environment.
- Tests for the four required behaviours exist and pass.

**TASK-012 — Implement the doctor tool and its tests**

- Each profile's readiness is exactly one of `ready`, `missing`, `mismatch`, `unsupported` or `not_checked`; a wrong package version is a `mismatch`, and an unexecuted check is never a pass.
- Running the tool changes no dependency, lock or source file, and it writes a report only when one is requested.
- Without the explicit online mode the tool performs no fetch and no publish.
- The output reports every area listed in REQ-012 in both human-readable and JSON form, and reports general tool readiness separately from native experiment acceptance.
- The tool runs with an interpreter that has none of the verification packages installed.

**TASK-013 — Create the default environment and reach python-verification readiness**

- The environment's interpreter is the exact patch named in the specification, and project commands run through `.venv/bin/python`.
- Installed versions equal the seven adopted versions, `pip check` reports no conflict, the imports succeed and `tools/check_native_reader_setup.py` passes.
- The environment record gives the interpreter, its distribution, the platform, the pip and build-tool versions, the package versions and the lock hashes, and an installation record is kept.
- The second bootstrap run reports no change, and the doctor reports `python-verification` as `ready`.
- No environment, cache or dependency directory appears as tracked or as unignored untracked content.

**TASK-014 — Prove installed-package behaviour outside the checkout**

- The record gives the source revision, the build environment with its tool versions, and the wheel's filename, size and SHA-256.
- The installed entry point and the representative operation ran from outside the checkout, and the imported module locations lie in the clean environment.
- The packaged resources listed in `pyproject.toml` are available to the installed package.
- No conclusion is drawn from an editable install.

**TASK-015 — Record the routine-driver baseline on the unmodified base revision**

- The record identifies the base revision and tree, the platform, interpreter and package versions, the commands and the output location.
- Each driver step and each in-place check is recorded as passed, failed, timed out, pending or not run, with the location of its log.
- No expectation, test or driver file was changed to obtain the baseline.

**TASK-016 — Write the local setup guide**

- The guide documents each profile's contents and readiness checks and the exact commands, and every command in it was run or is marked as not run.
- The guide states the native-by-default container decision with its reasons and that an emulated amd64 container is never native Linux qualification.
- The visual-verification section names Node.js 22 as the target, the committed npm versions, `npm ci` from `tools/package-lock.json` with its replacement behaviour and the separate Chromium step, and carries no Linux `--with-deps` option for macOS.
- The guide tells local users to write driver output outside the checkout and explains why.

### PHASE-004 — Local-mode instructions and continuity records

Adopt the explicit local execution mode coherently across every instruction surface, add the local entry point and the Claude adapter, and bring the continuity records and their tools in line.

**TASK-017 — Amend AGENTS.md and OK-ENG-006 for execution modes and local validation**

- `AGENTS.md` names both execution modes, requires the mode to be explicit, and no longer confines local-mode checks to the assistant's hosted workspace.
- The ephemeral-host rule and the browser handoff rules still apply, unchanged in meaning, to browser sessions.
- OK-ENG-006 describes validation on the selected local executor, replaces the temporary external environment example with the persistent one, and keeps the manual-only, default-false hosted-workflow rules and the no-payment direction.
- No statement about semantics, expectations, budgets or release gates changed.

**TASK-018 — Amend the workflow protocol, handoff contract and workflow guide for local mode**

- The seven local-mode rules of REQ-017 are stated, each beside the browser rule it replaces for local sessions.
- A local session or scope closes on a source checkpoint, a truthful task and session record, verified push state when online, and durable evidence, with a ZIP optional unless the selected task requires one.
- The conduct rules of REQ-025 and the parallel-work rules of REQ-035 are stated for local mode.
- Browser sessions still require the early recovery ZIP and the verified saved handoff.

**TASK-019 — Add the local entry document and the local prompts**

- The entry document contains the seven startup steps of REQ-024, the offline rule, and the instruction to run the doctor and the workflow structure check.
- The Go or Continue convention and its limits are stated as in REQ-023, with no dependence on ChatGPT Goals, scheduled Tasks or agent-private memory.
- No full suite and no historical archive download is a startup step.
- The prompts give concise instructions for starting, continuing, recovering and checkpointing a local session.

**TASK-020 — Add the Claude adapter**

- `CLAUDE.md` imports `AGENTS.md` and contains no duplicated or competing project rule.
- The adapter refers to the local entry document only for persistent local development and does not infer the execution mode.

**TASK-021 — Route both modes in the registry, the root README and the documentation guide**

- The registry names each mode's entry point and required reads, and neither mode is selected by a path or an agent name.
- The root README and the documentation guide lead with the local entry point and link to the browser workflow and to the setup guide.
- Every added link resolves.

**TASK-022 — Amend the OntoKin session and delivery skills for local mode**

- Both skills state the local-mode route and keep the browser route.
- Exactly one version of each skill exists, and all six `.claude/skills` links resolve.
- `to-trd` and `to-implementation-plan` remain explicit-invocation only.

**TASK-023 — Extend the session checkpoint template**

- The template carries the identity, source, work, environment, verification, recovery, coordination, continuation and delivery groups with the fields REQ-026 lists.
- Existing fields are kept, so earlier session records remain valid under the template.
- The template states that no receipt-of-the-receipt cycle is created.

**TASK-024 — Reconcile STATUS.md and compact CURRENT.json with provenance**

- The earlier `CURRENT.json` is retrievable unchanged from the recorded reference.
- `CURRENT.json` holds the current selection and checkpoint pointers and links to the retained history instead of embedded receipts.
- `STATUS.md` reconciles the hosted-workspace wording for local mode, shows the migration's status, and shows C271 as unfinished with its open gates.
- No historical statement, anchor or evidence reference was deleted.

**TASK-025 — Amend the workflow tool and its tests**

- `tools/chat_workflow.py check` passes on the migration branch, and records under the earlier schema remain interpretable.
- The old-to-new field mapping is documented, and the changed schema carries a version.
- A task created after main has moved records the actual base revision, as shown by a test.
- The focused tests pass.

**TASK-026 — Amend the local driver's inventories and its tests**

- The isolated workspace contains every instruction file and directory that tracked documentation links to, including the new local entry document, the Claude adapter and the committed TRD directory.
- The driver's `documents` step reports no missing local link caused by an uncopied instruction file.
- The focused driver tests pass, and no historical evidence hash was modified.

### PHASE-005 — Validation and demonstrations

Establish actual validation evidence for the candidate and demonstrate isolation, checkpointing and fresh-session resumption.

**TASK-027 — Run the changed-scope checks on the candidate and compare with the baseline**

- The record identifies the candidate commit and tree, the platform, interpreter and package versions, the commands, the outputs and the limitations.
- The documentation verifier, the workflow check, the focused tool tests and the routine driver were run, and each item is recorded as passed, failed, pending or not run.
- Every failure is classified as unchanged from the baseline or as new, and no new or worsened failure in released behaviour remains.
- No workflow definition gained a push, pull-request or scheduled trigger, and no expectation was changed.

**TASK-028 — Test a second worktree for recreation from specifications and for isolation**

- The fresh environment was created in a location with no prior environment and reaches the same reported readiness as the first.
- Setup and check commands run in the second worktree used that worktree's files and environment, as shown by recorded paths.
- The two worktrees share no writable environment, and neither changed the other's state.
- The evidence was preserved before the second worktree was removed.

**TASK-029 — Close a session with a checkpoint under the extended template**

- The checkpoint fills all nine field groups from observed state and names one next action with the condition that makes it safe.
- The checkpoint is enough for another agent to continue and is not a transcript.
- The task record's status agrees with the actual acceptance state.

**TASK-030 — Demonstrate fresh-session resumption in the owner's graphical workflow**

- The Code tab opened the local project and ran the documented workflow, and its version was read from the application itself.
- The fresh session's account of the selected task, the environment, the completed work, the last completed gate, the next action and the blockers matches the repository records.
- The shared instructions, the Claude adapter and the six skills were observed as loaded or discovered in that session.
- On the continuation instruction the session resumed the next unmet gate and neither restarted completed work nor selected another milestone.
- Worktree mode was enabled deliberately before any parallel editing, and the actual checkout path and branch were then verified.

### PHASE-006 — Review, integration and closure

Freeze and audit the candidate, obtain independent review, integrate into main through the established lifecycle, verify preservation, and close the scope with a truthful report.

**TASK-031 — Audit the candidate against every requirement and freeze it**

- Each requirement has its evidence location or an explicit open state, and each changed file traces to a requirement.
- No conflicting active instruction remains, and no `uv.lock`, Docker configuration, frozen requirements file or second status ledger was added.
- Readiness is reported for each profile, and environment readiness, task completion and product qualification are stated separately.
- The candidate commit and tree are recorded, and no later change is made without renewed review.

**TASK-032 — Obtain independent review of the exact candidate**

- The reviewer's identity, the exact candidate reviewed, the findings, their resolutions and the acceptance disposition are recorded.
- Every mandatory finding is resolved, and each affected revision was reviewed again.
- No self-review is reported as independent review.

**TASK-033 — Integrate into main and verify the resulting main**

- Local Git authentication was observed before publication, and no force update was used.
- The merge used an expected-head comparison, and the actual merge commit and tree were read back.
- The applicable resulting-main checks were run on the merge commit and recorded.
- The lease acquisition, expiry and release are recorded in `STATUS.md`.
- The main checkout is at the merge commit with no lost untracked file.

**TASK-034 — Verify preservation and clean up the migration branch and worktrees**

- Each identity in `PRESERVATION.json` equals its value on the resulting main: the Linux lock, the pins file, the npm manifest and lock, `.gitattributes` and the six skill links.
- The C271 branch head, pull request #274 and issue #273 were not merged, closed or deleted by the migration.
- The migration branch's disposition is observed and recorded as deleted, or as deletion pending with the exact pending action, and its history is retained in main.
- No worktree was removed while it held an unpublished commit, an untracked file or an active worker.

**TASK-035 — Prepare the main checkout's environment from the integrated specifications**

- The main checkout's environment was created from the integrated specification and lock, with the interpreter patch they name.
- The doctor reports `python-verification` as `ready` in the main checkout, or the exact blocking item is reported.
- The environment record for the main checkout is kept.

**TASK-036 — Publish the closing report and close the task record**

- The report states the changes, the checks actually run, readiness by profile, retained blockers, remaining work and the next selected action.
- The report does not present a successful install as C271 completion, native-tool qualification or a release pass.
- The task record, `CURRENT.json` and `STATUS.md` agree with the final state, and `tools/chat_workflow.py check` passes on main.
- The learning checkpoint's result or its skip rationale is recorded, and the lease is released.

## Stop conditions

Work stops at this scope's acceptance point, at a concrete blocker after other
useful work in the scope is done, or at a session boundary after recording
recovery state. An unexpected wider change, a new or worsened failure in
released behaviour, or a dependency on an unfinished scope also stops the
affected step.
