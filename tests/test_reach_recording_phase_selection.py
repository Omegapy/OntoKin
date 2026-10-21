"""Carrier-only phase proofs preserve complete source and delivered meaning."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.program_runtime import prepare_delivery
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions, _nodes
from reach_agent_support import source_case


def all_frame_bounds(simulator, start, end):
    return simulator.phase_bounds(start, end)["frames"]


class ReachRecordingPhaseSelectionTests(unittest.TestCase):
    def test_selected_bounds_cover_real_nodes_and_equal_complete_phase_values(self):
        # Moving roots and released joint parents remain selected, and every
        # object's proof prepares the same bounded source spin reduction.
        for case, start, end in (("P01", F(0), F(2)), ("P05", F(0), F(2)),
                                  ("P16", F(2), F(3))):
            with self.subTest(case=case):
                compiled = compile_construction(source_case(case))
                sim = ReachSimulator(compiled.model, work=compiled.reach_work)
                sim.advance(start, "after")
                selected = reach_export.recording_phase_bounds(sim, start, end)
                complete = all_frame_bounds(sim, start, end)
                self.assertEqual(selected, {path: complete[path] for path in selected})
                self.assertTrue({path + ".frame" for path in compiled.model.objects} <= selected.keys())
                self.assertTrue({joint.parent + ".frame" for joint in compiled.model.joints.values()}
                                <= selected.keys())
                for helpers in (False, True):
                    nodes = _nodes(compiled.model, ExportOptions(helpers=helpers),
                                   check=sim.work.tick, work=sim.work)
                    self.assertTrue({node.frame_path for node in nodes} <= selected.keys())
                self.assertLess(len(selected), len(complete))

    def test_selected_planning_preserves_entire_glb_including_helpers(self):
        for end, helpers in ((F(3), False), (F(1, 8), True)):
            with self.subTest(end=end, helpers=helpers):
                outputs = []
                for selected in (False, True):
                    compiled = compile_construction(source_case("P01"))
                    options = ExportOptions(end=end, fps=1, helpers=helpers)
                    if selected:
                        result = export_glb(compiled.model, options=options,
                            target_contract="ontokin.glb/0.6", work=compiled.reach_work)
                    else:
                        with patch.object(reach_export, "recording_phase_bounds", all_frame_bounds):
                            result = export_glb(compiled.model, options=options,
                                target_contract="ontokin.glb/0.6", work=compiled.reach_work)
                    self.assertEqual(result.report["validation"]["status"], "passed")
                    self.assertLessEqual(compiled.budget.operations, 100000)
                    outputs.append(result.data)
                self.assertEqual(outputs[0], outputs[1])

    def test_agent_capture_retains_identical_boundaries_and_run_state(self):
        results, plans = [], []
        for selected in (False, True):
            if selected:
                compiler, result = prepare_delivery(source_case("P01"), until=F(1, 4))
            else:
                with patch.object(reach_export, "recording_phase_bounds", all_frame_bounds):
                    compiler, result = prepare_delivery(source_case("P01"), until=F(1, 4))
            self.assertEqual(result["outcome"], "valid")
            results.append(result)
            plans.append(compiler.reach_delivery_plan)
        self.assertEqual(results[0], results[1])
        self.assertEqual(plans[0].boundaries, plans[1].boundaries)
        self.assertEqual(plans[0].boundary_records, plans[1].boundary_records)
        for complete, selected in zip(plans[0].phases, plans[1].phases):
            self.assertEqual((complete.start, complete.end), (selected.start, selected.end))
            self.assertEqual(selected.source, {path: complete.source[path] for path in selected.source})
            self.assertEqual(selected.carriers, {path: complete.carriers[path] for path in selected.carriers})

    def test_unused_site_finiteness_remains_part_of_source_boundary_validation(self):
        compiler = compile_construction(source_case("P01"))
        original = ReachSimulator._kinematics
        marker = RuntimeError("unselected source site is invalid")

        class InvalidFrame:
            @property
            def position(self):
                raise marker

        def invalid_site(simulator, time, state):
            objects, frames = original(simulator, time, state)
            return objects, {**frames, "unselected.site.frame": InvalidFrame()}

        with patch.object(ReachSimulator, "_kinematics", invalid_site):
            with self.assertRaises(RuntimeError) as caught:
                reach_export.reach_prefix_plan(compiler.model, F(1, 4), work=compiler.reach_work)
        self.assertIs(caught.exception, marker)

    def test_selection_is_interruptible_and_keeps_numeric_error_context(self):
        compiler = compile_construction(source_case("P01"))
        sim = ReachSimulator(compiler.model, work=compiler.reach_work)
        sim.advance(F(0), "after")
        marker = RuntimeError("cancel recording carrier enumeration")
        with patch.object(sim.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reach_export.recording_phase_bounds(sim, F(0), F(2))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)

        numeric = ReachAdmissionError("reach_numeric", "bounded phase failure")
        translated = RuntimeError("original simulator error translation")
        with patch("ontokin.reach_phase.phase_bounds", side_effect=numeric), \
                patch.object(sim, "_numeric_error", side_effect=translated) as convert:
            with self.assertRaises(RuntimeError) as caught:
                reach_export.recording_phase_bounds(sim, F(0), F(2))
        self.assertIs(caught.exception, translated)
        convert.assert_called_once_with(numeric, time=F(0))


if __name__ == "__main__":
    unittest.main()
