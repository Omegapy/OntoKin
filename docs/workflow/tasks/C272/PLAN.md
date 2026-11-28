# C272 implementation plan

Base: `38ee8d18a6cd67245acf8b21d755e979b84153c1`. Branch:
`work/c272-edit-rebuild-qualification`, in the worktree `../OntoKin-worktrees/c272` with
its own `.venv`. Director and integration owner token: `c272-4d816b3c0468`. Scope issue:
[282](https://github.com/Omegapy/OntoKin/issues/282).

The steps, dependencies and acceptance criteria below are those of PLAN-20261128-AC17E7E0,
revision 4, which the owner approved and instructed to execute on 2026-11-28 UTC. That
plan's tracker stays untracked in the owner's main checkout, because it is bound to that
project root (DEC-004). [task.json](task.json) is the acceptance ledger; a session that can
read both reports a mismatch and does not synchronize them. Requirements:
[REQUIREMENTS.md](REQUIREMENTS.md).

## Order and dependencies

| Step | Phase | Title | Requirements | Depends on |
| --- | --- | --- | --- | --- |
| TASK-001 | PHASE-001 | Reconcile the starting state and report it | REQ-001, REQ-003 | None |
| TASK-002 | PHASE-001 | Preserve the local changes and bring the main checkout up to date | REQ-001 | TASK-001 |
| TASK-003 | PHASE-001 | Create the branch, the worktree and its environment | REQ-002, REQ-003, REQ-005 | TASK-002 |
| TASK-004 | PHASE-001 | Create the task record on the scope's branch | REQ-001, REQ-002, REQ-003 | TASK-003 |
| TASK-005 | PHASE-001 | Correct the current-status text if it is still needed | REQ-004 | TASK-003 |
| TASK-006 | PHASE-001 | Publish the declaration checkpoint | REQ-002 | TASK-004, TASK-005 |
| TASK-007 | PHASE-002 | Map every required property to its observation and comparison | REQ-007, REQ-016 | TASK-006 |
| TASK-008 | PHASE-002 | Run the existing observer regression on this host | REQ-007, REQ-024 | TASK-006 |
| TASK-009 | PHASE-002 | Reconcile the C269 audit with C270 and C271 | REQ-009 | TASK-007 |
| TASK-010 | PHASE-002 | Record the missing components, their boundaries and effort | REQ-008, REQ-032, REQ-034 | TASK-007, TASK-009 |
| TASK-011 | PHASE-003 | Verify the frozen inputs and start each case in a fresh store | REQ-006, REQ-010, REQ-012 | TASK-010 |
| TASK-012 | PHASE-003 | Apply the V1 and V2 edits and observe the accepted source | REQ-013 | TASK-011 |
| TASK-013 | PHASE-003 | Submit the N1 candidate and observe rejection and preservation | REQ-014 | TASK-011 |
| TASK-014 | PHASE-003 | Create the accepted-state record and bind the delivered artifacts | REQ-015 | TASK-012 |
| TASK-015 | PHASE-003 | Record every exchange and exercise failure and retry | REQ-020, REQ-033 | TASK-012, TASK-013 |
| TASK-016 | PHASE-004 | Observe geometry, motion and declared relationships from the actual bytes | REQ-007, REQ-016, REQ-017 | TASK-014 |
| TASK-017 | PHASE-004 | Implement the missing observations within the recorded boundary | REQ-008, REQ-010, REQ-016 | TASK-010, TASK-016 |
| TASK-018 | PHASE-004 | Score each case and write the per-property results | REQ-010, REQ-016, REQ-017 | TASK-016, TASK-017 |
| TASK-019 | PHASE-004 | Rebuild each valid case in an empty workspace | REQ-018 | TASK-014, TASK-018 |
| TASK-020 | PHASE-004 | Add the residual controls that the workflow depends on | REQ-009 | TASK-009, TASK-016 |
| TASK-021 | PHASE-004 | Run the deliberate-fault and positive controls through the workflow's own checks | REQ-015, REQ-019 | TASK-018, TASK-019 |
| TASK-022 | PHASE-004 | Assemble the one documented command | REQ-011 | TASK-015, TASK-020, TASK-021 |
| TASK-023 | PHASE-005 | Run the fresh replay | REQ-021 | TASK-022 |
| TASK-024 | PHASE-005 | Prepare the visual-verification profile | REQ-005, REQ-023 | TASK-022 |
| TASK-025 | PHASE-005 | Validate the regenerated GLBs | REQ-022 | TASK-023, TASK-024 |
| TASK-026 | PHASE-005 | Inspect the playback and record the observation | REQ-022, REQ-031 | TASK-025 |
| TASK-027 | PHASE-006 | Run the checks that the changed scope requires | REQ-005, REQ-024, REQ-034 | TASK-023, TASK-026 |
| TASK-028 | PHASE-006 | Compare failing checks with main on the same host | REQ-025 | TASK-027 |
| TASK-029 | PHASE-006 | Publish the deliverable evidence on the scope's branch | REQ-028, REQ-033 | TASK-023, TASK-025, TASK-026 |
| TASK-030 | PHASE-006 | Write the report with the readiness table | REQ-007, REQ-028, REQ-029, REQ-031, REQ-033, REQ-034 | TASK-028, TASK-029 |
| TASK-031 | PHASE-006 | Audit every requirement and every changed file | REQ-003, REQ-006, REQ-032, REQ-033 | TASK-030 |
| TASK-032 | PHASE-006 | Obtain the independent review of the exact candidate | REQ-026 | TASK-031 |
| TASK-033 | PHASE-007 | Integrate under the lease and verify the resulting main | REQ-025, REQ-027 | TASK-032 |
| TASK-034 | PHASE-007 | Resolve the branch and the worktree | REQ-027 | TASK-033 |
| TASK-035 | PHASE-007 | Close the scope on the local closing state | REQ-030, REQ-031, REQ-033 | TASK-034 |

Phase gates: each phase follows the one before it. PHASE-004's new observations (TASK-017)
also wait for the owner's recorded answer to the gap record of TASK-010 wherever a missing
observation needs an independent interpretation of source expressions (DEC-006); work that
does not depend on such an observation continues. Integration (PHASE-007) waits for the
independent review of the exact candidate (TASK-032).

No step carries out, completes or depends on C271's phases P02 to P38, the current-host
readback contracts, their preparation, their host qualification or gate MR, and no step
needs a commit that only the closed pull request 274 holds.

## Ownership

The Director owns the task record, `STATUS.md`, `CURRENT.json`, the index and commits of
this branch, the main integration lease and all publication. Workers own only the paths
assigned to them and return results to the Director. The independent reviewer inspects and
reports and changes nothing (DEC-011).

## Deviations from the approved plan

None so far. A deviation is recorded here with the step, what the plan says, what was done
and the reason.
