# Lifecycle and recovery

Read this reference before changing a plan or task state, recording completion evidence, responding to a stale write or lock, or repairing generated files. The schema and result envelope are defined in [plan-contract.md](plan-contract.md).

## Authority does not flow from status

A lifecycle state records what the current canonical evidence and authority support. It does not create authority.

- Creating a plan authorizes only creation of a `draft` plan record.
- Marking a plan `ready` records approval of that exact baseline. It does not authorize implementation.
- Moving a plan to `in_progress` requires a current instruction that identifies the exact ready plan. It authorizes only work already within that instruction and the plan's normal local scope.
- A status transition never grants deletion, installation, dependency changes, publication, deployment, external communication, financial action, or another separately governed action.
- Completion requires current evidence and current confirmation; it cannot be inferred from elapsed time, a checklist mark, or a prior plan.

Use the current revision and canonical SHA-256 for every existing-plan mutation. Reopen the plan with `show` immediately before preparing a change.

## Plan lifecycle

| Current state | Meaning | Allowed next states |
| --- | --- | --- |
| `draft` | Sources, requirements, decisions, or plan structure remain unsettled. | `ready`, `retired`, `cancelled` |
| `ready` | Structure and coverage pass, material questions are settled, and the current user approved this exact revision. | `draft`, `in_progress`, `retired`, `cancelled` |
| `in_progress` | The current user authorized execution of the exact ready plan and work has begun. | `paused`, `blocked`, `completed`, `cancelled`, or `draft` after material scope change |
| `paused` | Work stopped intentionally without an external blocker. | `in_progress`, `cancelled`, or `draft` after material scope change |
| `blocked` | A named unmet condition prevents progress. | `in_progress`, `cancelled`, or `draft` after material scope change |
| `completed` | All completion gates passed against current evidence. | `in_progress` after explicit reopen, or `retired` |
| `retired` | The record is retained but is no longer active. | `draft` after explicit restore |
| `cancelled` | Work intentionally ended incomplete and the record is retained. | `draft` after explicit restoration and scope review |

Any edge not listed is prohibited. A legal edge can still fail because its gate, reason, stale-state check, or confirmation is missing.

### Draft to ready

The helper may accept `draft` to `ready` only when all conditions are current:

1. The project root and applicable live guidance were inspected.
2. At least one source and one requirement exist.
3. Material contradictions are resolved or have an explicit authorized disposition.
4. No open question or unconfirmed assumption that affects scope remains.
5. At least one phase and one task exist.
6. Every phase and task satisfies its complete field contract.
7. Every dependency exists, is acyclic, and respects phase order.
8. Every material source requirement maps to work or an explicit disposition.
9. Every task has a requirement or a labeled design-quality basis.
10. Validation for the current revision has no unresolved error finding.
11. The current user approves this exact revision and the mutation carries `--confirmed`.

An honest draft may be saved while any of these conditions is unresolved. Report the blockers; do not manufacture an answer or weaken the gate.

### Ready to in progress

This transition requires a current explicit instruction that identifies the exact plan. Record the instruction as the authority basis. Before the transition, recheck that the canonical plan remains at the approved revision and that planned work still fits the live project.

The transition does not execute tasks. An implementation agent or project workflow performs separately authorized work and then uses explicit tracker updates to record observed progress.

### Pause and block

Use `paused` for an intentional stop. Use `blocked` only for a named unmet condition outside the active task's control. Both states require a nonblank reason. Resume only when the pause instruction changes or the named blocker is resolved.

Do not use `blocked` to hide uncertainty that belongs in a draft question, to avoid difficult work, or to claim that planned tests ran.

### Material scope change

A change is material when it changes the approved outcome, requirements, exclusions, architecture, affected artifacts, authority boundary, acceptance criteria, phase structure, or other content on which readiness or execution approval depended.

Updating material scope while `ready` or `in_progress` returns the plan to `draft`. Recompute coverage and validation, reinspect the project as needed, and obtain approval of the new exact revision. A completed plan must be explicitly reopened before its baseline can change. Retirement and cancellation restore through `draft` before revision.

