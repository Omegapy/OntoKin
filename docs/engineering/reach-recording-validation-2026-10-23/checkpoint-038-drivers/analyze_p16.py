#!/usr/bin/env python3
"""Independent post-failure P16 clock census; never imports OntoKin.

This analyzes retained input from a failed request. It never resumes that
request and cannot establish an accepted export or release result.
"""
import argparse
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
COMMIT = "4ca73909f861fe4bef9694787473621c1d21c140"
TREE = "87c949b238055af1ce368c694e1d5683c8aeacde"
REVISION = "sha256:0487f3f410944484f0a6aad7bef37e1a59a1d13464b19af85661251c430388f7"
MANIFEST = "docs/language-design/planar-reach-v0.1/p16.files.json"
MANIFEST_SHA = "0d218a8b1245766fa3e4892ec5ccafd275ee92fd4195b3b852d5daaefa9e4070"
MAX_KEYS, MAX_BITS, MAX_BYTES = 10000, 32768, 64 * 1024 * 1024
OPTIONS = {"end": "4", "fps": 1, "helpers": False,
           "position_tolerance_m": .001, "rotation_tolerance_rad": .001,
           "time_tolerance_s": .000001}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if type(a) is float:
        return struct.pack('>d', a) == struct.pack('>d', b)
    return a == b


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def no_constant(value):
    raise ValueError('Nonfinite JSON value: ' + value)


