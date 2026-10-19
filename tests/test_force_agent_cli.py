"""Explicit force protocol selection through subprocess JSONL transport."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_force_agent as support

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = 'ontokin.agent/0.5'


class ForceAgentCLITests(unittest.TestCase):
    def invoke(self, directory, payload, *, selected=True):
        args = [sys.executable, '-m', 'ontokin', 'agent', '--store', str(directory), '--wait']
        if selected: args += ['--protocol', PROTOCOL]
        process = subprocess.run(args, input=payload, capture_output=True, cwd=ROOT, timeout=30)
        self.assertEqual(process.stderr, b'')
        return process.returncode, [json.loads(line) for line in process.stdout.splitlines()]

    def test_selected_protocol_survives_malformed_json_then_valid_create(self):
        b = support.source_case('P01')
        request = dict(schema_version=PROTOCOL, project_id='cli', request_id='create', operation='create',
                       bundle=b.to_payload(), expected_program_revision=None, requested_level='constructed')
        payload = b'{"broken":\n' + json.dumps(request).encode() + b'\n'
        with tempfile.TemporaryDirectory() as directory:
            code, results = self.invoke(directory, payload)
            self.assertEqual(code, 0)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['schema_version'], PROTOCOL)
            self.assertEqual(results[0]['protocol_error']['code'], 'OKA-E-JSON')
            self.assertEqual(results[1]['status'], 'succeeded')
            self.assertEqual(results[1]['accepted_program_revision'], b.program_revision)
            self.assertTrue((Path(directory)/'force-program-agent.sqlite3').is_file())
            self.assertFalse((Path(directory)/'agent.sqlite3').exists())

    def test_default_transport_keeps_original_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            _, results = self.invoke(directory, b'{"broken":\n', selected=False)
            self.assertEqual(results[0]['schema_version'], 'ontokin.agent/0.1')
            self.assertFalse((Path(directory)/'force-program-agent.sqlite3').exists())

    def test_corrupt_force_store_returns_controlled_error_without_replacement(self):
        for mode in ('file', 'directory'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'force-program-agent.sqlite3'
                if mode == 'file': path.write_bytes(b'not a database; preserve these bytes')
                else: path.mkdir()
                code, results = self.invoke(directory, b'')
                self.assertNotEqual(code, 0)
                self.assertEqual(results[0]['schema_version'], PROTOCOL)
                self.assertEqual(results[0]['protocol_error']['code'], 'OKA-E-STORE')
                if mode == 'file': self.assertEqual(path.read_bytes(), b'not a database; preserve these bytes')
                else: self.assertEqual(list(path.iterdir()), [])

    def test_unavailable_delivery_returns_no_artifact_via_transport(self):
        """Keep the legacy transport guard for generic delivery without a named target."""
        b = support.source_case('P01')
        common = dict(schema_version=PROTOCOL, project_id='cli')
        requests = [dict(common, request_id='create', operation='create', bundle=b.to_payload(),
                         expected_program_revision=None, requested_level='constructed'),
                    dict(common, request_id='validate', operation='validate', program_revision=b.program_revision,
                         requested_level='delivered')]
        with tempfile.TemporaryDirectory() as directory:
            code, results = self.invoke(directory, b'\n'.join(json.dumps(r).encode() for r in requests)+b'\n')
            self.assertEqual(code, 0)
            self.assertEqual(results[0]['status'], 'succeeded')
            self.assertIn(results[1]['status'], ('failed', 'rejected'))
            self.assertNotEqual(results[1]['achieved_level'], 'delivered')
            self.assertEqual(results[1]['accepted_program_revision'], b.program_revision)
            self.assertIn('OKL-E-CAPABILITY-UNSUPPORTED', [d['code'] for d in results[1]['diagnostics']])
            with support.sqlite3.connect(Path(directory)/'force-program-agent.sqlite3') as db:
                self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0], 0)

    def test_delivery_returns_bound_artifact_via_transport(self):
        b = support.source_case('P01')
        common = dict(schema_version=PROTOCOL, project_id='cli')
        requests = [dict(common, request_id='create', operation='create', bundle=b.to_payload(),
                         expected_program_revision=None, requested_level='constructed'),
                    dict(common, request_id='export', operation='export', program_revision=b.program_revision,
                         destination='ontokin.glb/0.5', options={'end':'1.5','fps':2,'helpers':False})]
        with tempfile.TemporaryDirectory() as directory:
            code, results = self.invoke(directory, b'\n'.join(json.dumps(r).encode() for r in requests)+b'\n')
            self.assertEqual(code, 0)  # JSONL transport completion is not operation success.
            self.assertEqual(results[0]['status'], 'succeeded')
            self.assertEqual(results[1]['status'], 'succeeded', results[1])
            self.assertEqual(results[1]['achieved_level'], 'delivered')
            self.assertEqual(results[1]['result']['destination'], 'ontokin.glb/0.5')
            self.assertEqual(results[1]['result']['report']['program_revision'], b.program_revision)
            self.assertEqual(results[1]['result']['run_state']['valid_until_seconds'], '1.5')
            with support.sqlite3.connect(Path(directory)/'force-program-agent.sqlite3') as db:
                self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0], 1)

    def test_future_force_failure_returns_no_artifact_via_transport(self):
        b = support.source_case('P21')
        common = dict(schema_version=PROTOCOL, project_id='cli')
        request = dict(common, request_id='create', operation='create', bundle=b.to_payload(),
                       expected_program_revision=None, requested_level='delivered', destination='ontokin.glb/0.5')
        with tempfile.TemporaryDirectory() as directory:
            code, results = self.invoke(directory, json.dumps(request).encode()+b'\n')
            self.assertEqual(code, 0)
            self.assertEqual(results[0]['status'], 'failed')
            self.assertIsNone(results[0]['accepted_program_revision'])
            self.assertNotEqual(results[0]['achieved_level'], 'delivered')
            self.assertIn('OKL-E-NUMERIC', [d['code'] for d in results[0]['diagnostics']])
            with support.sqlite3.connect(Path(directory)/'force-program-agent.sqlite3') as db:
                self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0], 0)
