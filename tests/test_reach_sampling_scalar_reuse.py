"""Repeated measured scalars and spin steps retain exact outputs and domains."""
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_kinematics import measured_residual_squared
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, exact, rational
from ontokin.reach_pose import ReachPoseOps, UNIT
from ontokin.scene import ExportOptions


def direct_residual(actual, target, work):
    result=F(0)
    for a,b in zip(actual,target):
        delta=exact(rational(a,work),rational(b,work),"sub",work)
        result=exact(result,exact(delta,delta,"mul",work),"add",work)
    return result


def previous_spin(self, initial, omega, elapsed, *, context, path,
                  max_steps, phase_plan=None):
    """Original cursor algorithm, retained only as an independent test oracle."""
    initial=self._rotation(initial); elapsed=rational(elapsed,self.work)
    omega=self._vector(omega)
    key=self._recording_cursor_key("previous-spin",context,path,max_steps,initial,omega,phase_plan)
    self.work.charge("orientation_stationary",3)
    if not any(omega) or not elapsed: return initial
    plan=self._checked_spin_plan(omega,elapsed,phase_plan)
    previous=self.work.lookup(key)
    delta=None
    if previous is not None and previous[2]<max_steps:
        last,rotation,count=previous
        self.work.charge("recording_rotation_cursor_guard")
        self.work.guard(last,*rotation.components,rotation.error_rad,count)
        delta=self._op(elapsed,last,"sub")
        from ontokin.reach_numeric import compare
        if compare(abs(delta),plan.max_elapsed_s,self.work)>0: delta=None
    if delta is None:
        result=self.advance_orientation(initial,omega,elapsed,phase_plan=plan)
        count=1
    else:
        if delta:
            from ontokin.reach_pose import METHOD
            increment_key=(METHOD,"recording_spin_increment",omega,plan,delta,
                           self.work.max_operand_bits)
            increment=self.work.lookup(increment_key)
            if increment is None:
                increment=self.spin_rotation(omega,delta,phase_plan=plan)
                self.work.remember(increment_key,increment)
            else:
                self.work.guard(*increment.components,increment.error_rad)
            result=self.multiply(increment,rotation)
        else: result=rotation
        self.work.charge("recording_rotation_step")
        count+=1
    self.work.remember(key,(elapsed,result,count))
    return result


