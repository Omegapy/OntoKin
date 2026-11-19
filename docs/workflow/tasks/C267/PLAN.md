# C267 implementation plan

Owner: `c267-root-ad39e933f0f3`. Branch: `work/c267-hinge-comparison`. Base: `47681b1e4c442a580910dba1fc5a823dc86ee6b0`. [Scope260](https://github.com/Omegapy/OntoKin/issues/260). [Requirements](REQUIREMENTS.md).

## P01. Publish scope, requirements, plan and recovery checkpoint

Requirements: R01, R02, R03, R04.

Artifacts: `docs/workflow/tasks/C267/REQUIREMENTS.md`, `docs/workflow/tasks/C267/PLAN.md`, `docs/workflow/tasks/C267/SESSION.md`.

Verification: Verify pinned startup reads, actual refs and saved recovery.

## P02. Implement comparator and independent controls

Requirements: R01, R02, R03, R04, R05.

Artifacts: `docs/engineering/localized-repair-c267/hinge_compare.py`, `docs/engineering/localized-repair-c267/test_hinge_compare.py`.

Verification: Run independent changed-input and adversarial controls.

## P03. Verify candidate and resolve independent review

Requirements: R05.

Artifacts: `docs/engineering/localized-repair-c267/RESULTS.md`, `docs/engineering/localized-repair-c267/REVIEW.md`.

Verification: Run C253/C255/C256/C257/C258/C261/C265/C266/C267 and metadata checks; exact-candidate review.

## P04. Integrate and verify actual main

Requirements: R06.

Artifacts: `docs/engineering/localized-repair-c267/INTEGRATION.json`.

Verification: Expected-head lease and PR merge; fresh main checks; ancestry and branch absence.

## P05. Freeze, verify, save and close

Requirements: R07, R06.

Artifacts: `docs/engineering/localized-repair-c267/DELIVERY.json`.

Verification: Exact ZIP manifest, fresh extraction and source snapshots; confirmed saved identity; external receipt.

## Ownership and bounded checks

Director owns documentation, task and evidence records, Git index/commits, all remote writes, STATUS/CURRENT under the verified main lease, packaging and delivery. `/root/comparator` owns only `hinge_compare.py`; `/root/controls` owns the independent test and control fixtures/coverage. `/root/reconcile` audits starting state and later independently reviews the exact candidate. All workers inherit the parent configuration; no external model runner is used.

This isolated standard-library engineering observer is not imported by product runtime. No released runtime/exporter/parser, existing component, contract, fixture, workflow or budget changes. The complete affected regression cohort is the C253 static corpus and C255/C256/C257/C258/C261/C265/C266/C267 components, plus workflow and preservation checks. Full product aggregate, native/visual/export/model trials, hosted workflows and other interpreter roles remain not-run; historical failures retain their states. A shared product change requires scope revision and complete inherited checks first.

Publish recoverable progress after scope, implementation, verification, integration and delivery. Retain failures and unique prior unpublished metadata as inert historical recovery, without restoring stale leases/task state. Freeze once, save the ZIP and prompts, publish the external receipt, close and stop.
