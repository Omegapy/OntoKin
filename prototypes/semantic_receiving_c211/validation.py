"""Finite independent checks for the exact C210 artifact received by C211.

This module uses only Python's standard library and does not import the OntoKin
compiler, GLB reader, evaluator, semantic producer, or Blender.
"""
from __future__ import annotations

import bisect
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
INPUTS = json.loads((HERE / 'input_bindings.json').read_text())
BUILD = json.loads((HERE / 'build_bindings.json').read_text())
REVISION = INPUTS['accepted_program_revision']
TIMES = ('0', '0.25', '0.5', '0.75', '1', '1.5', '2')
MESH_EPS = 0.000002
MATERIAL_EPS = 0.000002
POSITION_EPS = 0.001
ANGLE_EPS = 0.001
TEXT_NAME = 'OntoKin C211 accepted semantic sidecar'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(path):
    raw = Path(path).read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def finite_vector(value, size, label):
    require(isinstance(value, (list, tuple)) and len(value) == size, label + ': shape')
    require(all(type(x) in (int, float) and math.isfinite(x) for x in value), label + ': finite numbers')
    return value


def close_vector(actual, expected, tolerance, label):
    finite_vector(actual, len(expected), label)
    require(all(abs(x-y) <= tolerance for x, y in zip(actual, expected)), label + ': values differ')


def quaternion_angle(a, b):
    finite_vector(a, 4, 'quaternion')
    finite_vector(b, 4, 'quaternion')
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(x*x for x in b))
    require(na > 0 and nb > 0, 'zero quaternion')
    dot = abs(sum(x*y for x, y in zip(a, b)) / (na*nb))
    return 2*math.acos(min(1.0, dot))


def matrix(position, wxyz, scale=(1, 1, 1)):
    w, x, y, z = wxyz
    norm = math.sqrt(w*w+x*x+y*y+z*z)
    require(norm > 0, 'zero rotation')
    w, x, y, z = (v/norm for v in (w, x, y, z))
    rows = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    return [[rows[i][j]*scale[j] for j in range(3)] + [position[i]] for i in range(3)] + [[0, 0, 0, 1]]


