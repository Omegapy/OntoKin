"""Reuse exact phase numbers without retaining source identity or mutable state."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import (
    CoordinatePath, MAX_CACHE, ReachReference, ReferenceError, _Action,
    _Arithmetic, build_reference,
)
from reach_agent_support import source_case


def previous_joint_path(reference, joint, start, end, state):
    """Original independent phase expression, before pure-law reuse."""
    owner = state.claims.get((joint, "coordinate"))
    active = None if owner is None else state.actions[owner]
    action = None if owner is None else reference.model.actions[owner]
    if action is not None and action.kind == "reach_planar":
        index = (action.reach.shoulder, action.reach.elbow).index(joint)
        initial, target, ideal_initial = F(active.initial[index]), F(active.targets[index]), F(active.ideal_initial[index])
    elif action is not None:
        initial, target, ideal_initial = F(active.initial), F(action.goal), F(active.ideal_initial)
    else:
        initial = target = F(state.coordinates[joint])
        ideal_initial = F(state.ideal_coordinates[joint])
    op = reference.a.exact
    actual_slope = F(0) if active is None else op(op(target, initial, "sub"), action.duration, "div")
    ideal_slope = F(0) if active is None else op(op(target, ideal_initial, "sub"), action.duration, "div")
    elapsed = (F(0), F(0)) if active is None else (active.elapsed_at(start), active.elapsed_at(end))
    actual = tuple(op(initial, op(actual_slope, time, "mul"), "add") for time in elapsed)
    ideal = tuple(op(ideal_initial, op(ideal_slope, time, "mul"), "add") for time in elapsed)
    error = max(abs(op(x, y, "sub")) for x, y in zip(actual, ideal))
    if active is not None:
        error = op(error, op(op(max(abs(x) for x in actual), F(1, 1 << 53), "mul"), F(3, 1 << 1075), "add"), "add")
    if active is not None and active.status != "running":
        actual_slope = ideal_slope = F(0)
    return CoordinatePath(joint, owner, initial, target, elapsed[0], None if action is None else action.duration,
        ideal_slope, *actual, ideal_initial, *ideal, actual_slope, error)


def example(*, paired=False):
    reference = object.__new__(ReachReference)
    reference.a = _Arithmetic(work=ReachExecutionWork())
    action = SimpleNamespace(kind="reach_planar" if paired else "tween", goal=F(11, 13), duration=F(3),
                             reach=SimpleNamespace(shoulder="shoulder", elbow="elbow"))
    initial, ideal, target = F(1, 7), F(2, 7), F(11, 13)
    active = _Action(status="running", initial=(initial, -initial) if paired else initial,
                     ideal_initial=(ideal, -ideal) if paired else ideal,
                     targets=(target, -target) if paired else None)
    reference.model = SimpleNamespace(actions={"action": action})
    state = SimpleNamespace(claims={("shoulder", "coordinate"): "action", ("elbow", "coordinate"): "action"},
                            actions={"action": active}, coordinates={"shoulder": .25},
                            ideal_coordinates={"shoulder": F(1, 3)})
    return reference, state, action, active


class ReachReferencePathLawTests(unittest.TestCase):
    def compare(self, reference, state, start, end, joint="shoulder"):
        expected = object.__new__(ReachReference)
        expected.a = _Arithmetic(work=ReachExecutionWork())
        expected.model = reference.model
        result = reference._joint_path(joint, start, end, state)
        self.assertEqual(result, previous_joint_path(expected, joint, start, end, state))
        return result

    def test_tween_and_pair_laws_preserve_every_phase_number_and_lifecycle(self):
        for paired in (False, True):
            reference, state, _, active = example(paired=paired)
            for status in ("running", "paused", "completed", "running"):
                active.status, active.elapsed, active.since = status, F(1, 7), F(1, 11)
                for start, end in ((F(0), F(0)), (F(1, 11), F(1, 3)), (F(2), F(3))):
                    for joint in (("shoulder", "elbow") if paired else ("shoulder",)):
                        with self.subTest(paired=paired, status=status, start=start, joint=joint):
                            self.compare(reference, state, start, end, joint)
            del state.claims[("shoulder", "coordinate")]
            self.compare(reference, state, F(1), F(2))

    def test_equal_numeric_laws_keep_distinct_fresh_joint_and_action_identities(self):
        reference, state, action, active = example()
        first = self.compare(reference, state, F(0), F(1))
        reference.model.actions["replacement"] = deepcopy(action)
        state.actions["replacement"] = deepcopy(active)
        state.claims[("different_joint", "coordinate")] = "replacement"
        before = reference.a.work.operations
        with patch.object(reference.a, "exact", side_effect=AssertionError("recomputed pure law")):
            other = reference._joint_path("different_joint", F(0), F(1), state)
        self.assertEqual(reference.a.work.operations - before, 1)
        self.assertEqual((other.joint, other.action), ("different_joint", "replacement"))
        self.assertEqual((first.joint, first.action), ("shoulder", "action"))
        self.assertIsNot(first, other)
        self.assertEqual(other.coordinate_error, first.coordinate_error)
        self.assertEqual(other.actual_end, first.actual_end)

    def test_each_changed_numeric_operand_cannot_reuse_the_previous_phase(self):
        reference, state, action, active = example()
        self.compare(reference, state, F(0), F(1))
        changes = (
            lambda: setattr(active, "initial", F(2, 9)),
            lambda: setattr(active, "ideal_initial", F(4, 11)),
            lambda: setattr(action, "goal", F(13, 17)),
            lambda: setattr(action, "duration", F(4)),
            lambda: setattr(active, "elapsed", F(1, 13)),
            lambda: setattr(active, "since", F(1, 19)),
            lambda: setattr(active, "status", "paused"),
        )
        for index, change in enumerate(changes):
            change()
            with self.subTest(index=index):
                self.compare(reference, state, F(0), F(1))
                self.compare(reference, state, F(1, 7), F(5, 4))

    def test_warm_inputs_and_lowered_domain_keep_the_original_failure(self):
        reference, state, action, active = example()
        self.compare(reference, state, F(0), F(1))
        active.initial = F(1 << 32768)
        with patch.object(reference.a, "lookup", side_effect=AssertionError("hashed unguarded input")):
            with self.assertRaises(ReferenceError) as caught:
                reference._joint_path("shoulder", F(0), F(1), state)
        self.assertEqual(caught.exception.code, "resource")
        reference, state, action, active = example()
        active.initial = active.ideal_initial = F(0)
        action.goal, action.duration = F(1, 1 << 80), F(1 << 80)
        self.compare(reference, state, F(0), F(1))
        reference.a.work.max_operand_bits = 125
        with self.assertRaises(ReferenceError) as caught:
            reference._joint_path("shoulder", F(0), F(1), state)
        self.assertEqual(caught.exception.code, "resource")

    def test_cancellation_keeps_exception_identity_and_publishes_no_new_law(self):
        reference, state, _, _ = example()
        self.compare(reference, state, F(0), F(1))
        before = dict(reference.a.cache)
        marker = RuntimeError("cancel current independent phase proof")
        with patch.object(reference.a.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reference._joint_path("shoulder", F(0), F(1), state)
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)
        self.assertEqual(reference.a.cache, before)

    def test_eviction_keeps_the_original_cache_capacity_and_exact_recomputation(self):
        reference, state, action, _ = example()
        for index in range(MAX_CACHE + 2):
            action.goal = F(index, 17)
            self.compare(reference, state, F(0), F(1))
            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        action.goal = F(0)
        self.compare(reference, state, F(0), F(1))
        self.assertEqual(reference.a.work.max_operations, 100000)

    def test_actual_source_phases_equal_uncached_laws_and_use_less_work(self):
        for case, end in (("P01", F(1, 4)), ("P13", F(1, 4)),
                          ("L02", F(3, 4)), ("P16", F(9, 4))):
            values, operations = [], []
            for old in (False, True):
                context = patch.object(ReachReference, "_joint_path", previous_joint_path) if old else nullcontext()
                with context:
                    compiled = compile_construction(source_case(case))
                    reference = build_reference(compiled.model, end=end, work=compiled.reach_work)
                    values.append(tuple(reference.phases(path + ".frame", F(0), end)
                                        for path in reference.model.objects))
                    operations.append(compiled.budget.operations)
            with self.subTest(case=case):
                self.assertEqual(values[0], values[1])
                self.assertLess(operations[0], operations[1])


if __name__ == "__main__":
    unittest.main()
