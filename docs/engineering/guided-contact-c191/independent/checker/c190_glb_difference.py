"""Inspect every GLB field and recorded vertex when a native result is projected."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np


def decode(path):
    raw = Path(path).read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size, kind = struct.unpack_from('<I4s', raw, 12)
    assert kind == b'JSON'
    doc = json.loads(raw[20:20+size])
    size_b, kind = struct.unpack_from('<I4s', raw, 20+size)
    assert kind == b'BIN\0' and size_b == len(raw)-28-size
    return doc, raw[28+size:]


def fields(a, b, path=''):
    if type(a) != type(b):
        return [{'path': path, 'before': a, 'after': b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(set(a)|set(b)):
            if key not in a or key not in b:
                result.append({'path': path+'/'+key, 'before': a.get(key), 'after': b.get(key),
                               'beforePresent': key in a, 'afterPresent': key in b})
            else:
                result += fields(a[key], b[key], path+'/'+key)
        return result
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'path': path, 'before': a, 'after': b}]
        return [v for j in range(len(a)) for v in fields(a[j], b[j], path+'/'+str(j))]
    return [] if a == b else [{'path': path, 'before': a, 'after': b}]


def array(doc, blob, index):
    accessor = doc['accessors'][index]
    assert 'sparse' not in accessor
    view = doc['bufferViews'][accessor['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    dtype = np.dtype({5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[accessor['componentType']])
    start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
    stride = view.get('byteStride', width*dtype.itemsize)
    values = np.ndarray((accessor['count'], width), dtype, blob, start, (stride, dtype.itemsize))
    return values.astype(np.float64 if dtype.kind == 'f' else np.int64)


def quaternion_matrix(q):
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q.T
    return np.stack([1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w),
                     2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w),
                     2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)], axis=1).reshape(-1, 3, 3)


def states(doc, blob, times):
    nodes = doc['nodes']
    parents = {child: i for i, n in enumerate(nodes) for child in n.get('children', [])}
    tracks = {}
    animation, = doc['animations']
    for channel in animation['channels']:
        sampler = animation['samplers'][channel['sampler']]
        assert sampler.get('interpolation', 'LINEAR') == 'LINEAR'
        t = array(doc, blob, sampler['input'])[:, 0]
        data = array(doc, blob, sampler['output'])
        target = channel['target']
        if target['path'] == 'rotation':
            data /= np.linalg.norm(data, axis=1, keepdims=True)
            low = np.clip(np.searchsorted(t, times, side='right')-1, 0, len(t)-2)
            u = np.clip((times-t[low])/(t[low+1]-t[low]), 0, 1)[:, None]
            a, b = data[low], data[low+1]
            dot = np.sum(a*b, axis=1, keepdims=True)
            b = np.where(dot < 0, -b, b)
            orth = b-np.abs(dot)*a
            length = np.linalg.norm(orth, axis=1, keepdims=True)
            angle = np.arctan2(length, np.abs(dot))
            direction = np.divide(orth, length, out=np.zeros_like(orth), where=length>0)
            values = np.cos(u*angle)*a+np.sin(u*angle)*direction
        else:
            values = np.stack([np.interp(times, t, data[:, k]) for k in range(data.shape[1])], axis=1)
        tracks[(target['node'], target['path'])] = values
    cache = {}

    def world(index):
        if index in cache:
            return cache[index]
        node = nodes[index]
        if 'matrix' in node:
            local = np.broadcast_to(np.array(node['matrix']).reshape(4, 4).T, (len(times), 4, 4)).copy()
        else:
            def prop(key, default):
                return tracks.get((index, key), np.broadcast_to(node.get(key, default), (len(times), len(default))))
            local = np.zeros((len(times), 4, 4))
            local[:, 3, 3] = 1
            local[:, :3, 3] = prop('translation', [0, 0, 0])
            local[:, :3, :3] = quaternion_matrix(prop('rotation', [0, 0, 0, 1]))*prop('scale', [1, 1, 1])[:, None, :]
        cache[index] = world(parents[index]) @ local if index in parents else local
        return cache[index]
    result = {}
    for i, node in enumerate(nodes):
        if 'mesh' not in node:
            continue
        local = np.concatenate([array(doc, blob, p['attributes']['POSITION'])
                                for p in doc['meshes'][node['mesh']]['primitives']])
        matrix = world(i)
        vertices = np.einsum('tij,vj->tvi', matrix[:, :3, :3], local)+matrix[:, None, :3, 3]
        result[node['name']] = {'verticesMm': 1000*vertices, 'matrix': matrix,
                                'boundsMm': np.stack([vertices.min(1), vertices.max(1)], axis=1)*1000}
    return result


def compare(raw_path, final_path, native_path=None):
    raw_doc, raw_blob = decode(raw_path)
    final_doc, final_blob = decode(final_path)
    times = np.unique(np.concatenate([array(doc, blob, sampler['input'])[:, 0]
        for doc, blob in ((raw_doc, raw_blob), (final_doc, final_blob))
        for animation in doc['animations'] for sampler in animation['samplers']]))
    a, b = states(raw_doc, raw_blob, times), states(final_doc, final_blob, times)
    assert set(a) == set(b)
    parts = {}
    for name in a:
        av, bv = a[name]['verticesMm'], b[name]['verticesMm']
        assert av.shape == bv.shape, 'Vertex correspondence changed: '+name
        distances = np.linalg.norm(av-bv, axis=2)
        index = np.unravel_index(np.argmax(distances), distances.shape)
        relative = np.einsum('tji,tjk->tik', a[name]['matrix'][:, :3, :3], b[name]['matrix'][:, :3, :3])
        angle = np.arccos(np.clip((np.trace(relative, axis1=1, axis2=2)-1)/2, -1, 1))
        parts[name] = {'recordedStatesCompared': len(times), 'verticesPerState': av.shape[1],
            'maximumRecordedVertexDistanceMm': float(distances.max()),
            'maximumAtS': float(times[index[0]]), 'maximumVertexIndex': int(index[1]),
            'maximumRecordedBoundsComponentDifferenceMm': float(np.max(np.abs(a[name]['boundsMm']-b[name]['boundsMm']))),
            'maximumRecordedWorldOriginDifferenceMm': float(1000*np.linalg.norm(a[name]['matrix'][:, :3, 3]-b[name]['matrix'][:, :3, 3], axis=1).max()),
            'maximumRecordedBasisAngleDegrees': float(np.rad2deg(angle.max()))}
    native_max = None
    if native_path is not None:
        native = json.loads(Path(native_path).read_text())
        assert len(native) == len(times)
        assert max(abs(float(record['time_s'])-t) for record, t in zip(native, times)) < 1e-6
        blender_to_gltf = np.array([[1., 0, 0, 0], [0, 0, 1., 0], [0, -1., 0, 0], [0, 0, 0, 1.]])
        gltf_to_blender = np.linalg.inv(blender_to_gltf)
        native_max = 0.0
        named = {node['name']: node for node in raw_doc['nodes']}
        for name in a:
            local = np.concatenate([array(raw_doc, raw_blob, p['attributes']['POSITION'])
                for p in raw_doc['meshes'][named[name]['mesh']]['primitives']])
            native_m = np.array([record['matrices_blender_m'][name] for record in native])
            native_g = blender_to_gltf @ native_m @ gltf_to_blender
            vertices = 1000*(np.einsum('tij,vj->tvi', native_g[:, :3, :3], local)+native_g[:, None, :3, 3])
            difference = float(np.linalg.norm(vertices-b[name]['verticesMm'], axis=2).max())
            parts[name]['maximumNativeSampleToFinalVertexDistanceMm'] = difference
            native_max = max(native_max, difference)
    # Certify this specific projection continuously, rather than extending a
    # sample-only comparison to the native solver's unrecorded substeps.
    lanes = {}
    raw_tracks, final_tracks = {}, {}
    for doc, blob, tracks in ((raw_doc, raw_blob, raw_tracks), (final_doc, final_blob, final_tracks)):
        for channel in doc['animations'][0]['channels']:
            sampler = doc['animations'][0]['samplers'][channel['sampler']]
            target = channel['target']
            name = doc['nodes'][target['node']]['name']
            tracks[name, target['path']] = array(doc, blob, sampler['output'])
    for lane in ('left', 'right'):
        car, shoe = lane+'_carriage', lane+'_shoe'
        x, y = raw_tracks[car, 'translation'], final_tracks[car, 'translation']
        assert np.array_equal(x[:, 0], y[:, 0]), 'Native X samples changed'
        assert np.array_equal(y[:, 1:], np.broadcast_to(x[0, 1:], y[:, 1:].shape))
        assert (car, 'rotation') not in final_tracks
        assert np.all(b[car]['matrix'][:, :3, :3] == np.eye(3))
        q = raw_tracks.get((car, 'rotation'), np.broadcast_to([0., 0, 0, 1.], (len(times), 4))).copy()
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        angle = 2*np.arctan2(np.linalg.norm(q[:, :3], axis=1), np.abs(q[:, 3]))
        dot = np.sum(q[:-1]*q[1:], axis=1)
        orth = q[1:]-dot[:, None]*q[:-1]
        arc = 2*np.arctan2(np.linalg.norm(orth, axis=1), np.abs(dot))
        theta = np.minimum(np.pi, np.minimum(angle[:-1], angle[1:])+arc+1e-12)
        origin = a[car]['matrix'][0, :3, 3]*1000
        initial_basis = a[car]['matrix'][0, :3, :3]
        local = np.concatenate([(a[name]['verticesMm'][0]-origin) @ np.linalg.inv(initial_basis).T for name in (car, shoe)])
        radius = float(np.linalg.norm(local, axis=1).max())
        transverse = 1000*np.linalg.norm(x[:, 1:]-y[:, 1:], axis=1)
        bounds = np.maximum(transverse[:-1], transverse[1:])+2*radius*np.sin(theta/2)+1e-9
        lanes[lane] = {'localVertexRadiusMm': radius, 'intervalCount': len(bounds),
            'maximumContinuousRawToFinalVertexDeviationBoundMm': float(bounds.max()),
            'nativeXFloatValuesIdentical': True}
    accessors = []
    assert len(raw_doc['accessors']) == len(final_doc['accessors']), 'Accessor structure changed'
    for j in range(len(raw_doc['accessors'])):
        x, y = array(raw_doc, raw_blob, j), array(final_doc, final_blob, j)
        assert x.shape == y.shape, 'Accessor shape changed'
        rows = np.flatnonzero(np.any(x != y, axis=1))
        if len(rows):
            accessors.append({'accessor': j, 'changedRows': len(rows),
                'values': [{'row': int(k), 'before': x[k].tolist(), 'after': y[k].tolist()} for k in rows]})
    geometry_accessors = set()
    for mesh in raw_doc['meshes']:
        for p in mesh['primitives']:
            geometry_accessors.update(p['attributes'].values())
            if 'indices' in p:
                geometry_accessors.add(p['indices'])
    changed_accessors = {v['accessor'] for v in accessors}
    channels = []
    for channel in raw_doc['animations'][0]['channels']:
        sampler = raw_doc['animations'][0]['samplers'][channel['sampler']]
        if sampler['output'] in changed_accessors or sampler['input'] in changed_accessors:
            channels.append({'node': raw_doc['nodes'][channel['target']['node']]['name'],
                             'path': channel['target']['path'], 'inputAccessor': sampler['input'], 'outputAccessor': sampler['output']})
    return {'version': 'C190-independent-raw-final-audit-1',
        'rawSha256': hashlib.sha256(Path(raw_path).read_bytes()).hexdigest(),
        'finalSha256': hashlib.sha256(Path(final_path).read_bytes()).hexdigest(),
        'nativeTraceSha256': hashlib.sha256(Path(native_path).read_bytes()).hexdigest() if native_path else None,
        'binaryIdentical': raw_blob == final_blob, 'jsonFieldChanges': fields(raw_doc, final_doc),
        'logicalAccessorChanges': accessors, 'changedAnimationChannels': channels,
        'staticMeshesIdentical': raw_doc['meshes'] == final_doc['meshes'],
        'materialsIdentical': raw_doc.get('materials') == final_doc.get('materials'),
        'geometryAccessorValuesIdentical': not bool(geometry_accessors & changed_accessors),
        'sampleTimesComparedS': times.tolist(), 'parts': parts,
        'maximumRecordedVertexDistanceMm': max(p['maximumRecordedVertexDistanceMm'] for p in parts.values()),
        'maximumNativeSampleToFinalVertexDistanceMm': native_max,
        'continuousProjectionBounds': lanes,
        'maximumContinuousRawToFinalVertexDeviationBoundMm': max(v['maximumContinuousRawToFinalVertexDeviationBoundMm'] for v in lanes.values()),
        'scope': 'All JSON fields, all logical accessor elements, every recorded vertex and a conservative interval bound on raw GLB LINEAR/SLERP playback; native substep poses are not covered',
        'continuousBoundMethod': 'Identical linear X tracks. Endpoint norm bounds removed transverse displacement. SO(3) triangle inequality bounds each interpolated orientation by the smaller endpoint angle plus the endpoint arc; 2*r*sin(theta/2) bounds every carriage/shoe vertex displacement.',
        'betweenKeyGeometryDeviationCertified': True}