### Completion

The helper may accept `in_progress` to `completed` only when:

1. Every required task is `completed` or has an explicitly approved skip.
2. Every task acceptance criterion has current, meaningful evidence.
3. Stored phase states equal their derived task rollups.
4. Every requirement acceptance criterion is satisfied or has an authorized disposition.
5. Forward and reverse traceability pass.
6. The final project state was reinspected strictly after the current task and requirement evidence. An equal timestamp is not later. Each protected path has a current baseline fact whose evidence locator is that exact project-relative or absolute path and whose fact affirmatively states the observed preservation result, such as unchanged bytes, a digest, or continued absence. Negated, false, failed, incorrect, or unsuccessful preservation wording does not count.
7. Every planned test is labeled `passed`, `failed`, `blocked`, or `not_exercised`; a planned command is never reported as run.
8. The helper appends exactly one computed sentence stating the highest verification level actually reached. Caller-supplied enum spellings and human-readable aliases such as `end-to-end verified`, `broader suite`, or `targeted tests` are rejected.
9. The current user explicitly confirms the completion transition for this exact revision.

A failed, blocked, or not-exercised check can remain in the plan, but it cannot be presented as passing evidence. If it prevents an acceptance criterion, completion fails.

### Reopen, retire, cancel, and restore

- `completed` to `in_progress` requires explicit reopen authority and a reason. Preserve prior completion evidence and history; current task state determines what must be reopened.
- `retired` preserves a completed or inactive plan. It does not delete files.
- `cancelled` preserves incomplete work and its evidence. It does not turn tasks into completed or skipped work.
- Restoring `retired` or `cancelled` moves to `draft`, records authority and reason, and requires live project and scope review before readiness.

## Task lifecycle

| Current state | Meaning | Allowed next states |
| --- | --- | --- |
| `planned` | Defined but not started. | `in_progress`, `blocked`, `skipped` |
| `in_progress` | Separately authorized work is being performed. | `paused`, `blocked`, `completed` |
| `paused` | Work stopped intentionally. | `in_progress`, `blocked`, `skipped` |
| `blocked` | A named unmet condition prevents work. | `in_progress`, `paused`, `skipped` |
| `completed` | Acceptance and evidence gates passed. | `in_progress` after explicit reopen |
| `skipped` | The current user approved a reasoned exception. | `planned` after explicit restoration |

Any edge not listed is prohibited.

### Starting work

A task may enter `in_progress` only when:

- the exact plan is `in_progress`;
- the work is within the current implementation authority;
- every required predecessor is `completed` or has an authorized skip with valid coverage disposition;
- every declared predecessor phase is derived `completed`;
- the task still fits the live project; and
- the caller supplies current revision and SHA-256 preconditions.

A parallel-group label does not bypass a predecessor or authority gate.

### Blocking and pausing a task

`blocked` requires `blocker_reason`; `paused` requires `pause_reason`. The other field remains null. Resume records why the condition changed in history. Do not overload these fields with a skipped-task reason.

### Completing a task

Before requesting `completed`:

1. Reopen the task's acceptance criteria and planned verification steps.
2. Inspect current project state and run only authorized checks.
3. Record concise evidence through `record-evidence` against the exact task or requirement.
4. Distinguish tool output, agent inspection, user report, external report, planned check, and not-exercised work, and label each record with `result_status` as `planned`, `passed`, `failed`, `blocked`, `partial`, or `not_exercised`.
5. Confirm that each criterion has meaningful current evidence.
6. Request the legal task transition with current revision and hash.

Meaningless markers such as `done`, an unchecked plan statement, an expected command, or an unsupported success summary do not satisfy the gate. Case, Unicode, punctuation, dotted spelling, and marker-only combinations are normalized before this check. A user report remains labeled as a user report.

