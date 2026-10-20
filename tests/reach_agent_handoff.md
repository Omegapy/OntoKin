# Agent/0.6 implementation handoff

This is new implementation work following the published adoption
`6ae92101d467e956a7e15f2968a3a7a94dc9a3c7`. It does not modify the frozen
proposal, schemas, corpus, protocol templates or earlier evidence. The first
code checkpoint is local `28953a90d974ee14956fe2684bbec15929696c11`, published
by the integrator as `3a3179d7b9450977c2d4abdec927e8d5bc522dd3` with the same
tree `fd9d8cb885a6f6586beb7ca979df6b9e3571613f`.

**Execution status at this handoff: syntax checks only.** No actual source,
Agent, SQLite, unit, export or archive run has been performed for these new
files. The exclusive execution window and integrated dependencies are still
required. Defined tests and this mapping are not passing evidence.

## Owned implementation

The explicit binding selects source `0.6` / `planar-reach-0.1`, Agent/0.6,
`planar-reach-program-agent.sqlite3` and
`ontokin.planar-reach-program-agent-store/0.1`. Existing defaults remain
unchanged. The inherited store has no migration or new table schema. All 12
operations use the versioned protocol, including native surface pages and
artifact retrieval. Discovery copies the inherited catalog and identifies
the exact adopted source examples.

`program_runtime.py` dispatches reach action records through the lifecycle
owner's `reach_projection(model, path, sample, check=...)`. Both joint endpoint
owners receive associated actions. The existing source-index and exact patch
rules remain authoritative; a description identity or generated occurrence
does not acquire initializer edit authority.

`reach_context.py` registers only freshly computed inspection action groups,
constructed initial snapshots and new run snapshots. The narrow `agent.py`
hook runs after cancellation/source/run fencing and before serializing the run
inside its publication transaction. It binds the actual accepted head,
source's accepted-once status, service run identity and observation kind.
Earlier candidate descriptors, retained stronger prefixes, retries and nested
status/cancel receipts retain their original context. Final whole-response
guards still roll back acceptance, run and artifact publication atomically.

`ProgramRuntime.prepare_delivery` returns the transient compiler and a fresh
requested-prefix result. The service passes that same compiler and
`compiler.reach_work` to the export adapter, preserving one bounded numerical
context through compilation, evaluation and recording. No mutable work object
is placed on `SceneModel` or serialized in a result.

Delivery remains explicitly unavailable in this checkpoint. Root owns the
actual GLB/0.6 adapter and CLI parser selection. The delivery tests require
real integrated success and do not replace an unavailable adapter with a stub.

## Literal Agent test mapping

All names below are actual unittest methods, under `tests`. Each LP method
loads and executes the unchanged requests from
`docs/language-design/planar-reach-v0.1/draft2-supplements/protocol-cases.json`.

