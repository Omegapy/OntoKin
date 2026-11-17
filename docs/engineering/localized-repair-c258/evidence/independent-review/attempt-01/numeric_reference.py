"""Independent exact rational/binary-search quaternion projection reference.

No Decimal normalization, candidate imports, product parser or C255 helper.
Only used by independent finite controls, never by the proposed reader.
"""
from fractions import Fraction
from math import isfinite
from struct import pack, unpack

TOLERANCE = Fraction(1, 10**12)
ONE_BITS = unpack('>Q', pack('>d', 1.0))[0]


def from_bits(bits):
    return unpack('>d', pack('>Q', bits))[0]


def correctly_rounded_sqrt_of_ratio(value):
    """Round sqrt(value), where 0<=value<=1, by ordered positive binary64 bits."""
    assert 0 <= value <= 1
    low, high = 0, ONE_BITS
    while low < high:
        middle = (low + high + 1) // 2
        rational = Fraction.from_float(from_bits(middle))
        if rational*rational <= value:
            low = middle
        else:
            high = middle - 1
    floor = Fraction.from_float(from_bits(low))
    if floor*floor == value:
        return from_bits(low)
    ceiling = Fraction.from_float(from_bits(low + 1))
    midpoint = (floor + ceiling) / 2
    if value < midpoint*midpoint:
        return from_bits(low)
    if value > midpoint*midpoint:
        return from_bits(low + 1)
    return from_bits(low if low % 2 == 0 else low + 1)


def quaternion_reference(values):
    assert len(values) == 4
    assert all(type(x) in (int,float) and isfinite(x) for x in values)
    inputs = [Fraction.from_float(float(x)) for x in values]
    square_sum = sum(x*x for x in inputs)
    if not (1-TOLERANCE)**2 <= square_sum <= (1+TOLERANCE)**2:
        raise ValueError('outside adopted exact quaternion norm condition')
    sign = next((1 if x > 0 else -1 for x in inputs if x), 1)
    return [0.0 if not x else correctly_rounded_sqrt_of_ratio(x*x/square_sum) *
            (1 if x*sign > 0 else -1) for x in inputs]


if __name__ == '__main__':
    assert quaternion_reference([1,0,0,0]) == [1,0,0,0]
    assert quaternion_reference([-1,0,0,0]) == [1,0,0,0]
    assert quaternion_reference([0,1,0,0]) == [0,1,0,0]
    assert quaternion_reference([-.5,-.5,-.5,-.5]) == [.5,.5,.5,.5]
    assert quaternion_reference([1,5e-324,0,0]) == [1,5e-324,0,0]
    # Midpoint tie between zero and the smallest positive subnormal rounds even.
    eta = Fraction.from_float(5e-324)
    assert correctly_rounded_sqrt_of_ratio((eta/2)**2) == 0.0
    # Midpoint tie between odd and even subnormal significands rounds upward.
    assert correctly_rounded_sqrt_of_ratio((3*eta/2)**2) == 1e-323
    try:
        quaternion_reference([1.000000000002,0,0,0])
    except ValueError:
        pass
    else:
        raise AssertionError('invalid quaternion was accepted')
    print('PASS: exact norm/sign, subnormal projections and ties-to-even controls.')
