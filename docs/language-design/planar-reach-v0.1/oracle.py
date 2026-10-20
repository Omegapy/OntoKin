"""Independent high-precision expected values for proposed planar reach fixtures.

No OntoKin parser, compiler, simulator, geometry builder or exporter is imported.
The equations and support decisions are stated in OK-LANG-006 before runtime work.
This module is fixture preparation, not a new language implementation.
"""
from decimal import Decimal as D, localcontext
from fractions import Fraction as Q
import math

PI = D('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')
PRECISION = 84
P = float(PI)


def canonical(value):
    return D.from_float(float(value))


def sin(value):
    with localcontext() as context:
        context.prec = PRECISION + 12
        x = value % (2 * PI)
        if x > PI:
            x -= 2 * PI
        term = result = x
        for index in range(1, 220):
            term *= -x * x / ((2 * index) * (2 * index + 1))
            result += term
            if abs(term) < D(10) ** (-PRECISION - 8):
                return +result
        raise ArithmeticError('Independent sine series did not converge')


def cos(value):
    return sin(PI / 2 + value)


def atan(value):
    with localcontext() as context:
        context.prec = PRECISION + 12
        if value < 0:
            return -atan(-value)
        if value > 1:
            return PI / 2 - atan(1 / value)
        # Reduce to |x| <= tan(pi/8), making the alternating series geometric.
        if value > D('0.4'):
            return 2 * atan(value / (1 + (1 + value * value).sqrt()))
        term = result = value
        for index in range(1, 360):
            term *= -value * value
            addition = term / (2 * index + 1)
            result += addition
            if abs(addition) < D(10) ** (-PRECISION - 8):
                return +result
        raise ArithmeticError('Independent arctangent series did not converge')


def atan2(y, x):
    if x > 0:
        return atan(y / x)
    if x < 0:
        return atan(y / x) + (PI if y >= 0 else -PI)
    if y > 0:
        return PI / 2
    if y < 0:
        return -PI / 2
    raise ValueError('Underdetermined atan2(0,0)')


def solve(lengths, target, branch='positive', limits=None):
    """Return specified canonical joint targets or an independently classified failure."""
    left, right = map(float, lengths)
    x, y, z = map(float, target)
    if z != 0:
        return {'status': 'rejected', 'reach_code': 'reach_frame'}
    if not all(.125 <= value <= 4 for value in (left, right)):
        return {'status': 'rejected', 'reach_code': 'reach_domain'}
    if max(abs(x), abs(y)) > 8:
        return {'status': 'rejected', 'reach_code': 'reach_domain'}
    a, b, xx, yy = map(Q.from_float, (left, right, x, y))
    radius2 = xx * xx + yy * yy
    if radius2 < (a - b) ** 2 or radius2 > (a + b) ** 2:
        return {'status': 'rejected', 'reach_code': 'reach_unreachable'}
    if a == b and radius2 == 0:
        return {'status': 'rejected', 'reach_code': 'reach_singular'}
    exact_cos = (radius2 - a * a - b * b) / (2 * a * b)
    with localcontext() as context:
        context.prec = PRECISION
        c = D(exact_cos.numerator) / D(exact_cos.denominator)
        sine = max(D(0), 1 - c * c).sqrt()
        elbow = atan2(sine, c)
        if branch == 'negative':
            elbow = -elbow
        elif branch != 'positive':
            raise ValueError('Unknown fixture branch')
        # sin/cos of the mathematical elbow are exact c and signed sqrt(1-c*c).
        signed_sine = sine if branch == 'positive' else -sine
        shoulder = atan2(canonical(y), canonical(x)) - atan2(canonical(right) * signed_sine,
                                                            canonical(left) + canonical(right) * c)
        while shoulder < -PI:
            shoulder += 2 * PI
        while shoulder >= PI:
            shoulder -= 2 * PI
        pair = [float(shoulder), float(elbow)]
    if pair[0] == P:
        pair[0] = -P
    pair = [0. if value == 0 else value for value in pair]
    limits = limits or [[-P, P], [-P, P]]
    if any(not low <= value <= high for value, (low, high) in zip(pair, limits)):
        return {'status': 'rejected', 'reach_code': 'reach_limit', 'resolved_joint_targets_rad': pair}
    endpoint = pose(lengths, pair)
    residual = math.dist(endpoint['tip_position_base_m'], [x, y, 0.])
    if residual > 1e-9:
        raise ArithmeticError('Independent canonical solution exceeds proposed residual')
    return {'status': 'resolved', 'resolved_joint_targets_rad': pair,
            'tip_position_base_m': endpoint['tip_position_base_m'], 'position_residual_m': residual}


def pose(lengths, angles, rates=(0., 0.), base_translation=(0., 0., 0.), base_angle=0., base_velocity=(0., 0., 0.), root_rate=0.):
    """Independent two-link FK and rigid-root transport from canonical angles/rates."""
    with localcontext() as context:
        context.prec = PRECISION
        a, b = map(canonical, lengths)
        q1, q2 = map(canonical, angles)
        v1, v2 = map(canonical, rates)
        angle = canonical(base_angle)
        c1, s1, c12, s12 = cos(q1), sin(q1), cos(q1 + q2), sin(q1 + q2)
        elbow = [a * c1, a * s1, D(0)]
        tip = [elbow[0] + b * c12, elbow[1] + b * s12, D(0)]
        relative_v = [-a * s1 * v1 - b * s12 * (v1 + v2), a * c1 * v1 + b * c12 * (v1 + v2), D(0)]
        c, s = cos(angle), sin(angle)
        def rotate(vector):
            return [c * vector[0] - s * vector[1], s * vector[0] + c * vector[1], vector[2]]
        transformed = rotate(tip)
        origin, velocity = list(map(canonical, base_translation)), list(map(canonical, base_velocity))
        angular = canonical(root_rate)
        world_v = rotate(relative_v)
        world_v[0] += velocity[0] - angular * transformed[1]
        world_v[1] += velocity[1] + angular * transformed[0]
        world_v[2] += velocity[2]
        half = (angle + q1 + q2) / 2
        output = {'elbow_position_base_m': elbow, 'tip_position_base_m': tip,
                  'elbow_position_world_m': [u + v for u, v in zip(origin, rotate(elbow))],
                  'tip_position_world_m': [u + v for u, v in zip(origin, transformed)],
                  'tip_velocity_world_m_per_s': world_v,
                  'forearm_orientation_wxyz': [cos(half), D(0), D(0), sin(half)],
                  'forearm_omega_world_rad_per_s': [D(0), D(0), angular + v1 + v2]}
        result = {key: [0. if value == 0 else float(value) for value in values] for key, values in output.items()}
        quaternion = result['forearm_orientation_wxyz']
        if next(value for value in quaternion if value != 0) < 0:
            result['forearm_orientation_wxyz'] = [0. if value == 0 else -value for value in quaternion]
        return result


def sample(lengths, target_pair, duration, elapsed, **root):
    elapsed, duration = Q(str(elapsed)), Q.from_float(float(duration))
    if not 0 <= elapsed <= duration:
        raise ValueError('Sample outside active local interval')
    angles = [float(Q.from_float(value) * elapsed / duration) for value in target_pair]
    rates = [float(Q.from_float(value) / duration) for value in target_pair]
    return {'joint_coordinates_rad': angles, 'joint_rates_rad_per_s': rates,
            **pose(lengths, angles, rates, **root)}


if __name__ == '__main__':
    import json
    print(json.dumps(solve([1, 1], [1, 1, 0]), sort_keys=True, indent=2, allow_nan=False))
