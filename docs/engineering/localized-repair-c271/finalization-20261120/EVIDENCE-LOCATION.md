# C271 P02 evidence locations

`PHASE-OUTCOME.json` records the blocked phase decision. The required routine driver failed; the complete affected cohort passed. Neither a saved partial handoff nor successful evidence audits satisfy the failed integration gate.

## Canonical evidence

- `verification/REPORT.md` explains both original runs and their limits.
- `verification/RESULTS.json` records exact outcomes, identities and the external raw-archive receipt.
- `verification/RAW-EVIDENCE.zip` preserves all 73 raw payload files and its manifest. Paths such as `routine-candidate/logs/unit-tests.log` are archive members. The adjacent manifest and verification receipt identify their bytes.
- `verification/AFFECTED-RAW-EVIDENCE.zip` is the earlier published affected-only checkpoint. It remains historical evidence even though the complete archive includes that run.
- `independent-review/REPORT.md` and `INTEGRATION-REVIEW.json` record the independent not-eligible verdict. Other files in that directory preserve source inspections, corrected reviewer assumptions and their initial outputs.
- `operation-history/` retains verified publication identities, the unsuccessful credentialless CLI push, the unpublished equivalent commit object, and clean record checks. The failed push was reconciled before the successful conditional API publication.

Review files retain their original worker workspace paths and exact bytes. Their `../validation/` paths identify original execution locations; the corresponding complete payloads are inside `verification/RAW-EVIDENCE.zip`. A clean copied source tree is not embedded again: the source commit/tree, complete input manifests, initial five-file omission and zero-unique-change comparison are preserved.

## Delivery boundary

The final online session ZIP freezes an identified published candidate. Its later `P02-DELIVERY.json` receipt is separate and records the actual saved ZIP and two matching prompts. Receipt-only publication does not change behavior or repair either failed gate. C271, issue #273 and draft PR #274 remain open; the branch remains unmerged. Main receives no change from this phase.
