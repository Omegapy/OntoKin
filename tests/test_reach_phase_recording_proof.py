"""Optional recording angular laws are bound to fresh complete typed inputs."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_pose import RotationValue, UNIT
from test_reach_phase_coaxial import IDENTITY, chain, pose


def proof_chain():
    simulator = chain()
    simulator.model.program_revision = "test-coaxial-recording-proof"
    simulator.state.orientations = {"rig": IDENTITY}
    simulator.state.root_rotation_values = {}
    for action in simulator.model.actions.values():
        action.vector = None
    for active in simulator.state.actions.values():
        active.solution = None
        active.ideal_rotation_error = F(0)
        active.initial_rotation = None
    for joint in simulator.model.joints.values():
        joint.limits = (-10.0, 10.0)
    return simulator


def prove(simulator):
    return reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)


def current(simulator, kind, path):
    return reach_phase.current_recording_angular_witness(
        simulator.model, simulator.state, kind, path, work=simulator.work)


class RecordingAngularProofTests(unittest.TestCase):
    def test_opt_in_preserves_every_existing_result_and_publishes_immutable_laws(self):
        simulator = proof_chain()
        plain = reach_phase.phase_bounds(simulator, F(0), F(1))
        actual = prove(simulator)
        proof = actual.pop("recording_angular_proof")
        self.assertEqual(actual, plain)
        self.assertEqual((proof.start, proof.end, proof.program_revision),
                         (F(0), F(1), simulator.model.program_revision))
        self.assertEqual(set(proof.frames), set(actual["frames"]))
        record = proof.frames["second.frame"]
        self.assertEqual(record.rate.value, F(1))
        self.assertEqual(record.rate.axis, 2)
        self.assertEqual(record.parent, "first.end.frame")
        self.assertGreaterEqual(record.trig_count, 1)
        self.assertEqual(record.trig_count, actual["frames"]["second.frame"].trig_count)
        self.assertEqual(current(simulator, "joint", "elbow"), (record.parent, record.witness))
        with self.assertRaises(TypeError):
            proof.frames["second.frame"] = record
        with self.assertRaises(FrozenInstanceError):
            record.parent = "world"
        with self.assertRaises(FrozenInstanceError):
            proof.start = F(1)

    def test_each_new_proof_has_fresh_opaque_tokens_even_with_warm_numeric_cache(self):
        simulator = proof_chain()
        first = prove(simulator)["recording_angular_proof"]
        second = prove(simulator)["recording_angular_proof"]
        self.assertEqual(first, second)
        for path, record in first.frames.items():
            self.assertIs(type(record.token), object)
            self.assertIsNot(record.token, second.frames[path].token)
        self.assertLessEqual(len(simulator.work._cache), 256)
        self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))

    def test_changed_law_axis_pose_claim_clock_and_scalar_type_cannot_match(self):
        changes = (
            lambda sim: setattr(sim.model.joints["elbow"], "axis", (0.0, 0.0, -1.0)),
            lambda sim: setattr(sim.model.joints["elbow"], "axis", (0, 0, 1)),
            lambda sim: setattr(sim.model.joints["elbow"], "axis", (False, 0.0, 1.0)),
            lambda sim: setattr(sim.model.joints["elbow"], "limits", (-1.0, 1.0)),
            lambda sim: setattr(sim.model.sites["second.origin"], "pose", pose((0.0, 0.25, 0.0))),
            lambda sim: setattr(sim.model.sites["second.origin"], "pose", pose(rotation=(0.0, 0.0, 0.0, 1.0))),
            lambda sim: setattr(sim.state.actions["elbow"], "initial", -0.0),
            lambda sim: setattr(sim.state.actions["elbow"], "initial", 0),
            lambda sim: setattr(sim.state.actions["elbow"], "ideal_initial", F(1, 10)),
            lambda sim: setattr(sim.state.actions["elbow"], "elapsed", F(1, 4)),
            lambda sim: setattr(sim.state.actions["elbow"], "running_since", F(1, 4)),
            lambda sim: setattr(sim.state.actions["elbow"], "status", "paused"),
            lambda sim: setattr(sim.model.actions["elbow"], "duration", F(2)),
            lambda sim: setattr(sim.model.actions["elbow"], "goal", -0.75),
            lambda sim: sim.state.claims.__setitem__(("elbow", "coordinate"), "shoulder"),
        )
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                simulator = proof_chain()
                record = prove(simulator)["recording_angular_proof"].frames["second.frame"]
                change(simulator)
                self.assertNotEqual(current(simulator, "joint", "elbow"), (record.parent, record.witness))

    def test_stationary_root_orientation_and_parent_site_remain_in_the_witness(self):
        simulator = proof_chain()
        proof = prove(simulator)["recording_angular_proof"]
        root = proof.frames["rig.frame"]
        self.assertEqual(root.rate.value, 0)
        simulator.state.orientations["rig"] = (0.0, 0.0, 0.0, 1.0)
        self.assertNotEqual(current(simulator, "root", "rig"), (root.parent, root.witness))
        simulator.state.orientations["rig"] = IDENTITY
        simulator.state.root_rotation_values["rig"] = RotationValue(UNIT)
        self.assertNotEqual(current(simulator, "root", "rig"), (root.parent, root.witness))
        parent = proof.frames["first.end.frame"]
        simulator.model.sites["first.end"].pose = pose((1.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0))
        self.assertNotEqual(current(simulator, "site", "first.end"), (parent.parent, parent.witness))

    def test_mid_proof_local_mutation_omits_that_frame_and_its_descendants(self):
        simulator = proof_chain()
        original_witness = reach_phase.current_recording_angular_witness
        original_charge = simulator.work.charge
        armed = False
        seen = False

        def witness(model, state, kind, path, *, work):
            nonlocal armed, seen
            result = original_witness(model, state, kind, path, work=work)
            if kind == "site" and path == "first.end" and not seen:
                armed = seen = True
            return result

        def charge(kind="checkpoint", amount=1):
            nonlocal armed
            if kind == "phase_recording_proof_publish" and armed:
                simulator.model.sites["first.end"].pose = pose((1.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0))
                armed = False
            original_charge(kind, amount)

        with patch.object(reach_phase, "current_recording_angular_witness", witness), \
                patch.object(simulator.work, "charge", charge):
            proof = prove(simulator)["recording_angular_proof"]
        self.assertNotIn("first.end.frame", proof.frames)
        self.assertNotIn("second.frame", proof.frames)
        self.assertNotIn("second.tip.frame", proof.frames)

    def test_cancellation_lowered_domain_and_malformed_inputs_do_not_publish_authority(self):
        simulator = proof_chain()
        before = deepcopy(simulator.state.coordinates), dict(simulator.state.claims)
        marker = RuntimeError("cancel recording source witness")
        original = simulator.work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "recording_angular_witness_guard":
                with patch.object(simulator.work, "external_check", side_effect=marker):
                    return original(kind, amount)
            return original(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(RuntimeError) as caught:
                prove(simulator)
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertEqual((simulator.state.coordinates, simulator.state.claims), before)
        simulator.work = ReachExecutionWork(max_operand_bits=1024)
        self.assertIsNone(current(simulator, "joint", "elbow"))
        simulator.work = ReachExecutionWork()
        simulator.state.actions["elbow"].initial = (((((0.0,),),),),)
        self.assertIsNone(current(simulator, "joint", "elbow"))
        simulator.state.actions["elbow"].initial = float("nan")
        self.assertIsNone(current(simulator, "joint", "elbow"))
        for selector in (0, 1, "yes"):
            with self.assertRaises(ValueError):
                reach_phase.phase_bounds(proof_chain(), F(0), F(1), recording_proof=selector)


if __name__ == "__main__":
    unittest.main()
