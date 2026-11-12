"""Independent, read-only remeasurement of retained C211 normal observations.

Does not import OntoKin, the prior comparator, bpy, or any native application.
"""
from collections import Counter, defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--glb', type=Path, default=ROOT / 'input/c211/receiving-run/inputs/after.glb')
parser.add_argument('--observations', type=Path, default=ROOT / 'input/c211/receiving-run/import-observations.json')
parser.add_argument('--output', type=Path, default=Path(__file__).with_name('normal-remeasurement.json'))
args = parser.parse_args()
GLB, OBS, OUT = args.glb, args.observations, args.output
data = GLB.read_bytes()
magic, version, length = struct.unpack_from('<III', data)
assert magic == 0x46546C67 and version == 2 and length == len(data)
chunks = {}
offset = 12
while offset < length:
    size, kind = struct.unpack_from('<II', data, offset)
    chunks[kind] = data[offset+8:offset+8+size]
    offset += 8 + size
gltf = json.loads(chunks[0x4E4F534A])
binary = chunks[0x004E4942]
observed = json.loads(OBS.read_text())

def accessor(index):
    a = gltf['accessors'][index]
    assert not a.get('normalized', False) and 'sparse' not in a
    view = gltf['bufferViews'][a['bufferView']]
    fmt = {5126:'f', 5125:'I', 5123:'H', 5121:'B'}[a['componentType']]
    count = {'SCALAR':1, 'VEC3':3}[a['type']]
    pattern = '<' + fmt * count
    size = struct.calcsize(pattern)
    base = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', size)
    return [struct.unpack_from(pattern, binary, base + i*stride) for i in range(a['count'])]

def basis(v):
    return (v[0], -v[2], v[1])

def canonical_triangle(corners):
    rotations = [corners[i:] + corners[:i] for i in range(3)]
    return min(rotations, key=lambda row: tuple(x[0] for x in row))

def triangle_key(corners):
    return tuple(x[0] for x in corners)

def norm(v):
    return math.sqrt(sum(x*x for x in v))

source_nodes = [n for n in gltf['nodes'] if 'mesh' in n]
nodes = {n['name']:n for n in source_nodes}
assert len(nodes) == len(source_nodes), 'Duplicate input object names are unsupported'
assert Counter(o['name'] for o in observed['objects']) == Counter(nodes.keys()), 'Observed object inventory differs'
rows = []
global_corner_errors = []
counterexample = None
for obj in observed['objects']:
    node = nodes[obj['name']]
    mesh = gltf['meshes'][node['mesh']]
    assert len(mesh['primitives']) == 1
    primitive = mesh['primitives'][0]
    assert primitive.get('mode', 4) == 4
    positions = accessor(primitive['attributes']['POSITION'])
    normals = accessor(primitive['attributes']['NORMAL'])
    indices = [v[0] for v in accessor(primitive['indices'])]
    assert len(indices) % 3 == 0 and len(positions) == len(normals)
    assert all(math.isfinite(v) for row in positions + normals for v in row)
    assert all(0 <= i < len(positions) for i in indices)
    assert all(norm(n) > 0.0 for n in normals)
    expected = []
    for i in range(0, len(indices), 3):
        expected.append(canonical_triangle([(basis(positions[j]), basis(normals[j])) for j in indices[i:i+3]]))
    raw = obj['triangles_raw_blender']
    assert all(len(tri) == 3 and all(len(c) == 6 for c in tri) for tri in raw)
    assert all(math.isfinite(v) for tri in raw for c in tri for v in c)
    assert all(norm(c[3:]) > 0.0 for tri in raw for c in tri)
    actual = [canonical_triangle([(tuple(c[:3]), tuple(c[3:])) for c in tri]) for tri in raw]
    bins = defaultdict(list)
    for tri in actual:
        bins[triangle_key(tri)].append(tri)
    expected_counts = Counter(triangle_key(t) for t in expected)
    actual_counts = Counter(triangle_key(t) for t in actual)
    assert expected_counts == actual_counts, obj['name']
    assert all(n == 1 for n in expected_counts.values()), 'Coincident duplicate triangles require a different matcher'
    assert all(len(set(triangle_key(t))) == 3 for t in expected), 'Degenerate repeated-position corners are unsupported'
    failed_triangles = failed_corners = cardinal_corners = cardinal_failures = 0
    max_component = max_angle = max_input_length = max_observed_length = max_normalized_component = 0.0
    for wanted in expected:
        got = bins[triangle_key(wanted)].pop()
        triangle_errors = []
        for (position, n), (position2, m) in zip(wanted, got):
            assert position == position2
            component_error = max(abs(a-b) for a,b in zip(n,m))
            triangle_errors.append(component_error)
            global_corner_errors.append(component_error)
            failed_corners += component_error > 0.000002
            cardinal = sorted(abs(x) for x in n) == [0.0,0.0,1.0]
            cardinal_corners += cardinal
            cardinal_failures += cardinal and component_error > 0.000002
            nn, nm = norm(n), norm(m)
            normalized_error = max(abs(a/nn-b/nm) for a,b in zip(n,m))
            angle = math.acos(max(-1.0,min(1.0,sum(a*b for a,b in zip(n,m))/(nn*nm))))
            max_angle = max(max_angle,angle)
            max_input_length = max(max_input_length,abs(nn-1.0))
            max_observed_length = max(max_observed_length,abs(nm-1.0))
            max_normalized_component = max(max_normalized_component,normalized_error)
            if component_error > max_component:
                max_component = component_error
            if counterexample is None or component_error > counterexample['component_error']:
                counterexample = {'object':obj['name'],'local_position':position,'expected_normal':n,'observed_normal':m,'component_error':component_error,'normalized_component_error':normalized_error,'angular_error_rad':angle}
        failed_triangles += max(triangle_errors) > 0.000002
    assert all(not v for v in bins.values())
    rows.append({'object':obj['name'],'mesh_index':node['mesh'],'triangles':len(expected),'input_vertices':len(positions),'native_vertices':obj['vertex_count'],'failed_triangles':failed_triangles,'failed_corner_occurrences':failed_corners,'cardinal_corner_occurrences':cardinal_corners,'cardinal_failed_corners':cardinal_failures,'max_component_error':max_component,'max_direction_error_rad':max_angle,'max_normalized_component_error':max_normalized_component,'max_input_unit_length_deviation':max_input_length,'max_observed_unit_length_deviation':max_observed_length})