class GlbReader:
    """Independent little-endian decoder restricted to the frozen rigid GLB."""

    def __init__(self, raw):
        require(len(raw) >= 20, 'GLB header missing')
        magic, version, length = struct.unpack_from('<4sII', raw)
        require(magic == b'glTF' and version == 2 and length == len(raw), 'GLB header differs')
        chunks, offset = {}, 12
        while offset < length:
            require(offset + 8 <= length, 'GLB chunk header outside data')
            size, kind = struct.unpack_from('<I4s', raw, offset)
            offset += 8
            require(size % 4 == 0 and offset + size <= length and kind not in chunks, 'GLB chunk invalid')
            chunks[kind] = raw[offset:offset+size]
            offset += size
        require(set(chunks) == {b'JSON', b'BIN\x00'}, 'GLB chunk inventory differs')
        self.doc = json.loads(chunks[b'JSON'])
        self.binary = chunks[b'BIN\x00']
        require(len(self.doc['buffers']) == 1 and 'uri' not in self.doc['buffers'][0], 'external GLB buffer')
        require(not self.doc.get('skins') and len(self.doc['animations']) == 1, 'unsupported GLB structure')
        self.nodes = self.doc['nodes']
        require(len(self.nodes) == 18, 'object inventory count differs')
        self.names = [n['name'] for n in self.nodes]
        require(len(set(self.names)) == 18, 'duplicate GLB object name')
        require(all('mesh' in n and not n.get('children') for n in self.nodes), 'non-root or nonmesh node')
        self.tracks = {}
        animation = self.doc['animations'][0]
        for channel in animation['channels']:
            target = channel['target']
            key = (target['node'], target['path'])
            require(key not in self.tracks and target['path'] in ('translation', 'rotation', 'scale'), 'GLB animation target')
            sampler = animation['samplers'][channel['sampler']]
            times = [v[0] for v in self.accessor(sampler['input'])]
            values = self.accessor(sampler['output'])
            require(times == sorted(set(times)) and len(times) == len(values), 'GLB animation samples')
            interpolation = sampler.get('interpolation', 'LINEAR')
            require(interpolation in ('LINEAR', 'STEP'), 'GLB interpolation unsupported')
            self.tracks[key] = times, values, interpolation

    def accessor(self, index):
        a = self.doc['accessors'][index]
        require(not a.get('sparse') and not a.get('normalized'), 'unsupported accessor')
        view = self.doc['bufferViews'][a['bufferView']]
        require(view.get('buffer', 0) == 0, 'accessor buffer differs')
        scalar = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        fmt = struct.Struct('<' + scalar*width)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = view.get('byteStride', fmt.size)
        end = start + (a['count']-1)*stride + fmt.size
        require(a['count'] > 0 and stride >= fmt.size and start >= 0 and end <= len(self.binary), 'accessor bounds')
        require(end <= view.get('byteOffset', 0) + view['byteLength'], 'accessor exceeds view')
        rows = [list(fmt.unpack_from(self.binary, start+i*stride)) for i in range(a['count'])]
        require(all(math.isfinite(v) for row in rows for v in row), 'nonfinite accessor')
        return rows

    def triangles(self, index):
        primitives = self.doc['meshes'][self.nodes[index]['mesh']]['primitives']
        require(len(primitives) == 1, 'one material primitive required')
        p = primitives[0]
        require(p.get('mode', 4) == 4, 'triangles required')
        positions = self.accessor(p['attributes']['POSITION'])
        normals = self.accessor(p['attributes']['NORMAL'])
        indices = [row[0] for row in self.accessor(p['indices'])]
        require(len(indices) % 3 == 0 and len(positions) == len(normals), 'mesh topology shape')
        require(all(0 <= i < len(positions) for i in indices), 'mesh index outside vertices')
        return [[positions[i] + normals[i] for i in indices[j:j+3]] for j in range(0, len(indices), 3)]

    def material(self, index):
        p, = self.doc['meshes'][self.nodes[index]['mesh']]['primitives']
        m = self.doc['materials'][p['material']]
        values = m['pbrMetallicRoughness']
        return {'baseColorFactor': values.get('baseColorFactor', [1, 1, 1, 1]),
                'metallicFactor': values.get('metallicFactor', 1), 'roughnessFactor': values.get('roughnessFactor', 1),
                'alpha': values.get('baseColorFactor', [1, 1, 1, 1])[3], 'double_sided': m.get('doubleSided', False)}

    def sample(self, index, kind, time, default):
        if (index, kind) not in self.tracks:
            return default
        times, values, interpolation = self.tracks[index, kind]
        i = max(0, min(bisect.bisect_right(times, time)-1, len(times)-1))
        if i == len(times)-1 or interpolation == 'STEP':
            return values[i]
        u = (time-times[i])/(times[i+1]-times[i])
        a, b = values[i], values[i+1]
        if kind != 'rotation':
            return [(1-u)*x+u*y for x, y in zip(a, b)]
        dot = sum(x*y for x, y in zip(a, b))
        if dot < 0:
            b, dot = [-x for x in b], -dot
        if dot < 0.9995:
            theta = math.acos(min(1, dot))
            result = [(math.sin((1-u)*theta)*x+math.sin(u*theta)*y)/math.sin(theta) for x, y in zip(a, b)]
        else:
            result = [(1-u)*x+u*y for x, y in zip(a, b)]
        norm = math.sqrt(sum(x*x for x in result))
        return [x/norm for x in result]

    def pose(self, index, time):
        node = self.nodes[index]
        p = self.sample(index, 'translation', time, node.get('translation', [0, 0, 0]))
        xyzw = self.sample(index, 'rotation', time, node.get('rotation', [0, 0, 0, 1]))
        scale = self.sample(index, 'scale', time, node.get('scale', [1, 1, 1]))
        return p, [xyzw[3], *xyzw[:3]], scale


