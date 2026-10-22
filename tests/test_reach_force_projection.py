"""Reach force JSON batching preserves every inherited output guard and field."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import force_runtime
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.force_runtime import ForceSimulator
from ontokin.json_limits import measure_json
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


def simulator(case="P01"):
    built = compile_construction(source_case(case))
    return ReachSimulator(built.model, work=built.reach_work)


def inherited(sim):
    return ForceSimulator._bounded_projection(sim, sim.state)


class ReachForceProjectionTests(unittest.TestCase):
    def test_active_completed_and_latest_force_histories_equal_inherited_output(self):
        for time, side in ((F(2), "before"), (F(2), "after"),
                           (F(5, 2), "after"), (F(3), "after")):
            with self.subTest(time=time, side=side):
                sim = simulator("P16")
                sim.advance(time, side)
                expected = inherited(sim)
                actual = sim._bounded_projection(sim.state)
                self.assertEqual(actual, expected)
                self.assertEqual(set(actual), set(sim.state.forces))
                actual["payload"]["last_changes"].append({"external": True})
                self.assertEqual(sim._bounded_projection(sim.state), expected)

    def test_exact_cumulative_entry_and_byte_thresholds_remain_inherited(self):
        sim = simulator()
        expected = inherited(sim)
        sizes = [measure_json(value) for value in expected.values()]
        limits = (("MAX_OUTPUT_RECORDS", sum(size["entries"] for size in sizes)),
                  ("MAX_JSON_BYTES", sum(size["bytes"] for size in sizes)))
        for name, required in limits:
            with self.subTest(budget=name), patch.object(force_runtime, name, required):
                self.assertEqual(inherited(sim), expected)
                self.assertEqual(sim._bounded_projection(sim.state), expected)
            errors = []
            with patch.object(force_runtime, name, required - 1):
                for old in (True, False):
                    with self.assertRaises(OntoKinError) as caught:
                        inherited(sim) if old else sim._bounded_projection(sim.state)
                    diagnostic = caught.exception.diagnostic
                    errors.append((diagnostic.code, diagnostic.details))
            self.assertEqual(errors[0], errors[1])
            self.assertEqual(errors[0][0], "OKL-E-RESOURCE")

    def test_nonfinite_cycles_types_and_depth_use_the_complete_original_walk(self):
        cyclic = []
        cyclic.append(cyclic)
        deep = []
        for _ in range(129):
            deep = [deep]
        malformed = ({"finite": float("inf")}, {"cycle": cyclic}, {"deep": deep},
                     {1: "invalid key"}, {"unsupported": object()}, {"unicode": "\ud800"})
        sim = simulator()
        for value in malformed:
            errors = []
            with patch.object(sim, "_projection", return_value=value):
                for old in (True, False):
                    with self.assertRaises(Exception) as caught:
                        inherited(sim) if old else sim._bounded_projection(sim.state)
                    error = caught.exception
                    diagnostic = getattr(error, "diagnostic", None)
                    errors.append((type(error), str(error),
                                   None if diagnostic is None else diagnostic.details))
            self.assertEqual(errors[0], errors[1])

    def test_large_empty_force_map_saves_only_traversal_work(self):
        sim = simulator("P23")
        used, values = [], []
        for old in (True, False):
            before = sim.work.operations
            values.append(inherited(sim) if old else sim._bounded_projection(sim.state))
            used.append(sim.work.operations - before)
        self.assertEqual(values[0], values[1])
        self.assertEqual(len(values[0]), len(sim.model.objects))
        self.assertLess(used[1], used[0])
        self.assertEqual(sim.work.max_operations, 100000)

    def test_empty_measurement_does_not_conflate_other_zero_or_count_encodings(self):
        sim = simulator()
        paths = list(sim.state.forces)
        sim.state.forces[paths[0]].net = (-0.0, 0.0, 0.0)
        sim.state.forces[paths[1]].net = (0, 0, 0)
        sim.state.forces[paths[2]].started_count = False
        expected = inherited(sim)
        sizes = [measure_json(value) for value in expected.values()]
        entries, byte_count = sum(value["entries"] for value in sizes), sum(value["bytes"] for value in sizes)
        with patch.object(force_runtime, "MAX_OUTPUT_RECORDS", entries), \
                patch.object(force_runtime, "MAX_JSON_BYTES", byte_count):
            self.assertEqual(sim._bounded_projection(sim.state), expected)
        errors = []
        with patch.object(force_runtime, "MAX_JSON_BYTES", byte_count - 1):
            for ordinary in (True, False):
                with self.assertRaises(OntoKinError) as caught:
                    inherited(sim) if ordinary else sim._bounded_projection(sim.state)
                errors.append(caught.exception.diagnostic.details)
        self.assertEqual(errors[0], errors[1])

    def test_partial_batch_cancellation_retains_identity_and_private_state(self):
        sim = simulator()
        before = deepcopy(sim.state.forces)
        marker = RuntimeError("cancel partial force JSON batch")
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            # The first call visits the object; the second flushes its bounded
            # JSON batch even though its history is much smaller than 128 checks.
            if calls == 2:
                raise marker
        with patch.object(sim.work, "external_check", side_effect=cancel):
            with self.assertRaises(RuntimeError) as caught:
                sim._bounded_projection(sim.state)
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertEqual(sim.state.forces, before)
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
