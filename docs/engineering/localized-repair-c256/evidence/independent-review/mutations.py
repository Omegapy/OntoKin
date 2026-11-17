"""Reproducible byte mutations of a pinned C210 GLB for independent review."""
import copy
import json
import struct


def unpack(raw):
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+n])
    bsize, bkind = struct.unpack_from('<II', raw, 20+n)
    assert bkind == 0x004E4942
    return doc, bytearray(raw[28+n:28+n+bsize])


def pack(doc, binary, json_override=None):
    js = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode() if json_override is None else json_override
    js += b' '*((-len(js)) % 4)
    binary = bytes(binary)
    binary += b'\x00'*((-len(binary)) % 4)
    size = 12+8+len(js)+8+len(binary)
    return struct.pack('<4sII', b'glTF', 2, size)+struct.pack('<II', len(js), 0x4E4F534A)+js+struct.pack('<II', len(binary), 0x004E4942)+binary


def modify_json(raw, action):
    doc, binary = unpack(raw)
    action(doc)
    return pack(doc, binary)


def mutate_accessor(raw, accessor, row, values):
    doc, binary = unpack(raw)
    a = doc['accessors'][accessor]
    v = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    code, size = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4)}[a['componentType']]
    off = v.get('byteOffset', 0)+a.get('byteOffset', 0)+row*v.get('byteStride', size*width)
    if callable(values):
        values = values(list(struct.unpack_from('<'+code*width, binary, off)))
    assert len(values) == width
    struct.pack_into('<'+code*width, binary, off, *values)
    return pack(doc, binary)


def channel_accessor(raw, node, path):
    doc, _ = unpack(raw)
    animation = doc['animations'][0]
    c = next(c for c in animation['channels'] if c['target'] == {'node': node, 'path': path})
    return animation['samplers'][c['sampler']]['output']


def position_accessor(raw, node):
    doc, _ = unpack(raw)
    return doc['meshes'][doc['nodes'][node]['mesh']]['primitives'][0]['attributes']['POSITION']


def index_accessor(raw, node):
    doc, _ = unpack(raw)
    return doc['meshes'][doc['nodes'][node]['mesh']]['primitives'][0]['indices']


