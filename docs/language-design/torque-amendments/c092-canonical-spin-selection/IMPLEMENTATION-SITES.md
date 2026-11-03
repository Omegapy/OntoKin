# Complete reviewed angular dataflow checklist

This inventory is normative with `OK-LANG-022-CANONICAL-SPIN/0.1.0`.
It names C091 dataflow sites that implementation review must cover. A site in
an inherited module is an audit dependency, not authorization to edit a frozen
predecessor file. Use narrowly dispatched .22 overrides/helpers and retain all
earlier behavior. New call sites must be included in the actual review graph.

| Dataflow category | Verified C091 sites | Required treatment |
| --- | --- | --- |
| Constant-spin point dispatch | `ReachSimulator._advance_orientation`, `ordinary_target`, `_dynamic_kinematics`, prescribed `_resolve_kinematics`, `_latch_ordinary` | Select from actual dynamic or accumulated action elapsed; ignore wider/history plan operands for point values. |
| Source pose composition | `ReachPoseOps` rotation/product/vector/materialization; ordinary hinge/reach dependencies | Preserve operation order, full private anchors, fixed-grid and binary64 semantics. |
| Producer event transactions | `TorqueSimulator` release/impulse, `_aggregate`, `_force_aggregate`, `_aggregate_torque` | Preserve pre-split materialization, split neutral origin, ordered axis checks and complete rollback. |
| Producer continuous plans | `torque_phase.phase_bounds`, `torque_phase_fields`, `torque_transfer_bounds` | Phase plans prove coverage; all-stages error envelope retains complete real transfer, origin and marker bounds. |
| Producer recording points | `TorqueSimulator.recording_frames`, `torque_recording`, inherited capture/direct transform calls | Every actual .22 source point obeys the amended rule. Existing .22 direct graph/no-cursor treatment remains until a separate eligible proof establishes any optimization. |
| Independent exact arithmetic | `torque_axis_exact` and new .22-only source kernel if needed | Independently implement deterministic finite spin/hinge and canonical vector/rotation/materialization operations; never import producer arithmetic. |
| Independent retained origins | `AngularSupport`, `root_support`, `frame_support` and its compose/visit traversal | Retain complete source recipes and accumulated clocks through prescribed/dynamic roots, fixed sites, follows, hinges, sliders and released graphs. |
| Independent ordinary actions | `ReachReference._event`, `_coordinate`, `_canonical_targets`, action lifecycle consumed by the .22 subclass | Preserve existing coordinates, rates, paused elapsed, limits, ownership and inverse-kinematics rule. Use .22 integration without changing earlier bindings. |
| Independent event transfer | `TorqueReference._initialize`, `_finish`, `_release`, `_impulse`, `_coordinate_impulse` | Reconstruct every actual materialization and ordered canonical transfer plus complete independent uncertainty. |
| Independent force/torque origins | `TorqueReference._aggregate`, `_axis_check`, torque `_event`, `_aggregate_torque` | Exact source vector decides axis. Error-only boundary retains old full canonical recipe. Final torque transition and genuine reanchors use their adopted order. |
| Independent observation/error law | `_root_pose`, `_polynomial`, `_axis_rotation`, `_general_spin`, `_shadow_bounds`, `_required_shadow`, `_phase_extrema`, `_certify_prefix`, `_dynamic_source_basis` | Keep exact canonical recipe separate from continuous ideal/error enclosure; cover all closed-phase stage changes and source error lower requirements. |
| Independent recording domain | `_recording_body_domain`, `_recording_root_body`, `recording_stationary_frames`, `recording_pose_enclosures`, `_affected_root` | Preserve fixed-marker scope, unrelated branch support and disabled ineligible constant-rate witnesses. |
| Independent authority | `reach_reference.build_reference`, `reach_conformance.validate_reach_export`, `TorqueValidationScope` | Preserve explicit .22 dispatch, original-plus-detached source, native scalar checks, callback/clock/code/ledger checks and final callback-free admission. |
| Numerical identities | `torque_recording.source_numeric_basis`, `torque_conformance.verify_numeric_bases` | Same complete ordered producer input list and amended derivation list; actual bytes and separate independent-reader inventory. |
| Durable identities | service `submit`, `work_next`, `_check_engine`, `_identity_gate`, torque artifact reads | Apply COMPATIBILITY.md's unchanged explicit fences and historical response rule; no implicit migration. |

All supported source categories require both accepted controls and exact
refusal controls. Boolean support may remain a proved-zero optimization, but
its inability to prove a cancellation does not create a new language domain.
Recipe representation must not introduce a smaller arbitrary depth limit.
Current source/work/cache/operand bounds and actual charged work still apply.