def parse_json(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON exceeds 64 MiB analysis bound')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=no_constant)


def read(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or nonregular input: ' + str(path))
    raw = path.read_bytes()
    return parse_json(raw), {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': digest(raw)}, raw


def write(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    if len(raw) > MAX_BYTES:
        raise ValueError('Output exceeds 64 MiB analysis bound')
    with path.open('xb') as stream:
        stream.write(raw)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, condition, detail=None):
        row = {'name': name, 'passed': bool(condition)}
        if detail is not None:
            row['detail'] = detail
        self.rows.append(row)
        return row['passed']

    def require(self, name, condition, detail=None):
        if not self.add(name, condition, detail):
            raise ValueError('Required evidence check failed: ' + name)

    def report(self):
        failed = [r['name'] for r in self.rows if not r['passed']]
        return {'passed': not failed, 'check_count': len(self.rows), 'failed_checks': failed, 'checks': self.rows}


def member(root, name):
    if type(name) is not str or '\\' in name or '\0' in name:
        raise ValueError('Invalid member path')
    parts = PurePosixPath(name)
    if parts.is_absolute() or any(p in ('', '.', '..') for p in parts.parts):
        raise ValueError('Unsafe member path')
    path = root.joinpath(*parts.parts)
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Missing or escaping member: ' + name)
    return path


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def check_inventory(root, inventory, checks):
    checks.require('inventory commit/tree/clean identity', inventory['commit'] == COMMIT and inventory['tree'] == TREE and inventory['status'] == '')
    rows = inventory['files']
    checks.require('inventory totals', type(rows) is list and len(rows) == inventory['file_count'] and sum(r['bytes'] for r in rows) == inventory['total_bytes'])
    expected = {}
    for entry in git(root, 'ls-tree', '-r', '-z', 'HEAD').decode().split('\0'):
        if not entry:
            continue
        metadata, name = entry.split('\t', 1)
        mode, kind, blob = metadata.split()
        if kind != 'blob' or name in expected:
            raise ValueError('Unexpected Git tree entry')
        expected[name] = (mode, blob)
    seen, mismatches = set(), []
    for row in rows:
        name = row['path']
        if name in seen:
            raise ValueError('Duplicate inventory path')
        seen.add(name)
        path = member(root, name)
        raw = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        mode = '100755' if path.stat().st_mode & 0o111 else '100644'
        if (type(row['bytes']) is not int or len(raw) != row['bytes'] or digest(raw) != row['sha256']
                or blob != row['git_blob'] or mode != row['mode'] or expected.get(name) != (mode, blob)):
            mismatches.append(name)
    tracked = set(filter(None, git(root, 'ls-files', '-z').decode().split('\0')))
    checks.require('full tracked inventory membership and bytes', seen == set(expected) == tracked and not mismatches,
                   {'files': len(rows), 'bytes': inventory['total_bytes'], 'mismatches': mismatches})
    checks.require('actual clean execution checkout', git(root, 'rev-parse', 'HEAD').decode().strip() == COMMIT
                   and git(root, 'rev-parse', 'HEAD^{tree}').decode().strip() == TREE
                   and not git(root, 'status', '--porcelain=v1', '--untracked-files=all'))
    checks.require('original P16 manifest bytes', digest(member(root, MANIFEST).read_bytes()) == MANIFEST_SHA)
    raw = git(root, 'cat-file', 'commit', COMMIT)
    checks.require('actual original commit object', hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == COMMIT)


class Native:
    def __init__(self, bounds):
        self.bounds, self.nodes = bounds, 0

    def integer(self, text):
        if type(text) is not str or len(text) > MAX_BITS // 4 + 4:
            raise ValueError('Bad bounded integer')
        value = int(text, 16)
        if hex(value) != text or value.bit_length() > MAX_BITS:
            raise ValueError('Noncanonical integer')
        return value

    def decode(self, node, depth=0):
        self.nodes += 1
        if type(node) is not dict or depth > self.bounds['depth'] or self.nodes > self.bounds['native_nodes'] * 4:
            raise ValueError('Native capture node/depth bound exceeded')
        kind = node.get('type')
        if kind in ('NoneType', 'bool', 'str'):
            expected = {'NoneType': type(None), 'bool': bool, 'str': str}[kind]
            if set(node) != {'type', 'value'} or type(node['value']) is not expected:
                raise ValueError('Malformed scalar tag')
            if kind == 'str' and len(node['value']) > self.bounds['string_characters']:
                raise ValueError('Captured string too long')
            return node['value']
        if kind == 'int':
            if set(node) != {'type', 'hex'}:
                raise ValueError('Malformed integer tag')
            return self.integer(node['hex'])
        if kind == 'Fraction':
            if set(node) != {'type', 'numerator_hex', 'denominator_hex'}:
                raise ValueError('Malformed Fraction tag')
            n, d = self.integer(node['numerator_hex']), self.integer(node['denominator_hex'])
            if d <= 0 or math.gcd(n, d) != 1:
                raise ValueError('Noncanonical Fraction storage')
            return Fraction(n, d)
        if kind == 'float':
            if set(node) != {'type', 'hex', 'bits_be'} or len(node['bits_be']) != 16:
                raise ValueError('Malformed float tag')
            value = struct.unpack('>d', bytes.fromhex(node['bits_be']))[0]
            if not math.isfinite(value) or value.hex() != node['hex']:
                raise ValueError('Nonfinite or inconsistent float')
            return value
        if kind in ('tuple', 'list', 'set'):
            wanted = {'type', 'items'} | ({'iteration_order_semantics'} if kind == 'set' else set())
            if set(node) != wanted or type(node['items']) is not list or len(node['items']) > self.bounds['sequence_items']:
                raise ValueError('Malformed or excessive native sequence')
            values = [self.decode(x, depth + 1) for x in node['items']]
            if kind == 'set':
                if node['iteration_order_semantics'] != 'unordered' or len(set(values)) != len(values):
                    raise ValueError('Malformed native set')
                return set(values)
            return tuple(values) if kind == 'tuple' else values
        if kind == 'dict':
            if set(node) != {'type', 'entries'} or type(node['entries']) is not list or len(node['entries']) > self.bounds['mapping_items']:
                raise ValueError('Malformed native mapping')
            result = {}
            for pair in node['entries']:
                if type(pair) is not list or len(pair) != 2:
                    raise ValueError('Malformed mapping entry')
                key, value = (self.decode(x, depth + 1) for x in pair)
                if key in result:
                    raise ValueError('Repeated native key')
                result[key] = value
            return result
        raise ValueError('Required native value unavailable or unsupported: ' + str(kind))


def ratio(value):
    if type(value) is not Fraction:
        value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def canonical_clock(label):
    if type(label) is not dict or set(label) != {'numerator', 'denominator'}:
        raise ValueError('Clock label must have exactly its two fields')
    values = []
    for key in ('numerator', 'denominator'):
        text = label[key]
        if type(text) is not str or not 1 <= len(text) <= 9865 or re.fullmatch(r'0|[1-9][0-9]*', text, re.ASCII) is None:
            raise ValueError('Noncanonical clock integer text')
        value = 0
        for offset in range(0, len(text), 256):
            chunk = text[offset:offset + 256]
            value = value * 10 ** len(chunk) + int(chunk)
        if value.bit_length() > MAX_BITS:
            raise ValueError('Clock integer exceeds operand maximum')
        values.append(value)
    n, d = values
    if d <= 0 or math.gcd(n, d) != 1:
        raise ValueError('Clock label is not reduced with positive denominator')
    return Fraction(n, d)


def binary32(word):
    if type(word) is not int or not 0 <= word <= 0x7f7fffff:
        raise ValueError('Clock word is not nonnegative finite binary32')
    exponent, trailing = word >> 23, word & 0x7fffff
    if exponent == 0:
        return Fraction(trailing, 1 << 149)
    coefficient, shift = (1 << 23) + trailing, exponent - 150
    return Fraction(coefficient << shift) if shift >= 0 else Fraction(coefficient, 1 << -shift)


def rounding_cell(word):
    center = binary32(word)
    lower = Fraction(0) if word == 0 else (binary32(word - 1) + center) / 2
    upper_neighbor = Fraction(1 << 128) if word == 0x7f7fffff else binary32(word + 1)
    return lower, (center + upper_neighbor) / 2, not word & 1


def glb_clocks(raw, checks):
    checks.require('bounded exact GLB header', 20 <= len(raw) <= MAX_BYTES
                   and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)))
    chunks, offset = [], 12
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError('Truncated GLB chunk header')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if length % 4 or offset + length > len(raw):
            raise ValueError('Truncated or unaligned GLB chunk')
        chunks.append((kind, raw[offset:offset + length]))
        offset += length
    checks.require('complete JSON/BIN chunk sequence', len(chunks) == 2
                   and chunks[0][0] == 0x4e4f534a and chunks[1][0] == 0x004e4942 and offset == len(raw))
    document, binary = parse_json(chunks[0][1]), chunks[1][1]
    buffers = document['buffers']
    checks.require('single internal GLB buffer', type(buffers) is list and len(buffers) == 1
                   and 'uri' not in buffers[0] and type(buffers[0]['byteLength']) is int
                   and 0 <= len(binary) - buffers[0]['byteLength'] <= 3)
    checks.require('single original animation', type(document['animations']) is list and len(document['animations']) == 1)
    animation, axes, inputs = document['animations'][0], {}, []
    samplers = animation['samplers']
    checks.require('bounded nonempty common samplers', type(samplers) is list and 1 <= len(samplers) <= MAX_KEYS)
    for sampler in samplers:
        index = sampler['input']
        if type(index) is not int or not 0 <= index < len(document['accessors']):
            raise ValueError('Invalid clock accessor index')
        inputs.append(index)
        if index in axes:
            continue
        accessor = document['accessors'][index]
        checks.require('clock accessor scalar float32 ' + str(index), accessor['componentType'] == 5126
                       and accessor['type'] == 'SCALAR' and 'sparse' not in accessor
                       and accessor.get('normalized', False) is False)
        count = accessor['count']
        if type(count) is not int or not 1 <= count <= MAX_KEYS:
            raise ValueError('Clock count outside bounded domain')
        view_index = accessor['bufferView']
        if type(view_index) is not int or not 0 <= view_index < len(document['bufferViews']):
            raise ValueError('Invalid clock bufferView')
        view = document['bufferViews'][view_index]
        vo, ao, stride = view.get('byteOffset', 0), accessor.get('byteOffset', 0), view.get('byteStride', 4)
        if (view['buffer'] != 0 or any(type(x) is not int for x in (vo, ao, stride, view['byteLength']))
                or min(vo, ao) < 0 or stride < 4 or stride % 4
                or ao + (count - 1) * stride + 4 > view['byteLength']
                or vo + view['byteLength'] > buffers[0]['byteLength'] or (vo + ao) % 4):
            raise ValueError('Invalid clock byte range/stride')
        words = [struct.unpack_from('<I', binary, vo + ao + i * stride)[0] for i in range(count)]
        axes[index] = {'words': words, 'offset': vo + ao, 'stride': stride,
                       'count': count, 'view_index': view_index, 'accessor': accessor}
    first = axes[inputs[0]]['words']
    checks.require('every sampler has identical actual clock words', all(axes[i]['words'] == first for i in inputs))
    return document, animation, first, {'sampler_count': len(samplers), 'input_accessors_in_order': inputs,
            'binary_bytes': len(binary), 'binary_sha256': digest(binary),
            'unique_accessors': [{'index': key, **value} for key, value in axes.items()]}


def source_schedule(root, checks):
    """Restricted literal P16 schedule reconstruction, not a language evaluator."""
    manifest = parse_json(member(root, MANIFEST).read_bytes())
    entry_name = str(PurePosixPath(MANIFEST).parent / manifest['entry']['path'])
    raw = member(root, entry_name).read_bytes()
    source = raw.decode('utf-8')
    durations = re.findall(r'^\s*duration\s*=\s*([0-9]+(?:\.[0-9]+)?)\[s\];\s*$', source, re.MULTILINE)
    checks.require('one literal P16 duration', len(durations) == 1)
    end = Fraction(durations[0])
    actions, statements = {}, []
    for line in source.splitlines():
        match = re.fullmatch(r'\s*action\s+(\w+)\s+@\s+"[^"]+"\s*=\s*(.*);\s*', line)
        if match:
            clock = re.findall(r'([0-9]+(?:\.[0-9]+)?)\[s\]', match[2])
            checks.require('one literal duration in action ' + match[1], len(clock) == 1 and match[1] not in actions)
            actions[match[1]] = Fraction(clock[0])
            statements.append(line.strip())
    events = re.findall(r'^\s*at\s+([0-9]+(?:\.[0-9]+)?)\[s\]\s+sequence\s*\{([^{}]*)\}\s*$', source, re.MULTILINE)
    checks.require('complete explicit P16 event lines', len(events) == len(re.findall(r'^\s*at\s', source, re.MULTILINE)) == 2)
    boundaries, occurrences = {Fraction(0), end}, []
    for clock, body in events:
        start = Fraction(clock)
        boundaries.add(start)
        for name in re.findall(r'\bstart\s+(\w+)\s*;', body):
            if name not in actions:
                raise ValueError('Unknown literal scheduled action')
            finish = start + actions[name]
            boundaries.add(finish)
            occurrences.append({'kind': 'action', 'name': name, 'start': ratio(start), 'duration': ratio(actions[name]), 'end': ratio(finish)})
        for duration in re.findall(r'\bfor\s+([0-9]+(?:\.[0-9]+)?)\[s\]\s*;', body):
            finish = start + Fraction(duration)
            boundaries.add(finish)
            occurrences.append({'kind': 'force', 'start': ratio(start), 'duration': ratio(Fraction(duration)), 'end': ratio(finish)})
        statements.append('at ' + clock + '[s] sequence {' + body + '}')
    checks.require('bounded P16 schedule entries', len(actions) == 3 and len(occurrences) == 4 and all(0 <= t <= end for t in boundaries))
    return boundaries, end, {'source_path': entry_name, 'source_sha256': digest(raw), 'statements': statements,
            'occurrences': occurrences, 'boundaries': [ratio(x) for x in sorted(boundaries)],
            'scope': 'Independent restricted extraction of this identified source literal action, event and force durations; no production or reference kernel is invoked.'}


def source_bindings(root):
    requests = {'ontokin/reach_conformance.py': ['_integer', 'rational_clock', '_integer_clock_cell_contains',
                'clock_cell_contains', 'verify_retained_clocks', '_Bounds.compare', 'validate_reach_export'],
                'ontokin/reach_numeric.py': ['ReachExecutionWork.charge'],
                'ontokin/construction.py': ['ConstructionBudget.tick'],
                'ontokin/gltf.py': ['DecodedGLB.clock', 'read_glb']}
    result = {}
    for filename, names in requests.items():
        raw = member(root, filename).read_bytes()
        tree = ast.parse(raw)
        for name in names:
            nodes = tree.body
            for part in name.split('.'):
                found = [n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part]
                if len(found) != 1:
                    raise ValueError('Source binding missing or ambiguous: ' + filename + ':' + name)
                node, = found
                nodes = node.body
            result[filename + ':' + name] = {'source_path': filename, 'source_sha256': digest(raw),
                'first_line': node.lineno, 'last_line': node.end_lineno,
                'ast_sha256': digest(ast.dump(node, include_attributes=False).encode())}
    return result


def neutrality(pair, root, checks, evidence):
    reports, inventories, commands = {}, [], []
    for mode in ('control', 'capture'):
        directory = pair / mode
        values = {}
        for name in ('start.json', 'request-start.json', 'request-result.json', 'inputs-before.json', 'inputs-after.json'):
            value, meta, raw = read(directory / name)
            values[name] = value
            evidence[mode + '/' + name] = meta
            if name.startswith('inputs-'):
                inventories.append((value, raw))
        row = values['request-result.json']
        reports[mode] = row
        bad = [k for k in ('metadata_error', 'capture_failure', 'inventory_error', 'driver_failure', 'unexpected_completion') if k in row]
        checks.require(mode + ' request and metadata closed without capture errors', not bad
                       and row['request_executed'] is True and row['status'] == 'failed'
                       and row['metadata_status'] == 'captured' and row['exit_code'] == 1, bad)
        checks.require(mode + ' exact source and program', row['source_commit'] == COMMIT and row['source_tree'] == TREE
                       and row['source_files'] == MANIFEST and row['source_manifest_sha256'] == MANIFEST_SHA
                       and row['program_revision'] == row['expected_program_revision'] == REVISION
                       and row['target_contract'] == 'ontokin.glb/0.6')
        checks.require(mode + ' original request options', same(row['options'], OPTIONS))
        checks.require(mode + ' no instrumentation or promotion', row['trace_installed'] is False
                       and row['profile_installed'] is False and row['release_acceptance'] is False
                       and row['original_exception_identity_preserved'] is True)
        checks.require(mode + ' original resource failure', row['failure']['type'] == 'OntoKinError'
                       and row['failure']['message'] == 'Construction exceeded max_operations.'
                       and row['diagnostic']['code'] == 'OKL-E-RESOURCE'
                       and row['diagnostic']['details']['budget'] == 'max_operations'
                       and row['diagnostic']['details']['limit'] == 100000
                       and row['diagnostic']['details']['consumed'] == 100001)
        state = row['post_state']
        checks.require(mode + ' observation preserved complete native counts and caches', row['observation_preserved_counters_and_caches'] is True
                       and same(state, row['post_observation_state']))
        checks.require(mode + ' stable source and driver', row['inputs_stable'] is True and row['driver_unchanged'] is True)
        checks.require(mode + ' original work limits', same(state['work_limits'], {'max_operations': 100000,
                       'max_elapsed_ms': 30000, 'max_operand_bits': 32768, 'max_cache_entries': 256})
                       and same(state['construction_limits'], {'max_objects': 1000, 'max_operations': 100000,
                           'max_result_items': 1000, 'max_elapsed_ms': 30000, 'max_value_entries': 100000})
                       and state['category_metadata_limit'] == 512)
        work = state['reach_work']
        checks.require(mode + ' complete category reconciliation', type(work['counts']) is dict and len(work['counts']) <= 512
                       and all(type(k) is str and type(v) is int and v >= 0 for k, v in work['counts'].items())
                       and sum(work['counts'].values()) == work['operations']
                       and type(state['shared_operations']) is int and state['shared_operations'] == 100001
                       and state['shared_minus_reach_operations'] == 100001 - work['operations'])
        checks.require(mode + ' distinct numerical caches in original bounds', type(work['cache_entries']) is int and 0 <= work['cache_entries'] <= 256
                       and state['independent_arithmetic']['available'] is True
                       and 0 <= state['independent_arithmetic']['cache_entries_post_cleanup'] <= 256
                       and state['independent_arithmetic']['cache_operand_limit'] == 32768
                       and state['decoded_cache']['available'] is True)
        owner_flags = ('work_callback_error_is_original', 'work_external_check_is_construction_tick',
                       'construction_external_check_is_none', 'validation_work_is_compiler_work', 'validation_model_is_compiler_model')
        checks.require(mode + ' observed original ownership and exception relationships', all(state[k] is True for k in owner_flags)
                       and state['construction_callback_error_is_original'] is False
                       and state['trace_installed_post_failure'] is False and state['profile_installed_post_failure'] is False
                       and state['independent_arithmetic']['work_is_compiler_work'] is True
                       and state['independent_arithmetic']['check_is_work_tick'] is True)
        command = row['command']
        checks.require(mode + ' bounded exact driver command shape', type(command) is list and len(command) == 8
                       and all(type(x) is str for x in command) and command[2::2] == ['--root', '--output', '--mode'])
        driver, interpreter = Path(command[1]).resolve(), Path(command[0]).resolve()
        checks.require(mode + ' executable/driver/working-directory binding', Path(command[3]).resolve() == root
                       and Path(command[5]).resolve() == directory and command[7] == mode
                       and Path(row['cwd']).resolve() == root and row['environment']['executable'] == command[0]
                       and digest(driver.read_bytes()) == row['driver_sha256']
                       and digest(interpreter.read_bytes()) == row['environment']['executable_sha256'])
        trace = (directory / 'traceback.txt').read_bytes()
        evidence[mode + '/traceback.txt'] = {'path': str(directory / 'traceback.txt'), 'bytes': len(trace), 'sha256': digest(trace)}
        checks.require(mode + ' bounded complete traceback', type(row['traceback_frames']) is list
                       and 1 <= len(row['traceback_frames']) <= row['native_capture_bounds']['frames'])
        external = []
        for frame in row['traceback_frames']:
            if frame['scope'] == 'external_driver':
                external.append(frame)
                path = Path(frame['path']).resolve()
                checks.require(mode + ' external driver frame belongs to frozen driver', path == driver and frame['source_sha256'] == row['driver_sha256'])
            elif frame['scope'] == 'product':
                path = member(root, frame['path'])
            else:
                raise ValueError('Unknown traceback scope')
            raw = path.read_bytes()
            lines = raw.decode().splitlines()
            checks.require(mode + ' frame source ' + frame['qualname'], digest(raw) == frame['source_sha256']
                           and type(frame['line']) is int and 1 <= frame['line'] <= len(lines)
                           and lines[frame['line'] - 1] == frame['statement'])
        checks.require(mode + ' one explicit external frame', len(external) == 1)
        command_dir = pair / (mode + '-command')
        outer, meta, _ = read(command_dir / 'result.json')
        evidence[mode + '-command/result.json'] = meta
        start, meta, _ = read(command_dir / 'start.json')
        evidence[mode + '-command/start.json'] = meta
        commands.append(outer)
        checks.require(mode + ' closed outer command', outer['started_process'] is True and outer['exit_code'] == 1
                       and not outer.get('timed_out', False) and 'command_error' not in outer
                       and outer['driver_unchanged'] is True and outer['timeout_seconds'] == 180
                       and outer['command'] == [command[0], '-B', *command[1:]] and outer['cwd'] == row['cwd'])
        checks.require(mode + ' command start fields preserved', all(same(v, outer[k]) for k, v in start.items() if k != 'started_process'))
        checks.require(mode + ' both closed raw streams', [s['path'] for s in outer['streams']] == ['stdout.txt', 'stderr.txt'])
        for stream in outer['streams']:
            raw = member(command_dir, stream['path']).read_bytes()
            checks.require(mode + ' stream bytes ' + stream['path'], len(raw) == stream['bytes'] and digest(raw) == stream['sha256'])
        reports[mode + '_start'] = values['start.json']
    first, last = reports['control'], reports['capture']
    excluded = {'mode', 'command', 'started_at', 'finished_request_at', 'product_elapsed_seconds', 'finished_receipt_at',
                'capture_status', 'census_sha256', 'retained_reader_input'}
    checks.require('entire common result is exactly equal with native JSON types', same(
        {k: v for k, v in first.items() if k not in excluded}, {k: v for k, v in last.items() if k not in excluded}),
        {'excluded_only': sorted(excluded)})
    start_excluded = {'mode', 'command', 'started_at'}
    checks.require('entire common start receipt agrees', same(
        {k: v for k, v in reports['control_start'].items() if k not in start_excluded},
        {k: v for k, v in reports['capture_start'].items() if k not in start_excluded}))
    checks.require('all four tracked inventories are byte-identical', len(inventories) == 4 and all(raw == inventories[0][1] for _, raw in inventories))
    check_inventory(root, inventories[0][0], checks)
    inventory_hashes = {(r['sha256'], r['bytes']) for r in inventories[0][0]['files']}
    checks.require('all complete source units bind exact tracked bytes', len(first['source_units']) == 4
                   and all((u['sha256'], u['bytes']) in inventory_hashes and u['source_revision'] == 'sha256:' + u['sha256'] for u in first['source_units']))
    file_manifest = parse_json(member(root, MANIFEST).read_bytes())
    expected_units = {}
    for unit in [file_manifest['entry'], *file_manifest['modules']]:
        source_raw = member(root, str(PurePosixPath(MANIFEST).parent / unit['path'])).read_bytes()
        if unit['filename'] in expected_units:
            raise ValueError('Duplicate filename in original source manifest')
        expected_units[unit['filename']] = (len(source_raw), digest(source_raw))
    checks.require('exact complete manifest/source-unit closure', len({u['filename'] for u in first['source_units']}) == len(first['source_units'])
                   and {u['filename']: (u['bytes'], u['sha256']) for u in first['source_units']} == expected_units)
    checks.require('raw tracebacks agree without removing product frames', (pair / 'control/traceback.txt').read_bytes() == (pair / 'capture/traceback.txt').read_bytes())
    checks.require('capture runs after one failed control', first['capture_status'] == 'not_requested' and last['capture_status'] == 'captured')
    plan, meta, _ = read(pair / 'plan.json')
    evidence['plan.json'] = meta
    closed, closed_meta, _ = read(pair / 'pair-command.json')
    evidence['pair-command.json'] = closed_meta
    checks.require('frozen one-control then one-capture plan', plan['order'] == ['control', 'capture']
                   and plan['requests_per_mode'] == 1 and plan['source_commit'] == COMMIT and plan['source_tree'] == TREE
                   and plan['driver_sha256'] == first['driver_sha256'] and plan['expected_program_revision'] == REVISION
                   and plan['manifest_sha256'] == MANIFEST_SHA
                   and same(plan['request'], {'case': 'P16', 'fps_native_type': 'int', **OPTIONS})
                   and all(plan[k] is True for k in ('product_limits_unchanged', 'no_live_instrumentation',
                       'no_timing_acceptance_threshold', 'no_reruns_or_exclusions_in_this_plan', 'neutrality_required_before_census_interpretation')))
    checks.require('complete two-command closed runner receipt', closed['plan_sha256'] == meta['sha256']
                   and closed['processes_started'] == closed['commands_closed'] == 2 and closed['outer_error'] is None
                   and closed['orchestrator_unchanged'] is True and same(closed['commands'], commands))
    return last, {'comparison_rule': 'Complete common receipts, exact JSON types/float bits and raw traceback bytes; external frame is identified separately.',
                  'excluded_fields': sorted(excluded), 'control_seconds': first['product_elapsed_seconds'],
                  'capture_seconds': last['product_elapsed_seconds'], 'elapsed_neutrality_claimed': False,
                  'performance_acceptance_claimed': False, 'post_state': first['post_state'],
                  'source_inventory_files': inventories[0][0]['file_count'], 'source_inventory_bytes': inventories[0][0]['total_bytes']}


def census(pair, root, row, checks, evidence):
    captured, meta, _ = read(pair / 'capture/census.json')
    evidence['capture/census.json'] = meta
    checks.require('captured census hash and native bounds', meta['sha256'] == row['census_sha256']
                   and same(captured['bounds'], row['native_capture_bounds'])
                   and 0 < captured['native_nodes_encoded'] <= captured['bounds']['native_nodes'])
    native = Native(captured['bounds'])
    clock = {k: native.decode(v) for k, v in captured['clock'].items()}
    identities = captured['identity_relationships']
    checks.require('all declared capture identity relationships', identities['reference_model_is_compiler_model'] is False
                   and all(v is True for k, v in identities.items() if k != 'reference_model_is_compiler_model'))
    checks.require('original iterator never touched', captured['generator']['iterator_touched'] is False
                   and captured['pair_binding']['retained_iterator_touched'] is False)
    raw = member(pair / 'capture', row['retained_reader_input']['path']).read_bytes()
    common = row['post_state']['reader_input']
    checks.require('unvalidated input bytes bind both common and capture receipts', len(raw) == common['bytes'] == row['retained_reader_input']['bytes']
                   and digest(raw) == common['sha256'] == row['retained_reader_input']['sha256']
                   and common['status'] == row['retained_reader_input']['status'] == 'unvalidated_reader_input_from_failed_request')
    evidence['capture/unvalidated-reader-input.glb'] = {'path': str(pair / 'capture/unvalidated-reader-input.glb'), 'bytes': len(raw), 'sha256': digest(raw)}
    document, animation, words, storage = glb_clocks(raw, checks)
    labels = animation['extras']['ontokin']['exact_times_seconds']
    quantization = document['extras']['ontokin']['reach_quantization']
    retained = quantization['retained_keys']
    n = len(words)
    checks.require('complete bounded captured clock arrays', type(labels) is list and type(retained) is list
                   and type(clock['authored_records']) is list and type(clock['retained']) is list
                   and type(clock['authored']) is list and type(clock['times']) is list
                   and all(len(a) == n for a in (labels, retained, clock['authored_records'], clock['retained'], clock['authored'], clock['times'])))
    checks.require('typed labels exactly match captured native arrays', same(labels, clock['authored_records']) and same(retained, clock['retained']))
    actual_options = {k: native.decode(v) for k, v in captured['actual_export_options'].items()}
    checks.require('actual native options preserve types and values', type(actual_options['end']) is Fraction and actual_options['end'] == Fraction(4)
                   and same({k: v for k, v in actual_options.items() if k != 'end'}, {k: v for k, v in OPTIONS.items() if k != 'end'})
                   and type(clock['end']) is Fraction and clock['end'] == actual_options['end']
                   and type(clock['time_tolerance']) is float and same(clock['time_tolerance'], actual_options['time_tolerance_s']))
    source_boundaries, source_end, schedule = source_schedule(root, checks)
    checks.require('native source boundary sequence and semantic membership', type(clock['boundaries']) is tuple
                   and all(type(x) is Fraction for x in clock['boundaries']) and type(clock['semantic']) is set
                   and len(clock['boundaries']) == len(set(clock['boundaries']))
                   and set(clock['boundaries']) == clock['semantic'] == source_boundaries
                   and tuple(sorted(source_boundaries)) == clock['boundaries'] and clock['end'] == source_end)
    reference = captured['source_reference']['fields']
    checks.require('source reference retains same complete boundaries and horizon', native.decode(reference['end']) == clock['end']
                   and native.decode(reference['boundaries']) == clock['boundaries'])
    stored = captured['stored_axis']
    checks.require('captured raw word census and storage descriptions', stored['times_is_native_clock_cache_entry'] is True
                   and len(stored['words']) == n and stored['accessor_index'] == storage['input_accessors_in_order'][0]
                   and stored['binary_bytes'] == storage['binary_bytes'] and stored['binary_sha256'] == storage['binary_sha256']
                   and same(native.decode(stored['samplers']), animation['samplers'])
                   and same(native.decode(stored['accessor']), document['accessors'][stored['accessor_index']])
                   and same(native.decode(stored['buffer_view']), document['bufferViews'][stored['buffer_view_index']]))
    parsed, decoded, rows, cell_bounds, shifts = [], [], [], [], []
    for i, (label, record, word) in enumerate(zip(labels, retained, words)):
        value, actual = canonical_clock(label), binary32(word)
        lower, upper, inclusive = rounding_cell(word)
        left_ok = value > lower or inclusive and value == lower
        right_ok = value < upper or inclusive and value == upper
        shift = abs(value - actual)
        checks.require('clock row ' + str(i), type(clock['authored'][i]) is Fraction and clock['authored'][i] == value
                       and type(clock['times'][i]) is float and Fraction(clock['times'][i]) == actual
                       and set(record) == {'authored_seconds', 'stored_seconds', 'stored_binary32_bits', 'semantic_boundary'}
                       and same(record['authored_seconds'], label) and type(record['stored_seconds']) in (int, float)
                       and Fraction(record['stored_seconds']) == actual and record['stored_binary32_bits'] == format(word, '08x')
                       and type(record['semantic_boundary']) is bool and record['semantic_boundary'] == (value in source_boundaries)
                       and left_ok and right_ok and same(stored['words'][i], {'index': i, 'bytes_le': struct.pack('<I', word).hex(), 'binary32_bits_hex': format(word, '08x')}))
        parsed.append(value)
        decoded.append(actual)
        cell_bounds.append((lower, upper, inclusive))
        shifts.append(shift)
        rows.append({'index': i, 'label': label, 'label_type': 'dict[str,str]', 'parsed_type': 'Fraction',
            'parsed': ratio(value), 'actual_binary32_bits': format(word, '08x'), 'actual_binary32_bytes_le': struct.pack('<I', word).hex(),
            'stored_exact': ratio(actual), 'captured_float_bits_be': struct.pack('>d', clock['times'][i]).hex(),
            'stored_label_native_type': type(record['stored_seconds']).__name__, 'semantic_boundary': record['semantic_boundary'],
            'rounding_cell': {'lower': ratio(lower), 'upper': ratio(upper), 'ties_included': inclusive,
                              'lower_membership': left_ok, 'upper_membership': right_ok}, 'absolute_shift': ratio(shift)})
    checks.require('exact authored and actual stored axes strictly increase', all(a < b for a, b in zip(parsed, parsed[1:]))
                   and all(a < b for a, b in zip(decoded, decoded[1:])))
    checks.require('start/end and complete semantic coverage', parsed[0] == 0 and parsed[-1] == source_end and source_boundaries.issubset(parsed))
    max_shift = max(shifts)
    checks.require('completed maximum shift and original exact float tolerance', type(clock['maximum_shift']) is Fraction
                   and max_shift == clock['maximum_shift'] and max_shift <= Fraction(clock['time_tolerance']))
    checks.require('final row locals belong to last completed parse row', type(clock['index']) is int and clock['index'] == n - 1
                   and same(clock['record'], retained[-1]) and same(clock['source_record'], labels[-1])
                   and clock['source'] == parsed[-1] and same(clock['actual'], clock['times'][-1]) and clock['bits'] == words[-1])
    checks.require('ordered disjoint direct-rounding cells', all(
        a[1] < b[0] or a[1] == b[0] and not (a[2] and b[2]) for a, b in zip(cell_bounds, cell_bounds[1:])))
    checks.require('actual failure retains generator and compare operands', captured['generator']['available'] is True
                   and captured['attempted_comparison']['available'] is True
                   and captured['attempted_comparison']['result_available_in_frame'] is False)
    generator = {k: native.decode(v) for k, v in captured['generator']['fields'].items()}
    comparison = {k: native.decode(v) for k, v in captured['attempted_comparison']['fields'].items()}
    checks.require('typed exact native attempted operands', set(generator) == set(comparison) == {'a', 'b'}
                   and all(type(x) is Fraction for x in (*generator.values(), *comparison.values())) and generator == comparison)
    matching = [i for i in range(n - 1) if parsed[i] == comparison['a'] and parsed[i + 1] == comparison['b']]
    binding = captured['pair_binding']
    checks.require('one exact adjacent pair with preserved native identity binding', len(matching) == 1
                   and binding['status'] == 'uniquely_bound' and binding['matched_indices'] == matching
                   and binding['identity_match_count'] == binding['value_match_count'] == 1
                   and binding['generator_and_compare_operands_identical'] is True
                   and binding['generator_and_compare_native_values_equal'] is True
                   and binding['left_index'] == matching[0] and binding['right_index'] == matching[0] + 1)
    j = matching[0]
    frames = row['traceback_frames']
    compare_frames = [f for f in frames if f['module'] == 'ontokin.reach_conformance' and f['qualname'] == '_Bounds.compare']
    generator_frames = [f for f in frames if f['qualname'] == 'verify_retained_clocks.<locals>.<genexpr>']
    checks.require('actual refused stage is original authored compare charge', len(compare_frames) == len(generator_frames) == 1
                   and compare_frames[0]['statement'].strip() == 'self.tick("independent_exact_compare")'
                   and generator_frames[0]['line'] == captured['generator']['first_line'])
    stages = {(s['module'], s['function']): {k: native.decode(v) for k, v in s['fields'].items()} for s in captured['stage_locals']}
    checks.require('retained native stage fields identify refused shared charge', stages[('ontokin.reach_numeric', 'ReachExecutionWork.charge')] == {'kind': 'independent_exact_compare', 'amount': 1}
                   and stages[('ontokin.construction', 'ConstructionBudget.tick')]['amount'] == 1
                   and stages[('ontokin.construction', 'ConstructionBudget.exceeded')] == {'name': 'max_operations', 'consumed': 100001})
    counts = row['post_state']['reach_work']['counts']
    s = storage['sampler_count']
    checks.require('source ledger applies to observed native short full-domain inputs', words[0] == 0 and all(w != 0 for w in words[1:])
                   and all(len(text) <= 128 for label in labels for text in label.values())
                   and all(max(v.numerator.bit_length(), v.denominator.bit_length()) <= 1024 for v in parsed)
                   and row['post_state']['work_limits']['max_operand_bits'] == 32768)
    stage_counts = {'independent_common_clock': s, 'independent_retained_clock': n,
        'independent_clock_integer': 2 * n, 'independent_clock_reduction': n, 'independent_clock_reduction_return': n,
        'independent_clock_cell': n, 'independent_bound_decode': 2 * n, 'independent_exact_add': 2 * n - 1,
        'independent_exact_compare': 2 * n + j, 'independent_exact_sub': n}
    exact_stage_categories = ('independent_common_clock', 'independent_retained_clock', 'independent_clock_cell',
                              'independent_bound_decode', 'independent_exact_add', 'independent_exact_compare', 'independent_exact_sub')
    checks.require('observed complete categories exactly reconcile clock-only stage work', all(counts[k] == stage_counts[k] for k in exact_stage_categories))
    preceding_end_parse = {'independent_clock_integer': 2, 'independent_clock_reduction': 1, 'independent_clock_reduction_return': 1}
    checks.require('observed parse categories reconcile rows plus preceding supplied-end parse', all(counts[k] == stage_counts[k] + v for k, v in preceding_end_parse.items()))
    completed = sum(stage_counts.values())
    checks.require('complete source-bound stage formula', completed == s + 13 * n - 1 + j)
    return {'input_status': 'unvalidated_reader_input_from_failed_request', 'accepted_export': False,
        'clock_count': n, 'sampler_count': s, 'source_schedule': schedule, 'storage': storage,
        'boundaries': [ratio(x) for x in clock['boundaries']], 'maximum_shift': ratio(max_shift),
        'maximum_shift_indices': [i for i, v in enumerate(shifts) if v == max_shift],
        'time_tolerance_native_type': 'float', 'time_tolerance_bits_be': struct.pack('>d', clock['time_tolerance']).hex(),
        'time_tolerance_exact': ratio(Fraction(clock['time_tolerance'])), 'rows': rows,
        'failure': {'function': '_Bounds.compare', 'stage': 'independent_exact_compare shared precharge refusal',
                    'left_index': j, 'right_index': j + 1, 'a': ratio(comparison['a']), 'b': ratio(comparison['b']),
                    'outer_parse_index': clock['index'], 'operand_input_guards_completed': True,
                    'prospective_cross_product_guards_executed': False, 'comparison_arithmetic_executed': False,
                    'completed_authored_pairs': j, 'attempted_pair_ordinal_one_based': j + 1,
                    'iterator_advanced_by_capture': False, 'source_frame': compare_frames[0]},
        'stage_ledger': {'provenance': 'Source-control-flow reconstruction from the complete native axis and uniquely bound failure pair; not a live stage-entry observation.',
                        'completed_categories': stage_counts, 'completed_row_loop_charges': 13 * n - 1,
                        'completed_common_sampler_charges': s, 'completed_authored_comparisons': j,
                        'completed_stage_total': completed, 'refused_shared_charge': 1, 'refused_reach_charge': 0,
                        'observed_total_categories_equal_stage': list(exact_stage_categories),
                        'preceding_supplied_end_parse_categories': preceding_end_parse,
                        'shared_entry_reconstructed': row['post_state']['shared_operations'] - 1 - completed,
                        'reach_entry_reconstructed': row['post_state']['reach_work']['operations'] - completed,
                        'authored_monotonicity_shared_entry_reconstructed': row['post_state']['shared_operations'] - 1 - j,
                        'authored_monotonicity_reach_entry_reconstructed': row['post_state']['reach_work']['operations'] - j,
                        'clock_lookup_note': 'read_glb has populated accessor data. The first clock() may populate _clocks from cached accessor rows without a work tick; post-failure occupancy alone is not an entry snapshot.',
                        'unvisited_tail_executed': False, 'complete_request_deficit': None},
        'completed_product_checks': ['all retained row parsing', 'all direct rounding cells', 'all stored/semantic row labels',
                                     'completed maximum shift', 'start/end condition', str(j) + ' preceding authored comparisons'],
        'offline_only_checks_after_failure': ['complete authored ordering', 'semantic subset coverage', 'maximum shift against exact native float tolerance'],
        'possible_future_question': {'observation': 'The actual stored axis is strictly increasing, and every exact authored value lies in its independently reconstructed direct rounding cell. Ordered disjoint cells imply authored ordering.',
            'gross_authored_comparison_sites_in_complete_pass': n - 1,
            'net_savings_established': False, 'runtime_optimization_selected': False,
            'required_before_any_implementation': 'Prove native ownership/storage/callback/dispatch/domain/lifetime safety and full charged admission/lookup/copy/storage costs, preserving equivalent independent ordering validation and ordinary fallback. Per-row new work can consume the gross comparison opportunity.'},
        'source_bindings': source_bindings(root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--pair', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, pair, output = args.root.resolve(), args.pair.resolve(), args.output.resolve()
    if output.is_relative_to(root) or output.is_relative_to(pair):
        raise ValueError('Analysis output must be outside product source and frozen pair')
    output.mkdir(parents=True, exist_ok=False)
    checks, evidence = Checks(), {}
    report = {'schema': 'ontokin.checkpoint038-clock-analysis/0.1', 'started_at': datetime.now(timezone.utc).isoformat(),
              'source_commit': COMMIT, 'source_tree': TREE, 'program_revision': REVISION,
              'analyzer_sha256': digest(Path(__file__).read_bytes()), 'status': 'failed',
              'product_requests_executed': 0, 'product_tail_resumed': False, 'accepted_export': False,
              'candidate_promotion': False, 'release_acceptance': False, 'full_product_goal_completed': False}
    write(output / 'start.json', report)
    try:
        row, neutral = neutrality(pair, root, checks, evidence)
        report['neutrality'] = neutral
        report['neutrality_checks'] = checks.report()
        write(output / 'neutrality.json', report['neutrality_checks'])
        census_checks = Checks()
        report['census'] = census(pair, root, row, census_checks, evidence)
        report['census_checks'] = census_checks.report()
        report['status'] = 'passed'
    except BaseException as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)}
        report['neutrality_checks'] = checks.report()
        if 'census_checks' in locals():
            report['census_checks'] = census_checks.report()
        (output / 'error.txt').write_text(''.join(traceback.format_exception(error)))
    report.update(finished_at=datetime.now(timezone.utc).isoformat(), evidence=evidence)
    write(output / 'report.json', report)
    print(json.dumps({'status': report['status'], 'neutrality_checks': report['neutrality_checks']['check_count'],
                      'census_checks': report.get('census_checks', {}).get('check_count', 0),
                      'clock_count': report.get('census', {}).get('clock_count')}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
