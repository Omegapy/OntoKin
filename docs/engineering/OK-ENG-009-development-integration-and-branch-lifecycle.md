# Development integration and branch lifecycle

**Identity:** `OK-ENG-009/0.1.0`  
**Date:** October 28, 2026  
**Decision state:** Adopted operational policy under the owner-authorized C059 scope. Actual integration, checks and cleanup are recorded separately.

## Purpose and authority

Keep reviewed development moving into `main` while preserving honest capability boundaries, released behavior and the full [OntoKin goal](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/GOAL.md): a programming language primarily for AI agents to create, inspect, revise and reuse meaningful 3D objects and behavior through authoritative `.ok` source.

This decision clarifies the development-integration procedure in [AGENTS.md](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/AGENTS.md). It separates integration of a bounded increment from acceptance of an entire finite release. It changes no adopted language semantics, numerical limits, expected corpus, independent oracle or release requirement. Frozen contracts and historical evidence retain their exact bytes and meaning.

## 1. Main is the current development baseline

`main` may contain reviewed, explicitly incomplete development capabilities alongside released capabilities. Every integration record must identify which state applies to the affected feature:

| State | Required meaning |
| --- | --- |
| Released | The named scope has its complete adopted release evidence and verified integration. |
| Integrated development | The identified increment satisfies the development gates below; the broader feature remains incomplete or experimental. |
| Held or rejected | The change is retained for review or history and is not activated by integration of its evidence. |

A branch merge does not convert an integrated development capability into a released capability. Versioned releases remain the record of complete supported promises. Current STATUS must identify both the latest integrated development state and the latest accepted release state, with their exact revisions.

For planar reach, [OK-LANG-006/0.1.0](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/docs/language-design/planar-reach-v0.1/ADOPTION.md) and its [complete release contract](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/docs/language-design/planar-reach-v0.1/release-contract.md) retain every mandatory role and R01–R12/Q01–Q22 requirement. Incomplete source recording, delivery, compatibility, numerical or destination evidence remains failed or pending as recorded. No subset is relabeled as the complete release.

## 2. Contain experimental runtime behavior

An incomplete capability must have an actual enforceable entry boundary, such as its explicit source/profile or Agent/destination version. Discovery, documentation and diagnostics must identify its development status, supported behavior, limits and known failures. A status label alone is insufficient if runtime routing silently changes earlier supported behavior.

Earlier source, Agent and destination bindings retain their meanings. Experimental paths must not become an implicit default, satisfy a higher requested output level with lower-level success, or present unsupported output as valid. Existing revision integrity, failure atomicity, rollback, cancellation, resource limits and artifact identity remain mandatory. Unsupported requests must fail explicitly at the correct boundary.

Review every runtime change included by a stacked history. Held instrumentation or rejected optimizations need an explicit disposition before integration; their presence in a later evidence branch is not acceptance. If the incomplete implementation cannot be isolated from released paths, resolve that issue before integrating it. Documentation and preserved evidence can be integrated separately when their own checks pass.

## 3. Development integration gates

The integrator must establish all of the following for the exact candidate and current main:

1. **Identity and scope.** Record observed base and candidate commits/trees, changed files, dependencies, selected behavior, held changes and applicable checks. Review the cumulative change, including inherited runtime and workflow changes.
2. **Legacy regression.** Actually execute the complete required regression cohort for previously released behavior affected by the integration, with a justified inventory that preserves every applicable preexisting obligation. Required tests must pass without failures, errors or skipped obligations. For changes to shared language, construction, numerical, Agent or delivery machinery, use the complete inherited regression cohort. A prior green label, unchanged version string or new-feature-only cohort cannot establish this gate.
3. **Changed behavior.** Execute the relevant positive, boundary, negative and failure-path checks for the increment. Preserve original expectations and independent checks. The scope of successful checks must match the capability claimed.
4. **Failure accounting.** Retain every actual full-suite result, timeout, failure and interruption. Distinguish an unchanged failure of an explicitly incomplete feature from an introduced regression using exact input identities and observed evidence; reproduce uncertain cases. A failure is not exempt merely because it is called preexisting. New or worsened failures in released behavior block integration.
5. **Honest limits.** Record the actual interpreter/platform, missing compatibility or external roles, unresolved feature gates and enforceable runtime containment. Successful execution on one interpreter establishes only that interpreter. Missing release evidence remains pending; an executed contradiction remains failed.
6. **Resulting main.** Integrate through the verified lease and expected-head procedure below. Verify the actual resulting commit/tree, establish eligible input equality where prior candidate evidence is reused, and run relevant checks on resulting main. A main failure requires a scoped repair or revert with preserved evidence; do not leave it hidden behind the candidate's green result.

