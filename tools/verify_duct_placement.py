"""Verify third-placement GLBs against the independent, frozen C163 fixture."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_connected_duct import GLB, cross, measure, place, require, stationary_times, sub
else:
    from verify_connected_duct import GLB, cross, measure, place, require, stationary_times, sub


CONTRACT = Path(__file__).resolve().parents[1] / 'examples/connected-duct/third-contract.json'


def endpoints(raw):
    """Read endpoint centers and winding directions before imposing any mating constraints."""
    glb = GLB(raw, target='ontokin.glb/0.11')
    roots = glb.reference('scenes', glb.document['scene'])['nodes']
    objects = glb.objects()
    require(set(objects) == {'elbow', 'straight'} and sorted(roots) == sorted(objects.values()),
            'Expected both duct occurrences in the active scene')
    indexed = {i: glb.reference('nodes', i) for i in roots}
    stationary_times(glb, indexed)
    nodes = {name: indexed[i] for name, i in objects.items()}
    require(all(node['name'] == name for name, node in nodes.items()), 'Duct occurrence name differs')
    faces = {}
    for name, node in nodes.items():
        for primitive in glb.reference('meshes', node['mesh'])['primitives']:
            region = primitive['extras']['ontokin']['region_key']
            if region not in ('bottom', 'top'):
                continue
            positions = glb.accessor(primitive['attributes']['POSITION'])
            indices = glb.accessor(primitive['indices'])
            center_sum, normal_sum, area_sum = [0.] * 3, [0.] * 3, 0.
            for i in range(0, len(indices), 3):
                a, b, c = [place(positions[j], node) for j in indices[i:i+3]]
                normal = cross(sub(b, a), sub(c, a))
                area = math.hypot(*normal) / 2
                for k in range(3):
                    center_sum[k] += area * (a[k] + b[k] + c[k]) / 3
                    normal_sum[k] += normal[k]
                area_sum += area
            faces[name, region] = ([v / area_sum for v in center_sum],
                                    [v / math.hypot(*normal_sum) for v in normal_sum])
    return glb, nodes, faces


def quaternion_error(node, target):
    x, y, z, w = node['rotation']
    actual = (w, x, y, z)
    return min(math.dist(actual, target), math.dist(actual, [-v for v in target]))


def source_identity(glb, nodes):
    """Return comparable occurrence records after checking the two mutable source revisions."""
    records = deepcopy(nodes)
    program = glb.document['extras']['ontokin']['program']
    entry = program['sources']['entry']
    parts = 'sha256:' + hashlib.sha256(CONTRACT.with_name('parts.ok').read_bytes()).hexdigest()
    for unit in program['manifest']['units']:
        source = program['sources'][unit['source_id']]
        require(all(source.get(key) == value for key, value in unit.items()), 'Source manifest differs')
    for name, node in records.items():
        identity = node['extras']['ontokin']
        mapping = identity['source_mapping']
        require(mapping == program['occurrences'][name] and mapping['path'] == name
                and mapping['class_id'] == identity['class_name']
                and identity['element_id'] == mapping['element_id']
                and identity['program_revision'] == program['revision'],
                name + ' occurrence source mapping differs')
        for location in (mapping['definition'], mapping['declaration']):
            source = program['sources'][location['source_id']]
            require(all(location[key] == source[key] for key in ('filename', 'source_revision')),
                    name + ' source revision differs')
        require(mapping['declaration']['source_id'] == 'entry', 'Unexpected declaration source')
        require(mapping['definition']['filename'] == 'parts.ok' and mapping['definition']['source_revision'] == parts,
                'Unexpected parts definition source')
        del mapping['declaration']['source_revision']
        del identity['program_revision']
        if name == 'straight':
            del mapping['declaration']['end_byte']
            del node['translation'], node['rotation']
    return entry['source_revision'], records


def verify(before, after):
    spec = json.loads(CONTRACT.read_text())
    tol = spec['coordinate_tolerance_m']
    initial, nodes, faces = endpoints(before)
    elbow, normal = faces['elbow', 'top']
    inlet, inlet_normal = faces['straight', 'bottom']
    require(math.dist(elbow, spec['elbow_outlet_center_m']) <= tol
            and quaternion_error(nodes['elbow'], spec['rotation_wxyz']) <= spec['unit_normal_tolerance'],
            'Initial elbow placement differs from freeze')
    displacement = sub(inlet, elbow)
    expected_displacement = [v * spec['defective_axial_gap_m'] for v in spec['elbow_outlet_normal']]
    require(math.dist(displacement, expected_displacement) <= tol, 'Initial inlet displacement differs from freeze')
    # The fixture applies its signed tilt about the nominal straight's local Y axis.
    w, x, y, z = spec['straight_target_rotation_wxyz']
    half = math.radians(spec['defective_axis_error_deg']) / 2
    c, s = math.cos(half), math.sin(half)
    tilted = (w*c-y*s, x*c-z*s, y*c+w*s, z*c+x*s)
    require(quaternion_error(nodes['straight'], tilted) <= spec['unit_normal_tolerance'],
            'Initial straight orientation differs from freeze')
    gap = sum(a*b for a,b in zip(displacement, normal))
    angle = math.degrees(math.atan2(math.hypot(*cross(inlet_normal, normal)),
                                    -sum(a*b for a,b in zip(inlet_normal, normal))))
    require(abs(gap-spec['defective_axial_gap_m']) <= tol, 'Initial axial gap differs from freeze')
    require(abs(angle-spec['defective_axis_error_deg']) <= math.degrees(spec['unit_normal_tolerance']),
            'Initial tilt differs from freeze')
    measured = measure(after, placement='third')
    final, fixed, final_faces = endpoints(after)
    roll_error = quaternion_error(fixed['straight'], spec['straight_target_rotation_wxyz'])
    require(initial.geometry_streams() == final.geometry_streams(), 'Local duct geometry streams changed')
    entry_revision, original_identity = source_identity(initial, nodes)
    _, repaired_identity = source_identity(final, fixed)
    frozen = hashlib.sha256(CONTRACT.with_name('assembly-misplaced.ok').read_bytes()).hexdigest()
    require(entry_revision == 'sha256:' + frozen, 'Initial entry revision differs from frozen source')
    require(original_identity == repaired_identity, 'Duct geometry, placement or source identity changed')
    for label, endpoint in [('elbow_inlet', ('elbow','bottom')), ('elbow_outlet', ('elbow','top')),
                            ('straight_inlet', ('straight','bottom')), ('straight_outlet', ('straight','top'))]:
        require(math.dist(final_faces[endpoint][0], spec[label+'_center_m']) <= tol, label+' center differs')
    for name in ('elbow','straight'):
        port = measured['ports'][name]
        for key in ('inner_loop_m', 'outer_loop_m'):
            for corner in spec[key]:
                require(min(math.dist(corner,p) for p in port[key]) <= tol, name+' corner differs')
    require(abs(measured['rectangular_rim_overlap_m2'] - spec['expected_shared_area_m2']['repaired'])
            <= spec['area_tolerance_m2'], 'Shared opening differs')
    require(roll_error <= spec['unit_normal_tolerance'], 'Wrong square-roll solution')
    return dict(initial_axial_gap_m=gap, initial_axis_error_deg=angle,
                target_quaternion_distance=roll_error, repaired=measured)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.before.read_bytes(), args.after.read_bytes()), indent=2))
