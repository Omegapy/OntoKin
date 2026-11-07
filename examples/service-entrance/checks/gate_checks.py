"""C121-derived binary glTF reader and original gate motion tests for C122."""
import argparse
from bisect import bisect_right
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import re

POSITION_TOL = ANGLE_TOL = 0.001
CLOCK_TOL = Fraction(1, 1_000_000)
IDENTITY = (0., 0., 0., 1.)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_glb(data):
    magic, version, total, size, tag = struct.unpack_from("<4sIIII", data)
    require((magic, version, total, tag) == (b"glTF", 2, len(data), 0x4E4F534A),
            "invalid GLB header")
    graph = json.loads(data[20:20 + size])
    size_bin, tag_bin = struct.unpack_from("<II", data, 20 + size)
    offset = 28 + size
    require(tag_bin == 0x004E4942 and offset + size_bin == len(data), "invalid BIN chunk")
    buffer, = graph["buffers"]
    require("uri" not in buffer and 0 <= size_bin - buffer["byteLength"] <= 3,
            "invalid internal buffer")
    return graph, memoryview(data)[offset:offset + buffer["byteLength"]]


def indexed(items, index):
    require(type(index) is int and 0 <= index < len(items), "invalid glTF index")
    return items[index]


def accessor(graph, binary, index, kind):
    acc = indexed(graph["accessors"], index)
    view = indexed(graph["bufferViews"], acc["bufferView"])
    fmt = struct.Struct("<" + {"SCALAR": "f", "VEC3": "3f", "VEC4": "4f"}[kind])
    require(acc["type"] == kind and acc["componentType"] == 5126 and view["buffer"] == 0
            and "sparse" not in acc and not acc.get("normalized"), "unsupported animation accessor")
    count = acc["count"]
    stride = view.get("byteStride", fmt.size)
    start = acc.get("byteOffset", 0)
    base = view.get("byteOffset", 0)
    require(count >= 2 and start >= 0 and base >= 0 and stride >= fmt.size and
            start + (count - 1) * stride + fmt.size <= view["byteLength"]
            and base + view["byteLength"] <= len(binary), "animation accessor out of bounds")
    rows = [fmt.unpack_from(binary, base + start + i * stride) for i in range(count)]
    require(all(math.isfinite(v) for row in rows for v in row), "non-finite animation component")
    return rows


def unit(q):
    length = math.hypot(*q)
    require(abs(length - 1) <= 2e-6, "rotation is not a unit quaternion")
    return tuple(x / length for x in q)


def align(a, b):
    if math.fsum(x * y for x, y in zip(a, b)) < 0:
        return tuple(-v for v in b)
    return b


def angle(a, b):
    """Physical angular distance; both inputs are unit xyzw quaternions."""
    b = align(a, b)
    return 4 * math.atan2(math.dist(a, b), math.hypot(*(x + y for x, y in zip(a, b))))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    x, y, z = a
    i, j, k = b
    return y*k - z*j, z*i - x*k, x*j - y*i


def rotate(q, v):
    first = cross(q[:3], v)
    second = cross(q[:3], first)
    return tuple(x + 2 * (q[3]*f + s) for x, f, s in zip(v, first, second))


def lerp(a, b, u):
    return tuple(x + u * (y-x) for x, y in zip(a, b))


def read_tracks(graph, binary, *, raw_rotations=None):
    animation, = graph['animations']
    exact = [Fraction(int(v['numerator']), int(v['denominator'])) for v in
             animation['extras']['ontokin']['exact_times_seconds']]
    require(exact[0] == 0 and exact[-1] == Fraction(13,4) and all(a < b for a,b in zip(exact, exact[1:])),
            'invalid exact key times')
    times = None
    max_clock = Fraction(0)
    tracks = {}
    for channel in animation['channels']:
        sampler = indexed(animation['samplers'], channel['sampler'])
        target = channel['target']
        path = target['path']
        name = indexed(graph['nodes'], target['node'])['name']
        require((name,path) not in tracks and path in ('rotation','translation'), 'unexpected track')
        require(sampler.get('interpolation','LINEAR') == 'LINEAR', 'unexpected interpolation')
        clock = [x for x, in accessor(graph,binary,sampler['input'],'SCALAR')]
        require(len(clock)==len(exact) and clock[0]==0 and clock[-1]==3.25 and
                all(a < b for a,b in zip(clock,clock[1:])), 'invalid monotonically increasing 3.25-second clock')
        require(times is None or times == clock, 'expected common animation clock')
        times = clock
        max_clock = max(max_clock, max(abs(Fraction(x)-y) for x,y in zip(clock,exact)))
        values = accessor(graph,binary,sampler['output'],'VEC4' if path=='rotation' else 'VEC3')
        require(len(values)==len(clock), 'incorrect track length')
        if path == 'rotation' and raw_rotations is not None:
            raw_rotations[name] = values
        tracks[name,path] = [unit(q) for q in values] if path=='rotation' else values
    require(max_clock <= CLOCK_TOL, 'binary clock exceeds 1 microsecond tolerance')
    return times, tracks, float(max_clock)


