"""Captured source identities retain exact output bits and complete receipts."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import phase_bounds
from test_reach_recording_captured_graph import bits
from test_reach_recording_captured_roots import begin, cursors, prepared


def receipt():
    fixture = prepared("P16", F(0), F(2))
    phase = begin(fixture, (F(1, 8), F(1, 4)))
    return fixture, phase, phase.phase.graph.nodes["payload.frame"]


class ReachCapturedIdentityTests(unittest.TestCase):
    def test_identity_selector_requires_complete_typed_native_child_witness(self):
        _, _, node = receipt()
        self.assertTrue(node.identity_child)
        self.assertTrue(capture._identity_child_witness(node.record))
        witness = node.record.witness
        for signed in ("0x0.0p+0", "-0x0.0p+0"):
            current = list(witness)
            current[8] = (("tuple", (("binary64", signed),) * 3),
                          ("tuple", (("binary64", "0x1.0000000000000p+0"),)
                           + (("binary64", signed),) * 3))
            self.assertTrue(capture._identity_child_witness(replace(node.record, witness=tuple(current))))
        for field, value in (
            (2, ("string", "hinge")), (9, ("claim",)),
            (8, (("tuple", (("binary64", "0x1.0000000000000p-2"),)
                  + (("binary64", "0x0.0p+0"),) * 2), witness[8][1])),
            (8, (witness[8][0], ("tuple", (("binary64", "-0x1.0000000000000p+0"),)
                                + (("binary64", "0x0.0p+0"),) * 3))),
            (8, (("tuple", (("integer", 0),) * 3), witness[8][1])),
            (8, (witness[8][0], ("tuple", (("rational", 1, 1),)
                                + (("binary64", "0x0.0p+0"),) * 3))),
        ):
            with self.subTest(field=field, value=value):
                current = list(witness)
                current[field] = value
                self.assertFalse(capture._identity_child_witness(replace(node.record, witness=tuple(current))))
        class ForeignEqual:
            def __eq__(self, other):
                raise AssertionError("foreign equality must not run")
        for field, value in ((0, ForeignEqual()), (2, ("string", ForeignEqual())),
                             (9, ForeignEqual()),
                             (8, (("tuple", (("binary64", ForeignEqual()),) * 3), witness[8][1]))):
            current = list(witness)
            current[field] = value
            self.assertFalse(capture._identity_child_witness(replace(node.record, witness=tuple(current))))

    def test_original_p16_identity_placement_preserves_all_bits_and_allowances(self):
        times = tuple(F(index, 16) for index in range(1, 16))
        outcomes = []
        for enabled in (False, True):
            fixture = prepared("P16", F(0), F(2))
            sim = fixture[0]
            mode = nullcontext() if enabled else patch.object(capture, "_identity_child_witness", return_value=False)
            with mode:
                phase = begin(fixture, times)
            self.assertIsNotNone(phase)
            node = phase.phase.graph.nodes["payload.frame"]
            self.assertEqual(node.identity_child, enabled)
            before = sim.work.operations
            values = [bits(phase.sample(time)) for time in times]
            phase.finish()
            outcomes.append((values, sim.work.operations - before))
            self.assertEqual(sim.work.max_operations, 100000)
            self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
            self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])

    def test_captured_identity_is_not_selected_from_later_live_pose_changes(self):
        times = (F(1, 8), F(1, 4), F(3, 8))
        results = []
        for mutate in (False, True):
            fixture = prepared("P16", F(0), F(2))
            sim = fixture[0]
            phase = begin(fixture, times)
            node = phase.phase.graph.nodes["payload.frame"]
            self.assertTrue(node.identity_child)
            child = sim.model.sites[sim.model.joints["grip"].child]
            local = child.pose
            saved = local.position, local.rotation
            if mutate:
                object.__setattr__(local, "position", (17.0, 0.0, 0.0))
                object.__setattr__(local, "rotation", (0.0, 0.0, 0.0, 1.0))
            try:
                results.append([bits(phase.sample(time)) for time in times])
            finally:
                object.__setattr__(local, "position", saved[0])
                object.__setattr__(local, "rotation", saved[1])
            phase.finish()
        self.assertEqual(*results)

    def test_nonidentity_child_cannot_be_promoted_by_a_transient_live_edit(self):
        times = (F(1, 8), F(1, 4))
        outcomes = []
        for mutate in (False, True):
            fixture = prepared("P16", F(0), F(2))
            sim, paths, _, moving, context, interval = fixture
            child = sim.model.sites[sim.model.joints["grip"].child]
            child.pose = replace(child.pose, position=(0.125, 0.0, 0.0))
            bounds = phase_bounds(sim, *interval, sim.state, selected_frames=paths, recording_proof=True)
            phase = begin((sim, paths, bounds, moving, context, interval), times)
            self.assertIsNotNone(phase)
            node = phase.phase.graph.nodes["payload.frame"]
            self.assertFalse(node.identity_child)
            self.assertIsNot(node.operands[2], child.pose)
            saved = child.pose.position
            if mutate:
                object.__setattr__(child.pose, "position", (0.0, 0.0, 0.0))
            try:
                outcomes.append([bits(phase.sample(time)) for time in times])
            finally:
                object.__setattr__(child.pose, "position", saved)
            phase.finish()
        self.assertEqual(*outcomes)

    def test_persistent_identity_source_change_rejects_the_whole_phase(self):
        for mutation in ("position", "rotation", "joint_kind", "child_owner"):
            with self.subTest(mutation=mutation):
                fixture, phase, node = receipt()
                sim = fixture[0]
                phase.sample(F(1, 8))
                joint = sim.model.joints["grip"]
                child = sim.model.sites[joint.child]
                if mutation == "position":
                    child.pose = replace(child.pose, position=(0.25, 0.0, 0.0))
                elif mutation == "rotation":
                    child.pose = replace(child.pose, rotation=(0.0, 0.0, 0.0, 1.0))
                elif mutation == "joint_kind":
                    joint.kind = "rigid"
                else:
                    child.owner = "rig"
                phase.sample(F(1, 4))
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(cursors(sim.work))

    def test_identity_placement_keeps_two_depths_and_exact_parent_values(self):
        fixture, phase, _ = receipt()
        ops = phase.phase.ops
        original = ops.recording_parent_origin
        matches = []
        def observed(parent, rotation):
            result = original(parent, rotation)
            if rotation is parent.rotation:
                matches.append((parent, result))
            return result
        with patch.object(ops, "recording_parent_origin", side_effect=observed):
            phase.sample(F(1, 8))
            phase.sample(F(1, 4))
            phase.finish()
        self.assertGreaterEqual(len(matches), 2)
        for parent, result in matches:
            self.assertEqual(result.depth, parent.depth + 2)
            self.assertIs(result.position, parent.position)
            self.assertIs(result.rotation, parent.rotation)
            self.assertIs(result.zeros, parent.zeros)

    def test_identity_placement_retains_the_unchanged_depth_ceiling(self):
        for depth in (62, 63):
            with self.subTest(depth=depth):
                fixture, phase, _ = receipt()
                sim, ops = fixture[0], phase.phase.ops
                original, seen = ops.recording_parent_origin, []
                def observed(parent, rotation):
                    if rotation is parent.rotation:
                        parent = replace(parent, depth=depth)
                        seen.append(depth)
                    result = original(parent, rotation)
                    if rotation is parent.rotation:
                        self.assertEqual(result.depth, 64)
                    return result
                with patch.object(ops, "recording_parent_origin", side_effect=observed):
                    if depth == 62:
                        phase.sample(F(1, 8))
                        phase.sample(F(1, 4))
                        phase.finish()
                    else:
                        with self.assertRaises(fast.RecordingRoundingAmbiguity):
                            phase.sample(F(1, 8))
                        self.assertFalse(cursors(sim.work))
                self.assertTrue(seen)

    def test_cancel_or_narrowing_at_identity_placement_cannot_publish(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                fixture, phase, _ = receipt()
                sim, ops = fixture[0], phase.phase.ops
                original = ops.recording_parent_origin
                marker = RuntimeError("cancel exact captured identity")
                reached = []
                def checked(parent, rotation):
                    if rotation is parent.rotation and not reached:
                        reached.append(True)
                        def callback():
                            if cancel:
                                raise marker
                            sim.work.max_operand_bits = 128
                        sim.work.external_check = callback
                    return original(parent, rotation)
                with patch.object(ops, "recording_parent_origin", side_effect=checked):
                    with self.assertRaises(RuntimeError if cancel else fast.RecordingRoundingAmbiguity) as caught:
                        phase.sample(F(1, 8))
                self.assertTrue(reached)
                if cancel:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(sim.work.callback_error, marker)
                self.assertFalse(cursors(sim.work))


if __name__ == "__main__":
    unittest.main()
