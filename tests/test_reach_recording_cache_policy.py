"""Changing recording nodes do not displace reusable bounded arithmetic."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from test_reach_recording_sampler import simulator


def prepared(case, start=F(0), end=F(2)):
    result = simulator(case)
    result.advance(start, "after")
    result.phase_bounds(start, end)
    return result


class ReachRecordingCachePolicyTests(unittest.TestCase):
    def test_varying_graphs_keep_exact_outputs_with_less_cache_work(self):
        for case, start, end in (("P09", F(0), F(2)), ("P16", F(0), F(2)),
                                  ("L02", F(1, 2), F(3, 2)), ("L03", F(0), F(2))):
            with self.subTest(case=case):
                outputs, costs = [], []
                for use_hint in (False, True):
                    sim = prepared(case, start, end)
                    paths = tuple(path + ".frame" for path in sim.model.objects)
                    moving = sim.recording_moving_frames(sim.state, paths)
                    source_cache = sim._pose_cache
                    before = sim.work.operations
                    outputs.append([sim.recording_frames(start + (end - start) * fraction,
                        sim.state, paths, moving_frames=moving if use_hint else None)
                        for fraction in (F(1, 8), F(1, 4), F(3, 8))])
                    costs.append(sim.work.operations - before)
                    self.assertIs(sim._pose_cache, source_cache)
                    self.assertLessEqual(len(sim.work._cache), sim.work.max_cache_entries)
                self.assertEqual(outputs[0], outputs[1])
                self.assertLess(costs[1], costs[0])

    def test_site_inherits_its_moving_owners_cache_policy(self):
        sim = prepared("P09")
        object_paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, object_paths)
        tip = "rig.arm.forearm.tip.frame"
        self.assertNotIn(tip, moving)  # Only object carriers were classified.
        with patch.object(sim, "_pose_slot", wraps=sim._pose_slot) as retained:
            sim.recording_frames(F(1, 3), sim.state, (*object_paths, tip), moving_frames=moving)
        paths = [call.args[0][1] for call in retained.call_args_list]
        self.assertIn("rig", paths)
        self.assertNotIn("rig.arm.upper", paths)
        self.assertNotIn("rig.arm.forearm", paths)
        self.assertNotIn(tip, paths)

    def test_incomplete_or_stale_hints_cannot_hide_changed_source_operands(self):
        sim = prepared("P01")
        paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, paths)
        first = sim.recording_frames(F(1, 3), sim.state, paths, moving_frames=moving)
        original_state = sim.state
        sim.state.positions["rig"] = (0.5, 0.25, 0.0)
        changed = sim.recording_frames(F(1, 3), sim.state, paths, moving_frames=moving)
        self.assertIs(sim.state, original_state)
        self.assertNotEqual(first["rig.arm.forearm.frame"], changed["rig.arm.forearm.frame"])
        self.assertEqual(changed, sim.recording_frames(F(1, 3), sim.state, paths))

        sim = prepared("L02", F(0), F(1, 2))
        paths = tuple(path + ".frame" for path in sim.model.objects)
        old_hint = sim.recording_moving_frames(sim.state, paths)
        sim.recording_frames(F(1, 4), sim.state, paths, moving_frames=old_hint)
        sim.advance(F(1, 2), "after")
        sim.phase_bounds(F(1, 2), F(3, 2))
        for hint in (old_hint, frozenset(), frozenset(paths)):
            self.assertEqual(sim.recording_frames(F(3, 4), sim.state, paths, moving_frames=hint),
                             sim.recording_frames(F(3, 4), sim.state, paths))

    def test_policy_keeps_lowered_cache_and_operand_limits(self):
        sim = prepared("P01")
        paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, paths)
        sim.work._cache.clear()
        sim.work.max_cache_entries = 8
        for time in (F(1, 8), F(1, 4), F(3, 8)):
            sim.recording_frames(time, sim.state, paths, moving_frames=moving)
            self.assertLessEqual(len(sim.work._cache), 8)
            self.assertLessEqual(len(sim._pose_cache), 1)
        sim.work.max_operand_bits = 2048
        selected = ("rig.frame",)
        moving = frozenset(selected)
        sim.recording_frames(F(0), sim.state, selected, moving_frames=moving)
        for invalid, code in (((False, 0.0, 0.0), "reach_domain"),
                              ((F(1 << 2048), F(0), F(0)), "reach_resource")):
            with self.subTest(invalid_code=code):
                sim.state.positions["rig"] = invalid
                with self.assertRaises(OntoKinError) as caught:
                    sim.recording_frames(F(0), sim.state, selected, moving_frames=moving)
                self.assertEqual(caught.exception.diagnostic.details["reach_code"], code)

    def test_bypassed_slot_checks_original_callback_before_building(self):
        sim = prepared("P09")
        paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, paths)
        sim.recording_frames(F(1, 4), sim.state, paths, moving_frames=moving)
        marker = RuntimeError("cancel changing recording node")
        original_charge, original_check = sim.work.charge, sim.work.external_check
        current = [None]

        def charge(kind="checkpoint", amount=1):
            current[0] = kind
            return original_charge(kind, amount)

        def check():
            if current[0] == "recording_moving_pose":
                raise marker
            if original_check is not None:
                original_check()

        with patch.object(sim.work, "charge", side_effect=charge), \
                patch.object(sim.work, "external_check", side_effect=check):
            with self.assertRaises(RuntimeError) as caught:
                sim.recording_frames(F(1, 3), sim.state, paths, moving_frames=moving)
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertLessEqual(len(sim.work._cache), sim.work.max_cache_entries)


if __name__ == "__main__":
    unittest.main()
