"""Independent counterexamples for dynamic errors and normalised ideal rates."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import _Arithmetic, _PoseArithmetic, build_reference
from ontokin.reach_runtime import ReachSimulator
from tools.reach_source_rates import compare_rate_vector
from reach_agent_support import source_case


def variant(declarations, zero_events, later_events=""):
    payload = source_case("P01").to_payload()
    original = "    at 0[s] sequence { start reach; }"
    replacement = (declarations + "\n    at 0[s] sequence { start reach; "
                   + zero_events + " }\n" + later_events)
    assert payload["entry"]["source"].count(original) == 1
    payload["entry"]["source"] = payload["entry"]["source"].replace(original, replacement)
    return load_bundle(payload)


class IndependentAnchorDerivationTests(unittest.TestCase):
    def test_force_completion_retains_acceleration_discrepancy(self):
        # Exact ideal a = 1/3, whereas the public canonical acceleration is
        # binary64 1/3. At t=1 this creates Ea in v and Ea/2 in p, even
        # though the new phase's acceleration and all initial errors are zero.
        source = variant('    object payload @ "payload": shapes.Payload { mass = 3[kg]; motion = dynamic; }',
            'force payload @ "push" using vector(world, 1[N], 0[N], 0[N]) for 1[s];')
        compiler = compile_construction(source)
        snapshot = ReachSimulator(compiler.model, work=compiler.reach_work).advance(F(1), "after")
        unavailable = AssertionError("production expectation generator called")
        with patch("ontokin.reach_runtime.ReachSimulator", side_effect=unavailable), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=unavailable), \
             patch("ontokin.reach_kinematics.admit_planar", side_effect=unavailable):
            reference = build_reference(compiler.model, end=F(1), work=compiler.reach_work)
            anchor = reference._state_at(F(1), "after").dynamic["payload"]
            ea = abs(F(float(F(1, 3))) - F(1, 3))
            self.assertGreater(ea, 0)
            self.assertGreaterEqual(anchor.velocity_error, ea)
            self.assertGreaterEqual(anchor.position_error, ea / 2)
            self.assertEqual(anchor.time, 1)
            self.assertEqual(anchor.source_time, 1)
            ideal = reference.pose_enclosure("payload", F(1), "after")
            self.assertTrue(ideal.position[0].contains(F(1, 6)))
            self.assertTrue(ideal.velocity[0].contains(F(1, 3)))
            phase = reference.point_phase("payload", F(1), "after")
            result = compare_rate_vector(snapshot["objects"]["payload"]["velocity_m_per_s"],
                ideal.velocity, phase.source_numeric_velocity_error, work=compiler.reach_work)
        self.assertEqual(result["status"], "proved")
        self.assertLessEqual(compiler.reach_work.operations, 100000)

    def test_equal_canonical_force_retains_source_clock_and_moves_proof_clock(self):
        # 2^-54 is below half an ULP at 1. The exact ideal force changes at
        # t=1, while canonical net force and actual acceleration remain 1.
        tiny = "0.000000000000000055511151231257827021181583404541015625"
        source = variant('    object payload @ "payload": shapes.Payload { mass = 1[kg]; motion = dynamic; }',
            'force payload @ "push" using vector(world, 1[N], 0[N], 0[N]) for 2[s];',
            f'    at 1[s] sequence {{ force payload @ "tiny" using vector(world, {tiny}[N], 0[N], 0[N]) for 1[s]; }}')
        compiler = compile_construction(source)
        reference = build_reference(compiler.model, end=F(3, 2), work=compiler.reach_work)
        state = reference._state_at(F(1), "after")
        self.assertEqual(state.forces["payload"].acceleration, (1.0, 0.0, 0.0))
        self.assertEqual(state.forces["payload"].ideal_acceleration, (F(1) + F(1, 1 << 54), F(0), F(0)))
        self.assertEqual(state.dynamic["payload"].time, 1)
        self.assertEqual(state.dynamic["payload"].source_time, 0)
        actual = reference.pose_enclosure("payload", F(3, 2), ideal=False)
        ideal = reference.pose_enclosure("payload", F(3, 2), ideal=True)
        self.assertTrue(actual.velocity[0].contains(F(3, 2)))
        self.assertTrue(ideal.velocity[0].contains(F(3, 2) + F(1, 1 << 55)))
        self.assertTrue(ideal.position[0].contains(F(9, 8) + F(1, 1 << 57)))
        self.assertGreater(state.dynamic["payload"].velocity_error, 0)


class IndependentHingeRateTests(unittest.TestCase):
    def test_analytic_three_four_five_axis_uses_unit_ideal_rate(self):
        work = ReachExecutionWork()
        pose = _PoseArithmetic(_Arithmetic(work))
        actual = pose.hinge((3, 4, 0), F(0), F(2))
        ideal = pose.hinge((3, 4, 0), F(0), F(2), ideal=True)
        for value, expected in zip(actual.omega, (6, 8, 0)):
            self.assertTrue(value.contains(expected))
        for value, expected in zip(ideal.omega, (F(6, 5), F(8, 5), 0)):
            self.assertTrue(value.contains(expected))
        self.assertFalse(ideal.omega[0].contains(6))
        self.assertEqual(actual.orientation, ideal.orientation)

    def test_canonical_auxiliary_axis_defect_is_not_ideal_motion(self):
        source = variant('''    object auxiliary @ "auxiliary": shapes.Segment {}
    joint auxiliary_hinge @ "auxiliary-hinge": hinge {
        parent = rig.arm.forearm.hinge_tip;
        child = auxiliary.base;
        axis = vec3(0.6, 0.8, 0);
        limits = range(-180[deg], 180[deg]);
        initial = 0[rad];
    }
    action auxiliary_turn @ "auxiliary-turn" = tween(auxiliary_hinge, 1[rad], 1[s]);''',
            "start auxiliary_turn;")
        compiler = compile_construction(source)
        snapshot = ReachSimulator(compiler.model, work=compiler.reach_work).advance(F(0), "after")
        reference = build_reference(compiler.model, end=F(0), work=compiler.reach_work)
        axis = tuple(F(value) for value in compiler.model.joints["auxiliary_hinge"].axis)
        self.assertNotEqual(sum(value * value for value in axis), 1)
        ideal = reference.pose_enclosure("auxiliary", F(0))
        actual = snapshot["objects"]["auxiliary"]["angular_velocity_rad_per_s"]
        self.assertEqual(actual[:2], list(compiler.model.joints["auxiliary_hinge"].axis[:2]))
        # At zero all ancestor orientations are identity and their rates lie
        # along Z. The ideal X/Y rate therefore has unit Euclidean norm.
        squared = reference.a.total(reference.a.mul(value, value) for value in ideal.omega[:2])
        self.assertTrue(squared.contains(1))
        self.assertFalse(ideal.omega[0].contains(axis[0]))
        phase = reference.point_phase("auxiliary", F(0))
        result = compare_rate_vector(actual, ideal.omega,
            phase.source_numeric_angular_velocity_error, work=compiler.reach_work)
        self.assertEqual(result["status"], "proved")


if __name__ == "__main__":
    unittest.main()
