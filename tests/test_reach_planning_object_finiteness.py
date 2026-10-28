"""Recording planning proves unused fields without changing actual observations."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_export import _boundary_record, reach_prefix_plan
from ontokin.reach_numeric import ReachAdmissionError, float_bits
from ontokin.reach_pose import PoseValue, ReachPoseOps, RotationValue, UNIT, ZERO
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


FIELDS = ("position", "orientation", "velocity", "omega")


def pose_bits(pose):
    return tuple(tuple(float_bits(value) for value in getattr(pose, field)) for field in FIELDS)


def private_pose(ops, *, position=ZERO, quaternion=UNIT, velocity=ZERO, omega=ZERO):
    return PoseValue(position, RotationValue(quaternion), velocity, omega, F(0), ops)


class PlanningObjectFinitenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        built = compile_construction(source_case("P01"))
        # Obtain the actual private planner subtype; subsequent specimens use
        # fresh compiled requests rather than reusing its numeric state.
        cls.planner_type = type(reach_prefix_plan(built.model, F(0), work=built.reach_work).simulator)

    def simulator(self, *, planning):
        built = compile_construction(source_case("P01"))
        kind = self.planner_type if planning else ReachSimulator
        return kind(built.model, work=built.reach_work)

    def test_planning_leaves_unused_object_fields_lazy_and_preserves_every_public_bit(self):
        built = compile_construction(source_case("P01"))
        plan = reach_prefix_plan(built.model, F(0), work=built.reach_work)
        planner = plan.simulator
        actual, _ = planner._kinematics(F(0), planner.state)
        self.assertTrue(any(not {"velocity", "omega"}.issubset(pose._projection)
                            for pose in actual.values()))

        ordinary = self.simulator(planning=False)
        before = ordinary.advance(F(0), "before")
        after = ordinary.advance(F(0), "after")
        expected, _ = ordinary._kinematics(F(0), ordinary.state)
        self.assertEqual(plan.boundary_records, (_boundary_record(F(0), before, after,
            ordinary.incoming_releases_at(F(0))),))
        self.assertEqual(set(actual), set(expected))
        for path in actual:
            with self.subTest(path=path):
                self.assertEqual(set(expected[path]._projection), set(FIELDS))
                self.assertEqual(pose_bits(actual[path]), pose_bits(expected[path]))
        self.assertEqual(built.reach_work.max_operations, 100000)
        self.assertEqual(built.reach_work.max_operand_bits, 32768)
        self.assertEqual(built.reach_work.max_cache_entries, 256)

    def test_ordinary_object_validation_keeps_its_eager_projection_path(self):
        simulator = self.simulator(planning=False)
        with patch.object(simulator.pose_ops, "ensure_finite",
                          side_effect=AssertionError("recording proof entered ordinary observation")):
            objects, _ = simulator._kinematics(F(0), simulator.state)
        self.assertTrue(objects)
        self.assertTrue(all(set(pose._projection) == set(FIELDS) for pose in objects.values()))

    def test_complete_boundary_histories_and_materialized_release_anchors_match(self):
        for case in ("P16", "P19"):
            with self.subTest(case=case):
                built = compile_construction(source_case(case))
                plan = reach_prefix_plan(built.model, F(2), work=built.reach_work)
                control = compile_construction(source_case(case))
                ordinary = ReachSimulator(control.model, work=control.reach_work)
                expected = []
                for time in plan.boundaries:
                    before = ordinary.advance(time, "before")
                    after = ordinary.advance(time, "after")
                    expected.append(_boundary_record(time, before, after,
                        ordinary.incoming_releases_at(time)))
                self.assertEqual(plan.boundary_records, tuple(expected))
                self.assertEqual(set(plan.final_state.dynamic), set(ordinary.state.dynamic))
                if case == "P16":
                    self.assertIn("payload", plan.final_state.dynamic)
                for path, actual in plan.final_state.dynamic.items():
                    baseline = ordinary.state.dynamic[path]
                    self.assertEqual((actual.time, actual.since), (baseline.time, baseline.since))
                    self.assertEqual(set(actual.state._projection), set(FIELDS))
                    self.assertIsNotNone(actual.state.rotation.frozen_projection)
                    self.assertEqual(pose_bits(actual.state), pose_bits(baseline.state))
                    self.assertEqual(actual.state.rotation, baseline.state.rotation)
                    self.assertEqual(actual.state.position_error_m, baseline.state.position_error_m)
                self.assertEqual(plan.final_state.dynamic_errors, ordinary.state.dynamic_errors)
                self.assertEqual(plan.final_state.ideal_accelerations, ordinary.state.ideal_accelerations)

    def test_unused_invalid_object_is_rejected_before_complete_graph_publication(self):
        specimens = (
            {"position": (F(1 << 1024), F(0), F(0))},
            {"quaternion": (F(0), F(0), F(0), F(0))},
            {"velocity": (F(1 << 1024), F(0), F(0))},
            {"omega": (F(0), F(1 << 1024), F(0))},
        )
        for fields in specimens:
            outcomes = []
            for planning in (False, True):
                simulator = self.simulator(planning=planning)
                target = next(iter(simulator.model.objects))
                invalid = private_pose(simulator.pose_ops, **fields)
                original_slot = simulator._pose_slot

                def injected(path, signature, build):
                    return invalid if path == target else original_slot(path, signature, build)

                with patch.object(simulator, "_pose_slot", side_effect=injected):
                    with self.assertRaises(Exception) as caught:
                        simulator._kinematics(F(0), simulator.state)
                error = caught.exception
                outcomes.append((type(error), str(error), getattr(error, "details", None)))
                self.assertEqual(simulator._pose_cache, {})
            with self.subTest(fields=fields):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_planner_object_checkpoint_keeps_lower_cap_fallback(self):
        for cap in (64, 128, 512):
            outcomes = []
            for planning in (False, True):
                simulator = self.simulator(planning=planning)
                simulator.work.max_operand_bits = cap
                pose = private_pose(simulator.pose_ops,
                    position=(F(1, 1 << 96), F(0), F(0)),
                    quaternion=(F(1, 3), F(2, 7), F(3, 11), F(4, 13)))
                try:
                    simulator._check_object_pose(pose)
                except ReachAdmissionError as error:
                    outcomes.append((error.reach_code, error.details))
                else:
                    self.assertEqual(set(pose._projection), set(FIELDS))
                    outcomes.append(pose_bits(pose))
            with self.subTest(cap=cap):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_each_planner_object_field_preserves_cancellation_identity_and_live_cap(self):
        # Explicitly select the retained field layer whose four callbacks this
        # test interrupts. Complete-signature cancellation has its own test.
        self.enterContext(patch.object(ReachPoseOps, "_complete_finite_signature", return_value=False))
        for cancel_at in (1, 2, 3, 4):
            simulator = self.simulator(planning=True)
            pose = private_pose(simulator.pose_ops)
            original_check = simulator.work.external_check
            calls = 0
            marker = RuntimeError("cancel unused object projection proof")

            def cancel():
                nonlocal calls
                original_check()
                calls += 1
                if calls == cancel_at:
                    raise marker

            simulator.work.external_check = cancel
            with self.assertRaises(RuntimeError) as caught:
                simulator._check_object_pose(pose)
            self.assertIs(caught.exception, marker)
            self.assertIs(simulator.work.callback_error, marker)
            self.assertEqual(pose._projection, {})

        simulator = self.simulator(planning=True)
        pose = private_pose(simulator.pose_ops, position=(F(1, 1 << 96), F(0), F(0)))
        original_check = simulator.work.external_check

        def narrow():
            original_check()
            simulator.work.max_operand_bits = 128

        simulator.work.external_check = narrow
        with self.assertRaises(ReachAdmissionError) as caught:
            simulator._check_object_pose(pose)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["limit"], 128)

    def test_small_source_artifact_is_identical_with_eager_unused_projection(self):
        outputs = []

        def eager(ops, pose):
            pose.position, pose.orientation, pose.velocity, pose.omega

        for lazy in (False, True):
            built = compile_construction(source_case("P01"))
            original = ReachPoseOps.ensure_finite
            with patch.object(ReachPoseOps, "ensure_finite", original if lazy else eager):
                artifact = export_glb(built.model,
                    options=ExportOptions(end=F(1, 4), fps=1),
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            outputs.append(artifact.data)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
