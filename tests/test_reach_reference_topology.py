"""Independent topology and axis reuse retain actual state and operand domains."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_reference import (
    MAX_CACHE, MAX_OPERAND_BITS, Interval, ReachReference, ReferenceError,
    _Arithmetic, _PoseArithmetic, build_reference,
)
from reach_agent_support import source_case


class Work:
    def __init__(self):
        self.operations = 0
        self.max_operand_bits = MAX_OPERAND_BITS
        self.callback = None

    def tick(self):
        self.operations += 1
        if self.callback is not None:
            self.callback()
        if self.operations > 100000:
            raise RuntimeError("shared work exhausted")


def previous_incoming(reference, state):
    result = {}
    for path, joint in reference.model.joints.items():
        reference.a.tick()
        if joint.kind != "grip" or path in state.grips:
            result[reference.model.sites[joint.child].owner] = ("joint", path)
    for path, follow in reference.model.follows.items():
        reference.a.tick()
        result[follow.child] = ("follow", path)
    return result


def previous_axis(pose, axis):
    norm = pose.norm(axis)
    return tuple(pose.a.div(value, norm) for value in axis)


def topology(arithmetic=None, *, child="arm"):
    reference = object.__new__(ReachReference)
    reference.a = arithmetic if arithmetic is not None else _Arithmetic(work=Work())
    reference._incoming_graph_identity = object()
    reference.model = SimpleNamespace(
        joints={"hinge": SimpleNamespace(kind="hinge", child="hinge_site"),
                "grip": SimpleNamespace(kind="grip", child="grip_site")},
        sites={"hinge_site": SimpleNamespace(owner=child),
               "grip_site": SimpleNamespace(owner="payload")},
        follows={"follow": SimpleNamespace(child="decoration")})
    return reference, SimpleNamespace(grips={"grip"})


class ReachReferenceTopologyTests(unittest.TestCase):
    def test_grip_changes_and_distinct_captured_models_have_exact_fresh_relations(self):
        reference, state = topology()
        before = reference._incoming(state)
        self.assertEqual(before, previous_incoming(reference, state))
        with self.assertRaises(TypeError):
            before["payload"] = ("joint", "other")
        state.grips.clear()
        after = reference._incoming(state)
        self.assertEqual(after, previous_incoming(reference, state))
        self.assertNotIn("payload", after)
        self.assertIn("payload", before)
        state.grips.add("grip")
        self.assertIs(reference._incoming(state), before)
        other, other_state = topology(reference.a, child="other_arm")
        independent = other._incoming(other_state)
        self.assertIn("other_arm", independent)
        self.assertNotIn("arm", independent)
        self.assertEqual(independent, previous_incoming(other, other_state))

    def test_graph_hits_are_charged_cancelable_bounded_and_reconstruct_after_eviction(self):
        reference, state = topology()
        graph = reference._incoming(state)
        start = reference.a.work.operations
        self.assertIs(reference._incoming(state), graph)
        self.assertGreater(reference.a.work.operations, start)
        for index in range(MAX_CACHE + 1):
            reference.a.remember(("evict_graph", index), F(index))
        self.assertEqual(len(reference.a.cache), MAX_CACHE)
        restored = reference._incoming(state)
        self.assertEqual(restored, graph)
        self.assertIsNot(restored, graph)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        marker = RuntimeError("cancel warm independent topology")
        def cancel():
            raise marker
        reference.a.work.callback = cancel
        with self.assertRaises(RuntimeError) as caught:
            reference._incoming(state)
        self.assertIs(caught.exception, marker)

    def test_cancelled_graph_traversal_never_publishes_a_partial_mapping(self):
        reference, state = topology()
        marker = RuntimeError("cancel cold independent topology")
        def cancel():
            if reference.a.work.operations == 4:
                raise marker
        reference.a.work.callback = cancel
        with self.assertRaises(RuntimeError) as caught:
            reference._incoming(state)
        self.assertIs(caught.exception, marker)
        self.assertFalse(any(key[0] == "incoming_graph" for key in reference.a.cache))
        reference.a.work.callback = None
        self.assertEqual(reference._incoming(state), previous_incoming(reference, state))

    def test_source_histories_and_phase_enclosures_equal_uncached_topology(self):
        for case in ("P01", "P13", "P16", "L02"):
            with self.subTest(case=case):
                current = compile_construction(source_case(case))
                actual = build_reference(current.model, end=current.model.duration, work=current.reach_work)
                carrier = next(action.reach.tip + ".frame" for action in current.model.actions.values()
                               if action.kind == "reach_planar")
                previous = compile_construction(source_case(case))
                with patch.object(ReachReference, "_incoming", previous_incoming):
                    expected = build_reference(previous.model, end=previous.model.duration,
                                               work=previous.reach_work)
                    expected_history = expected.boundary_states()
                    expected_phases = expected.phases(carrier, F(0), expected.end)
                self.assertEqual(actual.boundary_states(), expected_history)
                self.assertEqual(actual.phases(carrier, F(0), actual.end), expected_phases)
                self.assertLess(current.budget.operations, previous.budget.operations)
                self.assertLessEqual(len(actual.a.cache), MAX_CACHE)

    def test_changing_hinge_angles_reuse_only_the_exact_normalized_axis(self):
        for raw_axis in ((0, 0, 1), (3, 4, 0), (0, 0, -1)):
            with self.subTest(axis=raw_axis):
                current = _PoseArithmetic(_Arithmetic(work=Work()))
                previous = _PoseArithmetic(_Arithmetic(work=Work()))
                for clock in range(1, 5):
                    actual = current.hinge(raw_axis, F(clock, 8), F(clock), ideal=bool(clock % 2))
                    with patch.object(previous, "_normalized_axis", lambda axis: previous_axis(previous, axis)):
                        expected = previous.hinge(raw_axis, F(clock, 8), F(clock), ideal=bool(clock % 2))
                    self.assertEqual(actual, expected)
                self.assertLess(current.a.work.operations, previous.a.work.operations)
                self.assertLessEqual(len(current.a.cache), MAX_CACHE)
        pose = _PoseArithmetic(_Arithmetic(work=Work()))
        uncertain = (Interval(F(1), F(2)), Interval(F(3), F(4)), Interval(F(0), F(0)))
        self.assertEqual(pose._normalized_axis(uncertain), previous_axis(pose, uncertain))

    def test_axis_hits_recheck_live_domain_and_preserve_cancellation(self):
        work = Work()
        pose = _PoseArithmetic(_Arithmetic(work=work))
        axis = pose.vector((1 << 24, 0, 0))
        pose._normalized_axis(axis)
        def narrow():
            work.max_operand_bits = 20
        work.callback = narrow
        with self.assertRaises(ReferenceError) as caught:
            pose._normalized_axis(axis)
        self.assertEqual(caught.exception.code, "resource")
        work.callback = None
        work.max_operand_bits = MAX_OPERAND_BITS
        pose._normalized_axis(axis)
        marker = RuntimeError("cancel warm normalized independent axis")
        def cancel():
            raise marker
        work.callback = cancel
        with self.assertRaises(RuntimeError) as caught:
            pose._normalized_axis(axis)
        self.assertIs(caught.exception, marker)


if __name__ == "__main__":
    unittest.main()
