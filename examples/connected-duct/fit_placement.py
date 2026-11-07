"""Fit a stationary duct joint from the named cap triangles of an exported GLB."""
from collections import Counter
from math import atan2, cos, dist, hypot, sin
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.verify_connected_duct import GLB, TOL, cross, place, require, stationary_times, sub


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(v):
    length = hypot(*v)
    require(length > 1e-12, 'Degenerate frame direction')
    return tuple(x/length for x in v)


def compose(q, p):
    w, *a = q
    v, *b = p
    return unit((w*v-dot(a, b), *(w*y+v*x+z for x, y, z in zip(a, b, cross(a, b)))))


def rotate(q, p):
    return place(p, {'rotation': (*q[1:], q[0]), 'translation': (0, 0, 0)})


def cap_frame(glb, node, endpoint):
    name = node['name']
    mesh = glb.reference('meshes', node['mesh'])
    require('skin' not in node and 'weights' not in node and 'weights' not in mesh, 'Expected rigid duct')
    meta = node['extras']['ontokin']
    # Region labels are corroborated by their independently carried source palette.
    # All frame coordinates and winding below come from the rendered triangles.
    palette = {row['key']: row for row in meta['geometry']['materials']}
    edges, adjacent, normals = Counter(), Counter(), []
    for primitive in mesh['primitives']:
        require(primitive.get('mode', 4) == 4 and 'targets' not in primitive, 'Expected rigid triangles')
        region = primitive.get('extras', {}).get('ontokin', {}).get('region_key')
        material = glb.reference('materials', primitive['material'])
        identity = material.get('extras', {}).get('ontokin', {})
        require(isinstance(region, str) and identity.get('source_region_key') == region and
                identity.get('occurrence_path') == name and identity.get('element_id') == meta['element_id'] and
                material.get('name') == f'{name}: {region}', 'Inconsistent endpoint identity')
        pbr = material['pbrMetallicRoughness']
        expected = palette[region]
        require((pbr.get('baseColorFactor'), pbr.get('metallicFactor'), pbr.get('roughnessFactor')) ==
                (expected['rgba'], expected['metallic'], expected['roughness']), 'Inconsistent endpoint material')
        points = [place(p, node) for p in glb.accessor(primitive['attributes']['POSITION'])]
        indices = glb.accessor(primitive['indices'])
        require(len(indices) % 3 == 0 and all(0 <= i < len(points) for i in indices), 'Invalid cap indices')
        for i in range(0, len(indices), 3):
            a, b, c = (points[j] for j in indices[i:i+3])
            sides = ((a, b), (b, c), (c, a))
            if region == endpoint:
                normals.append(cross(sub(b, a), sub(c, a)))
                edges.update(sides)
            else:
                adjacent.update(sides)
    require(normals and all(n == 1 for n in edges.values()), 'Missing cap or duplicate face edge')
    normal = unit(tuple(map(sum, zip(*normals))))
    require(all(dist(unit(n), normal) < TOL for n in normals), 'Inconsistent cap winding')
    boundary = {(a, b) for a, b in edges if (b, a) not in edges}
    require(all(adjacent[b, a] == 1 and adjacent[a, b] == 0 for a, b in boundary),
            'Cap winding or rim differs from adjacent wall')
    corners = {p for edge in boundary for p in edge}
    require(len(corners) == len(boundary) == 8, 'Expected two four-corner loops')
    center = tuple(sum(axis)/8 for axis in zip(*sorted(corners)))
    ordered = sorted(corners, key=lambda p: dist(center, p))
    inner, outer = ordered[:4], ordered[4:]
    require(dist(center, outer[0])-dist(center, inner[-1]) > TOL, 'Indistinguishable rim loops')
    for ring in (inner, outer):
        radial = dist(ring[0], center)
        for p in ring:
            require(abs(dot(sub(p, center), normal)) < TOL and abs(dist(p, center)-radial) < TOL,
                    'Cap corners do not form concentric planar rims')
            neighbors = [v for a, v in boundary if a == p]
            require(len(neighbors) == 1 and neighbors[0] in ring and
                    abs(dot(unit(sub(p, center)), unit(sub(neighbors[0], center)))) < TOL,
                    'Incomplete square rim loop')
    return center, normal, sorted(outer), sorted(inner)


def solve_placement(raw, *, elbow_region='top', straight_region='bottom'):
    """Return the absolute straight placement in OntoKin translation/quaternion order."""
    require((elbow_region, straight_region) == ('top', 'bottom'), 'Expected elbow outlet and straight inlet')
    glb = GLB(raw, target='ontokin.glb/0.11')
    require(not glb.document.get('extensionsUsed') and not glb.document.get('extensionsRequired'),
            'Expected unextended GLB')
    paths = glb.objects()
    roots = glb.reference('scenes', glb.document['scene'])['nodes']
    require(set(paths) == {'elbow', 'straight'} and sorted(roots) == sorted(paths.values()),
            'Expected the named duct roots')
    nodes = {i: glb.reference('nodes', i) for i in roots}
    occurrences = glb.document['extras']['ontokin']['program']['occurrences']
    for name, i in paths.items():
        node = nodes[i]
        meta = node['extras']['ontokin']
        mapping = occurrences[name]
        require(node['name'] == mapping['path'] == name and meta.get('source_mapping') == mapping and
                meta.get('element_id') == mapping['element_id'] and meta.get('class_name') == mapping['class_id'],
                'Inconsistent occurrence identity')
    stationary_times(glb, nodes)
    straight = nodes[paths['straight']]
    target, outlet, outer, inner = cap_frame(glb, nodes[paths['elbow']], elbow_region)
    source, inlet, old_outer, old_inner = cap_frame(glb, straight, straight_region)
    desired = tuple(-x for x in outlet)
    diagonal = unit(sub(old_outer[0], source))
    # Swing the inlet normal onto the mating normal. At a half turn the rim
    # diagonal supplies an orthogonal axis. The roll step handles each corner.
    axis = cross(inlet, desired)
    swing_angle = atan2(hypot(*axis), dot(inlet, desired))
    swing_axis = unit(axis) if hypot(*axis) > 1e-12 else diagonal
    swing = (cos(swing_angle/2), *(sin(swing_angle/2)*x for x in swing_axis))
    aligned = rotate(swing, diagonal)
    candidates = []
    for p in outer:
        goal = unit(sub(p, target))
        roll = atan2(dot(desired, cross(aligned, goal)), dot(aligned, goal))
        twist = (cos(roll/2), *(sin(roll/2)*x for x in desired))
        candidates.append(compose(twist, swing))
    # Largest |w| is the smallest rotation angle. Lexical target-corner order
    # breaks ties within floating-point precision.
    best = max(abs(q[0]) for q in candidates)
    correction = next(q for q in candidates if best-abs(q[0]) < 1e-12)
    for initial, final in ((old_outer, outer), (old_inner, inner)):
        for p in initial:
            predicted = rotate(correction, sub(p, source))
            require(min(dist(predicted, sub(t, target)) for t in final) < TOL, 'Rim dimensions do not match')
    offset = rotate(correction, sub(straight['translation'], source))
    x, y, z, w = straight['rotation']
    return {'translation_m': [a+b for a, b in zip(target, offset)],
            'rotation_wxyz': list(compose(correction, (w, x, y, z)))}
