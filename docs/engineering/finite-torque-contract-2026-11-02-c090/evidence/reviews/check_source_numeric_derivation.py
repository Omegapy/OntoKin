#!/usr/bin/env python3
"""Independent contract arithmetic; no OntoKin import or candidate output."""
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import itertools
import json
import math
import platform
import struct
import sys

COUNT = 0
GROUPS = {}


def check(condition, group, explanation):
    global COUNT
    COUNT += 1
    GROUPS[group] = GROUPS.get(group, 0) + 1
    if not condition:
        raise AssertionError(f"{group}: {explanation}")


def rn(value):
    result = float(value)
    if not math.isfinite(result):
        raise OverflowError("This checker only admits finite rounding.")
    return Q(result) if result else Q(0)


def envelope(value):
    return abs(value) / 2**53 + Q(1, 2**1075)


def polynomial(w, a, d):
    return w*d + a*d*d/2


def exact_maximum(w, a, left, right):
    candidates = [left, right]
    if a:
        vertex = -w/a
        if left <= vertex <= right:
            candidates.append(vertex)
    return max(abs(polynomial(w, a, t)) for t in candidates)


# Tie-to-even underflow leaves canonical legacy rotation unchanged, but not
# the independent physical reference. All operands remain within 32768 bits.
tau = Q(1, 2**1074)
inertia = Q(2)
ar = tau/inertia
ac = rn(rn(tau)/inertia)
d = Q(2**537)
check(rn(tau) == tau, 'underflow', 'Minimum subnormal is exactly admitted.')
check(ar == Q(1, 2**1075), 'underflow', 'Ideal acceleration is not zero.')
check(ac == 0, 'underflow', 'Half-minimum tie rounds to even zero.')
check(polynomial(Q(0), ac, d) == 0, 'underflow', 'Canonical legacy phase remains zero.')
check(polynomial(Q(0), ar, d) == Q(1, 4), 'underflow', 'Reference phase is exactly one quarter radian.')
check(ar*d == Q(1, 2**538), 'underflow', 'Reference speed is retained.')
check(max(x.numerator.bit_length() + x.denominator.bit_length() for x in [tau, ar, d, d*d]) < 32768,
      'underflow', 'No operand-width exclusion hides the witness.')

# Stale canonical anchor: integrate the reference directly from its initial
# origin, then compare with the error-origin recurrence at its newer clock.
e = Q(1, 3)
u = Q(2, 3)
p_c = polynomial(Q(0), Q(2), Q(1))
p_ref = polynomial(Q(0), Q(2), e) + polynomial(2*e, Q(1), u)
check(p_c == 1 and p_ref == Q(7, 9), 'stale_origin', 'Direct integral has the expected exact phases.')
check(abs(p_c-p_ref) == Q(2, 9), 'stale_origin', 'Discrepancy is two ninths.')
check(abs(Q(2)-1)*u*u/2 == abs(p_c-p_ref), 'stale_origin', 'New-origin recurrence encloses the direct integral.')

# Independently accumulate signed physical reference phase and speed through
# changing reference accelerations while the canonical anchor stays at zero.
# The bounds are compared with direct exact integrals, not with themselves.
widths = (Q(1, 4), Q(1, 2), Q(3, 4))
for ac, w0, alphas in itertools.product((Q(-2), Q(0), Q(3)), (Q(-1), Q(2)), itertools.product((Q(-3), Q(0), Q(4)), repeat=3)):
    time = Q(0)
    wr = w0
    phase_ref = Q(0)
    etheta = Q(0)
    eomega = Q(0)
    for width, ar in zip(widths, alphas):
        phase_ref += polynomial(wr, ar, width)
        wr += ar*width
        etheta += eomega*width + abs(ac-ar)*width*width/2
        eomega += abs(ac-ar)*width
        time += width
        check(abs(polynomial(w0, ac, time)-phase_ref) <= etheta,
              'piecewise_reference', 'Angle recurrence covers independently integrated history.')
        check(abs(w0+ac*time-wr) <= eomega,
              'piecewise_reference', 'Speed recurrence covers independently integrated history.')

