"""Whole captured planar chains preserve moving origins and source authority."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import phase_bounds
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_graph import bits, body_cache, prepared
from test_reach_recording_sampler import simulator


def chain(case="P09", start=F(0), end=F(2)):
    sim = simulator(case)
    sim.advance(start, "after")
    all_paths = tuple(path + ".frame" for path in sim.model.objects)
    moving = sim.recording_moving_frames(sim.state, all_paths)
    paths = tuple(path for path in all_paths if path in moving)
    proof = phase_bounds(sim, start, end, sim.state, selected_frames=paths, recording_proof=True)
    return sim, paths, proof, moving, object()


def arguments(fixture):
    _, _, proof, moving, context = fixture
    angular = proof["recording_angular_proof"]
    return dict(context=context, moving_frames=moving, phase_bounds=proof["frames"],
                phase_interval=(angular.start, angular.end), recording_angular_proof=angular)


def begin(fixture, times):
    sim, paths = fixture[:2]
    values = arguments(fixture)
    values.pop("moving_frames")
    return fast.begin_bounded_phase(sim, times, sim.state, paths, **values)


class ReachRecordingCapturedChainTests(unittest.TestCase):
    def test_actual_p09_and_both_l03_phases_match_all_native_bits_and_stored_cells(self):
        for case, start, end in (("P09", F(0), F(2)), ("L03", F(0), F(2)), ("L03", F(2), F(3))):
            with self.subTest(case=case, start=start):
                times = tuple(start + (end - start) * F(index, 16) for index in range(1, 16))
                outcomes = []
                for batched in (False, True):
                    fixture = chain(case, start, end)
                    sim, paths = fixture[:2]
                    original, before = deepcopy(sim.state), sim.work.operations
                    phase = begin(fixture, times) if batched else None
                    if batched:
                        self.assertIsNotNone(phase)
                        self.assertFalse(phase.phase.graph.static_carriers)
                    values, cells, positions = [], [], {path: set() for path in paths}
                    for time in times:
                        result = (phase.sample(time) if batched else
                            fast.sample_bounded_frames(sim, time, sim.state, paths, **arguments(fixture)))
                        values.append(bits(result))
                        cells.append(tuple((path, struct.pack("<7f", *pose.position, *pose.orientation))
                                           for path, pose in result.frames.items()))
                        for path, pose in result.frames.items():
                            positions[path].add(pose.position)
                    if batched:
                        self.assertFalse(body_cache(sim.work))
                        self.assertLessEqual(len(phase.phase.graph.nodes), 256)
                        self.assertLessEqual(len(phase.phase.constants), 256)
                        self.assertLessEqual(len(phase.phase.publication.pending), 256)
                        phase.finish()
                    self.assertTrue(any(len(values) > 1 for values in positions.values()))
                    self.assertEqual(sim.state, original)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                    self.assertEqual(sim.work.max_operations, 100000)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    outcomes.append((values, cells, sim.work.operations - before))
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_late_key_source_claim_site_and_topology_changes_reject_the_complete_group(self):
        times = (F(1, 8), F(1, 4), F(3, 8))
        for kind in ("law", "claim", "site", "topology"):
            with self.subTest(kind=kind):
                fixture = chain()
                sim = fixture[0]
                phase = begin(fixture, times)
                phase.sample(times[0])
                phase.sample(times[1])
                shoulder, elbow = sim.model.joints["rig.arm.shoulder"], sim.model.joints["rig.arm.elbow"]
                charge, hit = sim.work.charge, []
                def charged(name="checkpoint", amount=1):
                    if name == "recording_float_mul" and not hit:
                        hit.append(True)
                        if kind == "law":
                            action = sim.state.actions[sim.state.claims[(shoulder.path, "coordinate")]]
                            action.initial = (0.25, action.initial[1])
                        elif kind == "claim":
                            del sim.state.claims[(shoulder.path, "coordinate")]
                        elif kind == "site":
                            site = sim.model.sites[elbow.parent]
                            site.pose = replace(site.pose, position=(5.0, 0.0, 0.0))
                        else:
                            elbow.parent = shoulder.parent
                    return charge(name, amount)
                with patch.object(sim.work, "charge", side_effect=charged):
                    phase.sample(times[-1])
                    with self.assertRaises(ReachAdmissionError) as caught:
                        phase.finish()
                self.assertTrue(hit)
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(body_cache(sim.work))

    def test_transient_parent_and_site_mutations_cannot_change_child_origins(self):
        times = (F(1, 8), F(1, 4), F(3, 8))
        results = []
        for mutate in (False, True):
            fixture = chain()
            sim = fixture[0]
            phase = begin(fixture, times)
            values = [bits(phase.sample(times[0]))]
            site = sim.model.sites[sim.model.joints["rig.arm.elbow"].parent]
            pose, position = site.pose, sim.state.positions["rig"]
            if mutate:
                site.pose = replace(pose, position=(7.0, 0.0, 0.0))
                sim.state.positions["rig"] = (12.0, 0.0, 0.0)
            values.extend(bits(phase.sample(time)) for time in times[1:])
            site.pose, sim.state.positions["rig"] = pose, position
            phase.finish()
            results.append(values)
        self.assertEqual(results[0], results[1])

    def test_chain_reentrancy_keeps_every_inner_complete_body_cursor(self):
        fixture = chain()
        sim = fixture[0]
        times = (F(1, 8), F(1, 4), F(3, 8))
        outer = begin(fixture, times)
        outer.sample(times[0])
        charge, entered, retained = sim.work.charge, [], []
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_float_mul" and not entered:
                entered.append(True)
                inner_times = (F(3, 4), F(7, 8))
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
        self.assertEqual(len(retained[0]), 2)
        self.assertEqual(body_cache(sim.work), retained[0])

    def test_static_p23_working_parents_keep_the_existing_sampler(self):
        fixture = prepared()
        phase = begin(fixture, (F(1, 8), F(1, 4)))
        self.assertTrue(phase.phase.graph.static_carriers)
        with patch.object(capture, "_sample_chain_graph", side_effect=AssertionError("P23 retains static parents")):
            phase.sample(F(1, 8))
            phase.sample(F(1, 4))
            phase.finish()

    def test_graph_size_bound_and_unsupported_offsets_do_not_publish_cursors(self):
        fixture = chain()
        sim, paths, proof = fixture[:3]
        ops = fast.Binary64RecordingOps(sim.pose_ops, body_cursors=True)
        self.assertIsNone(capture._capture(sim, sim.state, paths, proof["recording_angular_proof"],
                                           ops, varying_parents=True, maximum_nodes=1))
        child = sim.model.sites[sim.model.joints["rig.arm.elbow"].child]
        child.pose = replace(child.pose, position=(0.25, 0.0, 0.0))
        proof = phase_bounds(sim, F(0), F(2), sim.state, selected_frames=paths, recording_proof=True)
        modified = (sim, paths, proof, fixture[3], fixture[4])
        before = sim.work.counts.get("recording_captured_phase_clock", 0)
        self.assertIsNone(begin(modified, (F(1, 8), F(1, 4))))
        self.assertEqual(sim.work.counts.get("recording_captured_phase_clock", 0), before)
        self.assertFalse(body_cache(sim.work))

    def test_actual_p09_and_l03_prefix_glbs_preserve_every_delivered_byte(self):
        for case in ("P09", "L03"):
            with self.subTest(case=case):
                outputs = []
                for batched in (False, True):
                    compiler = compile_construction(source_case(case))
                    mode = nullcontext() if batched else patch.object(fast, "begin_bounded_phase", return_value=None)
                    with mode:
                        result = export_glb(compiler.model,
                            options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                            target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                    self.assertEqual(result.report["validation"]["status"], "passed")
                    self.assertLessEqual(compiler.budget.operations, 100000)
                    if batched:
                        self.assertGreater(compiler.reach_work.counts.get("recording_captured_bound_guard", 0), 0)
                    outputs.append(result.data)
                self.assertEqual(outputs[0], outputs[1])
                self.assertEqual(read_glb(outputs[0]).binary, read_glb(outputs[1]).binary)


if __name__ == "__main__":
    unittest.main()
