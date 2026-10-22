"""Certified interior samples retain exact phase fallback and output bytes."""
from fractions import Fraction as F
from functools import partial
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from ontokin import reach_export, reach_recording_fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def fake_plan(work):
    states = (object(), object(), object())
    observations = []

    def pose(time, state, path):
        value = (float(time) + 10 * states.index(state) if path == "a.frame"
                 else 100.0 + states.index(state))
        return NS(position=(value, 0.0, 0.0), orientation=(1.0, 0.0, 0.0, 0.0))

    def frames(time, state, paths, **kwargs):
        observations.append((time, state, kwargs["recording_context"]))
        return {path: pose(time, state, path) for path in paths}

    sim = NS(recording_frames=frames, recording_moving_frames=lambda state, paths: frozenset(("a.frame",)),
             work=work)
    plan = NS(boundaries=(F(0), F(1), F(2)), phase_states=states[:2], final_state=states[-1],
              phases=(NS(source={}, recording_angular_proof=None),
                      NS(source={}, recording_angular_proof=None)), simulator=sim)
    nodes = [NS(frame_path=path, translations=[], rotations_xyzw=[]) for path in ("a.frame", "b.frame")]
    exact = (F(0), F(1, 4), F(1, 2), F(3, 4), F(1), F(3, 2), F(2))
    return plan, nodes, exact, observations, pose