result = {'schema':'ontokin.c212.independent-retained-normal-remeasurement/0.1','input_glb_sha256':hashlib.sha256(data).hexdigest(),'observations_sha256':hashlib.sha256(OBS.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Fresh stdlib GLB accessor decoding and exact oriented position-triple multiset matching; cyclic rotation only; raw normal comparison; no prior comparator imports','native_processes_started':0,'original_component_limit':0.000002,'objects':len(rows),'triangles':sum(r['triangles'] for r in rows),'exact_position_and_winding_matches':sum(r['triangles'] for r in rows),'failed_triangles':sum(r['failed_triangles'] for r in rows),'failed_corner_occurrences':sum(r['failed_corner_occurrences'] for r in rows),'max_component_error':max(r['max_component_error'] for r in rows),'max_direction_error_rad':max(r['max_direction_error_rad'] for r in rows),'max_normalized_component_error':max(r['max_normalized_component_error'] for r in rows),'max_input_unit_length_deviation':max(r['max_input_unit_length_deviation'] for r in rows),'max_observed_unit_length_deviation':max(r['max_observed_unit_length_deviation'] for r in rows),'cardinal_failed_corners':sum(r['cardinal_failed_corners'] for r in rows),'max_counterexample':counterexample,'objects_detail':rows}
failed_names = {r['object'] for r in rows if r['failed_triangles']}
failed_arrays = [o['triangles_raw_blender'] for o in observed['objects'] if o['name'] in failed_names]
result['failed_instances'] = len(failed_names)
result['distinct_failed_source_meshes'] = len({r['mesh_index'] for r in rows if r['failed_triangles']})
result['distinct_failed_observed_triangle_arrays'] = len({json.dumps(a,separators=(',',':')) for a in failed_arrays})
result['coverage_limit'] = 'Eight failed sphere instances reuse one source mesh and one identical observed triangle/normal array; not eight independent shape or build trials.'
result['correspondence_checks'] = {'unique_input_object_names':True,'exact_observed_object_inventory':True,'unique_oriented_triangle_keys_per_object':True,'three_distinct_positions_per_triangle':True,'finite_components_and_nonzero_normals':True,'all_observed_triangles_consumed_once':True,'ambiguous_correspondence_policy':'Refuse; no arbitrary matching of coincident triangles or degenerate corners'}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('objects_detail','max_counterexample')},indent=2))
