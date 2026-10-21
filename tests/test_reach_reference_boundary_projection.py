"""Independent recording histories retain the exact full-sample projection."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_reference import ReachReference, ReferenceError, build_reference
from reach_agent_support import source_case


def complete_sample_projection(reference, time, side):
    sample = reference.sample(time, side)
    return {"joint_states": sample["joints"], "action_states": sample["actions"],
            "pose_authorities": {path: value["pose_authority"] for path, value in sample["objects"].items()},
            "impulse_states": {path: value["impulses"] for path, value in sample["objects"].items()},
            "force_states": {path: value["forces"] for path, value in sample["objects"].items()},
            "reach_states": sample["reaches"]}


def reference_for(name, end=None, *, check=None):
    compiler = compile_construction(source_case(name), check=check)
    reference = build_reference(compiler.model, end=compiler.model.duration if end is None else end,
                                work=compiler.reach_work)
    return compiler, reference


class IndependentBoundaryProjectionTests(unittest.TestCase):
    def test_complete_boundary_trees_equal_full_samples_across_source_lifecycles(self):
        # Include followed geometry, a moving base, multiple simultaneous
        # coordinates, inherited impulses/forces/releases and replacement owners.
        for name in ("P01", "P02", "P05", "P13", "P16", "P18", "P19", "L01", "L02", "L03"):
            with self.subTest(case=name):
                compiler, reference = reference_for(name)
                actual = reference.boundary_states()
                previous_compiler, previous = reference_for(name)
                with patch.object(ReachReference, "_boundary_projection", complete_sample_projection):
                    expected = previous.boundary_states()
                self.assertEqual(actual, expected)
                self.assertEqual(reference._history_weight, previous._history_weight)
                self.assertLessEqual(compiler.budget.operations, 100000)
                self.assertLessEqual(previous_compiler.budget.operations, 100000)
                if name in ("P02", "P13"):
                    self.assertLess(compiler.budget.operations, previous_compiler.budget.operations)

    def test_boundary_projection_never_constructs_unrequested_complete_inspection(self):
        _, reference = reference_for("P02")
        reference._geometry = None
        marker = AssertionError("complete object inspection was allocated")
        with patch.object(reference, "sample", side_effect=marker), \
             patch.object(reference, "_geometry_values", side_effect=marker):
            histories = reference.boundary_states()
        self.assertEqual(len(histories), len(reference.boundaries))
        self.assertTrue(histories[-1]["reach_states_after"])
        self.assertIsNone(reference._geometry)

    def test_boundary_values_are_private_and_do_not_supply_full_sample_derivatives(self):
        _, reference = reference_for("P13")
        histories = reference.boundary_states()
        expected = copy.deepcopy(histories)
        for record in histories:
            for side in ("before", "after"):
                for name in ("joint_states", "action_states", "pose_authorities", "impulse_states", "force_states", "reach_states"):
                    record[name + "_" + side].clear()
            record["incoming_releases"].clear()
        self.assertEqual(reference.boundary_states(), expected)
        _, full = reference_for("P13")
        self.assertEqual(reference.sample(F(1)), full.sample(F(1)))
        self.assertTrue(any(component.magnitude for pose in reference._pose_map(
            F(1), reference._state_at(F(1), "after"), ideal=False).values() for component in pose.omega))

    def test_every_required_boundary_computation_still_propagates_failure(self):
        for method in ("_joint_observation", "_reach", "_forces", "_pose_map"):
            with self.subTest(method=method):
                _, reference = reference_for("P01")
                marker = RuntimeError("required independent history computation failed")
                with patch.object(reference, method, side_effect=marker):
                    with self.assertRaises(RuntimeError) as caught:
                        reference.boundary_states()
                self.assertIs(caught.exception, marker)
        marker = RuntimeError("required independent release computation failed")
        with patch.object(ReachReference, "_release", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reference_for("P16")
        self.assertIs(caught.exception, marker)

    def test_original_logical_preflight_and_actual_history_limits_remain(self):
        _, reference = reference_for("P01")
        reference._history_weight = 100001
        with patch.object(reference, "_boundary_projection", side_effect=AssertionError("allocated before preflight")):
            with self.assertRaises(ReferenceError) as caught:
                reference.boundary_states()
        self.assertEqual(caught.exception.code, "resource")
        reference._history_weight = 0
        with self.assertRaises(ReferenceError) as caught:
            reference.boundary_states()
        self.assertEqual(caught.exception.code, "resource")
        self.assertIn("actual H06 history", str(caught.exception))

    def test_selected_pose_evaluation_preserves_original_cancellation_identity(self):
        armed = False
        marker = RuntimeError("cancel independent boundary pose")
        def check():
            if armed:
                raise marker
        compiler, reference = reference_for("P01", check=check)
        original = reference._pose_map
        def cancel(*args, **kwargs):
            nonlocal armed
            armed = True
            return original(*args, **kwargs)
        with patch.object(reference, "_pose_map", side_effect=cancel):
            with self.assertRaises(RuntimeError) as caught:
                reference.boundary_states()
        self.assertIs(caught.exception, marker)
        self.assertIs(compiler.reach_work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
