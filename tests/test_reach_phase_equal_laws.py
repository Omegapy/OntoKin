"""Equal source and ideal joint laws retain exact phase values and live guards."""
from contextlib import nullcontext
import copy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_export import recording_phase_bounds
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from test_reach_phase import source
from test_reach_phase_mounts import PlanningSimulator


def affine_case(*, kind="tween", initial=F(1, 8), ideal=F(1, 8),
                target=F(5, 4), duration=F(7), status="running", cap=MAX_OPERAND_BITS):
    elapsed = lambda time: F(time) if status == "running" else F(1, 4)
    action = SimpleNamespace(kind=kind, goal=target, duration=duration)
    active = SimpleNamespace(initial=initial, ideal_initial=ideal,
                             status=status, elapsed_at=elapsed)
    if kind == "reach_planar":
        action.reach = SimpleNamespace(shoulder="joint", elbow="other")
        active.initial = (initial, 0.)
        active.ideal_initial = (ideal, F(0))
        active.solution = SimpleNamespace(target_rad=(target, 0.))
    state = SimpleNamespace(claims={("joint", "coordinate"): "action"},
                            actions={"action": active})
    return SimpleNamespace(model=SimpleNamespace(actions={"action": action}), state=state,
                           work=ReachExecutionWork(max_operand_bits=cap))


def sample(simulator, start=F(1, 3), end=F(2, 3)):
    return reach_phase.joint_phase(simulator, "joint", start, end, simulator.state)