def structural_cases(raw):
    """Each result is unsupported/invalid and must refuse the finite profile."""
    result = {}
    wrong = bytearray(raw); wrong[:4] = b'BAD!'; result['header-magic'] = bytes(wrong)
    wrong = bytearray(raw); struct.pack_into('<I', wrong, 4, 1); result['header-version'] = bytes(wrong)
    wrong = bytearray(raw); struct.pack_into('<I', wrong, 8, len(wrong)-4); result['header-length'] = bytes(wrong)
    result['short-header'] = raw[:8]
    result['short-bin'] = raw[:-4]
    result['extra-trailer'] = raw+b'\0\0\0\0'
    actions = {
        'external-buffer': lambda d: d['buffers'][0].update(uri='data:application/octet-stream;base64,AA=='),
        'buffer-short-length': lambda d: d['buffers'][0].update(byteLength=4),
        'buffer-negative-length': lambda d: d['buffers'][0].update(byteLength=-1),
        'view-negative-offset': lambda d: d['bufferViews'][0].update(byteOffset=-4),
        'view-short-length': lambda d: d['bufferViews'][0].update(byteLength=1),
        'view-bad-buffer': lambda d: d['bufferViews'][0].update(buffer=99),
        'view-bool-buffer': lambda d: d['bufferViews'][0].update(buffer=False),
        'accessor-negative-count': lambda d: d['accessors'][0].update(count=-1),
        'accessor-bool-count': lambda d: d['accessors'][0].update(count=True),
        'accessor-overrun-count': lambda d: d['accessors'][0].update(count=999999),
        'accessor-negative-offset': lambda d: d['accessors'][0].update(byteOffset=-4),
        'accessor-wrong-component': lambda d: d['accessors'][0].update(componentType=5123),
        'accessor-wrong-shape': lambda d: d['accessors'][0].update(type='VEC2'),
        'accessor-normalized': lambda d: d['accessors'][0].update(normalized=True),
        'accessor-sparse': lambda d: d['accessors'][0].update(sparse={'count': 1}),
        'accessor-missing-view': lambda d: d['accessors'][0].pop('bufferView'),
        'unknown-required-extension': lambda d: d.update(extensionsRequired=['EXT_fake']),
        'unknown-used-extension': lambda d: d.update(extensionsUsed=['EXT_fake']),
        'node-hierarchy': lambda d: d['nodes'][0].update(children=[1]),
        'node-scale': lambda d: d['nodes'][0].update(scale=[2., 1., 1.]),
        'node-reflection': lambda d: d['nodes'][0].update(scale=[-1., 1., 1.]),
        'node-matrix': lambda d: d['nodes'][0].update(matrix=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]),
        'node-skin': lambda d: d['nodes'][0].update(skin=0),
        'node-missing-mesh': lambda d: d['nodes'][0].pop('mesh'),
        'node-bad-mesh': lambda d: d['nodes'][0].update(mesh=999),
        'scene-duplicate-root': lambda d: d['scenes'][0]['nodes'].__setitem__(1, 0),
        'scene-missing-root': lambda d: d['scenes'][0]['nodes'].pop(),
        'scene-bad-root': lambda d: d['scenes'][0]['nodes'].__setitem__(0, 999),
        'scene-bool-index': lambda d: d.update(scene=False),
        'primitive-mode': lambda d: d['meshes'][0]['primitives'][0].update(mode=1),
        'primitive-morph': lambda d: d['meshes'][0]['primitives'][0].update(targets=[{'POSITION': 1}]),
        'primitive-missing-position': lambda d: d['meshes'][0]['primitives'][0]['attributes'].pop('POSITION'),
        'channel-duplicate': lambda d: d['animations'][0]['channels'].append(copy.deepcopy(d['animations'][0]['channels'][0])),
        'channel-missing': lambda d: d['animations'][0]['channels'].pop(),
        'channel-wrong-node': lambda d: d['animations'][0]['channels'][0]['target'].update(node=999),
        'channel-scale': lambda d: d['animations'][0]['channels'][0]['target'].update(path='scale'),
        'channel-bad-sampler': lambda d: d['animations'][0]['channels'][0].update(sampler=999),
        'sampler-step': lambda d: d['animations'][0]['samplers'][0].update(interpolation='STEP'),
        'sampler-cubic': lambda d: d['animations'][0]['samplers'][0].update(interpolation='CUBICSPLINE'),
        'sampler-wrong-output-count': lambda d: d['accessors'][d['animations'][0]['samplers'][0]['output']].update(count=120),
    }
    for label, action in actions.items():
        result[label] = modify_json(raw, action)
    doc, binary = unpack(raw)
    js = json.dumps(doc, separators=(',', ':')).encode()
    result['json-duplicate-key'] = pack(doc, binary, js[:-1]+b',"scene":0}')
    result['json-nan'] = pack(doc, binary, js.replace(b'"scene":0', b'"scene":NaN', 1))
    result['indices-out-of-range'] = mutate_accessor(raw, index_accessor(raw, 0), 0, [65535])
    result['position-nan'] = mutate_accessor(raw, position_accessor(raw, 0), 0, [float('nan'), 0., 0.])
    result['time-nan'] = mutate_accessor(raw, 0, 15, [float('nan')])
    result['time-duplicate'] = mutate_accessor(raw, 0, 15, [14/60])
    result['time-decreasing'] = mutate_accessor(raw, 0, 15, [.1])
    result['time-start-excludes-zero'] = mutate_accessor(raw, 0, 0, [.001])
    result['time-end-excludes-two'] = mutate_accessor(raw, 0, 120, [1.99])
    rot = channel_accessor(raw, 0, 'rotation')
    result['rotation-zero'] = mutate_accessor(raw, rot, 15, [0.,0.,0.,0.])
    result['rotation-nonunit'] = mutate_accessor(raw, rot, 15, [0.,0.,0.,2.])
    result['rotation-inf'] = mutate_accessor(raw, rot, 15, [0.,0.,0.,float('inf')])
    return result
