"""Size and place a variable-length straight between two named, stationary GLB ports."""
from math import dist, isfinite

from fit_placement import (GLB, TOL, SelectionError, compose, dot, named_frame, require,
                           rotate, select_occurrence, solve_placement, sub)


def solve(glb_bytes, source_name, source_region, sink_name, sink_region, moving_name, moving_bottom, moving_top):
    """Return the absolute inlet pose and positive axial span, in metres and wxyz order."""
    if (source_region, moving_bottom, moving_top, sink_region) != ('top', 'bottom', 'top', 'bottom'):
        raise SelectionError('Expected upstream/top, straight/bottom, straight/top and downstream/bottom')
    if len({source_name, moving_name, sink_name}) != 3:
        raise SelectionError('Expected three distinct occurrences')

    # The one-ended fit authenticates the occurrence inventory and stationary tracks,
    # then aligns both inlet rims. Its square-rim roll is unique modulo quarter turns.
    pose = solve_placement(glb_bytes, elbow=source_name, straight=moving_name)
    glb = GLB(glb_bytes, target='ontokin.glb/0.11')
    paths = glb.objects()
    occurrences = glb.document['extras']['ontokin']['program']['occurrences']
    sink_index = select_occurrence(paths, occurrences, sink_name, 'elbow')
    upstream = glb.reference('nodes', paths[source_name])
    downstream = glb.reference('nodes', sink_index)
    straight = glb.reference('nodes', paths[moving_name])
    for node in (upstream, downstream, straight):
        require('matrix' not in node and node.get('scale', [1, 1, 1]) == [1, 1, 1], 'Expected rigid unit scale')
    start, axis, _, _ = named_frame(glb, upstream, source_region)
    end, normal, outer, inner = named_frame(glb, downstream, sink_region)
    length = dot(sub(end, start), axis)
    require(isfinite(length) and length > 0, 'Straight span must be positive')
    center = tuple(a + length*b for a, b in zip(start, axis))
    require(dist(center, end) <= TOL, 'Downstream center has lateral offset')
    require(dist(axis, tuple(-v for v in normal)) <= TOL, 'Downstream normal does not face upstream')

    top, top_normal, old_outer, old_inner = named_frame(glb, straight, moving_top)
    bottom, _, _, _ = named_frame(glb, straight, moving_bottom)
    x, y, z, w = straight['rotation']
    old_axis = rotate((w, x, y, z), (0, 0, 1))
    old_length = dot(sub(top, bottom), old_axis)
    require(old_length > 0 and dist(bottom, straight['translation']) <= TOL and
            dist(sub(top, bottom), tuple(old_length*v for v in old_axis)) <= TOL,
            'Straight must extend from its origin along local +Z')
    correction = compose(pose['rotation_wxyz'], (w, -x, -y, -z))
    fitted_axis = rotate(pose['rotation_wxyz'], (0, 0, 1))
    require(dist(rotate(correction, top_normal), tuple(-v for v in normal)) <= TOL,
            'Straight outlet normal does not mate')
    # Resizing translates the outlet section along its local +Z. Preserve its actual
    # corner offsets so angular mismatch and different bore dimensions remain visible.
    for initial, target in ((old_outer, outer), (old_inner, inner)):
        for point in initial:
            offset = rotate(correction, sub(point, top))
            predicted = tuple(a + length*b + c for a, b, c in zip(pose['translation_m'], fitted_axis, offset))
            require(min(dist(predicted, corner) for corner in target) <= TOL, 'Downstream rim does not mate')
    return {**pose, 'length_m': length}
