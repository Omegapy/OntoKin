"""A complete current small-domain proof needs no duplicate field predicates."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_export import reach_prefix_plan
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork as Work, float_bits
from ontokin.reach_pose import ReachPoseOps, RotationValue
from reach_agent_support import source_case
from test_reach_projection_finiteness import private_pose, expose


class CompleteFinitenessTests(unittest.TestCase):
    def test_all_current_fields_prove_the_original_domain_in_one_checkpoint(self):
        largest = (1 << 512) - 1
        ops = ReachPoseOps(Work(max_cache_entries=1))
        pose = private_pose(ops, position=(F(largest), F(-1, largest), F(0)),
            quaternion=(F(largest, largest - 2), F(-1, largest - 4), F(largest - 6, 3), F(7, largest - 8)),
            velocity=(F(1, 3), F(-2, 7), F(5, 11)), omega=(F(0), F(largest, 13), F(-17, largest)))
        with patch.object(ops, '_ensure_finite_field', side_effect=AssertionError('duplicate field predicate')), \
                patch.object(ops, '_expose', side_effect=AssertionError('unused public projection')):
            ops.ensure_finite(pose)
        self.assertEqual(ops.work.operations, 1)
        self.assertEqual(ops.work.counts, {'pose_finiteness_proof': 1})
        self.assertEqual(pose._projection, {})
        self.assertFalse(ops.work._cache)
        self.assertTrue(all(value is not None for value in pose._finite_proof.fields))
        reference = ReachPoseOps(Work())
        original = replace(pose, _ops=reference, _projection={}, _projection_domains={})
        with patch.object(reference, '_complete_finite_signature', return_value=False):
            reference.ensure_finite(original)
        actual, expected = expose(ops, pose), expose(reference, original)
        self.assertEqual([[float_bits(value) for value in row] for row in actual],
                         [[float_bits(value) for value in row] for row in expected])
        self.assertTrue(all(math.isfinite(value) for row in actual for value in row))

    def test_changed_small_payloads_bind_the_current_exact_objects_without_rational_equality(self):
        ops = ReachPoseOps(Work())
        pose = private_pose(ops)
        ops.ensure_finite(pose)
        changed = replace(pose, exact_position=(F(3), F(-5), F(7)),
                          rotation=RotationValue(pose.rotation.components, F(1 << 40000)))
        ops._carry_finite_proof(pose, changed)
        before = ops.work.operations
        with patch.object(F, '__eq__', side_effect=AssertionError('unused fraction equality')):
            ops.ensure_finite(changed)
        self.assertEqual(ops.work.operations - before, 1)
        self.assertIs(changed._finite_proof.fields[0], changed.exact_position)
        self.assertIs(changed._finite_proof.fields[1], changed.rotation)
        self.assertEqual(changed._projection, {})

    def test_invalid_or_unproved_field_preserves_the_original_order_and_failure(self):
        for fields in (
            {'position': (F(1 << 1024), F(0), F(0)), 'quaternion': (F(0),) * 4},
            {'quaternion': (F(0),) * 4},
            {'velocity': (F(1 << MAX_OPERAND_BITS), F(0), F(0))},
            {'omega': (True, F(0), F(0))},
        ):
            outcomes = []
            for whole in (False, True):
                ops = ReachPoseOps(Work())
                pose = private_pose(ops, **fields)
                mode = patch.object(ops, '_complete_finite_signature', return_value=False) if not whole else \
                    patch.object(ops, '_complete_finite_signature', wraps=ops._complete_finite_signature)
                try:
                    with mode:
                        ops.ensure_finite(pose)
                    outcomes.append(('passed', expose(ops, pose)))
                except Exception as error:
                    outcomes.append((type(error), str(error), getattr(error, 'details', None)))
            with self.subTest(fields=tuple(fields)):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_callback_narrowing_uses_original_current_domain_and_preserves_prior_proof(self):
        ops = ReachPoseOps(Work())
        pose = private_pose(ops, position=(F(1 << 200), F(0), F(0)))
        ops.ensure_finite(pose)
        previous = pose._finite_proof
        with patch.object(ops.work, 'external_check', side_effect=lambda: setattr(ops.work, 'max_operand_bits', 128)), \
                self.assertRaises(ReachAdmissionError) as actual:
            ops.ensure_finite(pose)
        plain = ReachPoseOps(Work(max_operand_bits=128))
        with self.assertRaises(ReachAdmissionError) as expected:
            plain._ensure_finite_fields(private_pose(plain, position=pose.exact_position))
        self.assertEqual(actual.exception.details, expected.exception.details)
        self.assertIs(pose._finite_proof, previous)

    def test_513_bit_frozen_mutable_and_invalid_receipts_keep_the_retained_field_path(self):
        for variant in ('513_bits', 'frozen', 'mutable', 'memo', 'family'):
            ops = ReachPoseOps(Work())
            pose = private_pose(ops)
            if variant == '513_bits':
                pose = replace(pose, exact_position=(F(1 << 512), F(0), F(0)))
            elif variant == 'frozen':
                pose = replace(pose, rotation=replace(pose.rotation, frozen_projection=(1., -0., 0., -0.)))
            elif variant == 'mutable':
                pose = replace(pose, exact_velocity=[F(0), F(0), F(0)])
            elif variant == 'memo':
                object.__setattr__(pose, '_finite_proof', object())
            else:
                object.__setattr__(pose, '_finite_family', object())
            with self.subTest(variant=variant), patch.object(ops, '_ensure_finite_field', wraps=ops._ensure_finite_field) as field:
                ops.ensure_finite(pose)
            self.assertEqual([call.args[1] for call in field.call_args_list],
                             ['position', 'orientation', 'velocity', 'omega'])
            self.assertEqual(ops.work.max_operand_bits, MAX_OPERAND_BITS)

    def test_actual_payloads_are_read_after_the_callback_and_invalid_changes_are_rejected(self):
        ops = ReachPoseOps(Work())
        pose = private_pose(ops)
        old_velocity = pose.exact_velocity
        def change():
            object.__setattr__(pose, 'exact_velocity', (F(1 << 1024), F(0), F(0)))
            ops.work.external_check = None
        with patch.object(ops.work, 'external_check', side_effect=change), self.assertRaises(ReachAdmissionError):
            ops.ensure_finite(pose)
        self.assertIsNone(pose._finite_proof)
        object.__setattr__(pose, 'exact_velocity', old_velocity)

    def test_cancellation_preserves_completed_own_and_shared_receipts(self):
        ops = ReachPoseOps(Work())
        first = private_pose(ops)
        second = replace(first, exact_position=(F(1), F(0), F(0)))
        ops._carry_finite_proof(first, second)
        ops.ensure_finite(first)
        previous = first._finite_family.proof
        marker = RuntimeError('cancel complete small-pose proof')
        with patch.object(ops.work, 'external_check', side_effect=marker), self.assertRaises(RuntimeError) as caught:
            ops.ensure_finite(second)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.work.callback_error, marker)
        self.assertIs(first._finite_family.proof, previous)
        self.assertIsNone(second._finite_proof)
        self.assertEqual(second._projection, {})
        self.assertFalse(ops.work._cache)

    def test_complete_p23_plan_preserves_every_boundary_and_phase_with_less_work(self):
        outcomes, costs = [], []
        for whole in (False, True):
            built = compile_construction(source_case('P23'))
            mode = patch.object(ReachPoseOps, '_complete_finite_signature', return_value=False) if not whole else \
                patch.object(ReachPoseOps, '_complete_finite_signature', wraps=ReachPoseOps._complete_finite_signature)
            with mode:
                plan = reach_prefix_plan(built.model, F(3), work=built.reach_work)
            outcomes.append((plan.boundaries, plan.boundary_records, copy.deepcopy(plan.final_state),
                             tuple((phase.start, phase.end, phase.carriers, phase.source) for phase in plan.phases)))
            costs.append(built.budget.operations)
            self.assertLessEqual(built.budget.operations, 100000)
            self.assertLessEqual(len(built.reach_work._cache), 256)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertLess(costs[1], costs[0])


if __name__ == '__main__':
    unittest.main()
