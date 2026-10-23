"""Retained complete graph admission never substitutes for changed operands."""
import copy
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_export import reach_prefix_plan
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_finite import _RecordingGraphFiniteness
from reach_agent_support import source_case
from test_reach_projection_finiteness import private_pose


def graph(*, check=None, count=24, position=None):
    work = ReachExecutionWork(check=check)
    ops = ReachPoseOps(work)
    root = private_pose(ops)
    poses = {"object": root}
    frames = {"world": private_pose(ops), "object.frame": root}
    for index in range(count):
        frames[f"site{index}.frame"] = private_pose(ops,
            position=position if position is not None else (F(index + 1, 19), F(0), F(0)))
    owner = SimpleNamespace(work=work, pose_ops=ops, state=object(), check=None,
                            _recording_graph_finiteness=None)
    for pose in frames.values():
        ops.ensure_finite(pose)
    candidate = _RecordingGraphFiniteness.begin(owner, poses, frames)
    for path, pose in frames.items():
        candidate.append(path, pose)
    receipt = candidate.complete()
    owner._recording_graph_finiteness = receipt
    return owner, poses, frames, receipt


class RecordingGraphFinitenessTests(unittest.TestCase):
    def test_unchanged_graph_reuses_complete_proofs_without_projection_or_numeric_cache(self):
        owner, poses, frames, receipt = graph()
        self.assertIsNotNone(receipt)
        before = owner.work.operations
        with patch.object(owner.pose_ops, 'ensure_finite', side_effect=AssertionError('duplicate proof')), \
                patch.object(owner.pose_ops, '_expose', side_effect=AssertionError('unused projection')):
            self.assertTrue(receipt.matches(owner, poses, frames))
        self.assertLess(owner.work.operations - before, len(frames))
        self.assertFalse(owner.work._cache)
        self.assertTrue(all(pose._projection == {} for pose in frames.values()))
        self.assertEqual(owner.work.max_operations, 100000)

    def test_every_changed_private_field_rejects_the_old_graph(self):
        variants = (
            ('exact_position', (F(3), F(5), F(7))),
            ('exact_velocity', (F(11), F(0), F(0))),
            ('exact_omega', (F(0), F(13), F(0))),
            ('position_error_m', F(17)),
        )
        for field, value in variants:
            owner, poses, frames, receipt = graph()
            object.__setattr__(frames['site0.frame'], field, value)
            with self.subTest(field=field):
                self.assertFalse(receipt.matches(owner, poses, frames))
        for field, value in (('components', (F(0), F(1), F(0), F(0))),
                             ('error_rad', F(19)),
                             ('frozen_projection', (1., 0., 0., 0.))):
            owner, poses, frames, receipt = graph()
            object.__setattr__(frames['site0.frame'].rotation, field, value)
            with self.subTest(rotation_field=field):
                self.assertFalse(receipt.matches(owner, poses, frames))

    def test_integer_fingerprint_detects_in_place_fraction_mutation(self):
        owner, poses, frames, receipt = graph()
        value = frames['site0.frame'].exact_position[0]
        saved = value.numerator
        try:
            object.__setattr__(value, '_numerator', saved + 1)
            self.assertFalse(receipt.matches(owner, poses, frames))
        finally:
            object.__setattr__(value, '_numerator', saved)

    def test_complete_map_identity_order_and_alias_relations_are_required(self):
        for change in ('new_frames', 'new_poses', 'order', 'alias', 'added', 'replacement'):
            owner, poses, frames, receipt = graph()
            if change == 'new_frames':
                frames = dict(frames)
            elif change == 'new_poses':
                poses = dict(poses)
            elif change == 'order':
                value = frames.pop('world')
                frames['world'] = value
            elif change == 'alias':
                poses['object'] = private_pose(owner.pose_ops)
            elif change == 'added':
                frames['unselected.frame'] = private_pose(owner.pose_ops)
            else:
                frames['site0.frame'] = replace(frames['site0.frame'])
            with self.subTest(change=change):
                self.assertFalse(receipt.matches(owner, poses, frames))

    def test_changed_owners_state_callbacks_and_live_domain_cannot_borrow_receipt(self):
        for change in ('owner', 'state', 'work', 'ops', 'check', 'external', 'cap'):
            owner, poses, frames, receipt = graph()
            if change == 'owner':
                owner = SimpleNamespace(**vars(owner))
            elif change == 'state':
                owner.state = object()
            elif change == 'work':
                owner.work = ReachExecutionWork()
            elif change == 'ops':
                owner.pose_ops = ReachPoseOps(owner.work)
            elif change == 'check':
                owner.check = lambda: None
            elif change == 'external':
                owner.work.external_check = lambda: None
            else:
                owner.work.max_operand_bits = MAX_OPERAND_BITS - 1
            with self.subTest(change=change):
                self.assertFalse(receipt.matches(owner, poses, frames))

    def test_first_and_final_admission_callbacks_cannot_hide_changed_earlier_fields(self):
        for target in (1, 4):
            calls = 0
            armed = False
            def check():
                nonlocal calls
                if armed:
                    calls += 1
                    if calls == target:
                        object.__setattr__(frames['world'].rotation, 'error_rad', F(23))
            owner, poses, frames, receipt = graph(check=check)
            armed = True
            with self.subTest(callback=target):
                self.assertFalse(receipt.matches(owner, poses, frames))
                self.assertEqual(calls, 4)

    def test_transient_narrowing_leaves_receipt_before_a_later_restoration_callback(self):
        calls = 0
        armed = False
        def check():
            nonlocal calls
            if armed:
                calls += 1
                owner.work.max_operand_bits = 128 if calls == 1 else MAX_OPERAND_BITS
        owner, poses, frames, receipt = graph(check=check, position=(F(1 << 200), F(0), F(0)))
        armed = True
        self.assertFalse(receipt.matches(owner, poses, frames))
        self.assertEqual(calls, 1)
        self.assertEqual(owner.work.max_operand_bits, 128)
        armed = False
        with self.assertRaises(ReachAdmissionError) as caught:
            owner.pose_ops.ensure_finite(frames['site0.frame'])
        self.assertEqual(caught.exception.details['budget'], 'numeric_operand_bits')

    def test_callback_cancellation_and_resource_errors_preserve_original_identity(self):
        for marker in (RuntimeError('cancel graph admission'),
                       ReachAdmissionError('reach_resource', 'original callback failure',
                                           budget='numeric_operand_bits', limit=128, consumed=201)):
            armed = False
            def check():
                if armed:
                    raise marker
            owner, poses, frames, receipt = graph(check=check)
            armed = True
            with self.subTest(error=type(marker).__name__), self.assertRaises(type(marker)) as caught:
                receipt.matches(owner, poses, frames)
            self.assertIs(caught.exception, marker)
            self.assertIs(owner.work.callback_error, marker)
            self.assertFalse(receipt.active)

    def test_actual_operation_limit_is_checked_on_every_reuse(self):
        owner, poses, frames, receipt = graph()
        owner.work.max_operations = owner.work.operations
        with self.assertRaises(ReachAdmissionError) as caught:
            receipt.matches(owner, poses, frames)
        self.assertEqual(caught.exception.details['budget'], 'max_operations')
        self.assertFalse(receipt.active)

    def test_reentrant_receipt_replacement_cannot_publish_the_old_admission(self):
        armed = False
        def check():
            nonlocal armed
            if armed:
                armed = False
                self.assertFalse(receipt.matches(owner, poses, frames))
                owner._recording_graph_finiteness = object()
        owner, poses, frames, receipt = graph(check=check)
        armed = True
        self.assertFalse(receipt.matches(owner, poses, frames))

    def test_cold_capture_rechecks_an_earlier_row_after_later_callbacks(self):
        owner, poses, frames, receipt = graph()
        candidate = _RecordingGraphFiniteness.begin(owner, poses, frames)
        for index, (path, pose) in enumerate(frames.items()):
            candidate.append(path, pose)
            if index == 3:
                object.__setattr__(frames['world'].rotation, 'error_rad', F(29))
        self.assertIsNone(candidate.complete())

    def test_unsupported_families_memos_and_shapes_keep_the_original_path(self):
        for change in ('family', 'memo', 'foreign_ops', 'projection', 'incomplete', 'wide'):
            owner, poses, frames, receipt = graph()
            pose = frames['site0.frame']
            if change == 'family':
                owner.pose_ops._carry_finite_proof(pose, replace(pose))
            elif change == 'memo':
                object.__setattr__(pose, '_finite_proof', object())
            elif change == 'foreign_ops':
                object.__setattr__(pose, '_ops', ReachPoseOps(owner.work))
            elif change == 'projection':
                object.__setattr__(pose, '_projection', [])
            elif change == 'incomplete':
                object.__setattr__(pose, '_finite_proof', replace(pose._finite_proof, fields=(None,) * 4))
            else:
                object.__setattr__(pose, 'exact_position', (F(1 << 512), F(0), F(0)))
            with self.subTest(change=change):
                self.assertFalse(receipt.matches(owner, poses, frames))
                candidate = _RecordingGraphFiniteness.begin(owner, poses, frames)
                for path, current in frames.items():
                    candidate.append(path, current)
                self.assertIsNone(candidate.complete())
        owner, poses, frames, _ = graph()
        self.assertIsNone(_RecordingGraphFiniteness.begin(owner, poses,
            {str(index): frames['world'] for index in range(4097)}))

    def test_full_p23_plan_preserves_every_boundary_and_phase_with_bounded_savings(self):
        outcomes, costs, guards = [], [], []
        for enabled in (False, True):
            built = compile_construction(source_case('P23'))
            mode = (patch.object(_RecordingGraphFiniteness, 'begin', return_value=None) if not enabled else
                    patch.object(_RecordingGraphFiniteness, 'begin', wraps=_RecordingGraphFiniteness.begin))
            with mode:
                plan = reach_prefix_plan(built.model, F(3), work=built.reach_work)
            outcomes.append((plan.boundaries, plan.boundary_records, copy.deepcopy(plan.final_state),
                tuple((phase.start, phase.end, phase.carriers, phase.source, phase.recording_angular_proof)
                      for phase in plan.phases)))
            costs.append(built.budget.operations)
            guards.append(built.reach_work.counts.get('recording_graph_finiteness_guard', 0))
            self.assertLessEqual(built.budget.operations, 100000)
            self.assertLessEqual(len(built.reach_work._cache), 256)
            self.assertEqual(built.reach_work.max_operations, 100000)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertGreaterEqual(costs[0] - costs[1], 1000)
        self.assertEqual(guards[0], 0)
        self.assertGreater(guards[1], 0)


if __name__ == '__main__':
    unittest.main()