class ReachSamplingScalarReuseTests(unittest.TestCase):
    def test_residual_reuse_keeps_exact_result_and_avoids_repeated_arithmetic(self):
        actual=(.1,F(3,7),-2.0); target=(.3,F(5,11),0.0)
        work=ReachExecutionWork()
        expected=direct_residual(actual,target,ReachExecutionWork())
        self.assertEqual(measured_residual_squared(actual,target,work=work),expected)
        before=work.operations
        self.assertEqual(measured_residual_squared(actual,target,work=work),expected)
        direct=ReachExecutionWork()
        direct_residual(actual,target,direct)
        self.assertLess(work.operations-before,direct.operations)
        self.assertEqual(work.operations,sum(work.counts.values()))
        self.assertLessEqual(len(work._cache),256)

    def test_residual_new_values_eviction_and_zero_never_reuse_another_scalar(self):
        work=ReachExecutionWork(max_cache_entries=2)
        for a,b in (((1.,2.,3.),(1.,2.,3.)),((1.,2.,3.),(0.,0.,0.)),
                    ((4.,2.,3.),(1.,2.,3.)),((1.,2.,3.),(1.,2.,3.))):
            self.assertEqual(measured_residual_squared(a,b,work=work),
                             direct_residual(a,b,ReachExecutionWork()))
            self.assertLessEqual(len(work._cache),2)

    def test_residual_hit_checks_each_current_operand_before_lookup(self):
        work=ReachExecutionWork()
        measured_residual_squared((0,0,0),(0,0,0),work=work)
        for bad in (False,float("nan"),float("inf"),F(1<<32768)):
            with self.subTest(bad_type=type(bad).__name__):
                with patch.object(work,"lookup",wraps=work.lookup) as lookup:
                    with self.assertRaises(ReachAdmissionError):
                        measured_residual_squared((bad,0,0),(0,0,0),work=work)
                    lookup.assert_not_called()

    def test_residual_cap_changes_reestablish_original_intermediate_guard(self):
        actual=(F(1,1<<64),F(0),F(0)); target=(F(3,1<<64),F(0),F(0))
        for during_lookup in (False,True):
            with self.subTest(during_lookup=during_lookup):
                work=ReachExecutionWork()
                measured_residual_squared(actual,target,work=work)
                if during_lookup:
                    lookup=work.lookup
                    def narrowed(key):
                        result=lookup(key)
                        work.max_operand_bits=125
                        return result
                    context=patch.object(work,"lookup",side_effect=narrowed)
                else:
                    work.max_operand_bits=125
                    context=patch.object(work,"lookup",wraps=work.lookup)
                with context,self.assertRaises(ReachAdmissionError) as caught:
                    measured_residual_squared(actual,target,work=work)
                self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")
                self.assertEqual(caught.exception.details["consumed"],130)

    def test_residual_cancellation_leaves_no_partial_scalar(self):
        work=ReachExecutionWork(); marker=RuntimeError("cancel residual lookup")
        actual,target=(1,2,3),(4,5,6)
        measured_residual_squared(actual,target,work=work)
        before=dict(work._cache)
        original=work.lookup
        def cancelled(key):
            work.external_check=lambda:(_ for _ in ()).throw(marker)
            return original(key)
        with patch.object(work,"lookup",side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                measured_residual_squared(actual,target,work=work)
        self.assertIs(caught.exception,marker)
        self.assertEqual(dict(work._cache),before)

    def test_spin_cursor_keeps_every_component_allowance_and_projection(self):
        times=[F(i,64) for i in range(18)]
        times+=times[-1:]+list(reversed(times[3:10]))+[F(19,31),F(3,4)]
        for omega in ((0,0,F(1,4)),(F(1,8),F(-1,4),F(3,8))):
            for fixed_plan in (False,True):
                with self.subTest(omega=omega,fixed_plan=fixed_plan):
                    ops=ReachPoseOps(ReachExecutionWork())
                    reference=ReachPoseOps(ReachExecutionWork())
                    plans=[op.spin_plan(omega,F(2)) if fixed_plan else None
                           for op in (ops,reference)]
                    contexts=object(),object()
                    for time in times:
                        actual=ops.recording_advance_orientation((1,2,3,4),omega,time,
                            context=contexts[0],path="spin",max_steps=10000,phase_plan=plans[0])
                        expected=previous_spin(reference,(1,2,3,4),omega,time,
                            context=contexts[1],path="spin",max_steps=10000,phase_plan=plans[1])
                        self.assertEqual(actual,expected)
                        self.assertEqual(ops._unit_projection(actual),reference._unit_projection(expected))
                    self.assertLessEqual(len(ops.work._cache),256)

    def test_spin_increment_stays_in_cursor_and_avoids_one_use_product_entries(self):
        ops=ReachPoseOps(ReachExecutionWork()); context=object(); omega=(0,0,F(1,4))
        plan=ops.spin_plan(omega,F(2))
        args=dict(context=context,path="spin",max_steps=10000,phase_plan=plan)
        for time in (F(1,64),F(2,64)):
            ops.recording_advance_orientation(UNIT,omega,time,**args)
        before=tuple(key for key in ops.work._cache if "rotation_product" in key)
        with patch.object(ops,"spin_rotation",side_effect=AssertionError("recomputed spin increment")):
            ops.recording_advance_orientation(UNIT,omega,F(3,64),**args)
        self.assertEqual(before,tuple(key for key in ops.work._cache if "rotation_product" in key))
        self.assertEqual(ops.work.counts["recording_spin_increment_reuse"],1)

    def test_spin_cancelled_reuse_preserves_previous_cursor(self):
        ops=ReachPoseOps(ReachExecutionWork()); context=object(); omega=(0,0,F(1,4))
        plan=ops.spin_plan(omega,F(2))
        args=dict(context=context,path="spin",max_steps=10000,phase_plan=plan)
        for time in (F(1,64),F(2,64)):
            ops.recording_advance_orientation(UNIT,omega,time,**args)
        key=next(key for key in ops.work._cache if "recording_rotation_cursor" in key)
        before=ops.work._cache[key]; charge=ops.work.charge
        marker=RuntimeError("cancel spin reuse")
        def cancelled(kind="checkpoint",amount=1):
            if kind=="recording_spin_increment_reuse":
                ops.work.external_check=lambda:(_ for _ in ()).throw(marker)
            return charge(kind,amount)
        with patch.object(ops.work,"charge",side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                ops.recording_advance_orientation(UNIT,omega,F(3,64),**args)
        self.assertIs(caught.exception,marker)
        self.assertEqual(ops.work._cache[key],before)

    def test_spin_reuse_rechecks_a_callback_lowered_arithmetic_cap(self):
        ops=ReachPoseOps(ReachExecutionWork()); context=object(); omega=(0,0,F(1,4))
        plan=ops.spin_plan(omega,F(2))
        args=dict(context=context,path="spin",max_steps=10000,phase_plan=plan)
        for time in (F(1,64),F(2,64)):
            ops.recording_advance_orientation(UNIT,omega,time,**args)
        charge=ops.work.charge
        def narrowed(kind="checkpoint",amount=1):
            result=charge(kind,amount)
            if kind=="recording_spin_increment_reuse":ops.work.max_operand_bits=128
            return result
        with patch.object(ops.work,"charge",side_effect=narrowed):
            with self.assertRaises(ReachAdmissionError) as caught:
                ops.recording_advance_orientation(UNIT,omega,F(3,64),**args)
        self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")

    def test_p16_prefix_keeps_the_complete_original_glb(self):
        root=Path(__file__).resolve().parents[1]/"docs/language-design/planar-reach-v0.1"
        outputs=[]
        for original in (True,False):
            built=compile_construction(load_file_manifest(root/"p16.files.json"))
            method=previous_spin if original else ReachPoseOps.recording_advance_orientation
            with patch.object(ReachPoseOps,"recording_advance_orientation",method):
                result=export_glb(built.model,options=ExportOptions(end=F(1,4),fps=1,helpers=False),
                                  target_contract="ontokin.glb/0.6",work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"],"passed")
            self.assertLessEqual(built.budget.operations,100000)
            outputs.append(result.data)
        self.assertEqual(outputs[0],outputs[1])


if __name__=="__main__":
    unittest.main()