Observed and not-exercised implementation evidence can be appended only while the exact plan is `in_progress`. Draft planning may contain `planned_check` records, but creation itself cannot preload implementation evidence or completed task/requirement state.

### Skipping and restoring a task

A skip requires:

- a nonblank `skip_reason`;
- nonblank `skip_authority` that identifies the current explicit user exception;
- preservation of all prior evidence and history; and
- an accepted disposition for any requirement coverage that would otherwise become incomplete before phase or plan completion.

Lifecycle reasons and exception authorities must be substantive, not normalized placeholder text.

Outside `skipped`, `skip_reason` and `skip_authority` are null. Restoring a skipped task moves it to `planned`, clears the current skip fields, and retains the prior decision in history.
Changing either skip field while the task remains `skipped` is a new exception decision. It is allowed only while the exact plan is `in_progress` and requires current `confirmed: true`; an unconfirmed rewrite leaves every file byte-identical.

### Reopening a completed task

Reopen only with a current explicit instruction and reason. Move the task to `in_progress`, clear `completed_at`, preserve all prior evidence, append history, and recompute its phase. Evidence may become stale after project changes; do not erase it, but record new evidence and do not rely on stale evidence for later completion.

## Derived phase state

The helper never accepts a direct phase-status assignment. It recomputes the phase after any task, dependency, evidence, or coverage change:

1. `completed` when every required task is completed or is skipped with a valid accepted exception and disposed coverage.
2. `planned` when all tasks are planned.
3. `blocked` when required unfinished work has no executable path because of recorded blockers.
4. `paused` when all otherwise executable unfinished work is paused and no blocker controls the phase.
5. `in_progress` for every other valid started combination.

Stored and derived phase state must match. Drift is corrupt canonical state; do not hide it by editing a projection.

## Evidence discipline

Evidence records must be concise, current, attributable, and reviewable. Agent/tool observations require a command, test name, receipt, or exact locator. The helper binds every record to the target and its relevant current plan context. A changed target, linked requirement, source, coverage edge, phase contract, project constraint, preservation duty, objective, or scope makes the old record historical; an unrelated plan extension does not. Use the verification levels in the canonical contract. The level states the strongest successful observation actually reached:

1. `inspected_only`
2. `static_checks_passed`
3. `targeted_tests_passed`
4. `broader_suite_passed`
5. `runtime_observed`
6. `end_to_end_verified`

`planned` and `not_exercised` are classifications, not passing levels. A planned result is valid only for `planned_check` and cannot satisfy a verification-report gate. `not_exercised` uses the matching type, result status, and verification level. Failed, blocked, partial, planned, and not-exercised records do not raise the reported highest successful verification level. A high level on one narrow check does not prove a broader acceptance criterion. Record failed and partial results; do not delete them to make status look clean.

Evidence must not contain secrets, hidden reasoning, full transcripts, full source pages, or large raw logs. Summarize the observed result and retain a safe command, file, receipt, or citation locator. If redaction would change the meaning, stop and report that safe evidence cannot be stored.

## Revision-safe mutation

All existing-plan mutations follow the same sequence:

1. Run `show SELECTOR` and retain its exact `revision` and canonical `sha256`.
2. Prepare one bounded mutation payload.
3. Pass both preconditions to the helper.
4. The helper acquires its lock, rereads, rehashes, and compares state.
5. A mismatch returns `stale_state`; no file changes.
6. A valid no-op returns `no_op`; revision and history do not change.
7. A real canonical change advances revision by one and appends one action history entry.
8. Inspect the result envelope, then run `show` and `validate` again.

Do not retry a stale mutation automatically. Reread the new state, reconcile intent, and prepare a fresh change.

## Locks

Plan creation and catalog publication use a catalog lock. Existing-plan mutation uses a per-plan lock and follows one helper-defined lock order whenever both are needed. Lock creation, owner I/O, rename, and release are bound to no-follow directory descriptors and checked inode identities so a parent swap cannot redirect cleanup. A failed release is renamed to an exact helper-owned `.released-TOKEN` residue when possible. Read-only operations detect and report an active lock but do not remove it.