def primitive_points(graph, binary, primitive):
    points = accessor(graph, binary, primitive['attributes']['POSITION'], 'VEC3')
    require(primitive.get('mode', 4) == 4 and not primitive.get('targets'), 'expected rigid triangle geometry')
    if 'indices' not in primitive:
        return points
    acc = indexed(graph['accessors'], primitive['indices'])
    view = indexed(graph['bufferViews'], acc['bufferView'])
    fmt = struct.Struct('<' + {5121:'B', 5123:'H', 5125:'I'}[acc['componentType']])
    require(acc['type'] == 'SCALAR' and view['buffer'] == 0 and 'sparse' not in acc, 'unexpected indices')
    base = view.get('byteOffset', 0)
    start = acc.get('byteOffset', 0)
    require(start >= 0 and start+acc['count']*fmt.size <= view['byteLength'] and
            base + view['byteLength'] <= len(binary) and 'byteStride' not in view, 'invalid index buffer')
    return [indexed(points, fmt.unpack_from(binary, base + start + i*fmt.size)[0]) for i in range(acc['count'])]


def surfaces(graph, binary, node):
    require('EXT_mesh_gpu_instancing' not in node.get('extensions', {}),
            'mesh instancing is unsupported by the passage checker')
    mesh = indexed(graph['meshes'], node['mesh'])
    require('skin' not in node and 'weights' not in node and 'weights' not in mesh,
            'expected rigid mesh without skin or morph weights')
    return [primitive_points(graph, binary, p) for p in mesh['primitives']]


NUMBER = '([+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))'
BREAKS = (0, 0.5, 1, 2, 2.5, 3, 3.25)

def source_dynamics(source):
    """Read the restricted constructs actually used by this accepted C121 program."""
    gate = re.search('class Gate\\b(.*?)\\n}', source, re.S)[1]
    post = re.search('class Post\\b(.*?)\\n}', source, re.S)[1]
    require('geometry = extrude(' in gate and 'motion = dynamic;' in gate and ('collision = disabled;' in gate) and ('physical = no_body();' in post) and ('geometry = extrude(' in post), 'unexpected motion/mesh authority')
    require(re.search('object gate @ "gate": Gate', source) and re.search('object post @ "post": Post', source), 'unexpected object classes')
    mass = Fraction(re.search('sphere_body\\([^,]+,\\s*' + NUMBER + '\\[kg\\]\\)', gate)[1])
    require(mass > 0, 'nonpositive mass')
    initial = {}
    for key, unit_name in [('gravity', 'm/s^2'), ('velocity', 'm/s'), ('omega', 'rad/s')]:
        expr = re.search(key + ' = vector\\(world, ([^)]*)\\)', source)[1]
        values = [Fraction(x) for x in re.findall(NUMBER + '\\[' + re.escape(unit_name) + '\\]', expr)]
        require(values == [0, 0, 0], 'expected zero ' + key)
        initial[key] = list(map(float, values))
    poses = {}
    for name in ('gate', 'post'):
        block = re.search('object ' + name + '\\b([^}]+)', source)[1]
        xyz = re.search('placement = pose\\(world, vec3\\(([^)]*)\\), quat\\(1, 0, 0, 0\\)\\)', block)[1]
        poses[name] = [float(v) for v in re.findall(NUMBER + '\\[m\\]', xyz)]
    forces = []
    pattern = 'at ' + NUMBER + '\\[s\\] sequence\\s*\\{\\s*force gate @ "[^"]+" using vector\\(world, ' + NUMBER + '\\[N\\], 0\\[N\\], 0\\[N\\]\\) for ' + NUMBER + '\\[s\\];\\s*}'
    for start, force, duration in re.findall(pattern, source):
        start, force, duration = map(Fraction, (start, force, duration))
        forces.append((start, start + duration, force))
    require(len(forces) == 4 == len(re.findall(r'\bforce\s+gate\b', source)) and 'torque gate' not in source, 'unexpected loads')
    end_time = Fraction(re.search('duration = ' + NUMBER + '\\[s\\];', source)[1])
    require(end_time == Fraction(13, 4), 'incorrect scene duration')
    breaks = sorted({Fraction(0), end_time, *[e for f in forces for e in f[:2]]})
    require(tuple(breaks) == BREAKS, 'unexpected phase times')
    x = v = Fraction(0)
    phases = []
    for start, end in zip(breaks, breaks[1:]):
        f = sum((value for a, b, value in forces if a <= start < b))
        a = f / mass
        dt = end - start
        phases.append(dict(start_s=float(start), end_s=float(end), force_x_N=float(f), acceleration_x_m_s2=float(a), start_x_m=float(x), start_v_m_s=float(v)))
        x += dt * v + a * dt ** 2 / 2
        v += a * dt
        require(end not in (1, 2, 3, end_time) or (v == 0 and x == (Fraction(3, 2) if end in (1, 2) else 0)), 'incorrect source endpoint')
    return dict(mass_kg=float(mass), initial=initial, initial_world_positions_m=poses, phases=phases, peak_speed_m_s=max((abs(p['start_v_m_s']) for p in phases)))

