"""The Agent prefix can authorize one recording without a second source replay."""
from __future__ import annotations

import copy
from fractions import Fraction
import unittest
from unittest.mock import patch

from ontokin import program_runtime
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


class ReachDeliveryPlanTests(unittest.TestCase):
    def test_recording_retains_real_both_sides_and_separate_agent_action_projection(self):
        source = source_case("P01")
        observed = []
        snapshot = ReachSimulator.snapshot

        def observe(simulator, time, side):
            value = snapshot(simulator, time, side)
            observed.append((time, side, copy.deepcopy(value)))
            return value

        with patch.object(ReachSimulator, "snapshot", observe):
            compiler, result = program_runtime.prepare_delivery(source, until="0.25")
        self.assertEqual(result["outcome"], "valid", result)
        plan = compiler.reach_delivery_plan
        self.assertIs(plan.simulator.model, compiler.model)
        self.assertIs(plan.simulator.work, compiler.reach_work)
        self.assertEqual(plan.boundaries, (Fraction(0), Fraction(1, 4)))
        self.assertEqual([(time, side) for time, side, _ in observed], [
            (Fraction(0), "before"), (Fraction(0), "after"),
            (Fraction(1, 4), "before"), (Fraction(1, 4), "after")])
        for record in plan.boundary_records:
            for side in ("before", "after"):
                sample = next(value for _, observed_side, value in observed
                              if value["time_seconds"] == record["source_seconds"] and observed_side == side)
                self.assertEqual(record["action_states_" + side], sample["actions"])
                self.assertEqual(record["reach_states_" + side], sample["reaches"])
        current = result["run_state"]["last_valid_state"]
        self.assertEqual(current["actions"]["reach"]["value_type"], "AnglePair")
        self.assertIn("start_value", current["actions"]["reach"])
        self.assertIn("current_value", current["actions"]["reach"])
        self.assertIn("target_value", current["actions"]["reach"])
        self.assertNotIn("value_type", plan.boundary_records[-1]["action_states_after"]["reach"])
        # Publication later binds only the copied Agent result. The source
        # recording retains its own null run and accepted-source identities.
        current["reaches"]["reach"]["context_origin"] = "agent"
        current["reaches"]["reach"]["current"]["value"]["observation"]["run_id"] = "run:test"
        recorded = plan.boundary_records[-1]["reach_states_after"]["reach"]
        self.assertEqual(recorded["context_origin"], "source_recording")
        self.assertIsNone(recorded["current"]["value"]["observation"]["run_id"])

    def test_failed_future_boundary_preserves_prefix_and_never_exposes_partial_plan(self):
        source = source_case("L04")
        compiler, result = program_runtime.prepare_delivery(source, until="2")
        expected = program_runtime.evaluate_revision(source, until="2", profile=program_runtime.REACH_PROFILE)
        self.assertEqual(result["outcome"], expected["outcome"])
        self.assertEqual(result["diagnostics"], expected["diagnostics"])
        self.assertEqual(result["run_state"], expected["run_state"])
        self.assertEqual(result["run_state"]["valid_until_seconds"], "0.5")
        self.assertEqual(result["run_state"]["valid_until_side"], "before")
        self.assertFalse(hasattr(compiler, "reach_delivery_plan"))


if __name__ == "__main__":
    unittest.main()
