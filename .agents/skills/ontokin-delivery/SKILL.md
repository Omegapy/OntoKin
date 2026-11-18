---
name: ontokin-delivery
description: Implement, review, verify, integrate, and close one authorized OntoKin milestone. Use for work requiring durable requirements, an implementation plan, GitHub publication, or a verified continuation checkpoint.
---

# Deliver one OntoKin milestone

Read [AGENTS.md](../../../AGENTS.md), [ROLE.md](../../../ROLE.md), and
[PROTOCOL.md](../../../docs/workflow/PROTOCOL.md). This repository procedure
does not grant capabilities or expand authorization. Follow the existing
[development integration policy](../../../docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md).

## Define and implement the work

1. Identify the user's outcome, constraints, exclusions, and observable
   completion criteria. Give each material requirement a stable ID and source.
2. Map every requirement to planned work, dependencies, artifacts, ownership,
   risks, and verification. Preserve the difference between a requirements
   document, a plan, task state, and the product's release state. Do not invoke
   the separate managed `to-trd` or `to-implementation-plan` skills without
   their explicit invocation.
3. Reconcile the starting revision and active branch. Maintain one branch per
   bounded scope; keep checkpoints as commits. Respect shared-file ownership
   and the main integration lease.
4. Implement the authorized plan. Use bounded subagents when available and
   useful. Record material decisions and return design defects to the Director.
   Do not mark an in-scope requirement complete by silently reducing it.

## Verify the candidate

Inspect the actual changed files and each requirement's evidence. Execute
checks proportionate to the change under
[OK-ENG-006](../../../docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md).
Record the code revision or exact file hashes, inputs, command, interpreter,
platform, result, and log location. Preserve failures and interruptions.

For documentation and navigation, execute:

```sh
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
python3 tools/chat_workflow.py check
```

For runtime, semantics, exporters, or Agent interfaces, also execute the
applicable checks required by AGENTS and their adopted contracts. Structural
workflow checks do not certify language semantics or destination behavior.
Do not enable paid or automatic hosted jobs to substitute for local evidence.

Obtain the independent review required by the selected scope. Give the reviewer
the actual current artifacts and acceptance criteria. Distinguish independent
review from the author's self-check. Resolve mandatory findings and re-review
affected changed inputs; do not reuse a stale pass. If required review cannot
run, record the unmet gate.

## Integrate and verify actual main

The verified integration owner reviews the candidate against current main and
performs an authorized conditional/nonforce update or protected PR merge.
Reconcile an unknown result before retrying. Confirm the actual merge commit
and tree; run relevant checks on resulting main. If reusing prior evidence,
establish the input equality that makes it applicable.

A merged increment remains distinct from a complete product release. Preserve
unmet source, destination, comparative, and historical gates. Record blocked
integration as blocked rather than claiming completion from a branch pass.

## Close and hand off

1. Evaluate [ontokin-learning](../ontokin-learning/SKILL.md) after substantive
   verification. Record whether useful durable findings were captured or why
   capture was skipped; respect opt-out.
2. Update the task's requirement coverage and verification evidence, concise
   CURRENT/STATUS pointers, ownership disposition, and exact next action.
   Reopen and verify the durable GitHub checkpoint at its published revision.
3. For a completed branch, verify retained history, its latest head, absence of
   active ownership or unknown writes, and the integration result before
   deletion. Observe deletion rather than assuming it. If deletion is pending
   or unavailable, tell the user the exact completed branch to delete and retain
   that cleanup obligation in the checkpoint. Do not leave it unexplained.
4. Release or renew integration ownership at a substantive checkpoint. Report
   changed behavior, actual checks, integration and branch disposition, remaining
   limits, and the stable continuation entry.
5. Stop at the bounded milestone. A future ZIP is optional unless the current
   user request explicitly requires one; when required, verify and save that
   exact archive before claiming delivery. Do not replace a still-open earlier
   ZIP obligation with a new documentation-only completion claim.
