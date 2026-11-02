#!/usr/bin/env python3
"""Read-only independent predecessor byte audit. No production imports or execution.

Checks original observation and archive bytes, not candidate torque behavior.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--freeze', type=Path, required=True)
parser.add_argument('--preflight', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
assert not args.report.exists()
rows = []

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def check(name, actual, expected=True):
    row = {'name': name, 'passed': actual == expected}
    if not row['passed']:
        row.update(actual=str(actual), expected=str(expected))
    rows.append(row)

def load(path):
    return json.loads(path.read_text())

def identity(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'mode': f'{stat.S_IMODE(path.stat().st_mode):04o}',
            'sha256': digest(raw)}

archive_index_path = args.freeze / 'predecessor/ARCHIVES.json'
archives = load(archive_index_path)
for archive in archives['archives']:
    path = args.freeze / 'predecessor' / archive['archive']
    ident = identity(path)
    check(path.name + '/outer-bytes', ident['bytes'], archive['bytes'])
    check(path.name + '/outer-sha256', 'sha256:' + ident['sha256'], archive['sha256'])
    original = args.preflight / path.stem
    with zipfile.ZipFile(path) as z:
        expected = {m['path']: m for m in archive['members']}
        check(path.name + '/no-duplicates', len(z.namelist()), len(set(z.namelist())))
        check(path.name + '/complete-members', sorted(z.namelist()), sorted(expected))
        actual_original_paths = sorted(str(p.relative_to(original)) for p in original.rglob('*') if p.is_file())
        check(path.name + '/complete-original-directory', sorted(z.namelist()), actual_original_paths)
        for info in z.infolist():
            name = path.name + '/' + info.filename
            check(name + '/safe-relative-path', not info.filename.startswith('/') and '..' not in Path(info.filename).parts)
            data = z.read(info)
            member = expected[info.filename]
            check(name + '/member-bytes', len(data), member['bytes'])
            check(name + '/member-sha256', 'sha256:' + digest(data), member['sha256'])
            source = original / info.filename
            check(name + '/original-bytes', data, source.read_bytes())
            check(name + '/native-mode', stat.S_IMODE(info.external_attr >> 16), stat.S_IMODE(source.stat().st_mode))

batch_root = args.preflight / 'new-control-artifacts01'
batch = load(batch_root / 'RESULT.json')
physics = {c['id']: c for c in load(args.freeze / 'physics-cases.json')['cases']}
check('baseline/actual-original-status', batch['status'], 'failed')
check('baseline/exact-predecessor-commit', batch['source_commit'], '7b6900baa0357ab96c4639ac5c2ebe4e1791833e')
check('baseline/no-candidate-runtime', batch['candidate_torque_imported'], False)
check('baseline/no-derived-torque-oracles', batch['torque_expected_answers_derived'], False)
check('baseline/all-case-membership', sorted(c['id'] for c in batch['cases']), sorted(physics))
check('baseline/original-inputs-unchanged', batch['original_input_bytes_modes_unchanged'])
check('baseline/snapshot-inputs-unchanged', batch['snapshot_input_bytes_modes_unchanged'])

input_ids = load(batch_root / 'input-identities.json')
for name, ident in input_ids.items():
    check('baseline/input-snapshot/' + name, identity(batch_root / 'inputs' / name), ident)
    check('baseline/current-frozen-input/' + name, identity(args.freeze / name), ident)

def float_rows(value, prefix=''):
    result = []
    if type(value) is float:
        result.append({'pointer': prefix, 'hex': value.hex(),
                       'bits': struct.pack('>d', value).hex()})
    elif isinstance(value, list):
        for i, child in enumerate(value):
            result.extend(float_rows(child, prefix + '/' + str(i)))
    elif isinstance(value, dict):
        for key, child in sorted(value.items()):
            escaped = key.replace('~', '~0').replace('/', '~1')
            result.extend(float_rows(child, prefix + '/' + escaped))
    return result

def unpack_glb(raw):
    magic, version, size = struct.unpack_from('<4sII', raw)
    assert magic == b'glTF' and version == 2 and size == len(raw)
    offset = 12
    chunks = []
    while offset < len(raw):
        n, kind = struct.unpack_from('<I4s', raw, offset)
        assert n % 4 == 0
        data = raw[offset + 8:offset + 8 + n]
        assert len(data) == n
        chunks.append((kind, data))
        offset += 8 + n
    assert offset == len(raw) and [x[0] for x in chunks] == [b'JSON', b'BIN\0']
    return json.loads(chunks[0][1]), chunks[1][1]

def streams(document, binary):
    def view(index):
        spec = document['bufferViews'][index]
        start = spec.get('byteOffset', 0)
        raw = binary[start:start + spec['byteLength']]
        assert len(raw) == spec['byteLength']
        return {'buffer_view': index, 'specification': spec, 'bytes': len(raw), 'sha256': digest(raw)}
    def accessor(index):
        spec = document['accessors'][index]
        return {'accessor': index, 'specification': spec, 'view': view(spec['bufferView'])}
    meshes = []
    for mesh_index, mesh in enumerate(document['meshes']):
        for primitive_index, primitive in enumerate(mesh['primitives']):
            incoming = dict(primitive['attributes'])
            if 'indices' in primitive:
                incoming['INDICES'] = primitive['indices']
            meshes.append({'mesh': mesh_index, 'primitive': primitive_index,
                           'material': primitive.get('material'), 'mode': primitive.get('mode', 4),
                           'streams': {k: accessor(v) for k, v in sorted(incoming.items())}})
    images = [{'image': i, 'mime_type': image.get('mimeType'), 'view': view(image['bufferView'])}
              for i, image in enumerate(document.get('images', []))]
    return meshes, images

failed = []
float_count = 0
accepted = 0
for case in batch['cases']:
    key = case['id']
    original = physics[key]['predecessor_control']
    p = batch_root / 'cases' / key
    check(key + '/program-revision', case['program_revision'], original['identity']['program_revision'])
    check(key + '/sample-sides', case['sample_sides'], ['before', 'after'])
    # Baseline common clocks include the literal table AND all torque/force
    # boundaries inside the source horizon, including otherwise neutral ones.
    horizon = Fraction(physics[key]['horizon'])
    expected_clocks = {Fraction(x[0]) for x in physics[key]['samples']} | {Fraction(0), horizon}
    for interval in physics[key].get('torques', []) + physics[key].get('forces', []):
        start = Fraction(float(Fraction(interval['start'])))
        end = start + Fraction(float(Fraction(interval['duration'])))
        expected_clocks.update(t for t in (start, end) if 0 <= t <= horizon)
    check(key + '/clock-count', len(case['sample_times_seconds']), len(expected_clocks))
    check(key + '/exact-common-clocks', [Fraction(x) for x in case['sample_times_seconds']],
          sorted(expected_clocks))
    for evaluation in case['evaluations']:
        side = evaluation['side']
        states = load(p / (side + '-states.json'))
        check(key + '/' + side + '/valid', states['outcome'], 'valid')
        check(key + '/' + side + '/state-identity', identity(p / (side + '-states.json')), evaluation['states'])
        check(key + '/' + side + '/float-table-identity', identity(p / (side + '-binary64.json')), evaluation['binary64'])
        check(key + '/' + side + '/exact-clocks', [Fraction(s['time_seconds']) for s in states['samples']],
              [Fraction(x) for x in case['sample_times_seconds']])
        check(key + '/' + side + '/exact-side', {s['side'] for s in states['samples']}, {side})
        floats = float_rows(states)
        float_count += len(floats)
        check(key + '/' + side + '/every-binary64-field', floats, load(p / (side + '-binary64.json')))
    report = load(p / 'export-report.json')
    budget = report['execution_budget']
    check(key + '/original-default-source-budget', budget['source_request'], {'max_elapsed_ms': 30000, 'max_operations': 100000})
    check(key + '/original-default-host-budget', budget['host_ceilings'], {'max_elapsed_ms': 30000, 'max_operations': 100000})
    if case['export_has_bytes']:
        accepted += 1
        check(key + '/accepted', case['status'], 'passed')
        check(key + '/complete-GLB-identity', identity(p / 'original.glb'), case['glb'])
        raw = (p / 'original.glb').read_bytes()
        document, binary = unpack_glb(raw)
        supplied = load(p / 'glb-stream-identities.json')
        check(key + '/complete-JSON-document', document, supplied['document'])
        check(key + '/complete-BIN-sha256', digest(binary), supplied['binary_sha256'])
        check(key + '/complete-BIN-length', len(binary), supplied['binary_bytes'])
        meshes, images = streams(document, binary)
        check(key + '/complete-mesh-streams', meshes, supplied['mesh_streams'])
        check(key + '/complete-image-streams', images, supplied['images'])
        for table in ('materials', 'textures', 'samplers'):
            check(key + '/complete-' + table, document.get(table, []), supplied[table])
        check(key + '/literal-image-bytes', {image['view']['sha256'] for image in images},
              {digest((args.freeze / 'assets/label.png').read_bytes())})
        if case.get('repeat_glb'):
            check(key + '/actual-complete-repeat', (p / 'repeat.glb').read_bytes(), raw)
            check(key + '/repeat-receipt', case['repeat_complete_bytes_equal'])
    else:
        failed.append(key)
        check(key + '/failed-not-relabelled', case['status'], 'failed')
        check(key + '/absent-accepted-artifact', (p / 'original.glb').exists(), False)
        diagnostic = report['diagnostics'][0]
        if key != 'p28-release-then-torque':
            check(key + '/actual-operation-refusal', diagnostic['code'], 'OKL-E-RESOURCE')
            check(key + '/actual-cap-consumption', (budget['effective']['max_operations'], budget['consumed_operations']), (100000, 100001))
            check(key + '/actual-refusal-stage', budget['stage'], 'recording_export_readback')
        else:
            check(key + '/actual-spin-refusal', diagnostic['details']['export_code'], 'OKE-E-INDEPENDENT-VALIDATION')
            check(key + '/actual-spin-message', 'Independent spin norm is unresolved' in diagnostic['message'])
check('baseline/27-actual-artifacts', accepted, 27)
check('baseline/four-original-refusals', set(failed), {'p03-braking-reversal', 'p19-torque-then-impulse', 'p20-impulse-then-torque', 'p28-release-then-torque'})

result = {'schema_version': 'ontokin.independent-corpus-predecessor-review/1',
          'outcome': 'passed' if all(r['passed'] for r in rows) else 'failed',
          'checks': len(rows), 'binary64_fields_reconstructed': float_count,
          'archive_index_identity': identity(archive_index_path),
          'actual_artifact_batch_identity': identity(batch_root / 'RESULT.json'),
          'script_sha256': digest(Path(__file__).read_bytes()),
          'production_imported_or_executed': False, 'candidate_output_used': False,
          'runtime_or_release_acceptance': False,
          'failures': [r for r in rows if not r['passed']], 'rows': rows}
args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
raise SystemExit(0 if result['outcome'] == 'passed' else 1)
