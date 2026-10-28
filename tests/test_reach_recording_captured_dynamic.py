"""Captured free roots retain actual anchors, native bits and live receipts."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_pose import PoseValue
from test_reach_recording_captured_graph import bits
from test_reach_recording_captured_roots import begin, cursors, prepared, scalar


def dynamic_fixture(start=F(2), end=F(3)):
    return prepared("P16", start, end)


class ReachRecordingCapturedDynamicTests(unittest.TestCase):
    def test_actual_release_and_force_completion_match_every_native_bit_and_allowance(self):
        for start, end in ((F(2), F(3)), (F(3), F(4))):
            with self.subTest(start=start):
                times = tuple(start + (end - start) * value
                              for value in (F(1, 11), F(2, 11), F(3, 11), F(4, 11),
                                            F(6, 11), F(7, 11), F(8, 11), F(9, 11)))
                outcomes = []
                for batched in (False, True):
                    fixture = dynamic_fixture(start, end)
                    sim = fixture[0]
                    state = deepcopy(sim.state)
                    before = sim.work.operations
                    if batched:
                        phase = begin(fixture, times)
                        self.assertIsNotNone(phase)
                        graph = phase.phase.graph
                        node = graph.nodes["payload.frame"]
                        self.assertEqual(node.kind, "dynamic")
                        self.assertIsNone(node.record)
                        self.assertNotIn("payload.frame", graph.proof.frames)
                        self.assertNotIn("payload.frame", graph.original_proof.frames)
                        self.assertNotIsInstance(node.operands[0].position, PoseValue)
                        old = cursors(sim.work)
                        values = [bits(phase.sample(time)) for time in times]
                        self.assertEqual(cursors(sim.work), old)
                        phase.finish()
                    else:
                        values = [bits(scalar(fixture, time)) for time in times]
                    outcomes.append((values, sim.work.operations - before))
                    self.assertEqual(sim.state, state)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                    self.assertEqual(sim.work.max_operations, 100000)
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])

    def test_dynamic_private_spin_retains_the_original_127_step_reseed(self):
        times = tuple(F(3) + F(index, 200) for index in range(1, 131))
        outcomes = []
        for batched in (False, True):
            fixture = dynamic_fixture(F(3), F(4))
            sim = fixture[0]
            with patch.object(sim.pose_ops, "advance_orientation",
                              wraps=sim.pose_ops.advance_orientation) as seeds:
                if batched:
                    phase = begin(fixture, times)
                    self.assertIsNotNone(phase)
                    values = [bits(phase.sample(time)) for time in times]
                    self.assertEqual(len(phase.phase.publication.pending), 1)
                    self.assertFalse(cursors(sim.work))
                    phase.finish()
                else:
                    values = [bits(scalar(fixture, time)) for time in times]
                self.assertEqual(seeds.call_count, 2)
            outcomes.append(values)
        self.assertEqual(*outcomes)

    def test_complete_dynamic_receipt_rejects_each_current_source_change(self):
        cases = ("anchor_time", "anchor_since", "anchor_identity", "anchor_position",
                 "anchor_velocity", "anchor_omega", "anchor_rotation", "projection",
                 "mode", "claim", "gravity", "acceleration", "net_force", "force_payload",
                 "force_activation", "force_count", "ideal_acceleration", "anchor_error",
                 "error_clock", "mass", "bound", "topology")
        for change in cases:
            with self.subTest(change=change):
                fixture = dynamic_fixture()
                sim, _, source = fixture[:3]
                times = (F(17, 8), F(9, 4))
                phase = begin(fixture, times)
                self.assertIsNotNone(phase)
                phase.sample(times[0])
                anchor, history = sim.state.dynamic["payload"], sim.state.forces["payload"]
                initial = anchor.state
                if change == "anchor_time":
                    anchor.time += F(1, 16)
                elif change == "anchor_since":
                    anchor.since += F(1, 16)
                elif change == "anchor_identity":
                    sim.state.dynamic["payload"] = replace(anchor)
                elif change in {"anchor_position", "anchor_velocity", "anchor_omega"}:
                    field = {"anchor_position": "exact_position", "anchor_velocity": "exact_velocity",
                             "anchor_omega": "exact_omega"}[change]
                    old = getattr(initial, field)
                    anchor.state = replace(initial, **{field: (old[0] + F(1, 8), *old[1:])})
                elif change == "anchor_rotation":
                    old = initial.rotation.components
                    anchor.state = replace(initial, rotation=replace(initial.rotation,
                        components=(old[0], old[1], old[2], old[3] + F(1, 8))))
                elif change == "projection":
                    initial._projection["position"] = (99.0, 0.0, 0.0)
                elif change == "mode":
                    sim.state.modes["payload"] = "prescribed"
                elif change == "claim":
                    sim.state.claims[("payload", "orientation")] = "turn"
                elif change == "gravity":
                    sim.model.gravity = (0.0, 0.0, -1.0)
                elif change == "acceleration":
                    history.acceleration = (99.0, 0.0, 0.0)
                elif change == "net_force":
                    history.net = (99.0, 0.0, 0.0)
                elif change in {"force_payload", "force_activation"}:
                    force = next(iter(history.active.values()))
                    if change == "force_payload":
                        object.__setattr__(force.payload, "force_world_n", (99.0, 0.0, 0.0))
                    else:
                        object.__setattr__(force, "activation", F(17, 8))
                elif change == "force_count":
                    history.started_count += 1
                elif change == "ideal_acceleration":
                    sim.state.ideal_accelerations["payload"] = (F(99), F(0), F(0))
                elif change == "anchor_error":
                    sim.state.dynamic_errors["payload"] = replace(
                        sim.state.dynamic_errors["payload"], velocity_m_per_s=F(1))
                elif change == "error_clock":
                    sim.state.dynamic_error_times["payload"] += F(1, 16)
                elif change == "mass":
                    sim.model.objects["payload"].physical["mass"] += 1.0
                elif change == "bound":
                    old = source["frames"]["payload.frame"]
                    source["frames"]["payload.frame"] = replace(old, max_position_l1_m=old.max_position_l1_m + 1)
                else:
                    sim.state.active_grips.add("grip")
                phase.sample(times[1])
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(cursors(sim.work))

    def test_temporary_dynamic_source_replacements_cannot_contaminate_sampled_inputs(self):
        times = (F(17, 8), F(9, 4), F(19, 8))
        outcomes = []
        for mutate in (False, True):
            fixture = dynamic_fixture()
            sim = fixture[0]
            phase = begin(fixture, times)
            self.assertIsNotNone(phase)
            anchor, history = sim.state.dynamic["payload"], sim.state.forces["payload"]
            spin = phase.phase.graph.nodes["payload.frame"].operands[0].spin.original
            old = (anchor.state, history.acceleration, sim.model.gravity,
                   sim.state.ideal_accelerations["payload"], spin.precision_bits)
            if mutate:
                anchor.state = replace(anchor.state, exact_position=(F(99), F(0), F(0)),
                    exact_velocity=(F(99), F(0), F(0)), exact_omega=(F(0), F(0), F(99)))
                history.acceleration = (99.0, 0.0, 0.0)
                sim.model.gravity = (0.0, 0.0, -99.0)
                sim.state.ideal_accelerations["payload"] = (F(0), F(0), F(-99))
                object.__setattr__(spin, "precision_bits", 192)
            values = [bits(phase.sample(time)) for time in times]
            if mutate:
                (anchor.state, history.acceleration, sim.model.gravity,
                 sim.state.ideal_accelerations["payload"]) = old[:4]
                object.__setattr__(spin, "precision_bits", old[4])
            phase.finish()
            outcomes.append(values)
        self.assertEqual(*outcomes)

    def test_dynamic_cancellation_and_domain_changes_never_publish_a_private_cursor(self):
        for checkpoint in ("recording_body_cursor_reuse", "recording_captured_dynamic_guard", "cache_batch_domain"):
            for cancel in (False, True):
                with self.subTest(checkpoint=checkpoint, cancel=cancel):
                    fixture = dynamic_fixture(F(3), F(4))
                    sim = fixture[0]
                    times = (F(25, 8), F(13, 4))
                    phase = begin(fixture, times)
                    self.assertIsNotNone(phase)
                    phase.sample(times[0])
                    marker = fast._UnsupportedPlanar("original dynamic cancellation")
                    charge, hit = sim.work.charge, []
                    def checked(kind="checkpoint", amount=1):
                        if kind == checkpoint and not hit:
                            hit.append(True)
                            def reject():
                                sim.work.max_operand_bits = 128
                                if cancel:
                                    raise marker
                            sim.work.external_check = reject
                        return charge(kind, amount)
                    with patch.object(sim.work, "charge", side_effect=checked):
                        expected = fast._UnsupportedPlanar if cancel else fast.RecordingRoundingAmbiguity
                        with self.assertRaises(expected) as caught:
                            phase.sample(times[1])
                            phase.finish()
                    self.assertTrue(hit)
                    if cancel:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(sim.work.callback_error, marker)
                    self.assertFalse(cursors(sim.work))

    def test_unsupported_dynamic_roots_and_descendants_decline_before_future_clocks(self):
        for change in ("nonplanar_spin", "nonplanar_rotation", "missing_plan", "claim", "reattached", "descendant"):
            with self.subTest(change=change):
                fixture = dynamic_fixture()
                sim = fixture[0]
                anchor = sim.state.dynamic["payload"]
                if change == "nonplanar_spin":
                    anchor.state = replace(anchor.state, exact_omega=(F(1), F(0), F(0)))
                elif change == "nonplanar_rotation":
                    anchor.state = replace(anchor.state, rotation=replace(anchor.state.rotation,
                        components=(F(1), F(1), F(0), F(0))))
                elif change == "missing_plan":
                    sim.work._cache.pop(("reach_source_spin_phase", anchor.state.omega), None)
                elif change == "claim":
                    sim.state.claims[("payload", "translation")] = "travel"
                elif change == "reattached":
                    sim.state.active_grips.add("grip")
                else:
                    fixture = (sim, ("payload.origin.frame",), *fixture[2:])
                if change in ("nonplanar_spin", "nonplanar_rotation"):
                    # This deliberately synthesized native anchor has no
                    # applicable transition proof. Retaining the old witness
                    # instead must reject, as the transfer-admission test checks.
                    sim.state.dynamic_cells.pop("payload", None)
                before = sim.work.counts.get("recording_captured_phase_clock", 0)
                self.assertIsNone(begin(fixture, (F(17, 8), F(9, 4))))
                self.assertEqual(before, sim.work.counts.get("recording_captured_phase_clock", 0))

    def test_reentrant_dynamic_completion_retains_the_newer_complete_cursor(self):
        fixture = dynamic_fixture(F(3), F(4))
        sim = fixture[0]
        times = (F(25, 8), F(13, 4), F(27, 8))
        outer = begin(fixture, times)
        self.assertIsNotNone(outer)
        outer.sample(times[0])
        charge, inside, retained = sim.work.charge, [], []
        def checked(kind="checkpoint", amount=1):
            if kind == "recording_body_cursor_reuse" and not inside:
                inside.append(True)
                inner_times = (F(29, 8), F(15, 4))
                inner = begin(fixture, inner_times)
                for time in inner_times:
                    inner.sample(time)
                inner.finish()
                retained.append(cursors(sim.work))
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=checked):
            for time in times[1:]:
                outer.sample(time)
            outer.finish()
        self.assertEqual(len(retained), 1)
        self.assertEqual(cursors(sim.work), retained[0])
        self.assertLessEqual(len(sim.work._cache), 256)


if __name__ == "__main__":
    unittest.main()