| Adopted obligation | Literal method |
| --- | --- |
| LP01.01–LP01.09, failed prefix/reset | `test_reach_agent_protocol_cases.ReachProtocolCaseTests.test_lp01_failed_prefix_reset_all_nine_steps` |
| LP02.01–LP02.09, writable repair/retry/history | `test_reach_agent_protocol_cases.ReachProtocolCaseTests.test_lp02_authorized_root_repair_retry_history_all_nine_steps` |
| LP03.01–LP03.05, accepted construction/admission failure | `test_reach_agent_protocol_cases.ReachProtocolCaseTests.test_lp03_accepted_construction_failed_admission_repair_all_five_steps` |
| LP04.01–LP04.07 and Q03 | `test_reach_agent_protocol_cases.ReachProtocolCaseTests.test_lp04_q03_fixed_128_actions_real_n_and_n_minus_one_all_seven_steps` |
| LP05.01–LP05.12, current candidate versus retained history | `test_reach_agent_protocol_cases.ReachProtocolCaseTests.test_lp05_candidate_and_later_accepted_history_all_twelve_steps` |
| Q01, accepted P01 evaluation cancellation before publication | `test_reach_agent_transactions.ReachAgentTransactionTests.test_cancel_tentative_extension_preserves_stored_run_and_context` |
| Q22, same-project L04 → exact L02 and stale old run | `test_reach_agent.ReachAgentTests.test_same_project_action_edit_l04_to_l02_rejects_stale_run` |
| Separate tenth L04 recovery artifact | `test_reach_agent_delivery.ReachAgentDeliveryTests.test_l04_extra_recovery_export_is_fresh_run_with_unchanged_source` |
| Q08, P17 prefix and exact later failure | `test_reach_agent_delivery.ReachAgentDeliveryTests.test_q08_p17_short_prefix_and_exact_later_failure` |
| Complete 12-operation selection and defaults | `test_reach_agent_protocol.ReachAgentProtocolTests.test_exact_twelve_operations_and_unchanged_defaults` |
| Six isolated durable stores | `test_reach_agent_protocol.ReachAgentProtocolTests.test_six_stores_coexist_with_identical_project_and_request_ids` |
| Actual schema validation | `test_reach_agent_verification.ReachAgentSchemaVerificationTests.test_actual_created_sampled_failed_and_historical_receipts_match_frozen_schemas` |
| Stored run and returned projection agree | `test_reach_agent.ReachAgentTests.test_before_after_complete_projection_and_persisted_run_agree` |
| Paused and terminal history under new owner | `test_reach_agent.ReachAgentTests.test_paused_and_terminal_projections_retain_complete_independent_history` |
| Atomic final delivery guard | `test_reach_agent_delivery.ReachAgentDeliveryTests.test_final_delivery_envelope_guard_rolls_back_run_and_artifact` |
| One compiler/work context for delivery | `test_reach_agent_delivery.ReachAgentDeliveryTests.test_delivery_shares_one_compiler_and_numerical_work_context` |

Additional tests cover unrun versus constructed versus sampled context, named
aliases, both-joint object association, additive discovery, native surface
cursor context, changed request payloads, strict wire/options limits,
competing accepted heads and run versions, cancellation after computation,
source/run/artifact transaction rollback, and explicit JSONL selection.

### LP02 evidence correction after focused execution

The first focused LP02 comparisons incorrectly looked for four unchanged reach
actions. P13 and P20 each contain one named reach, on `arms["first"]`; the four
untouched siblings are generated part/property occurrences. Retaining full
nominal identity tuples was useful, but did not correct that mistaken model.
The corrected test executes all ten frozen `required_evidence_reads` attached
to LP02.08 and LP02.09: four sibling `forearm_length` reads and one complete
source-unit read for each revision. It requires exactly four identical sibling
identities, canonical values, dependency identities and library origins, plus
byte-identical pinned libraries. The single changed reach is checked against
the exact P13/P20 coordinates and targets. The nine main LP02 receipts and all
42 main protocol steps remain unchanged. Earlier failed logs remain evidence
of the test defect; this correction requires a fresh executed check.

Q03 fixes P24, its actual run at `1.5 after`, `selector.kind=action`,
`fields=[actions]`, `limit=128`, complete groups and no cursor. It measures N
from the entire published response. It also records actual cumulative
`ConstructionBudget.value_entries`, all runtime materializations and both
publication guards. N−1 must finish computation successfully and fail at the
final complete-response guard. An earlier constructor or runtime failure does
not satisfy this test. The query is never reduced to make a budget fit.

## Integration and remaining execution

The source/lifecycle owner supplies the new parser, payload, evaluator,
`reach_projection` and `compiler.reach_work`; the numeric owner supplies the
production arithmetic and pose helpers. Root supplies `cli.py` selection and
`export_glb(..., work=...)`. No copied proposal checker substitutes for those
implementations or their independent tests.

Before running, pause other workers through the integrator's exclusive-window
procedure and bind stable input hashes. The first Agent cohort can execute the
non-delivery modules with the integrated source/numeric/CLI changes. The
delivery cohort must then execute against the real adapter. Schema tests use
the pinned verification-only `jsonschema` and `referencing` packages and an
offline registry with unknown reference retrieval denied. A dependency skip
does not qualify as the required zero-skip cohort.

Q02 still needs an actual P23 cancellation trigger inside identified bounded
recording work once the root planner API is stable. The post-computation
delivery cancellation test is separate and does not claim Q02. Other hostile
destination probes, all nine ordinary Agent release artifacts, source/browser
roles, independent byte validation, compatibility and resulting-main checks
remain the root release runner's obligations. This handoff is only the Agent
implementation mapping, not the complete finite release mapping or acceptance.
