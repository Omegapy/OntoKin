"""Execute each adopted force source case against its predetermined outcomes."""
from __future__ import annotations

from dataclasses import replace
import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import unittest

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import construct, evaluate, evaluate_prefix, time_text

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/language-design/force-v0.1'
BASE = json.loads((DATA/'acceptance.json').read_text())
CASES = {case['id']: case for case in BASE['source_cases']}
REVIEW = json.loads((DATA/'reviewed-acceptance.json').read_text())
EXTRA = {case['id']: case for case in REVIEW['source_cases']}
ERRATA = json.loads((DATA/'source-errata.json').read_text())
CORRECTIONS = {case['id']: case for case in ERRATA['corrections']}


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def bundle(case_id):
    c = CORRECTIONS.get(case_id, CASES.get(case_id, EXTRA.get(case_id)))
    return load_file_manifest(DATA/c['file_manifest'])


def model(case_id):
    return compile_construction(bundle(case_id)).model


def changed(source, old, new):
    assert source.entry.text.count(old) == 1
    return ProgramBundle(replace(source.entry, raw=source.entry.text.replace(old, new).encode()), source.modules)


class ForceSourceCases(unittest.TestCase):
    def assert_vector(self, actual, expected, *, exact=False):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertTrue(math.isfinite(a))
            if exact:
                self.assertEqual(a, b)
            else:
                self.assertAlmostEqual(a, b, delta=1e-9)

    def assert_orientation(self, actual, expected):
        actual = [x/math.hypot(*actual) for x in actual]
        expected = [x/math.hypot(*expected) for x in expected]
        if sum(x*y for x,y in zip(actual,expected)) < 0:
            expected = [-x for x in expected]
        self.assertLessEqual(4*math.asin(min(1,math.dist(actual,expected)/2)),1e-9)

    def assert_sample(self, compiled, source, sample, oracle, exact=False):
        self.assertEqual(sample['time_seconds'], time_text(rational(oracle['time'])))
        self.assertEqual(sample['side'], oracle['side'])
        obj = sample['objects'][oracle['target']]
        for field, expected in [('position_m','position_m'), ('velocity_m_per_s','velocity_m_s'),
                                ('angular_velocity_rad_per_s','omega_world_rad_s')]:
            self.assert_vector(obj[field],oracle[expected],exact=exact)
        self.assert_orientation(obj['orientation_wxyz'],oracle['orientation_wxyz'])
        authority = obj['pose_authority']
        if oracle['dynamic_since'] is not None:
            self.assertEqual(authority['since_seconds'],time_text(rational(oracle['dynamic_since'])))
            self.assertEqual(authority['trajectory_anchor_seconds'],time_text(rational(oracle['anchor_time'])))
        f = obj['forces']
        self.assertEqual([r['force_key'] for r in f['active']],oracle['active_keys'])
        self.assertEqual(f['started_count'],oracle['started_count'])
        self.assertEqual(f['completed_count'],oracle['completed_count'])
        self.assertEqual(f['last_change_time_seconds'],None if oracle['last_boundary'] is None else time_text(rational(oracle['last_boundary'])))
        self.assertEqual([{'kind':r['kind'],'key':r['force_key']} for r in f['last_changes']],oracle['last_changes'])
        self.assert_vector(f['net_force_world_n'],oracle['net_force_world_n'],exact=exact)
        if oracle['acceleration_world_m_s2'] is None:
            self.assertIsNone(f['acceleration_world_m_per_s2'])
        else:
            self.assert_vector(f['acceleration_world_m_per_s2'],oracle['acceleration_world_m_s2'],exact=exact)
        for record in f['active']+f['last_changes']:
            self.assertEqual(record['program_revision'],source.program_revision)
            self.assertEqual(record['target_element_id'],obj['element_id'])
            self.assertEqual(record['target_path'],oracle['target'])
            self.assertEqual(record['force_element_id'],[compiled.module_key,compiled.scene_key,'force',record['force_key']])
            location = record['source_location']
            self.assertEqual(location['source_revision'],source.entry.revision)
            statement = source.entry.raw[location['start_byte']:location['end_byte']].decode()
            self.assertTrue(statement.startswith('force '))
            self.assertIn('@ "'+record['force_key']+'"',statement)
            block = next(b for b in compiled.events if time_text(b.time)==record['activation_time_seconds'])
            event = block.events[record['sequence_index']]
            self.assertEqual(event.force.key,record['force_key'])
            self.assertEqual(record['completion_time_seconds'],time_text(block.time+event.force.duration))
        self.assertEqual({r['force_key']:r['completion_time_seconds'] for r in f['active']},
                         {k:time_text(rational(v)) for k,v in oracle['active_ends'].items()})
        json.dumps(f,allow_nan=False)

    def check_original(self, case):
        source = bundle(case['id'])
        if case['kind'] == 'negative' and case['expected']['phase_group']=='elaboration':
            with self.assertRaises(OntoKinError) as caught:
                compile_construction(source)
            self.assertEqual(caught.exception.code,case['expected']['diagnostic_code'])
            return
        compiled = compile_construction(source).model
        if case['kind'] == 'negative':
            result = evaluate_prefix(compiled,compiled.duration)
            self.assertIsNotNone(result['failure'])
            error = result['failure']
            self.assertEqual(error.code,case['expected']['diagnostic_code'])
            self.assertEqual(error.diagnostic.time,rational(case['expected']['time']))
            self.assertEqual(error.diagnostic.side,case['expected']['side'])
            self.assertEqual(result['valid_until_seconds'],time_text(error.diagnostic.time))
            self.assertEqual(result['valid_until_side'],'before')
            if case['id']=='N22':
                self.assertEqual(result['last_valid_state']['objects']['ball']['forces']['started_count'],0)
            if case['id']=='N21':
                self.assertEqual(result['last_valid_state']['joints']['hold']['status'],'active')
            return
        expected_rows = copy.deepcopy(case['expected_samples'])
        for correction in ERRATA.get('sample_corrections',[]):
            if correction['id'] != case['id']:
                continue
            row = next(r for r in expected_rows if all(r[key]==correction[key] for key in ('time','side','target')))
            for field, old in correction['old'].items():
                self.assertEqual(row[field],old)
            row.update(correction['new'])
        requests = [{'time':rational(s['time']),'side':s['side']} for s in expected_rows]
        if case['id']=='P21':
            actual=[]
            for request in requests:
                result=evaluate_prefix(compiled,request['time'],side=request['side'])
                self.assertIsNone(result['failure'])
                actual.append(result['last_valid_state'])
        else:
            actual=evaluate(compiled,requests)['samples']
        for s,oracle in zip(actual,expected_rows):
            with self.subTest(time=s['time_seconds'],side=s['side'],target=oracle['target']):
                self.assert_sample(compiled,source,s,oracle,exact=case['id'] in ('P18','P19','P20'))

    def check_extra(self, case):
        source=bundle(case['id']); expected=case['expected']; id=case['id']
        if case['outcome']=='invalid' and expected['phase_group'] in ('elaboration','support'):
            with self.assertRaises(OntoKinError) as caught:compile_construction(source)
            self.assertEqual(caught.exception.code,expected['code'])
            return
        compiled=compile_construction(source).model
        if case['outcome']=='invalid':
            short=evaluate_prefix(compiled,expected['valid_prefix'])
            self.assertIsNone(short['failure'])
            result=evaluate_prefix(compiled,compiled.duration)
            self.assertIsNotNone(result['failure']);e=result['failure']
            self.assertEqual(e.code,expected['code'])
            self.assertEqual(time_text(e.diagnostic.time),expected['failure_time'])
            self.assertEqual(e.diagnostic.side,expected['failure_side'])
            if id=='S06':
                self.assertEqual(result['valid_until_seconds'],'1')
                self.assertEqual(result['valid_until_side'],'before')
                f=result['last_valid_state']['objects']['ball']['forces']
                self.assertEqual([r['force_key'] for r in f['active']],expected['retained_active_keys'])
                self.assertEqual(f['completed_count'],0)
                self.assertEqual(f['started_count'],2)
                self.assertEqual(e.diagnostic.details['changed_forces'][0]['force_key'],'b')
                location=e.diagnostic.details['changed_forces'][0]['source_location']
                self.assertEqual(e.diagnostic.node.start,location['start_byte'])
            return
        if 'same_physical_samples_as' in expected:
            rows=CASES[expected['same_physical_samples_as']]['expected_samples']
            actual=evaluate(compiled,[{'time':rational(r['time']),'side':r['side']} for r in rows])['samples']
            target=expected.get('target_path','ball')
            for sample,oracle in zip(actual,rows):
                obj=sample['objects'][target]
                self.assert_vector(obj['position_m'],oracle['position_m'],exact=id=='S01')
                self.assert_vector(obj['velocity_m_per_s'],oracle['velocity_m_s'],exact=id=='S01')
                self.assertEqual(obj['forces']['started_count'],oracle['started_count'])
                self.assertEqual(obj['forces']['completed_count'],oracle['completed_count'])
            return
        if id=='S09':
            end=rational(expected['completion_clock'])
            before,after=evaluate(compiled,[{'time':end,'side':'before'},end])['samples']
            self.assertEqual(before['objects']['ball']['forces']['active'][0]['force_key'],'push')
            f=after['objects']['ball']['forces']
            self.assertEqual(f['active'],[]);self.assertEqual(f['started_count'],1);self.assertEqual(f['completed_count'],1)
            self.assertEqual(after['objects']['ball']['pose_authority']['trajectory_anchor_seconds'],'0')
        elif id=='S11':
            s=evaluate(compiled,['1'])['samples'][0]
            self.assertEqual(len(s['objects']),1)
            f=s['objects']['marker']['forces']
            self.assertEqual(f['active'],[]);self.assertEqual(f['started_count'],0)
            self.assertIsNone(f['acceleration_world_m_per_s2'])
        elif id=='S12':
            obj=evaluate(compiled,['3'])['samples'][0]['objects']['ball']
            self.assert_vector(obj['position_m'],expected['position_m'])
            self.assert_vector(obj['velocity_m_per_s'],expected['velocity_m_s'])
            self.assertEqual(obj['forces']['completed_count'],expected['completed_count'])
        else:self.fail('Missing supplemental case checker '+id)


