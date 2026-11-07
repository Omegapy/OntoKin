"""Measure a stationary framed duct joint from rendered glTF triangles in a GLB."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__:
    from .texture_reference import GLB
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from texture_reference import GLB


TOL = 1e-5
AREA_TOL = 5e-5
PORTS = {'elbow': ('top', 1), 'straight': ('bottom', -1)}


class JointFailure(ValueError):
    def __init__(self, reason, measurements):
        super().__init__(reason)
        self.measurements = measurements


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def cross(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return (ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx)


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


@dataclass(frozen=True)
class PortFrame:
    center: tuple
    axes: tuple  # World directions of normal, first rim axis and second rim axis.

    def local(self, point):
        offset = sub(point, self.center)
        return tuple(sum(a*b for a,b in zip(axis, offset)) for axis in self.axes)

    def vector(self, local):
        return tuple(sum(a*b for a,b in zip(row, local)) for row in zip(*self.axes))

    def world(self, local):
        return tuple(a+b for a,b in zip(self.center, self.vector(local)))


FIXED = PortFrame((4,0,4), ((1,0,0),(0,1,0),(0,0,1)))


def port_frame(placement):
    if placement == 'fixed':
        return FIXED
    require(placement in ('oblique', 'third'), 'Unknown duct placement')
    path = Path(__file__).resolve().parents[1] / f'examples/connected-duct/{placement}-contract.json'
    expected = json.loads(path.read_text())
    return PortFrame(tuple(expected['elbow_outlet_center_m']), tuple(zip(*expected['rotation_rows'])))


def place(point, node):
    q = node['rotation']
    length = math.hypot(*q)
    require(abs(length-1) < TOL, 'Non-unit node rotation')
    x, y, z, w = (v/length for v in q)
    axis = (x, y, z)
    first = cross(axis, point)
    second = cross(axis, first)
    return tuple(p+t+2*(w*u+v) for p, t, u, v in zip(point, node['translation'], first, second))


def stationary_times(glb, nodes):
    require(len(glb.document['animations']) == 1, 'Expected one recorded clip')
    animation = glb.document['animations'][0]
    tracks = {}
    for channel in animation['channels']:
        target = channel['target']
        i, path = target['node'], target['path']
        require(type(i) is int and i in nodes and path in ('translation', 'rotation') and (i, path) not in tracks,
                'Unexpected or duplicate transform channel')
        index = channel['sampler']
        require(type(index) is int and 0 <= index < len(animation['samplers']), 'Invalid animation sampler reference')
        sampler = animation['samplers'][index]
        times = glb.accessor(sampler['input'])
        values = glb.accessor(sampler['output'])
        require(sampler.get('interpolation', 'LINEAR') == 'LINEAR' and len(times) == len(values)
                and times[0] == 0 and times[-1] == 1 and all(a < b for a, b in zip(times, times[1:])),
                'Expected ordered linear keys covering the one-second clip')
        base = nodes[i][path]
        for value in values:
            error = math.dist(base, value)
            if path == 'rotation':
                error = min(error, math.dist(base, [-v for v in value]))
            require(error < 1e-7, 'Moving transform at ' + nodes[i]['name'] + '/' + path)
        tracks[i, path] = times
    require(len(tracks) == 2 * len(nodes), 'Missing transform channel')
    return sorted({t for times in tracks.values() for t in times})


def opening_intersection(face, half):
    """Clip the triangle's joint-plane section to the open square, inset by TOL."""
    section = [v[1:] for v in face if abs(v[0]) <= TOL]
    for a, b in zip(face, face[1:]+face[:1]):
        if a[0]*b[0] < 0:
            t = (-a[0])/(b[0]-a[0])
            section.append(tuple(a[i]+t*(b[i]-a[i]) for i in (1, 2)))
    if all(abs(v[0]) <= TOL for v in face):
        section = [v[1:] for v in face]
    for axis in (0, 1):
        for sign in (-1, 1):
            polygon, section = section, []
            for a, b in zip(polygon, polygon[1:]+polygon[:1]):
                da = half-TOL-sign*a[axis]
                db = half-TOL-sign*b[axis]
                if da >= 0:
                    section.append(a)
                if da*db < 0:
                    section.append(tuple(x+(y-x)*da/(da-db) for x, y in zip(a, b)))
    return bool(section)


def rings(half):
    return [(0, y*r, z*r) for r in (1, half) for y, z in [(-1,-1),(1,-1),(1,1),(-1,1)]]


