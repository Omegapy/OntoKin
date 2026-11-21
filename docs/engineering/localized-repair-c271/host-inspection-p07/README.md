# C271 P07 — accepted host-inspection design

The exact design candidate is independently accepted for a later bounded implementation. [ADOPTION.json](ADOPTION.json) supplies the decision without changing the reviewed candidate bytes. Read [HOST-INSPECTION-DESIGN.md](HOST-INSPECTION-DESIGN.md), [QUALIFICATION-PLAN.md](QUALIFICATION-PLAN.md), the [control matrix](CONTROL-MATRIX.json), and the [independent review](review/REPORT.md).

The existing P06 provider consumes successful host observations but lacks their authoring entry point. This design adds a separately approved static inspection plan before observation, preserves P06's closed success schemas, and keeps failures and uncertain process counts in separate evidence records. It authorizes no execution.

The first later technical phase is the single authoring module and focused controls (HI). It stops before runtime preparation or Node/ldd. Actual host observations, original-seven outcomes, Gate H, the complete routine/R03, integration/R04 and parent closure/R05 remain unmet. [PHASE-OUTCOME.json](PHASE-OUTCOME.json) records the current boundary.

Earlier candidates, author drafts and failures remain in the saved handoff's `session/audit/host-design/` tree. Relative history references inside unchanged author records refer to that audit tree. The current exact candidate manifest is [DESIGN-CANDIDATE.json](DESIGN-CANDIDATE.json); reviewed payload hashes must continue to match it. This folder's later `P07-DELIVERY.json` records confirmed ZIP and prompt saves; PR #274 carries the final supplemental verification receipt identity.
