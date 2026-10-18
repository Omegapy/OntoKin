"""Transport version boundaries and bounded encoding before effects."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import load_bundle
from ontokin.json_limits import measure_json, bounded_dumps, JSONLimitError
from ontokin.program_protocol import canonical_request, validate_request

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = json.loads((ROOT/'docs/language-design/construction-v0.1/01-keyed-rack/program.bundle.json').read_text())


class ProgramProtocolTests(unittest.TestCase):
    def create_request(self):
        return {'schema_version':'ontokin.agent/0.2','project_id':'p','request_id':'create','operation':'create',
                'bundle':copy.deepcopy(PAYLOAD),'expected_program_revision':None,'requested_level':'represented'}

    def test_new_envelope_requires_program_fields_and_explicit_protocol(self):
        request = self.create_request()
        validate_request(request)
        for replacement in ({'schema_version':'ontokin.agent/0.1'}, {'expected_revision':None}, {'source_revision':load_bundle(PAYLOAD).entry.revision}):
            invalid = {**request, **replacement}
            with self.subTest(replacement=replacement), self.assertRaises(ProtocolError):
                validate_request(invalid)
        good = {'schema_version':'ontokin.agent/0.2','project_id':'p','request_id':'inspect','operation':'inspect',
                'program_revision':load_bundle(PAYLOAD).program_revision,'selector':{'element_id':['a']*256},'fields':['identity'],'limit':1}
        validate_request(good)
        for delta in ({'limit':1.0},{'selector':{'element_id':['a']*257}},{'program_revision':'sha256:'+'G'*64},{'destination':'ontokin.glb/0.1'}):
            with self.subTest(delta=delta), self.assertRaises(ProtocolError):
                validate_request({**good, **delta})

    def test_malformed_bundle_has_transport_error_before_candidate(self):
        request = self.create_request()
        request['bundle']['modules'].append(copy.deepcopy(request['bundle']['modules'][0]))
        with self.assertRaises(ProtocolError) as caught:
            validate_request(request)
        self.assertEqual(caught.exception.code, 'OKA-E-REQUEST')
        request = self.create_request()
        request['bundle']['entry']['source'] = 'invalid OntoKin source but a valid sealed transport'
        validate_request(request)
        self.assertTrue(load_bundle(request['bundle']).program_revision.startswith('sha256:'))

    def test_exact_utf8_json_size_and_logically_repeated_values(self):
        values = [None, True, False, 0, -17, 1.25, 'é😀\\"\n\u0001', {'é':['x',{},[]]}]
        for value in values:
            expected = json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
            self.assertEqual(measure_json(value)['bytes'],len(expected))
        shared = ['x']*10
        repeated = [shared]*10
        self.assertEqual(measure_json(repeated)['entries'],111)
        with self.assertRaises(JSONLimitError):
            measure_json(repeated,max_entries=110)
        cyclic=[];cyclic.append(cyclic)
        with self.assertRaises(ValueError):
            measure_json(cyclic)

    def test_oversized_shared_graph_fails_before_json_string_allocation(self):
        value = {'data':['x'*100000]*50}
        with patch('ontokin.json_limits.json.dumps', side_effect=AssertionError('unbounded encoding attempted')):
            with self.assertRaises(JSONLimitError):
                bounded_dumps(value)
        request = self.create_request()
        request['bundle']['entry']['source'] = 'x'*(4*1024*1024)
        with self.assertRaises(ProtocolError) as caught:
            canonical_request(request)
        self.assertEqual(caught.exception.code,'OKA-E-RESOURCE')

    def test_cli_requires_version_selection_and_keeps_stores_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            request = self.create_request()
            result = subprocess.run([sys.executable,'-m','ontokin','agent','--protocol','ontokin.agent/0.2','--store',directory,'--wait'],
                                    input=json.dumps(request)+'\n',text=True,capture_output=True,cwd=ROOT,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            response=json.loads(result.stdout)
            self.assertEqual(response['status'],'succeeded',response)
            self.assertEqual(response['schema_version'],'ontokin.agent/0.2')
            self.assertNotIn('source_revision',response)
            self.assertEqual(response['program_revision'],load_bundle(PAYLOAD).program_revision)
            old=subprocess.run([sys.executable,'-m','ontokin','agent','--store',directory,'--wait'],input=json.dumps(request)+'\n',
                               text=True,capture_output=True,cwd=ROOT,timeout=20)
            self.assertEqual(json.loads(old.stdout)['schema_version'],'ontokin.agent/0.1')
            self.assertEqual(json.loads(old.stdout)['status'],'rejected')
            self.assertTrue((Path(directory)/'agent.sqlite3').exists())
            self.assertTrue((Path(directory)/'program-agent.sqlite3').exists())

    def test_cli_invalid_json_still_returns_selected_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            result=subprocess.run([sys.executable,'-m','ontokin','agent','--protocol','ontokin.agent/0.2','--store',directory,'--wait'],
                                  input='{"request_id":"a","request_id":"b"}\n',text=True,capture_output=True,cwd=ROOT,timeout=20)
            response=json.loads(result.stdout)
            self.assertEqual(response['schema_version'],'ontokin.agent/0.2')
            self.assertEqual(response['protocol_error']['code'],'OKA-E-JSON')


if __name__ == '__main__':
    unittest.main()
