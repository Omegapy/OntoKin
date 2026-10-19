#!/usr/bin/env python3
"""Audit actual Agent force delivery without the compiler, simulator or exporter.

The reader binds transported patches, accepted sources, reference inspections,
artifact chunks and decoded recorded poses. Native geometry and browser review
remain separate roles over the same retained GLBs.
"""
from __future__ import annotations

import argparse
import base64
from bisect import bisect_right
import copy
from datetime import datetime, timezone
from fractions import Fraction as Q
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import load_bundle
from tools.verify_force_agent_workflow import (Reader as SourceReader, SchemaChecks,
    DATA, PROTOCOL, EvidenceError, authored_clock, clock, decode, require, sha, vector)

SCHEMA = 'ontokin.force-delivery-workflow/0.1'
AUDIT_SCHEMA = 'ontokin.force-delivery-audit/0.1'
TARGET = 'ontokin.glb/0.5'
CASE_IDS = ('P01', 'P07', 'P10', 'P11', 'P12', 'P13', 'P21')
CHUNK_BYTES = 32768
MAX_GLB_BYTES = 64 * 1024 * 1024
MAX_KEYFRAMES = 10000
MAX_BAKED_POSES = 250000
MAX_MESH_VERTICES = 250000
MAX_DECODED_COMPONENTS = 9 * MAX_BAKED_POSES + 12 * MAX_MESH_VERTICES
REFERENCE_FIELDS = ('element_id', 'position_m', 'orientation_wxyz', 'velocity_m_per_s',
                    'angular_velocity_rad_per_s', 'forces', 'impulses', 'pose_authority', 'own_mass_kg')
FORCE_PROFILE = {
    'name': 'force-0.1',
    'physical_model': 'free_homogeneous_sphere_with_own_isotropic_inertia',
    'source_forces': 'finite_duration_world_force_at_target_center_of_mass',
    'source_impulses': 'instantaneous_world_momentum_at_target_self_point',
    'continuous_external_forces': 'canonical_active_source_force_sum_plus_uniform_gravity',
    'continuous_external_torques': 'absent',
    'contacts': 'disabled',
    'boundary_state': 'complete_per_object_active_force_and_latest_force_impulse_boundary_records',
    'destination_behavior': 'recorded_rigid_animation_without_live_force_or_impulse_execution',
}


def checked_source_revision(manifest):
    revision = manifest['source_revision']
    require(isinstance(revision, dict) and set(revision) == {'commit', 'tree', 'worktree_clean'} and
            all(isinstance(revision[key], str) and re.fullmatch('[0-9a-f]{40}', revision[key])
                for key in ('commit', 'tree')) and revision['worktree_clean'] is True,
            'Delivery recording lacks a clean, identified source revision')
    require(manifest['source_revision_after'] == revision,
            'Source commit, tree or clean state changed during delivery recording')
    return revision


def entry_count(value):
    pending = [value]
    result = 0
    while pending:
        item = pending.pop()
        result += 1
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return result


def rotation_error(actual_xyzw, expected_wxyz):
    """Compare glTF XYZW with source/oracle WXYZ, including quaternion sign."""
    require(len(actual_xyzw) == len(expected_wxyz) == 4, 'Quaternion shape differs')
    actual_norm = math.hypot(*actual_xyzw)
    expected_norm = math.hypot(*expected_wxyz)
    require(actual_norm > 0 and abs(actual_norm - 1) < 1e-5 and expected_norm > 0, 'Invalid recorded quaternion')
    actual = [value / actual_norm for value in actual_xyzw]
    expected = [value / expected_norm for value in (*expected_wxyz[1:], expected_wxyz[0])]
    chord = min(math.dist(actual, expected), math.dist(actual, [-value for value in expected]))
    return 4 * math.asin(min(1, chord / 2))


def reference_objects(items, expected):
    """Bind the native reference to occurrence identities in actual responses."""
    require(len(items) == len(expected), 'Native reference contains the wrong object count')
    projected = {}
    for item in items:
        path = item['path']
        require(item['kind'] == 'object' and path in expected and path not in projected,
                'Native reference must contain the complete unique object occurrences')
        state = item['state']
        require(state.get('available') is True and item['element_id'] == state['element_id'] == expected[path]['element_id'],
                'Native reference occurrence identity and state differ')
        projected[path] = {field: item['element_id'] if field == 'element_id' else state[field]
                           for field in REFERENCE_FIELDS}
    require(set(projected) == set(expected), 'Native reference contains wrong objects')
    return projected


