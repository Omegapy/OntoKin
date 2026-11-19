# C268 one-phase plan

Implement, independently verify/review and integrate the finite historical endpoint reader; save verified delivery and stop.

Starting main: `b2ca38875bd7b43b85011bbc671ee9fee1682441`. Owner: `c268-root-c7dae94da130`. [Requirements](REQUIREMENTS.md).

## P01 — Scope and early recovery

Requirements: R01, R02, R03. Pinned startup, live reconciliation and confirmed early save.

Artifacts: `docs/workflow/tasks/C268/REQUIREMENTS.md`, `docs/workflow/tasks/C268/PLAN.md`, `docs/engineering/localized-repair-c268/EARLY-RECOVERY-RECEIPT.json`.

## P02 — Reader and independent controls

Requirements: R01, R02, R03, R04. Positive and adversarial independent controls.

Artifacts: `docs/engineering/localized-repair-c268/endpoint_reader.py`, `docs/engineering/localized-repair-c268/test_endpoint_reader.py`.

## P03 — Affected checks and exact review

Requirements: R04, R05. Complete affected cohort and independent review.

Artifacts: `docs/engineering/localized-repair-c268/RESULTS.md`, `docs/engineering/localized-repair-c268/REVIEW.json`.

## P04 — Integration and actual main

Requirements: R06. Conditional merge, fresh affected main checks, retained ancestry and branch disposition.

Artifacts: `docs/engineering/localized-repair-c268/INTEGRATION.json`.

## P05 — Verified saved handoff and closure

Requirements: R07. ZIP/extraction/source verification, confirmed save, external receipt and closure.

Artifacts: `docs/engineering/localized-repair-c268/DELIVERY.json`.

## Ownership and checks

Director owns tasks, shared state, evidence, Git index/commits, all remote writes, lease and delivery. Independent implementer owns endpoint_reader.py and an implementation report. Independent control author owns test_endpoint_reader.py, fixtures/control evidence and CONTROL-COVERAGE.md. A separate investigator reviews the exact candidate. Workers use fresh context and inherited model configuration, no nested fanout.

The complete affected cohort is the C253 corpus and C255/C256/C257/C258/C261/C265/C266/C267/C268 isolated observation components, plus workflow/documentation checks. No shared product code changes; complete product/Agent/export/native/visual/model/compatibility suites are not claimed. Unchanged historical failures remain visible. New/worsened affected failures block integration.

## Stop

Stop after confirmed final delivery, or first unplanned scope expansion with honest partial handoff; no next phase. Parent stays in_progress or review until every gate passes. A partial handoff is session delivery only.

Reviewer continuity: `/root/state_audit` launched with fresh context for startup, then retained that context for follow-up early-package and candidate review. Implementation/control workers launched separately with fresh contexts. No worker is represented as reset between follow-ups.