class ReachRecordingFastExportTests(unittest.TestCase):
    def test_production_bounded_endpoints_pass_independent_actual_bytes_without_cell_replay(self):
        for case, end in (("P01", F(3)), ("P02", F(1, 4)), ("P16", F(1, 4))):
            with self.subTest(case=case, end=end):
                compiler = compile_construction(source_case(case))
                with patch.object(reach_recording_fast, "certified_float32_cell",
                                  side_effect=AssertionError("Production supplies an explicit error enclosure")):
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=end, fps=1, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertGreater(compiler.reach_work.counts.get("recording_fast_endpoint_allowance", 0), 0)
                self.assertNotIn("recording_float_cell_domain", compiler.reach_work.counts)
                self.assertNotIn("recording_fast_phase_restart", compiler.reach_work.counts)
                self.assertLessEqual(compiler.budget.operations, 100000)

    def test_ambiguous_phase_discards_all_candidate_keys_and_restarts_with_fresh_context(self):
        work = ReachExecutionWork()
        plan, nodes, exact, observed, pose = fake_plan(work)
        attempts = []

        def candidate(sim, time, state, paths, **kwargs):
            attempts.append(time)
            if time == F(1, 2):
                raise reach_recording_fast.RecordingRoundingAmbiguity("a.frame", ("position",))
            value = pose(time, state, "a.frame")
            if time == F(1, 4):
                value = NS(position=(999.0, 0.0, 0.0), orientation=value.orientation)
            excess = NS(position_m=F(1, 1000000), rotation_rad=F(1, 1000000))
            return NS(frames={"a.frame": value}, excess_by_frame={"a.frame": excess})

        with patch.object(reach_recording_fast, "sample_certified_frames", candidate):
            excess = reach_export._sample_recording_nodes(plan, nodes, exact, work=work, require_same_cells=True)
        self.assertEqual(attempts, [F(1, 4), F(1, 2), F(3, 2)])
        self.assertNotIn(0, excess)
        self.assertEqual(excess[1]["a.frame"], (F(1, 1000000), F(1, 1000000)))
        for node in nodes:
            expected = [pose(time, plan.phase_states[0] if time < 1 else
                             plan.phase_states[1] if time < 2 else plan.final_state,
                             node.frame_path).position for time in exact]
            self.assertEqual(node.translations, expected)
            self.assertEqual(len(node.rotations_xyzw), len(exact))
        starts = [context for time, _, context in observed if time == 0]
        self.assertEqual(len(starts), 2)
        self.assertIsNot(starts[0], starts[1])
        self.assertEqual(work.counts["recording_fast_phase_restart"], 1)
        self.assertGreater(work.operations, len(exact))
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_callback_ambiguity_exception_propagates_without_phase_retry(self):
        work = ReachExecutionWork()
        plan, nodes, exact, _, _ = fake_plan(work)
        marker = reach_recording_fast.RecordingRoundingAmbiguity("cancel", ())

        def candidate(*args, **kwargs):
            with patch.object(work, "external_check", side_effect=marker):
                work.charge("candidate_callback")

        with patch.object(reach_recording_fast, "sample_certified_frames", candidate):
            with self.assertRaises(reach_recording_fast.RecordingRoundingAmbiguity) as caught:
                reach_export._sample_recording_nodes(plan, nodes, exact, work=work, require_same_cells=True)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertNotIn("recording_fast_phase_restart", work.counts)
        self.assertTrue(all(len(node.translations) == 1 for node in nodes))

    def test_ambiguous_hemisphere_lift_replays_the_complete_bake(self):
        work = ReachExecutionWork()
        plan, nodes, exact, observed, pose = fake_plan(work)
        candidate = NS(frames={"a.frame": NS(position=(0.25, 0.0, 0.0),
                                            orientation=(0.0, 1.0, 0.0, 0.0))},
                       excess_by_frame={"a.frame": NS(position_m=F(1, 1000000),
                                                      rotation_rad=F(1, 1000000))})
        with patch.object(reach_recording_fast, "sample_certified_frames", return_value=candidate) as sampled:
            excess = reach_export._sample_recording_nodes(plan, nodes, exact, work=work, require_same_cells=True)
        self.assertEqual(sampled.call_count, 1)
        self.assertEqual(excess, {})
        self.assertEqual(work.counts["recording_fast_lift_restart"], 1)
        self.assertNotIn("recording_fast_phase_restart", work.counts)
        self.assertEqual(sum(time == 0 for time, _, _ in observed), 2)
        for node in nodes:
            expected = [pose(time, plan.phase_states[0] if time < 1 else
                             plan.phase_states[1] if time < 2 else plan.final_state,
                             node.frame_path).position for time in exact]
            self.assertEqual(node.translations, expected)
            self.assertEqual(node.rotations_xyzw, [(0.0, 0.0, 0.0, 1.0)] * len(exact))

    def test_invalid_or_foreign_endpoint_allowance_cannot_enter_certificate(self):
        for frame, position, rotation in (("foreign.frame", F(0), F(0)),
                                          ("a.frame", False, F(0)),
                                          ("a.frame", F(0), F(-1))):
            with self.subTest(frame=frame, position=position, rotation=rotation):
                work = ReachExecutionWork()
                plan, nodes, exact, _, pose = fake_plan(work)
                result = NS(frames={"a.frame": pose(F(1, 4), plan.phase_states[0], "a.frame")},
                            excess_by_frame={frame: NS(position_m=position, rotation_rad=rotation)})
                with patch.object(reach_recording_fast, "sample_certified_frames", return_value=result):
                    with self.assertRaises(ValueError):
                        reach_export._sample_recording_nodes(plan, nodes, exact, work=work, require_same_cells=True)
                self.assertTrue(all(len(node.translations) == 1 for node in nodes))

    def test_actual_complete_geometry_clocks_and_pose_accessors_match_original_sampler(self):
        original = reach_export._sample_recording_nodes
        for case, end in (("P01", F(3)), ("L01", F(3, 4)), ("P16", F(1, 4))):
            with self.subTest(case=case, end=end):
                results = []
                for fast in (False, True):
                    compiler = compile_construction(source_case(case))
                    with patch.object(reach_export, "_sample_recording_nodes", partial(original, allow_fast=fast, require_same_cells=True)):
                        result = export_glb(compiler.model, options=ExportOptions(end=end, fps=1, helpers=False),
                            target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                    self.assertEqual(result.report["validation"]["status"], "passed")
                    self.assertLessEqual(compiler.budget.operations, 100000)
                    results.append(read_glb(result.data))
                self.assertEqual(results[0].binary, results[1].binary)
                for field in ("nodes", "meshes", "materials", "bufferViews", "accessors", "animations"):
                    self.assertEqual(results[0].document[field], results[1].document[field])


if __name__ == "__main__":
    unittest.main()
