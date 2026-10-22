"""Unused boundary fields retain their original public admissibility checks."""
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_pose import PoseValue, ReachPoseOps, RotationValue, UNIT, ZERO
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


def private_pose(ops, *, position=ZERO, quaternion=UNIT, velocity=ZERO, omega=ZERO):
    return PoseValue(position, RotationValue(quaternion), velocity, omega, F(0), ops)


def expose(ops, pose):
    return pose.position, pose.orientation, pose.velocity, pose.omega


class ReachProjectionFinitenessTests(unittest.TestCase):
    def setUp(self):
        # This cohort targets the original four ordered field proofs; the
        # complete current-signature proof is covered in its separate cohort.
        self.enterContext(patch.object(ReachPoseOps, "_complete_finite_signature", return_value=False))

    def test_mixed_denominators_and_full_small_domain_need_no_public_allocation(self):
        largest = (1 << 512) - 1
        quaternions = (UNIT, (F(0), F(-1), F(0), F(0)),
            (F(largest, largest - 2), F(-1, largest - 4),
             F(largest - 6, 3), F(7, largest - 8)))
        for quaternion in quaternions:
            with self.subTest(quaternion=quaternion):
                work = ReachExecutionWork(max_cache_entries=1)
                ops = ReachPoseOps(work)
                pose = private_pose(ops, position=(F(largest), F(-1, largest), F(0)),
                    quaternion=quaternion, velocity=(F(1, 3), F(-2, 7), F(5, 11)),
                    omega=(F(0), F(largest, 13), F(-17, largest)))
                # A finite proof has no need to execute even one extractor.
                with patch.object(ops, "_expose", side_effect=AssertionError("unused public tuple")):
                    self.assertIsNone(ops.ensure_finite(pose))
                self.assertEqual(pose._projection, {})
                self.assertEqual(len(work._cache), 0)
                self.assertEqual(work.counts["pose_finiteness_field"], 4)
                projected = expose(ops, pose)
                self.assertTrue(all(math.isfinite(value) for values in projected for value in values))
                self.assertLessEqual(len(work._cache), 1)
                self.assertEqual(work.max_operations, 100000)

    def test_large_finite_subnormal_and_frozen_values_use_original_projection(self):
        cases = (
            {"position": (F((1 << 1024) - (1 << 971)), F(0), F(0))},
            {"position": (F(1, 1 << 1074), F(-1, 1 << 1075), F(0))},
            {"quaternion": (F(1, 1 << 1074), F(0), F(0), F(1))},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                ops = ReachPoseOps(ReachExecutionWork())
                pose = private_pose(ops, **changes)
                ops.ensure_finite(pose)
                field = "orientation" if "quaternion" in changes else "position"
                self.assertIn(field, pose._projection)
                expected_ops = ReachPoseOps(ReachExecutionWork())
                expected = expose(expected_ops, private_pose(expected_ops, **changes))
                actual = expose(ops, pose)
                self.assertEqual([[float_bits(x) for x in row] for row in actual],
                                 [[float_bits(x) for x in row] for row in expected])
        ops = ReachPoseOps(ReachExecutionWork())
        frozen = (1., -0., 0., -0.)
        pose = replace(private_pose(ops), rotation=RotationValue(UNIT, F(0), frozen))
        ops.ensure_finite(pose)
        self.assertIs(pose._projection["orientation"], frozen)

    def test_overflow_zero_rotation_and_malformed_inputs_keep_original_failure(self):
        changes = (
            {"position": (F(1 << 1024), F(0), F(0))},
            {"quaternion": (F(0), F(0), F(0), F(0))},
            {"quaternion": (F(1), object(), F(0), F(0))},
            {"velocity": (F(1 << MAX_OPERAND_BITS), F(0), F(0))},
            # Position fails before an independently invalid quaternion.
            {"position": (F(1 << 1024), F(0), F(0)),
             "quaternion": (F(0), F(0), F(0), F(0))},
        )
        for fields in changes:
            observed = []
            for proof in (False, True):
                ops = ReachPoseOps(ReachExecutionWork())
                pose = private_pose(ops, **fields)
                with self.assertRaises(Exception) as caught:
                    ops.ensure_finite(pose) if proof else expose(ops, pose)
                error = caught.exception
                observed.append((type(error), str(error), getattr(error, "details", None)))
            with self.subTest(fields=fields):
                self.assertEqual(observed[0], observed[1])
        ops = ReachPoseOps(ReachExecutionWork())
        pose = private_pose(ops, quaternion=(F(1), F(0), F(0)))
        # An unexpected private shape is delegated, never accepted by proof.
        with patch.object(ops, "_expose", wraps=ops._expose) as projection:
            ops.ensure_finite(pose)
        self.assertIn("orientation", [call.args[1] for call in projection.call_args_list])

    def test_every_narrow_cap_keeps_original_projection_domain(self):
        for cap in (32, 64, 128, 512, 8192, MAX_OPERAND_BITS - 1):
            outcomes = []
            for proof in (False, True):
                ops = ReachPoseOps(ReachExecutionWork(max_operand_bits=cap))
                pose = private_pose(ops, position=(F(1, 1 << 96), F(0), F(0)),
                    quaternion=(F(1, 3), F(2, 7), F(3, 11), F(4, 13)))
                try:
                    ops.ensure_finite(pose) if proof else expose(ops, pose)
                except ReachAdmissionError as error:
                    outcomes.append((error.reach_code, error.details))
                else:
                    outcomes.append(expose(ops, pose))
                    self.assertEqual(set(pose._projection), {"position", "orientation", "velocity", "omega"})
            with self.subTest(cap=cap):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_fields_preserve_order_and_existing_actual_values_are_reused(self):
        visits = []
        marker = RuntimeError("original public omega failure")
        class ForeignPose:
            def __getattr__(self, name):
                visits.append(name)
                if name == "omega":
                    raise marker
                return (0.,)
        ops = ReachPoseOps(ReachExecutionWork())
        with self.assertRaises(RuntimeError) as caught:
            ops.ensure_finite(ForeignPose())
        self.assertIs(caught.exception, marker)
        self.assertEqual(visits, ["position", "orientation", "velocity", "omega"])
        pose = private_pose(ops)
        expected = expose(ops, pose)
        retained = dict(pose._projection)
        ops.work.max_operand_bits = 1
        with patch.object(ops, "_expose", side_effect=AssertionError("already projected")):
            ops.ensure_finite(pose)
        self.assertEqual(pose._projection, retained)
        self.assertEqual(tuple(pose._projection[name] for name in
            ("position", "orientation", "velocity", "omega")), expected)

    def test_each_field_is_cancellable_and_callback_cap_changes_take_fallback(self):
        for cancel_at in (1, 2, 3, 4):
            calls = 0
            marker = RuntimeError("cancel unused field proof")
            def cancel():
                nonlocal calls
                calls += 1
                if calls == cancel_at:
                    raise marker
            work = ReachExecutionWork(check=cancel)
            ops = ReachPoseOps(work)
            pose = private_pose(ops)
            with self.assertRaises(RuntimeError) as caught:
                ops.ensure_finite(pose)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(pose._projection, {})
            self.assertEqual(len(work._cache), 0)
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        pose = private_pose(ops, position=(F(1, 1 << 96), F(0), F(0)))
        def narrow():
            work.max_operand_bits = 128
        work.external_check = narrow
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.ensure_finite(pose)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_complete_recording_boundary_checks_unselected_private_frame(self):
        built = compile_construction(source_case("P01"))
        sim = ReachSimulator(built.model, work=built.reach_work)
        expected = sim.recording_boundary(F(0), "before")
        original = sim._kinematics
        unused = private_pose(sim.pose_ops, position=(F(1, 3), F(2, 7), F(3, 11)),
                              quaternion=(F(1), F(2), F(3), F(4)))
        def with_unused(time, state):
            objects, frames = original(time, state)
            return objects, {**frames, "unselected.site.frame": unused}
        with patch.object(sim, "_kinematics", with_unused):
            self.assertEqual(sim.recording_boundary(F(0), "before"), expected)
        self.assertEqual(unused._projection, {})
        unused = replace(unused, exact_position=(F(1 << 1024), F(0), F(0)))
        with patch.object(sim, "_kinematics", with_unused):
            with self.assertRaises(ReachAdmissionError) as caught:
                sim.recording_boundary(F(0), "before")
        self.assertEqual(caught.exception.reach_code, "reach_numeric")


if __name__ == "__main__":
    unittest.main()
