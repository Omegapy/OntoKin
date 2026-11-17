#!/usr/bin/env python3
"""Read the two historical C210 GLBs independently of OntoKin and C255 code.

This is a review probe, not a new product or route reader. Expected values are
the C253 SCORING equations and pinned raw keyed-rack declarations. The probe
does not import the implementation under review, exporter, parser or oracle.
"""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import struct

TIMES = (0., .25, .5, .75, 1., 1.5, 2.)
SLOTS = {'first': [('lower', -.6), ('middle', 0.), ('upper', .6)],
         'second': [('bottom', -1.2), ('lower', -.6), ('middle', 0.), ('upper', .6), ('top', 1.2)]}


def split_glb(raw):
    magic, version, total = struct.unpack_from('<4sII', raw, 0)
    assert magic == b'glTF' and version == 2 and total == len(raw)
    chunks = []
    off = 12
    while off < len(raw):
        size, kind = struct.unpack_from('<II', raw, off)
        assert size % 4 == 0 and off + 8 + size <= len(raw)
        chunks.append((kind, off + 8, raw[off+8:off+8+size]))
        off += 8 + size
    assert off == len(raw) and len(chunks) == 2
    assert chunks[0][0] == 0x4E4F534A and chunks[1][0] == 0x004E4942
    return json.loads(chunks[0][2]), chunks[1][1], chunks[1][2]


def decode(gltf, payload, base, index):
    a = gltf['accessors'][index]
    v = gltf['bufferViews'][a['bufferView']]
    code, width = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4), 5121: ('B', 1)}[a['componentType']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    stride = v.get('byteStride', n * width)
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    result = [list(struct.unpack_from('<'+code*n, payload, start+i*stride)) for i in range(a['count'])]
    assert all(math.isfinite(float(x)) for row in result for x in row)
    return result, {'accessor': index, 'bufferView': a['bufferView'],
                    'absoluteFirstElementByte': base+start, 'stride': stride,
                    'elementBytes': n*width, 'count': a['count']}


def interpolate(a, b, f, rotation):
    if not rotation:
        return [x+(y-x)*f for x, y in zip(a, b)]
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(x*x for x in b))
    assert abs(na-1) <= 1e-6 and abs(nb-1) <= 1e-6
    a, b = [x/na for x in a], [x/nb for x in b]
    dot = sum(x*y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-x for x in b], -dot
    dot = min(1., max(-1., dot))
    if dot > .999999:
        q = [x+(y-x)*f for x, y in zip(a, b)]
        norm = math.sqrt(sum(x*x for x in q))
        return [x/norm for x in q]
    angle = math.acos(dot)
    denom = math.sin(angle)
    return [(x*math.sin((1-f)*angle)+y*math.sin(f*angle))/denom for x, y in zip(a, b)]


def sample(gltf, payload, base, channel, time):
    s = gltf['animations'][0]['samplers'][channel['sampler']]
    assert s.get('interpolation', 'LINEAR') == 'LINEAR'
    ts, ti = decode(gltf, payload, base, s['input'])
    vals, vi = decode(gltf, payload, base, s['output'])
    ts = [x[0] for x in ts]
    assert len(ts) == len(vals) and all(x < y for x, y in zip(ts, ts[1:]))
    assert ts[0] <= time <= ts[-1]
    left = max(0, bisect.bisect_right(ts, time)-1)
    right = min(left+1, len(ts)-1)
    fraction = 0. if left == right else (time-ts[left])/(ts[right]-ts[left])
    rotation = channel['target']['path'] == 'rotation'
    value = interpolate(vals[left], vals[right], fraction, rotation)
    return value, {'sampler': channel['sampler'], 'time': ti, 'value': vi,
                   'left': left, 'right': right, 'fraction': fraction}


def expected_ids():
    result = {}
    for rack, slots in SLOTS.items():
        result[("keyed-rack", "demo", rack)] = (rack, None, None, False)
        for key, y in slots:
            stem = ("keyed-rack", "demo", rack, "fingers", key)
            result[stem] = (rack, key, y, False)
            result[stem+("blade",)] = (rack, key, y, True)
    return result


def source_pose(spec, time, length):
    rack, key, y, blade = spec
    x = -1. if rack == 'first' else 1.
    yy = (.2*time if rack == 'first' else 0.) + (y if key else 0.)
    q = [1., 0., 0., 0.]
    if blade and rack == 'first' and key == 'middle':
        angle = math.pi/4*min(time, 1.)
        x += length*.5*math.cos(angle)
        yy += length*.5*math.sin(angle)
        q = [math.cos(angle/2), 0., 0., math.sin(angle/2)]
    elif blade:
        x += .3
    return [x, yy, 0.], q


