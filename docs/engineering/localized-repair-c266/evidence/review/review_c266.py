"""Independent C266 public-API adversarial controls.

Expectations are declared from C260 / OK-LANG-002 / OK-AGENT-002 and the exact
source bytes. No product compiler, observer helper, authored test or expected
record is used to construct claims. The candidate is imported only to call its
public bind_hinge_inputs API after an exact hash guard.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import struct
import sys


PINS = {
    "before.main.ok": "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123",
    "after.main.ok": "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a",
    "hinges.ok": "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a",
    "before.glb": "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534",
    "after.glb": "05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8",
}
LEAF_ID = "package:example.hinges@1.0.0"
PATH = 'first.fingers["middle"]'
BLADE = PATH + '.blade'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_glb(raw):
    length, = struct.unpack_from('<I', raw, 12)
    return json.loads(raw[20:20 + length]), raw[20 + length:]


def glb(doc, rest):
    encoded = json.dumps(doc, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    return struct.pack('<4sII', b'glTF', 2, 20 + len(encoded) + len(rest)) + struct.pack('<I4s', len(encoded), b'JSON') + encoded + rest


def meta(doc):
    return doc['extras']['ontokin']


def node(doc, path):
    return next(n['extras']['ontokin'] for n in doc['nodes'] if n.get('extras', {}).get('ontokin', {}).get('path') == path)


def mapping(doc, which, path=PATH):
    return node(doc, path)['source_mapping'] if which == 'node' else meta(doc)['program']['occurrences'][path]


def rewrite(value, fn):
    if isinstance(value, dict):
        changed = {fn(k): rewrite(v, fn) for k, v in value.items()}
        return changed
    if isinstance(value, list):
        return [rewrite(x, fn) for x in value]
    return fn(value)


def walk_locations(value, filename, edits):
    if isinstance(value, dict):
        if value.get('filename') == filename and 'start_byte' in value and 'end_byte' in value:
            for field in ('start_byte', 'end_byte'):
                point = value[field]
                value[field] = point + sum(len(new) - (end - start) for start, end, new in edits if end <= point)
        for child in value.values():
            walk_locations(child, filename, edits)
    elif isinstance(value, list):
        for child in value:
            walk_locations(child, filename, edits)


def change_source(files, doc, filename, old, new, *, all_occurrences=True):
    original = files[filename]
    if old == b'':
        edits = [(0, 0, new)]
    else:
        edits = []
        cursor = 0
        while True:
            where = original.find(old, cursor)
            if where < 0:
                break
            edits.append((where, where + len(old), new))
            cursor = where + len(old)
            if not all_occurrences:
                break
        assert edits, (filename, old)
    result = original
    for start, end, addition in reversed(edits):
        result = result[:start] + addition + result[end:]
    walk_locations(doc, filename, edits)
    files[filename] = result
    old_revision, new_revision = 'sha256:' + sha(original), 'sha256:' + sha(result)
    doc = rewrite(doc, lambda x: new_revision if x == old_revision else x)
    if filename == 'hinges.ok':
        doc = change_source(files, doc, 'main.ok', old_revision.encode(), new_revision.encode())
    manifest = {
        'schema_version': 'ontokin.bundle/0.1',
        'entry_source_id': 'entry',
        'units': [
            {'source_id': 'entry', 'package_id': None, 'version': None, 'filename': 'main.ok', 'source_revision': 'sha256:' + sha(files['main.ok'])},
            {'source_id': LEAF_ID, 'package_id': 'example.hinges', 'version': '1.0.0', 'filename': 'hinges.ok', 'source_revision': 'sha256:' + sha(files['hinges.ok'])},
        ],
    }
    old_program = meta(doc)['program']['revision']
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    new_program = 'sha256:' + sha(b'ontokin.bundle/0.1\0' + canonical)
    doc = rewrite(doc, lambda x: new_program if x == old_program else x)
    meta(doc)['program']['manifest'] = manifest
    return doc


def replace_key(value, before='middle', after='m.id-le'):
    if not isinstance(value, str):
        return value
    if value == before:
        return after
    return value.replace('["' + before + '"]', '["' + after + '"]')


def assert_source_witnesses(files, doc):
    """Baseline controls independently establish where the key/value begins/ends."""
    for key, path in [('middle', PATH), ('lower', 'first.fingers["lower"]')]:
        m = mapping(doc, 'node', path)
        generated = m['generated']
        source = files['hinges.ok']
        loc = generated['input_entry']
        text = source[loc['start_byte']:loc['end_byte']]
        expected = ('"' + key + '": vec3(0[m], ' + ('0[m]' if key == 'middle' else '-spacing') + ', 0[m])').encode()
        assert text == expected, (key, text, expected)
        assert generated['input_entry']['source_id'] == LEAF_ID
        assert generated['collection_definition_id'] == ['entry', 'keyed-rack', 'definitions', 'rack', 'fingers']
        assert m['generated_ancestor'] == path
        descendant = mapping(doc, 'node', path + '.blade')
        assert descendant['generated_ancestor'] == path
        assert descendant['declaration_definition_id'] == ['package', 'example.hinges', 'hinges', 'definitions', 'finger', 'blade']
    assert mapping(doc, 'node', 'first')['declaration_definition_id'] is None


def build_cases(baseline, before_doc, rest, after_files, after_raw, before_raw):
    cases = []

    def add(name, mutate=None, *, allowed=False, count=18, files_mutate=None, raw=None, expect_codes=None):
        files, doc = copy.deepcopy(baseline), copy.deepcopy(before_doc)
        if mutate:
            mutate(doc)
        if files_mutate:
            doc = files_mutate(files, doc)
        cases.append({'name': name, 'allowed': allowed, 'objectCount': count, 'files': files,
                      'raw': glb(doc, rest) if raw is None else raw, 'expect_codes': expect_codes})

    add('original_before', allowed=True, raw=before_raw)
    cases.append({'name': 'original_after', 'allowed': True, 'objectCount': 18, 'files': after_files, 'raw': after_raw, 'expect_codes': None})
    add('node_order_reversed', lambda d: d['nodes'].reverse(), allowed=True)
    add('joint_rows_removed_limit', lambda d: meta(d).__setitem__('joints', []), allowed=True)
    add('joint_numeric_mismatch_limit', lambda d: meta(d)['joints'][0].__setitem__('initial', 0.125), allowed=True)
    add('joint_endpoint_mismatch_limit', lambda d: meta(d)['joints'][0].__setitem__('parent_site', 'unrelated.opaque'), allowed=True)
    add('unobserved_collection_and_module_limit', lambda d: (meta(d)['program'].__setitem__('collections', {'unobserved': True}), meta(d).__setitem__('module', 'not-observed'), meta(d).__setitem__('scene', 'not-observed')), allowed=True)
    add('unobserved_source_prose_limit', lambda d: meta(d)['source'].__setitem__('provenance', 'Changed annotation'), allowed=True)

    for which in ('node', 'program'):
        for name, operation in [
            ('owner_path', lambda m: m.__setitem__('owner_path', 'second')),
            ('root_path', lambda m: m.__setitem__('root_path', 'second')),
            ('typed_key_step', lambda m: m['path_steps'][2].__setitem__('kind', 'member')),
            ('definition_id', lambda m: m['definition_id'].__setitem__(-1, 'blade')),
            ('class_id', lambda m: m.__setitem__('class_id', 'entry/keyed-rack/definitions/rack')),
            ('declaration_start', lambda m: m['declaration'].__setitem__('start_byte', m['declaration']['start_byte'] + 1)),
            ('declaration_end', lambda m: m['declaration'].__setitem__('end_byte', m['declaration']['end_byte'] - 1)),
            ('declaration_source', lambda m: m['declaration'].__setitem__('source_id', LEAF_ID)),
            ('declaration_filename', lambda m: m['declaration'].__setitem__('filename', 'hinges.ok')),
            ('definition_end', lambda m: m['definition'].__setitem__('end_byte', m['definition']['end_byte'] - 1)),
            ('declaration_definition_null', lambda m: m.__setitem__('declaration_definition_id', None)),
            ('collection_id', lambda m: m['generated']['collection_id'].__setitem__(-1, 'wrong')),
            ('collection_definition', lambda m: m['generated']['collection_definition_id'].__setitem__(-1, 'wrong')),
            ('generation_key', lambda m: m['generated'].__setitem__('key', 'lower')),
            ('generation_input', lambda m: m['generated']['input'].__setitem__('start_byte', m['generated']['input']['start_byte'] + 1)),
            ('input_entry_key_only', lambda m: m['generated']['input_entry'].__setitem__('end_byte', m['generated']['input_entry']['start_byte'] + len(b'"middle"'))),
            ('input_entry_omit_value_tail', lambda m: m['generated']['input_entry'].__setitem__('end_byte', m['generated']['input_entry']['end_byte'] - 1)),
            ('input_entry_filename', lambda m: m['generated']['input_entry'].__setitem__('filename', 'main.ok')),
            ('input_entry_wrong_source', lambda m: m['generated']['input_entry'].__setitem__('source_id', 'entry')),
            ('input_entry_stale_hash', lambda m: m['generated']['input_entry'].__setitem__('source_revision', 'sha256:' + '0' * 64)),
            ('unique_span_true', lambda m: m['generated'].__setitem__('unique_declaration_span', True)),
            ('unique_span_integer_false', lambda m: m['generated'].__setitem__('unique_declaration_span', 0)),
            ('generated_ancestor_null', lambda m: m.__setitem__('generated_ancestor', None)),
            ('extra_mapping_field', lambda m: m.__setitem__('extra_claim', 1)),
            ('sparse_mapping', lambda m: m.clear()),
        ]:
            add(which + '_' + name, lambda d, w=which, op=operation: op(mapping(d, w)))
        add(which + '_ordinary_descendant_ancestor', lambda d, w=which: mapping(d, w, BLADE).__setitem__('generated_ancestor', 'second.fingers["middle"]'))
        add(which + '_ordinary_declaration_definition', lambda d, w=which: mapping(d, w, BLADE)['declaration_definition_id'].__setitem__(-2, 'blade'))
        add(which + '_root_decl_definition_not_null', lambda d, w=which: mapping(d, w, 'first').__setitem__('declaration_definition_id', ['entry', 'keyed-rack', 'definitions', 'rack']))
    add('both_repeated_maps_agree_but_wrong', lambda d: [mapping(d, w)['generated']['input_entry'].__setitem__('end_byte', 247) for w in ('node', 'program')])
    add('node_class_claim', lambda d: node(d, PATH).__setitem__('class_name', 'wrong/class'))
    add('node_program_revision', lambda d: node(d, PATH).__setitem__('program_revision', 'sha256:' + '0' * 64))
    add('entry_revision', lambda d: meta(d)['source'].__setitem__('entry_revision', 'sha256:' + '0' * 64))
    add('source_module_name', lambda d: meta(d)['program']['sources'][LEAF_ID].__setitem__('module_name', 'Wrong'))
    add('source_module_key', lambda d: meta(d)['program']['sources'][LEAF_ID].__setitem__('module_key', 'wrong'))
    add('source_unit_sparse', lambda d: meta(d)['program']['sources'][LEAF_ID].pop('version'))
    add('manifest_filename', lambda d: meta(d)['program']['manifest']['units'][1].__setitem__('filename', 'wrong.ok'))
    add('source_manifest_unit_order', lambda d: meta(d)['program']['manifest']['units'].reverse())
    add('source_manifest_extra_claim', lambda d: meta(d)['program']['manifest'].__setitem__('extra', 'claim'))

    def remove_object(d):
        d['nodes'] = [n for n in d['nodes'] if n.get('extras', {}).get('ontokin', {}).get('path') != BLADE]
        del meta(d)['program']['occurrences'][BLADE]
    add('matching_but_incomplete_object_tables', remove_object)

    add('utf8_entry_prefix_rebound', files_mutate=lambda f, d: change_source(f, d, 'main.ok', b'', '// π provenance\n'.encode()), allowed=True)
    add('utf8_leaf_prefix_and_pin_rebound', files_mutate=lambda f, d: change_source(f, d, 'hinges.ok', b'', '// é source\n'.encode()), allowed=True)

    def opaque_key(f, d):
        d = change_source(f, d, 'hinges.ok', b'"middle"', b'"m.id-le"')
        d = change_source(f, d, 'main.ok', b'"middle"', b'"m.id-le"')
        return rewrite(d, replace_key)
    add('opaque_punctuation_key_rebound', files_mutate=opaque_key, allowed=True)

    def rename_class(f, d):
        d = change_source(f, d, 'hinges.ok', b'class Finger', b'class DigitX')
        return change_source(f, d, 'main.ok', b'mech.Finger', b'mech.DigitX')
    add('lexical_class_rename_same_nominal_id', files_mutate=rename_class, allowed=True)

    def put_input_entry(d, path, f, filename, entry):
        start = f[filename].index(entry)
        record = {'source_id': 'entry' if filename == 'main.ok' else LEAF_ID,
                  'source_revision': 'sha256:' + sha(f[filename]), 'filename': filename,
                  'start_byte': start, 'end_byte': start + len(entry)}
        for which in ('node', 'program'):
            mapping(d, which, path)['generated']['input_entry'] = copy.deepcopy(record)

    def duplicate_pair(d, old_key, new_key):
        for suffix in ('', '.blade'):
            old_path = 'first.fingers["' + old_key + '"]' + suffix
            whole = next(n for n in d['nodes'] if n.get('extras', {}).get('ontokin', {}).get('path') == old_path)
            twin = rewrite(copy.deepcopy(whole), lambda x: replace_key(x, old_key, new_key))
            d['nodes'].append(twin)
            new_path = 'first.fingers["' + new_key + '"]' + suffix
            meta(d)['program']['occurrences'][new_path] = copy.deepcopy(twin['extras']['ontokin']['source_mapping'])

    def remove_pair(d, key):
        root = 'first.fingers["' + key + '"]'
        for path in (root, root + '.blade'):
            d['nodes'] = [n for n in d['nodes'] if n.get('extras', {}).get('ontokin', {}).get('path') != path]
            del meta(d)['program']['occurrences'][path]

    def insert_helper_key(f, d):
        entry = b'"edge": vec3(0[m], -2 * spacing, 0[m])'
        old = b'        "lower": vec3(0[m], -spacing, 0[m]),'
        d = change_source(f, d, 'hinges.ok', old, b'        ' + entry + b',\n' + old)
        # The retained row lies inside the replacement region, so derive its
        # relocated full interval directly from the new bytes.
        put_input_entry(d, 'first.fingers["lower"]', f, 'hinges.ok', b'"lower": vec3(0[m], -spacing, 0[m])')
        duplicate_pair(d, 'lower', 'edge')
        put_input_entry(d, 'first.fingers["edge"]', f, 'hinges.ok', entry)
        return d
    add('helper_membership_insert_with_complete_objects', files_mutate=insert_helper_key, allowed=True, count=20)

    def delete_helper_key(f, d):
        old = b'        "lower": vec3(0[m], -spacing, 0[m]),\n'
        d = change_source(f, d, 'hinges.ok', old, b'')
        remove_pair(d, 'lower')
        return d
    add('helper_membership_delete_with_complete_objects', files_mutate=delete_helper_key, allowed=True, count=16)

    def direct_final_override(f, d):
        middle = b'"middle": vec3(0[m], 0[m], 0[m])'
        extra = b'"z": vec3(0[m], 2[m], 0[m])'
        old = b'        fingers["middle"].length = 0.65[m];'
        new = b'        mounts = keyed<Vec3<Length>> {' + middle + b', ' + extra + b'};\n' + old
        d = change_source(f, d, 'main.ok', old, new)
        remove_pair(d, 'lower')
        remove_pair(d, 'upper')
        put_input_entry(d, PATH, f, 'main.ok', middle)
        duplicate_pair(d, 'middle', 'z')
        put_input_entry(d, 'first.fingers["z"]', f, 'main.ok', extra)
        return d
    add('final_owner_override_replaces_helper_membership', files_mutate=direct_final_override, allowed=True, count=16)

    def direct_default(f, d):
        entries = [b'"lower": vec3(0[m], -0.6[m], 0[m])', b'"middle": vec3(0[m], 0[m], 0[m])', b'"upper": vec3(0[m], 0.6[m], 0[m])']
        d = change_source(f, d, 'main.ok', b'mech.three_mounts(0.6[m])', b'keyed<Vec3<Length>> {' + b', '.join(entries) + b'}')
        for key, entry in zip(('lower', 'middle', 'upper'), entries):
            put_input_entry(d, 'first.fingers["' + key + '"]', f, 'main.ok', entry)
        return d
    add('direct_default_keyed_literal', files_mutate=direct_default, allowed=True)

    def stale_prefix(f, d):
        f['main.ok'] = b'// unchanged semantics\n' + f['main.ok']
        return d
    add('source_prefix_stale_artifact', files_mutate=stale_prefix)
    add('nonbytes_artifact', raw='not bytes')
    add('oversized_artifact', raw=b'X' * (4 * 1024 * 1024 + 1), expect_codes={'RESOURCE_LIMIT'})
    add('malformed_glb_header', raw=b'glTF')
    return cases


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--only', nargs='*', help='Run only the named independent controls')
    args = p.parse_args()
    candidate = args.candidate.read_bytes()
    assert sha(candidate) == args.expected_sha256, 'candidate identity differs'
    proof = args.repo / 'docs/engineering/semantic-export-c210/evidence/proof'
    payloads = {name: (proof / name).read_bytes() for name in PINS}
    for name, data in payloads.items():
        assert sha(data) == PINS[name], name
    files = {'main.ok': payloads['before.main.ok'], 'hinges.ok': payloads['hinges.ok']}
    doc, rest = parse_glb(payloads['before.glb'])
    assert_source_witnesses(files, doc)
    cases = build_cases(files, doc, rest, {'main.ok': payloads['after.main.ok'], 'hinges.ok': payloads['hinges.ok']}, payloads['after.glb'], payloads['before.glb'])
    if args.only:
        selected = set(args.only)
        cases = [case for case in cases if case['name'] in selected]
        assert {case['name'] for case in cases} == selected, 'unknown control name'
    spec = importlib.util.spec_from_file_location('c266_independent_review_candidate', args.candidate)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for case in cases:
        folder = args.output / 'cases' / case['name']
        folder.mkdir(parents=True)
        for filename, data in case['files'].items():
            (folder / filename).write_bytes(data)
        raw = case['raw']
        if isinstance(raw, bytes):
            (folder / 'artifact.glb').write_bytes(raw)
        item = {'name': case['name'], 'expected': 'input_binding_success_only' if case['allowed'] else 'typed_whole_input_refusal',
                'sourceHashes': {name: sha(data) for name, data in case['files'].items()},
                'artifactSha256': sha(raw) if isinstance(raw, bytes) else None,
                'artifactBytes': len(raw) if isinstance(raw, bytes) else None}
        try:
            value = module.bind_hinge_inputs(case['files'], raw)
            (folder / 'result.json').write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
            failures = []
            if not case['allowed']:
                failures.append('accepted contradictory or unsupported input')
            if value.get('schema') != 'ontokin.c266.hinge-input-binding/0.1':
                failures.append('wrong result schema')
            if value.get('inputBindingVerified') is not True:
                failures.append('missing positive input-binding flag')
            for field in ('hingeComparisonVerified', 'hingeSetAgreementVerified', 'endpointAgreementVerified', 'historicalInputsBound'):
                if value.get(field) is not False:
                    failures.append('nonclaim missing or true: ' + field)
            if 'hinges' in value:
                failures.append('qualified hinges key presented')
            if value.get('objectCount') != case['objectCount'] or len(value.get('records', [])) != case['objectCount']:
                failures.append('wrong complete object count')
            item.update({'outcome': 'accepted', 'passed': not failures, 'failures': failures})
        except Exception as error:
            detail = {'type': type(error).__name__, 'code': getattr(error, 'code', None), 'detail': str(error)}
            for field in ('pointer', 'origin', 'sourceHashes', 'sourceBytes', 'artifactSha256', 'artifactBytes'):
                if hasattr(error, field):
                    detail[field] = getattr(error, field)
            (folder / 'refusal.json').write_text(json.dumps(detail, indent=2, ensure_ascii=False) + '\n')
            passed = not case['allowed'] and isinstance(error, ValueError) and isinstance(detail['code'], str)
            if case['expect_codes'] and detail['code'] not in case['expect_codes']:
                passed = False
            if case['name'] == 'oversized_artifact' and detail.get('artifactSha256') is not None:
                passed = False
            item.update({'outcome': 'refused', 'passed': passed, 'refusal': detail})
        (folder / 'expectation.json').write_text(json.dumps({k:v for k,v in item.items() if k not in ('refusal',)}, indent=2) + '\n')
        records.append(item)
    report = {'schema': 'ontokin.c266.independent-public-api-review/0.1', 'candidateSha256': args.expected_sha256,
              'reviewerScriptSha256': sha(Path(__file__).read_bytes()), 'python': platform.python_version(), 'platform': platform.platform(),
              'sourcePins': PINS, 'controls': len(records), 'passed': all(x['passed'] for x in records),
              'passCount': sum(x['passed'] for x in records), 'failCount': sum(not x['passed'] for x in records), 'results': records}
    (args.output / 'RESULTS.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sourcePins', 'results')}, indent=2))
    for item in records:
        if not item['passed']:
            print('FAILED', item['name'], item.get('refusal', item.get('failures')))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
