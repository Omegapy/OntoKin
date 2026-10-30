# Shared execution accounting

The new source/CLI path uses one `SharedExecutionBudget`. Its operation count is semantic work, not a CPU instruction count or a memory quota. The clock measures cooperative elapsed wall time at checkpoints. An external host must enforce any process-level kill deadline it requires.

| Stage | Debit and ownership |
| --- | --- |
| Host preparation | Immutable bundle ingress and the loaded implementation fingerprint precede header admission. They remain bounded transport/host preparation and do not execute source expressions or grant an allowance. |
| Entry admission | Create the provisional ledger before scanning. Charge one operation per started 64 UTF-8 bytes and each emitted prefix token. Its limits are the minimum of defaults, host ceilings and known caller caps. |
| Authorization | Check the provisional deadline before promotion. Resolve source fields and explicit caller reductions, check host ceilings, then promote once. Keep the original start and every consumed operation. |
| Linking and parsing | `ConstructionBudget.tick` delegates to the admitted ledger. Whole-source lexical/parser work, including any header reparse, keeps its existing charges. |
| Construction | The adapter retains object and logical-value limits. Its reported operation count reads the shared ledger, including later stages; it has no second allowance. |
| Numerical operations | `ReachExecutionWork(execution_budget=...)` calls the ledger once per work unit. Its own counters report categories only. The legacy constructor retains its fixed maxima. Operand, cache, series and local admission limits do not change. |
| Evaluation | The explicit profile dispatch selects the inherited reach simulator, including force and impulse behavior. `evaluate_prefix` and its recording observer use the same numerical work context. A complete successful prefix supplies a recording plan without replaying a fresh request. |
| Recording and output | Scene construction, certificates, GLB encoding and actual supplied-byte readback use the existing numerical work context. GLB/0.7 refuses a missing, unadmitted or detached context. It cannot fall back to a fresh default meter. |
| New certificate reserve | GLB/0.7 multiplies source position and rotation error widths by `2`, charging two `recording_exact_mul` units per carrier and certificate group. Carrier acceleration and angular speed, plus enclosing speed, acceleration and angular speed, receive the exact factor `1 + 2^-48`: five `recording_budget_reserve` checkpoints and one `recording_exact_mul` for each nonzero derivative. Exact zero derivatives remain zero. Dependent chord, arc and total bounds are recomputed outward; the independent reader still checks the supplied quantities against its unchanged minima and the requested total tolerances. |
| Result | Success-report traversal remains charged and guarded by the existing JSON entry/depth/byte limits. The final receipt reports cumulative work. A bounded failure transport remains available after the product allowance is exhausted. |
| File persistence | Verified bytes and their report are staged after computation. Handled filesystem failures restore existing outputs or preserve recovery backups. This transport step does not perform further modeling, validation or budget promotion. |

Numerical callbacks do not also pass through `ConstructionBudget.tick`: that would double-charge the same adapter unit. Non-numerical compiler checkpoints and numerical work are distinct paid operations. Imported sources, frames, helpers and independently checked output cannot reset counters or the deadline. Every genuinely separate call to `execute_budgeted_export` starts a newly authorized top-level attempt.

The direct path leaves `agent_protocol`, `program_protocol`, legacy runtime budget constructors, Agent routing and stores unchanged. It does not expose Agent/0.7 or claim that saved-program authorization, retry identity, durable cancellation or concurrent service policy has been implemented. Those are C074 requirements.