A known failure in a correctly contained incomplete feature does not by itself certify or prohibit every unrelated increment. The decision must name its actual effect on the change and on released behavior. Any unresolved effect on a required development gate blocks that integration.

Use the existing local validation policy, [OK-ENG-006](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). Documentation-only changes use the preservation/link checker; runtime changes require the applicable actual runtime checks. Hosted workflows remain manual-only with default-false opt-in. This decision authorizes no paid or hosted execution and does not replace exclusive executor procedures where they apply.

## 4. Integrate through short, owned scopes

Use **one branch per active bounded work scope**, normally with **at most three active work branches** across the project, excluding `main` and retained archival references. Additional active branches require a recorded owner, distinct scope, dependency and reason. This default supports parallel work while keeping its integration order visible.

Checkpoints are commits and evidence records on the active scope branch, not a reason to create another branch. A resumed session reconciles the existing head and ownership before continuing that scope. Create a new branch when the work has a genuinely distinct ownership or dependency boundary, or when the prior scope is complete.

Each active scope records its owner, starting commit, affected files/features, dependencies, acceptance checks and concrete next action. Prefer a branch from current main. A stacked dependency must be explicit and short-lived; after the dependency integrates, reconcile the successor against actual main before publishing further changes.

Main integration remains serialized. Read the current refs, STATUS, issue handoffs and relevant CI; acquire or renew the bounded integration lease through the existing observed-head procedure. Use an expected-head conditional/nonforce update or protected PR merge. Never force-move main. Reconcile uncertain outcomes before retrying. Independent nonoverlapping work may continue under its own ownership.

After a verified integration, update concise current STATUS, close the completed scope and release or renew the lease at a substantive checkpoint. The next task should address a concrete remaining product or engineering requirement rather than reproduce a completed decision in another checkpoint.

## 5. Preserve history before retiring branches

Every existing branch must receive an explicit disposition: active, integrated, superseded, rejected or deferred. A branch may contain valuable history even when its runtime change is rejected.

Before deleting a branch:

1. Record its exact name, observed head and tree, related PRs, ownership, dependencies and disposition in the reconciliation manifest.
2. Create and read back a retained archival reference at that exact head, or a retention commit whose verified parent graph contains it. Bind every original name and head in an exact manifest, and verify the complete retention graph before removal. Preserve the reachable commits and evidence. Archive references must not be overwritten to alter historical results. An index-only retention commit must never be merged into main or used as a product development base.
3. Identify the successor or integration commit, or the unresolved work retained for a deferred scope. Preserve a mapping from old branch/PR references to commit permalinks and the archival ref; do not rewrite frozen evidence to hide old links or findings.
4. Confirm the branch has no active owner, unresolved write or dependent work that requires the live ref. Recheck its head immediately before removal. If concurrent mutation cannot be excluded, retain the branch until ownership is reconciled.
5. Record the actual deletion result separately from its planned disposition. A timeout or unknown response requires readback before retrying.

A deleted branch's archived head is recoverability evidence, not proof that its code was merged or accepted. Do not delete historical artifacts, failed attempts, reviewed input manifests or independent oracles as branch cleanup.

## 6. Resolve stacked PRs with provenance

A superseded PR may be closed once its final head is preserved and its disposition is recorded. Its closure record must identify the final head, archival ref, successor/integration PR or commit, reason for closure and any unresolved obligations carried forward.

Close unadopted or rejected proposals with that status. Close consolidated evidence PRs as superseded when appropriate. Use merged status only when an actual merge occurred. Do not infer release acceptance from either closure or integration.

Keep current STATUS short: released capability, integrated development capability, current owner/scope, exact latest evidence, known blockers and the next unmet goal. Detailed history belongs in linked records and the reconciliation manifest. Deferred domains from GOAL remain visible; no finite reach milestone completes OntoKin.
