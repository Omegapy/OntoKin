"""Native detached path admission before torque recording callbacks."""
from dataclasses import replace
from fractions import Fraction as F
import unittest

from ontokin.reach_numeric import ReachAdmissionError
from ontokin.diagnostics import OntoKinError
from ontokin.torque_recording import fixed_path_admission
from test_torque_runtime import simulator, source


class TorqueRecordingPathTests(unittest.TestCase):
    def make(self, callback=None):
        owners = {}
        def check():
            if owners.get("armed") and callback is not None:
                callback(owners)
        sim, ledger = simulator(source("p01-spin-up"), check=check)
        owners.update(sim=sim, ledger=ledger)
        sim.advance(F(0))
        owners["armed"] = True
        return sim, ledger, owners

    def test_exact_affected_edges_are_precharged(self):
        sim, ledger, _ = self.make()
        before = sim.work.counts.get("torque_recording_path", 0)
        result = fixed_path_admission(sim, sim.state)
        self.assertEqual(result["ball.label.frame"], "ball")
        self.assertEqual(result["ball.arm.tip.frame"], "ball")
        self.assertIsNone(result["sibling.label.frame"])
        expected = sum(site.owner == "ball" or site.owner.startswith("ball.")
                       for site in sim.model.sites.values())
        expected += sum(follow.child.startswith("ball.") for follow in sim.model.follows.values())
        self.assertEqual(sim.work.counts["torque_recording_path"] - before, expected)
        self.assertEqual(ledger.stage, "execution")

    def test_original_callback_exception_preserves_identity_and_stage(self):
        sentinel = RuntimeError("original path callback")
        def interrupt(owners):
            if owners["ledger"].stage == "torque_recording_path":
                raise sentinel
        sim, ledger, _ = self.make(interrupt)
        with self.assertRaises(RuntimeError) as caught:
            fixed_path_admission(sim, sim.state)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(ledger.stage, "execution")

    def test_mutated_follow_parent_cannot_be_published(self):
        def mutate(owners):
            if owners["ledger"].stage == "torque_recording_path" and not owners.get("changed"):
                owners["changed"] = True
                follow = next(value for value in owners["sim"].model.follows.values()
                              if value.child == "ball.label")
                follow.parent = "sibling.frame"
        sim, ledger, _ = self.make(mutate)
        with self.assertRaises(OntoKinError) as caught:
            fixed_path_admission(sim, sim.state)
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
        self.assertEqual(ledger.stage, "execution")

    def test_equal_claim_table_replacement_fails_owner_guard(self):
        def mutate(owners):
            if owners["ledger"].stage == "torque_recording_path" and not owners.get("changed"):
                owners["changed"] = True
                owners["sim"].state.claims = dict(owners["sim"].state.claims)
        sim, ledger, _ = self.make(mutate)
        with self.assertRaises(ReachAdmissionError):
            fixed_path_admission(sim, sim.state)
        self.assertEqual(ledger.stage, "execution")

    def test_axis_latch_mutation_fails_native_snapshot_readmission(self):
        def mutate(owners):
            if owners["ledger"].stage == "torque_recording_path" and not owners.get("changed"):
                owners["changed"] = True
                owners["sim"].state.torques["ball"].axis = "world_x"
        sim, _, _ = self.make(mutate)
        with self.assertRaises(ReachAdmissionError):
            fixed_path_admission(sim, sim.state)

    def test_foreign_dependency_table_is_rejected_before_iteration(self):
        class Foreign(dict):
            def items(self):
                raise AssertionError("must reject before foreign iteration")
        sim, _, _ = self.make()
        sim.model.follows = Foreign(sim.model.follows)
        with self.assertRaises(OntoKinError) as caught:
            fixed_path_admission(sim, sim.state)
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")

    def test_ordered_release_removes_historical_grip_from_affected_path(self):
        sim, _ = simulator(source("p28-release-then-torque"))
        sim.advance(F(1), "before")
        self.assertIsNone(fixed_path_admission(sim, sim.state)["ball.frame"])
        sim.advance(F(1), "after")
        self.assertEqual(fixed_path_admission(sim, sim.state)["ball.arm.tip.frame"], "ball")


if __name__ == "__main__":
    unittest.main()
