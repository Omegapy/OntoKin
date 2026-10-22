"""Already-built translated sites share only a completed immutable proof."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.model import Pose
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import PoseValue, ReachPoseOps
from test_reach_phase_mounts import PlanningSimulator
from test_reach_projection_finiteness import private_pose
from test_reach_source_translation import numerical_simulator, slot
from reach_agent_support import source_case


class ReachFinitenessFamilyTests(unittest.TestCase):
    def test_sites_built_before_the_first_check_share_only_unchanged_field_proofs(self):
        sim=numerical_simulator()
        initial=sim.pose_ops.make()
        local=Pose(position=(0.25,0.5,0.0))
        poses=[]
        for index in range(32):
            parent=replace(initial,exact_position=(F(index),F(0),F(0)),_projection={})
            poses.append(slot(sim,("follow",parent,local),"site_"+str(index)))
        self.assertTrue(all(pose._finite_proof is None for pose in poses))
        self.assertTrue(all(pose._finite_family is poses[0]._finite_family for pose in poses))
        self.assertIsNone(poses[0]._finite_family.proof)
        before=sim.work.operations
        with patch.object(sim.pose_ops,"_expose",side_effect=AssertionError("public tuple allocation")):
            for pose in poses:
                sim.pose_ops.ensure_finite(pose)
        self.assertEqual(sim.work.counts["pose_finiteness_field"],4+31)
        self.assertEqual(sim.work.operations-before,32+4+31)
        self.assertTrue(all(pose._projection=={} for pose in poses))
        self.assertTrue(all(pose._finite_proof is not None for pose in poses))
        self.assertLessEqual(len(sim.work._cache),256)
        self.assertIsNone(replace(poses[0])._finite_family)

    def test_cancelled_borrow_does_not_publish_an_own_or_shared_partial_proof(self):
        ops=ReachPoseOps(ReachExecutionWork())
        first=private_pose(ops)
        second=replace(first,exact_position=(F(1),F(0),F(0)))
        ops._carry_finite_proof(first,second)
        ops.ensure_finite(first)
        completed=first._finite_family.proof
        self.assertIsNone(second._finite_proof)
        marker=RuntimeError("cancel borrowed source proof")
        with patch.object(ops.work,"external_check",side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.ensure_finite(second)
        self.assertIs(caught.exception,marker)
        self.assertIs(ops.work.callback_error,marker)
        self.assertIsNone(second._finite_proof)
        self.assertIs(first._finite_family.proof,completed)
        self.assertEqual(second._projection,{})
        ops.ensure_finite(second)
        self.assertIs(second._finite_family.proof,second._finite_proof)
        self.assertIs(first._finite_proof,completed)

    def test_late_cap_change_rechecks_earlier_borrowed_position_under_live_cap(self):
        ops=ReachPoseOps(ReachExecutionWork())
        first=private_pose(ops,position=(F(1<<200),F(0),F(0)))
        second=replace(first,exact_velocity=(F(1),F(0),F(0)))
        ops._carry_finite_proof(first,second)
        ops.ensure_finite(first)
        completed=first._finite_family.proof
        charge=ops.work.charge

        def narrow(kind="checkpoint",amount=1):
            if kind=="pose_finiteness_field":
                ops.work.max_operand_bits=128
            charge(kind,amount)

        with patch.object(ops.work,"charge",narrow):
            with self.assertRaises(ReachAdmissionError) as caught:
                ops.ensure_finite(second)
        self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")
        self.assertEqual(caught.exception.details["limit"],128)
        self.assertIsNone(second._finite_proof)
        self.assertIs(first._finite_family.proof,completed)
        self.assertNotIn("position",second._projection)

    def test_malformed_shared_metadata_retains_original_field_checks(self):
        ops=ReachPoseOps(ReachExecutionWork())
        pose=private_pose(ops)
        ops.ensure_finite(pose)
        before=ops.work.counts["pose_finiteness_field"]
        object.__setattr__(pose,"_finite_family",object())
        ops.ensure_finite(pose)
        self.assertEqual(ops.work.counts["pose_finiteness_field"]-before,4)
        self.assertEqual(pose._projection,{})

    def test_complete_p23_boundaries_match_individual_completed_proof_carry(self):
        results=[]
        costs=[]
        for shared in (True,False):
            built=compile_construction(source_case("P23"))
            sim=PlanningSimulator(built.model,work=built.reach_work)
            ops=sim.pose_ops

            def individual(source,target):
                if (type(source) is PoseValue and type(target) is PoseValue and
                        source._ops is ops and target._ops is ops and
                        ops._valid_finite_proof(source._finite_proof)):
                    object.__setattr__(target,"_finite_proof",source._finite_proof)

            def observe():
                rows=[]
                for time in (0,2,3):
                    for side in ("before","after"):
                        sim.advance(F(time),side)
                        rows.append(sim.recording_boundary(F(time),side))
                return rows,copy.deepcopy(sim.state)

            if shared:
                results.append(observe())
            else:
                with patch.object(ops,"_carry_finite_proof",individual):
                    results.append(observe())
            costs.append(built.budget.operations)
            self.assertLessEqual(built.budget.operations,100000)
            self.assertLessEqual(len(sim.work._cache),256)
        self.assertEqual(results[0],results[1])
        self.assertGreater(costs[1]-costs[0],500)


if __name__=="__main__":
    unittest.main()
