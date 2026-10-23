"""Captured phase streams retain exact samples and one final live receipt."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
from types import MappingProxyType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.scene import ExportOptions, MAX_BAKED_POSES, MAX_KEYFRAMES
from reach_agent_support import source_case
from test_reach_recording_captured_graph import bits, body_cache, prepared, sample


def begin(fixture, times):
    sim, paths, phase, _, context = fixture
    return fast.begin_bounded_phase(sim, times, sim.state, paths, context=context,
        phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
        recording_angular_proof=phase["recording_angular_proof"])


def output_plan(fixture):
    sim, paths, phase = fixture[:3]
    plan = NS(boundaries=(F(0), F(2)), phase_states=(sim.state,), final_state=deepcopy(sim.state),
        phases=(NS(source=phase["frames"], recording_angular_proof=phase["recording_angular_proof"]),),
        simulator=sim)
    nodes = [NS(frame_path=path, translations=[], rotations_xyzw=[]) for path in paths]
    return plan, nodes


class ReachRecordingCapturedPhaseTests(unittest.TestCase):
    def test_small_and_shared_phase_streams_match_every_scalar_bit_and_enclosure(self):
        times = tuple(F(index, 8) for index in range(1, 13)) + (F(13, 8), F(7, 4))
        for count in (1, 6, 17):
            with self.subTest(count=count):
                outcomes = []
                for batched in (False, True):
                    fixture = prepared(count=count, distinct=True)
                    sim = fixture[0]
                    sample(fixture, F(1, 16))
                    state, before = deepcopy(sim.state), sim.work.operations
                    if batched:
                        phase = begin(fixture, times)
                        self.assertIsNotNone(phase)
                        original = body_cache(sim.work)
                        results = []
                        for time in times:
                            results.append(bits(phase.sample(time)))
                            self.assertTrue(all(key in original and original[key] is value
                                for key, value in body_cache(sim.work).items()))
                            self.assertLessEqual(len(phase.phase.publication.pending), count)
                            self.assertLessEqual(len(phase.phase.parents), count)
                        phase.finish()
                    else:
                        results = [bits(sample(fixture, time)) for time in times]
                    outcomes.append((results, sim.work.operations - before))
                    self.assertEqual(sim.state, state)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                    self.assertEqual(sim.work.max_operations, 100000)
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])

    def test_private_cursor_reseeds_at_the_original_127_step_limit(self):
        times = tuple(F(index, 100) for index in range(1, 131))
        results = []
        for batched in (False, True):
            fixture = prepared(count=1, distinct=True)
            sim = fixture[0]
            before = sim.work.counts.get("recording_float_body_direct_seed", 0)
            if batched:
                phase = begin(fixture, times)
                values = [bits(phase.sample(time)) for time in times]
                self.assertEqual(len(phase.phase.publication.pending), 1)
                self.assertFalse(body_cache(sim.work))
                phase.finish()
            else:
                values = [bits(sample(fixture, time)) for time in times]
            self.assertEqual(sim.work.counts["recording_float_body_direct_seed"] - before, 2)
            results.append(values)
        self.assertEqual(results[0], results[1])

    def test_each_source_parent_and_allowance_is_processed_once_per_phase(self):
        fixture = prepared(distinct=True)
        sim, paths = fixture[:2]
        times = (F(1, 8), F(1, 4), F(3, 8), F(1, 2))
        phase = begin(fixture, times)
        graph = phase.phase.graph
        with patch.object(capture, "_current_recording_angular_witness",
                          wraps=capture._current_recording_angular_witness) as receipts, \
                patch.object(fast, "recording_float_excess", wraps=fast.recording_float_excess) as allowances, \
                patch.object(sim.work, "lookup", wraps=sim.work.lookup) as lookups, \
                patch.object(phase.phase.ops, "recording_parent_origin",
                             wraps=phase.phase.ops.recording_parent_origin) as occurrences:
            for time in times:
                phase.sample(time)
            self.assertEqual(receipts.call_count, 0)
            self.assertFalse(body_cache(sim.work))
            phase.finish()
        records = [(call.args[2], call.args[3]) for call in receipts.call_args_list]
        self.assertEqual(len(records), len(graph.nodes))
        self.assertEqual(len(records), len(set(records)))
        self.assertEqual(allowances.call_count, len(paths))
        parent_reads = [call for call in lookups.call_args_list
                        if len(call.args[0]) > 1 and call.args[0][1] == "captured_constant_parent"]
        self.assertEqual(len(parent_reads), len(paths))
        self.assertEqual(occurrences.call_count, len(times) * len(paths))
        self.assertEqual(len(body_cache(sim.work)), 2)
        self.assertFalse(phase.phase.parents)
        self.assertFalse(phase.phase.publication.pending)

    def test_exact_clock_output_and_cache_bounds_decline_before_phase_work(self):
        fixture = prepared(count=3)
        invalid = ((F(1, 8),), (F(1, 8), F(1, 8)), (F(1, 4), F(1, 8)),
                   (F(0), F(1, 4)), (F(1, 4), F(2)), (F(1, 4), 1),
                   (F(1, 8),) * (MAX_KEYFRAMES + 1))
        for times in invalid:
            with self.subTest(times=times[:3]):
                self.assertIsNone(begin(fixture, times))
        sim, paths, phase, _, context = fixture
        with patch.object(sim.work, "max_cache_entries", 2):
            self.assertIsNone(begin(fixture, (F(1, 8), F(1, 4))))
        many_paths = tuple(f"object-{index}.frame" for index in range(256))
        self.assertGreater(MAX_KEYFRAMES * len(many_paths), MAX_BAKED_POSES)
        self.assertIsNone(fast.begin_bounded_phase(sim, (F(1, 8),) * MAX_KEYFRAMES,
            sim.state, many_paths, context=context, phase_bounds=phase["frames"],
            phase_interval=(F(0), F(2)), recording_angular_proof=phase["recording_angular_proof"]))
        self.assertEqual(sim.work.max_cache_entries, 256)
        self.assertEqual(sim.work.max_operations, 100000)
        self.assertFalse(body_cache(sim.work))

    def test_session_requires_complete_ordered_consumption_and_one_finish(self):
        fixture = prepared(count=1)
        times = (F(1, 8), F(1, 4))
        phase = begin(fixture, times)
        for method, arguments in ((phase.finish, ()), (phase.sample, (times[1],)),
                                   (phase.sample, (float(times[0]),))):
            with self.assertRaises(ReachAdmissionError):
                method(*arguments)
        phase.sample(times[0])
        phase.sample(times[1])
        phase.finish()
        with self.assertRaises(ReachAdmissionError):
            phase.finish()
        with self.assertRaises(ReachAdmissionError):
            phase.sample(times[1])

    def test_final_source_and_bound_receipts_cover_mutations_after_earlier_keys(self):
        for kind in ("root", "law", "proof", "bound", "state"):
            with self.subTest(kind=kind):
                fixture = prepared(count=3, distinct=True)
                sim, paths, source = fixture[:3]
                proof = source["recording_angular_proof"]
                records = dict(proof.frames)
                source["recording_angular_proof"] = replace(proof, frames=MappingProxyType(records))
                times = (F(1, 8), F(1, 4), F(3, 8))
                phase = begin(fixture, times)
                phase.sample(times[0])
                if kind == "root":
                    sim.state.positions["rig"] = (0.25, 0.0, 0.0)
                elif kind == "law":
                    elbow = paths[-1].removesuffix(".forearm.frame") + ".elbow"
                    action = sim.state.actions[sim.state.claims[(elbow, "coordinate")]]
                    action.initial = (0.25, 0.5)
                elif kind == "proof":
                    records[paths[-1]] = replace(records[paths[-1]], token=object())
                elif kind == "bound":
                    source["frames"][paths[-1]] = replace(source["frames"][paths[-1]],
                                                        max_position_l1_m=F(0))
                else:
                    sim.state = deepcopy(sim.state)
                for time in times[1:]:
                    phase.sample(time)
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(body_cache(sim.work))

    def test_temporary_source_and_bound_changes_never_enter_later_calculations(self):
        outcomes = []
        times = (F(1, 8), F(1, 4), F(3, 8))
        for mutate in (False, True):
            fixture = prepared(count=3, distinct=True)
            sim, paths, source = fixture[:3]
            phase = begin(fixture, times)
            position, bound = sim.state.positions["rig"], source["frames"][paths[-1]]
            values = [bits(phase.sample(times[0]))]
            if mutate:
                sim.state.positions["rig"] = (999.0, 0.0, 0.0)
                source["frames"][paths[-1]] = replace(bound, max_position_l1_m=F(999))
            values.extend(bits(phase.sample(time)) for time in times[1:])
            if mutate:
                sim.state.positions["rig"], source["frames"][paths[-1]] = position, bound
            phase.finish()
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_late_cancellation_and_narrow_domain_never_publish_pending_cursors(self):
        times = (F(1, 8), F(1, 4), F(3, 8))
        for checkpoint in ("recording_body_cursor_stage", "recording_body_shared_orientation",
                           "recording_captured_bound_guard", "cache_batch_domain", "cache_insert"):
            for cancel in (False, True):
                with self.subTest(checkpoint=checkpoint, cancel=cancel):
                    fixture = prepared(count=3, distinct=True)
                    sim = fixture[0]
                    sample(fixture, F(1, 16))
                    phase = begin(fixture, times)
                    phase.sample(times[0])
                    original, hit, finishing = body_cache(sim.work), [], []
                    marker = fast._UnsupportedPlanar("original late phase cancellation")
                    charge = sim.work.charge
                    def charged(kind="checkpoint", amount=1):
                        if kind == checkpoint and (checkpoint != "cache_insert" or finishing) and not hit:
                            hit.append(True)
                            def reject():
                                sim.work.max_operand_bits = 128
                                if cancel:
                                    raise marker
                            sim.work.external_check = reject
                        return charge(kind, amount)
                    with patch.object(sim.work, "charge", side_effect=charged):
                        expected = fast._UnsupportedPlanar if cancel else fast.RecordingRoundingAmbiguity
                        with self.assertRaises(expected) as caught:
                            for time in times[1:]:
                                phase.sample(time)
                            finishing.append(True)
                            phase.finish()
                    self.assertTrue(hit)
                    if cancel:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(sim.work.callback_error, marker)
                    self.assertTrue(all(key in original and original[key] is value
                        for key, value in body_cache(sim.work).items()))

    def test_original_resource_error_survives_a_transient_cap_restore(self):
        fixture = prepared(count=1)
        sim = fixture[0]
        times = (F(1, 8), F(1, 4))
        phase = begin(fixture, times)
        phase.sample(times[0])
        marker = ReachAdmissionError("reach_resource", "first restricted phase refusal")
        charge, changed = sim.work.charge, []
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_body_cursor_reuse" and not changed:
                changed.append(True)
                def reject():
                    sim.work.max_operand_bits = 128
                    try:
                        raise marker
                    finally:
                        sim.work.max_operand_bits = 32768
                sim.work.external_check = reject
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=charged):
            with self.assertRaises(ReachAdmissionError) as caught:
                phase.sample(times[1])
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertEqual(sim.work.max_operand_bits, 32768)
        self.assertFalse(body_cache(sim.work))

    def test_restored_cap_or_changed_capacity_preserves_previous_complete_cursors(self):
        for change in ("restore_operand", "capacity"):
            with self.subTest(change=change):
                fixture = prepared(count=3, distinct=True)
                sim = fixture[0]
                sample(fixture, F(1, 16))
                times = (F(1, 8), F(1, 4), F(3, 8))
                phase = begin(fixture, times)
                for time in times:
                    phase.sample(time)
                original, events = body_cache(sim.work), []
                charge = sim.work.charge
                def charged(kind="checkpoint", amount=1):
                    if kind == "cache_insert" and not events:
                        events.append(kind)
                        if change == "restore_operand":
                            sim.work.max_operand_bits = 128
                        else:
                            sim.work.max_cache_entries = 1
                    elif kind == "cache_operand_scope_reset" and change == "restore_operand":
                        events.append(kind)
                        sim.work.max_operand_bits = 32768
                    return charge(kind, amount)
                with patch.object(sim.work, "charge", side_effect=charged):
                    phase.finish()
                self.assertTrue(events)
                self.assertEqual(body_cache(sim.work), original)

    def test_reentrant_complete_phase_preserves_its_newer_cursor_group(self):
        fixture = prepared(count=3, distinct=True)
        sim = fixture[0]
        sample(fixture, F(1, 16))
        times = (F(1, 8), F(1, 4), F(3, 8))
        outer = begin(fixture, times)
        outer.sample(times[0])
        charge, inside, retained = sim.work.charge, [], []
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_body_shared_orientation" and not inside:
                inside.append(True)
                inner_times = (F(5, 8), F(3, 4))
                inner = begin(fixture, inner_times)
                for time in inner_times:
                    inner.sample(time)
                inner.finish()
                retained.append(body_cache(sim.work))
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=charged):
            for time in times[1:]:
                outer.sample(time)
            outer.finish()
        self.assertEqual(len(retained), 1)
        self.assertEqual(body_cache(sim.work), retained[0])
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_exporter_retains_all_pose_charges_and_original_boundary_samples(self):
        exact = (F(0), F(1, 8), F(1, 4), F(1, 2), F(2))
        results = []
        for batched in (False, True):
            fixture = prepared(count=3, distinct=True)
            sim = fixture[0]
            plan, nodes = output_plan(fixture)
            mode = nullcontext() if batched else patch.object(fast, "begin_bounded_phase", return_value=None)
            with mode, patch.object(sim, "recording_frames", wraps=sim.recording_frames) as ordinary:
                allowance = reach_export._sample_recording_nodes(plan, nodes, exact, work=sim.work)
            self.assertEqual([call.args[0] for call in ordinary.call_args_list], [F(0), F(2)])
            self.assertEqual(sim.work.counts["recording_sample"], len(exact))
            self.assertEqual(sim.work.counts["recording_pose"], len(exact) * len(nodes))
            self.assertEqual(sim.work.counts["recording_fast_endpoint_allowance"],
                             len(nodes) * (1 if batched else 3))
            self.assertNotIn("recording_fast_phase_restart", sim.work.counts)
            results.append(([(node.translations, node.rotations_xyzw) for node in nodes], allowance))
        self.assertEqual(results[0], results[1])

    def test_final_exporter_output_callback_cannot_escape_the_source_receipt(self):
        fixture = prepared(count=3, distinct=True)
        sim = fixture[0]
        plan, nodes = output_plan(fixture)
        exact = (F(0), F(1, 8), F(1, 4), F(1, 2), F(2))
        charge, poses = sim.work.charge, []
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_pose":
                poses.append(True)
                if len(poses) == (len(exact) - 1) * len(nodes):
                    sim.state.positions["rig"] = (0.5, 0.0, 0.0)
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=charged):
            with self.assertRaises(ReachAdmissionError) as caught:
                reach_export._sample_recording_nodes(plan, nodes, exact, work=sim.work)
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertFalse(body_cache(sim.work))

    def test_unsupported_mixed_graph_and_strict_diagnostic_keep_scalar_paths(self):
        fixture = prepared(count=3)
        sim, paths, source, _, context = fixture
        mixed = (paths[0].replace(".forearm.frame", ".upper.frame"), *paths[1:])
        before = sim.work.counts.get("recording_captured_phase_clock", 0)
        self.assertIsNone(fast.begin_bounded_phase(sim, (F(1, 8), F(1, 4)), sim.state, mixed,
            context=context, phase_bounds=source["frames"], phase_interval=(F(0), F(2)),
            recording_angular_proof=source["recording_angular_proof"]))
        self.assertEqual(sim.work.counts.get("recording_captured_phase_clock", 0), before)
        fixture = prepared(count=1)
        sim = fixture[0]
        plan, nodes = output_plan(fixture)
        with patch.object(fast, "begin_bounded_phase", side_effect=AssertionError("strict path has no phase batch")):
            reach_export._sample_recording_nodes(plan, nodes, (F(0), F(1, 8), F(1, 4), F(2)),
                                                 work=sim.work, require_same_cells=True)

    def test_complete_delivered_pose_bytes_match_current_scalar_production(self):
        for case, end in (("P01", F(3)), ("P16", F(1, 4))):
            with self.subTest(case=case):
                outcomes = []
                for batched in (False, True):
                    compiler = compile_construction(source_case(case))
                    mode = nullcontext() if batched else patch.object(fast, "begin_bounded_phase", return_value=None)
                    with mode:
                        result = export_glb(compiler.model,
                            options=ExportOptions(end=end, fps=1, helpers=False),
                            target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                    self.assertEqual(result.report["validation"]["status"], "passed")
                    self.assertLessEqual(compiler.budget.operations, 100000)
                    outcomes.append(read_glb(result.data))
                self.assertEqual(outcomes[0].binary, outcomes[1].binary)
                for field in ("nodes", "meshes", "materials", "bufferViews", "accessors", "animations"):
                    self.assertEqual(outcomes[0].document[field], outcomes[1].document[field])


if __name__ == "__main__":
    unittest.main()
