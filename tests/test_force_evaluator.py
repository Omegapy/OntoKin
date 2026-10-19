"""Force transaction, budget, prefix and inherited-profile regressions."""
from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction as Q
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import (_records_per_sample, construct, evaluate, evaluate_prefix,
                               inspect_in_frame, preflight)
from ontokin.force_runtime import ForceSimulator, _record, force_record_bound
from ontokin.json_limits import measure_json
from test_force_source import bundle, model, changed


class CancelledProbe(RuntimeError):
    pass


class ForceEvaluatorTests(unittest.TestCase):
    def test_complete_timeline_and_prefix_are_distinct(self):
        m=model('P21')
        prefix=evaluate_prefix(m,'1')
        self.assertIsNone(prefix['failure'])
        self.assertEqual(prefix['last_valid_state']['objects']['ball']['velocity_m_per_s'],[2,0,0])
        with self.assertRaises(OntoKinError) as e:evaluate(m,['1'])
        self.assertEqual(e.exception.code,'OKL-E-NUMERIC')
        self.assertEqual(e.exception.diagnostic.time,Q(2))

    def test_short_prefix_does_not_charge_an_unprocessed_endpoint(self):
        m=model('P01')
        self.assertGreater(_records_per_sample(m),30)
        with patch('ontokin.evaluator.MAX_OUTPUT_RECORDS',30):
            before=evaluate_prefix(m,'1',side='before')
            self.assertIsNone(before['failure'])
            self.assertEqual(before['last_valid_state']['objects']['ball']['forces']['started_count'],0)
            with self.assertRaises(OntoKinError) as e:evaluate_prefix(m,'1',side='after')
            self.assertEqual(e.exception.code,'OKL-E-RESOURCE')

    def test_exact_completion_beyond_binary64_is_not_scheduled_in_prefix(self):
        m=model('P18');result=evaluate_prefix(m,m.duration)
        self.assertIsNone(result['failure'])
        obj=result['last_valid_state']['objects']['ball']
        end=obj['forces']['active'][0]['completion_time_seconds']
        self.assertGreater(Q(end),m.duration)
        self.assertNotIn(end,result['boundary_times_seconds'])
        self.assertEqual(obj['forces']['completed_count'],0)

    def test_zero_interval_counts_and_records_without_trajectory_change(self):
        m=model('P05');sim=ForceSimulator(m);sim.advance(Q(0));old=copy.deepcopy(sim.state.dynamic['ball'])
        sim.advance(Q(1));self.assertEqual(sim.state.dynamic['ball'],old)
        sim.advance(Q(2));self.assertEqual(sim.state.dynamic['ball'],old)
        history=sim.snapshot(Q(2),'after')['objects']['ball']['forces']
        self.assertEqual(history['started_count'],1);self.assertEqual(history['completed_count'],1)
        self.assertEqual(history['last_changes'][0]['kind'],'completed')

    def test_expiring_replacement_preserves_anchor_and_identifies_both_changes(self):
        sim=ForceSimulator(model('P04'));sim.advance(Q(0));old=copy.deepcopy(sim.state.dynamic['ball'])
        sim.advance(Q(1));self.assertEqual(sim.state.dynamic['ball'],old)
        history=sim.snapshot(Q(1),'after')['objects']['ball']['forces']
        self.assertEqual([(r['kind'],r['force_key']) for r in history['last_changes']],
                         [('completed','a'),('started','b')])

    def test_unrelated_boundary_keeps_full_latest_force_records(self):
        b=bundle('P01');m=compile_construction(changed(b,'    at 1[s] sequence {','    at 0.5[s] sequence { }\n    at 1[s] sequence {')).model
        before,after=evaluate(m,['1','1.5'])['samples']
        self.assertEqual(before['objects']['ball']['forces'],after['objects']['ball']['forces'])

    def test_impulse_and_force_at_same_boundary_keep_sequence_and_one_motion_authority(self):
        b=bundle('P07');text=b.entry.text
        # Preserve actual source imports/geometry, move its authored impulse to
        # the same force-start sequence rather than inject host dynamics.
        start='    at 1[s] sequence {\n        impulse'
        text=text.replace('for 2[s];\n    }\n'+start,'for 2[s];\n        impulse')
        m=compile_construction(ProgramBundle(replace(b.entry,raw=text.encode()),b.modules)).model
        s=evaluate(m,['0'])['samples'][0]['objects']['ball']
        self.assertEqual(s['velocity_m_per_s'],[0,1,0]);self.assertEqual(s['angular_velocity_rad_per_s'],[0,0,5])
        self.assertEqual(s['forces']['active'][0]['sequence_index'],0)
        self.assertEqual(s['impulses']['last_applications'][0]['sequence_index'],1)
        self.assertEqual(s['pose_authority']['kind'],'free_sphere')
        self.assertEqual(s['own_mass_kg'],2)

    def test_force_world_axes_are_independent_of_body_orientation(self):
        b=bundle('P01');m=compile_construction(changed(b,'body_mass = 2[kg];',
            'body_mass = 2[kg]; placement = pose(world, vec3(0[m], 0[m], 0[m]), axis_angle(vec3(0, 0, 1), 1.5707963267948966[rad]));')).model
        obj=evaluate(m,['2'])['samples'][0]['objects']['ball']
        self.assertEqual(obj['position_m'],[1,0,0]);self.assertEqual(obj['velocity_m_per_s'],[2,0,0])
        self.assertEqual(obj['angular_velocity_rad_per_s'],[0,0,0])

    def test_actual_self_frame_inspection_does_not_mutate_world_force_projection(self):
        s=evaluate(model('P07'),['1.5'])['samples'][0]
        old=copy.deepcopy(s['objects']['ball']['forces'])
        selected=inspect_in_frame(s,'ball','ball.frame')
        self.assertEqual(selected['velocity_expressed_in'],'ball.frame')
        self.assertEqual(s['objects']['ball']['forces'],old)
        self.assertEqual(old['net_force_world_n'],[4,0,0])

    def test_final_aggregation_error_identifies_all_sources_and_rolls_back(self):
        sim=ForceSimulator(model('N18'));sim.advance(Q(0),'before');old=copy.deepcopy(sim.state)
        with self.assertRaises(OntoKinError) as caught:sim.advance(Q(0),'after')
        self.assertEqual(caught.exception.code,'OKL-E-NUMERIC')
        records=caught.exception.diagnostic.details['changed_forces']
        self.assertEqual([r['force_key'] for r in records],['a','b'])
        self.assertEqual(sim.state,old)
        self.assertTrue(sim.zero_pending)
        self.assertEqual(sim.event_index,0)

    def test_release_and_valid_force_are_rolled_back_by_later_invalid_force(self):
        b=bundle('P09');text=b.entry.text.replace('    at 0[s] sequence',
            '    object other @ "other": bodies.SphereProp { motion = static; }\n    at 0[s] sequence')
        text=text.replace('for 1[s];','for 1[s];\n        force other @ "bad" using vector(world, 0[N], 0[N], 0[N]) for 1[s];')
        m=compile_construction(ProgramBundle(replace(b.entry,raw=text.encode()),b.modules)).model
        sim=ForceSimulator(m);sim.advance(Q(1),'before');old=copy.deepcopy(sim.state)
        with self.assertRaises(OntoKinError):sim.advance(Q(1),'after')
        self.assertEqual(sim.state,old)
        self.assertEqual(sim.state.modes['ball'],'prescribed')
        self.assertIn('hold',sim.state.active_grips)
        self.assertEqual(sim.state.forces['ball'].started_count,0)

    def test_cancel_at_every_boundary_hook_never_publishes_partial_state(self):
        m=model('P09')
        counter=[0]
        sim=ForceSimulator(m);sim.advance(Q(1),'before')
        def count():counter[0]+=1
        sim.check=count;sim._process_boundary(Q(1));counted=counter[0]
        self.assertGreater(counted,20)
        for stop in range(1,counted+1):
            with self.subTest(hook=stop):
                sim=ForceSimulator(m);sim.advance(Q(1),'before')
                original=copy.deepcopy(sim.state);index=sim.event_index;history=list(sim.boundaries)
                calls=[0]
                def cancel():
                    calls[0]+=1
                    if calls[0]==stop:raise CancelledProbe('selected boundary hook')
                sim.check=cancel
                with self.assertRaises(CancelledProbe):sim._process_boundary(Q(1))
                self.assertEqual(sim.state,original)
                self.assertEqual(sim.event_index,index);self.assertEqual(sim.boundaries,history)

    def test_cancel_after_tentative_completion_preserves_active_set(self):
        sim=ForceSimulator(model('P01'));sim.advance(Q(2),'before');original=copy.deepcopy(sim.state)
        completed=[False];original_change=sim._change
        def change(history,time,kind,force):
            original_change(history,time,kind,force)
            if kind=='completed':completed[0]=True
        def check():
            if completed[0]:raise CancelledProbe('after tentative completion')
        sim._change=change;sim.check=check
        with self.assertRaises(CancelledProbe):sim._process_boundary(Q(2))
        self.assertTrue(completed[0]);self.assertEqual(sim.state,original)
        self.assertEqual(sim.state.forces['ball'].completed_count,0)

    def test_zero_time_callback_cancellation_is_not_rewritten(self):
        interruption=CancelledProbe('before activation')
        def check():raise interruption
        with self.assertRaises(CancelledProbe) as caught:evaluate_prefix(model('P14'),'0',check=check)
        self.assertIs(caught.exception,interruption)

    def test_lowered_compilation_budget_and_callback_identity(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_construction(bundle('P01'),budgets={'max_operations':100})
        self.assertEqual(caught.exception.code,'OKL-E-RESOURCE')
        interruption=OntoKinError('OKL-E-UNIT','intentional callback identity probe')
        def check():raise interruption
        with self.assertRaises(OntoKinError) as caught:compile_construction(bundle('P01'),check=check)
        self.assertIs(caught.exception,interruption)
        self.assertEqual(caught.exception.code,'OKL-E-UNIT')

    def test_output_bound_covers_all_nested_histories_and_coexisting_objects(self):
        for id in ('P01','P02','P03','P09','P10','P13','P19'):
            m=model(id);bound=force_record_bound(m)
            sim=ForceSimulator(m)
            clocks={Q(0),m.duration}
            for block in m.events:
                clocks.add(block.time)
                for event in block.events:
                    if event.force:clocks.add(min(m.duration,block.time+event.force.duration))
            for t in sorted(clocks):
                for side in ('before','after'):
                    sample=sim.advance(t,side)
                    entries=sum(measure_json(obj['forces'])['entries'] for obj in sample['objects'].values())
                    self.assertLessEqual(entries,bound)

    def test_oversized_history_is_rejected_before_simulator_allocation(self):
        b=bundle('P01')
        old='force ball @ "push" using vector(world, 4[N], 0[N], 0[N]) for 1[s];'
        text='\n'.join('force ball @ "k%d" using vector(world, 0[N], 0[N], 0[N]) for 1[s];'%i for i in range(260))
        m=compile_construction(changed(b,old,text)).model
        self.assertGreater(_records_per_sample(m)*10,100000)
        with patch('ontokin.evaluator._simulator',side_effect=AssertionError('allocated before admission')):
            with self.assertRaises(OntoKinError) as caught:evaluate(m,['1']*10)
        self.assertEqual(caught.exception.code,'OKL-E-RESOURCE')

    def test_construction_does_not_preflight_future_force_failure(self):
        self.assertEqual(construct(model('N18'))['outcome'],'valid')
        with self.assertRaises(OntoKinError) as caught:preflight(model('N18'))
        self.assertEqual(caught.exception.code,'OKL-E-NUMERIC')

    def test_old_impulse_profile_has_no_force_projection(self):
        from test_impulse_evaluator import compiled
        m=compiled('P02');obj=evaluate(m,['1'])['samples'][0]['objects']['ball']
        self.assertNotIn('forces',obj)
        self.assertEqual(obj['impulses']['applied_count'],1)
        self.assertEqual(m.profile,'impulse-0.1')


if __name__=='__main__':unittest.main()
