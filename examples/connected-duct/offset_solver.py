"""Fit two rigid bends and three variable spans between signed GLB port frames."""
from fractions import Fraction
from math import copysign, dist, frexp, hypot, isfinite

from fit_placement import (GLB, TOL, compose, cross, dot, named_frame, require, rotate,
                           select_occurrence, solve_placement, sub, unit)
from route_solver import add, align_turn, check_outlet, quaternion, scale


def solve(raw, *chain, middle_direction=None, evaluation=None):
    """Fit a unique measured direction, or a direction specified by the caller.

    For inference, evaluation receives both candidate decisions, including on refusal.
    """
    require(len(chain) == len(set(chain)) == 7, 'Expected seven distinct duct occurrences')
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
    a, c = start[1], scale(-1, end[1])
    if middle_direction is not None:
        require(len(middle_direction) == 3 and all(isfinite(v) for v in middle_direction),
                'Middle direction must have three finite components')
        return _fit_candidate(raw, chain, glb, nodes, start, end, (a, unit(middle_direction), c))

    report = evaluation if evaluation is not None else {}
    report.update(entry_direction=list(a), exit_direction=list(c), candidates=[],
                  selected_direction=None, reason=None)
    normal = cross(a, c)
    if hypot(*normal) <= TOL:
        report['reason'] = 'Parallel fixed port axes do not determine the middle direction'
        raise ValueError(report['reason'])
    normal = unit(normal)
    fits = []
    for direction in (normal, scale(-1, normal)):
        candidate = {'direction': list(direction), 'feasible': False, 'reason': None}
        report['candidates'].append(candidate)
        try:
            fit = _fit_candidate(raw, chain, glb, nodes, start, end, (a, direction, c), candidate)
        except ValueError as exc:
            candidate['reason'] = str(exc)
        else:
            candidate['feasible'] = True
            fits.append((candidate['direction'], fit))
    if len(fits) != 1:
        report['reason'] = ('No feasible middle direction' if not fits else
                            'Multiple feasible middle directions')
        raise ValueError(report['reason'])
    report['selected_direction'], fit = fits[0]
    return fit


def _rounding_offsets(value):
    """Open offsets from a finite binary32 sample to its rounding midpoints."""
    mantissa, exponent = frexp(abs(value))
    away = 2.0 ** max(exponent - 25, -150) if value else 2.0 ** -150
    toward = max(away / 2, 2.0 ** -150) if mantissa == 0.5 else away
    if not value:
        toward = 0.0
    return (-toward, away) if copysign(1, value) > 0 else (-away, toward)


def _boundary_trial(glb, fixed, measured, axes, dual, gap):
    """Hold rotations and interior lengths fixed. Can the two recorded translations
    round to these same samples if the out-of-range spans take their legal limits?
    """
    trial = [min(100.0, max(0.001, length)) for length in measured]
    changes = sub(trial, measured)
    if max(map(abs, changes)) >= TOL:
        return None
    # A JSON translation alone need not have binary32 precision. Require both
    # actual stationary FLOAT tracks to carry exactly the same components.
    animation, = glb.document['animations']
    ids = glb.objects()
    fixed_ids = {ids[node['name']] for node in fixed}
    checked = set()
    for channel in animation['channels']:
        target = channel['target']
        node_id = target['node']
        if target['path'] != 'translation' or node_id not in fixed_ids:
            continue
        index = channel['sampler']
        if node_id in checked or type(index) is not int or not 0 <= index < len(animation['samplers']):
            return None
        output = animation['samplers'][index]['output']
        accessor = glb.reference('accessors', output)
        if (accessor['componentType'], accessor['type']) != (5126, 'VEC3'):
            return None
        translation = tuple(glb.reference('nodes', node_id)['translation'])
        if any(sample != translation for sample in glb.accessor(output)):
            return None
        checked.add(node_id)
    if checked != fixed_ids:
        return None

    # Evaluate the trial against the measured equation directly. A tiny
    # inverse-solve residual must not disappear beside a large span at a tie.
    delta = [sum(Fraction(length) * Fraction(component)
                 for length, component in zip(trial, column)) - Fraction(distance)
             for column, distance in zip(zip(*axes), gap)]
    intervals = []
    for start, end in zip(fixed[0]['translation'], fixed[1]['translation']):
        start_lo, start_hi = _rounding_offsets(start)
        end_lo, end_hi = _rounding_offsets(end)
        intervals.append((end_lo - start_hi, end_hi - start_lo))
    # Exclude ties conservatively. Zero needs no movement at either endpoint.
    if any(d != 0 and not lo < d < hi for d, (lo, hi) in zip(delta, intervals)):
        return None
    # Coarse samples or nearly dependent axes can make an endpoint's rounding
    # cell uninformative about a span. Use TOL only to *refuse* poor resolution.
    radii = [max(-lo, hi) for lo, hi in intervals]
    span_uncertainty = [dot(tuple(map(abs, row)), radii) for row in dual]
    if max(span_uncertainty) >= TOL or hypot(*radii) >= TOL:
        return None
    return dict(trial_lengths_m=trial, required_endpoint_delta_m=list(map(float, delta)),
                open_delta_intervals_m=intervals, span_uncertainty_m=span_uncertainty)


def _fit_candidate(raw, chain, glb, nodes, start, end, axes, candidate=None):
    a, b, c = axes
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
    normals = (cross(b, c), cross(c, a), cross(a, b))
    measured = [dot(gap, normal)/determinant for normal in normals]
    lengths = measured
    if candidate is not None:
        candidate['lengths_m'] = measured
    if not all(0.001 <= length <= 100 for length in measured):
        dual = [scale(1 / determinant, normal) for normal in normals]
        trial = _boundary_trial(glb, (nodes[0], nodes[-1]), measured, axes, dual, gap)
        require(trial is not None, 'Straight spans must be within [0.001, 100] m: ' +
                ', '.join(f'{x:.9g}' for x in measured))
        lengths = trial['trial_lengths_m']
        if candidate is not None:
            candidate['boundary_trial'] = trial
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
        if lengths[index] != measured[index]:
            pose['measured_length_m'] = measured[index]
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
        target_center = cursor if index < len(turns) else end[0]
        check_outlet(nodes[straight], named_frame(glb, nodes[straight], 'bottom'),
                     named_frame(glb, nodes[straight], 'top'), pose, target, target_center, correction)
        if index < len(turns):
            previous_origin, desired_origin, previous_rotation = target[0], cursor, correction
            cursor = add(cursor, offset)
    return fit
