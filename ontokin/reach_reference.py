"""Independent source reference for the recorded planar reach profile.

This module deliberately imports no evaluator, reach solver, pose sampler,
planner, certifier, exporter, or preparation oracle.  It reads the immutable
constructed source records and interprets their equations and event clocks.
Fraction enclosures, rather than host transcendental answers, supply expected
poses.  A supplied request work context is shared throughout; this verifier
never creates another execution allowance.

The public numeric leaves are ``Interval`` instances where an exact binary64
answer is not a source invariant.  A consumer must check containment (including
the independently propagated source arithmetic allowance), not compare a
chosen interval midpoint as an exact expected answer.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
import copy
from dataclasses import dataclass, field, fields, is_dataclass, replace
from fractions import Fraction as F
import math
import struct
from types import MappingProxyType


MAX_OPERAND_BITS = 32768
MAX_BOUNDARIES = 10000
MAX_CACHE = 256
PRECISIONS = (128, 256, 512, 1024, 2048)
PI64 = F(3.141592653589793)
ZERO = (F(0), F(0), F(0))
UNIT = (F(1), F(0), F(0), F(0))


class ReferenceError(Exception):
    """The independent reference cannot certify the requested source prefix."""
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("Reversed reference interval")

    @property
    def magnitude(self):
        return max(abs(self.lo), abs(self.hi))

    def contains(self, value):
        return self.lo <= F(value) <= self.hi


class _Uncertain(Exception):
    pass


class _Arithmetic:
    """Outward Fraction arithmetic with a bounded dyadic endpoint grid.

    The integer-grid representation is deliberately not the production
    numerical kernel: each operation first forms exact Fraction extrema and
    rounds its endpoints outward.  All constituent scalar operations charge
    the caller, and operand growth is checked before multiplication/division.
    """
    def __init__(self, work=None, check=None, *, bits=128):
        if work is None and check is None:
            raise ValueError("Independent verification requires shared work or a bounded check callback")
        self.work = work
        self.check = work.tick if work is not None else check
        self.bits = bits
        self.scale = self._dyadic_denominator(bits)
        self.cache = {}
        self._cache_operand_limit = self.operand_limit

    @property
    def operand_limit(self):
        """Honor a caller's narrower live domain without enlarging this reader."""
        requested = getattr(self.work, "max_operand_bits", MAX_OPERAND_BITS)
        if type(requested) is not int or requested < 1:
            raise ReferenceError("resource", "Invalid independent reference operand limit")
        return min(MAX_OPERAND_BITS, requested)

    def _dyadic_denominator(self, exponent):
        if exponent + 1 > self.operand_limit:
            raise ReferenceError("resource", "Reference dyadic denominator exceeds operand limit")
        return 1 << exponent

    def _sync_cache_operand_limit(self):
        if self._cache_operand_limit != self.operand_limit:
            # Existing lookup/insertion charges cover their usual bounded
            # bookkeeping. A changed domain additionally charges this reset.
            self.tick()
            self.cache.clear()
            self._cache_operand_limit = self.operand_limit

    def tick(self):
        self.check()

    def guard(self, *values):
        limit = self.operand_limit
        for value in values:
            value = F(value)
            if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > limit:
                raise ReferenceError("resource", "Independent reference operand limit exceeded")

    def exact(self, a, b, kind):
        self.tick()
        a, b = F(a), F(b)
        self.guard(a, b)
        an, ad = abs(a.numerator).bit_length(), a.denominator.bit_length()
        bn, bd = abs(b.numerator).bit_length(), b.denominator.bit_length()
        if kind in ("add", "sub"):
            extent = max(an + bd, bn + ad) + 1
            denominator = ad + bd
        elif kind == "mul":
            extent, denominator = an + bn, ad + bd
        elif kind == "div":
            if not b:
                raise _Uncertain("Reference division includes zero")
            extent, denominator = an + bd, ad + bn
        else:
            raise ValueError(kind)
        if max(extent, denominator) > self.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        return {"add": F.__add__, "sub": F.__sub__, "mul": F.__mul__, "div": F.__truediv__}[kind](a, b)

    def exact_sum(self, *values):
        """Fold bounded exact scalars without allocating additions of zero."""
        self.tick()
        values = tuple(F(value) for value in values)
        self.guard(*values)
        result = F(0)
        for value in values:
            if value:
                result = value if not result else self.exact(result, value, "add")
        return result

    def exact_product(self, *values):
        """Guard every operand before omitting exact zero/identity products."""
        self.tick()
        values = tuple(F(value) for value in values)
        self.guard(*values)
        if any(not value for value in values):
            return F(0)
        result = F(1)
        for value in values:
            if value != 1:
                result = value if result == 1 else self.exact(result, value, "mul")
        return result

    def point(self, value):
        self.tick()
        value = F(value)
        self.guard(value)
        return Interval(value, value)

    def grid(self, low, high):
        self.tick()
        self._grid_domain(low, high)
        low_n = (low.numerator << self.bits) // low.denominator
        high_n = -((-high.numerator << self.bits) // high.denominator)
        return Interval(F(low_n, self.scale), F(high_n, self.scale))

    def _grid_domain(self, low, high):
        self.guard(low, high, self.scale)
        if max(abs(low.numerator).bit_length(), abs(high.numerator).bit_length()) + self.bits > self.operand_limit:
            raise ReferenceError("resource", "Reference endpoint grid exceeds operand limit")

    def _sum_enclosure(self, low, high):
        # Exact sums/differences of grid-aligned dyadics already have the same
        # outward endpoints. Omit both shifts, divisions and Fraction rebuilds;
        # retain the former grid's finite domain even for these avoided shifts.
        self.guard(low, high, self.scale)
        if all(value.denominator <= self.scale and
               not value.denominator & (value.denominator - 1) for value in (low, high)):
            self._grid_domain(low, high)
            return Interval(low, high)
        return self.grid(low, high)

    def interval(self, value):
        if isinstance(value, Interval):
            self.guard(value.lo, value.hi)
            return value
        return self.point(value)

    def add(self, a, b):
        a, b = self.interval(a), self.interval(b)
        self.tick()
        self.guard(a.lo, a.hi, b.lo, b.hi)
        if a.lo == a.hi == 0:
            return b
        if b.lo == b.hi == 0:
            return a
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "add")
            return self._sum_enclosure(value, value)
        return self._sum_enclosure(self.exact(a.lo, b.lo, "add"), self.exact(a.hi, b.hi, "add"))

    def neg(self, a):
        self.tick()
        a = self.interval(a)
        return Interval(-a.hi, -a.lo)

    def sub(self, a, b):
        a, b = self.interval(a), self.interval(b)
        self.tick()
        self.guard(a.lo, a.hi, b.lo, b.hi)
        if b.lo == b.hi == 0:
            return a
        if a.lo == a.hi == 0:
            return Interval(-b.hi, -b.lo)
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "sub")
            return self._sum_enclosure(value, value)
        return self._sum_enclosure(self.exact(a.lo, b.hi, "sub"), self.exact(a.hi, b.lo, "sub"))

    def _corner_domain(self, a, b, kind):
        """Retain all four old corner operand limits before selecting extrema.

        Sign monotonicity can omit interior products or quotients. It cannot
        let an omitted endpoint evade the original finite operand domain.
        These maxima are exactly the largest bit extents of the four old
        scalar preflights, with no integer product allocated here.
        """
        left, right = tuple(map(F, (a.lo, a.hi))), tuple(map(F, (b.lo, b.hi)))
        self.guard(*left, *right)
        an = max(abs(value.numerator).bit_length() for value in left)
        ad = max(value.denominator.bit_length() for value in left)
        bn = max(abs(value.numerator).bit_length() for value in right)
        bd = max(value.denominator.bit_length() for value in right)
        extent = max(an + bn, ad + bd) if kind == "mul" else max(an + bd, ad + bn)
        if extent > self.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")

    def mul(self, a, b):
        a, b = self.interval(a), self.interval(b)
        self.tick()
        self.guard(a.lo, a.hi, b.lo, b.hi)
        if a.lo == a.hi == 0 or b.lo == b.hi == 0:
            return Interval(F(0), F(0))
        if a.lo == a.hi == 1:
            return b
        if b.lo == b.hi == 1:
            return a
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "mul")
            return self.grid(value, value)
        self._corner_domain(a, b, "mul")
        if a.lo >= 0:
            if b.lo >= 0:
                pairs = ((a.lo, b.lo), (a.hi, b.hi))
            elif b.hi <= 0:
                pairs = ((a.hi, b.lo), (a.lo, b.hi))
            else:
                pairs = ((a.hi, b.lo), (a.hi, b.hi))
        elif a.hi <= 0:
            if b.lo >= 0:
                pairs = ((a.lo, b.hi), (a.hi, b.lo))
            elif b.hi <= 0:
                pairs = ((a.hi, b.hi), (a.lo, b.lo))
            else:
                pairs = ((a.lo, b.hi), (a.lo, b.lo))
        elif b.lo >= 0:
            pairs = ((a.lo, b.hi), (a.hi, b.hi))
        elif b.hi <= 0:
            pairs = ((a.hi, b.lo), (a.lo, b.lo))
        else:
            # Both intervals straddle zero: all four corners can determine
            # an extreme, so keep their complete original calculation.
            products = [self.exact(x, y, "mul") for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
            return self.grid(min(products), max(products))
        return self.grid(*(self.exact(x, y, "mul") for x, y in pairs))

    def div(self, a, b):
        a, b = self.interval(a), self.interval(b)
        if b.lo <= 0 <= b.hi:
            raise _Uncertain("Reference interval divisor contains zero")
        self.tick()
        self.guard(a.lo, a.hi, b.lo, b.hi)
        if a.lo == a.hi == 0:
            return a
        if b.lo == b.hi == 1:
            return a
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "div")
            return self.grid(value, value)
        self._corner_domain(a, b, "div")
        if b.lo > 0:
            if a.lo >= 0:
                pairs = ((a.lo, b.hi), (a.hi, b.lo))
            elif a.hi <= 0:
                pairs = ((a.lo, b.lo), (a.hi, b.hi))
            else:
                pairs = ((a.lo, b.lo), (a.hi, b.lo))
        elif a.lo >= 0:
            pairs = ((a.hi, b.hi), (a.lo, b.lo))
        elif a.hi <= 0:
            pairs = ((a.hi, b.lo), (a.lo, b.hi))
        else:
            pairs = ((a.hi, b.hi), (a.lo, b.hi))
        return self.grid(*(self.exact(x, y, "div") for x, y in pairs))

    def sqrt(self, value):
        value = self.interval(value)
        if value.lo < 0:
            raise _Uncertain("Reference radical is not certified nonnegative")
        result = []
        for endpoint in ((value.lo,) if value.lo == value.hi else (value.lo, value.hi)):
            self.tick()
            self.guard(value.lo, value.hi, self.scale)
            if abs(endpoint.numerator).bit_length() + 2 * self.bits > self.operand_limit:
                raise ReferenceError("resource", "Reference radical operand limit exceeded")
            scaled = (endpoint.numerator << (2 * self.bits)) // endpoint.denominator
            root = math.isqrt(scaled)
            low = F(root, self.scale)
            high = low if self.exact(low, low, "mul") == endpoint else F(root + 1, self.scale)
            result.append((low, high))
        return Interval(result[0][0], result[-1][1])

    def total(self, values):
        result = self.point(0)
        for value in values:
            result = self.add(result, value)
        return result

    def remember(self, key, value, *, admission=None):
        self.tick()
        self._sync_cache_operand_limit()
        if admission is not None and admission() is False:
            return value
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= MAX_CACHE:
            del self.cache[next(iter(self.cache))]
        self.cache[key] = value
        return value

    def lookup(self, key):
        """Reuse pure work within the same bounded independent context."""
        self.tick()
        self._sync_cache_operand_limit()
        value = self.cache.get(key)
        if value is not None:
            # Dictionary insertion order supplies bounded least-recent use;
            # no source state, allowance or external callback is cached.
            del self.cache[key]
            self.cache[key] = value
        return value

    def _atan_small(self, value):
        """Alternating atan series for an exact |x| <= 1/2, with next-term enclosure."""
        value = F(value)
        if value < 0:
            return self.neg(self._atan_small(-value))
        if value > F(1, 2):
            raise _Uncertain("Reference atan reduction did not reach its bounded series")
        square = self.exact(value, value, "mul")
        power, total = value, F(0)
        for k in range(self.bits + 8):
            term = self.exact(power, 2 * k + 1, "div")
            total = self.exact(total, term, "add" if k % 2 == 0 else "sub")
            power = self.exact(power, square, "mul")
            following = self.exact(power, 2 * k + 3, "div")
            if following < F(1, self._dyadic_denominator(self.bits + 8)):
                other = self.exact(total, following, "sub" if k % 2 == 0 else "add")
                return self.grid(min(total, other), max(total, other))
        raise _Uncertain("Finite reference atan series did not converge")

    def pi(self):
        key = ("pi", self.bits, self.operand_limit)
        cached = self.lookup(key)
        if cached is not None:
            return cached
        return self.remember(key, self.sub(self.mul(16, self._atan_small(F(1, 5))),
                                          self.mul(4, self._atan_small(F(1, 239)))))

    def _atan_point(self, value):
        if value < 0:
            return self.neg(self._atan_point(-value))
        if value > 1:
            return self.sub(self.div(self.pi(), 2), self._atan_point(self.exact(1, value, "div")))
        if value > F(1, 2):
            reduced = self.exact(self.exact(value, 1, "sub"), self.exact(value, 1, "add"), "div")
            return self.add(self.div(self.pi(), 4), self._atan_small(reduced))
        return self._atan_small(value)

    def atan(self, value):
        value = self.interval(value)
        low = self._atan_point(value.lo)
        high = low if value.lo == value.hi else self._atan_point(value.hi)
        return Interval(low.lo, high.hi)

    def atan2(self, y, x):
        y, x = self.interval(y), self.interval(x)
        if x.lo == x.hi == 0:
            if y.lo > 0:
                return self.div(self.pi(), 2)
            if y.hi < 0:
                return self.neg(self.div(self.pi(), 2))
            raise _Uncertain("Unresolved reference atan2 origin")
        if x.lo > 0:
            return self.atan(self.div(y, x))
        if x.hi < 0:
            base = self.atan(self.div(y, x))
            if y.lo >= 0:
                return self.add(base, self.pi())
            if y.hi <= 0:
                return self.sub(base, self.pi())
        if y.lo > 0:
            return self.sub(self.div(self.pi(), 2), self.atan(self.div(x, y)))
        if y.hi < 0:
            return self.sub(self.neg(self.div(self.pi(), 2)), self.atan(self.div(x, y)))
        raise _Uncertain("Reference atan2 quadrant is unresolved")

    def _series_integer(self, a, b, kind):
        """One charged integer operation with a prospective allocation guard."""
        self.tick()
        an, bn = abs(a).bit_length(), abs(b).bit_length()
        if kind == "shift":
            extent = an + b
        elif kind == "mul":
            extent = an + bn
        elif kind in ("add", "sub"):
            extent = max(an, bn) + 1
        elif kind in ("div", "divmod"):
            extent = max(an, bn)
        else:
            raise ValueError(kind)
        if max(an, bn, extent) > self.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        if kind == "shift":
            return a << b
        if kind == "mul":
            return a * b
        if kind == "add":
            return a + b
        if kind == "sub":
            return a - b
        return divmod(a, b) if kind == "divmod" else a // b

    def _series_factorials(self, last):
        key = ("series_factorials", self.operand_limit, last)
        cached = self.lookup(key)
        if cached is not None:
            return cached
        values = [1, 1]
        for factor in range(2, last + 1):
            values.append(self._series_integer(values[-1], factor, "mul"))
        return self.remember(key, tuple(values))

    def _series_coefficients(self, exponent, degree, factorials):
        """Build both exact factorial polynomials in two immutable integer lanes."""
        key = ("series_coefficients", self.operand_limit, exponent, degree)
        cached = self.lookup(key)
        if cached is not None:
            return cached
        common = factorials[2 * degree + 1]
        denominator = self._series_integer(common, 2 * exponent * degree, "shift")
        lane = self._series_integer(1, denominator.bit_length(), "shift")
        coefficients = []
        for index in range(degree + 1):
            odd = 2 * index + 1
            coefficient = (common if index == 0 else
                           self._series_integer(common, factorials[odd], "div"))
            if index != degree:
                coefficient = self._series_integer(coefficient, 2 * exponent * (degree - index), "shift")
            packed = self._series_integer(lane, odd, "add")
            if coefficient != 1:
                packed = self._series_integer(coefficient, packed, "mul")
            coefficients.append(packed)
        return self.remember(key, (tuple(coefficients), denominator, lane))

    def _series_dyadic(self, middle, squared):
        """Reproduce the adaptive Fraction series inside a proved integer domain.

        This is an independent midpoint/alternating-tail calculation. The
        production polynomial's degree, coefficients and error bound are not
        used. Outside the sufficient bound below the original recurrence runs.
        """
        self.tick()
        self.guard(middle, squared)
        denominator = middle.denominator
        limit = self.bits // 5 + 11
        if denominator & (denominator - 1) or not 1 <= limit <= 64:
            return None
        exponent = denominator.bit_length() - 1
        last = 2 * limit + 1
        # Every old term and partial sum has magnitude <= 1 and a reduced
        # denominator dividing (2L+1)! * d**(2L+1). Thus W bounds both reduced
        # widths, and 2W+1 dominates every old prospective Fraction preflight.
        # The extra 2e+5 covers packed multiply/subtract preflights; W+bits+11
        # covers the threshold shift. All final error/grid guards still run.
        width = last * exponent + last * last.bit_length() + 1
        if max(2 * width + 2 * exponent + 5, width + self.bits + 11) > self.operand_limit:
            return None
        if not middle:
            return F(0), F(1), F(0)
        factorials = self._series_factorials(last)
        power_base = squared.numerator
        threshold_bits = self.bits + 8
        growth = power_base.bit_length() - 2 * exponent

        # p < 2**bit_length(p) gives a sufficient, monotone upper bound for
        # the first accepted degree. Use only bit widths to locate it, then
        # exact comparisons below recover the original first strict stop.
        low, high = 1, limit
        while low < high:
            candidate = (low + high) // 2
            self.tick()
            if threshold_bits + growth * candidate < factorials[2 * candidate].bit_length():
                high = candidate
            else:
                low = candidate + 1
        degree = low
        self.tick()
        if threshold_bits + growth * degree >= factorials[2 * degree].bit_length():
            return None

        power, factor, remaining = 1, power_base, degree
        while remaining:
            if remaining & 1:
                power = self._series_integer(power, factor, "mul")
            remaining >>= 1
            if remaining:
                factor = self._series_integer(factor, factor, "mul")
        while degree > 1:
            previous = self._series_integer(power, power_base, "div")
            shift = 2 * exponent * (degree - 1) - threshold_bits
            if shift >= 0:
                numerator = previous
                bound = self._series_integer(factorials[2 * degree - 2], shift, "shift")
            else:
                numerator = self._series_integer(previous, -shift, "shift")
                bound = factorials[2 * degree - 2]
            self.tick()
            if numerator >= bound:
                break
            power, degree = previous, degree - 1

        coefficients, common_denominator, lane = self._series_coefficients(exponent, degree, factorials)
        packed = coefficients[-1]
        for coefficient in reversed(coefficients[:-1]):
            packed = self._series_integer(coefficient, self._series_integer(packed, power_base, "mul"), "sub")
        # For every partial Horner sum, both nonnegative lanes are no larger
        # than their constant coefficient; at the end they are <= Q < lane.
        # Consequently division extracts the two exact integer numerators.
        sine_numerator, cosine_numerator = self._series_integer(packed, lane, "divmod")
        sine_numerator = self._series_integer(middle.numerator, sine_numerator, "mul")
        sine_denominator = self._series_integer(common_denominator, exponent, "shift")
        tail_denominator = self._series_integer(factorials[2 * degree], 2 * exponent * degree, "shift")
        return (self.exact(sine_numerator, sine_denominator, "div"),
                self.exact(cosine_numerator, common_denominator, "div"),
                self.exact(power, tail_denominator, "div"))

    def _series_sincos(self, value):
        """Exact midpoint Taylor sums, with interval width and alternating tails.

        Both functions are globally 1-Lipschitz.  Evaluating one exact rational
        midpoint and adding its half-width is a rigorous interval calculation
        with far fewer repeated endpoint products than interval Horner powers.
        """
        value = self.interval(value)
        if value.magnitude > 1:
            raise _Uncertain("Reference sine reduction exceeds its proved range")
        middle = self.exact(self.exact(value.lo, value.hi, "add"), 2, "div")
        width = max(self.exact(middle, value.lo, "sub"), self.exact(value.hi, middle, "sub"))
        squared = self.exact(middle, middle, "mul")
        selected = self._series_dyadic(middle, squared)
        if selected is None:
            sine, cosine = middle, F(1)
            sine_term, cosine_term = middle, F(1)
            threshold = F(1, self._dyadic_denominator(self.bits + 8))
            for k in range(1, self.bits // 5 + 12):
                sine_term = -self.exact(self.exact(sine_term, squared, "mul"), (2 * k) * (2 * k + 1), "div")
                cosine_term = -self.exact(self.exact(cosine_term, squared, "mul"), (2 * k - 1) * (2 * k), "div")
                sine, cosine = self.exact(sine, sine_term, "add"), self.exact(cosine, cosine_term, "add")
                self.tick()
                tail = max(abs(sine_term), abs(cosine_term))
                if tail < threshold:
                    selected = sine, cosine, tail
                    break
            else:
                raise _Uncertain("Finite reference sine series did not converge")
        sine, cosine, tail = selected
        # For |middle| <= 1 each alternating series decreases in absolute
        # term size. The common current tail bounds the remainder; half-width
        # covers every input by the global 1-Lipschitz bound of both functions.
        error = self.exact(tail, width, "add")
        return (self.grid(self.exact(sine, error, "sub"), self.exact(sine, error, "add")),
                self.grid(self.exact(cosine, error, "sub"), self.exact(cosine, error, "add")))

    def sincos(self, value):
        value = self.interval(value)
        key = ("sincos", self.bits, self.operand_limit, value.lo, value.hi)
        cached = self.lookup(key)
        self.guard(value.lo, value.hi)
        if cached is not None:
            return cached
        if value.lo == value.hi == 0:
            return self.point(0), self.point(1)
        pi = self.pi()
        midpoint = self.exact(value.lo, value.hi, "add")
        quotient = self.exact(midpoint, self.exact(pi.lo, pi.hi, "add"), "div")
        self.tick()
        self.guard(quotient)
        # The fixed quadrant operation doubles the numerator and Fraction's
        # nearest-even conversion may double a division remainder. Check the
        # live domain after the callback, before either native allocation.
        if max(abs(quotient.numerator).bit_length(), quotient.denominator.bit_length()) + 1 > self.operand_limit:
            raise ReferenceError("resource", "Independent reference quadrant rounding exceeds operand limit")
        quadrant = round(quotient * 2)
        reduced = self.sub(value, self.mul(F(quadrant, 2), pi))
        sine, cosine = self._series_sincos(reduced)
        result = ((sine, cosine), (cosine, self.neg(sine)),
                  (self.neg(sine), self.neg(cosine)), (self.neg(cosine), sine))[quadrant % 4]
        return self.remember(key, result)

    def round64(self, value):
        """Use monotonic correctly rounded Fraction conversion to prove one cell."""
        value = self.interval(value)
        self.tick()
        self.guard(value.lo, value.hi)
        try:
            low, high = float(value.lo), float(value.hi)
        except OverflowError as error:
            raise ReferenceError("numeric", "Independent reference result exceeds binary64") from error
        if not math.isfinite(low) or not math.isfinite(high):
            raise ReferenceError("numeric", "Independent reference requires finite binary64")
        if low != high:
            raise _Uncertain("Reference enclosure crosses a binary64 rounding cell")
        return 0.0 if low == 0 else low


def _time_text(value):
    value = F(value)
    if value.denominator == 1:
        return str(value.numerator)
    # Exact clocks in this profile are dyadic and therefore have finite decimals.
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return str(value)
    places = max(twos, fives)
    scaled = abs(value.numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    digits = str(scaled).rjust(places + 1, "0")
    return ("-" if value < 0 else "") + (digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")


def _canonical_targets(payload, arithmetic):
    """Solve the defining signed-radical equations independently of production."""
    lengths = tuple(F(x) for x in payload.lengths_m)
    x, y, z = (F(v) for v in payload.target_m)
    a, b = lengths
    op = arithmetic.exact
    radius = op(op(x, x, "mul"), op(y, y, "mul"), "add")
    minimum = op(op(a, b, "sub"), op(a, b, "sub"), "mul")
    maximum = op(op(a, b, "add"), op(a, b, "add"), "mul")
    if z or radius < minimum or radius > maximum:
        raise ReferenceError("source_admission", "Independent reach is outside its exact annulus")
    if not radius:
        raise ReferenceError("source_admission", "Independent reach has a singular origin")
    if payload.branch not in {"elbow_positive", "elbow_negative"}:
        raise ReferenceError("source_admission", "Unknown independent reach branch")
    cosine = op(op(op(radius, op(a, a, "mul"), "sub"), op(b, b, "mul"), "sub"),
                op(op(2, a, "mul"), b, "mul"), "div")
    sign = 1 if payload.branch == "elbow_positive" else -1
    radical = op(1, op(cosine, cosine, "mul"), "sub")
    k = op(a, op(b, cosine, "mul"), "add")

    def radical_sign(constant, factor):
        # Sign of A+B*sqrt(r), including exact zeros, without a rounded
        # transcendental.  This prevents a true zero shoulder from becoming
        # an interval spanning many subnormal rounding cells.
        if not radical or not factor:
            return (constant > 0) - (constant < 0)
        if not constant or (constant > 0) == (factor > 0):
            return (factor > 0) - (factor < 0)
        squared = op(op(constant, constant, "mul"), op(op(factor, factor, "mul"), radical, "mul"), "sub")
        return ((constant > 0) - (constant < 0)) * ((squared > 0) - (squared < 0))

    shoulder_x = (op(x, k, "mul"), op(op(y, b, "mul"), sign, "mul"))
    shoulder_y = (op(y, k, "mul"), op(op(-x, b, "mul"), sign, "mul"))
    xsign, ysign = radical_sign(*shoulder_x), radical_sign(*shoulder_y)
    for precision in PRECISIONS:
        ar = _Arithmetic(arithmetic.work, arithmetic.check, bits=precision)
        try:
            if cosine == 1:
                elbow = ar.point(0)
            elif cosine == -1:
                elbow = ar.mul(sign, ar.pi())
            else:
                sine = ar.mul(sign, ar.sqrt(radical))
                elbow = ar.atan2(sine, cosine)
            root = ar.sqrt(radical)
            cartesian = []
            for (constant, factor), exact_sign in ((shoulder_x, xsign), (shoulder_y, ysign)):
                value = ar.point(0) if exact_sign == 0 else ar.add(constant, ar.mul(factor, root))
                if exact_sign and value.lo <= 0 <= value.hi:
                    raise _Uncertain("Reference signed radical needs refinement")
                cartesian.append(value)
            shoulder = ar.atan2(cartesian[1], cartesian[0])
            first, second = ar.round64(shoulder), ar.round64(elbow)
            if first == float(PI64):
                first = -float(PI64)
            if any(not low <= value <= high for value, (low, high) in zip((first, second), payload.limits_rad)):
                raise ReferenceError("source_admission", "Independent selected branch violates a closed limit")
            return (first, second)
        except _Uncertain:
            continue
    raise ReferenceError("numeric", "Finite independent admission could not establish canonical targets")


@dataclass(frozen=True)
class PoseEnclosure:
    position: tuple[Interval, ...]
    orientation: tuple[Interval, ...]
    velocity: tuple[Interval, ...]
    omega: tuple[Interval, ...]


@dataclass(frozen=True)
class RecordingPoseEnclosure:
    """Position/orientation only; no uncomputed derivative is exposed."""
    position: tuple[Interval, ...]
    orientation: tuple[Interval, ...]


@dataclass(frozen=True)
class CoordinatePath:
    joint: str
    action: str | None
    initial: F
    target: F
    local_elapsed_at_start: F
    duration: F | None
    slope: F
    actual_start: F
    actual_end: F
    ideal_initial: F
    ideal_start: F
    ideal_end: F
    actual_slope: F
    coordinate_error: F


@dataclass(frozen=True)
class ReferencePhase:
    start: F
    end: F
    carrier: str
    speed: F
    acceleration: F
    angular_speed: F
    coordinates: tuple[CoordinatePath, ...]
    root_position: tuple[Interval, ...]
    root_velocity: tuple[Interval, ...]
    root_acceleration: tuple[F, ...]
    root_orientation: tuple[Interval, ...]
    root_omega: tuple[Interval, ...]
    ideal_root_position: tuple[Interval, ...]
    ideal_root_velocity: tuple[Interval, ...]
    ideal_root_orientation: tuple[Interval, ...]
    ideal_root_omega: tuple[Interval, ...]
    offset_radius: F
    max_position_l1: F
    anchor_position_error: F
    anchor_rotation_error: F
    anchor_velocity_error: F
    anchor_angular_velocity_error: F
    source_numeric_position_error: F
    source_numeric_rotation_error: F
    source_numeric_velocity_error: F
    source_numeric_angular_velocity_error: F
    trig_count: int
    product_count: int
    vector_round_count: int
    coordinate_angle_error: F
    path: tuple[str, ...]


def build_reference(model, *, end, end_side="after", mode="recording", work=None, check=None):
    """Build a source-derived reference, sharing the caller's remaining work.

    ``work`` takes precedence over ``check`` to avoid charging the same request
    twice.  Supplying neither is an error: a verifier must not silently acquire
    another budget after compilation, source evaluation, or byte decoding.
    Explicit ``mode="observation"`` reconstructs requested source state without
    claiming complete H06 recording capacity; ``boundary_states`` is unavailable.
    """
    return ReachReference(model, end=F(end), end_side=end_side, mode=mode, arithmetic=_Arithmetic(work, check))


class _PoseArithmetic:
    def __init__(self, arithmetic):
        self.a = arithmetic

    def vector(self, value):
        if value is ZERO:
            key = self._key("zero_vector")
            cached = self.a.lookup(key)
            if cached is not None:
                return cached
            return self.a.remember(key, tuple(self.a.point(x) for x in ZERO))
        result = tuple(self.a.interval(x) for x in value)
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        return result

    @staticmethod
    def _zero(vector):
        return all(value.lo == value.hi == 0 for value in vector)

    def _key(self, operation, *values):
        return ("reference_pose", self.a.bits, self.a.operand_limit, operation, *values)

    def add(self, left, right):
        left, right = self.vector(left), self.vector(right)
        self.a.tick()
        self.a.guard(*(endpoint for vector in (left, right) for part in vector for endpoint in (part.lo, part.hi)))
        if self._zero(left):
            return right
        if self._zero(right):
            return left
        result = tuple(self.a.add(a, b) for a, b in zip(left, right))
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        return result

    def scale(self, vector, scalar):
        vector, scalar = self.vector(vector), self.a.interval(scalar)
        self.a.tick()
        self.a.guard(scalar.lo, scalar.hi, *(endpoint for part in vector for endpoint in (part.lo, part.hi)))
        if self._zero(vector) or scalar.lo == scalar.hi == 0:
            return (Interval(F(0), F(0)),) * len(vector)
        if scalar.lo == scalar.hi == 1:
            return vector
        result = tuple(self.a.mul(value, scalar) for value in vector)
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        return result

    def cross(self, a, b):
        a, b = self.vector(a), self.vector(b)
        self.a.tick()
        self.a.guard(*(endpoint for vector in (a, b) for part in vector for endpoint in (part.lo, part.hi)))
        if self._zero(a) or self._zero(b):
            return (Interval(F(0), F(0)),) * 3
        result = tuple(self.a.sub(self.a.mul(a[j], b[k]), self.a.mul(a[k], b[j]))
                       for j, k in ((1, 2), (2, 0), (0, 1)))
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        return result

    def norm(self, vector):
        # Squaring the whole interval loses correlation at zero; endpoint
        # squares supply the exact nonnegative range of each component.
        vector = self.vector(vector)
        key = self._key("norm", vector)
        cached = self.a.lookup(key)
        self.a.guard(*(endpoint for part in vector for endpoint in (part.lo, part.hi)))
        if cached is not None:
            return cached
        squares = []
        for value in vector:
            low = 0 if value.lo <= 0 <= value.hi else min(abs(value.lo), abs(value.hi))
            squares.append(Interval(self.a.exact(low, low, "mul"),
                                    self.a.exact(value.magnitude, value.magnitude, "mul")))
        return self.a.remember(key, self.a.sqrt(self.a.total(squares)))

    def quaternion(self, values):
        values = self.vector(values)
        key = self._key("quaternion", values)
        cached = self.a.lookup(key)
        self.a.guard(*(endpoint for part in values for endpoint in (part.lo, part.hi)))
        if cached is not None:
            return cached
        if len(values) == 4 and self._zero(values[1:]) and (values[0].lo > 0 or values[0].hi < 0):
            sign = F(1) if values[0].lo > 0 else F(-1)
            return self.a.remember(key, (Interval(sign, sign), *(Interval(F(0), F(0)),) * 3))
        denominator = self.norm(values)
        if denominator.lo <= 0:
            raise ReferenceError("numeric", "Independent quaternion normalization includes zero")
        return self.a.remember(key, tuple(self.a.div(value, denominator) for value in values))

    def multiply(self, left, right):
        a, b = left, right
        self.a.tick()
        self.a.guard(*(endpoint for values in (a, b) for part in values for endpoint in (part.lo, part.hi)))
        if all(value.lo == value.hi == expected for value, expected in zip(a, UNIT)):
            return b
        if all(value.lo == value.hi == expected for value, expected in zip(b, UNIT)):
            return a
        key = self._key("multiply", tuple(a), tuple(b))
        cached = self.a.lookup(key)
        self.a.guard(*(endpoint for values in (a, b) for part in values for endpoint in (part.lo, part.hi)))
        if cached is not None:
            return cached
        if self._zero((a[1], a[2], b[1], b[2])):
            # The exact Hamilton product of two world-Z representatives has
            # only scalar/Z components. Omit the twelve products proved zero;
            # interval-zero tests never treat an uncertain zero as exact.
            zero = self.a.point(0)
            return self.a.remember(key, (
                self.a.sub(self.a.mul(a[0], b[0]), self.a.mul(a[3], b[3])), zero, zero,
                self.a.add(self.a.mul(a[0], b[3]), self.a.mul(a[3], b[0]))))
        return self.a.remember(key, (
            self.a.sub(self.a.mul(a[0], b[0]), self.a.total(self.a.mul(a[i], b[i]) for i in (1, 2, 3))),
            self.a.total((self.a.mul(a[0], b[1]), self.a.mul(a[1], b[0]), self.a.mul(a[2], b[3]), self.a.neg(self.a.mul(a[3], b[2])))),
            self.a.total((self.a.mul(a[0], b[2]), self.a.neg(self.a.mul(a[1], b[3])), self.a.mul(a[2], b[0]), self.a.mul(a[3], b[1]))),
            self.a.total((self.a.mul(a[0], b[3]), self.a.mul(a[1], b[2]), self.a.neg(self.a.mul(a[2], b[1])), self.a.mul(a[3], b[0]))),
        ))

    def conjugate(self, q):
        self.a.guard(*(endpoint for part in q for endpoint in (part.lo, part.hi)))
        result = (q[0], *(self.a.neg(x) for x in q[1:]))
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        return result

    def rotate(self, q, vector):
        # Quaternion-vector multiplication follows a different arithmetic
        # expression from the source implementation's homogeneous matrix rows.
        vector = self.vector(vector)
        self.a.tick()
        self.a.guard(*(endpoint for values in (q, vector) for part in values for endpoint in (part.lo, part.hi)))
        if self._zero(vector):
            return vector
        if (len(q) == 4 and q[0].lo == q[0].hi and abs(q[0].lo) == 1
                and self._zero(q[1:])):
            return vector
        key = self._key("rotate", tuple(q), vector)
        cached = self.a.lookup(key)
        self.a.guard(*(endpoint for values in (q, vector) for part in values for endpoint in (part.lo, part.hi)))
        if cached is not None:
            return cached
        if self._zero((q[1], q[2])):
            # Expand q*(0,v)*conjugate(q) directly for scalar/Z q. This is
            # valid even for nonunit q: the Z component keeps w*w+z*z rather
            # than silently replacing it by one. No production rotation
            # matrix or homogeneous normalisation supplies this enclosure.
            factor_key = self._key("scalar_z_rotation_factors", tuple(q))
            factors = self.a.lookup(factor_key)
            if factors is None:
                ww, zz = self.a.mul(q[0], q[0]), self.a.mul(q[3], q[3])
                factors = (self.a.sub(ww, zz), self.a.mul(2, self.a.mul(q[0], q[3])),
                           self.a.add(ww, zz))
                self.a.remember(factor_key, factors)
            diagonal, off_diagonal, axis_scale = factors
            x, y, z = vector
            self.a.guard(*(endpoint for values in (q, vector, factors)
                           for part in values for endpoint in (part.lo, part.hi)))
            if z.lo == z.hi == 0 and y.lo == y.hi == 0:
                # An X-axis offset needs only the first two independently
                # derived Hamilton factors. Omit all products/sums of zero;
                # a unit offset can reuse the factors without any scaling.
                result = ((diagonal, off_diagonal, z) if x.lo == x.hi == 1 else
                          (self.a.mul(diagonal, x), self.a.mul(off_diagonal, x), z))
                self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
                return self.a.remember(key, result)
            if z.lo == z.hi == 0 and x.lo == x.hi == 0:
                first, second = ((off_diagonal, diagonal) if y.lo == y.hi == 1 else
                                 (self.a.mul(off_diagonal, y), self.a.mul(diagonal, y)))
                result = (self.a.neg(first), second, z)
                self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
                return self.a.remember(key, result)
            return self.a.remember(key, (
                self.a.sub(self.a.mul(diagonal, x), self.a.mul(off_diagonal, y)),
                self.a.add(self.a.mul(off_diagonal, x), self.a.mul(diagonal, y)),
                self.a.mul(axis_scale, z)))
        pure = (self.a.point(0), *vector)
        result = self.multiply(self.multiply(q, pure), self.conjugate(q))[1:]
        return self.a.remember(key, result)

    def spin(self, omega, elapsed):
        values = self.vector(omega)
        if not elapsed or all(value.lo == value.hi == 0 for value in values):
            return self.vector(UNIT)
        norm = self.norm(values)
        if norm.lo <= 0:
            raise ReferenceError("numeric", "Independent spin norm is unresolved")
        sine, cosine = self.a.sincos(self.a.mul(norm, F(elapsed) / 2))
        return (cosine, *(self.a.mul(self.a.div(value, norm), sine) for value in values))

    def _recording_rotate(self, q, vector):
        """Enclose an axis offset with one final grid per Hamilton factor.

        Recording poses need containment, so the exact square/product ranges
        can be combined before outward rounding. The ordinary pose operation
        retains its original cells. This path admits only small, native dyadic
        cells; that complete domain proves every omitted intermediate grid
        and the original corner preflights without trusting a producer pose.
        """
        def direct():
            return self.rotate(q, vector)

        requested = getattr(self.a.work, "max_operand_bits", MAX_OPERAND_BITS)
        if (type(requested) is not int or requested < MAX_OPERAND_BITS or self.a.bits != 128
                or self.a.work is None or not hasattr(self.a.work, "callback_error")
                or type(q) is not tuple or len(q) != 4 or type(vector) is not tuple or len(vector) != 3
                or any(type(cell) is not Interval or type(cell.lo) is not F or type(cell.hi) is not F
                       for cells in (q, vector) for cell in cells)):
            return direct()
        cells = (*q, *vector)
        # At most 131/129 bits at input, 262/258 at a product, 521/516
        # at a prospective difference and 649 after the final grid shift.
        # Original rounded factors and their possible axis scaling fit the
        # same <1024-bit envelope. Check sizes before ordering or arithmetic.
        if any(value.numerator.bit_length() > 131 or value.denominator.bit_length() > 129
               for cell in cells for value in (cell.lo, cell.hi)):
            return direct()
        if any(value.denominator > self.a.scale or value.denominator & (value.denominator - 1)
               for cell in cells for value in (cell.lo, cell.hi)):
            return direct()
        if (not self._zero((q[1], q[2], vector[2])) or self._zero(vector)
                or q[0].lo == q[0].hi and abs(q[0].lo) == 1 and self._zero(q[1:])):
            return direct()
        x, y, z = vector
        if y.lo == y.hi == 0:
            axis, scale = 0, x
        elif x.lo == x.hi == 0:
            axis, scale = 1, y
        else:
            return direct()
        cap = self.a.operand_limit

        def current():
            return self.a.operand_limit == cap

        def square(cell):
            if cell.lo == cell.hi:
                value = self.a.exact(cell.lo, cell.lo, "mul")
                return (value, value) if current() else None
            first = self.a.exact(cell.lo, cell.lo, "mul")
            if not current():
                return None
            last = self.a.exact(cell.hi, cell.hi, "mul")
            if not current():
                return None
            return ((F(0) if cell.lo <= 0 <= cell.hi else min(first, last)), max(first, last))

        def product(left, right):
            if left.lo == left.hi and right.lo == right.hi:
                value = self.a.exact(left.lo, right.lo, "mul")
                return (value, value) if current() else None
            if left.lo >= 0:
                pairs = (((left.lo, right.lo), (left.hi, right.hi)) if right.lo >= 0 else
                         ((left.hi, right.lo), (left.lo, right.hi)) if right.hi <= 0 else
                         ((left.hi, right.lo), (left.hi, right.hi)))
            elif left.hi <= 0:
                pairs = (((left.lo, right.hi), (left.hi, right.lo)) if right.lo >= 0 else
                         ((left.hi, right.hi), (left.lo, right.lo)) if right.hi <= 0 else
                         ((left.lo, right.hi), (left.lo, right.lo)))
            elif right.lo >= 0:
                pairs = ((left.lo, right.hi), (left.hi, right.hi))
            elif right.hi <= 0:
                pairs = ((left.hi, right.lo), (left.lo, right.lo))
            else:
                pairs = tuple((a, b) for a in (left.lo, left.hi) for b in (right.lo, right.hi))
            values = []
            for a, b in pairs:
                values.append(self.a.exact(a, b, "mul"))
                if not current():
                    return None
            return min(values), max(values)

        def calculate():
            self.a.tick()
            self.a.guard(*(value for cell in cells for value in (cell.lo, cell.hi)))
            if not current():
                return None
            key = self._key("recording_axis_rotation", q, vector)
            cached = self.a.lookup(key)
            if not current():
                return None
            if cached is not None:
                self.a.guard(*(value for cell in cached for value in (cell.lo, cell.hi)))
                return cached
            ww, zz = square(q[0]), None
            if ww is not None:
                zz = square(q[3])
            if zz is None:
                return None
            low = self.a.exact(ww[0], zz[1], "sub")
            if not current():
                return None
            high = self.a.exact(ww[1], zz[0], "sub")
            if not current():
                return None
            diagonal = self.a.grid(low, high)
            if not current():
                return None
            wz = product(q[0], q[3])
            if wz is None:
                return None
            low = self.a.exact(wz[0], 2, "mul")
            if not current():
                return None
            high = self.a.exact(wz[1], 2, "mul")
            if not current():
                return None
            off_diagonal = self.a.grid(low, high)
            if not current():
                return None
            if not scale.lo == scale.hi == 1:
                diagonal = self.a.mul(diagonal, scale)
                if not current():
                    return None
                off_diagonal = self.a.mul(off_diagonal, scale)
                if not current():
                    return None
            if axis:
                off_diagonal = self.a.neg(off_diagonal)
                if not current():
                    return None
            result = (diagonal, off_diagonal, z) if not axis else (off_diagonal, diagonal, z)
            self.a.guard(*(value for cell in result for value in (cell.lo, cell.hi)))
            self.a.remember(key, result, admission=current)
            return result if current() else None

        try:
            result = calculate()
        except ReferenceError as error:
            if error.code != "resource" or error is getattr(self.a.work, "callback_error", None):
                raise
            try:
                changed = not current()
            except ReferenceError:
                raise error
            if not changed:
                raise
            result = None
        # Keep the original calculation's own failure outside the retry
        # handler, including when a later callback could broaden its domain.
        return direct() if result is None else result

    def _recording_rotate_sincos(self, old_sine, old_cosine, sine, cosine, *, shared=False):
        """Round one independent complex interval update only at its outputs.

        Exact product extrema are added/subtracted before the two outward
        grids. Omitting the four intermediate grids gives a contained valid
        enclosure, without a producer value, floating operation or slack.
        A small complete dyadic domain proves every original preflight.
        """
        def direct():
            return (self.a.add(self.a.mul(old_sine, cosine), self.a.mul(old_cosine, sine)),
                    self.a.sub(self.a.mul(old_cosine, cosine), self.a.mul(old_sine, sine)))

        values = (old_sine, old_cosine, sine, cosine)
        requested = getattr(self.a.work, "max_operand_bits", MAX_OPERAND_BITS)
        if (type(requested) is not int or requested < MAX_OPERAND_BITS or self.a.bits != 128
                or self.a.work is None or not hasattr(self.a.work, "callback_error")
                or any(type(value) is not Interval or type(value.lo) is not F or type(value.hi) is not F
                       for value in values)):
            return direct()
        # Prove widths before lattice arithmetic, ordering or product selection.
        # Products need <=262/258 numerator/denominator bits; the largest
        # prospective sum/grid width is <=649. The original rounded path
        # and all comparison cross-products fit this same <1024-bit domain.
        if any(value.numerator.bit_length() > 131 or value.denominator.bit_length() > 129
               for cell in values for value in (cell.lo, cell.hi)):
            return direct()
        if any(value.denominator > self.a.scale or value.denominator & (value.denominator - 1)
               for cell in values for value in (cell.lo, cell.hi)):
            return direct()
        if any(value.lo > value.hi or value.lo == value.hi and value.lo in (F(-1), F(0), F(1))
               for value in values):
            # The ordinary zero/unit shortcuts are already less work.
            return direct()
        cap = self.a.operand_limit

        def product(a, b):
            if a.lo == a.hi and b.lo == b.hi:
                value = self.a.exact(a.lo, b.lo, "mul")
                return (value, value) if self.a.operand_limit == cap else None
            if a.lo >= 0:
                pairs = (((a.lo, b.lo), (a.hi, b.hi)) if b.lo >= 0 else
                         ((a.hi, b.lo), (a.lo, b.hi)) if b.hi <= 0 else
                         ((a.hi, b.lo), (a.hi, b.hi)))
            elif a.hi <= 0:
                pairs = (((a.lo, b.hi), (a.hi, b.lo)) if b.lo >= 0 else
                         ((a.hi, b.hi), (a.lo, b.lo)) if b.hi <= 0 else
                         ((a.lo, b.hi), (a.lo, b.lo)))
            elif b.lo >= 0:
                pairs = ((a.lo, b.hi), (a.hi, b.hi))
            elif b.hi <= 0:
                pairs = ((a.hi, b.lo), (a.lo, b.lo))
            else:
                pairs = tuple((x, y) for x in (a.lo, a.hi) for y in (b.lo, b.hi))
            endpoints = []
            for x, y in pairs:
                endpoints.append(self.a.exact(x, y, "mul"))
                if self.a.operand_limit != cap:
                    return None
            return (min(endpoints), max(endpoints)) if len(endpoints) == 4 else tuple(endpoints)

        def calculate():
            self.a.tick()
            self.a.guard(*(value for cell in values for value in (cell.lo, cell.hi)))
            if self.a.operand_limit != cap:
                return None
            if shared:
                # The exact interval update depends only on its four cells.
                # Broad recording batches may share that completed arithmetic
                # while each source path keeps its own phase/clock cursor.
                key = self._key("recording_interval_rotation", *values)
                cached = self.a.lookup(key)
                if self.a.operand_limit != cap:
                    return None
                if cached is not None:
                    self.a.guard(*(endpoint for cell in cached for endpoint in (cell.lo, cell.hi)))
                    return cached
            result = []
            for first, second, operation in ((old_sine, old_cosine, "add"),
                                             (old_cosine, old_sine, "sub")):
                left = product(first, cosine)
                if left is None:
                    return None
                right = product(second, sine)
                if right is None:
                    return None
                low = self.a.exact(left[0], right[0 if operation == "add" else 1], operation)
                if self.a.operand_limit != cap:
                    return None
                high = self.a.exact(left[1], right[1 if operation == "add" else 0], operation)
                if self.a.operand_limit != cap:
                    return None
                result.append(self.a.grid(low, high))
                if self.a.operand_limit != cap:
                    return None
            result = tuple(result)
            if shared:
                result = self.a.remember(key, result)
                if self.a.operand_limit != cap:
                    return None
            return result

        try:
            result = calculate()
        except ReferenceError as error:
            if error.code != "resource" or error is getattr(self.a.work, "callback_error", None):
                raise
            try:
                changed = self.a.operand_limit != cap
            except ReferenceError:
                raise error
            if not changed:
                raise
            result = None
        # The original fallback is outside the added calculation's handler;
        # its own failure can never be retried into a later broader domain.
        return direct() if result is None else result

    def _recording_sincos(self, coordinate, *, context, clock, shared=False):
        """Enclose successive point angles without a production error model.

        Only the explicit recording path supplies this cursor context. Its
        values live in the existing bounded arithmetic cache; a missing entry,
        changed phase/context, rewind or long run starts with the independent
        direct series again. Full source observations never enter this path.
        """
        def direct():
            return self.a.sincos(self.a.div(coordinate, 2))
        limit = self.a.operand_limit
        if (type(coordinate.lo) is not F or type(coordinate.hi) is not F or
                coordinate.lo != coordinate.hi or self.a.bits != 128 or
                limit != MAX_OPERAND_BITS or self.a.work is None or
                not hasattr(self.a.work, "callback_error")):
            return direct()
        key = self._key("recording_sincos", context)
        previous = self.a.lookup(key)
        clock = F(clock)
        self.a.guard(coordinate.lo, coordinate.hi, clock)
        if self.a.operand_limit != limit:
            return direct()
        steps, advance = 0, False
        if previous is not None:
            old_clock, old_coordinate, old_sine, old_cosine, steps = previous
            self.a.guard(old_clock, old_coordinate, old_sine.lo, old_sine.hi,
                         old_cosine.lo, old_cosine.hi)
            # This sufficient bound admits both exact delta preflights, the
            # final endpoint shift and the clock comparison before allocating
            # their products. Larger inputs retain the original direct path.
            extent = max(max(abs(value.numerator).bit_length(), value.denominator.bit_length())
                         for value in (coordinate.lo, old_coordinate, clock, old_clock))
            advance = (extent <= (limit - self.a.bits - 4) // 2 and
                       old_clock < clock and steps < 64)
        if advance:
            try:
                delta = self.a.exact(self.a.exact(coordinate.lo, old_coordinate, "sub"), 2, "div")
                if abs(delta) <= F(1, 4):
                    delta_cell = self.a.grid(delta, delta)
                else:
                    advance = False
            except ReferenceError as error:
                # A narrowing callback can make this extra delta operation
                # fail even when the original direct half-angle still fits.
                # Only our own changed-domain admission failure may retry;
                # the shared work's exact callback exception must escape.
                if error.code != "resource" or self.a.work.callback_error is error:
                    raise
                try:
                    changed = self.a.operand_limit != limit
                except ReferenceError:
                    raise error
                if not changed:
                    raise
                return direct()
            if advance:
                # Only added delta construction belongs to the retry above.
                # A direct trigonometric or interval fallback failure keeps
                # its identity even if a later callback would widen the cap.
                sine, cosine = self.a.sincos(delta_cell)
                result = (self._recording_rotate_sincos(old_sine, old_cosine, sine, cosine, shared=True)
                          if shared else self._recording_rotate_sincos(old_sine, old_cosine, sine, cosine))
                steps += 1
        if not advance:
            result, steps = direct(), 0
        # A callback can narrow the domain during any component operation.
        # Such a call must return to the direct current-domain proof, never
        # publish an accumulated broader-domain enclosure under a new cap.
        if self.a.operand_limit != limit:
            return direct()
        self.a.guard(*(endpoint for part in result for endpoint in (part.lo, part.hi)))
        self.a.remember(key, (clock, coordinate.lo, *result, steps))
        if self.a.operand_limit != limit:
            return direct()
        return result

    def _recording_repeated_increment(self, receipt, rate, elapsed):
        """Read one complete pure increment from an already admitted cursor.

        The cursor lookup and publication are still charged. Equal exact rate
        and elapsed operands need no new multiply, divide, grid or sin/cos
        lookup. Retain every original prospective width proof before using
        the completed cells; no source clock, witness or orientation is
        supplied by this receipt. Its Fraction endpoints are immutable and
        share the cursor's existing bounded cache slot.
        """
        if (self.a.bits != 128 or self.a.operand_limit != MAX_OPERAND_BITS or
                type(rate) is not F or type(elapsed) is not F or
                type(receipt) is not tuple or len(receipt) != 10 or
                any(type(value) is not F for value in receipt) or
                receipt[:2] != (rate, elapsed)):
            return None
        _, _, product, delta, low, high, sine_low, sine_high, cosine_low, cosine_high = receipt
        self.a.guard(*receipt)
        rn, rd = abs(rate.numerator).bit_length(), rate.denominator.bit_length()
        en, ed = abs(elapsed.numerator).bit_length(), elapsed.denominator.bit_length()
        pn, pd = abs(product.numerator).bit_length(), product.denominator.bit_length()
        # These are exactly the omitted rate*elapsed and product/2 preflights.
        if max(rn + en, rd + ed, pn + 1, pd + 2) > self.a.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        self.a._grid_domain(delta, delta)
        self.a.guard(low, high, sine_low, sine_high, cosine_low, cosine_high)
        return Interval(sine_low, sine_high), Interval(cosine_low, cosine_high)

    def _recording_body_orientation(self, direct, *, axis, rate, witness, context, clock, shared=False,
                                    source_admission=None, source_records=0, return_advance=False):
        """Advance an independently proved constant body-axis orientation.

        The caller supplies only its own ideal source proof and a context-free
        independent seed. Two complex interval products are exactly the right
        Hamilton product by the Cartesian increment. No production quaternion,
        derivative, numeric allowance or sampled agreement enters this proof.
        """
        def direct_result():
            result = direct()
            if source_admission is not None:
                for _ in range(source_records):
                    self.a.tick()
                source_admission()
                self.a.guard(*(endpoint for cell in result for endpoint in (cell.lo, cell.hi)))
            return (result, False) if return_advance else result

        limit = self.a.operand_limit
        if (self.a.bits != 128 or limit != MAX_OPERAND_BITS or self.a.work is None
                or not hasattr(self.a.work, "callback_error") or type(rate) is not F
                or axis not in (0, 1, 2) or type(axis) is not int or type(witness) is not tuple):
            return direct_result()
        key = self._key("recording_body_orientation", context)
        previous = self.a.lookup(key)
        clock = F(clock)
        self.a.guard(rate, clock)
        if self.a.operand_limit != limit:
            return direct_result()
        # The optional delta has at most 3076-bit prospective operands on this
        # sufficient domain. Other clocks/rates keep the ordinary source path.
        if any(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 1024
               for value in (rate, clock)):
            return direct_result()
        steps, advance, increment = 0, False, None
        if previous is not None:
            old_witness, old_axis, old_rate, old_clock, old_rotation, old_increment, steps = previous
            self.a.guard(old_rate, old_clock,
                         *(endpoint for cell in old_rotation for endpoint in (cell.lo, cell.hi)))
            advance = (old_witness == witness and old_axis == axis and old_rate == rate and
                       old_clock < clock and steps < 64 and
                       all(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 1024
                           for value in (old_clock, *(endpoint for cell in old_rotation
                                                       for endpoint in (cell.lo, cell.hi)))))
        if advance:
            if rate:
                try:
                    elapsed = self.a.exact(clock, old_clock, "sub")
                    if self.a.operand_limit != limit:
                        advance = False
                    else:
                        reused_increment = self._recording_repeated_increment(old_increment, rate, elapsed)
                        if reused_increment is None:
                            product = self.a.exact(rate, elapsed, "mul")
                            delta = self.a.exact(product, 2, "div")
                            if self.a.operand_limit != limit:
                                advance = False
                            elif abs(delta) <= F(1, 4):
                                delta_cell = self.a.grid(delta, delta)
                            else:
                                advance = False
                except ReferenceError as error:
                    if error.code != "resource" or self.a.work.callback_error is error:
                        raise
                    try:
                        changed = self.a.operand_limit != limit
                    except ReferenceError:
                        raise error
                    if not changed:
                        raise
                    advance = False
                if self.a.operand_limit != limit:
                    return direct_result()
                if advance:
                    # Keep all original transcendental and interval fallback
                    # failures outside the added delta's retry handler.
                    if reused_increment is None:
                        sine, cosine = self.a.sincos(delta_cell)
                        increment = (rate, elapsed, product, delta, delta_cell.lo, delta_cell.hi,
                                     sine.lo, sine.hi, cosine.lo, cosine.hi)
                    else:
                        sine, cosine = reused_increment
                        increment = old_increment
                    result = list(old_rotation)
                    for first, second in (((1, 0), (2, 3)), ((2, 0), (3, 1)),
                                          ((3, 0), (1, 2)))[axis]:
                        if self.a.operand_limit != limit:
                            return direct_result()
                        self.a.guard(sine.lo, sine.hi, cosine.lo, cosine.hi,
                                     *(endpoint for index in (first, second)
                                       for endpoint in (old_rotation[index].lo, old_rotation[index].hi)))
                        if self._zero((old_rotation[first], old_rotation[second])):
                            continue
                        result[first], result[second] = self._recording_rotate_sincos(
                            old_rotation[first], old_rotation[second], sine, cosine, shared=shared)
                    result = tuple(result)
            else:
                # Nonzero source contributions may cancel exactly. The
                # complete ideal world quaternion is then constant.
                result = old_rotation
            if advance:
                steps += 1
        if not advance:
            result, steps, increment = direct(), 0, None
        if self.a.operand_limit != limit:
            return direct_result()
        self.a.guard(*(endpoint for cell in result for endpoint in (cell.lo, cell.hi)))
        # Charge each bounded source-record recheck before the atomic final
        # admission. The hook runs after the insertion's own callback, with
        # no later callback before mutation, so a changed source never
        # publishes a mismatched witness/seed pair.
        for _ in range(source_records):
            self.a.tick()
        def admit():
            if self.a.operand_limit != limit:
                return False
            if source_admission is not None:
                source_admission()
            self.a.guard(*(endpoint for cell in result for endpoint in (cell.lo, cell.hi)))
            return True
        self.a.remember(key, (witness, axis, rate, clock, result, increment, steps), admission=admit)
        if self.a.operand_limit != limit:
            return direct_result()
        return (result, advance) if return_advance else result

    def _normalized_axis(self, axis):
        """Reuse the unchanged independent axis enclosure across hinge clocks."""
        key = self._key("normalized_axis", axis)
        value = self.a.lookup(key)
        self.a.guard(*(endpoint for part in axis for endpoint in (part.lo, part.hi)))
        if value is None:
            norm = self.norm(axis)
            value = tuple(self.a.div(part, norm) for part in axis)
            self.a.guard(*(endpoint for part in value for endpoint in (part.lo, part.hi)))
            self.a.remember(key, value)
        self.a.guard(*(endpoint for part in value for endpoint in (part.lo, part.hi)))
        return value

    def hinge(self, axis, coordinate, rate, *, ideal=False, recording_context=None, recording_time=None,
              shared_recording=False):
        axis = self.vector(axis)
        coordinate, rate = self.a.interval(coordinate), self.a.interval(rate)
        key = self._key("hinge", axis, coordinate, rate, ideal)
        if recording_context is not None:
            key += (recording_context, recording_time)
        cached = self.a.lookup(key)
        self.a.guard(coordinate.lo, coordinate.hi, rate.lo, rate.hi,
                     *(endpoint for part in axis for endpoint in (part.lo, part.hi)))
        if cached is not None:
            return cached
        normalized_axis = self._normalized_axis(axis)
        if recording_context is None:
            sine, cosine = self.a.sincos(self.a.div(coordinate, 2))
        else:
            context = (recording_context, axis)
            sine, cosine = (self._recording_sincos(coordinate, context=context, clock=recording_time, shared=True)
                            if shared_recording else self._recording_sincos(coordinate, context=context, clock=recording_time))
        rotation = (cosine, *(self.a.mul(value, sine) for value in normalized_axis))
        # The rotation's mathematical derivative uses a unit axis. The
        # inherited source inspection deliberately retains the canonical raw
        # axis, whose small norm defect is covered by the independent basis.
        omega = self.scale(normalized_axis if ideal else axis, rate)
        return self.a.remember(key, self.make(orientation=rotation, omega=omega, normalized=True))

    def make(self, position=ZERO, orientation=UNIT, velocity=ZERO, omega=ZERO, *, normalized=False):
        result = PoseEnclosure(self.vector(position), self.vector(orientation) if normalized else self.quaternion(orientation),
                               self.vector(velocity), self.vector(omega))
        self.a.guard(*(endpoint for values in (result.position, result.orientation, result.velocity, result.omega)
                       for part in values for endpoint in (part.lo, part.hi)))
        return result

    def identity(self):
        key = self._key("identity")
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.make())

    def constant(self, pose):
        key = self._key("constant", tuple(pose.position), tuple(pose.rotation))
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.make(pose.position, pose.rotation))

    def _identity_composition(self, parent, local):
        """Apply exact identity algebra after compose's charged lookup.

        Every component is admitted in the callback's current domain. Other
        shapes execute the original helpers, including their coercion/errors.
        This returns an existing immutable pose, with no new proof cache.
        """
        vectors = []
        for pose in (parent, local):
            if type(pose) is not PoseEnclosure:
                return None
            for values, size in ((pose.position, 3), (pose.orientation, 4),
                                 (pose.velocity, 3), (pose.omega, 3)):
                if (type(values) is not tuple or len(values) != size or
                        any(type(value) is not Interval or type(value.lo) is not F or type(value.hi) is not F
                            for value in values)):
                    return None
                vectors.append(values)
        def identity(pose):
            return (self._zero(pose.position) and self._zero(pose.velocity) and self._zero(pose.omega) and
                    all(value.lo == value.hi == expected for value, expected in zip(pose.orientation, UNIT)))
        if identity(parent):
            result = local
        elif identity(local):
            result = parent
        else:
            return None
        self.a.guard(*(endpoint for values in vectors for value in values for endpoint in (value.lo, value.hi)))
        return result

    def compose(self, parent, local, *, recording=False):
        key = self._key("recording_compose" if recording else "compose", parent, local)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        direct = self._identity_composition(parent, local)
        if direct is not None:
            return direct
        offset = (self._recording_rotate(parent.orientation, local.position) if recording else
                  self.rotate(parent.orientation, local.position))
        position = self.add(parent.position, offset)
        orientation = self.multiply(parent.orientation, local.orientation)
        rates = (parent.velocity, parent.omega, local.velocity, local.omega)
        if all(len(vector) == 3 and self._zero(vector) for vector in rates):
            # Every cross-product and rotated rate in the spatial derivative
            # equations is exactly zero, even for a nonunit raw quaternion.
            # An interval merely containing zero never takes this path.
            return self.a.remember(key, PoseEnclosure(position, orientation, parent.velocity, parent.omega))
        return self.a.remember(key, PoseEnclosure(position, orientation,
                             self.add(self.add(parent.velocity, self.cross(parent.omega, offset)),
                                      self.rotate(parent.orientation, local.velocity)),
                             self.add(parent.omega, self.rotate(parent.orientation, local.omega))))

    def _recording_sequential_domain(self, *vectors):
        """Admit immutable small cells before omitting per-result memoization."""
        return (self.a.bits == 128 and self.a.operand_limit == MAX_OPERAND_BITS and
                self.a.work is not None and hasattr(self.a.work, "callback_error") and
                all(type(values) is tuple and
                    all(type(cell) is Interval and type(cell.lo) is F and type(cell.hi) is F and
                        all(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 256
                            for value in (cell.lo, cell.hi)) for cell in values)
                    for values in vectors))

    def _recording_sequential_multiply(self, left, right):
        """Use the same scalar/Z Hamilton cells without a one-use cache entry.

        Small recording walks advance these operands at each clock. Retaining
        their completed products displaces the useful body cursors. Every
        performed scalar operation keeps the ordinary kernel and guard; only
        the unused lookup/insertion and a fresh exact-zero cell are omitted.
        """
        if (not self._recording_sequential_domain(left, right) or
                len(left) != 4 or len(right) != 4 or
                not self._zero((left[1], left[2], right[1], right[2]))):
            return self.multiply(left, right)
        self.a.tick()
        self.a.guard(*(endpoint for values in (left, right) for cell in values
                       for endpoint in (cell.lo, cell.hi)))
        if self.a.operand_limit != MAX_OPERAND_BITS:
            return self.multiply(left, right)
        if all(cell.lo == cell.hi == expected for cell, expected in zip(left, UNIT)):
            return right
        if all(cell.lo == cell.hi == expected for cell, expected in zip(right, UNIT)):
            return left
        zero = left[1]
        result = (
            self.a.sub(self.a.mul(left[0], right[0]), self.a.mul(left[3], right[3])), zero, zero,
            self.a.add(self.a.mul(left[0], right[3]), self.a.mul(left[3], right[0])))
        self.a.guard(*(endpoint for cell in result for endpoint in (cell.lo, cell.hi)))
        # A changed cap replays the original expression. Its failures are not
        # caught and cannot be retried after a later broadening callback.
        return (result if self.a.operand_limit == MAX_OPERAND_BITS else
                self.multiply(left, right))

    def _recording_sequential_compose(self, parent, local, *, recording=False):
        """Keep exact pose composition while declining one-use pose entries."""
        if type(parent) is not PoseEnclosure or type(local) is not PoseEnclosure:
            return self.compose(parent, local, recording=recording)
        vectors = tuple(values for pose in (parent, local) for values in
                        (pose.position, pose.orientation, pose.velocity, pose.omega))
        if (not self._recording_sequential_domain(*vectors) or
                any(len(values) != size for values, size in zip(vectors, (3, 4, 3, 3) * 2)) or
                not all(self._zero(values) for values in
                        (parent.velocity, parent.omega, local.velocity, local.omega))):
            return self.compose(parent, local, recording=recording)
        # This admission replaces compose's cache lookup. There is no new
        # retained pose, cache capacity, source state, or cursor authority.
        self.a.tick()
        self.a.guard(*(endpoint for values in vectors for cell in values
                       for endpoint in (cell.lo, cell.hi)))
        if self.a.operand_limit != MAX_OPERAND_BITS:
            return self.compose(parent, local, recording=recording)
        direct = self._identity_composition(parent, local)
        if direct is not None:
            return direct
        offset = (self._recording_rotate(parent.orientation, local.position) if recording else
                  self.rotate(parent.orientation, local.position))
        position = self.add(parent.position, offset)
        orientation = self._recording_sequential_multiply(parent.orientation, local.orientation)
        result = PoseEnclosure(position, orientation, parent.velocity, parent.omega)
        self.a.guard(*(endpoint for values in (result.position, result.orientation, result.velocity, result.omega)
                       for cell in values for endpoint in (cell.lo, cell.hi)))
        return (result if self.a.operand_limit == MAX_OPERAND_BITS else
                self.compose(parent, local, recording=recording))

    def inverse(self, pose):
        key = self._key("inverse", pose)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        orientation = self.conjugate(pose.orientation)
        return self.a.remember(key, self.make(self.rotate(orientation, tuple(self.a.neg(x) for x in pose.position)),
                                             orientation, normalized=True))


@dataclass
class _Action:
    status: str = "pending"
    elapsed: F = F(0)
    since: F = F(0)
    started: F | None = None
    initial: object = None
    ideal_initial: object = None
    targets: tuple[float, float] | None = None
    terminal: dict | None = None
    rotation_error: F = F(0)

    def elapsed_at(self, time):
        return self.elapsed + (time - self.since if self.status == "running" else 0)


@dataclass
class _Anchor:
    time: F
    since: F
    actual: PoseEnclosure
    ideal: PoseEnclosure
    position_error: F = F(0)
    rotation_error: F = F(0)
    velocity_error: F = F(0)
    omega_error: F = F(0)
    source_time: F | None = None


@dataclass
class _ForceHistory:
    active: dict = field(default_factory=dict)
    net: tuple = (0.0, 0.0, 0.0)
    acceleration: tuple | None = None
    ideal_acceleration: tuple | None = None
    started: int = 0
    completed: int = 0
    last_time: F | None = None
    changes: list = field(default_factory=list)


@dataclass
class _State:
    modes: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    orientations: dict = field(default_factory=dict)
    ideal_positions: dict = field(default_factory=dict)
    ideal_orientations: dict = field(default_factory=dict)
    coordinates: dict = field(default_factory=dict)
    ideal_coordinates: dict = field(default_factory=dict)
    actions: dict = field(default_factory=dict)
    claims: dict = field(default_factory=dict)
    grips: set = field(default_factory=set)
    dynamic: dict = field(default_factory=dict)
    forces: dict = field(default_factory=dict)
    impulses: dict = field(default_factory=dict)
    rotation_errors: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _SourceBound:
    extent: F = F(0)
    offset: F = F(0)
    trig: int = 0
    products: int = 0
    vectors: int = 0
    coordinate: F = F(0)
    anchor_position: F = F(0)
    anchor_rotation: F = F(0)
    position_error: F = F(0)
    rotation_error: F = F(0)
    velocity_error: F = F(0)
    omega_error: F = F(0)
    speed: F = F(0)
    acceleration: F = F(0)
    omega: F = F(0)
    alpha: F = F(0)
    actual_speed: F = F(0)
    actual_omega: F = F(0)


_SOURCE_BOUND_FIELDS = tuple(_SourceBound.__dataclass_fields__)


@dataclass(frozen=True)
class _AxialDerivative:
    """Ideal translational bounds and one constant body-frame angular rate."""
    speed: F
    acceleration: F
    axis: int | None
    rate: F


@dataclass(frozen=True)
class _RecordingBodyRate:
    """A source-derived constant body rate and its fresh ancestry witness."""
    axis: int | None
    rate: F
    moving: bool
    witness: tuple
    path: str
    direct: object
    receipts: tuple
    zero_origin: bool = False
    identity_relative: bool = False


@dataclass(frozen=True)
class _RecordingSourceReceipt:
    """An ephemeral getter plus the immutable source operands it admitted."""
    read: object
    values: tuple


def _plain(value, arithmetic):
    arithmetic.tick()
    if value is None or isinstance(value, (str, bool, int, float, F, Interval)):
        return value
    if is_dataclass(value):
        return {entry.name: _plain(getattr(value, entry.name), arithmetic) for entry in fields(value)}
    if isinstance(value, dict):
        return {key: _plain(item, arithmetic) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item, arithmetic) for item in value]
    raise ReferenceError("unsupported", "Independent reference encountered an unsupported source record",
                         value_type=type(value).__name__)


