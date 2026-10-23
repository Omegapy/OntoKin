"""Captured prescribed roots retain native arithmetic and final live admission."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import phase_bounds
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_graph import bits
from test_reach_recording_sampler import simulator


def prepared(case="P05", start=F(0), end=F(2)):
    sim = simulator(case)
    sim.advance(start, "after")
    all_paths = tuple(path + ".frame" for path in sim.model.objects)
    moving = sim.recording_moving_frames(sim.state, all_paths)
    paths = tuple(path for path in all_paths if path in moving)
    bounds = phase_bounds(sim, start, end, sim.state, selected_frames=paths, recording_proof=True)
    return sim, paths, bounds, moving, object(), (start, end)


def begin(fixture, times):
    sim, paths, bounds, _, context, interval = fixture
    return fast.begin_bounded_phase(sim, times, sim.state, paths, context=context,
        phase_bounds=bounds["frames"], phase_interval=interval,
        recording_angular_proof=bounds["recording_angular_proof"])


def scalar(fixture, time):
    sim, paths, bounds, moving, context, interval = fixture
    return fast.sample_bounded_frames(sim, time, sim.state, paths, context=context,
        moving_frames=moving, phase_bounds=bounds["frames"], phase_interval=interval,
        recording_angular_proof=bounds["recording_angular_proof"])


def cursors(work):
    return {key: value for key, value in work._cache.items()
            if len(key) > 2 and key[1] == "recording_rotation_cursor"
            and key[2] in {"certified_binary64_body", "certified_binary64_spin"}}


class ReachRecordingCapturedRootTests(unittest.TestCase):
    def test_prescribed_phase_matches_all_native_bits_and_allowances(self):
        for case, start, end in (("P05", F(0), F(2)), ("P05", F(2), F(3)),
                                 ("P16", F(0), F(2))):
            with self.subTest(case=case, start=start):
                times = tuple(start + (end - start) * F(index, 5) for index in (1, 2, 3, 4))
                outcomes = []
                for batched in (False, True):
                    fixture = prepared(case, start, end)
                    sim = fixture[0]
                    initial = deepcopy(sim.state)
                    before = sim.work.operations
                    if batched:
                        phase = begin(fixture, times)
                        self.assertIsNotNone(phase)
                        original = cursors(sim.work)
                        values = [bits(phase.sample(time)) for time in times]
                        self.assertEqual(cursors(sim.work), original)
                        phase.finish()
                    else:
                        values = [bits(scalar(fixture, time)) for time in times]
                    outcomes.append((values, sim.work.operations - before))
                    self.assertEqual(sim.state, initial)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                    self.assertEqual(sim.work.max_operations, 100000)
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLessEqual(outcomes[1][1], outcomes[0][1])
                if start == 0:
                    self.assertLess(outcomes[1][1], outcomes[0][1])

    def test_complete_prefix_bytes_match_without_captured_roots(self):
        data = []
        for enabled in (False, True):
            built = compile_construction(source_case("P05"), level="constructed")
            options = ExportOptions(end=F(1, 4), fps=1, helpers=False)
            if enabled:
                result = export_glb(built.model, options=options,
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            else:
                with patch.object(capture, "begin_captured_phase", return_value=None):
                    result = export_glb(built.model, options=options,
                        target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(built.budget.operations, 100000)
            data.append(result.data)
        self.assertEqual(*data)

    def test_final_receipt_rejects_each_prescribed_law_and_plan_change(self):
        for kind in ("move_vector", "move_initial", "move_clock", "spin_vector", "spin_initial",
                     "spin_clock", "claim", "root_position", "spin_plan"):
            with self.subTest(kind=kind):
                fixture = prepared()
                sim = fixture[0]
                times = (F(1, 8), F(1, 4))
                phase = begin(fixture, times)
                self.assertIsNotNone(phase)
                phase.sample(times[0])
                if kind == "move_vector":
                    sim.model.actions["travel"].vector = (0.75, 0.0, 0.0)
                elif kind == "move_initial":
                    sim.state.actions["travel"].initial = (0.125, 0.0, 0.0)
                elif kind == "move_clock":
                    sim.state.actions["travel"].running_since = F(1, 16)
                elif kind == "spin_vector":
                    sim.model.actions["turn"].vector = (0.0, 0.0, 0.5)
                elif kind == "spin_initial":
                    sim.state.actions["turn"].initial = (1.0, 0.0, 0.0, 0.125)
                elif kind == "spin_clock":
                    sim.state.actions["turn"].elapsed = F(1, 16)
                elif kind == "claim":
                    del sim.state.claims[("rig", "orientation")]
                elif kind == "root_position":
                    sim.state.positions["rig"] = (0.125, 0.0, 0.0)
                else:
                    plan = phase.phase.graph.nodes["rig.frame"].operands[4].original
                    object.__setattr__(plan, "precision_bits", plan.precision_bits + 1)
                phase.sample(times[1])
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(cursors(sim.work))

    def test_temporary_law_and_plan_mutations_never_change_captured_samples(self):
        times = (F(1, 8), F(1, 4), F(3, 8))
        results = []
        for mutate in (False, True):
            fixture = prepared()
            sim = fixture[0]
            phase = begin(fixture, times)
            self.assertIsNotNone(phase)
            root = phase.phase.graph.nodes["rig.frame"]
            plan = root.operands[4].original
            old = sim.model.actions["travel"].vector, sim.model.actions["turn"].vector, plan.precision_bits
            if mutate:
                sim.model.actions["travel"].vector = (99.0, 0.0, 0.0)
                sim.model.actions["turn"].vector = (0.0, 0.0, 99.0)
                object.__setattr__(plan, "precision_bits", 192)
            values = [bits(phase.sample(time)) for time in times]
            if mutate:
                sim.model.actions["travel"].vector, sim.model.actions["turn"].vector = old[:2]
                object.__setattr__(plan, "precision_bits", old[2])
            phase.finish()
            results.append(values)
        self.assertEqual(*results)

    def test_cancelled_or_narrowed_private_spin_cannot_publish_a_cursor(self):
        for cancel in (False, True):
            fixture = prepared()
            sim = fixture[0]
            times = (F(1, 8), F(1, 4))
            phase = begin(fixture, times)
            phase.sample(times[0])
            marker = RuntimeError("cancel captured prescribed root")
            charge, hit = sim.work.charge, []
            def checked(kind="checkpoint", amount=1):
                if kind == "recording_body_cursor_reuse" and not hit:
                    hit.append(True)
                    def reject():
                        if cancel:
                            raise marker
                        sim.work.max_operand_bits = 128
                    sim.work.external_check = reject
                return charge(kind, amount)
            with patch.object(sim.work, "charge", side_effect=checked):
                with self.assertRaises(RuntimeError if cancel else fast.RecordingRoundingAmbiguity) as caught:
                    phase.sample(times[1])
            self.assertTrue(hit)
            if cancel:
                self.assertIs(caught.exception, marker)
                self.assertIs(sim.work.callback_error, marker)
            self.assertFalse(cursors(sim.work))

    def test_unsupported_root_shapes_decline_before_future_clock_preflight(self):
        for kind in ("nonplanar", "bad_status", "missing_plan"):
            fixture = prepared()
            sim = fixture[0]
            if kind == "nonplanar":
                sim.model.actions["turn"].vector = (0.25, 0.0, 0.0)
            elif kind == "bad_status":
                sim.state.actions["turn"].status = "pending"
            else:
                sim.work._cache.pop(("reach_source_spin_phase", (0.0, 0.0, 0.25)), None)
            before = sim.work.counts.get("recording_captured_phase_clock", 0)
            self.assertIsNone(begin(fixture, (F(1, 8), F(1, 4))))
            self.assertEqual(before, sim.work.counts.get("recording_captured_phase_clock", 0))


if __name__ == "__main__":
    unittest.main()
