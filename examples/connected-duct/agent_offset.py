"""Fit a selected two-bend offset via one guarded Agent/0.11 edit."""
import argparse
import json
from functools import partial
from math import pi
from pathlib import Path
import tempfile

from agent_repair import OPTIONS, write_json
from agent_route import replay as replay_route
from agent_select import placement_patch
from agent_span import span_patch
from fit_placement import compose
from offset_solver import solve
from route_solver import axis_rotation
from ontokin.budget_runtime import execute_framed_loft_export
from ontokin.scene import ExportOptions
from tools.verify_connected_duct import PortFrame, cross, place, require
from tools.verify_inferred_duct_offset import endpoints, joint, obstructions, scene_triangles


def offset_patches(program, mappings, fit, chain, control):
    patches = []
    for index, name in enumerate(chain[1:-1], start=1):
        pose = fit[name]
        if index == 2 and control == 'wrong-plane':
            pose = dict(pose, rotation_wxyz=compose(pose['rotation_wxyz'], axis_rotation((0, 0, 1), -pi/2)))
        patches.append(placement_patch(program, mappings[name], pose))
        if index % 2:
            span = pose['length_m'] - (1 if index == 3 and control == 'interior-gap' else 0)
            patches.append(span_patch(program, mappings[name], span))
    return patches


def preview_boundary(program, fit, chain, policy):
    """Verify the actual trial export before allowing a rounded span to change source."""
    if not any('measured_length_m' in pose for pose in fit.values()):
        return None
    trial = execute_framed_loft_export(program, policy=policy, options=ExportOptions(**OPTIONS))
    if trial.data is None:
        raise ValueError(f'Boundary preview export failed: {trial.report.get("diagnostics", trial.report)}')
    glb, nodes, faces = endpoints(trial.data, chain)
    triangles = list(scene_triangles(glb, nodes))
    spec = json.loads(Path(__file__).with_name('inferred-offset-contract.json').read_bytes())
    for i, (upstream, downstream) in enumerate(zip(chain, chain[1:])):
        pair = [(upstream, 'top'), (downstream, 'bottom')]
        center, normal = faces[pair[0]]
        # The straight's local X follows an edge of its square bore at either end.
        straight = nodes[downstream if i % 2 == 0 else upstream]
        edge = place((1, 0, 0), {**straight, 'translation': (0, 0, 0)})
        frame = PortFrame(center, (normal, edge, cross(normal, edge)))
        row = joint(glb, nodes, faces, pair, center, spec, axes=frame.axes)
        require(row['passed'], f'Boundary preview joint {i+1}: {row.get("failure")}')
        require(not obstructions(triangles, frame, spec['inner_side_m']),
                f'Boundary preview joint {i+1} has an obstructed opening')
    return trial.data


def replay(manifest, output, store, chain, middle_direction=None, control=None):
    if middle_direction is None:
        def measure(raw, *names):
            evaluation = {}
            try:
                return solve(raw, *names, evaluation=evaluation)
            finally:
                write_json(output / 'directions.json', evaluation)
    else:
        measure = partial(solve, middle_direction=middle_direction)
    return replay_route(manifest, output, store, chain, control, solver=measure,
                        build_patches=offset_patches, preview=preview_boundary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--chain', nargs=7, required=True)
    parser.add_argument('--middle-direction', nargs=3, type=float, help='Override the direction inferred from the fixed ports')
    parser.add_argument('--control', choices=('wrong-plane', 'interior-gap', 'rollback'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='duct-offset-') as store:
        summary = replay(args.manifest, args.output, store, args.chain, args.middle_direction, args.control)
    if summary['outcome'] == 'fit-rejected':
        parser.exit(2, summary['reason'] + '\n')