class GLB:
    """Independent embedded-buffer reader and LINEAR/SLERP playback."""
    def __init__(self, raw, *, expected_objects=None):
        require(28 <= len(raw) <= MAX_GLB_BYTES, 'GLB byte bound differs')
        require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Malformed GLB header')
        offset = 12
        chunks = []
        while offset < len(raw):
            require(offset + 8 <= len(raw), 'Truncated GLB chunk header')
            length, kind = struct.unpack_from('<II', raw, offset)
            require(length % 4 == 0 and offset + 8 + length <= len(raw), 'Malformed GLB chunk length')
            chunks.append((kind, raw[offset + 8:offset + 8 + length]))
            offset += 8 + length
        require([kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942], 'Expected one JSON and one embedded BIN chunk')
        self.document = decode(chunks[0][1])
        self.binary = chunks[1][1]
        document = self.document
        require(document['asset']['version'] == '2.0', 'Wrong glTF version')
        require(len(document['buffers']) == 1 and 'uri' not in document['buffers'][0], 'External or multiple GLB buffers')
        require(0 <= len(self.binary) - document['buffers'][0]['byteLength'] <= 3, 'GLB buffer length differs')
        self.nodes = {}
        self.tracks = {}
        self.decoded_components = 0
        require(0 < len(document['nodes']) <= 1000, 'Recorded object count exceeds its bound')
        require(document['scene'] == 0 and len(document['scenes']) == 1 and
                document['scenes'][0]['nodes'] == list(range(len(document['nodes']))), 'The declared root-node scene differs')
        for index, node in enumerate(document['nodes']):
            require('children' not in node and 'matrix' not in node, 'Unexpected transformed node hierarchy')
            metadata = node.get('extras', {}).get('ontokin', {})
            require(metadata.get('kind') == 'object', 'Helpers were not requested by this workflow')
            path = metadata['path']
            require(path not in self.nodes, 'Duplicate source object node')
            self.nodes[path] = (index, node, metadata)
        if expected_objects is not None:
            require(set(self.nodes) == set(expected_objects), 'Encoded scene omitted or added source objects')
        require(len(document['animations']) == 1, 'Expected one recorded clip')
        animation = document['animations'][0]
        require(len(animation['channels']) == 2 * len(self.nodes), 'Missing or repeated recorded object channels')
        declared = {}
        track_keys = 0
        for channel in animation['channels']:
            target = channel['target']
            key = (target['node'], target['path'])
            require(key not in declared and target['path'] in ('translation', 'rotation'), 'Duplicate or unsupported animation channel')
            require(type(target['node']) is int and 0 <= target['node'] < len(document['nodes']), 'Invalid animation node')
            require(type(channel['sampler']) is int and 0 <= channel['sampler'] < len(animation['samplers']), 'Invalid animation sampler')
            sampler = animation['samplers'][channel['sampler']]
            require(sampler['interpolation'] == 'LINEAR', 'Wrong recorded interpolation')
            require(all(type(sampler[kind]) is int and 0 <= sampler[kind] < len(document['accessors'])
                        for kind in ('input', 'output')), 'Invalid animation accessor')
            inputs, outputs = (document['accessors'][sampler[kind]] for kind in ('input', 'output'))
            require(inputs['type'] == 'SCALAR' and inputs['componentType'] == outputs['componentType'] == 5126 and
                    outputs['type'] == ('VEC3' if key[1] == 'translation' else 'VEC4'),
                    'Animation data must use float32 scalars and transforms')
            require(type(inputs['count']) is int and 0 < inputs['count'] <= MAX_KEYFRAMES and
                    type(outputs['count']) is int and outputs['count'] == inputs['count'],
                    'Recorded animation exceeds its keyframe bound or has unequal tracks')
            track_keys += inputs['count']
            require(track_keys <= 2 * MAX_BAKED_POSES, 'Recorded animation exceeds its aggregate pose bound')
            declared[key] = sampler
        require(set(declared) == {(index, kind) for index in range(len(document['nodes']))
                                  for kind in ('translation', 'rotation')}, 'Missing recorded object channels')
        # Complete declared counts and source cardinality are checked before any
        # shared accessor can be expanded repeatedly through multiple channels.
        for key, sampler in declared.items():
            times = [value[0] for value in self.accessor(sampler['input'])]
            values = self.accessor(sampler['output'])
            require(times and len(times) == len(values) and all(a < b for a, b in zip(times, times[1:])), 'Invalid animation key sequence')
            require(all(len(value) == (3 if key[1] == 'translation' else 4) for value in values), 'Wrong transform accessor arity')
            self.tracks[key] = (times, values)

    def accessor(self, index):
        require(type(index) is int and 0 <= index < len(self.document['accessors']), 'Invalid accessor index')
        accessor = self.document['accessors'][index]
        require('sparse' not in accessor and not accessor.get('normalized', False), 'Unsupported accessor encoding')
        count = accessor['count']
        require(type(count) is int and 0 < count <= 250000, 'Accessor count exceeds the bounded profile')
        arity = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
        self.decoded_components += count * arity
        require(self.decoded_components <= MAX_DECODED_COMPONENTS, 'Decoded accessor expansion exceeds its aggregate bound')
        component = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[accessor['componentType']]
        fmt = '<' + component * arity
        size = struct.calcsize(fmt)
        view_index = accessor['bufferView']
        require(type(view_index) is int and 0 <= view_index < len(self.document['bufferViews']), 'Invalid accessor buffer view')
        view = self.document['bufferViews'][view_index]
        require(view.get('buffer', 0) == 0, 'Accessor names an external buffer')
        stride = view.get('byteStride', size)
        view_offset, local_offset = view.get('byteOffset', 0), accessor.get('byteOffset', 0)
        require(all(type(value) is int and value >= 0 for value in (view_offset, local_offset, view['byteLength'])) and
                type(stride) is int and stride >= size, 'Invalid accessor stride or offset')
        offset = view_offset + local_offset
        end = offset + (count - 1) * stride + size
        require(end <= view.get('byteOffset', 0) + view['byteLength'] <= self.document['buffers'][0]['byteLength'], 'Accessor exceeds its complete buffer view')
        values = [struct.unpack_from(fmt, self.binary, offset + row * stride) for row in range(count)]
        require(all(math.isfinite(value) for row in values for value in row), 'Nonfinite recorded accessor value')
        return values

    def pose(self, path, time):
        index = self.nodes[path][0]
        result = {}
        for kind in ('translation', 'rotation'):
            times, values = self.tracks[(index, kind)]
            if time <= times[0]:
                value = values[0]
            elif time >= times[-1]:
                value = values[-1]
            else:
                left = bisect_right(times, time) - 1
                factor = (time - times[left]) / (times[left + 1] - times[left])
                a, b = values[left], values[left + 1]
                if kind == 'rotation':
                    a = [v / math.hypot(*a) for v in a]
                    b = [v / math.hypot(*b) for v in b]
                    dot = sum(x * y for x, y in zip(a, b))
                    if dot < 0:
                        b = [-value for value in b]
                        dot = -dot
                    if dot < .9995:
                        angle = math.acos(min(1, dot))
                        denominator = math.sin(angle)
                        value = [(math.sin((1-factor) * angle) * x + math.sin(factor * angle) * y) / denominator
                                 for x, y in zip(a, b)]
                    else:
                        value = [(1-factor) * x + factor * y for x, y in zip(a, b)]
                    value = [v / math.hypot(*value) for v in value]
                else:
                    value = [(1-factor) * x + factor * y for x, y in zip(a, b)]
            result[kind] = value
        return result

    def geometry(self, path):
        _, node, metadata = self.nodes[path]
        if 'mesh' not in node:
            return None
        mesh = self.document['meshes'][node['mesh']]
        program_revision = self.document['extras']['ontokin']['program']['revision']
        require(metadata['program_revision'] == program_revision, 'Geometry occurrence has the wrong program revision')
        primitives = []
        for part in mesh['primitives']:
            material = copy.deepcopy(self.document['materials'][part['material']])
            provenance = material['extras']['ontokin']
            require(provenance['program_revision'] == program_revision and provenance['occurrence_path'] == path and
                    provenance['element_id'] == metadata['element_id'], 'Material has the wrong program or occurrence revision')
            require(part.get('mode', 4) == 4 and provenance['source_region_key'] == part['extras']['ontokin']['region_key'],
                    'Geometry primitive mode or material region binding differs')
            # An accepted source repair necessarily changes the program revision.
            # Validate that binding above, then compare all remaining material data.
            del provenance['program_revision']
            primitives.append({'positions': self.accessor(part['attributes']['POSITION']),
                'normals': self.accessor(part['attributes']['NORMAL']), 'indices': self.accessor(part['indices']),
                'mode': part.get('mode', 4), 'regions': copy.deepcopy(part['extras']), 'material': material})
        return {'source_geometry': copy.deepcopy(metadata['geometry']),
                'surface': copy.deepcopy(metadata.get('surface')), 'primitives': primitives}

    def require_same_geometry(self, other, path):
        require(self.geometry(path) == other.geometry(path), 'A physical repair changed decoded source geometry or materials')


