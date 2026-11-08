"""Fit a selected two-bend offset via one guarded Agent/0.11 edit."""
import argparse
from functools import partial
from math import pi
from pathlib import Path
import tempfile

from agent_route import replay as replay_route
from agent_select import placement_patch
from agent_span import span_patch
from fit_placement import compose
from offset_solver import solve
from route_solver import axis_rotation


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


def replay(manifest, output, store, chain, middle_direction, control=None):
    return replay_route(manifest, output, store, chain, control, solver=partial(solve, middle_direction=middle_direction),
                        build_patches=offset_patches)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--chain', nargs=7, required=True)
    parser.add_argument('--middle-direction', nargs=3, required=True, type=float)
    parser.add_argument('--control', choices=('wrong-plane', 'interior-gap', 'rollback'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='duct-offset-') as store:
        summary = replay(args.manifest, args.output, store, args.chain, args.middle_direction, args.control)
    if summary['outcome'] == 'fit-rejected':
        parser.exit(2, summary['reason'] + '\n')
