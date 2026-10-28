"""Mixed phases retain complete ordinary paths and captured planar source laws."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import struct
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_chain import arguments, begin, chain
from test_reach_recording_captured_graph import bits, body_cache


TIMES = (F(1, 8), F(1, 4), F(3, 8))


def fixture():
    return chain("P11")


def ordinary_paths(paths):
    return tuple(path for path in paths if path.startswith("rig.head"))


class ReachRecordingCapturedMixedTests(unittest.TestCase):
    def setUp(self):
        # P11 can now use the optional complete Cartesian capture. Keep this
        # earlier cohort exercising its ordinary/Y + captured/Z fallback,
        # including all source-receipt and observer guarantees of that path.
        original = fast.Binary64RecordingOps.__init__
        def planar_only(instance, *args, **kwargs):
            kwargs["cartesian_axes"] = False
            original(instance, *args, **kwargs)
        context = patch.object(fast.Binary64RecordingOps, "__init__", planar_only)
        context.start()
        self.addCleanup(context.stop)

    def test_actual_p11_cold_and_warm_bits_cells_bounds_order_and_operations(self):
        times = tuple(F(index, 16) for index in range(1, 32))
        outcomes = []
        for captured in (False, True):
            prepared = fixture()
            sim, paths = prepared[:2]
            before, original = sim.work.operations, deepcopy(sim.state)
            phase = begin(prepared, times) if captured else None
            if captured:
                self.assertIsInstance(phase.phase, capture._MixedCapturedPhase)
                self.assertEqual(phase.phase.ordinary, ordinary_paths(paths))
                self.assertEqual(phase.phase.graph.selected,
                                 tuple(path for path in paths if path not in ordinary_paths(paths)))
            values, cells = [], []
            for time in times:
                result = (phase.sample(time) if captured else
                    fast.sample_bounded_frames(sim, time, sim.state, paths, **arguments(prepared)))
                values.append(bits(result))
                cells.append(tuple((path, struct.pack("<7f", *pose.position, *pose.orientation))
                                   for path, pose in result.frames.items()))
                for path in ordinary_paths(paths):
                    self.assertEqual(result.excess_by_frame[path], fast._ZERO_EXCESS)
                self.assertEqual(set(result.frames), set(paths))
            if captured:
                self.assertFalse(body_cache(sim.work))
                self.assertLessEqual(len(phase.phase.graph.nodes), 256)
                self.assertLessEqual(len(phase.phase.publication.pending), 256)
                self.assertFalse(any(isinstance(value, dict) and value
                                     and all(hasattr(pose, "position") for pose in value.values())
                                     for value in vars(phase.phase).values()))
                phase.finish()
            self.assertEqual(sim.state, original)
            self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
            self.assertEqual(sim.work.max_operations, 100000)
            self.assertEqual(sim.work.max_operand_bits, 32768)
            self.assertLessEqual(len(sim.work._cache), 256)
            outcomes.append((values, cells, sim.work.operations - before))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_subclass_and_observer_keep_original_ordinary_dispatch_at_every_key(self):
        prepared = fixture()
        sim, paths, proof, _, context = prepared
        observed = []

        class ObservedSimulator(ReachSimulator):
            def recording_frames(self, time, state, selected_paths, **kwargs):
                observed.append((time, state, tuple(selected_paths), kwargs))
                return super().recording_frames(time, state, selected_paths, **kwargs)

        sim.__class__ = ObservedSimulator
        phase = begin(prepared, TIMES)
        self.assertIsNotNone(phase)
        for time in TIMES:
            result = phase.sample(time)
            self.assertEqual(set(result.frames), set(paths))
        phase.finish()
        self.assertEqual(len(observed), len(TIMES))
        for (time, state, selected, kwargs), expected in zip(observed, TIMES):
            self.assertEqual(time, expected)
            self.assertIs(state, sim.state)
            self.assertEqual(selected, ordinary_paths(paths))
            self.assertEqual(kwargs["moving_frames"], frozenset(paths))
            self.assertIs(kwargs["recording_context"], context)
            self.assertIs(kwargs["recording_angular_proof"], proof["recording_angular_proof"])

    def test_empty_all_ordinary_custom_topology_and_small_cache_keep_scalar_fallback(self):
        for kind in ("empty", "ordinary", "topology", "capacity"):
            with self.subTest(kind=kind):
                prepared = fixture()
                sim, paths = prepared[:2]
                if kind == "empty":
                    prepared = (sim, (), *prepared[2:])
                elif kind == "ordinary":
                    prepared = (sim, ordinary_paths(paths), *prepared[2:])
                elif kind == "topology":
                    incoming = sim._incoming
                    sim._incoming = lambda state: incoming(state)
                else:
                    sim.work.max_cache_entries = 1
                self.assertIsNone(begin(prepared, TIMES))
                self.assertFalse(body_cache(sim.work))

    def test_unsupported_native_branch_falls_back_without_partial_selected_coverage(self):
        prepared = fixture()
        sim = prepared[0]
        joint = sim.model.joints['rig.arms["left"].elbow']
        child = sim.model.sites[joint.child]
        child.pose = replace(child.pose, position=(0.25, 0.0, 0.0))
        # The actual source no longer matches the supplied proof. The whole
        # optional stream declines; it cannot silently drop the affected arm.
        self.assertIsNone(begin(prepared, TIMES))
        self.assertFalse(body_cache(sim.work))

    def test_oversized_unselected_source_collections_decline_before_mixed_copying(self):
        for name in (*capture._MIXED_SOURCE_TABLES, "active_grips"):
            with self.subTest(collection=name):
                prepared = fixture()
                sim, paths, proof = prepared[:3]
                if name == "active_grips":
                    sim.state.active_grips = {f"unused-{index}" for index in range(257)}
                else:
                    values = getattr(sim.model, name)
                    exemplar = next(iter(values.values()))
                    for index in range(257 - len(values)):
                        path = f"unused-{index}"
                        values[path] = replace(exemplar, path=path)
                    self.assertEqual(len(values), 257)
                ops = fast.Binary64RecordingOps(sim.pose_ops, body_cursors=True)
                before = sim.work.counts.get("recording_mixed_topology", 0)
                # Isolate the new optional helper; the earlier complete
                # capture has its own separately bounded eligibility rules.
                with patch.object(capture, "_topology_record", side_effect=AssertionError("no oversized copying")):
                    self.assertIsNone(capture._capture_classifier(sim, sim.state, paths,
                        proof["recording_angular_proof"], ops))
                    with patch.object(capture, "begin_captured_phase", return_value=None):
                        self.assertIsNone(begin(prepared, TIMES))
                self.assertEqual(sim.work.counts.get("recording_mixed_topology", 0), before)
                self.assertFalse(body_cache(sim.work))

    def test_equal_size_source_map_replacements_and_name_shadowing_reject_publication(self):
        for kind in (*capture._MIXED_SOURCE_TABLES, "object_site_shadow", "unselected_site_name"):
            with self.subTest(kind=kind):
                prepared = fixture()
                sim = prepared[0]
                phase = begin(prepared, TIMES)
                for time in TIMES:
                    phase.sample(time)
                before = body_cache(sim.work)
                if kind in capture._MIXED_SOURCE_TABLES:
                    setattr(sim.model, kind, dict(getattr(sim.model, kind)))
                elif kind == "object_site_shadow":
                    # None of the existing kind-specific node witnesses
                    # reads this unselected object's key. Its new name would
                    # change rig.neck.frame from a site to an object.
                    value = sim.model.objects.pop('rig.legs["middle"]')
                    sim.model.objects["rig.neck"] = replace(value, path="rig.neck")
                else:
                    used = {identity[1] for row in phase.phase.source.records
                            for identity in row[4] if identity[0] == "sites"}
                    used.update(joint.child for joint in sim.model.joints.values())
                    unused = next(path for path in sim.model.sites if path not in used)
                    value = sim.model.sites.pop(unused)
                    sim.model.sites["unselected.renamed"] = replace(value, path="unselected.renamed")
                self.assertEqual(tuple(len(getattr(sim.model, name))
                                       for name in capture._MIXED_SOURCE_TABLES), phase.phase.source.sizes)
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertEqual(body_cache(sim.work), before)

    def test_transient_site_shadowing_does_not_enter_frozen_classifier_membership(self):
        prepared = fixture()
        sim = prepared[0]
        classify, hits = fast._planar_paths, []

        def classified(source, state, selected, **kwargs):
            hits.append(True)
            original = tuple(sim.model.objects.items())
            path = 'rig.legs["middle"]'
            value = sim.model.objects.pop(path)
            sim.model.objects["rig.neck"] = replace(value, path="rig.neck")
            try:
                self.assertNotIn("rig.neck", source.model.objects)
                supported = classify(source, state, selected, **kwargs)
                self.assertEqual(supported, frozenset(item for item in selected
                                                      if item not in ordinary_paths(selected)))
                return supported
            finally:
                sim.model.objects.clear()
                sim.model.objects.update(original)

        with patch.object(fast, "_planar_paths", side_effect=classified):
            phase = begin(prepared, TIMES)
        self.assertEqual(len(hits), 1)
        self.assertIsNotNone(phase)
        for time in TIMES:
            self.assertEqual(set(phase.sample(time).frames), set(prepared[1]))
        phase.finish()

    def test_classifier_callbacks_use_only_copied_source_inputs(self):
        outcomes = []
        for changed in (False, True):
            prepared = fixture()
            sim = prepared[0]
            classify, hits = fast._planar_paths, []
            look = sim.model.joints["rig.look"]
            axis = look.axis

            def classified(source, state, selected, **kwargs):
                self.assertIsNot(source, sim)
                if changed:
                    hits.append(True)
                    look.axis = (0.0, 0.0, 1.0)
                try:
                    result = classify(source, state, selected, **kwargs)
                    self.assertFalse(any(path.startswith("rig.head") for path in result))
                    return result
                finally:
                    look.axis = axis

            with patch.object(fast, "_planar_paths", side_effect=classified):
                phase = begin(prepared, TIMES)
            self.assertIsNotNone(phase)
            results = [bits(phase.sample(time)) for time in TIMES]
            phase.finish()
            self.assertEqual(bool(hits), changed)
            outcomes.append(results)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_temporary_native_mutation_during_ordinary_sampling_cannot_enter_captured_operands(self):
        outcomes = []
        for changed in (False, True):
            prepared = fixture()
            sim = prepared[0]
            phase = begin(prepared, TIMES)
            ordinary = sim.recording_frames
            site = sim.model.sites[sim.model.joints['rig.arms["left"].elbow'].parent]
            pose, hits = site.pose, []

            def sampled(*args, **kwargs):
                result = ordinary(*args, **kwargs)
                if changed:
                    hits.append(True)
                    site.pose = replace(pose, position=(7.0, 0.0, 0.0))
                return result

            with patch.object(sim, "recording_frames", side_effect=sampled):
                values = [bits(phase.sample(time)) for time in TIMES]
            site.pose = pose
            phase.finish()
            self.assertEqual(bool(hits), changed)
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_final_receipt_rejects_ordinary_source_claim_identity_and_bound_changes(self):
        for kind in ("axis", "child", "follow", "law", "claim", "identity", "runtime",
                     "bounds_replace", "bounds_field", "proof"):
            with self.subTest(kind=kind):
                prepared = fixture()
                sim, paths, proof = prepared[:3]
                backing = dict(proof["recording_angular_proof"].frames)
                proof["recording_angular_proof"] = replace(proof["recording_angular_proof"],
                                                          frames=MappingProxyType(backing))
                phase = begin(prepared, TIMES)
                for time in TIMES:
                    phase.sample(time)
                before, hit = body_cache(sim.work), []
                look = sim.model.joints["rig.look"]
                claimant = sim.state.claims[(look.path, "coordinate")]
                path = ordinary_paths(paths)[0]

                def change():
                    if hit:
                        return
                    hit.append(True)
                    if kind == "axis":
                        look.axis = (0.0, 0.0, 1.0)
                    elif kind == "child":
                        child = sim.model.sites[look.child]
                        child.pose = replace(child.pose, position=(0.0, -0.5, 0.0))
                    elif kind == "follow":
                        follow = next(value for value in sim.model.follows.values()
                                      if value.child.startswith("rig.head.eyes"))
                        follow.offset = replace(follow.offset, position=(0.5, 0.0, 0.0))
                    elif kind == "law":
                        sim.state.actions[claimant].initial += 0.125
                    elif kind == "claim":
                        del sim.state.claims[(look.path, "coordinate")]
                    elif kind == "identity":
                        sim.model.objects["rig.head"] = replace(sim.model.objects["rig.head"])
                    elif kind == "runtime":
                        sim.state.actions[claimant] = deepcopy(sim.state.actions[claimant])
                    elif kind == "bounds_replace":
                        proof["frames"][path] = replace(proof["frames"][path])
                    elif kind == "bounds_field":
                        bound = proof["frames"][path]
                        object.__setattr__(bound, "rotation_error_rad", bound.rotation_error_rad + F(1, 1000))
                    else:
                        backing[path] = replace(backing[path])

                publish = sim.work.remember_batch

                def publishing(entries, *, admission):
                    sim.work.external_check = change
                    return publish(entries, admission=admission)

                with patch.object(sim.work, "remember_batch", side_effect=publishing):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        phase.finish()
                self.assertTrue(hit)
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertEqual(body_cache(sim.work), before)

    def test_final_receipt_binds_model_state_and_both_arithmetic_owners(self):
        for kind in ("model", "state", "source_ops", "work", "arithmetic_work"):
            with self.subTest(kind=kind):
                prepared = fixture()
                sim = prepared[0]
                phase = begin(prepared, TIMES)
                for time in TIMES:
                    phase.sample(time)
                work, before = sim.work, body_cache(sim.work)
                if kind == "model":
                    sim.model = deepcopy(sim.model)
                elif kind == "state":
                    sim.state = deepcopy(sim.state)
                elif kind == "source_ops":
                    sim.pose_ops = ReachPoseOps(sim.work)
                elif kind == "work":
                    sim.work = ReachExecutionWork()
                else:
                    sim.pose_ops.work = ReachExecutionWork()
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertEqual(body_cache(work), before)

    def test_ordinary_coverage_and_clock_errors_reject_before_native_publication(self):
        for kind in ("missing", "extra", "clock", "incomplete", "active"):
            with self.subTest(kind=kind):
                prepared = fixture()
                sim = prepared[0]
                phase = begin(prepared, TIMES)
                ordinary = sim.recording_frames

                def sampled(*args, **kwargs):
                    result = ordinary(*args, **kwargs)
                    if kind == "missing":
                        result.pop(next(iter(result)))
                    elif kind == "extra":
                        result["unselected.frame"] = next(iter(result.values()))
                    elif kind == "active":
                        phase.sample(TIMES[0])
                    return result

                with patch.object(sim, "recording_frames", side_effect=sampled):
                    with self.assertRaises(ReachAdmissionError):
                        if kind == "incomplete":
                            phase.finish()
                        else:
                            phase.sample(TIMES[1] if kind == "clock" else TIMES[0])
                self.assertFalse(body_cache(sim.work))

    def test_original_ordinary_callback_exception_keeps_its_identity(self):
        prepared = fixture()
        sim = prepared[0]
        phase = begin(prepared, TIMES)
        marker = fast._UnsupportedPlanar("ordinary observer cancellation")
        ordinary = sim.recording_frames

        def sampled(*args, **kwargs):
            def rejected():
                raise marker
            sim.work.external_check = rejected
            return ordinary(*args, **kwargs)

        with patch.object(sim, "recording_frames", side_effect=sampled):
            with self.assertRaises(fast._UnsupportedPlanar) as caught:
                phase.sample(TIMES[0])
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertFalse(body_cache(sim.work))

    def test_final_receipt_cancellation_and_live_operand_caps_publish_no_partial_group(self):
        for trigger in ("recording_mixed_source_guard", "cache_batch_domain", "cache_insert"):
            for cancelled in (False, True):
                with self.subTest(trigger=trigger, cancelled=cancelled):
                    prepared = fixture()
                    sim = prepared[0]
                    phase = begin(prepared, TIMES)
                    for time in TIMES:
                        phase.sample(time)
                    before, hit = body_cache(sim.work), []
                    charge = sim.work.charge
                    marker = RuntimeError("mixed phase publication cancelled")

                    def charged(kind="checkpoint", amount=1):
                        if kind == trigger and not hit:
                            hit.append(True)
                            def reject():
                                sim.work.max_operand_bits = 128
                                if cancelled:
                                    raise marker
                            sim.work.external_check = reject
                        return charge(kind, amount)

                    with patch.object(sim.work, "charge", side_effect=charged):
                        with self.assertRaises(RuntimeError if cancelled else fast.RecordingRoundingAmbiguity) as caught:
                            phase.finish()
                    self.assertTrue(hit)
                    if cancelled:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(sim.work.callback_error, marker)
                        self.assertEqual(body_cache(sim.work), before)
                    else:
                        self.assertTrue(all(key in before and before[key] is value
                                            for key, value in body_cache(sim.work).items()))

    def test_capacity_changes_during_ordinary_sampling_and_publication_keep_native_group_private(self):
        for final in (False, True):
            with self.subTest(final=final):
                prepared = fixture()
                sim = prepared[0]
                phase = begin(prepared, TIMES)
                if final:
                    for time in TIMES:
                        phase.sample(time)
                    charge, hit = sim.work.charge, []

                    def charged(kind="checkpoint", amount=1):
                        if kind == "cache_insert" and not hit:
                            hit.append(True)
                            sim.work.max_cache_entries = 1
                        return charge(kind, amount)

                    with patch.object(sim.work, "charge", side_effect=charged):
                        phase.finish()
                    self.assertTrue(hit)
                else:
                    ordinary = sim.recording_frames

                    def sampled(*args, **kwargs):
                        result = ordinary(*args, **kwargs)
                        sim.work.max_cache_entries = 1
                        return result

                    with patch.object(sim, "recording_frames", side_effect=sampled):
                        with self.assertRaises(fast.RecordingRoundingAmbiguity):
                            phase.sample(TIMES[0])
                self.assertFalse(body_cache(sim.work))

    def test_reentrant_ordinary_callback_keeps_inner_complete_native_cursors(self):
        prepared = fixture()
        sim = prepared[0]
        outer = begin(prepared, TIMES)
        outer.sample(TIMES[0])
        ordinary, entered, retained = sim.recording_frames, [], []

        def sampled(*args, **kwargs):
            if not entered:
                entered.append(True)
                inner_times = (F(3, 4), F(7, 8))
                inner = begin(prepared, inner_times)
                for time in inner_times:
                    inner.sample(time)
                inner.finish()
                retained.append(body_cache(sim.work))
            return ordinary(*args, **kwargs)

        with patch.object(sim, "recording_frames", side_effect=sampled):
            for time in TIMES[1:]:
                outer.sample(time)
            outer.finish()
        self.assertEqual(len(retained), 1)
        self.assertTrue(retained[0])
        self.assertEqual(body_cache(sim.work), retained[0])
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_actual_p11_prefix_glb_preserves_every_delivered_byte(self):
        outputs = []
        for captured in (False, True):
            compiler = compile_construction(source_case("P11"))
            mode = nullcontext() if captured else patch.object(fast, "begin_bounded_phase", return_value=None)
            with mode:
                result = export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(compiler.budget.operations, 100000)
            if captured:
                self.assertGreater(compiler.reach_work.counts.get("recording_mixed_source_guard", 0), 0)
            outputs.append(result.data)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
