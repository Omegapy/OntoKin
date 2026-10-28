"""Exact independent affine laws never retain clocks, owners or source states."""
from copy import deepcopy
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin import reach_reference
from ontokin.reach_reference import (
    MAX_CACHE, MAX_OPERAND_BITS, ReachReference, ReferenceError, _Action,
    _Arithmetic, _Uncertain, build_reference,
)
from reach_agent_support import source_case


def previous_coordinate(reference, joint, time, state, *, ideal=False):
    """The exact pre-reuse coordinate expression and its original guards."""
    reference.a.tick()
    owner = state.claims.get((joint, "coordinate"))
    if owner is None:
        return F((state.ideal_coordinates if ideal else state.coordinates)[joint]), F(0)
    action, active = reference.model.actions[owner], state.actions[owner]
    index = (action.reach.shoulder, action.reach.elbow).index(joint) if action.kind == "reach_planar" else None
    start = active.ideal_initial if ideal else active.initial
    initial = F(start[index] if index is not None else start)
    target = F(active.targets[index] if index is not None else action.goal)
    slope = reference.a.exact(reference.a.exact(target, initial, "sub"), action.duration, "div")
    coordinate = reference.a.exact(initial, reference.a.exact(slope, active.elapsed_at(time), "mul"), "add")
    if not ideal:
        coordinate = F(reference.a.round64(coordinate))
    return coordinate, slope if active.status == "running" else F(0)


def example(*, initial=F(1, 7), target=F(11, 13), duration=F(3), status="running", paired=False):
    reference = object.__new__(ReachReference)
    reference.a = _Arithmetic(work=ReachExecutionWork())
    action = SimpleNamespace(kind="reach_planar" if paired else "tween", goal=target, duration=duration,
                             reach=SimpleNamespace(shoulder="shoulder", elbow="elbow"))
    active = _Action(status=status, initial=(initial, -initial) if paired else initial,
                     ideal_initial=(initial, -initial) if paired else initial,
                     targets=(target, -target) if paired else None)
    reference.model = SimpleNamespace(actions={"action": action})
    state = SimpleNamespace(claims={("shoulder", "coordinate"): "action",
                                    ("elbow", "coordinate"): "action"},
                            actions={"action": active}, coordinates={"shoulder": .25},
                            ideal_coordinates={"shoulder": F(1, 3)})
    return reference, state, action, active


