"""A validated boundary output is transferred once, without retaining aliases."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.json_limits import JSONLimitError
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


class FreshOutputSimulator(ReachSimulator):
    def _validate_staged(self, time, staged, incoming):
        super()._validate_staged(time, staged, incoming)
        self._pending_reach_output = None


def prepared(name="P01", cls=ReachSimulator):
    compiler = compile_construction(source_case(name))
    return cls(compiler.model, work=compiler.reach_work)


class ReachPendingOutputTests(unittest.TestCase):
    def test_every_observed_field_equals_fresh_boundary_reconstruction(self):
        for name, time in (("P01", F(0)), ("P01", F(2)), ("P05", F(0)),
                           ("P11", F(0)), ("P16", F(2)), ("P18", F(2)),
                           ("P19", F(2)), ("L01", F(1, 2)),
                           ("L02", F(1, 2)), ("L03", F(2))):
            with self.subTest(case=name, time=time):
                actual = prepared(name)
                expected = prepared(name, FreshOutputSimulator)
                self.assertEqual(actual.advance(time), expected.advance(time))
                self.assertLess(actual.work.operations, expected.work.operations)
                self.assertIsNone(actual._pending_reach_output)

    def test_output_moves_once_and_exposed_mutations_do_not_change_state(self):
        sim = prepared()
        sim._process_boundary(F(0))
        pending = sim._pending_reach_output[3]
        transferred = sim._reach_map(F(0), "after", sim.state)
        self.assertIs(transferred, pending)
        self.assertIsNone(sim._pending_reach_output)
        original = copy.deepcopy(transferred)
        transferred["reach"]["current"]["value"]["joint_coordinates_rad"][0] = 999.0
        fresh = sim._reach_map(F(0), "after", sim.state)
        self.assertEqual(fresh, original)
        self.assertIsNot(fresh, transferred)
        self.assertLessEqual(len(sim.work._cache), 256)

        # Public bounded_data still creates a separate complete JSON graph.
        sim = prepared()
        sim._process_boundary(F(0))
        pending = sim._pending_reach_output[3]
        public = sim.snapshot(F(0), "after")
        self.assertIsNot(public["reaches"], pending)
        public["reaches"]["reach"]["current"]["value"]["joint_coordinates_rad"][0] = 999.0
        self.assertNotEqual(pending["reach"]["current"]["value"]["joint_coordinates_rad"][0], 999.0)

    def test_time_side_context_and_state_misses_discard_the_pending_output(self):
        for change in ("time", "side", "context", "state", "invalidation"):
            with self.subTest(change=change):
                sim = prepared()
                sim._process_boundary(F(0))
                pending = sim._pending_reach_output[3]
                time, side, state = F(0), "after", sim.state
                if change == "time":
                    time = F(1, 4)
                elif change == "side":
                    side = "before"
                elif change == "context":
                    sim.context_kind = "one_time"
                elif change == "state":
                    state = copy.deepcopy(state)
                else:
                    sim._invalidate()
                actual = sim._reach_map(time, side, state)
                self.assertIsNot(actual, pending)
                self.assertIsNone(sim._pending_reach_output)
                self.assertEqual(actual, sim._reach_map(time, side, state))

    def test_failed_validation_and_cancelled_transfer_leave_no_pending_output(self):
        sim = prepared()
        sim._process_boundary(F(0))
        staged = copy.deepcopy(sim.state)
        from ontokin import reach_runtime
        original = reach_runtime.measure_reach_json

        def reject_releases(value, **kwargs):
            if value is sim._pending_releases:
                raise JSONLimitError("logical_json_entries", 100000, 100001)
            return original(value, **kwargs)

        with patch.object(reach_runtime, "measure_reach_json", reject_releases):
            with self.assertRaises(OntoKinError) as caught:
                sim._validate_staged(F(0), staged, {})
        self.assertEqual(caught.exception.diagnostic.details["reach_code"], "reach_resource")
        self.assertIsNone(sim._pending_reach_output)

        sim = prepared()
        sim._process_boundary(F(0))
        marker = RuntimeError("cancel output transfer")
        with patch.object(sim.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                sim._reach_map(F(0), "after", sim.state)
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertIsNone(sim._pending_reach_output)


if __name__ == "__main__":
    unittest.main()