class ReachReference:
    """A bounded event ledger plus independent mathematical pose evaluation.

    The captured model is private.  Returned phase records are frozen and all
    returned source projections are fresh values, so consumer changes cannot
    alter later independent expectations.
    """
    def __init__(self, model, *, end, arithmetic, end_side="after", mode="recording"):
        if (model.profile != "planar-reach-0.1" or end < 0 or end > model.duration
                or end_side not in ("before", "after") or mode not in ("recording", "observation")):
            raise ReferenceError("unsupported", "Independent reference requires a valid planar reach prefix")
        self.a, self.p = arithmetic, _PoseArithmetic(arithmetic)
        self.end, self.end_side, self.mode = end, end_side, mode
        self.model = copy.copy(model)
        for name in ("objects", "sites", "joints", "follows", "actions", "source_provenance"):
            collection = getattr(model, name)
            captured = {}
            for key, value in collection.items():
                arithmetic.tick()
                captured[key] = copy.deepcopy(value)
            setattr(self.model, name, captured)
        self.model.events = []
        for block in model.events:
            arithmetic.tick()
            self.model.events.append(copy.deepcopy(block))
        self.model.events.sort(key=lambda block: block.time)
        self._incoming_graph_identity = object()
        self._targets, self._poses, self._phase_cache, self._basis_cache = {}, {}, {}, {}
        self._numeric_cache_limit = self.a.operand_limit
        self._state, self._records, self._before, self._after = _State(), [], [], []
        self._times, self._release_records = [], {}
        self._event_index = 0
        self._initialize()
        self._reach_history_weight = self._maximum_reach_weight() if mode == "recording" else None
        self._inherited_history_cache = {}
        self._history_weight = 0
        self._geometry = self._capture_geometry() if mode == "recording" else None
        self._build()
        self.boundaries = tuple(self._times)

    def _sync_numeric_cache(self):
        limit = self.a.operand_limit
        if self._numeric_cache_limit != limit:
            self.a.tick()
            self._targets.clear()
            self._poses.clear()
            self._phase_cache.clear()
            self._basis_cache.clear()
            self._numeric_cache_limit = self.a.operand_limit
        return self._numeric_cache_limit

    def _capture_geometry(self):
        return tuple({"path": path, "element_id": list(obj.element_id), "owner": obj.owner,
                      "geometry": _plain(obj.geometry, self.a), "appearance": list(obj.appearance),
                      "physical": _plain(obj.physical, self.a), "placement": _plain(obj.placement, self.a)}
                     for path, obj in self.model.objects.items())

    def _geometry_values(self):
        self.a.tick()
        if self._geometry is None:
            self._geometry = self._capture_geometry()
        return self._geometry

    @property
    def geometry_expectations(self):
        return copy.deepcopy(self._geometry_values())

    def _initialize(self):
        state = self._state
        for path, obj in self.model.objects.items():
            self.a.tick()
            state.modes[path] = obj.motion
            state.positions[path] = self.p.vector(obj.placement.position)
            state.orientations[path] = self.p.quaternion(obj.placement.rotation)
            state.ideal_positions[path] = state.positions[path]
            state.ideal_orientations[path] = state.orientations[path]
            state.rotation_errors[path] = F(0)
            state.forces[path] = _ForceHistory(acceleration=tuple(self.model.gravity) if obj.motion == "dynamic" else None,
                ideal_acceleration=tuple(F(x) for x in self.model.gravity) if obj.motion == "dynamic" else None)
            state.impulses[path] = {"applied_count": 0, "last_application_time_seconds": None, "last_applications": []}
            if obj.motion == "dynamic":
                pose = self.p.make(obj.placement.position, obj.placement.rotation, obj.velocity, obj.omega)
                state.dynamic[path] = _Anchor(F(0), F(0), pose, pose)
        for path, joint in self.model.joints.items():
            self.a.tick()
            if joint.initial is not None:
                state.coordinates[path] = joint.initial
                state.ideal_coordinates[path] = F(joint.initial)
            if joint.kind == "grip":
                state.grips.add(path)
        state.actions = {path: _Action() for path in self.model.actions}
        for action in self.model.actions.values():
            if action.kind == "reach_planar":
                self._validate_chain(action)

    def _validate_chain(self, action):
        self.a.tick()
        payload = action.reach
        shoulder, elbow = (self.model.joints[path] for path in (payload.shoulder, payload.elbow))
        parent, upper, hinge, forearm, tip = (self.model.sites[path] for path in
            (shoulder.parent, shoulder.child, elbow.parent, elbow.child, payload.tip))
        identity = (1.0, 0.0, 0.0, 0.0)
        conditions = (
            shoulder.kind == elbow.kind == "hinge", shoulder.axis == elbow.axis == (0.0, 0.0, 1.0),
            len({parent.owner, upper.owner, forearm.owner}) == 3, upper.owner == hinge.owner,
            forearm.owner == tip.owner, upper.pose.position == forearm.pose.position == (0.0, 0.0, 0.0),
            upper.pose.rotation == hinge.pose.rotation == forearm.pose.rotation == tip.pose.rotation == identity,
            hinge.pose.position[1:] == tip.pose.position[1:] == (0.0, 0.0),
            tuple(payload.lengths_m) == (hinge.pose.position[0], tip.pose.position[0]),
            tuple(payload.limits_rad) == (shoulder.limits, elbow.limits),
            payload.base_frame == shoulder.parent + ".frame" == payload.target_frame,
        )
        if not all(conditions):
            raise ReferenceError("source_identity", "Independent source geometry does not establish the claimed planar chain")

    def _copy_state(self, state):
        # Account for the actual retained state closure before allocating it.
        entries = (len(state.modes) * 11 + len(state.coordinates) + len(state.claims)
                   + len(state.actions) * 9 + sum(len(x.active) + len(x.changes) for x in state.forces.values()))
        if entries * (len(self._times) + 1) > 100000:
            raise ReferenceError("resource", "Independent reference retained-state limit exceeded")
        for _ in range(entries):
            self.a.tick()
        return copy.deepcopy(state)

    def _coordinate_boundary_plan(self, time):
        """Identify writes before allocating a boundary's private state.

        Coordinate lifecycle changes cannot alter object roots, modes, grips,
        anchors, impulses or forces. All other transitions take the complete
        copy path. The completion scan is the ordinary boundary scan, retained
        here rather than repeated after allocation.
        """
        self.a.tick()
        state = self._state
        coordinate_only = not state.dynamic
        completions, changed = [], set()
        writes_coordinates = False
        for path, active in state.actions.items():
            self.a.tick()
            if active.status == "running" and active.elapsed_at(time) == self.model.actions[path].duration:
                completions.append(path)
                changed.add(path)
                writes_coordinates = True
                if self.model.actions[path].kind not in {"reach_planar", "tween"}:
                    coordinate_only = False
        if (coordinate_only and self._event_index < len(self.model.events)
                and self.model.events[self._event_index].time == time):
            for event in self.model.events[self._event_index].events:
                self.a.tick()
                action = self.model.actions.get(event.target)
                if (event.kind not in {"start", "pause", "resume", "stop"} or action is None
                        or action.kind not in {"reach_planar", "tween"}):
                    coordinate_only = False
                    break
                changed.add(event.target)
                writes_coordinates |= event.kind == "stop"
        return completions, coordinate_only, changed, writes_coordinates

    def _copy_coordinate_state(self, state, changed, writes_coordinates):
        """Copy the actual coordinate writes, retaining immutable prior roots."""
        self.a.tick()
        # Without dynamic objects there has been no release or force history:
        # this language has no transition back from dynamic to prescribed.
        # Preserve the original logical retained-state limit even when a
        # boundary can share all or part of its predecessor's physical storage.
        entries = (len(state.modes) * 11 + len(state.coordinates) + len(state.claims)
                   + len(state.actions) * 9)
        if entries * (len(self._times) + 1) > 100000:
            raise ReferenceError("resource", "Independent reference retained-state limit exceeded")
        if not changed:
            return state
        result = copy.copy(state)
        result.actions = {}
        for path, active in state.actions.items():
            # A changed action gets a private complete record. Unchanged
            # records are immutable until a later transition copies them.
            for _ in range(9 if path in changed else 1):
                self.a.tick()
            result.actions[path] = copy.deepcopy(active) if path in changed else active
        result.claims = {}
        for key, owner in state.claims.items():
            self.a.tick()
            result.claims[key] = owner
        if writes_coordinates:
            for name in ("coordinates", "ideal_coordinates"):
                values = {}
                for key, value in getattr(state, name).items():
                    self.a.tick()
                    values[key] = value
                setattr(result, name, values)
        return result

    def _incoming(self, state):
        # Captured joints/follows never change. Only the current grip set
        # selects relations, including while a boundary stages a release.
        # Charge and capture that set, then share only the immutable relation
        # map in the existing bounded cache. A private token isolates models
        # even if two references intentionally share one arithmetic context.
        grips = []
        for path in state.grips:
            self.a.tick()
            grips.append(path)
        grips = frozenset(grips)
        key = ("incoming_graph", self._incoming_graph_identity, grips)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        result = {}
        for path, joint in self.model.joints.items():
            self.a.tick()
            if joint.kind != "grip" or path in grips:
                result[self.model.sites[joint.child].owner] = ("joint", path)
        for path, follow in self.model.follows.items():
            self.a.tick()
            result[follow.child] = ("follow", path)
        return self.a.remember(key, MappingProxyType(result))

    def _owner(self, frame):
        if frame == "world":
            return None
        path = frame.removesuffix(".frame")
        return path if path in self.model.objects else self.model.sites[path].owner

    def _channel(self, action):
        return (action.target, {"move": "translation", "spin": "orientation", "tween": "coordinate"}[action.kind])

    def _coordinate(self, joint, time, state, *, ideal=False):
        self.a.tick()
        owner = state.claims.get((joint, "coordinate"))
        if owner is None:
            return F((state.ideal_coordinates if ideal else state.coordinates)[joint]), F(0)
        action, active = self.model.actions[owner], state.actions[owner]
        index = (action.reach.shoulder, action.reach.elbow).index(joint) if action.kind == "reach_planar" else None
        start = active.ideal_initial if ideal else active.initial
        initial = F(start[index] if index is not None else start)
        target = F(active.targets[index] if index is not None else action.goal)
        # Only the exact affine slope is constant. Decode and guard the source
        # operands on every call; an equal law from another action or state
        # may share this immutable scalar, never its clock or running status.
        self.a.guard(initial, target)
        an, ad = abs(target.numerator).bit_length(), target.denominator.bit_length()
        bn, bd = abs(initial.numerator).bit_length(), initial.denominator.bit_length()
        if max(max(an + bd, bn + ad) + 1, ad + bd) > self.a.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        duration = F(action.duration)
        self.a.guard(duration)
        if not duration:
            raise _Uncertain("Reference division includes zero")
        if initial == target:
            # The affine law is exactly constant. Preserve the original
            # subtraction preflight above, zero/duration division domain,
            # zero*elapsed domain and initial+zero domain before omitting
            # their numeric operations. The observed clock and final binary64
            # projection remain current; no source value or clock is cached.
            if max(duration.denominator.bit_length(), 1 + abs(duration.numerator).bit_length()) > self.a.operand_limit:
                raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
            elapsed = F(active.elapsed_at(time))
            self.a.guard(elapsed)
            if max(abs(elapsed.numerator).bit_length(), 1 + elapsed.denominator.bit_length(),
                   max(an + 1, ad) + 1, ad + 1) > self.a.operand_limit:
                raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
            coordinate = initial if ideal else F(self.a.round64(initial))
            return coordinate, F(0)
        key = ("coordinate_affine_law", self.a.operand_limit, initial, target, duration)
        slope = self.a.lookup(key)
        missing = slope is None
        if missing:
            slope = self.a.exact(self.a.exact(target, initial, "sub"), duration, "div")
        coordinate = self.a.exact(initial, self.a.exact(slope, active.elapsed_at(time), "mul"), "add")
        if not ideal:
            coordinate = F(self.a.round64(coordinate))
        if missing:
            # A failed coordinate projection or cancellation publishes no law
            # from this sample. All reused values remain pure exact numbers.
            self.a.remember(key, slope)
        return coordinate, slope if active.status == "running" else F(0)

    def _prescribed_root_translation(self, path, time, state, *, ideal, pose_only):
        """The unchanged prescribed translation, independent of root orientation."""
        position = (state.ideal_positions if ideal else state.positions)[path]
        velocity, omega = self.p.vector(ZERO), self.p.vector(ZERO)
        move = state.claims.get((path, "translation"))
        if move is not None:
            action, active = self.model.actions[move], state.actions[move]
            initial = active.ideal_initial if ideal else active.initial
            position = self.p.add(initial, self.p.scale(action.vector, active.elapsed_at(time)))
            if not pose_only and active.status == "running":
                velocity = self.p.vector(action.vector)
        return position, velocity, omega

    def _root_pose(self, path, time, state, *, ideal, pose_only=False):
        if state.modes[path] == "dynamic":
            anchor = state.dynamic[path]
            saved = anchor.ideal if ideal else anchor.actual
            dt = time - anchor.time
            acceleration = ((state.forces[path].ideal_acceleration if ideal else state.forces[path].acceleration)
                            or self.model.gravity)
            position = self.p.add(self.p.add(saved.position, self.p.scale(saved.velocity, dt)),
                                  self.p.scale(acceleration, dt * dt / 2))
            rotation = self.p.multiply(self.p.spin(saved.omega, dt), saved.orientation)
            if pose_only:
                zero = self.p.vector(ZERO)
                return PoseEnclosure(position, rotation, zero, zero)
            return PoseEnclosure(position, rotation, self.p.add(saved.velocity, self.p.scale(acceleration, dt)), saved.omega)
        orientation = (state.ideal_orientations if ideal else state.orientations)[path]
        position, velocity, omega = self._prescribed_root_translation(
            path, time, state, ideal=ideal, pose_only=pose_only)
        spin = state.claims.get((path, "orientation"))
        if spin is not None:
            action, active = self.model.actions[spin], state.actions[spin]
            initial = active.ideal_initial if ideal else active.initial
            orientation = self.p.multiply(self.p.spin(action.vector, active.elapsed_at(time)), initial)
            if not pose_only and active.status == "running":
                omega = self.p.vector(action.vector)
        return PoseEnclosure(position, orientation, velocity, omega)

    def _recording_body_domain(self):
        return (self.a.bits == 128 and self.a.operand_limit == MAX_OPERAND_BITS and
                self.a.work is not None and hasattr(self.a.work, "callback_error"))

    def _recording_source_witness(self, *values):
        """Admit one bounded source record without retaining a second cache.

        Only immutable, small, typed source leaves enter a cursor receipt.
        This is a fresh structural admission, not an arithmetic result. Every
        subsequent exact rate/delta operation still uses charged arithmetic.
        """
        # Callers charge BEFORE capturing this immutable tuple. This helper
        # itself must not introduce a callback between capture and admission.
        if len(values) > 16:
            return None

        def admitted(value, depth=0):
            if value is None or type(value) is str:
                return True
            if type(value) is F:
                return max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 1024
            if type(value) is int:
                return abs(value).bit_length() <= 1024
            if type(value) is float:
                return math.isfinite(value)
            if type(value) is Interval:
                return (type(value.lo) is F and type(value.hi) is F and
                        admitted(value.lo, depth) and admitted(value.hi, depth))
            return (type(value) is tuple and depth < 3 and len(value) <= 8 and
                    all(admitted(item, depth + 1) for item in value))

        return values if all(admitted(value) for value in values) else None

    def _recording_admit_receipts(self, receipts):
        """Recheck captured operands after the last callback, without a new one."""
        def guard(value):
            if type(value) is F:
                self.a.guard(value)
            elif type(value) is int:
                self.a.guard(F(value))
            elif type(value) is float and self.a.operand_limit < 1075:
                self.a.guard(F(value))
            elif type(value) is Interval:
                self.a.guard(value.lo, value.hi)
            elif type(value) is tuple:
                for part in value:
                    guard(part)

        for receipt in receipts:
            try:
                current = receipt.read()
            except (KeyError, AttributeError, IndexError) as error:
                raise ReferenceError("identity", "Independent source changed during recording proof") from error
            if self._recording_source_witness(*current) is None:
                raise ReferenceError("identity", "Independent source changed during recording proof")
            guard(current)
            guard(receipt.values)
            if current != receipt.values:
                raise ReferenceError("identity", "Independent source changed during recording proof")

    def _recording_capture(self, read):
        self.a.tick()
        if not self._recording_body_domain():
            return None
        values = read()
        witness = self._recording_source_witness(*values)
        return None if witness is None else _RecordingSourceReceipt(read, witness)

    def _recording_proof_narrowed(self, error):
        """Only an added proof's own changed-domain refusal may fall back."""
        if error.code != "resource" or self.a.work.callback_error is error:
            return False
        try:
            return self.a.operand_limit != MAX_OPERAND_BITS
        except ReferenceError:
            return False

    def _recording_root_body(self, path, state):
        def read():
            action_path = state.claims.get((path, "orientation"))
            head = ("root", path, state.modes[path], state.ideal_orientations[path], action_path)
            if action_path is None:
                return head
            action, active = self.model.actions[action_path], state.actions[action_path]
            return (*head, action.kind, action.vector, active.ideal_initial, active.status,
                    active.elapsed, active.since, active.rotation_error)
        receipt = self._recording_capture(read)
        if receipt is None or receipt.values[2] == "dynamic":
            return None
        witness = receipt.values
        if witness[4] is None:
            orientation = witness[3]
            def direct(clock):
                self.a.tick()
                self.a.guard(*(endpoint for cell in orientation for endpoint in (cell.lo, cell.hi)))
                return orientation
            return _RecordingBodyRate(None, F(0), False, witness, path + ".frame", direct, (receipt,))
        kind, raw_vector, initial, status, elapsed, since, rotation_error = witness[5:]
        if kind != "spin" or type(raw_vector) is not tuple or len(raw_vector) != 3:
            return None
        def direct(clock):
            active_elapsed = (self.a.exact_sum(elapsed, self.a.exact(clock, since, "sub"))
                              if status == "running" else elapsed)
            return self.p.multiply(self.p.spin(raw_vector, active_elapsed), initial)
        if status != "running":
            return _RecordingBodyRate(None, F(0), False, witness, path + ".frame", direct, (receipt,))
        try:
            vector = tuple(F(value) for value in raw_vector)
            self.a.guard(*vector, rotation_error)
            nonzero = tuple(index for index, value in enumerate(vector) if value)
            if not nonzero:
                return _RecordingBodyRate(None, F(0), False, witness, path + ".frame", direct, (receipt,))
            if len(nonzero) != 1 or rotation_error:
                return None
            axis = nonzero[0]
            if max(abs(vector[axis].numerator).bit_length(), vector[axis].denominator.bit_length()) > 1024:
                return None
            sign = self._axis_transport(initial, axis)
            if sign is None or not self._recording_body_domain():
                return None
            rate = vector[axis] if sign == 1 else self.a.exact(F(0), vector[axis], "sub")
        except ReferenceError as error:
            if not self._recording_proof_narrowed(error):
                raise
            return None
        return (_RecordingBodyRate(axis, rate, bool(rate), witness, path + ".frame", direct, (receipt,))
                if self._recording_body_domain() else None)

    def _recording_fixed_sign(self, rotation, axis):
        if (type(rotation) is tuple and len(rotation) == 4 and
                all(type(part) in (int, float, F) for part in rotation)):
            zero = tuple(part == 0 for part in rotation)
            return (1 if not all(zero) and all(zero[index + 1] for index in range(3) if index != axis)
                    else -1 if not all(zero) and zero[0] and zero[axis + 1] else None)
        return self._axis_transport(rotation, axis)

    def _recording_fixed_orientation(self, parent, rotation, *, inverse=False):
        """Omit a fixed positive scalar quaternion's exact identity product."""
        self.a.tick()
        if (type(rotation) is tuple and len(rotation) == 4 and
                all(type(part) in (int, float, F) for part in rotation) and
                all(type(part) is not float or math.isfinite(part) for part in rotation)):
            self.a.guard(*rotation,
                         *(endpoint for cell in parent for endpoint in (cell.lo, cell.hi)))
            if rotation[0] > 0 and all(part == 0 for part in rotation[1:]):
                # Independent quaternion normalization maps this exact raw
                # operand to +1. Its conjugate is also +1; neither operation
                # nor a Hamilton product needs to be constructed.
                return parent
        fixed = self.p.quaternion(rotation)
        if inverse:
            fixed = self.p.conjugate(fixed)
        return self.p.multiply(parent, fixed)

    def _recording_attached_body(self, parent, attachment, *, path):
        if parent is None:
            return None
        kind, relation = attachment
        def read():
            if kind == "site":
                site = self.model.sites[relation]
                return (kind, relation, site.owner + ".frame", site.pose.position, site.pose.rotation)
            if kind == "follow":
                follow = self.model.follows[relation]
                return (kind, relation, follow.parent, follow.offset.position, follow.offset.rotation,
                        follow.child + ".frame")
            joint = self.model.joints[relation]
            child = self.model.sites[joint.child]
            pose = child.pose
            return (kind, relation, joint.parent + ".frame", pose.position, pose.rotation,
                    joint.kind, joint.child, child.owner + ".frame")
        receipt = self._recording_capture(read)
        if receipt is None:
            return None
        values = receipt.values
        if (values[2] != parent.path or (kind == "follow" and values[5] != path) or
                (kind == "static_joint" and (values[5] not in {"slider", "fixed", "grip"} or values[7] != path))):
            return None
        rotation = values[4]
        def direct(clock):
            return self._recording_fixed_orientation(parent.direct(clock), rotation,
                                                      inverse=kind == "static_joint")
        try:
            self.a.guard(parent.rate)
            sign = 1 if not parent.rate else self._recording_fixed_sign(rotation, parent.axis)
            if sign is None or not self._recording_body_domain():
                return None
            rate = parent.rate if sign == 1 else self.a.exact(F(0), parent.rate, "sub")
        except ReferenceError as error:
            if not self._recording_proof_narrowed(error):
                raise
            return None
        return (_RecordingBodyRate(parent.axis, rate, parent.moving, (parent.witness, values),
                                   path, direct, (*parent.receipts, receipt))
                if self._recording_body_domain() else None)

    def _recording_coordinate_recipe(self, relation, state):
        def read():
            owner = state.claims.get((relation, "coordinate"))
            if owner is None:
                return relation, None, state.ideal_coordinates[relation]
            action, active = self.model.actions[owner], state.actions[owner]
            axes = ((action.reach.shoulder, action.reach.elbow) if action.kind == "reach_planar" else None)
            return (relation, owner, action.kind, action.target, axes, action.duration, action.goal,
                    active.ideal_initial, active.targets, active.status, active.elapsed, active.since)
        receipt = self._recording_capture(read)
        if receipt is None:
            return None
        values = receipt.values
        if values[1] is None:
            initial = F(values[2])
            def direct(clock):
                self.a.guard(initial)
                return initial
            return F(0), direct, receipt
        _, _, kind, _, axes, duration, goal, start, targets, status, elapsed, since = values
        if kind not in {"reach_planar", "tween"}:
            return None
        index = axes.index(relation) if kind == "reach_planar" else None
        initial = F(start[index] if index is not None else start)
        target = F(targets[index] if index is not None else goal)
        self.a.guard(initial, target)
        # Preserve the original affine law's subtraction preflight, including
        # on a hit. Its immutable numeric cache is shared, not its source clock.
        an, ad = abs(target.numerator).bit_length(), target.denominator.bit_length()
        bn, bd = abs(initial.numerator).bit_length(), initial.denominator.bit_length()
        if max(max(an + bd, bn + ad) + 1, ad + bd) > self.a.operand_limit:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        duration = F(duration)
        self.a.guard(duration)
        if not duration:
            raise _Uncertain("Reference division includes zero")
        if initial == target:
            # Admission above still checks both the original subtraction
            # preflight and nonzero duration. The exact slope is then zero,
            # so there is no subtraction/division or numeric lookup to perform.
            slope = F(0)
        else:
            key = ("coordinate_affine_law", self.a.operand_limit, initial, target, duration)
            slope = self.a.lookup(key)
            if slope is None:
                slope = self.a.exact(self.a.exact(target, initial, "sub"), duration, "div")
                self.a.remember(key, slope)
        self.a.guard(initial, slope, elapsed, since)
        def direct(clock):
            if not slope and self._recording_body_domain():
                self.a.tick()
                values = tuple(F(value) for value in (initial, elapsed, since, clock))
                self.a.guard(*values)
                if (self._recording_body_domain() and
                        all(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 1024
                            for value in values)):
                    # Even with unrelated denominators, the original elapsed
                    # subtraction/sum and zero affine products fit below 4099
                    # bits on this sufficient domain. The result is initial.
                    # Current source receipts are still admitted atomically by
                    # the enclosing body proof after its final callback.
                    return initial
            active_elapsed = (self.a.exact_sum(elapsed, self.a.exact(clock, since, "sub"))
                              if status == "running" else elapsed)
            return self.a.exact(initial, self.a.exact(slope, active_elapsed, "mul"), "add")
        return slope if status == "running" else F(0), direct, receipt

    def _recording_hinge_body(self, parent, relation, state, *, path):
        if parent is None:
            return None
        def read():
            joint = self.model.joints[relation]
            child = self.model.sites[joint.child]
            return (joint.path, joint.kind, joint.parent, joint.child, joint.axis,
                    child.owner + ".frame", child.pose.position, child.pose.rotation)
        receipt = self._recording_capture(read)
        if receipt is None:
            return None
        values = receipt.values
        _, kind, parent_site, _, raw_axis, child_path, position, rotation = values
        if (kind != "hinge" or parent_site + ".frame" != parent.path or child_path != path
                or type(raw_axis) is not tuple or len(raw_axis) != 3):
            return None
        nonzero = tuple(index for index, value in enumerate(raw_axis) if value)
        if len(nonzero) != 1 or abs(raw_axis[nonzero[0]]) != 1:
            return None
        axis = nonzero[0]
        if parent.rate and parent.axis != axis:
            return None
        # This recipe uses the original affine subtraction/division kernels.
        # Their failures must escape; only arithmetic introduced for the
        # optional body-rate combination belongs in its changed-cap fallback.
        coordinate = self._recording_coordinate_recipe(relation, state)
        if coordinate is None or not self._recording_body_domain():
            return None
        rate, coordinate_at, coordinate_receipt = coordinate
        try:
            self.a.guard(rate, parent.rate)
            if any(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 1024
                   for value in (rate, parent.rate)):
                return None
            local_rate = rate if not rate or raw_axis[axis] == 1 else self.a.exact(F(0), rate, "sub")
            combined = (local_rate if not parent.rate else parent.rate if not local_rate else
                        self.a.exact(parent.rate, local_rate, "add"))
            if not self._recording_body_domain():
                return None
            sign = 1 if not combined else self._recording_fixed_sign(rotation, axis)
            if sign is None or not self._recording_body_domain():
                return None
            if sign == -1:
                combined = self.a.exact(F(0), combined, "sub")
        except ReferenceError as error:
            if not self._recording_proof_narrowed(error):
                raise
            return None
        if (not self._recording_body_domain() or
                max(abs(combined.numerator).bit_length(), combined.denominator.bit_length()) > 1024):
            return None
        def direct(clock):
            local = self.p.hinge(raw_axis, coordinate_at(clock), F(0), ideal=True).orientation
            result = self.p.multiply(parent.direct(clock), local)
            return self._recording_fixed_orientation(result, rotation, inverse=True)
        zero_origin = (type(position) is tuple and len(position) == 3 and
                       all(type(part) in (int, float, F) and part == 0 for part in position))
        law = coordinate_receipt.values
        if law[1] is None:
            zero_coordinate = law[2] == 0
        else:
            # The captured recipe already admitted these exact source values,
            # its original affine preflight and the nonzero duration. Requiring
            # BOTH endpoints to be zero proves the whole local angle is zero,
            # including a paused law; a zero sampled slope alone does not.
            index = law[4].index(relation) if law[2] == "reach_planar" else None
            start = law[7][index] if index is not None else law[7]
            target = law[8][index] if index is not None else law[6]
            zero_coordinate = start == target == 0
        identity_relative = (zero_origin and zero_coordinate and
            type(rotation) is tuple and len(rotation) == 4 and
            all(type(part) in (int, float, F) for part in rotation) and
            all(type(part) is not float or math.isfinite(part) for part in rotation) and
            rotation[0] > 0 and all(part == 0 for part in rotation[1:]))
        return _RecordingBodyRate(axis, combined, parent.moving or bool(rate),
                                  (parent.witness, values, coordinate_receipt.values), path, direct,
                                  (*parent.receipts, receipt, coordinate_receipt), zero_origin, identity_relative)

    def _recording_identity_parent(self, parent, body):
        """Reuse an admitted complete pose through an exact identity hinge.

        The source recipe remains unchanged for direct or narrow-domain
        fallback. This full-domain path only omits a second world trajectory
        whose complete relative transform has been proved exactly +identity.
        No source receipt, numeric cache or exposed field is borrowed implicitly.
        """
        if not body.identity_relative or not self._recording_body_domain():
            return None
        if type(parent) is not PoseEnclosure:
            return None
        vectors = (parent.position, parent.orientation, parent.velocity, parent.omega)
        if any(type(values) is not tuple or len(values) != size or
               any(type(cell) is not Interval or type(cell.lo) is not F or type(cell.hi) is not F
                   for cell in values) for values, size in zip(vectors, (3, 4, 3, 3))):
            return None
        # All current ancestry checks remain charged, even though there is no
        # new cursor to look up or publish. After their last callback the full
        # receipt chain and every returned field are admitted without another
        # callback. A changed domain takes the original immutable seed path.
        for _ in body.receipts:
            self.a.tick()
            if not self._recording_body_domain():
                return None
        self._recording_admit_receipts(body.receipts)
        self.a.guard(*(endpoint for values in vectors for cell in values for endpoint in (cell.lo, cell.hi)))
        return parent

    def _pose_map(self, time, state, *, ideal, pose_only=False, selected=None, recording_context=None,
                  recording_seed=False):
        if recording_context is not None and not (pose_only and ideal):
            raise ValueError("Independent recording recurrence requires ideal recording poses")
        if recording_seed and (recording_context is not None or not (pose_only and ideal)):
            raise ValueError("Independent recording seeds require context-free ideal recording poses")
        key = (id(state), time, ideal, pose_only)
        if recording_context is not None:
            key += (recording_context,)
        targets = (tuple(path + ".frame" for path in (*self.model.objects, *self.model.sites))
                   if selected is None else tuple(selected))
        # Equal independent curves can share a completed interval update in
        # broad batches while retaining each path's own context and clock.
        shared_recording = recording_context is not None and len(targets) > 16
        self.a.tick()
        limit = self._sync_numeric_cache()
        body_recording = recording_context is not None and self._recording_body_domain()
        # Recording walks re-admit their actual source witnesses. In
        # particular, a prior complete frame map must not bypass a changed
        # action/attachment receipt at the same explicit recording clock.
        cached = self._poses.get(key) if not (body_recording or recording_seed) else None
        if cached is not None and cached[0] is state:
            frames = cached[1]
            if all(path in frames for path in targets):
                return frames
        else:
            frames = {"world": self.p.identity()}
        incoming = self._incoming(state)
        visiting = set()
        # Only a lineage actually advanced by a world recording cursor may
        # use narrower composition cells. Cold seeds and ordinary/unsupported
        # graphs retain their exact original cells. This per-walk set stores
        # path flags only; every pose remains in the existing frame map.
        advanced_frames = set()
        body_rates = {"world": _RecordingBodyRate(None, F(0), False, ("world",), "world",
                                                 lambda clock: self.p.identity().orientation, ())}

        def compose(parent, local, advanced):
            # Preserve the ordinary two-operand composition interface for
            # context-free walks and their independently supplied oracles.
            # Only an actually advanced recording lineage selects the
            # optional narrower offset enclosure.
            if advanced and recording_context is not None and not shared_recording:
                return self.p._recording_sequential_compose(parent, local, recording=advanced)
            if advanced:
                return self.p.compose(parent, local, recording=True)
            return self.p.compose(parent, local)

        def frame(path):
            self.a.tick()
            if path in frames:
                return frames[path]
            advanced = False
            stem = path.removesuffix(".frame")
            if stem in self.model.sites:
                site = self.model.sites[stem]
                parent = frame(site.owner + ".frame")
                advanced = site.owner + ".frame" in advanced_frames
                value = compose(parent, self.p.constant(site.pose), advanced)
                if body_recording:
                    body_rates[path] = self._recording_attached_body(
                        body_rates.get(site.owner + ".frame"), ("site", stem), path=path)
            else:
                if stem in visiting or len(visiting) > 128:
                    raise ReferenceError("unsupported", "Independent source frame graph is cyclic or too deep")
                visiting.add(stem)
                if stem in incoming:
                    kind, relation = incoming[stem]
                    if kind == "follow":
                        follow = self.model.follows[relation]
                        parent = frame(follow.parent)
                        advanced = follow.parent in advanced_frames
                        value = compose(parent, self.p.constant(follow.offset), advanced)
                        if body_recording:
                            body_rates[path] = self._recording_attached_body(
                                body_rates.get(follow.parent), ("follow", relation), path=path)
                    else:
                        joint = self.model.joints[relation]
                        value = frame(joint.parent + ".frame")
                        advanced = joint.parent + ".frame" in advanced_frames
                        body = body_rates.get(joint.parent + ".frame")
                        child_pose = self.model.sites[joint.child].pose
                        used_body = False
                        if body_recording and joint.kind == "hinge" and body is not None:
                            body = self._recording_hinge_body(body, relation, state, path=path)
                            if (body is not None and body.zero_origin
                                    and self._recording_body_domain()):
                                identical = self._recording_identity_parent(value, body)
                                if identical is not None:
                                    value = identical
                                    used_body = True
                                elif body.moving:
                                    rotation, rotation_advanced = self.p._recording_body_orientation(
                                        lambda: body.direct(time), axis=body.axis, rate=body.rate, witness=body.witness,
                                        context=(recording_context, path), clock=time, shared=shared_recording,
                                        source_admission=lambda: self._recording_admit_receipts(body.receipts),
                                        source_records=len(body.receipts), return_advance=True)
                                    advanced = advanced or rotation_advanced
                                    self.a.guard(*(endpoint for vector in (value.position, rotation)
                                                   for cell in vector for endpoint in (cell.lo, cell.hi)))
                                    value = PoseEnclosure(value.position, rotation, value.velocity, value.omega)
                                    used_body = True
                        if joint.kind in {"hinge", "slider"} and not used_body:
                            coordinate, rate = self._coordinate(relation, time, state, ideal=ideal)
                            angle_context = ((recording_context, relation)
                                             if recording_context is not None and rate else None)
                            if pose_only:
                                rate = F(0)
                            if joint.kind == "hinge":
                                motion = self.p.hinge(joint.axis, coordinate, rate, ideal=ideal,
                                    recording_context=angle_context,
                                    recording_time=time if angle_context is not None else None,
                                    shared_recording=shared_recording)
                            elif joint.kind == "slider":
                                motion = self.p.make(self.p.scale(joint.axis, coordinate), velocity=self.p.scale(joint.axis, rate))
                            value = compose(value, motion, advanced)
                        if not used_body:
                            value = compose(value, self.p.inverse(self.p.constant(child_pose)), advanced)
                        if body_recording:
                            body_rates[path] = (body if joint.kind == "hinge" else
                                self._recording_attached_body(body, ("static_joint", relation), path=path))
                else:
                    body = self._recording_root_body(stem, state) if body_recording else None
                    if body_recording:
                        body_rates[path] = body
                    if body is not None and body.moving and self._recording_body_domain():
                        # Prescribed world translation has no orientation
                        # operand. Evaluate it first, then the captured root
                        # orientation so its final receipt admission follows
                        # all translation callbacks and precedes publication.
                        position, velocity, omega = self._prescribed_root_translation(
                            stem, time, state, ideal=ideal, pose_only=pose_only)
                        rotation, advanced = self.p._recording_body_orientation(
                            lambda: body.direct(time), axis=body.axis, rate=body.rate, witness=body.witness,
                            context=(recording_context, path), clock=time, shared=shared_recording,
                            source_admission=lambda: self._recording_admit_receipts(body.receipts),
                            source_records=len(body.receipts), return_advance=True)
                        value = PoseEnclosure(position, rotation, velocity, omega)
                    else:
                        value = self._root_pose(stem, time, state, ideal=ideal, pose_only=pose_only)
                visiting.remove(stem)
            if body_recording:
                # Added source-proof callbacks may change the live domain
                # after the ordinary pose was computed, even on a fallback.
                self.a.guard(*(endpoint for vector in (value.position, value.orientation,
                                                       value.velocity, value.omega)
                               for cell in vector for endpoint in (cell.lo, cell.hi)))
            if advanced:
                advanced_frames.add(path)
            frames[path] = value
            return value

        for path in targets:
            frame(path)
        if not (body_recording or recording_seed) and limit == self.a.operand_limit and len(self._poses) < MAX_CACHE:
            self._poses[key] = (state, frames)
        return frames

    def _state_at(self, time, side):
        time = F(time)
        if side not in {"before", "after"} or not 0 <= time <= self.end:
            raise ReferenceError("unsupported", "Reference sample is outside its certified prefix")
        if time == self.end and side == "after" and self.end_side == "before":
            raise ReferenceError("unsupported", "The final after-side is outside this incoming-only reference")
        index = bisect_left(self.boundaries, time)
        if index < len(self.boundaries) and self.boundaries[index] == time:
            return (self._before if side == "before" else self._after)[index]
        return self._after[index - 1]

    def pose_enclosure(self, carrier, time, side="after", *, ideal=True):
        """Return the independent mathematical pose, without source roundoff inflation."""
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        state = self._state_at(F(time), side)
        try:
            return self._pose_map(F(time), state, ideal=ideal, selected=(carrier,))[carrier]
        except KeyError as error:
            raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier) from error

    def recording_pose_enclosure(self, carrier, time, side="after", *, ideal=True):
        """Return one independent recording pose through the bounded batch API."""
        values = self.recording_pose_enclosures((carrier,), time, side, ideal=ideal)
        return next(iter(values.values()))

    def _recording_carriers(self, carriers):
        if not isinstance(carriers, (tuple, list)):
            raise ReferenceError("unsupported", "Recording carriers require a bounded list or tuple")
        if len(carriers) > 1 + len(self.model.objects) + len(self.model.sites):
            raise ReferenceError("resource", "Recording carrier selection exceeds the captured source inventory")
        selected = []
        for carrier in carriers:
            self.a.tick()
            if not isinstance(carrier, str):
                raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier)
            carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
            stem = carrier.removesuffix(".frame")
            if carrier != "world" and stem not in self.model.objects and stem not in self.model.sites:
                raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier)
            selected.append(carrier)
        return tuple(selected)

    def recording_stationary_frames(self, carriers, first, last, side="after"):
        """Prove unchanged actual and ideal pose operands within one state.

        This is a source-graph proof, not a zero-rate observation or a numeric
        cache. Every time-dependent local factor must be constant under both
        source laws. A different retained endpoint state conservatively forces
        fresh evaluation, including after completion, release and force events.
        """
        self.a.tick()
        selected = self._recording_carriers(carriers)
        first, last = F(first), F(last)
        self.a.guard(first, last)
        if first > last:
            raise ReferenceError("unsupported", "Recording stationarity requires ordered source clocks")
        state = self._state_at(last, side)
        if self._state_at(first, side) is not state:
            return frozenset()
        incoming, known, visiting = self._incoming(state), {"world": True}, set()

        def coordinate(path):
            self.a.tick()
            owner = state.claims.get((path, "coordinate"))
            if owner is None:
                return True
            action, active = self.model.actions[owner], state.actions[owner]
            if active.status != "running":
                return True
            if action.kind == "reach_planar":
                index = (action.reach.shoulder, action.reach.elbow).index(path)
                actual, ideal, target = active.initial[index], active.ideal_initial[index], active.targets[index]
            else:
                actual, ideal, target = active.initial, active.ideal_initial, action.goal
            actual, ideal, target = F(actual), F(ideal), F(target)
            self.a.guard(actual, ideal, target)
            if actual == ideal == target:
                self.a.guard(action.duration, active.elapsed_at(last))
                return True
            return False

        def root(path):
            self.a.tick()
            if state.modes[path] == "dynamic":
                # Dynamic anchors retain their ordinary full evaluation even
                # when a point observation happens to have zero derivatives.
                return False
            for channel in ("translation", "orientation"):
                self.a.tick()
                owner = state.claims.get((path, channel))
                if owner is not None and state.actions[owner].status == "running":
                    if any(self.model.actions[owner].vector):
                        return False
                    self.a.guard(state.actions[owner].elapsed_at(last))
            return True

        def visit(frame):
            self.a.tick()
            if frame in known:
                return known[frame]
            if frame in visiting or len(visiting) > 128:
                raise ReferenceError("unsupported", "Independent stationary frame graph is cyclic or too deep")
            visiting.add(frame)
            stem = frame.removesuffix(".frame")
            if stem in self.model.sites:
                value = visit(self.model.sites[stem].owner + ".frame")
            elif stem in incoming:
                kind, relation = incoming[stem]
                if kind == "follow":
                    value = visit(self.model.follows[relation].parent)
                else:
                    joint = self.model.joints[relation]
                    value = visit(joint.parent + ".frame")
                    if value and joint.kind in {"hinge", "slider"}:
                        value = coordinate(relation)
            else:
                value = root(stem)
            visiting.remove(frame)
            known[frame] = value
            return value

        return frozenset(carrier for carrier in selected if visit(carrier))

    def recording_pose_enclosures(self, carriers, time, side="after", *, ideal=True, recording_context=None):
        """Evaluate independent p/q once for the selected carrier ancestries.

        The default p/q expressions are identical to full pose evaluation.
        An explicit reader-owned context may instead accumulate independent
        hinge intervals within a single source phase. Spatial derivatives do
        not enter those expressions. Separate cache namespaces and a two-field
        return type prevent unused private zeros or accumulated recording
        intervals from becoming source velocity or release-state evidence.
        The fresh mapping contains only canonical requested carrier names.
        """
        self.a.tick()
        selected = self._recording_carriers(carriers)
        time = F(time)
        state = self._state_at(time, side)
        if recording_context is not None:
            if type(recording_context) is not object or not ideal:
                raise ValueError("Independent recording recurrence requires an opaque reader context and ideal poses")
            phase = ((bisect_left(self.boundaries, time) - 1) if side == "before" else
                     (bisect_right(self.boundaries, time) - 1))
            recording_context = (recording_context, id(state), phase, side)
        frames = self._pose_map(time, state, ideal=ideal, pose_only=True, selected=selected,
                                recording_context=recording_context)
        return {carrier: RecordingPoseEnclosure(frames[carrier].position, frames[carrier].orientation)
                for carrier in selected}

    def _next(self, state, current):
        times = [self.end]
        if self._event_index < len(self.model.events):
            times.append(self.model.events[self._event_index].time)
        for path, active in state.actions.items():
            self.a.tick()
            if active.status == "running":
                times.append(active.since + self.model.actions[path].duration - active.elapsed)
        for history in state.forces.values():
            for force in history.active.values():
                self.a.tick()
                times.append(force[1] + force[0].duration)
        later = [time for time in times if time > current]
        return min(later) if later else None

    def _build(self):
        time = F(0)
        while True:
            self.a.tick()
            if len(self._times) >= MAX_BOUNDARIES:
                raise ReferenceError("resource", "Independent semantic boundary cap exceeded")
            incoming_only = time == self.end and self.end_side == "before"
            if self.mode == "recording":
                weight = (1 + self._inherited_weight(time, "before") + self._reach_history_weight
                          if incoming_only else self._boundary_weight(time))
                self._history_weight += weight
                if self._history_weight > 100000:
                    raise ReferenceError("resource", "Independent complete H06 source histories exceed 100000 weighted records",
                                         budget="boundary_state_records", consumed=self._history_weight)
            # Every transition below writes only its private staged records. The
            # incoming state is the already retained immutable prior state;
            # copying it again repeats a whole source traversal and allocation
            # without creating a distinct semantic value. H06 still counts
            # each repeated before/after record separately.
            before = self._state
            if incoming_only:
                # No natural completion, force change, authored event or
                # staged validation belongs to the requested final side.
                # Retain an explicit unavailable sentinel, never a fabricated
                # after-state that a later query could mistake for evidence.
                self._times.append(time)
                self._before.append(before)
                self._after.append(None)
                self._release_records[time] = ()
                break
            completions, coordinate_only, changed, writes_coordinates = self._coordinate_boundary_plan(time)
            staged = (self._copy_coordinate_state(before, changed, writes_coordinates)
                      if coordinate_only else self._copy_state(before))
            releases = []
            for path in completions:
                self.a.tick()
                self._finish(path, time, staged, "completed")
            if not coordinate_only:
                for path, history in staged.forces.items():
                    for key in sorted(tuple(history.active)):
                        self.a.tick()
                        payload, start = history.active[key]
                        if start + payload.duration == time:
                            del history.active[key]
                            history.completed += 1
                            self._force_change(history, time, "completed", (payload, start))
            touched = set()
            if self._event_index < len(self.model.events) and self.model.events[self._event_index].time == time:
                for index, event in enumerate(self.model.events[self._event_index].events):
                    self.a.tick()
                    self._event(event, index, time, staged, before, touched, releases)
                self._event_index += 1
            if not coordinate_only:
                for path in staged.forces:
                    self._aggregate(path, time, staged)
            self._state = staged
            self._times.append(time)
            self._before.append(before)
            self._after.append(staged)
            self._release_records[time] = tuple(releases)
            if time == self.end:
                break
            following = self._next(staged, time)
            if following is None or following > self.end:
                following = self.end
            if following <= time:
                raise ReferenceError("source_admission", "Independent event ledger failed to advance")
            time = following

    def _round_vector(self, vector):
        result = []
        for value in vector:
            self.a.tick()
            # An interval may enclose more than one materialized float.  Keep
            # that uncertainty rather than selecting an unproved midpoint.
            lo, hi = float(value.lo), float(value.hi)
            if not math.isfinite(lo) or not math.isfinite(hi):
                raise ReferenceError("numeric", "Independent materialized source vector is nonfinite")
            result.append(Interval(F(lo), F(hi)))
        return tuple(result)

    def _finish(self, path, time, state, status):
        action, active = self.model.actions[path], state.actions[path]
        if action.kind in {"reach_planar", "tween"}:
            joints = (action.reach.shoulder, action.reach.elbow) if action.kind == "reach_planar" else (action.target,)
            coordinates = tuple(self._coordinate(joint, time, state)[0] for joint in joints)
            ideal_coordinates = tuple(self._coordinate(joint, time, state, ideal=True)[0] for joint in joints)
            for joint, coordinate, ideal in zip(joints, coordinates, ideal_coordinates):
                state.coordinates[joint] = float(coordinate)
                state.ideal_coordinates[joint] = ideal
                del state.claims[(joint, "coordinate")]
            if action.kind == "reach_planar":
                tip = self._base_tip(action, coordinates)
                residual = self._residual(tip.position, action.reach.target_m)
                if status == "completed" and residual.hi > F(1, 10**9):
                    raise ReferenceError("numeric", "Independent completed reach fails the source residual bound")
                active.terminal = {"outcome": "satisfied" if status == "completed" else "interrupted",
                                   "time_seconds": _time_text(time), "position_residual_m": residual,
                                   "joint_coordinates_rad": [float(x) for x in coordinates],
                                   "tip_pose_base": self._pose_record(tip)}
        elif action.kind == "move":
            elapsed = active.elapsed_at(time)
            state.positions[action.target] = self._round_vector(self.p.add(active.initial, self.p.scale(action.vector, elapsed)))
            state.ideal_positions[action.target] = self.p.add(active.ideal_initial, self.p.scale(action.vector, elapsed))
            del state.claims[self._channel(action)]
        elif action.kind == "spin":
            elapsed = active.elapsed_at(time)
            state.rotation_errors[action.target] = self._source_basis(action.target + ".frame", time, time, state).rotation_error
            state.orientations[action.target] = self.p.multiply(self.p.spin(action.vector, elapsed), active.initial)
            state.ideal_orientations[action.target] = self.p.multiply(self.p.spin(action.vector, elapsed), active.ideal_initial)
            del state.claims[self._channel(action)]
        else:
            raise ReferenceError("unsupported", "Independent action kind is unsupported", kind=action.kind)
        active.elapsed = active.elapsed_at(time)
        active.status = status
        self._poses.clear()
        self._basis_cache.clear()

    def _event(self, event, sequence_index, time, state, incoming, touched, releases):
        self._poses.clear()
        self._basis_cache.clear()
        if event.kind == "release":
            self._release(event, sequence_index, time, state, incoming, touched, releases)
            return
        if event.kind == "force":
            self._dynamic_admission(event.target, state)
            payload = event.force
            if payload is None:
                raise ReferenceError("source_admission", "Independent force has no source payload")
            history = state.forces[event.target]
            if payload.key in history.active:
                raise ReferenceError("source_admission", "Independent force key is already active")
            history.active[payload.key] = (payload, time)
            history.started += 1
            self._force_change(history, time, "started", (payload, time))
            return
        if event.kind == "impulse":
            self._impulse(event, time, state, touched)
            return
        if event.kind not in {"start", "pause", "resume", "stop"} or event.target not in state.actions:
            raise ReferenceError("unsupported", "Unknown independent lifecycle event")
        action, active = self.model.actions[event.target], state.actions[event.target]
        allowed = {"start": {"pending"}, "pause": {"running"}, "resume": {"paused"}, "stop": {"running", "paused"}}
        if active.status not in allowed[event.kind]:
            raise ReferenceError("source_admission", "Independent lifecycle transition is invalid")
        if action.kind == "reach_planar":
            channels = ((action.reach.shoulder, "coordinate"), (action.reach.elbow, "coordinate"))
        else:
            channels = (self._channel(action),)
        if event.kind == "start":
            if any(channel in state.claims for channel in channels):
                raise ReferenceError("source_admission", "Independent action admission conflicts with an active owner")
            if action.kind == "reach_planar":
                payload = action.reach
                key = (tuple(payload.lengths_m), tuple(payload.target_m), payload.branch, tuple(payload.limits_rad))
                self.a.tick()
                limit = self._sync_numeric_cache()
                if key not in self._targets:
                    targets = _canonical_targets(payload, self.a)
                    if limit == self.a.operand_limit:
                        self._targets[key] = targets
                else:
                    targets = self._targets[key]
                active.targets = targets
                residual = self._residual(self._base_tip(action, active.targets).position, payload.target_m)
                if residual.hi > F(1, 10**9):
                    raise ReferenceError("numeric", "Independent admitted targets fail their residual bound")
                active.initial = tuple(state.coordinates[joint] for joint, _ in channels)
                active.ideal_initial = tuple(state.ideal_coordinates[joint] for joint, _ in channels)
            elif action.kind == "tween":
                joint = self.model.joints[action.target]
                if not joint.limits[0] <= action.goal <= joint.limits[1]:
                    raise ReferenceError("source_admission", "Independent tween target exceeds closed limits")
                active.initial = state.coordinates[action.target]
                active.ideal_initial = state.ideal_coordinates[action.target]
            else:
                if state.modes[action.target] != "prescribed" or action.target in self._incoming(state):
                    raise ReferenceError("source_admission", "Independent root action has no free prescribed authority")
                active.initial = (state.positions if action.kind == "move" else state.orientations)[action.target]
                active.ideal_initial = (state.ideal_positions if action.kind == "move" else state.ideal_orientations)[action.target]
                if action.kind == "spin":
                    active.rotation_error = state.rotation_errors[action.target]
            active.started, active.since, active.elapsed, active.status = time, time, F(0), "running"
            for channel in channels:
                state.claims[channel] = event.target
        elif event.kind == "pause":
            active.elapsed, active.status = active.elapsed_at(time), "paused"
        elif event.kind == "resume":
            active.since, active.status = time, "running"
        else:
            self._finish(event.target, time, state, "stopped")
        for target, channel in channels:
            touched.add(("joint" if channel == "coordinate" else "object", target))

    def _force_change(self, history, time, kind, force):
        if history.last_time != time:
            history.last_time, history.changes = time, []
        history.changes.append((kind, force))

    def _aggregate(self, path, time, state):
        self.a.tick()
        history = state.forces[path]
        if state.modes[path] != "dynamic":
            history.acceleration = None
            return
        sums = [F(0), F(0), F(0)]
        for key in sorted(history.active):
            payload, _ = history.active[key]
            sums = [self.a.exact(value, component, "add") for value, component in zip(sums, payload.force_world_n)]
        net = tuple(self.a.round64(value) for value in sums)
        mass = F(self.model.objects[path].mass)
        acceleration = tuple(self.a.round64(self.a.exact(gravity, self.a.exact(force, mass, "div"), "add"))
                             for gravity, force in zip(self.model.gravity, net))
        ideal_acceleration = tuple(self.a.exact(gravity, self.a.exact(force, mass, "div"), "add")
                                   for gravity, force in zip(self.model.gravity, sums))
        previous = history.acceleration or tuple(self.model.gravity)
        previous_ideal = history.ideal_acceleration or tuple(F(x) for x in self.model.gravity)
        changed = history.last_time == time or history.acceleration is None
        if changed or acceleration != previous or ideal_acceleration != previous_ideal:
            original = state.dynamic[path]
            actual, ideal = self._root_pose(path, time, state, ideal=False), self._root_pose(path, time, state, ideal=True)
            # Capture the *old* phase before installing its new acceleration.
            # Its point basis includes Ea*T and Ea*T^2/2 as well as incoming
            # anchor errors; keeping only the original errors loses the force
            # arithmetic discrepancy at every completion or replacement.
            before = self._source_basis(path + ".frame", time, time, state)
            position_error, rotation_error = before.position_error, before.rotation_error
            velocity_error, omega_error = before.velocity_error, before.omega_error
            if acceleration != previous:
                # A changed canonical acceleration freezes the current public
                # source tuple. The orientation then denotes that tuple's
                # projective rotation, rather than an unnormalised unit q.
                actual = PoseEnclosure(self._round_vector(actual.position),
                    self.p.quaternion(self._expand_vector(ideal.orientation, rotation_error, rounded=True)),
                    self._round_vector(actual.velocity), self._round_vector(actual.omega))
            else:
                # Equal canonical acceleration retains the private trajectory.
                # Convert the old public-point error back to it using a proved
                # binary64 publication bound. Source and proof clocks differ.
                def publication(vector):
                    return self.a.exact(self.a.exact(self._l1(vector), F(1, 1 << 53), "mul"),
                                        F(3, 1 << 1075), "add")
                position_error = self.a.exact(position_error, publication(actual.position), "add")
                velocity_error = self.a.exact(velocity_error, publication(actual.velocity), "add")
                rotation_error = self.a.exact(rotation_error, F(1, 1 << 50), "add")
            state.dynamic[path] = _Anchor(time, original.since, actual, ideal,
                position_error, rotation_error, velocity_error, omega_error,
                time if acceleration != previous else (original.time if original.source_time is None else original.source_time))
        history.net, history.acceleration, history.ideal_acceleration = net, acceleration, ideal_acceleration
        self._poses.clear()
        self._basis_cache.clear()

    def _dynamic_admission(self, path, state):
        self.a.tick()
        obj = self.model.objects.get(path)
        if (obj is None or state.modes[path] != "dynamic" or path in self._incoming(state)
                or obj.physical.get("kind") != "sphere_body" or obj.mass <= 0 or not obj.inertia or obj.inertia <= 0):
            raise ReferenceError("source_admission", "Independent influence requires a free positive-mass dynamic sphere")

    def _occurrence(self, path):
        for collection in (self.model.actions, self.model.joints, self.model.sites, self.model.objects):
            if path in collection:
                return {"path": path, "element_id": list(collection[path].element_id)}
        raise ReferenceError("identity", "Independent source occurrence is unknown", path=path)

    def _dependencies(self, child, state):
        incoming, result = self._incoming(state), set()
        while child is not None:
            self.a.tick()
            if ("object", child) in result:
                raise ReferenceError("unsupported", "Independent release dependency graph contains a cycle")
            result.add(("object", child))
            if child not in incoming:
                break
            kind, relation = incoming[child]
            result.add((kind, relation))
            child = (self.model.sites[self.model.joints[relation].parent].owner if kind == "joint" else
                     self._owner(self.model.follows[relation].parent))
        return result

    def _expand_vector(self, vector, error, *, rounded=False):
        result = tuple(self.a.add(value, Interval(-error, error)) for value in vector)
        return self._round_vector(result) if rounded else result

    def _release(self, event, index, time, state, incoming, touched, releases):
        joint = self.model.joints.get(event.target)
        if joint is None or joint.kind != "grip" or event.target not in state.grips:
            raise ReferenceError("source_admission", "Independent release requires an active grip")
        child = self.model.sites[joint.child].owner
        dependencies = self._dependencies(child, incoming)
        if dependencies & touched:
            raise ReferenceError("source_admission", "Earlier statements changed independent incoming release dependencies")
        obj = self.model.objects[child]
        if state.modes[child] != "prescribed" or obj.physical.get("kind") != "sphere_body":
            raise ReferenceError("source_admission", "Independent grip child is not a prescribed physical sphere")
        actual = self._pose_map(time, incoming, ideal=False)[child + ".frame"]
        ideal = self._pose_map(time, incoming, ideal=True)[child + ".frame"]
        bound = self._phase(child + ".frame", time, time, incoming)
        materialized = PoseEnclosure(
            self._expand_vector(actual.position, bound.source_numeric_position_error, rounded=True),
            self.p.quaternion(self._expand_vector(actual.orientation,
                bound.source_numeric_rotation_error, rounded=True)),
            self._expand_vector(actual.velocity, bound.source_numeric_velocity_error, rounded=True),
            self._expand_vector(actual.omega, bound.source_numeric_angular_velocity_error, rounded=True))
        state.dynamic[child] = _Anchor(time, time, materialized, ideal,
            bound.source_numeric_position_error, bound.source_numeric_rotation_error,
            bound.source_numeric_velocity_error, bound.source_numeric_angular_velocity_error)
        state.grips.remove(event.target)
        state.modes[child] = "dynamic"
        contributors = []
        for path, action in self.model.actions.items():
            self.a.tick()
            active = incoming.actions[path]
            if action.kind != "reach_planar" or active.status != "running":
                continue
            payload = action.reach
            if not dependencies.intersection({("joint", payload.shoulder), ("joint", payload.elbow)}):
                continue
            pair = [self._coordinate(name, time, incoming) for name in (payload.shoulder, payload.elbow)]
            contributors.append({"action": self._occurrence(path), "shoulder": self._occurrence(payload.shoulder),
                "elbow": self._occurrence(payload.elbow), "joint_coordinates_rad": [float(item[0]) for item in pair],
                "joint_rates_rad_per_s": [self.a.round64(item[1]) for item in pair]})
        node = event.span
        source = self.model.source_provenance[node.source_id]
        releases.append({"program_revision": self.model.program_revision,
            "source_location": {"source_id": node.source_id, "source_revision": source["source_revision"],
                                "start_byte": node.start, "end_byte": node.end},
            "sequence_index": index, "time_seconds": _time_text(time), "grip": self._occurrence(event.target),
            "target": self._occurrence(child), "reach_contributors": contributors,
            "incoming_pose_world": self._pose_record(actual),
            "incoming_linear_velocity_world_m_per_s": list(actual.velocity),
            "incoming_angular_velocity_world_rad_per_s": list(actual.omega)})
        touched.update({("joint", event.target), ("object", child)})
        self._poses.clear()
        self._basis_cache.clear()

    def _impulse(self, event, time, state, touched):
        self._dynamic_admission(event.target, state)
        obj, payload = self.model.objects[event.target], event.impulse
        if payload is None:
            raise ReferenceError("source_admission", "Independent impulse has no source operands")
        ideal = self._root_pose(event.target, time, state, ideal=True)
        bound = self._phase(event.target + ".frame", time, time, state)
        # These are source-output enclosures, in each field's physical units.
        # A current controlled pose differs from the independent ideal pose
        # even when the exact mathematical rotation would round identically.
        # Propagate its proved errors before the impulse operations rather
        # than adding an unrelated global position/angle tolerance afterward.
        position = self._expand_vector(ideal.position, bound.source_numeric_position_error, rounded=True)
        orientation = self._expand_vector(ideal.orientation, bound.source_numeric_rotation_error, rounded=True)
        before_velocity = self._expand_vector(ideal.velocity, bound.source_numeric_velocity_error, rounded=True)
        before_omega = self._expand_vector(ideal.omega, bound.source_numeric_angular_velocity_error, rounded=True)
        ideal_lever = self.p.rotate(ideal.orientation, payload.point_self_m)
        lever_error = self.a.exact(self.a.exact(bound.source_numeric_rotation_error,
            self._l1(payload.point_self_m), "mul"), F(1, 1 << 96), "add")
        lever = self._expand_vector(ideal_lever, lever_error, rounded=True)
        point = self._round_vector(self.p.add(position, lever))
        angular = self._round_vector(self.p.cross(lever, self.p.vector(payload.impulse_world_n_s)))
        inverse_mass = self.a.exact(1, obj.mass, "div")
        inverse_inertia = self.a.exact(1, obj.inertia, "div")
        delta = self.p.scale(payload.impulse_world_n_s, inverse_mass)
        velocity = self._round_vector(self.p.add(before_velocity, delta))
        omega = self._round_vector(self.p.add(before_omega, self.p.scale(angular, inverse_inertia)))
        ideal_velocity = self.p.add(ideal.velocity, delta)
        ideal_omega = self.p.add(ideal.omega,
            self.p.scale(self.p.cross(ideal_lever, self.p.vector(payload.impulse_world_n_s)), inverse_inertia))
        if any(payload.impulse_world_n_s):
            original = state.dynamic[event.target]
            state.dynamic[event.target] = _Anchor(time, original.since,
                PoseEnclosure(position, self.p.quaternion(orientation), velocity, omega),
                PoseEnclosure(ideal.position, ideal.orientation, ideal_velocity, ideal_omega),
                bound.source_numeric_position_error, bound.source_numeric_rotation_error,
                self._distance(velocity, ideal_velocity), self._distance(omega, ideal_omega))
            touched.add(("object", event.target))
        history = state.impulses[event.target]
        if history["last_application_time_seconds"] != _time_text(time):
            history["last_application_time_seconds"] = _time_text(time)
            history["last_applications"] = []
        history["applied_count"] += 1
        history["last_applications"].append({"sequence_index": payload.sequence_index,
            "source_location": dict(payload.source), "target_element_id": list(obj.element_id), "target_path": event.target,
            "impulse_world_n_s": list(payload.impulse_world_n_s), "application_point_self_m": list(payload.point_self_m),
            "lever_arm_world_m": list(lever), "application_point_world_m": list(point),
            "angular_impulse_world_n_m_s": list(angular), "linear_velocity_before_world_m_per_s": list(before_velocity),
            "linear_velocity_after_world_m_per_s": list(velocity), "angular_velocity_before_world_rad_per_s": list(before_omega),
            "angular_velocity_after_world_rad_per_s": list(omega)})
        self._poses.clear()
        self._basis_cache.clear()

    def _base_tip(self, action, coordinates):
        coordinates = tuple(coordinates)
        key = self.p._key("base_tip", tuple(action.reach.lengths_m), coordinates)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        first, second = coordinates
        sine1, cosine1 = self.a.sincos(first)
        sine2, cosine2 = self.a.sincos(self.a.exact(first, second, "add"))
        a, b = action.reach.lengths_m
        position = (self.a.add(self.a.mul(a, cosine1), self.a.mul(b, cosine2)),
                    self.a.add(self.a.mul(a, sine1), self.a.mul(b, sine2)), self.a.point(0))
        rotation = self.p.hinge((0, 0, 1), self.a.exact(first, second, "add"), 0).orientation
        return self.a.remember(key, self.p.make(position, rotation, normalized=True))

    def _residual(self, position, target):
        position, target = tuple(position), tuple(target)
        key = self.p._key("residual", position, target)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        difference = tuple(self.a.sub(value, expected) for value, expected in zip(position, target))
        return self.a.remember(key, self.p.norm(difference))

    def _world_target(self, base, target):
        """Reuse only the immutable numerical operands of a world target."""
        target = tuple(target)
        key = self.p._key("world_target", base, target)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.p.compose(base, self.p.make(target)))

    def _joint_observation(self, path, time, state, observations):
        """One sample's exact joint value and its public binary64 projection."""
        self.a.tick()
        key = (self.a.operand_limit, path)
        cached = observations.get(key)
        if cached is not None:
            return cached
        coordinate, rate = self._coordinate(path, time, state)
        value = (coordinate, rate, float(coordinate), self.a.round64(rate))
        if len(observations) < MAX_CACHE:
            self.a.tick()
            observations[key] = value
        return value

    @staticmethod
    def _pose_record(pose):
        return {"position_m": list(pose.position), "orientation_wxyz": list(pose.orientation)}

    def sample(self, time, side="after"):
        time = F(time)
        state = self._state_at(time, side)
        if self._reach_history_weight is None:
            # Rate-only callers never request this complete reach projection.
            # A later sample must still pass its original capacity guard before
            # constructing any public sample rows.
            self._reach_history_weight = self._maximum_reach_weight()
        frames, incoming = self._pose_map(time, state, ideal=False), self._incoming(state)
        objects = {}
        geometry = {entry["path"]: entry for entry in
                    (self._geometry_values() if self._geometry is None else self._geometry)}
        for path, obj in self.model.objects.items():
            self.a.tick()
            pose, mode = frames[path + ".frame"], state.modes[path]
            if path in incoming:
                kind, relation = incoming[path]
                authority = {"kind": kind, "relation": relation}
            elif mode == "dynamic":
                anchor = state.dynamic[path]
                authority = {"kind": "free_sphere", "since_seconds": _time_text(anchor.since),
                             "trajectory_anchor_seconds": _time_text(anchor.time if anchor.source_time is None else anchor.source_time)}
            else:
                authority = {"kind": mode, "translation_action": state.claims.get((path, "translation")),
                             "orientation_action": state.claims.get((path, "orientation"))}
            mass = self.a.exact(0, 0, "add")
            for owned in self.model.objects.values():
                if owned.path == path or owned.path.startswith(path + "."):
                    mass = self.a.exact(mass, owned.mass, "add")
            gravity = ("active_dynamic" if mode == "dynamic" else
                       "inactive_prescribed" if mode == "prescribed" and obj.mass else
                       "inactive_static" if mode == "static" and obj.mass else "no_body")
            objects[path] = {"element_id": list(obj.element_id), "kind": "object", "name": obj.name,
                "class_name": obj.class_name, "owner": obj.owner, "motion": mode,
                "position_m": list(pose.position), "orientation_wxyz": list(pose.orientation),
                "velocity_m_per_s": list(pose.velocity), "angular_velocity_rad_per_s": list(pose.omega),
                "pose_frame": "world", "velocity_measured_in": "world", "velocity_expressed_in": "world",
                "velocity_reference_point": "center_of_mass" if obj.mass else "origin", "pose_authority": authority,
                "own_mass_kg": obj.mass, "owned_aggregate_mass_kg": self.a.round64(mass), "inertia_kg_m2": obj.inertia,
                "geometry": copy.deepcopy(geometry[path]["geometry"]), "physical": copy.deepcopy(geometry[path]["physical"]),
                "gravity_participation": gravity, "collision": obj.collision,
                "impulses": copy.deepcopy(state.impulses[path]), "forces": self._forces(path, state)}
        joints, joint_observations = {}, {}
        for path, joint in self.model.joints.items():
            self.a.tick()
            record = {"element_id": list(joint.element_id), "kind": joint.kind,
                "status": "inactive" if joint.kind == "grip" and path not in state.grips else "active",
                "parent_site": joint.parent, "child_site": joint.child,
                "coupling": "externally_prescribed_no_load_solution"}
            if joint.kind in {"hinge", "slider"}:
                physical = self._joint_observation(path, time, state, joint_observations)
                record.update(coordinate=physical[2], coordinate_rate=physical[3],
                    unit="rad" if joint.kind == "hinge" else "m", limits=list(joint.limits),
                    action=state.claims.get((path, "coordinate")))
            joints[path] = record
        actions = {path: {"element_id": list(action.element_id), "kind": action.kind, "target": action.target,
                         "status": state.actions[path].status, "local_elapsed_seconds": _time_text(state.actions[path].elapsed_at(time)),
                         "duration_seconds": _time_text(action.duration)} for path, action in self.model.actions.items()}
        frame_records = {path: {"position_m": list(value.position), "orientation_wxyz": list(value.orientation),
            "velocity_m_per_s": list(value.velocity), "angular_velocity_rad_per_s": list(value.omega)} for path, value in frames.items()}
        total_mass = F(0)
        for obj in self.model.objects.values():
            total_mass = self.a.exact(total_mass, obj.mass, "add")
        result = {"time_seconds": _time_text(time), "side": side, "objects": objects, "joints": joints,
                  "actions": actions, "frames": frame_records, "scene_mass_kg": self.a.round64(total_mass),
                  "reaches": {path: self._reach(path, time, side, state, frames, joint_observations)
                              for path, action in self.model.actions.items() if action.kind == "reach_planar"}}
        if self.mode == "observation":
            self._logical_entries(result)
        return result

    def _force_record(self, path, force):
        payload, start = force
        return {"force_key": payload.key,
            "force_element_id": [self.model.module_key, self.model.scene_key, "force", payload.key],
            "target_path": path, "target_element_id": list(self.model.objects[path].element_id),
            "program_revision": self.model.program_revision, "source_location": dict(payload.source),
            "sequence_index": payload.sequence_index, "force_world_n": list(payload.force_world_n),
            "activation_time_seconds": _time_text(start), "duration_seconds": _time_text(payload.duration),
            "completion_time_seconds": _time_text(start + payload.duration)}

    def _forces(self, path, state):
        history = state.forces[path]
        return {"active": [self._force_record(path, history.active[key]) for key in sorted(history.active)],
            "net_force_world_n": list(history.net),
            "acceleration_world_m_per_s2": None if history.acceleration is None else list(history.acceleration),
            "started_count": history.started, "completed_count": history.completed,
            "last_change_time_seconds": None if history.last_time is None else _time_text(history.last_time),
            "last_changes": [{"kind": kind, **self._force_record(path, force)} for kind, force in history.changes]}

    def _reach(self, path, time, side, state, frames, joint_observations):
        self.a.tick()
        action, active = self.model.actions[path], state.actions[path]
        payload = action.reach
        physical = [self._joint_observation(joint, time, state, joint_observations)
                    for joint in (payload.shoulder, payload.elbow)]
        coordinates = tuple(value[0] for value in physical)
        tip_base = self._base_tip(action, coordinates)
        target_world = self._world_target(frames[payload.base_frame], payload.target_m)
        admitted = active.targets is not None
        own_rates = [0.0, 0.0]
        if active.status == "running":
            own_rates = [self.a.round64(self.a.exact(self.a.exact(target, initial, "sub"), action.duration, "div"))
                         for target, initial in zip(active.targets, active.initial)]
        completion = (active.since + action.duration - active.elapsed if active.status == "running" else
                      F(active.terminal["time_seconds"]) if active.status == "completed" else None)
        current = {"observation": {"time_seconds": _time_text(time), "side": side, "run_id": None, "context_kind": "recorded_prefix"},
            "lifecycle": active.status,
            "goal_outcome": {"pending": "pending", "running": "active", "paused": "active", "stopped": "interrupted", "completed": "satisfied"}[active.status],
            "resolved_joint_targets_rad": list(active.targets) if admitted else None,
            "start_coordinates_rad": list(active.initial) if admitted else None,
            "start_time_seconds": _time_text(active.started) if admitted else None,
            "elapsed_seconds": _time_text(active.elapsed_at(time)) if admitted else None,
            "completion_time_seconds": None if completion is None else _time_text(completion),
            "joint_coordinates_rad": [value[2] for value in physical],
            "joint_rates_rad_per_s": [value[3] for value in physical],
            "action_joint_rates_rad_per_s": own_rates,
            "claimed_joint_ids": [list(self.model.joints[joint].element_id) for joint in (payload.shoulder, payload.elbow)]
                if active.status in {"running", "paused"} else [],
            "current_residual_m": self._residual(tip_base.position, payload.target_m) if admitted else None,
            "tip_pose_base": self._pose_record(tip_base), "tip_pose_world": self._pose_record(frames[payload.tip + ".frame"]),
            "current_world_target_m": list(target_world.position), "terminal_result": copy.deepcopy(active.terminal)}
        return self._description(path, current)

    def _description(self, path, current):
        action = self.model.actions[path]
        payload = action.reach
        base_site = self.model.sites[payload.base_frame.removesuffix(".frame")]
        frame = {"path": payload.base_frame, "site_element_id": list(base_site.element_id)}
        return {"kind": "reach_planar", "element_id": list(action.element_id),
            "description_identity": list(payload.description_identity), "program_revision": self.model.program_revision,
            "accepted_program_revision": None, "candidate_only": None, "context_origin": "source_recording",
            "source_location": self._source_location(payload.source_location), "channel": "joint_coordinates",
            "chain": {"shoulder": self._occurrence(payload.shoulder), "elbow": self._occurrence(payload.elbow),
                      "tip": self._occurrence(payload.tip), "base_frame": frame, "lengths_m": list(payload.lengths_m),
                      "closed_limits_rad": {"shoulder": list(payload.limits_rad[0]), "elbow": list(payload.limits_rad[1])}},
            "target": {"type": "Point3", "frame": copy.deepcopy(frame), "coordinates_m": list(payload.target_m)},
            "branch": payload.branch, "duration_seconds": _time_text(action.duration),
            "current": {"available": True, "reason": None, "value": current}}

    def _source_location(self, value):
        """Reuse one fixed immutable source projection, never a mutable row.

        An action alias may share its frozen four-field source location with
        many independently identified action occurrences. The complete scalar
        values form the key in the existing bounded pure cache; all occurrences
        still receive a fresh dictionary and retain their full H06 weight.
        Other source-record shapes retain the ordinary recursive conversion.
        """
        names = ("source_id", "source_revision", "start_byte", "end_byte")
        if (not is_dataclass(value)
                or not getattr(type(value), "__dataclass_params__").frozen
                or tuple(entry.name for entry in fields(value)) != names):
            return _plain(value, self.a)
        values = tuple(getattr(value, name) for name in names)
        if tuple(type(item) for item in values) != (str, str, int, int):
            return _plain(value, self.a)
        self.a.guard(values[2], values[3])
        key = ("source_location_projection", self.a.operand_limit, values)
        cached = self.a.lookup(key)
        if cached is None:
            projected = _plain(value, self.a)
            cached = self.a.remember(key, tuple(projected.items()))
        return dict(cached)

    def _logical_entries(self, value):
        """Independent JSON logical count; every repeated occurrence counts.

        Counts and cancellation checkpoints follow the bounded output walker,
        separately from numerical arithmetic units and H06 row weights.
        """
        count, stack = 0, [(value, 0)]
        while stack:
            item, depth = stack.pop()
            count += 1
            if count % 128 == 0:
                self.a.tick()
            if count > 100000 or depth > 128:
                raise ReferenceError("resource", "Independent JSON counting exceeds its finite entry/depth bound")
            if isinstance(item, dict):
                stack.extend((entry, depth + 1) for entry in item.values())
            elif isinstance(item, (tuple, list)):
                stack.extend((entry, depth + 1) for entry in item)
            elif item is not None and not isinstance(item, (str, bool, int, float, F, Interval)):
                raise ReferenceError("unsupported", "Independent JSON counter encountered an unsupported leaf")
        self.a.tick()
        return count

    def _maximum_reach_weight(self):
        total = 1
        pose = {"position_m": [0.0] * 3, "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]}
        for path, action in self.model.actions.items():
            self.a.tick()
            if action.kind != "reach_planar":
                continue
            payload = action.reach
            current = {"observation": {"time_seconds": "0", "side": "before", "run_id": None, "context_kind": "recorded_prefix"},
                "lifecycle": "completed", "goal_outcome": "satisfied", "resolved_joint_targets_rad": [0.0, 0.0],
                "start_coordinates_rad": [0.0, 0.0], "start_time_seconds": "0", "elapsed_seconds": "0",
                "completion_time_seconds": "0", "joint_coordinates_rad": [0.0, 0.0],
                "joint_rates_rad_per_s": [0.0, 0.0], "action_joint_rates_rad_per_s": [0.0, 0.0],
                "claimed_joint_ids": [list(self.model.joints[joint].element_id) for joint in (payload.shoulder, payload.elbow)],
                "current_residual_m": 0.0, "tip_pose_base": pose, "tip_pose_world": pose, "current_world_target_m": [0.0] * 3,
                "terminal_result": {"outcome": "satisfied", "time_seconds": "0", "position_residual_m": 0.0,
                                    "joint_coordinates_rad": [0.0, 0.0], "tip_pose_base": pose}}
            total += self._logical_entries(self._description(path, current))
            if total > 100000:
                raise ReferenceError("resource", "Independent complete reach projection weight exceeds its limit")
        return total

    def _inherited_weight(self, horizon, side):
        key = (horizon, side)
        if key in self._inherited_history_cache:
            return self._inherited_history_cache[key]
        # H05 omits the frame map and duplicate object row.  The remaining
        # ordinary rows plus empty impulse/force histories weigh 19*O+J+A.
        base = 19 * len(self.model.objects) + len(self.model.joints) + len(self.model.actions)
        impulse_groups, force_changes = {}, {}
        for block in self.model.events:
            self.a.tick()
            if block.time > horizon or block.time == horizon and side == "before":
                break
            for event in block.events:
                self.a.tick()
                if event.kind == "impulse":
                    target = self.model.objects[event.target]
                    group = impulse_groups.setdefault(block.time, {})
                    group[event.target] = group.get(event.target, 0) + 45 + len(target.element_id)
                if event.kind == "force":
                    payload = event.force
                    weight = self._logical_entries(self._force_record(event.target, (payload, block.time)))
                    force_changes.setdefault(block.time, []).append(("start", event.target, payload.key, weight))
                    end = block.time + payload.duration
                    if end < horizon or end == horizon and side == "after":
                        force_changes.setdefault(end, []).append(("end", event.target, payload.key, weight))
        retained, impulse_maximum = {}, 0
        for _, values in sorted(impulse_groups.items()):
            retained.update(values)
            impulse_maximum = max(impulse_maximum, sum(retained.values()))
        active, latest, maximum = {}, {}, 0
        for _, changes in sorted(force_changes.items()):
            group = {}
            for kind, target, force, weight in changes:
                self.a.tick()
                if kind == "end":
                    active.pop((target, force), None)
                else:
                    active[(target, force)] = weight
                group[target] = group.get(target, 0) + weight + 1
            latest.update(group)
            maximum = max(maximum, sum(active.values()) + sum(latest.values()))
        result = base + impulse_maximum + maximum
        self._inherited_history_cache[key] = result
        return result

    def _release_weight(self, time):
        total = 1
        for block in self.model.events:
            self.a.tick()
            if block.time != time:
                continue
            for index, event in enumerate(block.events):
                if event.kind != "release":
                    continue
                joint = self.model.joints[event.target]
                child = self.model.sites[joint.child].owner
                dependencies = self._dependencies(child, self._state)
                contributors = []
                for path, action in self.model.actions.items():
                    self.a.tick()
                    if action.kind != "reach_planar":
                        continue
                    payload = action.reach
                    if dependencies.intersection({("joint", payload.shoulder), ("joint", payload.elbow)}):
                        contributors.append({"action": self._occurrence(path), "shoulder": self._occurrence(payload.shoulder),
                            "elbow": self._occurrence(payload.elbow), "joint_coordinates_rad": [0.0, 0.0],
                            "joint_rates_rad_per_s": [0.0, 0.0]})
                node = event.span
                source = self.model.source_provenance[node.source_id]
                shape = {"program_revision": self.model.program_revision,
                    "source_location": {"source_id": node.source_id, "source_revision": source["source_revision"],
                                        "start_byte": node.start, "end_byte": node.end},
                    "sequence_index": index, "time_seconds": _time_text(time),
                    "grip": self._occurrence(event.target), "target": self._occurrence(child),
                    "reach_contributors": contributors,
                    "incoming_pose_world": {"position_m": [0.0] * 3, "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]},
                    "incoming_linear_velocity_world_m_per_s": [0.0] * 3,
                    "incoming_angular_velocity_world_rad_per_s": [0.0] * 3}
                total += self._logical_entries(shape)
        return total

    def _boundary_weight(self, time):
        return (2 + self._inherited_weight(time, "before") + self._inherited_weight(time, "after")
                + 2 * self._reach_history_weight + self._release_weight(time))

    def _boundary_projection(self, time, side):
        """Build exactly the independent source history promised at a boundary.

        Complete object inspection also constructs geometry, aggregate masses
        and all spatial derivatives. None is a field of this projection. The
        full event ledger has already established release/impulse anchors;
        retained-key poses and per-carrier phase bounds are checked separately.
        Reach observations need base/tip p/q plus actual joint observations,
        so their independent p/q path does not evaluate discarded derivatives.
        """
        self.a.tick()
        state = self._state_at(time, side)
        incoming = self._incoming(state)
        selected = {}
        for action in self.model.actions.values():
            self.a.tick()
            if action.kind == "reach_planar":
                selected[action.reach.base_frame] = None
                selected[action.reach.tip + ".frame"] = None
        frames = self._pose_map(time, state, ideal=False, pose_only=True, selected=tuple(selected))
        authorities, impulses, forces = {}, {}, {}
        for path in self.model.objects:
            self.a.tick()
            if path in incoming:
                kind, relation = incoming[path]
                authority = {"kind": kind, "relation": relation}
            elif state.modes[path] == "dynamic":
                anchor = state.dynamic[path]
                authority = {"kind": "free_sphere", "since_seconds": _time_text(anchor.since),
                             "trajectory_anchor_seconds": _time_text(anchor.time if anchor.source_time is None else anchor.source_time)}
            else:
                authority = {"kind": state.modes[path], "translation_action": state.claims.get((path, "translation")),
                             "orientation_action": state.claims.get((path, "orientation"))}
            authorities[path] = authority
            impulses[path] = copy.deepcopy(state.impulses[path])
            forces[path] = self._forces(path, state)
        joints, joint_observations = {}, {}
        for path, joint in self.model.joints.items():
            self.a.tick()
            record = {"element_id": list(joint.element_id), "kind": joint.kind,
                "status": "inactive" if joint.kind == "grip" and path not in state.grips else "active",
                "parent_site": joint.parent, "child_site": joint.child,
                "coupling": "externally_prescribed_no_load_solution"}
            if joint.kind in {"hinge", "slider"}:
                physical = self._joint_observation(path, time, state, joint_observations)
                record.update(coordinate=physical[2], coordinate_rate=physical[3],
                    unit="rad" if joint.kind == "hinge" else "m", limits=list(joint.limits),
                    action=state.claims.get((path, "coordinate")))
            joints[path] = record
        actions = {path: {"element_id": list(action.element_id), "kind": action.kind, "target": action.target,
                         "status": state.actions[path].status, "local_elapsed_seconds": _time_text(state.actions[path].elapsed_at(time)),
                         "duration_seconds": _time_text(action.duration)} for path, action in self.model.actions.items()}
        reaches = {path: self._reach(path, time, side, state, frames, joint_observations)
                   for path, action in self.model.actions.items() if action.kind == "reach_planar"}
        return {"joint_states": joints, "action_states": actions, "pose_authorities": authorities,
                "impulse_states": impulses, "force_states": forces, "reach_states": reaches}

    def boundary_states(self):
        # The full conservative H06 sum was checked before retaining each
        # state pair.  Projection allocation cannot precede that preflight.
        if self.mode != "recording":
            self.a.tick()
            raise ReferenceError("unsupported", "Observation-only references cannot provide complete recording histories")
        if self.end_side != "after":
            raise ReferenceError("unsupported", "Complete recording histories require the final after-side")
        if self._history_weight > 100000:
            raise ReferenceError("resource", "Independent boundary history preflight was exceeded")
        result, actual_weight = [], 0
        for time in self.boundaries:
            self.a.tick()
            record = {"source_seconds": _time_text(time), "incoming_releases": copy.deepcopy(list(self._release_records[time]))}
            for side in ("before", "after"):
                projection = self._boundary_projection(time, side)
                for name, value in projection.items():
                    record[name + "_" + side] = value
                actual_weight += self._inherited_weight(time, side) + self._logical_entries(projection["reach_states"])
            actual_weight += 2 + self._logical_entries(record["incoming_releases"])
            if actual_weight > self._history_weight or actual_weight > 100000:
                raise ReferenceError("resource", "Independent actual H06 history exceeds its preflight bound")
            result.append(record)
        return result

    def phases(self, carrier, start, end):
        """Return all positively overlapping independently derived phases.

        Endpoint-only contact never selects the next phase.  Clipped actual
        binary32 gaps can ask for every phase they touch using the same rule.
        """
        start, end = F(start), F(end)
        if not 0 <= start <= end <= self.end:
            raise ReferenceError("unsupported", "Independent phase interval is outside its source prefix")
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        result = []
        for index, (left, right) in enumerate(zip(self.boundaries, self.boundaries[1:])):
            self.a.tick()
            limit = self._sync_numeric_cache()
            if max(left, start) >= min(right, end):
                continue
            key = (carrier, max(left, start), min(right, end), index)
            if key not in self._phase_cache:
                value = self._phase(carrier, key[1], key[2], self._after[index])
                if limit == self.a.operand_limit and len(self._phase_cache) < MAX_CACHE:
                    self._phase_cache[key] = value
            else:
                value = self._phase_cache[key]
            result.append(value)
        return tuple(result)

    def point_phase(self, carrier, time, side="after"):
        """Bound one exact state, including newly materialized final anchors.

        A point does not add a positive-width phase.  It independently supplies
        the numerical basis for an inclusive endpoint or either boundary side.
        """
        self.a.tick()
        limit = self._sync_numeric_cache()
        time = F(time)
        state = self._state_at(time, side)
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        key = ("point", carrier, time, side)
        if key not in self._phase_cache:
            value = self._phase(carrier, time, time, state)
            if limit == self.a.operand_limit and len(self._phase_cache) < MAX_CACHE:
                self._phase_cache[key] = value
            return value
        return self._phase_cache[key]

    def _l1(self, vector):
        result = F(0)
        for value in vector:
            interval = self.a.interval(value)
            result = self.a.exact(result, interval.magnitude, "add")
        return result

    def _distance(self, first, last):
        return self._l1(tuple(self.a.sub(a, b) for a, b in zip(first, last)))

    def _ancestry(self, carrier, state):
        """Source edges and offsets, independently reconstructed from topology."""
        incoming, offsets, joints, path = self._incoming(state), [], [], []
        stem = carrier.removesuffix(".frame")
        if carrier == "world":
            return None, (), (), ("world",)
        if stem in self.model.sites:
            site = self.model.sites[stem]
            offsets.append(site.pose.position)
            path.append(carrier)
            stem = site.owner
        visited = set()
        while True:
            self.a.tick()
            if stem in visited or len(visited) > 128:
                raise ReferenceError("unsupported", "Independent derivative path is cyclic or too deep")
            visited.add(stem)
            path.append(stem + ".frame")
            if stem not in incoming:
                return stem, tuple(offsets), tuple(joints), tuple(path)
            kind, relation = incoming[stem]
            path.append(relation)
            if kind == "follow":
                follow = self.model.follows[relation]
                offsets.append(follow.offset.position)
                if follow.parent == "world":
                    return None, tuple(offsets), tuple(joints), tuple(path)
                parent = follow.parent.removesuffix(".frame")
                if parent in self.model.sites:
                    offsets.append(self.model.sites[parent].pose.position)
                    stem = self.model.sites[parent].owner
                else:
                    stem = parent
            else:
                joint = self.model.joints[relation]
                offsets.extend((self.model.sites[joint.child].pose.position, self.model.sites[joint.parent].pose.position))
                if joint.kind in {"hinge", "slider"}:
                    joints.append(relation)
                stem = self.model.sites[joint.parent].owner

    def _joint_path(self, joint, start, end, state):
        owner = state.claims.get((joint, "coordinate"))
        active = None if owner is None else state.actions[owner]
        action = None if owner is None else self.model.actions[owner]
        if action is not None and action.kind == "reach_planar":
            index = (action.reach.shoulder, action.reach.elbow).index(joint)
            initial, target, ideal_initial = F(active.initial[index]), F(active.targets[index]), F(active.ideal_initial[index])
        elif action is not None:
            initial, target, ideal_initial = F(active.initial), F(action.goal), F(active.ideal_initial)
        else:
            initial = target = F(state.coordinates[joint])
            ideal_initial = F(state.ideal_coordinates[joint])
        duration = None if action is None else F(action.duration)
        elapsed = (F(0), F(0)) if active is None else (active.elapsed_at(start), active.elapsed_at(end))
        self.a.guard(initial, target, ideal_initial, *elapsed, *((duration,) if duration is not None else ()))
        # Phase callers repeat the same scalar law for a carrier's ancestry
        # and its uniform basis. Equal cloned arms may share that pure law,
        # but never a joint/action identity or a state/clock object.
        key = ("coordinate_path_law", self.a.operand_limit, initial, target,
               ideal_initial, duration, elapsed, active is not None,
               active is not None and active.status == "running")
        numbers = self.a.lookup(key)
        if numbers is None:
            op = self.a.exact
            actual_slope = F(0) if active is None else op(op(target, initial, "sub"), duration, "div")
            ideal_slope = F(0) if active is None else op(op(target, ideal_initial, "sub"), duration, "div")
            actual = tuple(op(initial, op(actual_slope, time, "mul"), "add") for time in elapsed)
            ideal = tuple(op(ideal_initial, op(ideal_slope, time, "mul"), "add") for time in elapsed)
            error = max(abs(op(x, y, "sub")) for x, y in zip(actual, ideal))
            if active is not None:
                error = op(error, op(op(max(abs(x) for x in actual), F(1, 1 << 53), "mul"), F(3, 1 << 1075), "add"), "add")
            if active is not None and active.status != "running":
                actual_slope = ideal_slope = F(0)
            numbers = self.a.remember(key, (actual_slope, ideal_slope, actual, ideal, error))
        actual_slope, ideal_slope, actual, ideal, error = numbers
        return CoordinatePath(joint, owner, initial, target, elapsed[0], None if action is None else action.duration,
            ideal_slope, *actual, ideal_initial, *ideal, actual_slope, error)

    def _source_basis(self, carrier, start, end, state):
        """Reconstruct the documented uniform basis from source topology.

        This independently applies the constant/inverse/composition derivative
        rules.  Neither production phase records nor certificate fields are
        inputs.  Counts describe helper paths, so geometry and stopped/restarted
        coordinates cannot disappear from a claimed whole-phase bound.
        """
        key = (id(state), start, end)
        self.a.tick()
        self._sync_numeric_cache()
        cached = self._basis_cache.get(key)
        if cached is None or cached[0] is not state:
            cache = {"world": _SourceBound()}
            if len(self._basis_cache) < MAX_CACHE:
                self._basis_cache[key] = (state, cache)
        else:
            cache = cached[1]
            if carrier in cache:
                return cache[carrier]
        incoming = self._incoming(state)
        active_path = set()
        exact = self.a.exact

        add, mul = self.a.exact_sum, self.a.exact_product

        def rounding(extent):
            return add(mul(extent, F(1, 1 << 53)), F(3, 1 << 1075))

        def finish(**values):
            b = _SourceBound(**values)
            rotation = add(b.anchor_rotation, b.coordinate, mul(b.trig, F(1, 1 << 74)), mul(b.products, F(1, 1 << 91)))
            position = add(b.anchor_position, mul(b.offset, rotation), mul(b.vectors, F(1, 1 << 96)), rounding(b.extent))
            values.update(position_error=position, rotation_error=add(rotation, F(1, 1 << 50)))
            return _SourceBound(**values)

        def constant(pose, inverse=False):
            key = ("source_bound_constant", self.a.bits, self.a.operand_limit, tuple(pose.position), inverse)
            cached = self.a.lookup(key)
            if cached is not None:
                return cached
            extent = self._l1(pose.position)
            return self.a.remember(key, finish(
                extent=add(mul(2, extent), F(2, 1 << 96)) if inverse else extent,
                offset=extent if inverse else F(0), products=1, vectors=int(inverse)))

        def relative_composition(parent, local):
            radius = local.extent
            ideal_radius = add(radius, local.position_error)
            speed = add(parent.speed, mul(parent.omega, ideal_radius), local.speed)
            acceleration = add(parent.acceleration,
                mul(add(parent.alpha, mul(parent.omega, parent.omega)), ideal_radius),
                mul(2, parent.omega, local.speed), local.acceleration)
            omega = add(parent.omega, local.omega)
            alpha = add(parent.alpha, mul(parent.omega, local.omega), local.alpha)
            actual_speed = add(parent.actual_speed, mul(parent.actual_omega, add(radius, F(1, 1 << 96))),
                               local.actual_speed, F(2, 1 << 96))
            actual_omega = add(parent.actual_omega, local.actual_omega, F(2, 1 << 96))
            offset_error = add(local.position_error, mul(parent.rotation_error, radius), F(1, 1 << 96))
            velocity_error = add(parent.velocity_error, mul(parent.omega_error, ideal_radius),
                mul(parent.actual_omega, offset_error), local.velocity_error,
                mul(parent.rotation_error, local.actual_speed), F(4, 1 << 96), rounding(mul(2, actual_speed)))
            omega_error = add(parent.omega_error, local.omega_error,
                mul(parent.rotation_error, local.actual_omega), F(2, 1 << 96), rounding(mul(2, actual_omega)))
            return finish(extent=add(mul(2, radius), F(4, 1 << 96)),
                offset=add(parent.offset, local.offset, radius), trig=parent.trig + local.trig,
                products=parent.products + local.products + 1, vectors=parent.vectors + local.vectors + 2,
                coordinate=add(parent.coordinate, local.coordinate),
                anchor_position=add(parent.anchor_position, local.anchor_position),
                anchor_rotation=add(parent.anchor_rotation, local.anchor_rotation),
                velocity_error=velocity_error, omega_error=omega_error, speed=speed,
                acceleration=acceleration, omega=omega, alpha=alpha,
                actual_speed=actual_speed, actual_omega=actual_omega)

        def compose(parent, local):
            # Parent extent and accumulated offset affect only the final
            # position allowance. Parent position_error is not an operand of
            # this recurrence; every other parent field and the complete local
            # bound remain in the key, including local extent/offset/error.
            self.a.tick()
            self.a.guard(*(getattr(bound, name) for bound in (parent, local) for name in _SOURCE_BOUND_FIELDS))
            if any(value < 0 for value in (parent.extent, local.extent, parent.offset, local.offset)):
                raise ReferenceError("numeric", "Independent source composition has a negative extent or offset")
            extent, offset = parent.extent, parent.offset
            relative = replace(parent, extent=F(0), offset=F(0), position_error=F(0))
            key = ("source_bound_compose", self.a.bits, self.a.operand_limit, relative, local)
            base = self.a.lookup(key)
            if base is None:
                base = self.a.remember(key, relative_composition(relative, local))
            if not extent and not offset:
                return base
            total_extent, total_offset = add(extent, base.extent), add(offset, base.offset)
            if total_extent < 0 or total_offset < 0:
                raise ReferenceError("numeric", "Independent source composition has a negative extent or offset")
            correction = mul(extent, F(1, 1 << 53))
            if offset:
                # finish adds its exposed quaternion allowance only after
                # forming position. Its pre-exposure rotation also contains
                # the local coordinate, trig, product and anchor terms.
                rotation = exact(base.rotation_error, F(1, 1 << 50), "sub")
                correction = add(correction, mul(offset, rotation))
            # finish is affine in both final extent and accumulated offset.
            # These charged exact corrections restore the original Fraction
            # result, with no change to source allowances or enclosures.
            return replace(base, extent=total_extent, offset=total_offset,
                           position_error=add(base.position_error, correction))

        def root(path):
            actual_position, ideal_position = state.positions[path], state.ideal_positions[path]
            extent = self._l1(actual_position)
            position_error = self._distance(actual_position, ideal_position)
            speed = omega = F(0)
            rotation_error = state.rotation_errors[path]
            trig, products = 0, 1
            translation = state.claims.get((path, "translation"))
            if translation is not None:
                action, active = self.model.actions[translation], state.actions[translation]
                elapsed = max(abs(active.elapsed_at(start)), abs(active.elapsed_at(end)))
                extent = add(self._l1(active.initial), mul(self._l1(action.vector), elapsed))
                position_error = self._distance(active.initial, active.ideal_initial)
                speed = self._l1(action.vector) if active.status == "running" else F(0)
            orientation = state.claims.get((path, "orientation"))
            if orientation is not None:
                action, active = self.model.actions[orientation], state.actions[orientation]
                elapsed = max(abs(active.elapsed_at(start)), abs(active.elapsed_at(end)))
                rotation_error = active.rotation_error
                if any(action.vector) and elapsed:
                    trig, products = 1, 3
                omega = self._l1(action.vector) if active.status == "running" else F(0)
            return finish(extent=extent, trig=trig, products=products, anchor_position=position_error,
                anchor_rotation=rotation_error, speed=speed, omega=omega, actual_speed=speed, actual_omega=omega)

        def dynamic(path):
            anchor = state.dynamic[path]
            elapsed = max(abs(start - anchor.time), abs(end - anchor.time))
            acceleration = tuple(F(x) for x in (state.forces[path].acceleration or self.model.gravity))
            ideal_acceleration = state.forces[path].ideal_acceleration or tuple(F(x) for x in self.model.gravity)
            acceleration_error = sum((abs(exact(x, y, "sub")) for x, y in zip(acceleration, ideal_acceleration)), F(0))
            velocity, acceleration_size = self._l1(anchor.actual.velocity), self._l1(acceleration)
            extent = add(self._l1(anchor.actual.position), mul(velocity, elapsed), mul(acceleration_size, elapsed, elapsed, F(1, 2)))
            actual_speed = add(velocity, mul(acceleration_size, elapsed))
            position_error = add(anchor.position_error, mul(anchor.velocity_error, elapsed),
                                 mul(acceleration_error, elapsed, elapsed, F(1, 2)))
            velocity_error = add(anchor.velocity_error, mul(acceleration_error, elapsed), rounding(actual_speed))
            actual_omega = self._l1(anchor.actual.omega)
            moving = bool(actual_omega and elapsed)
            return finish(extent=extent, trig=int(moving), products=3 if moving else 1,
                anchor_position=position_error, anchor_rotation=add(anchor.rotation_error, mul(anchor.omega_error, elapsed)),
                velocity_error=velocity_error, omega_error=anchor.omega_error,
                speed=add(actual_speed, velocity_error), acceleration=self._l1(ideal_acceleration),
                omega=add(actual_omega, anchor.omega_error), actual_speed=actual_speed, actual_omega=actual_omega)

        def visit(frame):
            self.a.tick()
            if frame in cache:
                return cache[frame]
            if frame in active_path or len(active_path) > 128:
                raise ReferenceError("unsupported", "Independent uniform-basis graph is cyclic or too deep")
            active_path.add(frame)
            stem = frame.removesuffix(".frame")
            if stem in self.model.sites:
                site = self.model.sites[stem]
                value = compose(visit(site.owner + ".frame"), constant(site.pose))
            elif stem in incoming:
                kind, relation = incoming[stem]
                if kind == "follow":
                    follow = self.model.follows[relation]
                    value = compose(visit(follow.parent), constant(follow.offset))
                else:
                    joint = self.model.joints[relation]
                    motion = _SourceBound()
                    if joint.kind in {"hinge", "slider"}:
                        scalar = self._joint_path(relation, start, end, state)
                        axis = tuple(F(x) for x in joint.axis)
                        size = self._l1(axis)
                        rate_error = abs(exact(scalar.actual_slope, scalar.slope, "sub"))
                        if joint.kind == "hinge":
                            defect = abs(exact(add(*(mul(x, x) for x in axis)), F(1), "sub"))
                            motion = finish(trig=1, products=1, coordinate=scalar.coordinate_error,
                                omega_error=add(mul(size, rate_error), mul(defect, abs(scalar.slope))),
                                omega=abs(scalar.slope), actual_omega=mul(size, abs(scalar.actual_slope)))
                        else:
                            motion = finish(extent=mul(size, max(abs(scalar.actual_start), abs(scalar.actual_end))), products=1,
                                anchor_position=mul(size, scalar.coordinate_error), velocity_error=mul(size, rate_error),
                                speed=mul(size, abs(scalar.slope)), actual_speed=mul(size, abs(scalar.actual_slope)))
                    value = compose(compose(visit(joint.parent + ".frame"), motion),
                                    constant(self.model.sites[joint.child].pose, inverse=True))
            elif state.modes[stem] == "dynamic":
                value = dynamic(stem)
            else:
                value = root(stem)
            active_path.remove(frame)
            cache[frame] = value
            return value

        return visit(carrier)

    def _axis_transport(self, rotation, axis):
        """Prove a fixed source rotation preserves or reverses one axis.

        Exact zero patterns survive quaternion normalization. This proof also
        accepts independent intervals only when the required zeros are exact
        and at least one remaining component excludes zero. No approximate
        angle, sampled orientation or production phase value is an input.
        """
        self.a.tick()
        if type(rotation) not in (tuple, list) or len(rotation) != 4:
            return None
        values = tuple(self.a.interval(value) for value in rotation)
        self.a.guard(*(endpoint for value in values for endpoint in (value.lo, value.hi)))
        zero = tuple(value.lo == value.hi == 0 for value in values)
        if not any(value.lo > 0 or value.hi < 0 for value in values):
            return None
        if all(zero[index + 1] for index in range(3) if index != axis):
            return 1
        if zero[0] and zero[axis + 1]:
            return -1
        return None

    def _axial_derivatives(self, carrier, start, end, state):
        """Independently tighten ideal derivatives for proved coaxial paths.

        A constant angular vector in a body's coordinates is constant in the
        world too: d(Rw)/dt = R(w cross w) = 0. Parallel hinge rates can thus be
        added with their signs before taking a norm. Fixed attachments carry
        that vector through their exact axis-preserving/reversing rotations.

        The existing generic source basis, including every actual derivative
        and numeric error recurrence, remains untouched. This separate walk
        uses source offsets' L1 norms as bounds on their ideal Euclidean radii.
        Unsupported rotations, noncoaxial hinges and dynamic roots return no
        refinement. Its temporary graph map belongs to this one bounded walk;
        no additional retained numeric cache or production oracle is used.
        """
        incoming, found, visiting = self._incoming(state), {}, set()
        add, mul, exact = self.a.exact_sum, self.a.exact_product, self.a.exact

        def admit(value):
            if value is not None:
                self.a.guard(value.speed, value.acceleration, value.rate)
            return value

        def attached(parent, pose):
            self.a.tick()
            if parent is None:
                return None
            admit(parent)
            # The inverse attachment has the same Euclidean offset norm and
            # the same sign on a preserved/reversed axis as the forward pose.
            radius = self._l1(pose.position)
            sign = 1 if not parent.rate else self._axis_transport(pose.rotation, parent.axis)
            if sign is None:
                return None
            admit(parent)
            speed = add(parent.speed, mul(abs(parent.rate), radius))
            acceleration = add(parent.acceleration, mul(parent.rate, parent.rate, radius))
            rate = parent.rate if sign == 1 else exact(F(0), parent.rate, "sub")
            return _AxialDerivative(speed, acceleration, parent.axis if rate else None, rate)

        def root(path):
            if state.modes[path] == "dynamic":
                return None
            basis = self._source_basis(path + ".frame", start, end, state)
            self.a.guard(basis.speed, basis.acceleration)
            action_path = state.claims.get((path, "orientation"))
            if action_path is None or state.actions[action_path].status != "running":
                return _AxialDerivative(basis.speed, basis.acceleration, None, F(0))
            action, active = self.model.actions[action_path], state.actions[action_path]
            vector = tuple(F(value) for value in action.vector)
            self.a.guard(*vector, active.rotation_error)
            nonzero = tuple(index for index, value in enumerate(vector) if value)
            if not nonzero:
                return _AxialDerivative(basis.speed, basis.acceleration, None, F(0))
            if len(nonzero) != 1 or active.rotation_error:
                return None
            axis = nonzero[0]
            sign = self._axis_transport(active.ideal_initial, axis)
            if sign is None:
                return None
            self.a.guard(*vector, basis.speed, basis.acceleration, active.rotation_error)
            rate = vector[axis] if sign == 1 else exact(F(0), vector[axis], "sub")
            return _AxialDerivative(basis.speed, basis.acceleration, axis, rate)

        def joint_motion(parent, relation):
            joint = self.model.joints[relation]
            if parent is None or joint.kind not in {"hinge", "slider"}:
                return parent
            scalar = self._joint_path(relation, start, end, state)
            axis = tuple(F(value) for value in joint.axis)
            self.a.guard(*axis, scalar.slope, scalar.ideal_start, scalar.ideal_end)
            admit(parent)
            if joint.kind == "slider":
                size = self._l1(axis)
                radius = mul(size, max(abs(scalar.ideal_start), abs(scalar.ideal_end)))
                local_speed = mul(size, abs(scalar.slope))
                omega = abs(parent.rate)
                return _AxialDerivative(
                    add(parent.speed, mul(omega, radius), local_speed),
                    add(parent.acceleration, mul(omega, omega, radius), mul(F(2), omega, local_speed)),
                    parent.axis, parent.rate)
            nonzero = tuple(index for index, value in enumerate(axis) if value)
            if len(nonzero) != 1 or abs(axis[nonzero[0]]) != 1:
                return None
            direction = nonzero[0]
            if parent.rate and parent.axis != direction:
                return None
            local_rate = scalar.slope if axis[direction] == 1 else exact(F(0), scalar.slope, "sub")
            rate = add(parent.rate, local_rate)
            return _AxialDerivative(parent.speed, parent.acceleration, direction if rate else None, rate)

        def visit(frame):
            self.a.tick()
            if frame in found:
                return admit(found[frame])
            if frame in visiting or len(visiting) > 128:
                raise ReferenceError("unsupported", "Independent axial derivative graph is cyclic or too deep")
            visiting.add(frame)
            stem = frame.removesuffix(".frame")
            if frame == "world":
                value = _AxialDerivative(F(0), F(0), None, F(0))
            elif stem in self.model.sites:
                site = self.model.sites[stem]
                value = attached(visit(site.owner + ".frame"), site.pose)
            elif stem in incoming:
                kind, relation = incoming[stem]
                if kind == "follow":
                    follow = self.model.follows[relation]
                    value = attached(visit(follow.parent), follow.offset)
                else:
                    joint = self.model.joints[relation]
                    value = attached(joint_motion(visit(joint.parent + ".frame"), relation),
                                     self.model.sites[joint.child].pose)
            else:
                value = root(stem)
            visiting.remove(frame)
            found[frame] = admit(value)
            return value

        return visit(carrier)

    def _phase_root_poses(self, path, time, state):
        """Reuse complete phase-root calculations with fresh source authority.

        Both channels are evaluated from immutable captured operands. The
        existing bounded arithmetic cache retains only those typed operands
        and exact completed poses, never a state identity or mutable source
        object. Current authority and operands are read after every cache
        callback and before publication; a temporary source change during
        arithmetic cannot enter the captured calculation either.
        """
        def direct():
            return (self._root_pose(path, time, state, ideal=False),
                    self._root_pose(path, time, state, ideal=True))

        if (not self._recording_body_domain() or type(time) is not F
                or max(abs(time.numerator).bit_length(), time.denominator.bit_length()) > 1024):
            return direct()

        def read():
            mode = state.modes[path]
            if mode == "dynamic":
                anchor, force = state.dynamic[path], state.forces[path]
                if type(anchor.actual) is not PoseEnclosure or type(anchor.ideal) is not PoseEnclosure:
                    return ("unsupported",)
                poses = tuple((pose.position, pose.orientation, pose.velocity, pose.omega)
                              for pose in (anchor.actual, anchor.ideal))
                return ("dynamic", path, time, mode, anchor.time, *poses,
                        force.acceleration, force.ideal_acceleration, self.model.gravity)

            def action(channel):
                owner = state.claims.get((path, channel))
                if owner is None:
                    return None
                source, active = self.model.actions[owner], state.actions[owner]
                return (owner, source.kind, source.target, source.duration, source.vector,
                        (active.status, active.elapsed, active.since),
                        (active.initial, active.ideal_initial))

            return ("prescribed", path, time, mode,
                    (state.positions[path], state.orientations[path]),
                    (state.ideal_positions[path], state.ideal_orientations[path]),
                    action("translation"), action("orientation"))

        receipt = self._recording_capture(read)
        if receipt is None or receipt.values[0] == "unsupported":
            return direct()
        def capture(value):
            # Native frozen cells are copied as well as their containing
            # tuples. Source records can be replaced by a callback, and even
            # hostile in-place changes must never alter captured arithmetic.
            if type(value) is Interval:
                return Interval(value.lo, value.hi)
            if type(value) is tuple:
                return tuple(capture(part) for part in value)
            return value

        values = capture(receipt.values)

        def typed(value):
            if type(value) is F:
                return ("fraction", value.numerator, value.denominator)
            if type(value) is float:
                return ("float", value.hex())
            if type(value) is int:
                return ("int", value)
            if type(value) is Interval:
                return ("interval", typed(value.lo), typed(value.hi))
            if type(value) is tuple:
                return tuple(typed(part) for part in value)
            return ("none",) if value is None else ("string", value)

        signature, limit = typed(values), self.a.operand_limit
        key = ("source_phase_root_pair", self.a.bits, limit, signature)

        def current():
            return self.a.operand_limit == limit and self._recording_body_domain()

        def admit():
            if not current():
                return False
            try:
                observed = read()
            except (KeyError, AttributeError, IndexError) as error:
                raise ReferenceError("identity", "Independent phase root changed during proof") from error
            if (self._recording_source_witness(*observed) is None or typed(observed) != signature):
                raise ReferenceError("identity", "Independent phase root changed during proof")
            # The existing receipt guard admits all numeric leaves, without
            # another callback between this complete read and the return.
            self._recording_admit_receipts((_RecordingSourceReceipt(lambda: observed, values),))
            return True

        result = self.a.lookup(key)
        if not admit():
            return direct()
        if result is not None:
            self.a.guard(*(endpoint for pose in result
                           for vector in (pose.position, pose.orientation, pose.velocity, pose.omega)
                           for cell in vector for endpoint in (cell.lo, cell.hi)))
            return result

        def calculate(channel):
            if values[0] == "dynamic":
                saved = values[5 + channel]
                dt = time - values[4]
                acceleration = values[7 + channel] or values[9]
                position = self.p.add(self.p.add(saved[0], self.p.scale(saved[2], dt)),
                                      self.p.scale(acceleration, dt * dt / 2))
                rotation = self.p.multiply(self.p.spin(saved[3], dt), saved[1])
                return PoseEnclosure(position, rotation,
                    self.p.add(saved[2], self.p.scale(acceleration, dt)), saved[3])

            position, orientation = values[4 + channel]
            velocity, omega = self.p.vector(ZERO), self.p.vector(ZERO)
            move, spin = values[6:]

            def elapsed(action):
                status, amount, since = action[5]
                return amount + (time - since if status == "running" else 0)

            if move is not None:
                position = self.p.add(move[6][channel], self.p.scale(move[4], elapsed(move)))
                if move[5][0] == "running":
                    velocity = self.p.vector(move[4])
            if spin is not None:
                orientation = self.p.multiply(self.p.spin(spin[4], elapsed(spin)), spin[6][channel])
                if spin[5][0] == "running":
                    omega = self.p.vector(spin[4])
            return PoseEnclosure(position, orientation, velocity, omega)

        if values[0] == "dynamic":
            channel_inputs = tuple((values[5 + channel], values[7 + channel] or values[9])
                                   for channel in (0, 1))
        else:
            channel_inputs = tuple((values[4 + channel],
                                    *(None if action is None else action[6][channel] for action in values[6:]))
                                   for channel in (0, 1))
        actual = calculate(0)
        if not current():
            return direct()
        # Identical typed inputs use identical equations and intermediate
        # preflights in this unchanged domain, including every rate field.
        ideal = actual if typed(channel_inputs[0]) == typed(channel_inputs[1]) else calculate(1)
        result = actual, ideal
        if not admit():
            return direct()
        self.a.guard(*(endpoint for pose in result
                       for vector in (pose.position, pose.orientation, pose.velocity, pose.omega)
                       for cell in vector for endpoint in (cell.lo, cell.hi)))
        self.a.remember(key, result, admission=admit)
        # A newly narrowed cache-publication callback must execute the
        # original calculation in its own domain. Original errors escape.
        return result if current() else direct()

    def _phase_root_distance(self, first, last):
        """Omit the exact zero distance between equal native point vectors.

        Every original subtraction needs at most 2049 prospective bits on
        this small domain; even its optional 128-bit grid fits below 2178.
        The subsequent L1 fold contains only literal zeros. Equal uncertain
        cells retain their original nonzero interval-width calculation.
        """
        def points():
            if (type(first) is not tuple or type(last) is not tuple or len(first) != 3 or len(last) != 3
                    or any(type(cell) is not Interval or type(cell.lo) is not F or type(cell.hi) is not F
                           or max(abs(cell.lo.numerator).bit_length(), cell.lo.denominator.bit_length(),
                                  abs(cell.hi.numerator).bit_length(), cell.hi.denominator.bit_length()) > 1024
                           for vector in (first, last) for cell in vector)
                    or any(a.lo != a.hi or b.lo != b.hi or a.lo != b.lo for a, b in zip(first, last))):
                return None
            return tuple(tuple(cell.lo for cell in vector) for vector in (first, last))

        values = points()
        if not self._recording_body_domain() or values is None:
            return self._distance(first, last)
        self.a.tick()
        # Even native frozen cells can be replaced or maliciously mutated by
        # a callback. Recheck the zero premise before omitting subtraction;
        # no later callback occurs between this capture and the zero result.
        if points() != values:
            return self._distance(first, last)
        self.a.guard(*(value for vector in values for value in vector))
        # A callback can narrow the live domain before this zero proof. Keep
        # the prospective widths of the omitted original point subtractions
        # and their output grid before any later callback can restore it.
        for value in values[0]:
            if value:
                numerator, denominator = abs(value.numerator).bit_length(), value.denominator.bit_length()
                if max(numerator + denominator + 1, denominator * 2) > self.a.operand_limit:
                    raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
                self.a._grid_domain(F(0), F(0))
        if self.a.operand_limit < 2:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        if not self._recording_body_domain():
            return self._distance(first, last)
        return F(0)

    def _phase(self, carrier, start, end, state):
        root, _, joints, path = self._ancestry(carrier, state)
        identity = self.p.identity()
        actual_root, ideal_root = ((identity, identity) if root is None else
                                   self._phase_root_poses(root, start, state))
        acceleration = tuple(F(x) for x in ((state.forces[root].acceleration or self.model.gravity)
                             if root is not None and state.modes[root] == "dynamic" else ZERO))
        basis = self._source_basis(carrier, start, end, state)
        # A single constant angular contribution already has the same generic
        # norm and zero angular acceleration. Only compositions with a generic
        # cross contribution need this additional independent source proof.
        axial = self._axial_derivatives(carrier, start, end, state) if basis.alpha else None
        coordinates = tuple(self._joint_path(joint, start, end, state) for joint in joints)
        anchor_velocity = self._phase_root_distance(actual_root.velocity, ideal_root.velocity)
        anchor_omega = self._phase_root_distance(actual_root.omega, ideal_root.omega)
        if root is not None and state.modes[root] == "dynamic":
            anchor_velocity = max(anchor_velocity, state.dynamic[root].velocity_error)
            anchor_omega = max(anchor_omega, state.dynamic[root].omega_error)
        speed, acceleration_bound, angular_speed = (basis.speed, basis.acceleration, basis.omega) if axial is None else (
            axial.speed, axial.acceleration, abs(axial.rate))
        return ReferencePhase(start, end, carrier, speed, acceleration_bound, angular_speed, coordinates,
            actual_root.position, actual_root.velocity, acceleration, actual_root.orientation, actual_root.omega,
            ideal_root.position, ideal_root.velocity, ideal_root.orientation, ideal_root.omega,
            basis.offset, basis.extent, basis.anchor_position, basis.anchor_rotation, anchor_velocity, anchor_omega,
            basis.position_error, basis.rotation_error, basis.velocity_error, basis.omega_error,
            basis.trig, basis.products, basis.vectors, basis.coordinate, path)
