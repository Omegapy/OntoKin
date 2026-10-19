"""Review authored force fixtures independently of any force implementation."""
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import unittest

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/language-design/force-v0.1'
BASE_HASH = 'de423575e648ea9e14d8de8d5bb9b2bbe6330ae6fb01e182e34c3cb6df9d2ba2'
BASE = json.loads((DATA / 'acceptance.json').read_text())
CASES = {c['id']: c for c in BASE['source_cases']}
REVIEW = json.loads((DATA / 'reviewed-acceptance.json').read_text())
EXTRA = {c['id']: c for c in REVIEW['source_cases']}


def rational(c):
    return Q(int(c['numerator']), int(c['denominator']))


def sample(id, time, side='after', target='ball'):
    return next(s for s in CASES[id]['expected_samples']
                if rational(s['time']) == Q(time) and s['side'] == side and s['target'] == target)


def legacy_projection(bundle):
    text = re.sub(r'(?m)^\s*force [^\n]*;\s*$', '', bundle.entry.text)
    text = text.replace('"0.5"', '"0.4"').replace('"force-0.1"', '"impulse-0.1"')
    return ProgramBundle(replace(bundle.entry, raw=text.encode()), bundle.modules)


class ForceContractReviewTests(unittest.TestCase):
    def test_original_corpus_and_author_remain_byte_identical(self):
        self.assertEqual(hashlib.sha256((DATA/'acceptance.json').read_bytes()).hexdigest(), BASE_HASH)
        spec = importlib.util.spec_from_file_location('force_fixture_author', DATA/'author_fixtures.py')
        author = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(author)
        for name, raw in author.build(ROOT).items():
            self.assertEqual((DATA/name).read_bytes(), raw, name)

    def test_every_complete_bundle_and_force_span_matches_actual_bytes(self):
        self.assertEqual(len(CASES), 44)
        self.assertEqual(len(EXTRA), 12)
        for c in [*CASES.values(), *EXTRA.values()]:
            with self.subTest(case=c['id']):
                b = load_file_manifest(DATA/c['file_manifest'])
                self.assertEqual(b.program_revision, c['program_revision'])
                self.assertEqual(b.entry.revision, c['source_sha256'])
                for span in c.get('force_statements', []):
                    self.assertEqual(b.entry.raw[span['start_byte']:span['end_byte']].decode(), span['text'])

    def test_inherited_source_projection_compiles_without_preparing_geometry(self):
        selected = [c for c in CASES.values() if c['kind'] == 'positive']
        selected += [EXTRA[i] for i in ('S01','S07','S08','S09','S12')]
        for c in selected:
            with self.subTest(case=c['id']):
                compile_construction(legacy_projection(load_file_manifest(DATA/c['file_manifest'])))

    def test_scoped_repair_bytes_and_pinned_siblings(self):
        for c in CASES.values():
            if 'repair' not in c:
                continue
            r = c['repair']
            before = load_file_manifest(DATA/CASES[r['from_case']]['file_manifest'])
            after = load_file_manifest(DATA/c['file_manifest'])
            self.assertEqual(before.entry.raw[r['start_byte']:r['end_byte']].decode(),r['expected_text'])
            self.assertEqual(before.entry.raw[:r['start_byte']]+r['replacement'].encode()+before.entry.raw[r['end_byte']:], after.entry.raw)
            self.assertEqual(before.modules, after.modules)
            a = [s for s in CASES[r['from_case']]['expected_samples'] if s['target']==r['unchanged_sibling']]
            b = [s for s in c['expected_samples'] if s['target']==r['unchanged_sibling']]
            keyed_a = {(rational(s['time']),s['side']):s for s in a}
            keyed_b = {(rational(s['time']),s['side']):s for s in b}
            for key in keyed_a.keys() & keyed_b.keys():
                self.assertEqual(keyed_a[key], keyed_b[key])
            # A repaired duration adds sample clocks. Compare the unchanged
            # sibling against its own closed form at every clock, not row order.
            for s in a+b:
                t = rational(s['time'])
                x = Q(3) if t <= 1 else Q(3)+(t-1)**2/2 if t <= 2 else Q(7,2)+(t-2)
                self.assertEqual(s['position_m'],[float(x),0,0])

    def test_independent_single_interval_momentum_and_work(self):
        s = sample('P01', 2)
        self.assertEqual(s['position_m'], [1,0,0])
        self.assertEqual(s['velocity_m_s'], [2,0,0])
        self.assertEqual(2*s['velocity_m_s'][0],4*1)
        self.assertEqual(.5*2*s['velocity_m_s'][0]**2,4*s['position_m'][0])
        self.assertEqual(sample('P01',3)['position_m'],[3,0,0])
        self.assertEqual(s['active_keys'],[])
        self.assertEqual(sample('P01',2,'before')['active_keys'],['push'])

    def test_independent_overlap_gravity_and_spin_outcomes(self):
        for t,x,v in [(0,0,0),(1,1,2),(2,3.5,3),(3,6,2),(4,8,2)]:
            self.assertEqual(sample('P02',t)['position_m'],[x,0,0])
            self.assertEqual(sample('P02',t)['velocity_m_s'],[v,0,0])
        self.assertEqual(sample('P06',3)['position_m'],[0,-30,0])
        self.assertEqual(sample('P06',3)['velocity_m_s'],[0,-20,0])
        spin=sample('P07',3)
        self.assertEqual(spin['position_m'],[8,2,0])
        self.assertEqual(spin['omega_world_rad_s'],[0,0,5])
        self.assertAlmostEqual(abs(spin['orientation_wxyz'][0]),abs(math.cos(5)))
        self.assertEqual(sample('P09',3)['position_m'],[5,-3,0])
        self.assertEqual(sample('P09',3)['velocity_m_s'],[2,-9,0])

    def test_no_effect_boundaries_preserve_trajectory_anchor(self):
        for id in ('P03','P05'):
            self.assertTrue(all(rational(s['anchor_time'])==0 for s in CASES[id]['expected_samples']))
        self.assertEqual(rational(sample('P04',1)['anchor_time']),0)
        self.assertEqual(sample('P04',1)['active_keys'],['b'])
        self.assertEqual(sample('P04',1)['started_count'],2)
        self.assertEqual(sample('P04',1)['completed_count'],1)

    def test_exact_endpoints_are_not_replaced_by_decimal_addition(self):
        s=sample('P16',Q.from_float(.1))
        end=rational(s['active_ends']['push'])
        self.assertEqual(end,Q.from_float(.1)+Q.from_float(.2))
        self.assertNotEqual(end,Q.from_float(.3))
        large=sample('P18',Q.from_float(1e308))
        self.assertGreater(rational(large['active_ends']['push']),Q.from_float(sys.float_info.max))
        small=rational(EXTRA['S09']['expected']['completion_clock'])
        self.assertEqual(small,Q.from_float(math.ulp(0.0)))

    def test_extreme_oracles_require_final_rational_aggregation(self):
        self.assertTrue(math.isinf(1e308+1e308))
        self.assertEqual(sample('P19',1)['position_m'],[.5,0,0])
        self.assertEqual(sample('P19',1)['velocity_m_s'],[1,0,0])
        self.assertTrue(math.isinf(1e308/.5))
        self.assertEqual(sample('P20',0)['acceleration_world_m_s2'],[1e308,0,0])

    def test_interior_overflow_has_finite_endpoints_and_a_valid_short_prefix(self):
        p,v,a=map(Q.from_float,(1e308,1.4e308,-1e308))
        peak=-v/a
        self.assertTrue(math.isfinite(float(p+v*3+a*9/2)))
        self.assertGreater(p+v*peak+a*peak*peak/2,Q.from_float(sys.float_info.max))
        bundle=legacy_projection(load_file_manifest(DATA/EXTRA['S05']['file_manifest']))
        text=bundle.entry.text.replace('vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2])','vector(world, -1e308[m/s^2], 0[m/s^2], 0[m/s^2])')
        # Supply an equivalent inherited-gravity trajectory with an endpoint
        # source boundary. This establishes diagnostic side before force code.
        text=text.replace('    at 0[s] sequence {','    at 3[s] sequence {')
        compiler=compile_construction(ProgramBundle(replace(bundle.entry,raw=text.encode()),bundle.modules))
        self.assertIsNone(evaluate_prefix(compiler.model,'0.25')['failure'])
        result=evaluate_prefix(compiler.model,'3')
        self.assertEqual(result['failure'].code,'OKL-E-NUMERIC')
        self.assertEqual(result['failure'].diagnostic.side,'before')


if __name__ == '__main__':
    unittest.main()
