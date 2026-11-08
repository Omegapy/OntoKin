"""Fit a rigid quarter-turn and two resizable straights between signed GLB ports."""
from math import atan2, cos, dist, hypot, sin

from fit_placement import (GLB, TOL, compose, cross, dot, named_frame, require, rotate,
                           select_occurrence, solve_placement, sub, unit)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(k, v):
    return tuple(k*x for x in v)


def quaternion(node):
    x, y, z, w = node['rotation']
    return w, x, y, z


def axis_rotation(axis, angle):
    return (cos(angle/2), *scale(sin(angle/2), axis))


def align_turn(inlet, outlet, first, second):
    """Map both measured flow directions, including the antiparallel inlet case."""
    require(abs(dot(inlet, outlet)) <= TOL and abs(dot(first, second)) <= TOL,
            'Both the elbow and the fixed port axes must form a right angle')
    axis = cross(inlet, first)
    angle = atan2(hypot(*axis), dot(inlet, first))
    swing = axis_rotation(unit(axis) if hypot(*axis) > 1e-12 else unit(cross(inlet, outlet)), angle)
    aligned = rotate(swing, outlet)
    twist = atan2(dot(first, cross(aligned, second)), dot(aligned, second))
    result = compose(axis_rotation(first, twist), swing)
    require(dist(rotate(result, inlet), first) <= TOL and dist(rotate(result, outlet), second) <= TOL,
            'Rigid elbow cannot align both port directions')
    return result


def check_outlet(node, bottom, top, pose, target, target_center, target_rotation):
    """Changing span moves the outlet along local +Z and preserves both measured rims."""
    center, normal, outer, inner = top
    old = quaternion(node)
    axis = rotate(old, (0, 0, 1))
    offset = sub(center, bottom[0])
    require(dist(bottom[0], node['translation']) <= TOL and dot(offset, axis) > 0 and
            dist(offset, scale(dot(offset, axis), axis)) <= TOL,
            'Straight must extend from its origin along local +Z')
    delta = compose(pose['rotation_wxyz'], (old[0], *scale(-1, old[1:])))
    fitted_center = add(pose['translation_m'], scale(pose['length_m'], rotate(delta, axis)))
    require(dist(fitted_center, target_center) <= TOL, 'Straight outlet center does not mate')
    require(dist(rotate(delta, normal), scale(-1, rotate(target_rotation, target[1]))) <= TOL,
            'Straight outlet normal does not mate')
    for ring, other in zip((outer, inner), target[2:]):
        corners = [add(target_center, rotate(target_rotation, sub(p, target[0]))) for p in other]
        for point in ring:
            predicted = add(fitted_center, rotate(delta, sub(point, center)))
            require(min(dist(predicted, p) for p in corners) <= TOL, 'Straight outlet rim does not mate')


def solve(raw, source_name, first_name, bend_name, second_name, sink_name):
    """Return absolute translation, wxyz rotation, and straight spans for the ordered chain."""
    names = (source_name, first_name, bend_name, second_name, sink_name)
    require(len(set(names)) == 5, 'Expected five distinct duct occurrences')
    # Both inlet fits also verify stationary transforms and the named occurrence inventory.
    lead = solve_placement(raw, elbow=source_name, straight=first_name)
    tail = solve_placement(raw, elbow=bend_name, straight=second_name)
    glb = GLB(raw, target='ontokin.glb/0.11')
    paths = glb.objects()
    occurrences = glb.document['extras']['ontokin']['program']['occurrences']
    nodes = [glb.reference('nodes', select_occurrence(paths, occurrences, name, role)) for name, role in
             zip(names, ('elbow', 'straight', 'elbow', 'straight', 'elbow'))]
    require(all('matrix' not in n and n.get('scale', [1, 1, 1]) == [1, 1, 1] for n in nodes),
            'Expected rigid unit-scale nodes')
    source, first, bend, second, sink = nodes
    start = named_frame(glb, source, 'top')
    end = named_frame(glb, sink, 'bottom')
    inlet = named_frame(glb, bend, 'bottom')
    outlet = named_frame(glb, bend, 'top')
    a, b = start[1], scale(-1, end[1])
    correction = align_turn(scale(-1, inlet[1]), outlet[1], a, b)
    elbow_offset = rotate(correction, sub(outlet[0], inlet[0]))
    gap = sub(sub(end[0], start[0]), elbow_offset)
    # Solve the two-axis linear system using the actual (rounded) exported directions.
    ab = dot(a, b)
    first_length = (dot(gap, a) - ab*dot(gap, b))/(1 - ab*ab)
    second_length = dot(gap, b) - ab*first_length
    residual = dist(gap, add(scale(first_length, a), scale(second_length, b)))
    require(residual <= TOL, f'Fixed port axes are skew: lateral separation {residual:.9g} m')
    require(min(first_length, second_length) > 0, 'Both straight runs must have positive length')
    bend_inlet = add(start[0], scale(first_length, a))

    def move_with_bend(point):
        return list(add(bend_inlet, rotate(correction, sub(point, inlet[0]))))

    turn = {'translation_m': move_with_bend(bend['translation']),
            'rotation_wxyz': list(compose(correction, quaternion(bend)))}
    lead['length_m'] = first_length
    tail = {'translation_m': move_with_bend(tail['translation_m']),
            'rotation_wxyz': list(compose(correction, tail['rotation_wxyz'])), 'length_m': second_length}
    check_outlet(first, named_frame(glb, first, 'bottom'), named_frame(glb, first, 'top'), lead, inlet, bend_inlet, correction)
    check_outlet(second, named_frame(glb, second, 'bottom'), named_frame(glb, second, 'top'), tail, end, end[0], (1, 0, 0, 0))
    return {first_name: lead, bend_name: turn, second_name: tail}