# Actual canonical reanchors carry actual scalar rounding deltas. Subsequent
# exact integration can be compared directly with the unsplit ideal history.
for w0, ac, d1, d2 in itertools.product((Q(1, 10), Q(-7, 10)), (Q(3, 10), Q(-11, 10)), (Q(1, 3), Q(2, 7)), (Q(1, 5), Q(5, 6))):
    w0 = rn(w0)
    ac = rn(ac)
    old_phase = polynomial(w0, ac, d1)
    old_speed = w0+ac*d1
    phase_anchor = rn(old_phase)
    speed_anchor = rn(old_speed)
    etheta = abs(phase_anchor-old_phase)
    eomega = abs(speed_anchor-old_speed)
    canonical_phase = phase_anchor + polynomial(speed_anchor, ac, d2)
    reference_phase = polynomial(w0, ac, d1+d2)
    check(abs(canonical_phase-reference_phase) <= etheta+eomega*d2,
          'reanchor_transfer', 'Actual phase/speed rounding is carried across the anchor.')
    check(abs(speed_anchor+ac*d2-(w0+ac*(d1+d2))) <= eomega,
          'reanchor_transfer', 'Canonical reanchor cannot reset speed discrepancy.')

# This is an exact extremum witness: both endpoints are zero yet the interior
# exceeds the phase limit. Endpoint-only range checking would accept it.
w = Q(2**22)
a = Q(-2**23)
check(polynomial(w, a, Q(0)) == 0 and polynomial(w, a, Q(1)) == 0,
      'phase_domain', 'Equal endpoints do not bound the interior phase.')
check(exact_maximum(w, a, Q(0), Q(1)) == 2**20,
      'phase_domain', 'Equality at the exact vertex is admitted.')
check(exact_maximum(2*w, 2*a, Q(0), Q(1)) == 2**21,
      'phase_domain', 'Scaled reversal exceeds the bound despite zero endpoints.')
check(exact_maximum(2*w, 2*a, Q(0), Q(1, 16)) < 2**20,
      'phase_domain', 'A short prefix still passes.')
check(polynomial(Q(0), Q(1), Q(2**11)) == 2**21,
      'phase_domain', 'Before-request diagnostic witness exceeds the domain.')

# The uniform RN allowance covers normal values, subnormal boundaries and
# arbitrary rational endpoints/vertices without an unchecked float product.
values = [Q(0), Q(1, 2**1075), Q(3, 2**1075), Q(1, 2**1022), Q(1, 3), Q(2**20), Q(-2**20)]
values += [Q(sign*n, den) * Q(2)**scale for sign, n, den, scale in itertools.product((-1, 1), (1, 7, 53), (3, 5, 127), (-1074, -1022, -53, 0, 20))]
for value in values:
    check(abs(rn(value)-value) <= envelope(value), 'uniform_rounding', 'Whole-phase RN allowance encloses actual scalar error.')

# The full vector bound is essential when legacy transfer uncertainty has
# orthogonal components, even though the admitted canonical center is axial.
for uncertainty in ((Q(1, 5), Q(0), Q(0)), (Q(1, 5), Q(-2, 7), Q(1, 11))):
    l1 = sum(map(abs, uncertainty), Q(0))
    norm_squared = sum((x*x for x in uncertainty), Q(0))
    check(norm_squared <= l1*l1, 'vector_uncertainty', 'L1 encloses full angular-velocity uncertainty.')
    check(l1 > abs(uncertainty[2]), 'vector_uncertainty', 'Selected-axis projection would discard uncertainty.')

# Mechanical work uses the unwrapped scalar phase. A multiple of a full
# turn may have zero orientation distance, which cannot establish zero work.
check(Q(3)*Q(10) == 30, 'work_phase', 'Exact signed phase work retains the full unwrapped increment.')

result = {
    'schema_version': 'ontokin.independent-source-numeric-design-check/1',
    'outcome': 'passed',
    'assertions': COUNT,
    'groups': GROUPS,
    'runtime_imports': False,
    'candidate_output_used': False,
    'checks_only': 'Independent exact arithmetic and mathematical contract witnesses; no torque runtime, parser, kernel or artifact execution.',
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'python': sys.version,
    'platform': platform.platform(),
    'underflow_witness': {'tau': '2^-1074', 'inertia': '2', 'alpha_c': '0', 'alpha_ref': '2^-1075', 'time': '2^537', 'reference_phase': '1/4'},
}
print(json.dumps(result, indent=2, sort_keys=True))
