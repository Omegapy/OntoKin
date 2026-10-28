"""Exact phase results after eliminating repeated pure operand decoding."""
from contextlib import ExitStack
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_export import recording_phase_bounds
from ontokin.reach_numeric import ReachAdmissionError
from test_reach_phase import simulator, source
from test_reach_phase_mounts import PlanningSimulator, mounted_phases


def phase_key(key, kind):
    return len(key) > 2 and key[0] == reach_phase._CACHE_DOMAIN and key[2] == kind


def operation_case(kind):
    if kind in ("constant", "constant_extent_template"):
        sim = mounted_phases(1)
        sim.model.follows["mount_1"].offset.position = (0., .25, 0.)
        return sim, lambda: reach_phase.phase_bounds(sim, F(0), F(1))
    sim = simulator(source("P01"))
    path = sim.model.actions["reach"].reach.elbow
    if kind == "unclaimed_joint":
        sim.state.coordinates[path] = float.fromhex("0x0.0000000000001p-1022")
        sim.state.ideal_coordinates[path] = F(sim.state.coordinates[path])
    else:
        sim.advance(F(0), "after")
    if kind == "joint_local":
        return sim, lambda: reach_phase.phase_bounds(sim, F(0), F(2))
    return sim, lambda: reach_phase.joint_phase(sim, path, F(0), F(1, 2), sim.state)


def force_operation(stack, work, kind, operation):
    """A template needs a distinct constant; a publication needs a cold value."""
    original = work.lookup

    def lookup(key):
        if ((kind == "constant_extent_template" and phase_key(key, "constant"))
                or (operation == "remember" and phase_key(key, kind))):
            work.charge("cache_lookup")
            return None
        return original(key)

    stack.enter_context(patch.object(work, "lookup", lookup))


class ReachPhaseOperandReuseTests(unittest.TestCase):
    def test_complete_source_maps_equal_the_original_decoder_and_uniform_equations(self):
        for case, start, end in (("P23", F(0), F(2)), ("P23", F(2), F(3)),
                                 ("P01", F(0), F(2)), ("L01", F(0), F(1, 2)),
                                 ("L02", F(1, 2), F(3, 2)), ("P16", F(2), F(3))):
            with self.subTest(case=case, start=start):
                outputs, costs = [], []
                for reuse in (True, False):
                    built = compile_construction(source(case))
                    sim = PlanningSimulator(built.model, work=built.reach_work)
                    with ExitStack() as stack:
                        if not reuse:
                            stack.enter_context(patch.object(reach_phase, "_native_phase_key", return_value=None))
                        sim.advance(start, "after")
                        before_state = copy.deepcopy(sim.state)
                        before = built.budget.operations
                        outputs.append(recording_phase_bounds(sim, start, end))
                        costs.append(built.budget.operations - before)
                        self.assertEqual(sim.state, before_state)
                    self.assertLessEqual(built.budget.operations, 100000)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                self.assertEqual(outputs[0], outputs[1])
                if case == "P23":
                    self.assertLess(costs[0], costs[1])

    def test_translated_constant_templates_match_every_original_field(self):
        for extent in (F(1, 3), F(1 << 1900, 3), F(1, (1 << 1900) + 1)):
            with self.subTest(extent_bits=max(extent.numerator.bit_length(), extent.denominator.bit_length())):
                current = mounted_phases(4, extent=extent)
                previous = mounted_phases(4, extent=extent)
                actual = reach_phase.phase_bounds(current, F(0), F(1))
                with patch.object(reach_phase, "_native_phase_key", return_value=None):
                    expected = reach_phase.phase_bounds(previous, F(0), F(1))
                self.assertEqual(actual, expected)
                self.assertGreater(current.work.counts.get("phase_constant_extent_domain", 0), 0)
                self.assertLess(current.work.operations, previous.work.operations)

    def test_warm_constant_rechecks_changed_values_and_invalid_equal_types(self):
        sim, call = operation_case("constant")
        baseline = call()
        pose = sim.model.follows["mount_1"].offset
        for invalid in (False, float("nan"), F(1 << sim.work.max_operand_bits)):
            with self.subTest(invalid_type=type(invalid).__name__):
                with patch.object(pose, "position", (invalid, .25, 0.)):
                    with self.assertRaises(ReachAdmissionError):
                        call()
        with patch.object(pose, "position", (0., .5, 0.)):
            actual = call()
            with patch.object(reach_phase, "_native_phase_key", return_value=None):
                expected = call()
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, baseline)

    def test_narrowed_domain_replays_original_decode_after_lookup_and_publication(self):
        for kind in ("constant", "constant_extent_template", "unclaimed_joint", "claimed_joint", "joint_local"):
            for operation in ("lookup", "remember"):
                with self.subTest(kind=kind, operation=operation):
                    sim, call = operation_case(kind)
                    call()
                    observed = []
                    with ExitStack() as stack:
                        force_operation(stack, sim.work, kind, operation)
                        original = getattr(sim.work, operation)

                        def checked(key, *args):
                            if phase_key(key, kind):
                                observed.append(key)

                                def narrow():
                                    sim.work.max_operand_bits = 128

                                with patch.object(sim.work, "external_check", side_effect=narrow):
                                    return original(key, *args)
                            return original(key, *args)

                        stack.enter_context(patch.object(sim.work, operation, checked))
                        with self.assertRaises(ReachAdmissionError) as caught:
                            call()
                    self.assertTrue(observed)
                    self.assertEqual(caught.exception.reach_code, "reach_resource")
                    self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_cancelled_key_operations_keep_original_exception_and_completed_values(self):
        for kind in ("constant", "constant_extent_template", "unclaimed_joint", "claimed_joint", "joint_local"):
            for operation in ("lookup", "remember"):
                with self.subTest(kind=kind, operation=operation):
                    sim, call = operation_case(kind)
                    baseline = call()
                    retained = {key: value for key, value in sim.work._cache.items() if phase_key(key, kind)}
                    self.assertTrue(retained)
                    marker = RuntimeError("cancel phase operand " + kind + " " + operation)
                    with ExitStack() as stack:
                        force_operation(stack, sim.work, kind, operation)
                        original = getattr(sim.work, operation)

                        def checked(key, *args):
                            if phase_key(key, kind):
                                with patch.object(sim.work, "external_check", side_effect=marker):
                                    return original(key, *args)
                            return original(key, *args)

                        stack.enter_context(patch.object(sim.work, operation, checked))
                        with self.assertRaises(RuntimeError) as caught:
                            call()
                    self.assertIs(caught.exception, marker)
                    self.assertIs(sim.work.callback_error, marker)
                    for key, value in retained.items():
                        self.assertIs(sim.work._cache[key], value)
                    self.assertEqual(call(), baseline)


if __name__ == "__main__":
    unittest.main()
