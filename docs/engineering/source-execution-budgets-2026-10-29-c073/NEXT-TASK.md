# C074: configurable execution budgets in the Agent lifecycle

Resume from the latest reviewed C073 main after reconciling its actual Git identity, STATUS, integration lease, branches, PRs and issue scope closure under [AGENTS](../../../AGENTS.md). Preserve the complete [GOAL](../../../GOAL.md). The next bounded language capability is explicit `ontokin.agent/0.7` for source `0.7` / `planar-reach-budget-0.1`; the current source/CLI increment does not expose that service.

## Required increment

Extend the existing source-authoritative Agent workflow to use the [adopted host-policy and shared-budget model](../../language-design/execution-budgets-v0.1/ADOPTION-C073.md). Preserve earlier Agent protocols, command defaults, source revisions, diagnostics, finite limits, original test/fixture bytes and the unchanged 100,000-operation / 30,000-ms gates. Policy belongs to the trusted service host. Source and request fields can request or reduce resources but cannot grant a ceiling.

1. Publish a separately versioned Agent/0.7 decision, discovery contract and exact operation schema before exposing it. Report current defaults, host ceilings, accepted source requests, effective limits, consumed work, original deadline, implementation identity and terminal status. Keep the earlier schemas and protocol versions intact.
2. Admit each candidate entry source with a fresh provisional ledger, then promote that same ledger only under the current host policy. Imports, body construction, evaluation, recording, output checks and in-request supplied-byte validation share the remaining work and original monotonic start. A large allowance in a saved artifact or previous request grants no new authority.
3. Exercise actual create/edit acceptance and failure: exact UTF-8 patch preconditions, atomic source changes, authorization rejection, over-budget construction, accepted-revision rollback and source repair. On failure, retain the earlier accepted revision and artifact identity; report only an established valid prefix.
4. Reauthorize saved-program and saved-run requests under the current host policy and requested output level. Define a fresh per-request ledger and separate aggregate service limits. Do not silently resume with a previously larger allowance, trust artifact metadata or replace requested exported output with represented success.
5. Execute evaluate/export/retrieve, cancellation, repeated and idempotent requests, failure/retry paths, and cross-request isolation. Retain bounded JSON, source/object/output, operand, cache, cursor, sampling/key and artifact limits. Cancellation must preserve caller identity/order and publish no partial artifact.
6. Add new tests and actual protocol transcripts for the five deferred [conformance-plan](../../language-design/execution-budgets-v0.1/conformance-plan.json) cases: EB-15, EB-16, EB-18, EB-24 and EB-29. Reuse the frozen C073 workload only with its exact source/expected hashes and separately identified Agent evidence. A successful direct API call is not an Agent lifecycle test.

## Completion and evidence

Run the relevant full inherited regression cohort and unchanged local-driver roles on the exact candidate, plus the five new lifecycle cases, source-to-delivery workflow, independent destination checks and actual visual review for the claimed output. Preserve every failure, timeout and recovery. Record the current implementation, input hashes, interpreter/platform, commands, artifacts, reviews and actual merge/resulting-main checks. Integrate under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md) only after applicable gates pass; keep complete feature release distinct from this bounded development increment.

Historical original28 remains 24/28 failed, with P11/P16/P23/L03 unresolved under the original settings. M1 remains rejected; C035 remains held including adverse timing; C057, complete reach acceptance, missing compatibility/external roles and historical LFS migration remain open. No higher-budget success retroactively passes an original fixed-budget gate.

After this Agent increment, select and implement a representative next modeling, animation or simulation capability from GOAL. Another open-ended optimization investigation is not a prerequisite. Do not start an unscheduled continuation merely because this handoff names the next task.
