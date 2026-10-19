"""Actual Agent/0.5 messages and deliberate rehashed evidence counterexamples.

Schema dependencies are verification-only; dedicated CI must execute this file.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

HAS_SCHEMA = all(importlib.util.find_spec(n) for n in ('jsonschema', 'referencing'))

@unittest.skipUnless(HAS_SCHEMA, 'Run dedicated Force Agent verification with its pinned schema tools')
class ForceAgentEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_force_agent_demo import Recorder
        from tools.verify_force_agent_workflow import SchemaChecks
        cls.base = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.base.name) / 'workflow'
        cls.recorded = Recorder(cls.directory).build()
        cls.schemas = SchemaChecks()

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / 'workflow'
        shutil.copytree(type(self).directory, self.directory, ignore=shutil.ignore_patterns('service-store'))
        self.manifest = json.loads((self.directory / 'workflow.json').read_text())

    def save_manifest(self):
        from tools.build_force_agent_demo import write_json
        write_json(self.directory / 'workflow.json', self.manifest)

    def change(self, role, mutate, kind='response'):
        from tools.build_force_agent_demo import write_json, sha
        entry = next(r for r in self.manifest['exchanges'] if r['role'] == role)
        path = self.directory / entry[kind + '_file']
        document = json.loads(path.read_text())
        mutate(document)
        write_json(path, document)
        # Rehash: rejecting a checksum mismatch alone does not test the audit.
        entry[kind + '_sha256'] = sha(path.read_bytes())
        self.save_manifest()

    def reject(self, pattern=None):
        from tools.verify_force_agent_workflow import EvidenceError, verify
        if pattern:
            with self.assertRaisesRegex(EvidenceError, pattern): verify(self.directory, self.schemas)
        else:
            with self.assertRaises(EvidenceError): verify(self.directory, self.schemas)

    def sample_role(self, case='P01', time='1.5', side='after'):
        for row in self.manifest['exchanges']:
            if row['role'].startswith(case + '/sample/'):
                q = json.loads((self.directory / row['request_file']).read_text())
                if float(q['time']['seconds']) == float(time) and q['time']['side'] == side: return row['role']
        self.fail('Fixture sample not found')

    def test_actual_workflow_passes_without_compiler_or_evaluator(self):
        from tools.verify_force_agent_workflow import verify
        with patch('ontokin.construction.compile_construction', side_effect=AssertionError('Compiler called')), patch('ontokin.evaluator._Simulator', side_effect=AssertionError('Evaluator called')):
            result = verify(self.directory, self.schemas)
        self.assertEqual((result['exchanges'], result['source_snapshots'], result['predetermined_samples']), (418, 25, 334))
        self.assertFalse(result['full_force_release_complete'])
        self.assertFalse(result['destination_validated'])

    def test_rehashed_last_valid_position_is_not_accepted(self):
        self.change('P01/run', lambda d: d['result']['run_state']['last_valid_state']['objects']['ball']['position_m'].__setitem__(0, 99))
        self.reject('position_m')

    def test_rehashed_initial_active_force_count_is_not_accepted(self):
        entry = next(r for r in self.manifest['exchanges'] if r['role'] == self.sample_role())
        forces = json.loads((self.directory / entry['response_file']).read_text())['result']['items'][0]['state']['forces']
        self.change('P01/create', lambda d: d['result']['initial_state']['objects']['ball'].__setitem__('forces', copy.deepcopy(forces)))
        self.reject('force set|start count')

    def test_rehashed_duplicate_run_id_across_projects_is_not_accepted(self):
        run1 = next(r for r in self.manifest['exchanges'] if r['role'] == 'P01/run')
        run2 = next(r for r in self.manifest['exchanges'] if r['role'] == 'P02/run')
        before = json.loads((self.directory / run2['response_file']).read_text())['run_id']
        after = json.loads((self.directory / run1['response_file']).read_text())['run_id']
        def replace(value):
            if isinstance(value, dict):
                for k, v in value.items(): value[k] = replace(v)
            elif isinstance(value, list): value[:] = [replace(v) for v in value]
            elif value == before: return after
            return value
        for row in list(self.manifest['exchanges']):
            if row['role'].startswith('P02/'):
                for kind in ('request', 'response'): self.change(row['role'], replace, kind)
        self.reject('Run identity')

    def test_rehashed_success_receipt_cannot_use_unrequested_frame(self):
        self.change(self.sample_role(), lambda d: d.__setitem__('frame', 'ball.frame'), 'request')
        self.reject('frame')

    def test_rehashed_wrong_source_manifest_is_rejected(self):
        self.change('P01/run', lambda d: d['result']['source_manifest']['units'][0].__setitem__('filename', 'other.ok'))
        self.reject('manifest')

    def test_rehashed_active_force_vector_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces']['active'][0]['force_world_n'].__setitem__(0, 7))
        self.reject('force_world_n')

    def test_rehashed_force_source_span_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces']['active'][0]['source_location'].__setitem__('start_byte', 0))
        self.reject('source_location')

    def test_rehashed_force_sequence_index_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces']['active'][0].__setitem__('sequence_index', 9))
        self.reject('sequence_index')

    def test_rehashed_completion_clock_cannot_round_away_source_time(self):
        role = self.sample_role('P16', '0.2')
        self.change(role, lambda d: d['result']['items'][0]['state']['forces']['active'][0].__setitem__('completion_time_seconds', '0.3'))
        self.reject('completion_time_seconds')

    def test_rehashed_missing_completed_history_is_rejected(self):
        self.change(self.sample_role(time='2'), lambda d: d['result']['items'][0]['state']['forces']['last_changes'][0].__setitem__('kind', 'started'))
        self.reject('history')

    def test_rehashed_extra_schema_field_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces'].__setitem__('secret_force', 1))
        self.reject('schema')

    def test_rehashed_boolean_force_count_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces'].__setitem__('started_count', True))
        self.reject('schema')

    def test_rehashed_forged_acceleration_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state']['forces']['acceleration_world_m_per_s2'].__setitem__(0, 5))
        self.reject('acceleration')

    def test_rehashed_writable_authority_cannot_expand_to_sibling(self):
        self.change('P11/authority', lambda d: d['result']['items'][0]['source']['writable_spans'][0].__setitem__('start_byte', 0))
        self.reject('writable span')

    def test_rehashed_repair_cannot_change_frozen_patch(self):
        self.change('P12/repair', lambda d: d['patches'][0].__setitem__('replacement', '9'), 'request')
        self.reject()

    def test_rehashed_failed_edit_cannot_advance_head(self):
        self.change('P12/stale', lambda d: d.__setitem__('accepted_program_revision', 'sha256:' + '0'*64))
        self.reject('accepted revision')

    def test_rehashed_identical_retry_cannot_change_receipt(self):
        self.change('retry/same', lambda d: d['progress'].__setitem__('phase', 'different'))
        self.reject('receipt')

    def test_rehashed_reset_cannot_retain_force_history(self):
        self.change('prefix/reset', lambda d: d['result']['run_state']['last_valid_state']['objects']['ball']['forces'].__setitem__('started_count', 2))
        self.reject()

    def test_rehashed_self_velocity_is_world_measured_not_relative_zero(self):
        self.change('frame/self', lambda d: d['result']['items'][0]['state'].__setitem__('velocity_m_per_s', [0, 0, 0]))
        self.reject('velocity')

    def test_rehashed_missing_trace_entry_is_rejected(self):
        self.manifest['exchanges'].pop(1)
        for i, row in enumerate(self.manifest['exchanges'], 1): row['sequence'] = i
        self.manifest['exchange_count'] -= 1
        self.save_manifest(); self.reject()

    def test_rehashed_snapshot_cannot_replace_pinned_library(self):
        from tools.build_force_agent_demo import write_json, sha
        row = self.manifest['snapshots'][0]; p = self.directory / row['bundle_file']
        data = json.loads(p.read_text()); data['modules'][0]['source'] += '\n'
        write_json(p, data); row['bundle_sha256'] = sha(p.read_bytes())
        self.save_manifest(); self.reject('Snapshot')

    def test_path_traversal_is_rejected(self):
        self.manifest['exchanges'][0]['request_file'] = '../outside.json'
        self.save_manifest(); self.reject('Unsafe evidence path')

    def test_symlink_is_rejected(self):
        row = self.manifest['exchanges'][0]; p = self.directory / row['request_file']
        outside = Path(self.tmp.name) / 'outside.json'; outside.write_bytes(p.read_bytes())
        p.unlink(); p.symlink_to(outside); self.reject('symlink')

    def test_duplicate_json_key_and_nonfinite_number_rejected(self):
        from tools.verify_force_agent_workflow import EvidenceError, decode
        for value in (b'{"a":0,"a":1}', b'{"a":NaN}', b'{"a":1e999}'):
            with self.subTest(value=value), self.assertRaises(EvidenceError): decode(value)

    def test_unknown_schema_reference_does_not_fetch_network(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry
        from referencing.exceptions import NoSuchResource
        def deny(uri): raise NoSuchResource(ref=uri)
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network access')):
            v = Draft202012Validator({'$ref':'https://invalid.example/schema'}, registry=Registry(retrieve=deny))
            with self.assertRaises(Exception) as result: list(v.iter_errors({}))
            self.assertNotIsInstance(result.exception, AssertionError)

    def test_rehashed_missing_force_projection_is_rejected(self):
        self.change(self.sample_role(), lambda d: d['result']['items'][0]['state'].pop('forces'))
        self.reject()

    def test_rehashed_duplicate_request_id_requires_collision_receipt(self):
        first = self.sample_role(time='1')
        row = next(r for r in self.manifest['exchanges'] if r['role'] == first)
        request_id = json.loads((self.directory / row['request_file']).read_text())['request_id']
        for kind in ('request', 'response'):
            self.change(self.sample_role(), lambda d: d.__setitem__('request_id', request_id), kind)
        self.reject('request ID')

    def test_writer_does_not_overwrite_existing_evidence(self):
        from tools.build_force_agent_demo import Recorder
        before = (self.directory / 'workflow.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'empty output'): Recorder(self.directory)
        self.assertEqual((self.directory / 'workflow.json').read_bytes(), before)
