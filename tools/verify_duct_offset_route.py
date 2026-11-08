"""Measure the six C167 signed port joints from an independently decoded GLB."""
import argparse
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_connected_duct import cross
    from .verify_duct_route import EXAMPLE, endpoints, joint, require
else:
    from verify_connected_duct import cross
    from verify_duct_route import EXAMPLE, endpoints, joint, require


MASKS = {'fit': [True] * 6,
         'wrong-plane': [True, True, False, True, True, True],
         'interior-gap': [True, True, True, False, True, True]}


def axes_for(flow):
    transverse = (0, 1, 0) if not flow[1] else (0, 0, 1)
    return flow, transverse, cross(flow, transverse)


def verify(before, after):
    spec = json.loads((EXAMPLE / 'offset-contract.json').read_text())
    spec.update(inner_side_m=1.0, outer_side_m=2.0)
    original, originals, _ = endpoints(before, spec['chain'])
    glb, nodes, faces = endpoints(after, spec['chain'])
    fixed = ('outbound', 'inbound')
    for name in fixed:
        require(all(nodes[name][k] == originals[name][k] for k in ('translation', 'rotation')), name + ' moved')
    for name, node in nodes.items():
        require(not any(k in node for k in ('scale', 'matrix', 'children', 'skin', 'weights')), name + ' unsupported transform')
    initial, candidate = original.geometry_streams(), glb.geometry_streams()
    streams = {}
    for name in (*fixed, 'turn', 'rise'):
        keys = {(name, region, role) for region in ('top', 'bottom', 'inner', 'outer')
                for role in ('POSITION', 'NORMAL', 'indices')}
        require({k for k in candidate if k[0] == name} == keys == {k for k in initial if k[0] == name}, name + ' stream inventory differs')
        require(all(initial[k] == candidate[k] for k in keys), name + ' local geometry differs')
        streams[name] = len(keys)
    joints = []
    for names, center, flow in zip(spec['joints'], spec['joint_centers_m'], spec['flow_axes'], strict=True):
        pair = [item.split('/') for item in names]
        row = joint(glb, nodes, faces, pair, center, spec, axes=axes_for(flow))
        row['observed_centers_m'] = [faces[tuple(p)][0] for p in pair]
        row['observed_normals'] = [faces[tuple(p)][1] for p in pair]
        joints.append(row)
    spans = {n: math.dist(faces[n, 'top'][0], faces[n, 'bottom'][0]) for n in ('lead', 'bridge', 'tail')}
    spans_fit = all(abs(a-b) <= spec['maximum_rim_error_m'] for a,b in zip(spans.values(), spec['straight_spans_m'], strict=True))
    return {'passed': all(r['passed'] for r in joints) and spans_fit, 'glb_sha256': hashlib.sha256(after).hexdigest(),
            'fixed_poses_unchanged': list(fixed), 'identical_local_streams': streams, 'straight_spans_m': spans, 'joints': joints}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('initial', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--expect', choices=MASKS, default='fit')
    args = parser.parse_args()
    result = verify(args.initial.read_bytes(), args.candidate.read_bytes())
    print(json.dumps(result, indent=2, allow_nan=False))
    rows = result['joints']
    require([r['passed'] for r in rows] == MASKS[args.expect] and result['passed'] == (args.expect == 'fit'), 'Unexpected fit verdict')
    if args.expect == 'wrong-plane':
        require(math.dist(rows[2]['observed_normals'][0], (1, 0, 0)) <= 1e-5, 'Wrong-plane control did not travel along +X')
    if args.expect == 'interior-gap':
        require(abs(rows[3]['center_distance_m'] - 1) <= 1e-5, 'Expected a 1 m gap at joint 4')
