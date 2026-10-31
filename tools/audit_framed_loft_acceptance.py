#!/usr/bin/env python3
"""Independently reconcile C078 acceptance evidence; without importing product code.

This checker reads actual protocol JSONL, individual exchange files, a read-only
SQLite snapshot, pinned Git fixture bytes and delivered GLB animation accessors.
It never invokes OntoKin or imports production geometry or its predicates.
Existing geometry reports are reconciled, not rerun. Schema validation uses
the pinned verification-only JSON Schema packages and candidate Git schemas. Every invocation writes a
new report, including failures; the caller must grant the serialized audit slot.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import sys
import traceback


PROTOCOL = 'ontokin.agent/0.11'
PROFILE = 'framed-polygon-loft-0.1'
TARGET = 'ontokin.glb/0.11'
FIXTURES = 'examples/framed-polygon-lofts/'
FREEZE = 'da56cc3b57469c8a01546e4a3ac7cc8467ddccbb'
OPERATIONS = sorted(['discover', 'create', 'validate', 'inspect', 'surface.mesh_page',
                     'edit', 'evaluate', 'export', 'artifact', 'reset', 'cancel', 'status'])
DEFAULTS = {'max_operations': 100000, 'max_elapsed_ms': 30000}
MAXIMUM = {'max_operations': 2000000, 'max_elapsed_ms': 80000}
REDUCED = {'max_operations': 50000, 'max_elapsed_ms': 30000}
PROJECT = 'c078'
SOURCE_DIRS = {'ontokin', 'tests', 'tools', 'docs', 'examples', 'schemas', 'prototypes', '.github'}
ROOT_FILES = {'pyproject.toml', 'README.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'LICENSE',
              '.gitignore', '.gitattributes', '.lfsconfig'}
IGNORED = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox', '.cache',
           '.pytest_cache', '.mypy_cache', '.ruff_cache', 'build', 'dist', '_build'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def loads(raw):
    def bad(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            bad(value)
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=finite)


def bundle_identity(payload):
    """Published bundle identity formula, without the production bundle class."""
    units = [{'source_id': 'entry', 'package_id': None, 'version': None,
              'filename': payload['entry']['filename'],
              'source_revision': 'sha256:' + sha(payload['entry']['source'].encode('utf-8'))}]
    for module in payload['modules']:
        units.append({'source_id': 'package:' + module['package_id'] + '@' + module['version'],
                      'package_id': module['package_id'], 'version': module['version'],
                      'filename': module['filename'],
                      'source_revision': 'sha256:' + sha(module['source'].encode('utf-8'))})
    manifest = {'schema_version': 'ontokin.bundle/0.1', 'entry_source_id': 'entry',
                'units': sorted(units, key=lambda item: item['source_id'])}
    return 'sha256:' + sha(b'ontokin.bundle/0.1\0' + canonical(manifest)), manifest


def normalize_sections(sections):
    """Compare authored fields, accepting the documented native and summary shapes."""
    result = []
    for section in sorted(sections, key=lambda row: row['order']):
        frame = section.get('frame')
        origin = frame['position'] if type(frame) is dict else section['origin_m']
        rotation = frame['rotation'] if type(frame) is dict else section['orientation_wxyz']
        rings = []
        for ring in sorted(section['rings'], key=lambda row: row['order']):
            vertices = [{'key': vertex['key'], 'order': vertex['order'],
                         'point_m': vertex['point_m'],
                         'region': vertex.get('region', vertex.get('side_region'))}
                        for vertex in sorted(ring['vertices'], key=lambda row: row['order'])]
            rings.append({'key': ring['key'], 'order': ring['order'], 'role': ring['role'],
                          'vertices': vertices})
        result.append({'key': section['key'], 'order': section['order'],
                       'origin_m': origin, 'orientation_wxyz': rotation, 'rings': rings})
    return result


def legacy_geometry(framed):
    """Published identity-frame comparison, without interpreting source code."""
    result = loads(canonical(framed))
    sections = []
    for section in framed['sections']:
        if section['orientation_wxyz'] != [1, 0, 0, 0] or section['origin_m'][:2] != [0, 0]:
            raise ValueError('Legacy comparison requires frozen axial identity frames')
        sections.append({'key': section['key'], 'order': section['order'],
                         'station_m': section['origin_m'][2], 'rings': section['rings']})
    result['sections'] = sections
    result['station_range_m'] = [sections[0]['station_m'], sections[-1]['station_m']]
    for key in ('section_transform_rule', 'source_positions', 'progression'):
        result.pop(key, None)
    return result


def inventory_path(name):
    parts = Path(name).parts
    return bool(parts and (name in ROOT_FILES or parts[0] in SOURCE_DIRS) and
                not any(part in IGNORED or part == '.env' or part.startswith('.env.') or
                        part.endswith(('.pyc', '.pyo')) for part in parts))


def rotation_error_identity(rotation):
    """Geodesic angle for an actual xyzw quaternion, including sign equivalence."""
    if (type(rotation) not in (list, tuple) or len(rotation) != 4 or
            any(type(value) not in (int, float) or not math.isfinite(value) for value in rotation)):
        return math.inf
    norm = math.hypot(*rotation)
    if not norm or abs(norm - 1) > 1e-5:
        return math.inf
    return 2 * math.atan2(math.hypot(*rotation[:3]), abs(rotation[3]))


def returned_chunk(row, *, artifact_id, revision, producer, implementation, digest,
                   total, offset, maximum):
    """Read a single raw response; every continuation and ownership field matters."""
    request, response = row['request'], row['response']
    result = response['result']
    raw = base64.b64decode(result['data_base64'], validate=True)
    expected_next = offset + len(raw)
    expected_next = expected_next if expected_next < total else None
    valid = (
        type(total) is int and 0 < total <= 64 * 1024 * 1024 and
        type(offset) is int and 0 <= offset < total and
        request['operation'] == response['operation'] == 'artifact' and
        request['request_id'] == response['request_id'] and response['status'] == 'succeeded' and
        request['artifact_id'] == result['artifact_id'] == artifact_id and
        request.get('offset', 0) == result['offset'] == offset and request['max_bytes'] == maximum and
        len(raw) == min(maximum, total - offset) and result['program_revision'] == revision and
        response['program_revision'] == revision and result['sha256'] == digest and
        result['total_bytes'] == total and result['producer_request_id'] == producer and
        result['mime_type'] == 'model/gltf-binary' and
        result['artifact_provenance']['source_code_sha256'] == implementation and
        result['artifact_provenance']['program_revision'] == revision and
        result['next_offset'] == expected_next and response['truncated'] == (expected_next is not None))
    if not valid:
        raise ValueError('Returned chunk identity, bytes, ownership or continuation disagrees at offset ' + str(offset))
    return raw


def witness_positions(geometry):
    """Quantize frozen source witnesses using the separately inherited placement rule."""
    if 'source_positions' in geometry:
        source = [tuple(row['position_m']) for row in geometry['source_positions']]
        if any([float(value).hex() for value in row['position_m']] != row['position_hex']
               for row in geometry['source_positions']):
            raise ValueError('Frozen source-position hex identity disagrees')
    else:
        source = [(vertex['point_m'][0], vertex['point_m'][1], section['station_m'])
                  for section in geometry['sections'] for ring in section['rings'] for vertex in ring['vertices']]
    quaternion = geometry.get('local_orientation_wxyz', [1, 0, 0, 0])
    norm = math.hypot(*quaternion)
    w, x, y, z = (Fraction(value / norm) for value in quaternion)
    matrix = ((1 - 2*(y*y + z*z), 2*(x*y - w*z), 2*(x*z + w*y)),
              (2*(x*y + w*z), 1 - 2*(x*x + z*z), 2*(y*z - w*x)),
              (2*(x*z - w*y), 2*(y*z + w*x), 1 - 2*(x*x + y*y)))
    offset = geometry.get('local_position_m', [0, 0, 0])
    result = []
    for point in source:
        exact = tuple(Fraction(value) for value in point)
        placed = [float(sum(a*b for a, b in zip(row, exact))) + float(shift)
                  for row, shift in zip(matrix, offset)]
        result.append(tuple(struct.unpack('<f', struct.pack('<f', value))[0] for value in placed))
    return result


class Audit:
    def __init__(self, args):
        self.args = args
        self.root = args.acceptance_dir.resolve()
        self.repo = args.repo.resolve()
        self.inputs = {}
        self.git_inputs = {}
        self.report = {
            'schema_version': 'ontokin.c078-independent-agent-evidence/0.1',
            'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(),
            'acceptance_directory': str(self.root), 'candidate_commit': args.candidate_commit,
            'freeze_commit': args.freeze_commit,
            'checker': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).read_bytes())},
            'python': sys.version, 'command': [sys.executable, *sys.argv], 'checks': [], 'observed_requests': [],
            'coverage': {
                'raw_protocol_and_sqlite': 'independently reconciled on successful completion',
                'artifact_bytes': 'reconstructed from raw returned chunks and compared with the store and file',
                'motion': 'independently decoded from actual binary32 animation accessors',
                'geometry': 'actual supplied identities, flat corners, normals, PBR, area and volume rechecked; complete cap/strip/contact proofs reconciled to existing independent reports rather than rerun',
                'destination': 'GLB recorded playback only; no Unreal or live-physics claim'},
            'release_acceptance': False}

    def check(self, condition, label, **details):
        row = {'label': label, 'passed': bool(condition)}
        if details:
            row['observed'] = details
        self.report['checks'].append(row)
        if not condition:
            raise AssertionError(label)

    def read(self, name):
        path = self.root / name
        if not path.resolve().is_relative_to(self.root) or path.is_symlink():
            raise ValueError('Evidence must be a regular file within its declared directory: ' + str(name))
        raw = path.read_bytes()
        self.inputs[str(path)] = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
        return raw

    def json(self, name):
        return loads(self.read(name))

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-C', str(self.repo), *args],
                                       env=self.git_environment(), timeout=60)

    def git_environment(self):
        environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                           GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0',
                           GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1')
        return environment

    def git_file(self, revision, path):
        key = revision + ':' + path
        raw = self.git('show', key)
        self.git_inputs[key] = {'git_object': key, 'bytes': len(raw), 'sha256': sha(raw)}
        return raw

    def fixture(self, name):
        raw = self.git_file(self.args.freeze_commit, FIXTURES + name)
        self.check(raw == self.git_file(self.args.candidate_commit, FIXTURES + name),
                   'Candidate retains frozen fixture ' + name)
        item = self.freeze['files'].get(name)
        if item is not None:
            self.check(item == {'bytes': len(raw), 'sha256': sha(raw)}, 'Frozen manifest hash ' + name)
        return raw

    def payload(self, name, entry_filename=None):
        modules = []
        if name in {self.spec['assembly'][k] for k in ('entry', 'repaired_entry', 'invalid_entry')} | {self.spec['generated']['entry']}:
            library = self.spec['assembly']['library']
            modules = [{'package_id': library['package'], 'version': library['version'],
                        'filename': library['filename'], 'source': self.fixture(library['filename']).decode('utf-8')}]
        return {'schema_version': 'ontokin.bundle/0.1',
                'entry': {'filename': entry_filename or name, 'source': self.fixture(name).decode('utf-8')},
                'modules': modules}

    def equal_vector(self, actual, wanted, label, tolerance=.001):
        self.check(len(actual) == len(wanted) and
                   all(type(a) in (int, float) and math.isfinite(a) and abs(a-b) <= tolerance
                       for a, b in zip(actual, wanted)), label, actual=actual, expected=wanted)

    def prepare(self):
        self.check(bool(re.fullmatch('[0-9a-f]{40}', self.args.candidate_commit)), 'Exact candidate SHA supplied')
        self.check(bool(re.fullmatch('[0-9a-f]{40}', self.args.freeze_commit)), 'Exact freeze SHA supplied')
        summary = self.json('summary.json')
        self.summary = summary
        tree = self.git('rev-parse', self.args.candidate_commit + '^{tree}').decode().strip()
        self.report['candidate_tree'] = tree
        self.check(summary['status'] == 'passed' and 'failure' not in summary and
                   not summary.get('finalization_failures') and summary['release_acceptance'] is False,
                   'Acceptance completed its bounded development workflow')
        self.check(summary['git']['local_head'] == self.args.candidate_commit and
                   summary['git']['local_tree'] == tree and not summary['git']['tracked_worktree_status'] and
                   not summary['git'].get('untracked_source_files'), 'Acceptance identifies the exact clean candidate')
        before, after = self.json('source-before.json'), self.json('source-after.json')
        self.check(before == after, 'Complete recorded source inventories unchanged',
                   inventory_sha256=before['sha256'], file_count=before['file_count'])
        self.check(before['file_count'] == len(before['files']) and
                   len({x['path'] for x in before['files']}) == len(before['files']), 'Source inventory has unique complete entries')
        self.check(before['sha256'] == 'sha256:' + sha(canonical(before['files'])),
                   'Source inventory digest recomputes from its actual rows')
        self.bind_source_inventory(before)
        self.freeze = loads(self.git_file(self.args.freeze_commit, FIXTURES + 'acceptance-freeze.json'))
        self.check(self.json('input-freeze.json') == self.freeze, 'Acceptance used the exact published freeze')
        self.check(self.git_file(self.args.candidate_commit, FIXTURES + 'acceptance-freeze.json') ==
                   self.git_file(self.args.freeze_commit, FIXTURES + 'acceptance-freeze.json'), 'Candidate freeze manifest unchanged')
        self.spec = loads(self.fixture('expected.json'))
        self.check(self.freeze['case_count'] == len(self.spec['cases']) == 69 and
                   dict(Counter(case['expected_outcome'] for case in self.spec['cases'])) ==
                   self.freeze['outcome_counts'] ==
                   {'valid': 26, 'invalid': 40, 'source_valid_delivery_rejected': 3} and
                   self.spec['frozen_before_implementation'] is True and
                   self.spec['maximum_host_policy'] == MAXIMUM, 'Fixed independent fixture inventory')
        for name in self.freeze['files']:
            self.fixture(name)
        adoption = self.freeze['decision_file']
        self.check(sha(self.git_file(self.args.freeze_commit, adoption)) == self.freeze['decision_sha256'] and
                   self.git_file(self.args.candidate_commit, adoption) == self.git_file(self.args.freeze_commit, adoption),
                   'Candidate retains the exact adopted section-frame contract')
        self.check(summary['schema_version'] == 'ontokin.framed-loft-acceptance/0.1' and
                   summary['profile'] == PROFILE and summary['agent_contract'] == PROTOCOL and
                   summary['target_contract'] == TARGET and summary['frozen_input_commit'] == self.args.freeze_commit,
                   'Acceptance source, Agent and destination selectors are explicit')
        # Bind service implementation receipts to candidate Python bytes, using
        # the documented fingerprint ordering rather than importing the service.
        paths = self.git('ls-tree', '-r', '--name-only', self.args.candidate_commit, '--', 'ontokin').decode().splitlines()
        paths = sorted(p for p in paths if p.startswith('ontokin/') and p.count('/') == 1 and p.endswith('.py'))
        digest = hashlib.sha256()
        for path in paths:
            digest.update(Path(path).name.encode('utf-8') + b'\0' + self.git_file(self.args.candidate_commit, path) + b'\0')
        self.implementation_sha = 'sha256:' + digest.hexdigest()
        self.report['implementation_source_code_sha256'] = self.implementation_sha
        assembly = self.spec['assembly']
        self.programs = {}
        for role, filename in [('original', assembly['entry']), ('invalid', assembly['invalid_entry']),
                               ('repaired', assembly['repaired_entry'])]:
            payload = self.payload(filename, assembly['entry'])
            revision, manifest = bundle_identity(payload)
            self.programs[role] = {'payload': payload, 'revision': revision, 'manifest': manifest}
        self.report['programs'] = {role: {'revision': value['revision'], 'manifest': value['manifest']}
                                   for role, value in self.programs.items()}
        library = assembly['library']
        module = self.programs['original']['payload']['modules'][0]
        self.check(sha(module['source'].encode()) == library['sha256'] and
                   ('digest "sha256:' + library['sha256'] + '"') in self.programs['original']['payload']['entry']['source'],
                   'Pinned reusable module bytes and source import digest agree', source_id=library['source_id'])
        self.load_schemas()

    def bind_source_inventory(self, inventory):
        """Hash candidate blobs directly; no checkout state or summary flag substitutes."""
        entries = []
        for raw in self.git('ls-tree', '-rz', '--full-tree', self.args.candidate_commit).split(b'\0'):
            if not raw:
                continue
            metadata, encoded_name = raw.split(b'\t', 1)
            mode, kind, object_id = metadata.decode().split()
            name = encoded_name.decode('utf-8')
            if inventory_path(name):
                self.check(kind == 'blob' and mode in ('100644', '100755'),
                           'Inventory entry is a regular candidate blob ' + name)
                entries.append((name, object_id))
        rows = sorted(inventory['files'], key=lambda row: row['path'])
        self.check(sorted(inventory['files'], key=lambda row: Path(row['path'])) == inventory['files'] and
                   [name for name, _ in sorted(entries)] ==
                   [row['path'] for row in rows], 'Recorded complete source inventory equals candidate paths')
        process = subprocess.Popen(['git', '-C', str(self.repo), 'cat-file', '--batch'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=self.git_environment())
        total_bytes = 0
        try:
            for (name, object_id), wanted in zip(sorted(entries), rows):
                process.stdin.write((object_id + '\n').encode())
                process.stdin.flush()
                header = process.stdout.readline().decode().strip().split()
                if len(header) != 3 or header[:2] != [object_id, 'blob']:
                    raise ValueError('Candidate Git blob read failed: ' + name)
                remaining = size = int(header[2])
                digest = hashlib.sha256()
                while remaining:
                    data = process.stdout.read(min(remaining, 1024 * 1024))
                    if not data:
                        raise ValueError('Truncated candidate Git blob: ' + name)
                    digest.update(data)
                    remaining -= len(data)
                if process.stdout.read(1) != b'\n':
                    raise ValueError('Malformed candidate Git batch framing')
                self.check(wanted == {'path': name, 'bytes': size, 'sha256': 'sha256:' + digest.hexdigest()},
                           'Recorded source bytes equal candidate blob ' + name)
                total_bytes += size
            process.stdin.close()
            self.check(process.wait(timeout=60) == 0, 'Candidate Git batch completed')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            process.stdout.close()
            process.stderr.close()
            if not process.stdin.closed:
                process.stdin.close()
        self.report['source_inventory_binding'] = {'files': len(rows), 'bytes': total_bytes,
                                                    'sha256': inventory['sha256'],
                                                    'method': 'actual candidate Git blob bytes'}

    def load_schemas(self):
        """Resolve only the candidate-pinned local registry; never fetch remote schemas."""
        from importlib.metadata import version
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        names = self.git('ls-tree', '-r', '--name-only', self.args.candidate_commit, '--',
                         'docs/language-design/agent-v0.11').decode().splitlines()
        paths = sorted(name for name in names if name.endswith('.schema.json'))
        paths += ['docs/language-design/' + name for name in (
            'construction-v0.1/bundle.schema.json', 'agent-v0.2/diagnostic.schema.json',
            'force-v0.1/forces.schema.json', 'impulse-v0.1/impulses.schema.json',
            'planar-reach-v0.1/schema-drafts/reach-projection.schema.json',
            'planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json',
            'planar-reach-v0.1/schema-drafts/common.schema.json')]
        raws = [self.git_file(self.args.candidate_commit, path) for path in paths]
        schemas = [loads(raw) for raw in raws]
        self.check(len({schema['$id'] for schema in schemas}) == len(schemas),
                   'Candidate registry has unique schema identities')
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas)
        for schema in schemas:
            Draft202012Validator.check_schema(schema)
        by_path = {path: Draft202012Validator(schema, registry=registry) for path, schema in zip(paths, schemas)}
        self.validators = {kind: by_path['docs/language-design/agent-v0.11/' + kind + '.schema.json']
                           for kind in ('request', 'response')}
        self.check(self.json('schema-inventory.json') == [
            {'path': path, 'id': schema['$id'], 'bytes': len(raw), 'sha256': sha(raw)}
            for path, schema, raw in zip(paths, schemas, raws)],
            'Recorded schema inventory equals actual candidate-pinned schema bytes')
        self.report['schema_validation'] = {'jsonschema': version('jsonschema'),
                                            'referencing': version('referencing'),
                                            'registry': 'candidate Git files only',
                                            'schemas': len(schemas)}

    def exchanges(self):
        raw = self.read('protocol.jsonl')
        self.rows = [loads(line) for line in raw.splitlines()]
        self.check(bool(self.rows), 'Actual protocol contains exchanges', exchanges=len(self.rows))
        self.check({p.name for p in self.root.glob('exchange-*.json')} ==
                   {f'exchange-{i:03}.json' for i in range(1, len(self.rows)+1)}, 'Individual exchange files are complete and unique')
        self.by_op, self.by_id = defaultdict(list), defaultdict(list)
        for i, row in enumerate(self.rows, 1):
            self.check(set(row) == {'sequence', 'request', 'response'} and
                       row == self.json(f'exchange-{i:03}.json') and row['sequence'] == i,
                       'Raw JSONL matches exchange file ' + str(i))
            q, s = row['request'], row['response']
            self.validators['request'].validate(q)
            self.validators['response'].validate(s)
            self.check(True, 'Candidate schema validates both raw envelopes at exchange ' + str(i))
            self.check(q['schema_version'] == s['schema_version'] == PROTOCOL and
                       q['project_id'] == s['project_id'] == 'c078' and
                       q['request_id'] == s['request_id'] and q['operation'] == s['operation'],
                       'Request/response identity at exchange ' + str(i))
            self.by_op[q['operation']].append(row)
            self.by_id[q['request_id']].append(row)
        self.check(sorted(self.by_op) == OPERATIONS, 'All twelve operations occur in raw requests')
        self.check(list(self.by_id) == [f'c078-{i}' for i in range(1, len(self.by_id) + 1)],
                   'First-seen durable request identities are unique and contiguous')
        for op in OPERATIONS:
            self.check(any(row['response']['status'] == 'succeeded' for row in self.by_op[op]),
                       'Successful actual operation ' + op)
        self.report['operation_inventory'] = {op: {'exchanges': len(rows), 'statuses': dict(Counter(r['response']['status'] for r in rows)),
                                                 'request_ids': list(dict.fromkeys(r['request']['request_id'] for r in rows))}
                                               for op, rows in sorted(self.by_op.items())}
        self.check(self.summary['exchanges'] == len(self.rows) and self.summary['durable_requests'] == len(self.by_id) and
                   self.summary['schema_validated_exchanges'] == len(self.rows) and self.summary['operation_inventory'] == OPERATIONS,
                   'Summary counters reconcile to actual exchanges')
        self.report['schema_validation']['exchanges'] = len(self.rows)

    def one(self, op, predicate=lambda row: True):
        rows = [row for row in self.by_op[op] if predicate(row)]
        self.check(len(rows) == 1, 'Unique selected ' + op + ' exchange', sequences=[r['sequence'] for r in rows])
        return rows[0]

    def workflow(self):
        original, invalid, repaired = [self.programs[role]['revision'] for role in ('original', 'invalid', 'repaired')]
        spec = self.spec['assembly']
        self.create = self.one('create')
        q, response = self.create['request'], self.create['response']
        self.check(q['bundle'] == self.programs['original']['payload'] and q['expected_program_revision'] is None and
                   q['requested_level'] == response['achieved_level'] == 'constructed' and
                   response['accepted_program_revision'] == original, 'Create accepts the exact frozen pinned bundle')
        validated = self.one('validate', lambda row: row['response']['status'] == 'succeeded')
        self.check(validated['request']['program_revision'] == original and
                   validated['request']['requested_level'] == validated['response']['achieved_level'] == 'constructed' and
                   validated['response']['result']['stages']['constructed'] == 'valid' and
                   validated['response']['execution_budget']['effective'] == DEFAULTS,
                   'Ordinary composed validation actually constructs within unchanged defaults')
        discover = self.one('discover')['response']['result']
        self.check(discover['agent_contract'] == PROTOCOL and discover['language_version'] == '0.11' and
                   discover['profile'] == PROFILE and TARGET in discover['delivery_targets'] and
                   discover['execution_defaults'] == DEFAULTS and
                   sorted(discover['framed_polygon_loft_interface']['operations']) == OPERATIONS and
                   {'FramedPolygonSection', 'framed_polygon_section', 'loft_framed_rings', 'loft_rings'} <=
                   {item['name'] for item in discover['items']},
                   'Discovery exposes explicit new binding, inherited constructors and unchanged defaults')
        inspected = self.one('inspect', lambda row: row['request']['selector'] == {'kind': 'source'})
        units = {unit['source_id']: unit for unit in inspected['response']['result']['source_units']}
        wanted_units = self.programs['original']['manifest']['units']
        self.check(len(units) == len(inspected['response']['result']['source_units']) == len(wanted_units) and
                   set(units) == {unit['source_id'] for unit in wanted_units}, 'Source inspection returns exact source identities')
        texts = {'entry': q['bundle']['entry']['source'], spec['library']['source_id']: q['bundle']['modules'][0]['source']}
        for wanted in wanted_units:
            unit = units[wanted['source_id']]
            self.check(unit['filename'] == wanted['filename'] and unit['source_revision'] == wanted['source_revision'] and
                       unit['source'] == texts[wanted['source_id']], 'Inspection retains exact source ' + wanted['source_id'])
        inspection = self.one('inspect', lambda row: row['request']['selector'] == {'path': 'first'})
        surface = inspection['response']['result']['items'][0]['geometry']['surface']
        self.check(surface['schema_version'] == 'ontokin.framed-polygon-loft-summary/0.1' and
                   surface['profile'] == PROFILE and surface['family'] == 'framed_polygon_loft' and
                   surface['surface_rule'] == 'fixed-diagonal-triangles' and
                   surface['section_transform_rule'] == 'exact-rational-quaternion-single-round' and
                   surface['physical_participation'] == 'none' and
                   surface['motion_authority'] == 'carrier_evaluated_world_pose' and 'station_range_m' not in surface and
                   normalize_sections(surface['sections']) == normalize_sections(spec['first']['sections']) and
                   all(section['frame'] == 'carrier_self_frame' for section in surface['sections']),
                   'Inspection exposes original authored frames with no station or physical reinterpretation')
        for key in ('section_count', 'ring_count', 'hole_count', 'vertices_per_section', 'authored_vertex_count',
                    'cap_triangle_count', 'strip_triangle_count', 'triangle_count', 'vertex_count'):
            self.check(surface[key] == spec['first'][key], 'Inspection frozen count ' + key)
        self.check({region['key']: region['triangle_count'] for region in surface['regions']} ==
                   spec['first']['region_triangle_counts'], 'Inspection frozen used material counts')

        self.invalid_edit = self.one('edit', lambda row: row['response']['status'] in ('failed', 'rejected'))
        self.repair = self.one('edit', lambda row: row['response']['status'] == 'succeeded')
        for row, field, role in ((self.invalid_edit, 'invalid_edit', 'invalid'), (self.repair, 'repair', 'repaired')):
            q, response = row['request'], row['response']
            contract = spec[field]
            source = self.programs['original']['payload']['entry']['source'].encode('utf-8')
            old, new = contract['old'].encode('utf-8'), contract['new'].encode('utf-8')
            self.check(source.count(old) == 1, 'Frozen patch identifies exactly one byte occurrence ' + role)
            start = source.index(old)
            self.check(q['expected_program_revision'] == original and q['patches'] == [{
                'source_id': 'entry', 'source_revision': 'sha256:' + sha(source), 'element_id': ['sources', 'entry'],
                'start_byte': start, 'end_byte': start + len(old), 'expected_text': contract['old'], 'replacement': contract['new']}],
                'Exact original-unit UTF-8 patch authority ' + role)
            self.check(source[:start] + new + source[start + len(old):] ==
                       self.programs[role]['payload']['entry']['source'].encode('utf-8') and
                       response['program_revision'] == self.programs[role]['revision'],
                       'Actual patch selects exact frozen candidate ' + role)
        invalid_response = self.invalid_edit['response']
        self.check(self.invalid_edit['request']['requested_level'] == 'delivered' and
                   self.invalid_edit['request']['destination'] == TARGET and
                   invalid_response['accepted_program_revision'] == original and invalid_response['run_id'] is None and
                   invalid_response['result']['outcome'] == 'invalid' and
                   'artifact_id' not in invalid_response['result'] and
                   spec['invalid_edit']['diagnostic_code'] in [d['code'] for d in invalid_response['diagnostics']] and
                   not (invalid_response.get('execution_budget') or {}).get('budget_reason'),
                   'Delivered-level invalid frame edit reaches its frozen diagnostic without publishing state')
        self.check(self.repair['request']['requested_level'] == self.repair['response']['achieved_level'] == 'constructed' and
                   self.repair['response']['accepted_program_revision'] == repaired,
                   'Exact one-occurrence frame repair accepts the frozen revised bundle')
        for row in self.rows:
            wanted = None if row['sequence'] < self.create['sequence'] else original if row['sequence'] < self.repair['sequence'] else repaired
            self.check(row['response']['accepted_program_revision'] == wanted,
                       'Accepted revision at actual exchange ' + str(row['sequence']))
            result = row['response'].get('result')
            if type(result) is dict and 'source_manifest' in result:
                manifests = {program['revision']: program['manifest'] for program in self.programs.values()}
                self.check(result['source_manifest'] == manifests[row['response']['program_revision']],
                           'Actual source manifest at exchange ' + str(row['sequence']))

        sibling = [spec['module_id'], spec['scene_id'], 'sibling']
        first = sibling[:-1] + ['first']
        old = self.one('surface.mesh_page', lambda row: row['request']['element_id'] == sibling and row['request']['program_revision'] == original)
        new = self.one('surface.mesh_page', lambda row: row['request']['element_id'] == sibling and row['request']['program_revision'] == repaired)
        fields = ['positions_m', 'normals', 'triangles', 'region_keys', 'source_triangle_ordinals']
        old_page, new_page = old['response']['result'], new['response']['result']
        count = spec['sibling']['triangle_count']
        self.check(all(old_page[field] == new_page[field] for field in fields) and
                   old_page['geometry_sha256'] == new_page['geometry_sha256'],
                   'Complete sibling native geometry remains byte-for-byte equivalent through the repair')
        for row, page in ((old, old_page), (new, new_page)):
            self.check(page['returned_triangles'] == page['total_triangles'] == count and page['offset'] == 0 and
                       row['response']['next_cursor'] is None and page['source_triangle_ordinals'] == list(range(count)) and
                       len(page['triangles']) == len(page['region_keys']) == count and
                       len(page['positions_m']) == len(page['normals']) == 3 * count and
                       dict(Counter(page['region_keys'])) == spec['sibling']['region_triangle_counts'] and
                       page['coordinate_system'] == 'carrier_local_after_placement/0.1',
                       'Sibling page is the complete frozen nonempty native surface')
        first_page = self.one('surface.mesh_page', lambda row: row['request']['element_id'] == first and
                             row['request']['program_revision'] == original and 'cursor' not in row['request'])
        continued = self.one('surface.mesh_page', lambda row: row['request']['element_id'] == first and
                            row['request']['program_revision'] == original and 'cursor' in row['request'] and
                            'region' not in row['request'])
        filtered = self.one('surface.mesh_page', lambda row: 'region' in row['request'])
        stale = self.one('surface.mesh_page', lambda row: row['request']['program_revision'] == repaired and 'cursor' in row['request'])
        changed_first = self.one('surface.mesh_page', lambda row: row['request']['element_id'] == first and
                                row['request']['program_revision'] == repaired and 'cursor' not in row['request'])
        cursor = first_page['response']['next_cursor']
        self.check(cursor and first_page['request']['count'] == 3 and
                   first_page['response']['result']['source_triangle_ordinals'] == [0, 1, 2] and
                   continued['request']['cursor'] == cursor and
                   continued['response']['result']['source_triangle_ordinals'] == [3, 4, 5],
                   'Bounded source-derived mesh cursor continues the exact native triangle order')
        for row in (filtered, stale):
            self.check(row['request']['cursor'] == cursor and row['response']['status'] == 'rejected' and
                       row['response']['protocol_error']['code'] == 'OKL-E-REVISION',
                       'Mesh cursor rejects changed query or revision at exchange ' + str(row['sequence']))
        self.check(changed_first['response']['result']['element_id'] == first_page['response']['result']['element_id'] and
                   changed_first['response']['result']['geometry_sha256'] != first_page['response']['result']['geometry_sha256'],
                   'Repaired first occurrence preserves nominal identity while its geometry changes')
        self.mesh_pages = {'sibling_before': old_page, 'sibling_after': new_page,
                           'first_before': first_page['response']['result'], 'first_continued': continued['response']['result'],
                           'first_after': changed_first['response']['result']}

        self.evaluations = {}
        self.exports = {}
        for role, revision in (('original', original), ('repaired', repaired)):
            for operation, collection in (('evaluate', self.evaluations), ('export', self.exports)):
                selected = [rows[0] for rows in self.by_id.values() if rows[0]['request']['operation'] == operation and
                            rows[0]['request'].get('program_revision') == revision and rows[0]['response']['status'] == 'succeeded']
                self.check(len(selected) == 1, 'One successful durable ' + role + ' ' + operation)
                collection[role] = selected[0]
        self.evaluation, self.export = self.evaluations['repaired'], self.exports['repaired']
        evaluation_rows = self.by_id[self.evaluation['request']['request_id']]
        identical = [row for row in evaluation_rows if row['request'] == self.evaluation['request']]
        changed = [row for row in evaluation_rows if row['request'] != self.evaluation['request']]
        self.check(len(evaluation_rows) == 4 and len(identical) == 3 and
                   all(row['response'] == self.evaluation['response'] for row in identical) and
                   identical[-1]['sequence'] > self.export['sequence'] and len(changed) == 1 and
                   changed[0]['request'] == dict(self.evaluation['request'], until_seconds='0.5') and
                   changed[0]['response']['status'] == 'rejected' and
                   changed[0]['response']['protocol_error']['code'] == 'OKL-E-REQUEST-ID',
                   'Immediate and reopened identical evaluation retries retain one receipt; changed payload is refused')
        self.check(self.evaluations['original']['request']['until_seconds'] == '0.5' and
                   self.evaluation['request']['until_seconds'] == '1' and
                   all(row['request']['run_id'] is None and row['response']['achieved_level'] == 'evaluated'
                       for row in self.evaluations.values()), 'Original and repaired evaluation requests have frozen horizons')
        options = {'fps': self.spec['options']['fps'], 'end': str(self.spec['options']['end_time_seconds']), 'helpers': False}
        for role, row in self.exports.items():
            self.check(row['request']['destination'] == TARGET and row['request']['options'] == options and
                       row['response']['achieved_level'] == 'delivered', 'Explicit complete recorded export ' + role)
        export_retries = self.by_id[self.export['request']['request_id']]
        self.check(len(export_retries) == 2 and all(row['request'] == self.export['request'] and
                   row['response'] == self.export['response'] for row in export_retries),
                   'Historical export retry returns its original receipt under the lower current policy')
        duplicate_ids = {request_id for request_id, rows in self.by_id.items() if len(rows) > 1}
        self.check(duplicate_ids == {self.evaluation['request']['request_id'], self.export['request']['request_id']},
                   'No unaccounted request-identity reuse occurs')
        self.denied = [row for row in self.rows if (row['response'].get('execution_budget') or {}).get('budget_reason') == 'host_ceiling_exceeded']
        self.check(len(self.denied) == 2 and {row['request']['operation'] for row in self.denied} == {'artifact', 'evaluate'},
                   'Current lower host policy is exercised on both retained artifact and run requests')
        for row in self.denied:
            response, budget = row['response'], row['response']['execution_budget']
            self.check(response['status'] in ('failed', 'rejected') and budget['stage'] == 'header_admission' and
                       budget['host_ceilings'] == REDUCED and budget['defaults'] == DEFAULTS and
                       budget['source_request'] == DEFAULTS and budget['effective'] is None and
                       0 < budget['consumed_operations'] <= REDUCED['max_operations'] and
                       response['result']['outcome'] == 'resource_limit' and
                       response['run_id'] == row['request'].get('run_id') and
                       'data_base64' not in response['result'] and
                       any(d['code'] == 'OKL-E-RESOURCE' and d['details'].get('requested') == 100000 and
                           d['details'].get('ceiling') == 50000 for d in response['diagnostics']),
                       'Fresh current-policy refusal at exchange ' + str(row['sequence']))
            if row['request']['operation'] == 'artifact':
                self.check(row['request']['artifact_id'] == self.export['response']['result']['artifact_id'],
                           'Lower-policy artifact refusal targets the retained repaired bytes')
            else:
                self.check(row['request']['run_id'] == self.evaluation['response']['run_id'] and
                           row['request']['program_revision'] == repaired and
                           response['result']['run_state'] == self.evaluation['response']['result']['run_state'],
                           'Lower-policy evaluation preserves the exact already-retained repaired run')
        reduced = self.one('artifact', lambda row: 'budgets' in row['request'])
        self.reduced = reduced
        self.check(reduced['response']['status'] == 'succeeded' and reduced['request']['budgets'] == REDUCED and
                   reduced['request']['max_bytes'] == 64 and
                   reduced['response']['execution_budget']['host_ceilings'] == REDUCED and
                   reduced['response']['execution_budget']['caller_caps'] == REDUCED and
                   reduced['response']['execution_budget']['effective'] == REDUCED,
                   'Explicit caller reduction authorizes retained bytes within the current host ceiling')
        self.check(export_retries[-1]['sequence'] > max(row['sequence'] for row in self.denied) and
                   reduced['sequence'] > export_retries[-1]['sequence'], 'Historical retry and caller reduction follow the actual policy refusals')
        self.reset = self.one('reset')
        self.pending = self.one('validate', lambda row: row['response']['status'] == 'queued')
        cancel, status = self.one('cancel'), self.one('status')
        target = self.pending['request']['request_id']
        self.cancel_target = status['response']['result']['target']
        self.validators['response'].validate(self.cancel_target)
        self.check(cancel['request']['target_request_id'] == status['request']['target_request_id'] == target and
                   cancel['response']['result']['target_status'] == status['response']['result']['target_status'] == 'cancelled' and
                   cancel['response']['result']['target'] == self.cancel_target and self.cancel_target['request_id'] == target and
                   self.cancel_target['progress']['phase'] == 'cancelled_before_work' and
                   self.cancel_target['progress']['cancellation_requested'] is True and
                   self.cancel_target['result'] is None and self.cancel_target['execution_budget'] is None and
                   self.cancel_target['run_id'] is None, 'Queued cancellation retains a terminal receipt without starting work')

    def durable(self):
        name = 'framed-loft-program-agent.sqlite3'
        self.read(name)
        self.check(not any((self.root / (name + suffix)).exists() for suffix in ('-wal', '-shm', '-journal')),
                   'SQLite evidence is a standalone closed snapshot')
        connection = sqlite3.connect((self.root / name).as_uri() + '?mode=ro&immutable=1', uri=True)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute('PRAGMA query_only=ON')
            self.check(connection.execute('PRAGMA integrity_check').fetchall()[0][0] == 'ok', 'Read-only SQLite integrity check')
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            expected_tables = {'metadata', 'projects', 'sources', 'sessions', 'requests', 'runs', 'artifacts', 'acceptance_identities', 'sqlite_sequence'}
            self.check(names == expected_tables, 'Documented durable table inventory')
            metadata = dict(connection.execute('SELECT name,value FROM metadata'))
            self.check(metadata['schema_version'] == 'ontokin.framed-loft-program-agent-store/0.1', 'Explicit isolated store binding')
            tables = {name: [dict(row) for row in connection.execute('SELECT * FROM ' + name)]
                      for name in expected_tables - {'metadata', 'sqlite_sequence'}}
        finally:
            connection.close()
        self.report['sqlite_counts'] = {name: len(rows) for name, rows in sorted(tables.items())}
        repaired = self.programs['repaired']['revision']
        self.check(tables['projects'] == [{'id': 'c078', 'accepted_revision': repaired}], 'Durable accepted pointer remains repaired')
        self.check(len(tables['sessions']) == 2 and len({row['id'] for row in tables['sessions']}) == 2 and
                   all(row['closed'] == 1 for row in tables['sessions']),
                   'Both original and reopened durable sessions are closed')
        requests = {row['id']: row for row in tables['requests']}
        self.check(len(tables['requests']) == len(requests) == len(self.by_id) and set(requests) == set(self.by_id),
                   'Every unique raw request has exactly one durable row')
        for sequence, (request_id, exchanges) in enumerate(self.by_id.items(), 1):
            stored, first = requests[request_id], exchanges[0]
            q = first['request']
            expected_response = self.cancel_target if request_id == self.pending['request']['request_id'] else first['response']
            stored_response = loads(stored['response'])
            self.validators['request'].validate(loads(stored['payload']))
            self.validators['response'].validate(stored_response)
            self.check(stored['project_id'] == PROJECT and stored['sequence'] == sequence and
                       stored['operation'] == q['operation'] and stored['created'] <= stored['updated'] and
                       stored['digest'] == sha(canonical(q)) and stored['payload'].encode() == canonical(q) and
                       stored_response == expected_response and stored['state'] == expected_response['status'] and stored['owner'] is None and
                       stored['cancel_requested'] == int(request_id == self.pending['request']['request_id']),
                       'Durable payload and terminal response ' + request_id)
            engine = loads(stored['engine'])
            self.check(engine['source_code_sha256'] == self.implementation_sha, 'Candidate implementation in durable row ' + request_id)
            budget = stored_response.get('execution_budget')
            if budget:
                self.check(budget['implementation'] == engine and budget['request_id'] == request_id and budget['defaults'] == DEFAULTS,
                           'Retained budget identity ' + request_id)
            self.report['observed_requests'].append({
                'request_id': request_id, 'operation': q['operation'], 'exchange_sequences': [r['sequence'] for r in exchanges],
                'durable_sequence': stored['sequence'], 'durable_status': stored['state'],
                'payload_sha256': stored['digest'], 'response_sha256': sha(stored['response'].encode()),
                'program_revision': stored_response.get('program_revision'), 'accepted_program_revision': stored_response.get('accepted_program_revision'),
                'run_id': stored_response.get('run_id'), 'achieved_level': stored_response.get('achieved_level'),
                'diagnostic_codes': [d['code'] for d in stored_response.get('diagnostics', [])],
                'protocol_error': stored_response.get('protocol_error'),
                'consumed_operations': budget.get('consumed_operations') if budget else None,
                'budget_reason': budget.get('budget_reason') if budget else None})
        sources = {row['revision']: row for row in tables['sources']}
        self.check(len(sources) == len(tables['sources']) == 3 and set(sources) == {p['revision'] for p in self.programs.values()},
                   'Store retains exactly original, invalid candidate and repaired snapshots')
        for role, wanted in self.programs.items():
            row = sources[wanted['revision']]
            payload = loads(row['raw'])
            self.check(row['project_id'] == 'c078' and row['filename'] == '<program-bundle>' and payload == wanted['payload'] and
                       bundle_identity(payload) == (wanted['revision'], wanted['manifest']) and row['accepted_once'] == int(role != 'invalid'),
                       'Exact durable source and acceptance flag for ' + role,
                       revision=wanted['revision'], accepted_once=row['accepted_once'], stored_bytes_sha256=sha(row['raw']))
        identities = tables['acceptance_identities']
        self.check({r['revision'] for r in identities} == {self.programs[k]['revision'] for k in ('original', 'repaired')} and len(identities) == 2,
                   'Rejected source has no accepted identity publication')
        expected_ids = [{'element_id': [self.spec['assembly']['module_id'], self.spec['assembly']['scene_id'], name],
                         'definition_id': ['package', self.spec['assembly']['library']['package'], 'framed-loft-parts', 'definitions', 'shape']}
                        for name in ('first', 'sibling')]
        for row in identities:
            self.check(row['project_id'] == 'c078' and loads(row['identities']) == expected_ids and
                       loads(row['implementation'])['source_code_sha256'] == self.implementation_sha, 'Complete source-derived occurrence identities retained')
        runs = {row['id']: row for row in tables['runs']}
        selected = [self.evaluations['original'], self.exports['original'], self.evaluation, self.export, self.reset]
        self.check(len(runs) == len(tables['runs']) == 5 and
                   set(runs) == {row['response']['run_id'] for row in selected},
                   'Only original and repaired evaluation/export plus reset create five owned runs')
        self.report['runs'] = []
        for row in selected:
            response, revision = row['response'], row['request']['program_revision']
            stored = runs[response['run_id']]
            descriptor = loads(stored['descriptor'])
            self.check(stored['project_id'] == PROJECT and stored['source_revision'] == revision and stored['version'] == 1 and
                       descriptor == response['result']['run_state'] and descriptor['program_revision'] == revision and
                       descriptor['run_id'] == response['run_id'] and descriptor['candidate_only'] is False and
                       descriptor['failure'] is None and descriptor['implementation']['source_code_sha256'] == self.implementation_sha,
                       'Exact producer-owned durable run descriptor ' + response['run_id'])
            time = Fraction(0 if row['request']['operation'] == 'reset' else row['request'].get('until_seconds', '1'))
            self.check(Fraction(descriptor['valid_until_seconds']) == time, 'Run reaches requested frozen time ' + response['run_id'])
            objects = descriptor['last_valid_state']['objects']
            self.check(set(objects) == {'first', 'sibling'}, 'Run retains exact assembly carriers')
            first_geometry = self.spec['assembly']['first' if revision == self.programs['original']['revision'] else 'repaired_first']
            for name, geometry, origin, velocity in (
                    ('first', first_geometry, self.spec['assembly']['first_placement_m'], self.spec['motion_m_per_second']),
                    ('sibling', self.spec['assembly']['sibling'], self.spec['assembly']['sibling_placement_m'],
                     self.spec['assembly']['sibling_motion_m_per_second'])):
                obj = objects[name]
                self.equal_vector(obj['position_m'], [x + float(time)*v for x, v in zip(origin, velocity)], 'Run position ' + name)
                active_velocity = velocity if row['request']['operation'] == 'evaluate' and 0 < time < self.spec['duration_seconds'] else [0, 0, 0]
                self.equal_vector(obj['velocity_m_per_s'], active_velocity, 'Current run velocity after action completion or reset ' + name)
                self.equal_vector(obj['orientation_wxyz'], [1, 0, 0, 0], 'Run orientation ' + name)
                self.check(normalize_sections(obj['geometry']['sections']) == normalize_sections(geometry['sections']) and
                           all(section['frame']['frame'] == name + '.frame' for section in obj['geometry']['sections']) and
                           obj['element_id'] == [self.spec['assembly']['module_id'], self.spec['assembly']['scene_id'], name],
                           'Run retains exact source frames, owner and nominal identity ' + name)
            self.report['runs'].append({'run_id': stored['id'], 'producer_request_id': row['request']['request_id'],
                                        'operation': row['request']['operation'], 'program_revision': revision,
                                        'valid_until_seconds': descriptor['valid_until_seconds'],
                                        'descriptor_sha256': sha(stored['descriptor'].encode())})
        self.check(len(tables['artifacts']) == 2, 'Exactly two retained Agent artifacts')
        self.stored_artifacts = {row['id']: row for row in tables['artifacts']}
        self.check(len(self.stored_artifacts) == 2 and set(self.stored_artifacts) ==
                   {row['response']['result']['artifact_id'] for row in self.exports.values()},
                   'Each stored artifact has exactly one successful source-bound export producer')
        for before_name, after_name, roles in (
                ('before-invalid-edit.json', 'after-invalid-edit.json', ('original',)),
                ('before-reopen.json', 'after-reopen.json', ('original', 'repaired'))):
            before, after = self.json(before_name), self.json(after_name)
            selected_runs = {self.evaluations[role]['response']['run_id'] for role in roles} | {
                self.exports[role]['response']['run_id'] for role in roles}
            selected_artifacts = {self.exports[role]['response']['result']['artifact_id'] for role in roles}
            expected = {
                'accepted_program_revision': self.programs[roles[-1]]['revision'],
                'runs': [{'id': key, 'program_revision': runs[key]['source_revision'],
                          'descriptor': loads(runs[key]['descriptor']), 'version': runs[key]['version']}
                         for key in sorted(selected_runs)],
                'artifacts': [{'id': key, 'bytes': len(self.stored_artifacts[key]['data']),
                               'sha256': sha(self.stored_artifacts[key]['data']),
                               'stored_sha256': self.stored_artifacts[key]['sha256']}
                              for key in sorted(selected_artifacts)]}
            self.check(before == after == expected,
                       'Actual before/after state matches unchanged final SQLite ownership: ' + before_name,
                       state_sha256=sha(canonical(expected)))
        inventory = self.json('store-inventory.json')
        fields = ('id', 'operation', 'state', 'digest', 'payload', 'response', 'cancel_requested')
        projected = []
        for row in sorted(tables['requests'], key=lambda value: value['sequence']):
            value = {key: row[key] for key in fields}
            value.update(payload=loads(value['payload']), response=loads(value['response']))
            projected.append(value)
        artifacts = [{'id': row['id'], 'program_revision': row['source_revision'], 'bytes': len(row['data']),
                      'stored_sha256': row['sha256'], 'sha256': sha(row['data'])}
                     for row in sorted(tables['artifacts'], key=lambda value: value['id'])]
        self.check(inventory == {'schema_version': 'ontokin.framed-loft-program-agent-store/0.1',
                                 'integrity_check': ['ok'], 'requests': projected, 'artifacts': artifacts},
                   'Recorded store inventory independently reconciles to the immutable SQLite snapshot')

    def artifact_chunks(self):
        self.report['artifact_reconstructions'] = []
        accounted = {row['sequence'] for row in self.denied if row['request']['operation'] == 'artifact'}
        accounted.add(self.reduced['sequence'])
        for role, exported in self.exports.items():
            result = exported['response']['result']
            artifact_id, revision = result['artifact_id'], self.programs[role]['revision']
            chunks = [row for row in self.by_op['artifact'] if row['response']['status'] == 'succeeded' and
                      row['request']['artifact_id'] == artifact_id and 'budgets' not in row['request']]
            offset, parts, details = 0, [], []
            for row in chunks:
                raw = returned_chunk(row, artifact_id=artifact_id, revision=revision,
                    producer=exported['request']['request_id'], implementation=self.implementation_sha,
                    digest=result['sha256'], total=result['total_bytes'], offset=offset, maximum=1024)
                self.check(row['sequence'] > exported['sequence'], 'Chunk follows its actual export producer ' + str(row['sequence']))
                details.append({'exchange_sequence': row['sequence'], 'request_id': row['request']['request_id'],
                                'offset': offset, 'bytes': len(raw),
                                'next_offset': row['response']['result']['next_offset'], 'sha256': sha(raw)})
                offset += len(raw)
                parts.append(raw)
                accounted.add(row['sequence'])
            reconstructed = b''.join(parts)
            stored = self.stored_artifacts[artifact_id]
            digest = sha(reconstructed)
            report = loads(stored['report'])
            self.check(len(chunks) == (result['total_bytes'] + 1023) // 1024 and
                       offset == len(reconstructed) == result['total_bytes'] and
                       result['sha256'] == stored['sha256'] == 'sha256:' + digest and
                       artifact_id == stored['id'] == 'artifact:' + digest and
                       stored['project_id'] == PROJECT and stored['source_revision'] == revision and
                       bytes(stored['data']) == reconstructed == self.read('agent-' + role + '.glb'),
                       'Complete returned stream, retained SQLite BLOB and saved GLB are byte-identical: ' + role,
                       chunks=len(chunks), bytes=len(reconstructed), artifact_id=artifact_id, sha256=digest)
            self.check(report == result['report'] and report['artifact']['byte_length'] == len(reconstructed) and
                       report['artifact']['sha256'] == 'sha256:' + digest and report['program_revision'] == revision and
                       report['program']['manifest'] == self.programs[role]['manifest'] and
                       report['producer_request_id'] == exported['request']['request_id'] and report['target_contract'] == TARGET,
                       'Durable artifact report and exact export producer agree: ' + role)
            if role == 'repaired':
                reduced = returned_chunk(self.reduced, artifact_id=artifact_id, revision=revision,
                    producer=exported['request']['request_id'], implementation=self.implementation_sha,
                    digest=result['sha256'], total=result['total_bytes'], offset=0, maximum=64)
                self.check(reduced == reconstructed[:64], 'Caller-reduced read returns the same actual retained bytes')
            self.report['artifact_reconstructions'].append({
                'name': 'agent-' + role, 'artifact_id': artifact_id, 'program_revision': revision,
                'bytes': len(reconstructed), 'sha256': digest, 'chunks': details,
                'producer_request_id': exported['request']['request_id'],
                'durable_report_sha256': sha(stored['report'].encode())})
        self.check(accounted == {row['sequence'] for row in self.by_op['artifact']},
                   'All actual artifact requests belong to the two complete streams or explicit policy probes')
        self.check(self.summary['agent_export_operations'] == self.export['response']['execution_budget']['consumed_operations'],
                   'Reported Agent operation count equals the durable repaired export receipt')
        wanted = [{key: row[key] for key in ('artifact_id', 'program_revision', 'bytes', 'sha256')} |
                  {'chunks': len(row['chunks']), 'sqlite_bytes_equal': True}
                  for row in self.report['artifact_reconstructions']]
        self.check(self.summary['artifact_retrievals'] == wanted,
                   'Summary retrieval totals reconcile to independently reconstructed raw streams')

    def glb_motion(self, name, raw, expected):
        self.check(len(raw) >= 28 and struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'GLB header ' + name)
        size, kind = struct.unpack_from('<II', raw, 12)
        self.check(kind == 0x4e4f534a and size % 4 == 0 and 28 + size <= len(raw), 'GLB JSON framing ' + name)
        document = loads(raw[20:20+size])
        start = 20 + size
        size, kind = struct.unpack_from('<II', raw, start)
        self.check(kind == 0x004e4942 and size % 4 == 0 and start + 8 + size == len(raw), 'GLB binary framing ' + name)
        binary, buffers = raw[start+8:], document['buffers']
        self.check(len(buffers) == 1 and 'uri' not in buffers[0] and
                   type(buffers[0]['byteLength']) is int and 0 <= len(binary) - buffers[0]['byteLength'] <= 3,
                   'GLB uses a bounded actual inline buffer ' + name)
        metadata = document['extras']['ontokin']
        legacy = expected.get('legacy', False)
        target, profile, version = ('ontokin.glb/0.10', 'polygon-loft-0.1', '0.10') if legacy else (TARGET, PROFILE, '0.11')
        self.check(metadata['target_contract'] == target and metadata['schema_version'] == version and metadata['profile'] == profile and
                   metadata['program']['revision'] == expected['program_revision'] and
                   metadata['program']['manifest'] == expected['manifest'], 'GLB actual source and contract binding ' + name)
        nodes = document['nodes']
        actual_paths = {node['extras']['ontokin']['path']: i for i, node in enumerate(nodes)}
        self.check(len(actual_paths) == len(nodes) and set(actual_paths) == set(expected['nodes']) and
                   all(node['extras']['ontokin']['kind'] == 'object' for node in nodes), 'Exact actual GLB carrier inventory ' + name)
        roots = document['scenes'][document.get('scene', 0)]['nodes']
        self.check(len(document['scenes']) == 1 and sorted(roots) == list(range(len(nodes))),
                   'Every GLB carrier is an active independent scene root ' + name)

        def accessor(index, wanted_type, component_types=(5126,)):
            self.check(type(index) is int and 0 <= index < len(document['accessors']), 'Bounded accessor identity ' + name)
            item = document['accessors'][index]
            view_index = item['bufferView']
            self.check(type(view_index) is int and 0 <= view_index < len(document['bufferViews']), 'Bounded buffer view identity ' + name)
            view = document['bufferViews'][view_index]
            self.check(item['componentType'] in component_types and item['type'] == wanted_type,
                       'Actual accessor component and vector types ' + name)
            format_code, width = {5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}[item['componentType']]
            components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[wanted_type]
            count, offset = item['count'], item.get('byteOffset', 0)
            stride, base = view.get('byteStride', width*components), view.get('byteOffset', 0)
            self.check('sparse' not in item and not item.get('normalized') and view.get('buffer', 0) == 0 and
                       all(type(value) is int and value >= 0 for value in (count, offset, stride, base, view['byteLength'])) and
                       count > 0 and stride >= width*components and stride % width == 0 and (base+offset) % width == 0 and
                       offset + (count-1)*stride + width*components <= view['byteLength'] and
                       base + view['byteLength'] <= buffers[0]['byteLength'], 'Actual accessor stays within its own supplied view ' + name)
            rows = [list(struct.unpack_from('<' + format_code*components, binary, base+offset+i*stride)) for i in range(count)]
            self.check(all(math.isfinite(value) for row in rows for value in row), 'Finite actual accessor values ' + name)
            return [row[0] for row in rows] if wanted_type == 'SCALAR' else rows

        contents, measures, ordinal_maps, used_meshes = {}, {}, {}, set()
        for path, index in actual_paths.items():
            node, geometry = nodes[index], expected['nodes'][path]['geometry']
            self.check(not node.get('children') and 'matrix' not in node and node.get('scale', [1, 1, 1]) == [1, 1, 1],
                       'Carrier retains one independent rigid pose ' + name + ':' + path)
            if geometry is None:
                self.check('mesh' not in node, 'Geometry-free generated parent has no hidden mesh ' + name)
                continue
            mesh_index = node['mesh']
            self.check(type(mesh_index) is int and 0 <= mesh_index < len(document['meshes']) and mesh_index not in used_meshes,
                       'One source-owned logical mesh per visual carrier ' + name + ':' + path)
            used_meshes.add(mesh_index)
            primitives = document['meshes'][mesh_index]['primitives']
            witnesses = witness_positions(geometry)
            witness_set = set(witnesses)
            self.check(len(witnesses) == len(witness_set) == geometry['authored_vertex_count'],
                       'Frozen actual binary32 source identities remain distinct ' + name + ':' + path)
            regions, triangles, ordinals, used, visible = [], [], {}, Counter(), set()
            areas, volume6 = [], Fraction(0)
            attribute_pair = None
            for primitive in primitives:
                self.check(primitive.get('mode', 4) == 4, 'Actual surface primitive uses triangles ' + name)
                pair = (primitive['attributes']['POSITION'], primitive['attributes']['NORMAL'])
                if attribute_pair is None:
                    attribute_pair = pair
                self.check(pair == attribute_pair, 'All material regions share their complete logical corner buffers ' + name)
                positions, normals = accessor(pair[0], 'VEC3'), accessor(pair[1], 'VEC3')
                indices = accessor(primitive['indices'], 'SCALAR', (5123, 5125))
                self.check(len(positions) == len(normals) == geometry['vertex_count'] and len(indices) % 3 == 0 and
                           all(type(value) is int and 0 <= value < len(positions) for value in indices),
                           'Actual flat-corner and index bounds ' + name + ':' + path)
                used.update(indices)
                material_index = primitive['material']
                self.check(type(material_index) is int and 0 <= material_index < len(document['materials']),
                           'Bounded source material identity ' + name)
                material = document['materials'][material_index]
                region = primitive['extras']['ontokin']['region_key']
                self.check(region == material['extras']['ontokin']['source_region_key'] and region not in regions and
                           material['extras']['ontokin']['occurrence_path'] == path and
                           material['extras']['ontokin']['program_revision'] == expected['program_revision'] and
                           not material.get('doubleSided', False) and
                           material['pbrMetallicRoughness'] == {'baseColorFactor': geometry['palette'][region],
                               'metallicFactor': geometry['metallic'], 'roughnessFactor': geometry['roughness']},
                           'Actual primitive material and source provenance ' + name + ':' + path + ':' + region)
                self.check(len(indices)//3 == geometry['region_triangle_counts'][region], 'Actual regional triangle count ' + name + ':' + region)
                regions.append(region)
                for start in range(0, len(indices), 3):
                    selected = indices[start:start+3]
                    points = [positions[i] for i in selected]
                    normal = [normals[i] for i in selected]
                    self.check(all(tuple(point) in witness_set for point in points) and
                               len({tuple(point) for point in points}) == 3,
                               'Actual triangle references three frozen source-quantized identities ' + name)
                    visible.update(tuple(point) for point in points)
                    exact = [[Fraction(value) for value in point] for point in points]
                    u = [a-b for a, b in zip(exact[1], exact[0])]
                    v = [a-b for a, b in zip(exact[2], exact[0])]
                    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                    length = math.hypot(*(float(value) for value in cross))
                    self.check(length > 0 and normal[0] == normal[1] == normal[2] and
                               abs(math.hypot(*normal[0])-1) <= self.spec['tolerances']['normal'] and
                               sum(Fraction(a)*b for a, b in zip(normal[0], cross)) > 0,
                               'Actual triangle has nonzero area and one outward finite unit normal ' + name)
                    areas.append(length/2)
                    volume6 += sum(a*b for a, b in zip(exact[0], cross))
                    triangle = (region, points, normal, material['pbrMetallicRoughness'])
                    ordinal = selected[0] // 3
                    self.check(selected == [3*ordinal, 3*ordinal+1, 3*ordinal+2] and ordinal not in ordinals,
                               'Flat corner indices retain one source triangle ordinal ' + name)
                    triangles.append(triangle)
                    ordinals[ordinal] = triangle
            self.check(regions == sorted(geometry['region_triangle_counts']) and
                       used == Counter({i: 1 for i in range(geometry['vertex_count'])}) and
                       len(triangles) == geometry['triangle_count'] and visible == witness_set,
                       'Actual regions and every flat corner/source identity are used exactly as required ' + name + ':' + path)
            area, volume = math.fsum(areas), float(volume6/6)
            self.check(volume6 > 0 and abs(area-geometry['surface_area_m2']) <= self.spec['tolerances']['area_m2'] and
                       abs(volume-geometry['volume_m3']) <= self.spec['tolerances']['volume_m3'],
                       'Actual supplied triangles retain frozen area and positive signed volume ' + name + ':' + path)
            contents[path], measures[path] = triangles, {'surface_area_m2': area, 'signed_volume_m3': volume}
            ordinal_maps[path] = ordinals
        self.check(used_meshes == set(range(len(document.get('meshes', [])))), 'No unused hidden logical mesh is present ' + name)
        self.decoded_contents[name] = contents
        self.decoded_measures[name] = measures
        self.decoded_ordinals[name] = ordinal_maps
        self.check(len(document['animations']) == 1, 'Exactly one recorded clip ' + name)
        animation, channels = document['animations'][0], {}
        times = self.spec['sample_times_seconds']
        for channel in animation['channels']:
            node, prop = channel['target']['node'], channel['target']['path']
            self.check(type(node) is int and 0 <= node < len(nodes) and (node, prop) not in channels and
                       prop in ('translation', 'rotation'), 'Unique bounded rigid animation target ' + name)
            sampler_index = channel['sampler']
            self.check(type(sampler_index) is int and 0 <= sampler_index < len(animation['samplers']),
                       'Bounded actual animation sampler identity ' + name)
            sampler = animation['samplers'][sampler_index]
            self.check(sampler.get('interpolation', 'LINEAR') == 'LINEAR' and accessor(sampler['input'], 'SCALAR') == times,
                       'Actual recorded key times and interpolation ' + name)
            values = accessor(sampler['output'], 'VEC3' if prop == 'translation' else 'VEC4')
            self.check(len(values) == len(times), 'One actual value per recorded key ' + name)
            channels[node, prop] = values
        self.check(set(channels) == {(i, prop) for i in range(len(nodes)) for prop in ('translation', 'rotation')},
                   'Complete supplied translation and rotation channels ' + name)
        observations = []
        for path, wanted in expected['nodes'].items():
            index = actual_paths[path]
            for j, time in enumerate(times):
                translation, rotation = channels[index, 'translation'][j], channels[index, 'rotation'][j]
                self.equal_vector(translation, [origin+time*speed for origin, speed in zip(wanted['origin'], wanted['velocity'])],
                                  'Actual decoded position ' + name + ':' + path, self.spec['tolerances']['position_m'])
                self.check(rotation_error_identity(rotation) <= self.spec['tolerances']['rotation_rad'],
                           'Actual decoded quaternion geodesic error ' + name + ':' + path)
                observations.append({'path': path, 'time_seconds': time, 'translation': translation, 'rotation': rotation})
            self.equal_vector(nodes[index].get('translation', [0, 0, 0]), channels[index, 'translation'][0],
                              'Initial node translation equals first recorded state ' + name + ':' + path)
            self.equal_vector(nodes[index].get('rotation', [0, 0, 0, 1]), channels[index, 'rotation'][0],
                              'Initial node rotation equals first recorded state ' + name + ':' + path)
        return observations

    def source_receipts(self):
        self.source_reports = {}
        records = self.summary['cases']
        self.check([row['id'] for row in records] == [case['id'] for case in self.spec['cases']],
                   'Summary case inventory follows every independently frozen outcome')
        self.report['source_cases'] = []
        for case, record in zip(self.spec['cases'], records):
            payload = self.payload(case['source'])
            revision, manifest = bundle_identity(payload)
            report = self.json(case['id'] + '.receipt.json')
            self.source_reports[case['id']] = report
            budget = report['execution_budget']
            request = case.get('execution_request', DEFAULTS)
            diagnostics = report.get('diagnostics', [])
            codes = [item['code'] for item in diagnostics]
            legacy = case['id'] == 'earlier-version-rejection'
            target, profile = ('ontokin.glb/0.10', 'polygon-loft-0.1') if legacy else (TARGET, PROFILE)
            self.check(report['schema_version'] == 'ontokin.source-execution/0.1' and
                       report['program_revision'] == revision and report['source_revision'] ==
                       'sha256:' + sha(payload['entry']['source'].encode('utf-8')) and
                       report['requested_level'] == 'delivered' and report['target_contract'] == target and
                       report['profile'] == profile and
                       report['implementation_identity']['source_code_sha256'] == self.implementation_sha,
                       'Raw source receipt binds exact frozen source and candidate implementation ' + case['id'])
            self.check(budget['defaults'] == DEFAULTS and budget['source_request'] == budget['effective'] == request and
                       budget['host_ceilings'] == MAXIMUM and budget['caller_caps'] == {} and
                       type(budget['consumed_operations']) is int and 0 < budget['consumed_operations'] <= request['max_operations'] and
                       type(budget['elapsed_ms']) in (int, float) and 0 <= budget['elapsed_ms'] <= request['max_elapsed_ms'] and
                       budget['budget_reason'] is None and report['outcome'] != 'resource_limit' and
                       (report.get('error') or {}).get('code') != 'OKL-E-RESOURCE' and
                       all(item['code'] != 'OKL-E-RESOURCE' and item.get('category') != 'resource_limit' for item in diagnostics),
                       'Actual source work uses only its original requested operations and time ' + case['id'])
            valid = case['expected_outcome'] == 'valid'
            exists = (self.root / (case['id'] + '.glb')).is_file()
            if valid:
                raw = self.read(case['id'] + '.glb')
                self.check(exists and report['outcome'] == 'valid' and report['achieved_level'] == 'delivered' and
                           report['program']['manifest'] == manifest and report['artifact']['byte_length'] == len(raw) and
                           report['artifact']['sha256'] == 'sha256:' + sha(raw),
                           'Delivered source receipt binds the actual artifact bytes ' + case['id'])
            else:
                self.check(not exists and 'artifact' not in report and bool(diagnostics) and
                           report['achieved_level'] != 'delivered' and report['outcome'] != 'valid',
                           'Invalid frozen source has an actual diagnostic and no delivered file ' + case['id'])
                if case.get('diagnostic_code'):
                    self.check(case['diagnostic_code'] in codes, 'Exact frozen source diagnostic ' + case['id'])
                if case['expected_outcome'] == 'source_valid_delivery_rejected':
                    precision = any(item.get('details', {}).get('export_code') == 'OKE-E-GEOMETRY-PRECISION' or
                        (item.get('details', {}).get('export_code') == 'OKE-E-GLB-STRUCTURE' and
                         any(word in item.get('message', '').lower() for word in ('triangle', 'normal', 'winding')))
                        for item in diagnostics)
                    self.check(report['achieved_level'] == 'evaluated' and precision,
                               'Source-valid delivered bytes fail geometry precision without resource substitution ' + case['id'])
            self.check(record == {'id': case['id'], 'source': case['source'], 'program_revision': revision,
                                  'expected': case['expected_outcome'], 'actual': 'delivered' if valid else 'rejected',
                                  'achieved_level': report.get('achieved_level'), 'operations': budget['consumed_operations'],
                                  'elapsed_ms': budget['elapsed_ms'], 'diagnostic_codes': codes, 'status': 'passed'},
                       'Case summary reconciles to raw source receipt and supplied file ' + case['id'])
            self.report['source_cases'].append({'id': case['id'], 'program_revision': revision,
                'expected_outcome': case['expected_outcome'], 'diagnostic_codes': codes,
                'source_request': request, 'consumed_operations': budget['consumed_operations'],
                'elapsed_ms': budget['elapsed_ms'], 'receipt_sha256': sha(canonical(report))})

    def artifact_reports(self):
        controls = {}
        speed, assembly = self.spec['motion_m_per_second'], self.spec['assembly']
        for case in self.spec['cases']:
            if case['expected_outcome'] == 'valid':
                controls[case['id']] = (self.payload(case['source']),
                    {'shape': {'geometry': case['geometry'], 'origin': [0, 0, 0], 'velocity': speed}}, False)
        generated = self.spec['generated']
        origin, path = generated['root_placement_m'], generated['object_path']
        nodes = {path: {'geometry': None, 'origin': origin, 'velocity': speed}}
        for key, part in generated['parts'].items():
            part_path = path + '.' + generated['parts_member'] + '[' + json.dumps(key) + ']'
            nodes[part_path] = {'geometry': part['geometry'],
                               'origin': [origin[0], origin[1]+part['mount_y_m'], origin[2]], 'velocity': speed}
        controls['generated'] = (self.payload(generated['entry']), nodes, False)
        for role in ('original', 'repaired'):
            controls['agent-' + role] = (self.programs[role]['payload'], {
                'first': {'geometry': assembly['first' if role == 'original' else 'repaired_first'],
                          'origin': assembly['first_placement_m'], 'velocity': speed},
                'sibling': {'geometry': assembly['sibling'], 'origin': assembly['sibling_placement_m'],
                            'velocity': assembly['sibling_motion_m_per_second']}}, False)
        by_id = {case['id']: case for case in self.spec['cases']}
        for reference in self.spec['legacy_equivalence']:
            controls[Path(reference['source']).stem] = (self.payload(reference['source']),
                {'shape': {'geometry': legacy_geometry(by_id[reference['case']]['geometry']),
                           'origin': [0, 0, 0], 'velocity': speed}}, True)
        summary_rows = self.summary['artifacts'] + self.summary['legacy_artifacts']
        summary = {row['name']: row for row in summary_rows}
        self.check(len(self.summary['artifacts']) == 29 and len(self.summary['legacy_artifacts']) == 2 and
                   len(summary) == len(summary_rows) == len(controls) == 31 and set(summary) == set(controls) and
                   {path.name for path in self.root.glob('*.glb')} == {name+'.glb' for name in controls},
                   'All 29 new artifacts and both actual legacy companions are present exactly once')
        self.report['artifact_reports'], self.decoded_contents, self.decoded_measures = [], {}, {}
        self.decoded_ordinals = {}
        count_map = {'sections': 'section_count', 'rings': 'ring_count', 'holes': 'hole_count',
                     'authored_vertices': 'authored_vertex_count', 'triangles': 'triangle_count',
                     'cap_triangles_per_end': 'cap_triangle_count', 'strip_triangles': 'strip_triangle_count'}
        for name, (payload, nodes, legacy) in sorted(controls.items()):
            revision, manifest = bundle_identity(payload)
            expected, oracle, raw = self.json(name+'.expected.json'), self.json(name+'.oracle.json'), self.read(name+'.glb')
            schema = 'ontokin.ring-loft-destination-expected/0.1' if legacy else 'ontokin.framed-loft-destination-expected/0.1'
            target = 'ontokin.glb/0.10' if legacy else TARGET
            self.check(expected == {'schema_version': schema, 'case_id': name, 'program_revision': revision,
                                    'duration_seconds': self.spec['duration_seconds'], 'nodes': nodes},
                       'Artifact expectation derives from exact frozen facts ' + name)
            row = summary[name]
            self.check(row['path'] == name+'.glb' and row['bytes'] == len(raw) and row['sha256'] == sha(raw) and
                       row['program_revision'] == oracle['program_revision'] == revision and
                       row['source_revision'] == 'sha256:' + sha(payload['entry']['source'].encode('utf-8')) and
                       row['target_contract'] == oracle['target_contract'] == target and oracle['status'] == 'passed' and
                       row['geometry'] == oracle['geometry'], 'Actual artifact hashes and report linkage ' + name)
            observations = self.glb_motion(name, raw, {'program_revision': revision, 'manifest': manifest, 'nodes': nodes, 'legacy': legacy})
            geometry = {item['path']: item for item in oracle['geometry']}
            self.check(len(geometry) == len(oracle['geometry']) and set(geometry) ==
                       {path for path, value in nodes.items() if value['geometry'] is not None},
                       'Existing full topology report covers exact actual carriers ' + name)
            for path, report in geometry.items():
                wanted, measured = nodes[path]['geometry'], self.decoded_measures[name][path]
                self.check(report['status'] == 'passed' and report['intersections']['status'] == 'passed' and
                           all(report[left] == wanted[right] for left, right in count_map.items()) and
                           report['regions'] == wanted['region_triangle_counts'] and
                           abs(report['signed_volume_m3']-measured['signed_volume_m3']) <= 1e-12 and
                           abs(report['surface_area_m2']-measured['surface_area_m2']) <= 1e-10,
                           'Existing topology report measurements equal actual independently decoded triangles ' + name + ':' + path)
                if not legacy:
                    self.check(report['progression'] == wanted['progression'] and
                               report['flat_corners'] == wanted['vertex_count'] and report['source_intersections']['status'] == 'passed',
                               'Recorded frame progression and source topology evidence retains frozen identities ' + name + ':' + path)
            by_key = {(item['path'], item['time_seconds']): item for item in oracle['observations']}
            self.check(len(by_key) == len(oracle['observations']) == len(observations) == row['native_poses'] and
                       set(by_key) == {(item['path'], item['time_seconds']) for item in observations},
                       'Saved oracle observations cover every actual decoded sample ' + name)
            for observed in observations:
                saved = by_key[observed['path'], observed['time_seconds']]
                self.equal_vector(saved['translation'], observed['translation'], 'Saved oracle position equals supplied animation bytes ' + name, 1e-12)
                self.equal_vector(saved['rotation'], observed['rotation'], 'Saved oracle rotation equals supplied animation bytes ' + name, 1e-12)
            if name in ('generated', 'identity-solid-legacy', 'identity-hollow-legacy'):
                receipt = self.json(name + '.receipt.json')
                self.check(receipt['outcome'] == 'valid' and receipt['achieved_level'] == 'delivered' and
                           receipt['program_revision'] == revision and receipt['program']['manifest'] == manifest and
                           receipt['target_contract'] == target and receipt['artifact']['byte_length'] == len(raw) and
                           receipt['artifact']['sha256'] == 'sha256:' + sha(raw) and
                           receipt['implementation_identity']['source_code_sha256'] == self.implementation_sha and
                           receipt['execution_budget']['effective'] == DEFAULTS and
                           receipt['execution_budget']['budget_reason'] is None,
                           'Companion raw source receipt binds actual delivered bytes ' + name)
            self.report['artifact_reports'].append({'name': name, 'bytes': len(raw), 'sha256': sha(raw),
                'program_revision': revision, 'target_contract': target,
                'oracle_sha256': self.inputs[str(self.root/(name+'.oracle.json'))]['sha256'],
                'expectation_sha256': self.inputs[str(self.root/(name+'.expected.json'))]['sha256'],
                'complete_contact_checks_rerun': False, 'actual_decoded_measurements': self.decoded_measures[name],
                'actual_decoded_observations': observations})
        for left, right in self.spec['ordering_equivalence'] + self.spec['geometry_equivalence']:
            self.check(self.decoded_contents[left] == self.decoded_contents[right],
                       'Actual decoded topology, normals and PBR preserve frozen equivalence ' + left + ' / ' + right)
        legacy_rows = []
        for reference in self.spec['legacy_equivalence']:
            name = Path(reference['source']).stem
            case = reference['case']
            self.check(self.decoded_contents[name] == self.decoded_contents[case],
                       'Actual old and new identity-frame triangle streams are identical ' + case)
            legacy_rows.append({'case': case, 'reference': name, 'status': 'passed',
                                'reference_program_revision': summary[name]['program_revision'],
                                'framed_sha256': summary[case]['sha256'], 'legacy_sha256': summary[name]['sha256']})
        self.check(self.summary['legacy_equivalence'] == legacy_rows, 'Legacy equivalence summary reconciles to actual independent streams')
        self.check(self.decoded_contents['agent-original']['sibling'] == self.decoded_contents['agent-repaired']['sibling'] and
                   self.decoded_contents['agent-original']['first'] != self.decoded_contents['agent-repaired']['first'],
                   'Actual retrieved GLBs independently preserve sibling geometry and change only the repaired first surface')
        quantize = lambda point: [struct.unpack('<f', struct.pack('<f', value))[0] for value in point]
        for page_name, artifact, path in (
                ('sibling_before', 'agent-original', 'sibling'), ('sibling_after', 'agent-repaired', 'sibling'),
                ('first_before', 'agent-original', 'first'), ('first_continued', 'agent-original', 'first'),
                ('first_after', 'agent-repaired', 'first')):
            page = self.mesh_pages[page_name]
            self.check(len(page['triangles']) == len(page['region_keys']) == len(page['source_triangle_ordinals']),
                       'Native page has complete parallel triangle fields ' + page_name)
            for indices, region, ordinal in zip(page['triangles'], page['region_keys'], page['source_triangle_ordinals']):
                actual = self.decoded_ordinals[artifact][path][ordinal]
                self.check(len(indices) == 3 and actual[0] == region and
                           actual[1] == [quantize(page['positions_m'][index]) for index in indices] and
                           actual[2] == [quantize(page['normals'][index]) for index in indices],
                           'Raw native page triangle equals the actual retrieved GLB source ordinal ' + page_name + ':' + str(ordinal))
        self.report['decoded_observation_count'] = sum(len(row['actual_decoded_observations']) for row in self.report['artifact_reports'])

    def run(self):
        self.prepare()
        self.exchanges()
        self.workflow()
        self.durable()
        self.artifact_chunks()
        self.source_receipts()
        self.artifact_reports()
        self.check(all(Path(name).stat().st_size == value['bytes'] and sha(Path(name).read_bytes()) == value['sha256']
                       for name, value in self.inputs.items()), 'Every read input remains byte-identical after the audit')
        self.check(sha(Path(__file__).read_bytes()) == self.report['checker']['sha256'], 'Checker source unchanged during audit')
        self.report['status'] = 'passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acceptance-dir', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--candidate-commit', required=True)
    parser.add_argument('--freeze-commit', default=FREEZE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve earlier evidence and choose a new path.')
    if args.output.resolve().is_relative_to(args.repo.resolve()) or args.output.resolve().is_relative_to(args.acceptance_dir.resolve()):
        parser.error('Audit output must be outside both source and acceptance inputs.')
    audit = Audit(args)
    try:
        audit.run()
    except BaseException as exc:
        audit.report['status'] = 'failed'
        audit.report['failure'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
    audit.report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    audit.report['input_files'] = sorted(audit.inputs.values(), key=lambda row: row['path'])
    audit.report['git_inputs'] = sorted(audit.git_inputs.values(), key=lambda row: row['git_object'])
    audit.report['passed_checks'] = sum(row['passed'] for row in audit.report['checks'])
    audit.report['failed_checks'] = sum(not row['passed'] for row in audit.report['checks'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as file:
        json.dump(audit.report, file, indent=2, allow_nan=False)
        file.write('\n')
    print(json.dumps({'status': audit.report['status'], 'passed_checks': audit.report['passed_checks'],
                      'failed_checks': audit.report['failed_checks'], 'output': str(args.output.resolve()),
                      'output_sha256': sha(args.output.read_bytes()), 'checker_sha256': audit.report['checker']['sha256'],
                      'failure': audit.report.get('failure', {}).get('message')}))
    return 0 if audit.report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
