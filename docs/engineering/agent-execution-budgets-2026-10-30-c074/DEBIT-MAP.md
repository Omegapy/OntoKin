# C074 request accounting

Agent/0.7 composes the [C073 ledger](../source-execution-budgets-2026-10-29-c073/DEBIT-MAP.md) with durable request publication. No source or artifact field supplies policy. The trusted service snapshots one immutable `HostPolicy` at worker admission. Work queued earlier uses the policy at that admission; identical terminal retries return their historical receipts without a second execution.

| Stage | Actual accounting and boundary |
| --- | --- |
| JSON transport and queue admission | Existing finite JSON/source shapes are checked before queueing. Separate trusted limits bound pending and running rows in the local database. Control and cached-result transport remain bounded and grant no product work. |
| Provisional start | `_BudgetCheck` creates one `SharedExecutionBudget`. Its counter and monotonic start survive source promotion and every following method. |
| Candidate snapshot and edit preparation | Source snapshot bytes are charged per started 64 bytes; patch/module/index work uses the same provisional counter. Exact hash, UTF-8 and overlap preconditions execute before candidate source acceptance. No old source is compiled to discover the new request. |
| Header admission | Existing bounded C073 header scanner authorizes the exact candidate entry. The service also pins the entire immutable program revision, preventing a later in-request bundle substitution. |
| Construction and numerical work | `ExecutionProgramBudget`, `ExecutionConstructionBudget` and numerical work forward to that ledger. Other object/value/numerical/cache limits remain fixed. The ordinary legacy budget classes retain their original behavior. |
| Evaluation, inspection and mesh pages | Existing operations and bounded materialization receive the request check. The request-local compiler cache may serve identity inspection without recompilation; it grants no allowance and is never service-global. |
| Identity continuity | Complete candidate occurrence identities are derived and charged before acceptance. Their comparison with the earlier accepted descriptor is charged. The descriptor grants no execution authority or evaluated state. |
| Delivery | The evaluated requested-prefix plan, exporter and independent supplied-byte checks share the compiler's numerical work and remaining ledger. |
| Retrieval | A new request reauthorizes the exact retained source. The service hashes actual retained bytes with charged bounded blocks and compares exact artifact identity; then it returns a bounded chunk. This is current transport integrity, not a new physics/destination validation. Producer validation remains historical and separately identified. |
| Publication | Both complete-envelope traversals consume the same ledger, including the final traversal inside the effects transaction. A late limit failure rolls back source acceptance, run and artifact writes. Rejected delivery receipts lose tentative artifact fields and cannot claim delivered success. |
| Failure transport | Once product work stops, bounded failure transport publishes no new artifact and obtains no second product grant. Host callback exceptions retain identity. A failed host clock is not recalled while recording cancellation. |

The final top-level `execution_budget` receipt gives cumulative work. An artifact report's `execution_budget_at_export` is explicitly a partial snapshot with status `export_verified_pending_publication`; `producer_request_id` identifies its final durable producer response. Neither receipt authorizes later execution. Process-local monotonic times do not represent civil timestamps.

Cooperative checks do not preempt blocking host callbacks. Aggregate process memory, persistent-store capacity, retention and hard termination remain independently configured host responsibilities. Source/CLI-only discovery and legacy Agent registries retain their previous namespaces; new Agent discovery has explicit `.7` fields.