Lock age, file modification time, or a recorded process ID alone cannot prove abandonment. A PID may have been reused or may identify another environment. Never steal a lock merely because a timeout elapsed.

If a lock blocks work:

1. Stop the mutation.
2. Inspect the exact lock as read-only data.
3. Check for a live writer through available project-safe evidence.
4. Validate canonical state and inspect helper-owned temporary residue.
5. If active ownership remains possible, report `active_lock` and stop.
6. If abandonment is established, prepare one exact reconcile specification for only that lock, released-lock residue, partial-create residue, or helper-owned temporary file.
7. Obtain current explicit confirmation.
8. Run `reconcile`, then validate again.

## Canonical publication and partial success

The helper writes canonical JSON to a same-directory temporary regular file, flushes and syncs it, and atomically replaces `plan.json`. It then publishes plan projections and the catalog index.

If failure occurs before canonical replacement, canonical state remains unchanged and helper-owned temporary residue is reported for inspection. If canonical replacement succeeds but a projection or index write fails, the command returns `partial_projection`:

- the canonical mutation is committed;
- revision and history already advanced;
- the receipt names failed generated outputs;
- `recovery_required` identifies `rebuild-projections` or `reindex`;
- the caller must not repeat the canonical action.

Run the exact generated-file repair and validate byte parity. Projection repair never changes canonical revision.

## Projection drift

Missing, edited, or stale `PLAN.md`, phase files, `TRACEABILITY.md`, or `INDEX.md` do not change plan meaning. Use:

- `rebuild-projections SELECTOR` for one selected plan's generated files;
- `reindex` for the managed catalog index.

Both routes require valid canonical state, preserve unmanaged content, and are idempotent. They do not adopt standalone Markdown plans.

## Bounded reconcile

`reconcile` exists for one explicit recovery scope described by reviewed JSON input. It is not a general editor, migration engine, force-unlock switch, or corruption bypass.

Before plan-scope reconcile:

- select the exact plan;
- inspect the exact lock, temporary file, or recoverable discrepancy;
- prove that no active writer can reasonably own it;
- validate canonical state;
- confirm the target is helper-owned and confined to the selected plan or catalog;
- describe the one permitted operation and expected no-op behavior; and
- obtain current confirmation with `--confirmed`.

Reconcile must refuse to:

- infer intent from malformed JSON;
- create or alter evidence to satisfy a gate;
- rewrite a stale client update;
- remove a possibly active lock;
- delete or migrate a plan;
- touch an unmanaged file;
- cross the project root;
- mutate another state system; or
- repeat a prior successful canonical mutation.

Supported bounded actions are `remove_abandoned_lock`, `remove_released_lock`, `remove_orphan_temp`, and `remove_partial_create`. Released-lock recovery requires the exact scope, helper-generated release name, token, and optional owner digest. Partial-create recovery declares `state: temporary` with exact relative path and digest, or `state: empty` for an empty managed-shape remainder. If a partial result already removed the temporary, use the returned progressed `state: empty` input. For catalog scope, use the literal selector `catalog`; validate every managed canonical record before removing an abandoned catalog lock. If the catalog is absent, a removal-only catalog recovery is a byte-preserving no-op and does not create it. This route does not require selecting a plan, which is important when the catalog lock itself blocks plan mutation. After reconcile, run read-only `show` when a plan applies and `validate`. A second identical recovery call should be a safe no-op.
When projection publication and owned-lock cleanup both fail after canonical commit, follow the nested receipt in order: reconcile the exact lock residue, rebuild the plan projections, reindex, and validate. Do not let the later cleanup failure erase the earlier projection repair.

## When recovery is not possible

Stop and return the exact blocker when canonical state is corrupt, intent or authority is missing, a writer may still be active, the recovery target is not helper-owned, or the repair would require guessing. Preserve all files. Ask for the smallest missing source, decision, or external-state change rather than widening the recovery scope.
