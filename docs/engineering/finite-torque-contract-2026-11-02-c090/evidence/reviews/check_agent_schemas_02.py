#!/usr/bin/env python3
"""Independent schema-only C090 review; imports no OntoKin implementation."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import gzip
import hashlib
import importlib.metadata
import json
import platform
import sys

ROOT = Path('/workspace/scratch/05c3f95a49c1/c089-recovery/OntoKin')
BASELINE = Path('/workspace/scratch/05c3f95a49c1/c090-predecessor')
SNAPSHOT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews/agent-review-01-inputs')
OUTPUT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews')
TRANSCRIPT = Path('/workspace/scratch/05c3f95a49c1/c090-preflight/membership-agent/agent/transcript.json')
sys.path.insert(0, '/workspace/scratch/05c3f95a49c1/c090-preflight/verification-packages')
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


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


def mutate(value, path, replacement=None, delete=False):
    parent, key = path.rsplit('/', 1)
    item = pointer(value, parent)
    key = key.replace('~1', '/').replace('~0', '~')
    if isinstance(item, list):
        key = int(key)
    if delete:
        del item[key]
    else:
        item[key] = replacement


def base_leaves_preserved(old, new, changes, path=''):
    failures = []
    if path in changes:
        row = changes[path]
        if old != row['before'] or new != row['after']:
            failures.append(path + ': documented scalar change differs')
    elif isinstance(old, dict):
        if not isinstance(new, dict):
            failures.append(path + ': object changed type')
        else:
            for key, value in old.items():
                child = path + '/' + key.replace('~', '~0').replace('/', '~1')
                if key not in new:
                    failures.append(child + ': inherited key removed')
                else:
                    failures += base_leaves_preserved(value, new[key], changes, child)
    elif isinstance(old, list):
        if not isinstance(new, list) or len(new) < len(old):
            failures.append(path + ': inherited array shortened or changed type')
        else:
            for index, value in enumerate(old):
                failures += base_leaves_preserved(value, new[index], changes, path + '/' + str(index))
    elif old != new:
        failures.append(path + ': undocumented inherited scalar change')
    return failures


def main():
    inputs = read(SNAPSHOT / 'INPUTS.json')
    assert all(sha(SNAPSHOT / r['path']) == r['sha256'] for r in inputs)
    schemas = {name: read(SNAPSHOT / ('docs/language-design/agent-v0.22/' + name + '.schema.json'))
               for name in ('request', 'response', 'diagnostic')}
    schemas['torques'] = read(SNAPSHOT / 'docs/language-design/torque-v0.1/torques.schema.json')
    schemas['catalog'] = read(SNAPSHOT / 'docs/language-design/torque-v0.1/catalog.schema.json')
    empty = read(SNAPSHOT / 'docs/language-design/torque-v0.1/torques-empty.example.json')
    catalog = read(SNAPSHOT / 'docs/language-design/torque-v0.1/catalog.example.json')
    pool = {}
    for path in sorted((BASELINE / 'docs/language-design').rglob('*.schema.json'), key=lambda p: (len(p.parts), str(p))):
        document = read(path)
        if '$id' in document and document['$id'] not in pool:
            pool[document['$id']] = (document, path)
    inherited_ids = set(pool)
    namespace_collisions = [schema['$id'] for schema in schemas.values() if schema['$id'] in inherited_ids]
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        pool[schema['$id']] = (schema, SNAPSHOT / name)
    registry = Registry().with_resources((key, Resource.from_contents(document)) for key, (document, _) in pool.items())
    validators = {name: Draft202012Validator(schema, registry=registry) for name, schema in schemas.items()}
    rows = []
    payloads = []
    def check(name, validator, payload, expected_valid):
        errors = list(validator.iter_errors(payload))
        actual = not errors
        rows.append({'id': name, 'expected_valid': expected_valid, 'actual_valid': actual,
            'passed': actual == expected_valid,
            'payload_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'errors': [{'instance_path': list(e.absolute_path), 'schema_path': list(e.absolute_schema_path),
                        'message': e.message[:1500]} for e in errors[:8]]})
        payloads.append({'id': name, 'payload': payload, 'expected_valid': expected_valid})
    check('empty-torque-positive', validators['torques'], empty, True)
    check('catalog-positive', validators['catalog'], catalog, True)
    source_location = {'source_id': 'entry', 'source_revision': 'sha256:' + '1' * 64,
                       'start_byte': 100, 'end_byte': 200}
    interval = {'torque_key': 'drive', 'torque_element_id': ['synthetic', 'demo', 'torque', 'drive'],
        'target_path': 'ball', 'target_element_id': ['synthetic', 'demo', 'ball'],
        'program_revision': 'sha256:' + '2' * 64, 'source_location': source_location,
        'operand_location': {**source_location, 'start_byte': 160, 'end_byte': 166},
        'duration_location': {**source_location, 'start_byte': 180, 'end_byte': 184},
        'sequence_index': 0, 'activation_time_seconds': '0', 'duration_seconds': '0.5',
        'completion_time_seconds': '0.5', 'axis': 'world_z', 'torque_n_m': 0.0}
    zero = {'numerator': '0', 'denominator': '1'}
    latched = copy.deepcopy(empty)
    latched.update(active=[interval], axis='world_z', angular_acceleration_rad_per_s2=0.0,
        signed_angular_speed_rad_per_s=1.0, angular_acceleration_reference_rad_per_s2=zero,
        angular_error_bound_rad=zero, angular_speed_error_bound_rad_per_s=zero,
        started_count=1, last_change_time_seconds='0', last_changes=[{**interval, 'kind': 'started'}])
    split = copy.deepcopy(latched)
    split.update(rotation_route='split', rotation_anchor_seconds='0.25', phase_since_anchor_rad=-0.125,
                 angular_acceleration_rad_per_s2=2.0,
                 angular_acceleration_reference_rad_per_s2={'numerator': '2', 'denominator': '1'})
    check('latched-zero-positive', validators['torques'], latched, True)
    check('split-positive', validators['torques'], split, True)
    for name, prototype, path, value, deletion in [
        ('missing-axis', split, '/axis', None, True),
        ('missing-new-counter', split, '/started_count', None, True),
        ('invalid-axis', split, '/axis', 'world_y_negative', False),
        ('invalid-route', split, '/rotation_route', 'other', False),
        ('split-null-axis', split, '/axis', None, False),
        ('split-null-anchor', split, '/rotation_anchor_seconds', None, False),
        ('legacy-nonnull-anchor', latched, '/rotation_anchor_seconds', '0', False),
        ('unlatched-nonzero-count', empty, '/started_count', 1, False),
        ('unlatched-active-record', empty, '/active', [interval], False),
        ('latched-missing-history', latched, '/last_changes', [], False),
        ('bool-as-speed', split, '/signed_angular_speed_rad_per_s', True, False),
        ('counter-over-cap', split, '/completed_count', 100001, False),
        ('extra-state-field', split, '/unreviewed', 1, False),
        ('extra-record-field', split, '/active/0/unreviewed', 1, False),
        ('extra-source-location-field', split, '/active/0/source_location/unreviewed', 1, False),
        ('extra-rational-field', split, '/angular_error_bound_rad/unreviewed', 1, False),
        ('missing-record-location', split, '/active/0/operand_location', None, True),
        ('bad-source-digest', split, '/active/0/source_location/source_revision', 'sha256:bad', False),
        ('bad-interval-id-family', split, '/active/0/torque_element_id/2', 'force', False),
        ('bad-time-string', split, '/active/0/completion_time_seconds', '1/3', False),
        ('negative-rational-denominator', split, '/angular_error_bound_rad/denominator', '-1', False),
        ('negative-error-bound', split, '/angular_error_bound_rad/numerator', '-1', False),
    ]:
        payload = copy.deepcopy(prototype)
        mutate(payload, path, value, deletion)
        check(name, validators['torques'], payload, False)
    for field in catalog:
        payload = copy.deepcopy(catalog)
        del payload[field]
        check('catalog-missing-' + field, validators['catalog'], payload, False)
    payload = {**catalog, 'unreviewed': True}
    check('catalog-extra-field', validators['catalog'], payload, False)
    mapping = {'ontokin.agent/0.21': 'ontokin.agent/0.22',
               'keyed-membership-0.1': 'torque-0.1', 'ontokin.glb/0.21': 'ontokin.glb/0.22'}
    def adapt(value):
        if isinstance(value, list):
            return [adapt(child) for child in value]
        if isinstance(value, dict):
            result = {key: adapt(child) for key, child in value.items()}
            if all(key in value for key in ('impulses', 'pose_authority', 'forces')):
                result['torques'] = copy.deepcopy(empty)
            if result.get('kind') == 'object' and 'source' in result:
                result['source']['torque_intervals'] = []
            if result.get('operation') == 'discover' and result.get('status') == 'succeeded':
                result['result']['torque_interface'] = copy.deepcopy(catalog)
            return result
        return mapping.get(value, value) if type(value) is str else value
    transcript = read(TRANSCRIPT)
    examples = {}
    operation_counts = {}
    for item in transcript:
        request = adapt(item['request'])
        response = adapt(item['response']) if 'response' in item else None
        operation = request['operation']
        operation_counts[operation] = operation_counts.get(operation, 0) + 1
        check(f'synthetic-request-{item["sequence"]:05d}-{operation}', validators['request'], request, True)
        if response is not None:
            check(f'synthetic-response-{item["sequence"]:05d}-{operation}', validators['response'], response, True)
        if response is not None and response.get('status') == 'succeeded':
            examples.setdefault(operation, (request, response))
    discovery = copy.deepcopy(examples['discover'][1])
    del discovery['result']['torque_interface']
    check('discovery-missing-torque-interface', validators['response'], discovery, False)
    discovery = copy.deepcopy(examples['discover'][1])
    discovery['result']['torque_interface']['unreviewed'] = 0
    check('discovery-extra-torque-interface-field', validators['response'], discovery, False)
    for item in transcript:
        if 'response' not in item or item['request']['operation'] != 'inspect' or item['response']['status'] != 'succeeded':
            continue
        response = adapt(item['response'])
        for index, node in enumerate(response.get('result', {}).get('items', [])):
            if node.get('kind') == 'object' and 'source' in node:
                missing = copy.deepcopy(response)
                del missing['result']['items'][index]['source']['torque_intervals']
                check('resolved-object-source-missing-intervals', validators['response'], missing, False)
                extra = copy.deepcopy(response)
                extra['result']['items'][index]['source']['torque_intervals'] = [{**interval, 'unreviewed': 0}]
                check('resolved-object-source-extra-interval-field', validators['response'], extra, False)
                break
        else:
            continue
        break
    for item in transcript:
        if 'response' not in item:
            continue
        response = adapt(item['response'])
        state = response.get('result', {}).get('initial_state') if isinstance(response.get('result'), dict) else None
        if state and state.get('objects'):
            key = next(iter(state['objects']))
            missing = copy.deepcopy(response)
            del missing['result']['initial_state']['objects'][key]['torques']
            check('initial-state-missing-torques', validators['response'], missing, False)
            break
    for operation in sorted(examples):
        request = copy.deepcopy(examples[operation][0])
        request['schema_version'] = 'ontokin.agent/0.21'
        check('request-old-protocol-' + operation, validators['request'], request, False)
    request = copy.deepcopy(examples['artifact'][0])
    for suffix, field, value in [('bool-offset', 'offset', True), ('negative-offset', 'offset', -1),
                                 ('zero-chunk', 'max_bytes', 0), ('over-chunk', 'max_bytes', 65537)]:
        bad = {**request, field: value}
        check('artifact-' + suffix, validators['request'], bad, False)
    semantic_examples = []
    for name, path, value in [('rational-unreduced', '/angular_error_bound_rad', {'numerator': '2', 'denominator': '4'}),
                              ('active-count-mismatch', '/completed_count', 10),
                              ('interval-end-arithmetic-mismatch', '/active/0/completion_time_seconds', '0.75')]:
        payload = copy.deepcopy(split)
        mutate(payload, path, value)
        check('documented-semantic-check-' + name, validators['torques'], payload, True)
        semantic_examples.append({'id': name, 'schema_acceptance_expected': True,
            'independent_semantic_reader_must_reject': True})
    derivation = read(SNAPSHOT / 'docs/language-design/agent-v0.22/SCHEMA-DERIVATION.json')
    derivation_results = []
    for row in derivation['files']:
        original_path = BASELINE / row['baseline_path']
        new_path = SNAPSHOT / 'docs/language-design/agent-v0.22' / row['path']
        changes = {change['path']: change for change in row['scalar_changes']}
        defects = base_leaves_preserved(read(original_path), read(new_path), changes)
        derivation_results.append({'file': row['path'], 'baseline_hash_matches': sha(original_path) == row['baseline_sha256'],
            'new_hash_matches': sha(new_path) == row['new_sha256'], 'listed_scalar_changes': len(changes),
            'unlisted_inherited_changes': defects})
    with (OUTPUT / 'agent-review-02-synthetic-payloads.jsonl.gz').open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as compressed:
            for row in payloads:
                compressed.write((json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode())
    result = {'schema_version': 'ontokin.c090-independent-agent-schema-review/1',
        'status': 'passed' if not namespace_collisions and all(r['passed'] for r in rows) and all(
            r['baseline_hash_matches'] and r['new_hash_matches'] and not r['unlisted_inherited_changes'] for r in derivation_results) else 'failed',
        'scope': 'Independent schema and inherited-structure verification; synthetic adapted transport controls only; no torque runtime execution',
        'recorded_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
        'platform': platform.platform(), 'jsonschema': importlib.metadata.version('jsonschema'),
        'referencing': importlib.metadata.version('referencing'), 'driver_sha256': sha(Path(__file__)),
        'input_files': inputs, 'baseline_transcript_sha256': sha(TRANSCRIPT), 'namespace_collisions': namespace_collisions,
        'adaptation': 'Exact protocol/profile/destination string substitutions, empty torque state on complete object states, empty source intervals on resolved object source projections, and published synthetic torque catalog. Source strings/physical values are not executed or reinterpreted.',
        'operation_counts': operation_counts, 'request_count': len(transcript),
        'actual_response_count': sum('response' in item for item in transcript),
        'no_response_records': [{key: item.get(key) for key in ('sequence', 'workflow', 'step', 'error')} for item in transcript if 'response' not in item], 'new_schemas_checked': len(schemas), 'derivation': derivation_results,
        'checks': rows, 'passed_checks': sum(r['passed'] for r in rows), 'failed_checks': sum(not r['passed'] for r in rows),
        'documented_semantic_checks': semantic_examples,
        'snapshot_unchanged': all(sha(SNAPSHOT / r['path']) == r['sha256'] for r in inputs),
        'current_inputs_still_match_snapshot': all(sha(ROOT / r['path']) == r['sha256'] for r in inputs)}
    save(OUTPUT / 'agent-review-02-probes.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'passed_checks', 'failed_checks', 'namespace_collisions', 'current_inputs_still_match_snapshot')}))
    for row in rows:
        if not row['passed']:
            print(row['id'], row['expected_valid'], row['actual_valid'], row['errors'][:1])
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
