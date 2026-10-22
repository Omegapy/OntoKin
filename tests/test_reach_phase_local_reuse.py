"""Shared joint equations retain each source joint's exact phase and guards."""
import copy
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.reach_numeric import ReachAdmissionError
from test_reach_phase import simulator, source


@contextmanager
def recompute_local_bounds(work):
    original = work.lookup

    def lookup(key):
        if key[0] == reach_phase._CACHE_DOMAIN and key[2] == "joint_local":
            work.charge("cache_lookup")
            return None
        return original(key)

    with patch.object(work, "lookup", lookup):
        yield


class ReachPhaseLocalReuseTests(unittest.TestCase):
    def test_repeated_chains_match_exact_recomputation_with_less_work(self):
        # The two translated chains have their own source identities and
        # coordinate claims but share the same numerical hinge laws.
        outputs, costs = [], []
        for reuse in (True, False):
            sim = simulator(source("P23"))
            sim.advance(F(0), "after")
            paths = tuple(path + ".frame" for path in sim.model.objects
                          if '["first"]' in path or '["part-01"]' in path)
            before = sim.work.operations
            # Complete-node reuse can omit the local helper in either mode.
            # Isolate this local-cache comparison while retaining its strict
            # exact-result and work-reduction assertions.
            with patch.object(reach_phase, "_reuse_phase_nodes", return_value=False):
                if reuse:
                    result = reach_phase.phase_bounds(sim, F(0), F(2), selected_frames=paths)
                else:
                    with recompute_local_bounds(sim.work):
                        result = reach_phase.phase_bounds(sim, F(0), F(2), selected_frames=paths)
            outputs.append(result)
            costs.append(sim.work.operations - before)
            self.assertLessEqual(len(sim.work._cache), 256)
            self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
        self.assertEqual(outputs[0], outputs[1])
        self.assertLess(costs[0], costs[1])

    def test_changed_local_axis_and_ideal_law_cannot_borrow_a_bound(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        payload = sim.model.actions["reach"].reach
        joint = sim.model.joints[payload.elbow]
        baseline = reach_phase.phase_bounds(sim, F(0), F(2))
        for change in ("axis", "ideal_rate", "coordinate_error", "kind"):
            with self.subTest(change=change):
                state = copy.deepcopy(sim.state)
                axis, kind = joint.axis, joint.kind
                original = reach_phase.joint_phase

                def changed_phase(owner, path, start, end, current):
                    value = original(owner, path, start, end, current)
                    if path == payload.elbow:
                        if change == "ideal_rate":
                            value = replace(value, ideal_slope=value.ideal_slope + F(1, 32))
                        elif change == "coordinate_error":
                            value = replace(value, coordinate_error=value.coordinate_error + F(1, 1024))
                    return value

                if change == "axis":
                    axis = (F(3, 5), F(4, 5), F(0))
                elif change == "kind":
                    kind = "slider"
                with patch.object(joint, "axis", axis), patch.object(joint, "kind", kind), \
                        patch.object(reach_phase, "joint_phase", changed_phase):
                    actual = reach_phase.phase_bounds(sim, F(0), F(2), state)
                    with recompute_local_bounds(sim.work):
                        expected = reach_phase.phase_bounds(sim, F(0), F(2), state)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, baseline)

    def test_warm_joint_bound_rejects_equal_boolean_and_oversized_operands(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        reach_phase.phase_bounds(sim, F(0), F(2))
        original = reach_phase.joint_phase
        for invalid in (False, F(1 << sim.work.max_operand_bits)):
            with self.subTest(invalid_type=type(invalid).__name__):
                def changed_phase(*args):
                    return replace(original(*args), actual_start=invalid)
                with patch.object(reach_phase, "joint_phase", changed_phase):
                    with self.assertRaises(ReachAdmissionError):
                        reach_phase.phase_bounds(sim, F(0), F(2))

    def test_warm_joint_lookup_preserves_original_cancellation(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        reach_phase.phase_bounds(sim, F(0), F(2))
        original = sim.work.lookup
        marker = RuntimeError("cancel at the shared local bound")

        def lookup(key):
            if key[0] == reach_phase._CACHE_DOMAIN and key[2] == "joint_local":
                with patch.object(sim.work, "external_check", side_effect=marker):
                    return original(key)
            return original(key)

        with patch.object(sim.work, "lookup", lookup):
            with self.assertRaises(RuntimeError) as caught:
                reach_phase.phase_bounds(sim, F(0), F(2))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