def port(glb, node, width, frame, role=None):
    name = node['name']
    role = role or name
    cap_region, direction = PORTS[role]
    target = rings(width/2)
    edges, actual = Counter(), {}
    area = 0.0
    face_count = 0
    max_normal_error = 0.0
    max_corner_error = 0.0
    obstructed = False
    cap_normal = None
    outlet_points = set()
    mesh = glb.reference('meshes', node['mesh'])
    require('skin' not in node and 'weights' not in node and 'weights' not in mesh,
            'Expected rigid duct mesh')
    for primitive in mesh['primitives']:
        require(primitive.get('mode', 4) == 4 and 'targets' not in primitive, 'Expected rigid triangles')
        material = glb.reference('materials', primitive['material'])
        region = primitive.get('extras', {}).get('ontokin', {}).get('region_key')
        identity = material.get('extras', {}).get('ontokin', {})
        require(isinstance(region, str) and region == identity.get('source_region_key') and
                identity.get('occurrence_path') == name and material.get('name') == f'{name}: {region}',
                name + ' inconsistent region identity')
        cap = region == cap_region
        points = [frame.local(place(p, node)) for p in glb.accessor(primitive['attributes']['POSITION'])]
        indices = glb.accessor(primitive['indices'])
        require(len(indices) % 3 == 0 and all(0 <= j < len(points) for j in indices), 'Invalid triangle indices')
        for start in range(0, len(indices), 3):
            tri = [points[j] for j in indices[start:start+3]]
            if role == 'straight' and region == 'top':
                outlet_points.update(tri)
            if cap:
                normal = cross(sub(tri[1], tri[0]), sub(tri[2], tri[0]))
                magnitude = math.hypot(*normal)
                require(magnitude > 0, name + ' degenerate cap')
                unit = tuple(v/magnitude for v in normal)
                error = math.dist(unit, (direction, 0, 0))
                if cap_normal is None or error > max_normal_error:
                    cap_normal = unit
                max_normal_error = max(max_normal_error, error)
                if error > TOL:
                    raise JointFailure(name + ' cap normal differs',
                                       {'part': name, 'triangle_normal': frame.vector(unit),
                                        'expected_normal': frame.vector((direction, 0, 0)), 'normal_error': error})
                ids = []
                for p in tri:
                    j = min(range(8), key=lambda k: math.dist(p, target[k]))
                    max_corner_error = max(max_corner_error, math.dist(p, target[j]))
                    require(j not in actual or actual[j] == p, name + ' unwelded cap seam differs')
                    actual[j] = p
                    ids.append(j)
                edges.update(zip(ids, ids[1:]+ids[:1]))
                area += abs(normal[0])/2
                face_count += 1
            obstructed |= opening_intersection(tri, width/2)
    expected = {tuple(sorted((base+j, base+(j+1)%4))) for base in (0,4) for j in range(4)}
    boundary = set()
    for a, b in edges:
        require(a != b and edges[a,b] == 1, name + ' duplicate or degenerate face edge')
        if (b, a) not in edges:
            boundary.add(tuple(sorted((a,b))))
    require(boundary == expected and len(actual) == 8, name + ' incomplete rim loops')
    inner = [actual[i] for i in range(4, 8)]
    # Shoelace area of the observed bore in the joint plane.
    clear_area = abs(sum(a[1]*b[2] - a[2]*b[1] for a, b in zip(inner, inner[1:]+inner[:1])))/2
    outer = [actual[i] for i in range(4)]
    row = dict(cap_triangles=face_count, annulus_area_m2=area, clear_area_m2=clear_area,
               max_normal_error=max_normal_error, cap_normal=cap_normal,
               outer_loop_m=outer, inner_loop_m=inner,
               inner_center_m=[sum(p[axis] for p in inner)/4 for axis in range(3)],
               max_expected_corner_distance_m=max_corner_error,
               intersects_required_opening=obstructed)
    if role == 'straight':
        require(outlet_points, 'Missing straight outlet')
        # For the framed square, the midpoint of opposite extrema is its exterior center.
        outlet = [(min(axis)+max(axis))/2 for axis in zip(*outlet_points)]
        inlet = [sum(axis)/4 for axis in zip(*outer)]
        offset = sub(outlet, inlet)
        length = math.hypot(*offset)
        require(length > TOL, 'Coincident straight terminal centers')
        row['outlet_center_m'] = outlet
        row['centerline_direction'] = [v/length for v in offset]
        row['centerline_error'] = math.dist(row['centerline_direction'], (1, 0, 0))
    return row