class ReachPhaseEqualLawTests(unittest.TestCase):
    def test_affine_values_and_exposure_allowance_match_exact_equations(self):
        for kind in ("tween", "reach_planar"):
            for status in ("running", "paused"):
                for initial, target, duration in ((F(1, 8), F(5, 4), F(7)),
                        (-0., 1.5, F(2)), (F(-7, 9), F(11, 13), F(3, 7)),
                        (F(0), F(0), F(1))):
                    with self.subTest(kind=kind, status=status, initial=initial):
                        simulator = affine_case(kind=kind, status=status, initial=initial,
                                                ideal=F(initial), target=target, duration=duration)
                        result = sample(simulator)
                        rate = (F(target) - F(initial)) / duration
                        times = (F(1, 3), F(2, 3)) if status == "running" else (F(1, 4), F(1, 4))
                        positions = tuple(F(initial) + rate * time for time in times)
                        allowance = max(map(abs, positions)) / (1 << 53) + F(3, 1 << 1075)
                        expected = reach_phase.JointPhase(*positions, *positions,
                            rate if status == "running" else F(0),
                            rate if status == "running" else F(0), allowance)
                        self.assertEqual(result, expected)
                        self.assertGreater(result.coordinate_error, 0)

    def test_identical_laws_remove_duplicate_arithmetic_without_extra_cache(self):
        outputs, costs, counts, caches = [], [], [], []
        for reuse in (True, False):
            simulator = affine_case()
            before = copy.deepcopy(simulator.state)
            with (nullcontext() if reuse else patch.object(reach_phase, "_same_joint_phase_law", return_value=False)):
                outputs.append(sample(simulator))
            costs.append(simulator.work.operations)
            counts.append(simulator.work.counts)
            caches.append(tuple(simulator.work._cache))
            self.assertEqual(simulator.state, before)
            self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))
            self.assertLessEqual(len(simulator.work._cache), 256)
        self.assertEqual(outputs[0], outputs[1])
        self.assertGreaterEqual(costs[1] - costs[0], 5)
        self.assertEqual(counts[0]["exact_div"], 1)
        self.assertEqual(counts[1]["exact_div"], 2)
        self.assertLess(counts[0]["exact_mul"], counts[1]["exact_mul"])
        self.assertEqual(caches[0], caches[1])

    def test_distinct_exact_anchors_keep_separate_laws_even_when_float_rounding_agrees(self):
        initial = F(1)
        ideal = initial + F(1, 1 << 100)
        self.assertEqual(float(initial), float(ideal))
        simulator = affine_case(initial=initial, ideal=ideal)
        actual = sample(simulator)
        baseline = affine_case(initial=initial, ideal=ideal)
        with patch.object(reach_phase, "_same_joint_phase_law", return_value=False):
            expected = sample(baseline)
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual.actual_slope, actual.ideal_slope)
        self.assertNotEqual(actual.actual_start, actual.ideal_start)
        self.assertEqual(simulator.work.counts["exact_div"], 2)

    def test_warm_key_keeps_changed_current_inputs_and_invalid_equal_types(self):
        simulator = affine_case()
        original = sample(simulator)
        simulator.state.actions["action"].ideal_initial = F(3, 8)
        changed = sample(simulator)
        self.assertNotEqual(changed, original)
        self.assertNotEqual(changed.actual_slope, changed.ideal_slope)
        for value in (False, float("nan"), float("inf"), F(1 << MAX_OPERAND_BITS)):
            with self.subTest(type=type(value).__name__):
                simulator.state.actions["action"].initial = value
                simulator.state.actions["action"].ideal_initial = value
                with self.assertRaises(ReachAdmissionError):
                    sample(simulator)

    def test_narrow_domain_keeps_original_prospective_zero_difference_check(self):
        # Each equal endpoint fits, but their unreduced difference would need
        # 1,402 denominator bits. Equality cannot bypass this admission rule.
        for reuse in (True, False):
            simulator = affine_case(initial=F(1, 1 << 700), ideal=F(1, 1 << 700),
                                    target=F(1), duration=F(1), cap=1100)
            with (nullcontext() if reuse else patch.object(reach_phase, "_same_joint_phase_law", return_value=False)):
                with self.assertRaises(ReachAdmissionError) as caught:
                    sample(simulator, F(0), F(0))
            self.assertEqual(caught.exception.reach_code, "reach_resource")
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertFalse(simulator.work._cache)

    def test_callback_narrowing_at_reuse_rate_or_endpoint_reenters_current_domain(self):
        for stage in ("phase_equal_joint_law", "exact_div", "phase_product_domain"):
            with self.subTest(stage=stage):
                simulator = affine_case(initial=F(1, 1 << 700), ideal=F(1, 1 << 700),
                                        target=F(1), duration=F(1))
                original = simulator.work.charge
                armed = False
                changed = False

                def charge(kind="checkpoint", amount=1):
                    nonlocal armed, changed
                    if kind == "phase_equal_joint_law":
                        armed = True
                    if armed and not changed and kind == stage:
                        simulator.work.max_operand_bits = 1100
                        changed = True
                    original(kind, amount)

                with patch.object(simulator.work, "charge", charge):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        sample(simulator, F(0), F(0))
                self.assertTrue(changed)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertFalse(simulator.work._cache)

    def test_cancelled_reuse_propagates_original_exception_without_publishing(self):
        simulator = affine_case()
        simulator.work.remember(("existing",), object())
        retained = tuple(simulator.work._cache.items())
        before = copy.deepcopy(simulator.state)
        original = simulator.work.charge
        marker = RuntimeError("cancel equal affine law")

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_equal_joint_law":
                with patch.object(simulator.work, "external_check", side_effect=marker):
                    return original(kind, amount)
            return original(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(RuntimeError) as caught:
                sample(simulator)
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertEqual(tuple(simulator.work._cache.items()), retained)
        self.assertEqual(simulator.state, before)

    def test_complete_source_phase_maps_equal_independent_affine_recalculation(self):
        cases = (("P23", F(0), F(2)), ("P01", F(0), F(2)),
                 ("L01", F(0), F(1, 2)), ("L02", F(1, 2), F(3, 2)),
                 ("P16", F(2), F(3)))
        for case, start, end in cases:
            with self.subTest(case=case):
                values = []
                for reuse in (True, False):
                    built = compile_construction(source(case))
                    simulator = PlanningSimulator(built.model, work=built.reach_work)
                    simulator.advance(start, "after")
                    before = copy.deepcopy(simulator.state)
                    with (nullcontext() if reuse else patch.object(reach_phase, "_same_joint_phase_law", return_value=False)):
                        values.append(recording_phase_bounds(simulator, start, end, recording_proof=True))
                    self.assertEqual(simulator.state, before)
                    self.assertLessEqual(built.budget.operations, 100000)
                    self.assertLessEqual(len(simulator.work._cache), 256)
                self.assertEqual(values[0], values[1])


if __name__ == "__main__":
    unittest.main()
