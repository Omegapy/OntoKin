"""Project native GLB playback onto its specified frictionless X guide.

C191 adaptation of the preserved C190 projection: budget checkpoints and explicit bound failures.
Only final playback is changed. Raw GLB, native scene, solver poses, contact
response and all native X samples are retained. There is no stop-time/travel law.

Usage: python3 map_playback.py raw.glb final.glb post-export.json native-transforms.json
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys


def decode(path):
    data = path.read_bytes()
    assert struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data))
    cursor = 12
    model, binary = None, None
    while cursor < len(data):
        size, kind = struct.unpack_from('<II', data, cursor)
        payload = data[cursor + 8:cursor + 8 + size]
        if kind == 0x4E4F534A:
            model = json.loads(payload)
        elif kind == 0x004E4942:
            binary = bytearray(payload)
        else:
            raise ValueError('Unexpected GLB chunk')
        cursor += 8 + size
    return data, model, binary


def accessor(model, binary, index, budget=None):
    item = model['accessors'][index]
    assert item['componentType'] == 5126
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']]
    if budget:
        budget.charge('projection_accessor_scalars', item['count'] * width)
    view = model['bufferViews'][item['bufferView']]
    layout = struct.Struct('<' + 'f' * width)
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', layout.size)
    rows = [layout.unpack_from(binary, start + i * stride) for i in range(item['count'])]
    return rows, start, stride


def encode(model, binary):
    encoded = json.dumps(model, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    encoded += b' ' * (-len(encoded) % 4)
    binary = bytes(binary) + b'\x00' * (-len(binary) % 4)
    length = 12 + 8 + len(encoded) + 8 + len(binary)
    return (struct.pack('<4sII', b'glTF', 2, length)
            + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
            + struct.pack('<II', len(binary), 0x004E4942) + binary)


def norm(v):
    return math.sqrt(sum(x*x for x in v))


def normalize(q):
    n = norm(q)
    return [x / n for x in q]


def angle(q):
    q = normalize(q)
    return 2 * math.atan2(norm(q[:3]), abs(q[3]))


def arc(q, p):
    q, p = normalize(q), normalize(p)
    return 2 * math.acos(min(1.0, abs(sum(x*y for x,y in zip(q,p)))))


def rotate(q, point):
    x,y,z,w = normalize(q)
    matrix = [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
              [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
              [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    return [sum(matrix[i][k]*point[k] for k in range(3)) for i in range(3)]


def mapping_geometry(raw_model, raw_binary, final_model, final_binary, native, budget=None):
    """All recorded poses plus a conservative continuous playback interval bound."""
    nodes = raw_model['nodes']
    names = {node['name']:i for i,node in enumerate(nodes)}
    vertices = {}
    for name,index in names.items():
        primitive, = raw_model['meshes'][nodes[index]['mesh']]['primitives']
        vertices[name] = accessor(raw_model, raw_binary, primitive['attributes']['POSITION'], budget)[0]
    tracks = {}
    for channel in raw_model['animations'][0]['channels']:
        sampler = raw_model['animations'][0]['samplers'][channel['sampler']]
        tracks[(nodes[channel['target']['node']]['name'],channel['target']['path'])] = accessor(raw_model,raw_binary,sampler['output'], budget)[0]
    assert final_model['nodes'] == raw_model['nodes']
    assert final_model['meshes'] == raw_model['meshes']
    final_tracks = {}
    for channel in final_model['animations'][0]['channels']:
        assert channel['target']['path'] == 'translation'
        sampler = final_model['animations'][0]['samplers'][channel['sampler']]
        final_tracks[(nodes[channel['target']['node']]['name'], 'translation')] = accessor(final_model, final_binary, sampler['output'], budget)[0]
    max_native_final = 0.0
    max_raw_final_sample = 0.0
    per_part = {}
    lane_bounds = {}
    for lane in ('left','right'):
        name = lane + '_carriage'
        translations = tracks[(name,'translation')]
        rotations = tracks.get((name,'rotation'), [(0,0,0,1)]*len(translations))
        all_local = []
        for part in (name,lane+'_shoe'):
            offset = (0,0,0) if part == name else nodes[names[part]]['translation']
            all_local += [[p[a]+offset[a] for a in range(3)] for p in vertices[part]]
        radius = max(norm(p) for p in all_local)
        displacement = [norm([0,t[1]-translations[0][1],t[2]-translations[0][2]]) for t in translations]
        interval_bounds = []
        for i in range(len(translations)-1):
            if budget:
                budget.charge('projection_intervals')
            # Triangle inequality on SO(3): every SLERP orientation is at most
            # min(endpoint-angle-to-identity) + endpoint-arc from identity.
            theta = min(math.pi, min(angle(rotations[i]),angle(rotations[i+1])) + arc(rotations[i],rotations[i+1]))
            interval_bounds.append(1000*(max(displacement[i],displacement[i+1])+2*radius*math.sin(theta/2)))
        lane_bounds[lane] = {'carriage_and_shoe_max_local_radius_mm':radius*1000,
                            'continuous_raw_to_final_vertex_deviation_upper_bound_mm':max(interval_bounds),
                            'intervals_checked':len(interval_bounds)}
    for part,index in names.items():
        moving = part.endswith('_carriage') or part.endswith('_shoe')
        lane = part.split('_')[0] if moving else None
        local_offset = nodes[index].get('translation',[0,0,0]) if part.endswith('_shoe') else [0,0,0]
        worst_native = 0.0
        worst_raw = 0.0
        for sample_index,record in enumerate(native):
            native_matrix = record['matrices_blender_m'][part]
            if moving:
                carriage_name = lane+'_carriage'
                translation = tracks[(carriage_name,'translation')][sample_index]
                final_translation = final_tracks[(carriage_name,'translation')][sample_index]
                rotation = tracks.get((carriage_name,'rotation'),[(0,0,0,1)]*len(native))[sample_index]
            for vertex in vertices[part]:
                if budget:
                    budget.charge('projection_vertices')
                if moving:
                    local = [vertex[a]+local_offset[a] for a in range(3)]
                    final_point = [final_translation[a]+local[a] for a in range(3)]
                    rotated = rotate(rotation,local)
                    raw_point = [translation[a]+rotated[a] for a in range(3)]
                else:
                    final_point = [vertex[a]+nodes[index].get('translation',[0,0,0])[a] for a in range(3)]
                    raw_point = final_point
                blender_vertex = [vertex[0],-vertex[2],vertex[1]]
                point_b = [sum(native_matrix[a][k]*blender_vertex[k] for k in range(3))+native_matrix[a][3] for a in range(3)]
                native_point = [point_b[0],point_b[2],-point_b[1]]
                worst_native=max(worst_native,1000*norm([native_point[a]-final_point[a] for a in range(3)]))
                worst_raw=max(worst_raw,1000*norm([raw_point[a]-final_point[a] for a in range(3)]))
        per_part[part]={'max_native_sample_to_final_vertex_distance_mm':worst_native,
                        'max_raw_sample_to_final_vertex_distance_mm':worst_raw}
        max_native_final=max(max_native_final,worst_native)
        max_raw_final_sample=max(max_raw_final_sample,worst_raw)
    return {'native_sample_count':len(native),'native_sample_cadence_hz':240,
            'native_sample_to_final_max_vertex_distance_mm':max_native_final,
            'raw_sample_to_final_max_vertex_distance_mm':max_raw_final_sample,
            'continuous_raw_export_to_final_full_clip_bound_mm':max(v['continuous_raw_to_final_vertex_deviation_upper_bound_mm'] for v in lane_bounds.values()),
            'per_part':per_part,'per_lane_continuous_bound':lane_bounds,
            'continuous_bound_method':'Per each of 480 intervals, preserve identical linear X samples, bound removed transverse translation by endpoint norm, and bound rotated vertex displacement by 2*r*sin(theta/2), where theta is min(endpoint orientation angles)+endpoint SO(3) arc. This covers the full LINEAR/SLERP raw GLB playback clip.',
            'scope_limit':'The native solver has unrecorded substeps. All 481 recorded native poses are measured directly. The continuous bound covers interpolated raw native-export playback against final playback, not unknown substep native poses.'}


def map_playback(raw_path, final_path, report_path, native_path, budget=None):
    raw_bytes, model, binary = decode(raw_path)
    raw_model, raw_binary = copy.deepcopy(model), bytes(binary)
    assert len(model['animations']) == 1
    animation = model['animations'][0]
    nodes = model['nodes']
    changes = []
    retained = []
    translation_changes = []
    preserved_x = {}
    for channel_index,channel in enumerate(animation['channels']):
        target = channel['target']
        name = nodes[target['node']]['name']
        sampler = animation['samplers'][channel['sampler']]
        assert sampler['interpolation'] == 'LINEAR'
        rows,start,stride = accessor(model,binary,sampler['output'], budget)
        if target['path'] == 'rotation':
            assert name.endswith('_carriage')
            assert angle(rows[0]) < 1e-12
            changes.append({'json_path':f'animations[0].channels[{channel_index}]','operation':'remove','old':copy.deepcopy(channel),'reason':'Final playback uses the initial fixed orientation; native rotation samples remain untouched in raw GLB and native records.'})
            continue
        assert target['path'] == 'translation' and name.endswith('_carriage')
        x_before = b''.join(struct.pack('<f',row[0]) for row in rows)
        for sample_index,row in enumerate(rows):
            for axis in (1,2):
                if row[axis] != rows[0][axis]:
                    byte_offset = start + sample_index*stride + axis*4
                    struct.pack_into('<f',binary,byte_offset,rows[0][axis])
                    translation_changes.append({'accessor':sampler['output'],'node':name,'sample_index':sample_index,'axis':'XYZ'[axis],'buffer_byte_offset':byte_offset,'old_m':row[axis],'new_m':rows[0][axis]})
        after,_,_ = accessor(model,binary,sampler['output'], budget)
        x_after=b''.join(struct.pack('<f',row[0]) for row in after)
        assert x_before == x_after
        preserved_x[name]={'samples':len(rows),'float32_x_bytes_sha256':hashlib.sha256(x_before).hexdigest(),'bit_identical_raw_and_final':True}
        retained.append(channel)
    animation['channels'] = retained
    # Unused rotation sampler/accessor/buffer bytes are intentionally retained;
    # deleting them would create unrelated index and buffer remapping changes.
    final_bytes = encode(model,binary)
    final_path.write_bytes(final_bytes)
    native = json.loads(native_path.read_text())
    geometry = mapping_geometry(raw_model,raw_binary,model,binary,native,budget)
    if geometry['native_sample_to_final_max_vertex_distance_mm'] > .2 or geometry['continuous_raw_export_to_final_full_clip_bound_mm'] > .2:
        (report_path.parent / 'mapping-failure.json').write_text(json.dumps(geometry, indent=2) + '\n')
        raise ValueError('Mapping exceeds 0.2 mm: native=' + str(geometry['native_sample_to_final_max_vertex_distance_mm']) + ', continuous=' + str(geometry['continuous_raw_export_to_final_full_clip_bound_mm']))
    report = {'raw_sha256':hashlib.sha256(raw_bytes).hexdigest(),'final_sha256':hashlib.sha256(final_bytes).hexdigest(),
              'mapping':'Final playback projected onto the specified fixed-orientation X guide. Every native carriage X sample is unchanged. No stopping law, time threshold, position limit, or contact-time substitution is introduced.',
              'json_field_changes':changes,'binary_float_field_changes':translation_changes,
              'preserved_x_tracks':preserved_x,'geometry_deviation':geometry,
              'unchanged':'Raw GLB, native scene, native solver records, mesh geometry, materials, node hierarchy, node initial transforms, all animation input times, all carriage X samples, all shoe local transforms.',
              'container_change':'JSON chunk reserialized and chunk/total byte lengths updated; BIN chunk length unchanged. Unused rotation sampler/accessor/data are retained as inert data, with no animation channel referencing them.'}
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'final':str(final_path),'native_sample_max_mm':geometry['native_sample_to_final_max_vertex_distance_mm'],'continuous_export_bound_mm':geometry['continuous_raw_export_to_final_full_clip_bound_mm'],'changed_float_fields':len(translation_changes),'removed_rotation_channels':len(changes)},indent=2))
    return report


if __name__ == '__main__':
    map_playback(*(Path(arg) for arg in sys.argv[1:]))
