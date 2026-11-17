#!/usr/bin/env python3
"""Independent, original-input-only witness extraction; not a language evaluator.

Uses Python standard library and exact baseline Git objects only. No product,
C255, C256, C257 or proposed C258 modules/sidecars are imported. Source-derived
facts are calculated before reading the corresponding artifact rows.
"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import re
import struct
import subprocess

ROOT = Path('/workspace/scratch/da3bfd223c61/OntoKin')
OUT = Path(__file__).resolve().parent
REV = '9b9d06d99e55fa9cf4d42e74d07505e98840c2b1'
PROOF = 'docs/engineering/semantic-export-c210/evidence/proof/'


def read(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{REV}:{path}'])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


bindings = []
sources = {}
for name in ('before.main.ok', 'after.main.ok', 'hinges.ok'):
    raw = read(PROOF + name)
    sources[name] = raw
    bindings.append({'path': PROOF + name, 'bytes': len(raw), 'sha256': digest(raw)})


def witness(filename, exact):
    raw = sources[filename]
    needle = exact.encode()
    assert raw.count(needle) == 1, (filename, exact)
    start = raw.index(needle)
    return {'filename': filename, 'source_id': 'entry' if '.main.ok' in filename else
            'package:example.hinges@1.0.0', 'source_revision': 'sha256:' + digest(raw),
            'start_byte': start, 'end_byte': start + len(needle), 'text': exact}


authority_specs = {
    'docs/language-design/OK-LANG-001-core-language-specification.md': [
        (169,169), (188,199), (229,239), (266,278), (282,319), (375,395), (422,426)],
    'docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md': [
        (69,81), (110,168), (179,185), (207,225), (229,243)],
    'docs/engineering/localized-repair-c257/NEXT-TASK.md': [(1,29)]
}
authority = []
for path, ranges in authority_specs.items():
    raw = read(path)
    lines = raw.decode().splitlines()
    authority.append({'path': path, 'bytes': len(raw), 'sha256': digest(raw),
        'excerpts': [{'start_line': a, 'end_line': min(b, len(lines)),
                      'text': '\n'.join(lines[a-1:b])} for a,b in ranges]})
save('SOURCE-AUTHORITY.json', {'commit': REV, 'documents': authority})

source_results = {}
for endpoint in ('before', 'after'):
    entry_name = endpoint + '.main.ok'
    main = sources[entry_name].decode()
    hinges = sources['hinges.ok'].decode()
    module_name, module_key = re.search(r'module (\w+) @ "([^"]+)";', main).groups()
    scene_name, scene_key = re.search(r'scene (\w+) @ "([^"]+)"', main).groups()
    roots = re.findall(r'object (\w+) @ "([^"]+)": Rack', main)
    collection_name, collection_key = re.search(r'public parts (\w+) @ "([^"]+)"', main).groups()
    class_name, class_key = re.search(r'public class (\w+) @ "([^"]+)"', hinges).groups()
    follow_name, follow_key = re.search(r'public follow (\w+) @ "([^"]+)"', hinges).groups()
    package_module_key = re.search(r'module \w+ @ "([^"]+)";', hinges).group(1)
    spacing_literal = re.search(r'mech\.three_mounts\(([^)]+)\)', main).group(1)
    spacing = Decimal(re.fullmatch(r'([0-9.]+)\[m\]', spacing_literal).group(1))
    helper_entries = re.findall(r'"([^"]+)": vec3\(0\[m\], ([-]?spacing|0\[m\]), 0\[m\]\)', hinges)
    helper_values = {key: -spacing if value == '-spacing' else spacing if value == 'spacing'
                     else Decimal(0) for key, value in helper_entries}
    # The second occurrence has an explicit keyed input override. These values
    # are read from that .ok literal, not from any artifact/expected table.
    override = re.search(r'mounts = keyed<Vec3<Length>> \{(.*?)\n        \};', main, re.S).group(1)
    override_values = {key: Decimal(value) for key, value in re.findall(
        r'"([^"]+)": vec3\(0\[m\], ([-0-9.]+)\[m\], 0\[m\]\)', override)}
    assert len(roots) == 2 and len(helper_values) == 3 and len(override_values) == 5
    rows = []
    for (root_name, root_key), values in zip(roots, (helper_values, override_values)):
        for key in sorted(values):
            child = f'{root_name}.{collection_name}[{json.dumps(key)}]'
            child_id = [module_key, scene_key, root_key, collection_key, key]
            rows.append({'path': child + '.' + follow_name,
                'element_id': child_id + [follow_key],
                'child_object': child, 'child_element_id': child_id,
                'parent_frame': root_name + '.frame',
                'parent_object_element_id': [module_key, scene_key, root_key],
                'offset_frame': root_name + '.frame',
                'offset_position_m': [0.0, float(values[key]), 0.0],
                'offset_rotation_wxyz': [1.0, 0.0, 0.0, 0.0],
                'source_derived_definition_id': ['package', 'example.hinges', package_module_key,
                                                'definitions', class_key, follow_key]})
    origin_strings = [
        (entry_name, 'public parts fingers @ "fingers": mech.Finger for (key, offset) in self.mounts'),
        (entry_name, 'parent_frame = self.frame;'),
        (entry_name, 'mount_offset = offset;'),
        (entry_name, 'public param mounts @ "mounts": Keyed<Vec3<Length>> = mech.three_mounts(0.6[m]);'),
        (entry_name, 'mounts = keyed<Vec3<Length>> {' + override + '\n        };'),
        ('hinges.ok', 'public param parent_frame @ "parent-frame": FrameRef = world;'),
        ('hinges.ok', 'public param mount_offset @ "mount-offset": Vec3<Length> = vec3(0[m], 0[m], 0[m]);'),
        ('hinges.ok', 'public fn three_mounts @ "three-mounts"(spacing: Length) -> Keyed<Vec3<Length>>'),
        ('hinges.ok', 'public follow mounting @ "mounting" {\n        parent = self.parent_frame;\n        child = self;\n        offset = pose(self.parent_frame, self.mount_offset, quat(1, 0, 0, 0));\n    }'),
        ('hinges.ok', 'parent = self.parent_frame;'),
        ('hinges.ok', 'child = self;'),
        ('hinges.ok', 'offset = pose(self.parent_frame, self.mount_offset, quat(1, 0, 0, 0));')
    ]
    source_results[endpoint] = {'count': len(rows), 'rows': rows,
        'origins': [witness(*item) for item in origin_strings],
        'interpretation': 'RHS self in generated initializer is enclosing Rack; follow/default self is Finger. '
                          'Source-derived definition IDs use the actual declaring module/class/relation keys. '
                          'No geometry, motion, body, joint, accepted-revision or full source validity claim.'}
save('SOURCE-BASELINE.json', {'commit': REV, 'source_bindings': bindings, 'endpoints': source_results,
    'method': 'Direct source witnesses plus restricted original-source literal evaluation; '
              'manual lexical-scope derivation under adopted clauses, not a general parser.'})

artifacts = {}
for endpoint in ('before', 'after'):
    path = PROOF + endpoint + '.glb'
    raw = read(path)
    magic, version, total = struct.unpack_from('<4sII', raw)
    length, chunk_kind = struct.unpack_from('<I4s', raw, 12)
    assert (magic, version, total, chunk_kind) == (b'glTF', 2, len(raw), b'JSON')
    doc = json.loads(raw[20:20+length])
    meta = doc['extras']['ontokin']
    expected = [{k: row[k] for k in ('path', 'element_id', 'parent_frame', 'child_object',
                                    'offset_position_m', 'offset_rotation_wxyz')}
                for row in source_results[endpoint]['rows']]
    assert meta['follows'] == expected
    assert all(set(row) == set(expected[0]) for row in meta['follows'])
    assert set(meta['program']['occurrences']) == {n['extras']['ontokin']['path'] for n in doc['nodes']}
    artifacts[endpoint] = {'path': path, 'bytes': len(raw), 'sha256': digest(raw),
        'json_chunk': {'start_byte': 20, 'byte_length': length},
        'metadata_root': '/extras/ontokin', 'top_level_keys': list(meta),
        'program_keys': list(meta['program']), 'follows': meta['follows'],
        'field_origins': [{'array_index': i, 'pointer': '/extras/ontokin/follows/' + str(i),
                           'field_pointers': {k: '/extras/ontokin/follows/' + str(i) + '/' + k
                                              for k in row}} for i,row in enumerate(meta['follows'])],
        'source_claims': {k: meta[k] for k in ('source', 'module', 'scene', 'profile')},
        'program_identity_claims': {k: meta['program'][k] for k in
                                    ('revision', 'entry_source_id', 'manifest', 'sources')},
        'object_binding_claims': meta['program']['occurrences'],
        'node_follow_adjacent_claims': [{'node_index': i, 'path': n['extras']['ontokin']['path'],
              'properties': n['extras']['ontokin']['properties'],
              'authored_motion': n['extras']['ontokin']['authored_motion'],
              'physical': n['extras']['ontokin']['physical']}
              for i,n in enumerate(doc['nodes']) if n['extras']['ontokin']['path'] in
              {row['child_object'] for row in meta['follows']}],
        'absent_follow_authority': ['direct relation definition_id', 'direct relation source span',
                                    'independent offset reference frame field'],
        'node_count': len(doc['nodes']), 'scene_root_count': len(doc['scenes'][0]['nodes']),
        'transform_policy': meta['transform_policy'],
        'source_derived_rows_equal_actual_follow_claims': True,
        'trust_boundary': 'GLB values are artifact claims. Source association does not create missing '
                          'artifact relation provenance or prove geometry/motion/physical/joint consistency.'}
save('ARTIFACT-BASELINE.json', {'commit': REV, 'endpoints': artifacts})
save('BASELINE-CHECKS.json', {'commit': REV,
    'tree': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', REV + '^{tree}'], text=True).strip(),
    'source_follow_counts': {k: v['count'] for k,v in source_results.items()},
    'both_source_follow_graphs_equal': source_results['before']['rows'] == source_results['after']['rows'],
    'source_artifact_equal': {k: v['source_derived_rows_equal_actual_follow_claims'] for k,v in artifacts.items()},
    'imports': ['stdlib only'], 'product_or_expected_answer_imports': [],
    'script_sha256': digest(Path(__file__).read_bytes())})
print('PASS: direct original-source derivation and actual GLB traversal agree at 8 follows per endpoint.')
