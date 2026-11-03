"""Independent exact arithmetic for canonical angular zero proofs.

This module evaluates the documented homogeneous projective operations from
source operands. It imports no producer pose implementation or runtime state.
The 96-bit nearest-even grid and final binary64 exposure are actual arithmetic
steps, not a tolerance or an uncertainty midpoint.
"""
from fractions import Fraction as F
import struct

from .reach_reference import ReferenceError

GRID = 1 << 96


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
