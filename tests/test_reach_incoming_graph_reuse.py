"""A checked incoming graph survives only the unchanged boundary entrance."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


class ColdBoundarySimulator(ReachSimulator):
    def _process_boundary(self, time):
        self._invalidate()
        return super()._process_boundary(time)


def prepared(case, simulator_class=ReachSimulator):
    compiled = compile_construction(source_case(case))
    return simulator_class(compiled.model, work=compiled.reach_work)


class ReachIncomingGraphReuseTests(unittest.TestCase):
    def test_complete_incoming_graph_is_reused_and_outputs_equal_reconstruction(self):
        for case, time in (("P01", F(0)), ("P01", F(2)), ("P05", F(2)), ("P16", F(2))):
            with self.subTest(case=case, time=time):
                actual, expected = prepared(case), prepared(case, ColdBoundarySimulator)
                self.assertEqual(actual.advance(time, "before"), expected.advance(time, "before"))
                incoming_state = actual.state
                incoming = actual._kinematics(time, incoming_state)
                calls = []
                original = actual._kinematics

                def observed(clock, state):
                    result = original(clock, state)
                    if state is incoming_state:
                        calls.append(result)
                    return result

                start, cold_start = actual.work.operations, expected.work.operations
                with patch.object(actual, "_kinematics", side_effect=observed):
                    result = actual.advance(time, "after")
                self.assertEqual(result, expected.advance(time, "after"))
                self.assertTrue(calls)
                self.assertIs(calls[0][0], incoming[0])
                self.assertIs(calls[0][1], incoming[1])
                self.assertIsNot(actual.state, incoming_state)
                self.assertLess(actual.work.operations - start, expected.work.operations - cold_start)
                self.assertLessEqual(len(actual._pose_cache), 1)
                self.assertLessEqual(len(actual.work._cache), 256)

    def test_mutating_the_same_staged_state_invalidates_incoming_rates(self):
        sim = prepared("P14")
        sim.advance(F(0), "after")
        staged = copy.deepcopy(sim.state)
        elbow_child = sim.model.sites[sim.model.joints[sim.model.actions["reach"].reach.elbow].child].owner
        for time, status, moving in ((F(1, 2), "paused", False), (F(3, 2), "running", True)):
            with self.subTest(status=status):
                incoming = sim._kinematics(time, staged)
                event = next(block.events[0] for block in sim.model.events if block.time == time)
                sim._event(event, time, staged, incoming[0], {}, set())
                self.assertEqual(sim._pose_cache, {})
                outgoing = sim._kinematics(time, staged)
                self.assertIsNot(outgoing[0], incoming[0])
                self.assertEqual(staged.actions["reach"].status, status)
                self.assertEqual(any(outgoing[0][elbow_child].omega), moving)
                self.assertEqual(outgoing[0][elbow_child].position, incoming[0][elbow_child].position)
                sim._invalidate()
                self.assertEqual(outgoing, sim._kinematics(time, staged))

    def test_failed_staged_validation_discards_graphs_and_preserves_incoming_state(self):
        sim = prepared("P16")
        before = sim.advance(F(2), "before")
        incoming_state, event_index = sim.state, sim.event_index
        marker = RuntimeError("reject complete staged release")
        original = sim._validate_staged

        def rejected(*arguments):
            original(*arguments)
            raise marker

        with patch.object(sim, "_validate_staged", side_effect=rejected):
            with self.assertRaises(RuntimeError) as caught:
                sim.advance(F(2), "after")
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.state, incoming_state)
        self.assertEqual(sim.event_index, event_index)
        self.assertEqual(sim._pose_cache, {})
        self.assertEqual(sim._derived_pose_cache, {})
        self.assertIsNone(sim._pending_reach_output)
        self.assertIsNone(sim._terminal_pose_context)
        self.assertEqual(sim.incoming_releases_at(F(2)), [])
        self.assertEqual(sim.snapshot(F(2), "before"), before)

    def test_cancellation_discards_warm_incoming_graph_without_publishing(self):
        sim = prepared("P01")
        before = sim.advance(F(0), "before")
        incoming_state, event_index = sim.state, sim.event_index
        self.assertTrue(sim._pose_cache)
        marker = RuntimeError("cancel boundary entrance")
        with patch.object(sim.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                sim._process_boundary(F(0))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertIs(sim.state, incoming_state)
        self.assertEqual(sim.event_index, event_index)
        self.assertEqual(sim._pose_cache, {})
        self.assertIsNone(sim._pending_reach_output)
        self.assertIsNone(sim._terminal_pose_context)
        self.assertEqual(sim.snapshot(F(0), "before"), before)


if __name__ == "__main__":
    unittest.main()
