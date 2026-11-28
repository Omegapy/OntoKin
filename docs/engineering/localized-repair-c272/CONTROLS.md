# C272 controls

The controls serve TASK-020 and TASK-021 (REQ-009, REQ-015, REQ-019). `qualify.py` executes
them on the actual run's bytes and retains each result in `RESULTS.json`. Every fault control
also judges its clean twin, the same input without the fault, which must be accepted. All
controls are **evaluator controls**. None is a case outcome, a model attempt or a new
fixture of the frozen corpus.

## Executed in every run

| ID | Kind | Fault presented to the workflow's checks |
| --- | --- | --- |
| E01 | wrong-part edit | The real service accepted 0.75 m on `first.fingers["upper"]`; the result is judged as V1. |
| E02 | changed sibling | The real service accepted the V1 edit together with a second-rack mount change. |
| E03 | incorrect motion | One translation sample of the selected blade moved by 0.01 m; the records stay consistent. |
| E04a | stale provenance | The pre-edit source named with the new artifacts. |
| E04b | stale artifact | The pre-edit GLB and sidecar named with the accepted new source. |
| E04c | self-asserted acceptance | The client claims acceptance while the service's accepted state is the start. |
| E04d | self-asserted acceptance in the artifact | The delivered GLB with a sidecar whose acceptance claim names a program revision that the GLB does not carry; G3's `STALE_SIDECAR` fires. |
| E05 | accepted invalid candidate | N1's 0.75 kg candidate recorded as accepted and retained. |
| E06a | missing output | No GLB delivered for V1. |
| E06b | missing output, crashed case | The runner's case outcome is a crash. |
| E07a | inconsistent rebuild | The rebuilt GLB differs from the delivered one in one sample. |
| E07b | rebuild with an undeclared input | A real rebuild in a workspace that also held `extra.ok`. |
| E08 | changed dependency pin | The retained library differs from the bytes that `main.ok`'s digest names. |
| P01, P02 | positive | The independently correct 0.75 m and 0.65 m states. |
| P03 | positive | Every stored rotation keyframe of all 18 nodes negated in the actual GLB bytes, with the sidecar rebound, judged end to end. Because both members of each hinge pair are negated, the signs cancel in their relative rotation, so P03 shows sign equivalence end to end but would not by itself have caught review finding M2. `test_semantic_observe.test_negated_stored_rotations_are_the_same_motion` negates single nodes and does catch it (review-2, N1). |
| P04 | positive | A legitimate change of accepted revision, source hash and artifact hashes after the valid edit. |
| R01 to R03 | H20 | One ownership, one follow or one motion field of a delivered GLB changed alone. The workflow must reject it, and C267's hinge records must stay as they were, so that no hinge value is inferred from that field. |
| R04 | H20 | The actual length edit: C267's hinge records are equal across V1 apart from revision-bound digests and revision identities. |
| R05 to R07 | H24 | An excessive site table (306), a duplicate JSON key and a truncated GLB, each refused with a typed fault. |

Focused tests add field-level faults: [test_observe.py](test_observe.py) (nonfinite values, zero
quaternion, duplicate time, scale, matrix node, duplicate identity, changed owner),
[test_semantic_observe.py](test_semantic_observe.py) (14 single-field faults, stale sidecar,
bounds) and [test_score.py](test_score.py) (wrong units, pose, sibling dimension, missing site).
[test_runner.py](test_runner.py) covers an altered input byte and a crash with a retained record.

## The faults that SCORING lists

SCORING's section "Required oracle controls before runner admission" lists the faults below.
Existing C255 tests check them on inert records. They ran unchanged in this scope's observer
regression; they are cited, not re-implemented.

