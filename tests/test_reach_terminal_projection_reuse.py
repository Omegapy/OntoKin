"""Natural static handoffs reuse only same-operand canonical p/q receipts."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, float_bits
from test_reach_terminal_static_graph import prepared


class ReachTerminalProjectionReuseTests(unittest.TestCase):
    def test_same_operands_keep_pq_bits_and_start_fresh_zero_rate_projections(self):
        simulator = prepared("P01")
        simulator.advance(F(2), "before")
        incoming = simulator._kinematics(F(2), simulator.state)[1]
        saved = {path: (pose.position, pose.orientation) for path, pose in incoming.items()}
        copied = []
        original, original_check = simulator._terminal_static_kinematics, simulator._check_object_pose
        active = [False]
        def resolve(*args):
            active[0] = True
            try:
                return original(*args)
            finally:
                active[0] = False
        def check(pose):
            if active[0]:
                copied.append(pose)
                self.assertEqual(set(pose._projection), {"position", "orientation"})
                self.assertEqual(set(pose._projection_domains), {"position", "orientation"})
                self.assertFalse(any(pose.exact_velocity))
                self.assertFalse(any(pose.exact_omega))
            return original_check(pose)
        with patch.object(simulator, "_terminal_static_kinematics", side_effect=resolve), \
                patch.object(simulator, "_check_object_pose", side_effect=check):
            simulator.advance(F(2), "after")
        self.assertTrue(copied)
        outgoing = simulator._kinematics(F(2), simulator.state)[1]
        for path, pose in outgoing.items():
            self.assertEqual(tuple(map(float_bits, pose.position)), tuple(map(float_bits, saved[path][0])))
            self.assertEqual(tuple(map(float_bits, pose.orientation)), tuple(map(float_bits, saved[path][1])))
            if path != "world":
                self.assertIs(pose._projection["position"], incoming[path]._projection["position"])
                self.assertIs(pose._projection["orientation"], incoming[path]._projection["orientation"])
            self.assertEqual(pose.velocity, (0.0, 0.0, 0.0))
            self.assertEqual(pose.omega, (0.0, 0.0, 0.0))
        self.assertTrue(any(any(pose.exact_omega) for pose in incoming.values()))

    def test_missing_changed_or_malformed_projection_receipts_use_fresh_projection(self):
        for variant in ("missing", "cap", "operand", "shape", "list", "boolean", "nonfinite"):
            with self.subTest(variant=variant):
                simulator = prepared("P01")
                simulator.advance(F(2), "before")
                action = simulator.model.actions["reach"]
                path = action.reach.tip + ".frame"
                incoming = simulator._kinematics(F(2), simulator.state)[1][path]
                expected = incoming.position
                original = simulator._terminal_static_kinematics
                def resolve(*args):
                    pose = simulator._terminal_pose_context.frames[path]
                    pose._projection["position"] = (99.0, 98.0, 97.0)
                    if variant == "missing":
                        pose._projection_domains.pop("position", None)
                    elif variant == "cap":
                        pose._projection_domains["position"] = (simulator.work.max_operand_bits - 1, pose.exact_position)
                    elif variant == "operand":
                        pose._projection_domains["position"] = (simulator.work.max_operand_bits,
                                                                 tuple(list(pose.exact_position)))
                    elif variant == "shape":
                        pose._projection_domains["position"] = (simulator.work.max_operand_bits,)
                    elif variant == "list":
                        pose._projection["position"] = [99.0, 98.0, 97.0]
                    elif variant == "boolean":
                        pose._projection["position"] = (True, 0.0, 0.0)
                    else:
                        pose._projection["position"] = (math.nan, 0.0, 0.0)
                    return original(*args)
                with patch.object(simulator, "_terminal_static_kinematics", side_effect=resolve):
                    simulator.advance(F(2), "after")
                outgoing = simulator._kinematics(F(2), simulator.state)[1][path]
                self.assertEqual(tuple(map(float_bits, outgoing.position)), tuple(map(float_bits, expected)))

    def test_cancelled_projection_transfer_keeps_complete_incoming_boundary(self):
        simulator = prepared("P01")
        before = simulator.advance(F(2), "before")
        state, index = simulator.state, simulator.event_index
        original, original_check = simulator.work.charge, simulator.work.external_check
        marker = RuntimeError("cancel terminal projection transfer")
        stage = [None]
        def charge(kind="checkpoint", amount=1):
            stage[0] = kind
            return original(kind, amount)
        def check():
            if stage[0] == "source_terminal_static_projections":
                raise marker
            if original_check is not None:
                original_check()
        with patch.object(simulator.work, "charge", side_effect=charge), \
                patch.object(simulator.work, "external_check", side_effect=check):
            with self.assertRaises(RuntimeError) as caught:
                simulator.advance(F(2), "after")
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertIs(simulator.state, state)
        self.assertEqual(simulator.event_index, index)
        self.assertEqual(simulator._pose_cache, {})
        self.assertIsNone(simulator._terminal_pose_context)
        self.assertEqual(simulator.snapshot(F(2), "before"), before)

    def test_cap_change_during_transfer_cannot_publish_an_old_domain_receipt(self):
        simulator = prepared("P01")
        simulator.advance(F(2), "before")
        state = simulator.state
        original = simulator.work.charge
        changed = []
        def charge(kind="checkpoint", amount=1):
            result = original(kind, amount)
            if kind == "source_terminal_static_projections" and not changed:
                simulator.work.max_operand_bits = 8
                changed.append(True)
            return result
        with patch.object(simulator.work, "charge", side_effect=charge):
            with self.assertRaises((ReachAdmissionError, OntoKinError)) as caught:
                simulator.advance(F(2), "after")
        self.assertEqual(changed, [True])
        error = caught.exception
        details = error.details if isinstance(error, ReachAdmissionError) else error.diagnostic.details
        self.assertEqual(details["budget"], "numeric_operand_bits")
        self.assertIs(simulator.state, state)
        self.assertEqual(simulator._pose_cache, {})
        self.assertIsNone(simulator._terminal_pose_context)


if __name__ == "__main__":
    unittest.main()