class Reader(SourceReader):
    def raw(self, name, expected, *, maximum=MAX_GLB_BYTES):
        require(isinstance(name, str), 'Unsafe evidence path')
        path = PurePosixPath(name)
        require(not path.is_absolute() and '\\' not in name and str(path) == name and
                all(part not in ('.', '..') for part in path.parts), 'Unsafe evidence path')
        file = self.root
        for part in path.parts:
            file /= part
            require(not file.is_symlink(), 'Evidence symlinks are not accepted')
        require(file.is_file() and file.stat().st_size <= maximum, 'Missing or oversized retained file')
        raw = file.read_bytes()
        require(sha(raw) == expected, 'Evidence file digest differs: ' + name)
        return raw

    def keep_file(self, name):
        require(name not in self.files, 'Reused evidence file path: ' + name)
        self.files.add(name)

    def retained_case_files(self, record, program):
        """Bind the artifact directory to the exact accepted bundle bytes."""
        name = record['case_id']
        filenames = {'program.bundle.json', 'source-manifest.json', 'scene.glb', 'scene.export.json',
                     'scene.reference.json', 'oracle.json', *(unit.filename for unit in program.units)}
        require(set(record['files']) == filenames, 'Delivery files do not retain the exact source/artifact closure')
        files = {}
        for filename, descriptor in record['files'].items():
            require(descriptor['path'] == 'cases/' + name + '/' + filename, 'Wrong delivery file location')
            self.keep_file(descriptor['path'])
            files[filename] = self.raw(descriptor['path'], descriptor['sha256'])
        require(decode(files['program.bundle.json']) == program.to_payload() and
                decode(files['source-manifest.json']) == program.manifest(), 'Delivered bundle or manifest differs from accepted source')
        for unit in program.units:
            require(files[unit.filename] == unit.raw, 'Retained raw source file differs')
        return files

    def artifact_chunks(self, record, program, report, data):
        """Reconstruct the complete artifact from its actual transport receipts."""
        chunks = []
        offset = 0
        require(0 < len(data) <= MAX_GLB_BYTES and sha(data) == record['sha256'] and
                len(data) == record['total_bytes'] and
                record['artifact_id'] == 'artifact:' + sha(data).removeprefix('sha256:'),
                'Retained GLB differs from the artifact identity')
        require(record['artifact_roles'] and len(record['artifact_roles']) <= 2048, 'Missing or excessive artifact retrieval')
        for index, role in enumerate(record['artifact_roles']):
            require(role == f'{record["case_id"]}/artifact/{index:04d}', 'Artifact chunk roles are not contiguous')
            self.required.add(role)
            query, reply = self.at(role)
            require(query['operation'] == 'artifact' and query['project_id'] == record['project_id'] and
                    query['artifact_id'] == record['artifact_id'] and type(query['offset']) is int and query['offset'] == offset and
                    query['max_bytes'] == CHUNK_BYTES, 'Artifact request changed its identity, offset or limit')
            require(reply['status'] == 'succeeded' and reply['project_id'] == query['project_id'] and
                    reply['request_id'] == query['request_id'] and reply['operation'] == query['operation'] and
                    reply['program_revision'] == program.program_revision, 'Artifact response lost its request identity')
            part = reply['result']
            try:
                raw = base64.b64decode(part['data_base64'], validate=True)
            except (ValueError, TypeError) as error:
                raise EvidenceError('Invalid artifact base64 transport') from error
            require(base64.b64encode(raw).decode() == part['data_base64'] and
                    len(raw) == min(CHUNK_BYTES, len(data) - offset) > 0, 'Invalid or incomplete artifact chunk')
            require(part['program_revision'] == program.program_revision and part['artifact_id'] == record['artifact_id'] and
                    type(part['offset']) is int and part['offset'] == offset and part['total_bytes'] == len(data) and
                    part['sha256'] == sha(data) and part['mime_type'] == 'model/gltf-binary',
                    'Artifact response lost its source or complete byte identity')
            require(part['artifact_provenance'] == {'exporter': report['exporter'],
                'source_code_sha256': self.implementation['source_code_sha256'], 'program_revision': program.program_revision},
                'Artifact provenance differs')
            chunks.append(raw)
            offset += len(raw)
            require(part['next_offset'] == (offset if offset < len(data) else None) and
                    reply['truncated'] is (offset < len(data)), 'Artifact chunk continuation differs')
        require(b''.join(chunks) == data and offset == len(data), 'Artifact chunks do not reconstruct the retained GLB')
        return len(chunks)

    def trace(self, manifest):
        for sequence, record in enumerate(manifest['exchanges'], 1):
            role = record['role']
            require(role not in self.roles and record['sequence'] == sequence, 'Duplicate role or noncontiguous trace')
            for kind in ('request', 'response'):
                require(record[kind + '_file'] == f'exchanges/{sequence:04d}.{kind}.json', 'Exchange file order differs')
                self.keep_file(record[kind + '_file'])
            request = self.read(record['request_file'], record['request_sha256'])
            response = self.read(record['response_file'], record['response_sha256'])
            self.schemas.validate('request', request)
            self.schemas.validate('response', response)
            self.register_candidate(request)
            self.recursive(response)
            require(all(request[key] == response[key] for key in ('schema_version', 'project_id', 'request_id', 'operation')), 'Response does not belong to its request')
            require(record['method'] == ('submit' if role == 'cancel/submit' else 'handle'), 'Wrong transport method')
            self.roles[role] = (request, response)
            key = request['project_id'], request['request_id']
            previous = self.request_ledger.get(key)
            if previous is None:
                self.request_ledger[key] = (request, response)
            elif previous[0] != request:
                require(response['status'] == 'rejected' and response['protocol_error'] and
                        response['protocol_error']['code'] == 'OKL-E-REQUEST-ID', 'Changed-payload request ID was not rejected')
            elif previous[1]['status'] == 'queued':
                require(response['status'] == 'cancelled', 'Queued request has an unexpected terminal result')
                self.request_ledger[key] = (request, response)
            else:
                require(previous[1] == response, 'Exact request-ID retry changed its retained receipt')
            project = request['project_id']
            if request['operation'] in ('create', 'edit') and response['status'] == 'succeeded':
                if request['operation'] == 'create':
                    require(project not in self.heads, 'Create overwrote an accepted source')
                    expected = load_bundle(request['bundle']).program_revision
                else:
                    require(request['expected_program_revision'] == self.heads.get(project), 'Successful stale source edit')
                    expected = self.book.bundles[role.split('/')[0]].program_revision
                require(response['program_revision'] == expected, 'Accepted candidate identity differs')
                self.heads[project] = expected
                self.accepted.add((project, expected))
            require(response['accepted_program_revision'] == self.heads.get(project), 'Failed or read request changed the accepted head')

    def source_workflow(self, name):
        case, program = self.book.cases[name], self.book.bundles[name]
        if 'repair' in case:
            self.check_repair(name)
            self.required.update(name + '/' + role for role in ('create-base', 'authority', 'reject-scope', 'repair', 'stale'))
        else:
            self.create(name + '/create', name)
            self.required.add(name + '/create')
        self.check_run(name)
        self.required.add(name + '/run')
        for index, row in enumerate(case['expected_samples']):
            role = f'{name}/sample/{index:04d}'
            self.required.add(role)
            request, response = self.at(role)
            require(request['operation'] == 'inspect' and request['program_revision'] == program.program_revision and
                    request['run_id'] == self.runs[name], 'Source sample lost its request revision or run')
            require(request['selector'] == {'path': row['target']} and request['fields'] == ['identity', 'state'] and
                    request['limit'] == 1 and request.get('frame', 'world') == 'world', 'Source sample query was substituted')
            require(Q(request['time']['seconds']) == authored_clock(row['time']) and request['time']['side'] == row['side'], 'Source sample clock was substituted')
            require(response['status'] == 'succeeded' and not response['truncated'] and response['next_cursor'] is None and
                    response['result']['total'] == len(response['result']['items']) == 1, 'Source sample is incomplete')
            item = response['result']['items'][0]
            state = item['state']
            require(item['path'] == row['target'] and state['program_revision'] == program.program_revision and
                    state['run_id'] == response['run_id'] == self.runs[name] and state['available'] and
                    state['element_id'] == item['element_id'], 'Source sample context differs')
            require(clock(state['time_seconds']) == authored_clock(row['time']) and state['side'] == row['side'], 'Returned source sample clock differs')
            require(response['result']['context'] == dict(fields=['identity', 'state'], frame='world',
                program_revision=program.program_revision, run_id=self.runs[name], selector=request['selector'],
                side=row['side'], time_seconds=request['time']['seconds']) and state['pose_frame'] == 'world' and
                state['velocity_expressed_in'] == state['velocity_measured_in'] == 'world', 'Source inspection frame/context differs')
            self.sample(name, state, row)
        if name in ('P01', 'P10', 'P11', 'P12', 'P13'):
            role = name + '/mesh'
            self.required.add(role)
            request, response = self.at(role)
            require(request['operation'] == 'surface.mesh_page' and request['count'] == 2 and
                    request['program_revision'] == program.program_revision, 'Wrong source mesh query')
            require(response['status'] == 'succeeded' and response['result']['program_revision'] == program.program_revision and
                    response['result']['profile'] == 'surface-0.1', 'Source mesh page lost its profile or identity')

    def delivery(self, record):
        from tools.force_oracles import oracle_for, sample_requests, expected_pose, boundary_times
        name = record['case_id']
        require(name in CASE_IDS and name not in self.delivered, 'Duplicate or unexpected delivery case')
        program = self.book.bundles[name]
        endpoint = authored_clock(self.book.cases[name]['request_horizon'])
        options = {'end': str(endpoint.numerator) if endpoint.denominator == 1 else str(float(endpoint)), 'fps': 2, 'helpers': False}
        require(record['program_revision'] == program.program_revision and record['project_id'] == 'case-' + name and
                record['export_role'] == name + '/export' and record['options'] == options, 'Delivery settings or source identity differ')
        request, response = self.at(record['export_role'])
        self.required.add(record['export_role'])
        require(request['operation'] == 'export' and request['project_id'] == record['project_id'] and
                request['program_revision'] == program.program_revision and request['destination'] == TARGET and request['options'] == options, 'Export request was substituted')
        require(response['status'] == 'succeeded' and response['achieved_level'] == 'delivered' and
                response['accepted_program_revision'] == program.program_revision, 'Export did not deliver the accepted program')
        result = response['result']
        require(result['program_revision'] == program.program_revision and result['destination'] == TARGET and
                result['artifact_id'] == record['artifact_id'] and result['sha256'] == record['sha256'] and
                result['total_bytes'] == record['total_bytes'], 'Export receipt artifact binding differs')
        run = result['run_state']
        require(run['run_id'] == response['run_id'] and run['run_id'] not in self.run_ids and
                run['program_revision'] == program.program_revision and run['status'] == 'ready' and run['failure'] is None and
                run['valid_until_side'] == 'after' and clock(run['valid_until_seconds']) == endpoint and not run['candidate_only'], 'Export retained the wrong run or endpoint')
        self.run_ids.add(run['run_id'])
        self.snapshot_state(name, run['last_valid_state'], endpoint, 'after')
        files = self.retained_case_files(record, program)
        data = files['scene.glb']
        require(sha(data) == record['sha256'] and len(data) == record['total_bytes'] and
                record['artifact_id'] == 'artifact:' + sha(data).removeprefix('sha256:'), 'Retained GLB differs from the artifact identity')
        report = decode(files['scene.export.json'])
        require(report == result['report'], 'Retained export report differs from the actual receipt')
        require(report['schema_version'] == 'ontokin.glb-report/0.5' and report['target_contract'] == TARGET and
                report['program_revision'] == program.program_revision and report['program']['manifest'] == program.manifest(), 'Export report lost source identity')
        require(report['artifact']['sha256'] == sha(data) and report['artifact']['byte_length'] == len(data) and
                report['source_code_sha256'] == self.implementation['source_code_sha256'].removeprefix('sha256:') and
                report['exporter']['version'] == self.implementation['version'], 'Export report implementation or artifact differs')
        require(clock(report['sampling']['end_seconds']) == endpoint and report['sampling']['requested_fps'] == 2 and
                report['sampling']['evaluated_horizon'] == 'requested_prefix_inclusive_after_side' and
                report['validation']['status'] == 'passed' and report['force_profile'] == FORCE_PROFILE,
                'Export report interval, validation or force profile differs')
        limits = {'position_m': .001, 'rotation_rad': .001, 'time_seconds': .000001}
        require(all(type(report['tolerances'][key]) in (int, float) and 0 < report['tolerances'][key] <= value
                    for key, value in limits.items()), 'Delivery tolerances were relaxed')
        chunk_count = self.artifact_chunks(record, program, report, data)
        oracle = {**oracle_for(name), 'program_revision': program.program_revision}
        require(decode(files['oracle.json']) == oracle, 'Independent fixed-source oracle was modified')
        reference = decode(files['scene.reference.json'])
        require(reference['schema_version'] == 'ontokin.force-native-reference/0.1' and
                reference['program_revision'] == program.program_revision and reference['source_manifest'] == program.manifest() and
                reference['artifact_sha256'] == sha(data) and reference['implementation'] == self.implementation and
                reference['tolerances'] == report['tolerances'], 'Native reference lost source/artifact/implementation identity')
        samples = sample_requests(name)
        require(len(record['reference_roles']) == len(reference['samples']) == len(samples), 'Native reference sample count differs')
        decoded = GLB(data, expected_objects=self.book.objects(name))
        metadata = decoded.document['extras']['ontokin']
        require(metadata['target_contract'] == TARGET and metadata['profile'] == 'force-0.1' and
                metadata['program'] == report['program'] and metadata['source'] == report['source'] and
                metadata['force_profile'] == FORCE_PROFILE, 'Encoded source/program/profile provenance differs')
        require(set(decoded.nodes) == self.book.objects(name), 'Encoded scene omitted or added source objects')
        source_units = {unit.source_id: unit for unit in program.units}
        require(set(metadata['program']['sources']) == set(source_units), 'Encoded source closure differs')
        for source_id, unit in source_units.items():
            descriptor = metadata['program']['sources'][source_id]
            require(descriptor['source_revision'] == unit.revision and descriptor['filename'] == unit.filename, 'Encoded source unit identity differs')
        objects = {item['path']: item for item in (*oracle['shapes'], *oracle['empty_objects'])}
        boundaries = boundary_times(name)
        for times, _ in decoded.tracks.values():
            require(times[0] == 0 and abs(times[-1] - float(endpoint)) <= report['tolerances']['time_seconds'] and
                    all(min(abs(value - float(Q(boundary))) for value in times) <= report['tolerances']['time_seconds']
                        for boundary in boundaries), 'Encoded animation lost the requested interval or an exact boundary key')
        actual_samples = {}
        max_position = max_rotation = 0.
        for index, sample in enumerate(samples):
            role = record['reference_roles'][index]
            require(role == f'{name}/destination-sample/{index:04d}', 'Native reference roles are not contiguous')
            self.required.add(role)
            query, reply = self.at(role)
            require(query['operation'] == 'inspect' and query['program_revision'] == program.program_revision and
                    query['run_id'] == response['run_id'] and query['selector'] == {'kind': 'object'} and query['fields'] == ['identity', 'state'] and
                    query['limit'] == 1000 and query.get('frame', 'world') == 'world' and
                    query['time'] == {'seconds': sample['time_seconds'], 'side': sample['side']}, 'Native reference inspection was substituted')
            require(reply['status'] == 'succeeded' and not reply['truncated'] and reply['next_cursor'] is None and
                    reply['result']['total'] == len(reply['result']['items']) == len(objects), 'Native reference inspection is incomplete')
            require(reply['result']['context'] == dict(fields=['identity', 'state'], frame='world',
                program_revision=program.program_revision, run_id=response['run_id'], selector={'kind': 'object'},
                side=sample['side'], time_seconds=sample['time_seconds']), 'Native reference inspection context differs')
            states = {item['path']: item['state'] for item in reply['result']['items']}
            projected = reference_objects(reply['result']['items'], objects)
            require(reference['samples'][index] == {**sample, 'objects': projected}, 'Native reference was not obtained from the retained Agent responses')
            actual_samples[(sample['time_seconds'], sample['side'])] = states
            for path, state in states.items():
                require(state['program_revision'] == program.program_revision and state['run_id'] == response['run_id'] and
                        state['time_seconds'] == sample['time_seconds'] and state['side'] == sample['side'] and state['available'] and
                        state['pose_frame'] == 'world' and state['velocity_expressed_in'] == state['velocity_measured_in'] == 'world' and
                        state['element_id'] == objects[path]['element_id'], 'Native sample state context differs')
                self.book.check_projection(name, path, state, Q(sample['time_seconds']), sample['side'])
                expected_position, expected_rotation = expected_pose(objects[path], sample['time_seconds'])
                vector(state['position_m'], expected_position, 'Independent source reference position')
                require(rotation_error((*state['orientation_wxyz'][1:], state['orientation_wxyz'][0]), expected_rotation) <= 1e-7, 'Independent source reference rotation differs')
                pose = decoded.pose(path, float(sample['time_seconds']))
                position = math.dist(pose['translation'], expected_position)
                rotation = rotation_error(pose['rotation'], expected_rotation)
                require(position <= report['tolerances']['position_m'] and rotation <= report['tolerances']['rotation_rad'], 'Decoded recorded pose differs from the independent source oracle')
                max_position, max_rotation = max(max_position, position), max(max_rotation, rotation)
        require([record['source_seconds'] for record in metadata['boundary_states']] == boundaries, 'Exact encoded force boundaries were lost or added')
        for boundary in metadata['boundary_states']:
            states = actual_samples[(boundary['source_seconds'], 'after')]
            for key, field in (('force_states_after', 'forces'), ('impulse_states_after', 'impulses'),
                               ('pose_authorities_after', 'pose_authority')):
                require(boundary[key] == {path: state[field] for path, state in states.items()}, 'Encoded boundary source history differs: ' + key)
        self.delivered[name] = {'decoded': decoded, 'report': report, 'reference': reference,
            'sha256': sha(data), 'bytes': len(data), 'artifact_chunks': chunk_count,
            'source_samples': len(samples), 'max_position_error_m': max_position, 'max_rotation_error_rad': max_rotation}

    def extra_checks(self):
        roles = {'discovery', 'failure/invalid-create', 'failure/invalid-edit', 'retry/same-export',
                 'retry/collision', 'retry/status', 'isolation/foreign-artifact', 'failure/artifact-offset',
                 'failure/final-budget', 'failure/budget-candidate-export', 'cancel/submit', 'cancel/request',
                 'cancel/result', 'cancel/status', 'prefix/full-failure', 'prefix/reject-later', 'failure/head'}
        for role in roles:
            self.at(role)
        query, response = self.at('discovery')
        require(query['operation'] == 'discover' and query['profile'] == 'force-0.1' and response['status'] == 'succeeded' and
                not response['truncated'] and response['result']['delivery_targets'] == [TARGET], 'Missing current force delivery discovery')
        catalog = {item['name']: item for item in response['result']['items']}
        require(catalog[TARGET]['availability'] == 'available_in_bounded_profile' and
                catalog[TARGET]['available_levels'] == ['delivered'] and
                catalog['external_forces_and_actuators']['availability'] == 'unsupported', 'Discovery changed bounded capability meaning')
        for role, code in (('failure/invalid-create', 'OKL-E-TYPE'), ('failure/invalid-edit', 'OKL-E-EVENT-ORDER'),
            ('retry/collision', 'OKL-E-REQUEST-ID'), ('isolation/foreign-artifact', 'OKA-E-ARTIFACT'),
            ('failure/artifact-offset', 'OKA-E-ARTIFACT'), ('failure/final-budget', 'OKA-E-RESOURCE'),
            ('failure/budget-candidate-export', 'OKL-E-REVISION'), ('prefix/full-failure', 'OKL-E-NUMERIC'),
            ('prefix/reject-later', 'OKL-E-SAMPLE')):
            self.failure(self.at(role)[1], code)
        query, response = self.at('failure/invalid-create')
        require(query['bundle'] == self.book.bundles['N01'].to_payload() and response['accepted_program_revision'] is None, 'Wrong invalid source candidate')
        query, _ = self.at('failure/invalid-edit')
        program = self.book.bundles['P01']
        start = program.entry.raw.index(b'for 1[s]') + 4
        require(query['operation'] == 'edit' and query['expected_program_revision'] == program.program_revision and
                query['patches'] == [dict(source_id='entry', source_revision=program.entry.revision,
                    element_id=['force-demo', 'demo'], start_byte=start, end_byte=start + 4,
                    expected_text='1[s]', replacement='-1[s]')], 'Invalid repair request was substituted')
        export_query, exported = self.at('P01/export')
        retry_query, retry = self.at('retry/same-export')
        require(export_query == retry_query and exported == retry, 'Exact export retry differs')
        collision, _ = self.at('retry/collision')
        require(collision == {**export_query, 'options': {**export_query['options'], 'fps': 3}}, 'Retry collision did not change the actual export payload')
        query, response = self.at('retry/status')
        require(query['target_request_id'] == export_query['request_id'] and response['result']['target'] == exported, 'Export status did not reconcile its retained receipt')
        query, response = self.at('isolation/foreign-artifact')
        require(query['project_id'] != export_query['project_id'] and query['artifact_id'] == exported['result']['artifact_id'] and
                response['accepted_program_revision'] is None, 'Artifact project-isolation probe differs')
        query, _ = self.at('failure/artifact-offset')
        require(query['project_id'] == export_query['project_id'] and query['artifact_id'] == exported['result']['artifact_id'] and
                query['offset'] == exported['result']['total_bytes'] + 1, 'Artifact offset probe differs')
        query, response = self.at('failure/final-budget')
        require(query['operation'] == 'create' and query['bundle'] == program.to_payload() and query['requested_level'] == 'delivered' and
                query['destination'] == TARGET and query['options'] == export_query['options'] and
                query['budgets'] == {'max_value_entries': entry_count(exported) - 1}, 'Final response budget was not selected from the actual full result')
        require(response['accepted_program_revision'] is None and response['run_id'] is None and response['result'] is None and
                response['protocol_error']['details']['effects_committed'] is False, 'Final response budget published partial effects')
        query, response = self.at('failure/budget-candidate-export')
        require(query['project_id'] == self.at('failure/final-budget')[0]['project_id'] and
                query['program_revision'] == program.program_revision and response['accepted_program_revision'] is None, 'Failed delivered candidate acquired ordinary export authority')
        queued, receipt = self.at('cancel/submit')
        final_query, final = self.at('cancel/result')
        require(queued == final_query and queued['requested_level'] == 'delivered' and queued['destination'] == TARGET and
                receipt['status'] == 'queued' and final['status'] == 'cancelled' and final['accepted_program_revision'] is None and
                final['run_id'] is None and final['result'] is None, 'Cancelled delivered request published effects')
        for role in ('cancel/request', 'cancel/status'):
            query, response = self.at(role)
            require(query['target_request_id'] == queued['request_id'] and response['result']['target'] == final, 'Cancellation status lost the original request')
        query, response = self.at('prefix/full-failure')
        require(query['operation'] == 'export' and 'options' not in query and
                query['program_revision'] == self.book.bundles['P21'].program_revision and
                (response['result'] is None or 'artifact_id' not in response['result']), 'Full-horizon force failure produced an artifact')
        query, _ = self.at('prefix/reject-later')
        require(query['run_id'] == self.at('P21/export')[1]['run_id'] and
                query['time'] == {'seconds': '1.5', 'side': 'after'}, 'Prefix artifact run incorrectly authorizes a later state')
        query, response = self.at('failure/head')
        require(query['operation'] == 'inspect' and query['program_revision'] == program.program_revision and
                response['status'] == 'succeeded' and response['accepted_program_revision'] == program.program_revision, 'Failed repairs changed the accepted original source')
        for name in ('P11', 'P12', 'P13'):
            for path in ('rack.props["first"]', 'rack.props["second"]'):
                self.delivered['P10']['decoded'].require_same_geometry(self.delivered[name]['decoded'], path)
            before = self.at('P10/run')[1]['result']['run_state']['last_valid_state']['objects']['rack.props["second"]']
            after = self.at(name + '/run')[1]['result']['run_state']['last_valid_state']['objects']['rack.props["second"]']
            for field in ('position_m', 'orientation_wxyz', 'velocity_m_per_s', 'angular_velocity_rad_per_s'):
                require(before[field] == after[field], 'Physical source repair changed its unaffected sibling')
        return roles

    def audit(self):
        manifest = self.read('workflow.json')
        require(manifest['schema_version'] == SCHEMA and manifest['status'] == 'recorded', 'Incomplete or unsupported delivery workflow')
        require(manifest['implementation'] == self.implementation and manifest['protocol'] == PROTOCOL and
                manifest['target_contract'] == TARGET, 'Wrong current implementation or delivery binding')
        require(manifest['writer_sha256'] == sha((ROOT / 'tools/build_force_delivery_demo.py').read_bytes()), 'Stale delivery workflow writer')
        require(manifest['helper_inputs'] == {name: sha((ROOT / name).read_bytes()) for name in
                ('tools/build_force_agent_demo.py', 'tools/force_oracles.py')}, 'Stale delivery writer helpers')
        require(manifest['fixture_inputs'] == {name: sha((DATA / name).read_bytes()) for name in
                ('acceptance.json', 'reviewed-acceptance.json', 'source-errata.json', 'ADOPTION.md')}, 'Adopted source acceptance changed')
        revision = checked_source_revision(manifest)
        require(manifest['source_fixtures'] == list(CASE_IDS), 'Wrong selected Agent delivery corpus')
        self.required = set()
        self.delivered = {}
        self.trace(manifest)
        for name in CASE_IDS:
            self.source_workflow(name)
        require([record['case_id'] for record in manifest['deliveries']] == list(CASE_IDS), 'Missing or reordered source deliveries')
        for record in manifest['deliveries']:
            self.delivery(record)
        self.required.update(self.extra_checks())
        require(set(self.roles) == self.required, 'Unexpected or missing delivery workflow roles')
        labels = set()
        for snapshot in manifest['snapshots']:
            label = snapshot['label']
            require(label not in labels, 'Repeated source snapshot')
            labels.add(label)
            name = 'P10' if label.endswith('-base') else label
            require(name in CASE_IDS, 'Unexpected source snapshot')
            program = self.book.bundles[name]
            self.keep_file(snapshot['bundle_file'])
            payload = self.read(snapshot['bundle_file'], snapshot['bundle_sha256'])
            require(payload == program.to_payload() and snapshot['program_revision'] == program.program_revision and
                    (snapshot['project_id'], program.program_revision) in self.accepted, 'Source snapshot was not accepted by the actual trace')
        require(labels == set(CASE_IDS) | {'P11-base', 'P12-base', 'P13-base'}, 'Missing exact source snapshots')
        require(manifest['exchange_count'] == len(self.roles) and manifest['snapshot_count'] == len(labels) and
                manifest['delivery_count'] == len(self.delivered) and manifest['sample_count'] ==
                sum(len(self.book.cases[name]['expected_samples']) for name in CASE_IDS) and
                manifest['artifact_chunk_count'] == sum(item['artifact_chunks'] for item in self.delivered.values()) and
                manifest['destination_sample_count'] == sum(item['source_samples'] for item in self.delivered.values()), 'Incorrect retained evidence counts')
        actual_files = {path.relative_to(self.root).as_posix() for path in self.root.rglob('*')
                        if path.is_file() and path.relative_to(self.root).parts[0] != 'service-store'}
        require(actual_files == self.files | {'workflow.json'}, 'Unbound or missing retained workflow files')
        return dict(schema_version=AUDIT_SCHEMA, status='passed', checked_at_utc=datetime.now(timezone.utc).isoformat(),
            implementation=self.implementation, workflow_sha256=sha((self.root / 'workflow.json').read_bytes()),
            source_revision=revision, source_revision_after=manifest['source_revision_after'],
            environment=manifest['environment'],
            verifier_sha256=sha(Path(__file__).read_bytes()),
            helper_inputs={name: sha((ROOT / name).read_bytes()) for name in
                ('tools/verify_force_agent_workflow.py', 'tools/force_oracles.py')},
            schema_inputs=self.schemas.hashes, fixture_inputs=manifest['fixture_inputs'],
            exchanges=len(self.roles), source_snapshots=len(labels), source_cases=len(CASE_IDS),
            predetermined_samples=manifest['sample_count'], destination_samples=manifest['destination_sample_count'],
            force_projections_schema_checked=self.counter, artifact_chunks=manifest['artifact_chunk_count'],
            deliveries=[{'case_id': name, **{key: value for key, value in item.items() if key not in ('decoded', 'report', 'reference')}}
                        for name, item in self.delivered.items()],
            decoded_checks=['embedded GLB structure', 'exact program/source and force-boundary metadata',
                            'actual artifact-chunk reconstruction', 'independent predetermined source poses',
                            'unchanged sibling motion and physical-repair geometry/materials'],
            destination_validated=False, native_geometry_and_browser_review='separate_required_roles_over_retained_artifacts',
            full_force_release_complete=False, full_product_complete=False)


def verify(directory, schemas=None):
    try:
        return Reader(directory, schemas).audit()
    except EvidenceError:
        raise
    except Exception as error:
        raise EvidenceError(f'Malformed or unsupported delivery evidence: {type(error).__name__}: {error}') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workflow-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='Write the audit outside the immutable workflow directory')
    arguments = parser.parse_args()
    if arguments.output.resolve().is_relative_to(arguments.workflow_dir.resolve()):
        parser.error('Write the audit outside the immutable workflow directory')
    try:
        report = verify(arguments.workflow_dir)
    except EvidenceError as error:
        report = dict(schema_version=AUDIT_SCHEMA, status='failed', error=str(error), full_force_release_complete=False)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
