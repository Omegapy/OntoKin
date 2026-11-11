"""Read-only independent arithmetic cross-check of retained C200 native evidence.

Only the final review JSON is written. No repository modules are imported and
no Blender, Node, receiving, lifecycle, or qualification processes are started.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import hashlib
import json
import math
import re
import struct

BASE = Path('/workspace/scratch/ef5ae272e66e')
NATIVE = BASE / 'c200-native'
REPO = BASE / 'ontokin'
OUT = BASE / 'audit-repository/numeric-result-review.json'
LOCK_SHA = 'e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0'
G, M = F('0.000005'), F('0.000001')
issues, counts, native_rows, control_rows = [], Counter(), [], []


def load(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(condition, where, detail):
    counts['assertions'] += 1
    if not condition:
        issues.append({'where': where, 'detail': detail})


def flatten(value):
    if isinstance(value, (list, tuple)):
        return [n for item in value for n in flatten(item)]
    return [value]


def serial(value):
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return float(value)


def fixture(case):
    left = ['.20', '.06', '.12', '.005', '.004', '.006', '.020']
    right = ['.16', '.04', '.10', '.005', '.004', '.006', '.020']
    if case == 'Q02':
        left = ['.01', '.01', '.01', '.001', '.001', '.001', '.001']
        right = ['1', '.5', '1', '.05', '.025', '.025', '.1']
    if case == 'Q04':
        left[0] = '.24'
    if case == 'Q05':
        left[0] = '.18'
    result = {}
    for side, vals in [('left', left), ('right', right)]:
        x, y, z, c, wall, base, head = map(F, vals)
        width, depth, height = x+2*c, z+2*c, y+head
        outer_width, outer_depth = width+2*wall, depth+2*wall
        result[side] = {
            'back': (outer_width, height, wall),
            'base': (outer_width, base, outer_depth),
            'front': (outer_width, height, wall),
            'left-wall': (wall, height, depth),
            'payload': (x, y, z),
            'right-wall': (wall, height, depth),
        }
    return result


def allowance(case, identity):
    parts = identity.split('/') if isinstance(identity, str) else identity
    dims = fixture(case)[parts[2]][parts[3]]
    volume = math.prod(dims)
    return float(volume), float(math.prod(d+2*G for d in dims)-volume)


def threshold(kind, row, case):
    name = row.get('name', row.get('field'))
    if name == 'signed_volume_m3':
        expected, tol = allowance(case, row['semantic_id'])
        check(row['expected'] == expected, kind, 'Volume expectation differs from C198 dimensions')
        return tol
    if name.startswith('normal_') or name.startswith('rigid_'):
        return float(M)
    if name.startswith(('world_matrix_', 'matrix_')):
        i, j = map(int, name.rsplit('_', 2)[-2:])
        return float(G if j == 3 and i < 3 else M)
    return float(G)


def rows(kind, doc, case, where):
    summary = Counter()
    max_ratio = 0.0
    min_boundary_margin = None
    for row in doc['measurements']:
        comparison = row.get('comparison', 'absolute_difference')
        summary[comparison] += 1
        counts[kind+'_rows'] += 1
        actual = row.get('measured', row.get('actual'))
        expected = row['expected']
        label = where + '/' + row.get('name', row.get('field'))
        if comparison == 'exact':
            recomputed = actual == expected
        else:
            check(type(actual) in (int, float) and type(expected) in (int, float), label, 'Non-numeric operand')
            check(math.isfinite(actual) and math.isfinite(expected), label, 'Nonfinite operand')
            tol = threshold(kind, row, case)
            check(row['threshold'] == tol, label, 'Threshold differs from frozen tolerance or derived volume allowance')
            difference = actual - expected
            recomputed = difference >= -tol if comparison == 'minimum' else abs(difference) <= tol
            displayed = abs(difference) if kind == 'three' else difference
            # The independent reader calculates exact Fraction values before
            # serializing separate rounded values. Permit only their ULP error
            # when cross-checking the separately serialized difference.
            rounding = 2 * (math.ulp(actual) + math.ulp(expected) + math.ulp(row['difference'])) if kind in ('audit', 'control') else 0
            check(abs(displayed-row['difference']) <= rounding, label, 'Reported difference disagrees with operands')
            max_ratio = max(max_ratio, abs(difference)/tol)
            margin = difference+tol if comparison == 'minimum' else tol-abs(difference)
            min_boundary_margin = margin if min_boundary_margin is None else min(min_boundary_margin, margin)
        check(row['passed'] is recomputed, label, 'Reported comparison outcome disagrees with recomputation')
        if not recomputed:
            summary['failed'] += 1
            if kind in ('audit', 'control'):
                check(any(f['semantic_id'] == row['semantic_id'] and f['classification'] == row['classification'] and f['message'] == row['name']+' differs from the independent expectation' for f in doc['findings']), label, 'Failed numeric row lacks corresponding finding')
    return {**summary, 'total': len(doc['measurements']), 'max_absolute_difference_to_allowance_ratio': max_ratio, 'smallest_comparison_boundary_margin': min_boundary_margin}


def glb(path):
    raw = Path(path).read_bytes()
    magic, version, size = struct.unpack_from('<III', raw)
    check((magic, version, size) == (0x46546c67, 2, len(raw)), str(path), 'GLB header mismatch')
    chunks, offset = [], 12
    while offset < len(raw):
        length, kind = struct.unpack_from('<II', raw, offset)
        chunks.append((kind, raw[offset+8:offset+8+length]))
        offset += 8 + length
    check([x[0] for x in chunks] == [0x4e4f534a, 0x004e4942], str(path), 'Unexpected GLB chunks')
    return raw, json.loads(chunks[0][1]), chunks[1][1]


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    format_code, size = {5121: ('B', 1), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}[a['componentType']]
    width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    start = v.get('byteOffset', 0)+a.get('byteOffset', 0)
    stride = v.get('byteStride', size*width)
    result = [list(struct.unpack_from('<'+format_code*width, binary, start+i*stride)) for i in range(a['count'])]
    return [x[0] for x in result] if width == 1 else result


def local_matrix(node):
    if 'matrix' in node:
        return [[F(node['matrix'][4*j+i]) for j in range(4)] for i in range(4)]
    x, y, z, w = map(F, node.get('rotation', [0, 0, 0, 1]))
    rotation = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    scale, trans = list(map(F, node.get('scale', [1]*3))), list(map(F, node.get('translation', [0]*3)))
    return [[rotation[i][j]*scale[j] for j in range(3)]+[trans[i]] for i in range(3)] + [[F(0), F(0), F(0), F(1)]]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inspect_raw(path, audit, where, positive):
    raw, doc, binary = glb(path)
    check(sha(path) == audit['artifact_sha256'] and len(raw) == audit['artifact_bytes'], where, 'Audit artifact binding differs')
    if positive:
        check(len(doc['nodes']) == 14 and len(doc['meshes']) == 12, where, 'Raw GLB node/mesh counts differ')
        check(len(audit['nodes']) == 14 and sum('world_vertices' in n for n in audit['nodes'].values()) == 12, where, 'Audit node/mesh counts differ')
        check(doc['asset']['generator'] == 'Khronos glTF Blender I/O v4.5.48', where, 'Exporter version differs')
    parents = {child: i for i, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    worlds = {}
    def world(i):
        if i not in worlds:
            m = local_matrix(doc['nodes'][i])
            worlds[i] = mul(world(parents[i]), m) if i in parents else m
        return worlds[i]
    for i, node in enumerate(doc['nodes']):
        identity = node['name']
        if identity not in audit['nodes']:
            continue
        retained = audit['nodes'][identity]
        check(retained['extras'] == node.get('extras'), where+'/'+identity, 'Audit extras differ from raw GLB')
        check(retained['children'] == [doc['nodes'][j]['name'] for j in node.get('children', [])], where+'/'+identity, 'Audit children differ from raw GLB')
        check(retained['local_matrix'] == serial(local_matrix(node)), where+'/'+identity, 'Audit local matrix differs from decoded GLB')
        check(retained['world_matrix'] == serial(world(i)), where+'/'+identity, 'Audit world matrix differs from decoded GLB')
        if 'mesh' in node:
            primitive = doc['meshes'][node['mesh']]['primitives'][0]
            positions = accessor(doc, binary, primitive['attributes']['POSITION'])
            normals = accessor(doc, binary, primitive['attributes']['NORMAL'])
            indices = accessor(doc, binary, primitive['indices'])
            for key, values in [('positions', positions), ('normals', normals), ('indices', indices)]:
                check(retained[key] == values, where+'/'+identity, 'Audit '+key+' differ from actual binary accessor')
            vertices = [[sum(world(i)[axis][j]*F(p[j]) for j in range(3))+world(i)[axis][3] for axis in range(3)] for p in positions]
            check(retained['world_vertices'] == serial(vertices), where+'/'+identity, 'Audit world vertices differ from raw binary geometry and transforms')
    return raw, doc, binary


def three_checks(probe, audit, where):
    three = probe['three']
    check(three['position_tolerance_m'] == float(G) and three['matrix_tolerance'] == float(M), where, 'Three tolerances differ')
    check(three['version'] == '0.186.1' and three['revision'] == '186' and probe['node'] == 'v24.22.1', where, 'Node/Three version differs')
    check(three['node_count'] == len(three['nodes']) == 14, where, 'Three node count differs')
    check(three['mesh_count'] == sum('world_vertices' in n for n in three['nodes'].values()) == 12, where, 'Three mesh count differs')
    check(set(three['nodes']) == set(audit['nodes']), where, 'Three identity inventory differs')
    check(three['animations'] == 0 and three['findings'] == [] and three['passed'] is True, where, 'Three positive result differs')
    for identity, actual in three['nodes'].items():
        expected = audit['nodes'][identity]
        for key, target in [('original_name', identity), ('extras', expected['extras']), ('children', sorted(expected['children'])), ('parent', None if expected['extras']['role'] == 'tray-root' else '/'.join(expected['extras']['owner_id']))]:
            check(actual[key] == target, where+'/'+identity, 'Retained Three exact '+key+' mismatch')
            counts['three_recomputed_retained_exact_fields'] += 1
        if 'world_vertices' in expected:
            for key in ('positions', 'normals', 'indices', 'material'):
                check(actual[key] == expected[key], where+'/'+identity, 'Retained Three '+key+' mismatch')
                counts['three_recomputed_retained_exact_fields'] += 1
            check(len(actual['world_vertices']) == len(expected['world_vertices']) == 24, where+'/'+identity, 'Three vertex count differs')
    for row in three['measurements']:
        identity, field = row['semantic_id'], row['field']
        actual, reference = three['nodes'][identity], audit['nodes'][identity]
        if field.startswith('matrix_'):
            i, j = map(int, field.split('_')[-2:])
            a, e = actual['world_matrix'][i][j], reference['world_matrix'][i][j]
        elif field.startswith(('world_vertex_', 'normal_')):
            i, j = map(int, field.split('_')[-2:])
            key = 'world_vertices' if field.startswith('world_vertex_') else 'normals'
            a, e = actual[key][i][j], reference[key][i][j]
        else:
            axis = int(field.split('_')[-1])
            a_values = [v[axis] for v in actual['world_vertices']]
            e_values = [v[axis] for v in reference['world_vertices']]
            fn = min if field.startswith('world_min_') else max
            a, e = fn(a_values), fn(e_values)
            if field.startswith('world_size_'):
                a -= min(a_values)
                e -= min(e_values)
        check(row['actual'] == a and row['expected'] == e, where+'/'+field, 'Three row operands disagree with retained observed/reference nodes')
    kh = probe['khronos']
    check(kh['version'] == kh['report']['validatorVersion'] == '2.0.0-dev.3.10', where, 'Khronos version differs')
    issue = kh['report']['issues']
    check(all(issue[k] == 0 for k in ('numErrors', 'numWarnings', 'numInfos', 'numHints')) and issue['truncated'] is False and issue['messages'] == [], where, 'Khronos issue count/result differs')
    check(kh['passed'] is True and kh['report']['info']['drawCallCount'] == 12 and kh['report']['info']['totalTriangleCount'] == 144 and kh['report']['info']['totalVertexCount'] == 288, where, 'Khronos retained counts differ')


lockpath = REPO/'docs/engineering/static-tray-exporter-c200/EXECUTABLE-INPUTS.json'
lock = load(lockpath)
check(sha(lockpath) == LOCK_SHA, 'lock', 'Input lock hash differs')
schedule = {item['slot']: item for item in lock['slots']}
results = {}
audits = {}
raws = {}
check({p.stem for p in (NATIVE/'results').glob('N*.json')} == {'N%02d' % i for i in range(1, 13)}, 'inventory', 'Native result inventory differs')
for number in range(1, 13):
    slot = 'N%02d' % number
    result = load(NATIVE/'results'/ (slot+'.json'))
    results[slot] = result
    candidate, receiving = Path(result['candidate']), Path(result['receiving_candidate'])
    audit, received = load(candidate/'independent-audit.json'), load(receiving/'receiving-check.json')
    audits[slot] = audit
    observations = load(receiving/'observations.json')
    probe = load(NATIVE/'external-readback'/slot/'probe.json')
    external = load(NATIVE/'external-readback'/slot/'result.json')
    check(result['state'] == 'ACCEPTED' and result['native_starts'] == result['receiving_starts'] == 1, slot, 'Native acceptance/count differs')
    check(result['input_lock_sha256'] == probe['input_lock_sha256'] == external['input_lock_sha256'] == LOCK_SHA, slot, 'Result lock differs')
    check(result['case'] == audit['case'] == probe['case'] == schedule[slot]['case'] and result['route'] == schedule[slot]['route'], slot, 'Scheduled case or route differs')
    check(audit['passed'] is True and audit['findings'] == [], slot, 'Independent positive audit differs')
    check(received == result['receiving_check'], slot, 'Embedded receiving check differs from retained receiving file')
    check(received['passed'] is True and received['findings'] == [] and received['compared_imported_glb'] is True and received['compared_native_scene'] is True, slot, 'Receiving positive result differs')
    check(received['geometry_tolerance_m'] == float(G) and received['matrix_tolerance'] == float(M), slot, 'Receiving tolerance differs')
    check(observations['blender_version'] == [4, 5, 3] and observations['build_hash'] == '67807e1800cc', slot, 'Observed Blender version differs')
    for stage in ('imported_glb', 'native_scene'):
        check(observations[stage]['object_count'] == len(observations[stage]['nodes']) == 14 and sum('world_vertices' in v for v in observations[stage]['nodes'].values()) == 12, slot+'/'+stage, 'Observed receiving node/mesh count differs')
    check(probe['passed'] is True and external['passed'] is True and external['state'] == 'ACCEPTED' and external['checker_starts'] == 1 and probe['native_starts'] == probe['exports'] == external['native_starts'] == external['exports'] == 0, slot, 'External acceptance/count differs')
    check(probe['artifact_sha256'] == result['artifacts']['final.glb']['sha256'] == sha(candidate/'final.glb'), slot, 'Probe artifact binding differs')
    check(probe['audit_sha256'] == sha(candidate/'independent-audit.json') and external['probe_sha256'] == sha(NATIVE/'external-readback'/slot/'probe.json'), slot, 'Probe/audit binding differs')
    native_rows.append({'slot': slot, 'case': result['case'], 'audit': rows('audit', audit, result['case'], slot+'/audit'), 'receiving': rows('receiving', received, result['case'], slot+'/receiving'), 'three': rows('three', probe['three'], result['case'], slot+'/three')})
    check([native_rows[-1][k]['total'] for k in ('audit', 'receiving', 'three')] == [2056, 2351, 2060], slot, 'Expected measurement row count differs')
    check(all(native_rows[-1][k].get('failed', 0) == 0 for k in ('audit', 'receiving', 'three')), slot, 'Positive recorded operand comparison failed')
    raws[slot] = inspect_raw(candidate/'final.glb', audit, slot, True)
    check((candidate/'raw.glb').read_bytes() == raws[slot][0], slot, 'Raw/final byte copy differs')
    three_checks(probe, audit, slot+'/external')

definitions = {r['id']: r for r in load(REPO/'docs/engineering/static-tray-mapping-c198/CONTROLS.json')['controls'] if r['id'].startswith('D')}
control_docs = {}
control_raws = {}
for spec in lock['delivered_controls']:
    directory = Path(spec['directory'])
    result, audit = load(directory/'result.json'), load(directory/'audit.json')
    label = directory.name
    case = result['case']
    source = spec['after_slot']
    control_docs[label] = audit
    observed = sorted({r['classification'] for r in audit['findings']})
    required = definitions[case].get('required_findings', [definitions[case]['expected_diagnostic_class']] if 'expected_diagnostic_class' in definitions[case] else [])
    check(result['input_lock_sha256'] == LOCK_SHA and result['native_starts'] == 0 and result['source_slot'] == source, label, 'Control source/count/lock differs')
    check(result['observed_findings'] == observed and result['required_findings'] == required and set(required) <= set(observed), label, 'Control findings differ from actual audit/C198 requirements')
    check(result['audit_passed'] is audit['passed'] and result['passed'] is True and result['original_closure_preserved'] is True, label, 'Control result outcome differs')
    check((audit['passed'] is True and audit['findings'] == []) if case == 'D08' else (audit['passed'] is False and len(audit['findings']) > 0), label, 'Positive/negative control expectation differs')
    report = rows('control', audit, result['expected'], label)
    check(result['actual_input_sha256'] == audits[source]['artifact_sha256'] and result['actual_output_sha256'] == sha(directory/'changed.glb'), label, 'Control artifact hashes differ')
    check(result['corruption_receipt']['input_sha256'] == result['actual_input_sha256'] and result['corruption_receipt']['output_sha256'] == result['actual_output_sha256'], label, 'Control corruption receipt hash differs')
    control_raws[label] = inspect_raw(directory/'changed.glb', audit, label, False)
    control_rows.append({'control': label, 'required_findings': required, 'actual_findings': observed, 'findings_count': len(audit['findings']), 'rows': report})

# Verify concrete mutation effects against retained measurements/raw containers.
base = audits['N01']
left = 'equipment-tray/pair/left'
right = 'equipment-tray/pair/right'
d01 = control_docs['D01-copy']
for side in ('left', 'right'):
    matches = [r for r in d01['measurements'] if r['semantic_id'] == left.split('/') and r['name'] == 'minimum_clearance_'+side+'_m']
    check(len(matches) == 1 and abs(matches[0]['measured']-.003) <= float(G) and matches[0]['expected'] == .005 and matches[0]['passed'] is False, 'D01-copy', 'Required actual 0.003 m side-clearance failure absent')
check(d01['right_closure'] == base['right_closure'], 'D01-copy', 'Unrelated right sibling changed')
d02 = control_docs['D02-copy']
check(right+'/base' not in d02['nodes'] and len(control_raws['D02-copy'][1]['nodes']) == 13 and len(control_raws['D02-copy'][1]['meshes']) == 11, 'D02-copy', 'Actual right/base deletion absent')
check(all(v == d02['nodes'].get(k) for k,v in base['nodes'].items() if k.startswith(left)), 'D02-copy', 'Left geometry not independently preserved')
d03 = control_docs['D03-copy']
for end in ('min', 'max'):
    delta = d03['nodes'][right+'/front']['bounds'][end][2]-base['nodes'][right+'/front']['bounds'][end][2]
    check(abs(delta-.002) <= float(G), 'D03-copy', 'Actual right/front local Z displacement differs')
check(d03['right_closure'] != base['right_closure'], 'D03-copy', 'Right closure unexpectedly unchanged')
d04 = control_docs['D04-copy']
check(d04['nodes'][left+'/base']['bounds']['min'] == base['nodes'][left+'/base']['bounds']['min'] and d04['nodes'][left+'/base']['bounds']['max'] == base['nodes'][left+'/base']['bounds']['max'], 'D04-copy', 'Damaged mesh bounds changed')
check(len(d04['nodes'][left+'/base']['indices']) == 30 and d04['nodes'][left+'/base']['bounds']['topology_passed'] is False, 'D04-copy', 'Actual two-triangle deletion/topology failure absent')
d05 = control_docs['D05-copy']
check(any(r['name'] == 'rigid_determinant' and r['measured'] < 0 and r['passed'] is False for r in d05['measurements']), 'D05-copy', 'Actual reflection failure absent')
d06 = control_docs['D06-copy']
check(any(n['extras'] != base['nodes'][k]['extras'] for k,n in d06['nodes'].items()) and all(n.get('world_vertices') == base['nodes'][k].get('world_vertices') for k,n in d06['nodes'].items()), 'D06-copy', 'Identity-only corruption not observed')
check(len(control_raws['D07-copy'][1]['nodes']) == 15, 'D07-copy', 'Actual extra node absent')
copy_raw, copy_doc, copy_bin = control_raws['D08-copy']
order_raw, order_doc, order_bin = control_raws['D08-reordered']
check(copy_raw == raws['N01'][0], 'D08-copy', 'Exact copy differs bytewise')
check(order_raw != raws['N01'][0] and order_doc == raws['N01'][1] and order_bin == raws['N01'][2], 'D08-reordered', 'Reordered copy lacks required byte inequality and decoded equivalence')
check(control_docs['D08-copy']['measurements'] == control_docs['D08-reordered']['measurements'] == base['measurements'] and control_docs['D08-copy']['nodes'] == control_docs['D08-reordered']['nodes'] == base['nodes'], 'D08', 'Measured-equivalence relationship differs')

qualification = load(NATIVE/'qualification-result.json')
check(qualification['native_starts'] == qualification['receiving_starts'] == qualification['read_only_checker_starts'] == 12, 'qualification', 'Summary start counts differ')
check(len(qualification['transactions']) == len(qualification['external_readbacks']) == 12 and len(qualification['delivered_controls']) == 9 and qualification['measured_gates_passed'] is True, 'qualification', 'Summary retained result counts differ')
report = {
    'schema': 'ontokin.c200.numeric-result-review/0.1.0',
    'passed': not issues,
    'input_lock_sha256': LOCK_SHA,
    'method': 'Independent standard-library arithmetic over retained measured/expected operands; frozen thresholds and volume allowances recomputed; raw GLB accessors, transforms and world vertices decoded independently; Three retained numeric operands and exact identity/geometry fields cross-checked. No repository code imported.',
    'processes_started': {'native': 0, 'receiving': 0, 'node': 0, 'lifecycle': 0, 'qualification': 0},
    'counts': dict(counts),
    'native_results': native_rows,
    'delivered_controls': control_rows,
    'd08': {'copy_byte_identical': copy_raw == raws['N01'][0], 'reordered_byte_different': order_raw != raws['N01'][0], 'reordered_decoded_json_and_binary_identical': order_doc == raws['N01'][1] and order_bin == raws['N01'][2]},
    'versions': {'blender': '4.5.3', 'blender_build_hash': '67807e1800cc', 'gltf_exporter': '4.5.48', 'node': 'v24.22.1', 'three': '0.186.1', 'three_revision': '186', 'khronos_validator': '2.0.0-dev.3.10'},
    'qualification_status': qualification['status'],
    'discrepancies': issues,
    'limitations': [
        'This is a retained-evidence numeric cross-check; no fresh Blender/receiving/Node observations were produced.',
        'Independent-reader comparison operands are separately rounded JSON numbers; comparison outcomes and difference consistency were checked, allowing only serialization ULP error for the latter.',
        'Receiving exact/numeric comparison decisions were recomputed from retained rows; receiving geometry was not reimported or rendered.',
        'Khronos issue counts and versions were checked against retained reports; the validator was not rerun.',
        'The retained qualification-result.json explicitly remains MEASURED_GATES_PASSED_VISUAL_REVIEW_PENDING and qualified=false; this review does not replace visual review, lifecycle review or the parent closure audit.'
    ]
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({'passed': report['passed'], 'counts': report['counts'], 'discrepancy_count': len(issues), 'first_discrepancies': issues[:8], 'review': str(OUT)}, sort_keys=True))
