"""Check the named C164 joint against its frozen three-occurrence contract."""
import argparse
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_connected_duct import PortFrame, cross, measure_pair, require, stationary_times
    from .verify_duct_placement import endpoints, quaternion_error, source_identity
else:
    from verify_connected_duct import PortFrame, cross, measure_pair, require, stationary_times
    from verify_duct_placement import endpoints, quaternion_error, source_identity


EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/connected-duct'


def read_scene(raw, spec):
    moving = spec['moving'][0]
    names = [*spec['stationary'], moving]
    glb, nodes, faces = endpoints(raw, names)
    require(not glb.document.get('extensionsUsed') and not glb.document.get('extensionsRequired'),
            'Expected unextended GLB')
    streams = glb.geometry_streams()
    target, decoy = spec['target'][0], spec['decoy'][0]
    elbow_streams = {(region, role): data for (name, region, role), data in streams.items() if name == target}
    require(elbow_streams == {(region, role): data for (name, region, role), data in streams.items() if name == decoy},
            'Stationary elbows have different local geometry')
    program = glb.document['extras']['ontokin']['program']
    require(set(program['occurrences']) == set(nodes), 'Inconsistent occurrence inventory')
    for name, node in nodes.items():
        require(not any(key in node for key in ('matrix', 'scale', 'children')), name + ' unexpected transform')
        identity = node['extras']['ontokin']
        kind = 'straight' if name == moving else 'elbow'
        require(identity['class_name'] == 'package/example.connected-duct-parts/duct-parts/definitions/' + kind
                and identity['element_id'] == ['connected-duct', 'demo', name], name + ' instance identity differs')
        palette = {row['key']: row for row in identity['geometry']['materials']}
        for prim in glb.primitives(name):
            region = prim['extras']['ontokin']['region_key']
            material = glb.reference('materials', prim['material'])
            expected = palette[region]
            pbr = material['pbrMetallicRoughness']
            require((pbr['baseColorFactor'], pbr['metallicFactor'], pbr['roughnessFactor']) ==
                    (expected['rgba'], expected['metallic'], expected['roughness']), name + ' source material differs')
            meta = material['extras']['ontokin']
            require(meta['occurrence_path'] == name and meta['source_region_key'] == region
                    and meta['element_id'] == identity['element_id'] and meta['program_revision'] == program['revision']
                    and material['name'] == f'{name}: {region}', name + ' material occurrence identity differs')
    for name, pose in spec['stationary'].items():
        require(math.dist(nodes[name]['translation'], pose['translation_m']) <= spec['coordinate_tolerance_m']
                and quaternion_error(nodes[name], pose['rotation_wxyz']) <= spec['unit_normal_tolerance']
                and math.dist(faces[name, 'top'][0], pose['outlet_center_m']) <= spec['coordinate_tolerance_m'],
                name + ' stationary pose differs from freeze')
    revision, identities = source_identity(glb, nodes, moving)
    return glb, nodes, faces, streams, revision, identities


def roll_candidates(spec):
    """Postmultiply the nominal orientation by the four rolls about the straight's local Z."""
    w, x, y, z = spec['straight_target_rotation_wxyz']
    start = spec['initial_moving']['rotation_wxyz']
    candidates = []
    for i in range(4):
        c, s = math.cos(i*math.pi/4), math.sin(i*math.pi/4)
        q = (w*c-z*s, x*c+y*s, y*c-x*s, z*c+w*s)
        dot = abs(sum(a*b for a, b in zip(start, q)))
        candidates.append((math.degrees(2*math.acos(min(1, dot))), q))
    return candidates


def verify(before, after, decoy_control=None):
    spec = json.loads((EXAMPLE / 'selection-contract.json').read_text())
    moving, inlet = spec['moving']
    target, outlet = spec['target']
    decoy, decoy_outlet = spec['decoy']
    _, nodes, faces, streams, revision, identities = read_scene(before, spec)
    require(revision == 'sha256:' + hashlib.sha256((EXAMPLE / 'assembly-selection.ok').read_bytes()).hexdigest(),
            'Original entry source differs from freeze')
    start = spec['initial_moving']
    tol = spec['coordinate_tolerance_m']
    require(math.dist(nodes[moving]['translation'], start['translation_m']) <= tol and
            quaternion_error(nodes[moving], start['rotation_wxyz']) <= spec['unit_normal_tolerance'],
            'Initial moving pose differs from freeze')
    distances = {name: math.dist(faces[moving, inlet][0], faces[name, region][0])
                 for name, region in [spec['target'], spec['decoy']]}
    require(distances[decoy] < distances[target] and all(abs(d - spec['initial_outlet_distances_m'][name]) <= tol
                                                        for name, d in distances.items()), 'Initial outlet distances differ')
    candidates = roll_candidates(spec)
    best_angle, best = min(candidates)
    n, m = faces[target, outlet][1], faces[moving, inlet][1]
    tilt = math.degrees(math.atan2(math.hypot(*cross(n, m)), -sum(a*b for a,b in zip(n,m))))

    def check_joint(raw, selected, region):
        glb, fixed, caps, geometry, _, current = read_scene(raw, spec)
        require(geometry == streams and current == identities, 'Local geometry, occurrence or imported definition changed')
        distance = math.dist(caps[moving, inlet][0], caps[selected, region][0])
        require(distance <= tol, f'{moving}/{inlet} is {distance:.9g} m from {selected}/{region}')
        frame = PortFrame(spec['stationary'][selected]['outlet_center_m'], spec['joint_axes'])
        measured = measure_pair(raw, glb, fixed[selected], fixed[moving], spec['bore_width_m'], frame,
                                stationary_times(glb, {i: fixed[name] for name, i in glb.objects().items()}))
        ports = measured['ports']
        normal_error = math.dist(ports['elbow']['cap_normal'], [-v for v in ports['straight']['cap_normal']])
        require(normal_error <= spec['unit_normal_tolerance'], 'Port normals do not oppose')
        measured['opposing_normal_error'] = normal_error
        require(abs(measured['rectangular_rim_overlap_m2'] - spec['shared_area_m2']) <= spec['area_tolerance_m2'],
                'Incorrect common opening')
        require(quaternion_error(fixed[moving], best) <= spec['unit_normal_tolerance'], 'Wrong square-roll solution')
        measured['ports'] = {f'{selected}/{region}': measured['ports']['elbow'],
                             f'{moving}/{inlet}': measured['ports']['straight']}
        return measured

    result = dict(initial_sha256=hashlib.sha256(before).hexdigest(), initial_inlet_center_m=faces[moving, inlet][0],
                  initial_outlet_distances_m=distances, initial_axis_error_deg=tilt,
                  initial_outlet_centers_m={name: faces[name, 'top'][0] for name in spec['stationary']},
                  candidate_rotation_angles_deg=[angle for angle, q in candidates], selected_rotation_angle_deg=best_angle,
                  repaired=check_joint(after, target, outlet))
    if decoy_control is not None:
        flush = check_joint(decoy_control, decoy, decoy_outlet)
        try:
            check_joint(decoy_control, target, outlet)
        except ValueError as exc:
            require(f'from {target}/{outlet}' in str(exc), 'Wrong joint rejected for unexpected reason')
            result['decoy_control'] = dict(flush=flush, rejected_by_named_contract=str(exc))
        else:
            raise ValueError('Wrong joint passed named target verification')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--decoy-control', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.before.read_bytes(), args.after.read_bytes(),
                            args.decoy_control.read_bytes() if args.decoy_control else None), indent=2))
