# C269 one-phase plan

Starting main `23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb`. One phase: audit existing H01-H28 coverage, independently review it, publish and save the verified handoff, then stop.

## P01 — Scope, reconciliation and early recovery

Requirements: R01, R06. Outputs: `docs/workflow/tasks/C269/SESSION.md`, `docs/engineering/localized-repair-c269/EARLY-RECOVERY-RECEIPT.json`. Verification: Live reconciliation, exact startup read-set and confirmed early save.

## P02 — Independent coverage investigations

Requirements: R01, R02. Outputs: `docs/engineering/localized-repair-c269/COVERAGE.json`, `docs/engineering/localized-repair-c269/INPUT-IDENTITIES.json`. Verification: Actual assertion and source/evidence identity inspection for every H group.

## P03 — Synthesis, checks and independent review

Requirements: R02, R03, R04. Outputs: `docs/engineering/localized-repair-c269/AUDIT.md`, `docs/engineering/localized-repair-c269/NEXT-TASK.md`, `docs/engineering/localized-repair-c269/REVIEW.json`. Verification: Fresh documentation/workflow checks and exact-candidate independent review.

## P04 — Integration and actual-main checks

Requirements: R05. Outputs: `docs/engineering/localized-repair-c269/INTEGRATION.json`. Verification: Expected-head integration, exact readback, fresh main checks and retained-history disposition.

## P05 — Saved handoff, receipt and closure

Requirements: R06. Outputs: `docs/engineering/localized-repair-c269/DELIVERY.json`. Verification: Safe ZIP, manifest/extraction/source verification, confirmed saves and external receipt.

## Ownership, dependencies and risks

Director owns canonical task/CURRENT/STATUS, synthesis, Git index, commits, remote writes, lease and delivery. Two fresh-context investigators own disjoint H-group audit reports. A separate state investigator reviews the final candidate independently; no nested fanout. Workers write detailed evidence to assigned paths and return short summaries.

Dependencies are the unchanged C260 contract and existing component evidence. Main risk is mistaking partial assertions or a passing test count for complete qualification. Map material subcases, preserve exact execution provenance and expose absent or conflicting evidence. Reuse prior execution only after implementation, dependencies, fixtures, tests, commands and applicable environment bindings are established. Newly executed checks cover audit/document structure only.

## Stop

No missing control is implemented here. Stop after verified saved delivery or the first unplanned expansion with an honest partial handoff. Keep the task and scope issue open until all R01-R06 gates pass.
