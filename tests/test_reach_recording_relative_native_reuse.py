"""Shared local calculations preserve fresh native world-origin additions."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import math
import struct
import unittest
from unittest.mock import patch

from ontokin.model import Pose
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, MAX_FLOAT_ROTATION_STEPS, _AffineCoordinate, _AffineLaw,
    _FloatPose, _FloatRotation, _UnsupportedPlanar,
)
from test_reach_recording_graph_sharing import prepared_many, sample


def native(*, cache=256, sharing=True):
    work = ReachExecutionWork(max_cache_entries=cache)
    return Binary64RecordingOps(ReachPoseOps(work), share_arithmetic=sharing,
                                affine_coordinates=True)


def bits(value):
    return (struct.pack("<5d", *value.position, value.rotation.w, value.rotation.z),
            value.zeros, value.rotation.zero_w, value.rotation.zero_z, value.depth)


def leaf(ops, pose, *, inverse=False):
    return ops.recording_constant_pose(pose, inverse=inverse,
        build=lambda value, inverse=False: (ops.source_ops.inverse_pose(value) if inverse
                                           else ops.source_ops.constant_pose(value)))


def follow(ops, parent, local):
    return ops.compose_recording_fast(parent, leaf(ops, local))


def hinge(ops, parent, local, coordinate, axis, context):
    rotation = ops.recording_axis_rotation(axis, coordinate,
        context=context, path="hinge:test", max_steps=10000)
    return ops.compose_recording_fast(
        ops.compose_recording_fast(parent, ops.make_recording(orientation=rotation)),
        leaf(ops, local, inverse=True))


def reuse(ops, signature, build, *, context=None, path="test", max_steps=10000):
    return ops.recording_relative_pose(signature, build,
        context=context or object(), path=path, max_steps=max_steps)


class ReachRecordingRelativeNativeReuseTests(unittest.TestCase):
    def test_translated_follow_and_site_keep_exact_native_bits(self):
        tiny = math.ldexp(1.0, -1074)
        origins = (
            ((0.0, 0.0, 0.0), (True, True, True)),
            ((-0.0, 0.0, -0.0), (False, True, False)),
            ((float(2**54), -float(2**54), tiny), (False, False, False)),
            ((-float(2**54), float(2**54), -tiny), (False, False, False)),
            ((0.25, 7.75, -0.5), (False, False, False)),
            ((-1.0, -2.0, 0.0), (False, False, True)),
        )
        rotations = (_FloatRotation(1.0, 0.0, False, True),
                     _FloatRotation(0.6, 0.8, False, False))
        leaves = (Pose(), Pose(position=(1.0, 2.0, -tiny)),
                  Pose(position=(1.0 / 3.0, -2.0 / 7.0, 0.0), rotation=(0.8, 0.0, 0.0, 0.6)))
        for kind in ("follow", "site"):
            for rotation in rotations:
                for local in leaves:
                    actual, reference = native(), native()
                    builds = []
                    for position, zeros in origins:
                        parent = _FloatPose(position, rotation, zeros, 3)
                        signature = (("follow", parent, local) if kind == "follow" else (parent, local))
                        def build(base):
                            builds.append(base)
                            return follow(actual, base, local)
                        with self.subTest(kind=kind, parent=parent, local=local):
                            result = reuse(actual, signature, build)
                            expected = follow(reference, parent, local)
                            self.assertEqual(bits(result), bits(expected))
                    self.assertEqual(len(builds), 1)
                    self.assertEqual(actual.work.operations, sum(actual.work.counts.values()))

    def test_constant_joint_preserves_ordered_child_inverse_and_each_origin(self):
        local = Pose(position=(1.0 / 3.0, -2.0 / 7.0, 0.0), rotation=(0.8, 0.0, 0.0, 0.6))
        law = _AffineLaw(F(1, 7), F(1, 7), F(2), F(0))
        for axis in ((0.0, 0.0, 1.0), (0.0, -0.0, -1.0)):
            actual, reference = native(), native()
            context, builds = object(), []
            for index, elapsed in enumerate((F(0), F(1, 8), F(3, 2), F(2), F(1, 4))):
                parent = _FloatPose((float(2**54) if index % 2 else -1.0,
                    0.25 * index, -0.0), _FloatRotation(0.6, 0.8, False, False),
                    (False, index == 0, False), 2)
                coordinate = _AffineCoordinate(law, elapsed, True)
                signature = ("joint", parent, "hinge", axis, coordinate, F(0), local)
                def build(base):
                    builds.append(base)
                    return hinge(actual, base, local, coordinate, axis, context)
                result = reuse(actual, signature, build, context=context)
                expected = hinge(reference, parent, local, coordinate, axis, context)
                self.assertEqual(bits(result), bits(expected))
            self.assertEqual(len(builds), 1)

    def test_unchanging_affine_rotation_retains_its_exact_seed_without_cursor_history(self):
        ops = native()
        context = object()
        for value in (F(0), F(1, 7), F(-5, 3)):
            law = _AffineLaw(value, value, F(2), F(0))
            expected = ops._axis_rotation((F(0), F(0), F(1)), value, structural=False)
            before = ops.work.counts.get("recording_float_rotation_step", 0)
            for index in range(MAX_FLOAT_ROTATION_STEPS + 3):
                elapsed = F(index % 17, 9)
                result = ops.recording_axis_rotation((0.0, 0.0, 1.0),
                    _AffineCoordinate(law, elapsed, True), context=context,
                    path="hinge:test", max_steps=10000)
                self.assertEqual(result, expected)
                self.assertFalse(result.zero_w)
                self.assertFalse(result.zero_z)
            self.assertEqual(ops.work.counts.get("recording_float_rotation_step", 0), before)
        self.assertFalse(any("bounded_affine_axis" in key for key in ops.work._cache))
        self.assertEqual(ops.work.max_operations, 100000)

    def test_complete_rotation_local_pose_and_depth_operands_remain_distinct(self):
        ops = native()
        parent = _FloatPose((0.25, 0.5, 0.0), _FloatRotation(1.0, 0.0, False, True),
                            (False, False, True), 1)
        local = Pose(position=(1.0, 0.0, 0.0))
        variants = ((parent, local),
            (replace(parent, rotation=_FloatRotation(1.0, -0.0, False, False)), local),
            (replace(parent, rotation=_FloatRotation(0.6, 0.8, False, False)), local),
            (replace(parent, depth=2), local),
            (parent, replace(local, position=(1.0, -0.0, 0.0))),
            (parent, replace(local, rotation=(0.8, 0.0, 0.0, 0.6))))
        builds = []
        for current, fixed in variants:
            def build(base):
                builds.append((current, fixed))
                return follow(ops, base, fixed)
            result = reuse(ops, (current, fixed), build)
            self.assertEqual(bits(result), bits(follow(native(), current, fixed)))
        self.assertEqual(len(builds), len(variants))

    def test_varying_hinges_sliders_and_malformed_leaves_keep_original_path(self):
        ops = native()
        parent = _FloatPose((0.0, 0.0, 0.0), _FloatRotation(1.0, 0.0, False, True),
                            (True, True, True), 0)
        law = _AffineLaw(F(0), F(1), F(2), F(1, 2))
        coordinate = _AffineCoordinate(law, F(1), True)
        signatures = (
            ("joint", parent, "hinge", (0.0, 0.0, 1.0), coordinate, F(0), Pose()),
            ("joint", parent, "slider", (1.0, 0.0, 0.0), 0.5, F(0), Pose()),
            (parent, Pose(position=(False, 0.0, 0.0))),
            (parent, Pose(rotation=(float("nan"), 0.0, 0.0, 1.0))),
            (replace(parent, depth=64), Pose()),
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                self.assertIsNone(reuse(ops, signature,
                    lambda base: self.fail("An unsupported template executed its builder")))
        self.assertFalse(ops.work._cache)

    def test_constant_joint_rechecks_clock_scalar_types_and_cursor_domain_before_hits(self):
        ops = native()
        parent = _FloatPose((0.0, 0.0, 0.0), _FloatRotation(1.0, 0.0, False, True),
                            (True, True, True), 0)
        law = _AffineLaw(F(0), F(0), F(2), F(0))
        coordinate = _AffineCoordinate(law, F(1), True)
        axis, context = (0.0, 0.0, 1.0), object()
        signature = ("joint", parent, "hinge", axis, coordinate, F(0), Pose())
        reuse(ops, signature, lambda base: hinge(ops, base, Pose(), coordinate, axis, context), context=context)
        for bad in (replace(coordinate, elapsed=False), replace(coordinate, elapsed=F(-1)),
                    replace(coordinate, elapsed=F(3)), replace(coordinate, running=1),
                    replace(coordinate, law=replace(law, slope=False)),
                    replace(coordinate, law=replace(law, duration=F(0)))):
            with self.subTest(coordinate=bad), self.assertRaises((ReachAdmissionError, _UnsupportedPlanar)):
                reuse(ops, (*signature[:4], bad, *signature[5:]),
                    lambda base: self.fail("A malformed warm law reached its builder"), context=context)
        for kwargs in ({"context": "old"}, {"path": ""}, {"max_steps": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ReachAdmissionError):
                reuse(ops, signature,
                    lambda base: self.fail("A malformed warm cursor reached its builder"), **kwargs)

    def test_native_cache_callbacks_recheck_caps_and_preserve_failure_identity(self):
        parent = _FloatPose((0.25, 0.5, 0.0), _FloatRotation(1.0, 0.0, False, True),
                            (False, False, True), 1)
        local = Pose(position=(1.0, 0.0, 0.0))
        for final in ("cache_promote", "cache_insert", "cache_evict"):
            for narrow in (False, True):
                with self.subTest(final=final, narrow=narrow):
                    ops = native(cache=1 if final == "cache_evict" else 256)
                    signature = (parent, local)
                    build = lambda base: follow(ops, base, local)
                    if final == "cache_promote":
                        reuse(ops, signature, build)
                    elif final == "cache_evict":
                        ops.work.remember(("occupied",), object())
                    marker = ReachAdmissionError("reach_resource", "original callback rejection")
                    snapshots, armed = [], []
                    lookup, remember, charge = ops.work.lookup, ops.work.remember, ops.work.charge
                    def before(key, call, *args, **kwargs):
                        if len(key) > 1 and key[1] == "native_relative_pose":
                            snapshots.append(tuple(ops.work._cache.items()))
                            armed.append(True)
                        return call(key, *args, **kwargs)
                    def charged(kind="checkpoint", amount=1):
                        if armed and kind == final:
                            def reject():
                                ops.work.max_operand_bits = 128
                                if not narrow:
                                    raise marker
                            ops.work.external_check = reject
                        return charge(kind, amount)
                    look = (lambda key: before(key, lookup)) if final == "cache_promote" else lookup
                    save = (lambda key, value, **kwargs: before(key, remember, value, **kwargs))
                    with patch.object(ops.work, "lookup", side_effect=look), \
                            patch.object(ops.work, "remember", side_effect=save), \
                            patch.object(ops.work, "charge", side_effect=charged):
                        with self.assertRaises(_UnsupportedPlanar if narrow else ReachAdmissionError) as caught:
                            reuse(ops, signature, build)
                    self.assertTrue(snapshots)
                    if narrow:
                        self.assertFalse(any(len(key) > 1 and key[1] == "native_relative_pose"
                                             for key in ops.work._cache))
                    else:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(ops.work.callback_error, marker)
                        self.assertEqual(tuple(ops.work._cache.items()), snapshots[-1])

    def test_relative_results_use_only_the_existing_bounded_lru(self):
        ops = native(cache=4)
        parent = _FloatPose((0.25, 0.5, 0.0), _FloatRotation(1.0, 0.0, False, True),
                            (False, False, True), 1)
        results = []
        for index in range(20):
            local = Pose(position=(float(index), 0.0, 0.0))
            results.append(reuse(ops, (parent, local), lambda base: follow(ops, base, local)))
            self.assertLessEqual(len(ops.work._cache), 4)
        first = Pose()
        with patch.object(ops, "compose_recording_fast", wraps=ops.compose_recording_fast) as built:
            replay = reuse(ops, (parent, first), lambda base: follow(ops, base, first))
        self.assertEqual(bits(replay), bits(results[0]))
        self.assertTrue(built.called)
        self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))

    def test_actual_translated_arms_keep_frames_enclosures_and_all_source_admissions(self):
        histories = []
        for enabled in (False, True):
            sim, paths, phase = prepared_many()
            original, context = deepcopy(sim.state), object()
            before, counts = sim.work.operations, dict(sim.work.counts)
            mode = nullcontext() if enabled else patch.object(
                Binary64RecordingOps, "recording_relative_pose", return_value=None)
            with mode:
                frames = [sample(sim, paths, phase, time=time, context=context)
                          for time in (F(1, 8), F(1, 4), F(3, 8))]
            admissions = tuple(sim.work.counts.get(kind, 0) - counts.get(kind, 0) for kind in
                ("recording_body_witness", "recording_angular_witness_guard",
                 "recording_body_shared_orientation"))
            histories.append((frames, sim.work.operations - before, admissions))
            self.assertEqual(sim.state, original)
            self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(histories[0][0], histories[1][0])
        self.assertLess(histories[1][1], histories[0][1])
        self.assertEqual(histories[0][2], histories[1][2])


if __name__ == "__main__":
    unittest.main()
