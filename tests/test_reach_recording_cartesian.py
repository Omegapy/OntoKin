"""Cartesian captured arithmetic keeps source ancestry, actual origins and bounds."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.model import Pose
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import phase_bounds
from ontokin.reach_pose import ReachPoseOps, RotationValue, UNIT
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_pose import independent_oracle
from test_reach_recording_captured_chain import begin, chain
from test_reach_recording_captured_graph import bits, body_cache


TIMES = (F(1, 8), F(1, 4), F(3, 8))


def native(**options):
    return fast.Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()),
        body_cursors=True, cartesian_axes=True, **options)


def cyclic(values, axis):
    # The proper map sends basis (X,Y,Z) to (Y,Z,X) or (Z,X,Y).
    return tuple(values[(index - axis - 1) % 3] for index in range(3))


def rotation_bits(value):
    return struct.pack("<dd??", value.w, value.z, value.zero_w, value.zero_z)


def cursor_arguments():
    return dict(phase_start=F(0), phase_end=F(4), context=object(),
                path="carrier", proof_token=object(), max_steps=10000)


class ReachRecordingCartesianTests(unittest.TestCase):
    def test_cartesian_selector_and_private_axis_types_are_explicit(self):
        for value in (1, None, "yes"):
            with self.assertRaises(ValueError):
                fast.Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), cartesian_axes=value)
        ops = native()
        for value in (False, -1, 3, 1.0, None):
            with self.subTest(axis=value), self.assertRaises(fast._UnsupportedPlanar):
                ops._rotation_domain(fast._FloatRotation(1.0, 0.0, False, True, value))
        old = fast.Binary64RecordingOps(ops.source_ops)
        for axis in (0, 1):
            with self.assertRaises(fast._UnsupportedPlanar):
                old._project_rotation(RotationValue((F(1), *cyclic((F(0), F(0), F(1)), axis))))

    def test_projection_axis_and_frozen_source_unit_admission(self):
        for axis in range(3):
            with self.subTest(axis=axis):
                ops = native()
                source = RotationValue((F(3), *cyclic((F(0), F(0), F(4)), axis)))
                value = ops._project_rotation(source)
                self.assertEqual(value.axis, axis)
                self.assertEqual((value.w, value.z), (0.6, 0.8))
                public = (0.6, *cyclic((0.0, 0.0, 0.8), axis))
                frozen = RotationValue(tuple(F(value) for value in public), frozen_projection=public)
                self.assertEqual(ops._project_rotation(frozen).axis, axis)
                with self.assertRaises(fast._UnsupportedPlanar):
                    ops._project_rotation(replace(frozen, components=source.components))
                invalid = (0.5, *cyclic((0.0, 0.0, 0.5), axis))
                with self.assertRaises(fast._UnsupportedPlanar):
                    ops._project_rotation(RotationValue(tuple(F(value) for value in invalid),
                                                        frozen_projection=invalid))

    def test_zero_seeds_keep_the_declared_axis_and_canonical_zero_bits(self):
        for axis in range(3):
            ops = native()
            vector = cyclic((F(0), F(0), F(-1)), axis)
            value = ops._axis_rotation(vector, F(0), structural=False)
            self.assertEqual(value.axis, axis)
            self.assertFalse(value.zero_z)
            pose = ops.make_recording(orientation=value)
            self.assertEqual(struct.pack("<4d", *pose.orientation), struct.pack("<4d", 1., 0., 0., 0.))
            with self.assertRaises(fast._UnsupportedPlanar):
                ops._project_rotation(RotationValue((F(1), F(1), F(1), F(0))))

    def test_product_operation_order_and_canonical_lift_are_axis_invariant(self):
        rotations = ((0.6, 0.8, False, False), (0.6, -0.8, False, False),
                     (0.0, 1.0, True, False), (1.0, -0.0, False, False),
                     (1.0, 0.0, False, True))
        for left in rotations:
            for right in rotations:
                outputs = []
                for axis in range(3):
                    ops = native()
                    result = ops._product(fast._FloatRotation(*left, axis), fast._FloatRotation(*right, axis))
                    self.assertEqual(result.axis, axis)
                    outputs.append((rotation_bits(result), dict(ops.work.counts)))
                self.assertEqual(outputs[0], outputs[1])
                self.assertEqual(outputs[1], outputs[2])

    def test_cross_axis_products_decline_without_reusing_another_axis(self):
        ops = native(share_arithmetic=True)
        x = fast._FloatRotation(0.6, 0.8, False, False, 0)
        y = replace(x, axis=1)
        ops._product(x, x)
        with self.assertRaises(fast._UnsupportedPlanar):
            ops._product(x, y)
        identity = fast._FloatRotation(1.0, 0.0, False, True)
        self.assertIs(ops._product(identity, y), y)
        self.assertIs(ops._product(x, identity), x)

    def test_offset_permutation_preserves_signed_zero_subnormal_bits_and_counts(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        cases = (((1.0, -0.0, tiny), (False, True, False)),
                 ((-0.0, 1.0, -tiny), (True, False, False)),
                 ((0.25, -0.5, -0.0), (False, False, True)),
                 ((-1.0, 0.0, 2.0), (False, True, False)))
        for values in ((0.6, 0.8, False, False), (1.0, -0.0, False, False),
                       (0.0, 1.0, True, False), (tiny, -tiny, False, False)):
            for position, zeros in cases:
                original = native()
                expected, masks = original._rotated_offset(fast._FloatRotation(*values), position, zeros)
                for axis in (0, 1):
                    actual = native()
                    value, actual_masks = actual._rotated_offset(fast._FloatRotation(*values, axis),
                        cyclic(position, axis), cyclic(zeros, axis))
                    self.assertEqual(struct.pack("<3d", *value), struct.pack("<3d", *cyclic(expected, axis)))
                    self.assertEqual(actual_masks, cyclic(masks, axis))
                    self.assertEqual(actual.work.counts, original.work.counts)

    def test_retained_products_offsets_and_public_orientations_cannot_alias_axes(self):
        ops = native(share_arithmetic=True)
        rotations, offsets = [], []
        for axis in range(3):
            source = fast._FloatRotation(0.6, 0.8, False, False, axis)
            rotations.append(ops._product(source, source))
            offsets.append(ops._rotated_offset(source, (1.0, 2.0, 3.0), (False, False, False))[0])
        self.assertEqual([value.axis for value in rotations], [0, 1, 2])
        self.assertEqual(len(set(offsets)), 3)
        self.assertEqual(len({ops._rotation_bits(value) for value in rotations}), 3)
        for axis, value in enumerate(rotations):
            orientation = ops.make_recording(orientation=value).orientation
            self.assertEqual(orientation[axis + 1], value.z)
            self.assertEqual(tuple(v for i, v in enumerate(orientation[1:]) if i != axis), (0.0, 0.0))
        self.assertLessEqual(len(ops.work._cache), 256)
        self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))

    def test_strict_constant_projection_cannot_borrow_an_enabled_cartesian_value(self):
        ops = native()
        leaf = ops.source_ops.make((1, 2, 3), (1, 0, 1, 0))
        self.assertEqual(ops._pose(leaf).rotation.axis, 1)
        strict = fast.Binary64RecordingOps(ops.source_ops)
        with self.assertRaises(fast._UnsupportedPlanar):
            strict._pose(leaf)

    def test_strict_source_leaf_cannot_borrow_an_enabled_cartesian_cache_entry(self):
        for axis in (0, 1):
            ops = native(share_arithmetic=True)
            pose = Pose(position=(1.0, 2.0, 3.0), rotation=(0.6, *cyclic((0.0, 0.0, 0.8), axis)))
            def source(value, inverse=False):
                return ops.source_ops.inverse_pose(value) if inverse else ops.source_ops.constant_pose(value)
            for inverse in (False, True):
                value = ops.recording_constant_pose(pose, inverse=inverse, build=source)
                self.assertEqual(value.rotation.axis, axis)
                strict = fast.Binary64RecordingOps(ops.source_ops, share_arithmetic=True)
                with self.assertRaises(fast._UnsupportedPlanar):
                    strict.recording_constant_pose(pose, inverse=inverse, build=source)

    def test_strict_relative_pose_cannot_borrow_an_enabled_local_rotation(self):
        for axis in (0, 1):
            ops = native(share_arithmetic=True)
            strict = fast.Binary64RecordingOps(ops.source_ops, share_arithmetic=True)
            parent = ops.make_recording((1, 2, 3))
            local = Pose(position=(0.25, 0.5, 0.75), rotation=(0.6, *cyclic((0.0, 0.0, 0.8), axis)))
            def compose(owner, base):
                def source(value, inverse=False):
                    return (owner.source_ops.inverse_pose(value) if inverse
                            else owner.source_ops.constant_pose(value))
                leaf = owner.recording_constant_pose(local, build=source)
                return owner.compose_recording_fast(base, leaf)
            values = dict(context=object(), path="site", max_steps=10000)
            result = ops.recording_relative_pose((parent, local), lambda base: compose(ops, base), **values)
            self.assertEqual(result.rotation.axis, axis)
            with self.assertRaises(fast._UnsupportedPlanar):
                strict.recording_relative_pose((parent, local), lambda base: compose(strict, base), **values)

    def test_body_recurrence_from_zero_and_reseed_matches_independent_intervals(self):
        oracle = independent_oracle()
        for axis in range(3):
            ops, arguments = native(), cursor_arguments()
            rate, times, seeds = F(-7, 4), [F(0), F(1, 8), F(1, 4), F(1, 4), F(1, 2)], []
            arguments["max_steps"] = 3
            for time in times:
                def seed():
                    seeds.append(time)
                    return ops.source_ops.axis_rotation(cyclic((0, 0, 1), axis), rate * time)
                value = ops.recording_body_orientation(seed, axis, rate, time, **arguments)
                self.assertEqual(value.axis, axis)
                sine, cosine = oracle.Context(192, oracle.Budget()).sincos_point(rate * time / 2)
                distance = min(max(max(abs(sign * F(actual) - interval.lo),
                                       abs(sign * F(actual) - interval.hi))
                                   for actual, interval in ((value.w, cosine), (value.z, sine)))
                               for sign in (1, -1))
                self.assertLessEqual(distance, F(1, 2**41))
            self.assertEqual(seeds, [times[0], times[3]])

    def test_body_mismatched_seed_and_cap_or_cancellation_cannot_publish(self):
        ops = native()
        with self.assertRaises(fast._UnsupportedPlanar):
            ops.recording_body_orientation(lambda: RotationValue((F(1), F(0), F(0), F(1))),
                                           1, F(1), F(0), **cursor_arguments())
        for axis in (0, 1):
            for narrow in (False, True):
                ops, arguments = native(), cursor_arguments()
                for time in (F(0), F(1, 8)):
                    ops.recording_body_orientation(lambda: RotationValue(UNIT), axis, F(1), time, **arguments)
                previous, charge, hits = dict(body_cache(ops.work)), ops.work.charge, []
                marker = RuntimeError("cancel Cartesian recurrence")
                def interrupt(kind="checkpoint", amount=1):
                    if kind == "recording_float_mul" and not hits:
                        hits.append(kind)
                        ops.work.external_check = (lambda: setattr(ops.work, "max_operand_bits", 128)
                            if narrow else (_ for _ in ()).throw(marker))
                    return charge(kind, amount)
                with patch.object(ops.work, "charge", side_effect=interrupt):
                    with self.assertRaises(fast._UnsupportedPlanar if narrow else RuntimeError) as caught:
                        ops.recording_body_orientation(lambda: RotationValue(UNIT), axis, F(1), F(1, 4), **arguments)
                self.assertTrue(hits)
                if not narrow:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.work.callback_error, marker)
                self.assertEqual(body_cache(ops.work), previous)

    def test_actual_p11_captures_y_head_and_preserves_nonzero_world_origins(self):
        fixture = chain("P11")
        sim, paths = fixture[:2]
        original = deepcopy(sim.state)
        phase = begin(fixture, TIMES)
        self.assertIsInstance(phase.phase, capture._CapturedPhase)
        self.assertEqual(phase.phase.graph.selected, paths)
        traversals = sim.work.counts.get("source_pose_time_key", 0)
        values = [phase.sample(time) for time in TIMES]
        phase.finish()
        self.assertEqual(sim.work.counts.get("source_pose_time_key", 0), traversals)
        head_paths = tuple(path for path in paths if path.startswith("rig.head"))
        self.assertTrue(head_paths)
        for result in values:
            for path in head_paths:
                self.assertTrue(any(result.frames[path].position))
                self.assertGreater(result.excess_by_frame[path].quaternion_component, 0)
            self.assertEqual(set(result.frames), set(paths))
        self.assertEqual(sim.state, original)
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_persistent_axis_change_rejects_the_complete_phase_before_cursor_publication(self):
        fixture = chain("P11")
        sim = fixture[0]
        phase = begin(fixture, TIMES)
        for time in TIMES:
            phase.sample(time)
        look = next(value for value in sim.model.joints.values() if value.axis == (0.0, 1.0, 0.0))
        look.axis = (1.0, 0.0, 0.0)
        before = body_cache(sim.work)
        with self.assertRaises(ReachAdmissionError) as caught:
            phase.finish()
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertEqual(body_cache(sim.work), before)

    def test_transient_axis_and_neck_pose_mutation_cannot_enter_captured_arithmetic(self):
        results = []
        for mutate in (False, True):
            fixture = chain("P11")
            sim = fixture[0]
            phase = begin(fixture, TIMES)
            look = next(value for value in sim.model.joints.values() if value.axis == (0.0, 1.0, 0.0))
            site = sim.model.sites[look.parent]
            axis, pose = look.axis, site.pose
            values = [bits(phase.sample(TIMES[0]))]
            if mutate:
                look.axis = (1.0, 0.0, 0.0)
                site.pose = replace(pose, position=(8.0, 9.0, 10.0))
            values.extend(bits(phase.sample(time)) for time in TIMES[1:])
            look.axis, site.pose = axis, pose
            phase.finish()
            results.append(values)
        self.assertEqual(results[0], results[1])

    def test_axial_nonzero_child_origin_matches_ordinary_source_for_signed_x_and_y(self):
        for axis in (0, 1):
            for sign in (-1, 1):
                fixture = chain("P11")
                sim, paths, _, moving, context = fixture
                look = next(value for value in sim.model.joints.values() if value.axis == (0.0, 1.0, 0.0))
                look.axis = tuple(1.0 if index == axis else 0.0 for index in range(3))
                child = sim.model.sites[look.child]
                child.pose = replace(child.pose, position=tuple(sign * 0.25 if index == axis else 0.0
                                                                for index in range(3)))
                proof = phase_bounds(sim, F(0), F(2), sim.state, selected_frames=paths, recording_proof=True)
                phase = begin((sim, paths, proof, moving, context), TIMES)
                self.assertIsInstance(phase.phase, capture._CapturedPhase)
                values = [phase.sample(time).frames["rig.head.frame"] for time in TIMES]
                phase.finish()
                for time, value in zip(TIMES, values):
                    expected = sim.recording_frames(time, sim.state, ("rig.head.frame",))["rig.head.frame"]
                    self.assertEqual(value.position, expected.position)
                    self.assertLessEqual(min(max(abs(F(a) - sign * F(b))
                        for a, b in zip(value.orientation, expected.orientation)) for sign in (-1, 1)), F(1, 2**41))

    def test_nearly_axial_or_nearly_identity_child_keeps_ordinary_fallback(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        for kind in ("offset", "rotation"):
            fixture = chain("P11")
            sim, paths, _, moving, context = fixture
            look = next(value for value in sim.model.joints.values() if value.axis == (0.0, 1.0, 0.0))
            child = sim.model.sites[look.child]
            child.pose = (replace(child.pose, position=(tiny, -0.25, 0.0)) if kind == "offset" else
                          replace(child.pose, rotation=(1.0, 0.0, tiny, 0.0)))
            proof = phase_bounds(sim, F(0), F(2), sim.state, selected_frames=paths, recording_proof=True)
            phase = begin((sim, paths, proof, moving, context), TIMES)
            self.assertIsInstance(phase.phase, capture._MixedCapturedPhase)
            self.assertIn("rig.head.frame", phase.phase.ordinary)

    def test_axial_child_leaf_is_detached_before_transient_in_place_source_mutation(self):
        results = []
        for mutate in (False, True):
            fixture = chain("P11")
            sim = fixture[0]
            phase = begin(fixture, TIMES)
            node = phase.phase.graph.nodes["rig.head.frame"]
            child = sim.model.sites[sim.model.joints[node.path].child]
            self.assertIsNot(node.operands[2], child.pose)
            position = child.pose.position
            values = [bits(phase.sample(TIMES[0]))]
            if mutate:
                object.__setattr__(child.pose, "position", (7.0, 8.0, 9.0))
            values.extend(bits(phase.sample(time)) for time in TIMES[1:])
            object.__setattr__(child.pose, "position", position)
            phase.finish()
            results.append(values)
        self.assertEqual(results[0], results[1])

    def test_mixed_axis_ancestry_keeps_complete_ordinary_partition(self):
        fixture = chain("P11")
        sim, paths, _, moving, context = fixture
        look = next(value for value in sim.model.joints.values() if value.axis == (0.0, 1.0, 0.0))
        site = sim.model.sites[look.parent]
        site.pose = replace(site.pose, rotation=(0.6, 0.0, 0.0, 0.8))
        proof = phase_bounds(sim, F(0), F(2), sim.state, selected_frames=paths, recording_proof=True)
        phase = begin((sim, paths, proof, moving, context), TIMES)
        self.assertIsInstance(phase.phase, capture._MixedCapturedPhase)
        self.assertTrue(all(path in phase.phase.ordinary for path in paths if path.startswith("rig.head")))
        for time in TIMES:
            self.assertEqual(set(phase.sample(time).frames), set(paths))
        phase.finish()

    def test_custom_ordinary_observer_retains_its_per_key_dispatch(self):
        fixture = chain("P11")
        sim, paths = fixture[:2]
        with patch.object(sim, "recording_frames", wraps=sim.recording_frames) as observed:
            phase = begin(fixture, TIMES)
            self.assertIsInstance(phase.phase, capture._MixedCapturedPhase)
            for time in TIMES:
                self.assertEqual(set(phase.sample(time).frames), set(paths))
            phase.finish()
        self.assertEqual(observed.call_count, len(TIMES))
        self.assertTrue(all(all(path.startswith("rig.head") for path in call.args[2])
                            for call in observed.call_args_list))

    def test_late_dispatch_or_selector_changes_cannot_publish_cartesian_cursors(self):
        for change in ("dispatch", "selector"):
            fixture = chain("P11")
            sim = fixture[0]
            phase = begin(fixture, TIMES)
            for time in TIMES:
                phase.sample(time)
            if change == "dispatch":
                original = sim.recording_frames
                sim.recording_frames = lambda *args, **kwargs: original(*args, **kwargs)
            else:
                phase.phase.ops.recording_cartesian_axes = False
            previous = body_cache(sim.work)
            with self.assertRaises(fast.RecordingRoundingAmbiguity):
                phase.finish()
            self.assertEqual(body_cache(sim.work), previous)

    def test_actual_p11_prefix_passes_independent_supplied_byte_validation(self):
        compiler = compile_construction(source_case("P11"))
        original, captured = capture.begin_captured_phase, []
        def observed(*args, **kwargs):
            phase = original(*args, **kwargs)
            if phase is not None:
                captured.append((phase.ops.recording_cartesian_axes,
                    tuple(node.record.rate.axis for node in phase.graph.nodes.values()
                          if node.frame.startswith("rig.head") and node.record is not None)))
            return phase
        with patch.object(capture, "begin_captured_phase", side_effect=observed):
            result = export_glb(compiler.model, options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                                target_contract="ontokin.glb/0.6", work=compiler.reach_work)
        self.assertEqual(result.report["validation"]["status"], "passed")
        self.assertTrue(any(enabled and 1 in axes for enabled, axes in captured))
        self.assertEqual(compiler.reach_work.max_operations, 100000)
        self.assertLessEqual(compiler.reach_work.operations, 100000)
        self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))


if __name__ == "__main__":
    unittest.main()
