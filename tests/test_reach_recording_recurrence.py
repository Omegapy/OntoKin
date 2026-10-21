"""Recording cursors remain phase scoped and carry every endpoint allowance."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import PhaseBound
from ontokin.reach_pose import AXIS_ERROR, PRODUCT_ERROR, MAX_RECORDING_ROTATION_STEPS
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions, MAX_KEYFRAMES
from reach_agent_support import source_case
from test_reach_recording_sampler import simulator


class ReachRecordingRecurrenceTests(unittest.TestCase):
    def test_hinge_and_prescribed_spin_hooks_leave_full_source_graph_and_bounds_direct(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        bounds = sim.phase_bounds(F(0), F(2))
        _, source_frames = sim._kinematics(F(1, 8), sim.state)
        source_cache = sim._pose_cache
        paths = tuple(path + ".frame" for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, paths)
        context = object()
        with patch.object(sim.pose_ops, "recording_axis_rotation", wraps=sim.pose_ops.recording_axis_rotation) as hinge, \
                patch.object(sim.pose_ops, "recording_advance_orientation", wraps=sim.pose_ops.recording_advance_orientation) as spin:
            for time in (F(1, 4), F(1, 2)):
                sim.recording_frames(time, sim.state, paths, moving_frames=moving, recording_context=context)
        self.assertTrue(hinge.call_args_list)
        self.assertTrue(spin.call_args_list)
        self.assertTrue(all(call.kwargs["path"].startswith("hinge:") for call in hinge.call_args_list))
        self.assertTrue(any(call.kwargs["path"] == "prescribed:rig" for call in spin.call_args_list))
        for call in (*hinge.call_args_list, *spin.call_args_list):
            self.assertIs(call.kwargs["context"], context)
            self.assertEqual(call.kwargs["max_steps"], MAX_KEYFRAMES)
        self.assertEqual(MAX_RECORDING_ROTATION_STEPS, MAX_KEYFRAMES)
        self.assertIs(sim._pose_cache, source_cache)
        self.assertIs(sim._kinematics(F(1, 8), sim.state)[1], source_frames)
        self.assertEqual(sim.phase_bounds(F(0), F(2)), bounds)
        # No context means the direct algorithm, even after all cursors warm.
        with patch.object(sim.pose_ops, "recording_axis_rotation", side_effect=AssertionError("recording-only hinge")), \
                patch.object(sim.pose_ops, "recording_advance_orientation", side_effect=AssertionError("recording-only spin")):
            sim.recording_frames(F(3, 4), sim.state, paths)
            sim._kinematics(F(3, 4), sim.state)
        with self.assertRaises(ValueError):
            sim._resolve_kinematics(F(3, 4), sim.state, recording_context=context)

    def test_dynamic_spin_uses_its_own_cursor_without_changing_release_anchor(self):
        sim = simulator("P16")
        sim.advance(F(2), "after")
        sim.phase_bounds(F(2), F(3))
        anchor = sim.state.dynamic["payload"].state
        original_anchor = (anchor.position, anchor.orientation, anchor.velocity, anchor.omega)
        source_cache = sim._pose_cache
        context = object()
        with patch.object(sim.pose_ops, "recording_advance_orientation", wraps=sim.pose_ops.recording_advance_orientation) as spin:
            for time in (F(17, 8), F(9, 4)):
                sim.recording_frames(time, sim.state, ("payload.frame",),
                    moving_frames=frozenset(("payload.frame",)), recording_context=context)
        self.assertEqual(len(spin.call_args_list), 2)
        self.assertTrue(all(call.kwargs["path"] == "dynamic:payload" for call in spin.call_args_list))
        self.assertTrue(all(call.kwargs["context"] is context for call in spin.call_args_list))
        self.assertIs(sim.state.dynamic["payload"].state, anchor)
        self.assertEqual((anchor.position, anchor.orientation, anchor.velocity, anchor.omega), original_anchor)
        self.assertIs(sim._pose_cache, source_cache)
        self.assertGreater(sim.work.counts.get("recording_rotation_step", 0), 0)
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_new_context_cannot_reuse_a_prior_pass_recording_node_slot(self):
        sim = simulator("P01")
        sim.advance(F(0), "after")
        sim.phase_bounds(F(0), F(2))
        paths = ("rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        context = object()
        for time in (F(1, 4), F(1, 2), F(3, 4)):
            sim._resolve_kinematics(time, sim.state, selected_frames=paths,
                pose_only=True, recording_only=True, recording_context=context)
        _, restarted = sim._resolve_kinematics(F(3, 4), sim.state, selected_frames=paths,
            pose_only=True, recording_only=True, recording_context=object())
        _, direct = sim._resolve_kinematics(F(3, 4), sim.state, selected_frames=paths,
            pose_only=True, recording_only=True)
        for path in paths:
            # A fresh cursor seeds the direct actual rotation. Recording-only
            # identity elision removes unexecuted product allowances, so its
            # error can be smaller than the old direct composition's error.
            self.assertEqual((restarted[path].exact_position, restarted[path].rotation.components,
                              restarted[path].rotation.frozen_projection),
                             (direct[path].exact_position, direct[path].rotation.components,
                              direct[path].rotation.frozen_projection))
            self.assertLessEqual(restarted[path].rotation.error_rad,direct[path].rotation.error_rad)
        self.assertLessEqual(len(sim.work._cache), sim.work.max_cache_entries)

    def test_actual_recording_has_fresh_context_per_claim_phase_and_per_bake(self):
        original = ReachSimulator.recording_frames
        all_contexts, outputs = [], []
        for _ in range(2):
            observed = []
            def sample(sim, time, state, paths, *, moving_frames=None, recording_context=None):
                observed.append((state, recording_context, time))
                return original(sim, time, state, paths, moving_frames=moving_frames,
                                recording_context=recording_context)
            compiler = compile_construction(source_case("L02"))
            with patch.object(ReachSimulator, "recording_frames", sample):
                result = export_glb(compiler.model, options=ExportOptions(end=F(3, 4), fps=1, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(compiler.budget.operations, 100000)
            self.assertGreater(compiler.reach_work.counts.get("recording_rotation_step", 0), 0)
            per_state = {}
            for state, context, time in observed:
                self.assertIs(type(context), object)
                prior = per_state.setdefault(id(state), context)
                self.assertIs(prior, context)
            # Before and after the 0.5-second owner switch, then final seed.
            self.assertEqual(len(per_state), 3)
            self.assertEqual(len(set(per_state.values())), len(per_state))
            self.assertIsNot(observed[-1][1], observed[-2][1])
            all_contexts.append(set(per_state.values()))
            outputs.append(result.data)
        self.assertFalse(all_contexts[0] & all_contexts[1])
        self.assertEqual(outputs[0], outputs[1])

    def test_endpoint_excess_covers_path_offsets_and_preserves_source_bounds(self):
        work = ReachExecutionWork(max_cache_entries=3)
        bound = PhaseBound(trig_count=3, path_offset_l1_m=F(7, 2),
            max_position_l1_m=F(1 << 80), position_error_m=F(1, 1000), rotation_error_rad=F(1, 2000),
            carrier_speed_upper_m_per_s=F(2), angular_speed_upper_rad_per_s=F(3))
        expected_rotation = (MAX_KEYFRAMES - 1) * 3 * (AXIS_ERROR + 2 * PRODUCT_ERROR)
        position, rotation = reach_export._recording_endpoint_excess(bound, work=work)
        self.assertEqual(rotation, expected_rotation)
        self.assertEqual(position, F(7, 2) * expected_rotation)
        self.assertEqual(reach_export._recording_endpoint_excess(
            replace(bound, max_position_l1_m=F(0)), work=work), (position, rotation))
        self.assertEqual(reach_export._recording_endpoint_excess(
            replace(bound, path_offset_l1_m=F(14)), work=work), (4 * position, rotation))
        self.assertEqual(reach_export._recording_endpoint_excess(
            replace(bound, trig_count=0), work=work), (F(0), F(0)))
        self.assertEqual((bound.position_error_m, bound.rotation_error_rad,
            bound.carrier_speed_upper_m_per_s, bound.angular_speed_upper_rad_per_s),
            (F(1, 1000), F(1, 2000), F(2), F(3)))
        self.assertLessEqual(len(work._cache), 3)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_complete_certificates_charge_excess_at_endpoints_without_changing_source_or_rates(self):
        original = reach_export._recording_endpoint_excess
        position_increment, rotation_increment = F(1, 100000), F(1, 10000000)
        def enlarged(bound, *, work):
            position, rotation = original(bound, work=work)
            return position + position_increment, rotation + rotation_increment
        records = []
        for extra in (False, True):
            compiler = compile_construction(source_case("P01"))
            with patch.object(reach_export, "_recording_endpoint_excess", enlarged if extra else original):
                result = export_glb(compiler.model, options=ExportOptions(end=F(1, 16), fps=1, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            decoded = read_glb(result.data)
            records.append(decoded.document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"])
        self.assertEqual(len(records[0]), len(records[1]))
        unchanged = ("source_numeric_position_bound_m", "source_numeric_rotation_bound_rad",
            "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
            "enclosing_carrier_speed_bound_m_per_s", "enclosing_carrier_acceleration_bound_m_per_s2",
            "enclosing_angular_speed_bound_rad_per_s")
        for direct, enlarged in zip(*records):
            self.assertEqual({name: direct[name] for name in unchanged},
                             {name: enlarged[name] for name in unchanged})
            self.assertGreater(F(enlarged["max_endpoint_position_error_m"]) - F(direct["max_endpoint_position_error_m"]),
                               position_increment / 2)
            self.assertGreater(F(enlarged["max_endpoint_unit_quaternion_error"]) - F(direct["max_endpoint_unit_quaternion_error"]),
                               rotation_increment / 2)
            self.assertGreater(enlarged["total_position_bound_m"], direct["total_position_bound_m"])
            self.assertGreater(enlarged["total_rotation_bound_rad"], direct["total_rotation_bound_rad"])

    def test_endpoint_excess_warm_guards_and_original_cancellation_remain(self):
        work = ReachExecutionWork()
        bound = PhaseBound(trig_count=1, path_offset_l1_m=F(2))
        reach_export._recording_endpoint_excess(bound, work=work)
        for invalid in (replace(bound, trig_count=True), replace(bound, trig_count=-1),
                        replace(bound, path_offset_l1_m=True), replace(bound, path_offset_l1_m=F(-1))):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                reach_export._recording_endpoint_excess(invalid, work=work)
        work.max_operand_bits = 64
        with self.assertRaises(ReachAdmissionError) as caught:
            reach_export._recording_endpoint_excess(bound, work=work)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        before = tuple(work._cache.items())
        marker = RuntimeError("cancel recording endpoint allowance")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reach_export._recording_endpoint_excess(bound, work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(tuple(work._cache.items()), before)


if __name__ == "__main__":
    unittest.main()