class ReachReferenceCoordinateLawTests(unittest.TestCase):
    def compare(self, reference, state, time, *, joint="shoulder", ideal=False):
        expected = object.__new__(ReachReference)
        expected.a = _Arithmetic(work=ReachExecutionWork())
        expected.model = reference.model
        actual = reference._coordinate(joint, time, state, ideal=ideal)
        self.assertEqual(actual, previous_coordinate(expected, joint, time, state, ideal=ideal))
        return actual

    def test_exact_laws_preserve_tweens_pairs_ideal_states_and_paused_clocks(self):
        for paired in (False, True):
            reference, state, _, active = example(paired=paired)
            for status in ("running", "paused", "completed", "running"):
                active.status, active.elapsed, active.since = status, F(1, 7), F(1, 11)
                for time in (F(1, 11), F(1, 3), F(2), F(3)):
                    for ideal in (False, True):
                        for joint in (("shoulder", "elbow") if paired else ("shoulder",)):
                            with self.subTest(paired=paired, status=status, time=time, ideal=ideal, joint=joint):
                                self.compare(reference, state, time, joint=joint, ideal=ideal)
            active.ideal_initial = (F(2, 7), F(-3, 7)) if paired else F(2, 7)
            self.compare(reference, state, F(1), ideal=True)
            self.compare(reference, state, F(1), ideal=False)
            del state.claims[("shoulder", "coordinate")]
            self.assertEqual(self.compare(reference, state, F(2)), (F(1, 4), F(0)))
            self.assertEqual(self.compare(reference, state, F(2), ideal=True), (F(1, 3), F(0)))

    def test_warm_law_omits_only_repeated_slope_arithmetic(self):
        for ideal in (False, True):
            reference, state, _, _ = example()
            reference._coordinate("shoulder", F(0), state, ideal=ideal)
            start = reference.a.work.operations
            with patch.object(reference.a, "exact", wraps=reference.a.exact) as operation:
                actual = reference._coordinate("shoulder", F(1, 3), state, ideal=ideal)
            self.assertEqual([call.args[2] for call in operation.call_args_list], ["mul", "add"])
            used = reference.a.work.operations - start
            old, old_state, _, _ = example()
            expected = previous_coordinate(old, "shoulder", F(1, 3), old_state, ideal=ideal)
            self.assertEqual(actual, expected)
            self.assertLess(used, old.a.work.operations)
            self.assertEqual(reference.a.work.max_operations, 100000)

    def test_current_law_owner_elapsed_and_status_cannot_reuse_a_sample(self):
        reference, state, action, active = example()
        for initial, target, duration in ((F(1, 7), F(11, 13), F(3)),
                                          (F(2, 7), F(11, 13), F(3)),
                                          (F(2, 7), F(12, 13), F(3)),
                                          (F(2, 7), F(12, 13), F(5))):
            active.initial = active.ideal_initial = initial
            action.goal, action.duration = target, duration
            self.compare(reference, state, F(1, 2))
            active.elapsed, active.since, active.status = F(2, 3), F(1, 4), "paused"
            self.compare(reference, state, F(2))
            active.status = "running"
            self.compare(reference, state, F(2))
        state.actions["replacement"] = deepcopy(active)
        reference.model.actions["replacement"] = deepcopy(action)
        state.claims[("shoulder", "coordinate")] = "replacement"
        state.actions["replacement"].elapsed = F(1, 17)
        self.compare(reference, state, F(3, 4))

    def test_current_projection_keeps_subnormal_midpoints_and_paused_unbounded_rate(self):
        cases = ((F(0), F(float.fromhex("0x0.0000000000001p-1022")), F(2), F(1)),
                 (F(1), F(math.nextafter(1., math.inf)), F(2), F(1)),
                 (F(0), F(1), F(1, 1 << 1074), F(1, 1 << 1075)))
        for initial, target, duration, elapsed in cases:
            with self.subTest(duration=duration):
                reference, state, _, active = example(initial=initial, target=target, duration=duration, status="paused")
                reference._coordinate("shoulder", F(0), state)
                active.elapsed = elapsed
                self.compare(reference, state, F(1))
                self.compare(reference, state, F(1), ideal=True)

    def test_warm_input_and_subtraction_preflights_precede_any_lookup(self):
        for initial, target, duration, error in (
                (F(1 << MAX_OPERAND_BITS), F(1), F(1), ReferenceError),
                (F(0), float("nan"), F(1), ValueError),
                (F(0), F(1), float("inf"), OverflowError),
                (F(0), F(1), F(1 << MAX_OPERAND_BITS), ReferenceError),
                (F(0), F(1), F(0), _Uncertain)):
            reference, state, action, active = example()
            reference._coordinate("shoulder", F(0), state)
            active.initial, action.goal, action.duration = initial, target, duration
            with self.subTest(error=error.__name__), patch.object(reference.a, "lookup", wraps=reference.a.lookup) as lookup:
                with self.assertRaises(error):
                    reference._coordinate("shoulder", F(1), state)
                lookup.assert_not_called()
        reference, state, _, _ = example(initial=F(1, 1 << 64), target=F(3, 1 << 64), duration=F(1))
        reference._coordinate("shoulder", F(0), state)
        with patch.object(reach_reference, "MAX_OPERAND_BITS", 125), patch.object(reference.a, "lookup", wraps=reference.a.lookup) as lookup:
            with self.assertRaises(ReferenceError) as caught:
                reference._coordinate("shoulder", F(1), state)
            self.assertEqual(caught.exception.code, "resource")
            lookup.assert_not_called()

    def test_lower_reference_cap_reexecutes_the_original_division_preflight(self):
        reference, state, _, _ = example(initial=F(0), target=F(1, 1 << 80), duration=F(1 << 80))
        reference._coordinate("shoulder", F(0), state, ideal=True)
        with patch.object(reach_reference, "MAX_OPERAND_BITS", 125), patch.object(reference.a, "exact", wraps=reference.a.exact) as operation:
            with self.assertRaises(ReferenceError) as caught:
                reference._coordinate("shoulder", F(1), state, ideal=True)
            self.assertEqual(caught.exception.code, "resource")
            self.assertEqual([call.args[2] for call in operation.call_args_list], ["sub", "div"])

    def test_failed_projection_and_cancellation_publish_no_new_law(self):
        reference, state, _, _ = example(initial=F(1 << 1024), target=F(1 << 1024), duration=F(1))
        with self.assertRaises(ReferenceError):
            reference._coordinate("shoulder", F(0), state)
        self.assertFalse(any(key[0] == "coordinate_affine_law" for key in reference.a.cache))
        reference, state, _, _ = example()
        reference._coordinate("shoulder", F(0), state)
        before = dict(reference.a.cache)
        marker = RuntimeError("cancel the reused independent affine law")
        callbacks = 0
        def cancel():
            nonlocal callbacks
            callbacks += 1
            if callbacks == 2:
                raise marker
        with patch.object(reference.a.work, "external_check", side_effect=cancel):
            with self.assertRaises(RuntimeError) as caught:
                reference._coordinate("shoulder", F(1), state)
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)
        self.assertEqual(reference.a.cache, before)

    def test_eviction_retains_only_bounded_pure_exact_slopes(self):
        reference, state, action, _ = example()
        for index in range(MAX_CACHE + 2):
            action.goal = F(index, 17)
            self.compare(reference, state, F(1, 4), ideal=True)
            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        laws = [(key, value) for key, value in reference.a.cache.items() if key[0] == "coordinate_affine_law"]
        self.assertTrue(laws)
        self.assertTrue(all(type(value) is F and all(type(part) is F for part in key[2:]) for key, value in laws))
        action.goal = F(0)
        self.compare(reference, state, F(1, 4), ideal=True)

    def test_complete_source_histories_and_pose_enclosures_equal_the_previous_expression(self):
        for name, end in (("P01", F(1, 4)), ("L01", F(7, 4)),
                          ("L02", F(3, 4)), ("P16", F(9, 4))):
            observations = []
            for old in (False, True):
                built = compile_construction(source_case(name))
                def observe():
                    reference = build_reference(built.model, end=end, work=built.reach_work)
                    frames = tuple(path + ".frame" for path in reference.model.objects)
                    return (reference.boundary_states(),
                            reference.recording_pose_enclosures(frames, end / 2),
                            reference.recording_pose_enclosures(frames, end))
                if old:
                    with patch.object(ReachReference, "_coordinate", previous_coordinate):
                        observations.append(observe())
                else:
                    observations.append(observe())
                self.assertLessEqual(built.reach_work.operations, 100000)
            with self.subTest(case=name):
                self.assertEqual(observations[0], observations[1])


if __name__ == "__main__":
    unittest.main()
