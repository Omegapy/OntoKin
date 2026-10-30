"""Hostile hand-authored bytes for the independent C078 evidence reader.

These tests never construct or evaluate an OntoKin program, open an Agent
service, or import product geometry. They exercise proof boundaries that can be
corrupted while summary status flags remain unchanged.
"""
from __future__ import annotations

import base64
import copy
import math
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

from tools.audit_framed_loft_acceptance import (
    Audit, FREEZE, PROFILE, TARGET, bundle_identity, canonical, loads,
    returned_chunk, rotation_error_identity, sha, witness_positions,
)


def motion_glb(*, times=None, translation=None, rotation=None, mutate=None):
    """Hand-encode one geometry-free carrier, as used by generated parents."""
    times = [0, .25, .5, .75, 1] if times is None else times
    positions = [[0, time*.5, 0] for time in times]
    rotations = [[0, 0, 0, 1] for _ in times]
    if translation is not None:
        positions[-1] = translation
    if rotation is not None:
        rotations[-1] = rotation
    payload = {'schema_version': 'ontokin.bundle/0.1',
               'entry': {'filename': 'entry.ok', 'source': 'hand-authored evidence control'}, 'modules': []}
    revision, manifest = bundle_identity(payload)
    binary = bytearray()
    views, accessors = [], []
    for values, kind, components in ((times, 'SCALAR', 1), (positions, 'VEC3', 3), (rotations, 'VEC4', 4)):
        offset = len(binary)
        for row in values:
            binary.extend(struct.pack('<' + 'f'*components, *([row] if components == 1 else row)))
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(binary)-offset})
        accessors.append({'bufferView': len(views)-1, 'componentType': 5126, 'count': len(values), 'type': kind})
    document = {
        'asset': {'version': '2.0'}, 'buffers': [{'byteLength': len(binary)}],
        'bufferViews': views, 'accessors': accessors,
        'nodes': [{'extras': {'ontokin': {'kind': 'object', 'path': 'array'}}}],
        'scenes': [{'nodes': [0]}], 'scene': 0,
        'animations': [{'samplers': [{'input': 0, 'output': 1}, {'input': 0, 'output': 2}],
                        'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                                     {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]}],
        'extras': {'ontokin': {'schema_version': '0.11', 'target_contract': TARGET, 'profile': PROFILE,
                               'program': {'revision': revision, 'manifest': manifest}}},
    }
    if mutate is not None:
        mutate(document)
    encoded = canonical(document)
    encoded += b' ' * (-len(encoded) % 4)
    binary.extend(b'\0' * (-len(binary) % 4))
    raw = (struct.pack('<III', 0x46546c67, 2, 28+len(encoded)+len(binary)) +
           struct.pack('<II', len(encoded), 0x4e4f534a) + encoded +
           struct.pack('<II', len(binary), 0x004e4942) + binary)
    expected = {'program_revision': revision, 'manifest': manifest,
                'nodes': {'array': {'geometry': None, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}}}
    return raw, expected


def reader():
    result = Audit(SimpleNamespace(acceptance_dir=Path('/unused-evidence'), repo=Path('/unused-repository'),
                                   candidate_commit='0'*40, freeze_commit=FREEZE))
    result.spec = {'sample_times_seconds': [0, .25, .5, .75, 1],
                   'tolerances': {'position_m': .001, 'rotation_rad': .001}}
    result.decoded_contents, result.decoded_measures, result.decoded_ordinals = {}, {}, {}
    return result


def chunk_control():
    content = b'C078 supplied byte control'.ljust(64, b'.')
    identity = 'artifact:' + 'a'*64
    revision = 'sha256:' + 'b'*64
    implementation = 'sha256:' + 'c'*64
    digest = 'sha256:' + 'a'*64
    request = {'operation': 'artifact', 'request_id': 'request-3', 'artifact_id': identity,
               'offset': 0, 'max_bytes': 64}
    response = {'operation': 'artifact', 'request_id': 'request-3', 'status': 'succeeded',
                'program_revision': revision, 'truncated': True, 'result': {
                    'artifact_id': identity, 'offset': 0, 'program_revision': revision,
                    'sha256': digest, 'total_bytes': 128, 'producer_request_id': 'request-2',
                    'mime_type': 'model/gltf-binary', 'next_offset': 64,
                    'artifact_provenance': {'source_code_sha256': implementation, 'program_revision': revision},
                    'data_base64': base64.b64encode(content).decode()}}
    arguments = {'artifact_id': identity, 'revision': revision, 'producer': 'request-2',
                 'implementation': implementation, 'digest': digest, 'total': 128, 'offset': 0, 'maximum': 64}
    return {'request': request, 'response': response}, arguments, content


class RawJSONAndIdentityTests(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_never_become_evidence(self):
        for raw in ('{"status":"failed","status":"passed"}', '{"value":NaN}',
                    '{"value":Infinity}', '{"value":-Infinity}', '{"value":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                loads(raw)

    def test_bundle_identity_binds_filename_entry_and_pinned_library(self):
        payload = {'schema_version': 'ontokin.bundle/0.1',
                   'entry': {'filename': 'assembly.ok', 'source': 'entry text'},
                   'modules': [{'package_id': 'fixture.parts', 'version': '1.0.0',
                                'filename': 'parts.ok', 'source': 'pinned original'}]}
        baseline = bundle_identity(payload)[0]
        for section, field in (('entry', 'filename'), ('entry', 'source'), ('module', 'source')):
            changed = copy.deepcopy(payload)
            target = changed['modules'][0] if section == 'module' else changed[section]
            target[field] += ' changed'
            self.assertNotEqual(bundle_identity(changed)[0], baseline)

    def test_frozen_witness_hex_disagreement_is_rejected(self):
        geometry = {'source_positions': [{'position_m': [1, 2, 3],
                                         'position_hex': [float(1).hex(), float(2).hex(), float(4).hex()]}]}
        with self.assertRaisesRegex(ValueError, 'hex identity'):
            witness_positions(geometry)


class ReturnedArtifactChunkTests(unittest.TestCase):
    def test_complete_control_and_terminal_chunk(self):
        row, arguments, content = chunk_control()
        self.assertEqual(returned_chunk(row, **arguments), content)
        row['request']['offset'] = row['response']['result']['offset'] = arguments['offset'] = 64
        row['response']['result']['next_offset'] = None
        row['response']['truncated'] = False
        self.assertEqual(returned_chunk(row, **arguments), content)

    def test_changed_payload_ownership_or_continuation_is_rejected(self):
        mutations = (
            lambda row: row['request'].update(offset=1),
            lambda row: row['request'].update(request_id='wrong-request'),
            lambda row: row['response']['result'].update(producer_request_id='wrong-producer'),
            lambda row: row['response']['result'].update(program_revision='wrong-source'),
            lambda row: row['response']['result'].update(artifact_id='wrong-artifact'),
            lambda row: row['response']['result'].update(sha256='wrong-digest'),
            lambda row: row['response']['result'].update(total_bytes=129),
            lambda row: row['response']['result'].update(next_offset=63),
            lambda row: row['response'].update(truncated=False),
            lambda row: row['response']['result']['artifact_provenance'].update(source_code_sha256='wrong-implementation'),
            lambda row: row['response']['result'].update(data_base64=base64.b64encode(b'short').decode()),
        )
        for index, mutation in enumerate(mutations):
            row, arguments, unused = chunk_control()
            mutation(row)
            with self.subTest(index=index), self.assertRaises(ValueError):
                returned_chunk(row, **arguments)

    def test_non_base64_chunk_is_rejected(self):
        row, arguments, unused = chunk_control()
        row['response']['result']['data_base64'] = '!!invalid!!'
        with self.assertRaises(ValueError):
            returned_chunk(row, **arguments)


class ActualGLBMotionTests(unittest.TestCase):
    def read(self, **kwargs):
        raw, expected = motion_glb(**kwargs)
        return reader().glb_motion('hand-authored', raw, expected)

    def test_hand_authored_binary32_control_is_decoded(self):
        observations = self.read()
        self.assertEqual(len(observations), 5)
        self.assertEqual(observations[-1]['translation'], [0, .5, 0])

    def test_wrong_motion_is_rejected_from_bytes_despite_valid_metadata(self):
        with self.assertRaisesRegex(AssertionError, 'decoded position'):
            self.read(translation=[0, .51, 0])

    def test_geodesic_rotation_guard_is_stricter_than_componentwise_tolerance(self):
        rotation = [.00075, 0, 0, math.sqrt(1-.00075**2)]
        self.assertLess(max(abs(a-b) for a, b in zip(rotation, [0, 0, 0, 1])), .001)
        self.assertGreater(rotation_error_identity(rotation), .001)
        with self.assertRaisesRegex(AssertionError, 'geodesic'):
            self.read(rotation=rotation)

    def test_nonfinite_binary_values_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Finite actual accessor'):
            self.read(translation=[0, math.nan, 0])

    def test_repeated_clock_or_cross_view_accessor_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'key times'):
            self.read(times=[0, .25, .5, .75, .75])
        with self.assertRaisesRegex(AssertionError, 'own supplied view'):
            self.read(mutate=lambda document: document['bufferViews'][0].update(byteLength=16))

    def test_stale_source_duplicate_channel_and_hidden_mesh_are_rejected(self):
        mutations = (
            lambda document: document['extras']['ontokin']['program'].update(revision='sha256:'+'f'*64),
            lambda document: document['animations'][0]['channels'].append(
                copy.deepcopy(document['animations'][0]['channels'][0])),
            lambda document: document['nodes'][0].update(mesh=0),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(AssertionError):
                self.read(mutate=mutation)


if __name__ == '__main__':
    unittest.main()
