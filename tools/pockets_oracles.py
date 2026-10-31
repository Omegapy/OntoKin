"""Independent supplied-byte checks for the frozen blind polygon pocket inputs.

No OntoKin product code is imported. The strict accessor reader, exact planar
domain predicates, and independent shared-simplex reader are inherited from
earlier tools oracles. Pocket depths, faces and domains are reconstructed here
from the independently authored boundaries, never from a production mesh.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
import math
import struct

from tools.extrusion_oracles import close
from tools.framed_loft_oracles import (
    Decoded as _StrictReader, placement_matrix, place_point,
    _matrix_vector, _native, _binary64, _sign_cap,
)
from tools.holes_oracles import _cap_domain, _overlap_area2, _turn
from tools.ring_loft_oracles import (
    _cyclic, _face_measure, _check_face_normals, _exact_signed_volume6,
    check_surface_intersections,
)


class Decoded(_StrictReader):
    """Retain strict independent accessors with explicit .12 container admission."""

    def __init__(self, data, *, target='ontokin.glb/0.12',
                 profile='polygon-pockets-0.1', version='0.12'):
        assert len(data) >= 28
        assert struct.unpack_from('<III', data) == (0x46546c67, 2, len(data))
        length, kind = struct.unpack_from('<II', data, 12)
        assert kind == 0x4e4f534a and length % 4 == 0 and 20+length+8 <= len(data)
        self.document = json.loads(data[20:20+length])
        start = 20+length
        size, kind = struct.unpack_from('<II', data, start)
        assert kind == 0x004e4942 and size % 4 == 0 and start+8+size == len(data)
        self.binary = data[start+8:]
        buffers = self.document['buffers']
        assert len(buffers) == 1 and buffers[0].get('uri') is None
        declared = buffers[0]['byteLength']
        assert type(declared) is int and 0 <= size-declared <= 3
        meta = self.document['extras']['ontokin']
        assert meta['target_contract'] == target
        assert meta['profile'] == profile and meta['schema_version'] == version
        for node in self.document.get('nodes', []):
            scale = node.get('scale', [1, 1, 1])
            assert len(scale) == 3 and all(type(v) in (int, float) for v in scale)
            assert scale == [1, 1, 1] and 'matrix' not in node and not node.get('children')
        for animation in self.document.get('animations', []):
            targets = set()
            for channel in animation['channels']:
                target = channel['target']
                assert target['path'] in ('translation', 'rotation')
                key = (target['node'], target['path'])
                assert key not in targets
                targets.add(key)


class LegacyDecoded(Decoded):
    """Apply the same strict byte reader to the actual zero-pocket .8 reference."""

    def __init__(self, data):
        super().__init__(data, target='ontokin.glb/0.8',
                         profile='polygon-extrusion-0.1', version='0.8')


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _rotation_error(actual, expected):
    """Shortest quaternion angle in radians, including the equivalent sign."""
    assert len(actual) == len(expected) == 4
    assert all(math.isfinite(v) for v in (*actual, *expected))
    assert abs(math.hypot(*actual)-1) <= 1e-5 and abs(math.hypot(*expected)-1) <= 1e-5
    ax,ay,az,aw = actual
    bx,by,bz,bw = expected
    imaginary = (bw*ax-aw*bx-by*az+bz*ay,
                 bw*ay-aw*by-bz*ax+bx*az,
                 bw*az-aw*bz-bx*ay+by*ax)
    real = sum(a*b for a,b in zip(actual,expected))
    return 2*math.atan2(math.hypot(*imaginary),abs(real))


def _ratio(value):
    assert set(value) == {'numerator', 'denominator'}
    assert type(value['numerator']) is type(value['denominator']) is str
    result = Fraction(int(value['numerator']), int(value['denominator']))
    assert str(result.numerator) == value['numerator'] and str(result.denominator) == value['denominator']
    return result


def _domain(boundaries, coordinates, count, region, sign):
    lines = [(a, b) for vertices in boundaries for a, b in zip(vertices, vertices[1:]+vertices[:1])]
    polygons = [[coordinates[i] for i in vertices] for vertices in boundaries]
    exact_lines = [(coordinates[a], coordinates[b]) for a, b in lines]
    area2 = sum((a[0]*b[1]-a[1]*b[0] for a, b in exact_lines), Fraction(0))
    assert area2 > 0
    return {'outer': polygons[0], 'holes': polygons[1:], 'boundaries': lines,
            'exact_boundaries': exact_lines, 'coordinates': coordinates, 'area2': area2,
            'count': count, 'region': region, 'sign': sign}


def source_facts(wanted):
    """Recompute floors, logical positions, face counts and domains independently."""
    outer = sorted(wanted['outer_vertices'], key=lambda v: v['order'])
    pockets = sorted(wanted['pockets'], key=lambda p: p['order'])
    pockets = [{**p, 'vertices': sorted(p['vertices'], key=lambda v: v['order'])} for p in pockets]
    assert 0 <= len(pockets) <= 8 and len(outer) >= 3
    n = len(outer)+sum(len(p['vertices']) for p in pockets)
    assert n <= 64 and len({p['key'] for p in pockets}) == len(pockets)
    assert len({p['order'] for p in pockets}) == len(pockets)
    assert all(type(p['order']) is int and 0 <= p['order'] <= 65535 for p in pockets)
    height = Fraction(float(wanted['height_m']))
    assert Fraction(.001) <= height <= 100
    source, coordinates, boundaries, floors = {}, {}, [], {}
    for kind, key, vertices, floor in [('outer', 'outer', outer, 0.0)]+[
            ('pocket', p['key'], p['vertices'], None) for p in pockets]:
        assert len(vertices) >= 3 and len({v['key'] for v in vertices}) == len(vertices)
        assert len({v['order'] for v in vertices}) == len(vertices)
        assert all(type(v['order']) is int and 0 <= v['order'] <= 65535 for v in vertices)
        if kind == 'pocket':
            p = next(p for p in pockets if p['key'] == key)
            depth = Fraction(float(p['depth_m']))
            assert Fraction(.001) <= depth <= 100 and depth < height
            base = height-depth
            assert base >= Fraction(.001)
            floor = _binary64(base)
            effective = height-Fraction(floor)
            assert 0 < floor < height
            assert p['floor_m'] == p['remaining_base_m'] == floor
            assert _ratio(p['exact_remaining_base_m']) == base
            assert _ratio(p['effective_depth_m']) == effective
            floors[key] = floor
        ids = []
        for vertex in vertices:
            point = _native(vertex['point_m'], 2)
            assert all(abs(v) <= 100 for v in point)
            planar = (kind, key, vertex['key'])
            assert planar not in coordinates
            coordinates[planar] = point
            ids.append(planar)
            for level, z in (('lower', floor), ('top', float(height))):
                source[(*planar, level)] = (float(point[0]), float(point[1]), z)
        boundaries.append(ids)
    assert len(set(source.values())) == len(source) == 2*n
    if 'source_positions' in wanted:
        witnesses = {tuple(p['identity']): tuple(p['position_m']) for p in wanted['source_positions']}
        assert len(witnesses) == len(wanted['source_positions']) and witnesses == source
    domains = {
        'bottom': _domain([boundaries[0]], {i: coordinates[i] for i in boundaries[0]}, len(outer)-2,
                          wanted['bottom_region'], -1),
        'top': _domain(boundaries, coordinates, n+2*len(pockets)-2, wanted['top_region'], 1),
    }
    for pocket, ids in zip(pockets, boundaries[1:]):
        reversed_ids = [ids[0], *reversed(ids[1:])]
        domains['floor:'+pocket['key']] = _domain([reversed_ids],
            {i: coordinates[i] for i in ids}, len(ids)-2, pocket['floor_region'], 1)
    walls = {}
    for vertices, ids in zip([outer]+[p['vertices'] for p in pockets], boundaries):
        for index, vertex in enumerate(vertices):
            a, b = ids[index], ids[(index+1) % len(ids)]
            for triple in (((*a, 'lower'), (*b, 'lower'), (*a, 'top')),
                           ((*b, 'lower'), (*b, 'top'), (*a, 'top'))):
                walls[_cyclic(triple)] = vertex['region']
    assert wanted['authored_vertex_count'] == n and wanted['logical_vertex_count'] == 2*n
    assert wanted['pocket_count'] == len(pockets)
    assert wanted['bottom_triangle_count'] == len(outer)-2
    assert wanted['top_triangle_count'] == n+2*len(pockets)-2
    assert wanted['floor_triangle_count'] == n-len(outer)-2*len(pockets)
    assert wanted['wall_triangle_count'] == 2*n
    assert wanted['triangle_count'] == 4*n-4 and wanted['vertex_count'] == 12*n-12
    return source, domains, walls, floors


def check_geometry(decoded, path, wanted):
    """Require actual blind floors and complete independent face-domain coverage."""
    triangles = decoded.triangles(path)
    assert len(triangles) == wanted['triangle_count'], 'Complete triangle count differs'
    source, domains, expected_walls, floors = source_facts(wanted)
    offset = wanted.get('local_placement_m', [0, 0, 0])
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    matrix = placement_matrix(rotation)
    axis = tuple(row[2] for row in matrix)
    placed = {identity: place_point(p, rotation, offset) for identity, p in source.items()}
    quantized = {identity: tuple(_f32(v) for v in p) for identity, p in placed.items()}
    inverse = {p: identity for identity, p in quantized.items()}
    assert len(inverse) == len(source), 'Distinct source identities collapse after delivery'
    for identity, p in quantized.items():
        close(p, placed[identity], 1e-5)

    def rotate(normal):
        return tuple(_binary64(v) for v in _matrix_vector(matrix, _native(normal, 3)))

    seen, walls, regions, edges = set(), Counter(), Counter(), Counter()
    cap_faces = {k: [] for k in domains}
    cap_edges = {k: Counter() for k in domains}
    actual_triangles, source_triangles, actual_ids, areas, source_areas = [], [], [], [], []
    for region, positions, normals, material in triangles:
        assert len(positions) == len(normals) == 3
        positions = [tuple(p) for p in positions]
        ids = []
        for p in positions:
            assert all(math.isfinite(v) for v in p) and p in inverse, 'Corner is not source-quantized'
            ids.append(inverse[p]);seen.add(inverse[p])
        assert len(set(ids)) == 3, 'A face requires distinct source identities'
        original = [source[i] for i in ids]
        magnitude = _check_face_normals(positions, normals, source_points=original, rotate=rotate)
        assert normals[0] == normals[1] == normals[2], 'Flat face normals differ'
        areas.append(magnitude/2);source_areas.append(_face_measure(original)[1]/2)
        domain = None
        if all(i[-1] == 'top' for i in ids):
            domain = 'top'
        elif all(i[0] == 'outer' and i[-1] == 'lower' for i in ids):
            domain = 'bottom'
        elif all(i[0] == 'pocket' and i[-1] == 'lower' and i[1] == ids[0][1] for i in ids):
            domain = 'floor:'+ids[0][1]
        if domain is None:
            triple = _cyclic(ids)
            assert triple in expected_walls and region == expected_walls[triple], 'Wall diagonal, winding or material differs'
            walls[triple] += 1
        else:
            rule = domains[domain]
            assert region == rule['region'], 'Wrong bottom, top or floor material'
            _sign_cap(original, (Fraction(0),Fraction(0),Fraction(1)), rule['sign'], 'Source '+domain)
            _sign_cap(positions, axis, rule['sign'], 'Delivered '+domain)
            planar_ids = [i[:3] for i in ids]
            for a,b in zip(planar_ids,planar_ids[1:]+planar_ids[:1]):
                cap_edges[domain][a,b] += 1
            positive = planar_ids if rule['sign'] == 1 else list(reversed(planar_ids))
            face = tuple(rule['coordinates'][i] for i in positive)
            _cap_domain(face,rule['outer'],rule['holes'],rule['exact_boundaries'],tuple(rule['coordinates'].values()))
            cap_faces[domain].append(face)
        pbr = material['pbrMetallicRoughness']
        assert region in wanted['palette'] and material['extras']['ontokin']['source_region_key'] == region
        close(pbr['baseColorFactor'],wanted['palette'][region],1e-6)
        close([pbr['metallicFactor'],pbr['roughnessFactor']],[wanted['metallic'],wanted['roughness']],1e-6)
        assert not material.get('doubleSided',False)
        regions[region] += 1
        actual_triangles.append(positions);source_triangles.append(original);actual_ids.append(tuple(ids))
        for a,b in zip(ids,ids[1:]+ids[:1]):edges[a,b] += 1
    assert seen == set(source), 'Every logical source position must occur'
    assert set(walls) == set(expected_walls) and all(v == 1 for v in walls.values()), 'Every prescribed wall must occur once'
    domain_results = []
    for key,rule in domains.items():
        faces = cap_faces[key]
        assert len(faces) == rule['count'], 'Face-domain triangle count differs: '+key
        assert sum((_turn(*t) for t in faces),Fraction(0)) == rule['area2'], 'Domain coverage area differs: '+key
        for index,face in enumerate(faces):
            for other in faces[index+1:]:assert _overlap_area2(face,other) == 0, 'Cap interiors overlap'
        boundary = set(rule['boundaries'] if rule['sign'] == 1 else [(b,a) for a,b in rule['boundaries']])
        observed = cap_edges[key]
        for edge in boundary:assert observed[edge] == 1 and observed[edge[::-1]] == 0, 'Authored directed boundary differs'
        for edge,count in observed.items():
            assert count == 1
            if edge not in boundary:assert edge[::-1] not in boundary and observed[edge[::-1]] == 1
        domain_results.append({'domain':key,'triangles':len(faces),'authored_xy_area_m2':float(rule['area2']/2),'region':rule['region']})
    assert dict(sorted(regions.items())) == wanted['region_triangle_counts']
    assert all(count == 1 and edges[b,a] == 1 for (a,b),count in edges.items()), 'Closed opposite incidence differs'
    original_volume = _exact_signed_volume6(source_triangles)/6
    actual_volume = _exact_signed_volume6(actual_triangles)/6
    assert original_volume > 0 and actual_volume > 0, 'Signed volume must be positive'
    assert original_volume == Fraction(*map(int,wanted['volume_exact'])), 'Exact source volume differs'
    source_contacts = check_surface_intersections(source_triangles,actual_ids)
    actual_contacts = check_surface_intersections(actual_triangles,actual_ids)
    assert abs(math.fsum(source_areas)-wanted['surface_area_m2']) <= 1e-4
    assert abs(math.fsum(areas)-wanted['surface_area_m2']) <= 1e-4
    assert abs(float(actual_volume)-wanted['volume_m3']) <= 1e-4
    bounds = [[min(p[j] for p in placed.values()) for j in range(3)],
              [max(p[j] for p in placed.values()) for j in range(3)]]
    for actual,expected in zip(bounds,wanted['bounds_m']):close(actual,expected,1e-5)
    return {'status':'passed','path':path,'pockets':len(floors),'authored_vertices':wanted['authored_vertex_count'],
            'logical_vertices':len(source),'triangles':len(triangles),'flat_corners':3*len(triangles),
            'regions':dict(regions),'surface_area_m2':math.fsum(areas),'signed_volume_m3':float(actual_volume),
            'source_signed_volume_m3':float(original_volume),'face_domains':domain_results,'floor_coordinates_m':floors,
            'bounds_m':bounds,'oriented_edges':len(edges),'intersections':actual_contacts,
            'source_intersections':source_contacts,
            'coverage':'independent exact floor arithmetic, authored XY bottom/top/floor domains and complete actual 3D surfaces'}


def check_glb(data, nodes, program_revision=None, sample_times=(0,.25,.5,.75,1), *, legacy=False):
    """Inspect complete supplied carrier membership and fixed/dense rigid motion."""
    decoded = LegacyDecoded(data) if legacy else Decoded(data)
    assert set(decoded.objects()) == set(nodes)
    native_nodes = decoded.document['nodes']
    assert len(decoded.objects()) == len(native_nodes)
    assert all(n['extras']['ontokin']['kind'] == 'object' for n in native_nodes)
    mesh_indices = [n['mesh'] for n in native_nodes if 'mesh' in n]
    assert len(set(mesh_indices)) == len(mesh_indices)
    assert set(mesh_indices) == set(range(len(decoded.document.get('meshes', []))))
    scenes = decoded.document['scenes'];index = decoded.document.get('scene',0)
    assert type(index) is int and 0 <= index < len(scenes)
    roots = scenes[index]['nodes']
    assert all(type(i) is int for i in roots)
    assert len(roots) == len(decoded.document['nodes']) and set(roots) == set(range(len(roots)))
    animations = decoded.document.get('animations',[])
    assert len(animations) == 1
    channels = animations[0]['channels']
    assert {(c['target']['node'],c['target']['path']) for c in channels} == {
        (i,channel) for i in range(len(roots)) for channel in ('translation','rotation')}
    for channel in channels:
        i = channel['sampler'];assert type(i) is int and 0 <= i < len(animations[0]['samplers'])
        sampler = animations[0]['samplers'][i]
        assert sampler.get('interpolation','LINEAR') == 'LINEAR'
        clocks,rows = decoded.accessor(sampler['input']),decoded.accessor(sampler['output'])
        assert len(clocks) == len(rows) >= 2
        assert all(math.isfinite(v) for v in clocks) and all(a < b for a,b in zip(clocks,clocks[1:]))
        assert clocks == list(sample_times), 'Recorded key clocks must equal the frozen sampling grid'
        components = 3 if channel['target']['path'] == 'translation' else 4
        assert all(len(row) == components and all(math.isfinite(v) for v in row) for row in rows)
        if components == 4:assert all(abs(math.hypot(*row)-1) <= 1e-5 for row in rows)
    if program_revision is not None:assert decoded.document['extras']['ontokin']['program']['revision'] == program_revision
    geometry,observations = [],[]
    times = sorted(set(sample_times)|{i/20 for i in range(21)})
    for path,wanted in nodes.items():
        if wanted['geometry'] is None:assert not decoded.triangles(path)
        else:geometry.append(check_geometry(decoded,path,wanted['geometry']))
        native = native_nodes[decoded.objects()[path]]
        first = decoded.pose(path,min(sample_times))
        close(native.get('translation',[0,0,0]),first['translation'],1e-5)
        close(native.get('rotation',[0,0,0,1]),first['rotation'],1e-5)
        for time in times:
            pose = decoded.pose(path,time)
            close(pose['translation'],[x+time*v for x,v in zip(wanted['origin'],wanted['velocity'])],.001)
            assert _rotation_error(pose['rotation'],wanted.get('rotation_xyzw',[0,0,0,1])) <= .001, \
                'Recorded rotation exceeds the frozen angular tolerance'
            observations.append({'path':path,'time_seconds':time,'translation':list(pose['translation']),'rotation':list(pose['rotation'])})
    return {'status':'passed','geometry':geometry,'observations':observations,
            'target_contract':'ontokin.glb/0.8' if legacy else 'ontokin.glb/0.12',
            'program_revision':program_revision}
