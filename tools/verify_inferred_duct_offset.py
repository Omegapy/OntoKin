"""Check an inferred C168 route against the frozen scene, using exported triangles."""
import argparse
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_connected_duct import PortFrame, cross, opening_intersection, place, require
    from .verify_duct_offset_route import EXAMPLE, endpoints, joint
else:
    from verify_connected_duct import PortFrame, cross, opening_intersection, place, require
    from verify_duct_offset_route import EXAMPLE, endpoints, joint


def scene_triangles(glb, nodes):
    for name, node in nodes.items():
        mesh = glb.reference('meshes', node['mesh'])
        for primitive in mesh['primitives']:
            require(primitive.get('mode', 4) == 4 and 'targets' not in primitive, 'Expected rigid triangles')
            vertices = [place(p, node) for p in glb.accessor(primitive['attributes']['POSITION'])]
            indices = glb.accessor(primitive['indices'])
            for i in range(0, len(indices), 3):
                yield name, [vertices[j] for j in indices[i:i+3]]


def obstructions(triangles, frame, width):
    hits = {}
    for name, triangle in triangles:
        if opening_intersection([frame.local(p) for p in triangle], width / 2):
            hits[name] = hits.get(name, 0) + 1
    return hits


def verify(label, before, after):
    spec = json.loads((EXAMPLE / 'inferred-offset-contract.json').read_bytes())
    control = spec['interior_gap'] if label == 'interior-gap' else None
    case = spec['cases'][control['case'] if control else label]
    return verify_case(label, before, after, spec, case, EXAMPLE, control)


def verify_case(label, before, after, spec, case, example, control=None):
    chain = case['chain']
    original, originals, original_caps = endpoints(before, chain)
    glb, nodes, caps = endpoints(after, chain)
    manifest = json.loads((example / case['manifest']).read_bytes())
    for model in (original, glb):
        sources = model.document['extras']['ontokin']['program']['sources']
        for unit in manifest['modules']:
            source = sources['package:' + unit['package_id'] + '@' + unit['version']]
            digest = hashlib.sha256((example / unit['path']).read_bytes()).hexdigest()
            require(source['source_revision'] == 'sha256:' + digest, 'Rigid parts source differs from freeze')
    entry = (example / manifest['entry']['path']).read_bytes()
    require(original.document['extras']['ontokin']['program']['sources']['entry']['source_revision']
            == 'sha256:' + hashlib.sha256(entry).hexdigest(), 'Initial entry differs from freeze')

    fixed = (chain[0], chain[-1])
    for name in fixed:
        require(all(nodes[name][key] == originals[name][key] for key in ('translation', 'rotation')), name + ' moved')
    for node in (*originals.values(), *nodes.values()):
        require(not any(key in node for key in ('scale', 'matrix', 'children', 'skin', 'weights')),
                node['name'] + ' unsupported transform')
    before_streams, after_streams = original.geometry_streams(), glb.geometry_streams()
    rigid = spec['rigid_elbow']
    stream_counts = {}
    tol = spec['maximum_rim_error_m']
    for name in chain[::2]:
        expected = {(name, r, s) for r in rigid['regions'] for s in rigid['preserve_streams']}
        for streams in (before_streams, after_streams):
            require({k for k in streams if k[0] == name} == expected, name + ' stream inventory differs')
        require(all(before_streams[k] == after_streams[k] for k in expected), name + ' local geometry differs')
        stream_counts[name] = len(expected)
        node = originals[name]
        for cap, field in (('bottom', 'inlet'), ('top', 'outlet')):
            center, normal = original_caps[name, cap]
            require(math.dist(center, place(rigid['local_' + field + '_m'], node)) <= tol,
                    name + ' local elbow offset differs')
            rotated = place(rigid[field + '_outward_normal'], {**node, 'translation': (0, 0, 0)})
            require(math.dist(normal, rotated) <= spec['maximum_unit_normal_error'],
                    name + ' local elbow normal differs')

    triangles = list(scene_triangles(glb, nodes))
    reports = []
    axes = case['flow_axes']
    # The frozen flow along the middle segment is a transverse rim axis on the
    # two outer segments. The entry flow plays that role on the middle segment.
    for i, (pair, center, flow) in enumerate(zip(case['joints'], case['joint_centers_m'], axes, strict=True)):
        transverse = axes[0] if i in (2, 3) else axes[2]
        frame = PortFrame(center, (flow, transverse, cross(flow, transverse)))
        cap_pair = [part.split('/') for part in pair]
        row = joint(glb, nodes, caps, cap_pair, center, spec, axes=frame.axes)
        row['observed_centers_m'] = [caps[tuple(p)][0] for p in cap_pair]
        row['observed_normals'] = [caps[tuple(p)][1] for p in cap_pair]
        row['obstructing_triangles_by_occurrence'] = obstructions(triangles, frame, spec['inner_side_m'])
        require(not row['obstructing_triangles_by_occurrence'], f'Obstructed aperture at joint {i+1}')
        reports.append(row)
    expected_spans = list(case['straight_spans_m'])
    if control:
        expected_spans[1] -= control['shorten_middle_by_m']
        open_joint = reports[control['expected_open_joint'] - 1]
        require(abs(open_joint['center_distance_m'] - control['shorten_middle_by_m']) <= tol,
                'Control gap differs from frozen length')
    passed_joints = [i for i, row in enumerate(reports, 1) if row['passed']]
    require(passed_joints == (control['expected_closed_joints'] if control else list(range(1, 7))),
            f'Unexpected closed joints: {passed_joints}')
    spans = {name: math.dist(caps[name, 'top'][0], caps[name, 'bottom'][0]) for name in chain[1::2]}
    require(all(abs(a-b) <= tol for a,b in zip(spans.values(), expected_spans, strict=True)), 'Straight spans differ')
    return {'passed': True, 'case': label, 'initial_sha256': hashlib.sha256(before).hexdigest(),
            'glb_sha256': hashlib.sha256(after).hexdigest(), 'fixed_poses_unchanged': fixed,
            'identical_local_streams': stream_counts, 'triangles_checked_per_opening': len(triangles),
            'straight_spans_m': spans, 'joints': reports}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('positive', 'mirrored', 'rotated', 'interior-gap'))
    parser.add_argument('initial', type=Path)
    parser.add_argument('result', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.case, args.initial.read_bytes(), args.result.read_bytes())
    except (ValueError, KeyError, IndexError, ZeroDivisionError) as error:
        report = {'passed': False, 'case': args.case, 'failure': str(error)}
    rendered = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end='')
    raise SystemExit(0 if report['passed'] else 1)
