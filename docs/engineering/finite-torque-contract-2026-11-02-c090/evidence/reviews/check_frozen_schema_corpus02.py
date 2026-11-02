#!/usr/bin/env python3
"""Independent frozen schema/request review; all request examples remain synthetic."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import copy
import gzip
import hashlib
import importlib.metadata
import json
import platform
import shutil
import stat
import sys

OUT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews')
SOURCE = Path('/workspace/scratch/05c3f95a49c1/c090-corpus/docs/language-design/torque-v0.1/freeze')
CONTRACT = Path('/workspace/scratch/05c3f95a49c1/c089-recovery/OntoKin')
BASELINE = Path('/workspace/scratch/05c3f95a49c1/c090-predecessor')
SNAPSHOT = OUT / 'corpus-schema-review02-inputs'
sys.path.insert(0, '/workspace/scratch/05c3f95a49c1/c090-preflight/verification-packages')
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def read(path):
    return json.loads(path.read_bytes())


def identity(path):
    return {'bytes': path.stat().st_size, 'mode': format(stat.S_IMODE(path.stat().st_mode), '04o'),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def walk(value, path=''):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + '/' + str(index))


def pointer(value, path):
    if path in ('', '/'):
        return value
    for part in path.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def parent(value, path):
    prefix, key = path.rsplit('/', 1)
    owner = pointer(value, prefix)
    key = key.replace('~1', '/').replace('~0', '~')
    return owner, int(key) if isinstance(owner, list) else key


def main():
    assert not SNAPSHOT.exists()
    SNAPSHOT.mkdir()
    paths = {'schema-cases.json', 'agent/transport-cases.json', 'agent/request-workflows.json', 'agent/resource-cases.json'}
    documents = {name: read(SOURCE / name) for name in paths}
    bundles = set()
    for document in documents.values():
        for _, node in walk(document):
            if set(node) == {'$bundle_file'}:
                bundles.add(node['$bundle_file'])
    for name in bundles:
        manifest = read(SOURCE / name)
        paths.add(name)
        paths.add(manifest['entry']['path'])
        paths.update(r['path'] for r in manifest['modules'])
        paths.update(r['path'] for r in manifest['assets'])
    inputs = []
    for name in sorted(paths):
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        source, target = SOURCE / name, SNAPSHOT / 'corpus' / name
        assert not source.is_symlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target);target.chmod(stat.S_IMODE(source.stat().st_mode))
        inputs.append({'origin': 'corpus', 'path': name, **identity(source)})
    schema_paths = {
        'state': (CONTRACT, 'docs/language-design/torque-v0.1/torques.schema.json'),
        'request': (CONTRACT, 'docs/language-design/agent-v0.22/request.schema.json'),
        'bundle': (BASELINE, 'docs/language-design/textured-surfaces-v0.1/bundle.schema.json'),
    }
    schemas = {}
    for family, (source_root, name) in schema_paths.items():
        source, target = source_root / name, SNAPSHOT / 'contract' / (family + '.schema.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target);target.chmod(stat.S_IMODE(source.stat().st_mode))
        inputs.append({'origin': 'contract', 'family': family, 'path': name, **identity(source)})
        schemas[family] = read(target)
        Draft202012Validator.check_schema(schemas[family])
    save(SNAPSHOT / 'INPUTS.json', inputs)
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas.values())
    validators = {k: Draft202012Validator(v, registry=registry) for k, v in schemas.items()}
    corpus = SNAPSHOT / 'corpus'
    rows, payloads = [], []
    placeholder_values = []

    def materialize(value, key=None, location=''):
        if isinstance(value, list):
            return [materialize(v, None, location + '/' + str(i)) for i, v in enumerate(value)]
        if not isinstance(value, dict):
            return value.replace('${index}', '0') if isinstance(value, str) else value
        if set(value) == {'$bundle_file'}:
            manifest = read(corpus / value['$bundle_file'])
            return {'schema_version': 'ontokin.bundle/0.2',
                    'entry': {'filename': manifest['entry']['filename'], 'source': (corpus / manifest['entry']['path']).read_bytes().decode('utf-8')},
                    'modules': [{**{k: m[k] for k in ('package_id', 'version', 'filename')},
                                 'source': (corpus / m['path']).read_bytes().decode('utf-8')} for m in manifest['modules']],
                    'assets': [{**{k: a[k] for k in ('asset_id', 'media_type', 'sha256')},
                                'data_base64': base64.b64encode((corpus / a['path']).read_bytes()).decode('ascii')} for a in manifest['assets']]}
        if len(value) == 1 and next(iter(value)) in ('$response', '$capture', '$loop'):
            replacement = 0 if key == 'offset' or '$loop' in value else 'synthetic-schema-probe-identifier'
            placeholder_values.append({'location': location, 'template': value, 'synthetic_replacement': replacement})
            return replacement
        return {k: materialize(v, k, location + '/' + k) for k, v in value.items()}

    def check(identifier, family, value, expected=True, category='schema'):
        errors = list(validators[family].iter_errors(value))
        actual = not errors
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        rows.append({'id': identifier, 'category': category, 'family': family,
                     'declared_expected_schema_accepts': expected, 'actual_schema_accepts': actual,
                     'passed': True if expected is None else actual == expected,
                     'payload_sha256': hashlib.sha256(raw).hexdigest(),
                     'errors': [{'instance_path': list(e.absolute_path), 'schema_path': list(e.absolute_schema_path),
                                 'message': e.message[:1400]} for e in errors[:6]]})
        payloads.append({'id': identifier, 'payload': value, 'schema_expected': expected})

    state = read(corpus / 'schema-cases.json')
    for name, value in state['prototypes'].items():
        check('state-prototype/' + name, 'state', value, state['prototype_expected_schema_accepts'][name])
    for case in state['cases']:
        value = copy.deepcopy(state['prototypes'][case['prototype']])
        owner, key = parent(value, case['path'])
        operation = case['operation']
        if operation == 'remove':
            del owner[key]
        elif operation == 'append-copy':
            owner.append(copy.deepcopy(owner[key]))
        elif operation in ('replace', 'add'):
            owner[key] = copy.deepcopy(case['value'])
        else:
            raise ValueError('Undeclared state mutation ' + operation)
        check('state-mutation/' + case['id'], 'state', value, case['expected_schema_accepts'])
    requests = {}
    operation_counts = {}
    workflow = read(corpus / 'agent/request-workflows.json')
    for scenario in workflow['scenarios']:
        for group in ('steps', 'then'):
            for step in scenario.get(group, []):
                if 'request' in step:
                    requests[scenario['id'] + '.' + step['step']] = step['request']
        if 'export_request' in scenario:
            requests[scenario['id'] + '.export'] = scenario['export_request']
    for filename in ('agent/request-workflows.json', 'agent/resource-cases.json'):
        document = read(corpus / filename)
        for path, node in walk(document):
            if node.get('schema_version') == 'ontokin.agent/0.22' and 'operation' in node:
                concrete = materialize(node, location=filename + path)
                operation_counts[concrete['operation']] = operation_counts.get(concrete['operation'], 0) + 1
                check('request-template/' + filename + path, 'request', concrete)
    references = []
    for path, node in walk(workflow):
        if 'request_ref' in node and 'step' in node:
            name = node['request_ref']
            assert name in requests, 'Unresolved request_ref: ' + name
            value = copy.deepcopy(requests[name])
            value.update(copy.deepcopy(node.get('overrides', {})))
            concrete = materialize(value, location='request_ref' + path)
            check('request-reuse/' + path, 'request', concrete)
            references.append({'path': path, 'request_ref': name, 'overrides': node.get('overrides', {})})
    transport = read(corpus / 'agent/transport-cases.json')
    transport_results = []
    for case in transport['cases']:
        value = materialize(case['base_request'], location='transport/' + case['id'])
        check('transport-base/' + case['id'], 'request', value)
        value = copy.deepcopy(value)
        mutation = case['mutation']
        if mutation in ('replace', 'append'):
            owner, key = parent(value, case['path'])
            owner[key] = copy.deepcopy(case['value']) if mutation == 'replace' else owner[key] + case['value']
        elif mutation == 'append-copy-first':
            target = pointer(value, case['path']);target.append(copy.deepcopy(target[0]))
        elif mutation == 'add-member':
            pointer(value, case['path']).update(copy.deepcopy(case['value']))
        elif mutation == 'remove-member':
            del pointer(value, case['path'])[case['value']]
        else:
            raise ValueError('Undeclared transport mutation ' + mutation)
        check('transport-mutation/' + case['id'], 'request', value,
              case.get('expected_schema_accepts'), category='transport-shape-observation')
        identifier = case['id']
        if identifier == 'wrong-png-digest':
            asset = value['bundle']['assets'][0]
            condition = asset['sha256'] != 'sha256:' + hashlib.sha256(base64.b64decode(asset['data_base64'], validate=True)).hexdigest()
        elif identifier == 'wrong-media':
            condition = value['bundle']['assets'][0]['media_type'] != 'image/png'
        elif identifier == 'base64-whitespace':
            text = value['bundle']['assets'][0]['data_base64']
            try:
                decoded = base64.b64decode(text, validate=True)
                condition = base64.b64encode(decoded).decode() != text
            except ValueError:
                condition = True
        elif identifier == 'duplicate-asset':
            ids = [a['asset_id'] for a in value['bundle']['assets']]
            condition = len(ids) != len(set(ids))
        elif identifier == 'asset-extra-field':
            condition = bool(set(value['bundle']['assets'][0]) - {'asset_id', 'media_type', 'sha256', 'data_base64'})
        elif identifier == 'missing-assets':
            condition = 'assets' not in value['bundle']
        elif identifier == 'wrong-bundle-version':
            condition = value['bundle']['schema_version'] != 'ontokin.bundle/0.2'
        elif identifier == 'apply-torque-rpc':
            condition = value['operation'] not in workflow['required_operations']
        elif identifier == 'mutable-torque-request':
            condition = 'torque_n_m' in value
        elif identifier in ('boolean-operation-cap', 'zero-operation-cap', 'fractional-operation-cap'):
            cap = value['budgets']['max_operations']
            condition = type(cap) is not int or cap < 1
        else:
            raise ValueError('No independent transport condition for ' + identifier)
        transport_results.append({'id': identifier, 'independent_refusal_condition_present': condition,
                                  'declared_public_code': case['expected_code'],
                                  'actual_public_response_executed': False})
    with (OUT / 'corpus-schema-review02-payloads.jsonl.gz').open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as compressed:
            for row in payloads:
                compressed.write(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n')
    source_unchanged = all(identity(SOURCE / r['path']) == {k:r[k] for k in ('bytes','mode','sha256')}
                           for r in inputs if r['origin'] == 'corpus')
    contract_unchanged = all(identity(schema_paths[r['family']][0] / r['path']) == {k:r[k] for k in ('bytes','mode','sha256')}
                             for r in inputs if r['origin'] == 'contract')
    result = {'schema_version': 'ontokin.c090-independent-frozen-schema-corpus-review/1',
              'recorded_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'passed' if all(r['passed'] for r in rows) and all(r['independent_refusal_condition_present'] for r in transport_results) and source_unchanged and contract_unchanged else 'failed',
              'scope': 'Independent synthetic schema examples and materialized wire templates; no candidate source/service/runtime, actual response, SQLite or artifact execution',
              'schema_checks': len(rows), 'passed_checks': sum(r['passed'] for r in rows),
              'failed_checks': sum(not r['passed'] for r in rows),
              'state_prototypes': len(state['prototypes']), 'state_mutations': len(state['cases']),
              'checks': rows, 'transport_conditions': transport_results,
              'request_operation_counts': operation_counts, 'request_references': references,
              'synthetic_placeholder_substitutions': placeholder_values,
              'source_inputs_unchanged': source_unchanged, 'contract_inputs_unchanged': contract_unchanged,
              'input_inventory': identity(SNAPSHOT / 'INPUTS.json'),
              'driver': identity(Path(__file__)), 'python': sys.version, 'platform': platform.platform(),
              'jsonschema': importlib.metadata.version('jsonschema'), 'referencing': importlib.metadata.version('referencing'),
              'limits': ['Schema-valid semantic mutations are not passing physical states.',
                         'Transport cases without expected_schema_accepts are observations, not asserted shape refusals.',
                         'Independent transport conditions establish malformed input, not the exact actual public service response.',
                         'Synthetic placeholders never claim returned run/artifact/cursor/byte-length evidence.']}
    save(OUT / 'corpus-schema-review02.json', result)
    print(json.dumps({k:result[k] for k in ('status','schema_checks','passed_checks','failed_checks','source_inputs_unchanged','contract_inputs_unchanged')}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