| Listed fault | Covered by |
| --- | --- |
| Wrong target, wrong length, changed global/shared default, changed sibling | E01, E02 and the case checks (wrong length). Changed global or shared default: C255 `test_wrong_length_target_global_default_and_sibling` at record level; **no end-to-end control here** — any such source fails C255's exact source-byte check (E04a, E08 show that check). |
| Kilograms accepted as metres; missing or changed dependency pin | N1 itself (the service refuses), E05, E08. Missing pin: C255 `test_source_mutations_and_dependency_changes`; C271's H22.02 control for the observers. |
| Missing, extra or duplicate identity; changed ownership, follow or hinge relation | R01, R02, `test_observe` (duplicate identity, owner), `test_semantic_observe` (hinge axis and limit, follow offset), `test_score` (missing site); C255 `test_identity_membership_and_full_keys`, `test_every_semantic_relationship_collection`. |
| Correct metadata with wrong geometry, motion, units, reflection or scale | E03, R03, `test_score` (units), `test_observe` (scale, matrix node), `test_semantic_observe` (declared primitive); C255 `test_geometry_not_metadata`, `test_raw_scale_shear_reflection_and_decomposition`. |
| Omitted time or object, nonfinite value, zero quaternion, widened tolerance | `test_observe` (nonfinite, zero quaternion, duplicate time), `test_score` (missing site); C255 `test_pose_inventory_and_wrong_motion`, `test_nonfinite_boolean_and_zero_quaternion`, `test_no_tolerance_overrides`. No component of this workflow accepts a tolerance. |
| Stale accepted revision, source/artifact mismatch, falsely asserted acceptance | E04a to E04d; C255 `test_stale_mismatched_and_false_provenance`. |
| Invalid candidate promoted; rejected candidate that altered retained bytes | E05 and N1's byte preservation; C255 `test_n1_promotion_and_retained_byte_mutations`. |
| Rebuilds differently or depends on undeclared input | E07a, E07b; C255 `test_rebuild_difference_and_undeclared_input`. |
| Empty or missing output, timeout, infrastructure incident denominators | E06a, E06b, `test_runner` (crash). Timeout and infrastructure incident: **not executed here**. C255's inert `classify_attempt` control (`test_denominators_retain_all_started_failures`) covers only their accounting; it is an inert control, and it is counted as no executed case. |
| Positive controls: quaternion sign, legitimate provenance change | P03, P04; C255 `test_quaternion_sign_equivalence`, `test_legitimate_revision_and_artifact_changes`. |
| Boundary controls: inclusive tolerances and just-outside values | C255 `test_inclusive_source_dimension_boundary_and_next_float`, `test_pose_position_boundaries_reference_and_delivery`, `test_time_boundary_and_exact_reference_times`, `test_rotation_boundaries_and_no_raw_secondary_tolerance`. **No end-to-end boundary control here.** |

## Retained failures

The first independent review, of `d275baa4`, required changes. It is retained as
`evidence/review-1/REVIEW.md`.
- **M2.** G3 read the hinge angle without fixing the quaternion's sign. A correct GLB whose stored
  rotations carry the equivalent negative sign was therefore rejected. P03 negated pose records
  only after G3 had run, so it never exercised that claim.
- **The fix.** `3c206ac7` canonicalizes the sign, and P03 now negates the stored keyframes in
  the GLB bytes. A unit test that fails without the fix was added.
- **Other findings.** M1 (two evidence logs excluded by `.gitignore`) and M3 (per-property rows
  without observation, origin and derivation) were resolved at the same commit.

The `cad34f35` crash below kept no traceback; only its partial output directory beside the
clone and the cause stated here remain.


The first attempt of `qualify.py`, at `cad34f35`, stopped with an exception before writing
`RESULTS.json`: C255's decoder needs a rebuild state that the runner's record does not yet
have. `4aff6024` added a decoder for the runner's record.

The first complete development run, at `4aff6024`, failed P03 and R04. Two defects in C272's
own checks caused it:
- the locality check compared rotations exactly, so an equivalent quaternion sign counted as movement;
- the H20 hinge comparison counted revision-bound digests as declaration changes.

`78929c53` corrected both; C255's verdicts were unaffected. That run's `RESULTS.json` is
retained under `evidence/runs/failed-4aff6024/`.
