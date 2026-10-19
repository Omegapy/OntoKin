"""Actual Agent/0.5 source workflows and unchanged older protocol behavior."""
from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import load_file_manifest
from ontokin.construction_catalog import catalog
from ontokin.json_limits import measure_json
from ontokin.evaluator import time_text
from ontokin.program_agent import ProgramAgentService
from ontokin.program_bindings import PROGRAM_BINDINGS
from ontokin.program_protocol import bind
from test_impulse_agent import minimal_patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/language-design/force-v0.1'
CASES = {c['id']: c for c in json.loads((DATA/'acceptance.json').read_text())['source_cases']}
PROTOCOL = 'ontokin.agent/0.5'
BALL = ['force-demo', 'demo', 'ball']
SCENE = ['force-demo', 'demo']
RACK = SCENE + ['rack']
FIRST = RACK + ['props', 'first']


def source_case(name):
    program = load_file_manifest(DATA / CASES[name]['file_manifest'])
    assert program.program_revision == CASES[name]['program_revision']
    return program


class ForceAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = ProgramAgentService(self.tmp.name, protocol=PROTOCOL)
        self.number = 0

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def request(self, operation, **fields):
        self.number += 1
        return dict(schema_version=PROTOCOL, project_id='force', request_id=str(self.number), operation=operation, **fields)

    def send(self, operation, **fields):
        return self.service.handle(self.request(operation, **fields))

    def success(self, response):
        self.assertEqual(response['status'], 'succeeded', response)
        self.assertEqual(response['schema_version'], PROTOCOL)
        self.assertIsNone(response['protocol_error'], response)
        return response

    def error(self, response, code):
        self.assertIn(response['status'], ('failed', 'rejected'), response)
        codes = [d['code'] for d in response['diagnostics']]
        if response.get('protocol_error'):
            codes.append(response['protocol_error']['code'])
        self.assertIn(code, codes, response)
        return response

    def head(self):
        with self.service._store.connection() as db:
            return self.service._store.accepted(db, 'force')

    def create(self, name='P01', level='constructed'):
        b = source_case(name)
        c = self.success(self.send('create', bundle=b.to_payload(), expected_program_revision=None, requested_level=level))
        self.assertEqual(c['accepted_program_revision'], b.program_revision)
        return b, c

    def inspect(self, b, run=None, time='1.5', side='after', path='ball', **kwargs):
        fields = kwargs.pop('fields', ['identity', 'source', 'state', 'geometry'])
        context = {} if run is None else {'run_id':run,'time':{'seconds':time,'side':side}}
        r = self.success(self.send('inspect', program_revision=b.program_revision, selector={'path':path}, fields=fields, limit=1, **context, **kwargs))
        self.assertEqual(r['result']['total'], 1)
        return r['result']['items'][0]

    def evaluate(self, b, until='3', run=None):
        return self.success(self.send('evaluate', program_revision=b.program_revision, run_id=run, until_seconds=until))

    def test_construction_contains_complete_empty_force_state(self):
        _, c = self.create()
        f = c['result']['initial_state']['objects']['ball']['forces']
        self.assertEqual(f, dict(active=[],net_force_world_n=[0,0,0],acceleration_world_m_per_s2=[0,0,0],
                                 started_count=0,completed_count=0,last_change_time_seconds=None,last_changes=[]))

    def test_before_after_activation_completion_and_exact_source_records(self):
        b, _ = self.create()
        run = self.evaluate(b)['run_id']
        for time,side,keys,counts,a in [('1','before',[],(0,0),0),('1','after',['push'],(1,0),2),
                                      ('2','before',['push'],(1,0),2),('2','after',[],(1,1),0)]:
            with self.subTest(time=time,side=side):
                f=self.inspect(b,run,time,side)['state']['forces']
                self.assertEqual([r['force_key'] for r in f['active']],keys)
                self.assertEqual((f['started_count'],f['completed_count']),counts)
                self.assertEqual(f['acceleration_world_m_per_s2'],[a,0,0])
                for r in [*f['active'],*f['last_changes']]:
                    self.assertEqual(r['program_revision'], b.program_revision)
                    self.assertEqual(r['target_element_id'], BALL)
                    loc=r['source_location'];self.assertEqual(loc['source_revision'],b.entry.revision)
                    text=b.entry.raw[loc['start_byte']:loc['end_byte']].decode()
                    self.assertEqual(text,'force ball @ "push" using vector(world, 4[N], 0[N], 0[N]) for 1[s];')
                    self.assertEqual(r['completion_time_seconds'],'2')

    def test_overlap_sorted_active_keys_and_complete_recent_history(self):
        b,_=self.create('P02');run=self.evaluate(b,until='4')['run_id']
        f=self.inspect(b,run)['state']['forces']
        self.assertEqual([r['force_key'] for r in f['active']],['a','b'])
        self.assertEqual(f['net_force_world_n'],[2,0,0])
        self.assertEqual(f['acceleration_world_m_per_s2'],[1,0,0])
        self.assertEqual([(r['kind'],r['force_key']) for r in f['last_changes']],[('started','b')])
        f2=self.inspect(b,run,'2.5')['state']['forces']
        self.assertEqual(f2['net_force_world_n'],[-2,0,0])
        self.assertEqual([(r['kind'],r['force_key']) for r in f2['last_changes']],[('completed','a')])

    def test_unchanged_acceleration_preserves_anchor_but_not_provenance(self):
        b,_=self.create('P04');run=self.evaluate(b)['run_id']
        state=self.inspect(b,run)['state']
        self.assertEqual(state['pose_authority']['trajectory_anchor_seconds'],'0')
        self.assertEqual(state['forces']['started_count'],2)
        self.assertEqual(state['forces']['completed_count'],1)
        self.assertEqual(len(state['forces']['last_changes']),2)

    def test_world_force_fields_not_rotated_in_self_frame_inspection(self):
        b,_=self.create('P07');run=self.evaluate(b)['run_id']
        world=self.inspect(b,run)['state'];local=self.inspect(b,run,frame='ball.frame')['state']
        self.assertEqual(world['forces'],local['forces'])
        self.assertEqual(world['impulses'],local['impulses'])
        self.assertEqual(local['position_m'],[0,0,0])
        self.assertEqual(local['velocity_expressed_in'],'ball.frame')
        self.assertNotEqual(local['velocity_m_per_s'],world['velocity_m_per_s'])

    def test_exact_completion_beyond_binary64_and_requested_horizon(self):
        b,_=self.create('P18');end=time_text(Fraction.from_float(1.5e308))
        run=self.evaluate(b,end)['run_id']
        f=self.inspect(b,run,end)['state']['forces']
        self.assertEqual(Fraction(f['active'][0]['completion_time_seconds']),Fraction.from_float(1e308)*2)
        self.assertEqual(f['completed_count'],0)
        self.assertEqual(f['started_count'],1)

    def test_later_failure_preserves_certified_prefix_and_reset(self):
        b,_=self.create('P21');r=self.evaluate(b,'1');run=r['run_id']
        e=self.error(self.send('evaluate',program_revision=b.program_revision,run_id=run,until_seconds='4'),'OKL-E-NUMERIC')
        self.assertGreaterEqual(Fraction(e['result']['run_state']['valid_until_seconds']),1)
        self.assertEqual(self.inspect(b,run,'0.5')['state']['forces']['started_count'],1)
        bad=self.send('inspect',program_revision=b.program_revision,run_id=run,time={'seconds':'3','side':'after'},selector={'path':'ball'},fields=['state'],limit=1)
        self.error(bad,'OKL-E-SAMPLE')
        reset=self.success(self.send('reset',program_revision=b.program_revision))
        self.assertNotEqual(run,reset['run_id'])
        self.assertEqual(reset['result']['run_state']['valid_until_side'],'before')
        self.assertEqual(reset['result']['run_state']['last_valid_state']['objects']['ball']['forces']['started_count'],0)

    def test_three_exact_source_repairs_preserve_siblings_libraries_and_old_runs(self):
        for target,identity in [('P11',RACK),('P12',SCENE),('P13',SCENE)]:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as d, ProgramAgentService(d,protocol=PROTOCOL) as s:
                old=source_case('P10');new=source_case(target)
                c=s.handle(self.request('create',bundle=old.to_payload(),expected_program_revision=None,requested_level='evaluated'));self.success(c)
                r=s.handle(self.request('edit',expected_program_revision=old.program_revision,patches=[minimal_patch(old,new,identity)],requested_level='evaluated'));self.success(r)
                self.assertEqual(r['accepted_program_revision'],new.program_revision)
                self.assertEqual(s.read_program('force',new.program_revision),new)
                self.assertEqual(s.read_program('force',old.program_revision),old)
                self.assertEqual(old.modules,new.modules)
                a=c['result']['run_state']['last_valid_state']['objects']['rack.props["second"]']
                b=r['result']['run_state']['last_valid_state']['objects']['rack.props["second"]']
                for k in ('position_m','velocity_m_per_s','orientation_wxyz','angular_velocity_rad_per_s'):
                    self.assertEqual(a[k],b[k])
                # Identity provenance must change even for an unchanged sibling.
                self.assertEqual(b['forces']['last_changes'][0]['program_revision'],new.program_revision)
                self.assertNotEqual(c['run_id'],r['run_id'])

    def test_derived_force_and_occurrence_ids_do_not_authorize_scene_edit(self):
        b,_=self.create('P10');new=source_case('P12')
        for identity in (FIRST,SCENE+['force','push']):
            self.error(self.send('edit',expected_program_revision=b.program_revision,
                       patches=[minimal_patch(b,new,identity)],requested_level='constructed'),'OKL-E-REVISION')
            self.assertEqual(self.head(),b.program_revision)

    def test_stale_invalid_candidate_and_changed_retry_payload_preserve_head(self):
        b,_=self.create('P10');new=source_case('P12')
        invalid=minimal_patch(b,new,SCENE);invalid['replacement']='-1[s]'
        bad=self.send('edit',expected_program_revision=b.program_revision,patches=[invalid],requested_level='constructed')
        self.assertIn(bad['status'],('failed','rejected'))
        self.assertEqual(bad['accepted_program_revision'],b.program_revision)
        request=self.request('edit',expected_program_revision=b.program_revision,patches=[minimal_patch(b,new,SCENE)],requested_level='constructed')
        response=self.success(self.service.handle(request));self.assertEqual(response,self.service.handle(request))
        self.error(self.send('edit',expected_program_revision=b.program_revision,patches=[minimal_patch(b,new,SCENE)],requested_level='constructed'),'OKL-E-REVISION')
        changed=copy.deepcopy(request);changed['requested_level']='represented'
        self.assertEqual(self.service.handle(changed)['status'],'rejected')
        self.assertEqual(self.head(),new.program_revision)

    def test_mesh_page_contract_and_cursor_cross_query_isolation(self):
        b,_=self.create()
        a=self.success(self.send('surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1))
        self.assertEqual(a['result']['profile'],'surface-0.1')
        self.assertEqual(self.service._context_binding()['entry_profile'],'force-0.1')
        self.assertTrue(a['next_cursor'])
        self.success(self.send('surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1,cursor=a['next_cursor']))
        self.success(self.service.handle({**self.request('create',bundle=b.to_payload(),expected_program_revision=None,requested_level='constructed'),'project_id':'other'}))
        bad=self.service.handle({**self.request('surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1,cursor=a['next_cursor']),'project_id':'other'})
        self.assertIn(bad['status'],('rejected','failed'))
        with self.assertRaises(ProtocolError):
            bind('ontokin.agent/0.4').validate_request(self.request('surface.mesh_page',program_revision=b.program_revision,element_id=BALL,count=1))

    def test_planned_delivery_rejects_without_artifact_or_accepted_candidate(self):
        b,_=self.create()
        for operation in ('export','validate'):
            kw=dict(program_revision=b.program_revision,destination='ontokin.glb/0.5')
            if operation=='validate':kw['requested_level']='delivered'
            r=self.error(self.send(operation,**kw),'OKL-E-CAPABILITY-UNSUPPORTED')
            self.assertNotEqual(r['achieved_level'],'delivered')
            self.assertEqual(r['accepted_program_revision'],b.program_revision)
            self.assertEqual(r['diagnostics'][0]['blocks'],['delivered'])
        with self.service._store.connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)
        new=source_case('P02')
        r=self.error(self.service.handle({**self.request('create',bundle=new.to_payload(),expected_program_revision=None,requested_level='delivered',destination='ontokin.glb/0.5'),'project_id':'new'}),'OKL-E-CAPABILITY-UNSUPPORTED')
        self.assertIsNone(r['accepted_program_revision'])

    def test_final_response_entry_limit_rejects_inside_publication_transaction(self):
        b,baseline=self.create(level='evaluated')
        entries=measure_json(baseline)['entries'];prepared=[]
        original=self.service._execute
        def observe(task,check):
            original(task,check)
            prepared.append((task.accept,task.run is not None,task.artifact is not None))
        request={**self.request('create',bundle=b.to_payload(),expected_program_revision=None,
                               requested_level='evaluated',budgets={'max_value_entries':entries-1}),
                 'project_id':'limited'}
        with patch.object(self.service,'_execute',side_effect=observe):
            r=self.error(self.service.handle(request),'OKA-E-RESOURCE')
        self.assertEqual(prepared,[(True,True,False)])
        self.assertIsNone(r['accepted_program_revision'])
        self.assertIsNone(r['run_id']);self.assertIsNone(r['result'])
        self.assertFalse(r['protocol_error']['details']['effects_committed'])
        with self.service._store.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM runs WHERE project_id='limited'").fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)
        exact=self.success(self.service.handle({**request,'request_id':'exact','budgets':{'max_value_entries':entries}}))
        self.assertEqual(exact['accepted_program_revision'],b.program_revision)

    def test_cancel_queued_request_and_reconcile_status(self):
        b=source_case('P01')
        req=self.request('create',bundle=b.to_payload(),expected_program_revision=None,requested_level='constructed')
        self.assertEqual(self.service.submit(req)['status'],'queued')
        self.send('cancel',target_request_id=req['request_id'])
        self.service.work_next()
        r=self.service.handle(req)
        self.assertEqual(r['status'],'cancelled')
        self.assertIsNone(r['accepted_program_revision'])
        status=self.send('status',target_request_id=req['request_id'])
        self.assertEqual(status['result']['target']['status'],'cancelled')


class ForceAgentBindingTests(unittest.TestCase):
    def test_default_bindings_and_old_catalog_bytes_remain_unchanged(self):
        self.assertEqual(bind().SCHEMA_VERSION,'ontokin.agent/0.2')
        for profile,revision in [('construction-0.1','7c997692ee8d2516bc897ad898f34d101affb97ccb4a7eb95921bcd3b5f9f490'),
                                 ('surface-0.1','e11dab7746fa2ee9f7b36f172cef110fbb226e7a5f8b7cb5786dc07ee9234c35'),
                                 ('impulse-0.1','c6f868fc62f877f2849d3de228ca90412a6503bb5ff83043e15aa170ead57a8f')]:
            self.assertEqual(catalog(profile=profile)['revision'],'sha256:'+revision)
        self.assertFalse(PROGRAM_BINDINGS[PROTOCOL].delivery_available)

    def test_force_discovery_does_not_claim_delivery_or_general_physics(self):
        c=catalog(profile='force-0.1');self.assertEqual(c['delivery_targets'],[])
        self.assertEqual(c['agent_contract'],PROTOCOL)
        self.assertFalse(c['full_product_conformance_certified'])
        items={i['name']:i for i in c['items']}
        self.assertEqual(items['ontokin.glb/0.5']['availability'],'unsupported')
        self.assertEqual(items['force']['kind'],'event')
        self.assertIn('source_com_forces',items)
        self.assertEqual(items['external_forces_and_actuators']['availability'],'unsupported')
        self.assertEqual(len({i['id'] for i in c['items']}),len(c['items']))

    def test_five_same_directory_stores_and_request_ids_are_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            definitions=[('ontokin.agent/0.1','agent.sqlite3'),*[(b.protocol,b.store_filename) for b in PROGRAM_BINDINGS.values()]]
            for protocol,filename in definitions:
                s=AgentService(d) if protocol.endswith('/0.1') else ProgramAgentService(d,protocol=protocol)
                with s:
                    key='source_revision' if protocol.endswith('/0.1') else 'program_revision'
                    r=s.submit(dict(schema_version=protocol,project_id='same',request_id='same',operation='validate',requested_level='represented',**{key:'sha256:'+'a'*64}))
                    self.assertEqual(r['status'],'queued')
                    self.assertEqual(s._store.database_path.name,filename)
            self.assertEqual({p.name for p in Path(d).glob('*.sqlite3')},{f for _,f in definitions})

    def test_no_host_force_or_cross_protocol_input(self):
        p=bind(PROTOCOL)
        for name in ('force','apply_force','set_state','set_velocity','apply_impulse'):
            with self.assertRaises(ProtocolError):
                p.validate_request(dict(schema_version=PROTOCOL,project_id='p',request_id='x',operation=name))
        for older in ('ontokin.agent/0.1','ontokin.agent/0.2','ontokin.agent/0.3','ontokin.agent/0.4'):
            with self.assertRaises(ProtocolError):
                p.validate_request(dict(schema_version=older,project_id='p',request_id='x',operation='status',target_request_id='y'))
