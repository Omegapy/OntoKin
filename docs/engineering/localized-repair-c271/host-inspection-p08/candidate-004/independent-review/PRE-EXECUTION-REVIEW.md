# Candidate 004 independent pre-execution review

## Verdict and scope

Candidate004 is approved for one bounded 135-method focused run after root verifies the clean source checkpoint, exact reviewed identities, fresh evidence location, reviewed outer harness and explicit run grant. This approval does not authorize the reviewer to execute anything and does not accept the implementation.

Run001 on candidate003 failed during a shared test-fixture setup. The independent run review and corrected complete evidence audit are retained under review_work/run-001. Candidate004 addresses exactly that setup failure. All failures, earlier candidate snapshots and prior review records remain preserved.

## Exact reviewed change

Production module bytes are identical to candidate003: 147,900 bytes, SHA256 b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39.

The test snapshot is 139,313 bytes, SHA256 797eb208670f6f74f14c9b5849485bd6cf3522a265d4129618c4b50ddc0a739a. Independent byte comparison proves that its only change is the authorized line468 replacement from `patch.object(inspection, "_EvidenceStore.write", new=writing)` to `patch.object(inspection._EvidenceStore, "write", new=writing)`.

The helper captures the original class method before patching. The corrected call patches that class's `write` attribute with the unchanged function, which receives the store instance and delegates to the original writer after recording the requested path and invoking any configured fault. It changes target resolution only. All input construction, mutations, live predicates, mocks, assertion bodies, expected results and selected method definitions are unchanged.

The unchanged production and control assertions reuse the earlier complete static review chain, including PRE-01 through PRE-14, DTR-01 through DTR-09, C01-01 through C01-05, the named PATH Git closure relation, and C02-01 strict process-group integer checks. Their unchanged source hashes and control anchors have been verified. The failed runtime attempt revealed a fixture defect missed by that review; no implementation success is inferred from the static decisions.

## Mapping and integrity verification

All eight payloads in FREEZE-MANIFEST.json match their declared hashes and sizes. The exact map is 532,303 bytes, SHA256 9f9adb0979c228b6eede5f75db8a0649ddd3cebd73f239d29020e1c53a6c35b0. Every one of its 113 unique definition anchors matches its exact source byte span. All bound external inputs, source snapshots and unchanged guarded runner match their identities.

An exhaustive structural comparison with the accepted candidate003 map finds only: two candidate identity changes; 132 candidate path bindings; 131 test-file digest bindings; 20 corrected observation-helper digest bindings; and two added failure/correction history records. No oracle, predicate, route, mutation, count or assertion expectation changed. The readable map and disposition report record the same one-line correction and preserved failure.

The selection remains 109 original negative controls, five positive controls, 16 supplemental groups and five scoped regressions: 135 test methods. The independent base freeze, supplement and approved state correction bytes are unchanged. The original counts remain explicit, including the separately qualified serialization fixture.

The guarded runner remains 2,686 bytes, SHA256 27489064a600ea3cfba73381fa1f75cc781cdc72303bd97ee200c6ebdb4aafdd. Its pre-import process guards, complete selection, failfast behavior and result recording are unchanged. Run002 intent selects that runner once, declares the fresh run-002 root, retains all inputs/logs/fixtures, uses the same 180-second outer bound, and forbids replay. Root owns review and grant of the outer wrapper; this report binds its exact proposed identity without substituting for root's wrapper review.

## Preserved qualifications

- P08-D05 changes only HI17-D and HI18-A/B/C expected_state from REJECTED to UNKNOWN, preserving all other obligations.
- P08-D06 treats AS_RECORDED as a retained-content/graph statement. Durability stays UNKNOWN, evidence_finalized false and approval false. Read-only reconciliation adds no write, fsync, retry or log-tail authority.
- P08-D07 qualifies HI16-C as a live serialization-size guard with actual OS starts0, newly mocked supervisor starts0 and one supplied synthetic historical PID. Its original generic count reference and independent state-machine count controls remain intact.

## Required run boundary

Root must identify a clean published source checkpoint containing exactly these module/test bytes and preserved protected files before granting the single attempt. Execute only the mapped new focused test module through the unchanged guarded runner and reviewed bounded outer wrapper. Keep command, environment, complete separate logs, final result, fixtures/manifests and source/map/oracle identities. Stop after any result; failed or uncertain outcomes remain retained, and neither code changes nor another attempt follow without a new disposition.

Actual Node/ldd, host observations or qualification, runtime preparation, original seven methods, complete routine, integration, PR merge and parent closure remain outside this approval. Parent C271 and R03-R05 remain open. Independent post-run implementation review and final package verification still have to pass.

## Review evidence

- STATIC-VERIFICATION.json contains exact byte comparison, all anchors, input bindings, all map differences and zero static verification errors.
- test_current_host_inspection_v01.diff contains the independently generated one-line diff.
- review_work/run-001/REVIEW.md and VERIFICATION-002.json classify and verify the preserved failed attempt.
- PRE-EXECUTION-APPROVAL.json binds this report, candidate files, map, freeze, unchanged runner, run intent and outer-wrapper identity.

Reviewer activity: zero candidate imports, zero compilations, zero test runs, zero project process starts, zero source edits and zero Git operations. No mandatory residual static finding blocks the narrowly scoped next run. Implementation acceptance remains false until that result and its evidence are independently reviewed.
