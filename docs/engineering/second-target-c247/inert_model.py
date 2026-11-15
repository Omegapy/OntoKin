"""CPU model of the C247 capture contract, not an interpreter or native proof.

Packed values and nodes are fabricated. In particular, the model does not emulate
Godot's numeric encoding, object lifetime, engine diagnostics or allocation.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import math

MESHES = (0, 1, 2, 3, 2, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3)
EXPECTED_FORMAT = (1 << 35) | 1 | 2 | 4 | 4096
MAX_SCENE_NODES = 64
MAX_VERTICES = 100000
MAX_INDICES = 300000
MAX_RAW_BYTES = 16000000
NIL, INT, ARRAY, BYTE, INT32, FLOAT32, VECTOR3 = 0, 2, 28, 29, 30, 32, 36
SLOTS = {0: VECTOR3, 1: VECTOR3, 2: FLOAT32, 12: INT32}
RAW_ALLOWED = {'primitive', 'format', 'vertex_data', 'vertex_count', 'index_data',
               'index_count', 'aabb', 'uv_scale', 'material', 'attribute_data',
               'skin_data', 'lods', 'bone_aabbs', 'blend_shape_data'}
RAW_FORBIDDEN = {'attribute_data', 'skin_data', 'lods', 'bone_aabbs', 'blend_shape_data'}


@dataclass
class Packed:
    kind: int
    values: object


def kind(value):
    if isinstance(value, Packed):
        return value.kind
    return {type(None): NIL, bool: 1, int: INT, float: 3, str: 4,
            list: ARRAY, dict: 27}.get(type(value), -1)


@dataclass
class MeshView:
    identity: int
    surface_count: int = 1
    blend_shape_count: int = 0
    shadow_mesh: object = None
    native_class: str = 'ArrayMesh'
    script: object = None
    format: int = EXPECTED_FORMAT
    primitive: int = 3
    vertices: int = 3
    indices: int = 3
    arrays: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    alive: bool = True
    reads: int = 0
    mutate_at: object = None

    def read(self):
        self.reads += 1
        if self.mutate_at is not None:
            self.mutate_at(self)
        return self


@dataclass
class NodeView:
    identity: int
    native_class: str = 'MeshInstance3D'
    mesh: object = None
    children: list = field(default_factory=list)
    script: object = None
    parent: object = None
    alive: bool = True


class Registry:
    """Synthetic completed-receipt provider, with exact object binding and one close."""
    def __init__(self, state, chain):
        self.state = state
        self.chain = chain
        self.faults = []
        self.closed = False
        self.close_calls = 0

    def close_state(self, state):
        self.close_calls += 1
        if state is not self.state or self.closed:
            self.faults.append('wrong state or already closed')
            return {'component_complete': False}
        self.closed = True
        return deepcopy(self.chain)


class Refusal(Exception):
    pass


class Capture:
    def __init__(self):
        self.used = False
        self.errors = []
        self.result = {}
        self.scene_reads = 0
        self.mesh_reads = 0

    def refuse(self, reason):
        if not self.errors:
            self.errors.append(reason)
        self.result.update(phase='REFUSED', component_complete=False)
        raise Refusal(reason)

    def check(self, condition, reason):
        if not condition:
            self.refuse(reason)

    def live_meshes(self, root, chain):
        self.scene_reads += 1
        self.check(type(root) is NodeView and root.alive and root.native_class == 'Node3D'
                   and root.parent is None, 'invalid returned root class or parent')
        self.check(root.identity == chain['root']['instance_id'], 'returned root identity changed')
        wanted, retired = {}, set()
        for i in range(18):
            original, edge, final = chain['originals'][i], chain['edges'][i], chain['finals'][i]
            self.check(original['mesh'] == MESHES[i] and edge['old'] == original['old']
                       and edge['new'] == final['new'], 'inconsistent chain')
            self.check(final['new'] not in wanted and final['new'] != root.identity, 'duplicate final')
            wanted[final['new']] = i
            retired.add(original['old'])
        pending, seen, meshes = [root], set(), {}
        while pending:
            self.check(len(seen) < MAX_SCENE_NODES, 'scene traversal bound exceeded')
            node = pending.pop()
            self.check(type(node) is NodeView and node.alive, 'invalid scene member')
            self.check(node.identity not in seen and node.identity not in retired
                       and node.script is None, 'duplicate retired or scripted scene member')
            seen.add(node.identity)
            self.check(node.native_class != 'ImporterMeshInstance3D', 'unconverted member')
            if node.native_class in ('MeshInstance3D', 'CustomMeshInstance3D'):
                self.check(node.native_class == 'MeshInstance3D' and node.identity in wanted,
                           'unmapped or unsupported mesh member')
                meshes[wanted[node.identity]] = node
            self.check(len(pending) + len(node.children) + len(seen) <= MAX_SCENE_NODES,
                       'scene traversal bound exceeded')
            pending.extend(node.children)
        self.check(len(meshes) == 18, 'missing final live mesh membership')
        return meshes

    def mesh_binding(self, node, final):
        self.check(node.alive and node.native_class == 'MeshInstance3D' and node.script is None
                   and node.identity == final['new'], 'final node identity changed')
        mesh = node.mesh
        self.check(type(mesh) is MeshView and mesh.alive and mesh.native_class == 'ArrayMesh'
                   and mesh.script is None, 'unsupported mesh resource')
        bindings = [x for x in final['native']['resource_bindings']
                    if x['property']['type'] in (4, 21) and x['property']['value'] == 'mesh']
        self.check(len(bindings) == 1, 'missing or ambiguous final mesh binding')
        resource = bindings[0]['resource']
        self.check(resource['class'] == 'ArrayMesh' and resource['instance_id'] == mesh.identity,
                   'mesh resource differs from final chain facts')
        return mesh

    def surface(self, mesh, out):
        self.mesh_reads += 1
        mesh.read()
        out.update(mesh_instance_id=mesh.identity, mesh_class=mesh.native_class,
                   surface_count=mesh.surface_count, blend_shape_count=mesh.blend_shape_count,
                   shadow_mesh_present=mesh.shadow_mesh is not None)
        self.check(mesh.surface_count == 1 and mesh.blend_shape_count == 0 and mesh.shadow_mesh is None,
                   'surface blend shape or shadow unsupported')
        out.update(surface=0, format=mesh.format, primitive_type=mesh.primitive,
                   vertex_count=mesh.vertices, index_count=mesh.indices)
        self.check(type(mesh.format) is int and mesh.format == EXPECTED_FORMAT
                   and type(mesh.primitive) is int and mesh.primitive == 3, 'unsupported format or primitive')
        self.check(type(mesh.vertices) is int and 0 < mesh.vertices <= MAX_VERTICES
                   and type(mesh.indices) is int and 0 < mesh.indices <= MAX_INDICES
                   and mesh.indices % 3 == 0, 'invalid or excessive counts')
        raw = mesh.raw
        out['raw_surface_field_types'] = [{'key': key, 'type': kind(value)} for key, value in raw.items()]
        self.check(all(type(k) is str and k in RAW_ALLOWED for k in raw), 'unknown raw surface field')
        self.check(all(k in raw for k in ['format', 'primitive', 'vertex_count', 'index_count',
                                          'vertex_data', 'index_data']), 'missing raw surface field')
        self.check(all(type(raw[k]) is int for k in ['format', 'primitive', 'vertex_count', 'index_count']),
                   'raw descriptor type mismatch')
        out['raw_buffer_lengths'] = {}
        for key in ['vertex_data', 'index_data']:
            value = raw[key]
            self.check(type(value) is Packed and value.kind == BYTE, 'unsupported raw buffer type')
            out['raw_buffer_lengths'][key] = len(value.values)
            if not 0 < len(value.values) <= MAX_RAW_BYTES:
                out['omitted'] = [{'field': key, 'count': len(value.values), 'type': kind(value),
                                   'reason': 'empty or over raw buffer bound', 'cap': MAX_RAW_BYTES}]
                self.refuse('empty or excessive raw buffer')
            out[key] = deepcopy(value)
        self.check((raw['format'], raw['primitive'], raw['vertex_count'], raw['index_count']) ==
                   (mesh.format, mesh.primitive, mesh.vertices, mesh.indices), 'descriptors disagree')
        self.check(not RAW_FORBIDDEN.intersection(raw), 'unsupported raw surface field')
        arrays = mesh.arrays
        out.update(array_type=kind(arrays), array_count=len(arrays),
                   slot_types=[kind(v) for v in arrays[:13]],
                   slot_lengths=[len(v.values) if isinstance(v, Packed) and v.kind in (VECTOR3, FLOAT32, INT32)
                                 else None for v in arrays[:13]])
        names = {0: 'positions', 1: 'normals', 2: 'auxiliary_tangents', 12: 'indices'}
        caps = {0: MAX_VERTICES, 1: MAX_VERTICES, 2: 4*MAX_VERTICES, 12: MAX_INDICES}
        for slot, value in enumerate(arrays[:13]):
            if slot in SLOTS and kind(value) == SLOTS[slot]:
                if len(value.values) > caps[slot]:
                    out['omitted'] = [{'field': names[slot], 'count': len(value.values), 'type': kind(value),
                                       'reason': 'over slot bound', 'cap': caps[slot]}]
                    self.refuse('native slot exceeds capture bound')
                out[names[slot]] = deepcopy(value)
        self.check(type(arrays) is list and len(arrays) == 13, 'wrong slot count')
        for slot, value in enumerate(arrays):
            self.check(kind(value) == SLOTS.get(slot, NIL), 'wrong packed type or unexpected channel')
        self.check(len(arrays[0].values) == len(arrays[1].values) == mesh.vertices
                   and len(arrays[2].values) == 4 * mesh.vertices
                   and len(arrays[12].values) == mesh.indices, 'packed lengths disagree')
        for name in ['positions', 'normals']:
            self.check(all(type(v) is tuple and len(v) == 3 and all(type(c) is float and math.isfinite(c)
                           for c in v) for v in out[name].values), 'nonfinite or malformed vector')
        self.check(all(type(v) is float and math.isfinite(v) for v in out['auxiliary_tangents'].values),
                   'nonfinite or malformed tangent')
        self.check(all(type(v) is int and 0 <= v < mesh.vertices and v < 2**31
                       for v in out['indices'].values), 'native index out of bounds')

    def capture(self, registry, state, root):
        try:
            if self.used:
                self.refuse('capture is single use')
            self.used = True
            self.result = {'schema': 'ontokin.c247.native-mesh-arrays/0.1', 'phase': 'CAPTURING',
                           'component_complete': False, 'execution_admission': False,
                           'native_acceptance': False, 'R07': 'PENDING',
                           'value_origin': 'native-api-readback', 'parts': []}
            chain = registry.close_state(state)
            self.result['chain'] = chain
            self.check(chain.get('component_complete') is True and chain.get('phase') == 'CHAIN_COMPLETE_RAW_PENDING'
                       and chain.get('state_id') == id(state), 'no completed exact-state chain')
            self.check(not chain['errors'] and not registry.faults, 'registry or chain poisoned')
            meshes = self.live_meshes(root, chain)
            for i in range(18):
                row = {'source_node': i, 'source_mesh': chain['originals'][i]['mesh'], 'source_primitive': 0,
                       'native_node_instance_id': chain['finals'][i]['new'], 'native_surface': 0,
                       'association_basis': 'single primitive plus pinned ordered conversion and live replacement chain'}
                self.result['parts'].append(row)
                mesh = self.mesh_binding(meshes[i], chain['finals'][i])
                row['snapshot'] = {}
                self.surface(mesh, row['snapshot'])
            for i in range(18):
                mesh = self.mesh_binding(meshes[i], chain['finals'][i])
                after = {}
                try:
                    self.surface(mesh, after)
                    self.check(after == self.result['parts'][i]['snapshot'], 'native surface changed during capture')
                except Refusal:
                    self.result['parts'][i]['after_drift'] = after
                    raise
            self.live_meshes(root, chain)
            self.check(not registry.faults, 'registry changed during capture')
            self.result.update(phase='MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING', component_complete=True,
                               stability='two equal reads and final membership; not atomic against concurrent writes')
        except Refusal:
            pass
        self.result['errors'] = self.errors[:]
        return deepcopy(self.result)


def synthetic_fixture():
    """Eighteen fabricated mapped parts sharing five fabricated single-surface meshes."""
    meshes = []
    for i in range(5):
        arrays = [None] * 13
        arrays[0] = Packed(VECTOR3, [(float(i), -0.0, 0.0), (float(i)+1.0, 0.0, 0.0), (float(i), 1.0, 0.0)])
        arrays[1] = Packed(VECTOR3, [(0.0, 0.0, 0.5)] * 3)
        arrays[2] = Packed(FLOAT32, [0.0, 1.0, 0.0, -1.0] * 3)
        arrays[12] = Packed(INT32, [0, 2, 1])
        raw = {'primitive': 3, 'format': EXPECTED_FORMAT, 'vertex_count': 3, 'index_count': 3,
               'vertex_data': Packed(BYTE, bytes([i]) * 60), 'index_data': Packed(BYTE, b'\x00\x00\x02\x00\x01\x00')}
        meshes.append(MeshView(1000+i, arrays=arrays, raw=raw))
    state = object()
    root = NodeView(90, native_class='Node3D')
    chain = {'component_complete': True, 'phase': 'CHAIN_COMPLETE_RAW_PENDING', 'state_id': id(state),
             'root': {'instance_id': 90}, 'errors': [], 'originals': {}, 'edges': {}, 'finals': {}}
    for i, m in enumerate(MESHES):
        root.children.append(NodeView(200+i, mesh=meshes[m], parent=root))
        chain['originals'][i] = {'mesh': m, 'old': 100+i}
        chain['edges'][i] = {'old': 100+i, 'new': 200+i}
        chain['finals'][i] = {'new': 200+i, 'native': {'resource_bindings': [
            {'property': {'type': 21, 'value': 'mesh'}, 'resource': {'class': 'ArrayMesh', 'instance_id': 1000+m}}
        ]}}
    return Registry(state, chain), state, root
