"""Fit two rigid bends and three variable spans between signed GLB port frames."""
from math import dist, isfinite

from fit_placement import (GLB, TOL, compose, cross, dot, named_frame, require, rotate,
                           select_occurrence, solve_placement, sub, unit)
from route_solver import add, align_turn, check_outlet, quaternion, scale


def solve(raw, *chain, middle_direction):
    require(len(chain) == len(set(chain)) == 7, 'Expected seven distinct duct occurrences')
    require(len(middle_direction) == 3 and all(isfinite(v) for v in middle_direction),
            'Middle direction must have three finite components')
    middle = unit(middle_direction)
    glb = GLB(raw, target='ontokin.glb/0.11')
    paths = glb.objects()
    occurrences = glb.document['extras']['ontokin']['program']['occurrences']
    roles = ('elbow', 'straight', 'elbow', 'straight', 'elbow', 'straight', 'elbow')
    nodes = [glb.reference('nodes', select_occurrence(paths, occurrences, name, role))
             for name, role in zip(chain, roles)]
    require(all('matrix' not in n and n.get('scale', [1, 1, 1]) == [1, 1, 1] for n in nodes),
            'Expected rigid unit-scale nodes')
    start = named_frame(glb, nodes[0], 'top')
    end = named_frame(glb, nodes[-1], 'bottom')
    a, b, c = start[1], middle, scale(-1, end[1])
    axes = (a, b, c)
    gap = sub(end[0], start[0])
    turns = []
    for index, upstream in enumerate((2, 4)):
        inlet = named_frame(glb, nodes[upstream], 'bottom')
        outlet = named_frame(glb, nodes[upstream], 'top')
        rotation = align_turn(scale(-1, inlet[1]), outlet[1], axes[index], axes[index+1])
        offset = rotate(rotation, sub(outlet[0], inlet[0]))
        gap = sub(gap, offset)
        turns.append((inlet, rotation, offset))
    determinant = dot(a, cross(b, c))
    require(abs(determinant) > TOL, 'The three span axes must be linearly independent')
    lengths = [dot(gap, normal)/determinant for normal in (cross(b, c), cross(c, a), cross(a, b))]
    require(all(0.001 <= length <= 100 for length in lengths),
            'Straight spans must be within [0.001, 100] m: ' + ', '.join(f'{x:.9g}' for x in lengths))
    fit = {}
    cursor = start[0]
    previous_origin, desired_origin, previous_rotation = cursor, cursor, (1, 0, 0, 0)
    for index, straight in enumerate((1, 3, 5)):
        # Fit the inlet in its upstream occurrence's original frame, then move both together.
        aligned = solve_placement(raw, elbow=chain[straight-1], straight=chain[straight])
        pose = {'translation_m': list(add(desired_origin, rotate(previous_rotation,
                    sub(aligned['translation_m'], previous_origin)))),
                'rotation_wxyz': list(compose(previous_rotation, aligned['rotation_wxyz'])),
                'length_m': lengths[index]}
        fit[chain[straight]] = pose
        cursor = add(cursor, scale(lengths[index], axes[index]))
        target, correction = end, (1, 0, 0, 0)
        if index < len(turns):
            target, correction, offset = turns[index]
            bend = nodes[straight+1]
            fit[chain[straight+1]] = {
                'translation_m': list(add(cursor, rotate(correction, sub(bend['translation'], target[0])))),
                'rotation_wxyz': list(compose(correction, quaternion(bend)))}
        else:
            require(dist(cursor, end[0]) <= TOL, 'Route does not reach sink')
        check_outlet(nodes[straight], named_frame(glb, nodes[straight], 'bottom'),
                     named_frame(glb, nodes[straight], 'top'), pose, target, cursor, correction)
        if index < len(turns):
            previous_origin, desired_origin, previous_rotation = target[0], cursor, correction
            cursor = add(cursor, offset)
    return fit
