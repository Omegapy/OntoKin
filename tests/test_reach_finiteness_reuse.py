"""Completed per-pose proofs preserve full field admission and public bits."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.model import Pose
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps, RotationValue
from test_reach_phase_mounts import PlanningSimulator
from test_reach_projection_finiteness import private_pose
from test_reach_source_translation import numerical_simulator, slot
from reach_agent_support import source_case


class ReachFinitenessReuseTests(unittest.TestCase):
    def setUp(self):
        # Exercise the retained individual-field receipt layer. The complete
        # current-signature path has its own boundary/callback tests and would
        # otherwise remove the field checkpoints under inspection here.
        self.enterContext(patch.object(ReachPoseOps, "_complete_finite_signature", return_value=False))

    def test_completed_proof_reuses_one_charged_checkpoint_without_public_tuples(self):
        work=ReachExecutionWork()
        ops=ReachPoseOps(work)
        pose=private_pose(ops,position=(F(1,3),F(2,7),F(0)),
                          quaternion=(F(1),F(2),F(3),F(4)))
        with patch.object(ops,"_expose",side_effect=AssertionError("public allocation")):
            ops.ensure_finite(pose)
            completed=pose._finite_proof
            first=work.operations
            ops.ensure_finite(pose)
        self.assertEqual(work.operations-first,1)
        self.assertEqual(work.counts["pose_finiteness_field"],4)
        self.assertEqual(pose._projection,{})
        self.assertEqual(len(work._cache),0)
        self.assertEqual(pose,replace(pose))
        self.assertIsNone(replace(pose)._finite_proof)
        self.assertIs(copy.deepcopy(pose),pose)
        self.assertEqual(pose._finite_proof,completed)

    def test_source_translation_carries_only_completed_unchanged_field_proofs(self):
        sim=numerical_simulator()
        parent=sim.pose_ops.make()
        local=Pose(position=(0.25,0.5,0.0))
        first=slot(sim,("follow",parent,local))
        sim.pose_ops.ensure_finite(first)
        shifted=replace(parent,exact_position=(F(2),F(3),F(4)),_projection={})
        second=slot(sim,("follow",shifted,local),"second")
        self.assertIs(second._finite_proof,first._finite_proof)
        before=sim.work.counts["pose_finiteness_field"]
        with patch.object(sim.pose_ops,"_expose",side_effect=AssertionError("public allocation")):
            sim.pose_ops.ensure_finite(second)
        self.assertEqual(sim.work.counts["pose_finiteness_field"]-before,1)
        self.assertNotEqual(first.exact_position,second.exact_position)
        self.assertEqual(first._projection,{})
        self.assertEqual(second._projection,{})
        self.assertLessEqual(len(sim.work._cache),256)

    def test_each_changed_field_is_checked_and_failed_proof_does_not_publish(self):
        for name in ("exact_position","exact_velocity","exact_omega","rotation"):
            with self.subTest(field=name):
                ops=ReachPoseOps(ReachExecutionWork())
                original=private_pose(ops)
                ops.ensure_finite(original)
                invalid=(RotationValue((F(0),)*4) if name=="rotation" else
                         (F(1<<1024),F(0),F(0)))
                changed=replace(original,**{name:invalid},_projection={})
                ops._carry_finite_proof(original,changed)
                previous=changed._finite_proof
                with self.assertRaises((ReachAdmissionError,ZeroDivisionError)):
                    ops.ensure_finite(changed)
                self.assertIs(changed._finite_proof,previous)
                self.assertEqual(original._projection,{})

    def test_hot_cancellation_and_late_cap_narrowing_replay_prior_fields(self):
        ops=ReachPoseOps(ReachExecutionWork())
        original=private_pose(ops,position=(F(1<<200),F(0),F(0)))
        ops.ensure_finite(original)
        previous=original._finite_proof
        marker=RuntimeError("cancel completed finite proof")
        with patch.object(ops.work,"external_check",side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.ensure_finite(original)
        self.assertIs(caught.exception,marker)
        self.assertIs(ops.work.callback_error,marker)
        self.assertIs(original._finite_proof,previous)
        changed=replace(original,exact_velocity=(F(1),F(0),F(0)),_projection={})
        ops._carry_finite_proof(original,changed)
        charge=ops.work.charge

        def narrow(kind="checkpoint",amount=1):
            if kind=="pose_finiteness_field":
                ops.work.max_operand_bits=128
            charge(kind,amount)

        with patch.object(ops.work,"charge",narrow):
            with self.assertRaises(ReachAdmissionError) as caught:
                ops.ensure_finite(changed)
        self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")
        self.assertEqual(caught.exception.details["limit"],128)
        self.assertIs(changed._finite_proof,previous)
        self.assertNotIn("position",changed._projection)

    def test_changed_rotation_identity_does_not_compare_unused_error_fractions(self):
        ops=ReachPoseOps(ReachExecutionWork())
        original=private_pose(ops)
        ops.ensure_finite(original)
        # Projection finiteness never consumes the separately carried angle
        # allowance. A changed immutable rotation must recheck its components
        # without introducing an unguarded rational equality on that allowance.
        changed=replace(original,rotation=RotationValue(
            original.rotation.components,F(1<<40000)),_projection={})
        ops._carry_finite_proof(original,changed)
        before=ops.work.counts["pose_finiteness_field"]
        with patch.object(F,"__eq__",side_effect=AssertionError("unneeded exact equality")):
            ops.ensure_finite(changed)
        self.assertEqual(ops.work.counts["pose_finiteness_field"]-before,1)
        self.assertIs(changed._finite_proof.fields[1],changed.rotation)
        self.assertEqual(changed._projection,{})

    def test_existing_public_tuple_is_never_promoted_to_private_field_proof(self):
        ops=ReachPoseOps(ReachExecutionWork())
        pose=private_pose(ops,position=(F(1<<1024),F(0),F(0)))
        pose._projection["position"]=(0.0,0.0,0.0)
        ops.ensure_finite(pose)
        self.assertIsNone(pose._finite_proof.fields[0])
        ops.ensure_finite(pose)
        pose._projection.clear()
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.ensure_finite(pose)
        self.assertEqual(caught.exception.reach_code,"reach_numeric")

    def test_malformed_and_reentrant_memos_take_original_four_field_path(self):
        ops=ReachPoseOps(ReachExecutionWork())
        pose=private_pose(ops)
        object.__setattr__(pose,"_finite_proof",("not", "a", "proof"))
        ops.ensure_finite(pose)
        self.assertEqual(ops.work.counts["pose_finiteness_field"],4)
        self.assertEqual(pose._finite_proof,("not", "a", "proof"))
        object.__setattr__(pose,"_finite_proof",None)
        ops.ensure_finite(pose)
        before=ops.work.counts["pose_finiteness_field"]
        entered=False

        def reenter_once():
            nonlocal entered
            if not entered:
                entered=True
                ops.ensure_finite(pose)

        with patch.object(ops.work,"external_check",reenter_once):
            ops.ensure_finite(pose)
        self.assertTrue(entered)
        self.assertEqual(ops.work.counts["pose_finiteness_field"]-before,4)
        self.assertEqual(pose._projection,{})

    def test_mutable_private_vectors_never_supply_a_retained_field_proof(self):
        ops=ReachPoseOps(ReachExecutionWork())
        velocity=[F(0),F(0),F(0)]
        pose=private_pose(ops,velocity=velocity)
        ops.ensure_finite(pose)
        self.assertIsNone(pose._finite_proof.fields[2])
        velocity[0]=F(1<<MAX_OPERAND_BITS)
        pose._projection.clear()
        with self.assertRaises(ReachAdmissionError):
            ops.ensure_finite(pose)

    def test_complete_p23_boundaries_and_final_state_match_original_field_checks(self):
        results=[]
        costs=[]
        for reuse in (True,False):
            built=compile_construction(source_case("P23"))
            sim=PlanningSimulator(built.model,work=built.reach_work)

            def observe():
                records=[]
                for time in (0,2,3):
                    for side in ("before","after"):
                        sim.advance(F(time),side)
                        records.append(sim.recording_boundary(F(time),side))
                return records,copy.deepcopy(sim.state)

            if reuse:
                results.append(observe())
            else:
                with patch.object(sim.pose_ops,"ensure_finite",sim.pose_ops._ensure_finite_fields):
                    results.append(observe())
            costs.append(built.budget.operations)
            self.assertLessEqual(built.budget.operations,100000)
            self.assertEqual(sim.work.max_operand_bits,MAX_OPERAND_BITS)
            self.assertLessEqual(len(sim.work._cache),256)
        self.assertEqual(results[0],results[1])
        self.assertGreater(costs[1]-costs[0],1500)


if __name__=="__main__":
    unittest.main()
