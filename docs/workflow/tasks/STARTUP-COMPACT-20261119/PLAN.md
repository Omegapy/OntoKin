# One phase: compact startup instructions

Base: `7ff41e071fb694dadf1ba256b13168e1a4083926`. Owner: `startup-compact-9c7a0c0e0469`. Branch: `work/startup-compact-20261119`.

## P01 — Scope and early recovery

Requirements: R01. Outputs: `docs/engineering/startup-compact-20261119/PRESERVATION.json`.

## P02 — Compression and preservation

Requirements: R02, R03, R06. Outputs: `docs/engineering/startup-compact-20261119/METRICS.json`.

## P03 — Independent review and checks

Requirements: R04. Outputs: `docs/engineering/startup-compact-20261119/REVIEW.json`.

## P04 — Integration and saved delivery

Requirements: R05. Outputs: `docs/engineering/startup-compact-20261119/DELIVERY.json`.

Director owns task/evidence, Git publication, lease and packaging. Disjoint writers compress assigned documents; separate reviewer checks exact originals/candidate. No worker changes shared state or launches workers. Preserve C268 branch, task, evidence, CURRENT and its reserved state; acquire an integration lease only after observed expiry/release and reconciliation.

Checks: exact before-image and README hashes; links/anchors; obligation coverage; before/after size and available-tokenizer counts; workflow and documentation verification on candidate and actual main. No runtime changes or broad product qualification. Stop after saved handoff; a partial phase retains unmet gates.

A reversible packet experiment belongs to this phase and is preserved with 23 focused tests and independent review; it is excluded from active startup after measured low savings. Final production change is documentation only: compact records and mandatory-source deduplication, plus explicit omission of empty STATUS navigation-anchor lines from routine readout. Anchor bytes remain unchanged and required for history/link work. Full-file and readout metrics remain separate.