def validate_inputs(directory):
    directory = Path(directory)
    for name, expected in INPUTS['files'].items():
        require(identity(directory/name) == expected, 'input binding differs: ' + name)
    semantic = json.loads((directory/'after.semantic.json').read_text())
    reference = json.loads((directory/'after.reference.json').read_text())
    bundle = json.loads((directory/'after.program.bundle.json').read_text())
    proof = json.loads((directory/'proof.json').read_text())
    workflow = json.loads((directory/'workflow.json').read_text())
    require(bundle['entry']['source'].encode() == (directory/'after.main.ok').read_bytes(), 'entry/source equality')
    require(len(bundle['modules']) == 1 and bundle['modules'][0]['source'].encode() == (directory/'hinges.ok').read_bytes(), 'dependency/source equality')
    require(semantic['binding']['accepted_program_revision'] == reference['program_revision'] == proof['after_program_revision'] == REVISION, 'accepted revision differs')
    artifact_hash = 'sha256:' + INPUTS['files']['after.glb']['sha256']
    require(semantic['binding']['artifact']['sha256'] == reference['artifact_sha256'] == proof['after_artifact_sha256'] == artifact_hash, 'artifact binding differs')
    require(proof['status'] == workflow['status'] == 'passed', 'retained acceptance evidence failed')
    require(any(e['request']['operation'] == 'edit' and e['response_summary'].get('status') == 'succeeded' and e['response_summary'].get('accepted_program_revision') == REVISION for e in workflow['exchanges']), 'actual accepted edit missing')
    require(tuple(x['time_seconds'] for x in reference['samples']) == TIMES, 'frozen sample times differ')
    reader = GlbReader((directory/'after.glb').read_bytes())
    objects = semantic['objects']
    require(len(objects) == 18 and len({canonical(o['element_id']) for o in objects}) == 18, 'semantic ID inventory')
    require({o['path'] for o in objects} == set(reader.names), 'semantic/node names differ')
    for obj in objects:
        n = reader.nodes[obj['geometry_binding']['node']]
        require(n['name'] == obj['path'] and n['extras']['ontokin']['element_id'] == obj['element_id'], 'node/semantic identity differs')
    return semantic, reference, reader


def validate_build():
    require(identity(BUILD['executable']['path']) == {k: BUILD['executable'][k] for k in ('bytes', 'sha256')}, 'Blender executable changed')
    root = Path(BUILD['importer_root'])
    require({str(p) for p in root.rglob('*.py')} == {r['path'] for r in BUILD['importer_python_files']}, 'importer source inventory changed')
    for row in BUILD['importer_python_files']:
        require(identity(row['path']) == {k: row[k] for k in ('bytes', 'sha256')}, 'importer source changed: ' + row['path'])


def triangle_key(triangle):
    return tuple(math.floor(sum(vertex[k] for vertex in triangle)/3/MESH_EPS) for k in range(3))


def checked_triangles(triangles):
    require(isinstance(triangles, list), 'triangle inventory type')
    for triangle in triangles:
        require(isinstance(triangle, list) and len(triangle) == 3, 'triangle vertex count')
        for vertex in triangle:
            finite_vector(vertex, 6, 'triangle vertex/normal')
    return triangles


def compare_triangles(actual, expected, label):
    # A tolerance-aware one-to-one match avoids treating rounding buckets as
    # equality. Adjacent centroid buckets cover the permitted position error.
    require(len(actual) == len(expected), label + ': triangle inventory')
    checked_triangles(actual)
    checked_triangles(expected)
    buckets = {}
    for i, triangle in enumerate(expected):
        buckets.setdefault(triangle_key(triangle), set()).add(i)
    for triangle in actual:
        key = triangle_key(triangle)
        found = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bucket = (key[0]+dx, key[1]+dy, key[2]+dz)
                    for i in sorted(buckets.get(bucket, ())):
                        target = expected[i]
                        if any(all(abs(a-b) <= MESH_EPS for row, goal in zip(triangle[shift:]+triangle[:shift], target) for a, b in zip(row, goal)) for shift in range(3)):
                            found = (bucket, i)
                            break
                    if found is not None:
                        break
                if found is not None:
                    break
            if found is not None:
                break
        require(found is not None, label + ': triangle position/normal/winding differs')
        buckets[found[0]].remove(found[1])


