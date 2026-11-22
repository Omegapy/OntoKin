# Final P19 package builder review

The builder’s recovery and source-copy logic is suitable for the final package. Exact Git bytes, the unchanged lock, final P19 evidence, all six session evidence roots and failed evidence are retained. Existing archive replacement is refused; CRC, inventory and payload hashes are verified after extraction. Final acceptance still requires the actual frozen ZIP.

Before freeze, add explicit worker dispositions to PHASE.json. Current entries give only identity/role/owned paths, while generated recovery prose claims actual worker status is identified. State that the operational and documentary reviews are complete and the final package audit/save remains pending; identify any current process/write state separately.

One provenance robustness issue remains: final P19 paths come from `git ls-files` (the index), while bytes come from the frozen revision. No current omission is established. Selecting paths with `git ls-tree -r --name-only <revision> -- docs/engineering/localized-repair-c271/actual-input-p19`, or checking exact equality before freeze, makes the inventory source explicit.

Core publication is expected to remain pending during this review. Before builder invocation, final phase/prose must bind actual published commit/tree/readback and documentary checks while preserving the rpds-py mismatch, unaccepted H0 and pending final save. Missing final prose inputs already fail closed.

Read-set identities and precise findings are in FINAL-BUILDER-REVIEW.json. No technical checks, host observations, repository mutations or external operations occurred.
