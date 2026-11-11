"""Finite CPU admission controls for the direct-Python source harness.

Large requested work is rejected before it is performed. These tests start no
child process, native export, receiving process or lifecycle stub.
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01.canonical import json_bytes
from prototypes.static_tray_v01.errors import PROFILE,TrayError
from prototypes.static_tray_v01.fixtures import qualification_sets,write_sources
from prototypes.static_tray_v01.sources import lower_source


class StaticTraySourceResourcesTests(unittest.TestCase):
    def setUp(self):
        capture=os.environ.get('ONTOKIN_STATIC_TRAY_RESOURCE_CAPTURE')
        self.capture=bool(capture)
        if capture:
            self.root=Path(capture)/self._testMethodName
            self.root.mkdir(parents=True,exist_ok=False)
        else:
            self.temp=tempfile.TemporaryDirectory()
            self.addCleanup(self.temp.cleanup)
            self.root=Path(self.temp.name)
        self.serial=0
        self.rejections=[]

    def tearDown(self):
        if self.capture:
            inventory=[]
            for path in sorted(self.root.rglob('*')):
                if path.is_file():
                    data=path.read_bytes()
                    inventory.append({'path':path.relative_to(self.root).as_posix(),
                                      'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)})
            (self.root/'CONTROL-RECEIPT.json').write_bytes(json_bytes({
                'method':self._testMethodName,'scope':'CPU finite source controls; no native starts',
                'rejections':self.rejections,'files':inventory}))

    def source(self,extra=b"",*,helper=False):
        self.serial+=1
        manifest=write_sources(self.root/str(self.serial),'direct-python',qualification_sets()['Q01'])
        if extra:
            file=manifest.parent/('tray.py' if helper else 'main.py')
            file.write_bytes(file.read_bytes()+extra)
            self.rebind(manifest)
        return manifest

    def rebind(self,manifest):
        value=json.loads(manifest.read_bytes())
        for entry in value['files']:
            data=(manifest.parent/entry['filename']).read_bytes()
            entry['source_revision']='sha256:'+hashlib.sha256(data).hexdigest()
            entry['size_bytes']=len(data)
        manifest.write_bytes(json_bytes(value))

    def reject(self,manifest,code):
        with self.assertRaises(TrayError) as caught:
            lower_source('direct-python',manifest,PROFILE)
        self.assertEqual(caught.exception.code,'OTRAY-E-'+code)
        self.rejections.append({'manifest':manifest.relative_to(self.root).as_posix(),
                                'expected':'OTRAY-E-'+code,'actual':caught.exception.code})

    def test_frozen_source_still_uses_two_actual_helper_calls(self):
        result=lower_source('direct-python',self.source(),PROFILE)
        self.assertEqual(result.provenance['actual_helper_calls'],2)
        self.assertEqual(result.provenance['helper_calls'],['left','right'])
        self.assertLess(result.provenance['source_operations'],100000)
        self.assertGreater(result.provenance['source_operations'],result.provenance['source_trace_events'])

    def test_builtin_reduction_is_charged_per_item(self):
        outcomes=[]
        for count in (100,200):
            result=lower_source('direct-python',self.source(('unused=sum(range('+str(count)+'))\n').encode()),PROFILE)
            outcomes.append(result)
        self.assertEqual(outcomes[0].canonical_bytes,outcomes[1].canonical_bytes)
        # CPython can activate opcode notifications between successive compilations.
        # Separate charged builtin work from that observable tracing variation.
        guarded=[r.provenance['source_operations']-r.provenance['source_trace_events'] for r in outcomes]
        self.assertGreater(guarded[1]-guarded[0],100)

    def test_huge_builtin_requests_fail_before_materialization(self):
        for expression in ('sum(range(1000000000))','list(range(1000000000))',
                           'tuple(range(1000000000))','dict(zip(range(1000000000),range(1000000000)))'):
            with self.subTest(expression=expression):
                self.reject(self.source(('unused='+expression+'\n').encode()),'RESOURCE')

    def test_unbounded_operators_fail_before_execution(self):
        for expression in ('2 ** 1000000000','1 << 1000000000','"x" * 1000000000','[0] * 1000000000'):
            with self.subTest(expression=expression):
                self.reject(self.source(('unused='+expression+'\n').encode()),'SHAPE')

    def test_fraction_pack_and_public_methods_have_finite_surface(self):
        for expression in ('Fraction("1e1000000000")','pack("1000000000s",b"x")',
                           '"x".rjust(1000000000)','dict.fromkeys(range(1000000000))'):
            with self.subTest(expression=expression):
                self.reject(self.source(('unused='+expression+'\n').encode(),helper=True),'SHAPE')

    def test_nested_values_and_builtin_work_share_the_source_budget(self):
        self.reject(self.source(b'unused=sum(sum(range(512)) for item in range(64))\n'),'RESOURCE')
        self.reject(self.source(b'a=[]\na.append(a)\n'),'SHAPE')

    def test_alias_growth_is_bounded_before_result_serialization(self):
        # Each dictionary has only two keys, but repeated aliases would otherwise
        # expand exponentially when the helper snapshot is serialized.
        manifest=self.source()
        file=manifest.parent/'tray.py'
        raw=file.read_bytes().replace(b'def make_tray(side, values):\n',
            b'def make_tray(side, values):\n    alias={}\n    for item in range(32):\n        larger={}\n        larger["a"]=alias\n        larger["b"]=alias\n        alias=larger\n    return alias\n')
        file.write_bytes(raw)
        self.rebind(manifest)
        self.reject(manifest,'RESOURCE')

    def test_bulk_and_untransformed_assignment_paths_are_rejected(self):
        variants=(
            b'scratch=[]\nfor item in range(3):\n    scratch[0:0]=range(4096)\nassert scratch[8191] == 4095\n',
            b'scratch=[0]\nscratch[:]=scratch\n',
            b'scratch=[0]\ndel scratch[:]\n',
            b'scratch=[0]\nfor scratch[0] in range(2):\n    pass\n',
            b'scratch={}\nscratch["a"],other=(1,2)\n',
            b'scratch={}\nscratch["a"]:int=1\n',
            b'*scratch,=(item for item in range(4096))\n',
            b'scratch=[*range(4096)]\n',
        )
        for extra in variants:
            with self.subTest(source=extra):
                self.reject(self.source(extra),'SHAPE')

    def test_plain_item_assignment_remains_bounded_and_preserves_order(self):
        base=lower_source('direct-python',self.source(),PROFILE)
        extra=(b'scratch={"a":1}\nscratch["b"]=2\nvalues=[1,2]\nvalues[0]=3\n'
               b'assert scratch["b"] == 2\nassert values[0] == 3\n'
               b'order=[]\ndef rhs():\n    order.append("rhs")\n    return 1\n'
               b'def target():\n    order.append("target")\n    return scratch\n'
               b'def key():\n    order.append("key")\n    return "x"\n'
               b'target()[key()]=rhs()\nassert order == ["rhs","target","key"]\n')
        actual=lower_source('direct-python',self.source(extra),PROFILE)
        self.assertEqual(actual.canonical_bytes,base.canonical_bytes)
        self.reject(self.source(b'scratch={}\nscratch["self"]=scratch\n'),'SHAPE')
        self.reject(self.source(b'scratch={}\nfor item in range(4096):\n    scratch[item]=item\n'),'RESOURCE')

    def test_hidden_internal_helper_calls_are_counted(self):
        manifest=self.source()
        file=manifest.parent/'tray.py'
        raw=file.read_bytes()
        raw=raw.replace(b'def make_tray(side, values):\n',
            b'def make_tray(side, values):\n    if "recursed" not in values:\n        values=dict(values)\n        values["recursed"]=True\n        return make_tray(side,values)\n')
        file.write_bytes(raw)
        self.rebind(manifest)
        self.reject(manifest,'SHAPE')

    def test_manifest_and_source_reads_are_bounded(self):
        manifest=self.source()
        original=Path.read_bytes
        def no_unbounded_candidate_reads(path):
            if path.parent==manifest.parent:
                raise AssertionError('Candidate binding attempted unbounded read_bytes')
            return original(path)
        with patch.object(Path,'read_bytes',no_unbounded_candidate_reads):
            result=lower_source('direct-python',manifest,PROFILE)
        self.assertEqual(result.provenance['actual_helper_calls'],2)
        oversized=self.source()
        oversized.write_bytes(b' '*32769)
        self.reject(oversized,'RESOURCE')
        oversized=self.source()
        (oversized.parent/'main.py').write_bytes(b' '*32769)
        self.reject(oversized,'CLOSURE')

    def test_hardlinked_units_cannot_fake_two_distinct_files(self):
        manifest=self.source()
        (manifest.parent/'main.py').unlink()
        os.link(manifest.parent/'tray.py',manifest.parent/'main.py')
        self.rebind(manifest)
        self.reject(manifest,'CLOSURE')

    def test_external_deadline_callback_is_honored_inside_reductions(self):
        manifest=self.source(b'unused=sum(range(200))\n')
        fired=False
        def outer_deadline():
            nonlocal fired
            frame=sys._getframe()
            while frame is not None:
                if frame.f_code.co_name=='reduction' and frame.f_code.co_filename.endswith('/sources.py'):
                    fired=True
                    raise TrayError('RESOURCE','Controlled earlier outer deadline inside reduction')
                frame=frame.f_back
        with self.assertRaises(TrayError) as caught:
            lower_source('direct-python',manifest,PROFILE,check=outer_deadline)
        self.assertEqual(caught.exception.code,'OTRAY-E-RESOURCE')
        self.assertTrue(fired)


if __name__=='__main__':
    unittest.main()
