"""Independent exact arithmetic for canonical angular zero proofs.

This module evaluates the documented homogeneous projective operations from
source operands. It imports no producer pose implementation or runtime state.
The 96-bit nearest-even grid and final binary64 exposure are actual arithmetic
steps, not a tolerance or an uncertainty midpoint.
"""
from fractions import Fraction as F
from math import factorial, isqrt
import struct

from .reach_reference import ReferenceError

GRID = 1 << 96
PRECISIONS = (96, 192, 384, 768, 1536)
ARGUMENT_ERROR = F(1, 1 << 86)


def nearest_grid(value, a, *, bits=96):
    a.tick()
    value = F(value)
    a.guard(value)
    if abs(value.numerator).bit_length() + bits + 1 > a.operand_limit:
        raise ReferenceError("resource", "Independent angular grid numerator exceeds operand domain")
    denominator = 1 << bits
    numerator = value.numerator << bits
    quotient, remainder = divmod(numerator, value.denominator)
    quotient += 2*remainder > value.denominator or (2*remainder == value.denominator and quotient % 2)
    result = F(quotient, denominator)
    a.guard(result)
    return result


def rotation(values, a):
    a.tick()
    values = tuple(F(value) for value in values)
    a.guard(*values)
    maximum = max(map(abs, values))
    if not maximum:
        raise ReferenceError("numeric", "Independent canonical angular rotation is zero")
    exponent = maximum.numerator.bit_length() - maximum.denominator.bit_length()
    if max(maximum.numerator.bit_length() + max(-exponent, 0),
           maximum.denominator.bit_length() + max(exponent, 0)) + 2 > a.operand_limit:
        raise ReferenceError("resource", "Independent angular rescale exceeds operand domain")
    if maximum < (F(1 << exponent) if exponent >= 0 else F(1, 1 << -exponent)):
        exponent -= 1
    shift = -exponent - 1
    if abs(shift) + 2 > a.operand_limit:
        raise ReferenceError("resource", "Independent angular scale exceeds operand domain")
    scale = F(1 << shift) if shift >= 0 else F(1, 1 << -shift)
    result = tuple(nearest_grid(a.exact(value, scale, "mul"), a) for value in values)
    if next(value for value in result if value) < 0:
        result = tuple(-value for value in result)
    return result


def product(left, right, a):
    mul, add = lambda x, y: a.exact(x, y, "mul"), a.exact_sum
    w, x, y, z = left
    r, s, t, u = right
    return rotation((add(mul(w,r),-mul(x,s),-mul(y,t),-mul(z,u)),
                     add(mul(w,s),mul(x,r),mul(y,u),-mul(z,t)),
                     add(mul(w,t),-mul(x,u),mul(y,r),mul(z,s)),
                     add(mul(w,u),mul(x,t),-mul(y,s),mul(z,r))), a)


def rotated(q, values, a):
    mul = lambda x,y:a.exact(x,y,"mul")
    sub = lambda x,y:a.exact(x,y,"sub")
    div = lambda x,y:a.exact(x,y,"div")
    add = a.exact_sum
    a.tick()
    values = tuple(F(value) for value in values)
    a.guard(*q, *values)
    w,x,y,z = q
    squares = tuple(mul(value,value) for value in q)
    denominator = add(*squares)
    diagonal = lambda i,j: sub(denominator, mul(2,add(squares[i],squares[j])))
    pair = lambda first,second,third,fourth,sign: mul(2,a.exact(mul(first,second),mul(third,fourth),sign))
    rows = ((diagonal(2,3), pair(x,y,w,z,"sub"), pair(x,z,w,y,"add")),
            (pair(x,y,w,z,"add"), diagonal(1,3), pair(y,z,w,x,"sub")),
            (pair(x,z,w,y,"sub"), pair(y,z,w,x,"add"), diagonal(1,2)))
    return tuple(nearest_grid(div(add(*(mul(coefficient,value) for coefficient,value in zip(row,values))),
                                         denominator),a) for row in rows)


def cross(left, right, a):
    return tuple(a.exact(a.exact(left[j], right[k], "mul"),
                         a.exact(left[k], right[j], "mul"), "sub")
                 for j,k in ((1,2),(2,0),(0,1)))


def exposed_vector(values, a):
    return tuple(F(a.round64(value)) for value in values)


