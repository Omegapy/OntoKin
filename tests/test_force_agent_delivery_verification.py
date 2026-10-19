"""Pure adversarial tests for retained delivery evidence.

These deliberately small transport/parser fixtures are not Agent conformance
evidence. They test the same reader methods used by the actual workflow audit,
without constructing a service or invoking the compiler, evaluator or exporter.
The actual recorder and full audit are executed separately by local validation.
"""
from __future__ import annotations

import base64
import copy
import importlib.util
import io
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from tools.verify_force_delivery_workflow import (
    CHUNK_BYTES, DATA, EvidenceError, GLB, PROTOCOL, Reader,
    checked_source_revision, rotation_error, sha,
)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def binary_scene(document=None, binary=None):
    """A hand-encoded two-key transform clip; no production export path."""
    if binary is None:
        binary = struct.pack('<2f6f8f', 0, 1, 0, 0, 0, 2, 4, 6,
                             0, 0, 0, 1, 0, 0, math.sqrt(.5), math.sqrt(.5))
    if document is None:
        document = dict(asset={'version': '2.0'}, scene=0, scenes=[{'nodes': [0]}],
            nodes=[{'extras': {'ontokin': {'kind': 'object', 'path': 'ball'}}}],
            buffers=[{'byteLength': len(binary)}],
            bufferViews=[{'buffer': 0, 'byteOffset': offset, 'byteLength': size}
                         for offset, size in ((0, 8), (8, 24), (32, 32))],
            accessors=[{'bufferView': index, 'componentType': 5126, 'count': 2, 'type': kind}
                       for index, kind in enumerate(('SCALAR', 'VEC3', 'VEC4'))],
            animations=[{
                'samplers': [{'input': 0, 'output': index, 'interpolation': 'LINEAR'} for index in (1, 2)],
                'channels': [{'sampler': index, 'target': {'node': 0, 'path': kind}}
                             for index, kind in enumerate(('translation', 'rotation'))]}])
    payload = encode(document)
    payload += b' ' * (-len(payload) % 4)
    padded_binary = binary + b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(payload) + 8 + len(padded_binary)
    raw = (struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<II', len(payload), 0x4E4F534A) +
           payload + struct.pack('<II', len(padded_binary), 0x004E4942) + padded_binary)
    return raw, document, binary


class PureDeliveryReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.reader = object.__new__(Reader)
        self.reader.root = self.root
        self.reader.files = set()
        self.reader.roles = {}
        self.reader.required = set()
        self.reader.implementation = {'name': 'test-only', 'version': 'fixture',
                                      'source_code_sha256': 'sha256:' + 'a' * 64}
        self.program = load_file_manifest(DATA / 'p01-single-interval.files.json')
        self.report = {'exporter': {'name': 'test-only', 'version': 'fixture'}}
        # A SQLite connection would violate the pure-reader test boundary.
        guard = patch('sqlite3.connect', side_effect=AssertionError('Pure audit opened SQLite'))
        guard.start()
        self.addCleanup(guard.stop)

    def retain_files(self):
        values = {'program.bundle.json': encode(self.program.to_payload()),
                  'source-manifest.json': encode(self.program.manifest()),
                  'scene.glb': binary_scene()[0], 'scene.export.json': encode(self.report),
                  'scene.reference.json': b'{}\n', 'oracle.json': b'{}\n',
                  **{unit.filename: unit.raw for unit in self.program.units}}
        self.record = {'case_id': 'P01', 'files': {}}
        for filename, raw in values.items():
            path = 'cases/P01/' + filename
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_bytes(raw)
            self.record['files'][filename] = {'path': path, 'sha256': sha(raw)}

    def change_file(self, filename, raw):
        descriptor = self.record['files'][filename]
        (self.root / descriptor['path']).write_bytes(raw)
        descriptor['sha256'] = sha(raw)

    def chunks(self):
        self.data = bytes(range(256)) * 257
        self.record = dict(case_id='P01', project_id='case-P01',
            sha256=sha(self.data), total_bytes=len(self.data),
            artifact_id='artifact:' + sha(self.data).removeprefix('sha256:'), artifact_roles=[])
        for index, offset in enumerate(range(0, len(self.data), CHUNK_BYTES)):
            raw = self.data[offset:offset + CHUNK_BYTES]
            next_offset = offset + len(raw) if offset + len(raw) < len(self.data) else None
            role = f'P01/artifact/{index:04d}'
            query = dict(operation='artifact', project_id='case-P01', request_id=str(index),
                         artifact_id=self.record['artifact_id'], offset=offset, max_bytes=CHUNK_BYTES)
            part = dict(program_revision=self.program.program_revision, artifact_id=self.record['artifact_id'],
                offset=offset, total_bytes=len(self.data), sha256=sha(self.data), mime_type='model/gltf-binary',
                data_base64=base64.b64encode(raw).decode(), next_offset=next_offset,
                artifact_provenance={'exporter': self.report['exporter'],
                    'source_code_sha256': self.reader.implementation['source_code_sha256'],
                    'program_revision': self.program.program_revision})
            reply = dict(status='succeeded', project_id=query['project_id'], request_id=query['request_id'],
                operation='artifact', program_revision=self.program.program_revision,
                truncated=next_offset is not None, result=part)
            self.reader.roles[role] = (query, reply)
            self.record['artifact_roles'].append(role)

    def check_chunks(self):
        return self.reader.artifact_chunks(self.record, self.program, self.report, self.data)

    def test_complete_frozen_source_directory_is_bound_without_source_execution(self):
        self.retain_files()
        with patch('ontokin.construction.compile_construction', side_effect=AssertionError('Compiler called')):
            files = self.reader.retained_case_files(self.record, self.program)
        self.assertEqual(files[self.program.entry.filename], self.program.entry.raw)
        self.assertEqual(len(files), 6 + len(self.program.units))

    def test_rehashed_bundle_cannot_substitute_a_pinned_library(self):
        self.retain_files()
        payload = self.program.to_payload()
        payload['modules'][0]['source'] += '\n'
        self.change_file('program.bundle.json', encode(payload))
        with self.assertRaisesRegex(EvidenceError, 'accepted source'):
            self.reader.retained_case_files(self.record, self.program)

    def test_rehashed_raw_source_cannot_change_accepted_bytes(self):
        self.retain_files()
        self.change_file(self.program.entry.filename, self.program.entry.raw + b'\n')
        with self.assertRaisesRegex(EvidenceError, 'raw source'):
            self.reader.retained_case_files(self.record, self.program)

    def test_rehashed_source_manifest_cannot_change_filename(self):
        self.retain_files()
        manifest = self.program.manifest()
        manifest['units'][0]['filename'] = 'substituted.ok'
        self.change_file('source-manifest.json', encode(manifest))
        with self.assertRaisesRegex(EvidenceError, 'accepted source'):
            self.reader.retained_case_files(self.record, self.program)

    def test_source_closure_rejects_missing_units_and_extra_files(self):
        self.retain_files()
        original = copy.deepcopy(self.record)
        for missing in (True, False):
            self.record = copy.deepcopy(original)
            if missing:
                self.record['files'].pop(self.program.entry.filename)
            else:
                self.record['files']['unbound.ok'] = {'path': 'cases/P01/unbound.ok', 'sha256': sha(b'')}
            with self.subTest(missing=missing), self.assertRaisesRegex(EvidenceError, 'exact source/artifact closure'):
                self.reader.retained_case_files(self.record, self.program)

    def test_evidence_paths_reject_traversal_and_symlink_even_with_matching_hash(self):
        self.retain_files()
        descriptor = self.record['files']['scene.glb']
        for name in ('../outside.glb', '/tmp/outside.glb', 'cases//P01/scene.glb', 'cases/P01/./scene.glb'):
            with self.subTest(name=name), self.assertRaisesRegex(EvidenceError, 'Unsafe evidence path'):
                self.reader.raw(name, descriptor['sha256'])
        original = self.root / descriptor['path']
        outside = self.root / 'outside.glb'
        outside.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(outside)
        with self.assertRaisesRegex(EvidenceError, 'symlinks'):
            self.reader.raw(descriptor['path'], descriptor['sha256'])

    def test_complete_multichunk_transport_reconstructs_exact_bytes(self):
        self.chunks()
        self.assertEqual(self.check_chunks(), 3)
        self.assertEqual(self.reader.required, set(self.record['artifact_roles']))

    def test_rehashed_artifact_and_receipt_without_new_chunks_is_rejected(self):
        self.chunks()
        self.data = bytes([self.data[0] ^ 1]) + self.data[1:]
        self.record['sha256'] = sha(self.data)
        self.record['artifact_id'] = 'artifact:' + sha(self.data).removeprefix('sha256:')
        for query, reply in self.reader.roles.values():
            query['artifact_id'] = reply['result']['artifact_id'] = self.record['artifact_id']
            reply['result']['sha256'] = self.record['sha256']
        with self.assertRaisesRegex(EvidenceError, 'do not reconstruct'):
            self.check_chunks()

    def test_transport_rejects_omitted_duplicate_and_reordered_chunks(self):
        for mutation in ('missing', 'duplicate', 'reordered'):
            self.chunks()
            if mutation == 'missing':
                self.record['artifact_roles'].pop()
            elif mutation == 'duplicate':
                self.record['artifact_roles'].append(self.record['artifact_roles'][-1])
            else:
                self.record['artifact_roles'].reverse()
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                self.check_chunks()

    def test_transport_rejects_substituted_request_source_and_implementation(self):
        changes = (('query', 'offset', 1), ('query', 'project_id', 'foreign'),
                   ('query', 'max_bytes', CHUNK_BYTES // 2), ('reply', 'request_id', 'other'),
                   ('reply', 'program_revision', 'sha256:' + '0' * 64),
                   ('part', 'program_revision', 'sha256:' + '0' * 64), ('part', 'total_bytes', 1),
                   ('part', 'next_offset', None), ('reply', 'truncated', False),
                   ('provenance', 'source_code_sha256', 'sha256:' + '0' * 64))
        for target, field, value in changes:
            self.chunks()
            query, reply = self.reader.roles[self.record['artifact_roles'][0]]
            objects = {'query': query, 'reply': reply, 'part': reply['result'],
                       'provenance': reply['result']['artifact_provenance']}
            objects[target][field] = value
            with self.subTest(target=target, field=field), self.assertRaises(EvidenceError):
                self.check_chunks()

    def test_transport_rejects_invalid_noncanonical_and_incomplete_base64(self):
        for encoded in ('!', 'Zg===', base64.b64encode(b'x').decode()):
            self.chunks()
            self.reader.roles[self.record['artifact_roles'][0]][1]['result']['data_base64'] = encoded
            with self.subTest(encoded=encoded), self.assertRaises(EvidenceError):
                self.check_chunks()

    def test_actual_binary_linear_and_slerp_playback_is_independently_decoded(self):
        data, _, _ = binary_scene()
        pose = GLB(data).pose('ball', .5)
        self.assertEqual(pose['translation'], [1, 2, 3])
        self.assertLess(rotation_error(pose['rotation'], [math.cos(math.pi / 8), 0, 0, math.sin(math.pi / 8)]), 1e-7)

    def test_binary_reader_rejects_invalid_headers_and_chunk_lengths(self):
        raw, _, _ = binary_scene()
        for corrupt in (b'XXXX' + raw[4:], raw[:-1], raw[:12] + struct.pack('<I', 3) + raw[16:]):
            with self.subTest(length=len(corrupt)), self.assertRaises(EvidenceError):
                GLB(corrupt)

    def test_binary_reader_rejects_rehashed_transform_and_buffer_counterexamples(self):
        changes = (
            lambda d: d['buffers'][0].__setitem__('uri', 'external.bin'),
            lambda d: d['scenes'][0].__setitem__('nodes', []),
            lambda d: d['nodes'][0].__setitem__('matrix', [0] * 16),
            lambda d: d['accessors'][1].__setitem__('bufferView', -1),
            lambda d: d['accessors'][1].__setitem__('count', 250001),
            lambda d: d['bufferViews'][1].__setitem__('byteOffset', -8),
            lambda d: d['bufferViews'][1].__setitem__('byteStride', 4),
            lambda d: d['accessors'][0].__setitem__('componentType', 5125),
            lambda d: d['animations'][0]['channels'].append(copy.deepcopy(d['animations'][0]['channels'][0])),
            lambda d: d['animations'][0]['samplers'][0].__setitem__('interpolation', 'STEP'),
        )
        for index, change in enumerate(changes):
            _, document, binary = binary_scene()
            change(document)
            # Re-encode correct GLB lengths; a digest/header mismatch is not the rejection.
            forged, _, _ = binary_scene(document, binary)
            with self.subTest(index=index), self.assertRaises(EvidenceError):
                GLB(forged)

    def test_binary_reader_rejects_nonfinite_and_collapsed_animation_times(self):
        for replacement in (float('nan'), 0.):
            _, document, binary = binary_scene()
            binary = binary[:4] + struct.pack('<f', replacement) + binary[8:]
            with self.subTest(replacement=replacement), self.assertRaises(EvidenceError):
                GLB(binary_scene(document, binary)[0])

    def test_source_revision_requires_equal_clean_measured_endpoints(self):
        revision = {'commit': 'a' * 40, 'tree': 'b' * 40, 'worktree_clean': True}
        manifest = {'source_revision': revision, 'source_revision_after': copy.deepcopy(revision)}
        self.assertEqual(checked_source_revision(manifest), revision)
        for field, value in (('commit', 'c' * 40), ('tree', 'd' * 40), ('worktree_clean', False)):
            altered = copy.deepcopy(manifest)
            altered['source_revision_after'][field] = value
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                checked_source_revision(altered)
        for value in (False, 1):
            altered = copy.deepcopy(manifest)
            altered['source_revision']['worktree_clean'] = altered['source_revision_after']['worktree_clean'] = value
            with self.subTest(clean=value), self.assertRaises(EvidenceError):
                checked_source_revision(altered)

    def test_audit_command_cannot_overwrite_retained_workflow_files(self):
        from tools.verify_force_delivery_workflow import main
        original = self.root / 'workflow.json'
        original.write_bytes(b'{"retained":true}\n')
        with patch('sys.argv', ['verify_force_delivery_workflow', '--workflow-dir', str(self.root),
                                '--output', str(original)]), patch('sys.stderr', io.StringIO()), \
                self.assertRaises(SystemExit) as result:
            main()
        self.assertEqual(result.exception.code, 2)
        self.assertEqual(original.read_bytes(), b'{"retained":true}\n')


HAS_SCHEMA = all(importlib.util.find_spec(name) for name in ('jsonschema', 'referencing'))


@unittest.skipUnless(HAS_SCHEMA, 'Run the force-agent cohort with its pinned verification-only schema tools')
class PureDeliveryTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.verify_force_agent_workflow import SchemaChecks
        cls.schemas = SchemaChecks()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = {'exchanges': []}
        self.query = dict(schema_version=PROTOCOL, project_id='case-P01', request_id='retained-1',
                          operation='discover', profile='force-0.1', limit=1)
        self.reply = dict(schema_version=PROTOCOL, project_id='case-P01', request_id='retained-1',
            operation='discover', status='succeeded', program_revision=None, accepted_program_revision=None,
            requested_level=None, achieved_level=None, run_id=None, diagnostics=[], result={'items': []},
            progress=None, next_cursor=None, truncated=False, protocol_error=None)
        guard = patch('sqlite3.connect', side_effect=AssertionError('Pure trace audit opened SQLite'))
        guard.start()
        self.addCleanup(guard.stop)

    def append(self, role, query, reply):
        sequence = len(self.manifest['exchanges']) + 1
        entry = {'role': role, 'method': 'handle', 'sequence': sequence}
        for kind, document in (('request', query), ('response', reply)):
            name = f'exchanges/{sequence:04d}.{kind}.json'
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(encode(document))
            entry[kind + '_file'] = name
            entry[kind + '_sha256'] = sha(path.read_bytes())
        self.manifest['exchanges'].append(entry)

    def check(self):
        reader = Reader(self.root, self.schemas)
        reader.trace(self.manifest)
        return reader

    def test_actual_reader_accepts_identical_transport_retry(self):
        self.append('first', self.query, self.reply)
        self.append('retry', self.query, self.reply)
        self.assertEqual(len(self.check().request_ledger), 1)

    def test_rehashed_same_request_id_cannot_change_receipt(self):
        self.append('first', self.query, self.reply)
        self.reply['progress'] = {'phase': 'forged'}
        self.append('retry', self.query, self.reply)
        with self.assertRaisesRegex(EvidenceError, 'retained receipt'):
            self.check()

    def test_rehashed_changed_request_requires_rejection(self):
        self.append('first', self.query, self.reply)
        self.query['limit'] = 2
        self.append('collision', self.query, self.reply)
        with self.assertRaisesRegex(EvidenceError, 'request ID'):
            self.check()

    def test_rehashed_response_cannot_change_project_or_accepted_head(self):
        for field, value in (('project_id', 'foreign'), ('accepted_program_revision', 'sha256:' + 'a' * 64)):
            self.manifest = {'exchanges': []}
            response = {**self.reply, field: value}
            self.append('first', self.query, response)
            with self.subTest(field=field), self.assertRaises(EvidenceError):
                self.check()

    def test_rehashed_response_manifest_cannot_substitute_source_bytes(self):
        program = load_file_manifest(DATA / 'p01-single-interval.files.json')
        manifest = program.manifest()
        manifest['units'][0]['filename'] = 'forged.ok'
        self.reply['result'] = {'program_revision': program.program_revision, 'source_manifest': manifest}
        self.append('first', self.query, self.reply)
        with self.assertRaisesRegex(EvidenceError, 'exact request source bytes'):
            self.check()

    def test_rehashed_protocol_schema_additions_are_not_silently_ignored(self):
        self.reply['trusted_override'] = True
        self.append('first', self.query, self.reply)
        with self.assertRaisesRegex(EvidenceError, 'schema'):
            self.check()

    def test_source_only_and_component_workflows_are_not_relabelled_as_delivery(self):
        from tools.verify_force_delivery_workflow import verify
        for schema in ('ontokin.force-agent-workflow/0.1', 'ontokin.force-agent-workflow/0.2',
                       'ontokin.force-destination-workflow/0.1'):
            (self.root / 'workflow.json').write_bytes(encode({'schema_version': schema, 'status': 'recorded'}))
            with self.subTest(schema=schema), self.assertRaisesRegex(EvidenceError, 'unsupported delivery workflow'):
                verify(self.root, self.schemas)


if __name__ == '__main__':
    unittest.main()
