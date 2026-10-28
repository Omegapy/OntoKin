"""Direct immutable source leaves keep the original native transform bits."""
from contextlib import nullcontext
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import Binary64RecordingOps, _UnsupportedPlanar
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def native():
    return Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))


def build(ops):
    return lambda pose, inverse=False: (ops.source_ops.inverse_pose(pose) if inverse
                                       else ops.source_ops.constant_pose(pose))


def leaf(position=(0.0, 0.0, 0.0), rotation=(1.0, 0.0, 0.0, 0.0)):
    return SimpleNamespace(position=position, rotation=rotation)


def bits(value):
    return (tuple(float_bits(v) for v in value.position),
            tuple(float_bits(v) for v in value.orientation), value.zeros, value.depth,
            value.rotation.zero_w, value.rotation.zero_z)


class ReachRecordingIdentityLeavesTests(unittest.TestCase):
    def test_original_finite_binary64_positions_keep_all_native_bits_without_cache_work(self):
        points = ((0.0, -0.0, 0.0), (.1, -.2, .3),
                  (float.fromhex('0x0.0000000000001p-1022'), -1e-300, -0.0),
                  (float(2**500), -float(2**500), float.fromhex('0x1.fffffffffffffp+499')))
        for position in points:
            with self.subTest(position=position):
                old, current = native(), native()
                pose = leaf(position, (1.0, -0.0, 0.0, -0.0))
                with patch.object(old, '_direct_identity_source_leaf', return_value=None):
                    expected = old.recording_constant_pose(pose, build=build(old))
                    before = old.work.operations
                    self.assertEqual(bits(old.recording_constant_pose(pose, build=build(old))), bits(expected))
                    hot = old.work.operations - before
                for _ in range(3):
                    before = current.work.operations
                    with patch.object(current.work, 'lookup', side_effect=AssertionError('no cached calculation')), \
                            patch.object(current.work, 'remember', side_effect=AssertionError('no cache publication')):
                        actual = current.recording_constant_pose(pose, build=lambda *a, **k: self.fail('no source reconstruction'))
                    self.assertEqual(bits(actual), bits(expected))
                    self.assertEqual(current.work.operations - before, 1)
                    self.assertLess(current.work.operations - before, hot)
                self.assertFalse(current.work._cache)
                self.assertEqual(current.work.operations, sum(current.work.counts.values()))

    def test_inverse_of_a_literal_identity_keeps_the_original_canonical_zero_bits(self):
        pose = leaf((-0.0, 0.0, -0.0), (1.0, -0.0, -0.0, 0.0))
        old, current = native(), native()
        with patch.object(old, '_direct_identity_source_leaf', return_value=None):
            expected = old.recording_constant_pose(pose, inverse=True, build=build(old))
        actual = current.recording_constant_pose(pose, inverse=True, build=build(current))
        self.assertEqual(bits(actual), bits(expected))
        self.assertEqual(tuple(float_bits(v) for v in actual.position), (0, 0, 0))
        self.assertEqual(current.work.operations, 1)
        self.assertFalse(current.work._cache)

    def test_other_inverse_rotations_and_operand_types_retain_original_source_calculation(self):
        inputs = ((leaf((.1, .2, .3)), True),
                  (leaf(rotation=(-1.0, 0.0, 0.0, 0.0)), False),
                  (leaf(rotation=(1.0, 0.0, 0.0, .25)), False),
                  (leaf((F(1, 3), F(0), F(0))), False),
                  (leaf((1, 0, 0)), False),
                  (leaf(rotation=(F(1), F(0), F(0), F(0))), False))
        for pose, inverse in inputs:
            with self.subTest(pose=pose, inverse=inverse):
                old, current = native(), native()
                with patch.object(old, '_direct_identity_source_leaf', return_value=None):
                    expected = old.recording_constant_pose(pose, inverse=inverse, build=build(old))
                with patch.object(current, '_pose', wraps=current._pose) as projected:
                    actual = current.recording_constant_pose(pose, inverse=inverse, build=build(current))
                self.assertEqual(projected.call_count, 1)
                self.assertEqual(bits(actual), bits(expected))
                self.assertEqual(current.work.counts, old.work.counts)

    def test_malformed_and_out_of_range_values_keep_original_failure_and_cache(self):
        inputs = (leaf([0.0, 0.0, 0.0]), leaf((False, 0.0, 0.0)),
                  leaf((math.inf, 0.0, 0.0)), leaf((math.nan, 0.0, 0.0)),
                  leaf((float(2**501), 0.0, 0.0)),
                  leaf(rotation=(0.0, 0.0, 0.0, 0.0)))
        for pose in inputs:
            outcomes = []
            for direct in (False, True):
                ops = native()
                mode = nullcontext() if direct else patch.object(ops, '_direct_identity_source_leaf', return_value=None)
                with mode, self.assertRaises(Exception) as caught:
                    ops.recording_constant_pose(pose, build=build(ops))
                error = caught.exception
                outcomes.append((type(error), str(error), getattr(error, 'details', None)))
            with self.subTest(pose=pose):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_first_checkpoint_keeps_cancellation_identity_current_cap_and_existing_cache(self):
        for narrow in (False, True):
            with self.subTest(narrow=narrow):
                ops = native()
                ops.work.remember(('previous',), object())
                before = tuple(ops.work._cache.items())
                marker = RuntimeError('cancel direct native source leaf')
                def check():
                    if narrow:
                        ops.work.max_operand_bits = 128
                    else:
                        raise marker
                ops.work.external_check = check
                with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                    ops.recording_constant_pose(leaf(), build=build(ops))
                if not narrow:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.work.callback_error, marker)
                self.assertEqual(tuple(ops.work._cache.items()), before)

    def test_callback_changed_source_is_read_after_the_domain_checkpoint(self):
        ops, pose = native(), leaf()
        position = (.25, -.5, .75)
        def changed():
            pose.position = position
        ops.work.external_check = changed
        actual = ops.recording_constant_pose(pose, build=build(ops))
        self.assertEqual(actual.position, position)
        self.assertEqual(actual.zeros, (False, False, False))
        self.assertFalse(ops.work._cache)

    def test_direct_projection_keeps_the_shared_operation_limit(self):
        ops = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork(max_operations=1)))
        ops.recording_constant_pose(leaf(), build=build(ops))
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.recording_constant_pose(leaf(), build=build(ops))
        self.assertEqual(caught.exception.details, {
            'reach_code': 'reach_resource', 'budget': 'max_operations', 'limit': 1, 'consumed': 2})
        self.assertEqual(ops.work.operations, 1)
        self.assertFalse(ops.work._cache)

    def test_actual_glb_bytes_and_independent_acceptance_match_with_less_shared_work(self):
        for case, end in (('P01', F(3)), ('P16', F(1, 2))):
            outcomes = []
            for direct in (False, True):
                built = compile_construction(source_case(case), level='constructed')
                mode = nullcontext() if direct else patch.object(
                    Binary64RecordingOps, '_direct_identity_source_leaf', return_value=None)
                with mode:
                    artifact = export_glb(built.model, options=ExportOptions(end=end, fps=1),
                        target_contract='ontokin.glb/0.6', work=built.reach_work)
                outcomes.append((artifact.data, artifact.report['validation'], built.budget.operations))
                self.assertLessEqual(built.budget.operations, 100000)
                self.assertLessEqual(len(built.reach_work._cache), 256)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])


if __name__ == '__main__':
    unittest.main()