def rotation_error(a, b):
    a = [x/math.sqrt(sum(v*v for v in a)) for x in a]
    b = [x/math.sqrt(sum(v*v for v in b)) for x in b]
    chord = min(math.sqrt(sum((x-y)**2 for x, y in zip(a, b))),
                math.sqrt(sum((x+y)**2 for x, y in zip(a, b))))
    return 4*math.asin(min(1., chord*.5))


def measure(path, length):
    raw = path.read_bytes()
    g, base, payload = split_glb(raw)
    expected = expected_ids()
    identities = [tuple(n['extras']['ontokin']['element_id']) for n in g['nodes']]
    assert len(identities) == 18 and len(set(identities)) == 18 and set(identities) == set(expected)
    assert g['scene'] == 0 and set(g['scenes'][0]['nodes']) == set(range(18))
    assert len(g['scenes'][0]['nodes']) == 18 and all(not n.get('children') for n in g['nodes'])
    channels = {(c['target']['node'], c['target']['path']): c for c in g['animations'][0]['channels']}
    assert len(channels) == len(g['animations'][0]['channels']) == 36
    result = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'geometry': [], 'poses': [], 'errors': {}}
    max_position = max_angle = max_geometry = 0.
    for ni, node in enumerate(g['nodes']):
        oid = identities[ni]
        spec = expected[oid]
        rack, key, yy, blade = spec
        node_meta = node['extras']['ontokin']
        assert tuple(node_meta['source_mapping']['element_id']) == oid
        assert g['extras']['ontokin']['program']['occurrences'][node_meta['path']] == node_meta['source_mapping']
        definition = (['entry', 'keyed-rack', 'definitions', 'rack'] if not key else
                      ['package', 'example.hinges', 'hinges', 'definitions', 'blade' if blade else 'finger'])
        assert node_meta['source_mapping']['definition_id'] == definition
        primitive = g['meshes'][node['mesh']]['primitives'][0]
        vertices, vo = decode(g, payload, base, primitive['attributes']['POSITION'])
        indices, io = decode(g, payload, base, primitive['indices'])
        flat = [x[0] for x in indices]
        assert len(flat) % 3 == 0 and all(0 <= x < len(vertices) for x in flat)
        if key and not blade:
            error = max(abs(math.sqrt(sum(v*v for v in xyz))-.06) for xyz in vertices)
        else:
            size = ([.1, 1.8 if rack == 'first' else 3., .1] if not key else
                    [length if rack == 'first' and key == 'middle' else .6, .08, .08])
            error = max(abs(abs(xyz[i])-size[i]/2) for xyz in vertices for i in range(3))
        assert error <= .001
        max_geometry = max(error, max_geometry)
        result['geometry'].append({'id': list(oid), 'node': ni, 'vertices': vertices,
                                   'triangles': [flat[i:i+3] for i in range(0, len(flat), 3)],
                                   'positionOrigin': vo, 'indicesOrigin': io})
        for time in TIMES:
            pos, po = sample(g, payload, base, channels[(ni, 'translation')], time)
            qxyzw, qo = sample(g, payload, base, channels[(ni, 'rotation')], time)
            q = [qxyzw[3]] + qxyzw[:3]
            wanted, wantedq = source_pose(spec, time, length)
            pe = max(abs(x-y) for x, y in zip(pos, wanted))
            qe = rotation_error(q, wantedq)
            assert pe <= .001 and qe <= .001
            max_position, max_angle = max(pe, max_position), max(qe, max_angle)
            result['poses'].append({'id': list(oid), 'time_s': time, 'position_m': pos,
                                    'rotation_wxyz': q, 'translationOrigin': po, 'rotationOrigin': qo})
    result['errors'] = {'maxPositionComponent_m': max_position, 'maxRotationAngle_rad': max_angle,
                        'maxMeshCoordinateOrRadius_m': max_geometry}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads((args.repo/'docs/engineering/localized-repair-c253/corpus.json').read_text())
    source_bindings = {}
    for key in ('start_065', 'target_075', 'hinges'):
        entry = corpus['files'][key]
        raw = (args.repo/entry['path']).read_bytes()
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
        source_bindings[key] = entry
    proof = args.repo/'docs/engineering/semantic-export-c210/evidence/proof'
    results = {'sourceBindings': source_bindings, 'before': measure(proof/'before.glb', .65),
               'after': measure(proof/'after.glb', .75)}
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False)+'\n')
    print(json.dumps({name: {'geometry': len(results[name]['geometry']), 'poses': len(results[name]['poses']),
                             'errors': results[name]['errors']} for name in ('before', 'after')}))


if __name__ == '__main__':
    main()
