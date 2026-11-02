#!/usr/bin/env python3
"""Independent C090 recording schema probes; no OntoKin implementation imports."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import gzip
import hashlib
import importlib.metadata
import json
import platform
import shutil
import stat
import sys

AUTHOR = Path('/workspace/scratch/05c3f95a49c1/c090-recording')
ROOT = Path('/workspace/scratch/05c3f95a49c1/c089-recovery/OntoKin')
BASELINE = Path('/workspace/scratch/05c3f95a49c1/c090-predecessor')
OUTPUT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews')
SNAPSHOT = OUTPUT / 'recording-schema-review-01-inputs'
PREFIX = Path('docs/language-design/torque-v0.1')
sys.path.insert(0, '/workspace/scratch/05c3f95a49c1/c090-preflight/verification-packages')
from jsonschema import Draft202012Validator


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def pointer(value, path):
    for part in path.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def set_value(value, path, replacement=None, deletion=False):
    parent, key = path.rsplit('/', 1)
    owner = pointer(value, parent)
    key = key.replace('~1', '/').replace('~0', '~')
    if isinstance(owner, list):
        key = int(key)
    if deletion:
        del owner[key]
    else:
        owner[key] = replacement


def main():
    assert not SNAPSHOT.exists()
    SNAPSHOT.mkdir()
    names = [
        'recording-profile.schema.json', 'recording-quantization.schema.json',
        'RECORDING.md', 'recording/AMENDMENT-02.json',
        'recording/SCHEMA-DERIVATION-CHECKS-02.json',
    ]
    # The author's second derivation receipt filename is discovered only by an
    # explicit bounded name inventory, not by taking the most recent arbitrary file.
    if not (AUTHOR / PREFIX / names[-1]).exists():
        names.remove(names[-1])
    files = []
    for name in names:
        rel = PREFIX / name
        source = AUTHOR / rel
        target = SNAPSHOT / rel
        assert source.is_file() and not source.is_symlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(stat.S_IMODE(source.stat().st_mode))
        files.append({'path': str(rel), 'bytes': source.stat().st_size,
                      'mode': format(stat.S_IMODE(source.stat().st_mode), '04o'),
                      'sha256': sha(source)})
    save(SNAPSHOT / 'INPUTS.json', files)
    schemas = {name: read(SNAPSHOT / PREFIX / (name + '.schema.json'))
               for name in ('recording-profile', 'recording-quantization')}
    inherited_ids = set()
    for path in (BASELINE / 'docs/language-design').rglob('*.schema.json'):
        schema = read(path)
        if '$id' in schema:
            inherited_ids.add(schema['$id'])
    collisions = [s['$id'] for s in schemas.values() if s['$id'] in inherited_ids]
    validators = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema)
    profile = {
        'schema_version': 'ontokin.torque-recording/0.1',
        'source_profile': 'torque-0.1',
        'motion_model': 'finite_cartesian_world_axis_external_couple_on_free_own_sphere',
        'axis_domain': ['world_x', 'world_y', 'world_z'],
        'descendants': 'fixed_rigid_massless_visual_markers',
        'transform_policy': 'all_nodes_are_roots_with_baked_world_poses',
        'quantization_contract': 'ontokin.torque-quantization/0.1',
        'live_solver_embedded': False,
    }
    basis = {'name': 'synthetic-static-shape-control', 'version': '0',
             'implementation_sha256': 'sha256:' + '1' * 64,
             'method': 'Schema probe only; no observed implementation or physical attestation.',
             'derivation_sha256': 'sha256:' + '2' * 64}
    one = {'numerator': '1', 'denominator': '1'}
    zero = {'numerator': '0', 'denominator': '1'}
    interval = {
        'left_key_index': 0, 'right_key_index': 1,
        'carrier': {'path': 'ball', 'element_id': ['synthetic', 'demo', 'ball']},
        'source_phase_indices': [0], 'h_authored_seconds': one,
        'h_stored_seconds': one, 'landmark_radius_m': 1.0,
        'angular_speed_bound_rad_per_s': 0.0,
        'angular_acceleration_bound_rad_per_s2': 0.0,
        'carrier_acceleration_bound_m_per_s2': 0.0,
        'enclosing_carrier_speed_bound_m_per_s': 0.0,
        'enclosing_carrier_acceleration_bound_m_per_s2': 0.0,
        'carrier_position_bound_m': 0.0,
        'enclosing_angular_speed_bound_rad_per_s': 0.0,
        'enclosing_angular_acceleration_bound_rad_per_s2': 0.0,
        'max_endpoint_time_shift_s': 0.0,
        'max_endpoint_position_error_m': 0.0,
        'max_endpoint_unit_quaternion_error': 0.0,
        'stored_quaternion_arc_upper_rad': 0.0,
        'source_numeric_position_bound_m': 0.0,
        'source_numeric_rotation_bound_rad': 0.0,
        'destination_numeric_position_bound_m': 0.0,
        'destination_numeric_rotation_bound_rad': 0.0,
        'local_vertex_error_bound_m': 0.0,
        'ideal_position_bound_m': 0.0,
        'ideal_rotation_bound_rad': 0.0,
        'unit_quaternion_difference_bound': 0.0,
        'total_position_bound_m': 0.0,
        'total_rotation_bound_rad': 0.0,
    }
    quantization = {
        'schema_version': 'ontokin.torque-quantization/0.1',
        'rotation_interpolation': 'shortest_arc_slerp',
        'clock_conversion': 'binary32_rne_ties_to_even_from_exact_rational',
        'position_tolerance_m': .001, 'rotation_tolerance_rad': .001,
        'time_tolerance_s': .000001,
        'source_numeric_bound_basis': basis,
        'destination_numeric_bound_basis': basis,
        'retained_keys': [
            {'authored_seconds': zero, 'stored_seconds': 0.0,
             'stored_binary32_bits': '00000000', 'semantic_boundary': True},
            {'authored_seconds': one, 'stored_seconds': 1.0,
             'stored_binary32_bits': '3f800000', 'semantic_boundary': True},
        ],
        'interval_certificates': [interval],
        'all_values_independently_recomputed': True,
        'unknown_error_bound_policy': 'reject',
        'certificate_scope': 'specified source and supplied bytes; separately identified destination numeric behavior',
    }
    # A wire JSON document has no shared mutable object aliases. Detach reused
    # literal helpers so that each hostile pointer changes exactly one field.
    quantization = json.loads(json.dumps(quantization, allow_nan=False))
    rows, payloads = [], []

    def check(name, family, payload, expected_valid):
        errors = list(validators[family].iter_errors(payload))
        actual = not errors
        raw = json.dumps(payload, separators=(',', ':'), sort_keys=True, allow_nan=False).encode()
        rows.append({'id': name, 'family': family, 'expected_valid': expected_valid,
                     'actual_valid': actual, 'passed': actual == expected_valid,
                     'payload_sha256': hashlib.sha256(raw).hexdigest(),
                     'errors': [{'instance_path': list(e.absolute_path),
                                 'schema_path': list(e.absolute_schema_path),
                                 'message': e.message[:1200]} for e in errors[:8]]})
        payloads.append({'id': name, 'family': family,
                         'expected_valid': expected_valid, 'payload': payload})

    check('complete-profile-positive', 'recording-profile', profile, True)
    check('complete-quantization-positive', 'recording-quantization', quantization, True)
    for family, prototype in [('recording-profile', profile), ('recording-quantization', quantization)]:
        for key in prototype:
            payload = copy.deepcopy(prototype)
            del payload[key]
            check(f'{family}-missing-{key}', family, payload, False)
        check(f'{family}-extra-top-field', family, {**prototype, 'unreviewed': 0}, False)
    for key in profile:
        payload = copy.deepcopy(profile)
        payload[key] = 'wrong'
        check('profile-incorrect-' + key, 'recording-profile', payload, False)
    payload = copy.deepcopy(profile)
    payload['axis_domain'] = ['world.x', 'world.y', 'world.z']
    check('profile-dotted-axis-spelling-refused', 'recording-profile', payload, False)
    for key in interval:
        payload = copy.deepcopy(quantization)
        del payload['interval_certificates'][0][key]
        check('interval-missing-' + key, 'recording-quantization', payload, False)
        if type(interval[key]) in (int, float):
            payload = copy.deepcopy(quantization)
            payload['interval_certificates'][0][key] = True
            check('interval-bool-' + key, 'recording-quantization', payload, False)
            payload = copy.deepcopy(quantization)
            payload['interval_certificates'][0][key] = -1
            check('interval-negative-' + key, 'recording-quantization', payload, False)
    nested_paths = [
        '/source_numeric_bound_basis', '/destination_numeric_bound_basis',
        '/retained_keys/0', '/retained_keys/0/authored_seconds',
        '/interval_certificates/0', '/interval_certificates/0/carrier',
        '/interval_certificates/0/h_authored_seconds',
        '/interval_certificates/0/h_stored_seconds',
    ]
    for path in nested_paths:
        payload = copy.deepcopy(quantization)
        pointer(payload, path)['unreviewed'] = 0
        check('closed-nested-' + path, 'recording-quantization', payload, False)
        for key in pointer(quantization, path):
            payload = copy.deepcopy(quantization)
            del pointer(payload, path)[key]
            check('nested-missing-' + path + '/' + key, 'recording-quantization', payload, False)
    hostile = [
        ('zero-position-tolerance', '/position_tolerance_m', 0),
        ('zero-rotation-tolerance', '/rotation_tolerance_rad', 0),
        ('zero-time-tolerance', '/time_tolerance_s', 0),
        ('time-tolerance-over-cap', '/time_tolerance_s', .000002),
        ('bool-position-tolerance', '/position_tolerance_m', True),
        ('bad-source-digest', '/source_numeric_bound_basis/implementation_sha256', 'sha256:bad'),
        ('missing-source-basis-name', '/source_numeric_bound_basis/name', ''),
        ('bad-destination-digest', '/destination_numeric_bound_basis/derivation_sha256', 'sha256:' + 'G'*64),
        ('empty-retained-keys', '/retained_keys', []),
        ('bad-clock-bits', '/retained_keys/0/stored_binary32_bits', 'x0000000'),
        ('bool-clock', '/retained_keys/0/stored_seconds', True),
        ('negative-clock', '/retained_keys/0/stored_seconds', -1),
        ('nonbool-boundary', '/retained_keys/0/semantic_boundary', 1),
        ('zero-rational-denominator', '/retained_keys/0/authored_seconds/denominator', '0'),
        ('signed-zero-rational', '/retained_keys/0/authored_seconds/numerator', '-0'),
        ('negative-rational', '/interval_certificates/0/h_authored_seconds/numerator', '-1'),
        ('leading-zero-rational', '/interval_certificates/0/h_stored_seconds/denominator', '01'),
        ('rational-native-number', '/interval_certificates/0/h_stored_seconds/numerator', 1),
        ('empty-occurrence-path', '/interval_certificates/0/carrier/path', ''),
        ('empty-occurrence-id', '/interval_certificates/0/carrier/element_id', []),
        ('too-large-left-index', '/interval_certificates/0/left_key_index', 9999),
        ('too-large-right-index', '/interval_certificates/0/right_key_index', 10000),
        ('empty-source-phases', '/interval_certificates/0/source_phase_indices', []),
        ('duplicate-source-phases', '/interval_certificates/0/source_phase_indices', [0, 0]),
        ('bool-source-phase', '/interval_certificates/0/source_phase_indices', [True]),
        ('too-large-source-phase', '/interval_certificates/0/source_phase_indices', [100000]),
        ('too-large-unit-quaternion-error', '/interval_certificates/0/unit_quaternion_difference_bound', .500001),
        ('too-large-stored-arc', '/interval_certificates/0/stored_quaternion_arc_upper_rad', .8),
        ('wrong-interpolator', '/rotation_interpolation', 'nlerp'),
        ('wrong-clock-conversion', '/clock_conversion', 'epsilon_rounding'),
        ('unverified-values', '/all_values_independently_recomputed', False),
        ('unknown-bound-accepted', '/unknown_error_bound_policy', 'accept'),
    ]
    for name, path, value in hostile:
        payload = copy.deepcopy(quantization)
        set_value(payload, path, value)
        check(name, 'recording-quantization', payload, False)
    semantic = [
        ('unreduced-rational', '/interval_certificates/0/h_authored_seconds', {'numerator': '2', 'denominator': '2'}),
        ('stored-clock-bits-disagree', '/retained_keys/1/stored_binary32_bits', '00000000'),
        ('wrong-total-bound', '/interval_certificates/0/source_numeric_position_bound_m', 1.0),
        ('interval-key-not-in-key-array', '/interval_certificates/0/right_key_index', 99),
        ('unresolved-source-phase', '/interval_certificates/0/source_phase_indices', [99]),
    ]
    for name, path, value in semantic:
        payload = copy.deepcopy(quantization)
        set_value(payload, path, value)
        check('semantic-reader-required-' + name, 'recording-quantization', payload, True)
    with (OUTPUT / 'recording-schema-review-01-synthetic-payloads.jsonl.gz').open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as compressed:
            for row in payloads:
                compressed.write(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n')
    result = {
        'schema_version': 'ontokin.c090-independent-recording-schema-review/1',
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Synthetic complete metadata and hostile schema probes only; no physical certificate, artifact, destination execution or production import',
        'status': 'passed' if not collisions and all(r['passed'] for r in rows) else 'failed',
        'new_schemas_checked': len(schemas), 'namespace_collisions': collisions,
        'passed_checks': sum(r['passed'] for r in rows),
        'failed_checks': sum(not r['passed'] for r in rows),
        'checks': rows,
        'semantic_reader_still_required': [name for name, _, _ in semantic] + [
            'finite native numbers and exact binary32 conversion', 'current implementation/derivation/source identities',
            'full per-interval proof inequalities', 'source graph and radius derivations',
            'supplied GLB bytes and independent destination numerical evidence'],
        'input_files': files, 'snapshot_unchanged': all(sha(SNAPSHOT / r['path']) == r['sha256'] for r in files),
        'author_inputs_unchanged': all(sha(AUTHOR / r['path']) == r['sha256'] for r in files),
        'root_files_equal_snapshot': {r['path']: (ROOT / r['path']).exists() and sha(ROOT / r['path']) == r['sha256'] for r in files},
        'driver_sha256': sha(Path(__file__)), 'python': sys.version, 'platform': platform.platform(),
        'jsonschema': importlib.metadata.version('jsonschema'),
    }
    save(OUTPUT / 'recording-schema-review-01-probes.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'passed_checks', 'failed_checks', 'namespace_collisions', 'snapshot_unchanged', 'author_inputs_unchanged')}, sort_keys=True))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