def rectangular_overlap(ports):
    """Measure only the tested case of two coplanar axis-aligned rectangular rims."""
    bounds = []
    for row in ports.values():
        corners = row['inner_loop_m']
        if any(abs(p[0]) > TOL for p in corners):
            return None
        ys, zs = zip(*(p[1:] for p in corners))
        rect = (min(ys), max(ys), min(zs), max(zs))
        expected = [(y, z) for y in rect[:2] for z in rect[2:]]
        if not all(min(math.dist(v, p[1:]) for p in corners) <= TOL for v in expected):
            return None
        bounds.append(rect)
    a, b = bounds
    return math.prod(max(0, min(a[i+1], b[i+1]) - max(a[i], b[i])) for i in (0, 2))


def measure(raw, width=1, placement='fixed'):
    frame = port_frame(placement)
    require(width in (1,1.25), 'Expected frozen nominal or alternate width')
    glb = GLB(raw, target='ontokin.glb/0.11')
    doc = glb.document
    require(not doc.get('extensionsUsed') and not doc.get('extensionsRequired'), 'Expected unextended GLB')
    roots = glb.reference('scenes', doc['scene'])['nodes']
    nodes = {i:glb.reference('nodes', i) for i in roots}
    require(len(roots) == len(nodes) == len(doc['nodes']) == 2 and
            {n['name'] for n in nodes.values()} == set(PORTS), 'Expected separate elbow and straight roots')
    require(glb.objects() == {node['name']: i for i, node in nodes.items()}, 'Duct object path differs')
    times = stationary_times(glb, nodes)
    by_name = {n['name']: n for n in nodes.values()}
    return measure_pair(raw, glb, by_name['elbow'], by_name['straight'], width, frame, times)


def measure_pair(raw, glb, elbow, straight, width, frame, times):
    ports = {role: port(glb, node, width, frame, role)
             for role, node in [('elbow', elbow), ('straight', straight)]}
    rim_errors, gaps = [], []
    for key in ('outer_loop_m', 'inner_loop_m'):
        for a,b in zip(ports['elbow'][key], ports['straight'][key]):
            rim_errors.append(math.dist(a,b))
            gaps.append(abs(a[0]-b[0]))
    displacement = sub(ports['straight']['inner_center_m'], ports['elbow']['inner_center_m'])
    measured = dict(sha256=hashlib.sha256(raw).hexdigest(), bore_width_m=width, stationary_keys_s=times,
                    max_plane_gap_m=max(gaps), max_matched_corner_distance_m=max(rim_errors),
                    inner_center_displacement_m=frame.vector(displacement), rectangular_rim_overlap_m2=rectangular_overlap(ports),
                    ports=ports)
    for name, row in ports.items():
        for key in ('outer_loop_m', 'inner_loop_m'):
            row[key] = [frame.world(point) for point in row[key]]
        row['inner_center_m'] = frame.world(row['inner_center_m'])
        row['cap_normal'] = frame.vector(row['cap_normal'])
        if name == 'straight':
            row['outlet_center_m'] = frame.world(row['outlet_center_m'])
            row['centerline_direction'] = frame.vector(row['centerline_direction'])
    for name, row in ports.items():
        if row['max_expected_corner_distance_m'] > TOL:
            raise JointFailure(name + ' rim corner differs', measured)
        if row['intersects_required_opening']:
            raise JointFailure(name + ' obstructed opening', measured)
        if abs(row['annulus_area_m2']-(4-width**2)) > AREA_TOL or abs(row['clear_area_m2']-width**2) > AREA_TOL:
            raise JointFailure(name + ' incorrect annulus area', measured)
    if ports['straight']['centerline_error'] > TOL:
        raise JointFailure('straight centerline differs', measured)
    if max(rim_errors) > TOL or max(gaps) > TOL:
        raise JointFailure('Joint separation exceeds tolerance', measured)
    return measured


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--width', type=float, default=1, choices=(1,1.25))
    parser.add_argument('--placement', default='fixed', choices=('fixed', 'oblique', 'third'))
    args = parser.parse_args()
    try:
        print(json.dumps(measure(args.glb.read_bytes(), args.width, args.placement), indent=2))
    except JointFailure as exc:
        print(json.dumps({'failure': str(exc), 'measurements': exc.measurements}, indent=2))
        sys.exit(1)
    except ValueError as exc:
        parser.exit(1, str(exc)+'\n')