def validate_observations(report, semantic, reference, reader):
    require(report['schema'] == 'ontokin.c211.observations/0.1', 'observation schema')
    require(report['build']['version'] == BUILD['version'] and report['build']['build_hash'] == BUILD['build_hash'] and report['build']['executable_sha256'] == BUILD['executable']['sha256'], 'observed Blender build')
    require(report['input_sha256'] == {n: v['sha256'] for n, v in INPUTS['files'].items()}, 'observed input bindings')
    require(report['units'] == {'system': 'METRIC', 'scale_length': 1.0, 'length_unit': 'METERS'}, 'native units differ')
    require(report['physics_world'] is False, 'unexpected native physics')
    settings = report['import_settings']
    require(set(settings) == set(BUILD['importer_properties']), 'observed importer setting inventory')
    for key, row in BUILD['importer_properties'].items():
        if key == 'filepath':
            require(Path(settings[key]).is_absolute() and Path(settings[key]).name == 'after.glb', 'observed import filepath')
        else:
            require(settings[key] == row['default'], 'observed importer setting differs: ' + key)
    require(report['semantic_text'] == report['scene_mapping_json'] == canonical(semantic), 'complete sidecar mapping differs')
    expected = {o['path']: o for o in semantic['objects']}
    rows = report['objects']
    require(len(rows) == 18 and Counter(o['name'] for o in rows) == Counter(expected.keys()), 'native object names missing or duplicate')
    raw_extras = report['native_extras_before_mapping']
    require(set(raw_extras) == set(expected), 'raw imported metadata inventory differs')
    triangle_count = 0
    for row in rows:
        name = row['name']
        obj = expected[name]
        index = obj['geometry_binding']['node']
        require(row['type'] == 'MESH' and row['parent'] is None, name + ': native object/parent')
        require(not row['constraints'] and not row['modifiers'] and row['rigid_body'] is False, name + ': unselected native behavior')
        require(row['semantic_json'] == canonical(obj), name + ': object semantic mapping')
        require(row['element_id_json'] == canonical(obj['element_id']) and row['accepted_revision'] == REVISION, name + ': ID/revision mapping')
        compare_triangles(row['triangles'], reader.triangles(index), name)
        require(len(row['triangles_raw_blender']) == len(row['triangles']), name + ': missing raw triangle observations')
        checked_triangles(row['triangles_raw_blender'])
        # Independently check that the reported source-basis values actually
        # correspond to the retained raw Blender coordinates and normals.
        for raw, converted in zip(row['triangles_raw_blender'], row['triangles']):
            for rv, cv in zip(raw, converted):
                close_vector(cv, [rv[0], rv[2], -rv[1], rv[3], rv[5], -rv[4]], MESH_EPS, name + ': coordinate conversion')
        require(len(row['materials']) == 1 and len(row['triangle_material_indices']) == len(row['triangles']) and set(row['triangle_material_indices']) == {0}, name + ': native material slots')
        material, expected_material = row['material'], reader.material(index)
        raw_material = row['materials'][0]
        require(raw_material['use_nodes'] is True and raw_material['bsdf_type'] == 'BSDF_PRINCIPLED', name + ': actual Principled node')
        require(raw_material['inputs'] == {'Base Color': material['baseColorFactor'], 'Metallic': material['metallicFactor'], 'Roughness': material['roughnessFactor'], 'Alpha': material['alpha']}, name + ': raw/material summary differs')
        require(raw_material['use_backface_culling'] is not material['double_sided'], name + ': raw/material culling differs')
        close_vector(material['baseColorFactor'], expected_material['baseColorFactor'], MATERIAL_EPS, name + ': RGBA')
        for key in ('metallicFactor', 'roughnessFactor', 'alpha'):
            close_vector([material[key]], [expected_material[key]], MATERIAL_EPS, name + ': ' + key)
        require(material['double_sided'] == expected_material['double_sided'], name + ': double-sided state')
        triangle_count += len(row['triangles'])
    require(tuple(s['time_seconds'] for s in report['samples']) == TIMES, 'observed sample inventory')
    poses = 0
    for sample, fixed in zip(report['samples'], reference['samples']):
        t = float(sample['time_seconds'])
        require(abs(sample['frame']/60-t) <= 0.000001, 'native sample time')
        require(set(sample['objects']) == set(expected), 'sample objects differ')
        for name, observed in sample['objects'].items():
            index = expected[name]['geometry_binding']['node']
            decoded_p, decoded_q, decoded_s = reader.pose(index, t)
            target = fixed['objects'][name]
            close_vector(decoded_p, target['position_m'], POSITION_EPS, name + ': decoded/frozen position')
            require(quaternion_angle(decoded_q, target['orientation_wxyz']) <= ANGLE_EPS, name + ': decoded/frozen rotation')
            close_vector(observed['position_m'], decoded_p, POSITION_EPS, name + ': native/decoded position')
            close_vector(observed['position_m'], target['position_m'], POSITION_EPS, name + ': native/frozen position')
            require(quaternion_angle(observed['orientation_wxyz'], decoded_q) <= ANGLE_EPS, name + ': native/decoded rotation')
            require(quaternion_angle(observed['orientation_wxyz'], target['orientation_wxyz']) <= ANGLE_EPS, name + ': native/frozen rotation')
            close_vector(observed['scale'], decoded_s, MESH_EPS, name + ': native scale')
            close_vector(observed['scale'], [1, 1, 1], MESH_EPS, name + ': nonunit scale')
            reconstructed = matrix(observed['position_m'], observed['orientation_wxyz'], observed['scale'])
            require(len(observed['matrix']) == 4 and len(observed['matrix_world_blender']) == 4, 'matrix shape')
            # C^-1 M C with C mapping x,y,z to x,-z,y.
            raw = observed['matrix_world_blender']
            perm, signs = [0, 2, 1, 3], [1, 1, -1, 1]
            converted = [[signs[i]*signs[j]*raw[perm[i]][perm[j]] for j in range(4)] for i in range(4)]
            for a, b, c in zip(observed['matrix'], reconstructed, converted):
                close_vector(a, b, MESH_EPS, name + ': matrix/pose consistency')
                close_vector(a, c, MESH_EPS, name + ': raw/source matrix conversion')
            poses += 1
    native_types = Counter(type(x.get('ontokin')).__name__ for x in raw_extras.values())
    return {'status': 'passed', 'objects': 18, 'triangles': triangle_count, 'poses': poses,
            'times_seconds': list(TIMES), 'native_ontokin_property_types': dict(native_types),
            'semantic_mapping': 'explicit canonical JSON strings; separate from raw native extras',
            'losses': feature_treatment(semantic, native_types), 'full_release': False}


def feature_treatment(semantic, native_types):
    rows = []
    native = {'primitive_geometry': 'native triangulated geometry', 'materials': 'native Principled material inputs', 'world_motion': 'native baked animation'}
    for feature in semantic['features']:
        key = feature['feature']
        if key in ('action_execution', 'live_physics', 'source_reconstruction'):
            destination, note = 'unsupported', feature['reason']
        elif key in native:
            destination, note = feature['treatment'], native[key]
        else:
            destination, note = 'metadata_only', 'Exact canonical sidecar attached by C211; no executable destination meaning inferred.'
        rows.append({'feature': key, 'source_treatment': feature['treatment'], 'destination_treatment': destination, 'reason': note})
    rows.append({'feature': 'stock_importer_structured_extras', 'destination_treatment': 'observed',
                 'native_types': dict(native_types), 'reason': 'Raw imported properties are retained separately; strings are not parsed or credited as structured semantic preservation.'})
    return rows