def sqrt_binary64(value, a):
    """Nearest-even sqrt in [0,1], proved by exact binary64 midpoints."""
    a.tick()
    value = F(value)
    a.guard(value)
    if not 0 <= value <= 1:
        raise ReferenceError("numeric", "Independent unit projection has an invalid squared component")
    if value in (0, 1):
        return value
    low, high = 0, 0x3FF0000000000000
    decode = lambda bits: F(struct.unpack("<d", struct.pack("<Q", bits))[0])
    while high - low > 1:
        a.tick()
        middle = (low + high) // 2
        scalar = decode(middle)
        if a.exact(scalar, scalar, "mul") <= value:
            low = middle
        else:
            high = middle
    left, right = decode(low), decode(high)
    if a.exact(left,left,"mul") == value:
        return left
    middle = a.exact(a.exact(left,right,"add"),2,"div")
    square = a.exact(middle,middle,"mul")
    return right if value > square or value == square and low % 2 else left


def materialized(q, a):
    squares = tuple(a.exact(value,value,"mul") for value in q)
    norm = a.exact_sum(*squares)
    return tuple((-1 if value < 0 else 1)*sqrt_binary64(a.exact(square,norm,"div"),a)
                 for value,square in zip(q,squares))


def sqrt_bounds(value, precision, a):
    """Outward dyadic square-root enclosure with prospective integer guards."""
    a.tick()
    value = F(value)
    a.guard(value)
    if value < 0:
        raise ReferenceError("numeric", "Independent angular square root is negative")
    if value.numerator.bit_length() + 2*precision + 2 > a.operand_limit:
        raise ReferenceError("resource", "Independent angular square-root preflight exceeds operand domain")
    numerator, denominator = value.numerator << (2*precision), value.denominator
    root = isqrt(numerator // denominator)
    if 2*root.bit_length() + denominator.bit_length() + 1 > a.operand_limit:
        raise ReferenceError("resource", "Independent angular square-root comparison exceeds operand domain")
    scale = 1 << precision
    return F(root,scale), F(root if root*root*denominator == numerator else root+1,scale)


def pi_bounds(precision, a):
    key = ("independent_exact_axis_pi", precision)
    cached = a.lookup(key)
    if cached is not None:
        a.guard(*cached)
        return cached
    count = (precision+15)//4
    def arc(denominator):
        step = F(1,denominator*denominator)
        power, total = F(1,denominator), F(0)
        for index in range(count):
            term = a.exact(power,2*index+1,"div")
            total = a.exact(total,term,"sub" if index%2 else "add")
            power = a.exact(power,step,"mul")
        tail = a.exact(power,2*count+1,"div")
        other = a.exact(total,tail,"sub" if count%2 else "add")
        return min(total,other),max(total,other)
    first,last = arc(5),arc(239)
    low = a.exact(a.exact(16,first[0],"mul"),a.exact(4,last[1],"mul"),"sub")
    high = a.exact(a.exact(16,first[1],"mul"),a.exact(4,last[0],"mul"),"sub")
    scale = 1 << precision
    a.guard(F(scale))
    low_scaled, high_scaled = a.exact(low,scale,"mul"),a.exact(high,scale,"mul")
    result = (F(low_scaled.numerator//low_scaled.denominator,scale),
              F(-(-high_scaled.numerator//high_scaled.denominator),scale))
    return a.remember(key,result)


def polynomial_sincos(value, a):
    a.tick()
    a.guard(value)
    if abs(value)>1 or value.denominator > GRID or value.denominator & (value.denominator-1):
        raise ReferenceError("numeric", "Independent source sine polynomial requires its fixed reduced grid")
    square = a.exact(value,value,"mul")
    sine, cosine = F(1,factorial(25)), F(1,factorial(24))
    for index in range(11,-1,-1):
        sign = -1 if index%2 else 1
        sine = a.exact(a.exact(sine,square,"mul"),F(sign,factorial(2*index+1)),"add")
        cosine = a.exact(a.exact(cosine,square,"mul"),F(sign,factorial(2*index)),"add")
    return nearest_grid(a.exact(value,sine,"mul"),a),nearest_grid(cosine,a)


def reduced_sincos(lower, upper, pi, a):
    middle_pi = a.exact(a.exact(pi[0],pi[1],"add"),2,"div")
    ratio = a.exact(a.exact(lower,upper,"add"),middle_pi,"div")
    quadrant = nearest_grid(ratio,a,bits=0).numerator
    first,last = sorted(a.exact(quadrant,value,"mul") for value in pi)
    low = a.exact(lower,a.exact(last,2,"div"),"sub")
    high = a.exact(upper,a.exact(first,2,"div"),"sub")
    value = nearest_grid(a.exact(a.exact(low,high,"add"),2,"div"),a)
    error = max(a.exact(value,low,"sub"),a.exact(high,value,"sub"))
    if error > ARGUMENT_ERROR or abs(value)>1:
        return None
    sine,cosine = polynomial_sincos(value,a)
    return ((sine,cosine),(cosine,-sine),(-sine,-cosine),(-cosine,sine))[quadrant%4]


def axis_rotation(axis, angle, a):
    """The inherited finite source hinge law, independently reconstructed."""
    a.tick()
    axis,angle = tuple(F(value) for value in axis),F(angle)
    a.guard(*axis,angle)
    maximum = max(map(abs,axis))
    if not maximum:
        raise ReferenceError("numeric", "Independent canonical source axis is zero")
    scaled = tuple(a.exact(value,maximum,"div") for value in axis)
    norm = sqrt_bounds(a.exact_sum(*(a.exact(value,value,"mul") for value in scaled)),96,a)
    if not angle:
        return (F(1),F(0),F(0),F(0))
    midpoint = a.exact(a.exact(norm[0],norm[1],"add"),2,"div")
    unit = tuple(nearest_grid(a.exact(value,midpoint,"div"),a) for value in scaled)
    half = a.exact(angle,2,"div")
    if abs(half)<=1:
        pair = polynomial_sincos(nearest_grid(half,a),a)
    else:
        pair = None
        for precision in PRECISIONS:
            pair = reduced_sincos(half,half,pi_bounds(precision,a),a)
            if pair is not None:
                break
        if pair is None:
            raise ReferenceError("numeric", "Independent canonical source angle reduction cannot be certified")
    sine,cosine = pair
    return rotation((cosine,*(a.exact(value,sine,"mul") for value in unit)),a)


def spin_plan(omega, elapsed, a):
    """First certifying stage for this source vector and actual elapsed only.

    The plan contains pure independently computed operands. The original
    arithmetic cache owns at most 256 entries and re-admits its live operand
    domain. No source state, producer plan, horizon or action clock is cached.
    """
    a.tick()
    omega, elapsed = tuple(F(value) for value in omega), F(elapsed)
    a.guard(*omega, elapsed)
    key = ("independent_c092_spin_plan", omega, abs(elapsed))
    cached = a.lookup(key)
    if cached is not None:
        precision, scaled, maximum, norm, pi, error = cached
        a.guard(precision, *scaled, maximum, *norm, *pi, error)
        return cached
    maximum = max(map(abs,omega))
    if not maximum:
        raise ReferenceError("numeric", "A stationary source spin has no nonzero point plan")
    scaled = tuple(a.exact(value,maximum,"div") for value in omega)
    square = a.exact_sum(*(a.exact(value,value,"mul") for value in scaled))
    for precision in PRECISIONS:
        norm,pi = sqrt_bounds(square,precision,a),pi_bounds(precision,a)
        extent = a.exact(a.exact(maximum,abs(elapsed),"mul"),norm[1],"mul")
        quotient = a.exact(extent,pi[0],"div")
        a.tick()
        kmax = quotient.numerator//quotient.denominator+2
        a.guard(kmax)
        angular_width = a.exact(a.exact(maximum,abs(elapsed),"mul"),a.exact(norm[1],norm[0],"sub"),"mul")
        pi_width = a.exact(kmax,a.exact(pi[1],pi[0],"sub"),"mul")
        error = a.exact(a.exact(a.exact(angular_width,pi_width,"add"),4,"div"),F(1,1<<97),"add")
        a.tick()
        if error <= ARGUMENT_ERROR:
            return a.remember(key,(precision,scaled,maximum,norm,pi,error))
    raise ReferenceError("numeric", "Independent finite source spin phase reduction cannot be certified")


def spin_rotation(omega, elapsed, a):
    """Execute the selected point stage; later reduction failure is terminal."""
    a.tick()
    omega,elapsed = tuple(F(value) for value in omega),F(elapsed)
    a.guard(*omega,elapsed)
    if not any(omega) or not elapsed:
        return (F(1),F(0),F(0),F(0))
    _,scaled,maximum,norm,pi,_ = spin_plan(omega,elapsed,a)
    factor = a.exact(a.exact(maximum,elapsed,"mul"),2,"div")
    low,high = sorted(a.exact(factor,value,"mul") for value in norm)
    pair = reduced_sincos(low,high,pi,a)
    if pair is None:
        raise ReferenceError("numeric", "Independent selected source spin did not enclose its point")
    midpoint = a.exact(a.exact(norm[0],norm[1],"add"),2,"div")
    unit = tuple(nearest_grid(a.exact(value,midpoint,"div"),a) for value in scaled)
    sine,cosine = pair
    return rotation((cosine,*(a.exact(value,sine,"mul") for value in unit)),a)
