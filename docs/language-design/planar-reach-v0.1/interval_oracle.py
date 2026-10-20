"""Bounded rational enclosure proof for the proposed planar reach contract.

This is independent fixture evidence, not an OntoKin runtime implementation.
It imports neither OntoKin nor the original Decimal oracle. All transcendental
enclosures use rational arithmetic and explicit remainder bounds. See
numeric-admission.md for proofs, counted units and implementation obligations.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Q
from math import isqrt
import struct
from typing import Callable

PRECISIONS = (96, 192, 384, 768, 1536)
MAX_SERIES_TERMS = 12_000  # Recurrence steps, including one paired sin/cos step.
MAX_INTERVAL_OPERATIONS = 100_000
MAX_OPERAND_BITS = 32_768
PI64_BITS = 0x400921FB54442D18
SIGN = 1 << 63
FRACTION_MASK = (1 << 52) - 1
MAX_FINITE_BITS = 0x7FEFFFFFFFFFFFFF


class ResourceLimit(ArithmeticError):
    """The declared finite proof resource bound was reached."""


class NeedPrecision(ArithmeticError):
    """This finite enclosure does not yet certify the requested result."""


class NumericFailure(ArithmeticError):
    """No precision pass certified the result within the finite schedule."""


class Cancelled(ArithmeticError):
    """An explicitly supplied proof-check cancellation callback interrupted."""


@dataclass
class Budget:
    max_series_terms: int = MAX_SERIES_TERMS
    max_interval_operations: int = MAX_INTERVAL_OPERATIONS
    max_operand_bits: int = MAX_OPERAND_BITS
    max_proof_operations: int = MAX_INTERVAL_OPERATIONS
    cancel: Callable[[], bool] | None = None
    series_terms: int = 0
    interval_operations: int = 0
    exact_proof_operations: int = 0
    maximum_operand_bits: int = 0
    maximum_preflight_bits: int = 0

    def __post_init__(self):
        limits = ((self.max_series_terms, MAX_SERIES_TERMS),
                  (self.max_interval_operations, MAX_INTERVAL_OPERATIONS),
                  (self.max_operand_bits, MAX_OPERAND_BITS),
                  (self.max_proof_operations, MAX_INTERVAL_OPERATIONS))
        if any(type(value) is not int or not 0 <= value <= limit for value, limit in limits):
            raise ValueError("a lowered proof budget cannot raise a fixed maximum")

    def poll(self):
        if self.cancel is not None and self.cancel():
            raise Cancelled("proof check interrupted")

    def integers(self, *values: int):
        self.poll()
        width = max((abs(v).bit_length() for v in values), default=0)
        if width > self.max_operand_bits:
            raise ResourceLimit("integer/rational operand width")
        self.maximum_operand_bits = max(self.maximum_operand_bits, width)

    def fractions(self, *values: Q):
        for value in values:
            if not isinstance(value, Q):
                raise TypeError("proof operands must be Fractions")
            self.integers(value.numerator, value.denominator)

    def preflight(self, bits: int):
        self.poll()
        if bits > self.max_operand_bits:
            raise ResourceLimit("preflight intermediate width")
        self.maximum_preflight_bits = max(self.maximum_preflight_bits, bits)

    def term(self):
        self.poll()
        if self.series_terms >= self.max_series_terms:
            raise ResourceLimit("series recurrence steps")
        self.series_terms += 1

    def interval(self):
        self.poll()
        if (self.interval_operations >= self.max_interval_operations or
                self.interval_operations+self.exact_proof_operations >= self.max_proof_operations):
            raise ResourceLimit("outward interval operations")
        self.interval_operations += 1

    def exact(self):
        self.poll()
        # These declared helper operations share a finite proof-work counter.
        # Production still must charge all additional runtime work as specified.
        if self.interval_operations+self.exact_proof_operations >= self.max_proof_operations:
            raise ResourceLimit("exact proof operations")
        self.exact_proof_operations += 1

    def record(self):
        return {name: getattr(self, name) for name in (
            "series_terms", "interval_operations", "exact_proof_operations",
            "maximum_operand_bits", "maximum_preflight_bits")}


def exact_op(budget: Budget, operation: str, a: Q, b: Q) -> Q:
    """Preflight a conservative temporary-width bound before Fraction work."""
    budget.fractions(a, b)
    an, ad = abs(a.numerator).bit_length(), a.denominator.bit_length()
    bn, bd = abs(b.numerator).bit_length(), b.denominator.bit_length()
    if operation in ("add", "sub"):
        budget.preflight(max(an + bd, bn + ad, ad + bd) + 1)
    elif operation == "mul":
        budget.preflight(max(an + bn, ad + bd) + 1)
    elif operation == "div":
        if b == 0:
            raise ZeroDivisionError("zero exact divisor")
        budget.preflight(max(an + bd, ad + bn) + 1)
    else:
        raise ValueError("unknown exact operation")
    budget.exact()
    value = {"add": Q.__add__, "sub": Q.__sub__, "mul": Q.__mul__,
             "div": Q.__truediv__}[operation](a, b)
    budget.fractions(value)
    return value


@dataclass(frozen=True)
class Interval:
    lo: Q
    hi: Q

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("reversed interval")

    def record(self):
        return {"lower": rational_record(self.lo), "upper": rational_record(self.hi)}


def rational_record(value: Q):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def sign(value: Q) -> int:
    return (value > 0) - (value < 0)


class Context:
    """All constructed interval endpoints are outward dyadics at one precision."""
    def __init__(self, precision: int, budget: Budget):
        if precision not in PRECISIONS:
            raise ValueError("precision is outside the fixed schedule")
        budget.preflight(2 * precision + 2)
        self.precision, self.budget = precision, budget
        self.scale = 1 << precision
        self._pi = None

    def out(self, lo: Q, hi: Q, *, charged: bool = False) -> Interval:
        self.budget.fractions(lo, hi)
        if lo > hi:
            raise ValueError("reversed outward input")
        self.budget.preflight(max(abs(lo.numerator).bit_length(),
                                  abs(hi.numerator).bit_length()) + self.precision + 1)
        if not charged:
            self.budget.interval()
        lower = lo.numerator * self.scale // lo.denominator
        upper = -((-hi.numerator * self.scale) // hi.denominator)
        result = Interval(Q(lower, self.scale), Q(upper, self.scale))
        self.budget.fractions(result.lo, result.hi)
        return result

    def point(self, value: Q | int) -> Interval:
        value = Q(value)
        return self.out(value, value)

    def _temporary(self, *values: Q):
        self.budget.fractions(*values)
        widths = [max(abs(v.numerator).bit_length(), v.denominator.bit_length()) for v in values]
        self.budget.preflight(2 * max(widths, default=0) + 2)
        self.budget.interval()

    def add(self, a: Interval, b: Interval) -> Interval:
        self._temporary(a.lo, a.hi, b.lo, b.hi)
        return self.out(a.lo + b.lo, a.hi + b.hi, charged=True)

    def neg(self, a: Interval) -> Interval:
        self._temporary(a.lo, a.hi)
        return self.out(-a.hi, -a.lo, charged=True)

    def sub(self, a: Interval, b: Interval) -> Interval:
        self._temporary(a.lo, a.hi, b.lo, b.hi)
        return self.out(a.lo - b.hi, a.hi - b.lo, charged=True)

    def mul(self, a: Interval, b: Interval) -> Interval:
        self._temporary(a.lo, a.hi, b.lo, b.hi)
        products = (a.lo*b.lo, a.lo*b.hi, a.hi*b.lo, a.hi*b.hi)
        return self.out(min(products), max(products), charged=True)

    def div(self, a: Interval, b: Interval) -> Interval:
        self._temporary(a.lo, a.hi, b.lo, b.hi)
        if b.lo <= 0 <= b.hi:
            raise NeedPrecision("interval divisor contains zero")
        quotients = (a.lo/b.lo, a.lo/b.hi, a.hi/b.lo, a.hi/b.hi)
        return self.out(min(quotients), max(quotients), charged=True)

    def square(self, a: Interval) -> Interval:
        self._temporary(a.lo, a.hi)
        values = (a.lo*a.lo, a.hi*a.hi)
        return self.out(Q(0) if a.lo <= 0 <= a.hi else min(values), max(values), charged=True)

    def widen(self, value: Interval, error: Q) -> Interval:
        if error < 0:
            raise ValueError("negative remainder bound")
        self._temporary(value.lo, value.hi, error)
        return self.out(value.lo-error, value.hi+error, charged=True)

    def sqrt_point(self, value: Q) -> Interval:
        self.budget.fractions(value)
        if value < 0:
            raise ValueError("negative square root")
        self.budget.preflight(value.numerator.bit_length() + 2*self.precision + 1)
        self.budget.interval()
        scaled_numerator = value.numerator << (2*self.precision)
        floor_radicand = scaled_numerator // value.denominator
        self.budget.integers(floor_radicand)
        self.budget.poll()
        root = isqrt(floor_radicand)
        self.budget.poll()
        self.budget.preflight(max(2*root.bit_length() + value.denominator.bit_length(),
                                  scaled_numerator.bit_length()) + 1)
        exact = root*root*value.denominator == scaled_numerator
        result = Interval(Q(root, self.scale), Q(root if exact else root+1, self.scale))
        self.budget.fractions(result.lo, result.hi)
        return result

    def atan_small(self, value: Q) -> Interval:
        """Alternating series with an exact uniform first-omitted-term bound."""
        self.budget.fractions(value)
        if abs(value) > Q(1, 2):
            raise ValueError("arctangent series reduction failed")
        if value == 0:
            return self.point(0)
        count = (self.precision + 5) // 2
        x = self.point(value)
        x2 = self.square(x)
        power = x
        total = self.point(0)
        for index in range(count):
            self.budget.term()
            term = self.div(power, self.point(2*index+1))
            total = self.add(total, term) if index % 2 == 0 else self.sub(total, term)
            if index+1 < count:
                power = self.mul(power, x2)
        self.budget.preflight(2*count+1 + (2*count+1).bit_length() + 1)
        tail = Q(1, (1 << (2*count+1))*(2*count+1))
        return self.widen(total, tail)

    def pi(self) -> Interval:
        if self._pi is None:
            # Machin identity, proved by rational tangent addition in the text.
            self._pi = self.sub(self.mul(self.point(16), self.atan_small(Q(1, 5))),
                                self.mul(self.point(4), self.atan_small(Q(1, 239))))
        return self._pi

    def atan_point(self, value: Q) -> Interval:
        self.budget.fractions(value)
        if value < 0:
            return self.neg(self.atan_point(-value))
        if value > 1:
            inverse = exact_op(self.budget, "div", Q(1), value)
            return self.sub(self.div(self.pi(), self.point(2)), self.atan_point(inverse))
        if value > Q(1, 2):
            numerator = exact_op(self.budget, "sub", value, Q(1))
            denominator = exact_op(self.budget, "add", value, Q(1))
            transformed = exact_op(self.budget, "div", numerator, denominator)
            return self.add(self.div(self.pi(), self.point(4)), self.atan_small(transformed))
        return self.atan_small(value)

    def atan(self, value: Interval) -> Interval:
        lo = self.atan_point(value.lo)
        if value.lo == value.hi:
            return lo
        hi = self.atan_point(value.hi)
        return self.out(lo.lo, hi.hi)

    def atan2(self, y: Interval, x: Interval, sy: int, sx: int,
              negative_axis: bool = True) -> Interval:
        """Exact algebraic signs select the quadrant; intervals only bound size."""
        if sy == 0:
            if sx == 0:
                raise ValueError("underdetermined argument")
            if sx > 0:
                return self.point(0)
            return self.neg(self.pi()) if negative_axis else self.pi()
        if sx == 0:
            half_pi = self.div(self.pi(), self.point(2))
            return half_pi if sy > 0 else self.neg(half_pi)
        ax = x if sx > 0 else self.neg(x)
        ay = y if sy > 0 else self.neg(y)
        if ax.lo < 0 or ay.lo < 0:
            raise NeedPrecision("quadrant magnitude enclosure crosses zero")
        if ax.lo > 0 and (ay.lo == 0 or ax.lo >= ay.lo):
            theta = self.atan(self.div(ay, ax))
        elif ay.lo > 0:
            theta = self.sub(self.div(self.pi(), self.point(2)), self.atan(self.div(ax, ay)))
        else:
            raise NeedPrecision("both quadrant magnitudes include zero")
        if sx < 0:
            theta = self.sub(self.pi(), theta)
        return theta if sy > 0 else self.neg(theta)

    def sincos_point(self, value: Q) -> tuple[Interval, Interval]:
        """Paired Taylor recurrences and uniform Lagrange bounds on [-8,8]."""
        self.budget.fractions(value)
        if abs(value) > 8:
            raise ValueError("sine/cosine proof is limited to [-8,8]")
        if value == 0:
            return self.point(0), self.point(1)
        target = Q(1, 1 << (self.precision+8))
        count, numerator, denominator = 1, 64, 2
        while Q(numerator, denominator) > target or count < 5:
            self.budget.exact()
            self.budget.preflight(max(numerator.bit_length()+7,
                denominator.bit_length()+(2*count+2).bit_length()*2)+1)
            numerator *= 64
            denominator *= (2*count+1)*(2*count+2)
            count += 1
        self.budget.integers(numerator, denominator)
        cos_tail = Q(numerator, denominator)
        sin_tail = exact_op(self.budget, "mul", cos_tail, Q(8, 2*count+1))
        x = self.point(value)
        minus_x2 = self.neg(self.square(x))
        sin_term, cos_term = x, self.point(1)
        sine, cosine = self.point(0), self.point(0)
        for index in range(count):
            self.budget.term()
            if index:
                sin_term = self.div(self.mul(sin_term, minus_x2), self.point((2*index)*(2*index+1)))
                cos_term = self.div(self.mul(cos_term, minus_x2), self.point((2*index-1)*(2*index)))
            sine, cosine = self.add(sine, sin_term), self.add(cosine, cos_term)
        return self.widen(sine, sin_tail), self.widen(cosine, cos_tail)


def binary64_bits(value: float) -> int:
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def bits_float(bits: int) -> float:
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def bits_fraction(bits: int) -> Q:
    exponent, mantissa = (bits >> 52) & 0x7FF, bits & FRACTION_MASK
    if exponent == 0x7FF:
        raise ValueError("nonfinite binary64")
    if exponent:
        mantissa |= 1 << 52
        shift = exponent - 1023 - 52
    else:
        shift = -1074
    value = Q(mantissa << shift) if shift >= 0 else Q(mantissa, 1 << -shift)
    return -value if bits & SIGN else value


def _nearest_even_integer(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (2*remainder > denominator or (2*remainder == denominator and quotient % 2 == 1))


def round_binary64(value: Q, budget: Budget | None = None) -> int:
    """Integer-only exact rational -> nearest-even binary64; canonical +zero."""
    budget = budget or Budget()
    budget.fractions(value)
    budget.exact()
    if value == 0:
        return 0
    negative = value < 0
    n, d = abs(value.numerator), value.denominator
    exponent = n.bit_length() - d.bit_length()
    if exponent >= 0:
        budget.preflight(d.bit_length()+exponent+1)
        if n < d << exponent:
            exponent -= 1
    else:
        budget.preflight(n.bit_length()-exponent+1)
        if n << -exponent < d:
            exponent -= 1
    if exponent > 1023:
        return (SIGN if negative else 0) | (0x7FF << 52)
    shift = 1074 if exponent < -1022 else 52-exponent
    budget.preflight(max(n.bit_length()+max(0, shift), d.bit_length()+max(0, -shift))+2)
    m = _nearest_even_integer(n << shift, d) if shift >= 0 else _nearest_even_integer(n, d << -shift)
    if exponent < -1022:
        result = m
    else:
        if m == 1 << 53:
            m >>= 1
            exponent += 1
        result = (0x7FF << 52) if exponent > 1023 else ((exponent+1023) << 52) | (m-(1 << 52))
    return result | (SIGN if negative and result else 0)


def rounding_cell(bits: int) -> tuple[Q, Q, bool]:
    """Exact finite nearest-even cell; zero collapses the two signed zeroes."""
    value = bits_fraction(bits)
    magnitude = bits & ~SIGN
    if not magnitude:
        return -Q(1, 1 << 1075), Q(1, 1 << 1075), True
    if bits & SIGN:
        lo, hi, included = rounding_cell(magnitude)
        return -hi, -lo, included
    previous = bits_fraction(bits-1)
    following = Q(1 << 1024) if bits == MAX_FINITE_BITS else bits_fraction(bits+1)
    return (previous+value)/2, (value+following)/2, bits % 2 == 0


def cell_contains(enclosure: Interval, bits: int) -> bool:
    lower, upper, included = rounding_cell(bits)
    return ((enclosure.lo >= lower and enclosure.hi <= upper) if included else
            (enclosure.lo > lower and enclosure.hi < upper))


def certify_rounding(enclosure: Interval, budget: Budget) -> dict:
    lower_bits = round_binary64(enclosure.lo, budget)
    upper_bits = round_binary64(enclosure.hi, budget)
    if lower_bits != upper_bits or not cell_contains(enclosure, lower_bits):
        raise NeedPrecision("enclosure is not wholly inside one nearest-even cell")
    lower, upper, included = rounding_cell(lower_bits)
    return {"enclosure": enclosure.record(), "rounded_bits": f"{lower_bits:016x}",
            "cell_lower": rational_record(lower), "cell_upper": rational_record(upper),
            "midpoint_ties_included": included, "whole_enclosure_inside_cell": True}


def radical_sign(a: Q, b: Q, d: Q, budget: Budget) -> int:
    """Decide sign(a+b*sqrt(d)) exactly, including algebraic cancellation."""
    budget.fractions(a, b, d)
    budget.exact()
    if d < 0:
        raise ValueError("negative radical")
    if b == 0 or d == 0:
        return sign(a)
    if a == 0 or sign(a) == sign(b):
        return sign(b)
    a2 = exact_op(budget, "mul", a, a)
    b2d = exact_op(budget, "mul", exact_op(budget, "mul", b, b), d)
    difference = exact_op(budget, "sub", a2, b2d)
    return sign(a) * sign(difference)


def classify(lengths, target, branch="positive", budget: Budget | None = None):
    """Numeric domains and exact annulus only; source topology is not inferred."""
    budget = budget or Budget()
    if len(lengths) != 2 or len(target) != 3 or branch not in ("positive", "negative"):
        raise ValueError("expected two lengths, three target components and a branch")
    bits = [binary64_bits(float(v)) for v in [*lengths, *target]]
    if any((b >> 52) & 0x7FF == 0x7FF for b in bits):
        return {"status": "rejected", "reach_code": "reach_domain"}
    a, b, x, y, z = map(bits_fraction, bits)
    budget.fractions(a, b, x, y, z)
    budget.exact()
    if z != 0:
        return {"status": "rejected", "reach_code": "reach_frame"}
    if not Q(1, 8) <= a <= 4 or not Q(1, 8) <= b <= 4 or max(abs(x), abs(y)) > 8:
        return {"status": "rejected", "reach_code": "reach_domain"}
    r2 = exact_op(budget, "add", exact_op(budget, "mul", x, x), exact_op(budget, "mul", y, y))
    difference, total = exact_op(budget, "sub", a, b), exact_op(budget, "add", a, b)
    inner, outer = exact_op(budget, "mul", difference, difference), exact_op(budget, "mul", total, total)
    if not inner <= r2 <= outer:
        return {"status": "rejected", "reach_code": "reach_unreachable", "radius_squared": rational_record(r2)}
    if a == b and r2 == 0:
        return {"status": "rejected", "reach_code": "reach_singular", "radius_squared": rational_record(r2)}
    return {"status": "admissible_geometry", "values": (a, b, x, y), "radius_squared": r2,
            "input_bits": [f"{v:016x}" for v in bits]}


def prove_solution(lengths, target, branch="positive", budget: Budget | None = None) -> dict:
    """Prove the selected canonical pair and its real forward residual bound."""
    budget = budget or Budget()
    classified = classify(lengths, target, branch, budget)
    if classified["status"] != "admissible_geometry":
        return {**classified, "work": budget.record()}
    a, b, x, y = classified["values"]
    r2 = classified["radius_squared"]
    op = lambda name, left, right: exact_op(budget, name, left, right)
    c = op("div", op("sub", op("sub", r2, op("mul", a, a)), op("mul", b, b)),
           op("mul", Q(2), op("mul", a, b)))
    d = op("sub", Q(1), op("mul", c, c))
    if not -1 <= c <= 1 or d < 0:
        raise AssertionError("exact annulus and cosine disagree")
    s = Q(1 if branch == "positive" else -1)
    t = op("add", a, op("mul", b, c))
    xa, xb = op("mul", t, x), op("mul", op("mul", s, b), y)
    ya, yb = op("mul", t, y), -op("mul", op("mul", s, b), x)
    sx, sy = radical_sign(xa, xb, d, budget), radical_sign(ya, yb, d, budget)
    # The vector has norm r2. Exact positive scaling changes neither sign nor
    # argument, and avoids losing both components for subnormal-radius inputs.
    nxa, nxb, nya, nyb = (op("div", value, r2) for value in (xa, xb, ya, yb))
    attempts = []
    for precision in PRECISIONS:
        attempts.append(precision)
        context = Context(precision, budget)
        try:
            root = context.sqrt_point(d)
            xx = context.point(0) if sx == 0 else context.add(context.point(nxa), context.mul(context.point(nxb), root))
            yy = context.point(0) if sy == 0 else context.add(context.point(nya), context.mul(context.point(nyb), root))
            shoulder = context.atan2(yy, xx, sy, sx)
            elbow = context.atan2(root, context.point(c), sign(d), sign(c), negative_axis=False)
            if branch == "negative":
                elbow = context.neg(elbow)
            proofs = [certify_rounding(v, budget) for v in (shoulder, elbow)]
            rounded = [int(p["rounded_bits"], 16) for p in proofs]
            canonical = [rounded[0] ^ SIGN if rounded[0] == PI64_BITS else rounded[0], rounded[1]]
            q1, q2 = map(bits_fraction, canonical)
            sin1, cos1 = context.sincos_point(q1)
            sin12, cos12 = context.sincos_point(op("add", q1, q2))
            px = context.add(context.mul(context.point(a), cos1), context.mul(context.point(b), cos12))
            py = context.add(context.mul(context.point(a), sin1), context.mul(context.point(b), sin12))
            dx, dy = context.sub(px, context.point(x)), context.sub(py, context.point(y))
            residual2 = context.add(context.square(dx), context.square(dy))
            if residual2.hi > Q(1, 10**18):
                raise NeedPrecision("rounded-pair forward residual not certified")
            for index, proof in enumerate(proofs):
                proof.update({"coordinate": ("shoulder", "elbow")[index],
                              "canonical_bits": f"{canonical[index]:016x}",
                              "canonical_hex": bits_float(canonical[index]).hex(),
                              "positive_pi_shoulder_remap": rounded[index] != canonical[index]})
            return {"status": "proved", "method": "outward-dyadic-planar-ik/0.2",
                "input_bits": classified["input_bits"], "branch": branch,
                "precision_bits": precision, "precision_attempts": attempts,
                "exact_algebra": {"radius_squared": rational_record(r2), "cos_elbow": rational_record(c),
                    "radicand": rational_record(d), "shoulder_real_coefficients": [rational_record(xa), rational_record(xb)],
                    "shoulder_imag_coefficients": [rational_record(ya), rational_record(yb)],
                    "positive_direction_scale": rational_record(r2),
                    "shoulder_real_sign": sx, "shoulder_imag_sign": sy},
                "coordinates": proofs,
                "canonical_forward_tip": {"x": px.record(), "y": py.record()},
                "residual_squared_m2": residual2.record(), "residual_limit_squared_m2": rational_record(Q(1, 10**18)),
                "work": budget.record()}
        except NeedPrecision:
            continue
    raise NumericFailure("five precision passes could not certify the required rounding and residual")
