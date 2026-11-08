"""Score the four frozen C166 joints independently of the router and Agent edits."""
import argparse
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .verify_duct_placement import endpoints, require
    from .verify_duct_span import joint
else:
    from verify_duct_placement import endpoints, require
    from verify_duct_span import joint

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/connected-duct'
NAMES = ('outbound', 'lead', 'turn', 'tail', 'inbound')


def verify(before, after):
    spec = json.loads((EXAMPLE / 'route-contract.json').read_text())
    reference = json.loads((EXAMPLE / 'span-contract.json').read_text())
    for key in ('inner_side_m', 'outer_side_m'):
        spec[key] = reference[key]
    original, initial_nodes, _ = endpoints(before, NAMES)
    glb, nodes, faces = endpoints(after, NAMES)
    for name in ('outbound', 'inbound'):
        require(all(initial_nodes[name][k] == nodes[name][k] for k in ('rotation', 'translation')), name + ' moved')
    for name in NAMES:
        require(not any(k in nodes[name] for k in ('scale', 'matrix', 'children', 'skin', 'weights')), name + ' unsupported transform')
    # Local mesh coordinates of both anchors and of the purchased rigid elbow must persist.
    keep = lambda glb: {k: v for k, v in glb.geometry_streams().items() if k[0] in ('outbound', 'turn', 'inbound')}
    require(keep(original) == keep(glb), 'Stationary or rigid elbow geometry changed')
    joints = []
    for names, center, flow in zip(spec['joints'], spec['joint_centers_m'], spec['flow_axes']):
        pair = [item.split('/') for item in names]
        axes = (flow, (0, 1, 0), (-flow[2], 0, flow[0]))
        measured = joint(glb, nodes, faces, pair, center, spec, axes=axes)
        measured['observed_centers_m'] = [faces[tuple(p)][0] for p in pair]
        measured['observed_normals'] = [faces[tuple(p)][1] for p in pair]
        joints.append(measured)
    spans = [math.dist(faces[name, 'top'][0], faces[name, 'bottom'][0]) for name in ('lead', 'tail')]
    return {'passed': all(r['passed'] for r in joints) and all(abs(a-b) <= spec['maximum_rim_error_m'] for a,b in zip(spans, spec['straight_spans_m'])),
            'glb_sha256': hashlib.sha256(after).hexdigest(), 'straight_spans_m': spans, 'joints': joints}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('initial', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--expect', choices=['fit', 'wrong-turn', 'one-sided'], default='fit')
    args = parser.parse_args()
    result = verify(args.initial.read_bytes(), args.candidate.read_bytes())
    print(json.dumps(result, indent=2, allow_nan=False))
    masks = {'fit': [True]*4, 'wrong-turn': [True, True, False, True], 'one-sided': [True, True, True, False]}
    require([r['passed'] for r in result['joints']] == masks[args.expect] and result['passed'] == (args.expect == 'fit'), 'Unexpected joint result')
    if args.expect == 'one-sided':
        require(abs(result['joints'][3]['center_distance_m'] - 1) <= 1e-5, 'Unexpected terminal gap')