# Concrete, discoverable test names keep each frozen case independently visible.
def source_test(case, extra=False):
    def run(self):
        (self.check_extra if extra else self.check_original)(case)
    run.__doc__ = 'Adopted '+case['id']+': '+case['name']
    return run


for _case in CASES.values():
    setattr(ForceSourceCases,'test_'+_case['id']+'_'+_case['name'].replace('-','_'),source_test(_case))
for _case in EXTRA.values():
    setattr(ForceSourceCases,'test_'+_case['id']+'_'+_case['name'].replace('-','_'),source_test(_case,True))


class ForceSourceIntegrityTests(unittest.TestCase):
    def test_additive_erratum_preserves_original_bundles_and_expected_outcomes(self):
        self.assertEqual(hashlib.sha256((DATA/'reviewed-acceptance.json').read_bytes()).hexdigest(),
                         '2311dc26425cd3257df33e71e3246e2b6e14bba887da55bddc4b26915492c420')
        for id, correction in CORRECTIONS.items():
            original=load_file_manifest(DATA/correction['original_file_manifest']); updated=bundle(id)
            self.assertEqual(original.program_revision,correction['original_program_revision'])
            self.assertEqual(original.entry.revision,correction['original_source_sha256'])
            self.assertEqual(updated.entry.revision,correction['source_sha256'])
            self.assertEqual(updated.program_revision,correction['program_revision'])
            self.assertEqual(original.entry.text.replace(correction['replaced_utf8'],correction['replacement_utf8']),updated.entry.text)
            self.assertEqual(original.modules,updated.modules)
            self.assertEqual(correction['expected'],EXTRA[id]['expected'])

    def test_zero_before_side_erratum_matches_unchanged_earlier_source_semantics(self):
        from test_force_contract import legacy_projection
        original = compile_construction(legacy_projection(bundle('P09'))).model
        before = evaluate_prefix(original,'0',side='before')['last_valid_state']['objects']['ball']
        correction = ERRATA['sample_corrections'][0]
        self.assertEqual(before['velocity_m_per_s'],correction['new']['velocity_m_s'])
        self.assertEqual(before['angular_velocity_rad_per_s'],correction['new']['omega_world_rad_s'])
        after = evaluate_prefix(original,'0',side='after')['last_valid_state']['objects']['ball']
        self.assertNotEqual(after['velocity_m_per_s'],before['velocity_m_per_s'])

    def test_lowered_payload_is_frozen_and_sequences_include_nonforce_events(self):
        from dataclasses import FrozenInstanceError
        compiled=model('P09');force=next(e.force for b in compiled.events for e in b.events if e.force)
        self.assertEqual(force.sequence_index,1)
        with self.assertRaises(FrozenInstanceError):force.key='changed'

    def test_initial_construction_is_before_zero_activation(self):
        initial=construct(model('P14'))['initial_state']
        self.assertEqual(initial['side'],'before')
        self.assertEqual(initial['objects']['ball']['forces']['active'],[])


if __name__=='__main__':unittest.main()