def measure(data, physics, root_count=3):
    graph, binary = read_glb(data)
    times, tracks, clock_error = read_tracks(graph, binary)
    nodes = graph['nodes']
    require(len(nodes) == root_count and sorted(graph['scenes'][graph['scene']]['nodes']) == list(range(root_count)) and {n['name'] for n in nodes} >= {'post','gate'}, f'expected {root_count} root meshes including gate and post')
    require(all((not any((k in n for k in ('matrix', 'children', 'scale'))) for n in nodes)), 'unexpected hierarchy or scale')
    features = {}
    fixed_error = rotation_error = 0.0
    for n in nodes:
        name = n['name']
        if name not in ('gate', 'post'):
            continue
        triangles = surfaces(graph, binary, n)
        points = sorted(set((p for face in triangles for p in face)))
        require(len(points) >= 8, 'expected solid geometry')
        tr = tracks[name, 'translation']
        rot = tracks[name, 'rotation']
        require(all((align(rot[0], q) == rot[0] for q in rot)), 'nonconstant rotation keys')
        rotation_error = max(rotation_error, angle(IDENTITY, rot[0]))
        require(rotation_error <= ANGLE_TOL, 'rotated mesh')
        require(math.dist(tr[0], physics['initial_world_positions_m'][name]) <= POSITION_TOL, 'wrong initial pose')
        world = [add(rotate(rot[0], p), tr[0]) for p in points]
        lo, hi = ([op(row) for row in zip(*world)] for op in (min, max))
        feature = min(world, key=lambda p: (-p[0], -p[1], -p[2]))
        features[name] = dict(initial_bounds_m=[lo, hi], unique_vertices=len(points), triangle_count=sum(map(len, triangles)) // 3, initial_upper_right_front_vertex_m=feature)
        if name == 'post':
            fixed_error = max((math.dist(tr[0], p) for p in tr))
    require(fixed_error <= POSITION_TOL, 'post drift')
    tr = tracks['gate', 'translation']
    p0 = tr[0]
    dx = [p[0] - p0[0] for p in tr]
    indices = [min(range(len(times)), key=lambda i: abs(times[i] - t)) for t in BREAKS]
    require(all((abs(times[i] - t) <= float(CLOCK_TOL) for i, t in zip(indices, BREAKS))), 'missing phase boundary')
    endpoint = {str(t): dx[i] for t, i in zip(BREAKS, indices)}
    require(all((abs(dx[indices[j]] - want) <= POSITION_TOL for j, want in [(0, 0), (2, 1.5), (3, 1.5), (5, 0), (6, 0)])), 'wrong gate travel')
    off = max((math.dist(p[1:], p0[1:]) for p in tr))
    require(off <= POSITION_TOL, 'off-axis gate travel')
    hold = max((abs(dx[i] - value) for l, r, value in [(2, 3, 1.5), (5, 6, 0)] for i in range(indices[l], indices[r] + 1)))
    require(hold <= POSITION_TOL, 'gate drift during hold')
    for l, r, sign in [(0, 2, 1), (3, 5, -1)]:
        require(all((sign * (dx[i + 1] - dx[i]) >= 0 for i in range(indices[l], indices[r]))), 'gate reversed within stroke')
    worst = when = 0.0
    intervals = 0
    for i, (left, right) in enumerate(zip(times, times[1:])):
        slope = (dx[i + 1] - dx[i]) / (right - left)
        for p in physics['phases']:
            s = p['start_s']
            a = p['acceleration_x_m_s2']
            v = p['start_v_m_s']
            lo = max(s, left)
            hi = min(p['end_s'], right)
            if hi <= lo:
                continue
            intervals += 1
            candidates = [lo, hi]
            if a:
                candidates.append(max(lo, min(hi, s + (slope - v) / a)))
            for t in candidates:
                dt = t - s
                expected = p['start_x_m'] + v * dt + a * dt * dt / 2
                actual = dx[i] + slope * (t - left)
                error = abs(actual - expected)
                if error > worst:
                    worst, when = (error, t)
    bound = math.hypot(worst, off)
    require(bound <= POSITION_TOL, 'continuous source/GLB discrepancy')
    for name, meta in features.items():
        ref = meta['initial_upper_right_front_vertex_m']
        positions = tracks[name, 'translation']
        meta['world_vertex_at_phase_times_m'] = {str(t): add(ref, subtract(positions[i], positions[0])) for t, i in zip(BREAKS, indices)}
    return dict(keys=len(times), nonempty_clip_source_subintervals=intervals, mesh_features=features, gate_displacement_x_m=endpoint, max_clock_error_s=clock_error, max_post_displacement_m=fixed_error, max_gate_hold_error_m=hold, max_off_axis_m=off, max_rotation_rad=rotation_error, max_continuous_trajectory_error_bound_m=bound, max_x_error_at_s=when, opening_monotone=True, closing_monotone=True)

